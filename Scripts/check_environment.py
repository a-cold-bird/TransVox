#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境检测脚本
检查 GPU、依赖库、模型文件是否就绪
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EnvironmentChecker:
    """环境检测器"""
    
    def __init__(self):
        self.project_root = Path(__file__).resolve().parent
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0
    
    def print_section(self, title: str):
        """打印章节标题"""
        print("\n" + "="*60)
        print(f"  {title}")
        print("="*60)
    
    def check_gpu(self) -> bool:
        """检查 GPU 和 CUDA 是否可用"""
        self.print_section("检查 GPU 和 CUDA")
        
        try:
            import torch
            print(f"[OK] PyTorch 版本: {torch.__version__}")
            
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                print(f"[OK] CUDA 可用: {torch.version.cuda}")
                print(f"[OK] 检测到 {gpu_count} 个 GPU:")
                
                for i in range(gpu_count):
                    gpu_name = torch.cuda.get_device_name(i)
                    gpu_memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)
                    print(f"   GPU {i}: {gpu_name} ({gpu_memory:.1f} GB)")
                
                # 测试 GPU 计算
                try:
                    test_tensor = torch.randn(100, 100).cuda()
                    result = test_tensor @ test_tensor
                    print("[OK] GPU 计算测试通过")
                    self.checks_passed += 1
                    return True
                except Exception as e:
                    print(f"[!] GPU 计算测试失败: {e}")
                    self.warnings += 1
                    return False
            else:
                print("[X] CUDA 不可用，将使用 CPU 模式（速度较慢）")
                self.checks_failed += 1
                return False
                
        except ImportError:
            print("[X] PyTorch 未安装")
            self.checks_failed += 1
            return False
        except Exception as e:
            print(f"[X] GPU 检查异常: {e}")
            self.checks_failed += 1
            return False
    
    def check_ffmpeg(self) -> bool:
        """检查 ffmpeg 是否安装"""
        self.print_section("检查 FFmpeg")
        
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], 
                                   capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                print(f"[OK] {version_line}")
                self.checks_passed += 1
                return True
            else:
                print("[X] ffmpeg 命令执行失败")
                self.checks_failed += 1
                return False
        except FileNotFoundError:
            print("[X] ffmpeg 未安装或不在 PATH 中")
            print("   请安装: scoop install ffmpeg  或  choco install ffmpeg")
            self.checks_failed += 1
            return False
        except Exception as e:
            print(f"[X] ffmpeg 检查异常: {e}")
            self.checks_failed += 1
            return False
    
    def check_indextts(self) -> bool:
        """检查 IndexTTS 是否可用"""
        self.print_section("检查 IndexTTS")
        
        # 检查模型文件
        indextts_dir = self.project_root / 'tools' / 'index-tts'
        checkpoints_dir = indextts_dir / 'checkpoints'
        config_file = checkpoints_dir / 'config.yaml'
        
        if not indextts_dir.exists():
            print(f"[X] IndexTTS 目录不存在: {indextts_dir}")
            self.checks_failed += 1
            return False
        
        if not config_file.exists():
            print(f"[X] IndexTTS 配置文件不存在: {config_file}")
            print("   请运行: python download_models.py")
            self.checks_failed += 1
            return False
        
        print(f"[OK] IndexTTS 目录存在: {indextts_dir}")
        print(f"[OK] 配置文件存在: {config_file}")
        
        # 检查模型文件
        model_files = list(checkpoints_dir.glob('**/*.safetensors'))
        if model_files:
            print(f"[OK] 检测到 {len(model_files)} 个模型文件")
        else:
            print("[!] 未检测到 .safetensors 模型文件")
            self.warnings += 1
        
        # 尝试导入
        try:
            sys.path.insert(0, str(indextts_dir))
            from indextts.infer_v2 import IndexTTS2
            print("[OK] IndexTTS 模块导入成功")
            self.checks_passed += 1
            return True
        except ImportError as e:
            print(f"[X] IndexTTS 模块导入失败: {e}")
            print("   请检查 tools/index-tts 目录是否完整")
            self.checks_failed += 1
            return False
        except Exception as e:
            print(f"[!] IndexTTS 导入异常: {e}")
            self.warnings += 1
            return False
    
    def check_gptsovits(self) -> bool:
        """检查 GPT-SoVITS 是否可用"""
        self.print_section("检查 GPT-SoVITS")
        
        # 检查目录和配置文件
        gptsovits_dir = self.project_root / 'tools' / 'GPT-SoVITS'
        config_file = gptsovits_dir / 'GPT_SoVITS' / 'configs' / 'tts_infer.yaml'
        pretrained_dir = gptsovits_dir / 'GPT_SoVITS' / 'pretrained_models'
        
        if not gptsovits_dir.exists():
            print(f"[X] GPT-SoVITS 目录不存在: {gptsovits_dir}")
            self.checks_failed += 1
            return False
        
        print(f"[OK] GPT-SoVITS 目录存在: {gptsovits_dir}")
        
        if not config_file.exists():
            print(f"[X] 配置文件不存在: {config_file}")
            self.checks_failed += 1
            return False
        
        print(f"[OK] 配置文件存在: {config_file}")
        
        # 检查预训练模型
        if not pretrained_dir.exists():
            print(f"[X] 预训练模型目录不存在: {pretrained_dir}")
            print("   请运行: python download_models.py")
            self.checks_failed += 1
            return False
        
        # 检查关键模型文件
        ckpt_files = list(pretrained_dir.glob('**/*.ckpt'))
        pth_files = list(pretrained_dir.glob('**/*.pth'))
        
        if ckpt_files and pth_files:
            print(f"[OK] 检测到预训练模型:")
            print(f"   - {len(ckpt_files)} 个 .ckpt 文件")
            print(f"   - {len(pth_files)} 个 .pth 文件")
            self.checks_passed += 1
            return True
        else:
            print(f"[X] 预训练模型不完整:")
            print(f"   - .ckpt 文件: {len(ckpt_files)}")
            print(f"   - .pth 文件: {len(pth_files)}")
            print("   请运行: python download_models.py")
            self.checks_failed += 1
            return False
    
    def check_msst(self) -> bool:
        """检查 MSST-WebUI 是否可用"""
        self.print_section("检查 MSST-WebUI")
        
        msst_dir = self.project_root / 'tools' / 'MSST-WebUI'
        pretrain_dir = msst_dir / 'pretrain'
        
        if not msst_dir.exists():
            print(f"[X] MSST-WebUI 目录不存在: {msst_dir}")
            self.checks_failed += 1
            return False
        
        print(f"[OK] MSST-WebUI 目录存在: {msst_dir}")
        
        # 检查必需的模型文件（在子目录中）
        required_models = [
            ('vocal_models', 'model_mel_band_roformer_karaoke_aufr33_viperx_sdr_10.1956.ckpt'),
            ('vocal_models', 'big_beta5e.ckpt'),
            ('single_stem_models', 'dereverb_mel_band_roformer_less_aggressive_anvuew_sdr_18.8050.ckpt')
        ]
        
        missing_models = []
        for subdir, model_name in required_models:
            model_path = pretrain_dir / subdir / model_name
            if model_path.exists():
                size_mb = model_path.stat().st_size / (1024 * 1024)
                print(f"[OK] {subdir}/{model_name} ({size_mb:.1f} MB)")
            else:
                print(f"[X] {subdir}/{model_name} (缺失)")
                missing_models.append(f"{subdir}/{model_name}")
        
        if missing_models:
            print(f"\n[X] 缺少 {len(missing_models)} 个模型文件")
            print("   请运行: python download_models.py")
            self.checks_failed += 1
            return False
        
        print("[OK] 所有 MSST 模型文件就绪")
        self.checks_passed += 1
        return True
    
    def check_whisperx(self) -> bool:
        """检查 WhisperX 是否可用"""
        self.print_section("检查 WhisperX")
        
        try:
            import whisperx
            print(f"[OK] WhisperX 已安装")
            self.checks_passed += 1
            return True
        except ImportError:
            print("[X] WhisperX 未安装")
            print("   请运行: pip install -r requirements_all.txt")
            self.checks_failed += 1
            return False
    
    def check_dependencies(self) -> bool:
        """检查关键 Python 依赖"""
        self.print_section("检查 Python 依赖")
        
        dependencies = [
            ('torch', 'PyTorch'),
            ('numpy', 'NumPy'),
            ('srt', 'srt'),
            ('pydub', 'pydub'),
            ('tqdm', 'tqdm'),
            ('requests', 'requests'),
        ]
        
        all_ok = True
        for module_name, display_name in dependencies:
            try:
                module = __import__(module_name)
                version = getattr(module, '__version__', 'unknown')
                print(f"[OK] {display_name}: {version}")
            except ImportError:
                print(f"[X] {display_name} 未安装")
                all_ok = False
        
        if all_ok:
            self.checks_passed += 1
            return True
        else:
            print("\n请运行: pip install -r requirements_all.txt")
            self.checks_failed += 1
            return False
    
    def check_env_variables(self) -> bool:
        """检查环境变量配置"""
        self.print_section("检查环境变量")
        
        # 尝试从 .env 加载
        dotenv_path = self.project_root / '.env'
        env_vars = {}
        
        if dotenv_path.exists():
            print(f"[OK] 检测到 .env 文件: {dotenv_path}")
            try:
                with open(dotenv_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            k, v = line.split('=', 1)
                            env_vars[k.strip()] = v.strip().strip('"').strip("'")
            except Exception as e:
                print(f"[!] 读取 .env 失败: {e}")
        else:
            print("[!] .env 文件不存在")
        
        # 检查关键环境变量（支持多个可能的变量名）
        required_vars = {
            'GEMINI_API_KEY': '用于字幕翻译',
            'HUGGINGFACE_TOKEN': '用于说话人识别（pyannote）',  # 主要使用的变量名
        }
        
        # HF Token 的备选变量名
        hf_token_alternatives = ['HUGGINGFACE_TOKEN', 'HUGGING_FACE_HUB_TOKEN', 'HF_TOKEN']
        
        optional_vars = {
            'TRANSLATION_MODEL': 'Gemini 模型版本（默认: gemini-2.5-pro）',
            'HF_ENDPOINT': 'Hugging Face 镜像站（可选）'
        }
        
        all_ok = True
        
        print("\n必需的环境变量:")
        
        # 检查 GEMINI_API_KEY
        if 'GEMINI_API_KEY' in env_vars or 'GEMINI_API_KEY' in os.environ:
            value = env_vars.get('GEMINI_API_KEY') or os.environ.get('GEMINI_API_KEY', '')
            masked_value = value[:10] + '...' if len(value) > 10 else value
            print(f"[OK] GEMINI_API_KEY: {masked_value} (用于字幕翻译)")
        else:
            print(f"[X] GEMINI_API_KEY: 未设置 (用于字幕翻译)")
            all_ok = False
        
        # 检查 HF Token（支持多个变量名）
        hf_token_found = False
        hf_token_var = None
        for var in hf_token_alternatives:
            if var in env_vars or var in os.environ:
                value = env_vars.get(var) or os.environ.get(var, '')
                masked_value = value[:10] + '...' if len(value) > 10 else value
                print(f"[OK] {var}: {masked_value} (用于说话人识别)")
                hf_token_found = True
                hf_token_var = var
                break
        
        if not hf_token_found:
            print(f"[X] HUGGINGFACE_TOKEN: 未设置 (用于说话人识别（pyannote）)")
            print(f"   支持的变量名: {', '.join(hf_token_alternatives)}")
            all_ok = False
        
        print("\n可选的环境变量:")
        for var_name, description in optional_vars.items():
            if var_name in env_vars or var_name in os.environ:
                value = env_vars.get(var_name) or os.environ.get(var_name, '')
                print(f"[OK] {var_name}: {value} ({description})")
            else:
                print(f"[!] {var_name}: 未设置 ({description})")
        
        if all_ok:
            self.checks_passed += 1
            return True
        else:
            print("\n请在项目根目录创建 .env 文件并配置必需的环境变量")
            self.warnings += 1
            return False
    
    def run_all_checks(self) -> bool:
        """运行所有检查"""
        print("\n" + "=" + "环境检测开始".center(58, "=") + "=")
        
        # 1. 检查 GPU
        gpu_ok = self.check_gpu()
        
        # 2. 检查 ffmpeg
        ffmpeg_ok = self.check_ffmpeg()
        
        # 3. 检查 Python 依赖
        deps_ok = self.check_dependencies()
        
        # 4. 检查 MSST
        msst_ok = self.check_msst()
        
        # 5. 检查 GPT-SoVITS
        gptsovits_ok = self.check_gptsovits()
        
        # 6. 检查 IndexTTS
        indextts_ok = self.check_indextts()
        
        # 7. 检查 WhisperX
        whisperx_ok = self.check_whisperx()
        
        # 8. 检查环境变量
        env_ok = self.check_env_variables()
        
        # 总结
        self.print_section("检测结果总结")
        
        print(f"\n[OK] 通过: {self.checks_passed} 项")
        print(f"[!] 警告: {self.warnings} 项")
        print(f"[X] 失败: {self.checks_failed} 项")
        
        all_critical_ok = (
            ffmpeg_ok and 
            deps_ok and 
            msst_ok and 
            gptsovits_ok and 
            indextts_ok and 
            whisperx_ok
        )
        
        if all_critical_ok:
            print("\n" + "=" + "环境检测通过！".center(58, "=") + "=")
            if not gpu_ok:
                print("\n[!] 注意: GPU 不可用，将使用 CPU 模式（速度较慢）")
            if not env_ok:
                print("\n[!] 注意: 部分环境变量未配置，某些功能可能无法使用")
                print("   请参考 README.md 配置 Gemini API Key 和 Hugging Face Token")
            print("\n你可以开始使用视频翻译工具了！")
            print("运行示例:")
            print("  python full_auto_pipeline.py input/your_video.mp4 --target_lang zh")
            return True
        else:
            print("\n" + "=" + "环境检测未通过".center(58, "=") + "=")
            print("\n请根据上述错误信息修复环境问题。")
            print("常见解决方案:")
            print("  1. 安装依赖: pip install -r requirements_all.txt")
            print("  2. 下载模型: python download_models.py")
            print("  3. 安装 ffmpeg: scoop install ffmpeg (Windows) 或 apt-get install ffmpeg (Linux)")
            return False


def main():
    print("\n" + "="*60)
    print("  视频翻译工具 - 环境检测脚本")
    print("="*60)
    
    try:
        checker = EnvironmentChecker()
        success = checker.run_all_checks()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⏹️ 用户中断检测")
        return 1
    except Exception as e:
        logger.error(f"程序异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

