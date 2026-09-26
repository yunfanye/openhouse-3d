# Contributing

Install with `python -m pip install -e '.[dev]'` and read the
[architecture notes](docs/architecture.md). House-specific geometry belongs under
that house; broadly useful mesh/material/camera/media helpers belong in `archviz`.
Keep new configuration small and demonstrated by a runnable example.

For a fix or refactor, identify the behavior to preserve and add a regression test
when the change can break timing, geometry, validation, encoding, or recovery.
Avoid tests that merely restate a line of implementation. Run:

```sh
python -m pytest -q
python -m ruff check .
blender -b --python-exit-code 1 --python run.py -- --house _template --cam hero --samples 8 --scale 25 --no-polish --device CPU
```

The Python suite includes actual FFmpeg encodes and verifies frame boundaries,
video quality and audio packet preservation. It does not replace a Blender render
or a visual review. If changing Blender code, attach the Blender version, device,
render settings, affected camera/frame and a before/after comparison. If moving
geometry helpers, compare mesh/topology/material signatures too
(`tools/scene_signature.py` dumps one per build).

The pull request should describe the concrete problem, resulting behavior, tests,
and material limitations. Explain observed architectural evidence separately from
inferred geometry or new staging. Do not upload raw frame sequences, proprietary
fonts, credentials, or reference photos without redistribution rights.
