#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的全自动视频翻译流水线
从输入视频到最终翻译音频的一站式处理

功能:
- 自动音视频分离
- 自动人声分离
- 自动语音转录 (WhisperX/FunClip)
- 自动翻译字幕
- 自动语音合成 (indextts/gptsovits)
- 自动音视频合并

使用方法:
    python full_auto_pipeline.py input_video.mp4 [选项]
"""

import os
import sys
import argparse
import logging
import subprocess
import shutil
import re
import json
from pathlib import Path
from typing import Dict, Any, Optional

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

class FullAutoPipeline:
    """完整的全自动视频翻译流水线"""

    def __init__(self):
        self.project_root = Path(__file__).resolve().parent

    def get_video_duration(self, video_path: Path) -> Optional[float]:
        """
        获取视频时长（秒）

        Args:
            video_path: 视频文件路径

        Returns:
            float: 视频时长（秒），失败返回None
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'json',
                str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            duration = float(data['format']['duration'])
            return duration
        except Exception as e:
            logger.warning(f"无法获取视频时长: {e}")
            return None

    def get_srt_duration(self, srt_path: Path) -> Optional[float]:
        """
        获取SRT字幕文件的时长（最后一个字幕的结束时间）

        Args:
            srt_path: SRT文件路径

        Returns:
            float: 字幕时长（秒），失败返回None
        """
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 匹配SRT时间戳格式：00:00:00,000 --> 00:00:00,000
            time_pattern = r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})'
            matches = re.findall(time_pattern, content)

            if not matches:
                logger.warning("SRT文件中没有找到时间戳")
                return None

            # 获取最后一个字幕的结束时间
            last_match = matches[-1]
            end_h, end_m, end_s, end_ms = int(last_match[4]), int(last_match[5]), int(last_match[6]), int(last_match[7])

            # 转换为秒
            duration = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000.0
            return duration

        except Exception as e:
            logger.warning(f"无法获取SRT时长: {e}")
            return None

    def validate_duration_match(self, video_path: Path, srt_path: Path, tolerance: float = 10.0) -> tuple[bool, float]:
        """
        验证视频时长和字幕时长是否匹配

        Args:
            video_path: 视频文件路径
            srt_path: SRT字幕文件路径
            tolerance: 允许的误差（秒），默认10秒

        Returns:
            tuple[bool, float]: (是否匹配, 时长差异秒数)
        """
        video_duration = self.get_video_duration(video_path)
        srt_duration = self.get_srt_duration(srt_path)

        if video_duration is None or srt_duration is None:
            logger.warning("无法验证时长匹配，跳过检查")
            return True, 0.0

        difference = abs(video_duration - srt_duration)

        logger.info(f"📊 时长检查:")
        logger.info(f"   视频时长: {video_duration:.2f}秒 ({video_duration/60:.1f}分钟)")
        logger.info(f"   字幕时长: {srt_duration:.2f}秒 ({srt_duration/60:.1f}分钟)")
        logger.info(f"   时长差异: {difference:.2f}秒")

        if difference > tolerance:
            logger.warning(
                f"⚠️ 字幕时长差异较大:\n"
                f"   视频时长: {video_duration:.2f}秒\n"
                f"   字幕时长: {srt_duration:.2f}秒\n"
                f"   差异: {difference:.2f}秒（超过容忍度 {tolerance}秒）\n"
                f"   可能原因：LLM翻译时产生幻觉，时间戳格式错误"
            )
            return False, difference

        logger.info(f"✅ 时长验证通过（差异 {difference:.2f}秒 <= 容忍度 {tolerance}秒）")
        return True, difference

    def detect_language(self, video_path: str) -> str:
        """
        智能检测视频语言
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            str: 检测到的语言代码 (zh/en/ja/ko/auto)
        """
        # 简单的文件名语言检测
        filename = Path(video_path).stem.lower()
        
        if any(keyword in filename for keyword in ['zh', 'chinese', '中文', '中']):
            return 'zh'
        elif any(keyword in filename for keyword in ['en', 'english', '英文', '英']):
            return 'en'
        elif any(keyword in filename for keyword in ['ja', 'japanese', '日文', '日']):
            return 'ja'
        elif any(keyword in filename for keyword in ['ko', 'korean', '韩文', '韩']):
            return 'ko'
        else:
            return 'auto'
    
    def determine_target_language(self, source_lang: str) -> str:
        """
        根据源语言确定目标翻译语言
        
        Args:
            source_lang: 源语言
            
        Returns:
            str: 目标语言
        """
        # 默认翻译策略：中文->英文，其他->中文
        if source_lang in ['zh', 'chinese']:
            return 'en'
        else:
            return 'zh'
    
    def choose_transcription_engine(self, source_lang: str) -> str:
        """
        根据语言选择最佳转录引擎
        
        Args:
            source_lang: 源语言
            
        Returns:
            str: 转录引擎 (whisperx/funclip)
        """
        # 默认使用WhisperX，它支持多语言自动识别
        # FunClip也支持自动识别，但主要针对中文优化
        return 'whisperx'
    
    def step1_prepare_and_transcribe(self,
                                   video_path: str,
                                   video_stem: str,
                                   output_dir: Path,
                                   engine: str = 'whisperx',
                                   language: str = 'auto',
                                   enable_diarization: bool = True,
                                   enable_separation: bool = True) -> bool:
        """
        步骤1: 音视频处理和转录
        
        Args:
            video_path: 输入视频路径
            video_stem: 视频基名
            engine: 转录引擎 (whisperx/funclip)
            language: 语言 (auto - 自动识别)
            enable_diarization: 是否启用说话人识别
            enable_separation: 是否启用人声分离
            
        Returns:
            bool: 是否成功
        """
        try:
            logger.info("🔄 [Step 1] 音视频处理和转录")
            
            # 使用传入的输出目录（命名空间或默认）
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"使用转录引擎: {engine}")
            logger.info(f"语言设置: {language} (自动识别)")
            
            # 构建stepA命令（输出目录固定为 output/<video_stem>）
            cmd = [
                sys.executable, 'stepA_prepare_and_blank_srt.py',
                str(video_path),
                '-l', language
            ]
            
            if not enable_diarization:
                cmd.append('--no-diarize')
            # 传递人声分离开关（当禁用分离时，向 stepA 传入 --no-separation）
            if not enable_separation:
                cmd.append('--no-separation')
            
            # 执行stepA (修复编码问题)
            result = subprocess.run(cmd, check=True, capture_output=False, text=False)
            logger.info("✅ [Step 1] 音视频处理和转录完成")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ [Step 1] 音视频处理失败: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ [Step 1] 音视频处理异常: {e}")
            return False
    
    def step2_translate_subtitles(self,
                                output_dir: str,
                                video_stem: str,
                                video_path: Path,
                                target_lang: str = 'auto',
                                mode: str = 'whole') -> bool:
        """
        步骤2: 翻译字幕

        Args:
            output_dir: 输出目录
            video_stem: 视频基名
            video_path: 原始视频文件路径（用于时长验证）
            target_lang: 目标语言
            mode: 翻译模式

        Returns:
            bool: 是否成功
        """
        try:
            logger.info("🔄 [Step 2] 翻译字幕")

            output_path = Path(output_dir)
            srt_file = output_path / f"{video_stem}.srt"

            if not srt_file.exists():
                logger.error(f"SRT文件不存在: {srt_file}")
                return False

            # 自动确定目标语言
            if target_lang == 'auto':
                source_lang = self.detect_language(video_stem)
                target_lang = self.determine_target_language(source_lang)
                logger.info(f"目标翻译语言: {target_lang}")

            # 构建翻译命令
            translate_script = self.project_root / 'Scripts' / 'step4_translate_srt.py'
            cmd = [
                sys.executable, str(translate_script),
                str(srt_file),
                '--target_lang', target_lang
            ]

            # 添加翻译模式参数
            if mode == 'whole':
                cmd.append('--whole_file')

            # 执行翻译 (修复编码问题)
            result = subprocess.run(cmd, check=True, capture_output=False, text=False)
            logger.info("✅ [Step 2] 字幕翻译完成")

            # 验证翻译后的字幕时长（容忍度：2分钟）
            translated_srt = output_path / f"{video_stem}.translated.srt"
            original_srt = output_path / f"{video_stem}.srt"

            if translated_srt.exists():
                logger.info("🔍 [Step 2] 验证翻译后字幕时长...")
                is_valid, difference = self.validate_duration_match(video_path, translated_srt, tolerance=120.0)

                if not is_valid:
                    logger.warning(f"⚠️ [Step 2] 检测到字幕时长异常（差异: {difference:.2f}秒），尝试自动修复...")

                    # 自动调用修复工具
                    try:
                        fix_script = self.project_root / "Scripts" / "fix_translated_srt.py"
                        if not fix_script.exists():
                            logger.error(f"修复工具不存在: {fix_script}")
                            logger.error("字幕时长异常但无法自动修复，请手动检查")
                            return False

                        # 调用修复工具
                        cmd = [
                            sys.executable,
                            str(fix_script),
                            str(original_srt),
                            str(translated_srt)
                        ]

                        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

                        if result.returncode == 0:
                            logger.info("✅ [Step 2] 字幕时间戳自动修复完成")
                            logger.info(result.stdout)

                            # 修复后再次验证
                            logger.info("🔍 [Step 2] 重新验证修复后的字幕时长...")
                            is_valid_after, difference_after = self.validate_duration_match(
                                video_path, translated_srt, tolerance=120.0
                            )

                            if not is_valid_after:
                                logger.warning(
                                    f"⚠️ [Step 2] 修复后字幕时长仍然异常（差异: {difference_after:.2f}秒）\n"
                                    f"   这可能是LLM翻译时添加/删除了字幕条目\n"
                                    f"   将继续处理，但请手动检查字幕文件"
                                )
                        else:
                            logger.error(f"❌ [Step 2] 字幕修复失败: {result.stderr}")
                            logger.warning("将继续处理，但字幕时长可能存在问题")

                    except Exception as e:
                        logger.error(f"❌ [Step 2] 执行修复工具时出错: {e}")
                        logger.warning("将继续处理，但字幕时长可能存在问题")
            else:
                logger.warning(f"翻译后的字幕文件不存在，跳过时长验证: {translated_srt}")

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ [Step 2] 字幕翻译失败: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ [Step 2] 字幕翻译异常: {e}")
            return False
    
    def step3_index_tts_synthesis(self,
                                video_stem: str,
                                target_lang: str,
                                output_dir: Path) -> bool:
        """
        步骤3: IndexTTS语音合成 (默认TTS引擎)
        
        Args:
            video_stem: 视频基名
            target_lang: 目标语言 (zh/en - 必填)
            
        Returns:
            bool: 是否成功
        """
        try:
            logger.info("🔄 [Step 3] IndexTTS语音合成")
            
            # 验证目标语言
            if target_lang not in ['zh', 'en']:
                logger.error(f"IndexTTS不支持的目标语言: {target_lang}")
                return False
            
            # 构建stepB_index_pipeline命令（输出目录固定为 output/<video_stem>）
            cmd = [
                sys.executable, 'stepB_index_pipeline.py',
                video_stem,
                '--resume'
            ]
            
            # 执行IndexTTS合成 (修复编码问题)
            result = subprocess.run(cmd, check=True, capture_output=False, text=False)
            logger.info("✅ [Step 3] IndexTTS语音合成完成")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ [Step 3] IndexTTS合成失败: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ [Step 3] IndexTTS合成异常: {e}")
            return False
    
    def step3_gpt_sovits_synthesis(self,
                                 video_stem: str,
                                 output_dir: Path,
                                 text_lang: str = 'auto',
                                 prompt_lang: str = 'auto',
                                 mode: str = 'local') -> bool:
        """
        步骤3: GPT-SoVITS语音合成 (备选TTS引擎)
        
        Args:
            video_stem: 视频基名
            text_lang: 目标语言 (auto/zh/en/ja/ko)
            prompt_lang: 参考语言 (auto/zh/en/ja/ko)
            mode: 运行模式 (api优先，失败后local)
            
        Returns:
            bool: 是否成功
        """
        try:
            logger.info("🔄 [Step 3] GPT-SoVITS语音合成")
            
            # 自动确定语言参数
            if text_lang == 'auto':
                source_lang = self.detect_language(video_stem)
                text_lang = self.determine_target_language(source_lang)
                logger.info(f"TTS目标语言: {text_lang}")
            
            if prompt_lang == 'auto':
                prompt_lang = self.detect_language(video_stem)
                logger.info(f"参考音频语言: {prompt_lang}")
            
            # 根据 mode 优先顺序执行（输出目录固定为 output/<video_stem>）
            if mode == 'local':
                logger.info("使用本地模式...")
                try:
                    cmd = [
                        sys.executable, 'stepB_gptsovits_pipeline.py',
                        video_stem,
                        '--resume',
                        '--mode', 'local',
                        '--text_lang', text_lang,
                        '--prompt_lang', prompt_lang
                    ]
                    result = subprocess.run(cmd, check=True, capture_output=False, text=False)
                    logger.info("✅ [Step 3] GPT-SoVITS本地模式合成完成")
                    return True
                except subprocess.CalledProcessError:
                    logger.warning("⚠️ 本地模式失败，尝试 API 模式...")
                    mode = 'api'

            if mode == 'api':
                logger.info("尝试使用API模式...")
                cmd = [
                    sys.executable, 'stepB_gptsovits_pipeline.py',
                    video_stem,
                    '--resume',
                    '--mode', 'api',
                    '--text_lang', text_lang,
                    '--prompt_lang', prompt_lang
                ]
                result = subprocess.run(cmd, check=True, capture_output=False, text=False)
                logger.info("✅ [Step 3] GPT-SoVITS API模式合成完成")
                return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ [Step 3] GPT-SoVITS合成失败: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ [Step 3] GPT-SoVITS合成异常: {e}")
            return False
    
    def run_full_pipeline(self, 
                         video_path: str,
                         output_dir: Optional[str] = None,
                         engine: str = 'whisperx',
                         language: str = 'auto',
                         target_lang: str = None,
                         tts_engine: str = 'indextts',
                         tts_mode: str = 'local',
                         enable_diarization: bool = True,
                         enable_separation: bool = True,
                         translation_mode: str = 'whole',
                         embed_subtitle: bool = False,
                         subtitle_bilingual: bool = False) -> bool:
        """
        运行完整的全自动流水线
        
        Args:
            video_path: 输入视频路径
            output_dir: 输出目录 (废弃，使用固定格式)
            engine: 转录引擎 (whisperx/funclip，默认whisperx)
            language: 源语言 (auto - 自动识别)
            target_lang: 目标语言 (必填，IndexTTS支持zh/en，GPT-SoVITS支持zh/en/ja/ko)
            tts_engine: TTS引擎 (indextts/gptsovits，默认indextts)
            enable_diarization: 是否启用说话人识别
            enable_separation: 是否启用人声分离
            translation_mode: 翻译模式 (whole/smart)
            
        Returns:
            bool: 是否成功
        """
        try:
            # 验证输入文件
            video_path = Path(video_path).resolve()
            if not video_path.exists():
                logger.error(f"输入视频不存在: {video_path}")
                return False
            
            video_stem = video_path.stem
            
            # 验证目标语言参数
            if target_lang is None:
                logger.error("目标语言是必填参数")
                return False
            
            # 验证TTS引擎和语言兼容性
            if tts_engine == 'indextts' and target_lang not in ['zh', 'en']:
                logger.error(f"IndexTTS只支持中文(zh)和英文(en)，不支持: {target_lang}")
                return False
            
            # 输出目录：优先使用传入 -o，否则回退到 output/<video_stem>
            output_dir = Path(output_dir) if output_dir else (Path('output') / video_stem)
            
            logger.info("🚀 开始全自动视频翻译流水线")
            logger.info(f"📁 输入视频: {video_path}")
            logger.info(f"📁 输出目录: {output_dir}")
            logger.info(f"🔧 转录引擎: {engine}")
            logger.info(f"🗣️ 源语言: {language} (自动识别)")
            logger.info(f"🌐 目标语言: {target_lang}")
            logger.info(f"🎵 TTS引擎: {tts_engine}")
            if tts_engine == 'gptsovits':
                logger.info(f"🧩 GPT-SoVITS模式: {tts_mode}")
            logger.info(f"👥 说话人识别: {'启用' if enable_diarization else '禁用'}")
            logger.info(f"🎤 人声分离: {'启用' if enable_separation else '禁用'}")
            logger.info(f"📝 翻译模式: {translation_mode}")
            
            # Step 1: 音视频处理和转录
            success = self.step1_prepare_and_transcribe(
                video_path=video_path,
                video_stem=video_stem,
                output_dir=output_dir,
                engine=engine,
                language=language,
                enable_diarization=enable_diarization,
                enable_separation=enable_separation
            )
            if not success:
                return False
            
            # Step 2: 翻译字幕
            success = self.step2_translate_subtitles(
                output_dir=output_dir,
                video_stem=video_stem,
                video_path=video_path,
                target_lang=target_lang,
                mode=translation_mode
            )
            if not success:
                return False
            
            # Step 3: TTS语音合成
            if tts_engine == 'indextts':
                success = self.step3_index_tts_synthesis(
                    video_stem=video_stem,
                    target_lang=target_lang,
                    output_dir=output_dir
                )
            elif tts_engine == 'gptsovits':
                # 自动确定GPT-SoVITS语言参数
                final_text_lang = target_lang
                final_prompt_lang = self.detect_language(str(video_path))
                
                success = self.step3_gpt_sovits_synthesis(
                    video_stem=video_stem,
                    output_dir=output_dir,
                    text_lang=final_text_lang,
                    prompt_lang=final_prompt_lang,
                    mode=tts_mode  # 遵循 CLI 传入或默认本地，并在失败时尝试另一模式
                )
            else:
                logger.error(f"不支持的TTS引擎: {tts_engine}")
                return False
            
            if not success:
                return False
            
            # 显示最终结果
            logger.info("🎉 全自动视频翻译流水线执行完成！")
            
            # 检查生成的文件 (根据TTS引擎类型)
            if tts_engine == 'indextts':
                tts_dir = output_dir / 'tts'
                merge_dir = output_dir / 'merge'
            else:  # gptsovits
                tts_dir = output_dir / 'tts_gptsovits'
                merge_dir = output_dir / 'merge'
            
            if tts_dir.exists():
                tts_files = list(tts_dir.glob('*.wav'))
                tts_count = len(tts_files)
                logger.info(f"🎵 生成TTS音频: {tts_count} 个文件")
                logger.info(f"📁 TTS目录: {tts_dir}")
            
            if merge_dir.exists():
                final_videos = list(merge_dir.glob('*.mp4'))
                if final_videos:
                    logger.info(f"🎬 最终视频: {final_videos[0]}")
                else:
                    logger.info("🎬 最终视频: 生成中或未生成")
                logger.info(f"📁 合并目录: {merge_dir}")
            
            # 检查重要的中间文件
            srt_file = output_dir / f"{video_stem}.srt"
            translated_srt = output_dir / f"{video_stem}.translated.srt"
            merged_srt = output_dir / f"{video_stem}_merged_optimized.srt"
            
            if srt_file.exists():
                logger.info(f"📝 原始字幕: {srt_file}")
            if translated_srt.exists():
                logger.info(f"🌐 翻译字幕: {translated_srt}")
            if merged_srt.exists():
                logger.info(f"🔀 合并字幕: {merged_srt}")
            
            logger.info("✅ 流水线执行成功！所有步骤已完成。")
            
            # 可选步骤：嵌入字幕
            if embed_subtitle:
                logger.info("🔄 [Optional] 嵌入字幕到视频")
                try:
                    cmd = [
                        sys.executable, 'stepC_embed_subtitles.py',
                        video_stem,
                        '--no-pause'  # 自动模式，不暂停等待
                    ]
                    
                    if subtitle_bilingual:
                        cmd.append('--bilingual')
                    
                    result = subprocess.run(cmd, check=True, capture_output=False, text=False)
                    logger.info("✅ [Optional] 字幕嵌入完成")
                except subprocess.CalledProcessError as e:
                    logger.warning(f"⚠️ [Optional] 字幕嵌入失败: {e}")
                    logger.warning("主流程已完成，字幕嵌入失败不影响整体结果")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 全自动流水线执行异常: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    parser = argparse.ArgumentParser(
        description='完整的全自动视频翻译流水线',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 基本用法 - 使用IndexTTS将中文视频翻译为英文
  python full_auto_pipeline.py chinese_video.mp4 --target_lang en
  
  # 使用IndexTTS将英文视频翻译为中文  
  python full_auto_pipeline.py english_video.mp4 --target_lang zh
  
  # 使用FunClip转录引擎
  python full_auto_pipeline.py video.mp4 --engine funclip --target_lang en
  
  # 使用GPT-SoVITS进行多语言合成
  python full_auto_pipeline.py video.mp4 --target_lang ja --tts_engine gptsovits
  
  # 禁用说话人识别和人声分离 (加快处理速度)
  python full_auto_pipeline.py video.mp4 --target_lang zh --no-diarization --no-separation
  
  # 使用智能翻译模式
  python full_auto_pipeline.py video.mp4 --target_lang en --translation_mode smart
        """
    )
    
    # 必需参数
    parser.add_argument('video_path', help='输入视频文件路径')
    
    
    # 转录设置
    parser.add_argument('--engine', choices=['whisperx', 'funclip'], default='whisperx',
                       help='转录引擎选择 (默认: whisperx)')
    parser.add_argument('--language', choices=['auto'], default='auto',
                       help='源语言 (自动识别)')
    
    # 翻译设置
    parser.add_argument('--target_lang', choices=['zh', 'en', 'ja', 'ko'], required=True,
                       help='目标翻译语言 (必填)')
    parser.add_argument('--translation_mode', choices=['whole', 'smart'], default='whole',
                       help='翻译模式 (默认: whole)')
    
    # TTS设置
    parser.add_argument('--tts_engine', choices=['indextts', 'gptsovits'], default='indextts',
                       help='TTS引擎 (默认: indextts)')
    parser.add_argument('--tts_mode', choices=['local', 'api'], default='local',
                       help='GPT-SoVITS运行模式 (默认: local，失败后自动尝试 api)')  # 仅用于GPT-SoVITS
    
    # 功能开关
    parser.add_argument('--no-diarization', action='store_true',
                       help='禁用说话人识别 (加快处理速度)')
    parser.add_argument('--no-separation', action='store_true',
                       help='禁用人声分离 (加快处理速度)')
    
    # 字幕嵌入选项
    parser.add_argument('--embed-subtitle', action='store_true',
                       help='嵌入字幕到最终视频（默认: 不嵌入）')
    parser.add_argument('--subtitle-bilingual', action='store_true',
                       help='使用双语字幕（需配合 --embed-subtitle）')
    
    # 其他选项
    parser.add_argument('--resume', action='store_true',
                       help='跳过已存在的步骤 (实验性功能)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='显示详细日志')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # 创建流水线实例
        pipeline = FullAutoPipeline()
        
        # 运行流水线（输出目录固定为 output/<video_stem>）
        success = pipeline.run_full_pipeline(
            video_path=args.video_path,
            output_dir=None,  # 强制使用默认路径
            engine='whisperx',  # 固定使用 whisperx
            language=args.language,
            target_lang=args.target_lang,
            tts_engine=args.tts_engine,
            tts_mode=args.tts_mode,
            enable_diarization=not args.no_diarization,
            enable_separation=not args.no_separation,
            translation_mode=args.translation_mode,
            embed_subtitle=args.embed_subtitle,
            subtitle_bilingual=args.subtitle_bilingual
        )
        
        if success:
            print("\n✅ 全自动视频翻译流水线执行成功！")
            print("🎉 您的视频已完成翻译和语音合成处理！")
            return 0
        else:
            print("\n❌ 全自动视频翻译流水线执行失败！")
            print("请检查日志输出以了解详细错误信息。")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断流水线执行")
        return 1
    except Exception as e:
        logger.error(f"程序异常: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
