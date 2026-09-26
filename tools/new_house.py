"""Create a runnable house package without copying reference images or outputs."""
import argparse
import keyword
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def create(name, title, root=ROOT):
    if not name.isidentifier() or keyword.iskeyword(name) or name.startswith('_'):
        raise ValueError('Use a Python identifier such as my_house, without a leading underscore')
    destination = Path(root) / 'houses' / name
    if destination.exists():
        raise FileExistsError(f'House already exists: {destination}')
    shutil.copytree(Path(root) / 'houses/_template', destination,
                    ignore=shutil.ignore_patterns('output', 'photos', '__pycache__', '*.pyc'))
    config = destination / 'house.py'
    text = config.read_text(encoding='utf-8')
    text = text.replace('NAME = "_template"', f'NAME = {name!r}')
    text = text.replace('TITLE = "Template house"', f'TITLE = {title!r}')
    text = text.replace('BLEND = "template.blend"', f'BLEND = {name + ".blend"!r}')
    config.write_text(text, encoding='utf-8')
    (destination / 'photos').mkdir()
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name')
    parser.add_argument('--title', default='My house')
    args = parser.parse_args()
    print(create(args.name, args.title))


if __name__ == '__main__':
    main()
