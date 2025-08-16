#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建素材文件夹结构
用于批量素材替换系统
"""

import os

def create_folder_structure(base_path: str):
    """创建素材文件夹结构"""
    
    print("📁 创建素材文件夹结构...")
    print("=" * 50)
    
    # 创建主文件夹
    os.makedirs(base_path, exist_ok=True)
    print(f"✅ 主文件夹: {base_path}")
    
    # 创建子文件夹
    subfolders = ["background", "part1", "part2", "part3"]
    
    for folder in subfolders:
        folder_path = os.path.join(base_path, folder)
        os.makedirs(folder_path, exist_ok=True)
        print(f"✅ 子文件夹: {folder}/")
        
        # 创建说明文件
        if folder == "background":
            readme_content = """# Background 文件夹

请将背景图片文件（.jpg格式）放入此文件夹。

示例文件名：
- bg1.jpg
- bg2.jpg
- bg3.jpg

注意：文件将按字母顺序使用。
"""
        else:
            readme_content = f"""# {folder.upper()} 文件夹

请将{folder}视频文件（.mp4格式）放入此文件夹。

示例文件名：
- video1.mp4
- video2.mp4
- video3.mp4

注意：文件将按字母顺序使用。
"""
        
        readme_path = os.path.join(folder_path, "README.md")
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
    
    print(f"\n🎯 文件夹结构创建完成!")
    print(f"请按以下说明放入素材文件:")
    print(f"")
    print(f"📂 {base_path}/")
    print(f"  ├── 📁 background/     👈 放入 .jpg 背景图片文件")
    print(f"  ├── 📁 part1/          👈 放入 .mp4 视频文件")
    print(f"  ├── 📁 part2/          👈 放入 .mp4 视频文件")
    print(f"  └── 📁 part3/          👈 放入 .mp4 视频文件")
    print(f"")
    print(f"⚠️  重要提醒:")
    print(f"   • 支持任意数量的part文件夹（part1, part2, part3, part4...）")
    print(f"   • 文件将按字母顺序使用")
    print(f"   • 确保每个文件夹中至少有一个对应格式的文件")
    print(f"   • 生成的草稿数量 = 最少文件数量的文件夹中的文件数")

def check_existing_files(base_path: str):
    """检查现有文件"""
    if not os.path.exists(base_path):
        print(f"❌ 文件夹不存在: {base_path}")
        return
    
    print("\n📋 检查现有文件:")
    print("-" * 30)
    
    subfolders = ["background", "part1", "part2", "part3"]
    min_files = float('inf')
    
    for folder in subfolders:
        folder_path = os.path.join(base_path, folder)
        if os.path.exists(folder_path):
            if folder == "background":
                files = [f for f in os.listdir(folder_path) if f.lower().endswith('.jpg')]
            else:
                files = [f for f in os.listdir(folder_path) if f.lower().endswith('.mp4')]
            
            print(f"  {folder}: {len(files)} 个文件")
            if files:
                for file in sorted(files)[:3]:  # 只显示前3个
                    print(f"    📄 {file}")
                if len(files) > 3:
                    print(f"    ... 还有 {len(files) - 3} 个文件")
            
            if len(files) > 0:
                min_files = min(min_files, len(files))
        else:
            print(f"  {folder}: ❌ 文件夹不存在")
    
    if min_files != float('inf'):
        print(f"\n🎬 预计可生成 {min_files} 个草稿")
    else:
        print(f"\n⚠️  请先添加素材文件")

def main():
    """主函数"""
    base_path = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/test/materials"
    
    print("🛠️  素材文件夹设置工具")
    print("=" * 60)
    
    # 创建文件夹结构
    create_folder_structure(base_path)
    
    # 检查现有文件
    check_existing_files(base_path)
    
    print(f"\n✨ 设置完成!")
    print(f"   添加素材文件后，运行以下命令开始批量替换:")
    print(f"   python batch_replace_materials.py")

if __name__ == "__main__":
    main()