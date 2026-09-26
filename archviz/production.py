"""Render a frozen packed scene in resumable chunks, with input fingerprints.

Use a fresh run directory after changing scene, Blender version, device, or filter
settings. No renderer is launched on import. This module runs in system Python.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from .media import check_image, digest, write_json

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / 'tools/render_scene.py'


def bind_run(folder, fingerprint):
    folder = Path(folder)
    manifest = folder / 'run.json'
    if manifest.exists():
        if json.loads(manifest.read_text(encoding='utf-8')) != fingerprint:
            raise ValueError(f'Render inputs changed; use a new --out directory. Existing run: {folder}')
    elif any(folder.glob('frames/**/*')):
        raise ValueError(f'Unidentified existing frames; use a new --out directory: {folder}')
    else:
        write_json(manifest, fingerprint)


def missing_frames(folder, first, last, size):
    missing = []
    for frame in range(first, last + 1):
        path = Path(folder) / f'f_{frame:04d}.png'
        if not path.exists():
            missing.append(frame)
        else:
            # Corrupt files must not be treated as completed frames by Blender.
            try:
                check_image(path, size)
            except (OSError, ValueError, SyntaxError) as error:
                raise ValueError(f'Invalid completed frame {path}; remove it and resume: {error}') from error
    return missing


def run_worker(command, log, timeout, attempts=2):
    """Bounded retries; terminate only the subprocess started by this call."""
    for attempt in range(1, attempts + 1):
        with Path(log).open('a') as stream:
            stream.write(f'\nAttempt {attempt}: {command!r}\n')
            stream.flush()
            process = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
            try:
                code = process.wait(timeout=timeout)
            except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
                process.terminate()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                if isinstance(error, KeyboardInterrupt):
                    raise
                code = -1
        if code == 0:
            return
        print(f'[production] attempt {attempt} failed ({code}); see {log}', flush=True)
    raise RuntimeError(f'Render failed after {attempts} attempts; see {log}')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scene', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--shot', default='cinematic', help='Frame subfolder name')
    parser.add_argument('--blender', default=os.environ.get('BLENDER', 'blender'))
    parser.add_argument('--device', default=os.environ.get('ARCHVIZ_DEVICE', 'AUTO'),
                        choices=['AUTO', 'CPU', 'OPTIX', 'CUDA', 'HIP', 'ONEAPI', 'METAL'])
    parser.add_argument('--chunk', type=int, default=96)
    parser.add_argument('--timeout', type=float, default=3600, help='Maximum seconds per chunk attempt')
    parser.add_argument('--temporal', action='store_true', help='Generate vectors and filter after rendering all raw frames')
    parser.add_argument('--radius', type=int, default=3)
    parser.add_argument('--tolerance', type=float, default=10)
    args = parser.parse_args(argv)
    if args.chunk <= 0 or args.timeout <= 0 or args.radius < 1 or args.tolerance <= 0:
        parser.error('Chunk, timeout, radius and tolerance must be positive')
    if not args.shot.isidentifier():
        parser.error('--shot must be a Python identifier')
    blender = shutil.which(args.blender)
    if not blender:
        parser.error('Blender not found; set --blender or BLENDER to its executable')
    scene, out = args.scene.resolve(), args.out.resolve()
    if not scene.is_file():
        parser.error(f'Scene does not exist: {scene}')
    out.mkdir(parents=True, exist_ok=True)
    # O_EXCL prevents two controllers from sharing a run. Stale locks require
    # inspection of their recorded PID before removal; never guess and kill it.
    lock = out / 'production.lock'
    try:
        descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        parser.error(f'Run is locked: {lock}; inspect its PID before removing a stale lock')
    with os.fdopen(descriptor, 'w') as stream:
        stream.write(str(os.getpid()) + '\n')
    try:
        logs = out / 'logs'
        logs.mkdir(exist_ok=True)
        base = [blender, '-b', str(scene), '--python-exit-code', '1', '--python', str(WORKER), '--']
        run_worker(base + ['info', '--out', str(out / 'scene_info.json'), '--device', args.device], logs / 'info.log', args.timeout)
        info = json.loads((out / 'scene_info.json').read_text(encoding='utf-8'))
        code_paths = [WORKER, Path(__file__), ROOT / 'archviz/film.py', ROOT / 'archviz/filmkit.py',
                      ROOT / 'archviz/rendering.py', ROOT / 'tools/temporal.py']
        fingerprint = {'scene_sha256': digest(scene), 'scene_info': info, 'device': args.device,
                       'shot': args.shot, 'temporal': args.temporal, 'radius': args.radius,
                       'tolerance': args.tolerance,
                       'code': {p.relative_to(ROOT).as_posix(): digest(p) for p in code_paths}}
        bind_run(out, fingerprint)
        frames = out / 'frames' / args.shot
        frames.mkdir(parents=True, exist_ok=True)
        first, last = info['start'], info['end']
        if first < 1 or last < first:
            raise ValueError(f'Invalid scene frame range: {first}..{last}')
        for stage in (['frames', 'vectors', 'filter'] if args.temporal else ['frames']):
            for start in range(first, last + 1, args.chunk):
                end = min(last, start + args.chunk - 1)
                if stage == 'frames' and not missing_frames(frames, start, end, info['size']):
                    continue
                write_json(out / 'progress.json', {'stage': stage, 'range': [start, end], 'updated': time.time()})
                if stage == 'filter':
                    command = [blender, '-b', '--python-exit-code', '1', '--python', str(ROOT / 'tools/temporal.py'),
                               '--', str(frames), '--radius', str(args.radius), '--tol', str(args.tolerance),
                               '--range', f'{start}-{end}']
                else:
                    command = base + [stage, '--out', str(frames), '--start', str(start), '--end', str(end), '--device', args.device]
                run_worker(command, logs / f'{stage}_{start:04d}_{end:04d}.log', args.timeout)
            if stage in ('frames', 'filter'):
                folder = frames if stage == 'frames' else frames.with_name(args.shot + '_tf')
                missing = missing_frames(folder, first, last, info['size'])
                if missing:
                    raise ValueError(f'{stage} exited without required frames: {missing[:20]}')
        write_json(out / 'progress.json', {'stage': 'frames_complete', 'updated': time.time(), 'visual_review': 'pending'})
    finally:
        lock.unlink()


if __name__ == '__main__':
    main()
