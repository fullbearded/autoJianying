#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于配置文件的批量素材替换系统
使用JSON配置文件管理所有设置
"""

import os
from pathlib import Path
from config_manager import ConfigManager
from batch_replace_materials import MaterialBatchReplacer

class ConfigBasedReplacer(MaterialBatchReplacer):
    """基于配置文件的批量替换器"""
    
    def __init__(self, config_path: str = None):
        """初始化配置驱动的替换器
        
        Args:
            config_path: 配置文件路径，如果为None使用默认配置
        """
        self.config_manager = ConfigManager(config_path)
        
        # 从配置获取基本设置
        paths = self.config_manager.get_paths()
        template_config = self.config_manager.get_template_config()
        
        draft_folder_path = paths.get("draft_folder", "")
        template_name = template_config.get("name", "")
        
        if not draft_folder_path:
            raise ValueError("配置文件中未设置草稿文件夹路径")
        
        if not template_name:
            raise ValueError("配置文件中未设置模板名称")
        
        # 调用父类初始化
        super().__init__(draft_folder_path, template_name)
        
        # 应用配置文件中的设置
        self._apply_config_settings()
    
    def _apply_config_settings(self):
        """应用配置文件中的设置"""
        replacement_settings = self.config_manager.get_replacement_settings()
        
        # 更新设置
        for key, value in replacement_settings.items():
            if key in self.settings:
                self.settings[key] = value
        
        # 应用高级设置
        advanced_settings = self.config_manager.get_advanced_settings()
        self.segment_duration = advanced_settings.get("segment_duration", {}).get("value", "10s")
        self.background_duration = advanced_settings.get("background_duration", {}).get("value", "30s")
    
    def get_materials_folder(self) -> str:
        """从配置获取素材文件夹路径"""
        paths = self.config_manager.get_paths()
        materials_folder = paths.get("materials_folder", "")
        
        if not materials_folder:
            raise ValueError("配置文件中未设置素材文件夹路径")
        
        return materials_folder
    
    def print_config_driven_settings(self):
        """打印基于配置的设置"""
        media_type_names = {1: "图片", 2: "视频", 3: "图片和视频"}
        
        print("\n📋 基于配置文件的当前设置:")
        print("-" * 50)
        
        # 显示路径信息
        paths = self.config_manager.get_paths()
        print("📁 路径配置:")
        print(f"  草稿文件夹: {paths.get('draft_folder')}")
        print(f"  素材文件夹: {paths.get('materials_folder')}")
        
        # 显示模板信息
        template = self.config_manager.get_template_config()
        print(f"\n🎬 模板配置:")
        print(f"  模板名称: {template.get('name')}")
        
        # 显示替换设置
        settings = self.config_manager.get_replacement_settings()
        print(f"\n⚙️  替换设置:")
        
        # 获取设置描述和选项
        for key, value in settings.items():
            description = self.config_manager.get_setting_description(key)
            options = self.config_manager.get_setting_options(key)
            
            if key == "media_type":
                display_value = media_type_names.get(value, str(value))
            else:
                if str(value) in options:
                    display_value = options[str(value)]
                else:
                    display_value = str(value)
            
            print(f"  {description}: {display_value}")
        
        # 显示高级设置
        advanced = self.config_manager.get_advanced_settings()
        print(f"\n🔧 高级设置:")
        print(f"  默认片段时长: {advanced.get('segment_duration', {}).get('value', 'N/A')}")
        print(f"  背景图片时长: {advanced.get('background_duration', {}).get('value', 'N/A')}")
        
        # 显示支持的格式
        if settings.get("media_type") == 1:
            formats = advanced.get("supported_image_formats", {}).get("value", [])
            print(f"  支持格式: {', '.join(formats)}")
        elif settings.get("media_type") == 2:
            formats = advanced.get("supported_video_formats", {}).get("value", [])
            print(f"  支持格式: {', '.join(formats)}")
        else:
            img_formats = advanced.get("supported_image_formats", {}).get("value", [])
            vid_formats = advanced.get("supported_video_formats", {}).get("value", [])
            print(f"  支持格式: {', '.join(img_formats + vid_formats)}")
        
        print()
    
    def update_config_setting(self, setting_key: str, value: any):
        """更新配置设置并保存"""
        self.config_manager.update_replacement_setting(setting_key, value)
        self.config_manager.save_config()
        
        # 重新应用设置
        self._apply_config_settings()
        print(f"✅ 设置 {setting_key} 已更新为: {value}")
    
    def batch_replace_with_config(self) -> bool:
        """基于配置执行批量替换"""
        print("🚀 基于配置文件的批量素材替换")
        print("=" * 60)
        
        # 验证配置
        validation_results = self.config_manager.validate_paths()
        failed_paths = [path for path, exists in validation_results.items() if not exists and path != "output_folder"]
        
        if failed_paths:
            print("❌ 以下路径不存在:")
            for path in failed_paths:
                print(f"  - {path}")
            return False
        
        # 获取素材文件夹
        try:
            materials_folder = self.get_materials_folder()
        except ValueError as e:
            print(f"❌ {e}")
            return False
        
        # 显示配置驱动的设置
        self.print_config_driven_settings()
        
        # 执行批量替换
        return self.batch_replace(materials_folder)

def create_config_template():
    """创建配置模板文件"""
    config_dir = Path(__file__).parent / "config"
    template_path = config_dir / "settings_template.json"
    
    if template_path.exists():
        print(f"⚠️  配置模板已存在: {template_path}")
        return str(template_path)
    
    # 复制当前配置作为模板
    settings_path = config_dir / "settings.json"
    if settings_path.exists():
        import shutil
        shutil.copy2(settings_path, template_path)
        print(f"✅ 配置模板已创建: {template_path}")
        return str(template_path)
    else:
        print(f"❌ 原配置文件不存在，无法创建模板")
        return None

def show_config_options():
    """显示配置选项说明"""
    print("📋 配置选项说明:")
    print("=" * 50)
    
    config_manager = ConfigManager()
    
    print("\n⚙️  替换设置选项:")
    replacement_settings = config_manager.get("replacement_settings", {})
    
    for key, config in replacement_settings.items():
        if isinstance(config, dict):
            description = config.get("description", key)
            options = config.get("options", {})
            current_value = config.get("value", "N/A")
            
            print(f"\n🔧 {description} ({key}):")
            print(f"  当前值: {current_value}")
            if options:
                print(f"  可选项:")
                for opt_value, opt_desc in options.items():
                    marker = "👉" if str(current_value) == opt_value else "  "
                    print(f"    {marker} {opt_value}: {opt_desc}")

def main():
    """主函数"""
    print("🎬 基于配置文件的批量素材替换系统")
    print("=" * 60)
    
    try:
        # 创建配置驱动的替换器
        replacer = ConfigBasedReplacer()
        
        # 显示配置选项
        show_config_options()
        
        # 执行批量替换
        print(f"\n{'='*60}")
        success = replacer.batch_replace_with_config()
        
        if success:
            print("\n🎉 批量替换完成!")
        else:
            print("\n❌ 批量替换失败")
            
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        print("\n💡 提示:")
        print("1. 检查配置文件 config/settings.json 是否存在")
        print("2. 确保配置文件中的路径设置正确")
        print("3. 运行 python config_manager.py 查看配置状态")

if __name__ == "__main__":
    main()