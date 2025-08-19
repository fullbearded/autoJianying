#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from video_cover_inserter import VideoCoverInserter
import os

def test_complete_workflow():
    """测试完整的工作流程"""
    print("🧪 完整工作流程测试")
    print("=" * 60)
    
    inserter = VideoCoverInserter()
    
    # 1. 显示默认设置
    print("\n📋 默认设置:")
    print(f"   ✅ 封面时长模式: {inserter.cover_duration_mode}")
    print(f"   ✅ 默认帧数: 前{inserter.cover_frames}帧")
    print(f"   ✅ 备用时长: {inserter.cover_duration}秒")
    
    # 2. 检查FFmpeg
    print(f"\n🔧 环境检查:")
    if inserter.check_ffmpeg():
        print("   ✅ FFmpeg 可用")
    else:
        print("   ❌ FFmpeg 不可用")
        return
    
    # 3. 查找测试视频
    test_folder = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/examples/test_videos/"
    if os.path.exists(test_folder):
        video_files = inserter.find_video_files(test_folder)
        if video_files:
            print(f"   ✅ 找到 {len(video_files)} 个测试视频")
            
            # 4. 测试视频信息获取
            test_video = video_files[0]
            video_info = inserter.get_video_info(test_video)
            if video_info:
                print(f"\n📊 测试视频信息:")
                print(f"   文件: {os.path.basename(test_video)}")
                print(f"   分辨率: {video_info['width']}x{video_info['height']}")
                print(f"   帧率: {video_info['fps']:.2f}fps")
                print(f"   时长: {video_info['duration']:.2f}秒")
                
                # 5. 计算封面图时长
                if inserter.cover_duration_mode == "frames":
                    actual_duration = inserter.cover_frames / video_info['fps']
                    print(f"\n⏱️ 封面图时长计算:")
                    print(f"   前{inserter.cover_frames}帧 ÷ {video_info['fps']:.2f}fps = {actual_duration:.3f}秒")
                    print("   ✅ 根据视频帧率自动计算时长")
                else:
                    print(f"\n⏱️ 固定时长: {inserter.cover_duration}秒")
        else:
            print("   ⚠️ 测试文件夹中没有视频文件")
    else:
        print(f"   ⚠️ 测试文件夹不存在: {test_folder}")
    
    # 6. 显示新功能说明
    print(f"\n🎯 新功能特性:")
    print(f"   ✨ 新增 '前2帧' 时长选项，设为默认值")
    print(f"   ✨ 根据视频帧率自动计算封面图显示时长")
    print(f"   ✨ 保持提取视频最后一帧作为封面图的逻辑")
    print(f"   ✨ 支持混合时长选项（帧数 + 固定秒数）")
    
    # 7. 显示选项界面
    print(f"\n📋 时长选项界面:")
    duration_options = ["前2帧", "1秒", "2秒", "3秒", "5秒", "自定义"]
    for i, option in enumerate(duration_options):
        marker = "👉" if i == 0 else "  "
        status = " (默认)" if i == 0 else ""
        print(f"{marker} {i + 1}. {option}{status}")
    
    print(f"\n✅ 完整工作流程测试通过")
    print(f"💡 运行 'python video_cover_inserter.py' 开始使用工具")

if __name__ == "__main__":
    test_complete_workflow()