#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import tempfile
from video_cover_inserter import VideoCoverInserter

def create_test_mov_file():
    """创建一个测试用的MOV文件"""
    print("🎬 创建测试MOV文件")
    print("=" * 50)
    
    # 测试文件路径
    test_folder = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/examples/test_videos/"
    test_mov_path = os.path.join(test_folder, "四字阳章老师_和暖光清.mov")
    
    # 如果文件已存在，直接使用
    if os.path.exists(test_mov_path):
        print(f"✅ 测试MOV文件已存在: {os.path.basename(test_mov_path)}")
        return test_mov_path
    
    # 从现有MP4创建MOV测试文件
    source_mp4 = os.path.join(test_folder, "test_video.mp4")
    if not os.path.exists(source_mp4):
        print(f"❌ 源MP4文件不存在: {source_mp4}")
        return None
    
    print(f"📝 从MP4创建MOV测试文件...")
    print(f"   源文件: {os.path.basename(source_mp4)}")
    print(f"   目标文件: {os.path.basename(test_mov_path)}")
    
    # 使用FFmpeg转换为MOV格式
    cmd = [
        'ffmpeg',
        '-i', source_mp4,
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-movflags', '+faststart',
        '-y',
        test_mov_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode == 0 and os.path.exists(test_mov_path):
        file_size = os.path.getsize(test_mov_path) / (1024 * 1024)
        print(f"✅ MOV测试文件创建成功: {file_size:.2f} MB")
        return test_mov_path
    else:
        print(f"❌ MOV文件创建失败: {result.stderr}")
        return None

def test_mov_format_processing():
    """测试MOV格式处理"""
    print("\n🧪 测试MOV格式处理功能")
    print("=" * 60)
    
    # 创建测试文件
    test_mov_path = create_test_mov_file()
    if not test_mov_path:
        return
    
    inserter = VideoCoverInserter()
    
    # 1. 检查环境
    if not inserter.check_ffmpeg():
        print("❌ FFmpeg 不可用")
        return
    
    # 2. 获取MOV文件信息
    print(f"\n📊 分析MOV文件信息...")
    video_info = inserter.get_video_info(test_mov_path)
    if not video_info:
        print("❌ 无法获取MOV视频信息")
        return
        
    print(f"   📂 文件名: {os.path.basename(test_mov_path)}")
    print(f"   📦 容器格式: {video_info['format_info'].get('format_name', '未知')}")
    print(f"   🎥 视频编码: {video_info['video_codec']}")
    print(f"   🎵 音频编码: {video_info['audio_codec']}")
    print(f"   📏 分辨率: {video_info['width']}x{video_info['height']}")
    print(f"   ⏱️ 帧率: {video_info['fps']:.2f}fps")
    print(f"   🕐 时长: {video_info['duration']:.2f}秒")
    
    # 3. 创建输出文件夹
    test_folder = os.path.dirname(test_mov_path)
    output_folder = os.path.join(test_folder, "mov_format_test")
    os.makedirs(output_folder, exist_ok=True)
    print(f"\n📁 输出文件夹: {output_folder}")
    
    # 4. 处理MOV文件
    print(f"\n🎬 开始处理MOV文件...")
    print(f"   使用前{inserter.cover_frames}帧模式")
    
    success = inserter.process_single_video(test_mov_path, output_folder)
    
    if success:
        print(f"\n✅ MOV格式处理成功！")
        
        # 验证输出文件
        base_name = os.path.splitext(os.path.basename(test_mov_path))[0]
        output_video = os.path.join(output_folder, f"{base_name}_with_cover.mov")
        output_cover = os.path.join(output_folder, f"{base_name}_cover.jpg")
        
        if os.path.exists(output_video):
            # 文件大小对比
            original_size = os.path.getsize(test_mov_path) / (1024 * 1024)
            output_size = os.path.getsize(output_video) / (1024 * 1024)
            print(f"\n📹 输出文件验证:")
            print(f"   ✅ 输出格式: {os.path.splitext(output_video)[1]} (保持MOV格式)")
            print(f"   📊 原始大小: {original_size:.2f} MB")
            print(f"   📊 输出大小: {output_size:.2f} MB")
            print(f"   📊 大小比例: {output_size/original_size:.2f}x")
            
            # 验证输出视频格式
            output_info = inserter.get_video_info(output_video)
            if output_info:
                print(f"\n🔍 输出视频详细信息:")
                print(f"   📦 容器格式: {output_info['format_info'].get('format_name', '未知')}")
                print(f"   🎥 视频编码: {output_info['video_codec']}")
                print(f"   🎨 像素格式: {output_info['pixel_format']}")
                print(f"   🎵 音频编码: {output_info['audio_codec']}")
                print(f"   ⏱️ 总时长: {output_info['duration']:.3f}秒")
                
                # 格式匹配验证
                format_match = (
                    video_info['video_codec'] == output_info['video_codec'] and
                    video_info['audio_codec'] == output_info['audio_codec'] and
                    abs(video_info['fps'] - output_info['fps']) < 0.01
                )
                
                print(f"\n📋 格式匹配验证:")
                print(f"   {'✅' if format_match else '❌'} 编码器匹配: {format_match}")
                print(f"   {'✅' if '.mov' in output_video.lower() else '❌'} MOV格式保持: {'.mov' in output_video.lower()}")
        
        if os.path.exists(output_cover):
            cover_size = os.path.getsize(output_cover) / 1024
            print(f"\n🖼️ 封面图: {os.path.basename(output_cover)} ({cover_size:.1f} KB)")
            
        print(f"\n🎉 MOV格式处理测试完成！")
        print(f"📂 查看结果: {output_folder}")
        
    else:
        print(f"\n❌ MOV格式处理失败")

if __name__ == "__main__":
    test_mov_format_processing()