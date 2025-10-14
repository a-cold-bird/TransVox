#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step C: 一键字幕嵌入流程
根据视频 stem 自动查找字幕并嵌入到配音视频
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
        root = Path(__file__).resolve().parent
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


def main():
    parser = argparse.ArgumentParser(
        description='Step C: 一键字幕嵌入流程',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 嵌入单语字幕（译文，默认硬编码）
  python stepC_embed_subtitles.py EN_test
  
  # 嵌入双语字幕（软字幕模式）
  python stepC_embed_subtitles.py EN_test --bilingual --mode soft
  
  # 外挂字幕（兼容性最好）
  python stepC_embed_subtitles.py EN_test --mode external
  
  # 软字幕 + 外挂字幕（最完整）
  python stepC_embed_subtitles.py EN_test --mode both
  
  # 自定义硬编码样式
  python stepC_embed_subtitles.py EN_test --mode hardcode --font-size 24 --position top
        """
    )
    
    parser.add_argument('video_stem', help='视频文件基名（如 EN_test）')
    parser.add_argument('--bilingual', action='store_true', help='使用双语字幕（原文+译文）')
    parser.add_argument('--max-line-chars', type=int, default=40,
                       help='每行最大字符数（默认: 40）')
    parser.add_argument('--no-split', action='store_true',
                       help='不进行AI分行，直接复制字幕（默认: 启用分行）')
    parser.add_argument('--no-gemini', action='store_true',
                       help='禁用 AI 智能分行，使用标点分行')
    parser.add_argument('--no-pause', action='store_true',
                       help='不暂停等待手动编辑（自动模式）')
    
    # 嵌入模式
    parser.add_argument('--mode', '-m',
                       choices=['hardcode', 'soft', 'external', 'both'],
                       default='hardcode',
                       help='字幕嵌入模式（默认: hardcode）')
    parser.add_argument('--subtitle-lang', default='chi',
                       help='字幕语言代码（软字幕模式，默认: chi）')
    parser.add_argument('--subtitle-title', default='Chinese',
                       help='字幕轨道名称（软字幕模式，默认: Chinese）')
    
    # 硬编码字幕样式
    parser.add_argument('--font-size', type=int, default=15,
                       help='字体大小（硬编码模式，默认: 15）')
    parser.add_argument('--font-color', default='white',
                       choices=['white', 'black', 'red', 'blue', 'green', 'yellow'],
                       help='字体颜色（硬编码模式，默认: white）')
    parser.add_argument('--outline-width', type=int, default=1,
                       help='描边宽度（硬编码模式，默认: 1）')
    parser.add_argument('--position', choices=['top', 'bottom'], default='bottom',
                       help='字幕位置（硬编码模式，默认: bottom）')
    parser.add_argument('--margin', type=int, default=50,
                       help='垂直边距（硬编码模式，默认: 50）')
    
    args = parser.parse_args()
    
    try:
        project_root = Path(__file__).resolve().parent
        stem = args.video_stem
        
        # 自动查找文件
        output_dir = project_root / 'output' / stem
        video_file = output_dir / 'merge' / f"{stem}_dubbed.mp4"
        original_srt = output_dir / f"{stem}.srt"
        translated_srt = output_dir / f"{stem}.translated.srt"
        
        # 检查文件
        if not video_file.exists():
            logger.error(f"[X] 配音视频不存在: {video_file}")
            logger.info("    请先运行 TTS 流程生成配音视频")
            return 1
        
        logger.info(f"[OK] 找到配音视频: {video_file.name}")
        
        # 步骤 1: 处理字幕
        if args.bilingual:
            # 双语模式
            if not original_srt.exists():
                logger.error(f"[X] 原文字幕不存在: {original_srt}")
                return 1
            if not translated_srt.exists():
                logger.error(f"[X] 译文字幕不存在: {translated_srt}")
                return 1
            
            logger.info("[模式] 双语字幕")
            processed_srt = output_dir / f"{stem}.bilingual.srt"
            
            if args.no_split:
                # 不分行，直接复制占位
                logger.info("[跳过] 字幕分行，直接复制原字幕")
                import shutil
                shutil.copy2(translated_srt, processed_srt)
            else:
                cmd_process = [
                    sys.executable, 'Scripts/step8_process_subtitle.py',
                    str(original_srt),
                    str(processed_srt),
                    '--bilingual', str(translated_srt),
                    '--max-line-chars', str(args.max_line_chars)
                ]
                
                if args.no_gemini:
                    cmd_process.append('--no-gemini')
                
                logger.info(f"[步骤 1/2] 处理字幕（智能分行）...")
                result = subprocess.run(cmd_process, check=True)
        else:
            # 单语模式（译文）
            if not translated_srt.exists():
                logger.error(f"[X] 译文字幕不存在: {translated_srt}")
                return 1
            
            logger.info("[模式] 单语字幕（译文）")
            processed_srt = output_dir / f"{stem}.translated.processed.srt"
            
            if args.no_split:
                # 不分行，直接复制占位
                logger.info("[跳过] 字幕分行，直接复制译文字幕")
                import shutil
                shutil.copy2(translated_srt, processed_srt)
            else:
                cmd_process = [
                    sys.executable, 'Scripts/step8_process_subtitle.py',
                    str(translated_srt),
                    str(processed_srt),
                    '--max-line-chars', str(args.max_line_chars)
                ]
                
                if args.no_gemini:
                    cmd_process.append('--no-gemini')
                
                logger.info(f"[步骤 1/2] 处理字幕（智能分行）...")
                result = subprocess.run(cmd_process, check=True)
        
        if not processed_srt.exists():
            logger.error("[X] 字幕处理失败")
            return 1
        
        logger.info(f"[OK] 字幕已处理: {processed_srt.name}")
        
        # 可选暂停
        if not args.no_pause:
            logger.info("[提示] 可手动编辑此文件优化字幕，然后按任意键继续...")
            input()
        
        # 步骤 2: 嵌入到视频
        mode_suffix = {
            'hardcode': '_hardcoded',
            'soft': '_soft',
            'external': '',
            'both': '_with_subs'
        }
        suffix = mode_suffix.get(args.mode, '_subtitled')
        output_video = output_dir / 'merge' / f"{stem}_dubbed{suffix}.mp4"
        
        cmd_embed = [
            sys.executable, 'Scripts/step9_embed_to_video.py',
            str(video_file),
            str(processed_srt),
            '-o', str(output_video),
            '--mode', args.mode,
            '--subtitle-lang', args.subtitle_lang,
            '--subtitle-title', args.subtitle_title,
            '--font-size', str(args.font_size),
            '--font-color', args.font_color,
            '--outline-width', str(args.outline_width),
            '--position', args.position,
            '--margin', str(args.margin)
        ]
        
        mode_desc = {
            'hardcode': '硬编码（烧录到画面）',
            'soft': '软字幕（内嵌到容器）',
            'external': '外挂字幕（独立文件）',
            'both': '软字幕 + 外挂字幕'
        }
        
        logger.info(f"[步骤 2/2] 嵌入字幕到视频 ({mode_desc.get(args.mode)})...")
        result = subprocess.run(cmd_embed, check=True)
        
        if output_video.exists():
            print("\n[完成] 字幕嵌入成功！")
            print(f"[模式] {mode_desc.get(args.mode, args.mode)}")
            print(f"[输出] {output_video}")
            if args.mode in ['external', 'both']:
                print(f"[字幕] {output_video.with_suffix('.srt')}")
                print(f"[字幕] {output_video.with_suffix('.ass')}")
            return 0
        else:
            print("\n[失败] 视频生成失败")
            return 1
            
    except KeyboardInterrupt:
        print("\n[中断] 用户取消操作")
        return 1
    except subprocess.CalledProcessError as e:
        logger.error(f"[X] 子进程执行失败: {e}")
        return 1
    except Exception as e:
        logger.error(f"[错误] 程序异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
