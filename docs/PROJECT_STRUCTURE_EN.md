# TransVox Project Structure

This document describes the directory structure and key files of the TransVox project.

## Project Root

```
TransVox/
├── api_server.py              # FastAPI backend server
├── full_auto_pipeline.py      # Fully automated pipeline main script
├── stepA_prepare_and_blank_srt.py    # Step A: Preprocessing & transcription
├── stepB_index_pipeline.py    # Step B: IndexTTS pipeline
├── stepB_gptsovits_pipeline.py # Step B: GPT-SoVITS pipeline
├── stepC_embed_subtitles.py   # Step C: Embed subtitles
├── requirements.txt           # Python dependencies
├── transvox_config.json.example # Configuration example
├── .env_template              # Environment variables template
├── start.bat                  # Windows one-click startup script
└── start.sh                   # Linux one-click startup script
```

## Core Directories

### Scripts/ - Script Directory

Contains all sub-step scripts and utility scripts:

```
Scripts/
├── step1_separate_audio_video.py    # Separate audio and video
├── step2_separate_vocals.py         # Vocal separation
├── step3_transcribe_whisperx.py     # WhisperX transcription
├── step4_translate_srt.py           # Subtitle translation
├── step6_tts_indextts2.py          # IndexTTS speech synthesis
├── step6_tts_gptsovits.py          # GPT-SoVITS speech synthesis
├── step7_merge_tts_and_mux.py      # Merge audio
├── step9_embed_to_video.py         # Embed subtitles to video
├── download_models.py              # Model download script
├── download_nltk_data.py           # NLTK data download
├── check_environment.py            # Environment check
├── config_manager.py               # Configuration manager
├── config_tool.py                  # Configuration CLI tool
├── fix_translated_srt.py           # Fix translated subtitles
├── step_clean_output.py            # Clean output directory
└── test_system.py                  # System test
```

### web/ - Frontend Directory

Modern web interface built with Next.js + TypeScript:

```
web/
├── src/
│   ├── app/                   # Next.js App Router
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Homepage
│   │   ├── workspace/         # Workspace pages
│   │   ├── tools/             # Toolbox pages
│   │   └── globals.css        # Global styles
│   ├── components/            # React components
│   │   ├── ui/               # Base UI components (Radix UI)
│   │   ├── video/            # Video-related components
│   │   ├── pipeline/         # Pipeline components
│   │   └── tools/            # Toolbox components
│   ├── lib/                  # Utility functions
│   ├── api/                  # API client
│   ├── store/                # Zustand state management
│   ├── types/                # TypeScript type definitions
│   └── pages/                # Documentation pages (Nextra)
├── public/                   # Static assets
├── next.config.js            # Next.js configuration
├── tailwind.config.ts        # Tailwind CSS configuration
├── tsconfig.json             # TypeScript configuration
└── package.json              # Frontend dependencies
```

### tools/ - AI Model Tools Directory

Integrated third-party AI models and tools:

```
tools/
├── MSST-WebUI/               # Vocal separation tool
│   ├── pretrain/             # Pretrained models (gitignored)
│   ├── results/              # Separation results (gitignored)
│   └── start_seprate.bat     # Windows startup script
│
├── GPT-SoVITS/               # GPT-SoVITS TTS engine
│   ├── GPT_SoVITS/
│   │   ├── configs/          # Configuration files
│   │   │   └── tts_infer.yaml
│   │   └── pretrained_models/ # Pretrained models (gitignored)
│   └── api_v2.py             # API service
│
├── index-tts/                # IndexTTS-2 engine
│   ├── checkpoints/          # Model checkpoints (gitignored)
│   ├── indextts/             # Core code
│   └── setup.py              # Installation configuration
│
└── whisper-subtitles/        # Whisper subtitle tools
    ├── faster_whisper_subtitle_generator.py
    └── models/               # Whisper models (gitignored)
```

### docs/ - Documentation Directory

Project documentation and guides:

```
docs/
├── getting-started.md        # Quick start guide
├── cli-usage.md              # CLI usage documentation
├── CONFIG_GUIDE.md           # Configuration management guide
├── PROJECT_STRUCTURE.md      # Chinese version of this doc
├── PROJECT_STRUCTURE_EN.md   # This document
└── CONCURRENCY_REPORT.md     # Concurrency processing report
```

## Input/Output Directories

### input/ - Input Directory

Store videos to be processed:

```
input/
├── video1.mp4
├── video2.mp4
└── .gitkeep                  # Git placeholder file
```

Note: Video files are not committed to Git (excluded in .gitignore)

### output/ - Output Directory

Automatically generated processing results, organized by video stem:

```
output/
└── <video_stem>/
    ├── <stem>.srt                      # Original subtitles
    ├── <stem>.translated.srt           # Translated subtitles
    ├── <stem>_video_only.mp4           # Video without audio
    ├── <stem>_audio.wav                # Original audio
    ├── <stem>_speak.wav                # Separated vocals
    ├── <stem>_bgm.wav                  # Background music
    ├── tts_indextts/                   # IndexTTS output
    │   ├── <stem>_<index>_tts.wav
    │   └── ...
    ├── tts_gptsovits/                  # GPT-SoVITS output
    │   ├── <stem>_<index>_tts.wav
    │   └── ...
    └── merge/                          # Final output
        ├── <stem>_dubbed.mp4           # Dubbed video
        └── <stem>_dubbed_subtitled.mp4 # Dubbed video with subtitles
```

Note: The entire output/ directory is excluded by .gitignore

## Configuration Files

### User Configuration

- `.env` - Environment variables and API keys (gitignored)
- `transvox_config.json` - User preference configuration (gitignored)
- `.env_template` - Environment variables template (committed to Git)
- `transvox_config.json.example` - Configuration example (committed to Git)

### Project Configuration

- `requirements.txt` - Python dependency list
- `.gitignore` - Git ignore rules
- `CLAUDE.md` - Claude Code project guide
- `.claude/` - Claude Code configuration directory

## Key File Descriptions

### Backend Core Files

| File | Description |
|------|-------------|
| `api_server.py` | FastAPI backend server, provides REST API |
| `full_auto_pipeline.py` | Complete automated pipeline main script |
| `Scripts/config_manager.py` | Configuration management core module |
| `Scripts/step*.py` | Implementation of each processing step |

### Frontend Core Files

| File | Description |
|------|-------------|
| `web/src/app/page.tsx` | Homepage - video upload and pipeline configuration |
| `web/src/app/workspace/page.tsx` | Workspace - pipeline execution and result viewing |
| `web/src/components/tools/SubtitleSlicer.tsx` | Subtitle slicing and TTS tool |
| `web/src/store/useAppStore.ts` | Global state management |
| `web/src/api/services.ts` | API service wrapper |

### Configuration and Documentation

| File | Description |
|------|-------------|
| `CLAUDE.md` | Claude Code AI assistant project guide |
| `README.md` / `README_EN.md` | Project main documentation |
| `docs/*.md` | Detailed usage documentation |

## Model File Locations

All model files are excluded by .gitignore, download using `python Scripts/download_models.py`:

| Model | Storage Location | Size |
|-------|------------------|------|
| MSST-WebUI vocal separation | `tools/MSST-WebUI/pretrain/` | ~200MB |
| GPT-SoVITS pretrained | `tools/GPT-SoVITS/GPT_SoVITS/pretrained_models/` | ~1GB |
| IndexTTS-2 | `tools/index-tts/checkpoints/` | ~500MB |
| Whisper models | `tools/whisper-subtitles/models/` | ~1.5GB |

## Temporary and Cache Directories

The following directories are automatically generated and excluded in .gitignore:

```
__pycache__/                  # Python cache
venv/                         # Python virtual environment
web/node_modules/             # Node.js dependencies
web/.next/                    # Next.js build cache
logs/                         # Log files
cache/                        # Cache directory
*.log                         # Log files
```

## Git Version Control Strategy

### Included in Version Control

- Source code (`*.py`, `*.tsx`, `*.ts`, `*.js`)
- Configuration templates and examples
- Documentation (`*.md`)
- Scripts and tools
- Small resource files (`*.ttf`, `*.css`)

### Excluded from Version Control

- User configuration and keys (`.env`, `transvox_config.json`)
- Model files (`*.pth`, `*.ckpt`, `*.safetensors`)
- Input/output files (`input/`, `output/`)
- Build artifacts (`__pycache__/`, `.next/`, `dist/`)
- Dependency packages (`venv/`, `node_modules/`)
- Logs and cache (`logs/`, `cache/`, `*.log`)

## Development Workflow

### Adding New Features

1. **Backend scripts**: Add to `Scripts/` directory
2. **Frontend components**: Add to `web/src/components/`
3. **API endpoints**: Add in `api_server.py`
4. **Documentation**: Add corresponding docs in `docs/`

### Testing Process

1. Run environment check: `python Scripts/check_environment.py`
2. Run system tests: `python Scripts/test_system.py`
3. Frontend type check: `cd web && npm run type-check`
4. Frontend lint: `cd web && npm run lint`

### Pre-release Checklist

1. Update `README.md` and `README_EN.md`
2. Ensure all documentation is up-to-date
3. Verify `.gitignore` correctly excludes sensitive files
4. Run complete test suite
5. Check that dependency versions are pinned

## Related Resources

- [Getting Started Guide](./getting-started.md)
- [CLI Usage Documentation](./cli-usage.md)
- [Configuration Guide](./CONFIG_GUIDE.md)
- [Frontend README](../web/README.md)
