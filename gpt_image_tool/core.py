from __future__ import annotations

from dataclasses import dataclass
from typing import Any


DEFAULT_MODEL = "gpt-image-2"


class GenerationValidationError(ValueError):
    pass


@dataclass(frozen=True)
class SizeSpec:
    label: str
    api_size: str
    source_size: tuple[int, int] | None
    export_size: tuple[int, int] | None
    requires_upscale: bool
    size_kind: str


@dataclass(frozen=True)
class OpenAIRequestPlan:
    endpoint: str
    model: str
    request_json: dict[str, Any]
    image_refs: list[str]
    source_size: tuple[int, int] | None
    export_size: tuple[int, int] | None
    requires_upscale: bool
    size_kind: str


SIZE_PRESETS: dict[str, SizeSpec] = {
    "1k_square": SizeSpec("1k_square", "1024x1024", (1024, 1024), (1024, 1024), False, "native"),
    "1k_portrait": SizeSpec("1k_portrait", "1024x1536", (1024, 1536), (1024, 1536), False, "native"),
    "1k_landscape": SizeSpec("1k_landscape", "1536x1024", (1536, 1024), (1536, 1024), False, "native"),
    "2k_square": SizeSpec("2k_square", "2048x2048", (2048, 2048), (2048, 2048), False, "native"),
    "2k_portrait": SizeSpec("2k_portrait", "2048x3072", (2048, 3072), (2048, 3072), False, "native"),
    "2k_landscape": SizeSpec("2k_landscape", "3072x2048", (3072, 2048), (3072, 2048), False, "native"),
    "4k_square": SizeSpec("4k_square", "2048x2048", (2048, 2048), (4096, 4096), True, "upscaled_export"),
    "4k_portrait": SizeSpec("4k_portrait", "2160x3840", (2160, 3840), (2160, 3840), False, "native"),
    "4k_landscape": SizeSpec("4k_landscape", "3840x2160", (3840, 2160), (3840, 2160), False, "native"),
    "8k_square": SizeSpec("8k_square", "2048x2048", (2048, 2048), (8192, 8192), True, "upscaled_export"),
    "8k_portrait": SizeSpec("8k_portrait", "2160x3840", (2160, 3840), (4320, 7680), True, "upscaled_export"),
    "8k_landscape": SizeSpec("8k_landscape", "3840x2160", (3840, 2160), (7680, 4320), True, "upscaled_export"),
    "auto": SizeSpec("auto", "auto", None, None, False, "native"),
}


def resolve_size(size_label: str) -> SizeSpec:
    try:
        return SIZE_PRESETS[size_label]
    except KeyError as exc:
        raise GenerationValidationError(f"Unsupported size preset: {size_label}") from exc


def normalize_mode(mode: str) -> str:
    if mode not in {"text", "image", "image_text"}:
        raise GenerationValidationError(f"Unsupported generation mode: {mode}")
    return mode


def _normalize_quality(quality: str) -> str:
    if quality not in {"low", "medium", "high", "auto"}:
        raise GenerationValidationError("Quality must be low, medium, high, or auto")
    return quality


def build_openai_request_plan(
    *,
    mode: str,
    prompt: str,
    image_refs: list[str],
    size_label: str,
    n: int,
    quality: str,
    model: str = DEFAULT_MODEL,
) -> OpenAIRequestPlan:
    mode = normalize_mode(mode)
    quality = _normalize_quality(quality)
    prompt = (prompt or "").strip()
    image_refs = [ref for ref in image_refs if ref]

    if mode == "text" and not prompt:
        raise GenerationValidationError("Please enter a prompt")
    if mode in {"image", "image_text"} and not image_refs:
        raise GenerationValidationError("Image modes require at least one reference image")
    if mode == "image" and not prompt:
        prompt = "Create a high-quality variation based on the reference image while preserving the main subject."
    if not 1 <= int(n) <= 4:
        raise GenerationValidationError("Image count must be between 1 and 4")

    spec = resolve_size(size_label)
    request_json: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "size": spec.api_size,
        "n": int(n),
        "quality": quality,
    }
    endpoint = "/images/generations" if mode == "text" else "/images/edits"

    return OpenAIRequestPlan(
        endpoint=endpoint,
        model=model,
        request_json=request_json,
        image_refs=image_refs,
        source_size=spec.source_size,
        export_size=spec.export_size,
        requires_upscale=spec.requires_upscale,
        size_kind=spec.size_kind,
    )

