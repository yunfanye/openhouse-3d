# Photo galleries and synchronized comparison videos

Both commands run in ordinary Python. Paths inside a manifest are relative to its
own directory and must stay within it, including symlink resolution. Put a house's
manifests at its root so `photos/`, `assets/` and `output/` are reachable.

## Gallery manifest

Start from `houses/_template/gallery.example.json` or Webster's full `gallery.json`.
A minimal manifest:

```json
{
  "schema_version": 1,
  "house": "My house",
  "render_resolution": [1920, 1080],
  "notes": "Furniture is staged; hidden dimensions are inferred.",
  "pairs": [
    {
      "photo": 0,
      "title": "Front exterior",
      "camera": "hero",
      "original": "photos/00.jpg",
      "render": "output/renders/hero.png",
      "note": "Roof pitch inferred from the side photograph.",
      "render_kind": "whole_house_model"
    }
  ]
}
```

Photo IDs need not be consecutive, but must be unique nonnegative integers. List
pairs in the desired navigation order. A supporting floor plan belongs in
`supporting_references` as `{ "source": "photos/plan.jpg", "file": "floor_plan.jpg",
"kind": "original_floor_plan" }`. Optional `model` points to the packed house scene;
its hash is recorded, but the large scene is not silently bundled into a gallery ZIP.

```sh
python -m archviz.gallery --config houses/my_house/gallery.json \
  --out houses/my_house/output/gallery --archive houses/my_house/output/gallery.zip
```

The gallery validates every image before copying. It preserves source bytes, checks
the declared render dimensions and rejects apparently blank renders. It creates a
responsive, offline HTML viewer with keyboard controls and a comparison slider,
numbered images, downloadable pairs, an overview and checksummed `manifest.json`.
The ZIP contains only explicit generated members, not arbitrary logs in the directory.
Use notes to describe separate studies as `separate_photo_derived_detail`.

## Video timeline

The input movie must be limited-range BT.709 SDR, square-pixel, at a positive integer
constant frame rate. HDR, variable-rate phone recordings, anamorphic media and
fractional broadcast rates are outside this compositor's current contract. Normalize
such input with a deliberate color/timing conversion first; simply changing metadata
is not a valid HDR-to-SDR conversion. The source file is checked and never overwritten.

```json
{
  "schema_version": 1,
  "title": "My house · Photo comparison",
  "source": "output/house.mp4",
  "gallery": "output/gallery",
  "fps": 24,
  "frames": 240,
  "source_size": [1920, 1080],
  "output_size": [1920, 1800],
  "segments": [
    { "start_frame": 0, "photo": 0, "title": "Front exterior" }
  ]
}
```

The first segment starts at **frame 0**. Each following `start_frame` ends the prior
hold and must increase strictly. The last hold ends at `frames`. Optional
`review_time` is in seconds within that segment; otherwise the verifier samples its
middle. A photo may recur. A separate detail study is rejected because it cannot
represent the model shown in the original film.

```sh
python -m archviz.comparison --timeline houses/my_house/comparison_video_timeline.json \
  --work houses/my_house/output/comparison_work \
  --output houses/my_house/output/comparison.mp4 --prepare-only
# Inspect panels and composition.json, then run without --prepare-only.
```

Output width equals source width; only the height increases. The top movie is not
scaled or cropped. Its video is encoded again with H.264 CRF 12 to make one composite
MP4. The bottom panel is converted from image RGB into limited-range BT.709. Labels
and contained images scale with the canvas; photos are never stretched or cropped.
Audio, if present, is muxed afterward without a video-frame limit to avoid cutting
AAC packets early. Silent source movies are supported.

FFmpeg's concat demuxer defaults stills to 25 fps. Each panel explicitly sets
`option framerate` to the timeline rate, and repeats the last panel to close its
hold. This is necessary for exact frame switches. See the
[concat format specification](https://ffmpeg.org/ffmpeg-formats.html#concat).

Every normal encode runs verification. `--verify-only` rechecks an existing movie
using the work directory's `composition.json` and panels: full decode, timing,
all-frame cinematic SSIM, copied-audio packet hash, representative panels and both
sides of every switch. `poster.jpg`, `contact_sheet.jpg` and `validation.json` are
written to the work directory. Inspect them and native frames before acceptance.
The panel RGB error bound assumes ordinary photographic imagery; extreme chroma
noise may fail because H.264 uses 4:2:0 subsampling. Do not relax a failing quality
check without inspecting the reason.

Comparison renders need a photo-like viewpoint, but a moving cinematic camera may
only roughly align with them. The lower panel is an evidence/reference pair timed
to the room or feature being shown, not a claim of pixel registration with every
moving frame.
