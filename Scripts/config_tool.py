#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TransVox 配置管理工具
用于查看、修改和管理用户配置
"""

import sys
import argparse
import json
import logging
from pathlib import Path
from config_manager import ConfigManager

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def cmd_show(args):
    """显示当前配置"""
    config = ConfigManager()
    print("\n=== TransVox 当前配置 ===\n")
    print(json.dumps(config.get_all(), indent=2, ensure_ascii=False))
    print(f"\n配置文件位置: {config.config_path}")


def cmd_get(args):
    """获取指定配置项"""
    config = ConfigManager()
    value = config.get(args.key)
    if value is not None:
        print(f"{args.key} = {json.dumps(value, ensure_ascii=False)}")
    else:
        print(f"配置项不存在: {args.key}")
        return 1


def cmd_set(args):
    """设置配置项"""
    config = ConfigManager()

    # 尝试解析JSON值
    try:
        value = json.loads(args.value)
    except json.JSONDecodeError:
        # 如果不是有效的JSON，当作字符串处理
        value = args.value

    config.set(args.key, value)
    config.save_config()
    print(f"已设置: {args.key} = {json.dumps(value, ensure_ascii=False)}")


def cmd_reset(args):
    """重置配置为默认值"""
    config = ConfigManager()

    if args.confirm:
        config.reset_to_default()
        config.save_config()
        print("配置已重置为默认值")
    else:
        print("请使用 --confirm 参数确认重置操作")
        return 1


def cmd_preset(args):
    """应用预设配置"""
    config = ConfigManager()

    presets = {
        'fast': {
            'translation': {
                'api_type': 'gemini',
                'model': 'gemini-2.0-flash-exp',
            },
            'tts': {
                'engine': 'indextts',
            },
            'advanced': {
                'enable_diarization': False,
                'enable_separation': False,
            }
        },
        'quality': {
            'translation': {
                'api_type': 'gemini',
                'model': 'gemini-2.0-flash-thinking-exp',
            },
            'tts': {
                'engine': 'gptsovits',
            },
            'advanced': {
                'enable_diarization': True,
                'enable_separation': True,
            }
        },
        'chinese': {
            'translation': {
                'source_lang': 'auto',
                'target_lang': 'zh',
            }
        },
        'english': {
            'translation': {
                'source_lang': 'auto',
                'target_lang': 'en',
            }
        }
    }

    if args.name not in presets:
        print(f"错误: 未知的预设名称: {args.name}")
        print(f"可用预设: {', '.join(presets.keys())}")
        return 1

    config.update(presets[args.name])
    config.save_config()
    print(f"已应用预设: {args.name}")
    print("\n更新的配置:")
    print(json.dumps(presets[args.name], indent=2, ensure_ascii=False))


def cmd_path(args):
    """显示配置文件路径"""
    config = ConfigManager()
    print(config.config_path)


def main():
    parser = argparse.ArgumentParser(
        description='TransVox 配置管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查看所有配置
  python config_tool.py show

  # 获取特定配置项
  python config_tool.py get translation.api_type

  # 设置配置项
  python config_tool.py set translation.api_type openai
  python config_tool.py set translation.target_lang zh
  python config_tool.py set tts.engine gptsovits

  # 应用预设配置
  python config_tool.py preset fast       # 快速模式
  python config_tool.py preset quality    # 高质量模式
  python config_tool.py preset chinese    # 翻译为中文
  python config_tool.py preset english    # 翻译为英文

  # 重置为默认配置
  python config_tool.py reset --confirm

  # 查看配置文件位置
  python config_tool.py path
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='命令')

    # show 命令
    parser_show = subparsers.add_parser('show', help='显示所有配置')
    parser_show.set_defaults(func=cmd_show)

    # get 命令
    parser_get = subparsers.add_parser('get', help='获取配置项')
    parser_get.add_argument('key', help='配置键（点号分隔），如: translation.api_type')
    parser_get.set_defaults(func=cmd_get)

    # set 命令
    parser_set = subparsers.add_parser('set', help='设置配置项')
    parser_set.add_argument('key', help='配置键（点号分隔），如: translation.api_type')
    parser_set.add_argument('value', help='配置值')
    parser_set.set_defaults(func=cmd_set)

    # preset 命令
    parser_preset = subparsers.add_parser('preset', help='应用预设配置')
    parser_preset.add_argument('name', choices=['fast', 'quality', 'chinese', 'english'],
                               help='预设名称')
    parser_preset.set_defaults(func=cmd_preset)

    # reset 命令
    parser_reset = subparsers.add_parser('reset', help='重置为默认配置')
    parser_reset.add_argument('--confirm', action='store_true', help='确认重置')
    parser_reset.set_defaults(func=cmd_reset)

    # path 命令
    parser_path = subparsers.add_parser('path', help='显示配置文件路径')
    parser_path.set_defaults(func=cmd_path)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    try:
        return args.func(args) or 0
    except Exception as e:
        logger.error(f"错误: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
