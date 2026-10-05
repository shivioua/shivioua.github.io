# `check_image_quality.py`

Reads a set's YAML metadata and prints a report for its cover image and each image explicitly assigned to a track. It is a pre-render screening aid; its resolution and file-size heuristics do not assess visual sharpness or artistic quality.

## Requirements

- Python 3.10 or later.
- Pillow: `pip install pillow`
- PyYAML: `pip install pyyaml`

## Usage

```powershell
python scripts/check_image_quality.py path\to\set-metadata.yaml
```

The script accepts one YAML path as its positional argument. Use the same `cover_path`, `video.intermediate_scale`, and `tracklist` fields as the video-generation metadata.

## What Is Checked

- The `cover_path`, if present, and each `image` specified on a track are opened and measured.
- The report includes dimensions, megapixels, file size, a heuristic rating, and missing/unreadable file warnings.
- The default recommended source width is one quarter of `video.intermediate_scale`, which defaults to 8000 pixels (a 2000-pixel recommendation). The rating bands are based on image pixel count: under 0.5 MP is poor, 0.5-2 MP is low, 2-4 MP is fair, 4-8 MP is good, and 8 MP or more is excellent.
- Files below 30,000 bytes per megapixel are additionally flagged for possible heavy compression when they are at least 1 MP.
- A track without an explicit `image` is reported as using the cover image and is not opened as a separate file.

The report suggests considering a 4x AI upscale for flagged artwork. Treat this as a prompt to inspect the source yourself, not as a guarantee that upscaling will improve it. The script reports findings in the console; it does not modify images or metadata.

## Example Metadata

```yaml
cover_path: "C:\\Sets\\Example\\cover.jpg"
video:
  intermediate_scale: 8000
tracklist:
  - time: "00:00"
    track_name: "Artist - Track"
    image: "C:\\Sets\\Example\\slides\\01.jpg"
```