#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量素材替换演示脚本
创建示例文件并测试批量替换功能
"""

import os
import shutil
from pathlib import Path
from setup_materials_folder import create_folder_structure, check_existing_files

def create_demo_files(materials_path: str):
    """创建演示用的素材文件"""
    print("🎬 创建演示素材文件...")
    print("-" * 40)
    
    # 创建背景图片文件（空文件作为演示）
    bg_folder = os.path.join(materials_path, "background")
    for i in range(3):
        demo_file = os.path.join(bg_folder, f"demo_bg_{i+1}.jpg")
        with open(demo_file, 'w') as f:
            f.write(f"# Demo background image {i+1}\n# This is a placeholder file for demonstration")
        print(f"✅ 创建: background/demo_bg_{i+1}.jpg")
    
    # 创建视频文件（空文件作为演示）
    for part in ["part1", "part2", "part3"]:
        part_folder = os.path.join(materials_path, part)
        for i in range(2):  # 每个part文件夹创建2个文件
            demo_file = os.path.join(part_folder, f"demo_{part}_video_{i+1}.mp4")
            with open(demo_file, 'w') as f:
                f.write(f"# Demo {part} video {i+1}\n# This is a placeholder file for demonstration")
            print(f"✅ 创建: {part}/demo_{part}_video_{i+1}.mp4")
    
    print(f"\n🎯 演示文件创建完成!")

def cleanup_demo_files(materials_path: str):
    """清理演示文件"""
    if os.path.exists(materials_path):
        shutil.rmtree(materials_path)
        print(f"🧹 已清理演示文件夹: {materials_path}")

def main():
    """主函数"""
    materials_path = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/test/materials"
    
    print("🎭 批量素材替换演示")
    print("=" * 60)
    
    # 询问用户是否要创建演示文件
    choice = input("是否创建演示文件进行测试？(y/n): ").lower().strip()
    
    if choice == 'y':
        try:
            # 1. 创建文件夹结构
            print("\n📁 步骤1: 创建文件夹结构")
            create_folder_structure(materials_path)
            
            # 2. 创建演示文件
            print("\n📄 步骤2: 创建演示文件")
            create_demo_files(materials_path)
            
            # 3. 检查文件
            print("\n📋 步骤3: 检查文件状态")
            check_existing_files(materials_path)
            
            print(f"\n✨ 演示准备完成!")
            print(f"现在可以运行以下命令测试批量替换:")
            print(f"  python batch_replace_materials.py")
            print(f"")
            print(f"⚠️  注意: 这些是演示用的空文件，实际使用时请替换为真实的图片和视频文件")
            
            # 询问是否清理
            cleanup_choice = input(f"\n是否要清理演示文件？(y/n): ").lower().strip()
            if cleanup_choice == 'y':
                cleanup_demo_files(materials_path)
            
        except Exception as e:
            print(f"❌ 创建演示文件时出错: {e}")
    
    else:
        print("📖 使用说明:")
        print("1. 运行 python setup_materials_folder.py 创建文件夹结构")
        print("2. 将真实的素材文件放入对应文件夹:")
        print("   - background/ : .jpg 背景图片文件")
        print("   - part1/ : .mp4 视频文件")
        print("   - part2/ : .mp4 视频文件") 
        print("   - part3/ : .mp4 视频文件")
        print("3. 运行 python batch_replace_materials.py 执行批量替换")

if __name__ == "__main__":
    main()