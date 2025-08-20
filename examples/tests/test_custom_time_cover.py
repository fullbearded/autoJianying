#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的自定义时间点封面提取功能
验证能否正确从指定时间点提取帧作为封面
"""

import os
import sys
import tempfile

# 添加父目录到路径以导入video_cover_inserter
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from video_cover_inserter import VideoCoverInserter

def test_custom_time_cover():
    """测试指定时间点的封面提取功能"""
    print("🧪 测试自定义时间点封面提取功能")
    print("=" * 50)
    
    # 测试视频路径
    test_video = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/examples/tests/test_videos/四字阳章老师_和暖光清.mov"
    
    if not os.path.exists(test_video):
        print(f"❌ 测试视频不存在: {test_video}")
        return False
    
    # 创建插入器实例
    inserter = VideoCoverInserter()
    
    # 检查FFmpeg
    if not inserter.check_ffmpeg():
        print("❌ FFmpeg 不可用")
        return False
    
    # 获取视频信息
    print(f"\n📊 分析测试视频...")
    video_info = inserter.get_video_info(test_video)
    if not video_info:
        print("❌ 无法获取视频信息")
        return False
    
    print(f"   📂 文件: {os.path.basename(test_video)}")
    print(f"   ⏱️ 总时长: {video_info['duration']:.2f}秒")
    print(f"   📏 分辨率: {video_info['width']}x{video_info['height']}")
    print(f"   🎞️ 帧率: {video_info['fps']:.2f}fps")
    
    # 测试不同时间点的封面提取
    test_times = [0, 2.5, 5.0, video_info['duration']/2, video_info['duration']-1]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"\n🎯 测试不同时间点的封面提取:")
        
        for i, test_time in enumerate(test_times):
            if test_time > video_info['duration'] - 0.5:
                test_time = video_info['duration'] - 1.0  # 避免超出视频长度
                time_desc = "最后一帧"
            else:
                time_desc = f"第{test_time}秒"
            
            print(f"\n   测试{i+1}: {time_desc}")
            
            # 设置参数
            if i == len(test_times) - 1:  # 最后一个测试使用默认的最后一帧模式
                inserter.cover_source_mode = "last"
                inserter.cover_source_time = None
            else:
                inserter.cover_source_mode = "time"
                inserter.cover_source_time = test_time
            
            # 提取封面
            cover_image_path = os.path.join(temp_dir, f"cover_test_{i+1}.jpg")
            success = inserter.extract_frame_from_video(test_video, cover_image_path)
            
            if success and os.path.exists(cover_image_path):
                file_size = os.path.getsize(cover_image_path) / 1024  # KB
                print(f"      ✅ 封面提取成功: {file_size:.1f}KB")
            else:
                print(f"      ❌ 封面提取失败")
                return False
        
        # 测试完整的处理流程（使用指定时间点）
        print(f"\n🎬 测试完整处理流程 (第3秒封面):")
        
        # 设置参数
        inserter.cover_source_mode = "time"
        inserter.cover_source_time = 3.0
        inserter.cover_duration_mode = "frames"
        inserter.cover_frames = 2
        
        # 创建输出目录
        output_dir = os.path.join(temp_dir, "custom_time_test")
        os.makedirs(output_dir, exist_ok=True)
        
        # 处理视频
        success = inserter.process_single_video(test_video, output_dir)
        
        if success:
            # 验证输出文件
            base_name = os.path.splitext(os.path.basename(test_video))[0]
            output_video = os.path.join(output_dir, f"{base_name}_with_cover.mov")
            output_cover = os.path.join(output_dir, f"{base_name}_cover.jpg")
            
            if os.path.exists(output_video) and os.path.exists(output_cover):
                output_info = inserter.get_video_info(output_video)
                if output_info:
                    print(f"      ✅ 完整处理成功")
                    print(f"      📊 输出时长: {output_info['duration']:.3f}秒")
                    print(f"      📂 输出文件: {os.path.basename(output_video)}")
                    print(f"      🖼️ 封面文件: {os.path.basename(output_cover)}")
                    
                    # 复制结果到可查看的位置
                    result_dir = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/examples/tests/test_videos/custom_time_test"
                    os.makedirs(result_dir, exist_ok=True)
                    
                    import shutil
                    shutil.copy2(output_video, result_dir)
                    shutil.copy2(output_cover, result_dir)
                    print(f"      💾 结果已保存到: tests/test_videos/custom_time_test/")
                    
                    return True
        
        print(f"      ❌ 完整处理失败")
        return False

def main():
    """主测试函数"""
    success = test_custom_time_cover()
    
    if success:
        print(f"\n🎉 自定义时间点封面提取功能测试通过！")
        print(f"📋 功能验证:")
        print(f"   ✅ 可以从指定时间点提取帧")
        print(f"   ✅ 可以使用默认的最后一帧")
        print(f"   ✅ 完整处理流程正常")
        print(f"   ✅ 输出文件格式正确")
    else:
        print(f"\n❌ 测试失败")

if __name__ == "__main__":
    main()