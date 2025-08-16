#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试直接JSON替换功能
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from examples.interactive_cli import InteractiveDraftCLI


def create_mock_draft_info():
    """创建模拟的draft_info.json数据"""
    return {
        "canvas_config": {
            "width": 1920,
            "height": 1080,
            "ratio": "16:9"
        },
        "duration": 30000000,  # 30秒（微秒）
        "fps": 30.0,
        "tracks": [
            {
                "type": "video",
                "segments": [
                    {"id": "seg1", "material_id": "video1"},
                    {"id": "seg2", "material_id": "video2"}
                ]
            }
        ],
        "materials": {
            "videos": [
                {
                    "id": "video1",
                    "material_name": "original_video1.mp4",
                    "path": "##_draftpath_placeholder_0E685133-18CE-45ED-8CB8-2904A212EC80_##/materials/video/original_video1.mp4",
                    "duration": 15000000,
                    "width": 1920,
                    "height": 1080
                },
                {
                    "id": "video2", 
                    "material_name": "original_video2.mp4",
                    "path": "##_draftpath_placeholder_0E685133-18CE-45ED-8CB8-2904A212EC80_##/materials/video/original_video2.mp4",
                    "duration": 15000000,
                    "width": 1920,
                    "height": 1080
                }
            ]
        }
    }


def create_mock_video_file(path, duration_sec=10):
    """创建模拟的视频文件（空文件，用于测试）"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write("mock video file")
    return path


def test_direct_json_replacement():
    """测试直接JSON替换功能"""
    print("=== 测试直接JSON替换功能 ===")
    
    # 创建临时目录结构
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"创建临时测试目录: {temp_dir}")
        
        # 设置目录结构
        draft_folder = os.path.join(temp_dir, "drafts")
        test_draft_name = "test_draft"
        draft_path = os.path.join(draft_folder, test_draft_name)
        materials_path = os.path.join(draft_path, "materials", "video")
        
        os.makedirs(materials_path, exist_ok=True)
        
        # 创建模拟的draft_info.json
        draft_info = create_mock_draft_info()
        draft_info_path = os.path.join(draft_path, "draft_info.json")
        
        with open(draft_info_path, 'w', encoding='utf-8') as f:
            json.dump(draft_info, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 创建模拟草稿: {draft_info_path}")
        
        # 创建模拟的替换视频文件
        new_videos_dir = os.path.join(temp_dir, "new_videos")
        os.makedirs(new_videos_dir, exist_ok=True)
        
        new_video1 = create_mock_video_file(os.path.join(new_videos_dir, "new_video1.mp4"))
        new_video2 = create_mock_video_file(os.path.join(new_videos_dir, "new_video2.mp4"))
        
        print(f"✓ 创建替换视频: {new_video1}, {new_video2}")
        
        # 创建CLI实例并设置测试路径
        cli = InteractiveDraftCLI()
        cli.draft_folder_path = draft_folder
        cli.copied_draft_name = test_draft_name
        
        # 准备替换数据
        replacements = [
            {
                'original_name': 'original_video1.mp4',
                'original_id': 'video1',
                'new_file': new_video1,
                'new_name': 'new_video1.mp4'
            },
            {
                'original_name': 'original_video2.mp4', 
                'original_id': 'video2',
                'new_file': new_video2,
                'new_name': 'new_video2.mp4'
            }
        ]
        
        print(f"✓ 准备替换数据: {len(replacements)} 个替换项")
        
        # 执行直接JSON替换
        print("执行直接JSON替换...")
        success = cli.attempt_direct_json_replacement(replacements)
        
        if success:
            print("✓ 直接JSON替换成功!")
            
            # 验证结果
            print("验证替换结果...")
            
            # 检查备份文件
            backup_path = draft_info_path + ".backup"
            if os.path.exists(backup_path):
                print("✓ 备份文件已创建")
            else:
                print("❌ 备份文件未创建")
                return False
            
            # 检查新视频文件是否复制
            for replacement in replacements:
                target_file = os.path.join(materials_path, replacement['new_name'])
                if os.path.exists(target_file):
                    print(f"✓ 新视频文件已复制: {replacement['new_name']}")
                else:
                    print(f"❌ 新视频文件未复制: {replacement['new_name']}")
                    return False
            
            # 检查draft_info.json更新
            with open(draft_info_path, 'r', encoding='utf-8') as f:
                updated_info = json.load(f)
            
            videos = updated_info.get('materials', {}).get('videos', [])
            
            expected_names = {r['new_name'] for r in replacements}
            actual_names = {v.get('material_name') for v in videos}
            
            if expected_names == actual_names:
                print("✓ draft_info.json已正确更新")
                
                # 显示更新后的信息
                print("更新后的视频素材:")
                for video in videos:
                    print(f"  - {video.get('material_name')} ({video.get('width')}x{video.get('height')})")
                
                return True
            else:
                print(f"❌ draft_info.json更新不正确")
                print(f"期望: {expected_names}")
                print(f"实际: {actual_names}")
                return False
        else:
            print("❌ 直接JSON替换失败")
            return False


def test_get_video_file_info():
    """测试视频文件信息获取功能"""
    print("\n=== 测试视频文件信息获取功能 ===")
    
    # 创建模拟视频文件
    with tempfile.TemporaryDirectory() as temp_dir:
        mock_video = os.path.join(temp_dir, "test_video.mp4")
        create_mock_video_file(mock_video)
        
        cli = InteractiveDraftCLI()
        video_info = cli.get_video_file_info(mock_video)
        
        if video_info:
            print("✓ 视频信息获取成功")
            print(f"  时长: {video_info.get('duration', 0) / 1000000:.2f}秒")
            print(f"  分辨率: {video_info.get('width', '?')}x{video_info.get('height', '?')}")
            return True
        else:
            print("❌ 视频信息获取失败")
            return False


def main():
    """主测试函数"""
    print("开始测试直接JSON替换功能\n")
    
    tests = [
        ("直接JSON替换", test_direct_json_replacement),
        ("视频文件信息获取", test_get_video_file_info)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"✓ {test_name} 测试通过\n")
                passed += 1
            else:
                print(f"❌ {test_name} 测试失败\n")
        except Exception as e:
            print(f"❌ {test_name} 测试出错: {e}\n")
    
    print(f"=== 测试完成 ===")
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("✓ 所有测试通过!")
    else:
        print("❌ 部分测试失败")


if __name__ == "__main__":
    main()