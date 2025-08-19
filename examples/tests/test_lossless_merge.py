#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from video_cover_inserter import VideoCoverInserter
import os

def test_lossless_functionality():
    """测试新的无损合并功能"""
    print("🧪 测试无损合并功能")
    print("=" * 60)
    
    inserter = VideoCoverInserter()
    
    # 1. 环境检查
    print("\n🔧 环境检查:")
    if inserter.check_ffmpeg():
        print("   ✅ FFmpeg 可用")
    else:
        print("   ❌ FFmpeg 不可用，测试终止")
        return
    
    # 2. 查找测试视频
    test_folder = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/examples/test_videos/"
    if not os.path.exists(test_folder):
        print(f"   ❌ 测试文件夹不存在: {test_folder}")
        return
        
    video_files = inserter.find_video_files(test_folder)
    if not video_files:
        print(f"   ❌ 没有找到测试视频")
        return
        
    test_video = video_files[0]
    print(f"   ✅ 测试视频: {os.path.basename(test_video)}")
    
    # 3. 获取详细视频信息
    video_info = inserter.get_video_info(test_video)
    if not video_info:
        print("   ❌ 无法获取视频信息")
        return
        
    print(f"\n📊 原视频详细信息:")
    print(f"   分辨率: {video_info['width']}x{video_info['height']}")
    print(f"   帧率: {video_info['fps']:.2f}fps")
    print(f"   时长: {video_info['duration']:.2f}秒")
    print(f"   视频编码: {video_info['video_codec']}")
    print(f"   像素格式: {video_info['pixel_format']}")
    print(f"   视频比特率: {video_info['video_bitrate']}")
    
    if video_info['has_audio']:
        print(f"   音频编码: {video_info['audio_codec']}")
        print(f"   音频比特率: {video_info['audio_bitrate']}")
        print(f"   采样率: {video_info['sample_rate']}Hz")
        print(f"   声道数: {video_info['channels']}")
    else:
        print(f"   音频: 无")
    
    # 4. 显示无损处理特性
    print(f"\n🎯 无损处理特性:")
    print(f"   ✨ 三层合并策略:")
    print(f"      1. Stream Copy (无重编码，最佳质量)")
    print(f"      2. 无损重编码 (CRF=0)")
    print(f"      3. 高质量备选 (CRF=1)")
    
    print(f"   ✨ 完全匹配源视频参数:")
    print(f"      - 视频编码器: {video_info['video_codec']}")
    print(f"      - 像素格式: {video_info['pixel_format']}")
    if video_info['has_audio']:
        print(f"      - 音频编码器: {video_info['audio_codec']}")
        print(f"      - 音频比特率: ≥{video_info['audio_bitrate']}bps")
    
    # 5. 计算封面图时长
    if inserter.cover_duration_mode == "frames":
        actual_duration = inserter.cover_frames / video_info['fps']
        print(f"\n⏱️ 封面图时长计算:")
        print(f"   前{inserter.cover_frames}帧 ÷ {video_info['fps']:.2f}fps = {actual_duration:.3f}秒")
    
    # 6. 创建测试输出文件夹
    output_folder = os.path.join(test_folder, "lossless_test")
    os.makedirs(output_folder, exist_ok=True)
    print(f"\n📁 输出文件夹: {output_folder}")
    
    # 7. 进行测试处理
    print(f"\n🎬 开始无损测试处理...")
    success = inserter.process_single_video(test_video, output_folder)
    
    if success:
        print(f"\n✅ 无损测试成功！")
        
        # 8. 验证输出文件
        base_name = os.path.splitext(os.path.basename(test_video))[0]
        output_video = os.path.join(output_folder, f"{base_name}_with_cover.mp4")
        output_cover = os.path.join(output_folder, f"{base_name}_cover.jpg")
        
        if os.path.exists(output_video):
            output_size = os.path.getsize(output_video) / (1024 * 1024)
            original_size = os.path.getsize(test_video) / (1024 * 1024)
            print(f"📹 输出视频: {os.path.basename(output_video)}")
            print(f"   原始大小: {original_size:.2f} MB")
            print(f"   输出大小: {output_size:.2f} MB")
            print(f"   大小比例: {output_size/original_size:.2f}x")
            
            # 验证输出视频信息
            output_info = inserter.get_video_info(output_video)
            if output_info:
                print(f"📊 输出视频验证:")
                print(f"   分辨率匹配: {'✅' if output_info['width'] == video_info['width'] and output_info['height'] == video_info['height'] else '❌'}")
                print(f"   编码器匹配: {'✅' if output_info['video_codec'] == video_info['video_codec'] else '❌'}")
                print(f"   像素格式匹配: {'✅' if output_info['pixel_format'] == video_info['pixel_format'] else '❌'}")
                if video_info['has_audio'] and output_info['has_audio']:
                    print(f"   音频编码匹配: {'✅' if output_info['audio_codec'] == video_info['audio_codec'] else '❌'}")
        
        if os.path.exists(output_cover):
            print(f"🖼️ 封面图: {os.path.basename(output_cover)}")
            
        print(f"\n🎉 无损处理测试完成！")
        print(f"💡 文件输出位置: {output_folder}")
        
    else:
        print(f"\n❌ 无损测试失败")

if __name__ == "__main__":
    test_lossless_functionality()