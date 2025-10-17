#!/usr/bin/env python3
"""
Faster Whisper 字幕生成工具
基于faster_whisper的高效字幕生成，支持多语种
"""

import os
import sys
import argparse
import warnings
from pathlib import Path
from faster_whisper import WhisperModel
import json
from typing import Optional, List, Dict, Any
import time
import torch
from dotenv import load_dotenv

# Speaker diarization imports
try:
    from pyannote.audio import Pipeline
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False
    print("WARNING: pyannote.audio not available, speaker diarization disabled")

# Simplified/Traditional Chinese conversion
try:
    from opencc import OpenCC
    OPENCC_AVAILABLE = True
    cc = OpenCC('t2s')  # 繁体到简体
except ImportError:
    OPENCC_AVAILABLE = False
    print("INFO: opencc not available, Traditional Chinese will not be converted to Simplified Chinese")


# 支持的文件扩展名
SUPPORTED_EXTENSIONS = ['.mp4', '.wav', '.mp3', '.m4a', '.flac', '.ogg', '.wma', '.aac', '.avi', '.mkv', '.mov']

# 支持的语言代码
SUPPORTED_LANGUAGES = {
    "auto": "自动检测",
    "en": "English",
    "zh": "Chinese",
    "ja": "Japanese", 
    "ko": "Korean",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "ru": "Russian",
    "ar": "Arabic",
    "pt": "Portuguese",
    "it": "Italian",
    "nl": "Dutch",
    "tr": "Turkish",
    "pl": "Polish",
    "sv": "Swedish",
    "da": "Danish",
    "no": "Norwegian",
    "fi": "Finnish",
    "cs": "Czech",
    "hu": "Hungarian",
    "he": "Hebrew",
    "hi": "Hindi",
    "th": "Thai",
    "vi": "Vietnamese",
    "id": "Indonesian",
    "ms": "Malay",
    "tl": "Filipino",
    "uk": "Ukrainian",
    "bg": "Bulgarian",
    "hr": "Croatian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "et": "Estonian",
    "lv": "Latvian",
    "lt": "Lithuanian",
    "ro": "Romanian",
    "mt": "Maltese",
    "is": "Icelandic",
    "ga": "Irish",
    "cy": "Welsh",
    "eu": "Basque",
    "ca": "Catalan",
    "gl": "Galician",
}

class FasterWhisperSubtitleGenerator:
    def __init__(self, 
                 model_path: str = "./models/faster-whisper-large-v3",
                 device: str = "cuda",
                 compute_type: str = "float16",
                 diarize: bool = False,
                 hf_token: Optional[str] = None):
        """
        初始化Faster Whisper字幕生成器
        
        Args:
            model_path: 本地whisper模型路径
            device: 计算设备 ("cuda" 或 "cpu")
            compute_type: 计算精度 ("float16", "float32", "int8")
            diarize: 是否启用说话人识别
            hf_token: Hugging Face token（说话人识别需要）
        """
        # 加载环境变量，寻找项目根目录的.env文件
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent.parent  # 回到项目根目录
        env_path = project_root / '.env'
        load_dotenv(env_path)
        
        self.model_path = model_path
        self.device = device
        self.compute_type = compute_type
        self.diarize = diarize and PYANNOTE_AVAILABLE
        # 优先使用传入的token，否则从环境变量获取
        self.hf_token = hf_token or os.getenv('HUGGINGFACE_TOKEN')
        self.model = None
        self.diarization_pipeline = None
        
        if self.diarize and not PYANNOTE_AVAILABLE:
            print("WARNING: Speaker diarization requires pyannote.audio, feature disabled")
            self.diarize = False
        
        # 检查CUDA可用性
        import torch
        if device == "cuda" and not torch.cuda.is_available():
            print("WARNING: CUDA not available, switching to CPU mode")
            self.device = "cpu"
            self.compute_type = "float32"
        elif device == "cpu" and compute_type == "float16":
            print("WARNING: CPU does not support float16, switching to float32")
            self.compute_type = "float32"
    
    def load_model(self):
        """加载模型"""
        if self.model is not None:
            return

        print("Loading model...")
        print(f"Model path: {self.model_path}")
        print(f"Device: {self.device}")
        print(f"Compute type: {self.compute_type}")

        try:
            # 检查是否为本地路径
            if os.path.exists(self.model_path):
                # 本地模型存在，直接加载
                print(f"Loading model from local path: {self.model_path}")
                model_name_or_path = self.model_path
            else:
                # 本地模型不存在，尝试从HuggingFace下载
                print(f"Local model not found at: {self.model_path}")

                # 从路径中提取模型名称
                model_basename = os.path.basename(self.model_path)

                # 模型名称映射表
                model_mapping = {
                    'faster-whisper-tiny': 'Systran/faster-whisper-tiny',
                    'faster-whisper-tiny.en': 'Systran/faster-whisper-tiny.en',
                    'faster-whisper-base': 'Systran/faster-whisper-base',
                    'faster-whisper-base.en': 'Systran/faster-whisper-base.en',
                    'faster-whisper-small': 'Systran/faster-whisper-small',
                    'faster-whisper-small.en': 'Systran/faster-whisper-small.en',
                    'faster-whisper-medium': 'Systran/faster-whisper-medium',
                    'faster-whisper-medium.en': 'Systran/faster-whisper-medium.en',
                    'faster-whisper-large-v1': 'Systran/faster-whisper-large-v1',
                    'faster-whisper-large-v2': 'Systran/faster-whisper-large-v2',
                    'faster-whisper-large-v3': 'Systran/faster-whisper-large-v3',
                }

                # 尝试从映射表中获取HuggingFace repo ID
                repo_id = model_mapping.get(model_basename, None)

                if repo_id:
                    print(f"Attempting to download model from HuggingFace: {repo_id}")
                    model_name_or_path = repo_id
                else:
                    # 如果不在映射表中，假设它本身就是一个repo ID
                    print(f"Attempting to load model as HuggingFace repo ID: {self.model_path}")
                    model_name_or_path = self.model_path

            self.model = WhisperModel(
                model_name_or_path,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=4,
                num_workers=1
            )
            print("Model loaded successfully")

        except Exception as e:
            print(f"Model loading failed: {e}")
            raise
    
    def load_diarization_pipeline(self):
        """加载说话人识别管道"""
        if not self.diarize or not PYANNOTE_AVAILABLE:
            return
            
        try:
            print("Loading speaker diarization model...")
            # 设置Hugging Face token环境变量
            if self.hf_token:
                os.environ['HF_TOKEN'] = self.hf_token
                os.environ['HUGGINGFACE_HUB_TOKEN'] = self.hf_token
            
            # pyannote 4.0 从环境变量自动读取 token，不需要传参
            self.diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1"
            )
            if torch.cuda.is_available() and self.device == "cuda":
                self.diarization_pipeline = self.diarization_pipeline.to(torch.device("cuda"))
            print("Speaker diarization model loaded successfully")
        except Exception as e:
            print(f"Speaker diarization model loading failed: {e}")
            self.diarization_pipeline = None
            # 保持self.diarize=True以确保格式一致性，即使识别失败也使用默认说话人标签
    
    def perform_diarization(self, audio_file: str, min_speakers: int = 1, max_speakers: int = 5) -> Dict[str, Any]:
        """
        执行说话人识别

        Args:
            audio_file: 音频文件路径
            min_speakers: 最少说话人数（默认1）
            max_speakers: 最多说话人数（默认5）
        """
        if not self.diarize or not self.diarization_pipeline:
            return {}

        try:
            print(f"Performing speaker diarization (min_speakers={min_speakers}, max_speakers={max_speakers})...")
            diarization = self.diarization_pipeline(audio_file, min_speakers=min_speakers, max_speakers=max_speakers)
            
            # 将结果转换为时间段和说话人映射
            speaker_segments = {}
            speaker_labels = set()
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                start_time = turn.start
                end_time = turn.end
                # 将PyAnnote的说话人标签转换为spkX格式
                if speaker.startswith("SPEAKER_"):
                    speaker_num = speaker.replace("SPEAKER_", "")
                    converted_speaker = f"spk{speaker_num}"
                else:
                    # 如果不是SPEAKER_格式，尝试提取数字或使用原始标签
                    import re
                    match = re.search(r'\d+', speaker)
                    if match:
                        converted_speaker = f"spk{match.group()}"
                    else:
                        converted_speaker = speaker
                
                speaker_segments[(start_time, end_time)] = converted_speaker
                speaker_labels.add(converted_speaker)
            
            print(f"Speaker diarization completed, detected {len(set(speaker_segments.values()))} speakers")
            print(f"Speaker labels found: {sorted(speaker_labels)}")
            return speaker_segments
        except Exception as e:
            print(f"Speaker diarization failed: {e}")
            return {}
    
    def assign_speakers_to_segments(self, segments, speaker_segments):
        """为转录片段分配说话人，返回说话人映射字典"""
        speaker_mapping = {}
        
        for i, segment in enumerate(segments):
            if not speaker_segments:
                # 说话人识别失败时，所有片段都分配为spk0（将转换为speaker_1）
                speaker_mapping[i] = "spk0"
                continue
                
            segment_start = segment.start
            segment_end = segment.end
            
            # 找到重叠最大的说话人片段
            best_speaker = "spk0"  # 默认说话人
            max_overlap = 0
            
            for (speaker_start, speaker_end), speaker in speaker_segments.items():
                # 计算重叠时间
                overlap_start = max(segment_start, speaker_start)
                overlap_end = min(segment_end, speaker_end)
                overlap_duration = max(0, overlap_end - overlap_start)
                
                if overlap_duration > max_overlap:
                    max_overlap = overlap_duration
                    best_speaker = speaker
            
            # 记录segment的说话人信息
            speaker_mapping[i] = best_speaker
            
        return speaker_mapping
    
    def transcribe_audio(self,
                        audio_path: str,
                        language: str = "auto",
                        initial_prompt: str = "",
                        beam_size: int = 5,
                        best_of: int = 5,
                        temperature: float = 0.0,
                        condition_on_previous_text: bool = True,
                        vad_filter: bool = True,
                        vad_parameters: Optional[Dict[str, Any]] = None,
                        min_speakers: int = 1,
                        max_speakers: int = 5) -> Dict[str, Any]:
        """
        转录音频文件

        Args:
            audio_path: 音频/视频文件路径
            language: 语言代码，"auto"为自动检测
            initial_prompt: 初始提示词
            beam_size: 束搜索大小
            best_of: 最佳候选数
            temperature: 采样温度
            condition_on_previous_text: 是否基于前文条件化
            vad_filter: 是否启用VAD过滤
            vad_parameters: VAD参数
            min_speakers: 最少说话人数（用于说话人识别）
            max_speakers: 最多说话人数（用于说话人识别）

        Returns:
            转录结果字典
        """
        print(f"Starting transcription: {audio_path}")
        
        # 检查文件是否存在
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"File not found: {audio_path}")
        
        # 加载模型
        self.load_model()
        
        # 加载说话人识别模型（如果启用）
        if self.diarize:
            self.load_diarization_pipeline()
        
        # 确定语言参数
        lang_param = None if language == "auto" else language
        
        # 设置VAD参数
        if vad_parameters is None:
            vad_parameters = {
                "threshold": 0.5,
                "min_speech_duration_ms": 250,
                "max_speech_duration_s": 30,
                "min_silence_duration_ms": 100,
                "speech_pad_ms": 400,
            }
        
        try:
            start_time = time.time()
            
            # 转录
            segments, info = self.model.transcribe(
                audio_path,
                language=lang_param,
                initial_prompt=initial_prompt if initial_prompt else None,
                beam_size=beam_size,
                best_of=best_of,
                temperature=temperature,
                condition_on_previous_text=condition_on_previous_text,
                vad_filter=vad_filter,
                vad_parameters=vad_parameters,
                word_timestamps=True
            )
            
            # 执行说话人识别（如果启用）
            speaker_segments = {}
            if self.diarize:
                speaker_segments = self.perform_diarization(audio_path, min_speakers, max_speakers)
            
            # 收集结果并分配说话人
            result_segments = []
            segments_list = list(segments)  # 转换为列表以便重复使用
            
            # 为每个片段分配说话人（如果识别失败则使用默认值）
            speaker_mapping = self.assign_speakers_to_segments(segments_list, speaker_segments)
            
            for i, segment in enumerate(segments_list):
                segment_dict = {
                    "id": segment.id,
                    "seek": segment.seek,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "temperature": segment.temperature,
                    "avg_logprob": segment.avg_logprob,
                    "compression_ratio": segment.compression_ratio,
                    "no_speech_prob": segment.no_speech_prob,
                    "speaker": speaker_mapping.get(i, 'spk0'),  # 使用映射中的说话人信息
                    "words": []
                }
                
                # 添加单词级时间戳
                if segment.words:
                    for word in segment.words:
                        word_dict = {
                            "start": word.start,
                            "end": word.end,
                            "word": word.word,
                            "probability": word.probability
                        }
                        segment_dict["words"].append(word_dict)
                
                result_segments.append(segment_dict)
            
            elapsed_time = time.time() - start_time
            
            # 构建结果
            result = {
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration,
                "duration_after_vad": info.duration_after_vad,
                "segments": result_segments,
                "processing_time": elapsed_time
            }
            
            print(f"Detected language: {SUPPORTED_LANGUAGES.get(info.language, info.language)} (confidence: {info.language_probability:.2f})")
            print(f"Processing time: {elapsed_time:.2f} seconds")
            print(f"Audio duration: {info.duration:.2f} seconds")
            if info.duration_after_vad:
                print(f"Duration after VAD: {info.duration_after_vad:.2f} seconds")
            
            return result
            
        except Exception as e:
            print(f"Transcription failed: {e}")
            raise
    
    def format_timestamp(self, seconds: float) -> str:
        """格式化时间戳为SRT格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        milliseconds = int((seconds % 1) * 1000)
        seconds = int(seconds)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    
    def save_srt(self, result: Dict[str, Any], output_path: str):
        """保存SRT字幕文件"""
        srt_content = []

        for i, segment in enumerate(result["segments"], 1):
            start_time = self.format_timestamp(segment["start"])
            end_time = self.format_timestamp(segment["end"])
            text = segment["text"].strip()

            # 如果检测到中文，将繁体转换为简体
            if OPENCC_AVAILABLE and result.get("language") == "zh":
                text = cc.convert(text)

            speaker = segment.get("speaker", "spk0")
            
            # 当启用说话人识别时，始终添加说话人标签（即使识别失败也默认为speaker_1）
            # 转换speaker格式以匹配FunClip：spk0 -> speaker_1, spk1 -> speaker_2 等
            if self.diarize:
                if speaker and speaker.startswith("spk"):
                    try:
                        speaker_num = int(speaker.replace("spk", "")) + 1
                        formatted_text = f"[speaker_{speaker_num}] {text}"
                    except ValueError:
                        formatted_text = f"[speaker_1] {text}"  # 默认为speaker_1
                else:
                    # 如果没有有效的speaker信息，默认使用speaker_1
                    formatted_text = f"[speaker_1] {text}"
            else:
                formatted_text = text
            
            srt_content.append(f"{i}")
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(formatted_text)
            srt_content.append("")  # 空行
        
        srt_path = f"{output_path}.srt"
        try:
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(srt_content))
            print(f"SRT saved: {srt_path}")
        except Exception as e:
            print(f"Failed to save SRT: {e}")
    
    def save_json(self, result: Dict[str, Any], output_path: str):
        """保存JSON结果文件"""
        json_path = f"{output_path}.json"
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"JSON saved: {json_path}")
        except Exception as e:
            print(f"Failed to save JSON: {e}")
    
    def save_txt(self, result: Dict[str, Any], output_path: str):
        """保存纯文本文件"""
        txt_content = []
        
        for segment in result["segments"]:
            txt_content.append(segment["text"].strip())
        
        txt_path = f"{output_path}.txt"
        try:
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(txt_content))
            print(f"✅ 已保存TXT: {txt_path}")
        except Exception as e:
            print(f"❌ 保存TXT失败: {e}")
    
    def save_vtt(self, result: Dict[str, Any], output_path: str):
        """保存VTT字幕文件"""
        vtt_content = ["WEBVTT", ""]
        
        for segment in result["segments"]:
            start_time = self.format_timestamp(segment["start"]).replace(',', '.')
            end_time = self.format_timestamp(segment["end"]).replace(',', '.')
            text = segment["text"].strip()
            
            vtt_content.append(f"{start_time} --> {end_time}")
            vtt_content.append(text)
            vtt_content.append("")
        
        vtt_path = f"{output_path}.vtt"
        try:
            with open(vtt_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(vtt_content))
            print(f"✅ 已保存VTT: {vtt_path}")
        except Exception as e:
            print(f"❌ 保存VTT失败: {e}")
    
    def save_subtitles(self, result: Dict[str, Any], output_path: str, formats: List[str]):
        """保存字幕文件"""
        print(f"Saving subtitles to: {output_path}")
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # 只保存SRT格式
        self.save_srt(result, output_path)

def main():
    parser = argparse.ArgumentParser(description="Faster Whisper字幕生成工具")
    parser.add_argument("input", help="输入音频/视频文件路径")
    parser.add_argument("-o", "--output", help="输出文件路径（不含扩展名）")
    parser.add_argument("-l", "--language", default="auto", choices=list(SUPPORTED_LANGUAGES.keys()),
                      help="语言代码，默认自动检测")
    parser.add_argument("-m", "--model", default="./models/Systran--faster-whisper-medium",
                      help="本地模型路径")
    parser.add_argument("-d", "--device", default="cuda", choices=["cuda", "cpu"],
                      help="计算设备")
    parser.add_argument("--compute-type", default="float16", choices=["float16", "float32", "int8"],
                      help="计算精度")
    parser.add_argument("-f", "--formats", nargs="+", default=["srt", "json"],
                      choices=["srt", "json", "vtt", "txt"],
                      help="输出格式")
    parser.add_argument("-p", "--prompt", default="", help="初始提示词")
    parser.add_argument("--best-of", type=int, default=5, help="最佳候选数")
    parser.add_argument("--temperature", type=float, default=0.0, help="采样温度")
    parser.add_argument("--no-vad", action="store_true", help="禁用VAD过滤")
    parser.add_argument("--vad-threshold", type=float, default=0.5, help="VAD阈值")
    parser.add_argument("--diarize", action="store_true", help="启用说话人识别")
    parser.add_argument("--hf-token", help="Hugging Face token（说话人识别需要）")
    parser.add_argument("--min-speakers", type=int, default=1, help="最少说话人数（默认：1）")
    parser.add_argument("--max-speakers", type=int, default=5, help="最多说话人数（默认：5）")
    
    args = parser.parse_args()
    
    # 检查输入文件
    if not os.path.exists(args.input):
        print(f"❌ 输入文件不存在: {args.input}")
        sys.exit(1)
    
    # 检查文件扩展名
    input_path = Path(args.input)
    if input_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        print(f"❌ 不支持的文件格式: {input_path.suffix}")
        print(f"支持的格式: {', '.join(SUPPORTED_EXTENSIONS)}")
        sys.exit(1)
    
    # 确定输出路径
    if args.output:
        output_path = args.output
    else:
        output_path = str(input_path.with_suffix(""))
    
    # 显示配置信息
    print("Faster Whisper Subtitle Generator")
    print("=" * 50)
    print(f"Input file: {args.input}")
    print(f"Output path: {output_path}")
    print(f"Language: {SUPPORTED_LANGUAGES.get(args.language, args.language)}")
    print(f"Device: {args.device}")
    print(f"Compute type: {args.compute_type}")
    print(f"Output formats: {', '.join(args.formats)}")
    if args.prompt:
        print(f"Prompt: {args.prompt}")
    print("=" * 50)
    
    try:
        # 初始化生成器
        generator = FasterWhisperSubtitleGenerator(
            model_path=args.model,
            device=args.device,
            compute_type=args.compute_type,
            diarize=args.diarize,
            hf_token=args.hf_token
        )
        
        # 设置VAD参数
        vad_parameters = {
            "threshold": args.vad_threshold,
            "min_speech_duration_ms": 250,
            "max_speech_duration_s": 30,
            "min_silence_duration_ms": 100,
            "speech_pad_ms": 400,
        }
        
        # 转录（使用固定的beam_size=5）
        result = generator.transcribe_audio(
            args.input,
            language=args.language,
            initial_prompt=args.prompt,
            beam_size=5,  # 固定值，不再从命令行接受
            best_of=args.best_of,
            temperature=args.temperature,
            vad_filter=not args.no_vad,
            vad_parameters=vad_parameters,
            min_speakers=args.min_speakers,
            max_speakers=args.max_speakers
        )
        
        # 保存结果
        generator.save_subtitles(result, output_path, args.formats)
        
        print(f"\nSubtitle generation completed! Generated {len(result['segments'])} segments")
        
    except KeyboardInterrupt:
        print("\nUser interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\nProcessing failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
