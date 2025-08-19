#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from video_cover_inserter import VideoCoverInserter
import os

def test_duration_options():
    """测试新的时长选项功能"""
    inserter = VideoCoverInserter()
    
    print("🧪 测试新的封面图时长选项")
    print("=" * 50)
    
    # 测试默认设置
    print("\n📋 默认设置:")
    print(f"   模式: {inserter.cover_duration_mode}")
    print(f"   帧数: {inserter.cover_frames}")
    print(f"   默认时长: {inserter.cover_duration}秒")
    
    # 模拟视频信息
    test_video_info = {
        'fps': 30.0,
        'width': 1920,
        'height': 1080,
        'duration': 60.0
    }
    
    # 测试帧数模式计算
    print(f"\n🎬 假设视频信息:")
    print(f"   帧率: {test_video_info['fps']}fps")
    print(f"   分辨率: {test_video_info['width']}x{test_video_info['height']}")
    
    # 计算实际时长
    if inserter.cover_duration_mode == "frames":
        actual_duration = inserter.cover_frames / test_video_info['fps']
        print(f"\n⏱️ 封面图时长计算:")
        print(f"   前{inserter.cover_frames}帧 ÷ {test_video_info['fps']}fps = {actual_duration:.3f}秒")
    else:
        actual_duration = inserter.cover_duration
        print(f"\n⏱️ 封面图时长:")
        print(f"   {actual_duration}秒")
    
    # 测试不同帧率下的时长
    print(f"\n📊 不同帧率下的时长对比:")
    frame_rates = [24, 25, 30, 50, 60]
    for fps in frame_rates:
        duration = inserter.cover_frames / fps
        print(f"   {fps}fps: 前{inserter.cover_frames}帧 = {duration:.3f}秒")
    
    print("\n✅ 测试完成")
    print("💡 运行 python video_cover_inserter.py 来使用工具")
    
    # 显示新的选项界面
    print(f"\n🎯 新的时长选项:")
    duration_options = ["前2帧", "1秒", "2秒", "3秒", "5秒", "自定义"]
    for i, option in enumerate(duration_options):
        marker = "👉" if i == 0 else "  "
        print(f"{marker} {i + 1}. {option}")
    print("   默认选择: 前2帧 ⭐")

if __name__ == "__main__":
    test_duration_options()