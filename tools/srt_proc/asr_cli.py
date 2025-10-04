#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASR CLI脚本 - 直接命令行版本，不使用服务
"""

import os
import re
import argparse
import sys
from pathlib import Path
import torch
from funasr import AutoModel


def convert_audio(input_file):
    """转换音频格式为wav"""
    import ffmpeg
    
    output_file = input_file + ".wav"
    try:
        (
            ffmpeg.input(input_file)
            .output(output_file)
            .run(quiet=True, overwrite_output=True)
        )
        return output_file
    except Exception as e:
        print(f"音频转换失败: {e}")
        return input_file


def funasr_to_srt(funasr_result):
    """将FunASR结果转换为SRT格式"""
    if not funasr_result or len(funasr_result) == 0:
        return ""
    
    data = funasr_result[0]
    text = data['text']
    timestamps = data['timestamp']

    # 配置参数
    max_chars_per_line = 20  # 每行字幕的最大字符数

    # 首先按照标点符号分割文本为短句
    sentence_pattern = r'([^，。！？,.!?;；、]+[，。！？,.!?;；、]+)'
    phrases = re.findall(sentence_pattern, text)

    # 如果没有找到短句，就把整个文本作为一个短句
    if not phrases:
        phrases = [text]

    # 确保所有文本都被包含
    remaining_text = text
    for phrase in phrases:
        remaining_text = remaining_text.replace(phrase, '', 1)
    if remaining_text.strip():
        phrases.append(remaining_text.strip())

    # 计算每个短句对应的时间戳
    phrase_timestamps = []
    total_chars = len(text)

    char_index = 0
    for phrase in phrases:
        if not phrase.strip():
            continue

        phrase_len = len(phrase)
        # 计算短句在整个文本中的比例
        start_ratio = char_index / total_chars if total_chars > 0 else 0
        end_ratio = (char_index + phrase_len) / total_chars if total_chars > 0 else 1

        start_idx = min(int(start_ratio * len(timestamps)), len(timestamps) - 1)
        end_idx = min(int(end_ratio * len(timestamps)), len(timestamps) - 1)

        if start_idx == end_idx:
            if end_idx < len(timestamps) - 1:
                end_idx += 1

        start_time = timestamps[start_idx][0] if start_idx < len(timestamps) else 0
        end_time = timestamps[end_idx][1] if end_idx < len(timestamps) else start_time + 1000

        phrase_timestamps.append((phrase, start_time, end_time))
        char_index += phrase_len

    # 合并短句为合适长度的字幕段落，只考虑字数限制
    text_segments = []
    current_text = ""
    current_start = None
    current_end = None

    for phrase, start, end in phrase_timestamps:
        # 如果当前段落为空，直接添加
        if not current_text:
            current_text = phrase
            current_start = start
            current_end = end
            continue

        # 检查添加当前短句后是否会超出字数限制
        combined_text = current_text + phrase

        if len(combined_text) > max_chars_per_line:
            # 如果会超出限制，保存当前段落并开始新段落
            text_segments.append((current_text, current_start, current_end))
            current_text = phrase
            current_start = start
            current_end = end
        else:
            # 否则合并短句
            current_text = combined_text
            current_end = end

    # 添加最后一个段落
    if current_text:
        text_segments.append((current_text, current_start, current_end))

    # 生成SRT格式，去除每段末尾的标点符号
    srt_content = ""
    for i, (text, start, end) in enumerate(text_segments, 1):
        # 去除段落末尾的标点符号
        cleaned_text = re.sub(r'[，。！？,.!?;；、]+$', '', text)

        srt_content += f"{i}\n"
        srt_content += f"{format_timestamp(start)} --> {format_timestamp(end)}\n"
        srt_content += f"{cleaned_text.strip()}\n\n"

    return srt_content


def format_timestamp(milliseconds):
    """将毫秒转换为SRT格式的时间戳"""
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def transcribe_audio_cli(input_audio_path: str, output_srt_path: str = None) -> str:
    """
    CLI方式进行语音转写
    
    Args:
        input_audio_path: 输入音频文件路径
        output_srt_path: 输出SRT文件路径，如果为None则自动生成
    
    Returns:
        SRT文件路径
    """
    print(f"开始语音转写: {input_audio_path}")
    
    # 检查输入文件是否存在
    if not os.path.exists(input_audio_path):
        raise FileNotFoundError(f"音频文件不存在: {input_audio_path}")
    
    # 确定输出文件路径
    if output_srt_path is None:
        input_path = Path(input_audio_path)
        output_srt_path = input_path.parent / f"{input_path.stem}.srt"
    
    # 初始化设备
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"使用设备: {device}")
    
    try:
        # 初始化模型
        print("正在加载ASR模型...")
        model = AutoModel(
            model="paraformer-zh",
            vad_model="fsmn-vad",
            vad_kwargs={"max_single_segment_time": 60000},
            punc_model="ct-punc",
            device=device,
            # spk_model="cam++",
        )
        print("模型加载完成")
        
        # 检查音频格式，如果需要则转换
        input_file = input_audio_path
        ext_name = os.path.splitext(input_audio_path)[1].strip('.').lower()
        
        if ext_name not in ['wav', 'mp3']:
            print(f"音频格式不支持({ext_name})，尝试转换为wav...")
            input_file = convert_audio(input_audio_path)
        
        # 进行语音识别
        print("开始语音识别...")
        result = model.generate(
            input=input_file,
            batch_size_s=300,
            batch_size_threshold_s=60,
            # hotword='魔搭'
        )
        
        if not result or len(result) == 0:
            raise Exception("语音识别失败，未返回任何结果")
        
        print("语音识别完成，正在生成SRT字幕...")
        
        # 转换为SRT格式
        srt_content = funasr_to_srt(result)
        
        if not srt_content.strip():
            raise Exception("SRT转换失败，生成的字幕为空")
        
        # 保存SRT文件
        with open(output_srt_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        print(f"字幕文件已保存: {output_srt_path}")
        
        # 清理临时文件
        if input_file != input_audio_path and os.path.exists(input_file):
            os.remove(input_file)
            print("临时音频文件已清理")
        
        return str(output_srt_path)
        
    except Exception as e:
        print(f"语音转写失败: {e}")
        # 清理临时文件
        if 'input_file' in locals() and input_file != input_audio_path and os.path.exists(input_file):
            os.remove(input_file)
        raise


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="语音转写CLI工具")
    parser.add_argument("input_audio", help="输入音频文件路径")
    parser.add_argument("-o", "--output", help="输出SRT文件路径（可选，默认与输入文件同目录同名）")
    
    args = parser.parse_args()
    
    try:
        srt_path = transcribe_audio_cli(args.input_audio, args.output)
        print(f"\n[成功] 语音转写成功！")
        print(f"SRT文件: {srt_path}")
        
        # 显示部分字幕内容
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            preview_lines = lines[:min(10, len(lines))]
            print(f"\n字幕预览:")
            print('\n'.join(preview_lines))
            if len(lines) > 10:
                print("...")
        
    except Exception as e:
        print(f"\n[失败] 语音转写失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
