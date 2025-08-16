#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器
管理系统的所有配置选项
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        if config_path is None:
            # 默认配置文件路径
            current_dir = Path(__file__).parent
            config_path = current_dir / "config" / "settings.json"
        
        self.config_path = Path(config_path)
        self.config = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                print(f"✅ 配置文件加载成功: {self.config_path}")
            else:
                print(f"⚠️  配置文件不存在: {self.config_path}")
                self._create_default_config()
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """创建默认配置"""
        print("🔧 创建默认配置...")
        # 确保config目录存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 这里可以创建默认配置，但目前我们已经有了settings.json
        # 如果需要可以添加默认配置生成逻辑
        self.config = {}
    
    def save_config(self):
        """保存配置到文件"""
        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 更新最后修改时间
            if "metadata" in self.config:
                from datetime import datetime
                self.config["metadata"]["last_modified"] = datetime.now().strftime("%Y-%m-%d")
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            print(f"✅ 配置已保存: {self.config_path}")
            return True
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key_path: 配置键路径，如 "paths.draft_folder" 或 "replacement_settings.media_type.value"
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """设置配置值
        
        Args:
            key_path: 配置键路径
            value: 要设置的值
        """
        keys = key_path.split('.')
        current = self.config
        
        # 导航到最后一个键的父级
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # 设置值
        current[keys[-1]] = value
    
    def get_paths(self) -> Dict[str, str]:
        """获取路径配置"""
        return self.get("paths", {})
    
    def get_template_config(self) -> Dict[str, Any]:
        """获取模板配置"""
        return self.get("template", {})
    
    def get_replacement_settings(self) -> Dict[str, Any]:
        """获取替换设置"""
        settings = {}
        replacement_config = self.get("replacement_settings", {})
        
        for key, config in replacement_config.items():
            if isinstance(config, dict) and "value" in config:
                settings[key] = config["value"]
            else:
                settings[key] = config
        
        return settings
    
    def get_advanced_settings(self) -> Dict[str, Any]:
        """获取高级设置"""
        return self.get("advanced_settings", {})
    
    def get_ui_settings(self) -> Dict[str, Any]:
        """获取UI设置"""
        settings = {}
        ui_config = self.get("ui_settings", {})
        
        for key, config in ui_config.items():
            if isinstance(config, dict) and "value" in config:
                settings[key] = config["value"]
            else:
                settings[key] = config
        
        return settings
    
    def update_paths(self, paths: Dict[str, str]):
        """更新路径配置"""
        current_paths = self.get_paths()
        current_paths.update(paths)
        self.set("paths", current_paths)
    
    def update_replacement_setting(self, key: str, value: Any):
        """更新替换设置"""
        self.set(f"replacement_settings.{key}.value", value)
    
    def get_setting_options(self, setting_key: str) -> Dict[str, str]:
        """获取设置的可选项"""
        return self.get(f"replacement_settings.{setting_key}.options", {})
    
    def get_setting_description(self, setting_key: str) -> str:
        """获取设置的描述"""
        return self.get(f"replacement_settings.{setting_key}.description", "")
    
    def validate_paths(self) -> Dict[str, bool]:
        """验证路径是否存在"""
        paths = self.get_paths()
        validation_results = {}
        
        for key, path in paths.items():
            if key == "description":
                continue
            if path:
                validation_results[key] = os.path.exists(path)
            else:
                validation_results[key] = False
        
        return validation_results
    
    def print_config_summary(self):
        """打印配置摘要"""
        print("📋 当前配置摘要:")
        print("=" * 50)
        
        # 路径配置
        paths = self.get_paths()
        print("\n📁 路径配置:")
        for key, value in paths.items():
            if key != "description":
                exists = "✅" if (value and os.path.exists(value)) else "❌"
                print(f"  {key}: {value} {exists}")
        
        # 模板配置
        template = self.get_template_config()
        print(f"\n🎬 模板配置:")
        print(f"  名称: {template.get('name', 'N/A')}")
        
        # 替换设置
        settings = self.get_replacement_settings()
        print(f"\n⚙️  替换设置:")
        for key, value in settings.items():
            print(f"  {key}: {value}")
        
        # 版本信息
        metadata = self.get("metadata", {})
        print(f"\n📊 版本信息:")
        print(f"  版本: {metadata.get('version', 'N/A')}")
        print(f"  最后修改: {metadata.get('last_modified', 'N/A')}")

def main():
    """主函数 - 配置管理器演示"""
    print("🔧 配置管理器演示")
    print("=" * 50)
    
    # 创建配置管理器
    config_manager = ConfigManager()
    
    # 显示配置摘要
    config_manager.print_config_summary()
    
    # 演示获取配置
    print(f"\n🔍 配置获取演示:")
    print(f"草稿文件夹: {config_manager.get('paths.draft_folder')}")
    print(f"媒体类型: {config_manager.get('replacement_settings.media_type.value')}")
    print(f"默认片段时长: {config_manager.get('advanced_settings.segment_duration.value')}")
    
    # 演示设置配置
    print(f"\n✏️  配置修改演示:")
    config_manager.update_replacement_setting("media_type", 1)
    print(f"媒体类型已修改为: {config_manager.get('replacement_settings.media_type.value')}")
    
    # 验证路径
    print(f"\n🔍 路径验证:")
    validation_results = config_manager.validate_paths()
    for path_name, exists in validation_results.items():
        status = "✅ 存在" if exists else "❌ 不存在"
        print(f"  {path_name}: {status}")

if __name__ == "__main__":
    main()