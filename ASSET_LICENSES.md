# Asset provenance and redistribution

The MIT license applies to this project's code and documentation. It does not
relicense reference photographs, source floor plans, fonts, third-party textures,
or other media. The public-listing reference sets for Alpine, Stanford, Walsh and
Webster are included at the maintainer's direction so the examples can be followed
and reproduced. Images are removed on request under
[the photo removal policy](PHOTO_REMOVAL.md).

| Material | Provenance | Distribution policy |
| --- | --- | --- |
| Webster HDRI and photographic texture maps | Poly Haven; exact URLs and SHA-256 values in `houses/webster/assets/sources.json` | CC0; downloadable with `tools/fetch_assets.py` |
| Reference house photographs and listing floor plans | Public-listing reference sets; source manifests retained where available | Included for the Alpine, Stanford, Walsh and Webster examples; original rights retained; removal on request |
| Stanford HDRI sky | Poly Haven `kloppenheim_06_puresky`; URL and SHA-256 in `houses/stanford/assets/sources.json` | CC0; downloadable with `tools/fetch_assets.py`; not committed |
| Stanford film music | "Wonders of the Earth" by Grand_Project, Pixabay; details and SHA-256 in `houses/stanford/assets/music.json` | Pixabay Content License; manual download, not committed |
| Photo comparison videos, galleries and ZIPs | Include reference photographs | Published release videos (such as the Stanford side-by-side) are distributed at the maintainer's direction under the same removal-on-request policy; otherwise distribute only with permission covering the included photos |
| Stanford photo-rectified textures (art, prints, some textiles) | Rectified at build time from `houses/stanford/photos/` by `archviz/phototex.py`; every photo + pixel quad is listed in the modules' `PHOTO_TEX` tables | Renders and models that contain them carry the reference photographs' rights (and those of any artwork shown); nothing is written next to the photos |
| Webster music | Synthesized by `houses/webster/promo.py`; no third-party recording | Project-generated score; included in the final delivery |
| Alpine rug textures and score | `houses/alpine/assets/rug_*.png` drawn by `houses/alpine/textiles.py` (fixed seeds); score synthesized by `houses/alpine/promo.py` | Project-generated; MIT with the code |
| System fonts | Selected locally; not bundled in the repository | Do not copy proprietary system font files into releases |
| Blender, FFmpeg and Python dependencies | External tools installed separately | Their upstream licenses apply |

Poly Haven explicitly licenses its assets under [CC0](https://polyhaven.com/license).
The website's text and trademarks are distinct from its asset license. Attribution
links are retained to make source assets and changes auditable.

For each new asset record its author/source, original URL, local filename, license,
retrieval date when known, and SHA-256. For each reference photo record whether you
own it or have redistribution permission. Do not invent an author or permission
statement when it is unknown. Do not put credentials, signed download URLs or
private photo metadata into a public manifest.

Keep original image files and source records together so a removal request can
identify the affected material. Do not replace original credits or apply the MIT
code license to the reference images. See [the publishing guide](docs/publishing.md)
for source and release handling.
