"""Check image quality for all slides defined in a generate_set_video YAML file.

Usage:
    python check_image_quality.py <metadata.yaml>

Requirements:
    pip install pillow pyyaml
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from PIL import Image  # type: ignore
except ImportError:
    raise SystemExit("Requires Pillow. Install with: pip install pillow")

try:
    import yaml  # type: ignore
except ImportError:
    raise SystemExit("Requires PyYAML. Install with: pip install pyyaml")


_RATINGS: list[tuple[float, float, str, str]] = [
    # (min_mp, min_bytes_per_mp, emoji, label)
    (0.0, 0.0,    "🔴", "POOR        — AI upscale strongly recommended"),
    (0.5, 0.0,    "🟠", "LOW         — AI upscale recommended"),
    (2.0, 0.0,    "🟡", "FAIR        — acceptable, AI upscale optional"),
    (4.0, 0.0,    "🟢", "GOOD"),
    (8.0, 0.0,    "✅", "EXCELLENT"),
]

_COMPRESSION_THRESHOLD = 30_000  # bytes-per-MP below which we flag as compressed


def _rate(width: int, height: int, file_bytes: int) -> tuple[str, str]:
    mp = (width * height) / 1_000_000
    bytes_per_mp = file_bytes / mp if mp > 0 else 0

    emoji, label = "🔴", "POOR"
    for min_mp, _, e, l in reversed(_RATINGS):
        if mp >= min_mp:
            emoji, label = e, l
            break

    if bytes_per_mp < _COMPRESSION_THRESHOLD and mp >= 1.0:
        label += " (heavy JPEG compression — AI upscale may help)"

    return emoji, label


def _open_image(path: Path) -> tuple[int, int, int]:
    """Return (width, height, file_bytes) or (-1,-1,-1) on error."""
    if not path.exists():
        return -1, -1, -1
    try:
        with Image.open(path) as img:
            w, h = img.size
        return w, h, path.stat().st_size
    except Exception:
        return -1, -1, -1


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    metadata_path = Path(sys.argv[1])
    if not metadata_path.exists():
        raise SystemExit(f"File not found: {metadata_path}")

    metadata = _load_yaml(metadata_path)
    video = metadata.get("video", {})
    intermediate_scale = int(video.get("intermediate_scale", 8000))
    recommended_min_px = intermediate_scale // 4  # conservative minimum source width

    # ── Collect images ──────────────────────────────────────────────────────
    entries: list[tuple[str, Path | None]] = []

    cover = metadata.get("cover_path")
    if cover:
        entries.append(("cover_path", Path(cover)))

    for track in metadata.get("tracklist") or []:
        if not isinstance(track, dict):
            continue
        name = track.get("track_name", "(unknown)")
        img = track.get("image")
        entries.append((name, Path(img) if img else None))

    # ── Header ───────────────────────────────────────────────────────────────
    print()
    print("╔══ Image Quality Report ════════════════════════════════════════╗")
    print(f"  YAML              : {metadata_path.name}")
    print(f"  intermediate_scale: {intermediate_scale}px")
    print(f"  Recommended min.  : ≥ {recommended_min_px}px wide")
    print("╚════════════════════════════════════════════════════════════════╝")
    print()

    C_TRACK, C_FILE, C_SIZE, C_RES, C_MP = 40, 18, 9, 13, 7
    header = (
        f"{'Track':<{C_TRACK}} "
        f"{'File':<{C_FILE}} "
        f"{'Size':>{C_SIZE}} "
        f"{'Resolution':>{C_RES}} "
        f"{'MP':>{C_MP}}  Rating"
    )
    sep = "─" * len(header)
    print(header)
    print(sep)

    flagged: list[tuple[str, Path, str]] = []

    for label, img_path in entries:
        if img_path is None:
            tag = "(no image → uses cover_path)"
            print(f"  {label[:C_TRACK]:<{C_TRACK}} {tag}")
            continue

        w, h, size = _open_image(img_path)
        fname = img_path.name

        if w == -1:
            status = "FILE NOT FOUND"
            print(f"  {label[:C_TRACK]:<{C_TRACK}} {fname:<{C_FILE}} {'':>{C_SIZE}} {'':>{C_RES}} {'':>{C_MP}}  ❌ {status}")
            flagged.append((label, img_path, "missing"))
            continue

        mp = (w * h) / 1_000_000
        size_str = f"{size // 1024} KB" if size < 1_048_576 else f"{size / 1_048_576:.1f} MB"
        res_str = f"{w}×{h}"
        mp_str = f"{mp:.1f}"
        emoji, rating_label = _rate(w, h, size)

        warn = " ⚠" if w < recommended_min_px else ""
        print(
            f"  {label[:C_TRACK]:<{C_TRACK}} "
            f"{fname:<{C_FILE}} "
            f"{size_str:>{C_SIZE}} "
            f"{res_str:>{C_RES}} "
            f"{mp_str:>{C_MP}}  {emoji} {rating_label}{warn}"
        )

        if "POOR" in rating_label or "LOW" in rating_label or "FAIR" in rating_label or w < recommended_min_px:
            flagged.append((label, img_path, rating_label))

    print(sep)
    print()

    if flagged:
        print(f"  ⚠  {len(flagged)} file(s) flagged for AI upscaling:\n")
        for label, path, reason in flagged:
            print(f"     {path.name:<30}  {reason}")
        print()
        print("  Suggested tool: Upscayl desktop (free, local, GPU-accelerated)")
        print("  Download      : https://github.com/upscayl/upscayl/releases")
        print("  Recommended   : 4× upscale, model 'Real-ESRGAN (General Photo)'")
    else:
        print("  ✅  All images meet quality requirements.")

    print()


if __name__ == "__main__":
    main()
