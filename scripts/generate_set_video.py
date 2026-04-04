from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def load_metadata(path: Path) -> dict:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise SystemExit(
                "Reading YAML metadata requires PyYAML. Install it with: pip install pyyaml"
            ) from exc
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    raise SystemExit("Unsupported metadata format. Use .yaml, .yml or .json")


def build_ffmpeg_command(metadata: dict, ffmpeg_path: str) -> list[str]:
    video = metadata.get("video", {})
    width = int(video.get("width", 1920))
    height = int(video.get("height", 1080))
    audio_bitrate = str(metadata.get("output_audio_bitrate") or video.get("audio_bitrate", "192k"))
    crf = str(video.get("crf", 20))
    preset = str(video.get("preset", "medium"))

    cover_path = str(metadata["cover_path"])
    audio_path = str(metadata["audio_path"])
    output_path = str(metadata["output_path"])

    scale_pad = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,format=yuv420p"
    )

    return [
        ffmpeg_path,
        "-y",
        "-loop",
        "1",
        "-i",
        cover_path,
        "-i",
        audio_path,
        "-vf",
        scale_pad,
        "-c:v",
        "libx264",
        "-tune",
        "stillimage",
        "-crf",
        crf,
        "-preset",
        preset,
        "-c:a",
        "aac",
        "-b:a",
        audio_bitrate,
        "-pix_fmt",
        "yuv420p",
        "-shortest",
        "-movflags",
        "+faststart",
        output_path,
    ]


def derive_youtube_title(metadata: dict) -> str:
    youtube = metadata.get("youtube", {}) or {}
    explicit_title = youtube.get("title")
    if explicit_title:
        return str(explicit_title)

    project = str(metadata.get("project", "")).strip()
    title = str(metadata.get("title", "")).strip()
    if project and title:
        return f"{project} - {title}"
    if title:
        return title

    return Path(str(metadata["audio_path"])).stem


def sanitize_filename(name: str) -> str:
    sanitized = re.sub(r'[<>:"/\\|?*]', "-", name)
    sanitized = re.sub(r'\s+', " ", sanitized).strip().rstrip(".")
    return sanitized or "output"


def derive_output_path(metadata: dict, youtube_title: str) -> Path:
    explicit_output_path = metadata.get("output_path")
    if explicit_output_path:
        return Path(str(explicit_output_path))

    output_dir = metadata.get("output_dir")
    if output_dir:
        base_dir = Path(str(output_dir))
    else:
        base_dir = Path(str(metadata["audio_path"])).parent

    output_filename = sanitize_filename(youtube_title) + ".mp4"
    return base_dir / output_filename


def validate_paths(metadata: dict) -> None:
    for key in ("audio_path", "cover_path"):
        path = Path(metadata[key])
        if not path.exists():
            raise SystemExit(f"Missing file: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an MP4 for a DJ set from metadata.")
    parser.add_argument("metadata", help="Path to a YAML or JSON metadata file.")
    parser.add_argument(
        "--ffmpeg-path",
        help="Path to ffmpeg executable. Overrides ffmpeg_path from metadata.",
    )
    parser.add_argument(
        "--print-command",
        action="store_true",
        help="Print the ffmpeg command without running it.",
    )
    args = parser.parse_args()

    metadata_path = Path(args.metadata)
    if not metadata_path.exists():
        raise SystemExit(f"Metadata file not found: {metadata_path}")

    metadata = load_metadata(metadata_path)
    validate_paths(metadata)
    ffmpeg_path = args.ffmpeg_path or metadata.get("ffmpeg_path") or "ffmpeg"

    youtube_title = derive_youtube_title(metadata)
    output_path = derive_output_path(metadata, youtube_title)
    metadata["output_path"] = str(output_path)
    metadata.setdefault("youtube", {})
    metadata["youtube"]["title"] = youtube_title

    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = build_ffmpeg_command(metadata, str(ffmpeg_path))
    if args.print_command:
        print(subprocess.list2cmdline(command))
        return 0

    print(f"YouTube title: {youtube_title}")
    print(f"Generating MP4: {output_path}")
    try:
        completed = subprocess.run(command, check=False)
    except FileNotFoundError as exc:
        raise SystemExit(
            f"ffmpeg executable not found: {ffmpeg_path}. Pass --ffmpeg-path or set ffmpeg_path in metadata."
        ) from exc
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())