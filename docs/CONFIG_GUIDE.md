# TransVox 配置管理指南

TransVox 现在支持用户配置管理功能，让你可以保存和使用自己的翻译偏好设置！

## 功能特性

- ✅ 支持翻译引擎选择（Gemini 和 OpenAI）
- ✅ 默认使用 Gemini 2.0 Flash Exp 模型（更快速）
- ✅ 支持自定义输入/输出语言
- ✅ 支持选择 TTS 引擎（IndexTTS 或 GPT-SoVITS）
- ✅ 支持控制是否输出 SRT 字幕文件
- ✅ 配置保存在用户配置文件中，重启后自动加载

## 配置文件位置

配置文件位于项目根目录：
- `transvox_config.json` - 你的配置文件（Git 会忽略，不会提交）
- `transvox_config.json.example` - 配置模板（仅供参考）

**首次使用：**
配置文件不存在时会自动使用默认配置创建。你也可以手动复制模板：
```bash
# Windows
copy transvox_config.json.example transvox_config.json

# Linux/Mac
cp transvox_config.json.example transvox_config.json
```

## 使用配置管理工具

### 1. 查看当前配置

```bash
python config_tool.py show
```

### 2. 获取特定配置项

```bash
# 获取翻译引擎类型
python config_tool.py get translation.api_type

# 获取翻译模型
python config_tool.py get translation.model

# 获取 TTS 引擎
python config_tool.py get tts.engine
```

### 3. 修改配置

```bash
# 修改翻译引擎为 OpenAI
python config_tool.py set translation.api_type openai

# 修改翻译模型
python config_tool.py set translation.model gemini-2.0-flash-thinking-exp

# 修改目标语言为中文
python config_tool.py set translation.target_lang zh

# 修改 TTS 引擎为 GPT-SoVITS
python config_tool.py set tts.engine gptsovits

# 禁用 SRT 文件输出
python config_tool.py set output.save_srt false
```

### 4. 使用预设配置

#### 快速模式（推荐日常使用）
```bash
python config_tool.py preset fast
```
- 使用 Gemini 2.0 Flash Exp（速度快）
- 使用 IndexTTS
- 禁用说话人识别和人声分离（提高速度）

#### 高质量模式（推荐重要项目）
```bash
python config_tool.py preset quality
```
- 使用 Gemini 2.0 Flash Thinking Exp（质量高）
- 使用 GPT-SoVITS
- 启用说话人识别和人声分离（效果更好）

#### 语言预设
```bash
# 翻译为中文
python config_tool.py preset chinese

# 翻译为英文
python config_tool.py preset english
```

### 5. 重置配置

```bash
# 重置为默认配置（需要确认）
python config_tool.py reset --confirm
```

### 6. 查看配置文件位置

```bash
python config_tool.py path
```

## 默认配置

```json
{
  "translation": {
    "api_type": "gemini",
    "model": "gemini-2.0-flash-exp",
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

## 在脚本中使用配置

### 翻译字幕时指定引擎

```bash
# 使用 Gemini 翻译（默认）
python Scripts/step4_translate_srt.py input.srt --target_lang zh

# 使用 OpenAI 翻译（覆盖配置）
python Scripts/step4_translate_srt.py input.srt --target_lang zh --api_type openai

# 指定特定模型
python Scripts/step4_translate_srt.py input.srt --target_lang zh --model gemini-2.0-flash-thinking-exp
```

### 参数优先级

配置的优先级从高到低：
1. **命令行参数**：直接在命令行指定的参数
2. **配置文件**：保存在 `.transvox_config.json` 的配置
3. **环境变量**：在 `.env` 文件中设置的环境变量
4. **默认值**：代码中的默认值

### 示例：使用不同的配置

```bash
# 使用配置文件中的设置
python full_auto_pipeline.py input.mp4 --target_lang en

# 覆盖配置文件，使用 OpenAI
python full_auto_pipeline.py input.mp4 --target_lang en \
    --translation-api openai --translation-model gpt-4

# 完全自定义
python full_auto_pipeline.py input.mp4 \
    --target_lang ja \
    --tts_engine gptsovits \
    --translation-api gemini \
    --translation-model gemini-2.0-flash-thinking-exp
```

## 翻译引擎对比

### Gemini（推荐）

**优势：**
- ✅ 免费额度较高
- ✅ 速度快（Flash 模型）
- ✅ 支持多语言
- ✅ 质量优秀

**推荐模型：**
- `gemini-2.0-flash-exp`：速度最快，适合日常使用
- `gemini-2.0-flash-thinking-exp`：质量最高，适合重要项目

**配置：**
```bash
# 需要在 .env 文件中设置
GEMINI_API_KEY=你的API密钥
GEMINI_PROXY_URL=https://generativelanguage.googleapis.com/v1beta/
```

### OpenAI

**优势：**
- ✅ 翻译质量稳定
- ✅ API 兼容多种服务

**推荐模型：**
- `gpt-4`：质量最高
- `gpt-3.5-turbo`：速度快，成本低

**配置：**
```bash
# 需要在 .env 文件中设置
OPENAI_API_KEY=你的API密钥
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选，使用OpenAI兼容服务时需要
```

## TTS 引擎对比

### IndexTTS（默认，推荐）

**优势：**
- ✅ 速度快
- ✅ 效果好
- ✅ 支持中英文

**支持语言：**
- 中文 (zh)
- 英文 (en)

### GPT-SoVITS

**优势：**
- ✅ 支持更多语言
- ✅ 音质优秀
- ✅ 可自定义模型

**支持语言：**
- 中文 (zh)
- 英文 (en)
- 日文 (ja)
- 韩文 (ko)

## 常见问题

### Q: 配置文件在哪里？
A: 配置文件在项目根目录的 `transvox_config.json`，你可以直接用编辑器打开修改，也可以运行 `python config_tool.py path` 查看完整路径。

### Q: 如何查看当前使用的配置？
A: 运行 `python config_tool.py show`。

### Q: 配置不生效怎么办？
A:
1. 检查配置文件是否正确保存
2. 检查是否有命令行参数覆盖了配置
3. 检查环境变量是否设置

### Q: 如何恢复默认配置？
A: 运行 `python config_tool.py reset --confirm`。

### Q: Gemini 和 OpenAI 哪个更好？
A:
- **推荐 Gemini**：免费额度高，速度快，质量好
- 如果需要特定功能或已有 OpenAI 账号，可以使用 OpenAI

### Q: 如何选择翻译模型？
A:
- **日常使用**：`gemini-2.0-flash-exp`（快速）
- **重要项目**：`gemini-2.0-flash-thinking-exp`（高质量）
- **OpenAI**：`gpt-4`（最佳质量）或 `gpt-3.5-turbo`（快速）

## 相关文档

- [主 README](../README.md)
- [英文 README](../README_EN.md)
- [快速开始指南](./getting-started.md)
- [CLI 使用指南](./cli-usage.md)
