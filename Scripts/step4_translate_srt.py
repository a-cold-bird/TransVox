#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤4: 字幕翻译（整文件翻译模式）
使用 Gemini 或 OpenAI API 翻译字幕

环境变量配置:
- TRANSLATION_API_TYPE (默认: gemini) - API类型，支持 gemini 或 openai  
- TRANSLATION_MODEL (默认: gemini-2.5-pro) - 使用的模型

Gemini配置:
- GEMINI_API_KEY
- GEMINI_PROXY_URL

OpenAI配置:
- OPENAI_API_KEY  
- OPENAI_BASE_URL (默认: https://api.openai.com/v1)
"""

import os
import sys
import argparse
import requests
import logging
import time
from pathlib import Path
from typing import List
import srt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _load_dotenv_into_environ():
    try:
        root = Path(__file__).resolve().parent.parent
        dotenv_path = root / '.env'
        if dotenv_path.exists():
            with open(dotenv_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        k, v = line.split('=', 1)
                        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            logger.info(f"已从 .env 加载环境变量: {dotenv_path}")
    except Exception as e:
        logger.warning(f"加载 .env 失败: {e}")

_load_dotenv_into_environ()


def translate_srt_whole_file(subtitles: List[srt.Subtitle], target_lang: str, max_retries: int = 5) -> List[srt.Subtitle]:
    """
    整文件翻译：一次性提交完整 SRT 到 API
    
    Args:
        subtitles: 原始字幕列表
        target_lang: 目标语言
        max_retries: 最大重试次数
    
    Returns:
        翻译后的字幕列表
    """
    api_type = os.getenv('TRANSLATION_API_TYPE', 'gemini').lower()
    
    if api_type == 'openai':
        return _translate_with_openai(subtitles, target_lang, max_retries)
    else:
        return _translate_with_gemini(subtitles, target_lang, max_retries)


def _translate_with_gemini(subtitles: List[srt.Subtitle], target_lang: str, max_retries: int = 5) -> List[srt.Subtitle]:
    """使用 Gemini API 翻译"""
    api_key = os.getenv('GEMINI_API_KEY')
    proxy_url = os.getenv('GEMINI_PROXY_URL')
    model = os.getenv('TRANSLATION_MODEL', 'gemini-2.5-pro')
    
    if not api_key or not proxy_url:
        logger.error("GEMINI_API_KEY 或 GEMINI_PROXY_URL 未设置")
        return subtitles
    
    # 构建完整 SRT 文本
    original_srt_text = srt.compose(subtitles)
    
    # 语言名称映射
    lang_names = {'zh': '中文', 'en': '英文', 'ja': '日文', 'ko': '韩文'}
    target_lang_name = lang_names.get(target_lang, target_lang)
    
    prompt = f"""任务：将以下 SRT 字幕翻译为{target_lang_name}。

处理要求：
1. 合并语义不完整的连续字幕，确保每条语义完整
2. 每条字幕不超过 100 个字符
3. 翻译内容长度在发音上需要尽可能的与源语言符合，因为不同语言发音时间不同，以保证与原视频的时间戳相匹配
4. 翻译自然流畅，符合{target_lang_name}表达习惯

格式要求：
- 保留 [SPEAKER_1]、[speaker_2] 等说话人标签
- 删除错误字符、emoji、特殊符号
- 索引编号连续（1, 2, 3...）
- 时间戳格式：HH:MM:SS,mmm --> HH:MM:SS,mmm
- 时间戳必须合法且连续（合并字幕时，使用第一条的开始时间和最后一条的结束时间）

输出要求：
- 只输出纯 SRT 文本内容
- 不要任何解释
- 不要 Markdown 代码围栏
- 不要语言标签

--- 原始 SRT 开始 ---
{original_srt_text}
--- 原始 SRT 结束 ---
"""
    
    # 构建端点
    base = proxy_url[:-1] if proxy_url.endswith('/') else proxy_url
    url = f"{base}/models/{model}:generateContent"
    
    headers = {
        'x-goog-api-key': api_key,
        'Content-Type': 'application/json'
    }
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 8192
        }
    }
    
    # 重试机制
    for attempt in range(max_retries):
        try:
            logger.info(f"[Gemini] 翻译中... (尝试 {attempt + 1}/{max_retries})")
            
            response = requests.post(url, headers=headers, json=payload, timeout=180)
            
            response.raise_for_status()
            
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                parts = candidate.get('content', {}).get('parts', [])
                if parts and isinstance(parts[0], dict) and 'text' in parts[0]:
                    translated_text = parts[0]['text'].strip()
                    
                    # 清理可能的 Markdown 围栏
                    cleaned = translated_text
                    if cleaned.startswith('```'):
                        parts_list = cleaned.split('```')
                        if len(parts_list) >= 3:
                            cleaned = parts_list[1]
                            if '\n' in cleaned:
                                first, rest = cleaned.split('\n', 1)
                                if first.strip().lower() in ('srt', 'text', 'subtitle'):
                                    cleaned = rest
                    
                    # 解析翻译后的 SRT
                    try:
                        translated_subs = list(srt.parse(cleaned))
                        if translated_subs:
                            logger.info(f"[OK] 翻译成功（原 {len(subtitles)} 条 → 译 {len(translated_subs)} 条）")
                            return translated_subs
                        else:
                            logger.warning("[!] 翻译结果为空")
                    except Exception as e:
                        logger.warning(f"[!] SRT 解析失败: {e}")
            
            # 响应无效，等待后重试
            if attempt < max_retries - 1:
                logger.warning(f"[!] 翻译结果无效，等待后重试...")
                time.sleep(2 ** attempt)
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"[!] 请求失败（尝试 {attempt + 1}/{max_retries}）: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
        except Exception as e:
            logger.warning(f"[!] 翻译异常（尝试 {attempt + 1}/{max_retries}）: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    
    # 所有重试失败
    logger.error(f"[X] 翻译失败（{max_retries} 次重试后），返回原字幕")
    return subtitles


def _translate_with_openai(subtitles: List[srt.Subtitle], target_lang: str, max_retries: int = 5) -> List[srt.Subtitle]:
    """使用 OpenAI API 翻译"""
    api_key = os.getenv('OPENAI_API_KEY')
    base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    model = os.getenv('TRANSLATION_MODEL', 'gpt-4')
    
    if not api_key:
        logger.error("OPENAI_API_KEY 未设置")
        return subtitles
    
    original_srt_text = srt.compose(subtitles)
    
    lang_names = {'zh': '中文', 'en': '英文', 'ja': '日文', 'ko': '韩文'}
    target_lang_name = lang_names.get(target_lang, target_lang)
    
    prompt = f"""请将以下 SRT 字幕翻译为{target_lang_name}。

要求：
1. 仅翻译台词内容，保持索引与时间戳不变
2. 保留 [SPEAKER_N] 标签，只翻译文本
3. 翻译准确自然
4. 只输出 SRT 格式文本，不要代码围栏

{original_srt_text}
"""
    
    base = base_url[:-1] if base_url.endswith('/') else base_url
    url = f"{base}/chat/completions"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 8192
    }
    
    for attempt in range(max_retries):
        try:
            logger.info(f"[OpenAI] 翻译中... (尝试 {attempt + 1}/{max_retries})")
            response = requests.post(url, headers=headers, json=data, timeout=180)
            response.raise_for_status()
            
            result = response.json()
            if 'choices' in result and result['choices']:
                translated_text = result['choices'][0]['message']['content'].strip()
                
                # 清理 Markdown
                cleaned = translated_text
                if cleaned.startswith('```'):
                    parts_list = cleaned.split('```')
                    if len(parts_list) >= 3:
                        cleaned = parts_list[1].split('\n', 1)[1] if '\n' in parts_list[1] else parts_list[1]
                
                translated_subs = list(srt.parse(cleaned))
                if len(translated_subs) == len(subtitles):
                    logger.info(f"[OK] 翻译成功（{len(translated_subs)} 条字幕）")
                    return translated_subs
            
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                
        except Exception as e:
            logger.warning(f"[!] 翻译失败（尝试 {attempt + 1}/{max_retries}）: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    
    logger.error(f"[X] 翻译失败，返回原字幕")
    return subtitles


def translate_srt(srt_path: str, target_lang: str, output_path: str = None, max_retries: int = 5) -> str:
    """
    翻译 SRT 字幕文件（整文件模式）
    
    Args:
        srt_path: 输入SRT文件路径
        target_lang: 目标语言
        output_path: 输出SRT文件路径
        max_retries: 最大重试次数
    
    Returns:
        翻译后的SRT文件路径
    """
    srt_path = Path(srt_path)
    
    if not srt_path.exists():
        raise FileNotFoundError(f"SRT文件不存在: {srt_path}")
    
    # 设置输出路径
    if output_path is None:
        output_path = srt_path.parent / f"{srt_path.stem}.translated.srt"
    else:
        output_path = Path(output_path)
    
    logger.info(f"翻译字幕: {srt_path}")
    logger.info(f"目标语言: {target_lang}")
    logger.info(f"输出文件: {output_path}")
    
    try:
        # 读取原始SRT
        with open(srt_path, 'r', encoding='utf-8') as f:
            srt_content = f.read().lstrip('\ufeff')  # 去除 BOM
        
        subtitles = list(srt.parse(srt_content))
        logger.info(f"解析到 {len(subtitles)} 条字幕")
        
        # 整文件翻译
        logger.info("[模式] 整文件翻译")
        translated_subs = translate_srt_whole_file(subtitles, target_lang, max_retries)
        
        # 保存翻译结果
        translated_content = srt.compose(translated_subs)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_content)
        
        logger.info("[完成] 字幕翻译完成!")
        return str(output_path)
        
    except Exception as e:
        logger.error(f"[X] 字幕翻译失败: {e}")
        import traceback
        traceback.print_exc()
        raise


def main():
    parser = argparse.ArgumentParser(description="字幕翻译工具（整文件模式）")
    parser.add_argument("input_srt", help="输入SRT文件路径")
    parser.add_argument("--target_lang", default="en", help="目标翻译语言 (默认: en)")
    parser.add_argument("-o", "--output", help="输出SRT文件路径（可选）")
    parser.add_argument("--max-retries", type=int, default=5, help="最大重试次数（默认: 5）")
    parser.add_argument("--whole_file", action="store_true", help="整文件翻译模式（默认启用，保留此参数以兼容旧脚本）")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细日志")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        start_time = time.time()
        
        translated_srt_path = translate_srt(
            args.input_srt,
            args.target_lang,
            args.output,
            args.max_retries
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"\n[完成] 字幕翻译成功!")
        print(f"[输出] {translated_srt_path}")
        print(f"[耗时] {elapsed_time:.1f} 秒")
        
        # 显示文件大小
        size_kb = Path(translated_srt_path).stat().st_size / 1024
        print(f"[大小] {size_kb:.1f} KB")
        
        # 预览
        with open(translated_srt_path, 'r', encoding='utf-8') as f:
            lines = f.read().split('\n')
            preview = '\n'.join(lines[:min(20, len(lines))])
            print(f"\n[预览] 翻译结果:")
            print(preview)
            if len(lines) > 20:
                print("...")
        
        return 0
        
    except Exception as e:
        logger.error(f"[X] 处理失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
