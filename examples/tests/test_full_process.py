#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from video_cover_inserter import VideoCoverInserter

def test_full_process():
    """测试完整的处理流程"""
    inserter = VideoCoverInserter()
    
    # 设置测试路径（使用本地测试视频）
    test_folder = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/examples/test_videos/"
    
    print("🧪 开始测试完整处理流程")
    print(f"测试文件夹: {test_folder}")
    
    # 1. 检查FFmpeg
    if not inserter.check_ffmpeg():
        print("❌ FFmpeg 不可用，退出测试")
        return
    
    # 2. 查找视频文件
    video_files = inserter.find_video_files(test_folder)
    if not video_files:
        print("❌ 没有找到视频文件")
        return
    
    print(f"✅ 找到 {len(video_files)} 个视频文件")
    
    # 3. 设置输出文件夹
    import os
    output_folder = os.path.join(test_folder, "processed_with_cover")
    os.makedirs(output_folder, exist_ok=True)
    print(f"📁 输出文件夹: {output_folder}")
    
    # 4. 获取视频详细信息
    test_video = video_files[0]
    print(f"\n🎬 测试处理: {os.path.basename(test_video)}")
    
    # 显示视频详细信息
    video_info = inserter.get_video_info(test_video)
    if video_info:
        print(f"📊 详细信息:")
        print(f"   分辨率: {video_info['width']}x{video_info['height']}")
        print(f"   时长: {video_info['duration']:.2f}秒")
        print(f"   帧率: {video_info['fps']:.2f}fps")
        print(f"   视频编码: {video_info['video_codec']}")
        print(f"   像素格式: {video_info['pixel_format']}")
        print(f"   音频: {'有 (' + video_info['audio_codec'] + ')' if video_info['has_audio'] else '无'}")
    
    success = inserter.process_single_video(test_video, output_folder)
    
    if success:
        print("✅ 测试成功！")
        print(f"📁 请检查输出文件夹: {output_folder}")
        
        # 验证输出文件
        import os
        base_name = os.path.splitext(os.path.basename(test_video))[0]
        output_video = os.path.join(output_folder, f"{base_name}_with_cover.mp4")
        output_cover = os.path.join(output_folder, f"{base_name}_cover.jpg")
        
        if os.path.exists(output_video):
            size_mb = os.path.getsize(output_video) / (1024 * 1024)
            print(f"📹 输出视频: {os.path.basename(output_video)} ({size_mb:.1f} MB)")
            
        if os.path.exists(output_cover):
            print(f"🖼️ 封面图: {os.path.basename(output_cover)}")
    else:
        print("❌ 测试失败")

if __name__ == "__main__":
    test_full_process()