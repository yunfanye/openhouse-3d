"""Download explicitly listed assets with SHA-256 verification; never scrape listings."""
import argparse
import json
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from archviz.media import digest, local_path


def fetch(manifest):
    manifest = Path(manifest).resolve()
    rows = json.loads(manifest.read_text(encoding='utf-8'))
    for row in rows:
        destination = local_path(manifest.parent, row['file'])
        if not row['url'].startswith('https://') or len(row['sha256']) != 64:
            raise ValueError('Asset entries require an HTTPS URL and SHA-256 digest')
        if destination.exists():
            if digest(destination) != row['sha256']:
                raise ValueError(f'Existing asset differs from manifest: {destination}')
            print(f'Verified {destination.name}')
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + '.download')
        try:
            with urllib.request.urlopen(row['url'], timeout=60) as source, temporary.open('wb') as output:
                while True:
                    block = source.read(1024 * 1024)
                    if not block:
                        break
                    output.write(block)
            if digest(temporary) != row['sha256']:
                raise ValueError(f'Download checksum mismatch: {destination.name}')
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
        print(f'Downloaded {destination.name}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    fetch(parser.parse_args().manifest)
