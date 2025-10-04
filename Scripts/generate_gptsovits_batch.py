#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPT-SoVITS 批量推理JSON生成脚本
根据翻译后的SRT文件和音频切片生成批量TTS任务配置
"""

import os
import sys
import json
import argparse
import logging
import re
from pathlib import Path
from typing import List, Dict, Any
import srt

# 配置 logging 使用 UTF-8 编码，避免 Windows GBK 编码错误
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(stream=sys.stdout)
    ]
)
# 设置 stdout 编码为 UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

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

class GPTSoVITSBatchGenerator:
    def __init__(self):
        self.language_map = {
            'zh': 'zh',
            'en': 'en', 
            'ja': 'ja',
            'ko': 'ko',
            'chinese': 'zh',
            'english': 'en',
            'japanese': 'ja',
            'korean': 'ko',
            'auto': 'auto'
        }
    
    def find_matching_clip_and_lab(self, clips_dir: Path, subtitle_index: int, start_time: float, end_time: float) -> tuple:
        """
        根据字幕索引和时间戳查找对应的音频切片和lab文件
        
        Args:
            clips_dir: 切片目录
            subtitle_index: 字幕索引
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            tuple: (音频文件路径, lab文件路径)
        """
        # 查找匹配的音频文件（按索引和时间戳匹配）
        pattern_by_index = f"{subtitle_index:04d}_*"
        pattern_by_time = f"*_{start_time:.3f}-{end_time:.3f}_*"
        
        # 首先尝试按索引匹配
        audio_files = list(clips_dir.glob(f"{pattern_by_index}.wav"))
        if not audio_files:
            # 如果按索引找不到，尝试按时间戳匹配
            audio_files = list(clips_dir.glob(f"{pattern_by_time}.wav"))
        
        if not audio_files:
            logger.warning(f"未找到匹配的音频文件: 索引 {subtitle_index}, 时间 {start_time:.3f}-{end_time:.3f}")
            return None, None
        
        audio_file = audio_files[0]  # 取第一个匹配的文件
        
        # 查找对应的lab文件
        lab_file = audio_file.with_suffix('.lab')
        if not lab_file.exists():
            logger.warning(f"未找到对应的lab文件: {lab_file}")
            return str(audio_file), None
        
        return str(audio_file), str(lab_file)
    
    def read_lab_content(self, lab_path: str) -> str:
        """读取lab文件内容"""
        try:
            with open(lab_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            return content
        except Exception as e:
            logger.warning(f"读取lab文件失败 {lab_path}: {e}")
            return ""
    
    def generate_batch_json(self, 
                           translated_srt_path: str,
                           clips_dir: str,
                           output_json_path: str,
                           text_lang: str,
                           prompt_lang: str = 'zh',
                           tts_output_dir: str = None,
                           **tts_params) -> bool:
        """
        生成批量推理JSON配置
        
        Args:
            translated_srt_path: 翻译后的SRT文件路径
            clips_dir: 音频切片目录
            output_json_path: 输出JSON文件路径
            text_lang: 目标语言 (zh/en/ja/ko)
            prompt_lang: 参考音频语言 (默认zh)
            tts_output_dir: TTS输出目录 (默认为clips_dir/../tts_gptsovits)
            **tts_params: 其他TTS参数
            
        Returns:
            bool: 是否成功
        """
        try:
            # 验证输入参数
            srt_path = Path(translated_srt_path)
            clips_path = Path(clips_dir)
            
            if not srt_path.exists():
                logger.error(f"SRT文件不存在: {translated_srt_path}")
                return False
            
            if not clips_path.exists():
                logger.error(f"切片目录不存在: {clips_dir}")
                return False
            
            # 标准化语言代码
            text_lang = self.language_map.get(text_lang.lower(), text_lang.lower())
            prompt_lang = self.language_map.get(prompt_lang.lower(), prompt_lang.lower())
            
            if text_lang not in ['zh', 'en', 'ja', 'ko', 'auto']:
                logger.error(f"不支持的目标语言: {text_lang}")
                return False
            
            # 设置输出目录
            if tts_output_dir is None:
                tts_output_dir = clips_path.parent / 'tts_gptsovits'
            else:
                tts_output_dir = Path(tts_output_dir)
            
            # 读取SRT文件
            with open(srt_path, 'r', encoding='utf-8') as f:
                srt_content = f.read().lstrip('\ufeff')  # 去除BOM
            
            subtitles = list(srt.parse(srt_content))
            logger.info(f"解析到 {len(subtitles)} 条字幕")
            
            # 生成批量任务配置
            tasks = []
            
            for subtitle in subtitles:
                # 提取文本内容（去除说话人标签）
                text_content = subtitle.content.strip()
                
                # 去除各种格式的说话人标签：[SPEAKER_1], [speaker_3], [Speaker_3], [扬声器_2] 等
                # 匹配 [任意内容] 后跟空格或直接跟文本
                text_content = re.sub(r'^\[.*?\]\s*', '', text_content)
                
                if not text_content:
                    logger.warning(f"字幕 {subtitle.index} 文本为空，跳过")
                    continue
                
                # 计算时间戳
                start_time = subtitle.start.total_seconds()
                end_time = subtitle.end.total_seconds()
                
                # 查找对应的音频切片和lab文件
                audio_path, lab_path = self.find_matching_clip_and_lab(
                    clips_path, subtitle.index, start_time, end_time
                )
                
                if not audio_path:
                    logger.warning(f"字幕 {subtitle.index} 未找到对应音频切片，跳过")
                    continue
                
                # 读取lab文件内容作为prompt_text
                prompt_text = ""
                if lab_path:
                    prompt_text = self.read_lab_content(lab_path)
                
                # 生成输出文件名
                output_filename = f"{subtitle.index:04d}_{start_time:.3f}-{end_time:.3f}.tts.wav"
                output_path = tts_output_dir / output_filename
                
                # 创建任务配置
                task = {
                    "text": text_content,
                    "text_lang": text_lang,
                    "ref_audio_path": str(Path(audio_path).resolve()),
                    "prompt_text": prompt_text,
                    "prompt_lang": prompt_lang,
                    "output_path": str(output_path.resolve())
                }
                
                # 添加其他TTS参数
                if tts_params:
                    task.update(tts_params)
                
                tasks.append(task)
                
                logger.debug(f"任务 {subtitle.index}: {text_content[:30]}... -> {output_filename}")
            
            if not tasks:
                logger.error("没有生成任何有效任务")
                return False
            
            # 保存JSON文件
            os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)
            
            logger.info(f"批量配置已生成: {output_json_path}")
            logger.info(f"共生成 {len(tasks)} 个TTS任务")
            logger.info(f"目标语言: {text_lang}")
            logger.info(f"参考语言: {prompt_lang}")
            logger.info(f"输出目录: {tts_output_dir}")
            
            return True
            
        except Exception as e:
            logger.error(f"生成批量配置失败: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    parser = argparse.ArgumentParser(description='GPT-SoVITS 批量推理JSON生成脚本')
    parser.add_argument('translated_srt', help='翻译后的SRT文件路径')
    parser.add_argument('clips_dir', help='音频切片目录路径')
    parser.add_argument('output_json', help='输出JSON文件路径')
    parser.add_argument('--text_lang', default='auto',
                       choices=['zh', 'en', 'ja', 'ko', 'chinese', 'english', 'japanese', 'korean', 'auto'],
                       help='目标语言')
    parser.add_argument('--prompt_lang', default='zh',
                       choices=['zh', 'en', 'ja', 'ko', 'chinese', 'english', 'japanese', 'korean'],
                       help='参考音频语言，必须明确指定 (默认: zh)')
    parser.add_argument('--tts_output_dir', help='TTS输出目录 (默认: clips_dir/../tts_gptsovits)')
    
    # TTS参数
    parser.add_argument('--temperature', type=float, default=1.0, help='采样温度')
    parser.add_argument('--top_k', type=int, default=5, help='Top-k采样')
    parser.add_argument('--top_p', type=float, default=1.0, help='Top-p采样')
    parser.add_argument('--speed_factor', type=float, default=1.0, help='语速控制')
    parser.add_argument('--repetition_penalty', type=float, default=1.35, help='重复惩罚')
    parser.add_argument('--text_split_method', default='cut5', help='文本分割方法')
    
    args = parser.parse_args()
    
    try:
        generator = GPTSoVITSBatchGenerator()
        
        # 准备TTS参数
        tts_params = {}
        if args.temperature != 1.0:
            tts_params['temperature'] = args.temperature
        if args.top_k != 5:
            tts_params['top_k'] = args.top_k
        if args.top_p != 1.0:
            tts_params['top_p'] = args.top_p
        if args.speed_factor != 1.0:
            tts_params['speed_factor'] = args.speed_factor
        if args.repetition_penalty != 1.35:
            tts_params['repetition_penalty'] = args.repetition_penalty
        if args.text_split_method != 'cut5':
            tts_params['text_split_method'] = args.text_split_method
        
        success = generator.generate_batch_json(
            translated_srt_path=args.translated_srt,
            clips_dir=args.clips_dir,
            output_json_path=args.output_json,
            text_lang=args.text_lang,
            prompt_lang=args.prompt_lang,
            tts_output_dir=args.tts_output_dir,
            **tts_params
        )
        
        if success:
            print(f"\n✅ 批量配置生成成功: {args.output_json}")
            print(f"📁 使用以下命令执行批量TTS:")
            print(f"   python Scripts/step6_tts_gptsovits.py --batch_json {args.output_json}")
            return 0
        else:
            print("\n❌ 批量配置生成失败")
            return 1
            
    except KeyboardInterrupt:
        print("\n用户中断")
        return 1
    except Exception as e:
        logger.error(f"程序异常: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
