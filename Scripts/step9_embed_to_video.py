#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤9: 将字幕嵌入视频
支持多种字幕嵌入方式：
- hardcode: 硬编码（烧录）字幕到视频画面中
- soft: 软字幕（内嵌到容器，可关闭）
- external: 外挂字幕（生成独立字幕文件）
- both: 同时生成软字幕和外挂字幕
"""

import os
import sys
import argparse
import logging
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _load_dotenv_into_environ():
    """加载环境变量"""
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


class VideoSubtitleEmbedder:
    """视频字幕嵌入器 - 支持多种嵌入方式"""
    
    def __init__(self):
        self.project_root = Path(__file__).resolve().parent.parent
        self.font_dir = self.project_root / 'fonts'
        self.font_file = self.font_dir / 'LXGWWenKai-Regular.ttf'
    
    def check_font(self) -> bool:
        """检查字体文件是否存在（仅硬编码需要）"""
        if self.font_file.exists():
            logger.info(f"[OK] 字体文件: {self.font_file}")
            return True
        else:
            logger.error(f"[X] 字体文件不存在: {self.font_file}")
            logger.info("请下载霞鹜文楷字体:")
            logger.info("  https://github.com/lxgw/LxgwWenKai/releases")
            logger.info(f"  放置到: {self.font_dir}/LXGWWenKai-Regular.ttf")
            return False
    
    def process_subtitle(self,
                        video_path: Path,
                        subtitle_path: Path,
                        output_path: Path,
                        mode: str = 'hardcode',
                        font_size: int = 20,
                        font_color: str = 'white',
                        outline_color: str = 'black',
                        outline_width: int = 1,
                        position: str = 'bottom',
                        margin_v: int = 50,
                        subtitle_lang: str = 'chi',
                        subtitle_title: str = 'Subtitle') -> bool:
        """
        处理字幕 - 支持多种模式
        
        Args:
            mode: 嵌入模式
                - hardcode: 硬编码字幕（烧录到画面）
                - soft: 软字幕（内嵌到容器）
                - external: 外挂字幕（独立文件）
                - both: 软字幕 + 外挂字幕
        """
        if mode == 'hardcode':
            return self._embed_hardcode(
                video_path, subtitle_path, output_path,
                font_size, font_color, outline_color, outline_width,
                position, margin_v
            )
        elif mode == 'soft':
            return self._embed_soft(
                video_path, subtitle_path, output_path,
                subtitle_lang, subtitle_title
            )
        elif mode == 'external':
            return self._create_external(
                video_path, subtitle_path, output_path
            )
        elif mode == 'both':
            return self._embed_both(
                video_path, subtitle_path, output_path,
                subtitle_lang, subtitle_title
            )
        else:
            logger.error(f"[X] 不支持的模式: {mode}")
            return False
    
    def _embed_hardcode(self,
                      video_path: Path,
                      subtitle_path: Path,
                      output_path: Path,
                      font_size: int = 20,
                      font_color: str = 'white',
                      outline_color: str = 'black',
                      outline_width: int = 1,
                      position: str = 'bottom',
                      margin_v: int = 50) -> bool:
        """硬编码字幕（烧录到视频画面）"""
        try:
            if not self.check_font():
                return False
            
            # 构建 ffmpeg 字幕滤镜
            font_path_str = str(self.font_file.resolve()).replace('\\', '/').replace(':', '\\:')
            subtitle_path_str = str(subtitle_path.resolve()).replace('\\', '/').replace(':', '\\:')
            
            alignment = '2' if position == 'bottom' else '8'
            
            subtitle_filter = f"subtitles='{subtitle_path_str}':force_style='"
            subtitle_filter += f"FontName=LXGW WenKai,"
            subtitle_filter += f"FontSize={font_size},"
            subtitle_filter += f"PrimaryColour=&H{self._color_to_ass(font_color)}&,"
            subtitle_filter += f"OutlineColour=&H{self._color_to_ass(outline_color)}&,"
            subtitle_filter += f"BorderStyle=1,"
            subtitle_filter += f"Outline={outline_width},"
            subtitle_filter += f"Alignment={alignment},"
            subtitle_filter += f"MarginV={margin_v}"
            subtitle_filter += "'"
            
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-vf', subtitle_filter,
                '-c:v', 'libx264',
                '-c:a', 'copy',
                '-y',
                str(output_path)
            ]
            
            logger.info("[硬编码] 烧录字幕到视频画面...")
            logger.info(f"  视频: {video_path.name}")
            logger.info(f"  字幕: {subtitle_path.name}")
            logger.info(f"  字体: 霞鹜文楷 ({font_size}px)")
            logger.info(f"  位置: {position} (边距: {margin_v}px)")
            
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if output_path.exists():
                size_mb = output_path.stat().st_size / (1024 * 1024)
                logger.info(f"[OK] 硬编码完成: {output_path}")
                logger.info(f"     文件大小: {size_mb:.1f} MB")
                return True
            else:
                logger.error("[X] 输出文件未生成")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"[X] ffmpeg 执行失败: {e}")
            if e.stderr:
                logger.error(f"错误: {e.stderr[:500]}")
            return False
        except Exception as e:
            logger.error(f"[X] 硬编码失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _embed_soft(self,
                   video_path: Path,
                   subtitle_path: Path,
                   output_path: Path,
                   subtitle_lang: str = 'chi',
                   subtitle_title: str = 'Subtitle') -> bool:
        """软字幕（内嵌到容器，可关闭）"""
        try:
            logger.info("[软字幕] 将字幕内嵌到视频容器...")
            logger.info(f"  视频: {video_path.name}")
            logger.info(f"  字幕: {subtitle_path.name}")
            logger.info(f"  语言: {subtitle_lang}")
            
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-i', str(subtitle_path),
                '-c:v', 'copy',
                '-c:a', 'copy',
                '-c:s', 'mov_text',  # MP4 软字幕格式
                '-metadata:s:s:0', f'language={subtitle_lang}',
                '-metadata:s:s:0', f'title={subtitle_title}',
                '-disposition:s:0', 'default',  # 设为默认字幕轨
                '-y',
                str(output_path)
            ]
            
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if output_path.exists():
                size_mb = output_path.stat().st_size / (1024 * 1024)
                logger.info(f"[OK] 软字幕嵌入完成: {output_path}")
                logger.info(f"     文件大小: {size_mb:.1f} MB")
                logger.info(f"     提示: 播放器可以开关字幕显示")
                return True
            else:
                logger.error("[X] 输出文件未生成")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"[X] ffmpeg 执行失败: {e}")
            if e.stderr:
                logger.error(f"错误: {e.stderr[:500]}")
            return False
        except Exception as e:
            logger.error(f"[X] 软字幕嵌入失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_external(self,
                        video_path: Path,
                        subtitle_path: Path,
                        output_path: Path) -> bool:
        """外挂字幕（复制视频和字幕到同一目录）"""
        try:
            logger.info("[外挂字幕] 生成独立字幕文件...")
            logger.info(f"  视频: {video_path.name}")
            logger.info(f"  字幕: {subtitle_path.name}")
            
            # 复制视频文件
            if video_path != output_path:
                shutil.copy2(str(video_path), str(output_path))
                logger.info(f"  视频已复制: {output_path}")
            
            # 生成同名字幕文件
            subtitle_output = output_path.with_suffix('.srt')
            if subtitle_path != subtitle_output:
                shutil.copy2(str(subtitle_path), str(subtitle_output))
                logger.info(f"  字幕已复制: {subtitle_output}")
            
            # 额外生成 ASS 格式（更好的样式支持）
            ass_output = output_path.with_suffix('.ass')
            self._convert_srt_to_ass(subtitle_path, ass_output)
            
            logger.info(f"[OK] 外挂字幕生成完成")
            logger.info(f"     视频: {output_path}")
            logger.info(f"     字幕: {subtitle_output}")
            logger.info(f"     字幕: {ass_output}")
            logger.info(f"     提示: 播放器会自动加载同名字幕")
            return True
            
        except Exception as e:
            logger.error(f"[X] 外挂字幕生成失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _embed_both(self,
                   video_path: Path,
                   subtitle_path: Path,
                   output_path: Path,
                   subtitle_lang: str = 'chi',
                   subtitle_title: str = 'Subtitle') -> bool:
        """同时生成软字幕视频和外挂字幕"""
        try:
            logger.info("[混合模式] 生成软字幕 + 外挂字幕...")
            
            # 先生成软字幕视频
            if not self._embed_soft(video_path, subtitle_path, output_path,
                                   subtitle_lang, subtitle_title):
                return False
            
            # 再生成外挂字幕文件
            subtitle_output = output_path.with_suffix('.srt')
            if subtitle_path != subtitle_output:
                shutil.copy2(str(subtitle_path), str(subtitle_output))
                logger.info(f"[OK] 外挂字幕: {subtitle_output}")
            
            # 生成 ASS 格式
            ass_output = output_path.with_suffix('.ass')
            self._convert_srt_to_ass(subtitle_path, ass_output)
            logger.info(f"[OK] 外挂字幕: {ass_output}")
            
            logger.info(f"[OK] 混合模式完成")
            logger.info(f"     内嵌字幕: {output_path}")
            logger.info(f"     外挂字幕: {subtitle_output}, {ass_output}")
            return True
            
        except Exception as e:
            logger.error(f"[X] 混合模式失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _convert_srt_to_ass(self, srt_path: Path, ass_path: Path) -> bool:
        """将 SRT 转换为 ASS 格式（更好的样式支持）"""
        try:
            cmd = [
                'ffmpeg',
                '-i', str(srt_path),
                '-y',
                str(ass_path)
            ]
            
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            return True
            
        except Exception as e:
            logger.warning(f"SRT转ASS失败: {e}")
            return False
    
    def _color_to_ass(self, color: str) -> str:
        """颜色名称转 ASS BGR 格式"""
        color_map = {
            'white': 'FFFFFF',
            'black': '000000',
            'red': '0000FF',
            'blue': 'FF0000',
            'green': '00FF00',
            'yellow': '00FFFF',
            'cyan': 'FFFF00',
            'magenta': 'FF00FF',
        }
        return color_map.get(color.lower(), 'FFFFFF')


def main():
    parser = argparse.ArgumentParser(
        description='字幕嵌入工具 - 支持多种嵌入方式',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
嵌入模式说明:
  hardcode  - 硬编码（烧录到画面，无法关闭，文件较大）
  soft      - 软字幕（内嵌到容器，可关闭，文件较小）
  external  - 外挂字幕（独立文件，播放器自动加载）
  both      - 软字幕 + 外挂字幕（兼顾两种方式）

使用示例:
  # 硬编码字幕（默认）
  python step9_embed_to_video.py video.mp4 subtitle.srt
  
  # 软字幕（推荐，文件小且可关闭）
  python step9_embed_to_video.py video.mp4 subtitle.srt --mode soft
  
  # 外挂字幕（兼容性最好）
  python step9_embed_to_video.py video.mp4 subtitle.srt --mode external
  
  # 软字幕 + 外挂字幕（最完整）
  python step9_embed_to_video.py video.mp4 subtitle.srt --mode both
  
  # 自定义硬编码样式
  python step9_embed_to_video.py video.mp4 subtitle.srt --mode hardcode --font-size 24 --position top
        """
    )
    
    parser.add_argument('video', help='输入视频文件路径')
    parser.add_argument('subtitle', help='字幕文件路径（SRT 格式）')
    parser.add_argument('--output', '-o', help='输出视频路径（默认: 自动生成）')
    
    # 嵌入模式
    parser.add_argument('--mode', '-m',
                       choices=['hardcode', 'soft', 'external', 'both'],
                       default='hardcode',
                       help='嵌入模式（默认: hardcode）')
    
    # 软字幕/外挂字幕选项
    parser.add_argument('--subtitle-lang', default='chi',
                       help='字幕语言代码（默认: chi）')
    parser.add_argument('--subtitle-title', default='Chinese',
                       help='字幕轨道名称（默认: Chinese）')
    
    # 硬编码样式选项
    parser.add_argument('--font-size', type=int, default=15,
                       help='字体大小（硬编码模式，默认: 15）')
    parser.add_argument('--font-color', default='white',
                       choices=['white', 'black', 'red', 'blue', 'green', 'yellow'],
                       help='字体颜色（硬编码模式，默认: white）')
    parser.add_argument('--outline-color', default='black',
                       choices=['white', 'black', 'red', 'blue', 'green', 'yellow'],
                       help='描边颜色（硬编码模式，默认: black）')
    parser.add_argument('--outline-width', type=int, default=1,
                       help='描边宽度（硬编码模式，默认: 1）')
    parser.add_argument('--position', choices=['top', 'bottom'], default='bottom',
                       help='字幕位置（硬编码模式，默认: bottom）')
    parser.add_argument('--margin', type=int, default=50,
                       help='垂直边距（硬编码模式，默认: 50）')
    
    args = parser.parse_args()
    
    try:
        embedder = VideoSubtitleEmbedder()
        
        video_path = Path(args.video).resolve()
        subtitle_path = Path(args.subtitle).resolve()
        
        # 自动确定输出路径
        if args.output:
            output_path = Path(args.output).resolve()
        else:
            # 根据模式自动生成文件名
            mode_suffix = {
                'hardcode': '_hardcoded',
                'soft': '_soft',
                'external': '',
                'both': '_with_subs'
            }
            suffix = mode_suffix.get(args.mode, '_subtitled')
            output_path = video_path.parent / f"{video_path.stem}{suffix}.mp4"
        
        # 检查输入
        if not video_path.exists():
            logger.error(f"[X] 视频文件不存在: {video_path}")
            return 1
        
        if not subtitle_path.exists():
            logger.error(f"[X] 字幕文件不存在: {subtitle_path}")
            return 1
        
        # 显示模式信息
        mode_desc = {
            'hardcode': '硬编码（烧录到画面）',
            'soft': '软字幕（内嵌到容器）',
            'external': '外挂字幕（独立文件）',
            'both': '软字幕 + 外挂字幕'
        }
        logger.info("=" * 60)
        logger.info(f"字幕嵌入模式: {mode_desc.get(args.mode, args.mode)}")
        logger.info("=" * 60)
        
        # 处理字幕
        success = embedder.process_subtitle(
            video_path=video_path,
            subtitle_path=subtitle_path,
            output_path=output_path,
            mode=args.mode,
            font_size=args.font_size,
            font_color=args.font_color,
            outline_color=args.outline_color,
            outline_width=args.outline_width,
            position=args.position,
            margin_v=args.margin,
            subtitle_lang=args.subtitle_lang,
            subtitle_title=args.subtitle_title
        )
        
        if success:
            print("\n" + "=" * 60)
            print("[完成] 字幕处理成功！")
            print(f"[模式] {mode_desc.get(args.mode, args.mode)}")
            print(f"[输出] {output_path}")
            if args.mode in ['external', 'both']:
                print(f"[字幕] {output_path.with_suffix('.srt')}")
                print(f"[字幕] {output_path.with_suffix('.ass')}")
            print("=" * 60)
            return 0
        else:
            print("\n[失败] 字幕处理失败")
            return 1
            
    except KeyboardInterrupt:
        print("\n[中断] 用户取消操作")
        return 1
    except Exception as e:
        logger.error(f"[错误] 程序异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

