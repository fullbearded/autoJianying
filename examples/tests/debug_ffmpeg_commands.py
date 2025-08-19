#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import os
import tempfile

def test_basic_ffmpeg():
    """测试基础FFmpeg功能"""
    print("🔧 测试基础FFmpeg功能")
    print("=" * 50)
    
    # 1. 创建测试封面图
    test_video = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/examples/test_videos/test_video.mp4"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cover_image_path = os.path.join(temp_dir, "test_cover.jpg")
        cover_video_path = os.path.join(temp_dir, "test_cover_video.mp4")
        
        # 步骤1：提取封面图
        print("\n📸 步骤1：提取封面图")
        cmd1 = [
            'ffmpeg',
            '-i', test_video,
            '-ss', '9.0',  # 提取第9秒的帧
            '-vframes', '1',
            '-q:v', '2',
            '-y',
            cover_image_path
        ]
        
        print(f"   命令: {' '.join(cmd1)}")
        result1 = subprocess.run(cmd1, capture_output=True, text=True)
        if result1.returncode == 0 and os.path.exists(cover_image_path):
            print(f"   ✅ 封面图提取成功: {os.path.getsize(cover_image_path)} bytes")
        else:
            print(f"   ❌ 封面图提取失败: {result1.stderr}")
            return
        
        # 步骤2：创建最简单的封面视频
        print("\n🎞️ 步骤2：创建简单封面视频")
        cmd2 = [
            'ffmpeg',
            '-loop', '1',
            '-i', cover_image_path,
            '-t', '0.067',  # 2帧 @ 30fps
            '-r', '30',
            '-s', '1280x720',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',  # 先用兼容格式
            '-preset', 'fast',
            '-crf', '23',
            '-an',  # 无音频，简化测试
            '-y',
            cover_video_path
        ]
        
        print(f"   命令: {' '.join(cmd2)}")
        result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=30)
        if result2.returncode == 0 and os.path.exists(cover_video_path):
            print(f"   ✅ 简单封面视频创建成功: {os.path.getsize(cover_video_path)} bytes")
        else:
            print(f"   ❌ 简单封面视频创建失败:")
            print(f"      返回码: {result2.returncode}")
            print(f"      错误输出: {result2.stderr}")
            return
        
        # 步骤3：测试yuv444p像素格式
        print("\n🎨 步骤3：测试yuv444p像素格式")
        cover_video_444_path = os.path.join(temp_dir, "test_cover_video_444.mp4")
        cmd3 = [
            'ffmpeg',
            '-loop', '1',
            '-i', cover_image_path,
            '-t', '0.067',
            '-r', '30',
            '-s', '1280x720',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv444p',  # 测试原始像素格式
            '-preset', 'fast',
            '-crf', '23',
            '-an',
            '-y',
            cover_video_444_path
        ]
        
        print(f"   命令: {' '.join(cmd3)}")
        result3 = subprocess.run(cmd3, capture_output=True, text=True, timeout=30)
        if result3.returncode == 0 and os.path.exists(cover_video_444_path):
            print(f"   ✅ yuv444p封面视频创建成功: {os.path.getsize(cover_video_444_path)} bytes")
        else:
            print(f"   ❌ yuv444p封面视频创建失败:")
            print(f"      返回码: {result3.returncode}")
            print(f"      错误输出: {result3.stderr}")
        
        # 步骤4：测试带音频的版本
        print("\n🔊 步骤4：测试带音频封面视频")
        cover_video_audio_path = os.path.join(temp_dir, "test_cover_video_audio.mp4")
        cmd4 = [
            'ffmpeg',
            '-loop', '1',
            '-i', cover_image_path,
            '-f', 'lavfi',
            '-i', 'anullsrc=channel_layout=mono:sample_rate=44100',
            '-t', '0.067',
            '-r', '30',
            '-s', '1280x720',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv444p',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '69k',  # 匹配原视频比特率
            '-ar', '44100',
            '-ac', '1',
            '-shortest',
            '-y',
            cover_video_audio_path
        ]
        
        print(f"   命令: {' '.join(cmd4[:10])}... (简化显示)")
        result4 = subprocess.run(cmd4, capture_output=True, text=True, timeout=30)
        if result4.returncode == 0 and os.path.exists(cover_video_audio_path):
            print(f"   ✅ 带音频封面视频创建成功: {os.path.getsize(cover_video_audio_path)} bytes")
        else:
            print(f"   ❌ 带音频封面视频创建失败:")
            print(f"      返回码: {result4.returncode}")
            print(f"      错误输出: {result4.stderr[:300]}")
        
        # 步骤5：测试concat合并
        print("\n🔗 步骤5：测试视频合并")
        if os.path.exists(cover_video_444_path):
            output_path = os.path.join(temp_dir, "merged_video.mp4")
            
            # 创建文件列表
            filelist_path = os.path.join(temp_dir, "filelist.txt")
            with open(filelist_path, 'w') as f:
                f.write(f"file '{cover_video_444_path}'\n")
                f.write(f"file '{test_video}'\n")
            
            cmd5 = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', filelist_path,
                '-c', 'copy',
                '-y',
                output_path
            ]
            
            print(f"   命令: {' '.join(cmd5)}")
            result5 = subprocess.run(cmd5, capture_output=True, text=True, timeout=30)
            if result5.returncode == 0 and os.path.exists(output_path):
                print(f"   ✅ 视频合并成功: {os.path.getsize(output_path)} bytes")
                print(f"   📊 合并后大小对比:")
                print(f"      封面视频: {os.path.getsize(cover_video_444_path)} bytes")
                print(f"      原视频: {os.path.getsize(test_video)} bytes")
                print(f"      合并后: {os.path.getsize(output_path)} bytes")
            else:
                print(f"   ⚠️ stream copy合并失败:")
                print(f"      返回码: {result5.returncode}")
                print(f"      错误输出: {result5.stderr[:300]}")
                
                # 尝试重编码合并
                print("   🔄 尝试重编码合并...")
                cmd5_alt = [
                    'ffmpeg',
                    '-i', cover_video_444_path,
                    '-i', test_video,
                    '-filter_complex', '[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[outv][outa]',
                    '-map', '[outv]',
                    '-map', '[outa]',
                    '-c:v', 'libx264',
                    '-crf', '18',
                    '-c:a', 'aac',
                    '-y',
                    output_path
                ]
                
                result5_alt = subprocess.run(cmd5_alt, capture_output=True, text=True, timeout=60)
                if result5_alt.returncode == 0 and os.path.exists(output_path):
                    print(f"   ✅ 重编码合并成功: {os.path.getsize(output_path)} bytes")
                else:
                    print(f"   ❌ 重编码合并也失败: {result5_alt.stderr[:200]}")
        
    print(f"\n🎉 FFmpeg命令测试完成")

if __name__ == "__main__":
    test_basic_ffmpeg()