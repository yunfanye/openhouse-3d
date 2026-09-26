"""Checksum final deliverables and prune intermediates only after verification.

python -m archviz.delivery houses/my_house/output --record
python -m archviz.delivery houses/my_house/output
python -m archviz.delivery houses/my_house/output --prune
"""
import argparse
import json
from pathlib import Path
import shutil

from .media import digest, local_path, write_json


def record(final):
    final = Path(final).resolve()
    if not final.is_dir():
        raise ValueError(f'Final directory does not exist: {final}')
    files = {}
    for path in sorted(final.rglob('*')):
        if path.is_symlink():
            raise ValueError(f'Final delivery must contain real files, not symlinks: {path}')
        if path.is_file() and path != final / 'SHA256SUMS.json':
            files[path.relative_to(final).as_posix()] = {'sha256': digest(path), 'bytes': path.stat().st_size}
    if not files:
        raise ValueError('Refusing to record an empty delivery')
    write_json(final / 'SHA256SUMS.json', {'schema_version': 1, 'files': files})
    return files


def verify(final):
    final = Path(final).resolve()
    files = json.loads((final / 'SHA256SUMS.json').read_text(encoding='utf-8'))['files']
    if not files:
        raise ValueError('Delivery inventory is empty')
    paths = list(final.rglob('*'))
    if any(p.is_symlink() for p in paths):
        raise ValueError('Delivery must not contain symlinks')
    actual = {p.relative_to(final).as_posix() for p in paths
              if p.is_file() and p != final / 'SHA256SUMS.json'}
    if actual != set(files):
        raise ValueError(f'Delivery inventory differs: {actual.symmetric_difference(files.keys())}')
    for name, entry in files.items():
        path = local_path(final, name)
        if path.stat().st_size != entry['bytes'] or digest(path) != entry['sha256']:
            raise ValueError(f'Delivery checksum mismatch: {path}')
    return files


def prune(output, apply=False):
    output = Path(output)
    if output.name != 'output' or output.is_symlink():
        raise ValueError('Pruning is restricted to a directory named output')
    output = output.resolve()
    verify(output / 'final')
    candidates = sorted(p for p in output.iterdir() if p.name != 'final')
    total = 0
    for path in candidates:
        items = path.rglob('*') if path.is_dir() and not path.is_symlink() else [path]
        total += sum(p.lstat().st_size for p in items if p.is_file() or p.is_symlink())
    if apply:
        for path in candidates:
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink()
    return {'paths': [p.name for p in candidates], 'bytes': total, 'deleted': apply}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--record', action='store_true', help='Create/replace checksums after accepting a delivery')
    mode.add_argument('--prune', action='store_true', help='Delete everything outside final/ after validating its inventory')
    args = parser.parse_args(argv)
    if args.record:
        print(f'Recorded {len(record(args.output / "final"))} files')
    else:
        print(json.dumps(prune(args.output, args.prune), indent=2))


if __name__ == '__main__':
    main()
