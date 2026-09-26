# Setup and portability

The tested Blender runtime is 5.2.1. The house builders use Blender 5 APIs,
including layered actions, compositor node groups and video output settings.
Older Blender versions are not part of the supported contract. The Python tools
are tested separately from Blender; installing a package named `bpy` into the
system interpreter is unnecessary.

## Install

Install Blender from [Blender's downloads](https://www.blender.org/download/).
Make its executable available as `blender`, or substitute the full executable
path in Blender commands. `archviz.production` also accepts `--blender` / `BLENDER`.
On macOS, the app executable is typically
`/Applications/Blender.app/Contents/MacOS/Blender`.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
export ARCHVIZ_PYTHON="$PWD/.venv/bin/python"
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
$env:ARCHVIZ_PYTHON = "$PWD\.venv\Scripts\python.exe"
$env:BLENDER = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
& $env:BLENDER -b --python-exit-code 1 --python run.py -- --house _template --cam hero --scale 25 --samples 16 --device CPU --no-polish
```

Use the actual installed directory. Paths containing spaces must be quoted.
`ARCHVIZ_PYTHON` tells Blender which **external Python** has Pillow and NumPy when
it generates titles. System Python runs gallery/comparison/production tools;
Blender runs geometry, render, camera and vector-pass scripts.

## Device selection

`run.py --device` and `archviz.production --device` accept `AUTO`, `CPU`, `METAL`,
`OPTIX`, `CUDA`, `HIP`, and `ONEAPI`. `ARCHVIZ_DEVICE` supplies the default.
`AUTO` tries supported GPU backends and reports discovery failures if it uses CPU.
An explicitly requested unavailable GPU fails rather than silently changing devices.
Preferences are configured for the current process, not saved to the user's startup file.
CPU mode explicitly disables GPU denoising.

Only CPU and Metal were exercised on the maintainer's hardware. The other backend
names follow Blender's Cycles interface and need testing on their corresponding
hardware. A tiny CPU render is the portable installation check. See Blender's
[GPU rendering manual](https://docs.blender.org/manual/en/latest/render/cycles/gpu_rendering.html).

## Dependencies and fonts

`pyproject.toml` bounds Python dependencies. To record an exact production
installation, save `python -m pip freeze`, `blender --version`, OS, GPU and driver
information alongside the run manifest. Dependency bounds are not a bitwise
reproducibility guarantee across Blender, GPU drivers, fonts or operating systems.

Media tools use the FFmpeg executable supplied by `imageio-ffmpeg`; no separate
`ffmpeg` command is required. Set `IMAGEIO_FFMPEG_EXE` if using your own build,
which must provide H.264/AAC encoders and the `ssim`, `showinfo`, `vfrdet`, `scale`, and
`vstack` filters. FFmpeg and Blender retain their upstream licenses.

Typography selects a usable system font, then Pillow's bundled font. For stable
appearance across machines, set `ARCHVIZ_FONT` to the same licensed TTF/TTC file.
An invalid explicit font path fails. Font files are not copied from macOS into the
repository.

## Photographic assets

The starter is entirely procedural. Webster uses the six CC0 assets listed in
`houses/webster/assets/sources.json`; Stanford's film uses one CC0 HDRI sky listed in
`houses/stanford/assets/sources.json` (without it, Stanford falls back to the procedural sky):

```sh
python tools/fetch_assets.py houses/webster/assets/sources.json
python tools/fetch_assets.py houses/stanford/assets/sources.json
```

Existing files must match their recorded SHA-256. Downloads are checked before
being promoted from temporary files. This command only downloads explicitly
listed URLs; it does not scrape property listings or acquire reference-photo rights.
