#!/usr/bin/env python3
"""
将whisperx生成的SRT格式转换为项目标准的merged_optimized格式
从: "1  spk0" 格式
到: "[speaker_1]" 格式（在文本行内）
"""

import argparse
import re
from pathlib import Path
import sys

def convert_srt_format(input_path: str, output_path: str):
    """
    转换SRT格式
    
    Args:
        input_path: 输入的whisperx SRT文件路径
        output_path: 输出的merged_optimized格式SRT文件路径
    """
    
    # 读取输入文件
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return False
    
    # 分割为字幕块
    subtitle_blocks = content.strip().split('\n\n')
    converted_blocks = []
    
    for block in subtitle_blocks:
        if not block.strip():
            continue
            
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
            
        # 解析第一行：序号和说话人
        first_line = lines[0].strip()
        
        # 匹配格式: "1  spk0"
        match = re.match(r'^(\d+)\s+(\w+)$', first_line)
        if not match:
            # 如果格式不匹配，保持原样
            converted_blocks.append(block)
            continue
            
        subtitle_id = match.group(1)
        speaker_id = match.group(2)
        
        # 转换说话人标识
        # spk0 -> speaker_1, spk1 -> speaker_2, etc.
        if speaker_id.startswith('spk'):
            try:
                spk_num = int(speaker_id[3:])
                speaker_tag = f"[speaker_{spk_num + 1}]"
            except ValueError:
                speaker_tag = f"[{speaker_id}]"
        elif speaker_id.startswith('SPEAKER_'):
            # 处理pyannote格式: SPEAKER_00 -> speaker_1
            try:
                spk_num = int(speaker_id.split('_')[1])
                speaker_tag = f"[speaker_{spk_num + 1}]"
            except (ValueError, IndexError):
                speaker_tag = f"[{speaker_id.lower()}]"
        else:
            speaker_tag = f"[{speaker_id}]"
        
        # 重新构建字幕块
        new_block = []
        new_block.append(subtitle_id)  # 只有序号，没有说话人
        new_block.append(lines[1])     # 时间戳行
        
        # 文本行：在开头添加说话人标识
        text_lines = lines[2:]
        if text_lines:
            # 将说话人标识添加到第一行文本的开头
            first_text = text_lines[0]
            modified_first_text = f"{speaker_tag} {first_text}"
            
            new_block.append(modified_first_text)
            # 添加其余文本行（如果有）
            new_block.extend(text_lines[1:])
        
        converted_blocks.append('\n'.join(new_block))
    
    # 写入输出文件
    try:
        output_content = '\n\n'.join(converted_blocks) + '\n'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_content)
        print(f"✅ 转换完成: {output_path}")
        return True
    except Exception as e:
        print(f"❌ 写入文件失败: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='将whisperx SRT格式转换为项目标准格式')
    parser.add_argument('input', help='输入的whisperx SRT文件路径')
    parser.add_argument('-o', '--output', help='输出文件路径（可选）')
    parser.add_argument('--suffix', default='_merged_optimized', 
                       help='输出文件后缀（默认: _merged_optimized）')
    
    args = parser.parse_args()
    
    # 检查输入文件
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 输入文件不存在: {args.input}")
        sys.exit(1)
    
    # 确定输出路径
    if args.output:
        output_path = args.output
    else:
        # 自动生成输出路径
        stem = input_path.stem
        # 移除可能的后缀
        if stem.endswith('_with_speakers'):
            stem = stem[:-14]  # 移除 '_with_speakers'
        elif stem.endswith('_faster_whisper'):
            stem = stem[:-15]  # 移除 '_faster_whisper'
        
        output_path = input_path.parent / f"{stem}{args.suffix}.srt"
    
    # 显示转换信息
    print("🔄 SRT格式转换工具")
    print("=" * 50)
    print(f"📁 输入文件: {input_path}")
    print(f"📁 输出文件: {output_path}")
    print(f"🔄 转换格式: whisperx -> merged_optimized")
    print("=" * 50)
    
    # 执行转换
    success = convert_srt_format(str(input_path), str(output_path))
    
    if success:
        print(f"🎉 格式转换成功！")
        print(f"📋 可用于主项目的SRT文件: {output_path}")
    else:
        print("❌ 转换失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
