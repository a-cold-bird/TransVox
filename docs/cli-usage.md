# TransVox CLI 使用指南

[English](./cli-usage_en.md) | 简体中文

本文档详细介绍 TransVox 命令行工具的使用方法。

## 目录

- [环境配置](#环境配置)
- [全自动流程](#全自动流程)
- [分步执行](#分步执行)
- [字幕嵌入](#字幕嵌入)
- [辅助工具](#辅助工具)
- [使用建议](#使用建议)

---

## 环境配置

### API Key 配置

TransVox 需要以下 API Key 才能正常工作：

#### 1. Gemini API Key（字幕翻译）

1. 访问 [Google AI Studio](https://aistudio.google.com/) 创建 Gemini API Key
2. 将 Key 写入 `.env` 文件：
   ```bash
   GEMINI_API_KEY=your_key_here
   ```
3. （可选）配置模型版本：
   ```bash
   TRANSLATION_MODEL=gemini-2.5-pro  # 默认值
   # 或使用其他模型：gemini-2.0-flash
   ```

#### 2. Hugging Face Token（说话人识别）

1. 登录 [Hugging Face](https://huggingface.co/)，进入 Settings → Access Tokens
2. 创建 Token，勾选 **"Read access to contents of selected repos"**
3. 选择以下仓库并同意使用条款：
   - [`pyannote/speaker-diarization-3.1`](https://huggingface.co/pyannote/speaker-diarization-3.1)
   - [`pyannote/segmentation-3.0`](https://huggingface.co/pyannote/segmentation-3.0)
4. 写入 `.env` 文件：
   ```bash
   HUGGINGFACE_TOKEN=your_token_here
   ```

### GPT-SoVITS 模型配置（可选）

如需使用自定义模型，编辑配置文件：

**配置文件位置：** `tools/GPT-SoVITS/GPT_SoVITS/configs/tts_infer.yaml`

**关键参数：**

```yaml
custom:
  bert_base_path: GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large
  cnhuhbert_base_path: GPT_SoVITS/pretrained_models/chinese-hubert-base
  device: cuda              # 设备：cuda 或 cpu
  is_half: true             # 是否使用半精度（FP16）
  t2s_weights_path: GPT_SoVITS/pretrained_models/s1v3.ckpt  # GPT 模型
  version: v2Pro            # 模型版本
  vits_weights_path: GPT_SoVITS/pretrained_models/v2Pro/s2Gv2Pro.pth  # SoVITS 模型
```

**使用自己训练的模型：**

1. 训练模型后，模型保存在：
   - GPT: `tools/GPT-SoVITS/GPT_weights/` 或 `GPT_weights_v2/`
   - SoVITS: `tools/GPT-SoVITS/SoVITS_weights/` 或 `SoVITS_weights_v2/`

2. 修改 `custom` 配置：
   ```yaml
   t2s_weights_path: GPT_weights_v2/your_gpt_model.ckpt
   vits_weights_path: SoVITS_weights_v2/your_sovits_model.pth
   ```

---

## 全自动流程

### 基本用法

一键完成从视频到配音的全流程：

```bash
python full_auto_pipeline.py input/your_video.mp4 --target_lang zh
```

### 常用参数

| 参数 | 选项 | 说明 | 默认值 |
|------|------|------|--------|
| `--target_lang` | zh/en/ja/ko | 目标翻译语言（**必填**） | 无 |
| `--tts_engine` | indextts/gptsovits | TTS 引擎 | indextts |
| `--tts_mode` | local/api | GPT-SoVITS 运行模式 | local |
| `--no-diarization` | - | 禁用说话人识别 | 启用 |
| `--no-separation` | - | 禁用人声分离 | 启用 |
| `--translation_mode` | whole/smart | 翻译模式 | whole |
| `--embed-subtitle` | - | 自动嵌入字幕 | 不嵌入 |
| `--subtitle-bilingual` | - | 使用双语字幕 | 单语 |

### 使用示例

**1. 英文→中文（IndexTTS）**

```bash
python full_auto_pipeline.py input/EN_test.mp4 --target_lang zh
```

**2. 中文→英文（IndexTTS）**

```bash
python full_auto_pipeline.py input/ZH_test.mp4 --target_lang en
```

**3. 英文→日文（GPT-SoVITS）**

```bash
python full_auto_pipeline.py input/video.mp4 --target_lang ja --tts_engine gptsovits
```

**4. 快速模式（禁用人声分离和说话人识别）**

```bash
python full_auto_pipeline.py input/video.mp4 --target_lang zh --no-diarization --no-separation
```

**5. 自动嵌入单语字幕**

```bash
python full_auto_pipeline.py input/video.mp4 --target_lang zh --embed-subtitle
```

**6. 自动嵌入双语字幕**

```bash
python full_auto_pipeline.py input/video.mp4 --target_lang zh --embed-subtitle --subtitle-bilingual
```

### 输出位置

- **配音视频：** `output/<视频名>/merge/<视频名>_dubbed.mp4`
- **带字幕视频：** `output/<视频名>/merge/<视频名>_dubbed_subtitled.mp4`（如启用 --embed-subtitle）

---

## 分步执行

如需更精细的控制（如手动修改字幕），可分步执行：

### 步骤 1：预处理与转录

```bash
python stepA_prepare_and_blank_srt.py input/your_video.mp4 -e whisperx -l auto
```

**参数说明：**
- `-e whisperx`：使用 WhisperX 引擎（推荐）
- `-l auto`：自动检测语言

**输出：**
- `output/<stem>/<stem>.srt`：原始字幕文件
- `output/<stem>/<stem>_speak.wav`：分离的人声
- `output/<stem>/<stem>_video_only.mp4`：无音频视频

### 步骤 2：翻译字幕

```bash
python Scripts/step4_translate_srt.py output/<stem>/<stem>.srt --target_lang zh --whole_file
```

**参数说明：**
- `--target_lang {zh|en|ja|ko}`：目标语言
- `--whole_file`：一次性翻译整个文件（推荐）

**输出：**
- `output/<stem>/<stem>.translated.srt`：翻译后的字幕

> 💡 **免费替代方案：** 使用 [在线字幕翻译工具](https://tools.newzone.top/zh/subtitle-translator)（无需 API Key）

> 此时可手动编辑 `.srt` 文件以修正翻译内容

### 步骤 3：语音合成

选择以下 TTS 引擎之一：

#### 3a. IndexTTS（仅支持中英文）

```bash
python stepB_index_pipeline.py <stem>
```

**特点：**
- 自动检测目标语言
- Zero-Shot 语音克隆效果好
- 仅支持中文和英文

#### 3b. GPT-SoVITS（支持中日英韩）

```bash
python stepB_gptsovits_pipeline.py <stem> --mode local --text_lang zh --prompt_lang en
```

**参数说明：**
- `<stem>`：视频文件基名（去扩展名）
  - 例如：`input/EN_test.mp4` 的 stem 是 `EN_test`
- `--text_lang {zh|en|ja|ko|auto}`：目标语言（TTS 合成语言）
  - 示例：英译中 → `--text_lang zh`
  - 示例：中译英 → `--text_lang en`
- `--prompt_lang {zh|en|ja|ko}`：参考音频语言（原视频语言）**必须明确指定**
  - 示例：英译中 → `--prompt_lang en`
  - 示例：中译英 → `--prompt_lang zh`
- `--mode {local|api}`：运行模式
  - `local`：本地推理（**推荐**，需配置模型）
  - `api`：API 模式（需手动启动 GPT-SoVITS API 服务）
- `--resume`：跳过已存在的步骤，适合中断后继续

**输出：**
- `output/<stem>/tts*/`：TTS 音频片段
- `output/<stem>/merge/`：最终视频

---

## 字幕嵌入

### 方式一：全自动流程中启用

```bash
# 单语字幕
python full_auto_pipeline.py input/video.mp4 --target_lang zh --embed-subtitle

# 双语字幕
python full_auto_pipeline.py input/video.mp4 --target_lang zh --embed-subtitle --subtitle-bilingual
```

### 方式二：独立运行

```bash
# 基本用法（自动 AI 分行 + 暂停编辑 + 嵌入）
python stepC_embed_subtitles.py <stem>

# 双语字幕
python stepC_embed_subtitles.py <stem> --bilingual

# 跳过字幕分行（直接使用原字幕）
python stepC_embed_subtitles.py <stem> --no-split

# 使用标点分行（不调用 API）
python stepC_embed_subtitles.py <stem> --no-gemini
```

### 字幕处理选项

| 参数 | 说明 |
|------|------|
| `--no-split` | 不分行，直接复制原字幕 |
| `--no-gemini` | 使用标点分行（不调用 AI API） |
| `--max-line-chars <数字>` | 每行最大字符数（默认 40） |
| `--bilingual` | 创建双语字幕 |
| `--no-pause` | 不暂停等待编辑（自动模式） |

### 字体要求

首次使用需下载 [霞鹜文楷字体](https://github.com/lxgw/LxgwWenKai/releases)：
- 下载 `LXGWWenKai-Regular.ttf`
- 放到 `fonts/` 目录

---

## 辅助工具

### 1. 下载视频

```bash
# 使用批处理文件
download_video.bat

# 或手动运行
python -m yt_dlp -o "input/%(title)s.%(ext)s" -f "bv*[ext=mp4]+ba/b" "视频链接"
```

支持 YouTube、Bilibili、抖音等 1000+ 网站。

### 2. 清理输出目录

```bash
python step_clean_output.py
```

默认清空 `output/` 目录，脚本会自动重建空目录。

### 3. 环境检测

```bash
python check_environment.py
```

检查项：
- GPU 和 CUDA 是否可用
- ffmpeg 是否安装
- Python 依赖是否完整
- 模型是否下载
- 环境变量是否配置

---

## 使用建议

### 视频素材要求

为获得最佳效果，建议选择符合以下条件的视频：

- ✅ **人声清晰：** 背景音乐不要有歌声，纯配乐或无 BGM 最佳
- ✅ **单人发言：** 尽量避免多个角色同时说话
- ✅ **音质良好：** 避免过多噪音、混响或音量过低

### 工作流程对比

**快速流程（自动化，适合测试）：**

```bash
python full_auto_pipeline.py input/video.mp4 --target_lang zh
```

**高质量流程（推荐）：**

1. **生成初始字幕：**
   ```bash
   python stepA_prepare_and_blank_srt.py input/video.mp4 -e whisperx -l auto
   ```

2. **手动打轴：** 使用 Aegisub 等工具校正时间轴

3. **翻译润色：** 使用在线工具或人工翻译，确保自然流畅

4. **保存校正后的字幕：**
   - `output/<stem>/<stem>_merged_optimized.srt` - 原文字幕（用于切割音频）
   - `output/<stem>/<stem>.translated.srt` - 翻译后字幕（用于 TTS）

5. **运行 TTS 合成：**
   ```bash
   python stepB_index_pipeline.py <stem>
   ```

### 说话人识别说明

- 项目**自带说话人识别功能**（基于 pyannote）
- 会在字幕中自动标注 `[SPEAKER_1]`, `[SPEAKER_2]` 等
- TTS 合成时会自动使用对应片段的原音色作为参考
- 如果识别不准确，可使用 `--no-diarization` 禁用

### 常见问题

#### 1. 显存不足

- **推荐配置：** 2080Ti 及以上
- **解决方案：**
  - 改用 GPT-SoVITS 替代 IndexTTS
  - 优先选择 `whisperx` 作为转录引擎

#### 2. 最终视频未生成

1. 检查 `output/<stem>/tts*/` 是否有 `.wav` 文件
2. 检查 `output/<stem>/merge/` 是否写入失败
3. 查看控制台日志定位报错
4. 确认 API Key/Token 配置正确

#### 3. 结果不理想

- **字幕时间轴不准：** 使用 Aegisub 手动校正
- **翻译不准确：** 手动润色 `.translated.srt`
- **语音不自然：** 检查原视频音质，或尝试更换 TTS 引擎
- **说话人混乱：** 手动修正 `_merged_optimized.srt` 中的说话人标签

---

## 语言支持

### TTS 引擎语言支持

| 引擎 | 支持语言 |
|------|----------|
| IndexTTS | 中文（zh）、英文（en） |
| GPT-SoVITS | 中文（zh）、英文（en）、日文（ja）、韩文（ko） |

### 目录结构

```
TransVox/
├── input/                      # 输入视频
├── output/<stem>/              # 输出目录
│   ├── <stem>_video_only.mp4   # 无音频视频
│   ├── <stem>_speak.wav        # 分离的人声
│   ├── <stem>.srt              # 原始字幕
│   ├── <stem>.translated.srt   # 翻译后字幕
│   ├── tts*/                   # TTS 音频
│   └── merge/                  # 最终视频
│       ├── <stem>_dubbed.mp4           # 配音视频
│       └── <stem>_dubbed_subtitled.mp4 # 带字幕视频
└── Scripts/                    # 处理脚本
```

---

## 更多资源

- [快速开始指南](./getting-started.md)
- [配置管理指南](./CONFIG_GUIDE.md)
- [项目主页](https://github.com/a-cold-bird/TransVox)
- [问题反馈](https://github.com/a-cold-bird/TransVox/issues)
