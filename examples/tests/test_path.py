#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from video_cover_inserter import VideoCoverInserter

def test_path():
    inserter = VideoCoverInserter()
    test_path = "/Volumes/高速存储-158XXXX6956/0_书法自媒体/产品素材/汉字墨迹20250819/成品/"
    
    print("=== 路径测试 ===")
    print(f"测试路径: {test_path}")
    print(f"路径存在: {os.path.exists(test_path)}")
    print(f"是目录: {os.path.isdir(test_path)}")
    
    # 测试路径修复功能
    fixed_path = inserter.try_fix_path(test_path)
    print(f"修复后路径: {fixed_path}")
    
    # 测试文件扫描
    if os.path.exists(test_path):
        print("\n=== 扫描视频文件 ===")
        video_files = inserter.find_video_files(test_path)
        print(f"找到 {len(video_files)} 个视频文件")
    
if __name__ == "__main__":
    test_path()