#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Part B: 从手动SRT出发完成后续流程
- 使用手动SRT进行切割（基于 *speak.wav）
- 使用已翻译或原文SRT进行 TTS（通常与切割SRT一致）
- 合并TTS与背景音并替换视频音轨

说明:
- 不调用 Gemini。纯本地流程，适合用户手动维护SRT的场景。
- 自动寻找 {video_stem}_merged_optimized.srt 和 {video_stem}.translated.srt
"""

import os
import sys
import argparse
import logging
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


def main():
    _load_dotenv_into_environ()

    parser = argparse.ArgumentParser(description='Part B: 从手动SRT完成 切割→TTS→合并')
    parser.add_argument('video_stem', help='视频基名（例如 input/foo.mp4 -> foo）')
    parser.add_argument('--resume', action='store_true', default=False, 
                       help='跳过已存在的步骤（切割/TTS/合并）（默认：关闭，每次重新处理所有步骤）')
    parser.add_argument('--max_workers', type=int, default=4, help='切割并发')
    parser.add_argument('--lab', action='store_true', help='生成.lab文件（默认不生成）')
    args = parser.parse_args()

    base = args.video_stem
    # 强制使用 output/<video_stem> 作为输出目录
    output_dir = Path('output') / base
    output_dir.mkdir(parents=True, exist_ok=True)

    speak_wav = output_dir / f"{base}_speak.wav"
    instru_wav = output_dir / f"{base}_instru.wav"
    video_only = output_dir / f"{base}_video_only.mp4"
    
    # 自动寻找符合命名规范的SRT文件
    merged_srt = output_dir / f"{base}_merged_optimized.srt"
    translated_srt = output_dir / f"{base}.translated.srt"

    if not speak_wav.exists():
        raise FileNotFoundError(f"缺少人声音频: {speak_wav}")
    if not translated_srt.exists():
        raise FileNotFoundError(f"缺少翻译后SRT: {translated_srt}")
    
    logger.info(f"使用翻译后SRT进行切割和合成: {translated_srt}")

    # 1) 切割（检查切片数量是否与翻译字幕匹配）
    import subprocess
    import srt
    
    # 读取翻译字幕获取正确的条目数
    with open(translated_srt, 'r', encoding='utf-8') as f:
        subs = list(srt.parse(f.read()))
    expected_clips = len(subs)
    
    clips_dir = output_dir / 'clips'
    num_clips = len(list(clips_dir.glob('*.wav'))) if clips_dir.exists() else 0
    
    if args.resume and clips_dir.exists() and num_clips == expected_clips:
        logger.info(f'[B-1] 切片完整 ({num_clips}/{expected_clips})，启用 --resume 跳过切割')
    else:
        if num_clips != expected_clips:
            logger.info(f'[B-1] 切片数量不匹配 (现有:{num_clips}, 需要:{expected_clips})，重新切割')
        else:
            logger.info('[B-1] 开始切割音频')
        cmd_cut = [
            sys.executable, 'Scripts/step5_cut_audio_by_srt.py',
            str(speak_wav), str(translated_srt),  # 改为使用翻译后的字幕切割
            '-o', str(clips_dir), '--format', 'wav', '--sample_rate', '16000', '--channels', '1',
            '--max_workers', str(args.max_workers)
        ]
        if not getattr(args, 'lab', False):
            cmd_cut.append('--no_lab')
        logger.info('[B-1] 按翻译后SRT切割音频')
        subprocess.run(cmd_cut, check=True)

    # 2) TTS（直接使用该SRT）
    tts_dir = output_dir / 'tts'
    tts_dir.mkdir(parents=True, exist_ok=True)
    
    # 智能resume策略：检测缺失的TTS文件并重新生成
    num_clips = len(list(clips_dir.glob('*.wav')))
    num_tts = len(list(tts_dir.glob('*.tts.wav'))) if tts_dir.exists() else 0
    
    # 检测缺失的TTS文件
    if args.resume and num_tts > 0:
        clip_files = {f.stem.split('.tts')[0]: f for f in clips_dir.glob('*.wav')}
        tts_files = {f.stem.split('.tts')[0]: f for f in tts_dir.glob('*.tts.wav')}
        missing_clips = set(clip_files.keys()) - set(tts_files.keys())
        
        if missing_clips:
            logger.info(f'[B-2] 检测到 {len(missing_clips)} 个缺失的 TTS 文件，重新生成...')
            # 重新运行 TTS（会跳过已存在的）
            cmd_tts = [
                sys.executable, 'Scripts/step6_tts_indextts2.py',
                '--translated_srt', str(translated_srt), '--clips_dir', str(clips_dir), '--out_dir', str(tts_dir)
            ]
            subprocess.run(cmd_tts, check=True)
        else:
            logger.info(f'[B-2] TTS 文件完整 ({num_tts}/{num_clips})，启用 --resume 跳过')
    else:
        # 完整生成 TTS
        cmd_tts = [
            sys.executable, 'Scripts/step6_tts_indextts2.py',
            '--translated_srt', str(translated_srt), '--clips_dir', str(clips_dir), '--out_dir', str(tts_dir)
        ]
        logger.info(f'[B-2] TTS 合成 ({num_clips} 个切片)')
        subprocess.run(cmd_tts, check=True)

    # 3) 合并与替换音轨（始终重新合成）
    merge_dir = output_dir / 'merge'
    merge_dir.mkdir(parents=True, exist_ok=True)
    final_video = merge_dir / f"{base}_dubbed.mp4"
    
    # 即使启用 resume，如果 TTS 有更新，也重新合并
    if args.resume and final_video.exists() and num_tts == num_clips:
        logger.info('[B-3] TTS 完整且视频已存在，启用 --resume 跳过合并')
    else:
        cmd_merge = [
            sys.executable, 'Scripts/step7_merge_tts_and_mux.py',
            '--tts_dir', str(tts_dir), '--instru', str(instru_wav), '--video', str(video_only),
            '--srt', str(translated_srt), '--out_dir', str(merge_dir)
        ]
        logger.info(f'[B-3] 合并并替换音轨（TTS: {num_tts} 个文件）')
        subprocess.run(cmd_merge, check=True)

    print('\n[完成] 手动SRT完整流程已完成')
    print(f"[输出] clips: {clips_dir}")
    print(f"[输出] tts: {tts_dir}")
    print(f"[输出] 最终视频目录: {merge_dir}")


if __name__ == '__main__':
    main()


