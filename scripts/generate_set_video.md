# generate_set_video.py

Generates an MP4 video file from a DJ set's audio and cover/slide images, ready for upload to YouTube.

## Requirements

- Python 3.10+
- [ffmpeg](https://ffmpeg.org/) in PATH or specified via `ffmpeg_path`
- PyYAML (`pip install pyyaml`) when using `.yaml`/`.yml` metadata files

## Usage

```
python generate_set_video.py <metadata> [options]
```

| Argument             | Description                                                                                   |
|----------------------|-----------------------------------------------------------------------------------------------|
| `metadata`           | Path to a `.yaml`, `.yml` or `.json` metadata file                                            |
| `--ffmpeg-path PATH` | Path to the ffmpeg executable. Overrides `ffmpeg_path` from metadata                          |
| `--images-dir DIR`   | Directory with additional slide images. Overrides `images_dir` from metadata                  |
| `--cover-duration N` | Seconds to display the cover image (slideshow mode). Overrides `cover_duration` from metadata |
| `--slide-duration N` | Seconds to display each slide image. Overrides `slide_duration` from metadata                 |
| `--print-command`    | Print the ffmpeg command without running it                                                   |

## Metadata file

All configuration is stored in a YAML (or JSON) file alongside the set files.

### Full example

```yaml
project: Progressive Awake
title: 7 months of dream (July 2009)
slug: 7-months-of-dream-dont-want-to-wake-up-july-2009
date: 2009-07-15

audio_path: C:\Users\you\Sets\2009-07-15\Shivioua - 7 Months Of Dream.mp3
cover_path:  C:\Users\you\Sets\2009-07-15\Shivioua - 7 Months Of Dream.jpg

# --- Slideshow (optional) ---
images_dir: C:\Users\you\Sets\2009-07-15\photos
cover_duration: 15   # seconds the cover is shown first (default: 10)
slide_duration: 8    # seconds per slide image (default: 10)

# --- Output ---
# output_path: explicit output file path (optional)
output_dir: C:\Users\you\Sets\output   # output directory (optional, defaults to audio_path dir)
output_audio_bitrate: 192k

ffmpeg_path: "C:\\Apps\\ffmpeg\\bin\\ffmpeg.exe"

video:
  width: 1920
  height: 1080
  crf: 20
  preset: medium

youtube:
  privacy: private
  publish_at:        # ISO 8601 datetime, leave empty to skip scheduling
  # title:           # explicit YouTube title; derived from project + title if omitted

description: |
  Your set description here.

tracklist:
  - artist - track title
  - artist - track title
```

### Field reference

#### Required

| Field        | Description                                      |
|--------------|--------------------------------------------------|
| `audio_path` | Path to the source MP3/audio file                |
| `cover_path` | Path to the cover image (always the first frame) |

#### Output

| Field                  | Default   | Description                                                                 |
|------------------------|-----------|-----------------------------------------------------------------------------|
| `output_path`          | derived   | Explicit output `.mp4` path. Takes priority over `output_dir`               |
| `output_dir`           | audio dir | Directory for the generated MP4. Filename is derived from the YouTube title |
| `output_audio_bitrate` | `192k`    | AAC audio bitrate in the output video                                       |

#### Slideshow

| Field            | Default | Description                                                                            |
|------------------|---------|----------------------------------------------------------------------------------------|
| `images_dir`     | —       | Directory of additional slide images. If absent, the cover loops for the full duration |
| `cover_duration` | `10`    | Seconds the cover image is displayed at the start                                      |
| `slide_duration` | `10`    | Seconds each image from `images_dir` is displayed                                      |

Supported image formats: `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.tiff`, `.tif`, `.gif`.  
Images in `images_dir` are sorted alphabetically and played in that order after the cover.

#### Video encoding

Nested under the `video` key:

| Field    | Default  | Description                                               |
|----------|----------|-----------------------------------------------------------|
| `width`  | `1920`   | Output frame width                                        |
| `height` | `1080`   | Output frame height                                       |
| `crf`    | `20`     | libx264 CRF quality (lower = better quality, larger file) |
| `preset` | `medium` | libx264 encoding preset (`ultrafast` … `veryslow`)        |

#### YouTube metadata

Nested under the `youtube` key:

| Field        | Description                                                                |
|--------------|----------------------------------------------------------------------------|
| `title`      | Explicit YouTube title. If omitted, derived as `"<project> - <title>"`     |
| `privacy`    | Intended privacy setting (informational, not applied automatically)        |
| `publish_at` | Intended scheduled publish time (informational, not applied automatically) |

#### Other

| Field         | Default  | Description                                                     |
|---------------|----------|-----------------------------------------------------------------|
| `ffmpeg_path` | `ffmpeg` | Path to the ffmpeg executable                                   |
| `project`     | —        | Project/brand name, used to derive the YouTube title            |
| `title`       | —        | Set title, used to derive the YouTube title and output filename |
| `description` | —        | Set description (informational)                                 |
| `tracklist`   | —        | List of tracks (informational)                                  |

## Output filename

When `output_path` is not set, the filename is derived from the YouTube title with characters illegal in filenames replaced by `-`. For example:

```
Progressive Awake - 7 months of dream (July 2009).mp4
```

## Modes of operation

### Single-image mode (no `images_dir`)

The cover image loops as a still frame for the full duration of the audio:

```
ffmpeg -loop 1 -i cover.jpg -i audio.mp3 ... -shortest output.mp4
```

### Slideshow mode (`images_dir` provided)

A temporary concat list is generated and passed to ffmpeg's concat demuxer:

```
file '/path/to/cover.jpg'
duration 15
file '/path/to/photos/01.jpg'
duration 8
file '/path/to/photos/02.jpg'
duration 8
...
```

The video ends when the audio ends (`-shortest`), so the last image may be cut short if the audio finishes before all slides are shown, or the last slide will hold if the audio outlasts the images.
