"""Shared media I/O for system Python; importing this module never imports bpy."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def write_json(path, data):
    """Replace a report atomically so interruption cannot leave half a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temporary.replace(path)


def local_path(root, value):
    """Resolve a manifest path within its root, including symlink containment."""
    root = Path(root).resolve()
    path = (root / value).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f'Path escapes manifest root: {value}')
    return path


def font(size, path=None, serif=False, face='regular'):
    """Use an explicit font or a platform font, then Pillow's bundled font.

    Explicit paths fail on typos. Automatic discovery catches only a missing or
    unreadable font; other Pillow errors propagate. For identical typography on
    different machines, provide the same licensed font via ARCHVIZ_FONT.
    """
    from PIL import ImageFont
    selected = path or os.environ.get('ARCHVIZ_FONT')
    if selected:
        return ImageFont.truetype(str(selected), size)
    candidates = (
        ['/System/Library/Fonts/Supplemental/Baskerville.ttc', 'DejaVuSerif.ttf', 'times.ttf']
        if serif else
        ['/System/Library/Fonts/HelveticaNeue.ttc', 'DejaVuSans.ttf', 'arial.ttf']
    )
    for candidate in candidates:
        try:
            index = {'ultralight': 5, 'light': 7, 'regular': 0, 'medium': 10}[face] if candidate.endswith('HelveticaNeue.ttc') else 0
            return ImageFont.truetype(candidate, size, index=index)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def fit_image(path, size, background='#182123'):
    from PIL import Image, ImageOps
    with Image.open(path) as source:
        fitted = ImageOps.contain(ImageOps.exif_transpose(source).convert('RGB'), size,
                                 Image.Resampling.LANCZOS)
    canvas = Image.new('RGB', size, background)
    canvas.paste(fitted, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2))
    return canvas


def check_image(path, size=None, min_stddev=None):
    from PIL import Image, ImageStat
    with Image.open(path) as image:
        if size is not None and image.size != tuple(size):
            raise ValueError(f'{path}: expected {tuple(size)}, found {image.size}')
        image.verify()
    if min_stddev is not None:
        with Image.open(path) as image:
            deviation = max(ImageStat.Stat(image.convert('RGB').resize((160, 107))).stddev)
        if deviation < min_stddev:
            raise ValueError(f'{path}: image appears blank (stddev {deviation:.2f})')


def ffmpeg(args, **kwargs):
    import imageio_ffmpeg
    return subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-y', *args],
                          check=True, **kwargs)


def metadata(path):
    import imageio_ffmpeg
    frames = imageio_ffmpeg.read_frames(str(path))
    try:
        return next(frames)
    finally:
        frames.close()


def read_frame(path, number, size, fps):
    from PIL import Image
    result = ffmpeg(['-v', 'error', '-ss', f'{number / fps:.12f}', '-i', str(path),
                     '-frames:v', '1', '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-'],
                    stdout=subprocess.PIPE)
    if len(result.stdout) != size[0] * size[1] * 3:
        raise ValueError(f'Could not decode frame {number} from {path}')
    return Image.frombytes('RGB', tuple(size), result.stdout)


def audio_hash(path):
    return ffmpeg(['-v', 'error', '-i', str(path), '-map', '0:a:0', '-c:a', 'copy',
                   '-f', 'hash', '-hash', 'sha256', '-'],
                  stdout=subprocess.PIPE, text=True).stdout.strip()
