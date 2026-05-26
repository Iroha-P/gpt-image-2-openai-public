from __future__ import annotations

import asyncio
import base64
import json as jsonlib
import os
import shutil
import socket
import sys
import threading
import time
import webbrowser
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from uuid import uuid4

_APP_DIR = Path(__file__).resolve().parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from gpt_image_tool.core import GenerationValidationError, build_openai_request_plan
from gpt_image_tool.openai_client import OpenAIImageClient
from gpt_image_tool.processing import convert_and_resize
from gpt_image_tool.prompt_skills import build_skill_prompt, list_skill_options
from gpt_image_tool.psd_export import PSD_FILENAME, build_psd_split_prompt, create_layered_psd


TOOL_NAME = "GPT Image 2 OpenAI Public"
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
CONFIG_PATH = BASE_DIR / "config.json"
LOCAL_CONFIG_PATH = BASE_DIR / "config.local.json"
OUTPUT_ROOT = BASE_DIR.parent.parent / "output" / "gpt_image_2_openai_public"

_DEFAULT_CFG = {
    "openai_api_key": "",
    "openai_base_url": "https://api.openai.com/v1",
    "model": "gpt-image-2",
    "main_port": 8170,
    "realesrgan_path": "",
    "default_upscale_mode": "native",
}


def load_config() -> dict:
    cfg = dict(_DEFAULT_CFG)
    for path in (CONFIG_PATH, LOCAL_CONFIG_PATH):
        if path.exists():
            try:
                cfg.update(jsonlib.loads(path.read_text(encoding="utf-8-sig")))
            except Exception as exc:
                print(f"[config] failed to read {path.name}: {exc}")
    env_key = os.environ.get("OPENAI_API_KEY", "").strip()
    cfg["_key_source"] = "environment" if env_key else "local"
    if env_key:
        cfg["openai_api_key"] = env_key
    return cfg


def save_config(cfg: dict) -> None:
    local_cfg = dict(cfg)
    local_cfg.pop("_key_source", None)
    if os.environ.get("OPENAI_API_KEY"):
        local_cfg["openai_api_key"] = ""
    LOCAL_CONFIG_PATH.write_text(jsonlib.dumps(local_cfg, ensure_ascii=False, indent=2), encoding="utf-8")


APP_CFG = load_config()
MAIN_PORT = int(APP_CFG["main_port"])


async def _cleanup_stale_running_files() -> None:
    if not OUTPUT_ROOT.exists():
        return
    for meta_path in OUTPUT_ROOT.rglob("_meta.json"):
        try:
            meta = jsonlib.loads(meta_path.read_text(encoding="utf-8"))
            if meta.get("status") == "running":
                meta["status"] = "error"
                meta["error_msg"] = "Service restarted before this run finished."
                meta_path.write_text(jsonlib.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await _cleanup_stale_running_files()
    yield


app = FastAPI(title=TOOL_NAME, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class _TrackedSemaphore(asyncio.Semaphore):
    def __init__(self, value=1):
        super().__init__(value)
        self.active = 0

    async def __aenter__(self):
        await super().__aenter__()
        self.active += 1
        return self

    async def __aexit__(self, *args):
        self.active -= 1
        return await super().__aexit__(*args)


API_GLOBAL_SEM = _TrackedSemaphore(4)
_active_local = 0
_task_progress: dict[str, dict] = {}
_ws_clients: set[WebSocket] = set()


def _progress_key(client_id: str, task_id: str, run_id: str) -> str:
    return f"{client_id}:{task_id}:{run_id}"


def _result_dir(client_id: str, task_id: str, run_id: str) -> Path:
    return OUTPUT_ROOT / client_id / task_id / "results" / run_id


def _safe_path_part(value: object, fallback: str = "item") -> str:
    text = str(value or "").strip()
    chars = []
    for char in text:
        if char.isalnum() or char in {"-", "_"}:
            chars.append(char)
        elif char.isspace() or char in {".", "/"}:
            chars.append("-")
    part = "".join(chars).strip("-_")
    while "--" in part:
        part = part.replace("--", "-")
    return (part or fallback)[:64].strip("-_") or fallback


def _write_readable_output(meta: dict, run_dir: Path) -> Path | None:
    saved_files = [name for name in meta.get("saved_files", []) if name]
    psd_file = meta.get("psd_file")
    output_files = saved_files + ([psd_file] if psd_file else [])
    if meta.get("status") != "done" or not output_files:
        return None
    created = float(meta.get("created_at") or time.time())
    stamp = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(created))
    label = "_".join(
        [
            stamp,
            _safe_path_part(meta.get("mode"), "mode"),
            _safe_path_part(meta.get("size_label"), "size"),
            _safe_path_part(str(meta.get("run_id", ""))[:8], "run"),
        ]
    )
    readable_dir = OUTPUT_ROOT / "_readable_results" / label
    readable_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for filename in output_files:
        src = run_dir / filename
        if src.exists() and src.is_file():
            shutil.copy2(src, readable_dir / filename)
            copied.append(filename)
    if not copied:
        return None
    prompt = meta.get("prompt_original") or meta.get("prompt") or ""
    (readable_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    (readable_dir / "OUTPUT_PATH.txt").write_text(
        "\n".join(
            [
                f"Original result path: {run_dir}",
                f"Readable mirror path: {readable_dir}",
                f"Created at: {stamp}",
                f"Tool: {TOOL_NAME}",
                f"Mode: {meta.get('mode', '')}",
                f"Size: {meta.get('size_label', '')}",
                f"Status: {meta.get('status', '')}",
                f"Files: {', '.join(copied)}",
                "",
                "Prompt:",
                prompt,
            ]
        ),
        encoding="utf-8",
    )
    return readable_dir


async def _cleanup_progress_later(key: str) -> None:
    await asyncio.sleep(300)
    _task_progress.pop(key, None)


async def _broadcast_online() -> None:
    msg = jsonlib.dumps({"type": "online", "count": len(_ws_clients)})
    dead = []
    for ws in _ws_clients:
        try:
            await ws.send_text(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _ws_clients.discard(ws)


@app.websocket("/ws/online")
async def ws_online(websocket: WebSocket):
    await websocket.accept()
    _ws_clients.add(websocket)
    try:
        await _broadcast_online()
        while True:
            await websocket.receive_text()
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        _ws_clients.discard(websocket)
        await asyncio.sleep(0.1)
        await _broadcast_online()


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = TEMPLATES_DIR / "index.html"
    if not html_path.exists():
        raise HTTPException(404, "Template file not found")
    return html_path.read_text(encoding="utf-8")


@app.get("/api/config")
async def get_config():
    cfg = load_config()
    safe = dict(cfg)
    key = safe.get("openai_api_key", "")
    safe["has_openai_api_key"] = bool(key)
    safe["openai_api_key"] = "********" if key else ""
    return safe


@app.post("/api/config")
async def update_config(body: dict):
    cfg = load_config()
    for key in ["openai_api_key", "openai_base_url", "model", "realesrgan_path", "default_upscale_mode"]:
        if key in body:
            cfg[key] = body[key]
    save_config(cfg)
    return {"ok": True, "config": await get_config()}


@app.post("/api/create-task")
async def create_task(client_id: str = Form("")):
    return {"task_id": uuid4().hex, "client_id": client_id or uuid4().hex}


@app.get("/api/prompt-skills")
async def prompt_skills():
    return list_skill_options()


async def _read_uploads(images: list[UploadFile] | None) -> list[str]:
    image_refs: list[str] = []
    for image in (images or [])[:16]:
        raw = await image.read()
        if raw:
            encoded = base64.b64encode(raw).decode("ascii")
            content_type = image.content_type or "image/png"
            image_refs.append(f"data:{content_type};base64,{encoded}")
    return image_refs


@app.post("/api/generate")
async def generate(
    client_id: str = Form(""),
    task_id: str = Form(""),
    mode: str = Form("text"),
    prompt: str = Form(""),
    size_label: str = Form("1k_square"),
    n: int = Form(1),
    quality: str = Form("auto"),
    upscale_mode: str = Form("native"),
    make_psd: bool = Form(False),
    psd_remove_white: bool = Form(True),
    psd_white_tolerance: int = Form(24),
    psd_split_layers: bool = Form(True),
    skill_use_case: str = Form(""),
    skill_style: str = Form(""),
    skill_subject: str = Form(""),
    skill_mode: str = Form("free"),
    images: Optional[list[UploadFile]] = File(None),
):
    client_id = client_id or uuid4().hex
    task_id = task_id or uuid4().hex
    prompt_original = prompt
    prompt_effective = build_skill_prompt(
        prompt,
        use_case=skill_use_case,
        style=skill_style,
        subject=skill_subject,
        mode=skill_mode,
    )
    if make_psd and psd_split_layers:
        prompt_effective = build_psd_split_prompt(prompt_effective, int(n))
    try:
        image_refs = await _read_uploads(images)
        build_openai_request_plan(
            mode=mode,
            prompt=prompt_effective,
            image_refs=image_refs,
            size_label=size_label,
            n=n,
            quality=quality,
            model=load_config().get("model", "gpt-image-2"),
        )
    except GenerationValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    run_id = uuid4().hex
    key = _progress_key(client_id, task_id, run_id)
    _task_progress[key] = {"status": "running", "progress": 0.01, "message": "Task created"}
    asyncio.create_task(
        _run_generation(
            client_id,
            task_id,
            run_id,
            mode,
            prompt_effective,
            image_refs,
            size_label,
            n,
            quality,
            upscale_mode,
            make_psd,
            psd_remove_white,
            psd_white_tolerance,
            psd_split_layers,
            skill_use_case,
            skill_style,
            skill_subject,
            skill_mode,
            prompt_original,
        )
    )
    return {"run_id": run_id}


def _write_meta(path: Path, meta: dict) -> None:
    path.write_text(jsonlib.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


async def _run_generation(
    client_id: str,
    task_id: str,
    run_id: str,
    mode: str,
    prompt: str,
    image_refs: list[str],
    size_label: str,
    n: int,
    quality: str,
    upscale_mode: str,
    make_psd: bool,
    psd_remove_white: bool,
    psd_white_tolerance: int,
    psd_split_layers: bool,
    skill_use_case: str,
    skill_style: str,
    skill_subject: str,
    skill_mode: str,
    prompt_original: str | None,
):
    global _active_local
    key = _progress_key(client_id, task_id, run_id)
    run_dir = _result_dir(client_id, task_id, run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    created_at = time.time()
    cfg = load_config()
    meta = {
        "client_id": client_id,
        "task_id": task_id,
        "run_id": run_id,
        "created_at": created_at,
        "status": "running",
        "mode": mode,
        "prompt": prompt,
        "prompt_original": prompt if prompt_original is None else prompt_original,
        "prompt_effective": prompt,
        "prompt_skill": {
            "use_case": skill_use_case,
            "style": skill_style,
            "subject": skill_subject,
            "mode": skill_mode,
        },
        "size_label": size_label,
        "quality": quality,
        "provider": "openai",
        "model": cfg.get("model", "gpt-image-2"),
        "saved_files": [],
        "make_psd": bool(make_psd),
        "psd_split_layers": bool(psd_split_layers),
    }
    _write_meta(run_dir / "_meta.json", meta)
    _active_local += 1
    try:
        api_key = cfg.get("openai_api_key", "")
        if not api_key:
            raise RuntimeError("Missing OpenAI API key. Set OPENAI_API_KEY or enter it in Settings.")
        plan = build_openai_request_plan(
            mode=mode,
            prompt=prompt,
            image_refs=image_refs,
            size_label=size_label,
            n=n,
            quality=quality,
            model=cfg.get("model", "gpt-image-2"),
        )
        meta["api_endpoint"] = plan.endpoint
        meta["api_size"] = plan.request_json["size"]
        meta["source_size"] = plan.source_size
        meta["export_size"] = plan.export_size
        meta["size_kind"] = plan.size_kind
        _task_progress[key] = {"status": "running", "progress": 0.15, "message": "Submitting to OpenAI"}
        async with API_GLOBAL_SEM:
            client = OpenAIImageClient(api_key=api_key, base_url=cfg.get("openai_base_url", "https://api.openai.com/v1"))
            images = await client.run(plan)
        if not images:
            raise RuntimeError("OpenAI returned no images")
        _task_progress[key] = {"status": "running", "progress": 0.75, "message": "Saving images"}
        saved_files = []
        postprocess = []
        for idx, image in enumerate(images, start=1):
            raw_path = run_dir / f"_raw_{idx:03d}.png"
            out_name = f"R_{idx:03d}.png"
            out_path = run_dir / out_name
            raw_path.write_bytes(image.content)
            pp_meta = convert_and_resize(
                raw_path,
                out_path,
                export_size=plan.export_size,
                mode=upscale_mode if plan.requires_upscale else "native",
                realesrgan_path=cfg.get("realesrgan_path", ""),
            )
            try:
                raw_path.unlink()
            except Exception:
                pass
            saved_files.append(out_name)
            postprocess.append(pp_meta)
        psd_meta = None
        psd_error = ""
        if make_psd and saved_files:
            try:
                psd_meta = create_layered_psd(
                    [run_dir / filename for filename in saved_files],
                    run_dir / PSD_FILENAME,
                    remove_white_background=psd_remove_white,
                    white_tolerance=psd_white_tolerance,
                )
            except Exception as exc:
                psd_error = str(exc)
        meta.update({"status": "done", "saved_files": saved_files, "postprocess": postprocess})
        if psd_meta:
            meta["psd"] = psd_meta
            meta["psd_file"] = psd_meta["psd_file"]
        if psd_error:
            meta["psd_error"] = psd_error
        readable_dir = _write_readable_output(meta, run_dir)
        if readable_dir:
            meta["readable_output_dir"] = str(readable_dir)
        done_progress = {"status": "done", "progress": 1, "saved_files": saved_files}
        if psd_meta:
            done_progress["psd_file"] = psd_meta["psd_file"]
        if psd_error:
            done_progress["psd_error"] = psd_error
        if readable_dir:
            done_progress["readable_output_dir"] = str(readable_dir)
        _task_progress[key] = done_progress
    except Exception as exc:
        meta["status"] = "error"
        meta["error_msg"] = str(exc)
        _task_progress[key] = {"status": "error", "progress": 1, "error_msg": str(exc)}
    finally:
        _active_local = max(0, _active_local - 1)
        _write_meta(run_dir / "_meta.json", meta)
        asyncio.create_task(_cleanup_progress_later(key))


@app.get("/api/task-progress/{client_id}/{task_id}/{run_id}")
async def task_progress_api(client_id: str, task_id: str, run_id: str):
    item = _task_progress.get(_progress_key(client_id, task_id, run_id))
    if not item:
        raise HTTPException(404, "Task not found or expired")
    return item


@app.get("/api/active-tasks")
async def active_tasks():
    return {"local": _active_local, "openai": API_GLOBAL_SEM.active}


@app.get("/api/result-image/{client_id}/{task_id}/{run_id}/{filename}")
async def result_image(client_id: str, task_id: str, run_id: str, filename: str):
    path = _result_dir(client_id, task_id, run_id) / filename
    if path.name != filename or not path.exists():
        raise HTTPException(404, "Result file not found")
    return FileResponse(path)


@app.get("/api/result-psd/{client_id}/{task_id}/{run_id}")
async def result_psd(client_id: str, task_id: str, run_id: str):
    path = _result_dir(client_id, task_id, run_id) / PSD_FILENAME
    if not path.exists():
        raise HTTPException(404, "PSD result file not found")
    return FileResponse(path, media_type="image/vnd.adobe.photoshop", filename=PSD_FILENAME)


@app.get("/api/history")
async def history_list(client_id: str = ""):
    root = OUTPUT_ROOT / client_id if client_id else OUTPUT_ROOT
    items = []
    if root.exists():
        for meta_path in root.rglob("_meta.json"):
            try:
                items.append(jsonlib.loads(meta_path.read_text(encoding="utf-8")))
            except Exception:
                pass
    items.sort(key=lambda item: item.get("created_at", 0), reverse=True)
    return items[:100]


@app.delete("/api/clear-output")
async def clear_output():
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    _task_progress.clear()
    return {"ok": True}


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    def _get_local_ip() -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "unknown"

    def open_browser():
        if os.environ.get("NO_BROWSER"):
            return
        time.sleep(2)
        webbrowser.open(f"http://localhost:{MAIN_PORT}")

    threading.Thread(target=open_browser, daemon=True).start()
    print()
    print("=" * 60)
    print(f"  {TOOL_NAME} starting")
    print(f"  Local: http://localhost:{MAIN_PORT}")
    print(f"  LAN:   http://{_get_local_ip()}:{MAIN_PORT}")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=MAIN_PORT)
