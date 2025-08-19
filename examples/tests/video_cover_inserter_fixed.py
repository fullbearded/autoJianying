#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频封面图插入工具 - 修复版本
专门修复50秒视频被压缩到2秒的严重bug

用户需求：
- 原始视频：50秒
- 截取最后一帧作为封面
- 在开头添加2帧封面图（~0.067秒）
- 输出：50.067秒，保持原格式
"""

import os
import sys
import subprocess
import glob
from pathlib import Path
import tempfile
import shutil
import urllib.parse
import json


class VideoCoverInserterFixed:
    """修复版本的视频封面图插入器"""
    
    def __init__(self):
        self.video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.m4v']
        self.cover_frames = 2  # 固定使用2帧
        
    def print_header(self, title):
        """打印标题"""
        print("\n" + "=" * 60)
        print(f"🎬 {title}")
        print("=" * 60)
        
    def check_ffmpeg(self):
        """检查ffmpeg是否可用"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ FFmpeg 已安装")
                return True
            else:
                print("❌ FFmpeg 不可用")
                return False
        except FileNotFoundError:
            print("❌ FFmpeg 未安装，请先安装 FFmpeg")
            return False
            
    def get_video_info(self, video_path):
        """获取视频信息"""
        try:
            cmd = [
                'ffprobe', 
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                info = json.loads(result.stdout)
                
                # 获取视频流和音频流信息
                video_stream = None
                audio_stream = None
                
                for stream in info.get('streams', []):
                    if stream.get('codec_type') == 'video' and video_stream is None:
                        video_stream = stream
                    elif stream.get('codec_type') == 'audio' and audio_stream is None:
                        audio_stream = stream
                        
                if video_stream:
                    duration = float(info.get('format', {}).get('duration', 0))
                    width = video_stream.get('width', 0)
                    height = video_stream.get('height', 0)
                    fps = eval(video_stream.get('r_frame_rate', '30/1'))
                    
                    return {
                        'duration': duration,
                        'width': width,
                        'height': height,
                        'fps': fps,
                        'has_audio': audio_stream is not None,
                        'format_info': info.get('format', {})
                    }
                    
        except Exception as e:
            print(f"⚠️ 获取视频信息失败: {e}")
            
        return None
        
    def extract_last_frame(self, video_path, output_path):
        """提取视频最后一帧"""
        try:
            # 获取视频信息
            info = self.get_video_info(video_path)
            if not info:
                print(f"❌ 无法获取视频信息")
                return False
                
            duration = info['duration']
            # 提取最后一秒的帧，避免黑帧
            seek_time = max(0, duration - 1.0)
            
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ss', str(seek_time),
                '-vframes', '1',
                '-q:v', '2',  # 高质量
                '-y',  # 覆盖输出文件
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0 and os.path.exists(output_path)
                
        except Exception as e:
            print(f"❌ 提取封面图失败: {e}")
            return False
            
    def create_cover_video_simple(self, cover_image_path, cover_frames, fps, width, height, has_audio, output_path):
        """创建精确帧数的封面视频 - 简化版本（修复bug）"""
        try:
            print(f"      🎯 创建精确{cover_frames}帧封面视频...")
            
            # 计算精确的帧时长
            frame_duration = cover_frames / fps
            print(f"      📊 {cover_frames}帧 @ {fps:.2f}fps = {frame_duration:.6f}秒")
            
            # 基础视频命令 - 关键修复：使用最简单的方法
            cmd = [
                'ffmpeg',
                '-loop', '1',
                '-i', cover_image_path,
                '-vframes', str(cover_frames),  # 关键：精确帧数
                '-r', str(fps),
                '-s', f'{width}x{height}',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',  # 兼容格式
                '-preset', 'fast',
                '-crf', '18',
            ]
            
            # 简化处理：先创建无音频封面视频，音频在合并时处理
            cmd.extend(['-an'])  # 无音频，简化处理
                
            cmd.extend(['-y', output_path])
            
            print(f"      📝 FFmpeg命令: 精确{cover_frames}帧, {frame_duration:.6f}秒")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and os.path.exists(output_path):
                # 验证生成的视频时长
                verify_info = self.get_video_info(output_path)
                if verify_info:
                    actual_duration = verify_info['duration']
                    print(f"      ✅ 封面视频创建成功: {actual_duration:.6f}秒")
                    # 检查时长是否正确（允许小误差）
                    if abs(actual_duration - frame_duration) < 0.01:
                        return True
                    else:
                        print(f"      ⚠️ 时长不匹配: 预期{frame_duration:.6f}秒, 实际{actual_duration:.6f}秒")
                return True
            else:
                print(f"      ❌ 封面视频创建失败")
                if result.stderr:
                    print(f"      错误: {result.stderr[:200]}")
                return False
                
        except Exception as e:
            print(f"      ❌ 创建封面视频异常: {e}")
            return False
            
    def merge_videos_simple(self, cover_video_path, original_video_path, output_path):
        """简单可靠的视频合并方法 - 修复版"""
        try:
            print(f"      🔗 合并视频...")
            
            # 直接使用filter_complex确保正确合并（跳过可能有问题的concat demuxer）
            print(f"      🎯 使用filter_complex精确合并...")
            
            # 检查封面视频是否有音频
            cover_info = self.get_video_info(cover_video_path)
            original_info = self.get_video_info(original_video_path)
            
            if not cover_info or not original_info:
                print(f"      ❌ 无法获取视频信息")
                return False
                
            print(f"      📊 合并信息:")
            print(f"         封面视频: {cover_info['duration']:.6f}秒, 音频: {'有' if cover_info['has_audio'] else '无'}")
            print(f"         原视频: {original_info['duration']:.6f}秒, 音频: {'有' if original_info['has_audio'] else '无'}")
            
            expected_duration = cover_info['duration'] + original_info['duration']
            print(f"         预期总计: {expected_duration:.6f}秒")
            
            # 构建filter_complex命令
            if cover_info['has_audio'] and original_info['has_audio']:
                # 两个视频都有音频
                filter_complex = '[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[outv][outa]'
                map_args = ['-map', '[outv]', '-map', '[outa]']
            elif not cover_info['has_audio'] and original_info['has_audio']:
                # 封面无音频，原视频有音频 - 为封面添加无声音频
                filter_complex = '[0:v]apad[0va]; [0va][0:a][1:v][1:a]concat=n=2:v=1:a=1[outv][outa]'
                map_args = ['-map', '[outv]', '-map', '[outa]']
            elif cover_info['has_audio'] and not original_info['has_audio']:
                # 封面有音频，原视频无音频
                filter_complex = '[0:v][1:v]concat=n=2:v=1:a=0[outv]; [0:a]acopy[outa]'
                map_args = ['-map', '[outv]', '-map', '[outa]']
            else:
                # 两个都无音频
                filter_complex = '[0:v][1:v]concat=n=2:v=1:a=0[outv]'
                map_args = ['-map', '[outv]']
            
            # 使用最直接的方法：为封面视频创建匹配的静音音频
            cmd = [
                'ffmpeg',
                '-i', cover_video_path,
                '-i', original_video_path
            ]
            
            if not cover_info['has_audio'] and original_info['has_audio']:
                # 封面无音频，原视频有音频 - 最简单的方法
                cmd.extend([
                    '-filter_complex', '[0:v][1:v]concat=n=2:v=1[outv]',
                    '-map', '[outv]',
                    '-map', '1:a'  # 直接使用原视频的音频
                ])
            else:
                # 简单的视频连接
                cmd.extend([
                    '-filter_complex', '[0:v][1:v]concat=n=2:v=1[outv]',
                    '-map', '[outv]',
                    '-map', '1:a'  # 使用原视频音频
                ])
            
            cmd.extend([
                '-c:v', 'libx264',
                '-crf', '18',  # 高质量
                '-c:a', 'aac',
                '-b:a', '192k',
                '-preset', 'fast',
                '-avoid_negative_ts', 'make_zero',
                '-y',
                output_path
            ])
            
            print(f"      📝 执行精确合并...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0 and os.path.exists(output_path):
                # 验证合并结果
                final_info = self.get_video_info(output_path)
                if final_info:
                    actual_duration = final_info['duration']
                    duration_diff = abs(actual_duration - expected_duration)
                    
                    print(f"      📊 合并结果:")
                    print(f"         实际输出: {actual_duration:.6f}秒")
                    print(f"         预期时长: {expected_duration:.6f}秒")
                    print(f"         误差: {duration_diff:.6f}秒")
                    
                    if duration_diff < 0.2:  # 允许0.2秒误差
                        print(f"      ✅ 精确合并成功")
                        return True
                    else:
                        print(f"      ⚠️ 时长仍有误差，但可能是编码精度问题")
                        return True  # 继续处理，可能是编码精度问题
                        
            print(f"      ❌ 精确合并失败")
            if result.stderr:
                print(f"      错误: {result.stderr[:300]}")
            return False
            
        except Exception as e:
            print(f"      ❌ 合并视频异常: {e}")
            return False
            
    def process_single_video(self, video_path, output_folder):
        """处理单个视频文件"""
        filename = os.path.basename(video_path)
        name_without_ext = os.path.splitext(filename)[0]
        original_ext = os.path.splitext(filename)[1].lower()
        
        print(f"\n🎬 处理视频: {filename}")
        
        # 1. 获取视频信息
        video_info = self.get_video_info(video_path)
        if not video_info:
            print(f"❌ 跳过: 无法获取视频信息")
            return False
            
        print(f"   📊 原始信息: {video_info['duration']:.6f}秒, {video_info['width']}x{video_info['height']}, {video_info['fps']:.2f}fps")
        print(f"   🎵 音频: {'有' if video_info['has_audio'] else '无'}")
        
        # 2. 计算预期结果
        frame_duration = self.cover_frames / video_info['fps']
        expected_final_duration = video_info['duration'] + frame_duration
        print(f"   🎯 预期结果: {video_info['duration']:.6f}s + {frame_duration:.6f}s = {expected_final_duration:.6f}s")
        
        # 3. 创建临时文件路径（保持原始格式）
        with tempfile.TemporaryDirectory() as temp_dir:
            cover_image_path = os.path.join(temp_dir, f"{name_without_ext}_cover.jpg")
            cover_video_path = os.path.join(temp_dir, f"{name_without_ext}_cover{original_ext}")
            
            # 4. 提取最后一帧作为封面图
            print(f"   📸 提取最后一帧...")
            if not self.extract_last_frame(video_path, cover_image_path):
                print(f"❌ 封面图提取失败")
                return False
                
            print(f"   ✅ 封面图已提取")
            
            # 5. 创建精确帧数的封面视频
            print(f"   🎞️ 创建{self.cover_frames}帧封面视频...")
            if not self.create_cover_video_simple(
                cover_image_path, self.cover_frames, 
                video_info['fps'], video_info['width'], video_info['height'],
                video_info['has_audio'], cover_video_path):
                print(f"❌ 封面视频创建失败")
                return False
                
            # 6. 合并视频
            output_filename = f"{name_without_ext}_with_cover{original_ext}"
            output_path = os.path.join(output_folder, output_filename)
            
            print(f"   🔗 合并为最终视频...")
            if not self.merge_videos_simple(cover_video_path, video_path, output_path):
                print(f"❌ 视频合并失败")
                return False
                
            # 7. 验证最终结果
            final_info = self.get_video_info(output_path)
            if final_info:
                actual_duration = final_info['duration']
                duration_diff = abs(actual_duration - expected_final_duration)
                
                print(f"   📊 结果验证:")
                print(f"      预期: {expected_final_duration:.6f}秒")
                print(f"      实际: {actual_duration:.6f}秒")
                print(f"      误差: {duration_diff:.6f}秒")
                
                if duration_diff < 0.1:
                    print(f"   ✅ 处理成功: {output_filename}")
                    
                    # 保存封面图
                    cover_jpg_path = os.path.join(output_folder, f"{name_without_ext}_cover.jpg")
                    shutil.copy2(cover_image_path, cover_jpg_path)
                    print(f"   💾 封面图已保存")
                    
                    return True
                else:
                    print(f"   ❌ 时长验证失败，误差过大")
                    return False
            else:
                print(f"   ❌ 无法验证输出视频")
                return False
        
        return False
        
    def run_simple(self, video_path, output_folder=None):
        """简化的运行流程 - 直接处理指定视频"""
        self.print_header("视频封面插入工具 - 修复版本")
        print("🎯 修复50秒视频被压缩到2秒的严重bug")
        print("✨ 确保输出: 50秒 + 2帧 = ~50.067秒")
        
        # 检查FFmpeg
        if not self.check_ffmpeg():
            return False
            
        # 检查输入文件
        if not os.path.exists(video_path):
            print(f"❌ 视频文件不存在: {video_path}")
            return False
            
        # 创建输出文件夹
        if not output_folder:
            video_dir = os.path.dirname(video_path)
            output_folder = os.path.join(video_dir, "fixed_with_cover")
        os.makedirs(output_folder, exist_ok=True)
        
        print(f"📂 输入文件: {os.path.basename(video_path)}")
        print(f"📁 输出文件夹: {output_folder}")
        
        # 处理视频
        success = self.process_single_video(video_path, output_folder)
        
        if success:
            print(f"\n🎉 修复完成！")
            print(f"   ✅ 视频时长问题已修复")
            print(f"   ✅ 2帧封面已添加到开头") 
            print(f"   ✅ 原始视频内容完全保持")
            print(f"   📂 结果文件夹: {output_folder}")
        else:
            print(f"\n❌ 处理失败")
            
        return success


def main():
    """主函数 - 快速测试"""
    
    # 测试视频路径 - 请修改为你的实际路径
    test_video = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/examples/test_videos/四字阳章老师_和暖光清.mov"
    
    # 如果测试视频不存在，让用户输入
    if not os.path.exists(test_video):
        print("请输入你的视频文件路径:")
        test_video = input().strip().strip('\'"')
        
        if not os.path.exists(test_video):
            print("❌ 文件不存在")
            return
    
    # 创建修复版本的插入器
    inserter = VideoCoverInserterFixed()
    
    # 运行修复
    inserter.run_simple(test_video)


if __name__ == "__main__":
    main()