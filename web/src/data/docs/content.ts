import { DocContent } from '@/types/docs'

export const docsContent: Record<string, DocContent> = {
  'index': {
    en: {
      title: 'Introduction',
      description: 'Welcome to TransVox Documentation',
      content: `
# Welcome to TransVox

TransVox is an AI-powered video translation and voice cloning system that automatically translates videos to target languages while preserving the original speaker's voice characteristics.

## What is TransVox?

TransVox combines cutting-edge AI technologies to provide a complete video dubbing solution:

- **Automatic Speech Recognition** using WhisperX
- **Advanced LLM Translation** powered by Gemini/OpenAI
- **Voice Cloning** with IndexTTS and GPT-SoVITS
- **Intelligent Subtitle Processing** with precise timing

## Core Feature

### Video Dubbing with Voice Preservation
The primary function of TransVox is **automatic video dubbing** - translating video content to different languages while preserving the original speaker's voice characteristics. This creates a seamless viewing experience where the content sounds as if it was originally recorded in the target language.

**How it works:**
1. Extract and analyze the original speaker's voice
2. Transcribe and translate the dialogue
3. Generate speech in the target language using the cloned voice
4. Merge the dubbed audio back into the video

### Key Supporting Features

**Zero-Shot Voice Cloning**
- No training data required
- Preserves tone, pitch, and speaking rhythm
- Maintains emotional expression

**Multi-Language Support**
- Chinese (Simplified)
- English
- Japanese
- Korean

**Full Automation**
- End-to-end processing pipeline
- Automatic speech recognition
- Intelligent subtitle timing
- Seamless audio-video synchronization

## System Requirements

- **GPU**: NVIDIA GPU with CUDA support (GTX 2080Ti or better recommended)
- **RAM**: 16GB minimum, 32GB recommended
- **Storage**: 50GB free space for models and processing
- **OS**: Windows 10/11, Linux (Ubuntu 20.04+), macOS (Intel/Apple Silicon)

## Quick Links

- [Installation Guide](/docs/installation)
- [Quick Start Tutorial](/docs/quick-start)
- [API Reference](/docs/api/rest)
- [GitHub Repository](https://github.com/your-repo/transvox)

## Getting Help

- **Documentation**: Browse our comprehensive guides
- **Issues**: Report bugs on GitHub
- **Community**: Join our Discord server
`,
    },
    zh: {
      title: '简介',
      description: '欢迎使用 TransVox 文档',
      content: `
# 欢迎使用 TransVox

TransVox 是一个 AI 驱动的视频翻译和声音克隆系统，能够自动将视频翻译成目标语言，同时保留原说话人的声音特征。

## 什么是 TransVox？

TransVox 结合了最先进的 AI 技术，提供完整的视频配音解决方案：

- 使用 **WhisperX 自动语音识别**
- **Gemini/OpenAI 先进的 LLM 语言模型翻译**
- 使用 **IndexTTS 和 GPT-SoVITS 进行语音克隆**
- **智能字幕处理**，精确对齐时间轴

## 核心功能

### 视频同声翻译（保留原声）
TransVox 的主要功能是**自动视频配音** - 将视频内容翻译成不同语言，同时保留原说话人的声音特征。这创造了一种无缝的观看体验，让内容听起来就像最初是用目标语言录制的一样。

**工作流程：**
1. 提取并分析原说话人的声音
2. 转录并翻译对话内容
3. 使用克隆的声音生成目标语言的语音
4. 将配音音频合并回视频

### 关键支持功能

**零样本声音克隆**
- 无需训练数据
- 保留音调、音高和说话节奏
- 维持情感表达

**多语言支持**
- 中文（简体）
- 英语
- 日语
- 韩语

**全自动化**
- 端到端处理流水线
- 自动语音识别
- 智能字幕时间轴
- 无缝音视频同步

## 系统要求

- **GPU**: 支持 CUDA 的 NVIDIA GPU（推荐 GTX 2080Ti 或更好）
- **内存**: 最低 16GB，推荐 32GB
- **存储空间**: 50GB 可用空间用于模型和处理
- **操作系统**: Windows 10/11、Linux (Ubuntu 20.04+)、macOS (Intel/Apple Silicon)

## 快速链接

- [安装指南](/docs/installation)
- [快速入门教程](/docs/quick-start)
- [API 参考](/docs/api/rest)
- [GitHub 仓库](https://github.com/your-repo/transvox)

## 获取帮助

- **文档**: 浏览我们的综合指南
- **问题**: 在 GitHub 上报告错误
- **社区**: 加入我们的 Discord 服务器
`,
    },
  },

  'installation': {
    en: {
      title: 'Installation',
      description: 'Install TransVox on your system',
      content: `
# Installation

This guide will help you install TransVox and all its dependencies.

## Prerequisites

Before installing TransVox, ensure your system has:

### Required Software
- **Python 3.10+**: Download from [python.org](https://www.python.org)
- **Node.js 18+**: Download from [nodejs.org](https://nodejs.org)
- **Git**: For cloning the repository
- **FFmpeg**: For video/audio processing
- **NVIDIA GPU** with CUDA 12.8 support

### API Keys
You'll need:
- **Gemini API Key** (or OpenAI API Key) for translation
- **Hugging Face Token** for speaker diarization models

## Installation Steps

### 1. Clone the Repository

\`\`\`bash
git clone https://github.com/your-repo/transvox.git
cd transvox
\`\`\`

### 2. Create Virtual Environment

#### Windows
\`\`\`bash
python -m venv venv
venv\\Scripts\\activate
\`\`\`

#### Linux/Mac
\`\`\`bash
python -m venv venv
source venv/bin/activate
\`\`\`

### 3. Install Python Dependencies

\`\`\`bash
# Upgrade pip
pip install --upgrade pip

# Install PyTorch with CUDA support
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu128

# Install other dependencies
pip install -r requirements.txt

# Install IndexTTS
pip install -e tools/index-tts
\`\`\`

### 4. Download AI Models

\`\`\`bash
python download_models.py
\`\`\`

This will download:
- WhisperX models
- Pyannote speaker diarization models
- IndexTTS checkpoint
- GPT-SoVITS models

### 5. Install Frontend Dependencies

\`\`\`bash
cd web
npm install
cd ..
\`\`\`

### 6. Configure Environment

Create a \`.env\` file in the root directory:

\`\`\`env
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
HUGGINGFACE_TOKEN=your_hugging_face_token_here

# Optional: For users in China
HF_ENDPOINT=https://hf-mirror.com
\`\`\`

### 7. Verify Installation

\`\`\`bash
python check_environment.py
\`\`\`

Expected output:
\`\`\`
✓ Python version: 3.10.x
✓ PyTorch installed with CUDA support
✓ FFmpeg found
✓ All required packages installed
✓ Models downloaded successfully
\`\`\`

## Troubleshooting

### CUDA Not Detected
If PyTorch doesn't detect your GPU:
1. Verify NVIDIA drivers are installed
2. Check CUDA toolkit version matches PyTorch
3. Reinstall PyTorch with correct CUDA version

### Model Download Fails
- Use \`HF_ENDPOINT=https://hf-mirror.com\` for Chinese users
- Check your internet connection
- Manually download models if needed

### FFmpeg Not Found
- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org) and add to PATH
- **Linux**: \`sudo apt install ffmpeg\`
- **Mac**: \`brew install ffmpeg\`

## Next Steps

- [Quick Start Guide](/docs/quick-start)
- [Configuration](/docs/api/configuration)
`,
    },
    zh: {
      title: '安装',
      description: '在您的系统上安装 TransVox',
      content: `
# 安装

本指南将帮助您安装 TransVox 及其所有依赖项。

## 前置条件

在安装 TransVox 之前，确保您的系统具备：

### 必需软件
- **Python 3.10+**: 从 [python.org](https://www.python.org) 下载
- **Node.js 18+**: 从 [nodejs.org](https://nodejs.org) 下载
- **Git**: 用于克隆仓库
- **FFmpeg**: 用于视频/音频处理
- 支持 CUDA 12.8 的 **NVIDIA GPU**

### API 密钥
您需要：
- **Gemini API 密钥**（或 OpenAI API 密钥）用于翻译
- **Hugging Face Token** 用于说话人识别模型

## 安装步骤

### 1. 克隆仓库

\`\`\`bash
git clone https://github.com/your-repo/transvox.git
cd transvox
\`\`\`

### 2. 创建虚拟环境

#### Windows
\`\`\`bash
python -m venv venv
venv\\Scripts\\activate
\`\`\`

#### Linux/Mac
\`\`\`bash
python -m venv venv
source venv/bin/activate
\`\`\`

### 3. 安装 Python 依赖

\`\`\`bash
# 升级 pip
pip install --upgrade pip

# 安装支持 CUDA 的 PyTorch
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu128

# 安装其他依赖
pip install -r requirements.txt

# 安装 IndexTTS
pip install -e tools/index-tts
\`\`\`

### 4. 下载 AI 模型

\`\`\`bash
python download_models.py
\`\`\`

这将下载：
- WhisperX 模型
- Pyannote 说话人识别模型
- IndexTTS 检查点
- GPT-SoVITS 模型

### 5. 安装前端依赖

\`\`\`bash
cd web
npm install
cd ..
\`\`\`

### 6. 配置环境

在根目录创建 \`.env\` 文件：

\`\`\`env
# API 密钥
GEMINI_API_KEY=你的_gemini_api_密钥
HUGGINGFACE_TOKEN=你的_hugging_face_token

# 可选：中国用户使用
HF_ENDPOINT=https://hf-mirror.com
\`\`\`

### 7. 验证安装

\`\`\`bash
python check_environment.py
\`\`\`

预期输出：
\`\`\`
✓ Python 版本: 3.10.x
✓ PyTorch 已安装并支持 CUDA
✓ FFmpeg 已找到
✓ 所有必需包已安装
✓ 模型下载成功
\`\`\`

## 故障排查

### CUDA 未检测到
如果 PyTorch 未检测到您的 GPU：
1. 验证 NVIDIA 驱动已安装
2. 检查 CUDA toolkit 版本是否匹配 PyTorch
3. 使用正确的 CUDA 版本重新安装 PyTorch

### 模型下载失败
- 中国用户使用 \`HF_ENDPOINT=https://hf-mirror.com\`
- 检查您的网络连接
- 必要时手动下载模型

### FFmpeg 未找到
- **Windows**: 从 [ffmpeg.org](https://ffmpeg.org) 下载并添加到 PATH
- **Linux**: \`sudo apt install ffmpeg\`
- **Mac**: \`brew install ffmpeg\`

## 下一步

- [快速入门指南](/docs/quick-start)
- [配置](/docs/api/configuration)
`,
    },
  },

  'quick-start': {
    en: {
      title: 'Quick Start',
      description: 'Get started with TransVox in minutes',
      content: `
# Quick Start

This guide will walk you through your first video translation using TransVox.

## Method 1: Web Interface (Recommended)

### Step 1: Start the Services

\`\`\`bash
# Windows
start.bat

# Linux/Mac
./start.sh
\`\`\`

The script will:
1. Kill any existing processes on ports 3000 and 8000
2. Configure proxy settings
3. Start the backend API server (port 8000)
4. Start the frontend web server (port 3000)

### Step 2: Access the Interface

Open your browser and navigate to:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

### Step 3: Upload a Video

1. Click on **Workspace** in the navigation
2. Drag and drop your video file (or click to browse)
3. Supported formats: MP4, MKV, AVI, MOV, WebM
4. Wait for the upload to complete

### Step 4: Configure Settings

In the right panel, configure:
1. **Source Language**: Auto-detect or manual selection
2. **Target Language**: Choose your desired output language
3. **TTS Engine**:
   - IndexTTS (recommended for Chinese/English)
   - GPT-SoVITS (supports Chinese/English/Japanese/Korean)

### Step 5: Start Processing

1. Click "Start Pipeline"
2. Monitor progress in real-time
3. Processing time varies based on video length (typically 2-5x real-time)

### Step 6: Download Result

Once complete:
1. Preview the translated video
2. Download the final output
3. Access subtitle files if saved

## Method 2: Command Line Interface

### Basic Usage

\`\`\`bash
python full_auto_pipeline.py input/video.mp4 --target_lang zh
\`\`\`

### Advanced Options

\`\`\`bash
python full_auto_pipeline.py input/video.mp4 \\
  --target_lang zh \\
  --tts_engine indextts \\
  --source_lang en \\
  --skip_steps vocal_separation
\`\`\`

### Available Parameters

- \`--target_lang\`: Target language (zh/en/ja/ko)
- \`--source_lang\`: Source language (auto/en/zh/ja/ko)
- \`--tts_engine\`: TTS engine (indextts/gptsovits)
- \`--skip_steps\`: Skip specific steps (comma-separated)

### Step-by-Step Processing

For more control, use individual scripts:

\`\`\`bash
# Step A: Prepare and generate blank SRT
python stepA_prepare_and_blank_srt.py input/video.mp4 -e whisperx

# Step B: Process with IndexTTS
python stepB_index_pipeline.py video_stem

# Step C: Embed subtitles
python stepC_embed_subtitles.py video_stem
\`\`\`

## Example Workflow

### Translate English video to Chinese

\`\`\`bash
# 1. Place your video in the input folder
cp ~/Downloads/presentation.mp4 input/

# 2. Run the pipeline
python full_auto_pipeline.py input/presentation.mp4 --target_lang zh

# 3. Find output in output/presentation/merge/
\`\`\`

### Expected Output Structure

\`\`\`
output/presentation/
├── presentation_video_only.mp4  # Video without audio
├── presentation_speak.wav       # Separated vocals
├── presentation.srt             # Original transcription
├── presentation.translated.srt  # Translated subtitles
├── tts_indextts/                # Generated TTS audio
└── merge/
    └── presentation_final.mp4   # Final output
\`\`\`

## Tips for Best Results

1. **Video Quality**: Use high-quality source videos for better speech recognition
2. **Audio Clarity**: Videos with clear speech work best (minimize background noise)
3. **Speaker Count**: Works best with 1-3 speakers
4. **Language Pairs**: Chinese ↔ English gives best results
5. **Video Length**: Start with shorter videos (< 5 minutes) for testing

## Next Steps

- [Learn about Features](/docs/features/translation)
- [API Reference](/docs/api/rest)
- [Advanced Configuration](/docs/api/configuration)
`,
    },
    zh: {
      title: '快速入门',
      description: '几分钟内开始使用 TransVox',
      content: `
# 快速入门

本指南将引导您完成第一次使用 TransVox 进行视频翻译。

## 方法 1: Web 界面（推荐）

### 步骤 1: 启动服务

\`\`\`bash
# Windows
start.bat

# Linux/Mac
./start.sh
\`\`\`

脚本将：
1. 终止端口 3000 和 8000 上的现有进程
2. 配置代理设置
3. 启动后端 API 服务器（端口 8000）
4. 启动前端 Web 服务器（端口 3000）

### 步骤 2: 访问界面

在浏览器中打开：
- **前端界面**: http://localhost:3000
- **API 文档**: http://localhost:8000/docs

### 步骤 3: 上传视频

1. 点击导航栏中的**工作空间**
2. 拖放视频文件（或点击浏览）
3. 支持的格式：MP4、MKV、AVI、MOV、WebM
4. 等待上传完成

### 步骤 4: 配置设置

在右侧面板中配置：
1. **源语言**: 自动检测或手动选择
2. **目标语言**: 选择您想要的输出语言
3. **TTS 引擎**:
   - IndexTTS（推荐用于中英文）
   - GPT-SoVITS（支持中英日韩）

### 步骤 5: 开始处理

1. 点击"启动流水线"
2. 实时监控进度
3. 处理时间因视频长度而异（通常为实时的 2-5 倍）

### 步骤 6: 下载结果

完成后：
1. 预览翻译后的视频
2. 下载最终输出
3. 访问字幕文件（如果已保存）

## 方法 2: 命令行界面

### 基本用法

\`\`\`bash
python full_auto_pipeline.py input/video.mp4 --target_lang zh
\`\`\`

### 高级选项

\`\`\`bash
python full_auto_pipeline.py input/video.mp4 \\
  --target_lang zh \\
  --tts_engine indextts \\
  --source_lang en \\
  --skip_steps vocal_separation
\`\`\`

### 可用参数

- \`--target_lang\`: 目标语言（zh/en/ja/ko）
- \`--source_lang\`: 源语言（auto/en/zh/ja/ko）
- \`--tts_engine\`: TTS 引擎（indextts/gptsovits）
- \`--skip_steps\`: 跳过特定步骤（逗号分隔）

### 分步处理

为了更好地控制，使用单独的脚本：

\`\`\`bash
# 步骤 A: 准备并生成空白 SRT
python stepA_prepare_and_blank_srt.py input/video.mp4 -e whisperx

# 步骤 B: 使用 IndexTTS 处理
python stepB_index_pipeline.py video_stem

# 步骤 C: 嵌入字幕
python stepC_embed_subtitles.py video_stem
\`\`\`

## 示例工作流

### 将英文视频翻译成中文

\`\`\`bash
# 1. 将视频放入 input 文件夹
cp ~/Downloads/presentation.mp4 input/

# 2. 运行流水线
python full_auto_pipeline.py input/presentation.mp4 --target_lang zh

# 3. 在 output/presentation/merge/ 中查找输出
\`\`\`

### 预期输出结构

\`\`\`
output/presentation/
├── presentation_video_only.mp4  # 无音频视频
├── presentation_speak.wav       # 分离的人声
├── presentation.srt             # 原始转录
├── presentation.translated.srt  # 翻译后的字幕
├── tts_indextts/                # 生成的 TTS 音频
└── merge/
    └── presentation_final.mp4   # 最终输出
\`\`\`

## 获得最佳效果的技巧

1. **视频质量**: 使用高质量源视频以获得更好的语音识别
2. **音频清晰度**: 语音清晰的视频效果最好（最小化背景噪音）
3. **说话人数量**: 1-3 个说话人效果最佳
4. **语言对**: 中英文互译效果最好
5. **视频长度**: 从较短的视频开始测试（< 5 分钟）

## 下一步

- [了解功能](/docs/features/translation)
- [API 参考](/docs/api/rest)
- [高级配置](/docs/api/configuration)
`,
    },
  },

  'features/translation': {
    en: {
      title: 'Video Translation',
      description: 'Learn how to translate videos with TransVox',
      content: `
# Video Translation

TransVox uses advanced AI translation to provide accurate and natural subtitle translations.

## Translation Engines

### Gemini API (Recommended)
- Latest Google AI model (gemini-2.5-flash)
- Excellent context understanding
- Supports technical terminology
- Rate limits: Check your API quota

### OpenAI API
- ChatGPT-powered translation
- Good for conversational content
- Customizable with system prompts

## Supported Languages

**Source and Target Languages:**
- Chinese (Simplified) - zh
- English - en
- Japanese - ja
- Korean - ko

All languages can be used as both source and target for translation.

## Translation Quality

### Context-Aware Translation
The system:
- Analyzes entire sentences for context
- Preserves meaning and nuance
- Adapts to different speaking styles
- Maintains terminology consistency

### Best Results With
- Educational videos
- Presentations
- Tutorials
- Interviews

### May Need Manual Review
- Highly specialized jargon
- Cultural references
- Wordplay and idioms

## Configuration

Edit \`transvox_config.json\` in the project root directory:

\`\`\`json
{
  "translation": {
    "api_type": "gemini",
    "model": "gemini-2.5-flash",
    "source_lang": "auto",
    "target_lang": "zh"
  }
}
\`\`\`

## Tips for Best Results

1. **Clear Speech** - Ensure source audio is clear
2. **Proper Punctuation** - Better SRT timing = better translation
3. **Context** - Add custom glossaries for specialized terms
4. **Review** - Always review automated translations
`,
    },
    zh: {
      title: '视频翻译',
      description: '了解如何使用 TransVox 翻译视频',
      content: `
# 视频翻译

TransVox 使用先进的 AI 翻译技术提供准确自然的字幕翻译。

## 翻译引擎

### Gemini API（推荐）
- 最新的 Google AI 模型（gemini-2.5-flash）
- 出色的上下文理解能力
- 支持专业术语
- 速率限制：查看您的 API 配额

### OpenAI API
- ChatGPT 驱动的翻译
- 适合对话内容
- 可使用系统提示自定义

## 支持的语言

**源语言和目标语言：**
- 中文（简体）- zh
- 英语 - en
- 日语 - ja
- 韩语 - ko

所有语言都可以作为源语言和目标语言进行翻译。

## 翻译质量

### 上下文感知翻译
系统会：
- 分析整个句子的上下文
- 保留含义和细微差别
- 适应不同的说话风格
- 保持术语一致性

### 效果最佳的内容
- 教育视频
- 演示文稿
- 教程
- 访谈

### 可能需要人工审核
- 高度专业化的术语
- 文化参考
- 文字游戏和成语

## 配置

编辑项目根目录下的 \`transvox_config.json\`：

\`\`\`json
{
  "translation": {
    "api_type": "gemini",
    "model": "gemini-2.5-flash",
    "source_lang": "auto",
    "target_lang": "zh"
  }
}
\`\`\`

## 获得最佳结果的技巧

1. **清晰语音** - 确保源音频清晰
2. **正确标点** - 更好的 SRT 时间轴 = 更好的翻译
3. **上下文** - 为专业术语添加自定义词汇表
4. **审核** - 始终审核自动翻译
`,
    },
  },

  'features/voice-cloning': {
    en: {
      title: 'Voice Cloning',
      description: 'Zero-shot voice cloning technology',
      content: `
# Voice Cloning

TransVox uses advanced zero-shot voice cloning to preserve the original speaker's voice characteristics.

## How It Works

### Zero-Shot Technology
No training required! The system:
1. Extracts voice characteristics from the original audio
2. Analyzes pitch, tone, and rhythm
3. Generates new speech in the target language
4. Maintains the speaker's unique vocal signature

## Supported TTS Engines

### IndexTTS (Recommended)
**Best for:** Chinese and English

**Advantages:**
- Fast processing speed
- High-quality audio output
- Excellent voice similarity
- Stable performance

**Configuration:**
\`\`\`yaml
# tools/index-tts/checkpoints/config.yaml
model_path: "checkpoints/index_v2.pth"
device: "cuda"  # Requires NVIDIA GPU with CUDA
\`\`\`

### GPT-SoVITS
**Best for:** Multi-language support

**Advantages:**
- Supports Chinese, English, Japanese, Korean
- Customizable with your own models
- Fine-grained control over speech parameters

**Configuration:**
\`\`\`yaml
# tools/GPT-SoVITS/GPT_SoVITS/configs/tts_infer.yaml
custom:
  your_model:
    gpt_path: "path/to/gpt.ckpt"
    sovits_path: "path/to/sovits.pth"
\`\`\`

**Note:** CUDA-enabled GPU is required for TTS generation.

## Quality Factors

### Voice Similarity
Depends on:
- Quality of reference audio (3-10 seconds recommended)
- Speaker clarity
- Background noise level
- Speaking style consistency

### Best Practices

1. **Reference Audio**
   - Use clear, high-quality audio
   - 5-10 seconds minimum
   - No background music
   - Consistent volume

2. **Processing**
   - Keep subtitle segments natural (5-15 seconds)
   - Avoid very short or very long segments
   - Maintain consistent speaking pace

3. **Post-Processing**
   - Check audio levels
   - Remove artifacts if any
   - Adjust volume normalization

## Advanced Options

### Temperature Control
Lower = more consistent, Higher = more varied

\`\`\`python
tts_config = {
    "temperature": 0.8,  # 0.1-1.0
    "top_p": 0.9,
    "top_k": 20
}
\`\`\`

### Custom Models
Train your own GPT-SoVITS models for specific voices:
1. Prepare training data (10-30 minutes of audio)
2. Run training script
3. Configure in \`tts_infer.yaml\`
`,
    },
    zh: {
      title: '声音克隆',
      description: '零样本声音克隆技术',
      content: `
# 声音克隆

TransVox 使用先进的零样本声音克隆技术来保留原说话人的声音特征。

## 工作原理

### 零样本技术
无需训练！系统会：
1. 从原始音频中提取声音特征
2. 分析音高、音调和节奏
3. 以目标语言生成新语音
4. 保持说话人独特的声音特征

## 支持的 TTS 引擎

### IndexTTS（推荐）
**最适合**: 中文和英文

**优势**：
- 处理速度快
- 高质量音频输出
- 出色的声音相似度
- 性能稳定

**配置**：
\`\`\`yaml
# tools/index-tts/checkpoints/config.yaml
model_path: "checkpoints/index_v2.pth"
device: "cuda"  # 需要支持 CUDA 的 NVIDIA GPU
\`\`\`

### GPT-SoVITS
**最适合**: 多语言支持

**优势**：
- 支持中文、英文、日文、韩文
- 可使用自定义模型
- 对语音参数的精细控制

**配置**：
\`\`\`yaml
# tools/GPT-SoVITS/GPT_SoVITS/configs/tts_infer.yaml
custom:
  your_model:
    gpt_path: "path/to/gpt.ckpt"
    sovits_path: "path/to/sovits.pth"
\`\`\`

**注意：** TTS 生成需要支持 CUDA 的 GPU。

## 质量因素

### 声音相似度
取决于：
- 参考音频质量（推荐 3-10 秒）
- 说话人清晰度
- 背景噪音水平
- 说话风格一致性

### 最佳实践

1. **参考音频**
   - 使用清晰、高质量的音频
   - 最少 5-10 秒
   - 无背景音乐
   - 音量一致

2. **处理**
   - 保持字幕段落自然（5-15 秒）
   - 避免过短或过长的段落
   - 保持一致的语速

3. **后期处理**
   - 检查音频电平
   - 删除任何杂音
   - 调整音量归一化

## 高级选项

### 温度控制
较低 = 更一致，较高 = 更多变化

\`\`\`python
tts_config = {
    "temperature": 0.8,  # 0.1-1.0
    "top_p": 0.9,
    "top_k": 20
}
\`\`\`

### 自定义模型
为特定声音训练您自己的 GPT-SoVITS 模型：
1. 准备训练数据（10-30 分钟音频）
2. 运行训练脚本
3. 在 \`tts_infer.yaml\` 中配置
`,
    },
  },

  'features/subtitles': {
    en: {
      title: 'Subtitle Processing',
      description: 'Advanced subtitle generation and processing',
      content: `
# Subtitle Processing

TransVox provides advanced subtitle generation and processing capabilities using WhisperX.

## Speech Recognition

### WhisperX Engine
- High-precision speech-to-text
- Speaker diarization (who spoke when)
- Word-level timestamps
- Multiple language support

### Accuracy Factors
- Audio quality
- Speaker clarity
- Background noise
- Language/accent

## Features

### Speaker Diarization
Automatically identifies different speakers:

\`\`\`
[00:00:01.000 --> 00:00:03.500] Speaker_01
Hello, welcome to this tutorial.

[00:00:03.600 --> 00:00:06.200] Speaker_02
Thanks for having me!
\`\`\`

### Timeline Precision
- Word-level timing accuracy
- Natural speech segmentation
- Respects sentence boundaries
- Optimized for readability

### Format Support

#### SRT (SubRip)
\`\`\`srt
1
00:00:01,000 --> 00:00:03,500
Hello, welcome to this tutorial.

2
00:00:03,600 --> 00:00:06,200
Thanks for having me!
\`\`\`

#### ASS (Advanced SubStation Alpha)
- Rich styling options
- Custom fonts and colors
- Position control
- Animation effects

### Subtitle Embedding

Three embedding modes:

1. **Hardcode (Burned-in)**
   - Permanently embedded in video
   - Cannot be turned off
   - Best compatibility

2. **Soft Subtitle**
   - Embedded in container
   - Can be toggled on/off
   - Multiple subtitle tracks supported

3. **External File**
   - Separate .srt or .ass file
   - Easy to edit
   - Widely compatible

## Configuration

### Subtitle Style

\`\`\`python
subtitle_config = {
    "fontSize": 24,
    "fontColor": "#FFFFFF",
    "outlineColor": "#000000",
    "outlineWidth": 2,
    "position": "bottom",
    "margin": 10
}
\`\`\`

### Processing Options

\`\`\`json
{
  "subtitle": {
    "mode": "hardcode",
    "language": "zh",
    "fontSize": 24,
    "fontColor": "#FFFFFF",
    "position": "bottom"
  }
}
\`\`\`

## Tips

1. **Audio Quality**: Use high-quality source audio
2. **Noise Reduction**: Remove background noise before processing
3. **Speaker Count**: Works best with 1-3 speakers
4. **Editing**: Always review and edit as needed
`,
    },
    zh: {
      title: '字幕处理',
      description: '高级字幕生成和处理',
      content: `
# 字幕处理

TransVox 使用 WhisperX 提供高级字幕生成和处理功能。

## 语音识别

### WhisperX 引擎
- 高精度语音转文本
- 说话人识别（谁在何时说话）
- 词级时间戳
- 多语言支持

### 准确性因素
- 音频质量
- 说话人清晰度
- 背景噪音
- 语言/口音

## 功能

### 说话人识别
自动识别不同的说话人：

\`\`\`
[00:00:01.000 --> 00:00:03.500] Speaker_01
你好，欢迎来到本教程。

[00:00:03.600 --> 00:00:06.200] Speaker_02
感谢邀请！
\`\`\`

### 时间轴精度
- 词级计时准确性
- 自然的语音分段
- 尊重句子边界
- 优化可读性

### 格式支持

#### SRT (SubRip)
\`\`\`srt
1
00:00:01,000 --> 00:00:03,500
你好，欢迎来到本教程。

2
00:00:03,600 --> 00:00:06,200
感谢邀请！
\`\`\`

#### ASS (Advanced SubStation Alpha)
- 丰富的样式选项
- 自定义字体和颜色
- 位置控制
- 动画效果

### 字幕嵌入

三种嵌入模式：

1. **硬编码（烧录）**
   - 永久嵌入视频
   - 无法关闭
   - 最佳兼容性

2. **软字幕**
   - 嵌入容器中
   - 可以切换开/关
   - 支持多个字幕轨道

3. **外挂文件**
   - 独立的 .srt 或 .ass 文件
   - 易于编辑
   - 广泛兼容

## 配置

### 字幕样式

\`\`\`python
subtitle_config = {
    "fontSize": 24,
    "fontColor": "#FFFFFF",
    "outlineColor": "#000000",
    "outlineWidth": 2,
    "position": "bottom",
    "margin": 10
}
\`\`\`

### 处理选项

\`\`\`json
{
  "subtitle": {
    "mode": "hardcode",
    "language": "zh",
    "fontSize": 24,
    "fontColor": "#FFFFFF",
    "position": "bottom"
  }
}
\`\`\`

## 技巧

1. **音频质量**: 使用高质量源音频
2. **降噪**: 处理前去除背景噪音
3. **说话人数量**: 1-3 个说话人效果最佳
4. **编辑**: 始终根据需要审核和编辑
`,
    },
  },

  'features/web-tools': {
    en: {
      title: 'Web Toolbox',
      description: 'Specialized tools for video processing',
      content: `
# Web Toolbox

The TransVox web interface includes a comprehensive toolbox with specialized tools for various video processing tasks. Access these tools via the main navigation.

## Available Tools

### 1. Video Download Tool

Download videos from online platforms directly into TransVox.

**Supported Platforms:**
- YouTube
- Bilibili
- Twitter/X
- And more (via yt-dlp)

**Features:**
- Quality selection
- Auto-translation option
- Direct import to workspace

**Usage:**
1. Navigate to Tools → Video Download
2. Paste the video URL
3. Select desired quality
4. Click Download
5. Optionally enable auto-translation

**Example:**
\`\`\`
URL: https://youtube.com/watch?v=xxxxx
Quality: 1080p
✓ Auto-translate after download
\`\`\`

### 2. Transcribe Tool

Generate subtitle files from video or audio using WhisperX.

**Features:**
- High-precision speech recognition
- Speaker diarization (identifies different speakers)
- Auto-detect language or manual selection
- Export to SRT format

**Usage:**
1. Upload video or audio file
2. Select source language (or auto-detect)
3. Click "Generate Subtitles"
4. Download the generated SRT file

**Supported Formats:**
- Video: MP4, MKV, AVI, MOV, WebM
- Audio: WAV, MP3, FLAC, AAC

### 3. Translate Subtitles Tool

Translate subtitle files using advanced LLM models (Gemini/OpenAI).

**Features:**
- Context-aware translation
- Preserves timing information
- Maintains formatting
- Supports multiple languages

**Usage:**
1. Upload SRT subtitle file
2. Select target language
3. Choose translation engine (Gemini recommended)
4. Click "Translate"
5. Download translated SRT

**Translation Quality:**
- Preserves sentence structure
- Maintains terminology consistency
- Adapts to context

### 4. Subtitle Slicer

Extract video segments based on subtitle timestamps.

**Use Cases:**
- Create clips from specific subtitle lines
- Extract highlights
- Generate video snippets for social media

**Features:**
- Precise timestamp-based cutting
- Batch processing
- Multiple export options

**Usage:**
1. Upload video file
2. Upload corresponding SRT file
3. Select subtitle lines to extract
4. Choose output format
5. Download video clips

### 5. Audio Separator

Separate vocals from background music using MSST-WebUI.

**Features:**
- High-quality vocal isolation
- Background music extraction
- Noise reduction
- Multiple separation modes

**Usage:**
1. Upload audio or video file
2. Select separation mode:
   - Vocals only
   - Background only
   - Both (separate files)
3. Click "Separate"
4. Download results

**Applications:**
- Prepare clean vocals for TTS
- Extract background music
- Remove unwanted audio elements

### 6. TTS Synthesis Tools

Generate speech from text using voice cloning.

**Available Engines:**
- **IndexTTS**: Fast, high-quality (Chinese/English)
- **GPT-SoVITS**: Multi-language support

**Features:**
- Zero-shot voice cloning
- Batch generation
- Custom voice models
- Voice parameter control

**Usage:**
1. Upload reference audio (5-10 seconds)
2. Enter text to synthesize
3. Select TTS engine
4. Configure voice parameters
5. Generate and download audio

**Voice Parameters:**
- Temperature (consistency vs variation)
- Speaking rate
- Pitch adjustment

## Tool Integration

All tools integrate seamlessly:

**Example Workflow:**
1. **Download** video from URL
2. **Transcribe** to generate original subtitles
3. **Translate** subtitles to target language
4. **Separate** audio for clean vocals
5. **Generate TTS** from translated subtitles
6. **Merge** in main workspace

## API Access

All tools are also available via REST API:

\`\`\`bash
# Video Download
POST /api/tools/download

# Transcribe
POST /api/tools/transcribe

# Translate
POST /api/tools/translate

# Audio Separation
POST /api/tools/separate

# TTS Generation
POST /api/tools/tts
\`\`\`

See [REST API Documentation](/docs/api/rest) for details.

## Tips for Best Results

1. **Video Download**: Always check copyright before downloading
2. **Transcribe**: Use high-quality audio for better accuracy
3. **Translate**: Review and edit translations for critical content
4. **Audio Separation**: Works best with clear vocal tracks
5. **TTS**: Use clean, clear reference audio

## Limitations

- **Video Download**: Respects platform rate limits
- **Transcribe**: Accuracy depends on audio quality
- **Translate**: May need manual review for specialized terms
- **Audio Separation**: Works best with studio recordings
- **TTS**: Voice similarity depends on reference audio quality
`,
    },
    zh: {
      title: 'Web 工具箱',
      description: '视频处理的专业工具',
      content: `
# Web 工具箱

TransVox Web 界面包含一套完整的工具箱，提供各种视频处理任务的专业工具。通过主导航访问这些工具。

## 可用工具

### 1. 视频下载工具

直接从在线平台下载视频到 TransVox。

**支持的平台：**
- YouTube
- Bilibili
- Twitter/X
- 更多平台（通过 yt-dlp）

**功能：**
- 画质选择
- 自动翻译选项
- 直接导入到工作空间

**使用方法：**
1. 导航到 工具 → 视频下载
2. 粘贴视频 URL
3. 选择所需画质
4. 点击下载
5. 可选择启用自动翻译

**示例：**
\`\`\`
URL: https://youtube.com/watch?v=xxxxx
画质: 1080p
✓ 下载后自动翻译
\`\`\`

### 2. 语音识别工具

使用 WhisperX 从视频或音频生成字幕文件。

**功能：**
- 高精度语音识别
- 说话人识别（识别不同的说话人）
- 自动检测语言或手动选择
- 导出为 SRT 格式

**使用方法：**
1. 上传视频或音频文件
2. 选择源语言（或自动检测）
3. 点击"生成字幕"
4. 下载生成的 SRT 文件

**支持的格式：**
- 视频：MP4、MKV、AVI、MOV、WebM
- 音频：WAV、MP3、FLAC、AAC

### 3. 字幕翻译工具

使用先进的 LLM 模型（Gemini/OpenAI）翻译字幕文件。

**功能：**
- 上下文感知翻译
- 保留时间信息
- 维护格式
- 支持多种语言

**使用方法：**
1. 上传 SRT 字幕文件
2. 选择目标语言
3. 选择翻译引擎（推荐 Gemini）
4. 点击"翻译"
5. 下载翻译后的 SRT

**翻译质量：**
- 保留句子结构
- 保持术语一致性
- 适应上下文

### 4. 字幕切片工具

根据字幕时间戳提取视频片段。

**使用场景：**
- 从特定字幕行创建片段
- 提取精彩片段
- 为社交媒体生成视频片段

**功能：**
- 基于时间戳的精确切割
- 批量处理
- 多种导出选项

**使用方法：**
1. 上传视频文件
2. 上传对应的 SRT 文件
3. 选择要提取的字幕行
4. 选择输出格式
5. 下载视频片段

### 5. 音频分离工具

使用 MSST-WebUI 分离人声和背景音乐。

**功能：**
- 高质量人声分离
- 背景音乐提取
- 降噪处理
- 多种分离模式

**使用方法：**
1. 上传音频或视频文件
2. 选择分离模式：
   - 仅人声
   - 仅背景
   - 两者（分别文件）
3. 点击"分离"
4. 下载结果

**应用场景：**
- 为 TTS 准备干净的人声
- 提取背景音乐
- 去除不需要的音频元素

### 6. TTS 合成工具

使用声音克隆从文本生成语音。

**可用引擎：**
- **IndexTTS**：快速、高质量（中英文）
- **GPT-SoVITS**：多语言支持

**功能：**
- 零样本声音克隆
- 批量生成
- 自定义声音模型
- 声音参数控制

**使用方法：**
1. 上传参考音频（5-10 秒）
2. 输入要合成的文本
3. 选择 TTS 引擎
4. 配置声音参数
5. 生成并下载音频

**声音参数：**
- 温度（一致性 vs 变化）
- 语速
- 音高调整

## 工具集成

所有工具无缝集成：

**示例工作流：**
1. **下载** 来自 URL 的视频
2. **转录** 生成原始字幕
3. **翻译** 字幕到目标语言
4. **分离** 音频获得干净人声
5. **生成 TTS** 从翻译后的字幕
6. **合并** 在主工作空间

## API 访问

所有工具也可通过 REST API 访问：

\`\`\`bash
# 视频下载
POST /api/tools/download

# 语音识别
POST /api/tools/transcribe

# 翻译
POST /api/tools/translate

# 音频分离
POST /api/tools/separate

# TTS 生成
POST /api/tools/tts
\`\`\`

详见 [REST API 文档](/docs/api/rest)。

## 最佳实践技巧

1. **视频下载**：下载前请检查版权
2. **语音识别**：使用高质量音频以获得更好的准确性
3. **翻译**：对于关键内容，请审核和编辑翻译
4. **音频分离**：对于清晰的人声轨道效果最佳
5. **TTS**：使用干净、清晰的参考音频

## 限制

- **视频下载**：尊重平台速率限制
- **语音识别**：准确性取决于音频质量
- **翻译**：专业术语可能需要人工审核
- **音频分离**：录音室录音效果最佳
- **TTS**：声音相似度取决于参考音频质量
`,
    },
  },

  'api/rest': {
    en: {
      title: 'REST API',
      description: 'TransVox REST API documentation',
      content: `
# REST API

TransVox provides a comprehensive REST API for video translation and processing.

## Base URL

\`\`\`
http://localhost:8000
\`\`\`

## Authentication

Currently no authentication required for local deployment. API keys may be required for cloud deployment.

## Endpoints

### Video Upload

**POST** \`/api/videos/upload\`

Upload a video file for processing.

**Request:**
\`\`\`bash
curl -X POST http://localhost:8000/api/videos/upload \\
  -F "file=@video.mp4"
\`\`\`

**Response:**
\`\`\`json
{
  "success": true,
  "data": {
    "fileId": "uuid-here",
    "fileName": "video.mp4",
    "fileSize": 15728640,
    "filePath": "/path/to/video.mp4"
  }
}
\`\`\`

### Start Pipeline

**POST** \`/api/pipeline/start\`

Start the translation pipeline.

**Request:**
\`\`\`json
{
  "videoFile": "/path/to/video.mp4",
  "outputDir": "output/video_20240101",
  "translation": {
    "sourceLanguage": "en",
    "targetLanguage": "zh"
  },
  "tts": {
    "engine": "indextts"
  },
  "subtitle": {
    "mode": "hardcode",
    "position": "bottom"
  }
}
\`\`\`

**Response:**
\`\`\`json
{
  "success": true,
  "data": {
    "taskId": "task-uuid",
    "status": "processing",
    "message": "Pipeline started successfully"
  }
}
\`\`\`

### Get Pipeline Status

**GET** \`/api/pipeline/status/{task_id}\`

Check the status of a running pipeline.

**Response:**
\`\`\`json
{
  "success": true,
  "data": {
    "id": "task-uuid",
    "status": "processing",
    "progress": 45,
    "currentTask": "tts",
    "message": "Generating TTS audio...",
    "result": null
  }
}
\`\`\`

### Stop Pipeline

**POST** \`/api/pipeline/stop/{task_id}\`

Stop a running pipeline.

**Response:**
\`\`\`json
{
  "success": true,
  "message": "Pipeline stopped successfully"
}
\`\`\`

### Get Configuration

**GET** \`/api/config\`

Get current configuration.

**Response:**
\`\`\`json
{
  "success": true,
  "data": {
    "api": {
      "gemini_api_key": "***",
      "gemini_base_url": "https://generativelanguage.googleapis.com"
    },
    "translation": {
      "api_type": "gemini",
      "model": "gemini-2.5-flash",
      "source_lang": "auto",
      "target_lang": "zh"
    },
    "tts": {
      "engine": "indextts"
    }
  }
}
\`\`\`

### Update Configuration

**POST** \`/api/config\`

Update configuration.

**Request:**
\`\`\`json
{
  "translation": {
    "target_lang": "ja"
  },
  "tts": {
    "engine": "gptsovits"
  }
}
\`\`\`

## Error Responses

All error responses follow this format:

\`\`\`json
{
  "success": false,
  "error": "Error message",
  "message": "Detailed error description"
}
\`\`\`

### Common Error Codes

- \`400\`: Bad Request - Invalid parameters
- \`404\`: Not Found - Resource not found
- \`500\`: Internal Server Error - Server error

## Interactive API Documentation

Visit http://localhost:8000/docs for interactive Swagger UI documentation.
`,
    },
    zh: {
      title: 'REST API',
      description: 'TransVox REST API 文档',
      content: `
# REST API

TransVox 提供全面的 REST API 用于视频翻译和处理。

## 基础 URL

\`\`\`
http://localhost:8000
\`\`\`

## 认证

本地部署当前不需要认证。云部署可能需要 API 密钥。

## 端点

### 视频上传

**POST** \`/api/videos/upload\`

上传视频文件进行处理。

**请求:**
\`\`\`bash
curl -X POST http://localhost:8000/api/videos/upload \\
  -F "file=@video.mp4"
\`\`\`

**响应:**
\`\`\`json
{
  "success": true,
  "data": {
    "fileId": "uuid-here",
    "fileName": "video.mp4",
    "fileSize": 15728640,
    "filePath": "/path/to/video.mp4"
  }
}
\`\`\`

### 启动流水线

**POST** \`/api/pipeline/start\`

启动翻译流水线。

**请求:**
\`\`\`json
{
  "videoFile": "/path/to/video.mp4",
  "outputDir": "output/video_20240101",
  "translation": {
    "sourceLanguage": "en",
    "targetLanguage": "zh"
  },
  "tts": {
    "engine": "indextts"
  },
  "subtitle": {
    "mode": "hardcode",
    "position": "bottom"
  }
}
\`\`\`

**响应:**
\`\`\`json
{
  "success": true,
  "data": {
    "taskId": "task-uuid",
    "status": "processing",
    "message": "Pipeline started successfully"
  }
}
\`\`\`

### 获取流水线状态

**GET** \`/api/pipeline/status/{task_id}\`

检查运行中的流水线状态。

**响应:**
\`\`\`json
{
  "success": true,
  "data": {
    "id": "task-uuid",
    "status": "processing",
    "progress": 45,
    "currentTask": "tts",
    "message": "正在生成 TTS 音频...",
    "result": null
  }
}
\`\`\`

### 停止流水线

**POST** \`/api/pipeline/stop/{task_id}\`

停止运行中的流水线。

**响应:**
\`\`\`json
{
  "success": true,
  "message": "流水线已成功停止"
}
\`\`\`

### 获取配置

**GET** \`/api/config\`

获取当前配置。

**响应:**
\`\`\`json
{
  "success": true,
  "data": {
    "api": {
      "gemini_api_key": "***",
      "gemini_base_url": "https://generativelanguage.googleapis.com"
    },
    "translation": {
      "api_type": "gemini",
      "model": "gemini-2.5-flash",
      "source_lang": "auto",
      "target_lang": "zh"
    },
    "tts": {
      "engine": "indextts"
    }
  }
}
\`\`\`

### 更新配置

**POST** \`/api/config\`

更新配置。

**请求:**
\`\`\`json
{
  "translation": {
    "target_lang": "ja"
  },
  "tts": {
    "engine": "gptsovits"
  }
}
\`\`\`

## 错误响应

所有错误响应遵循此格式：

\`\`\`json
{
  "success": false,
  "error": "错误消息",
  "message": "详细错误描述"
}
\`\`\`

### 常见错误代码

- \`400\`: 错误请求 - 无效参数
- \`404\`: 未找到 - 资源不存在
- \`500\`: 内部服务器错误 - 服务器错误

## 交互式 API 文档

访问 http://localhost:8000/docs 查看交互式 Swagger UI 文档。
`,
    },
  },

  'api/configuration': {
    en: {
      title: 'Configuration',
      description: 'Configure TransVox settings',
      content: `
# Configuration

Learn how to configure TransVox for optimal performance.

## Configuration File

TransVox uses \`transvox_config.json\` located in the root directory.

### Structure

\`\`\`json
{
  "api": {
    "gemini_api_key": "your-key-here",
    "gemini_base_url": "https://generativelanguage.googleapis.com",
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
  }
}
\`\`\`

## Editing Configuration

You can edit the configuration file directly or use the Web interface.

### Direct File Editing

Edit \`transvox_config.json\` in your text editor:

\`\`\`json
{
  "translation": {
    "api_type": "gemini",
    "target_lang": "zh"
  },
  "tts": {
    "engine": "indextts"
  },
  "api": {
    "gemini_api_key": "YOUR_KEY"
  }
}
\`\`\`

### Using Web Interface

Access configuration via Settings page at http://localhost:3000/settings

## Environment Variables

Create a \`.env\` file:

\`\`\`env
# API Keys
GEMINI_API_KEY=your_key_here
HUGGINGFACE_TOKEN=your_token_here

# Optional settings
HF_ENDPOINT=https://hf-mirror.com  # For China users
HTTP_PROXY=http://127.0.0.1:7890   # Proxy settings
HTTPS_PROXY=http://127.0.0.1:7890
\`\`\`

## TTS Engine Configuration

### IndexTTS

Edit \`tools/index-tts/checkpoints/config.yaml\`:

\`\`\`yaml
model_path: "checkpoints/index_v2.pth"
device: "cuda"  # Requires CUDA GPU
sample_rate: 22050
\`\`\`

### GPT-SoVITS

Edit \`tools/GPT-SoVITS/GPT_SoVITS/configs/tts_infer.yaml\`:

\`\`\`yaml
custom:
  my_voice:
    gpt_path: "GPT_weights/my-gpt.ckpt"
    sovits_path: "SoVITS_weights/my-sovits.pth"
    prompt_text: ""
    prompt_lang: "zh"
\`\`\`

## Advanced Options

### Skip Steps

Skip specific pipeline steps:

\`\`\`bash
python full_auto_pipeline.py input.mp4 \\
  --skip_steps vocal_separation,subtitle_embed
\`\`\`

Available steps:
- \`audio_separation\`
- \`vocal_separation\`
- \`transcribe\`
- \`translate\`
- \`tts\`
- \`merge\`
- \`subtitle_embed\`
`,
    },
    zh: {
      title: '配置',
      description: '配置 TransVox 设置',
      content: `
# 配置

了解如何配置 TransVox 以获得最佳性能。

## 配置文件

TransVox 使用位于根目录的 \`transvox_config.json\`。

### 结构

\`\`\`json
{
  "api": {
    "gemini_api_key": "你的密钥",
    "gemini_base_url": "https://generativelanguage.googleapis.com",
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
  }
}
\`\`\`

## 编辑配置

您可以直接编辑配置文件或使用 Web 界面。

### 直接编辑文件

在文本编辑器中编辑 \`transvox_config.json\`：

\`\`\`json
{
  "translation": {
    "api_type": "gemini",
    "target_lang": "zh"
  },
  "tts": {
    "engine": "indextts"
  },
  "api": {
    "gemini_api_key": "YOUR_KEY"
  }
}
\`\`\`

### 使用 Web 界面

通过设置页面访问配置：http://localhost:3000/settings

## 环境变量

创建 \`.env\` 文件：

\`\`\`env
# API 密钥
GEMINI_API_KEY=你的密钥
HUGGINGFACE_TOKEN=你的token

# 可选设置
HF_ENDPOINT=https://hf-mirror.com  # 中国用户
HTTP_PROXY=http://127.0.0.1:7890   # 代理设置
HTTPS_PROXY=http://127.0.0.1:7890
\`\`\`

## TTS 引擎配置

### IndexTTS

编辑 \`tools/index-tts/checkpoints/config.yaml\`：

\`\`\`yaml
model_path: "checkpoints/index_v2.pth"
device: "cuda"  # 需要 CUDA GPU
sample_rate: 22050
\`\`\`

### GPT-SoVITS

编辑 \`tools/GPT-SoVITS/GPT_SoVITS/configs/tts_infer.yaml\`：

\`\`\`yaml
custom:
  my_voice:
    gpt_path: "GPT_weights/my-gpt.ckpt"
    sovits_path: "SoVITS_weights/my-sovits.pth"
    prompt_text: ""
    prompt_lang: "zh"
\`\`\`

## 高级选项

### 跳过步骤

跳过特定的流水线步骤：

\`\`\`bash
python full_auto_pipeline.py input.mp4 \\
  --skip_steps vocal_separation,subtitle_embed
\`\`\`

可用步骤：
- \`audio_separation\` - 音频分离
- \`vocal_separation\` - 人声分离
- \`transcribe\` - 转录
- \`translate\` - 翻译
- \`tts\` - 文本转语音
- \`merge\` - 合并
- \`subtitle_embed\` - 字幕嵌入
`,
    },
  },

  'advanced/custom-models': {
    en: {
      title: 'Custom Models',
      description: 'Use custom AI models with TransVox',
      content: `
# Custom Models

Learn how to use and train custom models with TransVox.

## GPT-SoVITS Custom Models

### Training Your Own Model

1. **Prepare Training Data**
   - 10-30 minutes of clean audio
   - Single speaker
   - Clear pronunciation
   - No background music

2. **Process Audio**
\`\`\`bash
cd tools/GPT-SoVITS
python prepare_datasets.py --audio_dir /path/to/audio
\`\`\`

3. **Train Model**
\`\`\`bash
python train.py --config configs/train_config.yaml
\`\`\`

4. **Configure**
Edit \`tts_infer.yaml\`:
\`\`\`yaml
custom:
  my_voice:
    gpt_path: "GPT_weights/my_voice.ckpt"
    sovits_path: "SoVITS_weights/my_voice.pth"
\`\`\`

### Using Pre-trained Models

Download community models and place in:
- \`tools/GPT-SoVITS/GPT_weights/\`
- \`tools/GPT-SoVITS/SoVITS_weights/\`

## IndexTTS Models

Currently uses pre-trained model. Custom training coming soon!

## Tips

- Use high-quality audio
- Consistent speaking style
- Clear pronunciation
- No background noise
`,
    },
    zh: {
      title: '自定义模型',
      description: '在 TransVox 中使用自定义 AI 模型',
      content: `
# 自定义模型

了解如何在 TransVox 中使用和训练自定义模型。

## GPT-SoVITS 自定义模型

### 训练您自己的模型

1. **准备训练数据**
   - 10-30 分钟的清晰音频
   - 单个说话人
   - 发音清晰
   - 无背景音乐

2. **处理音频**
\`\`\`bash
cd tools/GPT-SoVITS
python prepare_datasets.py --audio_dir /path/to/audio
\`\`\`

3. **训练模型**
\`\`\`bash
python train.py --config configs/train_config.yaml
\`\`\`

4. **配置**
编辑 \`tts_infer.yaml\`：
\`\`\`yaml
custom:
  my_voice:
    gpt_path: "GPT_weights/my_voice.ckpt"
    sovits_path: "SoVITS_weights/my_voice.pth"
\`\`\`

### 使用预训练模型

下载社区模型并放置在：
- \`tools/GPT-SoVITS/GPT_weights/\`
- \`tools/GPT-SoVITS/SoVITS_weights/\`

## IndexTTS 模型

当前使用预训练模型。自定义训练即将推出！

## 技巧

- 使用高质量音频
- 一致的说话风格
- 清晰的发音
- 无背景噪音
`,
    },
  },

}
