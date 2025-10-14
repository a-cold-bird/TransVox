#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型下载和检查脚本
自动下载所需的 MSST、GPT-SoVITS 和 IndexTTS 模型
支持使用 Hugging Face 镜像站加速下载
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import List, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _load_dotenv_into_environ():
    """加载 .env 环境变量"""
    try:
        root = Path(__file__).resolve().parent
        dotenv_path = root / '.env'
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
            logger.info(f"[OK] 已从 .env 加载环境变量: {dotenv_path}")
    except Exception as e:
        logger.warning(f"加载 .env 失败: {e}")


class ModelDownloader:
    """模型下载器"""
    
    def __init__(self):
        self.project_root = Path(__file__).resolve().parent
        
        # 从环境变量读取 HF_ENDPOINT
        hf_endpoint = os.getenv('HF_ENDPOINT', '').strip()
        if hf_endpoint:
            logger.info(f"[OK] 使用 HF 镜像站: {hf_endpoint}")
        else:
            logger.info("使用官方 Hugging Face 源")
    
    def check_hf_cli(self) -> bool:
        """检查 huggingface-cli 是否安装"""
        try:
            result = subprocess.run(['huggingface-cli', '--version'], 
                                   capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logger.info(f"[OK] huggingface-cli 已安装: {result.stdout.strip()}")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        logger.error("[X] huggingface-cli 未安装")
        logger.info("请安装: pip install huggingface-hub[cli]")
        return False
    
    def check_model_exists(self, model_path: Path) -> bool:
        """检查模型文件是否存在"""
        if model_path.exists():
            size_mb = model_path.stat().st_size / (1024 * 1024)
            logger.info(f"[OK] 已存在: {model_path.name} ({size_mb:.1f} MB)")
            return True
        return False
    
    def download_msst_models(self) -> bool:
        """下载 MSST-WebUI 模型"""
        logger.info("\n" + "="*60)
        logger.info("[下载] MSST-WebUI 人声分离模型")
        logger.info("="*60)
        
        msst_pretrain = self.project_root / 'tools' / 'MSST-WebUI' / 'pretrain'
        msst_pretrain.mkdir(parents=True, exist_ok=True)
        
        models = [
            {
                'url': 'https://hf-mirror.com/Sucial/MSST-WebUI/resolve/main/All_Models/vocal_models/model_mel_band_roformer_karaoke_aufr33_viperx_sdr_10.1956.ckpt',
                'path': msst_pretrain / 'vocal_models' / 'model_mel_band_roformer_karaoke_aufr33_viperx_sdr_10.1956.ckpt',
                'name': 'Karaoke 人声分离模型'
            },
            {
                'url': 'https://hf-mirror.com/Sucial/MSST-WebUI/resolve/main/All_Models/vocal_models/big_beta5e.ckpt',
                'path': msst_pretrain / 'vocal_models' / 'big_beta5e.ckpt',
                'name': 'Big Beta 人声分离模型'
            },
            {
                'url': 'https://hf-mirror.com/Sucial/MSST-WebUI/resolve/main/All_Models/single_stem_models/dereverb_mel_band_roformer_less_aggressive_anvuew_sdr_18.8050.ckpt',
                'path': msst_pretrain / 'single_stem_models' / 'dereverb_mel_band_roformer_less_aggressive_anvuew_sdr_18.8050.ckpt',
                'name': 'Dereverb 去混响模型'
            }
        ]
        
        all_exist = True
        for model in models:
            logger.info(f"\n检查: {model['name']}")
            if self.check_model_exists(model['path']):
                continue
            
            all_exist = False
            logger.info(f"下载: {model['name']}...")
            
            try:
                # 使用 wget 或 curl 下载
                if self._download_file(model['url'], model['path']):
                    logger.info(f"[OK] 下载完成: {model['name']}")
                else:
                    logger.error(f"[X] 下载失败: {model['name']}")
                    return False
            except Exception as e:
                logger.error(f"[X] 下载异常: {e}")
                return False
        
        if all_exist:
            logger.info("\n[OK] 所有 MSST 模型已存在，跳过下载")
        else:
            logger.info("\n[OK] MSST 模型下载完成")
        return True
    
    def download_gptsovits_models(self) -> bool:
        """下载 GPT-SoVITS 模型"""
        logger.info("\n" + "="*60)
        logger.info("📦 下载 GPT-SoVITS 模型")
        logger.info("="*60)
        
        gpt_sovits_dir = self.project_root / 'tools' / 'GPT-SoVITS' / 'GPT_SoVITS'
        gpt_sovits_dir.mkdir(parents=True, exist_ok=True)
        
        # 检查是否已有预训练模型
        pretrained_dir = gpt_sovits_dir / 'pretrained_models'
        if pretrained_dir.exists() and any(pretrained_dir.glob('**/*.ckpt')):
            logger.info(f"[OK] 检测到已有 GPT-SoVITS 模型: {pretrained_dir}")
            logger.info("跳过下载（如需重新下载，请删除该目录）")
            return True
        
        logger.info("下载 GPT-SoVITS 预训练模型...")
        logger.info("仓库: lj1995/GPT-SoVITS")
        
        try:
            # 切换到 GPT-SoVITS 目录
            os.chdir(str(gpt_sovits_dir))
            
            cmd = ['huggingface-cli', 'download', 'lj1995/GPT-SoVITS', '--local-dir', '.']
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
            logger.info("[OK] GPT-SoVITS 模型下载完成")
            
            # 返回项目根目录
            os.chdir(str(self.project_root))
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"[X] GPT-SoVITS 模型下载失败: {e}")
            logger.error(f"错误输出: {e.stderr}")
            os.chdir(str(self.project_root))
            return False
        except Exception as e:
            logger.error(f"[X] GPT-SoVITS 下载异常: {e}")
            os.chdir(str(self.project_root))
            return False
    
    def download_indextts_models(self) -> bool:
        """下载 IndexTTS 模型"""
        logger.info("\n" + "="*60)
        logger.info("📦 下载 IndexTTS 模型")
        logger.info("="*60)
        
        indextts_dir = self.project_root / 'tools' / 'index-tts'
        checkpoints_dir = indextts_dir / 'checkpoints'
        checkpoints_dir.mkdir(parents=True, exist_ok=True)
        
        # 检查是否已有模型
        if (checkpoints_dir / 'config.yaml').exists() and any(checkpoints_dir.glob('**/*.safetensors')):
            logger.info(f"[OK] 检测到已有 IndexTTS 模型: {checkpoints_dir}")
            logger.info("跳过下载（如需重新下载，请删除该目录）")
            return True
        
        logger.info("下载 IndexTTS 预训练模型...")
        logger.info("仓库: IndexTeam/IndexTTS-2")
        
        try:
            cmd = ['huggingface-cli', 'download', 'IndexTeam/IndexTTS-2', 
                   '--local-dir', str(checkpoints_dir)]
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
            logger.info("[OK] IndexTTS 模型下载完成")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"[X] IndexTTS 模型下载失败: {e}")
            logger.error(f"错误输出: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"[X] IndexTTS 下载异常: {e}")
            return False
    
    def _download_file(self, url: str, output_path: Path) -> bool:
        """使用 wget 或 curl 下载文件"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 尝试使用 wget
        try:
            cmd = ['wget', '-O', str(output_path), url, '--no-check-certificate']
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
        
        # 尝试使用 curl
        try:
            cmd = ['curl', '-L', '-o', str(output_path), url, '--insecure']
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
        
        # 尝试使用 Python urllib
        try:
            import urllib.request
            logger.info("使用 Python urllib 下载...")
            urllib.request.urlretrieve(url, str(output_path))
            return True
        except Exception as e:
            logger.error(f"下载失败: {e}")
            return False
    
    def download_all(self) -> bool:
        """下载所有模型"""
        logger.info("\n[启动] 开始下载所有必需模型\n")
        
        success = True
        
        # 1. 下载 MSST 模型
        if not self.download_msst_models():
            logger.error("MSST 模型下载失败")
            success = False
        
        # 2. 下载 GPT-SoVITS 模型
        if not self.download_gptsovits_models():
            logger.error("GPT-SoVITS 模型下载失败")
            success = False
        
        # 3. 下载 IndexTTS 模型
        if not self.download_indextts_models():
            logger.error("IndexTTS 模型下载失败")
            success = False
        
        return success


def main():
    print("="*60)
    print("视频翻译工具 - 模型下载脚本")
    print("="*60)
    print("\n本脚本将下载以下模型：")
    print("1. MSST-WebUI 人声分离模型（3个文件，约 500MB）")
    print("2. GPT-SoVITS 预训练模型（约 2-3GB）")
    print("3. IndexTTS-2 预训练模型（约 1-2GB）")
    print("\n[提示] 如需使用 HF 镜像站，请在 .env 中设置: HF_ENDPOINT=https://hf-mirror.com\n")
    
    # 加载 .env 环境变量
    _load_dotenv_into_environ()
    
    print("\n" + "="*60)
    print("开始下载模型...")
    print("="*60 + "\n")
    
    try:
        downloader = ModelDownloader()
        
        # 检查 huggingface-cli
        if not downloader.check_hf_cli():
            print("\n[X] 请先安装 huggingface-hub:")
            print("   pip install huggingface-hub[cli]")
            return 1
        
        # 下载所有模型
        success = downloader.download_all()
        
        if success:
            print("\n" + "="*60)
            print("[完成] 所有模型下载完成！")
            print("="*60)
            print("\n你现在可以开始使用视频翻译工具了。")
            print("运行示例:")
            print("  python full_auto_pipeline.py input/your_video.mp4 --target_lang zh")
            return 0
        else:
            print("\n" + "="*60)
            print("[X] 部分模型下载失败")
            print("="*60)
            print("\n请检查网络连接和日志输出，然后重新运行此脚本。")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️ 用户中断下载")
        return 1
    except Exception as e:
        logger.error(f"程序异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

