#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤2: 人声与背景音分离
使用MSST工具分离人声和背景音
"""

import os
import sys
import shutil
import argparse
import subprocess
import logging
from pathlib import Path
from pydub import AudioSegment

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def _load_dotenv_into_environ():
    try:
        root = Path(__file__).resolve().parent
        dotenv_path = (root / '.env') if (root / '.env').exists() else (root.parent / '.env')
        if dotenv_path.exists():
            with open(dotenv_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        k, v = line.split('=', 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        os.environ.setdefault(k, v)
            logger.info(f"已从 .env 加载环境变量: {dotenv_path}")
    except Exception as e:
        logger.warning(f"加载 .env 失败: {e}")

_load_dotenv_into_environ()


def separate_vocals(full_audio_path: str, output_dir: str = None) -> tuple:
    """
    人声与背景音分离
    
    Args:
        full_audio_path: 完整音频文件路径
        output_dir: 输出目录，如果为None则使用音频文件所在目录
    
    Returns:
        (speak_path, instru_path): 人声和背景音文件路径
    """
    full_audio_path = Path(full_audio_path)
    
    if not full_audio_path.exists():
        raise FileNotFoundError(f"音频文件不存在: {full_audio_path}")
    
    # 设置输出目录
    if output_dir is None:
        output_dir = full_audio_path.parent
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取基础文件名
    base_name = full_audio_path.stem.replace('_full_audio', '')
    
    logger.info(f"开始分离人声和背景音: {full_audio_path}")
    logger.info(f"输出目录: {output_dir}")
    
    # 准备MSST输入目录
    msst_input_dir = Path("tools/MSST-WebUI/input")
    msst_results_dir = Path("tools/MSST-WebUI/results")
    
    # 清空输入和结果目录
    if msst_input_dir.exists():
        shutil.rmtree(msst_input_dir)
    if msst_results_dir.exists():
        shutil.rmtree(msst_results_dir)
    
    msst_input_dir.mkdir(exist_ok=True)
    msst_results_dir.mkdir(exist_ok=True)
    
    # 复制音频到MSST输入目录
    input_audio_name = f"{base_name}_full_audio.wav"
    shutil.copy2(full_audio_path, msst_input_dir / input_audio_name)
    logger.info(f"音频文件已复制到MSST输入目录: {input_audio_name}")
    
    try:
        # 使用当前Python环境，而不是硬编码路径
        venv_python = sys.executable
        
        # 执行MSST分离
        logger.info("正在执行MSST人声分离...")
        cmd = [
            venv_python, "scripts/preset_infer_cli.py",
            "-p", "./presets/preset.json",
            "-i", "input/",
            "-o", "results/",
            "-f", "wav",
            "--extra_output_dir"
        ]
        
        # 切换到MSST目录执行
        original_cwd = os.getcwd()
        os.chdir("tools/MSST-WebUI")
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        logger.info("MSST分离执行完成")
        
        os.chdir(original_cwd)
        
        # 根据MSST的固定命名规则查找分离结果文件
        base_audio_name = input_audio_name.replace('.wav', '')

        # 人声文件：经过三步处理后的最终人声（去混响）
        vocals_file = msst_results_dir / f"{base_audio_name}_vocals_karaoke_noreverb.wav"

        # 背景音与和声文件：在 extra_output 目录中
        extra_dir = msst_results_dir / "extra_output"
        instru_file = extra_dir / f"{base_audio_name}_other.wav"              # 背景音（需要保留）
        harmony_file = extra_dir / f"{base_audio_name}_vocals_other.wav"      # 和声（不需要）

        logger.info(f"查找人声文件: {vocals_file}")
        logger.info(f"查找背景音文件(来自 extra_output): {instru_file}")
        logger.info(f"查找和声文件(来自 extra_output): {harmony_file}")
        
        # 复制结果到输出目录
        speak_path = output_dir / f"{base_name}_speak.wav"
        instru_path = output_dir / f"{base_name}_instru.wav"
        
        if vocals_file and vocals_file.exists():
            shutil.copy2(vocals_file, speak_path)
            logger.info(f"人声文件已保存: {speak_path}")
        else:
            # 如果没有人声文件，使用原始音频
            shutil.copy2(full_audio_path, speak_path)
            logger.warning("未找到人声文件，使用原始音频")
        
        if instru_file and instru_file.exists():
            shutil.copy2(instru_file, instru_path)
            logger.info(f"背景音文件已保存: {instru_path}")
        else:
            # 创建静音背景音
            audio = AudioSegment.from_wav(full_audio_path)
            silent = AudioSegment.silent(duration=len(audio))
            silent.export(instru_path, format="wav")
            logger.warning("未找到背景音文件，创建静音文件")
        
        # 检查输出文件
        if not speak_path.exists():
            raise Exception(f"人声文件生成失败: {speak_path}")
        if not instru_path.exists():
            raise Exception(f"背景音文件生成失败: {instru_path}")
        
        logger.info("[成功] 人声与背景音分离完成!")
        return str(speak_path), str(instru_path)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"MSST执行失败: {e}")
        if e.stderr:
            logger.error(f"错误输出: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"人声分离失败: {e}")
        raise
    finally:
        # 清理临时文件
        if msst_input_dir.exists():
            shutil.rmtree(msst_input_dir)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="人声与背景音分离工具")
    parser.add_argument("input_audio", help="输入音频文件路径")
    parser.add_argument("-o", "--output", help="输出目录路径（可选）")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细日志")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        speak_path, instru_path = separate_vocals(args.input_audio, args.output)
        
        print(f"\n[成功] 人声与背景音分离成功!")
        print(f"[输出] 人声文件: {speak_path}")
        print(f"[输出] 背景音文件: {instru_path}")
        
        # 显示文件信息
        speak_size = Path(speak_path).stat().st_size / (1024*1024)
        instru_size = Path(instru_path).stat().st_size / (1024*1024)
        print(f"\n[信息] 文件信息:")
        print(f"人声大小: {speak_size:.1f} MB")
        print(f"背景音大小: {instru_size:.1f} MB")
        
    except Exception as e:
        logger.error(f"处理失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
