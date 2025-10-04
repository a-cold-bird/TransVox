#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Part A: 准备阶段
- 步骤1: 音视频分离 (生成 *_video_only.mp4 与 *_full_audio.wav)
- 步骤2: 人声与背景分离 (生成 *_speak.wav 与 *_instru.wav)
- 步骤3: 转写初始 SRT（使用 WhisperX large-v3）
- 生成标准命名的 SRT 模板文件：{video_stem}_merged_optimized.srt 和 {video_stem}.translated.srt

说明:
- 本脚本可选触发整文件翻译（仅翻译，不进行智能合并）。
- 未指定翻译时，行为与以往一致，生成占位文件供后续步骤使用。
"""

import os
import sys
import argparse
import logging
import shutil
import subprocess
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _load_dotenv_into_environ() -> None:
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
                        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            logger.info(f"已从 .env 加载环境变量: {dotenv_path}")
    except Exception as e:
        logger.warning(f"加载 .env 失败: {e}")


def run_step1_and_step2(video_path: Path, output_dir: Path, enable_separation: bool = True) -> None:
    # 使用当前Python环境
    py = sys.executable

    import subprocess

    # 步骤1: 分离音视频
    logger.info('[A-1] 音视频分离')
    cmd1 = [py, 'Scripts/step1_separate_audio_video.py', str(video_path), '-o', str(output_dir)]
    subprocess.run(cmd1, check=True, encoding='utf-8')

    # 步骤2: 人声与背景分离（可跳过）
    full_audio = output_dir / f"{video_path.stem}_full_audio.wav"
    if enable_separation:
        logger.info('[A-2] 人声与背景分离')
        cmd2 = [py, 'Scripts/step2_separate_vocals.py', str(full_audio)]
        subprocess.run(cmd2, check=True, encoding='utf-8')
    else:
        logger.info('[A-2] 已指定跳过人声分离，复制原始音频作为speak与instru占位')
        speak_wav = output_dir / f"{video_path.stem}_speak.wav"
        instru_wav = output_dir / f"{video_path.stem}_instru.wav"
        try:
            shutil.copy2(full_audio, speak_wav)
            # 为保持下游兼容，提供一个占位的instru（使用同一音频），合并阶段可能需手动调整
            shutil.copy2(full_audio, instru_wav)
        except Exception as e:
            logger.error(f'复制占位音频失败: {e}')
            raise


def run_step3_transcribe(speak_wav: Path, output_dir: Path, engine: str = 'whisperx', 
                         language: str = 'auto', diarize: bool = True) -> Path:
    """调用 step3 转录脚本生成初始 SRT"""
    import subprocess
    if not speak_wav.exists():
        raise FileNotFoundError(f"缺少人声音频: {speak_wav}")
    
    logger.info(f'[A-3] WHISPERX 转写初始SRT')
    
    # 调用 step3 转录脚本
    if engine == 'whisperx':
        # 使用whisperx转录
        video_stem = speak_wav.stem.replace('_speak', '')
        temp_output = output_dir / f"{video_stem}_whisperx_temp"
        
        cmd = [
            sys.executable, 'tools/whisper-subtitles/faster_whisper_subtitle_generator.py',
            str(speak_wav),
            '-l', language,
            '--device', 'cuda',
            '--no-vad',
            '-m', './tools/whisper-subtitles/models/Systran--faster-whisper-base',
            '-o', str(temp_output)
        ]
        
        if diarize:
            cmd.append('--diarize')
            # 添加Hugging Face token（如果存在）
            hf_token = os.getenv('HUGGINGFACE_TOKEN')
            if hf_token:
                cmd.extend(['--hf-token', hf_token])
            
        subprocess.run(cmd, check=True, encoding='utf-8')
        
        # 检查生成的临时SRT文件
        temp_srt = Path(f"{temp_output}.srt")
        if not temp_srt.exists():
            raise FileNotFoundError(f"WhisperX 未生成临时 SRT: {temp_srt}")
        
        # 转换为项目标准格式
        final_srt = output_dir / f"{video_stem}.srt"
        convert_cmd = [
            sys.executable, 'tools/whisper-subtitles/convert_to_merged_format.py',
            str(temp_srt),
            '-o', str(final_srt)
        ]
        subprocess.run(convert_cmd, check=True)
        
        # 清理临时文件
        if temp_srt.exists():
            temp_srt.unlink()
            
        if not final_srt.exists():
            raise FileNotFoundError(f"WhisperX 格式转换失败: {final_srt}")
        
        logger.info(f"WhisperX转录完成: {final_srt}")
        return final_srt
    
    else:
        raise ValueError(f"不支持的转录引擎: {engine}")
    
    logger.info(f"初始SRT: {init_srt}")
    return init_srt


def create_manual_srt(output_dir: Path, base_name: str) -> Path:
    manual_srt = output_dir / f"{base_name}_manual.srt"
    if manual_srt.exists():
        logger.info(f"检测到已存在的手动SRT: {manual_srt}")
        return manual_srt
    # 提供一个可编辑模板（示例一条）
    template = (
        "1\n"
        "00:00:00,000 --> 00:00:02,000\n"
        "[speaker_1] 在这里输入文本\n\n"
    )
    manual_srt.write_text(template, encoding='utf-8')
    logger.info(f"已生成手动SRT模板: {manual_srt}")
    return manual_srt


def ensure_pipeline_placeholders(output_dir: Path, base_name: str, init_srt: Path) -> tuple:
    """
    生成与流水线一致命名的占位文件：
    - 合并后SRT: {base}_merged_optimized.srt （初始可拷贝自 manual，或空壳）
    - 翻译后SRT: {base}.translated.srt （初始空壳，供用户后续粘贴翻译或用脚本生成）
    """
    merged_srt = output_dir / f"{base_name}_merged_optimized.srt"
    translated_srt = output_dir / f"{base_name}.translated.srt"

    if not merged_srt.exists():
        # 复制原始SRT内容到合并SRT文件
        if init_srt.exists():
            shutil.copy2(init_srt, merged_srt)
            logger.info(f"已创建合并后SRT (复制自原始SRT): {merged_srt}")
        else:
            merged_srt.write_text('', encoding='utf-8')
            logger.info(f"已创建空白合并后SRT: {merged_srt}")
    if not translated_srt.exists():
        # 需求：输出为空文件，由用户自行填写
        translated_srt.write_text('', encoding='utf-8')
        logger.info(f"已创建空白翻译后SRT: {translated_srt}")
    return merged_srt, translated_srt


def main():
    _load_dotenv_into_environ()

    parser = argparse.ArgumentParser(description='Part A: 准备与生成SRT（可选整文件翻译）')
    parser.add_argument('input_video', help='输入视频文件路径')
    # parser.add_argument('-e', '--engine', default='whisperx', choices=['whisperx'],
    #                    help='转录引擎选择 (默认: whisperx)')
    parser.add_argument('-l', '--language', default='auto', 
                       help='语言代码，用于转录的视频语言 (默认: auto)')
    parser.add_argument('--no-diarize', action='store_true', 
                       help='禁用说话人识别 (默认启用)')
    parser.add_argument('--no-separation', action='store_true',
                       help='跳过人声分离（默认开启人声分离）')
    parser.add_argument('--translate', choices=['zh','en','ja','ko'],
                       help='完成转写后按指定语言整文件翻译SRT（不进行智能合并）')
    args = parser.parse_args()

    video_path = Path(args.input_video).resolve()
    if not video_path.exists():
        raise FileNotFoundError(f"输入视频不存在: {video_path}")

    # 强制使用 output/<video_stem> 作为输出目录
    output_dir = Path('output') / video_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"使用转录引擎: whisperx")
    logger.info(f"语言设置: {args.language}")
    logger.info(f"说话人识别: {'禁用' if args.no_diarize else '启用'}")

    run_step1_and_step2(video_path, output_dir, enable_separation=not args.no_separation)
    # 调用 step3 生成初始 SRT
    speak_wav = output_dir / f"{video_path.stem}_speak.wav"
    init_srt = run_step3_transcribe(speak_wav, output_dir, 
                                   engine='whisperx',  # 固定使用 whisperx
                                   language=args.language, 
                                   diarize=not args.no_diarize)


    # 以初始SRT为基础，生成与流水线一致的占位文件（不生成 _manual.srt）
    merged_srt, translated_srt = ensure_pipeline_placeholders(output_dir, video_path.stem, init_srt)

    # 可选：整文件翻译（不进行智能合并）
    if args.translate:
        target_lang = args.translate
        logger.info(f'开始整文件翻译（不进行合并），目标语言: {target_lang} ...')
        try:
            cmd_translate = [
                sys.executable, 'Scripts/step4_translate_srt.py',
                str(init_srt), '--target_lang', target_lang, '--whole_file'
            ]
            # 输出到标准 translated 路径
            cmd_translate.extend(['-o', str(translated_srt)])
            subprocess.run(cmd_translate, check=True)
            logger.info(f'整文件翻译完成: {translated_srt}')
        except subprocess.CalledProcessError as e:
            logger.error(f'整文件翻译失败: {e}')
            raise

    video_only = output_dir / f"{video_path.stem}_video_only.mp4"
    speak_wav = output_dir / f"{video_path.stem}_speak.wav"
    instru_wav = output_dir / f"{video_path.stem}_instru.wav"

    print('\n[PREPARATION COMPLETED]')
    print(f"[OUTPUT] Silent video: {video_only}")
    print(f"[OUTPUT] Voice audio: {speak_wav}")
    print(f"[OUTPUT] Background audio: {instru_wav}")
    print(f"[OUTPUT] Initial SRT: {init_srt}")
    print(f"[OUTPUT] Merged optimized SRT: {merged_srt}")
    print(f"[NEXT] Edit merged SRT in editor: {merged_srt}")
    print(f"[NEXT] Fill translated SRT for TTS: {translated_srt}")
    print('[NOTE] Keep merged and translated indices and timestamps aligned, text can contain [speaker_x] tags')


if __name__ == '__main__':
    main()


