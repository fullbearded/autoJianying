#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import tempfile

def diagnose_video_duration_bug():
    """诊断视频时长被压缩的问题"""
    print("🔍 诊断视频时长压缩问题")
    print("=" * 60)
    
    # 使用测试视频
    test_video = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/examples/test_videos/四字阳章老师_和暖光清.mov"
    
    if not os.path.exists(test_video):
        print(f"❌ 测试视频不存在: {test_video}")
        return
    
    # 1. 检查原始视频信息
    print(f"\n📊 原始视频信息:")
    cmd_probe = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json', 
        '-show_format', '-show_streams', test_video
    ]
    
    result = subprocess.run(cmd_probe, capture_output=True, text=True)
    if result.returncode == 0:
        import json
        info = json.loads(result.stdout)
        duration = float(info['format']['duration'])
        for stream in info['streams']:
            if stream['codec_type'] == 'video':
                fps = eval(stream['r_frame_rate'])
                width = stream['width']
                height = stream['height']
                break
        
        print(f"   时长: {duration:.3f}秒")
        print(f"   帧率: {fps:.2f}fps") 
        print(f"   分辨率: {width}x{height}")
        
        # 计算2帧的时长
        two_frames_duration = 2.0 / fps
        print(f"   2帧时长: {two_frames_duration:.6f}秒")
        print(f"   预期总时长: {duration + two_frames_duration:.3f}秒")
    
    # 2. 测试正确的封面视频创建
    with tempfile.TemporaryDirectory() as temp_dir:
        cover_image = os.path.join(temp_dir, "cover.jpg")
        cover_video = os.path.join(temp_dir, "cover_video.mov")
        final_video = os.path.join(temp_dir, "final_video.mov")
        
        # 步骤1: 提取最后一帧
        print(f"\n🎬 步骤1: 提取最后一帧")
        cmd_extract = [
            'ffmpeg', '-i', test_video, '-ss', str(duration-1), 
            '-vframes', '1', '-q:v', '2', '-y', cover_image
        ]
        result1 = subprocess.run(cmd_extract, capture_output=True, text=True)
        if result1.returncode == 0:
            print(f"   ✅ 封面图提取成功")
        else:
            print(f"   ❌ 封面图提取失败: {result1.stderr}")
            return
            
        # 步骤2: 创建2帧封面视频 - 关键修复
        print(f"\n🎞️ 步骤2: 创建2帧封面视频")
        
        # 关键: 使用-vframes而不是-t来精确控制帧数
        cmd_cover = [
            'ffmpeg',
            '-loop', '1',
            '-i', cover_image,
            '-vframes', '2',  # 关键：精确控制2帧，而不是时长
            '-r', str(fps),
            '-s', f'{width}x{height}',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-an',  # 先不加音频
            '-y', cover_video
        ]
        
        print(f"   命令: {' '.join(cmd_cover)}")
        result2 = subprocess.run(cmd_cover, capture_output=True, text=True)
        if result2.returncode == 0:
            print(f"   ✅ 2帧封面视频创建成功")
            
            # 检查封面视频时长
            cmd_check = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', cover_video]
            check_result = subprocess.run(cmd_check, capture_output=True, text=True)
            if check_result.returncode == 0:
                cover_duration = float(check_result.stdout.strip())
                print(f"   📊 封面视频实际时长: {cover_duration:.6f}秒")
        else:
            print(f"   ❌ 封面视频创建失败: {result2.stderr}")
            return
        
        # 步骤3: 正确的合并方式
        print(f"\n🔗 步骤3: 合并视频")
        
        # 创建文件列表
        filelist = os.path.join(temp_dir, "filelist.txt")
        with open(filelist, 'w') as f:
            f.write(f"file '{cover_video}'\n")
            f.write(f"file '{test_video}'\n")
        
        cmd_concat = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', filelist,
            '-c', 'copy',  # 使用copy避免重编码
            '-y', final_video
        ]
        
        print(f"   命令: {' '.join(cmd_concat)}")
        result3 = subprocess.run(cmd_concat, capture_output=True, text=True)
        
        if result3.returncode == 0:
            print(f"   ✅ 视频合并成功")
            
            # 检查最终视频时长
            cmd_final_check = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', final_video]
            final_result = subprocess.run(cmd_final_check, capture_output=True, text=True)
            if final_result.returncode == 0:
                final_duration = float(final_result.stdout.strip())
                print(f"   📊 最终视频时长: {final_duration:.3f}秒")
                print(f"   📊 预期时长: {duration + two_frames_duration:.3f}秒")
                print(f"   {'✅' if abs(final_duration - (duration + two_frames_duration)) < 0.1 else '❌'} 时长匹配: {abs(final_duration - (duration + two_frames_duration)) < 0.1}")
                
                # 复制到测试输出文件夹查看
                output_path = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/examples/test_videos/debug_fixed.mov"
                subprocess.run(['cp', final_video, output_path])
                print(f"   💾 修复后视频已保存: {output_path}")
            
        else:
            print(f"   ❌ 视频合并失败: {result3.stderr}")
    
    print(f"\n🎯 诊断完成！")

if __name__ == "__main__":
    diagnose_video_duration_bug()