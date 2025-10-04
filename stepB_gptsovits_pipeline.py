#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPT-SoVITS Step B Pipeline
完整的GPT-SoVITS TTS流水线：切割 → 生成.lab → TTS合成 → 音视频合并

功能:
- 根据SRT字幕文件切割音频并生成.lab文件
- 使用GPT-SoVITS进行语音合成
- 合并TTS音频与背景音乐
- 替换视频音轨
"""

import os
import sys
import json
import argparse
import logging
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Any

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

class GPTSoVITSPipeline:
    def __init__(self):
        self.project_root = Path(__file__).resolve().parent
    
    def step1_cut_audio_and_generate_lab(self, 
                                        speak_audio: str,
                                        srt_file: str,
                                        clips_dir: str,
                                        audio_format: str = 'wav',
                                        sample_rate: int = 16000,
                                        channels: int = 1,
                                        max_workers: int = 4,
                                        no_lab: bool = False,
                        generate_lab: bool = True) -> bool:
        """
        步骤1: 根据SRT切割音频并生成.lab文件
        
        Args:
            speak_audio: 人声音频文件路径
            srt_file: SRT字幕文件路径
            clips_dir: 输出切片目录
            audio_format: 音频格式 (默认: wav)
            sample_rate: 采样率
            channels: 声道数
            max_workers: 并发数
            no_lab: 是否不生成.lab文件 (废弃参数)
            generate_lab: 是否生成.lab文件 (默认: True，GPT-SoVITS需要)
            
        Returns:
            bool: 是否成功
        """
        try:
            logger.info("🔄 [Step 1] 切割音频并生成.lab文件")
            
            # 构建切割命令 (GPT-SoVITS默认需要.lab文件)
            cmd = [
                sys.executable, 'Scripts/step5_cut_audio_by_srt.py',
                str(speak_audio), str(srt_file),
                '-o', str(clips_dir),
                '--format', 'wav',  # GPT-SoVITS固定使用wav格式
                '--sample_rate', str(sample_rate),
                '--channels', str(channels),
                '--max_workers', str(max_workers)
            ]
            
            # GPT-SoVITS需要.lab文件，只有在明确不需要时才禁用
            if not generate_lab:
                cmd.append('--no_lab')
            
            # 执行切割
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
            logger.info("✅ [Step 1] 音频切割和.lab文件生成完成")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ [Step 1] 音频切割失败: {e}")
            logger.error(f"错误输出: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"❌ [Step 1] 音频切割异常: {e}")
            return False
    
    def step2_generate_batch_config(self, 
                                   translated_srt: str,
                                   clips_dir: str,
                                   batch_json: str,
                                   text_lang: str = 'auto',
                                   prompt_lang: str = 'auto',
                                   tts_output_dir: str = None,
                                   **tts_params) -> bool:
        """
        步骤2: 生成GPT-SoVITS批量推理配置
        
        Args:
            translated_srt: 翻译后的SRT文件路径
            clips_dir: 音频切片目录
            batch_json: 输出的批量配置JSON文件路径
            text_lang: 目标语言
            prompt_lang: 参考音频语言
            tts_output_dir: TTS输出目录
            **tts_params: 其他TTS参数
            
        Returns:
            bool: 是否成功
        """
        try:
            logger.info("🔄 [Step 2] 生成GPT-SoVITS批量推理配置")
            
            # 构建命令
            cmd = [
                sys.executable, 'Scripts/generate_gptsovits_batch.py',
                str(translated_srt), str(clips_dir), str(batch_json),
                '--text_lang', text_lang,
                '--prompt_lang', prompt_lang
            ]
            
            if tts_output_dir:
                cmd.extend(['--tts_output_dir', str(tts_output_dir)])
            
            # 添加TTS参数
            for key, value in tts_params.items():
                if key in ['temperature', 'top_k', 'top_p', 'speed_factor', 'repetition_penalty']:
                    cmd.extend([f'--{key}', str(value)])
                elif key == 'text_split_method':
                    cmd.extend(['--text_split_method', str(value)])
            
            # 执行生成
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
            logger.info("✅ [Step 2] 批量推理配置生成完成")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ [Step 2] 批量配置生成失败: {e}")
            logger.error(f"错误输出: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"❌ [Step 2] 批量配置生成异常: {e}")
            return False
    
    def step3_gpt_sovits_synthesis(self, 
                                  batch_json: str,
                                  mode: str = 'local',
                                  api_url: str = None,
                                  config_path: str = None) -> bool:
        """
        步骤3: GPT-SoVITS语音合成
        
        Args:
            batch_json: 批量推理配置JSON文件路径
            mode: 运行模式 ('local' 或 'api')
            api_url: API完整URL (从环境变量GPTSOVITS_API_URL获取，或手动指定)
            config_path: 本地模式配置文件路径 (默认使用tools/GPT-SoVITS/config.json)
            
        Returns:
            bool: 是否成功
        """
        try:
            logger.info("🔄 [Step 3] GPT-SoVITS语音合成")
            
            # 构建命令
            cmd = [
                sys.executable, 'Scripts/step6_tts_gptsovits.py',
                '--mode', mode,
                '--batch_json', str(batch_json)
            ]
            
            if mode == 'api':
                # 从环境变量或参数获取API URL
                final_api_url = api_url or os.getenv('GPTSOVITS_API_URL', 'http://127.0.0.1:9880')
                logger.info(f"使用API URL: {final_api_url}")
                cmd.extend(['--api_url', final_api_url])
            elif mode == 'local':
                # 使用默认配置或指定配置
                final_config = config_path or 'tools/GPT-SoVITS/config.json'
                if Path(final_config).exists():
                    cmd.extend(['--config', str(final_config)])
                else:
                    logger.info("使用GPT-SoVITS默认配置")
            
            # 执行合成
            result = subprocess.run(cmd, check=True)
            logger.info("✅ [Step 3] GPT-SoVITS语音合成完成")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ [Step 3] GPT-SoVITS合成失败: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ [Step 3] GPT-SoVITS合成异常: {e}")
            return False
    
    def step4_merge_audio_and_video(self, 
                                   tts_dir: str,
                                   background_audio: str,
                                   video_file: str,
                                   srt_file: str,
                                   output_dir: str) -> bool:
        """
        步骤4: 合并TTS音频和背景音，替换视频音轨
        
        Args:
            tts_dir: TTS输出目录
            background_audio: 背景音频文件路径
            video_file: 视频文件路径
            srt_file: SRT字幕文件路径
            output_dir: 输出目录
            
        Returns:
            bool: 是否成功
        """
        try:
            logger.info("🔄 [Step 4] 合并TTS音频和背景音，替换视频音轨")
            
            # 构建命令
            cmd = [
                sys.executable, 'Scripts/step7_merge_tts_and_mux.py',
                '--tts_dir', str(tts_dir),
                '--instru', str(background_audio),
                '--video', str(video_file),
                '--srt', str(srt_file),
                '--out_dir', str(output_dir)
            ]
            
            # 执行合并
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
            logger.info("✅ [Step 4] 音视频合并完成")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ [Step 4] 音视频合并失败: {e}")
            logger.error(f"错误输出: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"❌ [Step 4] 音视频合并异常: {e}")
            return False
    
    def run_full_pipeline(self, 
                         video_stem: str,
                         output_dir: str = None,
                         mode: str = 'local',
                         text_lang: str = 'auto',
                         prompt_lang: str = 'auto',
                         no_lab: bool = False,
                         resume: bool = False,
                         **kwargs) -> bool:
        """
        运行完整的GPT-SoVITS流水线
        
        Args:
            video_stem: 视频基名
            output_dir: 输出目录
            mode: GPT-SoVITS运行模式
            text_lang: 目标语言
            prompt_lang: 参考音频语言
            no_lab: 是否不生成.lab文件
            resume: 是否跳过已存在的步骤
            **kwargs: 其他参数
            
        Returns:
            bool: 是否成功
        """
        try:
            # 强制使用 output/<video_stem> 作为输出目录
            output_dir = Path('output') / video_stem
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 文件路径
            speak_audio = output_dir / f"{video_stem}_speak.wav"
            background_audio = output_dir / f"{video_stem}_instru.wav"
            video_file = output_dir / f"{video_stem}_video_only.mp4"
            merged_srt = output_dir / f"{video_stem}_merged_optimized.srt"
            translated_srt = output_dir / f"{video_stem}.translated.srt"
            
            clips_dir = output_dir / 'clips'
            tts_dir = output_dir / 'tts_gptsovits'
            merge_dir = output_dir / 'merge'
            batch_json = output_dir / 'gptsovits_batch.json'
            
            # 检查必需文件
            missing_files = []
            for file_path, name in [
                (speak_audio, "人声音频"),
                (merged_srt, "合并后SRT"),
                (translated_srt, "翻译后SRT")
            ]:
                if not file_path.exists():
                    missing_files.append(f"{name}: {file_path}")
            
            if missing_files:
                logger.error("❌ 缺少必需文件:")
                for missing in missing_files:
                    logger.error(f"   - {missing}")
                return False
            
            logger.info(f"🚀 开始GPT-SoVITS完整流水线")
            logger.info(f"📁 输出目录: {output_dir}")
            logger.info(f"🎵 人声音频: {speak_audio}")
            logger.info(f"📝 合并SRT: {merged_srt}")
            logger.info(f"🌐 翻译SRT: {translated_srt}")
            logger.info(f"🔧 运行模式: {mode}")
            logger.info(f"🗣️ 目标语言: {text_lang}")
            logger.info(f"🎤 参考语言: {prompt_lang}")
            
            # Step 1: 切割音频并生成.lab文件
            if resume and clips_dir.exists() and any(clips_dir.glob('*.wav')):
                logger.info("⏭️ [Step 1] 检测到已有音频切片，跳过切割步骤")
            else:
                success = self.step1_cut_audio_and_generate_lab(
                    speak_audio=speak_audio,
                    srt_file=merged_srt,
                    clips_dir=clips_dir,
                    audio_format='wav',  # GPT-SoVITS固定使用wav
                    sample_rate=kwargs.get('sample_rate', 16000),
                    channels=kwargs.get('channels', 1),
                    max_workers=kwargs.get('max_workers', 4),
                    generate_lab=True  # GPT-SoVITS需要.lab文件
                )
                if not success:
                    return False
            
            # Step 2: 生成批量推理配置
            if resume and batch_json.exists():
                logger.info("⏭️ [Step 2] 检测到已有批量配置，跳过生成步骤")
            else:
                tts_params = {
                    'temperature': kwargs.get('temperature', 1.0),
                    'top_k': kwargs.get('top_k', 5),
                    'top_p': kwargs.get('top_p', 1.0),
                    'speed_factor': kwargs.get('speed_factor', 1.0),
                    'repetition_penalty': kwargs.get('repetition_penalty', 1.35),
                    'text_split_method': kwargs.get('text_split_method', 'cut5')
                }
                # 只传递非默认值的参数
                filtered_params = {k: v for k, v in tts_params.items() 
                                 if (k == 'temperature' and v != 1.0) or
                                    (k == 'top_k' and v != 5) or
                                    (k == 'top_p' and v != 1.0) or
                                    (k == 'speed_factor' and v != 1.0) or
                                    (k == 'repetition_penalty' and v != 1.35) or
                                    (k == 'text_split_method' and v != 'cut5')}
                
                success = self.step2_generate_batch_config(
                    translated_srt=translated_srt,
                    clips_dir=clips_dir,
                    batch_json=batch_json,
                    text_lang=text_lang,
                    prompt_lang=prompt_lang,
                    tts_output_dir=tts_dir,
                    **filtered_params
                )
                if not success:
                    return False
            
            # Step 3: GPT-SoVITS语音合成
            # 检查TTS文件数量
            num_clips = len(list(clips_dir.glob('*.wav'))) if clips_dir.exists() else 0
            num_tts = len(list(tts_dir.glob('*.tts.wav'))) if tts_dir.exists() else 0
            
            if resume and tts_dir.exists() and num_tts >= num_clips and num_clips > 0:
                logger.info(f"⏭️ [Step 3] 检测到已有TTS文件 ({num_tts}/{num_clips})，跳过合成步骤")
            else:
                success = self.step3_gpt_sovits_synthesis(
                    batch_json=batch_json,
                    mode=mode,
                    api_url=kwargs.get('api_url'),
                    config_path=kwargs.get('config_path')
                )
                if not success:
                    return False
            
            # Step 4: 音视频合并
            final_video = merge_dir / f"{video_stem}_dubbed.mp4"
            if resume and final_video.exists():
                logger.info("⏭️ [Step 4] 检测到最终视频已存在，跳过合并步骤")
            else:
                # 检查可选文件
                if background_audio.exists() and video_file.exists():
                    success = self.step4_merge_audio_and_video(
                        tts_dir=tts_dir,
                        background_audio=background_audio,
                        video_file=video_file,
                        srt_file=merged_srt,
                        output_dir=merge_dir
                    )
                    if not success:
                        logger.warning("⚠️ [Step 4] 音视频合并失败，但TTS合成已完成")
                else:
                    logger.warning("⚠️ [Step 4] 缺少背景音频或视频文件，跳过音视频合并")
                    logger.info(f"   背景音频: {background_audio} (存在: {background_audio.exists()})")
                    logger.info(f"   视频文件: {video_file} (存在: {video_file.exists()})")
            
            # 显示结果
            logger.info("🎉 GPT-SoVITS流水线执行完成！")
            logger.info("📊 输出总结:")
            logger.info(f"   🎵 音频切片: {clips_dir} ({len(list(clips_dir.glob('*.wav')))} 个文件)")
            if not no_lab:
                logger.info(f"   📝 标签文件: {clips_dir} ({len(list(clips_dir.glob('*.lab')))} 个.lab文件)")
            logger.info(f"   🗣️ TTS音频: {tts_dir} ({len(list(tts_dir.glob('*.tts.wav')))} 个文件)")
            logger.info(f"   📋 批量配置: {batch_json}")
            if merge_dir.exists():
                logger.info(f"   🎬 最终视频: {merge_dir}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 流水线执行异常: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    parser = argparse.ArgumentParser(description='GPT-SoVITS Step B 完整流水线')
    
    # 基本参数
    parser.add_argument('video_stem', help='视频基名（例如 EN_test）')
    
    # 流水线控制
    parser.add_argument('--resume', action='store_true', default=False, 
                       help='跳过已存在的步骤（默认：关闭，每次重新处理所有步骤）')
    parser.add_argument('--no-lab', action='store_true', help='不生成.lab文件')
    
    # GPT-SoVITS参数
    parser.add_argument('--mode', choices=['local', 'api'], default='local', help='GPT-SoVITS运行模式')
    parser.add_argument('--text_lang', default='auto', help='目标语言')
    parser.add_argument('--prompt_lang', default='auto', help='参考音频语言')
    parser.add_argument('--api_url', help='API完整URL (从环境变量GPTSOVITS_API_URL获取)')
    parser.add_argument('--config', help='本地模式配置文件路径 (默认: tools/GPT-SoVITS/config.json)')
    
    # 音频切割参数
    parser.add_argument('--audio_format', default='wav', choices=['wav', 'mp3', 'flac'], help='音频格式')
    parser.add_argument('--sample_rate', type=int, default=16000, help='采样率')
    parser.add_argument('--channels', type=int, default=1, help='声道数')
    parser.add_argument('--max_workers', type=int, default=4, help='切割并发数')
    
    # TTS参数
    parser.add_argument('--temperature', type=float, default=1.0, help='采样温度')
    parser.add_argument('--top_k', type=int, default=5, help='Top-k采样')
    parser.add_argument('--top_p', type=float, default=1.0, help='Top-p采样')
    parser.add_argument('--speed_factor', type=float, default=1.0, help='语速控制')
    parser.add_argument('--repetition_penalty', type=float, default=1.35, help='重复惩罚')
    parser.add_argument('--text_split_method', default='cut5', help='文本分割方法')
    
    args = parser.parse_args()
    
    try:
        # 创建流水线实例
        pipeline = GPTSoVITSPipeline()
        
        # 准备参数
        kwargs = {
            'audio_format': args.audio_format,
            'sample_rate': args.sample_rate,
            'channels': args.channels,
            'max_workers': args.max_workers,
            'temperature': args.temperature,
            'top_k': args.top_k,
            'top_p': args.top_p,
            'speed_factor': args.speed_factor,
            'repetition_penalty': args.repetition_penalty,
            'text_split_method': args.text_split_method,
            'api_url': args.api_url,
            'config_path': args.config
        }
        
        # 运行流水线（输出目录固定为 output/<video_stem>）
        success = pipeline.run_full_pipeline(
            video_stem=args.video_stem,
            output_dir=None,  # 强制使用默认路径
            mode=args.mode,
            text_lang=args.text_lang,
            prompt_lang=args.prompt_lang,
            no_lab=args.no_lab,
            resume=args.resume,
            **kwargs
        )
        
        if success:
            print("\n✅ GPT-SoVITS流水线执行成功！")
            return 0
        else:
            print("\n❌ GPT-SoVITS流水线执行失败！")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断流水线执行")
        return 1
    except Exception as e:
        logger.error(f"程序异常: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
