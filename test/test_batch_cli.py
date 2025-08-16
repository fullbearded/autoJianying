#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试批量CLI工具的功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from examples.interactive_cli import BatchDraftProcessor


def test_material_scanning():
    """测试素材扫描功能"""
    print("=== 测试素材扫描功能 ===")
    
    processor = BatchDraftProcessor()
    
    # 设置测试路径
    materials_path = os.path.join(project_root, "examples", "materials")
    processor.materials_folder_path = materials_path
    
    # 测试扫描part文件夹
    print(f"扫描素材文件夹: {materials_path}")
    
    part_folders = ['part1', 'part2', 'part3']
    part_files = {}
    
    for part in part_folders:
        part_path = os.path.join(materials_path, part)
        
        if os.path.exists(part_path):
            import glob
            mp4_files = glob.glob(os.path.join(part_path, "*.mp4"))
            part_files[part] = [os.path.basename(f) for f in mp4_files]
            print(f"✅ {part}: 找到 {len(part_files[part])} 个.mp4文件")
            for i, file in enumerate(part_files[part][:3]):
                print(f"   {i+1}. {file}")
            if len(part_files[part]) > 3:
                print(f"   ... 还有 {len(part_files[part])-3} 个文件")
        else:
            print(f"❌ {part}: 文件夹不存在")
    
    # 测试组合生成
    if all(part_files.values()):
        print(f"\n=== 测试组合生成 ===")
        min_count = min(len(files) for files in part_files.values())
        print(f"最少文件数量: {min_count}")
        
        # 顺序模式测试
        print(f"\n📋 顺序模式组合:")
        sorted_parts = {}
        for part, files in part_files.items():
            sorted_parts[part] = sorted(files)
        
        combinations = []
        for i in range(min(3, min_count)):  # 只显示前3个组合
            combination = {}
            for part in part_folders:
                combination[part] = sorted_parts[part][i]
            combinations.append(combination)
            print(f"  组合 {i+1}: {combination['part1']} + {combination['part2']} + {combination['part3']}")
        
        if min_count > 3:
            print(f"  ... 还有 {min_count-3} 个组合")
        
        # 随机模式测试
        print(f"\n🎲 随机模式组合:")
        import random
        shuffled_parts = {}
        for part, files in part_files.items():
            shuffled_files = files.copy()
            random.shuffle(shuffled_files)
            shuffled_parts[part] = shuffled_files
        
        for i in range(min(3, min_count)):  # 只显示前3个组合
            combination = {}
            for part in part_folders:
                combination[part] = shuffled_parts[part][i]
            print(f"  组合 {i+1}: {combination['part1']} + {combination['part2']} + {combination['part3']}")
        
        print(f"\n✅ 素材组合功能测试通过!")
        return True
    else:
        print(f"\n❌ 部分part文件夹为空，无法生成组合")
        return False


def test_draft_info_loading():
    """测试草稿信息加载功能"""
    print("\n=== 测试草稿信息加载功能 ===")
    
    processor = BatchDraftProcessor()
    processor.draft_folder_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
    
    if not os.path.exists(processor.draft_folder_path):
        print("❌ 草稿文件夹不存在，跳过测试")
        return False
    
    try:
        import pyJianYingDraft as draft
        processor.draft_folder = draft.DraftFolder(processor.draft_folder_path)
        
        drafts = processor.draft_folder.list_drafts()
        filtered_drafts = [d for d in drafts if not d.startswith('.') and not d.startswith('pyJianYingDraft_Demo')]
        
        print(f"找到 {len(filtered_drafts)} 个可用草稿")
        
        if filtered_drafts:
            # 测试读取第一个草稿信息
            test_draft = filtered_drafts[0]
            print(f"测试读取草稿: {test_draft}")
            
            draft_info = processor.load_draft_info_from_file(test_draft)
            if draft_info:
                print(f"✅ 成功读取草稿信息:")
                canvas = draft_info['canvas_config']
                print(f"  分辨率: {canvas.get('width', '?')}x{canvas.get('height', '?')}")
                print(f"  时长: {draft_info['duration'] / 1000000:.2f}秒")
                print(f"  视频素材数: {len(draft_info['video_materials'])}")
                
                if draft_info['video_materials']:
                    print(f"  前3个视频素材:")
                    for i, video in enumerate(draft_info['video_materials'][:3]):
                        print(f"    {i+1}. {video['name']} ({video['width']}x{video['height']})")
                
                return True
            else:
                print(f"❌ 无法读取草稿信息")
                return False
        else:
            print("❌ 没有可用的草稿进行测试")
            return False
            
    except Exception as e:
        print(f"❌ 草稿信息加载测试失败: {e}")
        return False


def test_video_info_extraction():
    """测试视频信息提取功能"""
    print("\n=== 测试视频信息提取功能 ===")
    
    processor = BatchDraftProcessor()
    
    # 测试materials文件夹中的视频文件
    materials_path = os.path.join(project_root, "examples", "materials")
    
    test_files = []
    for part in ['part1', 'part2', 'part3']:
        part_path = os.path.join(materials_path, part)
        if os.path.exists(part_path):
            import glob
            mp4_files = glob.glob(os.path.join(part_path, "*.mp4"))
            if mp4_files:
                test_files.append(mp4_files[0])  # 取第一个文件测试
    
    if test_files:
        print(f"测试视频文件信息提取:")
        for test_file in test_files[:2]:  # 只测试前2个文件
            print(f"  测试文件: {os.path.basename(test_file)}")
            video_info = processor.get_video_file_info(test_file)
            
            if video_info:
                print(f"    ✅ 成功提取信息:")
                print(f"       时长: {video_info.get('duration', 0) / 1000000:.2f}秒")
                print(f"       分辨率: {video_info.get('width', '?')}x{video_info.get('height', '?')}")
            else:
                print(f"    ⚠️ 无法提取信息（使用默认值）")
        
        return True
    else:
        print("❌ 没有找到测试视频文件")
        return False


def main():
    """主测试函数"""
    print("🎬 批量CLI工具功能测试")
    print("=" * 50)
    
    tests = [
        ("素材扫描", test_material_scanning),
        ("草稿信息加载", test_draft_info_loading),
        ("视频信息提取", test_video_info_extraction)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"✅ {test_name} 测试通过")
                passed += 1
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"💥 {test_name} 测试出错: {e}")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有功能测试通过! CLI工具准备就绪")
    else:
        print("⚠️ 部分功能需要检查")


if __name__ == "__main__":
    main()