# TransVox

> AI-Powered Video Translation with Voice Cloning | AI 视频翻译与语音克隆

[English](./README_EN.md) | 简体中文

TransVox 是一款强大的 AI 驱动视频翻译配音工具，能够自动将视频翻译为目标语言并生成配音，同时保留原说话人的音色特征。基于 WhisperX、GPT-SoVITS、IndexTTS 等先进的开源 AI 模型构建，提供从视频到配音的完整自动化流程。

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/)
[![GitHub stars](https://img.shields.io/github/stars/a-cold-bird/TransVox?style=social)](https://github.com/a-cold-bird/TransVox)

## 核心特性

- **全自动流程** - 一键完成从视频到配音的全流程处理
- **AI 语音克隆** - 使用 Zero-Shot TTS 保留原说话人音色
- **多语言支持** - 支持中英日韩互译
- **说话人识别** - 自动识别并标注不同说话人
- **人声分离** - 高质量分离人声和背景音
- **智能字幕** - AI 智能分行，双语字幕支持
- **GPU 加速** - 支持 CUDA 12.8，充分利用 GPU 性能
- **灵活配置** - 支持多种 TTS 引擎、转录引擎，可自定义模型
- **配置管理** - 支持保存用户偏好设置
- **现代化 Web 界面** - Next.js + TypeScript，暗色模式，响应式设计
- **专业工具箱** - 字幕切片、音频分离、TTS 生成等独立工具

## 目录

- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [使用方法](#使用方法)
- [配置管理](#配置管理)
- [测试](#测试)
- [项目文档](#项目文档)
- [依赖项目与致谢](#依赖项目与致谢)
- [开源协议](#开源协议)

## 环境要求

- **GPU:** NVIDIA GPU（推荐 2080Ti 及以上，显存 11GB+）
- **Python:** 3.10（推荐）
- **CUDA:** 12.8（与 PyTorch 版本匹配）
- **FFmpeg:** 已安装并在 PATH 中可用
- **Node.js:** 18+ （用于 Web 界面）

## 快速开始

### 1. 安装 Python 依赖

**Windows:**

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip

# 安装 PyTorch (CUDA 12.8)
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu128

# 安装项目依赖
pip install -r requirements.txt

# 安装 IndexTTS
pip install -e tools/index-tts

# 下载 NLTK 数据
python Scripts/download_nltk_data.py
```

**Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# 安装 PyTorch
pip3 install torch torchvision

# 安装项目依赖
pip install -r requirements.txt

# 安装 IndexTTS
pip install -e tools/index-tts

# 下载 NLTK 数据
python Scripts/download_nltk_data.py

# 安装 ffmpeg
sudo apt-get update && sudo apt-get install -y ffmpeg
```

### 2. 下载必需模型

运行自动下载脚本：

```bash
python Scripts/download_models.py
```

脚本会自动下载以下模型：
- MSST-WebUI 人声分离模型
- GPT-SoVITS 预训练模型
- IndexTTS-2 预训练模型

**国内用户加速提示:** 在 `.env` 中添加 `HF_ENDPOINT=https://hf-mirror.com` 使用镜像站

### 3. 配置 API Key

复制 `.env_template` 为 `.env`：

```bash
cp .env_template .env
```

编辑 `.env` 文件，添加以下配置：

```bash
# Gemini API Key (字幕翻译)
GEMINI_API_KEY=your_gemini_api_key

# Hugging Face Token (说话人识别)
HUGGINGFACE_TOKEN=your_huggingface_token

# 可选：国内用户加速
HF_ENDPOINT=https://hf-mirror.com
```

**获取 API Key:**

1. **Gemini API Key:** 访问 [Google AI Studio](https://aistudio.google.com/) 创建
2. **Hugging Face Token:** 访问 [Hugging Face](https://huggingface.co/) Settings → Access Tokens 创建

### 4. 验证安装

运行环境检测脚本：

```bash
python Scripts/check_environment.py
```

如果所有检查都通过，说明安装成功。

## 使用方法

TransVox 提供两种使用方式：CLI 命令行工具和 Web 界面。

### 方式一：CLI 命令行工具

#### 全自动流程

一键完成从视频到配音的全流程：

```bash
# 英文视频翻译为中文
python full_auto_pipeline.py input/EN_test.mp4 --target_lang zh

# 中文视频翻译为英文
python full_auto_pipeline.py input/ZH_test.mp4 --target_lang en

# 使用 GPT-SoVITS (支持中日英韩)
python full_auto_pipeline.py input/video.mp4 --target_lang ja --tts_engine gptsovits

# 自动嵌入双语字幕
python full_auto_pipeline.py input/video.mp4 --target_lang zh --embed-subtitle --subtitle-bilingual
```

#### 分步执行

如需更精细的控制（如手动修改字幕），可分步执行：

```bash
# 步骤 1: 预处理与转录
python stepA_prepare_and_blank_srt.py input/your_video.mp4 -e whisperx -l auto

# 步骤 2: 翻译字幕
python Scripts/step4_translate_srt.py output/<stem>/<stem>.srt --target_lang zh --whole_file

# 步骤 3: 语音合成
python stepB_index_pipeline.py <stem>  # IndexTTS (中英文)
# 或
python stepB_gptsovits_pipeline.py <stem> --mode local --text_lang zh --prompt_lang en  # GPT-SoVITS (中日英韩)

# 步骤 4: 嵌入字幕 (可选)
python stepC_embed_subtitles.py <stem>
```

详细使用说明请参考 [CLI 使用指南](./docs/cli-usage.md)。

### 方式二：Web 界面

#### 安装前端依赖

```bash
cd web
npm install
```

#### 启动服务

**使用一键启动脚本（推荐）:**

```bash
# Windows
.\start.bat

# Linux
chmod +x start.sh  # 首次运行需要添加执行权限
./start.sh
```

启动脚本会自动：
- 检查 Python 和 Node.js 环境
- 检查虚拟环境和依赖
- 检查端口占用
- 同时启动后端和前端服务
- 显示访问地址和日志位置

**停止服务:**

```bash
# Windows
.\stop.bat

# Linux
chmod +x stop.sh  # 首次运行需要添加执行权限
./stop.sh
```

**或按 Ctrl+C 停止（Linux）**

**或手动启动:**

```bash
# 终端 1: 启动后端
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload

# 终端 2: 启动前端
cd web
npm run dev
```

**访问服务:**
- **前端界面:** http://localhost:3000
- **在线文档:** http://localhost:3000/docs (中英文档，交互式导航)
- **后端 API 文档:** http://localhost:8000/docs

详细说明请参考 [快速开始指南](./docs/getting-started.md)。

## 配置管理

TransVox 支持保存用户偏好设置。配置文件位于项目根目录 `transvox_config.json`。

### 配置文件示例

首次运行时，系统会自动创建配置文件。你也可以手动创建或编辑：

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

### 配置说明

- **api**: API 密钥和基础 URL 配置
- **translation**: 翻译引擎选择（gemini/openai）和语言设置
- **tts**: TTS 引擎选择（indextts/gptsovits）
- **output**: 输出选项
- **advanced**: 高级功能开关

详细配置说明请参考 [配置管理指南](./docs/CONFIG_GUIDE.md)。

## 测试

运行系统测试脚本验证安装和功能：

```bash
python Scripts/test_system.py
```

测试脚本会检查：
- Python 环境和依赖
- 配置系统
- API 服务器端点
- 前端编译
- 核心模块导入

## 项目文档

### 在线文档（推荐）

启动 Web 界面后，访问 **http://localhost:3000/docs** 查看完整的交互式文档，支持：

- 中英双语切换
- 侧边栏导航
- 实时搜索
- 暗色主题
- 代码高亮

### 文档目录

**快速开始:**
- [项目简介](./docs/getting-started.md) - TransVox 介绍和核心特性
- [环境要求](./docs/getting-started.md#环境要求) - 硬件和软件需求
- [安装指南](./docs/getting-started.md#安装) - 详细安装步骤
- [API 配置](./docs/getting-started.md#api配置) - Gemini 和 HuggingFace Token 配置

**使用指南:**
- [CLI 使用指南](./docs/cli-usage.md) - 命令行工具完整使用文档
- [自动流程](./docs/cli-usage.md#全自动流程) - 一键处理完整流程
- [分步执行](./docs/cli-usage.md#分步执行) - 精细控制每个步骤

**配置管理:**
- [配置管理指南](./docs/CONFIG_GUIDE.md) - 用户配置和翻译引擎设置
- [TTS 引擎配置](./docs/CONFIG_GUIDE.md#tts引擎) - IndexTTS 和 GPT-SoVITS 配置
- [翻译引擎配置](./docs/CONFIG_GUIDE.md#翻译引擎) - Gemini 和 OpenAI 配置

## 依赖项目与致谢

本项目基于以下开源项目集成与构建，特此致谢：

- Whisper 字幕工具集: [`JimLiu/whisper-subtitles`](https://github.com/JimLiu/whisper-subtitles)
- 人声分离套件: [`SUC-DriverOld/MSST-WebUI`](https://github.com/SUC-DriverOld/MSST-WebUI)
- 多语言 TTS (GPT-SoVITS): [`RVC-Boss/GPT-SoVITS`](https://github.com/RVC-Boss/GPT-SoVITS)
- IndexTTS 引擎: [`index-tts/index-tts`](https://github.com/index-tts/index-tts)

同时感谢 Hugging Face 上 [pyannote](https://huggingface.co/pyannote) 社区模型的贡献。

## 开源协议

本项目采用 MIT 协议开源，详见 [LICENSE](LICENSE) 文件。

## 贡献与支持

欢迎参与 TransVox 的开发：

- **报告问题:** [GitHub Issues](https://github.com/a-cold-bird/TransVox/issues)
- **功能建议:** [GitHub Discussions](https://github.com/a-cold-bird/TransVox/discussions)
- **提交代码:** Fork 项目并提交 Pull Request

如果这个项目对你有帮助，欢迎 Star 支持！

---

**Made by TransVox Team**
