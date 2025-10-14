#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复翻译后的字幕文件时间戳
根据原始字幕的时间戳，修正翻译后字幕的时间戳问题
"""

import sys
import io
import re
from pathlib import Path
from typing import List, Tuple

# 设置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class SubtitleEntry:
    """字幕条目"""
    def __init__(self, index: int, start: str, end: str, text: str):
        self.index = index
        self.start = start
        self.end = end
        self.text = text

    def __str__(self):
        return f"{self.index}\n{self.start} --> {self.end}\n{self.text}\n"


def fix_timestamp_format(timestamp: str) -> str:
    """
    修复LLM导致的时间戳格式错误

    常见错误：将分钟位移到小时位，秒位移到分钟位，毫秒位移到秒位
    例如：00:01:00,979 → 01:00:979 (HH:MM:SSS)

    修复逻辑：
    1. 检测格式错误（秒数>59说明这是毫秒位）
    2. 重构为正确格式：HH:MM:SSS → 00:HH:MM,SSS
    """
    # 标准格式：HH:MM:SS,mmm
    standard_match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})', timestamp)
    if standard_match:
        h, m, s, ms = standard_match.groups()
        # 检查是否在合理范围内
        if int(s) <= 59:
            return timestamp  # 格式正确，无需修复

    # 错误格式1：HH:MM:SSS (秒位其实是毫秒，格式为 HH:MM:mmm)
    wrong_format1 = re.match(r'(\d{2}):(\d{2}):(\d{3})$', timestamp)
    if wrong_format1:
        h, m, ms = wrong_format1.groups()
        # 这种情况下，HH实际是分钟，MM实际是秒，SSS实际是毫秒
        # 修复为：00:HH:MM,SSS
        return f"00:{h}:{m},{ms}"

    # 错误格式2：HH:SSS (只有两段，第二段是三位数)
    wrong_format2 = re.match(r'(\d{2}):(\d{3})$', timestamp)
    if wrong_format2:
        m, combined = wrong_format2.groups()
        # 这种情况：HH:SSS 实际是 MM:Smm 或 MM:SSS
        # 需要进一步解析
        # 假设是 00:MM:SS,mmm 的错误表示
        if len(combined) == 3:
            s = combined[0]
            ms = combined[1:] + "0"  # 补齐到3位
            return f"00:{m}:{s},{ms}0"

    # 如果无法识别，返回原始值
    return timestamp


def parse_srt(content: str, auto_fix: bool = False) -> List[SubtitleEntry]:
    """
    解析SRT文件内容

    Args:
        content: SRT文件内容
        auto_fix: 是否自动修复时间戳格式错误
    """
    entries = []

    # 分割字幕块
    blocks = re.split(r'\n\s*\n', content.strip())

    for block in blocks:
        if not block.strip():
            continue

        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue

        # 解析序号
        try:
            index = int(lines[0].strip())
        except ValueError:
            continue

        # 解析时间戳 - 尝试多种格式
        # 标准格式：HH:MM:SS,mmm --> HH:MM:SS,mmm
        time_match = re.match(r'([\d:,]+)\s*-->\s*([\d:,]+)', lines[1])
        if not time_match:
            continue

        start = time_match.group(1).strip()
        end = time_match.group(2).strip()

        # 如果启用自动修复，修复时间戳格式
        if auto_fix:
            start = fix_timestamp_format(start)
            end = fix_timestamp_format(end)

        # 解析文本（可能有多行）
        text = '\n'.join(lines[2:])

        entries.append(SubtitleEntry(index, start, end, text))

    return entries


def fix_translated_srt(original_path: Path, translated_path: Path, output_path: Path = None):
    """
    修复翻译后的字幕文件

    Args:
        original_path: 原始字幕文件路径
        translated_path: 翻译后字幕文件路径
        output_path: 输出路径（可选，默认覆盖翻译文件）
    """
    if output_path is None:
        output_path = translated_path

    # 读取原始字幕
    with open(original_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
    original_entries = parse_srt(original_content)

    # 读取翻译后字幕（启用自动修复）
    with open(translated_path, 'r', encoding='utf-8') as f:
        translated_content = f.read()
    translated_entries = parse_srt(translated_content, auto_fix=True)

    print(f"原始字幕条目数: {len(original_entries)}")
    print(f"翻译后字幕条目数: {len(translated_entries)}")
    print(f"\n修复逻辑:")
    print(f"  自动检测并修复LLM导致的时间戳格式错误")
    print(f"  (例如: 01:00:979 → 00:01:00,979)")
    print(f"  保留所有翻译后的时间戳，即使看起来不合理")

    # 修复逻辑：
    # 只在 parse_srt 中进行格式自动修复，不替换为原始时间戳
    fixed_entries = []
    auto_fixed_count = 0
    kept_count = 0

    def is_auto_fixed(original_ts: str, fixed_ts: str) -> bool:
        """检查时间戳是否被自动修复过"""
        return original_ts != fixed_ts

    # 重新读取翻译文件来对比是否被修复
    with open(translated_path, 'r', encoding='utf-8') as f:
        original_translated_content = f.read()
    original_translated_entries = parse_srt(original_translated_content, auto_fix=False)

    for i, translated_entry in enumerate(translated_entries):
        # 检查是否被自动修复
        if i < len(original_translated_entries):
            orig_start = original_translated_entries[i].start if i < len(original_translated_entries) else ""
            orig_end = original_translated_entries[i].end if i < len(original_translated_entries) else ""

            was_fixed = (is_auto_fixed(orig_start, translated_entry.start) or
                        is_auto_fixed(orig_end, translated_entry.end))

            if was_fixed:
                auto_fixed_count += 1
            else:
                kept_count += 1

        fixed_entries.append(translated_entry)

    print()
    if kept_count > 0:
        print(f"✓ 时间戳保持原样: {kept_count} 条")
    if auto_fixed_count > 0:
        print(f"✓ 自动修复格式: {auto_fixed_count} 条")

    # 写入修复后的文件
    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in fixed_entries:
            f.write(str(entry))
            f.write('\n')

    print(f"\n✅ 修复完成！")
    print(f"   原始字幕: {original_path}")
    print(f"   翻译字幕: {translated_path}")
    print(f"   输出文件: {output_path}")
    print(f"   修复条目: {len(fixed_entries)} 条")


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("用法: python fix_translated_srt.py <原始字幕.srt> <翻译字幕.srt> [输出文件.srt]")
        print()
        print("示例:")
        print("  python fix_translated_srt.py original.srt translated.srt")
        print("  python fix_translated_srt.py original.srt translated.srt fixed.srt")
        sys.exit(1)

    original_path = Path(sys.argv[1])
    translated_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None

    # 检查文件是否存在
    if not original_path.exists():
        print(f"❌ 错误：原始字幕文件不存在: {original_path}")
        sys.exit(1)

    if not translated_path.exists():
        print(f"❌ 错误：翻译字幕文件不存在: {translated_path}")
        sys.exit(1)

    # 修复字幕
    fix_translated_srt(original_path, translated_path, output_path)


if __name__ == '__main__':
    main()
