# GPT Image 2 Studio

A local web workbench for GPT Image 2 using the official OpenAI image API.

## Features

- Text-to-image
- Image-to-image
- Image plus text generation
- Bilingual UI: English and Chinese
- Fast API key entry on the main screen
- Prompt-skill presets, random inspiration, and apply-to-prompt enhancement
- 1K to 8K export presets
- Clear labeling for native output vs local upscaled export
- Optional PSD layered export
- Same-canvas PSD layer split prompting
- Local generation history

## Quick Start

### English

1. Install Python 3.11 or newer.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Set your OpenAI API key:

```powershell
$env:OPENAI_API_KEY="your_api_key_here"
```

4. Start the app:

```powershell
.\start.bat
```

5. Open:

```text
http://127.0.0.1:8170/
```

You can also enter the API key in the quick API key box on the main screen or in the Settings panel. The app saves local credentials to `config.local.json`, which is ignored by Git. For public repositories, keep `config.json` blank and use environment variables or `config.local.json` for real credentials.

### 中文

1. 安装 Python 3.11 或更新版本。
2. 安装依赖：

```powershell
pip install -r requirements.txt
```

3. 设置 OpenAI API Key：

```powershell
$env:OPENAI_API_KEY="your_api_key_here"
```

4. 启动工具：

```powershell
.\start.bat
```

5. 打开：

```text
http://127.0.0.1:8170/
```

也可以在主界面的快速 API Key 输入框，或右上角 Settings / 设置 面板里填写 API Key。应用会把本地密钥保存到 Git 已忽略的 `config.local.json`。开源仓库中请保持 `config.json` 为空，不要提交真实密钥。

## Configuration

Default config:

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

When `OPENAI_API_KEY` is set, saving settings will not write that key back into any config file. The tracked `config.json` should stay sanitized.

## Size Notes

Some presets are native API requests. Larger presets are local exports produced from a supported source size and then resized or upscaled locally. The UI marks these as `Upscaled export`.

## PSD Export

Enable `Export PSD layers` to create `result_layers.psd`.

For best layered PSD results, also enable `Prompt same-canvas layers`. This asks the image model to return same-size layer images that can be stacked in Photoshop.

## Prompt Skills

This public version keeps the Skill-version workflow from `002_gpt_image_2_tool_skill`: free mode, light enhancement, structured prompt mode, use-case presets, style presets, subject presets, random inspiration, and apply-to-prompt generation.
