#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清空输出目录脚本

默认清空项目根目录下的 output/，也可通过 --path 指定其他目录。
安全策略：
- 仅允许删除位于当前项目内的目录；
- 若目录不存在则直接结束；
- 删除后自动重建同名空目录（便于后续流程）。
"""

import os
import sys
import argparse
import shutil
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='清空输出目录')
    parser.add_argument('--path', default='output', help='要清空的目录（默认: output）')
    args = parser.parse_args()

    target = Path(args.path).resolve()
    project_root = Path(__file__).resolve().parent

    # 安全：仅允许删除项目内目录
    try:
        target.relative_to(project_root)
    except ValueError:
        logger.error(f"拒绝操作：{target} 不在当前项目内")
        sys.exit(1)

    if not target.exists():
        logger.info(f"目录不存在，无需清理: {target}")
        return

    if not target.is_dir():
        logger.error(f"目标不是目录: {target}")
        sys.exit(1)

    logger.info(f"开始清理目录: {target}")
    shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    logger.info(f"已清理并重建目录: {target}")


if __name__ == '__main__':
    main()



