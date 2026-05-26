<div align="center">

# GPT Image 2 Studio

### A local image-generation workbench for the official OpenAI Images API

[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](#requirements)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776ab.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/built%20with-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Official OpenAI endpoint by default. No third-party provider config. No bundled API key.**

[Homepage](https://iroha-p.github.io/gpt-image-2-openai-public/) | [Download Source](https://github.com/Iroha-P/gpt-image-2-openai-public/archive/refs/heads/main.zip) | [OpenAI Images API](https://platform.openai.com/docs/guides/images)

</div>

## Why GPT Image 2 Studio?

Most image-generation demos are either a thin API form or a heavy creative suite. **GPT Image 2 Studio** sits in the useful middle: a local web console that gives you prompt skills, reference-image workflows, export-size planning, PSD helpers, and clean output history while still calling the official OpenAI image API directly.

- **Official OpenAI API** - uses `https://api.openai.com/v1` by default and supports `OPENAI_API_KEY`
- **Public-safe configuration** - the tracked `config.json` keeps `openai_api_key` blank, while local secrets live in ignored `config.local.json`
- **Large image-generation skill library** - built-in prompt skills cover use cases, styles, and subject types for thousands of combinations
- **Text, image, and mixed workflows** - text-to-image, image-to-image, and image-plus-text generation
- **Production export helpers** - 1K to 8K presets, native/upscaled export labels, readable result mirrors, and optional PSD layers

## Screenshots

| Studio Console | Settings |
| :------------: | :------: |
| ![GPT Image 2 Studio console](docs/screenshot-studio.png) | ![GPT Image 2 Studio settings](docs/screenshot-settings.png) |

| Mobile Layout |
| :-----------: |
| ![GPT Image 2 Studio mobile layout](docs/screenshot-mobile.png) |

## Image Generation Skills

This public version keeps the advanced prompt-skill workflow from the internal Skill edition, but routes generation through the official OpenAI API.

The built-in skill system combines:

- **10 use-case skills**: avatar, social post, infographic, YouTube thumbnail, storyboard, product marketing, e-commerce main image, game asset, poster, app/web design
- **16 visual style skills**: photography, cinematic still, anime/manga, illustration, line art, comic, 3D render, chibi, isometric, pixel art, oil painting, watercolor, Chinese ink, retro, cyberpunk, minimalism
- **15 subject skills**: portrait, model, character, group/couple, product, food/drink, fashion item, vehicle, architecture/interior, landscape, cityscape, diagrams, typography, abstract backgrounds, and more

Together, those presets create thousands of structured generation directions. You can use them lightly, generate a structured prompt, or hit random inspiration when you need a fast creative starting point.

## Features

### Official OpenAI Generation

- Text-to-image through `/images/generations`
- Image editing through `/images/edits`
- Configurable model name, defaulting to `gpt-image-2`
- API key from environment, local config, or quick in-app entry

### Prompt Skill Console

- Free, light enhancement, and structured prompt modes
- Use-case, style, and subject selectors
- Random inspiration button
- Apply-to-prompt workflow for editable generated prompts
- Bilingual UI labels in English and Chinese

### Export And Post-Processing

- Size presets from 1K to 8K
- Clear native vs upscaled export labeling
- Standard resize or Real-ESRGAN path support
- Local output history
- Readable result mirrors for quick browsing

### PSD Workflow

- Optional `result_layers.psd` export
- Same-canvas layer prompting for Photoshop-friendly stacks
- White-background removal with configurable tolerance

## Quick Start

### 1. Install dependencies

```powershell
pip install -r requirements.txt
```

### 2. Set your OpenAI API key

Recommended:

```powershell
$env:OPENAI_API_KEY="your_api_key_here"
```

You can also paste the key into the quick API-key box in the app. Local credentials are saved to `config.local.json`, which is ignored by Git.

### 3. Start the app

```powershell
.\start.bat
```

Open:

```text
http://127.0.0.1:8170/
```

## Configuration

Tracked public default:

```json
{
  "openai_api_key": "",
  "openai_base_url": "https://api.openai.com/v1",
  "model": "gpt-image-2",
  "main_port": 8170,
  "realesrgan_path": "",
  "default_upscale_mode": "native"
}
```

Credential priority:

1. `OPENAI_API_KEY` environment variable
2. Local `config.local.json`
3. Public default `config.json`

The repository version intentionally contains no real API key and no third-party provider configuration.

## Requirements

- Python 3.11 or newer
- OpenAI API key with image-generation access
- Modern browser
- Optional: Real-ESRGAN executable for AI upscaling

## Project Structure

```text
gpt-image-2-openai-public/
├─ app.py
├─ config.json
├─ config.example.json
├─ gpt_image_tool/
│  ├─ core.py
│  ├─ openai_client.py
│  ├─ prompt_skills.py
│  ├─ processing.py
│  └─ psd_export.py
├─ templates/
│  └─ index.html
├─ docs/
│  ├─ index.html
│  └─ screenshots
└─ README.md
```

## Safety Notes

- Do not commit `config.local.json`
- Do not commit generated outputs
- Keep `config.json` sanitized for public repositories
- Use the official OpenAI base URL unless you intentionally run a compatible endpoint

## License

MIT
