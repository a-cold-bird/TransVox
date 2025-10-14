#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPT-SoVITS TTS 合成脚本
支持本地模式和API模式两种调用方式
"""

import os
import sys
import json
import argparse
import logging
import requests
from pathlib import Path
from typing import List, Dict, Any
import srt
import subprocess

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def _load_dotenv_into_environ():
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

class GPTSoVITSTTS:
    def __init__(self, mode="local", api_host="127.0.0.1", api_port=9880, config_path=None):
        """
        初始化GPT-SoVITS TTS客户端
        
        Args:
            mode: "local" 或 "api"
            api_host: API服务器地址
            api_port: API服务器端口
            config_path: 本地模式配置文件路径
        """
        self.mode = mode
        self.api_host = api_host
        self.api_port = api_port
        self.api_base_url = f"http://{api_host}:{api_port}"
        
        if mode == "local":
            # 确保配置文件路径是绝对路径
            if config_path:
                self.config_path = str(Path(config_path).resolve())
            else:
                self.config_path = str(Path("tools/GPT-SoVITS/GPT_SoVITS/configs/tts_infer.yaml").resolve())
            self._init_local_client()
        else:
            self._test_api_connection()
    
    def _init_local_client(self):
        """初始化本地客户端"""
        try:
            # 获取项目根目录（Scripts的父目录）
            project_root = Path(__file__).resolve().parent.parent
            gpt_sovits_root = project_root / "tools" / "GPT-SoVITS"
            gpt_sovits_lib = gpt_sovits_root / "GPT_SoVITS"

            # 验证路径存在
            if not gpt_sovits_root.exists():
                raise FileNotFoundError(f"GPT-SoVITS目录不存在: {gpt_sovits_root}")

            for path in [str(gpt_sovits_root), str(gpt_sovits_lib)]:
                if path not in sys.path:
                    sys.path.insert(0, path)

            # 清除可能失败的模块导入缓存
            # 这很重要！如果之前导入失败过，Python 会缓存失败结果
            modules_to_clear = [
                'tools', 'tools.i18n', 'tools.i18n.i18n',
                'tools.audio_sr',
                'local_tts',
                'GPT_SoVITS', 'GPT_SoVITS.TTS_infer_pack', 'GPT_SoVITS.TTS_infer_pack.TTS'
            ]
            for module_name in modules_to_clear:
                if module_name in sys.modules:
                    del sys.modules[module_name]
                    logger.debug(f"清除模块缓存: {module_name}")

            # 切换到GPT-SoVITS目录（某些模块可能依赖相对路径）
            original_cwd = os.getcwd()
            os.chdir(str(gpt_sovits_root))

            try:
                from local_tts import LocalTTSClient
                # 在GPT-SoVITS目录中初始化客户端，这样相对路径才正确
                relative_config = os.path.relpath(self.config_path, str(gpt_sovits_root))
                self.local_client = LocalTTSClient(relative_config)
            except ImportError as e:
                logger.error(f"无法导入local_tts模块: {e}")
                logger.error("请确保tools/GPT-SoVITS/local_tts.py存在并且所有依赖已安装")
                raise
            finally:
                # 恢复原始工作目录
                os.chdir(original_cwd)
            logger.info("本地GPT-SoVITS客户端初始化成功")
        except Exception as e:
            logger.error(f"本地客户端初始化失败: {e}")
            raise
    
    def _test_api_connection(self):
        """测试API连接"""
        try:
            response = requests.get(f"{self.api_base_url}/", timeout=5)
            logger.info(f"API连接测试成功: {self.api_base_url}")
        except Exception as e:
            logger.warning(f"API连接测试失败: {e}")
    
    def synthesize_single(self, 
                         text: str,
                         text_lang: str,
                         ref_audio_path: str,
                         prompt_text: str,
                         prompt_lang: str,
                         output_path: str,
                         **kwargs) -> bool:
        """
        单个文本合成
        
        Args:
            text: 要合成的文本
            text_lang: 文本语言 (zh/en/ja/ko)
            ref_audio_path: 参考音频路径
            prompt_text: 参考音频文本
            prompt_lang: 参考音频语言
            output_path: 输出路径
            **kwargs: 其他参数
            
        Returns:
            bool: 是否成功
        """
        if self.mode == "local":
            return self._synthesize_local(text, text_lang, ref_audio_path, 
                                        prompt_text, prompt_lang, output_path, **kwargs)
        else:
            return self._synthesize_api(text, text_lang, ref_audio_path,
                                      prompt_text, prompt_lang, output_path, **kwargs)
    
    def _synthesize_local(self, text, text_lang, ref_audio_path, prompt_text, prompt_lang, output_path, **kwargs):
        """本地模式合成"""
        try:
            # 获取项目根目录
            project_root = Path(__file__).resolve().parent.parent
            gpt_sovits_root = project_root / "tools" / "GPT-SoVITS"

            # ⚠️ 重要：在切换工作目录之前就转换路径为绝对路径！
            # 因为 resolve() 会基于当前工作目录解析相对路径
            abs_ref_audio = Path(ref_audio_path).resolve()
            abs_output = Path(output_path).resolve()

            # 切换到GPT-SoVITS目录进行合成
            original_cwd = os.getcwd()
            os.chdir(str(gpt_sovits_root))

            try:

                success = self.local_client.synthesize_speech(
                    text=text,
                    text_lang=text_lang,
                    ref_audio_path=str(abs_ref_audio),
                    prompt_text=prompt_text,
                    prompt_lang=prompt_lang,
                    output_path=str(abs_output),
                    **kwargs
                )
                return success
            finally:
                os.chdir(original_cwd)

        except Exception as e:
            logger.error(f"本地合成失败: {e}")
            return False
    
    def _synthesize_api(self, text, text_lang, ref_audio_path, prompt_text, prompt_lang, output_path, **kwargs):
        """API模式合成"""
        try:
            # 准备请求参数
            params = {
                "text": text,
                "text_lang": text_lang.lower(),
                "ref_audio_path": ref_audio_path,
                "prompt_text": prompt_text,
                "prompt_lang": prompt_lang.lower(),
                "top_k": kwargs.get("top_k", 5),
                "top_p": kwargs.get("top_p", 1.0),
                "temperature": kwargs.get("temperature", 1.0),
                "text_split_method": kwargs.get("text_split_method", "cut5"),
                "batch_size": kwargs.get("batch_size", 1),
                "speed_factor": kwargs.get("speed_factor", 1.0),
                "seed": kwargs.get("seed", -1),
                "media_type": "wav",
                "streaming_mode": False,
                "repetition_penalty": kwargs.get("repetition_penalty", 1.35)
            }
            
            # 发送请求
            response = requests.post(f"{self.api_base_url}/tts", json=params, timeout=60)
            
            if response.status_code == 200:
                # 保存音频文件
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                file_size = os.path.getsize(output_path)
                logger.info(f"API合成成功: {output_path} ({file_size} bytes)")
                return True
            else:
                logger.error(f"API请求失败: {response.status_code}, {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"API合成失败: {e}")
            return False
    
    def batch_synthesize_from_json(self, json_path: str) -> Dict[str, Any]:
        """
        从JSON文件批量合成
        
        Args:
            json_path: 批量任务JSON文件路径
            
        Returns:
            dict: 合成结果统计
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                tasks = json.load(f)
        except Exception as e:
            logger.error(f"读取JSON文件失败: {e}")
            return {"success": 0, "failed": 1, "error": str(e)}
        
        results = {"success": 0, "failed": 0, "details": []}
        
        logger.info(f"开始批量合成，共 {len(tasks)} 个任务")
        
        for i, task in enumerate(tasks, 1):
            logger.info(f"处理任务 {i}/{len(tasks)}")
            
            try:
                # 检查必需参数
                required_params = ["text", "text_lang", "ref_audio_path", "output_path"]
                missing_params = [p for p in required_params if p not in task]
                if missing_params:
                    logger.error(f"任务 {i} 缺少参数: {missing_params}")
                    results["failed"] += 1
                    results["details"].append({
                        "task": i, 
                        "status": "failed", 
                        "error": f"缺少参数: {missing_params}",
                        "params": task
                    })
                    continue
                
                # 执行合成
                success = self.synthesize_single(**task)
                
                if success:
                    results["success"] += 1
                    results["details"].append({"task": i, "status": "success", "params": task})
                    logger.info(f"任务 {i} 完成: {task['output_path']}")
                else:
                    results["failed"] += 1
                    results["details"].append({"task": i, "status": "failed", "params": task})
                    
            except Exception as e:
                logger.error(f"任务 {i} 执行异常: {e}")
                results["failed"] += 1
                results["details"].append({
                    "task": i, 
                    "status": "error", 
                    "error": str(e), 
                    "params": task
                })
        
        logger.info(f"批量合成完成: 成功 {results['success']} 个，失败 {results['failed']} 个")
        return results

def main():
    parser = argparse.ArgumentParser(description='GPT-SoVITS TTS 合成脚本')
    parser.add_argument('--mode', choices=['api', 'local'], default='local', help='运行模式')
    parser.add_argument('--api_host', default='127.0.0.1', help='API服务器地址')
    parser.add_argument('--api_port', type=int, default=9880, help='API服务器端口')
    parser.add_argument('--api_url', help='API完整URL (优先于api_host和api_port)')
    parser.add_argument('--config', help='本地模式配置文件路径')
    
    # 单个合成参数
    parser.add_argument('--text', help='要合成的文本')
    parser.add_argument('--text_lang', choices=['zh', 'en', 'ja', 'ko', 'auto'], default='auto', help='文本语言')
    parser.add_argument('--ref_audio', help='参考音频路径')
    parser.add_argument('--prompt_text', help='参考音频文本')
    parser.add_argument('--prompt_lang', choices=['zh', 'en', 'ja', 'ko'], default='zh', help='参考音频语言')
    parser.add_argument('--output', help='输出音频路径')
    
    # 批量合成参数
    parser.add_argument('--batch_json', help='批量合成JSON文件路径')
    
    # TTS参数
    parser.add_argument('--temperature', type=float, default=1.0, help='采样温度')
    parser.add_argument('--top_k', type=int, default=5, help='Top-k采样')
    parser.add_argument('--top_p', type=float, default=1.0, help='Top-p采样')
    parser.add_argument('--speed_factor', type=float, default=1.0, help='语速控制')
    
    args = parser.parse_args()
    
    try:
        # 初始化TTS客户端
        if args.mode == 'api' and args.api_url:
            # 从完整URL解析host和port
            from urllib.parse import urlparse
            parsed = urlparse(args.api_url)
            api_host = parsed.hostname or args.api_host
            api_port = parsed.port or args.api_port
            logger.info(f"使用API URL: {args.api_url} (解析为 {api_host}:{api_port})")
        else:
            api_host = args.api_host
            api_port = args.api_port
        
        tts_client = GPTSoVITSTTS(
            mode=args.mode,
            api_host=api_host,
            api_port=api_port,
            config_path=args.config
        )
        
        # 批量合成
        if args.batch_json:
            results = tts_client.batch_synthesize_from_json(args.batch_json)
            print(f"\n批量合成结果: 成功 {results['success']} 个，失败 {results['failed']} 个")
            return 0 if results['failed'] == 0 else 1
        
        # 单个合成
        if args.text and args.ref_audio and args.output:
            success = tts_client.synthesize_single(
                text=args.text,
                text_lang=args.text_lang,
                ref_audio_path=args.ref_audio,
                prompt_text=args.prompt_text or '',
                prompt_lang=args.prompt_lang,
                output_path=args.output,
                temperature=args.temperature,
                top_k=args.top_k,
                top_p=args.top_p,
                speed_factor=args.speed_factor
            )
            
            if success:
                print("合成成功!")
                return 0
            else:
                print("合成失败!")
                return 1
        
        print("请指定 --batch_json 进行批量合成，或指定 --text, --ref_audio, --output 进行单个合成")
        return 1
        
    except KeyboardInterrupt:
        print("\n用户中断")
        return 1
    except Exception as e:
        logger.error(f"程序异常: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
