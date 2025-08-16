#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试无限制part文件夹功能
"""

import os
import shutil
from pathlib import Path

def create_test_structure_with_more_parts(base_path: str):
    """创建包含更多part文件夹的测试结构"""
    print("🧪 创建扩展测试结构...")
    print("-" * 40)
    
    # 清理现有结构
    if os.path.exists(base_path):
        shutil.rmtree(base_path)
    
    # 创建主文件夹
    os.makedirs(base_path, exist_ok=True)
    
    # 创建background文件夹
    bg_folder = os.path.join(base_path, "background")
    os.makedirs(bg_folder, exist_ok=True)
    for i in range(2):
        demo_file = os.path.join(bg_folder, f"test_bg_{i+1}.jpg")
        with open(demo_file, 'w') as f:
            f.write(f"# Test background {i+1}")
        print(f"✅ 创建: background/test_bg_{i+1}.jpg")
    
    # 创建5个part文件夹（超过原来的3个限制）
    for part_num in range(1, 6):  # part1 到 part5
        part_folder = os.path.join(base_path, f"part{part_num}")
        os.makedirs(part_folder, exist_ok=True)
        
        # 每个文件夹创建不同数量的文件来测试最小数量逻辑
        file_count = 3 if part_num <= 3 else 2  # part1-3有3个文件，part4-5有2个文件
        
        for i in range(file_count):
            demo_file = os.path.join(part_folder, f"test_part{part_num}_video_{i+1}.mp4")
            with open(demo_file, 'w') as f:
                f.write(f"# Test part{part_num} video {i+1}")
            print(f"✅ 创建: part{part_num}/test_part{part_num}_video_{i+1}.mp4")
    
    print(f"\n🎯 扩展测试结构创建完成!")
    print(f"📊 文件数量统计:")
    print(f"   background: 2 个文件")
    print(f"   part1: 3 个文件")
    print(f"   part2: 3 个文件") 
    print(f"   part3: 3 个文件")
    print(f"   part4: 2 个文件")
    print(f"   part5: 2 个文件")
    print(f"   预计生成草稿: 2 个 (最少文件数量)")

def test_validation():
    """测试验证功能"""
    print("\n🔍 测试文件夹验证功能...")
    print("-" * 40)
    
    from batch_replace_materials import MaterialBatchReplacer
    
    draft_folder_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
    materials_folder = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/test/test_materials"
    
    try:
        replacer = MaterialBatchReplacer(draft_folder_path)
        
        # 测试验证
        is_valid, message = replacer.validate_folder_structure(materials_folder)
        print(f"验证结果: {'✅ 通过' if is_valid else '❌ 失败'}")
        print(f"消息: {message}")
        
        if is_valid:
            # 测试获取材料文件
            materials = replacer.get_material_files(materials_folder)
            print(f"\n📋 发现的材料文件:")
            for folder, files in materials.items():
                print(f"  {folder}: {len(files)} 个文件")
                for file in files[:2]:  # 只显示前2个
                    print(f"    📄 {file}")
                if len(files) > 2:
                    print(f"    ... 还有 {len(files) - 2} 个文件")
            
            # 测试生成组合
            combinations = replacer.create_replacement_combinations(materials)
            print(f"\n🔄 生成的组合数量: {len(combinations)}")
            
            # 显示第一个组合作为示例
            if combinations:
                print(f"示例组合 1:")
                for folder, file in combinations[0].items():
                    print(f"  {folder}: {file}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def main():
    """主函数"""
    test_materials_folder = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/test/test_materials"
    
    print("🚀 测试无限制part文件夹功能")
    print("=" * 60)
    
    # 创建测试结构
    create_test_structure_with_more_parts(test_materials_folder)
    
    # 测试验证功能
    test_validation()
    
    # 询问是否清理
    choice = input(f"\n是否要清理测试文件？(y/n): ").lower().strip()
    if choice == 'y':
        if os.path.exists(test_materials_folder):
            shutil.rmtree(test_materials_folder)
            print(f"🧹 已清理测试文件夹: {test_materials_folder}")
    else:
        print(f"📁 测试文件保留在: {test_materials_folder}")
        print(f"   可以用于测试批量替换功能")

if __name__ == "__main__":
    main()