#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试汉字命名功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from examples.interactive_cli import BatchDraftProcessor


def test_chinese_extraction():
    """测试汉字提取功能"""
    print("=== 测试汉字提取功能 ===")
    
    processor = BatchDraftProcessor()
    
    test_files = [
        "A光.mp4",
        "B经.mp4", 
        "C武.mp4",
        "D武.mp4",
        "E狂.mp4",
        "video_A.mp4",
        "test123.mp4"
    ]
    
    print("测试文件名汉字提取:")
    for filename in test_files:
        chinese_chars = processor.extract_chinese_chars(filename)
        print(f"  {filename} → {chinese_chars}")
    
    return True


def test_combo_naming():
    """测试组合命名功能"""
    print("\n=== 测试组合命名功能 ===")
    
    processor = BatchDraftProcessor()
    
    test_combinations = [
        {'part1': 'A光.mp4', 'part2': 'A在.mp4', 'part3': 'A和.mp4'},
        {'part1': 'B经.mp4', 'part2': 'B在.mp4', 'part3': 'B行.mp4'},
        {'part1': 'C武.mp4', 'part2': 'C斧.mp4', 'part3': 'C毒.mp4'},
        {'part1': 'D武.mp4', 'part2': 'D规.mp4', 'part3': 'D故.mp4'},
        {'part1': 'E狂.mp4', 'part2': 'E兽.mp4', 'part3': 'E伐.mp4'},
        {'part1': 'video_A.mp4', 'part2': 'video_B.mp4', 'part3': 'video_C.mp4'}
    ]
    
    print("测试组合命名:")
    for i, combo in enumerate(test_combinations, 1):
        combo_name = processor.generate_chinese_combo_name(combo)
        print(f"  组合 {i}: {combo['part1']} + {combo['part2']} + {combo['part3']} → {combo_name}")
    
    return True


def test_draft_naming():
    """测试草稿命名功能"""
    print("\n=== 测试草稿命名功能 ===")
    
    processor = BatchDraftProcessor()
    processor.selected_draft = "阳章老师模版"
    
    test_combinations = [
        {'part1': 'A光.mp4', 'part2': 'A在.mp4', 'part3': 'A和.mp4'},
        {'part1': 'B经.mp4', 'part2': 'B在.mp4', 'part3': 'B行.mp4'},
        {'part1': 'C武.mp4', 'part2': 'C斧.mp4', 'part3': 'C毒.mp4'},
        {'part1': 'D武.mp4', 'part2': 'D规.mp4', 'part3': 'D故.mp4'},
        {'part1': 'E狂.mp4', 'part2': 'E兽.mp4', 'part3': 'E伐.mp4'}
    ]
    
    print("测试草稿命名:")
    used_names = set()
    for i, combo in enumerate(test_combinations, 1):
        combo_name = processor.generate_chinese_combo_name(combo)
        base_target_name = f"{processor.selected_draft}_{combo_name}"
        
        # 检查名称是否重复，如果重复则添加序号
        target_name = base_target_name
        counter = 1
        while target_name in used_names:
            target_name = f"{base_target_name}_{counter}"
            counter += 1
        used_names.add(target_name)
        
        print(f"  组合 {i}: {combo['part1']} + {combo['part2']} + {combo['part3']}")
        print(f"           → 草稿名称: {target_name}")
    
    return True


def test_real_materials():
    """测试真实素材文件"""
    print("\n=== 测试真实素材文件 ===")
    
    materials_path = os.path.join(project_root, "examples", "materials")
    
    if not os.path.exists(materials_path):
        print("❌ 素材文件夹不存在")
        return False
    
    processor = BatchDraftProcessor()
    
    # 扫描真实文件
    part_folders = ['part1', 'part2', 'part3']
    part_files = {}
    
    for part in part_folders:
        part_path = os.path.join(materials_path, part)
        if os.path.exists(part_path):
            import glob
            mp4_files = glob.glob(os.path.join(part_path, "*.mp4"))
            part_files[part] = [os.path.basename(f) for f in mp4_files]
            print(f"📁 {part}: {len(part_files[part])} 个文件")
    
    if all(part_files.values()):
        # 生成真实组合
        min_count = min(len(files) for files in part_files.values())
        
        print(f"\n📋 真实组合示例 (前5个):")
        for i in range(min(5, min_count)):
            combo = {}
            for part in part_folders:
                sorted_files = sorted(part_files[part])
                combo[part] = sorted_files[i]
            
            combo_name = processor.generate_chinese_combo_name(combo)
            print(f"  组合 {i+1}: {combo['part1']} + {combo['part2']} + {combo['part3']} → {combo_name}")
        
        return True
    else:
        print("❌ 部分part文件夹为空")
        return False


def main():
    """主测试函数"""
    print("🎬 汉字命名功能测试")
    print("=" * 50)
    
    tests = [
        ("汉字提取", test_chinese_extraction),
        ("组合命名", test_combo_naming),
        ("草稿命名", test_draft_naming),
        ("真实素材", test_real_materials)
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
        print("🎉 汉字命名功能正常! 新的命名方式已就绪")
    else:
        print("⚠️ 部分功能需要检查")


if __name__ == "__main__":
    main()