#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据SRT时间戳批量切割音频

功能:
- 读取SRT(建议使用带[speaker_N]的merged版本)
- 使用ffmpeg按时间戳切割音频，文件名包含索引/时间/说话人/文本片段
- 为每个音频片段生成对应的.lab文件，包含文本内容
- 支持输出格式/采样率/声道/并发
"""

import os
import sys
import argparse
import logging
import subprocess
from pathlib import Path
from typing import List
import srt
import concurrent.futures
import re

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


def _format_ts(tdelta) -> float:
    return tdelta.total_seconds()


def _sanitize_filename(text: str, max_len: int = 40) -> str:
    invalid = '<>:"/\\|?*\n\r\t'
    cleaned = ''.join('_' if c in invalid else c for c in text)
    cleaned = cleaned.strip()
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rstrip()
    return cleaned


def _ensure_ffmpeg() -> None:
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, capture_output=True)
    except Exception:
        raise RuntimeError('未检测到ffmpeg，请安装并加入PATH后重试')


def cut_one(index: int,
            subtitle: srt.Subtitle,
            input_audio: Path,
            out_dir: Path,
            fmt: str,
            sr: int,
            ch: int,
            reencode: bool = True,
            max_duration: float = 30.0,
            min_duration: float = 0.2,
            generate_lab: bool = True) -> Path:
    start = _format_ts(subtitle.start)
    end = _format_ts(subtitle.end)
    duration = end - start
    # 合法性修复
    if duration <= 0:
        logger.warning(f"字幕 {index} 时长非法({duration:.3f}s)，自动修复为 {min_duration:.3f}s (start={start:.3f}, end={end:.3f})")
        duration = min_duration
        end = start + duration
    if duration > max_duration:
        logger.warning(f"字幕 {index} 时长异常过长({duration:.3f}s)，按阈值截断为 {max_duration:.3f}s (start={start:.3f}, end={end:.3f})")
        duration = max_duration
        end = start + duration
    content = (subtitle.content or '').strip()

    # 解析说话人标签
    speaker = ''
    if content.startswith('[') and '] ' in content:
        bracket = content.split('] ', 1)[0] + ']'
        speaker = bracket.strip('[]')
    text_snip = content
    if '] ' in content:
        text_snip = content.split('] ', 1)[1].strip()

    text_snip = _sanitize_filename(text_snip)
    speaker_part = f"_{_sanitize_filename(speaker)}" if speaker else ''
    name = f"{index:04d}_{start:.3f}-{end:.3f}{speaker_part}_{text_snip}.{fmt}"
    out_path = out_dir / name

    # ffmpeg命令
    # 使用 -ss 和 -t，避免浮点尾差，用reencode确保格式一致
    cmd = [
        'ffmpeg', '-y',
        '-ss', f"{start:.3f}",
        '-i', str(input_audio),
        '-t', f"{duration:.3f}"
    ]
    if reencode:
        cmd += ['-ac', str(ch), '-ar', str(sr)]
        if fmt.lower() == 'wav':
            cmd += ['-c:a', 'pcm_s16le']
        elif fmt.lower() == 'mp3':
            cmd += ['-c:a', 'libmp3lame', '-b:a', '192k']
        elif fmt.lower() == 'flac':
            cmd += ['-c:a', 'flac']
        else:
            # 默认选择aac
            cmd += ['-c:a', 'aac', '-b:a', '192k']
    else:
        cmd += ['-c', 'copy']
    cmd += [str(out_path)]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        
        # 生成对应的.lab文件
        if generate_lab:
            lab_path = out_path.with_suffix('.lab')
            
            # 提取完整的文本内容（去除说话人标签）
            full_text = content.strip()
            if full_text.startswith('[') and '] ' in full_text:
                # 去除说话人标签，保留完整文本
                lab_content = full_text.split('] ', 1)[1].strip()
            else:
                lab_content = full_text
            
            # 如果提取后的文本为空，使用原始内容
            if not lab_content.strip():
                lab_content = full_text
            
            try:
                with open(lab_path, 'w', encoding='utf-8') as f:
                    f.write(lab_content)
                logger.debug(f"已生成.lab文件: {lab_path.name}")
            except Exception as e:
                logger.warning(f"生成.lab文件失败 #{index}: {e}")
        
        return out_path
    except subprocess.CalledProcessError as e:
        logger.error(f"切割失败 #{index}: {e.stderr.decode(errors='ignore')}")
        raise


def main():
    parser = argparse.ArgumentParser(description='根据SRT时间戳切割音频')
    parser.add_argument('input_audio', help='输入音频文件，如 .wav/.mp3')
    parser.add_argument('input_srt', help='SRT字幕文件路径')
    parser.add_argument('-o', '--output_dir', default='output/clips', help='输出目录')
    parser.add_argument('--format', default='wav', choices=['wav', 'mp3', 'flac'], help='输出音频格式')
    parser.add_argument('--sample_rate', type=int, default=16000, help='输出采样率')
    parser.add_argument('--channels', type=int, default=1, help='输出声道数')
    parser.add_argument('--max_workers', type=int, default=4, help='并发线程数')
    parser.add_argument('--start_index', type=int, default=1, help='起始字幕索引(包含)')
    parser.add_argument('--end_index', type=int, default=10**9, help='结束字幕索引(包含)')
    parser.add_argument('--no_reencode', action='store_true', help='不重编码，尝试直接裁切(可能不兼容)')
    parser.add_argument('--max_duration', type=float, default=30.0, help='单条最大切割时长秒，超出将截断 (默认30)')
    parser.add_argument('--min_duration', type=float, default=0.2, help='单条最小时长秒，非法(<=0)则使用该值 (默认0.2)')
    parser.add_argument('--no_lab', action='store_true', help='不生成.lab文件（默认生成）')

    args = parser.parse_args()

    input_audio = Path(args.input_audio)
    input_srt = Path(args.input_srt)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not input_audio.exists():
        logger.error(f"找不到输入音频: {input_audio}")
        sys.exit(1)
    if not input_srt.exists():
        logger.error(f"找不到SRT文件: {input_srt}")
        sys.exit(1)

    try:
        _ensure_ffmpeg()
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)

    with open(input_srt, 'r', encoding='utf-8') as f:
        raw_text = f.read().lstrip('\ufeff')  # 去除可能的BOM

    # 仅规范化时间行：形如 "... --> ..."
    def normalize_ts_token(tok: str) -> str:
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

    norm_lines = []
    changed = False
    for line in raw_text.splitlines():
        if ' --> ' in line:
            parts = line.split(' --> ')
            if len(parts) == 2:
                left = normalize_ts_token(parts[0])
                right = normalize_ts_token(parts[1])
                new_line = f"{left} --> {right}"
                if new_line != line:
                    changed = True
                norm_lines.append(new_line)
                continue
        norm_lines.append(line)
    norm_text = '\n'.join(norm_lines)
    if changed:
        logger.warning('检测到不完整/不规范的时间戳，已仅规范化时间行（补全/替换小数点）')

    subs: List[srt.Subtitle] = list(srt.parse(norm_text))

    # 过滤索引范围
    jobs = [sub for sub in subs if args.start_index <= sub.index <= args.end_index]
    logger.info(f"总字幕条目: {len(subs)}，切割范围内条目: {len(jobs)}")

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        future_to_idx = {}
        for sub in jobs:
            future = ex.submit(
                cut_one,
                sub.index,
                sub,
                input_audio,
                out_dir,
                args.format,
                args.sample_rate,
                args.channels,
                not args.no_reencode,
                args.max_duration,
                args.min_duration,
                not args.no_lab
            )
            future_to_idx[future] = sub.index

        for fut in concurrent.futures.as_completed(future_to_idx):
            idx = future_to_idx[fut]
            try:
                out_path = fut.result()
                results.append(out_path)
                logger.info(f"完成切割 #{idx}: {out_path.name}")
            except Exception as e:
                logger.warning(f"跳过 #{idx}: {e}")

    logger.info(f"切割完成，成功 {len(results)}/{len(jobs)}")


if __name__ == '__main__':
    main()


