#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 IndexTTS2 合成的切片按 SRT 时间轴合并为整轨，并与背景音混合，替换视频音轨。

输入：
- 视频无声文件（step1 输出的 *_video_only.mp4）
- 背景音频（step2 输出的 *_instru.wav）
- TTS 切片目录（step6 输出的 *.tts.wav）
- SRT（建议使用 merged.srt 或 cleaned .srt）

输出：
- tts_only.wav：按时间轴拼接/对齐后的整轨 TTS
- mix.wav：与背景音混合后的整轨音频
- *_dubbed.mp4：替换音轨后的视频
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional
import re
import srt
from pydub import AudioSegment
import subprocess

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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


def _ms(td) -> int:
    return int(td.total_seconds() * 1000)


def collect_tts_files(tts_dir: Path) -> Dict[int, Path]:
    mapping: Dict[int, Path] = {}
    for p in tts_dir.glob('*.tts.wav'):
        try:
            idx = int(p.stem.split('_', 1)[0])
            mapping[idx] = p
        except Exception:
            continue
    return mapping


def build_tts_track(subs: List[srt.Subtitle], tts_dir: Path, sample_rate: int = 22050, debug_dir: Optional[Path] = None) -> AudioSegment:
    idx_to_file = collect_tts_files(tts_dir)
    if not idx_to_file:
        raise FileNotFoundError(f"未找到TTS切片: {tts_dir}/*.tts.wav")
    
    # 检查字幕条数和切片条数的一致性
    srt_count = len(subs)
    tts_count = len(idx_to_file)
    logger.info(f"字幕条数: {srt_count}, TTS切片数: {tts_count}")
    
    if srt_count == 0:
        raise ValueError("SRT文件为空，无法进行音频合并")
    
    if tts_count == 0:
        raise ValueError("TTS切片为空，请检查TTS合成是否成功")
    
    # 检查缺失的切片
    missing_indices = []
    for sub in subs:
        if sub.index not in idx_to_file:
            missing_indices.append(sub.index)
    
    if missing_indices:
        logger.warning(f"缺失TTS切片索引: {missing_indices}")
        logger.warning(f"可用切片索引: {sorted(idx_to_file.keys())}")
        # 不抛出异常，允许部分缺失，但会在合并时使用静音替代
    # 从最小底轨开始，按需扩展，避免异常时间戳导致超长静音
    base = AudioSegment.silent(duration=50, frame_rate=sample_rate)
    # 按开始时间排序，确保顺序正确
    ordered_subs = sorted(subs, key=lambda s: (s.start, s.index))
    last_end_ms = 0
    # 调试输出准备
    writer = None
    if debug_dir:
        debug_dir.mkdir(parents=True, exist_ok=True)
        import csv
        writer = open(debug_dir / 'placements.csv', 'w', newline='', encoding='utf-8')
        csvw = csv.writer(writer)
        csvw.writerow(['index','planned_start_s','srt_end_s','adjusted_start_s','prev_end_s','seg_len_s','overlap_s','note'])
    for sub in ordered_subs:
        wav_path = idx_to_file.get(sub.index)
        if not wav_path:
            logger.warning(f"缺少TTS切片，字幕{sub.index} 跳过: {sub.content}")
            continue
        seg = AudioSegment.from_file(wav_path)
        if seg.frame_rate != sample_rate:
            seg = seg.set_frame_rate(sample_rate)
        # 插入策略：尊重字幕时间戳，但避免过大间隔
        planned_start = _ms(sub.start)
        srt_end_ms = _ms(sub.end)
        gap_threshold = 500  # 间隔超过 500ms 才保留，否则紧密连接
        
        if planned_start < last_end_ms:
            # 重叠：紧邻插入
            start_ms = last_end_ms
            logger.info(
                f"顺延插入 | idx={sub.index} planned={planned_start/1000:.3f}s -> adjusted={last_end_ms/1000:.3f}s "
                f"prev_end={last_end_ms/1000:.3f}s seg_len={len(seg)/1000:.3f}s"
            )
        elif planned_start - last_end_ms > gap_threshold:
            # 间隔较大：按时插入（保留间隔）
            start_ms = planned_start
            logger.info(
                f"按时插入 | idx={sub.index} start={start_ms/1000:.3f}s gap={(planned_start-last_end_ms)/1000:.3f}s seg_len={len(seg)/1000:.3f}s"
            )
        else:
            # 间隔较小（<500ms）：紧密连接
            start_ms = last_end_ms
            logger.info(
                f"紧密连接 | idx={sub.index} planned={planned_start/1000:.3f}s -> tight={last_end_ms/1000:.3f}s gap_removed={(planned_start-last_end_ms)/1000:.3f}s seg_len={len(seg)/1000:.3f}s"
            )
        # 如果需要，扩展底轨长度，避免尾部被截断
        expected_end = start_ms + len(seg)
        if expected_end > len(base):
            extend_ms = expected_end - len(base) + 50
            logger.debug(f"扩展底轨: +{extend_ms}ms (new_total={ (len(base)+extend_ms)/1000:.3f}s)")
            base += AudioSegment.silent(duration=extend_ms, frame_rate=sample_rate)
        base = base.overlay(seg, position=start_ms)
        last_end_ms = expected_end
        # 详细调试记录
        if debug_dir:
            overlap_s = max(0.0, (last_end_ms - len(seg)) - planned_start) / 1000.0 if planned_start < (last_end_ms - len(seg)) else 0.0
            note = 'shifted' if start_ms != planned_start else 'on_time'
            import csv
            csvw = csv.writer(writer)
            csvw.writerow([
                sub.index,
                f"{planned_start/1000:.3f}",
                f"{srt_end_ms/1000:.3f}",
                f"{start_ms/1000:.3f}",
                f"{(last_end_ms-len(seg))/1000:.3f}",
                f"{len(seg)/1000:.3f}",
                f"{overlap_s:.3f}",
                note
            ])
    if writer:
        writer.close()
    return base


def loop_or_trim(bg: AudioSegment, target_ms: int) -> AudioSegment:
    if len(bg) == 0:
        return AudioSegment.silent(duration=target_ms, frame_rate=bg.frame_rate or 22050)
    chunks: List[AudioSegment] = []
    cur = 0
    while cur < target_ms:
        remain = target_ms - cur
        if len(bg) <= remain:
            chunks.append(bg)
            cur += len(bg)
        else:
            chunks.append(bg[:remain])
            cur += remain
    out = sum(chunks)
    return out.set_frame_rate(bg.frame_rate)


def mux_video(video_mp4: Path, audio_wav: Path, out_mp4: Path) -> None:
    cmd = [
        'ffmpeg', '-y',
        '-i', str(video_mp4),
        '-i', str(audio_wav),
        '-map', '0:v', '-map', '1:a',
        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
        str(out_mp4)
    ]
    subprocess.run(cmd, check=True)


def _guess_speak_from_instru(instru_path: Path) -> Optional[Path]:
    """根据 *_instru.wav 推断 *_speak.wav 路径。"""
    name = instru_path.name
    if name.endswith('_instru.wav'):
        return instru_path.with_name(name.replace('_instru.wav', '_speak.wav'))
    # 兼容其它命名：优先替换 'instru' -> 'speak'
    if 'instru' in name:
        return instru_path.with_name(name.replace('instru', 'speak'))
    # 同目录下尝试同stem的 speak
    return instru_path.with_name(instru_path.stem + '_speak.wav')


def _match_loudness_to_reference(target: AudioSegment, reference: AudioSegment) -> AudioSegment:
    """将 target 的响度匹配到 reference（基于 dBFS）。"""
    try:
        ref_db = reference.dBFS
        tgt_db = target.dBFS
        if ref_db == float('-inf') or tgt_db == float('-inf'):
            logger.warning('响度匹配跳过：检测到静音（-inf dBFS）')
            return target
        gain = ref_db - tgt_db
        logger.info(f'响度匹配: ref={ref_db:.2f}dBFS, tgt={tgt_db:.2f}dBFS, gain={gain:.2f}dB')
        return target.apply_gain(gain)
    except Exception as e:
        logger.warning(f'响度匹配失败，已跳过: {e}')
        return target


def main():
    parser = argparse.ArgumentParser(description='合并TTS整轨并替换视频音轨，加入背景音')
    parser.add_argument('--video', required=True, help='无声视频文件 *_video_only.mp4')
    parser.add_argument('--instru', required=True, help='背景音文件 *_instru.wav')
    parser.add_argument('--srt', required=True, help='SRT 文件（与TTS切片索引对应）')
    parser.add_argument('--tts_dir', required=True, help='TTS 切片目录（*.tts.wav）')
    parser.add_argument('--out_dir', default='output/merge', help='输出目录')
    parser.add_argument('--sr', type=int, default=22050, help='输出采样率（默认22050）')
    parser.add_argument('--bg_gain', type=float, default=-10.0, help='背景音增益(dB)，负值为衰减（默认-10dB）')
    parser.add_argument('--debug_dir', help='调试输出目录（保存placements.csv等）')
    args = parser.parse_args()

    video = Path(args.video)
    instru = Path(args.instru)
    srt_path = Path(args.srt)
    tts_dir = Path(args.tts_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 规范化SRT时间戳，确保为 HH:MM:SS,mmm，避免异常时间导致总时长过长
    raw = srt_path.read_text(encoding='utf-8', errors='ignore').lstrip('\ufeff')
    def _norm_tok(tok: str) -> str:
        tok = tok.strip().replace('.', ',')
        # 匹配各种时间格式：HH:MM:SS,mmm 或 MM:SS,mmm 或 SS,mmm
        m = re.fullmatch(r'(?:([0-9]{1,2}):)?(?:([0-9]{1,2}):)?([0-9]{1,2})(?:,([0-9]{1,3}))?', tok)
        if not m:
            return tok
        
        # 根据匹配的组数判断格式
        if m.group(1) and m.group(2):  # HH:MM:SS,mmm 格式
            hh = m.group(1).zfill(2)
            mm = m.group(2).zfill(2)
            ss = m.group(3).zfill(2)
        elif m.group(2):  # MM:SS,mmm 格式
            hh = '00'
            mm = m.group(2).zfill(2)
            ss = m.group(3).zfill(2)
        else:  # SS,mmm 格式，当作 00:00:SS,mmm
            hh = '00'
            mm = '00'
            ss = m.group(3).zfill(2)
        
        ms = (m.group(4) or '000').zfill(3)
        return f"{hh}:{mm}:{ss},{ms}"
    norm_lines: List[str] = []
    for line in raw.splitlines():
        if ' --> ' in line:
            parts = line.split(' --> ')
            if len(parts) == 2:
                left = _norm_tok(parts[0])
                right = _norm_tok(parts[1])
                norm_lines.append(f"{left} --> {right}")
                continue
        norm_lines.append(line)
    subs = list(srt.parse('\n'.join(norm_lines)))
    if not subs:
        raise ValueError('SRT 为空')

    # 构建 TTS 整轨
    logger.info('构建TTS整轨...')
    debug_dir = Path(args.debug_dir) if args.debug_dir else None
    tts_track = build_tts_track(subs, tts_dir, sample_rate=args.sr, debug_dir=debug_dir)
    # 响度匹配到干声 *_speak.wav
    speak_path = _guess_speak_from_instru(instru)
    try:
        if speak_path and speak_path.exists():
            speak_seg = AudioSegment.from_wav(speak_path)
            if speak_seg.frame_rate != args.sr:
                speak_seg = speak_seg.set_frame_rate(args.sr)
            tts_track = _match_loudness_to_reference(tts_track, speak_seg)
        else:
            logger.warning(f'未找到干声用于响度匹配: {speak_path}')
    except Exception as e:
        logger.warning(f'加载干声失败，跳过响度匹配: {e}')
    tts_wav = out_dir / 'tts_only.wav'
    tts_track.export(tts_wav, format='wav')
    logger.info(f'TTS整轨: {tts_wav}')

    # 背景音轨处理
    logger.info('加载背景音...')
    bg = AudioSegment.from_wav(instru)
    if bg.frame_rate != args.sr:
        bg = bg.set_frame_rate(args.sr)
    total_ms = len(tts_track)
    bg = loop_or_trim(bg, total_ms)
    if args.bg_gain != 0:
        bg = bg + args.bg_gain

    # 混音
    mix = bg.overlay(tts_track)
    mix_wav = out_dir / 'mix.wav'
    mix.export(mix_wav, format='wav')
    logger.info(f'混音输出: {mix_wav}')

    # 替换视频音轨
    dubbed_mp4 = out_dir / (video.stem.replace('_video_only', '') + '_dubbed.mp4')
    logger.info('替换视频音轨...')
    mux_video(video, mix_wav, dubbed_mp4)
    logger.info(f'完成: {dubbed_mp4}')


if __name__ == '__main__':
    main()


