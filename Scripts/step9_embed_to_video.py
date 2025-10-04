#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤9: 将字幕嵌入视频
使用霞鹜文楷字体将字幕硬编码（烧录）到视频中
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
    """视频字幕嵌入器"""
    
    def __init__(self):
        self.project_root = Path(__file__).resolve().parent.parent
        self.font_dir = self.project_root / 'fonts'
        self.font_file = self.font_dir / 'LXGWWenKai-Regular.ttf'
    
    def check_font(self) -> bool:
        """检查字体文件是否存在"""
        if self.font_file.exists():
            logger.info(f"[OK] 字体文件: {self.font_file}")
            return True
        else:
            logger.error(f"[X] 字体文件不存在: {self.font_file}")
            logger.info("请下载霞鹜文楷字体:")
            logger.info("  https://github.com/lxgw/LxgwWenKai/releases")
            logger.info(f"  放置到: {self.font_dir}/LXGWWenKai-Regular.ttf")
            return False
    
    def embed_subtitle(self,
                      video_path: Path,
                      subtitle_path: Path,
                      output_path: Path,
                      font_size: int = 20,
                      font_color: str = 'white',
                      outline_color: str = 'black',
                      outline_width: int = 1,
                      position: str = 'bottom',
                      margin_v: int = 50) -> bool:
        """将字幕嵌入视频"""
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
            
            logger.info("[启动] 嵌入字幕到视频...")
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
                logger.info(f"[OK] 字幕嵌入完成: {output_path}")
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
            logger.error(f"[X] 嵌入失败: {e}")
            import traceback
            traceback.print_exc()
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
        description='将字幕嵌入视频（使用霞鹜文楷字体）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 嵌入字幕（自动输出到视频目录）
  python step9_embed_to_video.py video.mp4 subtitle.srt
  
  # 指定输出路径
  python step9_embed_to_video.py video.mp4 subtitle.srt -o output.mp4
  
  # 自定义样式
  python step9_embed_to_video.py video.mp4 subtitle.srt --font-size 24 --position top
        """
    )
    
    parser.add_argument('video', help='输入视频文件路径')
    parser.add_argument('subtitle', help='字幕文件路径（已处理过的 SRT）')
    parser.add_argument('--output', '-o', help='输出视频路径（默认: 同目录 _subtitled.mp4）')
    
    # 字幕样式
    parser.add_argument('--font-size', type=int, default=15, help='字体大小（默认: 15）')
    parser.add_argument('--font-color', default='white',
                       choices=['white', 'black', 'red', 'blue', 'green', 'yellow'],
                       help='字体颜色（默认: white）')
    parser.add_argument('--outline-color', default='black',
                       choices=['white', 'black', 'red', 'blue', 'green', 'yellow'],
                       help='描边颜色（默认: black）')
    parser.add_argument('--outline-width', type=int, default=1, help='描边宽度（默认: 1）')
    parser.add_argument('--position', choices=['top', 'bottom'], default='bottom',
                       help='字幕位置（默认: bottom）')
    parser.add_argument('--margin', type=int, default=50, help='垂直边距（默认: 50）')
    
    args = parser.parse_args()
    
    try:
        embedder = VideoSubtitleEmbedder()
        
        video_path = Path(args.video).resolve()
        subtitle_path = Path(args.subtitle).resolve()
        
        # 自动确定输出路径
        if args.output:
            output_path = Path(args.output).resolve()
        else:
            output_path = video_path.parent / f"{video_path.stem}_subtitled.mp4"
        
        # 检查输入
        if not video_path.exists():
            logger.error(f"[X] 视频文件不存在: {video_path}")
            return 1
        
        if not subtitle_path.exists():
            logger.error(f"[X] 字幕文件不存在: {subtitle_path}")
            return 1
        
        # 嵌入字幕
        success = embedder.embed_subtitle(
            video_path=video_path,
            subtitle_path=subtitle_path,
            output_path=output_path,
            font_size=args.font_size,
            font_color=args.font_color,
            outline_color=args.outline_color,
            outline_width=args.outline_width,
            position=args.position,
            margin_v=args.margin
        )
        
        if success:
            print("\n[完成] 字幕嵌入成功！")
            print(f"[输出] {output_path}")
            return 0
        else:
            print("\n[失败] 字幕嵌入失败")
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

