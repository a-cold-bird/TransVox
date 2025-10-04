#!/usr/bin/env python3
"""
IndexTTS 项目简单打包脚本
将项目和环境打包成压缩包
"""

import os
import shutil
import zipfile
from pathlib import Path
import platform

def create_package():
    """创建 IndexTTS 打包版本"""
    print("🎯 开始打包 IndexTTS 项目...")
    
    # 项目根目录
    project_root = Path(".").resolve()
    package_dir = project_root / "IndexTTS_Portable"
    
    # 清理并创建打包目录
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(exist_ok=True)
    print(f"✅ 创建打包目录: {package_dir}")
    
    # 需要复制的文件和目录
    files_to_copy = [
        "indextts/",
        "webui.py", 
        "pyproject.toml",
        "uv.lock",
        "requirements.txt",
        "setup.py",
        "README.md",
        "LICENSE",
        "INDEX_MODEL_LICENSE_EN.txt",
        "INDEX_MODEL_LICENSE_ZH.txt",
        "examples/",
        "assets/",
        "tools/",
        "prompts/",
        "outputs/",
        "tests/",
        "checkpoints/",
        "workenv/",  # 包含虚拟环境
    ]
    
    # 复制文件
    for item in files_to_copy:
        src = project_root / item
        if src.exists():
            if src.is_dir():
                shutil.copytree(src, package_dir / item, dirs_exist_ok=True)
            else:
                shutil.copy2(src, package_dir / item)
            print(f"✅ 复制: {item}")
        else:
            print(f"⚠️  跳过不存在的文件: {item}")
    
    # 创建启动脚本
    create_launch_scripts(package_dir)
    
    # 创建说明文档
    create_readme(package_dir)
    
    # 创建压缩包
    create_zip_package(package_dir)
    
    print(f"\n🎉 打包完成！")
    print(f"📁 打包目录: {package_dir}")
    print(f"📦 压缩包: {package_dir}.zip")

def create_launch_scripts(target_dir):
    """创建启动脚本"""
    # Windows 批处理脚本
    windows_script = target_dir / "启动IndexTTS.bat"
    with open(windows_script, 'w', encoding='utf-8') as f:
        f.write("""@echo off
chcp 65001 >nul
title IndexTTS WebUI
echo.
echo ========================================
echo           IndexTTS WebUI 启动器
echo ========================================
echo.

REM 检查 Python 环境
if exist "workenv\\Scripts\\python.exe" (
    echo 使用内置 Python 环境...
    workenv\\Scripts\\python.exe webui.py %*
) else (
    echo 使用系统 Python 环境...
    python webui.py %*
)

echo.
echo 按任意键退出...
pause >nul
""")
    
    # Linux/Mac shell 脚本
    linux_script = target_dir / "启动IndexTTS.sh"
    with open(linux_script, 'w', encoding='utf-8') as f:
        f.write("""#!/bin/bash
echo "========================================"
echo "          IndexTTS WebUI 启动器"
echo "========================================"
echo

# 检查 Python 环境
if [ -f "workenv/bin/python" ]; then
    echo "使用内置 Python 环境..."
    workenv/bin/python webui.py "$@"
else
    echo "使用系统 Python 环境..."
    python webui.py "$@"
fi
""")
    
    # 设置执行权限
    if platform.system() != "Windows":
        os.chmod(linux_script, 0o755)
    
    print("✅ 创建启动脚本")

def create_readme(target_dir):
    """创建说明文档"""
    readme_content = """# IndexTTS 便携版

## 系统要求
- Windows 10/11 或 Linux/Mac
- 至少 8GB 内存
- 支持 CUDA 的显卡（推荐，CPU 也可运行但较慢）

## 使用方法

### Windows 用户
1. 解压到任意目录
2. 双击运行 `启动IndexTTS.bat`
3. 等待程序启动完成
4. 在浏览器中打开 http://localhost:7860

### Linux/Mac 用户
1. 解压到任意目录
2. 运行 `./启动IndexTTS.sh`
3. 等待程序启动完成
4. 在浏览器中打开 http://localhost:7860

## 注意事项
- 首次运行会自动下载必要的模型文件（约 2-3GB）
- 确保网络连接正常
- 如遇到问题，请查看控制台输出信息
- 如果系统没有 Python，程序会使用内置的 Python 环境

## 文件说明
- `checkpoints/`: 模型文件目录
- `examples/`: 示例音频文件
- `outputs/`: 生成的音频输出目录
- `prompts/`: 用户上传的音频文件目录
- `workenv/`: Python 虚拟环境（包含所有依赖）

## 功能特点
- 零配置，解压即用
- 包含完整的 Python 环境和所有依赖
- 支持中英文语音合成
- 支持情感控制和音色克隆
- 提供 Web 界面，操作简单

## 技术支持
如有问题，请访问项目主页：https://github.com/index-tts/index-tts
"""
    
    readme_file = target_dir / "使用说明.md"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("✅ 创建说明文档")

def create_zip_package(source_dir):
    """创建 ZIP 压缩包"""
    zip_path = source_dir.with_suffix('.zip')
    
    print(f"📦 正在创建压缩包: {zip_path}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = Path(root) / file
                arc_path = file_path.relative_to(source_dir.parent)
                zipf.write(file_path, arc_path)
    
    # 计算文件大小
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"✅ 压缩包创建完成: {zip_path} ({size_mb:.1f} MB)")

if __name__ == "__main__":
    create_package()
