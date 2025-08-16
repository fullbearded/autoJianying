#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式批量素材替换系统
支持用户选择媒体类型配置
"""

import os
from batch_replace_materials import MaterialBatchReplacer

def get_user_media_choice():
    """获取用户的媒体类型选择"""
    print("\n📋 媒体类型配置:")
    print("请选择要处理的媒体类型:")
    print("1. 图片 (.jpg, .jpeg, .png, .bmp)")
    print("2. 视频 (.mp4, .avi, .mov, .mkv) [默认]")
    print("3. 图片和视频 (混合模式)")
    
    while True:
        try:
            choice = input("请输入选择 (1-3，默认2): ").strip()
            if not choice:
                return 2  # 默认选择视频
            
            choice_num = int(choice)
            if choice_num in [1, 2, 3]:
                return choice_num
            else:
                print("❌ 请输入1、2或3")
        except ValueError:
            print("❌ 请输入有效的数字")

def show_folder_structure_guide(media_choice: int, materials_folder: str):
    """显示文件夹结构指南"""
    print(f"\n📁 请在以下路径创建素材文件夹结构:")
    print(f"  {materials_folder}/")
    print(f"  ├── background/     (放入 .jpg 背景图片文件)")
    
    if media_choice == 1:
        print(f"  ├── part1/          (放入图片文件: .jpg, .jpeg, .png, .bmp)")
        print(f"  ├── part2/          (放入图片文件: .jpg, .jpeg, .png, .bmp)")
        print(f"  ├── part3/          (放入图片文件: .jpg, .jpeg, .png, .bmp)")
        print(f"  ├── part4/          (可选，放入图片文件)")
    elif media_choice == 2:
        print(f"  ├── part1/          (放入视频文件: .mp4, .avi, .mov, .mkv)")
        print(f"  ├── part2/          (放入视频文件: .mp4, .avi, .mov, .mkv)")
        print(f"  ├── part3/          (放入视频文件: .mp4, .avi, .mov, .mkv)")
        print(f"  ├── part4/          (可选，放入视频文件)")
    else:
        print(f"  ├── part1/          (放入图片或视频文件)")
        print(f"  ├── part2/          (放入图片或视频文件)")
        print(f"  ├── part3/          (放入图片或视频文件)")
        print(f"  ├── part4/          (可选，放入图片或视频文件)")
    
    print(f"  └── ...             (支持更多part文件夹)")

def show_media_type_examples(media_choice: int):
    """显示媒体类型的使用示例"""
    media_type_names = {1: "图片", 2: "视频", 3: "图片和视频"}
    
    print(f"\n💡 {media_type_names[media_choice]}模式使用场景:")
    
    if media_choice == 1:
        print("   • 图片轮播视频制作")
        print("   • 产品展示相册")
        print("   • 静态内容演示")
        print("   • 海报设计合成")
    elif media_choice == 2:
        print("   • 视频片段拼接")
        print("   • 多素材混剪")
        print("   • 短视频批量制作")
        print("   • 视频模板替换")
    else:
        print("   • 图片+视频混合内容")
        print("   • 灵活的素材组合")
        print("   • 多媒体演示文稿")
        print("   • 复杂项目制作")

def confirm_proceed():
    """确认是否继续执行"""
    while True:
        choice = input("\n是否继续执行批量替换？(y/n): ").lower().strip()
        if choice in ['y', 'yes']:
            return True
        elif choice in ['n', 'no']:
            return False
        else:
            print("❌ 请输入 y 或 n")

def main():
    """主函数"""
    # 配置路径
    draft_folder_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
    template_name = "4翰墨书院模版"
    materials_folder = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/test/materials"
    
    print("🎬 交互式批量素材替换系统")
    print("=" * 60)
    print(f"模板草稿: {template_name}")
    
    try:
        # 创建替换器
        replacer = MaterialBatchReplacer(draft_folder_path, template_name)
        
        # 获取用户选择的媒体类型
        media_choice = get_user_media_choice()
        replacer.set_media_type(media_choice)
        
        # 显示文件夹结构指南
        show_folder_structure_guide(media_choice, materials_folder)
        
        # 显示使用场景示例
        show_media_type_examples(media_choice)
        
        # 检查素材文件夹是否存在
        if not os.path.exists(materials_folder):
            print(f"\n❌ 素材文件夹不存在: {materials_folder}")
            print("请先运行以下命令创建文件夹结构:")
            print("  python setup_materials_folder.py")
            return
        
        # 确认是否继续
        if not confirm_proceed():
            print("👋 操作已取消")
            return
        
        # 执行批量替换
        replacer.batch_replace(materials_folder)
        
    except KeyboardInterrupt:
        print("\n\n👋 操作被用户中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")

if __name__ == "__main__":
    main()