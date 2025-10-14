#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤1: 音视频分离
从视频文件中分离出视频流和音频流
"""

import os
import sys
import argparse
import subprocess
import logging
from pathlib import Path

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


def separate_audio_video(input_video: str, output_dir: str = None) -> tuple:
    """
    音视频分离
    
    Args:
        input_video: 输入视频文件路径
        output_dir: 输出目录，如果为None则自动创建
    
    Returns:
        (video_only_path, full_audio_path): 分离后的视频和音频文件路径
    """
    input_video = Path(input_video)
    
    if not input_video.exists():
        raise FileNotFoundError(f"输入视频文件不存在: {input_video}")
    
    # 设置输出目录
    if output_dir is None:
        output_dir = Path("output") / input_video.stem
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 设置输出文件路径
    base_name = input_video.stem
    video_only_path = output_dir / f"{base_name}_video_only.mp4"
    full_audio_path = output_dir / f"{base_name}_full_audio.wav"
    
    logger.info(f"开始分离音视频: {input_video}")
    logger.info(f"输出目录: {output_dir}")
    
    try:
        # 分离视频流（无声视频）
        logger.info("正在分离视频流...")
        cmd_video = [
            "ffmpeg", "-i", str(input_video),
            "-an", "-c:v", "copy",
            "-y", str(video_only_path)
        ]
        result = subprocess.run(cmd_video, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        logger.info(f"视频流分离完成: {video_only_path}")
        
        # 分离音频流
        logger.info("正在分离音频流...")
        cmd_audio = [
            "ffmpeg", "-i", str(input_video),
            "-vn", "-acodec", "pcm_s16le", "-ar", "44100",
            "-y", str(full_audio_path)
        ]
        try:
            result = subprocess.run(cmd_audio, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
            logger.info(f"音频流分离完成: {full_audio_path}")
        except subprocess.CalledProcessError as e:
            # 检查是否是因为没有音频流导致的失败
            if "Output file #0 does not contain any stream" in e.stderr or "does not contain any stream" in e.stderr:
                logger.warning("[警告] 视频文件没有音频流，跳过音频提取")
                logger.warning("[提示] 创建空的音频文件以保持兼容性")

                # 创建一个最小的静音音频文件
                import struct

                # WAV文件头 + 1秒静音数据 (44100 Hz, 16-bit, mono)
                sample_rate = 44100
                duration = 1.0  # 1秒
                num_samples = int(sample_rate * duration)

                # WAV文件头 (44字节)
                wav_header = struct.pack('<4sL4s4sLHHLLHH4sL',
                    b'RIFF',              # RIFF标识
                    36 + num_samples * 2, # 文件大小
                    b'WAVE',              # WAVE标识
                    b'fmt ',              # fmt子块
                    16,                   # fmt块大小
                    1,                    # PCM格式
                    1,                    # 单声道
                    sample_rate,          # 采样率
                    sample_rate * 2,      # 字节率
                    2,                    # 块对齐
                    16,                   # 位深度
                    b'data',              # data子块
                    num_samples * 2       # 数据大小
                )

                # 1秒的静音数据 (16位样本，全部为0)
                silence_data = b'\x00\x00' * num_samples

                # 写入WAV文件
                with open(full_audio_path, 'wb') as f:
                    f.write(wav_header)
                    f.write(silence_data)

                logger.info(f"[静音] 已创建静音音频文件: {full_audio_path}")
            else:
                # 其他类型的错误，重新抛出
                raise
        
        # 检查输出文件
        if not video_only_path.exists():
            raise Exception(f"视频文件生成失败: {video_only_path}")
        if not full_audio_path.exists():
            raise Exception(f"音频文件生成失败: {full_audio_path}")
        
        logger.info("[成功] 音视频分离完成!")
        return str(video_only_path), str(full_audio_path)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg执行失败: {e}")
        if e.stderr:
            logger.error(f"错误输出: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"音视频分离失败: {e}")
        raise


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="音视频分离工具")
    parser.add_argument("input_video", help="输入视频文件路径")
    parser.add_argument("-o", "--output", help="输出目录路径（可选）")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细日志")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        video_path, audio_path = separate_audio_video(args.input_video, args.output)
        
        print(f"\n[成功] 音视频分离成功!")
        print(f"[输出] 视频文件: {video_path}")
        print(f"[输出] 音频文件: {audio_path}")
        
        # 显示文件信息
        video_size = Path(video_path).stat().st_size / (1024*1024)
        audio_size = Path(audio_path).stat().st_size / (1024*1024)
        print(f"\n[信息] 文件信息:")
        print(f"视频大小: {video_size:.1f} MB")
        print(f"音频大小: {audio_size:.1f} MB")
        
    except Exception as e:
        logger.error(f"处理失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
