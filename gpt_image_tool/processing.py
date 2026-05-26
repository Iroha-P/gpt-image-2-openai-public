from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image


def _resize_png(src: Path, dst: Path, export_size: tuple[int, int] | None) -> None:
    with Image.open(src) as image:
        out = image.convert("RGBA")
        if export_size and out.size != export_size:
            out = out.resize(export_size, Image.Resampling.LANCZOS)
        dst.parent.mkdir(parents=True, exist_ok=True)
        out.save(dst, "PNG")


def _run_realesrgan(src: Path, dst: Path, realesrgan_path: str, scale: int) -> tuple[bool, str]:
    exe = Path(realesrgan_path or "")
    if not exe.exists():
        return False, "Real-ESRGAN executable is not configured or does not exist"
    command = [str(exe), "-i", str(src), "-o", str(dst), "-s", str(scale), "-f", "png"]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=900)
    except Exception as exc:
        return False, f"Real-ESRGAN failed: {exc}"
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or str(completed.returncode)
        return False, f"Real-ESRGAN returned an error: {detail}"
    return dst.exists(), "" if dst.exists() else "Real-ESRGAN did not create an output file"


def _scale_for_size(src: Path, export_size: tuple[int, int] | None) -> int:
    if not export_size:
        return 2
    with Image.open(src) as image:
        width, height = image.size
    target_w, target_h = export_size
    ratio = max(target_w / max(width, 1), target_h / max(height, 1))
    if ratio <= 2:
        return 2
    if ratio <= 3:
        return 3
    return 4


def convert_and_resize(
    src: str | Path,
    dst: str | Path,
    *,
    export_size: tuple[int, int] | None,
    mode: str,
    realesrgan_path: str = "",
) -> dict:
    src_path = Path(src)
    dst_path = Path(dst)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {"upscale_mode": mode, "fallback_used": False, "fallback_reason": ""}
    if mode == "native":
        _resize_png(src_path, dst_path, None)
        return metadata
    if mode == "ai":
        temp_out = dst_path.with_name(dst_path.stem + "_ai.png")
        ok, reason = _run_realesrgan(src_path, temp_out, realesrgan_path, _scale_for_size(src_path, export_size))
        if ok:
            _resize_png(temp_out, dst_path, export_size)
            try:
                temp_out.unlink()
            except Exception:
                pass
            return metadata
        metadata["upscale_mode"] = "standard"
        metadata["fallback_used"] = True
        metadata["fallback_reason"] = reason
    _resize_png(src_path, dst_path, export_size)
    return metadata

