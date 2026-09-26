# Publishing source and deliverables

## Keep source small and runnable

Commit code, manifests, documentation, tests, small project-owned source assets,
and the reference sets for Alpine, Stanford, Walsh and Webster, with source
manifests where available. Stanford's filenames use `01.jpg` through `32.jpg`;
image bytes are preserved. New house photo folders remain ignored by default.
Ignore output directories, downloaded maps, environments and caches.
Use release assets for accepted movies/models/gallery ZIPs. A `.gitignore` rule does
not untrack existing files or remove older commits; inspect both the proposed source
snapshot and repository history before changing visibility.

Preserve the example references during housekeeping and follow
[the removal policy](../PHOTO_REMOVAL.md) when an image is requested for removal.
Do not rewrite or discard published history casually.

## Review a source release

- Verify the starter builds from a fresh source checkout without private photos,
  external asset caches, local paths or a saved production `.blend`.
- Run the Python suite and lint. Check links and command examples. Record the Blender
  smoke render separately: CI currently checks Python/media behavior, not Cycles.
- Inspect tracked files for outputs, secrets, private manifests and unexpectedly
  large blobs. Verify the MIT license and separate asset-rights notes are present.
- Record the source commit and versions used for a delivery. Use a tag for the
  release so commands and source files can be identified later.

## Package final media

`output/final/SHA256SUMS.json` lists exact retained files and their sizes/digests.
Verify it immediately before archiving. Package that explicit final directory,
not its parent `output/`, which may contain frame caches and unaccepted candidates.
Include the frozen model, source movie, comparison movie, score, gallery, useful
stills, QA and any portable model derivatives needed to open it on another machine.

The gallery contains original photo bytes. It therefore preserves EXIF metadata,
including location if present. Make a reviewed distribution copy if redaction is
necessary; regenerate checksums afterward rather than silently altering originals.
Photo ownership, photographer credits and licenses must be accurate. Source URLs
and a listing's public availability are not a substitute for permission.

A release note should identify the source commit, accepted movie frame count,
resolution/fps, known inferred architecture, staging, separate studies, validation
performed and any media access restrictions. Keep machine-specific logs and temporary
paths out of the public description. Historical QA can remain in a private delivery
archive when needed to audit the work.
