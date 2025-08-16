#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试不同媒体类型的功能
"""

import os
import shutil
from pathlib import Path
from batch_replace_materials import MaterialBatchReplacer

def create_test_materials(base_path: str, media_type: int):
    """创建测试素材文件"""
    print(f"🧪 创建媒体类型 {media_type} 的测试素材...")
    
    # 清理现有结构
    if os.path.exists(base_path):
        shutil.rmtree(base_path)
    
    # 创建主文件夹
    os.makedirs(base_path, exist_ok=True)
    
    # 创建background文件夹（始终是图片）
    bg_folder = os.path.join(base_path, "background")
    os.makedirs(bg_folder, exist_ok=True)
    for i in range(2):
        demo_file = os.path.join(bg_folder, f"test_bg_{i+1}.jpg")
        with open(demo_file, 'w') as f:
            f.write(f"# Test background image {i+1}")
        print(f"✅ 创建: background/test_bg_{i+1}.jpg")
    
    # 根据媒体类型创建part文件夹
    for part_num in range(1, 4):  # part1, part2, part3
        part_folder = os.path.join(base_path, f"part{part_num}")
        os.makedirs(part_folder, exist_ok=True)
        
        if media_type == 1:  # 仅图片
            extensions = ['.jpg', '.png']
            for i, ext in enumerate(extensions):
                demo_file = os.path.join(part_folder, f"test_part{part_num}_image_{i+1}{ext}")
                with open(demo_file, 'w') as f:
                    f.write(f"# Test part{part_num} image {i+1}")
                print(f"✅ 创建: part{part_num}/test_part{part_num}_image_{i+1}{ext}")
                
        elif media_type == 2:  # 仅视频
            extensions = ['.mp4', '.avi']
            for i, ext in enumerate(extensions):
                demo_file = os.path.join(part_folder, f"test_part{part_num}_video_{i+1}{ext}")
                with open(demo_file, 'w') as f:
                    f.write(f"# Test part{part_num} video {i+1}")
                print(f"✅ 创建: part{part_num}/test_part{part_num}_video_{i+1}{ext}")
                
        else:  # 图片和视频混合
            # 混合创建图片和视频文件
            files_to_create = [
                (f"test_part{part_num}_image_1.jpg", f"# Test part{part_num} image"),
                (f"test_part{part_num}_video_1.mp4", f"# Test part{part_num} video")
            ]
            for filename, content in files_to_create:
                demo_file = os.path.join(part_folder, filename)
                with open(demo_file, 'w') as f:
                    f.write(content)
                print(f"✅ 创建: part{part_num}/{filename}")

def test_media_type_validation(media_type: int):
    """测试特定媒体类型的验证"""
    print(f"\n🔍 测试媒体类型 {media_type} 的验证功能...")
    print("-" * 50)
    
    draft_folder_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
    test_materials_folder = f"/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/test/test_materials_type_{media_type}"
    
    try:
        # 创建测试素材
        create_test_materials(test_materials_folder, media_type)
        
        # 创建替换器并设置媒体类型
        replacer = MaterialBatchReplacer(draft_folder_path)
        replacer.set_media_type(media_type)
        
        # 测试验证
        is_valid, message = replacer.validate_folder_structure(test_materials_folder)
        print(f"验证结果: {'✅ 通过' if is_valid else '❌ 失败'}")
        print(f"消息: {message}")
        
        if is_valid:
            # 测试获取材料文件
            materials = replacer.get_material_files(test_materials_folder)
            print(f"\n📋 发现的材料文件:")
            for folder, files in materials.items():
                print(f"  {folder}: {len(files)} 个文件")
                for file in files:
                    ext = Path(file).suffix.lower()
                    file_type = "图片" if ext in ['.jpg', '.jpeg', '.png', '.bmp'] else "视频"
                    print(f"    📄 {file} ({file_type})")
            
            # 测试生成组合
            combinations = replacer.create_replacement_combinations(materials)
            print(f"\n🔄 生成的组合数量: {len(combinations)}")
            
            if combinations:
                print(f"示例组合 1:")
                for folder, file in combinations[0].items():
                    ext = Path(file).suffix.lower()
                    file_type = "图片" if ext in ['.jpg', '.jpeg', '.png', '.bmp'] else "视频"
                    print(f"  {folder}: {file} ({file_type})")
        
        # 清理测试文件
        if os.path.exists(test_materials_folder):
            shutil.rmtree(test_materials_folder)
            print(f"\n🧹 已清理测试文件夹")
        
        return is_valid
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        # 清理测试文件
        if os.path.exists(test_materials_folder):
            shutil.rmtree(test_materials_folder)
        return False

def main():
    """主函数"""
    print("🚀 测试媒体类型功能")
    print("=" * 60)
    
    media_types = [
        (1, "图片模式"),
        (2, "视频模式"), 
        (3, "混合模式")
    ]
    
    results = []
    
    for media_type, type_name in media_types:
        print(f"\n{'='*60}")
        print(f"🎯 测试 {type_name} (类型 {media_type})")
        print(f"{'='*60}")
        
        success = test_media_type_validation(media_type)
        results.append((type_name, success))
    
    # 显示测试结果汇总
    print(f"\n{'='*60}")
    print("📊 测试结果汇总:")
    print(f"{'='*60}")
    
    for type_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {type_name}: {status}")
    
    all_passed = all(success for _, success in results)
    print(f"\n🎉 整体测试结果: {'✅ 全部通过' if all_passed else '❌ 部分失败'}")

if __name__ == "__main__":
    main()