#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户配置管理模块 - 支持多用户配置隔离
每个用户有独立的配置文件，配置失效时使用环境变量默认值
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """用户配置管理器 - 支持用户隔离"""

    # 默认配置结构（从环境变量读取）
    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """从环境变量获取默认配置"""
        return {
            # API 配置
            "api": {
                "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
                "gemini_base_url": os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"),
                "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
                "openai_base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            },

            # 翻译设置
            "translation": {
                "api_type": os.getenv("DEFAULT_TRANSLATION_API", "gemini"),
                "model": os.getenv("DEFAULT_TRANSLATION_MODEL", "gemini-2.5-flash"),
                "source_lang": "auto",
                "target_lang": os.getenv("DEFAULT_TARGET_LANG", "zh"),
            },

            # TTS设置
            "tts": {
                "engine": os.getenv("DEFAULT_TTS_ENGINE", "indextts"),
            },

            # 输出设置
            "output": {
                "save_srt": True,
            },

            # 其他设置
            "advanced": {
                "enable_diarization": True,
                "enable_separation": True,
            }
        }

    def __init__(self, user_id: Optional[str] = None, config_path: Optional[Path] = None):
        """
        初始化配置管理器

        Args:
            user_id: 用户ID，用于配置隔离
            config_path: 自定义配置文件路径（优先级高于user_id）
        """
        if config_path is not None:
            # 使用指定的配置文件路径
            self.config_path = Path(config_path)
            self.user_id = None
        elif user_id is not None:
            # 用户级配置文件：config/{user_id}/config.json
            project_root = Path(__file__).resolve().parent.parent
            config_dir = project_root / 'config' / user_id
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_path = config_dir / 'config.json'
            self.user_id = user_id
        else:
            # 默认全局配置文件（向后兼容）
            project_root = Path(__file__).resolve().parent.parent
            self.config_path = project_root / 'transvox_config.json'
            self.user_id = None

        self.config = self._load_config()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件，如果不存在或失效则使用默认配置"""
        default_config = self.get_default_config()

        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)

                # 合并用户配置和默认配置
                config = self._merge_config(default_config.copy(), user_config)
                logger.info(f"已加载用户配置: {self.config_path}")
                return config
            except Exception as e:
                logger.warning(f"加载配置文件失败，使用环境变量默认配置: {e}")
                return default_config
        else:
            logger.info(f"配置文件不存在，使用环境变量默认配置: {self.config_path}")
            return default_config

    def _validate_config(self) -> bool:
        """
        验证配置有效性
        检查必需的API密钥是否配置
        """
        issues = []

        # 检查翻译API配置
        api_type = self.config.get('translation', {}).get('api_type', '')
        if api_type == 'gemini':
            api_key = self.config.get('api', {}).get('gemini_api_key', '')
            if not api_key:
                env_key = os.getenv('GEMINI_API_KEY', '')
                if env_key:
                    logger.info("使用环境变量中的 GEMINI_API_KEY")
                    self.config['api']['gemini_api_key'] = env_key
                else:
                    issues.append("未配置 Gemini API Key")
        elif api_type == 'openai':
            api_key = self.config.get('api', {}).get('openai_api_key', '')
            if not api_key:
                env_key = os.getenv('OPENAI_API_KEY', '')
                if env_key:
                    logger.info("使用环境变量中的 OPENAI_API_KEY")
                    self.config['api']['openai_api_key'] = env_key
                else:
                    issues.append("未配置 OpenAI API Key")

        if issues:
            logger.warning(f"配置验证发现问题: {', '.join(issues)}")
            logger.warning("部分功能可能无法正常使用，请在设置中配置API密钥")
            return False

        return True

    def _merge_config(self, base: Dict, updates: Dict) -> Dict:
        """递归合并配置字典"""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._merge_config(base[key], value)
            else:
                base[key] = value
        return base

    def save_config(self) -> bool:
        """保存配置到文件"""
        try:
            # 确保父目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            logger.info(f"配置已保存: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key_path: 配置键路径，用点号分隔，如 "translation.api_type"
            default: 默认值

        Returns:
            配置值
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any) -> None:
        """
        设置配置值

        Args:
            key_path: 配置键路径，用点号分隔，如 "translation.api_type"
            value: 配置值
        """
        keys = key_path.split('.')
        config = self.config

        # 导航到最后一个键的父字典
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        # 设置值
        config[keys[-1]] = value

    def update(self, updates: Dict[str, Any]) -> None:
        """
        批量更新配置

        Args:
            updates: 配置更新字典
        """
        self.config = self._merge_config(self.config, updates)

    def reset_to_default(self) -> None:
        """重置为环境变量默认配置"""
        self.config = self.get_default_config()
        logger.info("配置已重置为环境变量默认值")

    def get_all(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self.config.copy()

    def has_valid_api_config(self) -> bool:
        """检查是否有有效的API配置"""
        api_type = self.config.get('translation', {}).get('api_type', '')

        if api_type == 'gemini':
            return bool(self.config.get('api', {}).get('gemini_api_key', ''))
        elif api_type == 'openai':
            return bool(self.config.get('api', {}).get('openai_api_key', ''))

        return False

    # 便捷方法

    def get_translation_config(self) -> Dict[str, Any]:
        """获取翻译配置"""
        return self.config.get('translation', {})

    def get_tts_config(self) -> Dict[str, Any]:
        """获取TTS配置"""
        return self.config.get('tts', {})

    def get_output_config(self) -> Dict[str, Any]:
        """获取输出配置"""
        return self.config.get('output', {})

    def get_advanced_config(self) -> Dict[str, Any]:
        """获取高级配置"""
        return self.config.get('advanced', {})


# 用户配置管理器缓存（支持多用户）
_user_config_managers: Dict[str, ConfigManager] = {}


def get_config_manager(user_id: Optional[str] = None) -> ConfigManager:
    """
    获取配置管理器实例（支持用户隔离）

    Args:
        user_id: 用户ID，None表示全局配置

    Returns:
        ConfigManager实例
    """
    cache_key = user_id or '__global__'

    if cache_key not in _user_config_managers:
        _user_config_managers[cache_key] = ConfigManager(user_id=user_id)

    return _user_config_managers[cache_key]


def reset_config_manager(user_id: Optional[str] = None) -> None:
    """
    重置配置管理器（用于测试或强制重新加载）

    Args:
        user_id: 用户ID，None表示重置全局配置
    """
    cache_key = user_id or '__global__'

    if cache_key in _user_config_managers:
        del _user_config_managers[cache_key]


def clear_all_config_managers() -> None:
    """清除所有用户的配置管理器缓存"""
    _user_config_managers.clear()


if __name__ == '__main__':
    # 测试配置管理器
    logging.basicConfig(level=logging.INFO)

    # 测试用户隔离
    user1_config = ConfigManager(user_id='user1')
    user2_config = ConfigManager(user_id='user2')

    print("User1 默认配置:")
    print(json.dumps(user1_config.get_all(), indent=2, ensure_ascii=False))

    # 修改User1配置
    user1_config.set('translation.api_type', 'openai')
    user1_config.set('translation.target_lang', 'en')
    user1_config.save_config()

    # 修改User2配置
    user2_config.set('translation.api_type', 'gemini')
    user2_config.set('translation.target_lang', 'ja')
    user2_config.save_config()

    # 验证配置隔离
    print("\nUser1 配置:")
    print(f"API Type: {user1_config.get('translation.api_type')}")
    print(f"Target Lang: {user1_config.get('translation.target_lang')}")

    print("\nUser2 配置:")
    print(f"API Type: {user2_config.get('translation.api_type')}")
    print(f"Target Lang: {user2_config.get('translation.target_lang')}")
