# TransVox 快速开始指南

[English](./getting-started_en.md) | 简体中文

本指南将帮助你快速安装、配置和运行 TransVox。

## 目录

- [环境要求](#环境要求)
- [安装步骤](#安装步骤)
- [启动服务](#启动服务)
- [快速使用](#快速使用)
- [故障排查](#故障排查)

---

## 环境要求

### 硬件要求

- **GPU：** NVIDIA GPU（推荐 2080Ti 及以上）
- **显存：** 至少 8GB（推荐 11GB+）
- **硬盘：** 至少 20GB 可用空间（用于模型和临时文件）

### 软件要求

- **操作系统：** Windows 10/11 或 Linux
- **Python：** 3.10（推荐）
- **CUDA：** 12.8（与 PyTorch 版本匹配）
- **FFmpeg：** 已安装并在 PATH 中可用

---

## 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/a-cold-bird/TransVox.git
cd TransVox
```

### 2. 创建虚拟环境

**Windows：**

```powershell
python -m venv venv
venv\Scripts\activate
```

**Linux：**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

**Windows：**

```powershell
python -m pip install --upgrade pip

# 安装 PyTorch（CUDA 12.8）
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu128

# 安装项目依赖
pip install -r requirements.txt

# 安装 IndexTTS
pip install -e tools/index-tts

# 下载 NLTK 数据（GPT-SoVITS 英文处理需要）
python download_nltk_data.py
```

**Linux：**

```bash
pip install --upgrade pip

# 安装 PyTorch（CUDA）
pip3 install torch torchvision

# 安装项目依赖
pip install -r requirements.txt

# 安装 IndexTTS
pip install -e tools/index-tts

# 下载 NLTK 数据
python download_nltk_data.py

# 安装 ffmpeg（若未安装）
sudo apt-get update && sudo apt-get install -y ffmpeg
```

### 4. 安装 FFmpeg（如未安装）

**Windows：**

```powershell
# 使用 Scoop
scoop install ffmpeg

# 或使用 Chocolatey
choco install ffmpeg
```

**Linux：**

```bash
sudo apt-get install ffmpeg
```

### 5. 下载必需模型

运行自动下载脚本：

```bash
python download_models.py
```

脚本会自动下载：
- MSST-WebUI 人声分离模型
- GPT-SoVITS 预训练模型
- IndexTTS-2 预训练模型

> **提示：国内用户加速** 在 `.env` 中添加 `HF_ENDPOINT=https://hf-mirror.com`

### 6. 配置 API Key

复制 `.env_template` 为 `.env`：

```bash
cp .env_template .env
```

编辑 `.env` 文件，添加以下配置：

```bash
# Gemini API Key（字幕翻译）
GEMINI_API_KEY=your_gemini_api_key

# Hugging Face Token（说话人识别）
HUGGINGFACE_TOKEN=your_huggingface_token

# 可选：国内用户加速
HF_ENDPOINT=https://hf-mirror.com
```

**获取 API Key 的方法：**

1. **Gemini API Key：**
   - 访问 [Google AI Studio](https://aistudio.google.com/)
   - 创建 API Key

2. **Hugging Face Token：**
   - 登录 [Hugging Face](https://huggingface.co/)
   - 进入 Settings → Access Tokens
   - 创建 Token，勾选 "Read access to contents of selected repos"
   - 选择并同意以下仓库的使用条款：
     - [`pyannote/speaker-diarization-3.1`](https://huggingface.co/pyannote/speaker-diarization-3.1)
     - [`pyannote/segmentation-3.0`](https://huggingface.co/pyannote/segmentation-3.0)

### 7. 验证安装

运行环境检测脚本：

```bash
python check_environment.py
```

脚本会检查：
- ✅ GPU 和 CUDA 是否可用
- ✅ FFmpeg 是否安装
- ✅ Python 依赖是否完整
- ✅ 模型是否下载
- ✅ 环境变量是否配置

如果所有检查都通过，说明安装成功！

---

## 启动服务

TransVox 提供两种使用方式：CLI 命令行工具和 Web 界面。

### 方式一：CLI 命令行工具（推荐）

直接使用命令行工具，无需启动服务：

```bash
python full_auto_pipeline.py input/your_video.mp4 --target_lang zh
```

详细使用方法请参考 [CLI 使用指南](./cli-usage.md)。

### 方式二：Web 界面

如需使用 Web 界面，需要启动后端和前端服务。

#### 使用一键启动脚本（推荐）

**Windows：**

```powershell
# 启动所有服务
.\start.bat

# 或分别启动
.\start-backend.bat   # 启动后端
.\start-frontend.bat  # 启动前端
```

**Linux：**

```bash
# 启动所有服务
./start.sh

# 或分别启动
./start-backend.sh   # 启动后端
./start-frontend.sh  # 启动前端
```

#### 手动启动

**1. 启动后端服务**

在第一个终端窗口：

```bash
# Windows
cd F:\SHIRO_Object\TransVox
venv\Scripts\activate
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload

# Linux
cd /path/to/TransVox
source venv/bin/activate
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

**等待看到：** `Uvicorn running on http://0.0.0.0:8000`

**2. 启动前端服务**

在第二个终端窗口：

```bash
cd web
npm run dev
```

**等待看到：** `Ready in X.Xs`

**3. 访问服务**

- **前端界面：** http://localhost:3000
- **后端 API 文档：** http://localhost:8000/docs

---

## 快速使用

### CLI 快速开始

1. 将视频文件放到 `input/` 目录

2. 运行全自动流程：

```bash
# 英文视频翻译为中文
python full_auto_pipeline.py input/EN_test.mp4 --target_lang zh

# 中文视频翻译为英文
python full_auto_pipeline.py input/ZH_test.mp4 --target_lang en
```

3. 查看结果：

输出文件在 `output/<视频名>/merge/` 目录：
- `<视频名>_dubbed.mp4` - 配音视频

### Web 界面快速开始

1. 访问 http://localhost:3000

2. 点击"工作空间"

3. 上传视频文件

4. 选择目标语言和 TTS 引擎

5. 点击"开始处理"

6. 等待处理完成，下载结果

---

## 故障排查

### 后端启动问题

#### 问题 1：后端启动卡住不动

**可能原因：**
- 正在导入大型库（第一次很慢）
- 检查 CUDA/GPU
- 加载模型权重

**解决方案：**
1. 耐心等待 30-60 秒
2. 查看是否有错误输出
3. 检查 Python 进程是否在运行
4. 检查 CPU/内存使用情况

#### 问题 2：CUDA 不可用

**检查 CUDA 版本：**

```bash
nvidia-smi  # 查看 CUDA 版本
python -c "import torch; print(torch.cuda.is_available())"
```

**解决方案：**
- 确保安装的 PyTorch 版本与系统 CUDA 版本匹配
- 重新安装 PyTorch：

```bash
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu128
```

#### 问题 3：端口被占用

```bash
# Windows
netstat -ano | findstr :8000

# Linux
lsof -i :8000
```

**解决方案：**
- 修改启动端口：`uvicorn api_server:app --port 8001`

### 前端启动问题

#### 问题 1：npm 安装失败

```bash
cd web
rm -rf node_modules package-lock.json
npm install
```

#### 问题 2：前端无法连接后端

**检查：**
1. 后端是否在 http://localhost:8000 运行
2. `web/.env.local` 中的 `NEXT_PUBLIC_API_URL` 是否正确
3. 浏览器控制台错误

### CLI 使用问题

#### 问题 1：模型未找到

```bash
python download_models.py
```

#### 问题 2：API Key 错误

检查 `.env` 文件中的配置是否正确：

```bash
# 查看配置
cat .env

# 或在 Python 中验证
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('GEMINI_API_KEY'))"
```

#### 问题 3：FFmpeg 未找到

```bash
# 检查 FFmpeg 是否安装
ffmpeg -version

# Windows
where ffmpeg

# Linux
which ffmpeg
```

如未安装，参考上文"安装 FFmpeg"部分。

### 显存不足

**推荐配置：** 2080Ti 及以上（11GB 显存）

**解决方案：**
1. 使用 GPT-SoVITS 替代 IndexTTS（显存占用更小）
2. 优先选择 `whisperx` 作为转录引擎
3. 禁用人声分离：`--no-separation`
4. 禁用说话人识别：`--no-diarization`

### 结果不理想

**字幕时间轴不准：**
- 使用 Aegisub 手动校正字幕时间轴

**翻译不准确：**
- 手动编辑 `.translated.srt` 文件
- 使用专业翻译工具

**语音不自然：**
- 检查原视频音质
- 尝试更换 TTS 引擎
- 确保原视频人声清晰

---

## 下一步

- [CLI 使用指南](./cli-usage.md) - 详细的命令行使用说明
- [配置管理指南](./CONFIG_GUIDE.md) - 用户配置和翻译引擎设置
- [项目主页](https://github.com/a-cold-bird/TransVox) - 项目源码和更新

---

## 获取帮助

如果遇到问题：

1. 搜索 [GitHub Issues](https://github.com/a-cold-bird/TransVox/issues)
2. 提交新的 Issue
3. 加入讨论 [GitHub Discussions](https://github.com/a-cold-bird/TransVox/discussions)

---

**祝你使用愉快！**
