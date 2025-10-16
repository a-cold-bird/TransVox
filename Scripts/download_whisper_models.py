#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Whisper 模型下载脚本
用于预先下载 faster-whisper 模型到本地，避免运行时下载
"""

import os
import sys
import argparse
from pathlib import Path
from faster_whisper import WhisperModel
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 可用的模型列表
AVAILABLE_MODELS = {
    'tiny': 'Systran/faster-whisper-tiny',
    'tiny.en': 'Systran/faster-whisper-tiny.en',
    'base': 'Systran/faster-whisper-base',
    'base.en': 'Systran/faster-whisper-base.en',
    'small': 'Systran/faster-whisper-small',
    'small.en': 'Systran/faster-whisper-small.en',
    'medium': 'Systran/faster-whisper-medium',
    'medium.en': 'Systran/faster-whisper-medium.en',
    'large-v1': 'Systran/faster-whisper-large-v1',
    'large-v2': 'Systran/faster-whisper-large-v2',
    'large-v3': 'Systran/faster-whisper-large-v3',
}

# 模型大小信息（近似）
MODEL_SIZES = {
    'tiny': '~75 MB',
    'tiny.en': '~75 MB',
    'base': '~142 MB',
    'base.en': '~142 MB',
    'small': '~466 MB',
    'small.en': '~466 MB',
    'medium': '~1.5 GB',
    'medium.en': '~1.5 GB',
    'large-v1': '~2.9 GB',
    'large-v2': '~2.9 GB',
    'large-v3': '~2.9 GB',
}


def download_model(model_name: str, device: str = "cpu", compute_type: str = "int8",
                   cache_dir: str = None) -> bool:
    """
    下载指定的 Whisper 模型

    Args:
        model_name: 模型名称（如 'base', 'large-v3'）
        device: 设备类型（'cpu' 或 'cuda'）
        compute_type: 计算类型（'int8', 'float16', 'float32'）
        cache_dir: 缓存目录（可选）

    Returns:
        bool: 下载是否成功
    """
    if model_name not in AVAILABLE_MODELS:
        logger.error(f"❌ 不支持的模型: {model_name}")
        logger.info(f"可用模型: {', '.join(AVAILABLE_MODELS.keys())}")
        return False

    repo_id = AVAILABLE_MODELS[model_name]
    logger.info(f"📥 开始下载模型: {model_name}")
    logger.info(f"   HuggingFace Repo: {repo_id}")
    logger.info(f"   预计大小: {MODEL_SIZES.get(model_name, '未知')}")
    logger.info(f"   设备: {device}")
    logger.info(f"   计算类型: {compute_type}")

    if cache_dir:
        logger.info(f"   缓存目录: {cache_dir}")

    try:
        # 下载并初始化模型（这会触发模型下载）
        logger.info("⏳ 正在下载模型文件...")

        kwargs = {
            'device': device,
            'compute_type': compute_type,
        }

        if cache_dir:
            kwargs['download_root'] = cache_dir

        model = WhisperModel(repo_id, **kwargs)

        logger.info(f"✅ 模型下载成功: {model_name}")

        # 显示模型信息
        logger.info(f"   模型已缓存，后续使用将直接从本地加载")

        return True

    except Exception as e:
        logger.error(f"❌ 模型下载失败: {e}")
        return False


def list_models():
    """列出所有可用的模型"""
    print("\n可用的 Whisper 模型:")
    print("=" * 70)
    print(f"{'模型名称':<15} {'大小':<15} {'HuggingFace Repo'}")
    print("-" * 70)
    for name, repo in AVAILABLE_MODELS.items():
        size = MODEL_SIZES.get(name, '未知')
        print(f"{name:<15} {size:<15} {repo}")
    print("=" * 70)
    print("\n推荐:")
    print("  - 快速测试: tiny, base")
    print("  - 平衡性能: small, medium")
    print("  - 最佳质量: large-v3 (推荐)")
    print("  - 仅英语: 选择 .en 后缀的模型")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Whisper 模型下载工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 下载 base 模型（CPU，推荐用于快速测试）
  python download_whisper_models.py base

  # 下载 large-v3 模型（GPU，推荐用于生产环境）
  python download_whisper_models.py large-v3 --device cuda --compute-type float16

  # 下载多个模型
  python download_whisper_models.py base small large-v3

  # 列出所有可用模型
  python download_whisper_models.py --list
        """
    )

    parser.add_argument(
        'models',
        nargs='*',
        help='要下载的模型名称（可以指定多个）'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='列出所有可用的模型'
    )

    parser.add_argument(
        '--device',
        choices=['cpu', 'cuda'],
        default='cpu',
        help='设备类型（默认: cpu）'
    )

    parser.add_argument(
        '--compute-type',
        choices=['int8', 'float16', 'float32'],
        default='int8',
        help='计算类型（默认: int8，适合 CPU）'
    )

    parser.add_argument(
        '--cache-dir',
        type=str,
        help='模型缓存目录（可选）'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='下载所有模型（不推荐，总大小约 10+ GB）'
    )

    args = parser.parse_args()

    # 列出模型
    if args.list:
        list_models()
        return

    # 确定要下载的模型
    models_to_download = []

    if args.all:
        models_to_download = list(AVAILABLE_MODELS.keys())
        logger.warning("⚠️  将下载所有模型，总大小约 10+ GB")
        response = input("确认继续？(yes/no): ")
        if response.lower() not in ['yes', 'y']:
            logger.info("已取消")
            return
    elif args.models:
        models_to_download = args.models
    else:
        logger.error("❌ 请指定要下载的模型或使用 --list 查看可用模型")
        parser.print_help()
        return

    # 检查 CUDA 可用性
    import torch
    if args.device == 'cuda':
        if not torch.cuda.is_available():
            logger.warning("⚠️  CUDA 不可用，将使用 CPU 模式")
            args.device = 'cpu'
            args.compute_type = 'int8'
        else:
            logger.info(f"✅ CUDA 可用: {torch.cuda.get_device_name(0)}")

    # 下载模型
    success_count = 0
    failed_models = []

    for model_name in models_to_download:
        print(f"\n{'='*70}")
        success = download_model(
            model_name,
            device=args.device,
            compute_type=args.compute_type,
            cache_dir=args.cache_dir
        )

        if success:
            success_count += 1
        else:
            failed_models.append(model_name)

    # 总结
    print(f"\n{'='*70}")
    print(f"下载完成: {success_count}/{len(models_to_download)} 成功")

    if failed_models:
        print(f"失败的模型: {', '.join(failed_models)}")

    print("=" * 70)


if __name__ == "__main__":
    main()
