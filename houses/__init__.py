"""One package per house.  houses/<name>/ holds plan.py (constants), house.py (config), shots.py (film), the geometry
modules, photos/ and output/.  This module only knows where things are (bpy-free, used by run.py and the tools)."""
import importlib, os
import keyword

ROOT = os.path.dirname(os.path.abspath(__file__))


def path(name, *parts):
    if not name.isidentifier() or keyword.iskeyword(name):
        raise ValueError('House name must be a Python identifier')
    return os.path.join(ROOT, name, *parts)


def load(name):
    """The house's config module (houses/<name>/house.py) - bpy-free, so tools under system python can use it too."""
    path(name)  # Validate before importing a dynamically selected package.
    return importlib.import_module(f"houses.{name}.house")
