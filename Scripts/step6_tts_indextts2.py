#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 IndexTTS2 对按 SRT 切割得到的音频片段进行逐条TTS合成：
- 文本来源：翻译后的 SRT（建议使用带说话人标签的 merged.translated.srt）
- 说话人参考：每个切割出来的片段自身作为参考（保持原说话人音色）
- 输出：与输入切片一一对应的合成 wav（同名到指定目录）
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List
import srt

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


def _strip_speaker(text: str) -> str:
    t = (text or '').strip()
    if t.startswith('[') and '] ' in t:
        i = t.find(']')
        return t[i+1:].lstrip()
    return t


def load_translated_map(translated_srt_path: Path) -> Dict[int, str]:
    subs = list(srt.parse(translated_srt_path.read_text(encoding='utf-8', errors='ignore')))
    mapping = {}
    for sub in subs:
        mapping[sub.index] = _strip_speaker(sub.content)
    logger.info(f"已加载翻译字幕 {len(mapping)} 条: {translated_srt_path}")
    return mapping


def collect_clip_files(clips_dir: Path) -> Dict[int, Path]:
    """根据文件名前缀的索引(例如 0001_...) 收集音频切片。"""
    idx_to_file: Dict[int, Path] = {}
    for p in clips_dir.glob('*.wav'):
        name = p.name
        # 形如 0001_0.390-1.935_... .wav
        try:
            idx = int(name.split('_', 1)[0])
            idx_to_file[idx] = p
        except Exception:
            continue
    logger.info(f"已收集切片 {len(idx_to_file)} 个: {clips_dir}")
    return idx_to_file


def infer_all(clips_dir: Path, translated_srt: Path, out_dir: Path,
              cfg_path: Path, model_dir: Path,
              max_items: int = 0,
              resume: bool = True) -> None:
    # 准备 IndexTTS2
    # 优先使用项目根下的 tools/index-tts 作为 indextts 包根目录
    project_root = Path(__file__).resolve().parent.parent
    idx_root = (project_root / 'tools' / 'index-tts').resolve()
    # 不再指定或覆盖 Hugging Face 缓存目录，使用系统/默认配置
    if str(idx_root) not in sys.path:
        sys.path.insert(0, str(idx_root))
    try:
        from indextts.infer_v2 import IndexTTS2
    except Exception as e:
        logger.error(f"无法导入本地 IndexTTS2，请确认 tools/index-tts 是否完整: {e}")
        raise

    tts = IndexTTS2(cfg_path=str(cfg_path), model_dir=str(model_dir), use_cuda_kernel=False)

    # 数据
    idx_to_text = load_translated_map(translated_srt)
    idx_to_file = collect_clip_files(clips_dir)

    out_dir.mkdir(parents=True, exist_ok=True)

    done = 0
    for idx in sorted(idx_to_file.keys()):
        if max_items and done >= max_items:
            break
        wav_in = idx_to_file.get(idx)
        text = idx_to_text.get(idx, '').strip()
        if not text:
            logger.warning(f"字幕 {idx} 无翻译文本，跳过 {wav_in.name}")
            continue

        out_path = out_dir / (wav_in.stem + '.tts.wav')
        if resume and out_path.exists() and out_path.stat().st_size > 0:
            logger.info(f"已存在，跳过 #{idx}: {out_path.name}")
            done += 1
            continue
        try:
            logger.info(f"TTS合成 #{idx}: {wav_in.name}")
            # 使用每条切片自身作为说话人参考
            tts.infer(spk_audio_prompt=str(wav_in), text=text, output_path=str(out_path), verbose=False)
            done += 1
        except Exception as e:
            logger.warning(f"TTS失败 #{idx}: {e}")

    logger.info(f"TTS完成: 成功 {done}/{len(idx_to_file)}，输出目录: {out_dir}")


def main():
    parser = argparse.ArgumentParser(description='IndexTTS2 对切割音频逐条合成')
    parser.add_argument('--clips_dir', required=True, help='音频切片目录（step5 输出）')
    parser.add_argument('--translated_srt', required=True, help='翻译后的 SRT 路径')
    parser.add_argument('--out_dir', default='output/tts', help='TTS 输出目录')
    parser.add_argument('--cfg_path', default=str(Path(__file__).resolve().parent.parent / 'tools' / 'index-tts' / 'checkpoints' / 'config.yaml'), help='IndexTTS2 配置')
    parser.add_argument('--model_dir', default=str(Path(__file__).resolve().parent.parent / 'tools' / 'index-tts' / 'checkpoints'), help='IndexTTS2 模型目录')
    parser.add_argument('--max_items', type=int, default=0, help='仅处理前 N 条（0 表示全部）')
    parser.add_argument('--no_resume', action='store_true', help='不跳过已存在的 .tts.wav 输出')
    args = parser.parse_args()

    clips_dir = Path(args.clips_dir)
    translated_srt = Path(args.translated_srt)
    out_dir = Path(args.out_dir)
    cfg_path = Path(args.cfg_path)
    model_dir = Path(args.model_dir)

    infer_all(clips_dir, translated_srt, out_dir, cfg_path, model_dir,
              max_items=args.max_items, resume=not args.no_resume)


if __name__ == '__main__':
    main()


