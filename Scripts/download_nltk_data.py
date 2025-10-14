#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载 NLTK 所需的数据资源
用于 GPT-SoVITS 的英文文本处理
"""

import nltk
import sys

def download_nltk_data():
    """下载所有必需的 NLTK 数据"""
    print("="*60)
    print("  下载 NLTK 数据资源")
    print("="*60)
    
    # 需要的数据包
    required_data = [
        'averaged_perceptron_tagger_eng',  # 英文词性标注
        'averaged_perceptron_tagger',      # 通用词性标注
        'cmudict',                          # CMU 发音词典（g2p-en 需要）
        'punkt',                            # 分句器
        'punkt_tab',                        # 分句数据
    ]
    
    failed = []
    
    for data_name in required_data:
        try:
            print(f"\n[下载] {data_name}...")
            nltk.download(data_name, quiet=False)
            print(f"[OK] {data_name} 下载完成")
        except Exception as e:
            print(f"[!] {data_name} 下载失败: {e}")
            failed.append(data_name)
    
    print("\n" + "="*60)
    if not failed:
        print("[完成] 所有 NLTK 数据下载完成！")
        print("="*60)
        return 0
    else:
        print(f"[失败] {len(failed)} 个数据包下载失败:")
        for name in failed:
            print(f"  - {name}")
        print("="*60)
        return 1

if __name__ == '__main__':
    try:
        sys.exit(download_nltk_data())
    except KeyboardInterrupt:
        print("\n\n[中断] 用户取消下载")
        sys.exit(1)
    except Exception as e:
        print(f"\n[错误] 下载异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

