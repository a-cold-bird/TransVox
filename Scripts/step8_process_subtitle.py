#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤8: 处理字幕文件（智能分行、创建双语字幕）
为嵌入视频准备优化后的字幕
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _load_dotenv_into_environ():
    """加载环境变量"""
    try:
        root = Path(__file__).resolve().parent
        dotenv_path = (root / '.env') if (root / '.env').exists() else (root.parent / '.env')
        if dotenv_path.exists():
            with open(dotenv_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        k, v = line.split('=', 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        os.environ.setdefault(k, v)
            logger.info(f"已从 .env 加载环境变量: {dotenv_path}")
    except Exception as e:
        logger.warning(f"加载 .env 失败: {e}")

_load_dotenv_into_environ()


class SubtitleProcessor:
    """字幕处理器"""
    
    def _call_openai_api(self, prompt: str, max_tokens: int = 256, max_retries: int = 5) -> str:
        """调用 OpenAI API"""
        import requests
        import time
        
        api_key = os.getenv('OPENAI_API_KEY')
        base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        model = os.getenv('OPENAI_MODEL', 'gpt-4')
        
        if not api_key:
            raise RuntimeError('OPENAI_API_KEY 未设置')
        
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
            "max_tokens": max_tokens
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=data, timeout=15)
                response.raise_for_status()
                
                result = response.json()
                if 'choices' in result and result['choices']:
                    return result['choices'][0]['message']['content'].strip()
                
                if attempt < max_retries - 1:
                    time.sleep(1)
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"[!] OpenAI 请求失败（尝试 {attempt + 1}/{max_retries}）: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        
        raise RuntimeError(f'OpenAI API 调用失败（{max_retries} 次重试后）')
    
    def _call_gemini_api(self, prompt: str, max_tokens: int = 256, max_retries: int = 5) -> str:
        """调用 Gemini API（复用 step4 的调用逻辑）"""
        import requests
        import time
        
        api_key = os.getenv('GEMINI_API_KEY')
        proxy_url = os.getenv('GEMINI_PROXY_URL')
        model = os.getenv('TRANSLATION_MODEL', 'gemini-2.5-pro')
        
        if not api_key or not proxy_url:
            raise RuntimeError('Gemini API 配置缺失')
        
        # 构建端点（与 step4 完全一致）
        base = proxy_url[:-1] if proxy_url.endswith('/') else proxy_url
        url = f"{base}/models/{model}:generateContent"
        alt_url = os.getenv('GEMINI_PROXY_URL_ALT', '').strip() or url.replace('gemini_fresh', 'gemini_flash_new')
        
        headers = {
            'x-goog-api-key': api_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": max_tokens
            }
        }
        
        # 重试机制（与 step4 一致）
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=15)
                
                try:
                    response.raise_for_status()
                except requests.HTTPError as he:
                    status = getattr(he.response, 'status_code', None)
                    # 429/503 尝试备用端点
                    if status in (429, 503) and alt_url and alt_url != url:
                        time.sleep(1)
                        response = requests.post(alt_url, headers=headers, json=payload, timeout=15)
                        response.raise_for_status()
                    else:
                        raise
                
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    parts = candidate.get('content', {}).get('parts', [])
                    if parts and isinstance(parts[0], dict) and 'text' in parts[0]:
                        return parts[0]['text'].strip()
                
                # 响应格式无效，重试
                if attempt < max_retries - 1:
                    time.sleep(1)
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"[!] Gemini 请求失败（尝试 {attempt + 1}/{max_retries}）: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        
        raise RuntimeError(f'Gemini API 调用失败（{max_retries} 次重试后）')
    
    def _split_long_line_with_ai(self, text: str, max_chars: int = 40, max_retries: int = 5) -> str:
        """使用 AI API 智能分行（支持 Gemini 和 OpenAI）"""
        import re
        text = re.sub(r'^\[.*?\]\s*', '', text.strip())
        
        if len(text) <= max_chars:
            return text
        
        try:
            prompt = f"""请将以下字幕文本分成多行，每行不超过{max_chars}个字符(严格遵循字符限制)。
要求：
1. 在合适的语义边界处断行（词组、短语、分句）
2. 保持语义完整，不要在词语中间断开
3. 只返回分行后的文本，每行用换行符分隔
4. 不要添加任何解释或标记

原文：
{text}"""
            
            # 根据 TRANSLATION_API_TYPE 选择 API
            api_type = os.getenv('TRANSLATION_API_TYPE', 'gemini').lower()
            
            if api_type == 'openai':
                split_text = self._call_openai_api(prompt, max_tokens=256, max_retries=max_retries)
            else:
                split_text = self._call_gemini_api(prompt, max_tokens=256, max_retries=max_retries)
            
            # 验证结果
            lines = split_text.split('\n')
            valid = all(len(line) <= max_chars * 1.2 for line in lines)
            
            if valid:
                return split_text
            else:
                logger.warning("[!] AI 分行结果超长，使用简单分行")
                return self._fallback_split(text, max_chars)
                
        except Exception as e:
            logger.warning(f"[!] AI 分行失败: {e}")
            return self._fallback_split(text, max_chars)
    
    def _fallback_split(self, text: str, max_chars: int) -> str:
        """标点符号分行回退方案"""
        punctuation = ['。', '！', '？', '，', '、', '.', '!', '?', ',', ';', ' ']
        
        lines = []
        current_line = ""
        
        for char in text:
            current_line += char
            if len(current_line) >= max_chars and char in punctuation:
                lines.append(current_line.strip())
                current_line = ""
        
        if current_line:
            lines.append(current_line.strip())
        
        if len(lines) == 0:
            lines = [text[i:i+max_chars] for i in range(0, len(text), max_chars)]
        
        return '\n'.join(lines)
    
    def process_subtitle(self, 
                        input_srt: Path, 
                        output_srt: Path,
                        max_line_chars: int = 40,
                        use_gemini: bool = True) -> bool:
        """
        处理单个字幕文件（智能分行）
        
        Args:
            input_srt: 输入字幕路径
            output_srt: 输出字幕路径
            max_line_chars: 每行最大字符数
            use_gemini: 是否使用 Gemini 分行
        
        Returns:
            bool: 是否成功
        """
        try:
            import srt
            
            with open(input_srt, 'r', encoding='utf-8') as f:
                subs = list(srt.parse(f.read()))
            
            processed_subs = []
            for sub in subs:
                if use_gemini:
                    processed_text = self._split_long_line_with_ai(sub.content, max_line_chars)
                else:
                    import re
                    text = re.sub(r'^\[.*?\]\s*', '', sub.content.strip())
                    processed_text = self._fallback_split(text, max_line_chars)
                
                processed_sub = srt.Subtitle(
                    index=sub.index,
                    start=sub.start,
                    end=sub.end,
                    content=processed_text
                )
                processed_subs.append(processed_sub)
            
            with open(output_srt, 'w', encoding='utf-8') as f:
                f.write(srt.compose(processed_subs))
            
            logger.info(f"[OK] 字幕处理完成: {output_srt}")
            logger.info(f"     共 {len(processed_subs)} 条字幕")
            return True
            
        except Exception as e:
            logger.error(f"[X] 字幕处理失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_bilingual_subtitle(self,
                                 original_srt: Path,
                                 translated_srt: Path,
                                 output_srt: Path,
                                 max_line_chars: int = 40,
                                 use_gemini: bool = True) -> bool:
        """
        创建双语字幕文件
        
        Args:
            original_srt: 原文字幕路径
            translated_srt: 译文字幕路径
            output_srt: 输出双语字幕路径
            max_line_chars: 每行最大字符数
            use_gemini: 是否使用 Gemini 分行
        
        Returns:
            bool: 是否成功
        """
        try:
            import srt
            
            with open(original_srt, 'r', encoding='utf-8') as f:
                original_subs = list(srt.parse(f.read()))
            
            with open(translated_srt, 'r', encoding='utf-8') as f:
                translated_subs = list(srt.parse(f.read()))
            
            bilingual_subs = []
            for orig, trans in zip(original_subs, translated_subs):
                if use_gemini:
                    orig_text = self._split_long_line_with_ai(orig.content, max_line_chars)
                    trans_text = self._split_long_line_with_ai(trans.content, max_line_chars)
                else:
                    import re
                    orig_content = re.sub(r'^\[.*?\]\s*', '', orig.content.strip())
                    trans_content = re.sub(r'^\[.*?\]\s*', '', trans.content.strip())
                    orig_text = self._fallback_split(orig_content, max_line_chars)
                    trans_text = self._fallback_split(trans_content, max_line_chars)
                
                bilingual_content = f"{orig_text}\n{trans_text}"
                bilingual_sub = srt.Subtitle(
                    index=orig.index,
                    start=orig.start,
                    end=orig.end,
                    content=bilingual_content
                )
                bilingual_subs.append(bilingual_sub)
            
            with open(output_srt, 'w', encoding='utf-8') as f:
                f.write(srt.compose(bilingual_subs))
            
            logger.info(f"[OK] 双语字幕创建完成: {output_srt}")
            logger.info(f"     共 {len(bilingual_subs)} 条字幕")
            return True
            
        except Exception as e:
            logger.error(f"[X] 创建双语字幕失败: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    parser = argparse.ArgumentParser(
        description='处理字幕文件（智能分行、创建双语字幕）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 处理单个字幕（智能分行）
  python step8_process_subtitle.py input.srt output.srt
  
  # 创建双语字幕
  python step8_process_subtitle.py original.srt bilingual_output.srt --bilingual translated.srt
  
  # 禁用 Gemini，使用简单分行
  python step8_process_subtitle.py input.srt output.srt --no-gemini
        """
    )
    
    parser.add_argument('input_srt', help='输入字幕文件路径')
    parser.add_argument('output_srt', help='输出字幕文件路径')
    parser.add_argument('--bilingual', help='译文字幕路径（创建双语字幕）')
    parser.add_argument('--max-line-chars', type=int, default=40,
                       help='每行最大字符数（默认: 40）')
    parser.add_argument('--no-gemini', action='store_true',
                       help='禁用 Gemini 智能分行')
    
    args = parser.parse_args()
    
    try:
        processor = SubtitleProcessor()
        
        input_srt = Path(args.input_srt).resolve()
        output_srt = Path(args.output_srt).resolve()
        
        if not input_srt.exists():
            logger.error(f"[X] 输入字幕不存在: {input_srt}")
            return 1
        
        output_srt.parent.mkdir(parents=True, exist_ok=True)
        
        # 双语模式
        if args.bilingual:
            translated_srt = Path(args.bilingual).resolve()
            if not translated_srt.exists():
                logger.error(f"[X] 译文字幕不存在: {translated_srt}")
                return 1
            
            logger.info("[模式] 创建双语字幕")
            success = processor.create_bilingual_subtitle(
                input_srt,
                translated_srt,
                output_srt,
                max_line_chars=args.max_line_chars,
                use_gemini=not args.no_gemini
            )
        else:
            logger.info("[模式] 处理单语字幕")
            success = processor.process_subtitle(
                input_srt,
                output_srt,
                max_line_chars=args.max_line_chars,
                use_gemini=not args.no_gemini
            )
        
        if success:
            print("\n[完成] 字幕处理成功！")
            print(f"[输出] {output_srt}")
            print("\n[下一步] 使用 step9_embed_to_video.py 将字幕嵌入视频")
            return 0
        else:
            print("\n[失败] 字幕处理失败")
            return 1
            
    except KeyboardInterrupt:
        print("\n[中断] 用户取消操作")
        return 1
    except Exception as e:
        logger.error(f"[错误] 程序异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

