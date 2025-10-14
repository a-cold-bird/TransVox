# TransVox

> AI-Powered Video Translation with Voice Cloning | AI 视频翻译与语音克隆

English | [简体中文](./README.md)

TransVox is a powerful AI-driven video translation and dubbing tool that automatically translates videos to target languages while preserving the original speaker's voice characteristics. Built on advanced open-source AI models including WhisperX, GPT-SoVITS, and IndexTTS, it provides a complete automated pipeline from video to dubbed output.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/)
[![GitHub stars](https://img.shields.io/github/stars/a-cold-bird/TransVox?style=social)](https://github.com/a-cold-bird/TransVox)

## Core Features

- **Fully Automated Pipeline** - One-click processing from video to dubbed output
- **AI Voice Cloning** - Zero-Shot TTS preserves original speaker's voice characteristics
- **Multilingual Support** - Supports Chinese, English, Japanese, Korean translation
- **Speaker Diarization** - Automatically identifies and labels different speakers
- **Vocal Separation** - High-quality separation of vocals and background music
- **Smart Subtitles** - AI-powered intelligent line breaking, bilingual subtitle support
- **GPU Acceleration** - CUDA 12.8 support for optimal GPU performance
- **Flexible Configuration** - Multiple TTS engines, transcription engines, custom models
- **Configuration Management** - Save and manage user preference settings
- **Modern Web Interface** - Next.js + TypeScript, dark mode, responsive design
- **Professional Toolbox** - Subtitle slicing, audio separation, TTS generation tools

## Table of Contents

- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Configuration Management](#configuration-management)
- [Testing](#testing)
- [Documentation](#documentation)
- [Acknowledgments](#acknowledgments)
- [License](#license)

## Requirements

- **GPU:** NVIDIA GPU (recommended: 2080Ti or higher, 11GB+ VRAM)
- **Python:** 3.10 (recommended)
- **CUDA:** 12.8 (matching PyTorch version)
- **FFmpeg:** Installed and available in PATH

---

## Quick Start

### 1. Install Python Dependencies

**Windows:**

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip

# Install PyTorch (CUDA 12.8)
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu128

# Install project dependencies
pip install -r requirements.txt

# Install IndexTTS
pip install -e tools/index-tts

# Download NLTK data
python Scripts/download_nltk_data.py

# Install ffmpeg (if not installed)
# scoop install ffmpeg   or   choco install ffmpeg
```

**Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install PyTorch
pip3 install torch torchvision

# Install project dependencies
pip install -r requirements.txt

# Install IndexTTS
pip install -e tools/index-tts

# Download NLTK data
python Scripts/download_nltk_data.py

# Install ffmpeg (if not installed)
sudo apt-get update && sudo apt-get install -y ffmpeg
```

### 2. Download Required Models

Run the automatic download script:

```bash
python Scripts/download_models.py
```

The script will automatically download:
- MSST-WebUI vocal separation models
- GPT-SoVITS pretrained models
- IndexTTS-2 pretrained models

> 💡 **For users in China:** Add `HF_ENDPOINT=https://hf-mirror.com` to `.env` for faster downloads

<details>
<summary>Manual Download (Optional, click to expand)</summary>

**MSST-WebUI Models:**
- [model_mel_band_roformer_karaoke_aufr33_viperx_sdr_10.1956.ckpt](https://hf-mirror.com/Sucial/MSST-WebUI/resolve/main/All_Models/vocal_models/model_mel_band_roformer_karaoke_aufr33_viperx_sdr_10.1956.ckpt)
  → `tools/MSST-WebUI/pretrain/vocal_models/`
- [big_beta5e.ckpt](https://hf-mirror.com/Sucial/MSST-WebUI/resolve/main/All_Models/vocal_models/big_beta5e.ckpt)
  → `tools/MSST-WebUI/pretrain/vocal_models/`
- [dereverb_mel_band_roformer_less_aggressive_anvuew_sdr_18.8050.ckpt](https://hf-mirror.com/Sucial/MSST-WebUI/resolve/main/All_Models/single_stem_models/dereverb_mel_band_roformer_less_aggressive_anvuew_sdr_18.8050.ckpt)
  → `tools/MSST-WebUI/pretrain/single_stem_models/`

**GPT-SoVITS Models:** → `tools/GPT-SoVITS/GPT_SoVITS/`
```bash
huggingface-cli download lj1995/GPT-SoVITS --local-dir tools/GPT-SoVITS/GPT_SoVITS
```

**IndexTTS Models:** → `tools/index-tts/checkpoints/`
```bash
huggingface-cli download IndexTeam/IndexTTS-2 --local-dir tools/index-tts/checkpoints
```

</details>

### 3. Configure API Keys

Copy `.env_template` to `.env`:

```bash
cp .env_template .env
```

Edit the `.env` file and add the following configuration:

```bash
# Gemini API Key (for subtitle translation)
GEMINI_API_KEY=your_gemini_api_key

# Hugging Face Token (for speaker diarization)
HUGGINGFACE_TOKEN=your_huggingface_token

# Optional: For users in China
HF_ENDPOINT=https://hf-mirror.com
```

**How to Get API Keys:**

1. **Gemini API Key:** Visit [Google AI Studio](https://aistudio.google.com/) to create
2. **Hugging Face Token:** Visit [Hugging Face](https://huggingface.co/) Settings → Access Tokens to create

### 4. Verify Installation

Run the environment check script:

```bash
python Scripts/check_environment.py
```

If all checks pass, installation is successful.

## Usage

TransVox provides two usage methods: CLI command-line tools and Web interface.

### Method 1: CLI Command-Line Tools (Recommended)

#### Fully Automated Pipeline

One-click processing from video to dubbed output:

```bash
# English video to Chinese
python full_auto_pipeline.py input/EN_test.mp4 --target_lang zh

# Chinese video to English
python full_auto_pipeline.py input/ZH_test.mp4 --target_lang en

# Use GPT-SoVITS (supports CN/EN/JA/KO)
python full_auto_pipeline.py input/video.mp4 --target_lang ja --tts_engine gptsovits

# Auto-embed bilingual subtitles
python full_auto_pipeline.py input/video.mp4 --target_lang zh --embed-subtitle --subtitle-bilingual
```

#### Step-by-Step Execution

For more granular control (e.g., manual subtitle editing), execute step by step:

```bash
# Step 1: Preprocessing and transcription
python stepA_prepare_and_blank_srt.py input/your_video.mp4 -e whisperx -l auto

# Step 2: Translate subtitles (or use online tools)
python Scripts/step4_translate_srt.py output/<stem>/<stem>.srt --target_lang zh --whole_file

# Step 3: Speech synthesis
python stepB_index_pipeline.py <stem>  # IndexTTS (CN/EN)
# or
python stepB_gptsovits_pipeline.py <stem> --mode local --text_lang zh --prompt_lang en  # GPT-SoVITS (CN/EN/JA/KO)

# Step 4: Embed subtitles (optional)
python stepC_embed_subtitles.py <stem>
```

For detailed usage instructions, see [CLI Usage Guide](./docs/cli-usage.md).

### Method 2: Web Interface

#### Install Frontend Dependencies

```bash
cd web
npm install
```

#### Start Services

**Using one-click startup scripts (Recommended):**

```bash
# Windows
.\start.bat

# Linux
chmod +x start.sh  # Add execute permission on first run
./start.sh
```

The startup script will automatically:
- Check Python and Node.js environment
- Check virtual environment and dependencies
- Check port availability
- Start both backend and frontend services
- Display access URLs and log locations

**Stop Services:**

```bash
# Windows
.\stop.bat

# Linux
chmod +x stop.sh  # Add execute permission on first run
./stop.sh
```

**Or press Ctrl+C to stop (Linux)**

**Or start manually:**

```bash
# Terminal 1: Start backend
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start frontend
cd web
npm run dev
```

**Access services:**
- **Frontend Interface:** http://localhost:3000
- **Online Documentation:** http://localhost:3000/docs (Bilingual docs with interactive navigation)
- **Backend API Docs:** http://localhost:8000/docs

For detailed instructions, see [Getting Started Guide](./docs/getting-started.md).

## Configuration Management

TransVox supports saving user preference settings. The configuration file is located at `transvox_config.json` in the project root directory.

### Configuration File Example

On first run, the system will automatically create the configuration file. You can also manually create or edit it:

```json
{
  "api": {
    "gemini_api_key": "",
    "gemini_base_url": "https://generativelanguage.googleapis.com/v1beta",
    "openai_api_key": "",
    "openai_base_url": "https://api.openai.com/v1"
  },
  "translation": {
    "api_type": "gemini",
    "model": "gemini-2.5-flash",
    "source_lang": "auto",
    "target_lang": "zh"
  },
  "tts": {
    "engine": "indextts"
  },
  "output": {
    "save_srt": true
  },
  "advanced": {
    "enable_diarization": true,
    "enable_separation": true
  }
}
```

### Configuration Options

- **api**: API keys and base URL configuration
- **translation**: Translation engine selection (gemini/openai) and language settings
- **tts**: TTS engine selection (indextts/gptsovits)
- **output**: Output options
- **advanced**: Advanced feature toggles

For detailed configuration instructions, see [Configuration Guide](./docs/CONFIG_GUIDE.md).

## Testing

Run the system test script to verify installation and functionality:

```bash
python Scripts/test_system.py
```

The test script checks:
- Python environment and dependencies
- Configuration system
- API server endpoints
- Frontend compilation
- Core module imports

## Documentation

### Online Documentation (Recommended)

After starting the Web interface, visit **http://localhost:3000/docs** for complete interactive documentation with:

- Chinese/English language toggle
- Sidebar navigation
- Real-time search
- Dark theme
- Code highlighting

### Documentation Index

**Getting Started:**
- [Introduction](./docs/getting-started.md) - TransVox overview and core features
- [Requirements](./docs/getting-started.md#requirements) - Hardware and software requirements
- [Installation](./docs/getting-started.md#installation) - Detailed installation steps
- [API Configuration](./docs/getting-started.md#api-configuration) - Gemini and HuggingFace Token setup

**Usage Guide:**
- [CLI Usage Guide](./docs/cli-usage.md) - Complete command-line tool documentation
- [Auto Pipeline](./docs/cli-usage.md#auto-pipeline) - One-click complete workflow
- [Step-by-Step](./docs/cli-usage.md#step-by-step) - Granular control of each step

**Configuration:**
- [Configuration Guide](./docs/CONFIG_GUIDE.md) - User configuration and translation engine settings
- [TTS Engines](./docs/CONFIG_GUIDE.md#tts-engines) - IndexTTS and GPT-SoVITS configuration
- [Translation Engines](./docs/CONFIG_GUIDE.md#translation) - Gemini and OpenAI configuration

## Acknowledgments

This project is built upon and integrates the following open-source projects:

- Whisper subtitle tools: [`JimLiu/whisper-subtitles`](https://github.com/JimLiu/whisper-subtitles)
- Vocal separation toolkit: [`SUC-DriverOld/MSST-WebUI`](https://github.com/SUC-DriverOld/MSST-WebUI)
- Multilingual TTS (GPT-SoVITS): [`RVC-Boss/GPT-SoVITS`](https://github.com/RVC-Boss/GPT-SoVITS)
- IndexTTS engine: [`index-tts/index-tts`](https://github.com/index-tts/index-tts)

Special thanks to the [pyannote](https://huggingface.co/pyannote) community on Hugging Face for their contributions.

## License

This project is open-sourced under the MIT License. See [LICENSE](LICENSE) for details.

## Contributing

Welcome to contribute to TransVox development:

- **Report Issues:** [GitHub Issues](https://github.com/a-cold-bird/TransVox/issues)
- **Feature Requests:** [GitHub Discussions](https://github.com/a-cold-bird/TransVox/discussions)
- **Submit Code:** Fork the project and submit a Pull Request

If this project helps you, please give it a Star!

---

**Made by TransVox Team**
