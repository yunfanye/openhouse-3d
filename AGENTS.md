# Working on this repository

- Read README.md and the affected house's README.md before changing a workflow.
- Keep transferable helpers in archviz; do not import a house into the library.
- Preserve accepted deliveries under houses/*/output/final; compare SHA-256 before
  and after housekeeping. Source rebuilding is separate from the accepted binary.
- Plan geometry and permanent fixtures follow reference evidence. Label inferred
  dimensions and staging. Check every reference, not only the hero view.
- Run `python -m pytest -q` and `python -m ruff check .`. For Blender changes, run a
  small CPU template render with `--python-exit-code 1`, then an affected-house build
  or focused render. Record actual visual and structural checks.
- Use one full-scene Cycles job per GPU unless measurements justify concurrency.
- Never resume frames after a scene/settings change in the same run directory.
- Generated outputs and new house photo folders are ignored. The Alpine, Stanford,
  Walsh and Webster references are intentionally tracked; preserve them during cleanup. Follow PHOTO_REMOVAL.md for removal requests.
  Package explicit final files in releases; document the provenance of new inputs.
- Alpine is an incomplete experimental project. Do not restart its production as
  part of housekeeping or use its partial frames as an accepted delivery.
