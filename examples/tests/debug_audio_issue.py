#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试音频处理导致的时长问题
比较简单方法 vs 复杂音频处理的差异
"""

import os
import subprocess
import tempfile
import json

def compare_audio_vs_no_audio():
    """比较有音频和无音频的封面视频创建"""
    print("🔍 调试音频处理时长问题")
    print("=" * 50)
    
    test_video = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/examples/test_videos/四字阳章老师_和暖光清.mov"
    
    if not os.path.exists(test_video):
        print(f"❌ 测试视频不存在")
        return
    
    # 获取原视频信息
    cmd_info = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_format', '-show_streams', test_video
    ]
    result = subprocess.run(cmd_info, capture_output=True, text=True)
    info = json.loads(result.stdout)
    
    # 提取关键信息
    duration = float(info['format']['duration'])
    video_stream = None
    audio_stream = None
    
    for stream in info['streams']:
        if stream['codec_type'] == 'video' and not video_stream:
            video_stream = stream
        elif stream['codec_type'] == 'audio' and not audio_stream:
            audio_stream = stream
    
    fps = eval(video_stream['r_frame_rate'])
    width = video_stream['width']
    height = video_stream['height']
    sample_rate = int(audio_stream['sample_rate'])
    channels = int(audio_stream['channels'])
    channel_layout = audio_stream['channel_layout']
    
    print(f"📊 原视频信息:")
    print(f"   时长: {duration:.6f}秒")
    print(f"   帧率: {fps:.2f}fps")
    print(f"   音频: {sample_rate}Hz, {channels}ch, {channel_layout}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 1. 提取封面图
        cover_image = os.path.join(temp_dir, "cover.jpg")
        cmd_extract = [
            'ffmpeg', '-i', test_video, '-ss', str(duration-1),
            '-vframes', '1', '-q:v', '2', '-y', cover_image
        ]
        subprocess.run(cmd_extract, capture_output=True)
        
        # 2. 测试简单无音频版本（像诊断脚本）
        print(f"\n🎞️ 测试1: 简单无音频2帧封面视频")
        cover_simple = os.path.join(temp_dir, "cover_simple.mov")
        cmd_simple = [
            'ffmpeg',
            '-loop', '1',
            '-i', cover_image,
            '-vframes', '2',
            '-r', str(fps),
            '-s', f'{width}x{height}',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-an',  # 无音频
            '-y', cover_simple
        ]
        
        result1 = subprocess.run(cmd_simple, capture_output=True, text=True)
        if result1.returncode == 0:
            # 检查时长
            cmd_check = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', cover_simple]
            check_result = subprocess.run(cmd_check, capture_output=True, text=True)
            simple_duration = float(check_result.stdout.strip())
            print(f"   ✅ 简单封面视频: {simple_duration:.6f}秒")
        else:
            print(f"   ❌ 简单封面视频失败: {result1.stderr}")
            return
        
        # 3. 测试复杂带音频版本（像主脚本）
        print(f"\n🎵 测试2: 复杂带音频2帧封面视频")
        cover_complex = os.path.join(temp_dir, "cover_complex.mov")
        cmd_complex = [
            'ffmpeg',
            '-loop', '1',
            '-i', cover_image,
            '-f', 'lavfi',
            '-i', f"anullsrc=channel_layout={channel_layout}:sample_rate={sample_rate}",
            '-vframes', '2',  # 关键：精确2帧
            '-r', str(fps),
            '-s', f'{width}x{height}',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-preset', 'fast',
            '-crf', '18',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-ar', str(sample_rate),
            '-ac', str(channels),
            '-shortest',  # 关键：音频匹配视频长度
            '-movflags', '+faststart',
            '-y', cover_complex
        ]
        
        print(f"   命令: ffmpeg -loop 1 ... -vframes 2 ... -shortest ...")
        result2 = subprocess.run(cmd_complex, capture_output=True, text=True)
        if result2.returncode == 0:
            # 检查时长
            cmd_check = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', cover_complex]
            check_result = subprocess.run(cmd_check, capture_output=True, text=True)
            complex_duration = float(check_result.stdout.strip())
            print(f"   ✅ 复杂封面视频: {complex_duration:.6f}秒")
        else:
            print(f"   ❌ 复杂封面视频失败: {result2.stderr}")
            return
        
        # 4. 对比两种方法的合并结果
        print(f"\n🔗 测试合并结果:")
        
        # 简单方法合并
        final_simple = os.path.join(temp_dir, "final_simple.mov")
        filelist_simple = os.path.join(temp_dir, "list_simple.txt")
        with open(filelist_simple, 'w') as f:
            f.write(f"file '{cover_simple}'\\n")
            f.write(f"file '{test_video}'\\n")
        
        cmd_merge_simple = [
            'ffmpeg', '-f', 'concat', '-safe', '0', '-i', filelist_simple,
            '-c', 'copy', '-y', final_simple
        ]
        result3 = subprocess.run(cmd_merge_simple, capture_output=True, text=True)
        
        if result3.returncode == 0:
            cmd_check = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', final_simple]
            check_result = subprocess.run(cmd_check, capture_output=True, text=True)
            simple_final_duration = float(check_result.stdout.strip())
            print(f"   简单方法最终时长: {simple_final_duration:.6f}秒")
        else:
            print(f"   简单方法合并失败，尝试重编码...")
            # 尝试重编码合并
            cmd_reencode = [
                'ffmpeg', '-i', cover_simple, '-i', test_video,
                '-filter_complex', '[0:v][1:v]concat=n=2:v=1:a=0[outv]; [1:a]acopy[outa]',
                '-map', '[outv]', '-map', '[outa]',
                '-c:v', 'libx264', '-crf', '18', '-c:a', 'aac',
                '-y', final_simple
            ]
            result3_alt = subprocess.run(cmd_reencode, capture_output=True, text=True)
            if result3_alt.returncode == 0:
                cmd_check = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', final_simple]
                check_result = subprocess.run(cmd_check, capture_output=True, text=True)
                simple_final_duration = float(check_result.stdout.strip())
                print(f"   简单方法最终时长（重编码）: {simple_final_duration:.6f}秒")
            else:
                print(f"   简单方法重编码也失败")
                simple_final_duration = 0
        
        # 复杂方法合并
        final_complex = os.path.join(temp_dir, "final_complex.mov")
        filelist_complex = os.path.join(temp_dir, "list_complex.txt")
        with open(filelist_complex, 'w') as f:
            f.write(f"file '{cover_complex}'\\n")
            f.write(f"file '{test_video}'\\n")
        
        cmd_merge_complex = [
            'ffmpeg', '-f', 'concat', '-safe', '0', '-i', filelist_complex,
            '-c', 'copy', '-y', final_complex
        ]
        result4 = subprocess.run(cmd_merge_complex, capture_output=True, text=True)
        
        if result4.returncode == 0:
            cmd_check = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', final_complex]
            check_result = subprocess.run(cmd_check, capture_output=True, text=True)
            complex_final_duration = float(check_result.stdout.strip())
            print(f"   复杂方法最终时长: {complex_final_duration:.6f}秒")
        else:
            print(f"   复杂方法合并失败: {result4.stderr}")
            complex_final_duration = 0
        
        # 分析结果
        expected_duration = duration + (2 / fps)
        print(f"\n📊 结果分析:")
        print(f"   原视频时长: {duration:.6f}秒")
        print(f"   预期总时长: {expected_duration:.6f}秒")
        print(f"   简单方法: {simple_final_duration:.6f}秒 (差异: {abs(simple_final_duration - expected_duration):.6f}秒)")
        print(f"   复杂方法: {complex_final_duration:.6f}秒 (差异: {abs(complex_final_duration - expected_duration):.6f}秒)")
        
        if abs(simple_final_duration - expected_duration) < 0.1:
            print(f"   ✅ 简单方法时长正确")
        else:
            print(f"   ❌ 简单方法时长错误")
            
        if abs(complex_final_duration - expected_duration) < 0.1:
            print(f"   ✅ 复杂方法时长正确")
        else:
            print(f"   ❌ 复杂方法时长错误")
            
        # 保存测试结果供检查
        output_dir = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/examples/test_videos/debug_comparison"
        os.makedirs(output_dir, exist_ok=True)
        
        if simple_final_duration > 0:
            subprocess.run(['cp', final_simple, os.path.join(output_dir, 'simple_method.mov')])
            print(f"   💾 简单方法结果: debug_comparison/simple_method.mov")
        
        if complex_final_duration > 0:
            subprocess.run(['cp', final_complex, os.path.join(output_dir, 'complex_method.mov')])
            print(f"   💾 复杂方法结果: debug_comparison/complex_method.mov")

if __name__ == "__main__":
    compare_audio_vs_no_audio()