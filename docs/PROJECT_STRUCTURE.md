# TransVox 项目结构

本文档描述 TransVox 项目的目录结构和关键文件。

## 项目根目录

```
TransVox/
├── api_server.py              # FastAPI 后端服务器
├── full_auto_pipeline.py      # 全自动流程主脚本
├── stepA_prepare_and_blank_srt.py    # 步骤A: 预处理与转录
├── stepB_index_pipeline.py    # 步骤B: IndexTTS 流程
├── stepB_gptsovits_pipeline.py # 步骤B: GPT-SoVITS 流程
├── stepC_embed_subtitles.py   # 步骤C: 嵌入字幕
├── requirements.txt           # Python 依赖
├── transvox_config.json.example # 配置文件示例
├── .env_template              # 环境变量模板
├── start.bat                  # Windows 一键启动脚本
└── start.sh                   # Linux 一键启动脚本
```

## 核心目录

### Scripts/ - 脚本目录

包含所有子步骤脚本和工具脚本：

```
Scripts/
├── step1_separate_audio_video.py    # 分离音频和视频
├── step2_separate_vocals.py         # 人声分离
├── step3_transcribe_whisperx.py     # WhisperX 转录
├── step4_translate_srt.py           # 字幕翻译
├── step6_tts_indextts2.py          # IndexTTS 语音合成
├── step6_tts_gptsovits.py          # GPT-SoVITS 语音合成
├── step7_merge_tts_and_mux.py      # 合并音频
├── step9_embed_to_video.py         # 嵌入字幕到视频
├── download_models.py              # 模型下载脚本
├── download_nltk_data.py           # NLTK 数据下载
├── check_environment.py            # 环境检测
├── config_manager.py               # 配置管理器
├── config_tool.py                  # 配置命令行工具
├── fix_translated_srt.py           # 修复翻译字幕
├── step_clean_output.py            # 清理输出目录
└── test_system.py                  # 系统测试
```

### web/ - 前端目录

Next.js + TypeScript 构建的现代化 Web 界面：

```
web/
├── src/
│   ├── app/                   # Next.js App Router
│   │   ├── layout.tsx         # 根布局
│   │   ├── page.tsx           # 首页
│   │   ├── workspace/         # 工作区页面
│   │   ├── tools/             # 工具箱页面
│   │   └── globals.css        # 全局样式
│   ├── components/            # React 组件
│   │   ├── ui/               # 基础 UI 组件 (Radix UI)
│   │   ├── video/            # 视频相关组件
│   │   ├── pipeline/         # 流程组件
│   │   └── tools/            # 工具箱组件
│   ├── lib/                  # 工具函数
│   ├── api/                  # API 客户端
│   ├── store/                # Zustand 状态管理
│   ├── types/                # TypeScript 类型定义
│   └── pages/                # 文档页面 (Nextra)
├── public/                   # 静态资源
├── next.config.js            # Next.js 配置
├── tailwind.config.ts        # Tailwind CSS 配置
├── tsconfig.json             # TypeScript 配置
└── package.json              # 前端依赖
```

### tools/ - AI 模型工具目录

集成的第三方 AI 模型和工具：

```
tools/
├── MSST-WebUI/               # 人声分离工具
│   ├── pretrain/             # 预训练模型 (gitignored)
│   ├── results/              # 分离结果 (gitignored)
│   └── start_seprate.bat     # Windows 启动脚本
│
├── GPT-SoVITS/               # GPT-SoVITS TTS 引擎
│   ├── GPT_SoVITS/
│   │   ├── configs/          # 配置文件
│   │   │   └── tts_infer.yaml
│   │   └── pretrained_models/ # 预训练模型 (gitignored)
│   └── api_v2.py             # API 服务
│
├── index-tts/                # IndexTTS-2 引擎
│   ├── checkpoints/          # 模型检查点 (gitignored)
│   ├── indextts/             # 核心代码
│   └── setup.py              # 安装配置
│
└── whisper-subtitles/        # Whisper 字幕工具
    ├── faster_whisper_subtitle_generator.py
    └── models/               # Whisper 模型 (gitignored)
```

### docs/ - 文档目录

项目文档和指南：

```
docs/
├── getting-started.md        # 快速开始指南
├── cli-usage.md              # CLI 使用文档
├── CONFIG_GUIDE.md           # 配置管理指南
├── PROJECT_STRUCTURE.md      # 本文档
└── CONCURRENCY_REPORT.md     # 并发处理报告
```

## 输入输出目录

### input/ - 输入目录

存放待处理的视频文件：

```
input/
├── video1.mp4
├── video2.mp4
└── .gitkeep                  # Git 占位文件
```

注意：视频文件不会被提交到 Git（已在 .gitignore 中排除）

### output/ - 输出目录

自动生成的处理结果，按视频 stem 组织：

```
output/
└── <video_stem>/
    ├── <stem>.srt                      # 原始字幕
    ├── <stem>.translated.srt           # 翻译后字幕
    ├── <stem>_video_only.mp4           # 无音频视频
    ├── <stem>_audio.wav                # 原始音频
    ├── <stem>_speak.wav                # 分离的人声
    ├── <stem>_bgm.wav                  # 背景音乐
    ├── tts_indextts/                   # IndexTTS 输出
    │   ├── <stem>_<index>_tts.wav
    │   └── ...
    ├── tts_gptsovits/                  # GPT-SoVITS 输出
    │   ├── <stem>_<index>_tts.wav
    │   └── ...
    └── merge/                          # 最终输出
        ├── <stem>_dubbed.mp4           # 配音视频
        └── <stem>_dubbed_subtitled.mp4 # 带字幕配音视频
```

注意：整个 output/ 目录都被 .gitignore 排除

## 配置文件

### 用户配置

- `.env` - 环境变量和 API 密钥（gitignored）
- `transvox_config.json` - 用户偏好配置（gitignored）
- `.env_template` - 环境变量模板（提交到 Git）
- `transvox_config.json.example` - 配置示例（提交到 Git）

### 项目配置

- `requirements.txt` - Python 依赖列表
- `.gitignore` - Git 忽略规则
- `CLAUDE.md` - Claude Code 项目指南
- `.claude/` - Claude Code 配置目录

## 关键文件说明

### 后端核心文件

| 文件 | 说明 |
|------|------|
| `api_server.py` | FastAPI 后端服务器，提供 REST API |
| `full_auto_pipeline.py` | 完整自动化流程主脚本 |
| `Scripts/config_manager.py` | 配置管理核心模块 |
| `Scripts/step*.py` | 各个处理步骤的实现 |

### 前端核心文件

| 文件 | 说明 |
|------|------|
| `web/src/app/page.tsx` | 首页 - 视频上传和流程配置 |
| `web/src/app/workspace/page.tsx` | 工作区 - 流程执行和结果查看 |
| `web/src/components/tools/SubtitleSlicer.tsx` | 字幕切片与 TTS 工具 |
| `web/src/store/useAppStore.ts` | 全局状态管理 |
| `web/src/api/services.ts` | API 服务封装 |

### 配置和文档

| 文件 | 说明 |
|------|------|
| `CLAUDE.md` | Claude Code AI 助手项目指南 |
| `README.md` / `README_EN.md` | 项目主文档 |
| `docs/*.md` | 详细使用文档 |

## 模型文件位置

所有模型文件都被 .gitignore 排除，使用 `python Scripts/download_models.py` 下载：

| 模型 | 存储位置 | 大小 |
|------|----------|------|
| MSST-WebUI 人声分离 | `tools/MSST-WebUI/pretrain/` | ~200MB |
| GPT-SoVITS 预训练 | `tools/GPT-SoVITS/GPT_SoVITS/pretrained_models/` | ~1GB |
| IndexTTS-2 | `tools/index-tts/checkpoints/` | ~500MB |
| Whisper 模型 | `tools/whisper-subtitles/models/` | ~1.5GB |

## 临时和缓存目录

以下目录会自动生成，已在 .gitignore 中排除：

```
__pycache__/                  # Python 缓存
venv/                         # Python 虚拟环境
web/node_modules/             # Node.js 依赖
web/.next/                    # Next.js 构建缓存
logs/                         # 日志文件
cache/                        # 缓存目录
*.log                         # 日志文件
```

## Git 版本控制策略

### 包含在版本控制中

- 源代码 (`*.py`, `*.tsx`, `*.ts`, `*.js`)
- 配置模板和示例
- 文档 (`*.md`)
- 脚本和工具
- 小型资源文件 (`*.ttf`, `*.css`)

### 排除在版本控制外

- 用户配置和密钥 (`.env`, `transvox_config.json`)
- 模型文件 (`*.pth`, `*.ckpt`, `*.safetensors`)
- 输入输出文件 (`input/`, `output/`)
- 构建产物 (`__pycache__/`, `.next/`, `dist/`)
- 依赖包 (`venv/`, `node_modules/`)
- 日志和缓存 (`logs/`, `cache/`, `*.log`)

## 开发工作流

### 添加新功能

1. **后端脚本**: 添加到 `Scripts/` 目录
2. **前端组件**: 添加到 `web/src/components/`
3. **API 端点**: 在 `api_server.py` 中添加
4. **文档**: 在 `docs/` 中添加相应文档

### 测试流程

1. 运行环境检查: `python Scripts/check_environment.py`
2. 运行系统测试: `python Scripts/test_system.py`
3. 前端类型检查: `cd web && npm run type-check`
4. 前端 Lint: `cd web && npm run lint`

### 发布前检查

1. 更新 `README.md` 和 `README_EN.md`
2. 确保所有文档是最新的
3. 验证 `.gitignore` 正确排除敏感文件
4. 运行完整测试套件
5. 检查依赖版本是否固定

## 相关资源

- [快速开始指南](./getting-started.md)
- [CLI 使用文档](./cli-usage.md)
- [配置管理指南](./CONFIG_GUIDE.md)
- [前端 README](../web/README.md)
