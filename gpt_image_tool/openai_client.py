from __future__ import annotations

import base64
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from .core import OpenAIRequestPlan


@dataclass(frozen=True)
class GeneratedImage:
    content: bytes
    filename: str
    media_type: str


def _decode_data_url(value: str) -> tuple[bytes, str, str]:
    if not value.startswith("data:") or ";base64," not in value:
        path = Path(value)
        media_type = mimetypes.guess_type(path.name)[0] or "image/png"
        return path.read_bytes(), path.name, media_type
    header, encoded = value.split(",", 1)
    media_type = header[5:].split(";", 1)[0] or "image/png"
    suffix = mimetypes.guess_extension(media_type) or ".png"
    return base64.b64decode(encoded), f"reference{suffix}", media_type


def _extract_images(data: dict[str, Any]) -> list[GeneratedImage]:
    results: list[GeneratedImage] = []
    for index, item in enumerate(data.get("data") or [], start=1):
        b64 = item.get("b64_json")
        if b64:
            results.append(
                GeneratedImage(
                    content=base64.b64decode(b64),
                    filename=f"openai_{index:03d}.png",
                    media_type="image/png",
                )
            )
    return results


class OpenAIImageClient:
    def __init__(self, *, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    async def generate(self, plan: OpenAIRequestPlan) -> list[GeneratedImage]:
        payload = dict(plan.request_json)
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                f"{self.base_url}{plan.endpoint}",
                headers={**self._headers(), "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            return _extract_images(response.json())

    async def edit(self, plan: OpenAIRequestPlan) -> list[GeneratedImage]:
        data = {key: str(value) for key, value in plan.request_json.items()}
        files = []
        for ref in plan.image_refs:
            raw, filename, media_type = _decode_data_url(ref)
            files.append(("image", (filename, raw, media_type)))
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                f"{self.base_url}{plan.endpoint}",
                headers=self._headers(),
                data=data,
                files=files,
            )
            response.raise_for_status()
            return _extract_images(response.json())

    async def run(self, plan: OpenAIRequestPlan) -> list[GeneratedImage]:
        if plan.endpoint == "/images/edits":
            return await self.edit(plan)
        return await self.generate(plan)
