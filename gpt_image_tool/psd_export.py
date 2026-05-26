from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image


PSD_FILENAME = "result_layers.psd"


def _normalize_tolerance(tolerance: int) -> int:
    return max(0, min(int(tolerance), 80))


def white_to_alpha(image: Image.Image, tolerance: int = 24) -> Image.Image:
    tolerance = _normalize_tolerance(tolerance)
    rgba = image.convert("RGBA")
    limit = 255 - tolerance
    width, height = rgba.size
    pixels = rgba.load()
    queue: deque[tuple[int, int]] = deque()
    visited: set[tuple[int, int]] = set()

    def is_background_candidate(x: int, y: int) -> bool:
        r, g, b, alpha = pixels[x, y]
        return alpha > 0 and r >= limit and g >= limit and b >= limit

    def add_if_white(x: int, y: int) -> None:
        if (x, y) not in visited and is_background_candidate(x, y):
            visited.add((x, y))
            queue.append((x, y))

    for x in range(width):
        add_if_white(x, 0)
        add_if_white(x, height - 1)
    for y in range(height):
        add_if_white(0, y)
        add_if_white(width - 1, y)

    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < width and 0 <= ny < height:
                add_if_white(nx, ny)

    for x, y in visited:
        r, g, b, _alpha = pixels[x, y]
        pixels[x, y] = (r, g, b, 0)
    return rgba


def build_psd_split_prompt(user_prompt: str, layer_count: int) -> str:
    count = max(1, int(layer_count))
    base = (user_prompt or "").strip() or "Create a complete finished composition."
    return (
        f"{base}\n\n"
        "PSD layer split requirements:\n"
        f"Split the final composition into {count} same-size images. Each image should keep one major element or element group.\n"
        "Every split image must use the exact same canvas size, coordinates, scale, and relative element positions. Do not re-layout elements.\n"
        "Keep all non-element areas pure white, with no texture, shadow, gradient, or checkerboard pattern.\n"
        "The app will remove edge-connected white background and stack all layers at top-left alignment in a PSD file."
    )


def _canvas_size(images: list[Image.Image]) -> tuple[int, int]:
    return (max((image.width for image in images), default=1), max((image.height for image in images), default=1))


def create_layered_psd(
    image_paths: list[str | Path],
    output_path: str | Path,
    *,
    remove_white_background: bool,
    white_tolerance: int,
) -> dict:
    if not image_paths:
        raise ValueError("PSD export requires at least one image")
    try:
        from psd_tools import PSDImage
        from psd_tools.constants import Compression
    except ImportError as exc:
        raise RuntimeError("psd-tools is required for PSD export") from exc

    tolerance = _normalize_tolerance(white_tolerance)
    paths = [Path(path) for path in image_paths]
    images: list[Image.Image] = []
    try:
        for path in paths:
            image = Image.open(path).convert("RGBA")
            images.append(white_to_alpha(image, tolerance) if remove_white_background else image.copy())

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        psd = PSDImage.new("RGB", _canvas_size(images), color=0)
        psd.background_color = None
        for path, image in zip(paths, images):
            psd.create_pixel_layer(image, name=path.stem, top=0, left=0, compression=Compression.RLE)
        psd.save(output)
    finally:
        for image in images:
            image.close()

    return {
        "psd_file": Path(output_path).name,
        "layer_count": len(paths),
        "remove_white_background": bool(remove_white_background),
        "white_tolerance": tolerance,
    }

