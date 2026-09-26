"""Manifest-driven offline photo/render galleries. Run: python -m archviz.gallery --help."""
import argparse
import html
import json
import math
from pathlib import Path
import shutil
import zipfile

from PIL import Image, ImageDraw

from .media import check_image, digest, fit_image as fit, font, local_path, write_json

def pair_image(number, title, original, render, note, output):
    width, height, gap = 1280, 854, 24
    canvas = Image.new('RGB', (width*2 + gap*3, height + 150), '#182123')
    d = ImageDraw.Draw(canvas)
    d.text((gap, 15), f'{number:02d}  /  {title}', font=font(27), fill='#f2f3ed')
    d.text((gap, 55), 'ORIGINAL PHOTO', font=font(19), fill='#bec7c2')
    d.text((width+gap*2, 55), 'BLENDER RENDER', font=font(19), fill='#cfdfb9')
    canvas.paste(fit(original, (width, height)), (gap, 88))
    canvas.paste(fit(render, (width, height)), (width+gap*2, 88))
    words, line, y = note.split(), '', height + 106
    for word in words:
        candidate = (line + ' ' + word).strip()
        if d.textlength(candidate, font=font(19)) > canvas.width - gap*2:
            d.text((gap, y), line, font=font(19), fill='#bec7c2')
            line, y = word, y + 24
        else:
            line = candidate
    d.text((gap, y), line, font=font(19), fill='#bec7c2')
    canvas.save(output, quality=94, subsampling=0)
    return canvas


def gallery(records, out, config):
    cards, thumbs, options = [], [], []
    for position, v in enumerate(records):
        i, title = v['photo'], html.escape(v['title'])
        original, render = v['original'], v['render']
        cards.append(f'''<article class="pair" id="photo-{i:02d}" data-photo="{i}">
  <div class="pair-heading"><h2><span>{i:02d}</span> {title}</h2><p class="count">{position+1} / {len(records)}</p></div>
  <div class="side-by-side">
    <figure><figcaption><span class="dot original-dot"></span>Original photo<a href="{original}" target="_blank" rel="noopener" aria-label="Open original photo {i:02d}">Open ↗</a></figcaption><img src="{original}" width="1920" height="1280" loading="lazy" alt="Original listing photo {i:02d}: {title}"></figure>
    <figure><figcaption><span class="dot render-dot"></span>Rendered view<a href="{render}" target="_blank" rel="noopener" aria-label="Open render {i:02d}">Open ↗</a></figcaption><img src="{render}" width="1920" height="1280" loading="lazy" alt="Blender render matching photo {i:02d}: {title}"></figure>
  </div>
  <div class="wipe" hidden>
    <div class="wipe-images" style="--split:50%">
      <img src="{render}" width="1920" height="1280" loading="lazy" alt="Rendered view for photo {i:02d}">
      <img class="wipe-original" src="{original}" width="1920" height="1280" loading="lazy" alt="Original photo {i:02d}">
      <span class="wipe-label left">Original</span><span class="wipe-label right">Render</span>
      <div class="wipe-divider" aria-hidden="true"><span>↔</span></div>
      <input type="range" min="0" max="100" value="50" step="1" aria-label="Photo {i:02d} comparison slider: original photo visible percentage" aria-valuetext="50% original photo">
    </div><p class="wipe-hint">Drag to compare · use arrow keys for fine adjustments. Camera alignment is approximate.</p>
  </div>
  <div class="pair-footer"><p>{html.escape(v['note'])}</p><a class="download" href="{v['pair']}" download>Download pair ↓</a></div>
</article>''')
        thumbs.append(f'''<a class="thumbnail" href="#photo-{i:02d}" data-select="{i}" aria-label="View photo {i:02d}: {title}"><img src="thumbnails/{i:02d}.jpg" width="300" height="200" loading="lazy" alt=""><span><b>{i:02d}</b>{title}</span></a>''')
        options.append(f'<option value="{i}">{i:02d} · {title}</option>')
    template = (Path(__file__).parent / 'templates/gallery.html').read_text(encoding='utf-8')
    page = template.replace('<!-- PAIRS -->', '\n'.join(cards))
    page = page.replace('<!-- THUMBNAILS -->', '\n'.join(thumbs))
    page = page.replace('<!-- OPTIONS -->', '\n'.join(options))
    for key, value in {'TITLE': config['house'], 'HEADING': config.get('heading', config['house'] + ', side by side.'), 'COUNT': str(len(records)), 'DESCRIPTION': config.get('description', 'Original photos paired with rendered views.'), 'NOTES': config.get('notes', 'Camera alignment and hidden dimensions are approximate.')}.items():
        page = page.replace('{{' + key + '}}', html.escape(value))
    references = ' '.join(f'<a href="references/{html.escape(item["file"], quote=True)}" target="_blank" rel="noopener">{html.escape(item["kind"].replace("_", " ").capitalize())} ↗</a>' for item in config.get('supporting_references', []))
    page = page.replace('{{REFERENCES}}', references)
    (out / 'index.html').write_text(page, encoding='utf-8')


def build(config_path, out, archive=None):
    config_path, out = Path(config_path).resolve(), Path(out).resolve()
    config = json.loads(config_path.read_text(encoding='utf-8'))
    if config.get('schema_version') != 1:
        raise ValueError('Gallery requires schema_version 1')
    rows = config['pairs']
    numbers = [row['photo'] for row in rows]
    if not numbers or any(type(n) is not int or n < 0 for n in numbers) or len(set(numbers)) != len(numbers):
        raise ValueError('Photo IDs must be unique nonnegative integers; at least one pair is required')
    if not config.get('house'):
        raise ValueError('house must be a display title')
    sources = []
    for row in rows:
        if not isinstance(row.get('title'), str) or not row['title'].strip():
            raise ValueError(f'Photo {row["photo"]} requires a title')
        original = local_path(config_path.parent, row['original'])
        render = local_path(config_path.parent, row['render'])
        if any(path.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.webp') for path in (original, render)):
            raise ValueError('Gallery images must be browser-readable PNG, JPEG, or WebP files')
        check_image(original)
        check_image(render, config.get('render_resolution'), min_stddev=8)
        if row.get('render_kind', 'whole_house_model') not in ('whole_house_model', 'separate_photo_derived_detail'):
            raise ValueError(f'Unknown render_kind: {row}')
        sources.append((row, original, render))
    references = []
    for reference in config.get('supporting_references', []):
        name = reference['file']
        if Path(name).name != name or name in ('', '.', '..'):
            raise ValueError(f'Reference file must be a basename: {name}')
        source = local_path(config_path.parent, reference['source'])
        check_image(source)
        references.append((reference, source))
    model = local_path(config_path.parent, config['model']) if config.get('model') else None
    model_hash = digest(model) if model else None
    # Validate every input before producing any gallery files.
    for folder in ('originals', 'renders', 'pairs', 'thumbnails', 'references'):
        (out / folder).mkdir(parents=True, exist_ok=True)
    records, tiles, members = [], [], []
    for row, original, render in sources:
        number = row['photo']
        record = dict(row, original=f'originals/{number:02d}{original.suffix.lower()}',
                      render=f'renders/{number:02d}{render.suffix.lower()}', pair=f'pairs/{number:02d}.jpg',
                      note=row.get('note', ''), render_kind=row.get('render_kind', 'whole_house_model'))
        for kind, source in [('original', original), ('render', render)]:
            destination = out / record[kind]
            if source != destination.resolve():
                shutil.copy2(source, destination)
            record[kind + '_sha256'] = digest(destination)
            members.append(destination)
        thumb = out / f'thumbnails/{number:02d}.jpg'
        fit(original, (300, 200)).save(thumb, quality=86)
        tile = pair_image(number, row['title'], original, render, record['note'], out / record['pair'])
        tiles.append(tile.resize((780, round(tile.height * 780 / tile.width)), Image.Resampling.LANCZOS))
        members.extend([thumb, out / record['pair']])
        records.append(record)
    overview = Image.new('RGB', (1608, 92 + math.ceil(len(tiles) / 2) * (tiles[0].height + 18)), '#111918')
    draw = ImageDraw.Draw(overview)
    draw.text((24, 18), f'{config["house"]} / {len(records)} PHOTO PAIRS', font=font(28), fill='#eef2e9')
    draw.text((24, 56), 'Original left · Blender render right', font=font(18), fill='#bec7c2')
    for index, tile in enumerate(tiles):
        overview.paste(tile, (18 + index % 2 * 798, 92 + index // 2 * (tile.height + 18)))
    overview.save(out / 'overview.jpg', quality=92)
    reference_records = []
    for reference, source in references:
        destination = out / 'references' / reference['file']
        if source != destination.resolve():
            shutil.copy2(source, destination)
        reference_records.append({'file': destination.relative_to(out).as_posix(),
                                  'kind': reference['kind'], 'paired': False, 'sha256': digest(source)})
        members.append(destination)
    manifest = {'schema_version': 1, 'house': config['house'], 'photo_pair_count': len(records),
                'render_resolution': config.get('render_resolution'), 'pairs': records,
                'supporting_references': reference_records, 'house_model_sha256': model_hash}
    write_json(out / 'manifest.json', manifest)
    gallery(records, out, config)
    (out / 'README.md').write_text(
        f'# {config["house"]} photo comparisons\n\nOpen `index.html` in a browser; the gallery works offline. '
        'Use the photo selector, previous/next buttons, or keyboard-accessible comparison slider.\n\n'
        f'{config.get("notes", "")}\n\n'
        '`manifest.json` records camera mappings, image hashes, and supporting references. '
        'Photographs retain their original rights; the software license does not relicense media.\n',
        encoding='utf-8')
    members.extend(out / name for name in ('index.html', 'README.md', 'manifest.json', 'overview.jpg'))
    if archive:
        archive = Path(archive)
        archive.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=3) as bundle:
            for path in sorted(set(members)):
                bundle.write(path, Path('gallery') / path.relative_to(out))
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path, help='Gallery JSON; paths are relative to this file')
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--archive', type=Path, help='Optional ZIP of only the generated gallery files')
    args = parser.parse_args(argv)
    result = build(args.config, args.out, args.archive)
    print(f'Built {result["photo_pair_count"]} photo pairs: {args.out / "index.html"}')


if __name__ == '__main__':
    main()
