from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

try:
    from mutagen.mp3 import MP3  # type: ignore
except ImportError:
    MP3 = None  # type: ignore


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


def _escape_concat_path(path: Path) -> str:
    return path.as_posix().replace("'", "\\'")


def time_to_seconds(t_str: str) -> float:
    """Convert MM:SS or HH:MM:SS format to seconds."""
    parts = list(map(int, t_str.split(":")))
    if len(parts) == 2:
        return float(parts[0] * 60 + parts[1])
    if len(parts) == 3:
        return float(parts[0] * 3600 + parts[1] * 60 + parts[2])
    return 0.0


def get_audio_duration(audio_path: Path) -> float:
    """Return audio duration in seconds using mutagen."""
    if MP3 is None:
        raise SystemExit(
            "Getting audio duration requires mutagen. Install it with: pip install mutagen"
        )
    return MP3(str(audio_path)).info.length


def generate_profile_settings(set_type: str) -> tuple[str, float, float]:
    """Return (z_formula, pan_period_seconds, fps).

    Pan uses a constant-velocity triangle wave bounce: x and y are in linear
    sawtooth motion at 90° phase offset, so when x is at a turning point y is
    at maximum speed and vice versa — the combined motion is always moving.
    Triangle wave eliminates the velocity=0 pauses that sine/cosine produce at
    their peaks, which appear as visible stutters/freezes.
    intermediate_scale default is 8000 so each 1-source-pixel integer step
    maps to only ~0.28 output pixels, making step artefacts imperceptible.
    """
    if set_type == "progressive_awake":
        # Slow zoom (max 1.15x in ~24s) + 90s hypnotic drift (~0.93px/frame src)
        return "min(zoom+0.00025,1.15)", 90.0, 25.0
    if set_type == "quantum_energy":
        # Fast zoom (max 1.25x in ~11s) + 30s aggressive bounce (~2.79px/frame src)
        return "min(zoom+0.0009,1.25)", 30.0, 25.0
    if set_type == "fresh_dance":
        # Medium zoom (max 1.20x in ~18s) + 60s fresh drift (~1.39px/frame src)
        return "min(zoom+0.00045,1.20)", 60.0, 25.0
    return "1", 90.0, 25.0


def build_chunk_command(
    ffmpeg_path: str,
    img_path: Path,
    duration: float,
    filter_complex: str,
    output_path: Path,
    encoder: str,
    crf: str,
    preset: str,
    fps: float,
) -> list[str]:
    if encoder == "h264_qsv":
        # Upload frames to Intel GPU just before encoding; CPU handles all filters.
        # -init_hw_device and -filter_hw_device are required so hwupload has a device context.
        vf = filter_complex + ",hwupload=extra_hw_frames=64,format=qsv"
        codec_args = ["-c:v", "h264_qsv", "-global_quality", crf, "-preset", preset]
        pix_args: list[str] = []
        color_args: list[str] = []
        hw_args = ["-init_hw_device", "qsv=hw", "-filter_hw_device", "hw"]
    else:
        vf = filter_complex
        codec_args = ["-c:v", "libx264", "-crf", crf, "-preset", preset]
        pix_args = ["-pix_fmt", "yuv420p"]
        # Declare correct color metadata so players don't misinterpret JPEG full-range source.
        color_args = ["-colorspace", "bt709", "-color_primaries", "bt709",
                      "-color_trc", "bt709", "-color_range", "tv"]
        hw_args: list[str] = []

    return [
        ffmpeg_path, "-y",
        "-hide_banner", "-loglevel", "error",
        *hw_args,
        "-threads", "0",
        "-loop", "1", "-i", str(img_path),
        "-t", str(duration),
        "-filter_complex", vf,
        *codec_args,
        *pix_args,
        *color_args,
        "-r", str(fps),
        str(output_path),
    ]


def build_final_command(
    ffmpeg_path: str,
    concat_file: Path,
    audio_path: Path,
    output_path: Path,
    audio_bitrate: str,
) -> list[str]:
    return [
        ffmpeg_path, "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", audio_bitrate,
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path),
    ]


def build_final_xfade_command(
    ffmpeg_path: str,
    video_files: list[Path],
    audio_path: Path,
    output_path: Path,
    audio_bitrate: str,
    durations: list[float],
    transition_duration: float,
    crf: str,
    preset: str,
) -> list[str]:
    """Build a final merge command with cross-dissolve transitions between chunks."""
    n = len(video_files)
    audio_index = n

    input_args: list[str] = []
    for vf in video_files:
        input_args += ["-i", str(vf)]
    input_args += ["-i", str(audio_path)]

    if n == 1:
        filter_complex = "[0:v]null[vout]"
    else:
        parts: list[str] = []
        cumulative_offset = 0.0
        prev_label = "[0:v]"
        for i in range(1, n):
            cumulative_offset += durations[i - 1] - transition_duration
            out_label = "[vout]" if i == n - 1 else f"[x{i:04d}]"
            parts.append(
                f"{prev_label}[{i}:v]xfade=transition=fade"
                f":duration={transition_duration}:offset={cumulative_offset:.3f}{out_label}"
            )
            prev_label = f"[x{i:04d}]"
        filter_complex = ";".join(parts)

    return [
        ffmpeg_path, "-y",
        "-hide_banner",
        *input_args,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", f"{audio_index}:a:0",
        "-c:v", "libx264", "-crf", crf, "-preset", preset,
        "-pix_fmt", "yuv420p",
        "-colorspace", "bt709", "-color_primaries", "bt709",
        "-color_trc", "bt709", "-color_range", "tv",
        "-c:a", "aac", "-b:a", audio_bitrate,
        "-shortest",
        "-movflags", "+faststart",
        str(output_path),
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
        help="Print all ffmpeg commands without running them.",
    )
    args = parser.parse_args()

    metadata_path = Path(args.metadata)
    if not metadata_path.exists():
        raise SystemExit(f"Metadata file not found: {metadata_path}")

    metadata = load_metadata(metadata_path)
    validate_paths(metadata)

    ffmpeg_path = str(args.ffmpeg_path or metadata.get("ffmpeg_path") or "ffmpeg")
    set_type = str(metadata.get("set_type", "progressive_awake"))

    font_path_raw = str(metadata.get("font_path", "Arial"))
    font_resolved = Path(font_path_raw)
    if not font_resolved.is_absolute():
        font_resolved = Path(__file__).parent / font_path_raw
    if font_resolved.suffix and not font_resolved.exists():
        raise SystemExit(f"Font file not found: {font_resolved}")
    font_path = str(font_resolved).replace("\\", "/").replace(":", "\\:")

    audio_file_path = Path(metadata["audio_path"])
    total_duration = get_audio_duration(audio_file_path)

    video = metadata.get("video", {})
    width = int(video.get("width", 1920))
    height = int(video.get("height", 1080))
    crf = str(video.get("crf", 22))
    preset = str(video.get("preset", "fast"))
    encoder = str(video.get("encoder", "libx264"))
    intermediate_scale = int(video.get("intermediate_scale", 8000))
    transition_duration = float(video.get("transition_duration", 0.0))

    tracklist = metadata.get("tracklist") or []
    if not tracklist:
        raise SystemExit("Error: Tracklist is empty in metadata.")
    for i, track in enumerate(tracklist):
        if not isinstance(track, dict) or "time" not in track or "track_name" not in track:
            raise SystemExit(
                f"Tracklist item {i} must be a dict with 'time' and 'track_name' fields. "
                "Got: " + repr(track)
            )

    # Compute per-track duration from consecutive timestamps
    for i, track in enumerate(tracklist):
        start_sec = time_to_seconds(track["time"])
        end_sec = (
            time_to_seconds(tracklist[i + 1]["time"])
            if i < len(tracklist) - 1
            else total_duration
        )
        track["_duration"] = end_sec - start_sec

    youtube_title = derive_youtube_title(metadata)
    output_path = derive_output_path(metadata, youtube_title)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    audio_bitrate = str(
        metadata.get("output_audio_bitrate") or video.get("audio_bitrate", "320k")
    )
    zoom_formula, pan_period, fps = generate_profile_settings(set_type)

    tmp_dir = tempfile.mkdtemp()
    temp_video_files: list[Path] = []

    try:
        chunk_commands: list[tuple[dict, list[str]]] = []

        for i, track in enumerate(tracklist):
            img_path = Path(str(track.get("image") or metadata["cover_path"]))
            dur = track["_duration"]
            total_frames = int(fps * dur)

            # Triangle wave bounce: constant velocity, no zero-speed pauses.
            # x and y are 90° out of phase so the combined path always moves.
            # Formula: tri(t) = 1 - 2*|frac(t) - 0.5|  →  0→1→0 linear bounce.
            period_frames = int(fps * pan_period)
            x_formula = (
                f"(iw-iw/zoom)*(1-2*abs(mod(on/{period_frames},1)-0.5))"
            )
            y_formula = (
                f"(ih-ih/zoom)*(1-2*abs(mod(on/{period_frames}+0.25,1)-0.5))"
            )

            # Escape special chars for FFmpeg drawtext text values
            def _esc(s: str) -> str:
                return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "")

            track_text = _esc(track["track_name"])
            project_text = _esc(youtube_title)

            # Scale source to fill the 16:9 intermediate canvas (any source AR),
            # then centre-crop to the exact intermediate dimensions before zoompan.
            # force_original_aspect_ratio=increase ensures the image always covers
            # the canvas with no black bars, regardless of source aspect ratio.
            inter_h = intermediate_scale * height // width  # e.g. 8000*1080//1920=4500
            filter_complex = (
                f"scale={intermediate_scale}:{inter_h}:force_original_aspect_ratio=increase,"
                f"crop={intermediate_scale}:{inter_h}:(iw-{intermediate_scale})/2:(ih-{inter_h})/2,"
                f"zoompan=z='{zoom_formula}':x='{x_formula}':y='{y_formula}'"
                f":d={total_frames}:s={width}x{height}:fps={fps},"
                f"drawtext=fontfile='{font_path}':text='{project_text}':"
                f"x=50:y=50:fontsize=36:fontcolor=white:alpha=0.5:"
                f"box=1:boxcolor=black@0.4:boxborderw=10,"
                f"drawtext=fontfile='{font_path}':text='NOW PLAYING\\: {track_text}':"
                f"x=50:y=H-120:fontsize=30:fontcolor=white:"
                f"box=1:boxcolor=black@0.6:boxborderw=15"
            )

            chunk_output = Path(tmp_dir) / f"chunk_{i:04d}.mp4"
            temp_video_files.append(chunk_output)

            cmd = build_chunk_command(
                ffmpeg_path=ffmpeg_path,
                img_path=img_path,
                duration=dur,
                filter_complex=filter_complex,
                output_path=chunk_output,
                encoder=encoder,
                crf=crf,
                preset=preset,
                fps=fps,
            )
            chunk_commands.append((track, cmd))

        durations = [t["_duration"] for t in tracklist]
        if transition_duration > 0:
            final_cmd = build_final_xfade_command(
                ffmpeg_path=ffmpeg_path,
                video_files=list(temp_video_files),
                audio_path=audio_file_path,
                output_path=output_path,
                audio_bitrate=audio_bitrate,
                durations=durations,
                transition_duration=transition_duration,
                crf=crf,
                preset=preset,
            )
            concat_file: Path | None = None
        else:
            concat_file = Path(tmp_dir) / "concat_list.txt"
            final_cmd = build_final_command(
                ffmpeg_path=ffmpeg_path,
                concat_file=concat_file,
                audio_path=audio_file_path,
                output_path=output_path,
                audio_bitrate=audio_bitrate,
            )

        if args.print_command:
            for _, cmd in chunk_commands:
                print(subprocess.list2cmdline(cmd))
            print(subprocess.list2cmdline(final_cmd))
            return 0

        wall_start = time.monotonic()
        print(f"YouTube title : {youtube_title}")
        print(f"Output        : {output_path}")
        print(f"Profile       : {set_type.upper()} | Tracks: {len(tracklist)}")
        print(f"Started       : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        for i, (track, cmd) in enumerate(chunk_commands):
            dur = track["_duration"]
            chunk_start = time.monotonic()
            print(f" -> [{i + 1}/{len(tracklist)}] Rendering: {track['track_name']} ({int(dur)}s)")
            try:
                completed = subprocess.run(cmd, check=False, capture_output=True)
            except FileNotFoundError as exc:
                raise SystemExit(
                    f"ffmpeg executable not found: {ffmpeg_path}. "
                    "Pass --ffmpeg-path or set ffmpeg_path in metadata."
                ) from exc
            # Print stderr filtering cosmetic fontconfig warnings (libfontconfig bypasses -loglevel).
            stderr_text = completed.stderr.decode("utf-8", errors="replace")
            for line in stderr_text.splitlines():
                if not line.startswith("Fontconfig"):
                    print(line, file=sys.stderr)
            if completed.returncode != 0:
                raise SystemExit(
                    f"ffmpeg failed on chunk {i} with exit code {completed.returncode}."
                )
            chunk_elapsed = time.monotonic() - chunk_start
            print(f"    Done in {chunk_elapsed:.1f}s (ratio {chunk_elapsed / dur:.2f}x realtime)")

        if concat_file is not None:
            with open(concat_file, "w", encoding="utf-8") as f:
                for file_path in temp_video_files:
                    f.write(f"file '{_escape_concat_path(file_path)}'\n")

        merge_start = time.monotonic()
        if transition_duration > 0:
            print(f"Merging with {transition_duration}s cross dissolve (re-encoding)...")
        else:
            print("Merging scenes and audio (stream copy)...")
        try:
            completed = subprocess.run(final_cmd, check=False)
        except FileNotFoundError as exc:
            raise SystemExit(
                f"ffmpeg executable not found: {ffmpeg_path}. "
                "Pass --ffmpeg-path or set ffmpeg_path in metadata."
            ) from exc
        print(f"Merge done in {time.monotonic() - merge_start:.1f}s")

        total_elapsed = time.monotonic() - wall_start
        mm, ss = divmod(int(total_elapsed), 60)
        print(f"Finished      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total time    : {mm}m {ss}s")

        return completed.returncode

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())