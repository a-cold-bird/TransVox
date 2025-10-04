#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPT-SoVITS 本地调用脚本
直接使用TTS核心功能，无需API服务器
输入路径: input/
输出路径: output/
"""

import os
import sys
import argparse
import numpy as np
import soundfile as sf
from pathlib import Path

# 添加GPT-SoVITS路径到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "GPT_SoVITS"))

from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config

class LocalTTSClient:
    def __init__(self, config_path="GPT_SoVITS/configs/tts_infer.yaml"):
        """
        初始化本地TTS客户端
        
        Args:
            config_path (str): TTS配置文件路径
        """
        
        print("[初始化] 加载TTS配置...")
        try:
            self.tts_config = TTS_Config(config_path)
            print(f"[成功] 配置加载完成")
            print(f"[信息] 设备: {self.tts_config.device}")
            print(f"[信息] 版本: {self.tts_config.version}")
            print(f"[信息] 半精度: {self.tts_config.is_half}")
        except Exception as e:
            print(f"[错误] 配置加载失败: {e}")
            raise
        
        print("[初始化] 加载TTS模型...")
        try:
            self.tts_pipeline = TTS(self.tts_config)
            print("[成功] TTS模型加载完成")
        except Exception as e:
            print(f"[错误] TTS模型加载失败: {e}")
            raise
    
    
    def synthesize_speech(self, 
                         text, 
                         text_lang, 
                         ref_audio_path, 
                         prompt_text="", 
                         prompt_lang="zh",
                         output_path=None,
                         **kwargs):
        """
        本地语音合成
        
        Args:
            text (str): 要合成的文本
            text_lang (str): 文本语言 (zh/en/ja/ko)
            ref_audio_path (str): 参考音频文件完整路径
            prompt_text (str): 参考音频的提示文本
            prompt_lang (str): 提示文本语言
            output_path (str): 输出文件完整路径
            **kwargs: 其他TTS参数
            
        Returns:
            bool: 是否成功
        """
        
        # 检查输出路径
        if output_path is None:
            output_path = f"output_{text_lang}.wav"
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # 检查参考音频文件
        if not os.path.exists(ref_audio_path):
            print(f"[错误] 参考音频文件不存在: {ref_audio_path}")
            return False
        
        print(f"[信息] 参考音频: {ref_audio_path}")
        print(f"[信息] 参考文本: {prompt_text}")
        print(f"[信息] 目标文本: {text}")
        print(f"[信息] 目标语言: {text_lang}")
        print(f"[信息] 输出路径: {output_path}")
        
        # 设置TTS参数
        tts_params = {
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
            "batch_threshold": kwargs.get("batch_threshold", 0.75),
            "split_bucket": kwargs.get("split_bucket", True),
            "speed_factor": kwargs.get("speed_factor", 1.0),
            "fragment_interval": kwargs.get("fragment_interval", 0.3),
            "seed": kwargs.get("seed", -1),
            "parallel_infer": kwargs.get("parallel_infer", True),
            "repetition_penalty": kwargs.get("repetition_penalty", 1.35),
            "sample_steps": kwargs.get("sample_steps", 32),
            "super_sampling": kwargs.get("super_sampling", False),
            "return_fragment": False  # 不使用片段返回模式
        }
        
        try:
            print("[请求] 开始语音合成...")
            
            # 调用TTS合成
            tts_generator = self.tts_pipeline.run(tts_params)
            
            # 获取合成结果
            sample_rate, audio_data = next(tts_generator)
            
            # 保存音频文件
            sf.write(output_path, audio_data, sample_rate, format='wav')
            
            # 显示结果信息
            file_size = os.path.getsize(output_path)
            duration = len(audio_data) / sample_rate
            print(f"[成功] 音频已保存到: {output_path}")
            print(f"[信息] 文件大小: {file_size} bytes")
            print(f"[信息] 采样率: {sample_rate} Hz")
            print(f"[信息] 音频时长: {duration:.2f} 秒")
            
            return True
            
        except Exception as e:
            print(f"[错误] 语音合成失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def batch_synthesize(self, task_list):
        """
        批量语音合成
        
        Args:
            task_list (list): 任务列表，每个任务是一个字典包含合成参数
                              每个任务应包含: text, text_lang, ref_audio_path, output_path等
            
        Returns:
            dict: 合成结果统计
        """
        results = {"success": 0, "failed": 0, "details": []}
        
        print(f"[批量] 开始批量合成，共 {len(task_list)} 个任务")
        
        for i, task in enumerate(task_list, 1):
            print(f"\n[批量] 处理任务 {i}/{len(task_list)}")
            
            try:
                # 确保必需的参数存在
                if "ref_audio_path" not in task:
                    print(f"[错误] 任务 {i} 缺少 ref_audio_path 参数")
                    results["failed"] += 1
                    results["details"].append({"task": i, "status": "failed", "error": "缺少ref_audio_path", "params": task})
                    continue
                
                if "output_path" not in task:
                    print(f"[错误] 任务 {i} 缺少 output_path 参数")
                    results["failed"] += 1
                    results["details"].append({"task": i, "status": "failed", "error": "缺少output_path", "params": task})
                    continue
                
                success = self.synthesize_speech(**task)
                if success:
                    results["success"] += 1
                    results["details"].append({"task": i, "status": "success", "params": task})
                else:
                    results["failed"] += 1
                    results["details"].append({"task": i, "status": "failed", "params": task})
            except Exception as e:
                print(f"[错误] 任务 {i} 执行失败: {e}")
                results["failed"] += 1
                results["details"].append({"task": i, "status": "error", "error": str(e), "params": task})
        
        print(f"\n[批量] 批量合成完成: 成功 {results['success']} 个，失败 {results['failed']} 个")
        return results

def main():
    parser = argparse.ArgumentParser(description="GPT-SoVITS 本地语音合成")
    
    # 基本参数
    parser.add_argument("--config", default="GPT_SoVITS/configs/tts_infer.yaml", help="TTS配置文件路径")
    parser.add_argument("--text", help="要合成的文本")
    parser.add_argument("--text_lang", default="zh", choices=["zh", "en", "ja", "ko"], help="文本语言")
    parser.add_argument("--ref_audio", help="参考音频文件完整路径")
    parser.add_argument("--prompt_text", default="", help="参考音频的提示文本")
    parser.add_argument("--prompt_lang", default="zh", choices=["zh", "en", "ja", "ko"], help="提示文本语言")
    parser.add_argument("--output", help="输出音频文件完整路径")
    
    
    # 高级参数
    parser.add_argument("--top_k", type=int, default=5, help="Top-k采样参数")
    parser.add_argument("--top_p", type=float, default=1.0, help="Top-p采样参数")
    parser.add_argument("--temperature", type=float, default=1.0, help="采样温度")
    parser.add_argument("--text_split_method", default="cut5", help="文本分割方法")
    parser.add_argument("--batch_size", type=int, default=1, help="批处理大小")
    parser.add_argument("--speed_factor", type=float, default=1.0, help="语速控制")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--repetition_penalty", type=float, default=1.35, help="重复惩罚")
    
    # 功能选项
    parser.add_argument("--batch_file", help="批量处理配置文件 (JSON格式)")
    
    args = parser.parse_args()
    
    try:
        # 初始化TTS客户端
        client = LocalTTSClient(args.config)
        
        # 批量处理
        if args.batch_file:
            import json
            with open(args.batch_file, 'r', encoding='utf-8') as f:
                task_list = json.load(f)
            results = client.batch_synthesize(task_list)
            print(f"\n[结果] 批量处理完成: {results['success']} 成功, {results['failed']} 失败")
            return
        
        # 检查必需参数
        if not args.text:
            print("[错误] 需要指定 --text 参数")
            sys.exit(1)
        if not args.ref_audio:
            print("[错误] 需要指定 --ref_audio 参数")
            sys.exit(1)
        if not args.output:
            print("[错误] 需要指定 --output 参数")
            sys.exit(1)
        
        # 单个合成任务
        success = client.synthesize_speech(
            text=args.text,
            text_lang=args.text_lang,
            ref_audio_path=args.ref_audio,
            prompt_text=args.prompt_text,
            prompt_lang=args.prompt_lang,
            output_path=args.output,
            top_k=args.top_k,
            top_p=args.top_p,
            temperature=args.temperature,
            text_split_method=args.text_split_method,
            batch_size=args.batch_size,
            speed_factor=args.speed_factor,
            seed=args.seed,
            repetition_penalty=args.repetition_penalty
        )
        
        if success:
            print("\n[完成] 语音合成成功!")
            sys.exit(0)
        else:
            print("\n[失败] 语音合成失败!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n[中断] 用户中断了程序")
        sys.exit(1)
    except Exception as e:
        print(f"\n[异常] 程序执行异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
