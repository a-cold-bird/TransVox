#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤4: 字幕翻译（整文件翻译模式）
使用 Gemini 或 OpenAI API 翻译字幕

环境变量配置:
- TRANSLATION_API_TYPE (默认: gemini) - API类型，支持 gemini 或 openai
- TRANSLATION_MODEL (默认: gemini-2.5-flash) - 使用的模型

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
from typing import List, Optional
import srt

# 添加项目根目录到路径以导入config_manager
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from config_manager import get_config_manager
    CONFIG_MANAGER_AVAILABLE = True
except ImportError:
    CONFIG_MANAGER_AVAILABLE = False

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


def test_gemini_api(api_key: str, proxy_url: str, model: str = 'gemini-2.5-flash') -> bool:
    """测试Gemini API是否可用"""
    try:
        # 支持自定义版本路径，不再自动拼接
        base = proxy_url.rstrip('/')
        # 如果用户已经提供了完整路径，直接使用；否则按原逻辑拼接
        if 'generateContent' in base or ':generateContent' in base:
            url = base
        else:
            url = f"{base}/models/{model}:generateContent"

        headers = {
            'x-goog-api-key': api_key,
            'Content-Type': 'application/json'
        }

        payload = {
            "contents": [{"parts": [{"text": "Hello"}]}],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 10
            }
        }

        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"[API测试] Gemini API不可用: {e}")
        return False


def test_openai_api(api_key: str, base_url: str, model: str = 'gpt-4') -> bool:
    """测试OpenAI API是否可用"""
    try:
        # 支持自定义版本路径，不再自动拼接
        base = base_url.rstrip('/')
        # 如果用户已经提供了完整路径，直接使用；否则按原逻辑拼接
        if 'chat/completions' in base:
            url = base
        else:
            url = f"{base}/chat/completions"

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        data = {
            "model": model,
            "messages": [{"role": "user", "content": "Hello"}],
            "temperature": 0.3,
            "max_tokens": 10
        }

        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"[API测试] OpenAI API不可用: {e}")
        return False


def translate_srt_whole_file(subtitles: List[srt.Subtitle], target_lang: str, max_retries: int = 5,
                            api_type: Optional[str] = None, model: Optional[str] = None,
                            context_prompt: Optional[str] = None) -> List[srt.Subtitle]:
    """
    整文件翻译：一次性提交完整 SRT 到 API

    Args:
        subtitles: 原始字幕列表
        target_lang: 目标语言
        max_retries: 最大重试次数
        api_type: API类型（可选，优先级：参数 > 配置文件 > 环境变量）
        model: 模型名称（可选，优先级：参数 > 配置文件 > 环境变量）
        context_prompt: 用户提供的上下文信息（语言、内容、专有名词等）

    Returns:
        翻译后的字幕列表
    """
    # 优先级：参数 > 配置文件 > 环境变量
    if api_type is None:
        if CONFIG_MANAGER_AVAILABLE:
            config = get_config_manager()
            api_type = config.get('translation.api_type', 'gemini')
        else:
            api_type = os.getenv('TRANSLATION_API_TYPE', 'gemini')

    api_type = api_type.lower()

    if api_type == 'openai':
        return _translate_with_openai(subtitles, target_lang, max_retries, model, context_prompt)
    else:
        return _translate_with_gemini(subtitles, target_lang, max_retries, model, context_prompt)


def _translate_with_gemini(subtitles: List[srt.Subtitle], target_lang: str, max_retries: int = 5,
                          model: Optional[str] = None, context_prompt: Optional[str] = None) -> List[srt.Subtitle]:
    """使用 Gemini API 翻译"""
    # 优先级：配置文件 > 环境变量
    if CONFIG_MANAGER_AVAILABLE:
        config = get_config_manager()
        api_key = config.get('api.gemini_api_key', '') or os.getenv('GEMINI_API_KEY', '')
        proxy_url = config.get('api.gemini_base_url', '') or os.getenv('GEMINI_PROXY_URL', '')
    else:
        api_key = os.getenv('GEMINI_API_KEY', '')
        proxy_url = os.getenv('GEMINI_PROXY_URL', '')

    # 优先级：参数 > 配置文件 > 环境变量
    if model is None:
        if CONFIG_MANAGER_AVAILABLE:
            config = get_config_manager()
            model = config.get('translation.model', 'gemini-2.5-flash')
        else:
            model = os.getenv('TRANSLATION_MODEL', 'gemini-2.5-flash')

    if not api_key or not proxy_url:
        logger.error("[配置] GEMINI_API_KEY 或 GEMINI_PROXY_URL 未设置")
        return subtitles

    # 测试API可用性
    logger.info("[API测试] 检查Gemini API可用性...")
    if not test_gemini_api(api_key, proxy_url, model):
        logger.error(f"[API测试] Gemini API不可用，跳过翻译")
        return subtitles
    logger.info("[API测试] Gemini API可用")
    
    # 构建完整 SRT 文本
    original_srt_text = srt.compose(subtitles)
    
    # 语言名称映射
    lang_names = {'zh': '中文', 'en': '英文', 'ja': '日文', 'ko': '韩文'}
    target_lang_name = lang_names.get(target_lang, target_lang)

    # 构建上下文部分
    context_section = ""
    if context_prompt and context_prompt.strip():
        context_section = f"""

背景信息：
{context_prompt.strip()}

请在翻译时参考以上背景信息，特别注意其中提到的专有名词、人名、术语等，确保翻译的准确性和一致性。
"""

    prompt = f"""任务：将以下 SRT 字幕翻译为{target_lang_name}。{context_section}

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
- 时间戳必须合法且连续（合并字幕时，使用第一条的开始时间和最后一条的结束时间）
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
    
    # 构建端点 - 支持自定义版本路径
    base = proxy_url.rstrip('/')
    # 如果用户已经提供了完整路径，直接使用；否则按原逻辑拼接
    if 'generateContent' in base or ':generateContent' in base:
        url = base
    else:
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
    logger.error(f"[翻译失败] {max_retries} 次重试后仍然失败，将使用原字幕")
    return subtitles


def _translate_with_openai(subtitles: List[srt.Subtitle], target_lang: str, max_retries: int = 5,
                          model: Optional[str] = None, context_prompt: Optional[str] = None) -> List[srt.Subtitle]:
    """使用 OpenAI API 翻译"""
    # 优先级：配置文件 > 环境变量
    if CONFIG_MANAGER_AVAILABLE:
        config = get_config_manager()
        api_key = config.get('api.openai_api_key', '') or os.getenv('OPENAI_API_KEY', '')
        base_url = config.get('api.openai_base_url', '') or os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    else:
        api_key = os.getenv('OPENAI_API_KEY', '')
        base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')

    # 优先级：参数 > 配置文件 > 环境变量
    if model is None:
        if CONFIG_MANAGER_AVAILABLE:
            config = get_config_manager()
            model = config.get('translation.model', 'gpt-4')
        else:
            model = os.getenv('TRANSLATION_MODEL', 'gpt-4')

    if not api_key:
        logger.error("[配置] OPENAI_API_KEY 未设置")
        return subtitles

    # 测试API可用性
    logger.info("[API测试] 检查OpenAI API可用性...")
    if not test_openai_api(api_key, base_url, model):
        logger.error(f"[API测试] OpenAI API不可用，跳过翻译")
        return subtitles
    logger.info("[API测试] OpenAI API可用")
    
    original_srt_text = srt.compose(subtitles)

    lang_names = {'zh': '中文', 'en': '英文', 'ja': '日文', 'ko': '韩文'}
    target_lang_name = lang_names.get(target_lang, target_lang)

    # 构建上下文部分
    context_section = ""
    if context_prompt and context_prompt.strip():
        context_section = f"""

背景信息：
{context_prompt.strip()}

请在翻译时参考以上背景信息，特别注意其中提到的专有名词、人名、术语等，确保翻译的准确性和一致性。
"""

    prompt = f"""请将以下 SRT 字幕翻译为{target_lang_name}。{context_section}

要求：
1. 仅翻译台词内容，保持索引与时间戳不变
2. 保留 [SPEAKER_N] 标签，只翻译文本
3. 翻译准确自然
4. 只输出 SRT 格式文本，不要代码围栏

{original_srt_text}
"""
    
    # 支持自定义版本路径 - 支持自定义版本路径
    base = base_url.rstrip('/')
    # 如果用户已经提供了完整路径，直接使用；否则按原逻辑拼接
    if 'chat/completions' in base:
        url = base
    else:
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
    
    logger.error(f"[翻译失败] {max_retries} 次重试后仍然失败，将使用原字幕")
    return subtitles


def translate_srt(srt_path: str, target_lang: str, output_path: str = None, max_retries: int = 5,
                 api_type: Optional[str] = None, model: Optional[str] = None,
                 context_prompt: Optional[str] = None) -> str:
    """
    翻译 SRT 字幕文件（整文件模式）

    Args:
        srt_path: 输入SRT文件路径
        target_lang: 目标语言
        output_path: 输出SRT文件路径
        max_retries: 最大重试次数
        api_type: API类型（可选）
        model: 翻译模型（可选）
        context_prompt: 用户提供的上下文信息（语言、内容、专有名词等）

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
        translated_subs = translate_srt_whole_file(subtitles, target_lang, max_retries, api_type, model, context_prompt)

        # 检查翻译是否成功
        if translated_subs == subtitles:
            logger.error("[翻译失败] 翻译未成功，所有重试均失败")
            raise RuntimeError(
                "字幕翻译失败：API调用失败或返回结果无效。"
                "请检查API配置（API Key、Base URL）和网络连接。"
            )
        else:
            logger.info(f"[翻译结果] 翻译成功 (原 {len(subtitles)} 条 → 译 {len(translated_subs)} 条)")
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
    parser.add_argument("--api_type", choices=['gemini', 'openai'], help="翻译API类型（可选，优先级高于配置文件）")
    parser.add_argument("--model", help="翻译模型名称（可选，优先级高于配置文件）")
    parser.add_argument("--context", help="翻译上下文信息（语言、内容、专有名词等，可选）")
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
            args.max_retries,
            args.api_type,
            args.model,
            args.context
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
