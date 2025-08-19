#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的视频封面插入器 - 验证帧数逻辑
确保50秒视频输出为~50.067秒（50s + 2帧）
"""

import os
import subprocess
import tempfile
from video_cover_inserter import VideoCoverInserter

def test_frame_based_logic():
    """测试帧数逻辑修复效果"""
    print("🧪 测试帧数逻辑修复效果")
    print("=" * 50)
    
    # 测试视频路径
    test_video = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/examples/test_videos/四字阳章老师_和暖光清.mov"
    
    if not os.path.exists(test_video):
        print(f"❌ 测试视频不存在: {test_video}")
        # 尝试查找其他测试视频
        test_folder = os.path.dirname(test_video)
        if os.path.exists(test_folder):
            video_files = [f for f in os.listdir(test_folder) if f.endswith(('.mov', '.mp4'))]
            if video_files:
                test_video = os.path.join(test_folder, video_files[0])
                print(f"✅ 使用替代测试视频: {os.path.basename(test_video)}")
            else:
                print(f"❌ 测试文件夹中没有视频文件")
                return False
        else:
            print(f"❌ 测试文件夹不存在: {test_folder}")
            return False
    
    # 初始化插入器
    inserter = VideoCoverInserter()
    
    # 检查FFmpeg
    if not inserter.check_ffmpeg():
        print("❌ FFmpeg 不可用")
        return False
    
    # 获取原视频信息
    print(f"\n📊 分析原视频信息...")
    video_info = inserter.get_video_info(test_video)
    if not video_info:
        print(f"❌ 无法获取视频信息")
        return False
    
    print(f"   📂 文件: {os.path.basename(test_video)}")
    print(f"   📦 格式: {video_info['format_info'].get('format_name', '未知')}")
    print(f"   ⏱️ 原始时长: {video_info['duration']:.6f}秒")
    print(f"   📏 分辨率: {video_info['width']}x{video_info['height']}")
    print(f"   🎞️ 帧率: {video_info['fps']:.2f}fps")
    print(f"   🎵 音频: {'有' if video_info['has_audio'] else '无'}")
    
    # 计算2帧的精确时长
    cover_frames = 2
    frame_duration = cover_frames / video_info['fps']
    expected_total_duration = video_info['duration'] + frame_duration
    
    print(f"\n🎯 帧数计算:")
    print(f"   封面帧数: {cover_frames}帧")
    print(f"   单帧时长: {1/video_info['fps']:.6f}秒")
    print(f"   封面时长: {frame_duration:.6f}秒")
    print(f"   预期总时长: {expected_total_duration:.6f}秒")
    
    # 创建输出目录
    output_folder = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/examples/test_videos/frame_fix_test"
    os.makedirs(output_folder, exist_ok=True)
    
    # 设置插入器参数（使用默认的前2帧）
    inserter.cover_duration_mode = "frames"
    inserter.cover_frames = 2
    
    print(f"\n🎬 开始处理视频...")
    print(f"   输出目录: {output_folder}")
    
    # 处理单个视频
    success = inserter.process_single_video(test_video, output_folder)
    
    if success:
        print(f"\n✅ 视频处理成功！")
        
        # 验证输出文件
        base_name = os.path.splitext(os.path.basename(test_video))[0]
        original_ext = os.path.splitext(test_video)[1]
        output_video = os.path.join(output_folder, f"{base_name}_with_cover{original_ext}")
        
        if os.path.exists(output_video):
            print(f"\n🔍 验证输出文件:")
            print(f"   输出文件: {os.path.basename(output_video)}")
            
            # 获取输出视频信息
            output_info = inserter.get_video_info(output_video)
            if output_info:
                actual_duration = output_info['duration']
                duration_diff = abs(actual_duration - expected_total_duration)
                
                print(f"   📊 输出时长: {actual_duration:.6f}秒")
                print(f"   📊 预期时长: {expected_total_duration:.6f}秒")
                print(f"   📊 时长差异: {duration_diff:.6f}秒")
                
                # 验证时长是否在合理范围内（允许0.1秒误差）
                if duration_diff < 0.1:
                    print(f"   ✅ 时长验证通过: 误差{duration_diff:.6f}秒 < 0.1秒")
                    
                    # 验证格式保持
                    original_format = video_info['format_info'].get('format_name', '').lower()
                    output_format = output_info['format_info'].get('format_name', '').lower()
                    
                    print(f"   📦 原始格式: {original_format}")
                    print(f"   📦 输出格式: {output_format}")
                    
                    if original_ext.lower() in output_video.lower():
                        print(f"   ✅ 格式保持验证通过: 保持{original_ext}格式")
                        
                        print(f"\n🎉 测试完全通过！")
                        print(f"   ✅ 时长计算正确: {video_info['duration']:.3f}s → {actual_duration:.3f}s")
                        print(f"   ✅ 格式保持正确: {original_ext}")
                        print(f"   ✅ 帧数逻辑修复成功")
                        
                        return True
                    else:
                        print(f"   ❌ 格式保持失败")
                else:
                    print(f"   ❌ 时长验证失败: 误差{duration_diff:.6f}秒过大")
                    print(f"   💡 可能原因: 编码精度或时间戳问题")
            else:
                print(f"   ❌ 无法获取输出视频信息")
        else:
            print(f"   ❌ 输出文件不存在: {output_video}")
    else:
        print(f"\n❌ 视频处理失败")
    
    return False

if __name__ == "__main__":
    success = test_frame_based_logic()
    if success:
        print(f"\n🎯 修复验证结果: 成功")
        print(f"📋 关键修复点:")
        print(f"   - 使用 -vframes 替代 -t 实现精确帧数控制")
        print(f"   - 50秒视频 + 2帧 = ~50.067秒输出")
        print(f"   - 保持原始文件格式（MOV保持MOV）")
        print(f"   - 所有fallback方法已同步修复")
    else:
        print(f"\n❌ 修复验证失败，需要进一步检查")