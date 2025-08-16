#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置编辑器
交互式编辑配置文件
"""

import os
from config_manager import ConfigManager

class ConfigEditor:
    """配置编辑器类"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
    
    def show_main_menu(self):
        """显示主菜单"""
        print("\n🔧 配置编辑器主菜单:")
        print("=" * 40)
        print("1. 查看当前配置")
        print("2. 编辑路径配置")
        print("3. 编辑替换设置")
        print("4. 编辑模板配置")
        print("5. 编辑高级设置")
        print("6. 验证配置")
        print("7. 保存配置")
        print("8. 重置为默认配置")
        print("0. 退出")
        print("-" * 40)
    
    def view_current_config(self):
        """查看当前配置"""
        print("\n📋 当前配置:")
        print("=" * 50)
        self.config_manager.print_config_summary()
    
    def edit_paths(self):
        """编辑路径配置"""
        print("\n📁 编辑路径配置:")
        print("-" * 30)
        
        paths = self.config_manager.get_paths()
        
        print("当前路径配置:")
        for key, value in paths.items():
            if key != "description":
                exists = "✅" if (value and os.path.exists(value)) else "❌"
                print(f"  {key}: {value} {exists}")
        
        print("\n选择要编辑的路径:")
        path_keys = [k for k in paths.keys() if k != "description"]
        for i, key in enumerate(path_keys, 1):
            print(f"{i}. {key}")
        print("0. 返回主菜单")
        
        try:
            choice = int(input("请选择 (0-{}): ".format(len(path_keys))))
            if choice == 0:
                return
            elif 1 <= choice <= len(path_keys):
                key = path_keys[choice - 1]
                current_value = paths.get(key, "")
                print(f"\n当前 {key}: {current_value}")
                
                new_value = input(f"输入新的 {key} 路径 (回车保持不变): ").strip()
                if new_value:
                    # 验证路径
                    if os.path.exists(new_value):
                        self.config_manager.set(f"paths.{key}", new_value)
                        print(f"✅ {key} 已更新为: {new_value}")
                    else:
                        confirm = input(f"⚠️  路径不存在，确定要设置吗？(y/n): ").lower()
                        if confirm == 'y':
                            self.config_manager.set(f"paths.{key}", new_value)
                            print(f"✅ {key} 已更新为: {new_value}")
                        else:
                            print("❌ 取消更新")
        except ValueError:
            print("❌ 请输入有效的数字")
    
    def edit_replacement_settings(self):
        """编辑替换设置"""
        print("\n⚙️  编辑替换设置:")
        print("-" * 30)
        
        replacement_settings = self.config_manager.get("replacement_settings", {})
        
        print("当前替换设置:")
        setting_keys = list(replacement_settings.keys())
        for i, key in enumerate(setting_keys, 1):
            config = replacement_settings[key]
            if isinstance(config, dict):
                description = config.get("description", key)
                current_value = config.get("value", "N/A")
                print(f"{i}. {description}: {current_value}")
        
        print("0. 返回主菜单")
        
        try:
            choice = int(input("选择要编辑的设置 (0-{}): ".format(len(setting_keys))))
            if choice == 0:
                return
            elif 1 <= choice <= len(setting_keys):
                key = setting_keys[choice - 1]
                self._edit_single_setting(key)
        except ValueError:
            print("❌ 请输入有效的数字")
    
    def _edit_single_setting(self, setting_key: str):
        """编辑单个设置"""
        config = self.config_manager.get(f"replacement_settings.{setting_key}", {})
        description = config.get("description", setting_key)
        current_value = config.get("value", "N/A")
        options = config.get("options", {})
        
        print(f"\n🔧 编辑设置: {description}")
        print(f"当前值: {current_value}")
        
        if options:
            print("可选项:")
            option_keys = list(options.keys())
            for i, (opt_key, opt_desc) in enumerate(options.items(), 1):
                marker = "👉" if str(current_value) == opt_key else "  "
                print(f"{marker} {i}. {opt_key}: {opt_desc}")
            
            print("0. 取消")
            
            try:
                choice = int(input(f"选择新值 (0-{len(option_keys)}): "))
                if choice == 0:
                    return
                elif 1 <= choice <= len(option_keys):
                    new_key = option_keys[choice - 1]
                    # 转换值类型
                    if new_key.lower() in ['true', 'false']:
                        new_value = new_key.lower() == 'true'
                    elif new_key.isdigit():
                        new_value = int(new_key)
                    else:
                        new_value = new_key
                    
                    self.config_manager.update_replacement_setting(setting_key, new_value)
                    print(f"✅ {description} 已更新为: {options[new_key]}")
            except ValueError:
                print("❌ 请输入有效的数字")
        else:
            new_value = input(f"输入新值 (当前: {current_value}): ").strip()
            if new_value:
                # 尝试转换类型
                if new_value.lower() in ['true', 'false']:
                    new_value = new_value.lower() == 'true'
                elif new_value.isdigit():
                    new_value = int(new_value)
                
                self.config_manager.update_replacement_setting(setting_key, new_value)
                print(f"✅ {description} 已更新为: {new_value}")
    
    def edit_template_config(self):
        """编辑模板配置"""
        print("\n🎬 编辑模板配置:")
        print("-" * 30)
        
        template = self.config_manager.get_template_config()
        current_name = template.get("name", "")
        
        print(f"当前模板名称: {current_name}")
        new_name = input("输入新的模板名称 (回车保持不变): ").strip()
        
        if new_name:
            self.config_manager.set("template.name", new_name)
            print(f"✅ 模板名称已更新为: {new_name}")
    
    def edit_advanced_settings(self):
        """编辑高级设置"""
        print("\n🔧 编辑高级设置:")
        print("-" * 30)
        
        advanced = self.config_manager.get_advanced_settings()
        
        settings_list = [
            ("segment_duration", "默认片段时长"),
            ("background_duration", "背景图片时长"),
            ("max_part_folders", "最大part文件夹数量")
        ]
        
        print("当前高级设置:")
        for i, (key, desc) in enumerate(settings_list, 1):
            value = advanced.get(key, {})
            if isinstance(value, dict):
                current_value = value.get("value", "N/A")
            else:
                current_value = value
            print(f"{i}. {desc}: {current_value}")
        
        print("0. 返回主菜单")
        
        try:
            choice = int(input(f"选择要编辑的设置 (0-{len(settings_list)}): "))
            if choice == 0:
                return
            elif 1 <= choice <= len(settings_list):
                key, desc = settings_list[choice - 1]
                current_value = advanced.get(key, {}).get("value", "N/A")
                
                print(f"\n当前 {desc}: {current_value}")
                new_value = input(f"输入新值: ").strip()
                
                if new_value:
                    # 转换数字类型
                    if new_value.isdigit():
                        new_value = int(new_value)
                    
                    self.config_manager.set(f"advanced_settings.{key}.value", new_value)
                    print(f"✅ {desc} 已更新为: {new_value}")
        except ValueError:
            print("❌ 请输入有效的数字")
    
    def validate_config(self):
        """验证配置"""
        print("\n🔍 配置验证:")
        print("-" * 30)
        
        # 验证路径
        validation_results = self.config_manager.validate_paths()
        print("路径验证结果:")
        all_valid = True
        for path_name, exists in validation_results.items():
            if path_name == "output_folder":
                continue  # 输出文件夹可以不存在
            status = "✅ 存在" if exists else "❌ 不存在"
            print(f"  {path_name}: {status}")
            if not exists:
                all_valid = False
        
        # 验证设置
        print("\n设置验证结果:")
        settings = self.config_manager.get_replacement_settings()
        media_type = settings.get("media_type", 2)
        if media_type in [1, 2, 3]:
            print(f"  媒体类型: ✅ 有效 ({media_type})")
        else:
            print(f"  媒体类型: ❌ 无效 ({media_type})")
            all_valid = False
        
        print(f"\n整体验证结果: {'✅ 通过' if all_valid else '❌ 需要修正'}")
    
    def save_config(self):
        """保存配置"""
        if self.config_manager.save_config():
            print("✅ 配置已保存")
        else:
            print("❌ 保存配置失败")
    
    def reset_config(self):
        """重置配置"""
        confirm = input("⚠️  确定要重置所有配置吗？这将无法撤销 (y/n): ").lower()
        if confirm == 'y':
            # 这里可以实现重置逻辑
            print("🔧 配置重置功能待实现")
        else:
            print("❌ 取消重置")
    
    def run(self):
        """运行配置编辑器"""
        print("🔧 配置编辑器")
        print("=" * 50)
        
        while True:
            self.show_main_menu()
            
            try:
                choice = int(input("请选择操作 (0-8): "))
                
                if choice == 0:
                    print("👋 退出配置编辑器")
                    break
                elif choice == 1:
                    self.view_current_config()
                elif choice == 2:
                    self.edit_paths()
                elif choice == 3:
                    self.edit_replacement_settings()
                elif choice == 4:
                    self.edit_template_config()
                elif choice == 5:
                    self.edit_advanced_settings()
                elif choice == 6:
                    self.validate_config()
                elif choice == 7:
                    self.save_config()
                elif choice == 8:
                    self.reset_config()
                else:
                    print("❌ 无效选择，请重试")
                    
            except ValueError:
                print("❌ 请输入有效的数字")
            except KeyboardInterrupt:
                print("\n\n👋 退出配置编辑器")
                break

def main():
    """主函数"""
    editor = ConfigEditor()
    editor.run()

if __name__ == "__main__":
    main()