# `generate_set_video.py`

Creates an MP4 for a DJ set from its audio, cover art, and timestamped per-track images. Each track scene displays the project title and current track while applying a slow zoom and pan profile. An optional cross-dissolve blends adjacent scenes. The script renders temporary video chunks with FFmpeg, merges them with the original audio, and removes its temporary files afterward.

It prepares a video file for a later upload; it does not upload, schedule, or publish anything on YouTube. The `youtube` metadata is descriptive only.

## Requirements

- Python 3.10 or later.
- FFmpeg, available on `PATH` or configured with `ffmpeg_path` / `--ffmpeg-path`.
- Mutagen: `pip install mutagen` (used to read the MP3 duration).
- PyYAML: `pip install pyyaml` for `.yaml` or `.yml` metadata. JSON metadata uses the standard library.
- A valid font file for FFmpeg `drawtext`, configured using `font_path`.

For Intel Quick Sync intermediate encoding, FFmpeg must also be built with the `h264_qsv` encoder and run on a machine with a working QSV device. The final cross-fade merge is encoded with `libx264`.

## Usage

From the repository root:

```powershell
python scripts/generate_set_video.py path\to\set-metadata.yaml
```

Supported command-line options:

| Option               | Description                                          |
|----------------------|------------------------------------------------------|
| `--ffmpeg-path PATH` | Override `ffmpeg_path` from the metadata.            |
| `--print-command`    | Print the planned FFmpeg commands without rendering. |

Other paths and rendering options are configured in the metadata file. The current script does not accept `--images-dir`, `--cover-duration`, or `--slide-duration`; images are selected per track in `tracklist`.

## Metadata Example

```yaml
project: Progressive Awake
title: Example set (October 2026)
set_type: progressive_awake
font_path: "C:\\Windows\\Fonts\\arial.ttf"

audio_path: "C:\\Sets\\Example\\mix.mp3"
cover_path: "C:\\Sets\\Example\\cover.jpg"
output_path: "C:\\Sets\\Example\\mix.mp4" # optional
output_audio_bitrate: 192k
ffmpeg_path: "C:\\Apps\\ffmpeg\\bin\\ffmpeg.exe"

video:
  width: 1920
  height: 1080
  crf: 20
  preset: medium
  encoder: libx264
  intermediate_scale: 8000
  transition_duration: 2.5 # seconds; set to 0 for hard cuts

youtube:
  title: "Progressive Awake - Example set (October 2026)"
  privacy: private
  publish_at:

description: |
  Description prepared for a later YouTube upload.

tracklist:
  - time: "00:00"
    track_name: "Artist - First track"
    image: "C:\\Sets\\Example\\slides\\01.jpg"
  - time: "05:30"
    track_name: "Artist - Second track"
    image: "C:\\Sets\\Example\\slides\\02.jpg"
```

`audio_path` and `cover_path` must exist. A track must be a mapping with `time` and `track_name`; `image` is optional and falls back to `cover_path`. Timestamps use `MM:SS` or `HH:MM:SS`, should be in ascending order, and determine each scene's duration up to the next track. The last scene runs to the audio duration. Track image paths are passed to FFmpeg during rendering, so check that they exist before starting a long render.

## Metadata Fields

| Field                                                                          | Default / behavior                                                                                        |
|--------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| `project`, `title`                                                             | Used to derive the on-screen project title and default output filename.                                   |
| `youtube.title`                                                                | Optional explicit title; otherwise `project - title` is used.                                             |
| `audio_path`, `cover_path`                                                     | Required existing audio and cover files. Audio duration is read from the MP3.                             |
| `tracklist`                                                                    | Required non-empty list of mappings with `time` and `track_name`; optional `image` per track.             |
| `font_path`                                                                    | Font passed to FFmpeg `drawtext`. Relative paths resolve from the `scripts` directory.                    |
| `set_type`                                                                     | Motion profile: `progressive_awake`, `quantum_energy`, or `fresh_dance`; defaults to `progressive_awake`. |
| `output_path`                                                                  | Optional explicit MP4 path; takes precedence over `output_dir`.                                           |
| `output_dir`                                                                   | Optional output directory; defaults to the audio file's directory.                                        |
| `output_audio_bitrate`                                                         | AAC output bitrate; defaults to `video.audio_bitrate` or `320k`.                                          |
| `ffmpeg_path`                                                                  | FFmpeg executable; defaults to `ffmpeg`.                                                                  |
| `video.width`, `video.height`                                                  | Output dimensions; default to 1920 x 1080.                                                                |
| `video.crf`, `video.preset`                                                    | Encoder quality and preset; defaults to `22` and `fast`.                                                  |
| `video.encoder`                                                                | Intermediate chunk encoder: `libx264` by default, or `h264_qsv`.                                          |
| `video.intermediate_scale`                                                     | Internal image-processing width; defaults to 8000.                                                        |
| `video.transition_duration`                                                    | Cross-dissolve duration in seconds; defaults to 0 (hard cuts).                                            |
| `description`, `tags`, `date`, `slug`, `youtube.privacy`, `youtube.publish_at` | Descriptive or downstream workflow metadata; not uploaded to YouTube by this script.                      |

## Rendering Behavior

- The source image is scaled and cropped to fill the output aspect ratio, then rendered with a brand-specific zoom/pan profile. Track and project titles are overlaid on the video.
- Each image scene is rendered as a temporary chunk. With a positive `transition_duration`, adjacent chunks are joined with an FFmpeg cross-dissolve and the final video is re-encoded with `libx264`. With no transition, chunks are concatenated with stream copy before the audio is added.
- The result uses AAC audio and ends at the shorter of the rendered video and source audio (`-shortest`). The default output filename is derived from the YouTube title, with characters invalid in filenames replaced by hyphens.
- `--print-command` is useful for reviewing FFmpeg arguments and resolved paths before rendering. It does not validate that every track image is readable by FFmpeg.

For image dimensions and missing artwork, run [`check_image_quality.py`](check_image_quality.md) against the same metadata before rendering.
