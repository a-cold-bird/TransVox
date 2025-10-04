#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的 WhisperX 转录脚本
使用 faster-whisper large-v3 模型进行语音识别
支持说话人识别（pyannote）
"""

import os
import sys
import argparse
import logging
import subprocess
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _load_dotenv_into_environ():
    """加载环境变量"""
    try:
        root = Path(__file__).resolve().parent.parent
        dotenv_path = root / '.env'
        if dotenv_path.exists():
            with open(dotenv_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        k, v = line.split('=', 1)
                        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            logger.info(f"已从 .env 加载环境变量: {dotenv_path}")
    except Exception as e:
        logger.warning(f"加载 .env 失败: {e}")

_load_dotenv_into_environ()


def transcribe_audio(
    audio_path: Path,
    output_path: Path,
    language: str = 'auto',
    model: str = 'large-v3',
    diarize: bool = True,
    device: str = 'cuda'
) -> Path:
    """
    使用 WhisperX 转录音频
    
    Args:
        audio_path: 音频文件路径
        output_path: 输出 SRT 路径（不含扩展名）
        language: 语言代码（auto/zh/en/ja/ko）
        model: Whisper 模型大小
        diarize: 是否启用说话人识别
        device: 设备（cuda/cpu）
    
    Returns:
        生成的 SRT 文件路径
    """
    logger.info("[启动] WhisperX 转录")
    logger.info(f"  音频: {audio_path}")
    logger.info(f"  模型: {model}")
    logger.info(f"  语言: {language}")
    logger.info(f"  说话人识别: {'启用' if diarize else '禁用'}")
    
    # 构建命令
    cmd = [
        sys.executable,
        'tools/whisper-subtitles/faster_whisper_subtitle_generator.py',
        str(audio_path),
        '-l', language,
        '--device', device,
        '--no-vad',
        '-m', model,
        '-o', str(output_path)
    ]
    
    if diarize:
        cmd.append('--diarize')
        hf_token = os.getenv('HUGGINGFACE_TOKEN')
        if hf_token:
            cmd.extend(['--hf-token', hf_token])
        else:
            logger.warning("[!] HUGGINGFACE_TOKEN 未设置，说话人识别可能失败")
    
    # 执行转录
    try:
        subprocess.run(cmd, check=True)
        
        # 检查输出
        srt_file = Path(f"{output_path}.srt")
        if srt_file.exists():
            logger.info(f"[完成] 转录成功: {srt_file}")
            return srt_file
        else:
            raise FileNotFoundError(f"转录失败，未生成 SRT: {srt_file}")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"[X] WhisperX 执行失败: {e}")
        raise
    except Exception as e:
        logger.error(f"[X] 转录异常: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description='WhisperX 音频转录工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 基本用法
  python transcribe_whisperx.py input.wav -o output
  
  # 指定语言
  python transcribe_whisperx.py input.wav -o output -l zh
  
  # 禁用说话人识别
  python transcribe_whisperx.py input.wav -o output --no-diarize
  
  # 使用不同模型
  python transcribe_whisperx.py input.wav -o output -m base
        """
    )
    
    parser.add_argument('audio', help='输入音频文件路径（wav/mp3/m4a 等）')
    parser.add_argument('-o', '--output', required=True, help='输出 SRT 文件路径（不含 .srt 扩展名）')
    parser.add_argument('-l', '--language', default='auto',
                       help='语言代码（auto/zh/en/ja/ko，默认: auto）')
    parser.add_argument('-m', '--model', default='large-v3',
                       choices=['tiny', 'base', 'small', 'medium', 'large-v2', 'large-v3'],
                       help='Whisper 模型大小（默认: large-v3）')
    parser.add_argument('--no-diarize', action='store_true',
                       help='禁用说话人识别')
    parser.add_argument('--device', default='cuda', choices=['cuda', 'cpu'],
                       help='设备（默认: cuda）')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='显示详细日志')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        audio_path = Path(args.audio).resolve()
        output_path = Path(args.output).resolve()
        
        if not audio_path.exists():
            logger.error(f"[X] 音频文件不存在: {audio_path}")
            return 1
        
        # 创建输出目录
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 执行转录
        srt_file = transcribe_audio(
            audio_path=audio_path,
            output_path=output_path,
            language=args.language,
            model=args.model,
            diarize=not args.no_diarize,
            device=args.device
        )
        
        print(f"\n[完成] 转录成功！")
        print(f"[输出] {srt_file}")
        
        # 显示统计
        with open(srt_file, 'r', encoding='utf-8') as f:
            content = f.read()
            import srt
            subs = list(srt.parse(content))
            print(f"[统计] 共 {len(subs)} 条字幕")
            if subs:
                duration = (subs[-1].end - subs[0].start).total_seconds()
                print(f"[时长] {duration:.1f} 秒")
        
        return 0
        
    except Exception as e:
        logger.error(f"[X] 转录失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
