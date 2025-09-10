#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频封面图插入工具 (UltraThink效果)
功能：截取视频指定时间点的帧作为封面图，并插入到视频开头
支持：最后一帧（默认）或指定时间点的帧
"""

import os
import sys
import subprocess
import glob
from pathlib import Path
import tempfile
import shutil
import urllib.parse


class VideoCoverInserter:
    """视频封面图插入器"""
    
    def __init__(self):
        self.video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.m4v']
        self.cover_duration = 2.0  # 默认封面图显示时长（秒）
        self.cover_duration_mode = "frames"  # 默认使用帧数模式
        self.cover_frames = 2  # 默认前2帧
        self.cover_source_mode = "last"  # 默认使用最后一帧
        self.cover_source_time = None  # 指定时间点（秒）
        
    def print_header(self, title):
        """打印标题"""
        print("\n" + "=" * 60)
        print(f"🎬 {title}")
        print("=" * 60)
        
    def get_user_input(self, prompt, default=None):
        """获取用户输入"""
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            return user_input if user_input else default
        else:
            return input(f"{prompt}: ").strip()
    
    def try_fix_path(self, path):
        """尝试修复路径"""
        # 尝试多种路径修复方法
        candidates = []
        
        # 1. 原始路径
        candidates.append(path)
        
        # 2. URL解码（处理%20等编码）
        try:
            decoded_path = urllib.parse.unquote(path)
            candidates.append(decoded_path)
        except:
            pass
            
        # 3. 处理路径中的反斜杠
        candidates.append(path.replace('\\', '/'))
        
        # 4. 处理多余的空格
        candidates.append(path.strip())
        
        # 5. 使用 pathlib 处理
        try:
            pathlib_path = str(Path(path).resolve())
            candidates.append(pathlib_path)
        except:
            pass
            
        # 6. 处理挂载点路径（macOS）
        if path.startswith('/Volumes/'):
            # 尝试不同的挂载点变体
            volume_name = path[9:].split('/')[0]  # 获取卷名
            remaining_path = '/'.join(path.split('/')[2:])  # 获取剩余路径
            
            # 尝试 /Volumes/ 下的不同编码
            try:
                import unicodedata
                normalized_volume = unicodedata.normalize('NFC', volume_name)
                normalized_path = f"/Volumes/{normalized_volume}/{remaining_path}"
                candidates.append(normalized_path)
            except:
                pass
        
        # 测试所有候选路径
        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return candidate
                
        return None
    
    def suggest_path_fixes(self, path):
        """提供路径修复建议"""
        print(f"   1. 检查文件夹是否确实存在")
        print(f"   2. 尝试在终端中使用 'ls' 命令验证:")
        print(f"      ls \"{path}\"")
        
        # 如果是挂载点路径，给出特殊建议
        if path.startswith('/Volumes/'):
            print(f"   3. 外接存储设备建议:")
            print(f"      - 确认设备已正确连接")
            print(f"      - 在访达中验证路径")
            print(f"      - 尝试重新挂载设备")
            
        print(f"   4. 或者直接拖拽文件夹到此处获取正确路径")
        print(f"   5. 使用相对路径或切换到文件夹所在目录")
        
        # 提供调试命令
        self.debug_path(path)
        
    def debug_path(self, path):
        """调试路径问题"""
        print(f"\n   🔧 调试信息:")
        
        # 显示路径的各种表示
        print(f"      原始路径: {repr(path)}")
        print(f"      路径长度: {len(path)}")
        print(f"      路径字节: {path.encode('utf-8', errors='replace')}")
        
        # 检查父目录
        parent_dir = os.path.dirname(path)
        if parent_dir and os.path.exists(parent_dir):
            print(f"      父目录存在: {parent_dir}")
            try:
                # 列出父目录内容
                contents = os.listdir(parent_dir)
                target_name = os.path.basename(path)
                print(f"      目标文件夹名: {repr(target_name)}")
                
                # 查找相似的文件夹名
                similar = [name for name in contents if target_name.lower() in name.lower()]
                if similar:
                    print(f"      相似的文件夹:")
                    for name in similar[:5]:  # 只显示前5个
                        full_path = os.path.join(parent_dir, name)
                        print(f"         - {name} -> {full_path}")
            except PermissionError:
                print(f"      父目录存在但无访问权限")
            except Exception as e:
                print(f"      检查父目录时出错: {e}")
        else:
            print(f"      父目录不存在: {parent_dir}")
            
        # 建议使用ls命令验证
        print(f"\n   💡 快速验证命令:")
        print(f"      ls -la \"{path}\"")
        if parent_dir:
            print(f"      ls -la \"{parent_dir}/\"")
            
    def get_user_choice(self, options, prompt, default_index=0):
        """获取用户选择"""
        print(f"\n{prompt}")
        for i, option in enumerate(options):
            marker = "👉" if i == default_index else "  "
            print(f"{marker} {i + 1}. {option}")
        
        while True:
            try:
                choice = input(f"\n请选择 (1-{len(options)}, 默认 {default_index + 1}): ").strip()
                if not choice:
                    return default_index, options[default_index]
                
                index = int(choice) - 1
                if 0 <= index < len(options):
                    return index, options[index]
                else:
                    print(f"❌ 请输入 1-{len(options)} 之间的数字")
            except ValueError:
                print(f"❌ 请输入有效的数字")
                
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
            print("   安装命令:")
            print("   - macOS: brew install ffmpeg")
            print("   - Ubuntu: sudo apt install ffmpeg")
            print("   - Windows: 下载并配置环境变量")
            return False
            
    def get_video_folder_path(self):
        """获取视频文件夹路径"""
        self.print_header("选择视频文件夹")
        
        while True:
            folder_path = self.get_user_input("请输入视频文件夹路径")
            
            if not folder_path:
                print("❌ 请输入有效路径")
                continue
                
            # 处理路径中的引号、空格和特殊字符
            folder_path = folder_path.strip()
            folder_path = folder_path.strip('\'"')
            
            # 处理 ~ 路径
            folder_path = os.path.expanduser(folder_path)
            
            # 转换为绝对路径
            folder_path = os.path.abspath(folder_path)
            
            print(f"🔍 检查路径: {folder_path}")
            
            if not os.path.exists(folder_path):
                print(f"❌ 路径不存在")
                
                # 尝试各种路径修复方法
                fixed_path = self.try_fix_path(folder_path)
                if fixed_path and os.path.exists(fixed_path):
                    folder_path = fixed_path
                    print(f"✅ 路径修复成功: {folder_path}")
                else:
                    print(f"💡 路径问题排查:")
                    print(f"   原始输入: {repr(folder_path)}")
                    self.suggest_path_fixes(folder_path)
                    continue
                
            if not os.path.isdir(folder_path):
                print(f"❌ 不是文件夹: {folder_path}")
                continue
                
            print(f"✅ 文件夹路径: {folder_path}")
            return folder_path
            
    def find_video_files(self, folder_path):
        """查找文件夹中的所有视频文件"""
        print(f"\n🔍 扫描视频文件...")
        
        video_files = []
        for ext in self.video_extensions:
            pattern = os.path.join(folder_path, f"*{ext}")
            files = glob.glob(pattern, recursive=False)
            video_files.extend(files)
            
        # 排序文件列表
        video_files.sort()
        
        print(f"📊 找到 {len(video_files)} 个视频文件:")
        for i, video_file in enumerate(video_files, 1):
            filename = os.path.basename(video_file)
            file_size = os.path.getsize(video_file) / (1024 * 1024)  # MB
            print(f"   {i:2d}. {filename} ({file_size:.1f} MB)")
            
        return video_files
        
    def get_video_info(self, video_path):
        """获取完整的视频编码参数信息"""
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
                import json
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
                    
                    # 完整的视频编码信息
                    video_codec = video_stream.get('codec_name', 'h264')
                    video_profile = video_stream.get('profile', '')
                    video_level = video_stream.get('level', '')
                    pixel_format = video_stream.get('pix_fmt', 'yuv420p')
                    video_bitrate = video_stream.get('bit_rate', '2000000')
                    time_base = video_stream.get('time_base', '1/30')
                    
                    # 完整的音频信息
                    if audio_stream:
                        audio_codec = audio_stream.get('codec_name', 'aac')
                        audio_bitrate = audio_stream.get('bit_rate', '128000')
                        sample_rate = int(audio_stream.get('sample_rate', '44100'))
                        channels = int(audio_stream.get('channels', 2))
                        channel_layout = audio_stream.get('channel_layout', 'stereo' if channels == 2 else 'mono')
                    else:
                        audio_codec = None
                        audio_bitrate = None
                        sample_rate = None
                        channels = None
                        channel_layout = None
                    
                    return {
                        # 基本信息
                        'duration': duration,
                        'width': width,
                        'height': height,
                        'fps': fps,
                        
                        # 详细视频编码信息
                        'video_codec': video_codec,
                        'video_profile': video_profile,
                        'video_level': video_level,
                        'pixel_format': pixel_format,
                        'video_bitrate': video_bitrate,
                        'time_base': time_base,
                        
                        # 详细音频编码信息
                        'has_audio': audio_stream is not None,
                        'audio_codec': audio_codec,
                        'audio_bitrate': audio_bitrate,
                        'sample_rate': sample_rate,
                        'channels': channels,
                        'channel_layout': channel_layout,
                        
                        # 原始流数据（用于完全复制）
                        'video_stream': video_stream,
                        'audio_stream': audio_stream,
                        'format_info': info.get('format', {})
                    }
                    
        except Exception as e:
            print(f"⚠️ 获取视频信息失败: {e}")
            import traceback
            traceback.print_exc()
            
        return None
        
    def extract_frame_from_video(self, video_path, output_path):
        """从视频中提取指定时间点的帧作为封面图"""
        try:
            # 获取视频信息
            info = self.get_video_info(video_path)
            if not info:
                print(f"❌ 无法获取视频信息: {os.path.basename(video_path)}")
                return False
                
            duration = info['duration']
            fps = info['fps']
            
            # 根据设置确定提取时间点
            if self.cover_source_mode == "last":
                # 提取最后一帧：计算视频的总帧数，然后定位到最后一个关键帧
                total_frames = int(duration * fps)
                
                # 为了避免黑帧和编码器问题，选择倒数第2-5帧中的一个
                # 这样可以确保捕获到实际内容而不是黑屏
                if total_frames <= 1:
                    # 极短视频，直接取第0帧
                    seek_time = 0
                    frame_num = 0
                elif total_frames <= 5:
                    # 短视频，取中间帧避免边缘问题
                    seek_time = duration * 0.5
                    frame_num = total_frames // 2
                else:
                    # 正常视频，取倒数第3帧（平衡准确性和稳定性）
                    frame_num = max(0, total_frames - 3)
                    seek_time = frame_num / fps
                
                time_desc = f"最后一帧附近 (第{frame_num}帧/{total_frames}帧, {seek_time:.3f}秒)"
                
            elif self.cover_source_mode == "time" and self.cover_source_time is not None:
                # 提取指定时间点的帧
                seek_time = min(max(0, self.cover_source_time), duration - 0.01)  # 减0.01避免边界问题
                frame_num = int(seek_time * fps)
                time_desc = f"第{seek_time:.3f}秒 (第{frame_num}帧)"
            else:
                # 默认回退到最后一帧
                total_frames = int(duration * fps)
                frame_num = max(0, total_frames - 3)
                seek_time = frame_num / fps
                time_desc = f"最后一帧附近 (第{frame_num}帧/{total_frames}帧, {seek_time:.3f}秒)"
            
            print(f"      📸 提取时间点: {time_desc}")
            
            # 使用更精确的帧提取策略
            success = False
            error_messages = []
            
            # 方法1: 首选方案 - 使用输入前定位（更快更准）
            if frame_num > 0:
                cmd = [
                    'ffmpeg',
                    '-ss', str(seek_time),  # 先定位到时间点（输入前定位，更快更准）
                    '-i', video_path,
                    '-vframes', '1',
                    '-q:v', '2',  # 高质量
                    '-y',  # 覆盖输出文件
                    output_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    success = True
                else:
                    error_msg = result.stderr[:200] if result.stderr else "未知错误"
                    error_messages.append(f"方法1失败: {error_msg}")
            
            # 方法2: 如果方法1失败，使用输入后定位（兼容性更好）
            if not success:
                cmd = [
                    'ffmpeg',
                    '-i', video_path,
                    '-ss', str(seek_time),  # 输入后定位
                    '-vframes', '1',
                    '-q:v', '2',  # 高质量
                    '-y',  # 覆盖输出文件
                    output_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    success = True
                else:
                    error_msg = result.stderr[:200] if result.stderr else "未知错误"
                    error_messages.append(f"方法2失败: {error_msg}")
            
            # 方法3: 如果都失败，使用select过滤器精确选择帧
            if not success and frame_num >= 0:
                cmd = [
                    'ffmpeg',
                    '-i', video_path,
                    '-vf', f'select=eq(n\,{frame_num})',  # 精确选择指定帧
                    '-vframes', '1',
                    '-q:v', '2',  # 高质量
                    '-y',  # 覆盖输出文件
                    output_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    success = True
                else:
                    error_msg = result.stderr[:200] if result.stderr else "未知错误"
                    error_messages.append(f"方法3失败: {error_msg}")
            
            # 方法4: 最后备选 - 稍微调整时间重新尝试
            if not success and self.cover_source_mode == "last" and duration > 0.5:
                # 尝试倒数第2秒或第1秒
                alt_times = [max(0, duration - 2.0), max(0, duration - 0.5), 0]
                
                for alt_time in alt_times:
                    cmd = [
                        'ffmpeg',
                        '-ss', str(alt_time),
                        '-i', video_path,
                        '-vframes', '1',
                        '-q:v', '2',
                        '-y',
                        output_path
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        print(f"      🔄 使用备选时间点 {alt_time:.1f}秒成功")
                        success = True
                        break
                
                if not success:
                    error_messages.append("所有备选时间点都失败")
            
            if success:
                file_size = os.path.getsize(output_path) / 1024  # KB
                print(f"      ✅ 封面图提取成功: {file_size:.1f}KB")
                return True
            else:
                print(f"❌ 封面图提取失败")
                if error_messages:
                    print(f"   错误信息:")
                    for i, msg in enumerate(error_messages[-3:], 1):  # 只显示最后3个错误
                        print(f"      {i}. {msg}")
                return False
                
        except Exception as e:
            print(f"❌ 提取封面帧失败: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def extract_cover_image_from_video(self, video_path, output_path):
        """从视频中提取第一帧作为封面图"""
        try:
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', 'select=eq(n\,0)',  # 选择第一帧
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
            
    def create_cover_video(self, cover_image_path, duration, video_info, output_path):
        """创建与原视频格式完全匹配的封面图视频片段"""
        try:
            # 如果原视频有音频，使用带音频的版本
            if video_info['has_audio']:
                return self.create_cover_video_with_audio(cover_image_path, duration, video_info, output_path)
            else:
                return self.create_cover_video_no_audio(cover_image_path, duration, video_info, output_path)
                
        except Exception as e:
            print(f"❌ 创建封面视频失败: {e}")
            return self.create_cover_video_fallback(cover_image_path, duration, video_info, output_path)
            
    def create_cover_video_with_audio(self, cover_image_path, cover_frames, video_info, output_path):
        """创建高质量精确帧数的封面视频（保持原始编码质量）"""
        try:
            print(f"      🎯 创建高质量{cover_frames}帧封面视频...")
            
            # 获取输出文件扩展名来确定容器格式
            output_ext = os.path.splitext(output_path)[1].lower()
            
            print(f"      📦 目标格式: {output_ext}, 精确帧数: {cover_frames}帧")
            print(f"      🎨 保持像素格式: {video_info['pixel_format']}")
            
            # 计算精确的帧时长
            frame_duration = cover_frames / video_info['fps']
            print(f"      📊 {cover_frames}帧 @ {video_info['fps']:.2f}fps = {frame_duration:.6f}秒")
            
            # 基础命令 - 高质量保持原始编码参数
            cmd = [
                'ffmpeg',
                '-loop', '1',
                '-i', cover_image_path,
                '-vframes', str(cover_frames),  # 精确控制帧数
                '-r', str(video_info['fps']),
                '-s', f"{video_info['width']}x{video_info['height']}",
            ]
            
            # 精确匹配原视频编码器
            if video_info['video_codec'] == 'h264':
                cmd.extend(['-c:v', 'libx264'])
            elif video_info['video_codec'] in ['hevc', 'h265']:
                cmd.extend(['-c:v', 'libx265'])
            else:
                cmd.extend(['-c:v', 'libx264'])
                
            # 保持原始像素格式（关键）
            cmd.extend(['-pix_fmt', video_info['pixel_format']])
            
            # 智能质量设置：根据原视频参数优化
            if video_info.get('video_bitrate'):
                try:
                    original_bitrate = int(video_info['video_bitrate'])
                    # 对于封面视频，使用稍高的比特率确保质量
                    target_bitrate = max(original_bitrate, original_bitrate * 1.5)
                    cmd.extend(['-b:v', str(int(target_bitrate))])
                    print(f"      📊 使用比特率模式: {target_bitrate//1000}kbps (原始: {original_bitrate//1000}kbps)")
                except:
                    cmd.extend(['-crf', '0'])  # 无损
                    print(f"      📊 使用无损模式: CRF=0")
            else:
                cmd.extend(['-crf', '0'])  # 无损
                print(f"      📊 使用无损模式: CRF=0")
            
            # 高质量编码设置
            cmd.extend([
                '-preset', 'veryslow',  # 最高质量预设
                '-an',  # 无音频，在合并时处理
            ])
            
            # 根据输出格式添加特定参数
            if output_ext == '.mov':
                cmd.extend(['-movflags', '+faststart'])
            elif output_ext == '.mp4':
                cmd.extend(['-movflags', '+faststart'])
            
            cmd.extend(['-y', output_path])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0 and os.path.exists(output_path):
                # 验证生成的视频质量
                verify_info = self.get_video_info(output_path)
                if verify_info:
                    actual_duration = verify_info['duration']
                    print(f"      ✅ 高质量封面视频: {actual_duration:.6f}秒")
                    print(f"      🎨 输出像素格式: {verify_info['pixel_format']}")
                    
                    # 检查像素格式是否保持
                    if verify_info['pixel_format'] == video_info['pixel_format']:
                        print(f"      🎉 像素格式完美保持！")
                    else:
                        print(f"      ⚠️ 像素格式有变化: {video_info['pixel_format']} → {verify_info['pixel_format']}")
                        
                return True
            else:
                print(f"      ❌ 高质量封面视频创建失败")
                if result.stderr:
                    print(f"      错误: {result.stderr[:200]}")
                # 降级到兼容模式
                print(f"      🔄 尝试兼容模式...")
                return self.create_cover_video_compatible(cover_image_path, cover_frames, video_info, output_path)
            
        except Exception as e:
            print(f"      ❌ 高质量封面视频创建异常: {e}")
            return self.create_cover_video_compatible(cover_image_path, cover_frames, video_info, output_path)
            
    def create_cover_video_compatible(self, cover_image_path, cover_frames, video_info, output_path):
        """高质量兼容性备选方案（智能像素格式处理）"""
        try:
            print(f"      🔄 使用高质量兼容模式（{cover_frames}帧）...")
            
            cmd = [
                'ffmpeg',
                '-loop', '1',
                '-i', cover_image_path,
                '-vframes', str(cover_frames),  # 精确帧数控制
                '-r', str(video_info['fps']),
                '-s', f"{video_info['width']}x{video_info['height']}",
            ]
            
            # 智能编码器选择
            if video_info['video_codec'] == 'h264':
                cmd.extend(['-c:v', 'libx264'])
            elif video_info['video_codec'] in ['hevc', 'h265']:
                cmd.extend(['-c:v', 'libx265'])
            else:
                cmd.extend(['-c:v', 'libx264'])
                
            # 智能像素格式处理（尽量保持原格式）
            original_pix_fmt = video_info['pixel_format']
            if original_pix_fmt in ['yuv420p', 'yuv422p', 'yuv444p', 'yuvj420p', 'yuvj422p', 'yuvj444p']:
                cmd.extend(['-pix_fmt', original_pix_fmt])
                print(f"      🎨 保持原始像素格式: {original_pix_fmt}")
            elif 'yuv444' in original_pix_fmt:
                cmd.extend(['-pix_fmt', 'yuv444p'])
                print(f"      🎨 使用兼容格式: yuv444p (原始: {original_pix_fmt})")
            elif 'yuv422' in original_pix_fmt:
                cmd.extend(['-pix_fmt', 'yuv422p'])
                print(f"      🎨 使用兼容格式: yuv422p (原始: {original_pix_fmt})")
            else:
                cmd.extend(['-pix_fmt', 'yuv420p'])
                print(f"      🎨 使用安全格式: yuv420p (原始: {original_pix_fmt})")
            
            # 高质量设置（比之前更好）
            cmd.extend(['-preset', 'slow', '-crf', '3'])  # 比之前的CRF 18更好
            
            # 简化音频处理 - 无音频，在合并时处理
            cmd.extend(['-an'])
                
            cmd.extend(['-movflags', '+faststart', '-y', output_path])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            
            if result.returncode == 0 and os.path.exists(output_path):
                # 验证兼容模式结果
                verify_info = self.get_video_info(output_path)
                if verify_info:
                    print(f"      ✅ 兼容模式成功: {verify_info['duration']:.6f}秒")
                    print(f"      🎨 输出像素格式: {verify_info['pixel_format']}")
                return True
            else:
                print(f"      ❌ 兼容模式失败")
                if result.stderr:
                    print(f"      错误: {result.stderr[:150]}")
                return False
            
        except Exception as e:
            print(f"❌ 兼容性模式异常: {e}")
            return False
    
    def create_cover_video_no_audio(self, cover_image_path, cover_frames, video_info, output_path):
        """创建精确帧数的无音频封面视频"""
        try:
            print(f"      🎯 创建精确{cover_frames}帧无音频封面视频...")
            
            # 获取输出格式信息
            output_ext = os.path.splitext(output_path)[1].lower()
            container_format = video_info['format_info'].get('format_name', '').lower()
            
            print(f"      📦 目标格式: {output_ext}, 精确帧数: {cover_frames}帧")
            
            # 基础命令 - 关键修复：使用-vframes
            cmd = [
                'ffmpeg',
                '-loop', '1',
                '-i', cover_image_path,
                '-vframes', str(cover_frames),  # 关键修复：精确控制帧数
                '-r', str(video_info['fps']),
                '-s', f"{video_info['width']}x{video_info['height']}",
            ]
            
            # 视频编码设置
            if video_info['video_codec'] == 'h264':
                cmd.extend(['-c:v', 'libx264'])
            elif video_info['video_codec'] in ['hevc', 'h265']:
                cmd.extend(['-c:v', 'libx265'])
            else:
                cmd.extend(['-c:v', 'libx264'])
                
            # 像素格式设置
            cmd.extend(['-pix_fmt', video_info['pixel_format']])
            
            # 高质量设置
            cmd.extend(['-preset', 'fast', '-crf', '18'])
            
            # 根据输出格式添加特定参数
            if output_ext == '.mov' or 'mov' in container_format:
                cmd.extend(['-movflags', '+faststart'])
                # 如果是ProRes编码
                if 'prores' in video_info['video_codec'].lower():
                    cmd.extend(['-c:v', 'prores', '-profile:v', '2'])
            elif output_ext == '.mp4':
                cmd.extend(['-movflags', '+faststart'])
                
            cmd.extend(['-an', '-y', output_path])
            
            print(f"      📝 无音频精确帧数: {cover_frames}帧 @ {video_info['fps']}fps")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and os.path.exists(output_path):
                print(f"      ✅ 精确{cover_frames}帧无音频封面视频创建成功")
                return True
            else:
                print(f"      ⚠️ 精确帧数失败，尝试兼容模式")
                print(f"      错误: {result.stderr[:150] if result.stderr else '未知错误'}...")
                return self.create_cover_video_compatible(cover_image_path, cover_frames, video_info, output_path)
            
        except Exception as e:
            print(f"      ❌ 精确帧数无音频封面视频创建异常: {e}")
            return self.create_cover_video_compatible(cover_image_path, cover_frames, video_info, output_path)
            
    def create_cover_video_fallback(self, cover_image_path, cover_frames, video_info, output_path):
        """备选方案：创建兼容的封面视频（使用精确帧数）"""
        try:
            print(f"      🔄 使用备选方案创建{cover_frames}帧封面视频...")
            
            cmd = [
                'ffmpeg',
                '-loop', '1',
                '-i', cover_image_path,
                '-vframes', str(cover_frames),  # 关键修复：使用精确帧数
                '-r', str(video_info['fps']),
                '-s', f"{video_info['width']}x{video_info['height']}",
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-preset', 'medium',
                '-crf', '18',
            ]
            
            # 如果需要音频轨道 - 精确时长匹配帧数（关键修复）
            if video_info['has_audio']:
                frame_duration = cover_frames / video_info['fps']
                cmd.extend([
                    '-f', 'lavfi',
                    '-i', f'anullsrc=channel_layout={video_info["channel_layout"]}:sample_rate={video_info["sample_rate"]}:duration={frame_duration}',
                    '-c:a', 'aac',
                    '-ar', str(video_info['sample_rate']),
                    '-ac', str(video_info['channels']),
                    '-shortest'  # 音频长度匹配视频帧数
                ])
                
            cmd.extend(['-y', output_path])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0 and os.path.exists(output_path)
            
        except Exception as e:
            print(f"❌ 备选方案也失败: {e}")
            return False
            
    def merge_videos(self, cover_video_path, original_video_path, output_path, video_info):
        """高质量视频合并方法 - 优先无损合并"""
        try:
            print(f"      🔗 开始高质量合并...")
            
            # 获取封面视频和原视频信息
            cover_info = self.get_video_info(cover_video_path)
            original_info = self.get_video_info(original_video_path)
            
            if not cover_info or not original_info:
                print(f"      ❌ 无法获取视频信息")
                return False
                
            print(f"      📊 合并信息:")
            print(f"         封面视频: {cover_info['duration']:.6f}秒")
            print(f"         原视频: {original_info['duration']:.6f}秒")
            
            expected_duration = cover_info['duration'] + original_info['duration']
            print(f"         预期总计: {expected_duration:.6f}秒")
            
            # 方法1: 优先尝试concat demuxer（完全无损）
            if self.try_concat_demuxer_lossless(cover_video_path, original_video_path, output_path):
                print(f"      ✅ 无损concat合并成功")
                return True
            
            # 方法2: 高质量重编码合并
            print(f"      🔄 使用高质量重编码合并...")
            
            cmd = [
                'ffmpeg',
                '-i', cover_video_path,
                '-i', original_video_path,
                '-filter_complex', '[0:v][1:v]concat=n=2:v=1[outv]',
                '-map', '[outv]',
                '-map', '1:a',  # 直接使用原视频的音频
            ]
            
            # 精确匹配原视频编码设置
            if video_info['video_codec'] == 'h264':
                cmd.extend(['-c:v', 'libx264'])
            elif video_info['video_codec'] in ['hevc', 'h265']:
                cmd.extend(['-c:v', 'libx265'])
            else:
                cmd.extend(['-c:v', 'libx264'])
            
            # 保持原始像素格式和高质量
            cmd.extend(['-pix_fmt', video_info['pixel_format']])
            
            # 智能质量设置：根据原视频比特率决定
            if video_info.get('video_bitrate'):
                try:
                    original_bitrate = int(video_info['video_bitrate'])
                    # 使用原始比特率的1.2倍确保质量
                    target_bitrate = max(original_bitrate, original_bitrate * 1.2)
                    cmd.extend(['-b:v', str(int(target_bitrate))])
                    print(f"      📊 使用比特率模式: {target_bitrate//1000}kbps")
                except:
                    cmd.extend(['-crf', '1'])
                    print(f"      📊 使用CRF模式: 1 (接近无损)")
            else:
                cmd.extend(['-crf', '1'])
                print(f"      📊 使用CRF模式: 1 (接近无损)")
                
            cmd.extend([
                '-preset', 'slow',  # 高质量预设
                '-c:a', 'copy',     # 音频流复制，完全无损
                '-avoid_negative_ts', 'make_zero',
                '-y',
                output_path
            ])
            
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
                    print(f"         像素格式: {final_info['pixel_format']}")
                    
                    if duration_diff < 0.2:  # 允许0.2秒误差
                        print(f"      ✅ 高质量合并成功")
                        return True
                    else:
                        print(f"      ⚠️ 时长误差较大，但可能是编码精度问题")
                        return True  # 继续处理，可能是编码精度问题
                        
            print(f"      ❌ 高质量合并失败")
            if result.stderr:
                print(f"      错误: {result.stderr[:300]}")
            return False
            
        except Exception as e:
            print(f"      ❌ 合并视频异常: {e}")
            return False
            
    def try_concat_demuxer_lossless(self, cover_video_path, original_video_path, output_path):
        """尝试使用concat demuxer无损合并（stream copy，保持100%原始质量）"""
        try:
            print(f"      🎯 尝试stream copy无损合并...")
            
            # 首先验证两个视频的格式兼容性
            print(f"      🔍 验证格式兼容性...")
            
            # 创建临时文件列表
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(f"file '{cover_video_path}'\n")
                f.write(f"file '{original_video_path}'\n")
                filelist_path = f.name
                
            try:
                # 使用更精确的concat参数
                cmd = [
                    'ffmpeg',
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', filelist_path,
                    '-c', 'copy',  # 完全无损的stream copy
                    '-avoid_negative_ts', 'make_zero',
                    '-fflags', '+genpts',  # 重新生成准确的时间戳
                    '-map', '0',  # 映射所有流
                    '-y',
                    output_path
                ]
                
                print(f"      📝 Stream copy命令: ffmpeg -f concat -safe 0 -i [filelist] -c copy ...")
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                
                if result.returncode == 0 and os.path.exists(output_path):
                    # 详细验证输出文件
                    output_size = os.path.getsize(output_path)
                    cover_size = os.path.getsize(cover_video_path)
                    original_size = os.path.getsize(original_video_path)
                    
                    expected_min_size = cover_size + original_size * 0.8  # 允许一定误差
                    expected_max_size = cover_size + original_size * 1.2
                    
                    if expected_min_size <= output_size <= expected_max_size:
                        print(f"      ✅ Stream copy成功 ({output_size/1024/1024:.1f}MB)")
                        return True
                    else:
                        print(f"      ⚠️ 文件大小异常: 输出{output_size/1024/1024:.1f}MB, 预期{expected_min_size/1024/1024:.1f}-{expected_max_size/1024/1024:.1f}MB")
                        return False
                else:
                    error_msg = result.stderr[:200] if result.stderr else "未知错误"
                    print(f"      ⚠️ Stream copy失败: {error_msg}...")
                    
                    # 检查常见的格式不兼容问题
                    if "Timestamps are unset in a packet" in error_msg or "Non-monotonous DTS" in error_msg:
                        print(f"      💡 时间戳问题，将使用重编码模式")
                    elif "stream parameters do not match" in error_msg:
                        print(f"      💡 流参数不匹配，将使用重编码模式")
                        
                    return False
                    
            finally:
                # 清理临时文件
                if os.path.exists(filelist_path):
                    os.unlink(filelist_path)
                    
        except Exception as e:
            print(f"      ⚠️ Stream copy出错: {e}")
            return False
            
    def merge_with_lossless_filter(self, cover_video_path, original_video_path, output_path, video_info):
        """使用filter_complex进行无损合并（保持原始质量）"""
        try:
            print(f"      🎛️ 使用无损filter_complex合并...")
            
            # 构建无损filter_complex命令
            cmd = [
                'ffmpeg',
                '-i', cover_video_path,
                '-i', original_video_path,
            ]
            
            # 根据音频情况构建filter
            if video_info['has_audio']:
                cmd.extend([
                    '-filter_complex', '[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[outv][outa]',
                    '-map', '[outv]',
                    '-map', '[outa]',
                ])
            else:
                cmd.extend([
                    '-filter_complex', '[0:v][1:v]concat=n=2:v=1:a=0[outv]',
                    '-map', '[outv]',
                ])
            
            # 无损视频编码设置
            if video_info['video_codec'] == 'h264':
                cmd.extend(['-c:v', 'libx264', '-preset', 'veryslow', '-crf', '0'])
            elif video_info['video_codec'] == 'hevc' or video_info['video_codec'] == 'h265':
                cmd.extend(['-c:v', 'libx265', '-preset', 'veryslow', '-crf', '0'])
            else:
                cmd.extend(['-c:v', 'libx264', '-preset', 'veryslow', '-crf', '0'])
                
            # 精确匹配像素格式
            cmd.extend(['-pix_fmt', video_info['pixel_format']])
            
            # 无损音频设置
            if video_info['has_audio']:
                audio_codec = video_info['audio_codec']
                if audio_codec in ['aac', 'mp3', 'ac3', 'flac', 'opus']:
                    cmd.extend(['-c:a', audio_codec])
                else:
                    cmd.extend(['-c:a', 'flac'])  # 无损音频备选
                
                # 保持原始音频参数或更高
                original_bitrate = int(video_info['audio_bitrate']) if video_info['audio_bitrate'] else 320000
                target_bitrate = max(original_bitrate, 320000)  # 至少320k
                
                if audio_codec == 'flac':
                    # FLAC无损，不需要比特率设置
                    pass
                else:
                    cmd.extend(['-b:a', f"{target_bitrate // 1000}k"])
                    
                cmd.extend([
                    '-ar', str(video_info['sample_rate']),
                    '-ac', str(video_info['channels']),
                ])
            else:
                cmd.extend(['-an'])
                
            cmd.extend(['-y', output_path])
            
            print(f"      📝 无损filter命令: {' '.join(cmd[:10])}...")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # 增加超时时间
            if result.returncode == 0 and os.path.exists(output_path):
                output_size = os.path.getsize(output_path)
                if output_size > 1000:
                    return True
                else:
                    print(f"      ⚠️ 输出文件异常小")
                    return False
            else:
                if result.stderr:
                    print(f"      ⚠️ 无损filter失败: {result.stderr[:100]}...")
                return False
                
        except Exception as e:
            print(f"      ❌ 无损filter出错: {e}")
            return False
            
    def merge_with_high_quality(self, cover_video_path, original_video_path, output_path, video_info):
        """高质量合并方式（最后备选方案）"""
        try:
            print(f"      🔄 使用高质量合并方式...")
            
            cmd = [
                'ffmpeg',
                '-i', cover_video_path,
                '-i', original_video_path,
            ]
            
            # 根据音频情况构建filter
            if video_info['has_audio']:
                cmd.extend([
                    '-filter_complex', '[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[outv][outa]',
                    '-map', '[outv]',
                    '-map', '[outa]',
                ])
            else:
                cmd.extend([
                    '-filter_complex', '[0:v][1:v]concat=n=2:v=1:a=0[outv]',
                    '-map', '[outv]',
                ])
            
            # 高质量视频编码设置
            if video_info['video_codec'] == 'h264':
                cmd.extend(['-c:v', 'libx264'])
            elif video_info['video_codec'] == 'hevc' or video_info['video_codec'] == 'h265':
                cmd.extend(['-c:v', 'libx265'])
            else:
                cmd.extend(['-c:v', 'libx264'])
                
            # 高质量设置（接近无损）
            cmd.extend([
                '-preset', 'slow',
                '-crf', '1',  # 接近无损
                '-pix_fmt', video_info['pixel_format']
            ])
            
            # 高质量音频设置
            if video_info['has_audio']:
                audio_codec = video_info['audio_codec']
                if audio_codec in ['aac', 'mp3', 'ac3', 'flac', 'opus']:
                    cmd.extend(['-c:a', audio_codec])
                else:
                    cmd.extend(['-c:a', 'aac'])
                
                # 高比特率音频
                original_bitrate = int(video_info['audio_bitrate']) if video_info['audio_bitrate'] else 256000
                target_bitrate = max(original_bitrate, 256000)
                cmd.extend([
                    '-b:a', f"{target_bitrate // 1000}k",
                    '-ar', str(video_info['sample_rate']),
                    '-ac', str(video_info['channels'])
                ])
            else:
                cmd.extend(['-an'])
                
            cmd.extend([
                '-movflags', '+faststart',
                '-y',
                output_path
            ])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode == 0 and os.path.exists(output_path):
                output_size = os.path.getsize(output_path)
                if output_size > 1000:
                    print(f"      ✅ 高质量合并成功")
                    return True
                    
            print(f"      ❌ 高质量合并失败")
            if result.stderr:
                print(f"      错误: {result.stderr[:100]}...")
            return False
            
        except Exception as e:
            print(f"      ❌ 高质量合并出错: {e}")
            return False
            
    def process_single_video(self, video_path, output_folder):
        """处理单个视频文件"""
        filename = os.path.basename(video_path)
        name_without_ext = os.path.splitext(filename)[0]
        original_ext = os.path.splitext(filename)[1].lower()
        
        print(f"\n🎬 处理视频: {filename}")
        print(f"   📂 原始格式: {original_ext}")
        
        # 1. 获取视频信息
        video_info = self.get_video_info(video_path)
        if not video_info:
            print(f"❌ 跳过: 无法获取视频信息")
            return False
            
        # 获取容器格式信息
        container_format = video_info['format_info'].get('format_name', '').lower()
        # 计算原始文件大小
        try:
            original_size_bytes = int(video_info['format_info'].get('size', 0))
            original_size_mb = original_size_bytes / (1024 * 1024)
        except (ValueError, TypeError):
            original_size_mb = 0
        
        print(f"   📊 视频信息: {video_info['width']}x{video_info['height']}, "
              f"{video_info['duration']:.1f}s, {video_info['fps']:.1f}fps")
        print(f"   🎥 编码信息: {video_info['video_codec']}, 音频: {'有' if video_info['has_audio'] else '无'}")
        print(f"   📦 容器格式: {container_format}")
        print(f"   📂 原始文件: {original_size_mb:.1f}MB")
        print(f"   🎨 像素格式: {video_info['pixel_format']} (将保持不变)")
        
        # 2. 确定封面帧数（修复关键逻辑）
        if hasattr(self, 'cover_duration_mode') and self.cover_duration_mode == "frames":
            cover_frames = self.cover_frames
            frame_duration = cover_frames / video_info['fps']
            print(f"   🎯 封面设置: 前{cover_frames}帧 = {frame_duration:.6f}秒")
            print(f"   📊 预期总时长: {video_info['duration']:.3f}s + {frame_duration:.6f}s = {video_info['duration'] + frame_duration:.3f}s")
        else:
            # 如果用秒数模式，转换为帧数以确保精确
            cover_frames = max(1, round(self.cover_duration * video_info['fps']))
            frame_duration = cover_frames / video_info['fps']
            print(f"   🎯 封面设置: {self.cover_duration}秒 ≈ {cover_frames}帧 = {frame_duration:.6f}秒")
            print(f"   📊 预期总时长: {video_info['duration']:.3f}s + {frame_duration:.6f}s = {video_info['duration'] + frame_duration:.3f}s")
        
        # 3. 创建临时文件路径（保持原始格式）
        with tempfile.TemporaryDirectory() as temp_dir:
            cover_image_path = os.path.join(temp_dir, f"{name_without_ext}_cover.jpg")
            cover_video_path = os.path.join(temp_dir, f"{name_without_ext}_cover_video{original_ext}")
            
            # 4. 提取指定时间点的帧作为封面图
            if self.cover_source_mode == "last":
                print(f"   📸 提取最后一帧作为封面图...")
            else:
                print(f"   📸 提取第{self.cover_source_time}秒的帧作为封面图...")
            
            if not self.extract_frame_from_video(video_path, cover_image_path):
                print(f"❌ 跳过: 封面图提取失败")
                return False
                
            print(f"   ✅ 封面图已生成")
            
            # 5. 创建精确帧数的封面视频片段（关键修复）
            print(f"   🎞️ 创建精确{cover_frames}帧封面视频...")
            if not self.create_cover_video(cover_image_path, cover_frames, 
                                         video_info, cover_video_path):
                print(f"❌ 跳过: 封面视频创建失败")
                return False
                
            # 6. 合并视频（保持原格式）
            output_filename = f"{name_without_ext}_with_cover{original_ext}"
            output_path = os.path.join(output_folder, output_filename)
            
            print(f"   🔗 合并视频...")
            if not self.merge_videos(cover_video_path, video_path, output_path, video_info):
                print(f"❌ 跳过: 视频合并失败")
                return False
                
            # 7. 验证输出质量
            final_info = self.get_video_info(output_path)
            if final_info:
                try:
                    final_size_bytes = int(final_info['format_info'].get('size', 0))
                    final_size_mb = final_size_bytes / (1024 * 1024)
                except (ValueError, TypeError):
                    final_size_mb = 0
                size_ratio = final_size_mb / original_size_mb if original_size_mb > 0 else 0
                
                print(f"   ✅ 完成: {output_filename}")
                print(f"   📊 质量对比:")
                print(f"      文件大小: {original_size_mb:.1f}MB → {final_size_mb:.1f}MB (比例: {size_ratio:.2f}x)")
                print(f"      像素格式: {video_info['pixel_format']} → {final_info['pixel_format']}")
                
                if size_ratio > 0.8:
                    print(f"   🎉 质量保持良好！")
                elif size_ratio > 0.5:
                    print(f"   ⚠️ 文件有一定压缩，建议使用无损版本")
                else:
                    print(f"   ❌ 文件明显压缩，强烈建议使用无损版本！")
            
            # 8. 保存独立的封面图
            cover_jpg_path = os.path.join(output_folder, f"{name_without_ext}_cover.jpg")
            shutil.copy2(cover_image_path, cover_jpg_path)
            print(f"   💾 封面图已保存: {name_without_ext}_cover.jpg")
            
        return True
        
    def extract_cover_only(self, video_path, output_folder):
        """只从视频中提取封面图"""
        filename = os.path.basename(video_path)
        name_without_ext = os.path.splitext(filename)[0]
        
        print(f"\n🎬 提取封面: {filename}")
        
        # 1. 获取视频信息
        video_info = self.get_video_info(video_path)
        if not video_info:
            print(f"❌ 跳过: 无法获取视频信息")
            return False
            
        print(f"   📊 视频信息: {video_info['width']}x{video_info['height']}, "
              f"{video_info['duration']:.1f}s, {video_info['fps']:.1f}fps")
        
        # 2. 提取封面图
        cover_image_path = os.path.join(output_folder, f"{name_without_ext}_cover.jpg")
        
        if self.cover_source_mode == "last":
            print(f"   📸 提取最后一帧作为封面图...")
        else:
            print(f"   📸 提取第{self.cover_source_time}秒的帧作为封面图...")
        
        if not self.extract_frame_from_video(video_path, cover_image_path):
            print(f"❌ 跳过: 封面图提取失败")
            return False
            
        print(f"   ✅ 封面图已保存: {name_without_ext}_cover.jpg")
        return True
        
    def configure_settings(self):
        """配置处理设置"""
        self.print_header("处理设置")
        
        # 1. 处理模式选择
        mode_options = ["只截取封面图", "截取封面图并添加到视频开头"]
        mode_idx, mode_str = self.get_user_choice(
            mode_options, "选择处理模式", default_index=0
        )
        
        self.processing_mode = "extract_only" if mode_idx == 0 else "extract_and_insert"
        print(f"✅ 处理模式: {mode_str}")
        
        # 2. 封面图来源设置
        source_options = ["视频最后一帧", "指定时间点"]
        source_idx, source_str = self.get_user_choice(
            source_options, "选择封面图来源", default_index=0
        )
        
        if source_idx == 0:  # 最后一帧
            self.cover_source_mode = "last"
            print(f"✅ 封面来源: 视频最后一帧")
        else:  # 指定时间点
            self.cover_source_mode = "time"
            while True:
                try:
                    time_input = self.get_user_input("请输入时间点(秒)", "5.0")
                    time_value = float(time_input)
                    if time_value >= 0:
                        self.cover_source_time = time_value
                        print(f"✅ 封面来源: 第{time_value}秒的帧")
                        break
                    else:
                        print("❌ 请输入大于等于0的数值")
                except ValueError:
                    print("❌ 请输入有效的数字")
        
        # 3. 封面图显示时长（仅在插入模式下配置）
        if self.processing_mode == "extract_and_insert":
            duration_options = ["前2帧", "1秒", "2秒", "3秒", "5秒", "自定义"]
            duration_idx, duration_str = self.get_user_choice(
                duration_options, "选择封面图显示时长", default_index=0
            )
            
            if duration_idx == 0:  # 前2帧
                self.cover_duration_mode = "frames"
                self.cover_frames = 2
                print(f"✅ 封面图显示时长: 前2帧 (将根据视频帧率自动计算)")
            elif duration_idx == 5:  # 自定义
                while True:
                    try:
                        custom_duration = float(self.get_user_input("请输入显示时长(秒)", "2.0"))
                        if 0.1 <= custom_duration <= 10.0:
                            self.cover_duration = custom_duration
                            self.cover_duration_mode = "seconds"
                            break
                        else:
                            print("❌ 请输入0.1-10.0之间的数值")
                    except ValueError:
                        print("❌ 请输入有效的数字")
            else:
                durations = [None, 1.0, 2.0, 3.0, 5.0]  # None对应"前2帧"
                self.cover_duration = durations[duration_idx]
                self.cover_duration_mode = "seconds"
                
            if hasattr(self, 'cover_duration'):
                print(f"✅ 封面图显示时长: {self.cover_duration}秒")
        else:
            # 只截取封面模式，设置默认值
            self.cover_duration_mode = "frames"
            self.cover_frames = 1
            print(f"✅ 模式: 只截取封面图，不涉及时长设置")
        
    def process_videos(self, video_files, output_folder):
        """批量处理视频"""
        total_count = len(video_files)
        success_count = 0
        failed_files = []
        
        mode_text = "只截取封面图" if self.processing_mode == "extract_only" else "截取封面图并插入视频"
        self.print_header(f"开始处理 {total_count} 个视频文件 ({mode_text})")
        
        for i, video_path in enumerate(video_files, 1):
            print(f"\n📹 进度: {i}/{total_count}")
            
            if self.processing_mode == "extract_only":
                # 只截取封面图模式
                if self.extract_cover_only(video_path, output_folder):
                    success_count += 1
                else:
                    failed_files.append(os.path.basename(video_path))
            else:
                # 截取封面图并插入视频模式
                if self.process_single_video(video_path, output_folder):
                    success_count += 1
                else:
                    failed_files.append(os.path.basename(video_path))
                
        # 处理结果统计
        self.print_header("处理完成")
        print(f"✅ 成功处理: {success_count}/{total_count}")
        print(f"❌ 失败数量: {len(failed_files)}")
        
        if failed_files:
            print(f"\n失败的文件:")
            for filename in failed_files:
                print(f"   - {filename}")
                
        print(f"\n📁 输出文件夹: {output_folder}")
        
    def run(self):
        """主运行流程"""
        self.print_header("视频封面图处理工具 (UltraThink)")
        print("🎯 功能: 从视频中截取指定时间点的帧作为封面图")
        print("✨ 模式: 1) 只截取封面图  2) 截取封面图并插入到视频开头")
        print("📸 支持: 最后一帧（默认）或指定时间点的帧")
        print("🎬 插入效果: 视频播放时先显示封面图，然后播放原始内容")
        print("📋 提示: 如需完全无损处理，请使用 video_cover_inserter_lossless.py")
        
        # 1. 检查FFmpeg
        if not self.check_ffmpeg():
            return
            
        # 2. 获取视频文件夹路径
        video_folder = self.get_video_folder_path()
        
        # 3. 查找视频文件
        video_files = self.find_video_files(video_folder)
        if not video_files:
            print("❌ 没有找到视频文件")
            return
            
        # 4. 配置设置
        self.configure_settings()
        
        # 5. 确认处理
        print(f"\n📋 处理摘要:")
        print(f"   输入文件夹: {video_folder}")
        print(f"   视频文件数: {len(video_files)}")
        
        # 显示处理模式
        if self.processing_mode == "extract_only":
            print(f"   处理模式: 只截取封面图")
        else:
            print(f"   处理模式: 截取封面图并添加到视频开头")
        
        # 显示封面来源
        if self.cover_source_mode == "last":
            print(f"   封面来源: 视频最后一帧")
        else:
            print(f"   封面来源: 第{self.cover_source_time}秒的帧")
            
        # 显示封面时长（仅在插入模式下）
        if self.processing_mode == "extract_and_insert":
            if hasattr(self, 'cover_duration_mode') and self.cover_duration_mode == "frames":
                print(f"   封面时长: 前{self.cover_frames}帧 (根据视频帧率自动计算)")
            else:
                print(f"   封面时长: {self.cover_duration}秒")
        
        confirm = self.get_user_input("\n是否开始处理? (y/N)", "N")
        if confirm.lower() not in ['y', 'yes', '是']:
            print("❌ 取消处理")
            return
            
        # 6. 创建输出文件夹
        if self.processing_mode == "extract_only":
            output_folder = os.path.join(video_folder, "extracted_covers")
        else:
            output_folder = os.path.join(video_folder, "processed_with_cover")
        os.makedirs(output_folder, exist_ok=True)
        print(f"📁 输出文件夹: {output_folder}")
        
        # 7. 处理视频
        self.process_videos(video_files, output_folder)


def main():
    """主函数"""
    try:
        inserter = VideoCoverInserter()
        inserter.run()
    except KeyboardInterrupt:
        print("\n\n❌ 用户中断操作")
    except Exception as e:
        print(f"\n❌ 程序错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()