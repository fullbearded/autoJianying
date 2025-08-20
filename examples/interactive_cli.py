#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量草稿复制与素材替换工具
支持part1/part2/part3/part4...无限扩展文件夹组合式素材替换
"""

import os
import sys
import json
import time
import glob
import random
import shutil
import re
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pyJianYingDraft as draft
import platform
import sys

# Windows控制台编码处理
if platform.system() == "Windows":
    try:
        # 尝试设置控制台编码为UTF-8
        import locale
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except:
        # 如果失败，使用安全的ASCII字符
        pass


class BatchDraftProcessor:
    """批量草稿处理器"""
    
    def __init__(self, debug=False):
        self.debug = debug  # 调试模式
        
        # 根据操作系统设置默认草稿文件夹路径
        if platform.system() == "Windows":
            self.draft_folder_path = os.path.expanduser("~/AppData/Local/JianyingPro/User Data/Projects/com.lveditor.draft")
        elif platform.system() == "Darwin":  # macOS
            self.draft_folder_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
        else:
            # Linux 或其他系统，使用一个通用路径
            self.draft_folder_path = os.path.expanduser("~/JianyingPro/User Data/Projects/com.lveditor.draft")
        self.materials_folder_path = None
        self.selected_draft = None
        self.draft_folder = None
        self.material_combinations = []
        self.processing_mode = None  # "sequential" 或 "random"
        self.replacement_mode = None  # "video", "image", "all"
        self.timeline_mode = None  # "speed_adjust", "crop_end", "crop_start", "crop_random", "keep_original"
        
        # 音频和字幕配置
        self.enable_audio_subtitle = False
        self.audios_folder_path = None
        self.audio_volume = 100  # 默认100%
        self.audio_fade_in = 0  # 默认0秒
        self.audio_fade_out = 0  # 默认0秒
        self.audio_selection_mode = "sequential"  # "sequential" 或 "random"，默认按顺序
        self.audio_longer_handling = "none"  # "none", "speed_up", "trim"，默认无处理
        self.audio_shorter_handling = "none"  # "none", "trim_video", "allow_silence", "slow_down"，默认无处理
        self.enable_subtitles = True  # 默认启用字幕
        self.subtitle_style = "default"  # "default", "white_bg_black_border"
        
        # 背景音乐配置
        self.enable_background_music = False
        self.background_music_folder_path = None
        self.bg_music_volume = 100  # 默认100%
        self.bg_music_fade_in = 0  # 默认0秒
        self.bg_music_fade_out = 0  # 默认0秒
        self.bg_music_selection_mode = "sequential"  # "sequential" 或 "random"，默认按顺序
        self.bg_music_longer_handling = "none"  # "none", "speed_up", "trim"，默认无处理
        self.bg_music_shorter_handling = "none"  # "none", "trim_video", "allow_silence", "slow_down"，默认无处理
        
        # 文本替换配置
        self.enable_text_replacement = False
        self.text_replacement_count = 1  # 1或2，默认1段
        self.text_folder_path = None  # 文本文件夹路径
        self.text_files = {}  # {'content': 'path/to/content.txt', 'watermark': 'path/to/watermark.txt'}
        self.text_selection_mode = "sequential"  # "sequential" 或 "random"，默认按顺序循环
        self.text_contents = {}  # 缓存解析后的文本内容
        self.selected_text_tracks = []  # 选中要替换的文本轨道
        
        # 封面图配置
        self.enable_cover_image = False  # 是否生成封面图
        self.cover_image_style = "timeline_last_frame"  # 封面图样式: "timeline_last_frame", "video_last_frame", "ultrathink"
        self.last_replaced_videos = []  # 记录最近替换的视频文件
        self.jianying_app_path = None  # 剪映程序路径
        
    def safe_emoji_print(self, emoji, text):
        """安全的emoji打印，Windows兼容"""
        try:
            print(f"{emoji} {text}")
        except UnicodeEncodeError:
            # Windows console fallback without emoji
            print(f"[*] {text}")
    
    def print_header(self, title):
        """打印标题"""
        print("\n" + "=" * 70)
        self.safe_emoji_print("🎬", title)
        print("=" * 70)
    
    def print_section(self, title):
        """打印章节标题"""
        print()
        self.safe_emoji_print("📋", title)
        print("-" * 50)
    
    def print_success(self, message):
        """打印成功信息"""
        self.safe_emoji_print("✅", message)
    
    def print_warning(self, message):
        """打印警告信息"""
        self.safe_emoji_print("⚠️", message)
    
    def print_error(self, message):
        """打印错误信息"""
        self.safe_emoji_print("❌", message)
    
    def get_user_input(self, prompt, allow_empty=False, default=None):
        """获取用户输入"""
        while True:
            try:
                full_prompt = f"{prompt}"
                if default:
                    full_prompt += f" [默认: {default}]"
                full_prompt += ": "
                
                user_input = input(full_prompt).strip()
                if user_input:
                    return user_input
                elif default:
                    return default
                elif allow_empty:
                    return user_input
                print("输入不能为空，请重新输入")
            except KeyboardInterrupt:
                print("\n\n👋 用户取消操作，再见!")
                sys.exit(0)
    
    def get_user_choice(self, options, prompt="请选择", default_index=None):
        """获取用户选择"""
        while True:
            try:
                print(f"\n{prompt}:")
                for i, option in enumerate(options, 1):
                    default_marker = " (默认)" if default_index is not None and i == default_index + 1 else ""
                    print(f"  {i}. {option}{default_marker}")
                print(f"  0. 退出")
                
                if default_index is not None:
                    choice = input(f"\n👉 输入选择 (直接回车使用默认值): ").strip()
                else:
                    choice = input("\n👉 输入选择: ").strip()
                
                # 如果是空输入且有默认值，使用默认值
                if choice == "" and default_index is not None:
                    return default_index, options[default_index]
                
                if choice == '0':
                    print("\n👋 再见!")
                    sys.exit(0)
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(options):
                    return choice_num - 1, options[choice_num - 1]
                else:
                    print("❌ 选择超出范围，请重新输入")
            except ValueError:
                print("❌ 请输入有效的数字")
            except KeyboardInterrupt:
                print("\n\n👋 用户取消操作，再见!")
    
    def setup_paths(self):
        """设置路径"""
        self.print_header("路径设置")
        
        print(f"当前草稿文件夹: {self.draft_folder_path}")
        print(f"操作系统: {platform.system()}")
        
        if not os.path.exists(self.draft_folder_path):
            self.print_error("草稿文件夹不存在!")
            
            # Windows系统特定的提示信息
            if platform.system() == "Windows":
                self.print_error("\n🔧 Windows系统常见草稿文件夹位置:")
                self.print_error("1. 标准位置: %USERPROFILE%\\AppData\\Local\\JianyingPro\\User Data\\Projects\\com.lveditor.draft")
                expanded_path = os.path.expanduser("~/AppData/Local/JianyingPro/User Data/Projects/com.lveditor.draft")
                self.print_error(f"2. 展开后路径: {expanded_path}")
                
                # 检查一些常见的替代路径
                alternative_paths = [
                    os.path.expanduser("~/AppData/Roaming/JianyingPro/User Data/Projects/com.lveditor.draft"),
                    "C:\\Program Files\\JianyingPro\\User Data\\Projects\\com.lveditor.draft",
                    "C:\\Program Files (x86)\\JianyingPro\\User Data\\Projects\\com.lveditor.draft"
                ]
                
                print("🔍 正在检查可能的替代路径...")
                for alt_path in alternative_paths:
                    if os.path.exists(alt_path):
                        self.print_success(f"找到可能的路径: {alt_path}")
                        use_alt = input(f"是否使用此路径? (y/n): ").strip().lower()
                        if use_alt == 'y':
                            self.draft_folder_path = alt_path
                            break
            
            if not os.path.exists(self.draft_folder_path):
                new_path = self.get_user_input("请输入正确的草稿文件夹路径")
                if os.path.exists(new_path):
                    self.draft_folder_path = new_path
                    self.print_success("草稿文件夹路径已更新")
                else:
                    self.print_error("路径仍然无效，请检查后重试")
                    return False
        
        try:
            self.draft_folder = draft.DraftFolder(self.draft_folder_path)
            # 检测剪映程序路径
            self.detect_jianying_app_path()
            return True
        except Exception as e:
            self.print_error(f"初始化草稿文件夹失败: {e}")
            return False
    
    def detect_jianying_app_path(self):
        """检测剪映程序路径，支持多个版本"""
        if platform.system() == "Windows":
            # Windows系统可能的剪映程序路径
            possible_paths = [
                # 用户提供的5.9版本路径
                r"C:\Users\yangb\AppData\Local\JianyingPro\Apps\5.9.0.11632",
                # 其他常见路径模式
                os.path.expanduser("~/AppData/Local/JianyingPro/Apps"),
                # 程序文件安装路径
                "C:/Program Files/JianyingPro/Apps",
                "C:/Program Files (x86)/JianyingPro/Apps"
            ]
            
            for base_path in possible_paths:
                if os.path.exists(base_path):
                    # 如果是Apps文件夹，查找版本子文件夹
                    if base_path.endswith("Apps"):
                        try:
                            # 查找版本文件夹
                            for item in os.listdir(base_path):
                                version_path = os.path.join(base_path, item)
                                if os.path.isdir(version_path) and any(char.isdigit() for char in item):
                                    self.jianying_app_path = version_path
                                    if self.debug:
                                        self.print_success(f"找到剪映程序: {self.jianying_app_path}")
                                    return self.jianying_app_path
                        except:
                            continue
                    else:
                        # 直接的版本路径
                        self.jianying_app_path = base_path
                        if self.debug:
                            self.print_success(f"找到剪映程序: {self.jianying_app_path}")
                        return self.jianying_app_path
            
            if self.debug:
                self.print_warning("未找到剪映程序路径")
        
        return None
    
    def get_compatible_draft_file_path(self, draft_name):
        """获取兼容的草稿文件路径 (支持多版本格式)"""
        draft_folder = os.path.join(self.draft_folder_path, draft_name)
        
        # 尝试多种草稿文件格式 (兼容不同版本的剪映)
        possible_files = [
            "draft_info.json",      # 剪映6.0+版本
            "draft_content.json"    # 剪映5.9及以下版本
        ]
        
        for file_name in possible_files:
            potential_path = os.path.join(draft_folder, file_name)
            if os.path.exists(potential_path):
                return potential_path
        
        return None
    
    def load_draft_info_from_file(self, draft_name):
        """从草稿文件加载草稿信息 (兼容多个版本的文件格式)"""
        draft_folder = os.path.join(self.draft_folder_path, draft_name)
        
        # 尝试多种草稿文件格式 (兼容不同版本的剪映)
        possible_files = [
            "draft_info.json",      # 剪映6.0+版本
            "draft_content.json"    # 剪映5.9及以下版本
        ]
        
        draft_info_path = None
        for file_name in possible_files:
            potential_path = os.path.join(draft_folder, file_name)
            if os.path.exists(potential_path):
                draft_info_path = potential_path
                break
        
        if not draft_info_path:
            if self.debug:
                self.print_warning(f"草稿 {draft_name} 未找到支持的草稿文件格式")
                # 列出实际存在的文件以供调试
                if os.path.exists(draft_folder):
                    files = os.listdir(draft_folder)
                    self.print_warning(f"草稿文件夹中的文件: {files}")
            return None
        
        try:
            with open(draft_info_path, 'r', encoding='utf-8') as f:
                draft_info = json.load(f)
                
            if self.debug:
                self.print_success(f"成功读取草稿文件: {os.path.basename(draft_info_path)}")
            
            # 提取基本信息
            canvas = draft_info.get('canvas_config', {})
            duration = draft_info.get('duration', 0)
            fps = draft_info.get('fps', 30.0)
            
            # 统计轨道信息
            tracks_stats = {}
            if 'tracks' in draft_info:
                for track in draft_info['tracks']:
                    track_type = track.get('type', 'unknown')
                    tracks_stats[track_type] = tracks_stats.get(track_type, 0) + 1
            
            # 统计素材信息
            materials_stats = {}
            if 'materials' in draft_info:
                for material_type, material_list in draft_info['materials'].items():
                    if isinstance(material_list, list) and material_list:
                        materials_stats[material_type] = len(material_list)
            
            # 提取视频素材信息
            video_materials = []
            if 'materials' in draft_info and 'videos' in draft_info['materials']:
                for video in draft_info['materials']['videos']:
                    if isinstance(video, dict):
                        video_materials.append({
                            'id': video.get('id', ''),
                            'name': video.get('material_name', video.get('name', '')),
                            'path': video.get('path', ''),
                            'duration': video.get('duration', 0),
                            'width': video.get('width', 0),
                            'height': video.get('height', 0)
                        })
            
            return {
                'draft_name': draft_name,
                'canvas_config': canvas,
                'duration': duration,
                'fps': fps,
                'tracks': tracks_stats,
                'materials': materials_stats,
                'video_materials': video_materials,
                'raw_data': draft_info
            }
            
        except Exception as e:
            print(f"读取 draft_info.json 失败: {e}")
            return None
    
    def select_source_draft(self):
        """选择源草稿作为复制模版"""
        self.print_header("选择复制模版草稿")
        
        try:
            draft_list = self.draft_folder.list_drafts()
            # 过滤掉系统文件和demo草稿 (Windows兼容性: 过滤隐藏文件夹)
            filtered_drafts = []
            for d in draft_list:
                if not d.startswith('.') and not d.startswith('pyJianYingDraft_Demo'):
                    # Windows兼容性: 检查是否为有效的草稿文件夹
                    draft_path = os.path.join(self.draft_folder_path, d)
                    if os.path.isdir(draft_path):
                        filtered_drafts.append(d)
            
            if not filtered_drafts:
                self.print_error("没有找到可用的草稿")
                self.print_error(f"请检查草稿文件夹路径是否正确: {self.draft_folder_path}")
                if platform.system() == "Windows":
                    self.print_error("Windows系统默认路径: ~/AppData/Local/JianyingPro/User Data/Projects/com.lveditor.draft")
                return False
            
            print(f"📁 草稿文件夹: {self.draft_folder_path}")
            print(f"📊 找到 {len(filtered_drafts)} 个可用草稿:")
            
            # 显示草稿详细信息
            draft_options = []
            for draft_name in filtered_drafts:
                draft_info = self.load_draft_info_from_file(draft_name)
                if draft_info:
                    canvas = draft_info['canvas_config']
                    duration_sec = draft_info['duration'] / 1000000 if draft_info['duration'] else 0
                    video_count = len(draft_info['video_materials'])
                    
                    info_str = f"{draft_name} ({canvas.get('width', '?')}x{canvas.get('height', '?')}, {duration_sec:.1f}s, {video_count}个视频)"
                else:
                    info_str = f"{draft_name} (信息读取失败)"
                draft_options.append(info_str)
            
            choice_idx, choice_str = self.get_user_choice(draft_options, "选择作为复制模版的源草稿")
            
            self.selected_draft = filtered_drafts[choice_idx]
            self.print_success(f"已选择源草稿: {self.selected_draft}")
            
            # 显示源草稿的视频素材信息
            draft_info = self.load_draft_info_from_file(self.selected_draft)
            if draft_info and draft_info['video_materials']:
                print(f"\n📹 源草稿包含 {len(draft_info['video_materials'])} 个视频素材:")
                for i, video in enumerate(draft_info['video_materials']):
                    duration_sec = video['duration'] / 1000000 if video['duration'] else 0
                    print(f"  {i+1}. {video['name']} ({video['width']}x{video['height']}, {duration_sec:.1f}s)")
            
            return True
            
        except Exception as e:
            self.print_error(f"列出草稿失败: {e}")
            self.print_error(f"当前草稿文件夹路径: {self.draft_folder_path}")
            
            if platform.system() == "Windows":
                self.print_error("\n🔧 Windows系统故障排查指南:")
                self.print_error("1. 检查剪映是否已安装")
                self.print_error("2. 确认草稿文件夹路径是否正确")
                self.print_error("3. 标准路径: %USERPROFILE%\\AppData\\Local\\JianyingPro\\User Data\\Projects\\com.lveditor.draft")
                self.print_error("4. 确保有足够的文件系统访问权限")
                alternate_path = input("\n是否要手动输入草稿文件夹路径? (y/n): ").strip().lower()
                if alternate_path == 'y':
                    new_path = input("请输入正确的草稿文件夹路径: ").strip()
                    if os.path.exists(new_path):
                        self.draft_folder_path = new_path
                        self.print_success("路径已更新，请重试")
                        return self.setup_paths() and self.select_source_draft()
                    else:
                        self.print_error("提供的路径不存在")
            
            return False
    
    def setup_materials_folder(self):
        """设置素材文件夹"""
        self.print_section("设置素材文件夹")
        
        # 设置默认路径为当前目录下的materials文件夹
        default_path = "./materials"
        
        # 提示用户手动设置素材文件夹路径
        custom_path = self.get_user_input("请输入素材文件夹路径", default=default_path)
        
        # 验证路径是否存在
        if custom_path and os.path.exists(custom_path):
            self.materials_folder_path = custom_path
            print(f"✅ 素材文件夹设置为: {custom_path}")
        else:
            self.print_error(f"素材文件夹不存在: {custom_path}")
            return False
        
        print(f"📁 素材文件夹: {self.materials_folder_path}")
        return True
    
    def select_replacement_mode(self):
        """选择替换模式"""
        self.print_section("选择替换模式")
        
        mode_options = [
            "仅替换视频片段 (part1/part2/part3...)",
            "仅替换图片素材 (background)",
            "替换所有素材 (视频+图片)"
        ]
        
        mode_idx, mode_str = self.get_user_choice(mode_options, "选择素材替换模式")
        
        if mode_idx == 0:
            self.replacement_mode = "video"
        elif mode_idx == 1:
            self.replacement_mode = "image"
        else:
            self.replacement_mode = "all"
        
        print(f"✅ 选择模式: {mode_str}")
        return True
    
    def configure_audio_subtitle_options(self):
        """配置音频和字幕选项"""
        self.print_section("音频和字幕配置")
        
        # 询问是否启用音频和字幕
        enable_options = ["是", "否"]
        enable_idx, enable_str = self.get_user_choice(enable_options, "是否添加音频和字幕", default_index=1)
        
        if enable_idx == 1:  # 选择"否"
            self.enable_audio_subtitle = False
            print("✅ 跳过音频和字幕功能")
            return True
        
        self.enable_audio_subtitle = True
        print("✅ 启用音频和字幕功能")
        
        # 设置音频文件夹路径
        if not self.setup_audios_folder():
            return False
        
        # 配置音量
        print(f"\n🔊 音量大小配置 (当前: {self.audio_volume}%)")
        volume_input = self.get_user_input("请输入音量大小 (0-1000, 默认100, 最大1000=20.0dB)", allow_empty=True)
        if volume_input:
            try:
                volume = int(volume_input)
                if 0 <= volume <= 1000:
                    self.audio_volume = volume
                    db_value = 20 * (volume / 100 - 1) if volume != 100 else 0
                    print(f"✅ 音量设置为: {volume}% (≈{db_value:.1f}dB)")
                else:
                    print("⚠️ 音量超出范围，使用默认值100%")
            except ValueError:
                print("⚠️ 音量输入无效，使用默认值100%")
        
        # 配置淡入淡出时长
        print(f"\n🎵 淡入淡出配置 (当前: 淡入{self.audio_fade_in}s, 淡出{self.audio_fade_out}s)")
        fade_in_input = self.get_user_input("请输入淡入时长(秒, 默认0)", allow_empty=True)
        if fade_in_input:
            try:
                self.audio_fade_in = float(fade_in_input)
                print(f"✅ 淡入时长设置为: {self.audio_fade_in}s")
            except ValueError:
                print("⚠️ 淡入时长输入无效，使用默认值0s")
        
        fade_out_input = self.get_user_input("请输入淡出时长(秒, 默认0)", allow_empty=True)
        if fade_out_input:
            try:
                self.audio_fade_out = float(fade_out_input)
                print(f"✅ 淡出时长设置为: {self.audio_fade_out}s")
            except ValueError:
                print("⚠️ 淡出时长输入无效，使用默认值0s")
        
        # 配置音频选择规则
        print(f"\n📋 音频选择规则")
        selection_options = [
            "按文件名顺序",
            "随机选择"
        ]
        selection_idx, selection_str = self.get_user_choice(selection_options, "音频文件选择规则", default_index=0)
        self.audio_selection_mode = "sequential" if selection_idx == 0 else "random"
        print(f"✅ 音频选择规则: {selection_str}")
        
        # 配置音频比视频长的处理方式
        print(f"\n⏱️ 音频比视频长的处理方式")
        longer_options = [
            "无 (保持音频原样)",
            "加速音频以缩短时长，使得音频和视频画面一样长",
            "裁剪掉音频后面的部分，使得音频和视频画面一样长"
        ]
        longer_idx, longer_str = self.get_user_choice(longer_options, "音频比视频长时的处理", default_index=0)
        if longer_idx == 0:
            self.audio_longer_handling = "none"
        elif longer_idx == 1:
            self.audio_longer_handling = "speed_up"
        else:
            self.audio_longer_handling = "trim"
        print(f"✅ 音频较长处理: {longer_str}")
        
        # 配置音频比视频短的处理方式
        print(f"\n⏱️ 音频比视频短的处理方式")
        shorter_options = [
            "无 (保持音频原样)",
            "音频保持默认速度，裁剪掉长于音频的后面的视频画面（比如音频是1分钟，视频画面是2分钟，这项配置会把视频裁剪为1分钟，后半部分视频就看不到了）",
            "音频保证默认速度，视频后面部分没有音频声音",
            "减速音频以延展时长，使得音频和视频画面一样长"
        ]
        shorter_idx, shorter_str = self.get_user_choice(shorter_options, "音频比视频短时的处理", default_index=0)
        if shorter_idx == 0:
            self.audio_shorter_handling = "none"
        elif shorter_idx == 1:
            self.audio_shorter_handling = "trim_video"
        elif shorter_idx == 2:
            self.audio_shorter_handling = "allow_silence"
        else:
            self.audio_shorter_handling = "slow_down"
        print(f"✅ 音频较短处理: {shorter_str}")
        
        # 配置字幕选项
        print(f"\n📝 字幕配置")
        subtitle_options = ["是", "否"]
        subtitle_idx, subtitle_str = self.get_user_choice(subtitle_options, "是否加载音频对应的SRT字幕文件", default_index=0)
        self.enable_subtitles = (subtitle_idx == 0)
        print(f"✅ 字幕功能: {'启用' if self.enable_subtitles else '禁用'}")
        
        if self.enable_subtitles:
            print("💡 提示: 请确保SRT字幕文件与音频文件同名且在同一目录")
            print("   例如: abc.mp3 对应的字幕文件为 abc.srt")
            
            # 配置字幕样式
            print(f"\n🎨 字幕样式配置")
            style_options = [
                "白底黑框 (12字号，白底，黑色边框，自动换行)",
                "默认样式 (系统默认字幕样式)"
            ]
            style_idx, style_str = self.get_user_choice(style_options, "选择字幕样式", default_index=0)
            
            if style_idx == 0:
                self.subtitle_style = "white_bg_black_border"
                print(f"    🔧 [DEBUG] 设置字幕样式: white_bg_black_border")
            else:
                self.subtitle_style = "default"
                print(f"    🔧 [DEBUG] 设置字幕样式: default")
            
            print(f"    🔧 [DEBUG] 最终self.subtitle_style值: '{self.subtitle_style}'")
            print(f"✅ 字幕样式: {style_str}")
        
        # 配置背景音乐
        print(f"\n🎵 背景音乐配置")
        bg_music_options = ["是", "否"]
        bg_music_idx, bg_music_str = self.get_user_choice(bg_music_options, "是否添加背景音乐", default_index=1)
        
        if bg_music_idx == 1:  # 选择"否"
            self.enable_background_music = False
            print("✅ 跳过背景音乐功能")
            return True
        
        self.enable_background_music = True
        print("✅ 启用背景音乐功能")
        
        # 设置背景音乐文件夹路径
        if not self.setup_background_music_folder():
            return False
        
        # 配置背景音乐音量
        print(f"\n🔊 背景音乐音量配置 (当前: {self.bg_music_volume}%)")
        bg_volume_input = self.get_user_input("请输入背景音乐音量大小 (0-1000, 默认100, 最大1000=20.0dB)", allow_empty=True)
        if bg_volume_input:
            try:
                bg_volume = int(bg_volume_input)
                if 0 <= bg_volume <= 1000:
                    self.bg_music_volume = bg_volume
                    db_value = 20 * (bg_volume / 100 - 1) if bg_volume != 100 else 0
                    print(f"✅ 背景音乐音量设置为: {bg_volume}% (≈{db_value:.1f}dB)")
                else:
                    print("⚠️ 音量超出范围，使用默认值100%")
            except ValueError:
                print("⚠️ 音量输入无效，使用默认值100%")
        
        # 配置背景音乐淡入淡出时长
        print(f"\n🎵 背景音乐淡入淡出配置 (当前: 淡入{self.bg_music_fade_in}s, 淡出{self.bg_music_fade_out}s)")
        bg_fade_in_input = self.get_user_input("请输入背景音乐淡入时长(秒, 默认0)", allow_empty=True)
        if bg_fade_in_input:
            try:
                self.bg_music_fade_in = float(bg_fade_in_input)
                print(f"✅ 背景音乐淡入时长设置为: {self.bg_music_fade_in}s")
            except ValueError:
                print("⚠️ 淡入时长输入无效，使用默认值0s")
        
        bg_fade_out_input = self.get_user_input("请输入背景音乐淡出时长(秒, 默认0)", allow_empty=True)
        if bg_fade_out_input:
            try:
                self.bg_music_fade_out = float(bg_fade_out_input)
                print(f"✅ 背景音乐淡出时长设置为: {self.bg_music_fade_out}s")
            except ValueError:
                print("⚠️ 淡出时长输入无效，使用默认值0s")
        
        # 配置背景音乐选择规则
        print(f"\n📋 背景音乐选择规则")
        bg_selection_options = [
            "按文件名顺序",
            "随机选择"
        ]
        bg_selection_idx, bg_selection_str = self.get_user_choice(bg_selection_options, "背景音乐文件选择规则", default_index=0)
        self.bg_music_selection_mode = "sequential" if bg_selection_idx == 0 else "random"
        print(f"✅ 背景音乐选择规则: {bg_selection_str}")
        
        # 配置背景音乐比视频长的处理方式
        print(f"\n⏱️ 背景音乐比视频长的处理方式")
        bg_longer_options = [
            "无",
            "加速音频以缩短时长，使得音频和视频画面一样长",
            "裁剪掉音频后面的部分，使得音频和视频画面一样长"
        ]
        bg_longer_idx, bg_longer_str = self.get_user_choice(bg_longer_options, "背景音乐比视频长时的处理", default_index=0)
        if bg_longer_idx == 0:
            self.bg_music_longer_handling = "none"
        elif bg_longer_idx == 1:
            self.bg_music_longer_handling = "speed_up"
        else:
            self.bg_music_longer_handling = "trim"
        print(f"✅ 背景音乐较长处理: {bg_longer_str}")
        print(f"    🔧 [DEBUG] 设置bg_music_longer_handling = '{self.bg_music_longer_handling}'")
        
        # 配置背景音乐比视频短的处理方式
        print(f"\n⏱️ 背景音乐比视频短的处理方式")
        bg_shorter_options = [
            "无",
            "音频保持默认速度，裁剪掉长于音频的后面的视频画面（比如音频是1分钟，视频画面是2分钟，这项配置会把视频裁剪为1分钟，后半部分视频就看不到了）",
            "音频保证默认速度，视频后面部分没有音频声音",
            "减速音频以延展时长，使得音频和视频画面一样长"
        ]
        bg_shorter_idx, bg_shorter_str = self.get_user_choice(bg_shorter_options, "背景音乐比视频短时的处理", default_index=0)
        if bg_shorter_idx == 0:
            self.bg_music_shorter_handling = "none"
        elif bg_shorter_idx == 1:
            self.bg_music_shorter_handling = "trim_video"
        elif bg_shorter_idx == 2:
            self.bg_music_shorter_handling = "allow_silence"
        else:
            self.bg_music_shorter_handling = "slow_down"
        print(f"✅ 背景音乐较短处理: {bg_shorter_str}")
        
        # 配置文本替换功能
        print(f"\n📝 文本替换配置")
        text_options = ["是", "否"]
        text_idx, text_str = self.get_user_choice(text_options, "是否需要文本替换", default_index=1)
        
        if text_idx == 1:  # 选择"否"
            self.enable_text_replacement = False
            print("✅ 跳过文本替换功能")
        else:
            self.enable_text_replacement = True
            print("✅ 启用文本替换功能")
            
            # 选择替换文本数量
            count_options = ["1段（标题）", "2段（标题+水印）"]
            count_idx, count_str = self.get_user_choice(count_options, "选择替换的文本数量", default_index=0)
            
            self.text_replacement_count = count_idx + 1
            print(f"✅ 文本替换数量: {self.text_replacement_count}段")
            
            # 先从源草稿中提取文本轨道，让用户选择要替换的轨道
            if not self.configure_text_tracks_selection():
                print("⚠️ 文本轨道选择失败，将跳过文本替换功能")
                self.enable_text_replacement = False
            else:
                # 设置文本文件夹路径
                if not self.setup_text_folder():
                    print("⚠️ 文本文件夹设置失败，将跳过文本替换功能")
                    self.enable_text_replacement = False
                else:
                    # 设置文本文件路径（不展示内容）
                    if not self.setup_text_files_simple():
                        print("⚠️ 文本文件设置失败，将跳过文本替换功能")
                        self.enable_text_replacement = False
                    else:
                        # 读取和解析文本内容
                        if not self.load_text_contents():
                            print("⚠️ 文本内容读取失败，将跳过文本替换功能")
                            self.enable_text_replacement = False
                        else:
                            # 选择文本替换规则
                            selection_options = ["按顺序然后循环", "随机"]
                            selection_idx, selection_str = self.get_user_choice(selection_options, "文本选择规则", default_index=0)
                            
                            self.text_selection_mode = "sequential" if selection_idx == 0 else "random"
                            print(f"✅ 文本选择规则: {selection_str}")
        
        # 配置封面图功能
        print(f"\n🖼️ 封面图配置")
        cover_options = ["是", "否"]
        cover_idx, cover_str = self.get_user_choice(cover_options, "是否需要生成封面图", default_index=1)
        
        if cover_idx == 1:  # 选择"否"
            self.enable_cover_image = False
            print("✅ 跳过封面图生成")
        else:
            self.enable_cover_image = True
            
            # 选择封面图生成样式
            style_options = [
                "草稿时间线最后一帧（推荐）",
                "视频文件最后一帧",
                "剪映样式（ultrathink兼容）"
            ]
            style_idx, style_str = self.get_user_choice(style_options, "选择封面图样式", default_index=0)
            
            if style_idx == 0:
                self.cover_image_style = "timeline_last_frame"
                print("✅ 启用封面图生成（草稿时间线最后一帧）")
            elif style_idx == 1:
                self.cover_image_style = "video_last_frame"
                print("✅ 启用封面图生成（视频文件最后一帧）")
            else:
                self.cover_image_style = "ultrathink"
                print("✅ 启用封面图生成（剪映样式兼容）")
        
        return True
    
    def setup_audios_folder(self):
        """设置音频文件夹"""
        print(f"\n📁 音频文件夹配置")
        
        # 默认音频文件夹路径
        default_audios_path = os.path.join(self.materials_folder_path, "audios")
        
        print(f"默认音频文件夹: {default_audios_path}")
        
        if os.path.exists(default_audios_path):
            self.audios_folder_path = default_audios_path
            print(f"✅ 找到默认音频文件夹")
        else:
            print(f"⚠️ 默认音频文件夹不存在")
            
            # 询问是否创建或使用其他路径
            create_options = [
                f"创建默认音频文件夹: {default_audios_path}",
                "指定其他音频文件夹路径"
            ]
            create_idx, create_str = self.get_user_choice(create_options, "请选择")
            
            if create_idx == 0:
                # 创建默认文件夹
                try:
                    os.makedirs(default_audios_path, exist_ok=True)
                    self.audios_folder_path = default_audios_path
                    print(f"✅ 已创建音频文件夹: {default_audios_path}")
                except Exception as e:
                    print(f"❌ 创建音频文件夹失败: {e}")
                    return False
            else:
                # 指定其他路径
                custom_path = self.get_user_input("请输入音频文件夹路径")
                if os.path.exists(custom_path):
                    self.audios_folder_path = custom_path
                    print(f"✅ 使用指定音频文件夹: {custom_path}")
                else:
                    print(f"❌ 指定的音频文件夹不存在: {custom_path}")
                    return False
        
        # 检查音频文件夹中的文件
        audio_files = []
        audio_extensions = ['*.mp3', '*.wav', '*.aac', '*.m4a', '*.flac']
        for ext in audio_extensions:
            files = glob.glob(os.path.join(self.audios_folder_path, ext))
            audio_files.extend(files)
        
        if audio_files:
            print(f"📊 找到 {len(audio_files)} 个音频文件")
        else:
            print(f"⚠️ 音频文件夹为空，请添加音频文件后重新运行")
            print(f"💡 支持的音频格式: {', '.join(audio_extensions)}")
            return False
        
        return True
    
    def setup_background_music_folder(self):
        """设置背景音乐文件夹"""
        print(f"\n📁 背景音乐文件夹配置")
        
        # 默认背景音乐文件夹路径：./materials/musics
        default_bg_music_path = os.path.join(self.materials_folder_path, "musics")
        
        print(f"默认背景音乐文件夹: {default_bg_music_path}")
        
        if os.path.exists(default_bg_music_path):
            self.background_music_folder_path = default_bg_music_path
            print(f"✅ 找到默认背景音乐文件夹")
        else:
            print(f"⚠️ 默认背景音乐文件夹不存在")
            
            # 询问是否创建或使用其他路径
            create_options = [
                f"创建默认背景音乐文件夹: {default_bg_music_path}",
                "指定其他背景音乐文件夹路径"
            ]
            create_idx, create_str = self.get_user_choice(create_options, "请选择")
            
            if create_idx == 0:
                # 创建默认文件夹
                try:
                    os.makedirs(default_bg_music_path, exist_ok=True)
                    self.background_music_folder_path = default_bg_music_path
                    print(f"✅ 已创建背景音乐文件夹: {default_bg_music_path}")
                except Exception as e:
                    print(f"❌ 创建背景音乐文件夹失败: {e}")
                    return False
            else:
                # 指定其他路径
                custom_path = self.get_user_input("请输入背景音乐文件夹路径")
                if os.path.exists(custom_path):
                    self.background_music_folder_path = custom_path
                    print(f"✅ 使用指定背景音乐文件夹: {custom_path}")
                else:
                    print(f"❌ 指定的背景音乐文件夹不存在: {custom_path}")
                    return False
        
        # 检查背景音乐文件夹中的文件
        bg_music_files = []
        audio_extensions = ['*.mp3', '*.wav', '*.aac', '*.m4a', '*.flac', '*.MP3', '*.WAV', '*.AAC', '*.M4A', '*.FLAC']
        for ext in audio_extensions:
            files = glob.glob(os.path.join(self.background_music_folder_path, ext))
            bg_music_files.extend(files)
        
        if bg_music_files:
            print(f"📊 找到 {len(bg_music_files)} 个背景音乐文件")
        else:
            print(f"⚠️ 背景音乐文件夹为空，请添加音频文件后重新运行")
            print(f"💡 支持的音频格式: {', '.join(audio_extensions)}")
            return False
        
        return True
    
    def select_timeline_mode(self):
        """选择时间线处理模式"""
        if self.replacement_mode == "image":
            # 图片模式不需要时间线处理
            self.timeline_mode = "keep_original"
            return True
        
        self.print_section("选择时间线处理模式")
        
        print("当新视频素材长度与原素材不同时的处理方式：")
        
        mode_options = [
            "变速调整 - 太长就加速，太短就减速，保持时间线不变 ⭐ 推荐",
            "裁剪尾部 - 太长就裁剪后面，太短就减速，保持时间线不变",
            "裁剪头部 - 太长就裁剪前面，太短就减速，保持时间线不变", 
            "随机裁剪 - 太长就随机裁剪，太短就减速，保持时间线不变",
            "保持原样 - 不调整，按新素材长度播放，时间线会改变"
        ]
        
        mode_idx, mode_str = self.get_user_choice(mode_options, "选择时间线处理模式")
        
        if mode_idx == 0:
            self.timeline_mode = "speed_adjust"
        elif mode_idx == 1:
            self.timeline_mode = "crop_end"
        elif mode_idx == 2:
            self.timeline_mode = "crop_start"
        elif mode_idx == 3:
            self.timeline_mode = "crop_random"
        else:
            self.timeline_mode = "keep_original"
        
        print(f"✅ 选择时间线处理: {mode_str}")
        
        # 显示处理说明
        if self.timeline_mode == "speed_adjust":
            print("📊 示例: 原素材15s，新素材10s → 新素材减速1.5x播放，保持15s时长")
        elif self.timeline_mode == "crop_end":
            print("✂️ 示例: 原素材15s，新素材20s → 新素材裁剪为15s（保留前15s）")
        elif self.timeline_mode == "keep_original":
            print("🎬 示例: 原素材15s，新素材10s → 新素材播放10s，时间线变化")
        
        return True
    
    def discover_part_folders(self):
        """动态发现所有part文件夹"""
        part_folders = []
        
        # 从草稿中获取part素材名称
        if hasattr(self, 'selected_draft') and self.selected_draft:
            draft_info = self.load_draft_info_from_file(self.selected_draft)
            if draft_info and 'video_materials' in draft_info:
                for video in draft_info['video_materials']:
                    name = video.get('name', '')
                    # 匹配 partN.mp4 格式
                    import re
                    match = re.match(r'part(\d+)\.mp4', name)
                    if match:
                        part_num = int(match.group(1))
                        part_folder = f'part{part_num}'
                        if part_folder not in part_folders:
                            part_folders.append(part_folder)
        
        # 如果没有从草稿中发现，扫描materials文件夹
        if not part_folders and self.materials_folder_path:
            materials_path = Path(self.materials_folder_path)
            for item in materials_path.iterdir():
                if item.is_dir() and item.name.startswith('part') and item.name[4:].isdigit():
                    part_folders.append(item.name)
        
        # 默认至少包含part1-part3
        if not part_folders:
            part_folders = ['part1', 'part2', 'part3']
        
        # 按数字排序
        part_folders.sort(key=lambda x: int(x[4:]) if x[4:].isdigit() else 999)
        
        if self.debug:
            print(f"    🔍 DEBUG 发现part文件夹: {part_folders}")
        
        return part_folders

    def create_part_folders_and_scan(self):
        """创建文件夹并扫描素材"""
        self.print_section("创建素材文件夹结构")
        
        # 动态发现所有part文件夹
        part_folders = self.discover_part_folders()
        
        # 根据替换模式决定需要处理的文件夹
        if self.replacement_mode == "video":
            folders_to_process = part_folders
            file_extensions = ['*.mp4', '*.mov', '*.avi', '*.mkv']
        elif self.replacement_mode == "image":
            folders_to_process = ['background']
            file_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
        else:  # "all"
            folders_to_process = part_folders + ['background']
            file_extensions = ['*.mp4', '*.mov', '*.avi', '*.mkv', '*.jpg', '*.jpeg', '*.png', '*.bmp']
        
        part_files = {}
        
        for folder in folders_to_process:
            folder_path = os.path.join(self.materials_folder_path, folder)
            
            # 创建文件夹（如果不存在）
            if not os.path.exists(folder_path):
                os.makedirs(folder_path, exist_ok=True)
                print(f"✅ 创建文件夹: {folder}")
            else:
                print(f"📁 文件夹已存在: {folder}")
            
            # 扫描对应的文件类型
            all_files = []
            for ext in file_extensions:
                files = glob.glob(os.path.join(folder_path, ext))
                all_files.extend(files)
            
            part_files[folder] = [os.path.basename(f) for f in all_files]
            
            if folder == 'background':
                print(f"  └── 找到 {len(part_files[folder])} 个图片文件: {part_files[folder][:3]}{'...' if len(part_files[folder]) > 3 else ''}")
            else:
                print(f"  └── 找到 {len(part_files[folder])} 个视频文件: {part_files[folder][:3]}{'...' if len(part_files[folder]) > 3 else ''}")
        
        # 检查是否所有文件夹都有文件
        if not all(part_files.values()):
            self.print_warning("部分文件夹为空，请添加对应文件后重新运行")
            empty_folders = [folder for folder, files in part_files.items() if not files]
            print(f"空的文件夹: {empty_folders}")
            
            # 提示用户如何添加文件
            print(f"\n💡 请在以下文件夹中添加对应文件:")
            for folder in empty_folders:
                folder_path = os.path.join(self.materials_folder_path, folder)
                if folder == 'background':
                    print(f"  - {folder_path} (添加 .jpg/.png 图片文件)")
                else:
                    print(f"  - {folder_path} (添加 .mp4 视频文件)")
            
            return False
        
        # 生成素材组合
        return self.generate_material_combinations(part_files)
    
    def scan_audio_files(self):
        """扫描音频文件"""
        if not self.audios_folder_path or not os.path.exists(self.audios_folder_path):
            return []
        
        audio_files = []
        audio_extensions = ['*.mp3', '*.wav', '*.aac', '*.m4a', '*.flac']
        
        for ext in audio_extensions:
            files = glob.glob(os.path.join(self.audios_folder_path, ext))
            audio_files.extend([os.path.basename(f) for f in files])
        
        # 根据音频选择模式排序
        if self.audio_selection_mode == "sequential":
            audio_files.sort()
        else:  # random
            random.shuffle(audio_files)
        
        return audio_files
    
    def scan_background_music_files(self):
        """扫描背景音乐文件"""
        if not self.background_music_folder_path or not os.path.exists(self.background_music_folder_path):
            return []
        
        bg_music_files = []
        audio_extensions = ['*.mp3', '*.wav', '*.aac', '*.m4a', '*.flac', '*.MP3', '*.WAV', '*.AAC', '*.M4A', '*.FLAC']
        
        for ext in audio_extensions:
            files = glob.glob(os.path.join(self.background_music_folder_path, ext))
            bg_music_files.extend([os.path.basename(f) for f in files])
        
        # 根据背景音乐选择模式排序
        if self.bg_music_selection_mode == "sequential":
            bg_music_files.sort()
        else:  # random
            random.shuffle(bg_music_files)
        
        return bg_music_files
    
    def generate_material_combinations(self, part_files):
        """生成素材组合"""
        self.print_section("生成素材组合")
        
        # 找到文件数量最少的文件夹（决定组合数量），排除音频和背景音乐文件夹
        non_audio_files = {k: v for k, v in part_files.items() if k not in ['audios', 'bg_musics']}
        min_count = min(len(files) for files in non_audio_files.values()) if non_audio_files else 0
        
        print(f"📊 各文件夹文件数量:")
        for folder, files in part_files.items():
            if folder == 'background':
                print(f"  {folder}: {len(files)} 个图片文件")
            elif folder == 'audios':
                print(f"  {folder}: {len(files)} 个音频文件")
            elif folder == 'bg_musics':
                print(f"  {folder}: {len(files)} 个背景音乐文件")
            else:
                print(f"  {folder}: {len(files)} 个视频文件")
        
        print(f"🔢 最少文件数量: {min_count} (决定最大组合数)")
        
        # 让用户选择处理模式
        mode_options = [
            "顺序模式 (不重复，按文件名排序组合)",
            "随机裂变模式 (打乱排序，随机组合)"
        ]
        
        mode_idx, mode_str = self.get_user_choice(mode_options, "选择素材组合模式")
        self.processing_mode = "sequential" if mode_idx == 0 else "random"
        
        print(f"✅ 选择模式: {mode_str}")
        
        # 配置音频和字幕选项
        if not self.configure_audio_subtitle_options():
            return False
        
        # 如果启用了音频和字幕功能，扫描音频文件并添加到part_files
        if self.enable_audio_subtitle:
            audio_files = self.scan_audio_files()
            if audio_files:
                part_files['audios'] = audio_files
                print(f"🎵 找到 {len(audio_files)} 个音频文件")
        
        # 如果启用了背景音乐功能，扫描背景音乐文件并添加到part_files
        if self.enable_background_music:
            bg_music_files = self.scan_background_music_files()
            if bg_music_files:
                part_files['bg_musics'] = bg_music_files
                print(f"🎶 找到 {len(bg_music_files)} 个背景音乐文件")
                
        # 重新显示文件数量统计（包含音频和背景音乐文件）
        if self.enable_audio_subtitle or self.enable_background_music:
            print(f"\n📊 更新后的文件夹文件数量:")
            for folder, files in part_files.items():
                if folder == 'background':
                    print(f"  {folder}: {len(files)} 个图片文件")
                elif folder == 'audios':
                    print(f"  {folder}: {len(files)} 个音频文件")
                elif folder == 'bg_musics':
                    print(f"  {folder}: {len(files)} 个背景音乐文件")
                else:
                    print(f"  {folder}: {len(files)} 个视频文件")
        
        # 生成组合
        self.material_combinations = []
        
        if self.processing_mode == "sequential":
            # 顺序模式：按文件名排序
            sorted_parts = {}
            for folder, files in part_files.items():
                if folder not in ['audios', 'bg_musics']:
                    sorted_parts[folder] = sorted(files)
                else:
                    # 音频文件和背景音乐文件已经在对应的scan函数中按规则排序了
                    sorted_parts[folder] = files
            
            for i in range(min_count):
                combination = {}
                for folder in part_files.keys():
                    if folder in ['audios', 'bg_musics'] and folder in sorted_parts:
                        # 音频文件和背景音乐文件按自己的选择模式循环使用
                        audio_files = sorted_parts[folder]
                        if audio_files:
                            combination[folder] = audio_files[i % len(audio_files)]
                    else:
                        combination[folder] = sorted_parts[folder][i]
                self.material_combinations.append(combination)
        
        else:
            # 随机模式：打乱排序
            shuffled_parts = {}
            for folder, files in part_files.items():
                if folder not in ['audios', 'bg_musics']:
                    shuffled_files = files.copy()
                    random.shuffle(shuffled_files)
                    shuffled_parts[folder] = shuffled_files
                else:
                    # 音频文件和背景音乐文件已经在对应的scan函数中按规则排序了
                    shuffled_parts[folder] = files
            
            for i in range(min_count):
                combination = {}
                for folder in part_files.keys():
                    if folder in ['audios', 'bg_musics'] and folder in shuffled_parts:
                        # 音频文件和背景音乐文件按自己的选择模式循环使用
                        audio_files = shuffled_parts[folder]
                        if audio_files:
                            combination[folder] = audio_files[i % len(audio_files)]
                    else:
                        combination[folder] = shuffled_parts[folder][i]
                self.material_combinations.append(combination)
        
        # 显示生成的组合
        print(f"\n🎯 生成了 {len(self.material_combinations)} 个素材组合:")
        for i, combo in enumerate(self.material_combinations, 1):
            combo_name = self.generate_chinese_combo_name(combo)
            combo_display = self.format_combination_display(combo)
            print(f"  组合 {i}: {combo_display} → {combo_name}")
        
        return True
    
    def format_combination_display(self, combination):
        """格式化组合显示，包含详细的音频和字幕文件信息"""
        parts = []
        audio_info = []
        subtitle_info = []
        
        # 动态获取所有part文件夹，按数字排序
        sorted_folders = sorted([k for k in combination.keys() if k.startswith('part')], 
                               key=lambda x: int(x[4:]) if x[4:].isdigit() else 999)
        
        # 添加视频文件
        for folder in sorted_folders:
            if folder in combination:
                parts.append(combination[folder])
        
        # 添加background文件夹（如果存在）
        if 'background' in combination:
            parts.append(combination['background'])
        
        # 处理音频文件信息
        if 'audios' in combination:
            audio_file = combination['audios']
            parts.append(audio_file)
            
            # 查找对应的字幕文件（假设和音频文件同名但扩展名不同）
            audio_base = os.path.splitext(audio_file)[0]
            subtitle_file = None
            
            # 检查可能的字幕文件扩展名
            subtitle_extensions = ['.srt', '.txt', '.lrc', '.vtt']
            if hasattr(self, 'audios_folder_path'):
                for ext in subtitle_extensions:
                    potential_subtitle = f"{audio_base}{ext}"
                    subtitle_path = os.path.join(self.audios_folder_path, potential_subtitle)
                    if os.path.exists(subtitle_path):
                        subtitle_file = potential_subtitle
                        break
            
            audio_info.append(f"音频: {audio_file}")
            if subtitle_file:
                subtitle_info.append(f"字幕: {subtitle_file}")
            else:
                subtitle_info.append("字幕: 无匹配文件")
        
        # 添加bg_musics文件夹（如果存在）
        if 'bg_musics' in combination:
            bg_music = combination['bg_musics']
            parts.append(bg_music)
            audio_info.append(f"背景音乐: {bg_music}")
        
        # 构建显示字符串
        display_parts = " + ".join(parts)
        
        # 添加详细信息
        if audio_info or subtitle_info:
            detail_parts = []
            if audio_info:
                detail_parts.extend(audio_info)
            if subtitle_info:
                detail_parts.extend(subtitle_info)
            if detail_parts:
                display_parts += f" ({', '.join(detail_parts)})"
        
        return display_parts
    
    def extract_chinese_chars(self, filename):
        """从文件名中提取汉字字符"""
        # 移除文件扩展名
        name_without_ext = os.path.splitext(filename)[0]
        # 使用正则表达式提取汉字字符
        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', name_without_ext)
        if chinese_chars:
            return ''.join(chinese_chars)
        else:
            # 如果没有汉字，返回原文件名（去掉扩展名）
            return name_without_ext
    
    def generate_chinese_combo_name(self, combination):
        """根据组合生成汉字组合名称"""
        chinese_parts = []
        
        # 按顺序提取各部分的汉字
        # 动态创建所有必要的文件夹
        dynamic_folders = self.discover_part_folders() + ['background']
        for folder in dynamic_folders:
            if folder in combination:
                chinese_chars = self.extract_chinese_chars(combination[folder])
                chinese_parts.append(chinese_chars)
        
        # 组合汉字
        combo_name = "".join(chinese_parts)
        return combo_name if combo_name else "未命名"
    
    def batch_process_drafts(self):
        """批量处理草稿"""
        if not self.material_combinations:
            self.print_error("没有可用的素材组合")
            return False
        
        # 清空之前记录的视频文件列表
        self.last_replaced_videos = []
        
        self.print_header("批量复制草稿并替换素材")
        
        total_combinations = len(self.material_combinations)
        print(f"📊 将创建 {total_combinations} 个草稿副本")
        
        # 确认开始处理
        confirm = self.get_user_input(f"确认开始批量处理 {total_combinations} 个草稿? (y/n)", allow_empty=True)
        if confirm.lower() not in ['y', 'yes', '']:
            print("❌ 用户取消操作")
            return False
        
        # 获取源草稿信息
        source_draft_info = self.load_draft_info_from_file(self.selected_draft)
        if not source_draft_info:
            self.print_error("无法读取源草稿信息")
            return False
        
        successful_drafts = []
        failed_drafts = []
        used_names = set()  # 跟踪已使用的名称
        
        # 批量处理，添加重试机制
        for i, combination in enumerate(self.material_combinations, 1):
            print(f"\n🔄 处理组合 {i}/{total_combinations}")
            
            # 显示详细的组合信息
            combo_display = self.format_combination_display(combination)
            combo_name = self.generate_chinese_combo_name(combination)
            print(f"   📋 组合内容: {combo_display}")
            print(f"   🎯 目标名称: {combo_name}")
            
            # 生成新草稿名称（使用汉字组合）
            base_target_name = f"{self.selected_draft}_{combo_name}"
            
            # 检查名称是否重复，如果重复则添加序号
            target_name = base_target_name
            counter = 1
            while target_name in used_names:
                target_name = f"{base_target_name}_{counter}"
                counter += 1
            used_names.add(target_name)
            
            # 重试机制：最多尝试3次
            max_retries = 3
            success = False
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        print(f"  🔄 重试第 {attempt} 次...")
                    
                    # 复制草稿
                    print(f"  📋 复制草稿: {target_name}")
                    copy_success = self.copy_single_draft(target_name)
                    
                    if copy_success:
                        # 替换素材
                        print(f"  🔄 替换素材...")
                        replacement_success = self.replace_materials_for_draft(target_name, combination)
                        
                        if replacement_success:
                            successful_drafts.append(target_name)
                            print(f"  ✅ 组合 {i} 处理成功" + (f" (第{attempt+1}次尝试)" if attempt > 0 else ""))
                            success = True
                            break
                        else:
                            last_error = "素材替换失败"
                            print(f"  ⚠️ 组合 {i} 素材替换失败" + (f" (第{attempt+1}次尝试)" if attempt > 0 else ""))
                    else:
                        last_error = "草稿复制失败"
                        print(f"  ⚠️ 组合 {i} 草稿复制失败" + (f" (第{attempt+1}次尝试)" if attempt > 0 else ""))
                    
                    # 如果不是最后一次尝试，等待一会儿再重试
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(1)
                
                except Exception as e:
                    last_error = str(e)
                    print(f"  ⚠️ 组合 {i} 处理出错: {e}" + (f" (第{attempt+1}次尝试)" if attempt > 0 else ""))
                    
                    # 如果不是最后一次尝试，等待一会儿再重试
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(1)
            
            # 如果所有重试都失败了
            if not success:
                failed_drafts.append((target_name, last_error or "未知错误"))
                print(f"  ❌ 组合 {i} 最终失败，已尝试 {max_retries} 次")
                print(f"       继续处理下一个组合，保持文字替换顺序不变")
        
        # 显示处理结果
        self.print_header("批量处理结果")
        print(f"✅ 成功处理: {len(successful_drafts)} 个草稿")
        print(f"❌ 失败: {len(failed_drafts)} 个草稿")
        
        if successful_drafts:
            print(f"\n📄 成功创建的草稿:")
            for draft_name in successful_drafts:
                print(f"  • {draft_name}")
        
        if failed_drafts:
            print(f"\n💥 失败的草稿:")
            for draft_name, error in failed_drafts:
                print(f"  • {draft_name}: {error}")
        
        # 保存成功创建的草稿列表，供文本替换功能使用，按组合顺序保存
        self.successful_drafts = successful_drafts
        
        # 保存组合顺序映射，确保文字替换时按原始顺序进行
        self.draft_combination_mapping = []
        for i, combination in enumerate(self.material_combinations, 1):
            combo_name = self.generate_chinese_combo_name(combination)
            base_target_name = f"{self.selected_draft}_{combo_name}"
            
            # 查找实际创建的草稿名称（可能有序号后缀）
            actual_draft_name = None
            for draft_name in successful_drafts:
                if draft_name.startswith(base_target_name):
                    actual_draft_name = draft_name
                    break
            
            # 记录组合信息，包括成功和失败的
            mapping_info = {
                'combination_index': i,
                'combination': combination,
                'combo_name': combo_name,
                'target_name': base_target_name,
                'actual_draft_name': actual_draft_name,
                'success': actual_draft_name is not None
            }
            self.draft_combination_mapping.append(mapping_info)
        
        print(f"\n📊 文字替换映射表已建立，共 {len(self.draft_combination_mapping)} 个组合")
        
        # 显示映射表详情
        print(f"\n📋 组合映射详情:")
        for mapping_info in self.draft_combination_mapping:
            index = mapping_info['combination_index']
            combo_name = mapping_info['combo_name']
            success = mapping_info['success']
            status = "✅ 成功" if success else "❌ 失败"
            print(f"   组合 {index}: {combo_name} - {status}")
        
        print(f"\n💡 文字替换将严格按照组合顺序 1-{len(self.draft_combination_mapping)} 进行")
        
        return len(successful_drafts) > 0
    
    def copy_single_draft(self, target_name):
        """复制单个草稿"""
        try:
            # 执行复制
            copied_script = self.draft_folder.duplicate_as_template(self.selected_draft, target_name)
        except Exception as e:
            # 新版剪映加密，使用原始复制方式
            pass
        
        # 检查是否实际创建成功
        time.sleep(0.5)  # 等待文件系统同步
        updated_drafts = self.draft_folder.list_drafts()
        
        if target_name in updated_drafts:
            return True
        else:
            return False
    
    def replace_materials_for_draft(self, draft_name, combination):
        """为指定草稿替换素材"""
        try:
            # 获取草稿信息
            draft_info = self.load_draft_info_from_file(draft_name)
            if not draft_info:
                print(f"    ❌ 无法读取草稿信息: {draft_name}")
                return False
            
            # 准备替换数据
            replacements = []
            
            # 根据替换模式处理不同类型的素材
            if self.replacement_mode in ["video", "all"]:
                video_materials = draft_info['video_materials']
                if video_materials:
                    replacements.extend(self.prepare_video_replacements(video_materials, combination))
            
            if self.replacement_mode in ["image", "all"]:
                # 处理图片素材（从draft_info中获取图片素材信息）
                image_replacements = self.prepare_image_replacements(draft_info, combination)
                if image_replacements:
                    replacements.extend(image_replacements)
            
            if not replacements:
                print(f"    ❌ 没有找到可替换的素材")
                # 如果没有常规素材替换，但有音频和字幕需要添加，仍然继续处理
                if not (self.enable_audio_subtitle and 'audios' in combination):
                    return False
            
            # 先处理常规素材替换（视频、图片）
            success = True
            if replacements:
                success = self.attempt_direct_json_replacement(draft_name, replacements)
            
            # 处理音频和字幕（使用库API）
            if self.enable_audio_subtitle and 'audios' in combination:
                audio_success = self.add_audio_and_subtitle_with_api(draft_name, combination)
                success = success and audio_success
            
            return success
            
        except Exception as e:
            print(f"    ❌ 素材替换出错: {e}")
            return False
    
    def prepare_video_replacements(self, video_materials, combination):
        """准备视频素材替换"""
        replacements = []
        
        for video in video_materials:
            video_name = video['name']
            
            # 基于素材名称匹配对应的part文件夹
            matching_folder = None
            
            # 动态检查素材名称是否包含partN关键词
            import re
            match = re.search(r'part(\d+)', video_name.lower())
            if match:
                part_num = match.group(1)
                matching_folder = f'part{part_num}'
                
                if self.debug:
                    print(f"    🔍 DEBUG 匹配素材: {video_name} → {matching_folder}")
            
            if matching_folder and matching_folder in combination:
                new_file_name = combination[matching_folder]
                new_file_path = os.path.join(self.materials_folder_path, matching_folder, new_file_name)
                
                if os.path.exists(new_file_path):
                    replacements.append({
                        'original_name': video['name'],
                        'original_id': video['id'],
                        'new_file': new_file_path,
                        'new_name': new_file_name,
                        'type': 'video',
                        'folder': matching_folder
                    })
                    print(f"    🔄 将用 {matching_folder}/{new_file_name} 替换 {video_name}")
                else:
                    print(f"    ⚠️ 文件不存在: {new_file_path}")
            else:
                print(f"    ⚠️ 无法匹配素材: {video_name}")
        
        return replacements
    
    def prepare_image_replacements(self, draft_info, combination):
        """准备图片素材替换"""
        replacements = []
        
        # 检查是否有background组合
        if 'background' not in combination:
            return replacements
        
        # 从draft_info中查找图片素材
        if 'materials' in draft_info.get('raw_data', {}):
            materials = draft_info['raw_data']['materials']
            
            # 查找图片素材
            for material_type in ['images', 'stickers']:
                if material_type in materials:
                    for image in materials[material_type]:
                        if isinstance(image, dict):
                            image_name = image.get('material_name', image.get('name', ''))
                            
                            # 检查是否是background相关的图片
                            if 'background' in image_name.lower():
                                new_file_name = combination['background']
                                new_file_path = os.path.join(self.materials_folder_path, 'background', new_file_name)
                                
                                if os.path.exists(new_file_path):
                                    replacements.append({
                                        'original_name': image_name,
                                        'original_id': image.get('id', ''),
                                        'new_file': new_file_path,
                                        'new_name': new_file_name,
                                        'type': 'image',
                                        'folder': 'background'
                                    })
                                    print(f"    🔄 将用 background/{new_file_name} 替换 {image_name}")
                                else:
                                    print(f"    ⚠️ 文件不存在: {new_file_path}")
        
        return replacements
    
    def prepare_audio_replacements(self, draft_info, combination):
        """准备音频素材替换"""
        replacements = []
        
        if 'audios' not in combination:
            return replacements
        
        new_audio_file = combination['audios']
        new_audio_path = os.path.join(self.audios_folder_path, new_audio_file)
        
        if not os.path.exists(new_audio_path):
            print(f"    ⚠️ 音频文件不存在: {new_audio_path}")
            return replacements
        
        # 查找现有的音频素材
        existing_audio = None
        if 'materials' in draft_info.get('raw_data', {}):
            materials = draft_info['raw_data']['materials']
            if 'audios' in materials:
                for audio in materials['audios']:
                    if isinstance(audio, dict):
                        existing_audio = audio
                        break
        
        if existing_audio:
            # 替换现有音频素材
            replacements.append({
                'original_name': existing_audio.get('material_name', existing_audio.get('name', '')),
                'original_id': existing_audio.get('id', ''),
                'new_file': new_audio_path,
                'new_name': new_audio_file,
                'type': 'audio',
                'folder': 'audios',
                'mode': 'replace'
            })
            print(f"    🔄 将替换音频素材: {existing_audio.get('material_name', '')} → {new_audio_file}")
        else:
            # 添加新的音频素材
            replacements.append({
                'original_name': '',
                'original_id': '',
                'new_file': new_audio_path,
                'new_name': new_audio_file,
                'type': 'audio',
                'folder': 'audios',
                'mode': 'add'
            })
            print(f"    ➕ 将添加新音频素材: {new_audio_file}")
        
        return replacements
    
    def attempt_direct_json_replacement(self, draft_name, replacements):
        """直接操作草稿文件进行素材替换 (兼容多版本格式)"""
        try:
            # 使用兼容性方法获取草稿文件路径
            draft_file_path = self.get_compatible_draft_file_path(draft_name)
            
            if not draft_file_path:
                self.print_error(f"草稿文件不存在，已检查 draft_info.json 和 draft_content.json")
                return False
            
            # 读取当前的草稿文件
            with open(draft_file_path, 'r', encoding='utf-8') as f:
                draft_info = json.load(f)
            
            # 备份原文件
            backup_path = draft_file_path + ".backup"
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(draft_info, f, ensure_ascii=False, indent=2)
            
            success_count = 0
            
            # 分别处理视频、图片和音频素材
            for replacement in replacements:
                if replacement['type'] == 'video':
                    if self.replace_video_material(draft_info, replacement, draft_name):
                        success_count += 1
                elif replacement['type'] == 'image':
                    if self.replace_image_material(draft_info, replacement, draft_name):
                        success_count += 1
                elif replacement['type'] == 'audio':
                    if self.replace_audio_material(draft_info, replacement, draft_name):
                        success_count += 1
            
            if success_count > 0:
                # 保存更新后的草稿文件
                with open(draft_file_path, 'w', encoding='utf-8') as f:
                    json.dump(draft_info, f, ensure_ascii=False, indent=2)
                
                print(f"    ✅ 素材替换完成! 成功替换 {success_count}/{len(replacements)} 个素材")
                return True
            else:
                print(f"    ❌ 没有成功替换任何素材")
                return False
                
        except Exception as e:
            print(f"    ❌ 直接JSON替换失败: {e}")
            return False
    
    def replace_video_material(self, draft_info, replacement, draft_name):
        """替换视频素材"""
        try:
            # 创建video materials目录
            materials_dir = os.path.join(self.draft_folder_path, draft_name, "materials", "video")
            if not os.path.exists(materials_dir):
                os.makedirs(materials_dir, exist_ok=True)
            
            # 查找并更新视频素材
            if 'materials' in draft_info and 'videos' in draft_info['materials']:
                videos = draft_info['materials']['videos']
                
                for video in videos:
                    if video.get('material_name') == replacement['original_name']:
                        # 获取原始片段在时间线上的实际使用时长
                        original_duration = self.get_actual_segment_duration(draft_info, video.get('id'))
                        
                        # 如果获取不到实际片段时长，使用素材时长作为备选
                        if not original_duration:
                            original_duration = video.get('duration', 0)
                            print(f"    💡 使用素材总时长作为原始时长: {original_duration/1000000:.1f}s")
                        else:
                            print(f"    🎯 获取实际片段时长: {original_duration/1000000:.1f}s")
                        
                        # 复制新文件到草稿materials目录
                        new_filename = replacement['new_name']
                        target_path = os.path.join(materials_dir, new_filename)
                        
                        shutil.copy2(replacement['new_file'], target_path)
                        
                        # 记录最近替换的视频文件（用于封面图生成）
                        if not hasattr(self, 'last_replaced_videos'):
                            self.last_replaced_videos = []
                        self.last_replaced_videos.append(replacement['new_file'])
                        
                        # 获取新文件的信息
                        new_file_info = self.get_video_file_info(replacement['new_file'])
                        new_duration = new_file_info.get('duration', 0) if new_file_info else 0
                        
                        if self.debug:
                            print(f"    🔍 DEBUG: 原始时长 {original_duration} 微秒, 新时长 {new_duration} 微秒")
                            print(f"    🔍 DEBUG: 新文件信息: {new_file_info}")
                            print(f"    🔍 DEBUG: 文件路径: {replacement['new_file']}")
                        
                        # 计算速度调整比例 (让新素材适应原始时长)
                        speed_ratio = 1.0
                        if original_duration > 0 and new_duration > 0:
                            # 计算时长差异
                            duration_diff = abs(new_duration - original_duration) / 1000000  # 转换为秒
                            
                            # 如果差异在1秒内，允许最后一帧填充，不调整速度
                            if duration_diff <= 1.0:
                                speed_ratio = 1.0
                                print(f"    📊 时长调整: 原始{original_duration/1000000:.1f}s → 新素材{new_duration/1000000:.1f}s → 差异{duration_diff:.1f}s≤1s，保持原速")
                            else:
                                # 速度 = 新素材时长 / 原始时长 (让新素材播放时间适应原始时长)
                                speed_ratio = new_duration / original_duration
                                action = "加速" if speed_ratio > 1.0 else "减速" if speed_ratio < 1.0 else "保持"
                                print(f"    📊 时长调整: 原始{original_duration/1000000:.1f}s → 新素材{new_duration/1000000:.1f}s → {action}{speed_ratio:.2f}x")
                        
                        # 更新素材信息
                        video['material_name'] = new_filename
                        video['path'] = f"##_draftpath_placeholder_0E685133-18CE-45ED-8CB8-2904A212EC80_##/materials/video/{new_filename}"
                        
                        # 更新素材时长为新素材的实际时长
                        video['duration'] = new_duration
                        
                        if new_file_info:
                            if 'width' in new_file_info:
                                video['width'] = new_file_info['width']
                            if 'height' in new_file_info:
                                video['height'] = new_file_info['height']
                        
                        # 查找并更新使用此素材的片段，设置速度
                        if speed_ratio != 1.0:
                            self.update_segments_speed(draft_info, video.get('id'), speed_ratio, new_duration)
                        
                        print(f"    ✅ 更新视频素材: {replacement['original_name']} → {new_filename}")
                        return True
            
            return False
            
        except Exception as e:
            print(f"    ❌ 替换视频素材失败 {replacement['original_name']}: {e}")
            return False
    
    def update_segments_speed(self, draft_info, material_id, speed_ratio, new_material_duration=None):
        """更新使用指定素材的片段速度"""
        try:
            if 'tracks' not in draft_info:
                return
            
            updated_segments = 0
            
            # 创建Speed对象并添加到speeds数组
            import uuid
            speed_id = uuid.uuid4().hex
            speed_obj = {
                "curve_speed": None,
                "id": speed_id,
                "mode": 0,
                "speed": speed_ratio,
                "type": "speed"
            }
            
            # 确保speeds数组存在
            if 'speeds' not in draft_info:
                draft_info['speeds'] = []
            
            # 添加speed对象到speeds数组
            draft_info['speeds'].append(speed_obj)
            
            for track in draft_info['tracks']:
                if track.get('type') == 'video' and 'segments' in track:
                    segments = track['segments']
                    
                    for segment in segments:
                        # 检查片段是否使用了指定的素材
                        if segment.get('material_id') == material_id:
                            if self.debug:
                                print(f"    🔍 DEBUG segment结构: {list(segment.keys())}")
                                if 'target_timerange' in segment:
                                    print(f"    🔍 DEBUG target_timerange: {segment['target_timerange']}")
                                if 'source_timerange' in segment:
                                    print(f"    🔍 DEBUG source_timerange: {segment['source_timerange']}")
                            
                            # 更新source_timerange以适应新素材时长
                            if new_material_duration and 'source_timerange' in segment:
                                # 保持source_timerange的start不变，只更新duration
                                source_start = segment['source_timerange'].get('start', 0)
                                segment['source_timerange']['duration'] = new_material_duration
                                
                                if self.debug:
                                    print(f"    🔍 DEBUG 更新source_timerange: start={source_start}, duration={new_material_duration}")
                            
                            # 更新片段速度引用
                            segment['speed'] = speed_ratio
                            
                            # 更新extra_material_refs，添加speed_id引用
                            if 'extra_material_refs' not in segment:
                                segment['extra_material_refs'] = []
                            
                            # 移除旧的speed引用（如果存在）
                            segment['extra_material_refs'] = [ref for ref in segment['extra_material_refs'] 
                                                            if not any(speed.get('id') == ref for speed in draft_info.get('speeds', []))]
                            
                            # 添加新的speed引用
                            segment['extra_material_refs'].append(speed_id)
                            
                            updated_segments += 1
                            print(f"    🎬 更新片段速度: {speed_ratio:.2f}x (ID: {speed_id})")
            
            if updated_segments == 0:
                print(f"    ⚠️ 未找到使用素材 {material_id} 的片段")
                # 如果没有使用到，移除刚创建的speed对象
                draft_info['speeds'] = [s for s in draft_info['speeds'] if s['id'] != speed_id]
            
        except Exception as e:
            print(f"    ❌ 更新片段速度失败: {e}")
    
    def replace_image_material(self, draft_info, replacement, draft_name):
        """替换图片素材"""
        try:
            # 创建image materials目录
            materials_dir = os.path.join(self.draft_folder_path, draft_name, "materials", "image")
            if not os.path.exists(materials_dir):
                os.makedirs(materials_dir, exist_ok=True)
            
            # 查找并更新图片素材
            if 'materials' in draft_info:
                for material_type in ['images', 'stickers']:
                    if material_type in draft_info['materials']:
                        images = draft_info['materials'][material_type]
                        
                        for image in images:
                            if isinstance(image, dict) and image.get('material_name') == replacement['original_name']:
                                # 复制新文件到草稿materials目录
                                new_filename = replacement['new_name']
                                target_path = os.path.join(materials_dir, new_filename)
                                
                                shutil.copy2(replacement['new_file'], target_path)
                                
                                # 获取新文件的信息
                                new_file_info = self.get_image_file_info(replacement['new_file'])
                                
                                # 更新素材信息
                                image['material_name'] = new_filename
                                image['path'] = f"##_draftpath_placeholder_0E685133-18CE-45ED-8CB8-2904A212EC80_##/materials/image/{new_filename}"
                                
                                if new_file_info:
                                    if 'width' in new_file_info:
                                        image['width'] = new_file_info['width']
                                    if 'height' in new_file_info:
                                        image['height'] = new_file_info['height']
                                
                                print(f"    ✅ 更新图片素材: {replacement['original_name']} → {new_filename}")
                                return True
            
            return False
            
        except Exception as e:
            print(f"    ❌ 替换图片素材失败 {replacement['original_name']}: {e}")
            return False
    
    def get_image_file_info(self, image_path):
        """获取图片文件信息"""
        try:
            from PIL import Image
            with Image.open(image_path) as img:
                width, height = img.size
                return {
                    'width': width,
                    'height': height
                }
        except Exception:
            # 如果PIL不可用，返回基础信息
            try:
                file_size = os.path.getsize(image_path)
                return {'width': 1920, 'height': 1080}  # 默认分辨率
            except:
                return None
    
    def replace_audio_material(self, draft_info, replacement, draft_name):
        """替换或添加音频素材"""
        try:
            # 创建audio materials目录
            materials_dir = os.path.join(self.draft_folder_path, draft_name, "materials", "audio")
            if not os.path.exists(materials_dir):
                os.makedirs(materials_dir, exist_ok=True)
            
            # 复制新文件到草稿materials目录
            new_filename = replacement['new_name']
            target_path = os.path.join(materials_dir, new_filename)
            shutil.copy2(replacement['new_file'], target_path)
            
            # 获取新文件的信息
            new_audio_info = self.get_audio_file_info(replacement['new_file'])
            new_duration = new_audio_info.get('duration', 0) if new_audio_info else 0
            
            if replacement['mode'] == 'replace' and replacement['original_name']:
                # 替换现有音频素材
                if 'materials' in draft_info and 'audios' in draft_info['materials']:
                    audios = draft_info['materials']['audios']
                    
                    for audio in audios:
                        if isinstance(audio, dict) and audio.get('material_name') == replacement['original_name']:
                            # 更新素材信息
                            audio['material_name'] = new_filename
                            audio['path'] = f"##_draftpath_placeholder_0E685133-18CE-45ED-8CB8-2904A212EC80_##/materials/audio/{new_filename}"
                            audio['duration'] = new_duration
                            
                            # 应用音量设置
                            if hasattr(self, 'audio_volume') and self.audio_volume != 100:
                                # 音量设置会在片段级别应用
                                pass
                            
                            print(f"    ✅ 更新音频素材: {replacement['original_name']} → {new_filename}")
                            
                            # 处理字幕导入
                            if self.enable_subtitles:
                                self.import_audio_subtitle(draft_info, replacement['new_file'], draft_name)
                            
                            return True
            else:
                # 添加新音频素材
                import uuid
                audio_id = uuid.uuid4().hex
                
                audio_material = {
                    "check_flag": 63487,
                    "duration": new_duration,
                    "extra_type_option": 0,
                    "file_Path": "",
                    "height": 0,
                    "id": audio_id,
                    "intensifies_audio_path": "",
                    "intensifies_path": "",
                    "is_ai_generate_content": False,
                    "local_material_id": "",
                    "material_id": "",
                    "material_name": new_filename,
                    "material_type": "audio",
                    "path": f"##_draftpath_placeholder_0E685133-18CE-45ED-8CB8-2904A212EC80_##/materials/audio/{new_filename}",
                    "request_id": "",
                    "reverse_intensifies_path": "",
                    "reverse_path": "",
                    "source_platform": 0,
                    "stable_id": "",
                    "team_id": "",
                    "type": "audio",
                    "width": 0
                }
                
                # 确保materials结构存在
                if 'materials' not in draft_info:
                    draft_info['materials'] = {}
                if 'audios' not in draft_info['materials']:
                    draft_info['materials']['audios'] = []
                
                # 添加音频素材
                draft_info['materials']['audios'].append(audio_material)
                
                # 添加音频轨道和片段
                self.add_audio_track_and_segment(draft_info, audio_material, new_duration)
                
                print(f"    ✅ 添加新音频素材: {new_filename}")
                
                # 处理字幕导入
                if self.enable_subtitles:
                    self.import_audio_subtitle(draft_info, replacement['new_file'], draft_name)
                
                return True
            
            return False
            
        except Exception as e:
            print(f"    ❌ 处理音频素材失败 {replacement['new_name']}: {e}")
            return False
    
    def get_audio_file_info(self, audio_path):
        """获取音频文件信息"""
        try:
            # 尝试使用pyJianYingDraft的AudioMaterial
            from pyJianYingDraft import AudioMaterial
            audio_material = AudioMaterial(audio_path)
            
            return {
                'duration': audio_material.duration  # 微秒
            }
        except Exception as e:
            print(f"    ⚠️ 使用AudioMaterial获取音频信息失败: {e}")
            
            # 备用方法：使用ffprobe
            try:
                import subprocess
                cmd = [
                    'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format',
                    audio_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    import json
                    info = json.loads(result.stdout)
                    
                    if 'format' in info and 'duration' in info['format']:
                        duration_sec = float(info['format']['duration'])
                        return {'duration': int(duration_sec * 1000000)}  # 转换为微秒
                
                return {'duration': 30000000}  # 默认30秒
                
            except Exception as e2:
                print(f"    ⚠️ ffprobe方法也失败: {e2}")
                return {'duration': 30000000}  # 默认30秒
    
    def add_audio_track_and_segment(self, draft_info, audio_material, audio_duration):
        """添加音频轨道和片段"""
        try:
            # 确保tracks结构存在
            if 'tracks' not in draft_info:
                draft_info['tracks'] = []
            
            # 查找或创建音频轨道
            audio_track = None
            for track in draft_info['tracks']:
                if track.get('type') == 'audio':
                    audio_track = track
                    break
            
            if not audio_track:
                # 创建新的音频轨道
                import uuid
                track_id = uuid.uuid4().hex
                
                audio_track = {
                    "attribute": 0,
                    "flag": 0,
                    "id": track_id,
                    "segments": [],
                    "type": "audio"
                }
                draft_info['tracks'].append(audio_track)
            
            # 创建音频片段
            import uuid
            segment_id = uuid.uuid4().hex
            
            # 计算目标时长（根据配置处理音频长度）
            target_duration = self.calculate_target_audio_duration(draft_info, audio_duration)
            
            audio_segment = {
                "cartoon": False,
                "clip": {
                    "alpha": 1.0,
                    "flip": {
                        "horizontal": False,
                        "vertical": False
                    },
                    "rotation": 0.0,
                    "scale": {
                        "x": 1.0,
                        "y": 1.0
                    },
                    "transform": {
                        "x": 0.0,
                        "y": 0.0
                    }
                },
                "common_keyframes": [],
                "enable_adjust": True,
                "enable_color_curves": True,
                "enable_color_match_adjust": False,
                "enable_color_wheels": True,
                "enable_lut": True,
                "enable_smart_color_adjust": False,
                "extra_material_refs": [],
                "group_id": "",
                "hdr_settings": None,
                "id": segment_id,
                "intensifies_audio": False,
                "is_placeholder": False,
                "is_tone_modify": False,
                "keyframe_refs": [],
                "last_nonzero_volume": 1.0,
                "material_id": audio_material['id'],
                "render_index": 0,
                "reverse": False,
                "source_timerange": {
                    "duration": audio_duration,
                    "start": 0
                },
                "speed": 1.0,
                "target_timerange": {
                    "duration": target_duration,
                    "start": 0
                },
                "template_id": "",
                "template_scene": "default",
                "track_attribute": 0,
                "track_render_index": 0,
                "uniform_scale": {
                    "on": True,
                    "value": 1.0
                },
                "visible": True,
                "volume": self.audio_volume / 100.0  # 转换为0-1范围
            }
            
            # 应用淡入淡出
            if self.audio_fade_in > 0 or self.audio_fade_out > 0:
                self.apply_audio_fade(audio_segment, target_duration)
            
            # 添加片段到轨道
            audio_track['segments'].append(audio_segment)
            
            print(f"    🎵 添加音频片段到轨道，时长: {target_duration/1000000:.1f}s，音量: {self.audio_volume}%")
            
        except Exception as e:
            print(f"    ❌ 添加音频轨道和片段失败: {e}")
    
    def calculate_target_audio_duration(self, draft_info, audio_duration):
        """根据配置计算目标音频时长"""
        try:
            # 获取视频总时长
            video_duration = draft_info.get('duration', 0)
            
            if video_duration <= 0:
                return audio_duration
            
            # 根据配置处理音频长度
            if audio_duration > video_duration:
                # 音频比视频长
                if self.audio_longer_handling == "speed_up":
                    # 加速音频以适应视频长度
                    return video_duration
                elif self.audio_longer_handling == "trim":
                    # 裁剪音频
                    return video_duration
                else:
                    # 保持原样
                    return audio_duration
                    
            elif audio_duration < video_duration:
                # 音频比视频短
                if self.audio_shorter_handling == "trim_video":
                    # 裁剪视频
                    # 这里返回音频长度，视频裁剪需要在其他地方处理
                    return audio_duration
                elif self.audio_shorter_handling == "slow_down":
                    # 减速音频以适应视频长度
                    return video_duration
                else:
                    # 保持原样或允许静音
                    return audio_duration
            
            return audio_duration
            
        except Exception as e:
            print(f"    ⚠️ 计算目标音频时长失败: {e}")
            return audio_duration
    
    def apply_audio_fade(self, audio_segment, duration):
        """应用音频淡入淡出效果"""
        try:
            fade_in_duration = int(self.audio_fade_in * 1000000)  # 转换为微秒
            fade_out_duration = int(self.audio_fade_out * 1000000)  # 转换为微秒
            
            # 创建音量关键帧
            keyframes = []
            
            if fade_in_duration > 0:
                # 淡入关键帧
                keyframes.extend([
                    {"time": 0, "value": 0.0},
                    {"time": min(fade_in_duration, duration), "value": self.audio_volume / 100.0}
                ])
            
            if fade_out_duration > 0 and duration > fade_out_duration:
                # 淡出关键帧
                fade_start = duration - fade_out_duration
                keyframes.extend([
                    {"time": fade_start, "value": self.audio_volume / 100.0},
                    {"time": duration, "value": 0.0}
                ])
            
            if keyframes:
                # 添加音量关键帧到片段
                audio_segment['volume_keyframes'] = keyframes
                print(f"    🎚️ 应用音频淡入淡出: 淡入{self.audio_fade_in}s, 淡出{self.audio_fade_out}s")
            
        except Exception as e:
            print(f"    ⚠️ 应用音频淡入淡出失败: {e}")
    
    def import_audio_subtitle(self, draft_info, audio_file_path, draft_name):
        """导入音频对应的字幕文件"""
        try:
            # 查找对应的SRT文件
            audio_name = os.path.splitext(os.path.basename(audio_file_path))[0]
            srt_file_path = os.path.join(os.path.dirname(audio_file_path), f"{audio_name}.srt")
            
            if not os.path.exists(srt_file_path):
                print(f"    💬 未找到字幕文件: {audio_name}.srt")
                return False
            
            # 使用pyJianYingDraft的字幕导入功能
            # 这里需要创建一个临时的ScriptFile对象来使用import_srt方法
            print(f"    📝 找到字幕文件: {audio_name}.srt")
            
            # 由于这是直接操作JSON，我们需要手动解析SRT并添加文本片段
            subtitle_segments = self.parse_srt_file(srt_file_path)
            if subtitle_segments:
                self.add_subtitle_track_and_segments(draft_info, subtitle_segments)
                print(f"    ✅ 导入字幕: {len(subtitle_segments)} 条字幕")
                return True
            
            return False
            
        except Exception as e:
            print(f"    ❌ 导入字幕失败: {e}")
            return False
    
    def parse_srt_file(self, srt_file_path):
        """解析SRT字幕文件"""
        try:
            subtitle_segments = []
            
            with open(srt_file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # 按空行分割字幕块
            blocks = content.split('\n\n')
            
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) >= 3:
                    # 序号
                    index = lines[0].strip()
                    
                    # 时间范围
                    time_line = lines[1].strip()
                    time_parts = time_line.split(' --> ')
                    if len(time_parts) == 2:
                        start_time = self.parse_srt_time(time_parts[0])
                        end_time = self.parse_srt_time(time_parts[1])
                        
                        # 字幕文本
                        text = '\n'.join(lines[2:])
                        
                        subtitle_segments.append({
                            'start': start_time,
                            'end': end_time,
                            'duration': end_time - start_time,
                            'text': text
                        })
            
            return subtitle_segments
            
        except Exception as e:
            print(f"    ❌ 解析SRT文件失败: {e}")
            return []
    
    def parse_srt_time(self, time_str):
        """解析SRT时间格式为微秒"""
        try:
            # 格式: 00:00:20,000
            time_str = time_str.replace(',', '.')
            parts = time_str.split(':')
            
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            
            total_seconds = hours * 3600 + minutes * 60 + seconds
            return int(total_seconds * 1000000)  # 转换为微秒
            
        except Exception as e:
            print(f"    ⚠️ 解析时间失败: {time_str}, {e}")
            return 0
    
    def add_subtitle_track_and_segments(self, draft_info, subtitle_segments):
        """添加字幕轨道和片段"""
        try:
            # 确保tracks结构存在
            if 'tracks' not in draft_info:
                draft_info['tracks'] = []
            
            # 查找或创建文本轨道
            text_track = None
            for track in draft_info['tracks']:
                if track.get('type') == 'text':
                    text_track = track
                    break
            
            if not text_track:
                # 创建新的文本轨道
                import uuid
                track_id = uuid.uuid4().hex
                
                text_track = {
                    "attribute": 0,
                    "flag": 0,
                    "id": track_id,
                    "segments": [],
                    "type": "text"
                }
                draft_info['tracks'].append(text_track)
            
            # 为每个字幕创建文本片段
            for subtitle in subtitle_segments:
                import uuid
                segment_id = uuid.uuid4().hex
                material_id = uuid.uuid4().hex
                
                # 创建文本素材
                text_material = {
                    "alignment": 1,
                    "background_alpha": 1.0,
                    "background_color": "",
                    "background_height": 0.04,
                    "background_horizontal_offset": 0.0,
                    "background_round_radius": 0.0,
                    "background_style": 0,
                    "background_vertical_offset": 0.0,
                    "background_width": 0.04,
                    "bold_width": 0.0,
                    "border_alpha": 1.0,
                    "border_color": "#000000",
                    "border_width": 0.016,
                    "check_flag": 7,
                    "combo_info": {
                        "text_templates": []
                    },
                    "font_category": 0,
                    "font_path": "",
                    "font_resource_id": "",
                    "font_size": 0.06,
                    "font_title": "思源黑体 CN Medium",
                    "font_url": "",
                    "fonts": [
                        {
                            "font_path": "",
                            "font_title": "思源黑体 CN Medium"
                        }
                    ],
                    "force_apply_line_max_width": False,
                    "global_alpha": 1.0,
                    "has_shadow": True,
                    "id": material_id,
                    "initial_scale": 1.0,
                    "is_rich_text": False,
                    "italic_degree": 0,
                    "ktv_color": "",
                    "layer_weight": 1,
                    "letter_spacing": 0.0,
                    "line_spacing": 0.02,
                    "material_type": "text",
                    "name": "",
                    "preset_category": "",
                    "preset_category_id": "",
                    "preset_has_set_alignment": False,
                    "preset_id": "",
                    "preset_index": 0,
                    "preset_name": "",
                    "recognize_type": 0,
                    "relevance_segment": [],
                    "shadow_alpha": 0.8,
                    "shadow_angle": -45.0,
                    "shadow_color": "#000000",
                    "shadow_distance": 0.005,
                    "shadow_point": {
                        "x": 0.003535534143447876,
                        "y": -0.003535534143447876
                    },
                    "shadow_smoothness": 0.45,
                    "shape_clip_x": False,
                    "shape_clip_y": False,
                    "style_name": "",
                    "sub_type": 0,
                    "text": subtitle['text'],
                    "text_alpha": 1.0,
                    "text_color": "#FFFFFF",
                    "text_curve": None,
                    "text_preset_resource_id": "",
                    "text_size": 30,
                    "text_to_audio_ids": [],
                    "tts_auto_update": False,
                    "type": "text",
                    "typesetting": 0,
                    "underline": False,
                    "underline_offset": 0.22,
                    "underline_width": 0.05,
                    "use_effect_default_color": True,
                    "words": [
                        {
                            "end_time": subtitle['end'],
                            "start_time": subtitle['start'],
                            "text": subtitle['text']
                        }
                    ]
                }
                
                # 添加文本素材到materials
                if 'materials' not in draft_info:
                    draft_info['materials'] = {}
                if 'texts' not in draft_info['materials']:
                    draft_info['materials']['texts'] = []
                
                draft_info['materials']['texts'].append(text_material)
                
                # 创建文本片段
                text_segment = {
                    "cartoon": False,
                    "clip": {
                        "alpha": 1.0,
                        "flip": {
                            "horizontal": False,
                            "vertical": False
                        },
                        "rotation": 0.0,
                        "scale": {
                            "x": 1.0,
                            "y": 1.0
                        },
                        "transform": {
                            "x": 0.0,
                            "y": 0.35  # 字幕位置
                        }
                    },
                    "common_keyframes": [],
                    "enable_adjust": True,
                    "enable_color_curves": True,
                    "enable_color_match_adjust": False,
                    "enable_color_wheels": True,
                    "enable_lut": True,
                    "enable_smart_color_adjust": False,
                    "extra_material_refs": [],
                    "group_id": "",
                    "hdr_settings": None,
                    "id": segment_id,
                    "intensifies_audio": False,
                    "is_placeholder": False,
                    "is_tone_modify": False,
                    "keyframe_refs": [],
                    "last_nonzero_volume": 1.0,
                    "material_id": material_id,
                    "render_index": 0,
                    "reverse": False,
                    "source_timerange": {
                        "duration": subtitle['duration'],
                        "start": 0
                    },
                    "speed": 1.0,
                    "target_timerange": {
                        "duration": subtitle['duration'],
                        "start": subtitle['start']
                    },
                    "template_id": "",
                    "template_scene": "default",
                    "track_attribute": 0,
                    "track_render_index": 0,
                    "uniform_scale": {
                        "on": True,
                        "value": 1.0
                    },
                    "visible": True,
                    "volume": 1.0
                }
                
                # 添加片段到文本轨道
                text_track['segments'].append(text_segment)
            
        except Exception as e:
            print(f"    ❌ 添加字幕轨道和片段失败: {e}")
    
    def load_draft_as_script_file(self, draft_name):
        """加载草稿为ScriptFile对象，兼容不同版本的文件结构"""
        draft_path = os.path.join(self.draft_folder_path, draft_name)
        
        # 首先尝试新版本格式 (draft_content.json)
        draft_content_path = os.path.join(draft_path, "draft_content.json")
        if os.path.exists(draft_content_path):
            print(f"    📄 找到 draft_content.json，使用新版本格式")
            return draft.ScriptFile.load_template(draft_content_path)
        
        # 然后尝试5.9版本格式 (draft_info.json)
        draft_info_path = os.path.join(draft_path, "draft_info.json")
        if os.path.exists(draft_info_path):
            print(f"    📄 找到 draft_info.json，使用5.9版本格式")
            return self.convert_draft_info_to_script_file(draft_info_path, draft_path)
        
        raise FileNotFoundError(f"既没有找到 draft_content.json 也没有找到 draft_info.json 在草稿 {draft_name} 中")
    
    def convert_draft_info_to_script_file(self, draft_info_path, draft_path):
        """将 draft_info.json 转换为 ScriptFile 对象"""
        import tempfile
        import json
        
        # 读取 draft_info.json
        with open(draft_info_path, 'r', encoding='utf-8') as f:
            draft_info = json.load(f)
        
        # 创建临时的 draft_content.json 文件
        # 基本上 draft_info.json 的结构就是 draft_content.json 的结构
        # 只是文件名不同
        temp_dir = tempfile.mkdtemp()
        temp_draft_content = os.path.join(temp_dir, "draft_content.json")
        
        # 直接复制内容，因为格式基本相同
        with open(temp_draft_content, 'w', encoding='utf-8') as f:
            json.dump(draft_info, f, ensure_ascii=False, indent=2)
        
        # 使用临时文件创建 ScriptFile
        script = draft.ScriptFile.load_template(temp_draft_content)
        
        # 设置正确的保存路径
        script.save_path = draft_info_path
        
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir)
        
        return script
    
    def replace_path_placeholders_in_script(self, script, draft_path):
        """替换script中所有的路径占位符为实际路径"""
        try:
            # 定义占位符
            placeholder = "##_draftpath_placeholder_0E685133-18CE-45ED-8CB8-2904A212EC80_##"
            
            # 递归替换JSON对象中的所有路径占位符
            def replace_placeholders_recursive(obj):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if isinstance(value, str) and placeholder in value:
                            obj[key] = value.replace(placeholder, draft_path)
                            if self.debug:
                                print(f"🔧 替换占位符: {key} = {obj[key]}")
                        elif isinstance(value, (dict, list)):
                            replace_placeholders_recursive(value)
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        if isinstance(item, str) and placeholder in item:
                            obj[i] = item.replace(placeholder, draft_path)
                            if self.debug:
                                print(f"🔧 替换占位符: [list] = {obj[i]}")
                        elif isinstance(item, (dict, list)):
                            replace_placeholders_recursive(item)
            
            # 替换script.content中的所有占位符
            replace_placeholders_recursive(script.content)
            
            print(f"✅ 已替换所有路径占位符: {placeholder} → {draft_path}")
                
        except Exception as e:
            print(f"❌ 替换路径占位符时出错: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
    
    def update_draft_meta_info(self, draft_path):
        """更新草稿元信息文件的时间戳，确保剪映能检测到变更"""
        try:
            import time
            
            meta_info_path = os.path.join(draft_path, "draft_meta_info.json")
            if not os.path.exists(meta_info_path):
                print(f"⚠️ draft_meta_info.json 不存在: {meta_info_path}")
                return
            
            # 读取现有的元信息
            with open(meta_info_path, 'r', encoding='utf-8') as f:
                meta_info = json.load(f)
            
            # 更新时间戳（使用微秒时间戳，与剪映格式一致）
            current_time = int(time.time() * 1000000)  # 微秒时间戳
            
            meta_info['tm_draft_modified'] = current_time
            
            # 如果存在 tm_draft_cloud_modified，也更新它
            if 'tm_draft_cloud_modified' in meta_info:
                meta_info['tm_draft_cloud_modified'] = current_time
            
            # 写回文件
            with open(meta_info_path, 'w', encoding='utf-8') as f:
                json.dump(meta_info, f, ensure_ascii=False, indent=None, separators=(',', ':'))
            
            print(f"✅ 已更新草稿元信息时间戳: {current_time}")
                
        except Exception as e:
            print(f"❌ 更新草稿元信息时出错: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
    
    def update_root_meta_info(self, draft_name, draft_path):
        """更新剪映根索引文件，确保新草稿能被立即扫描到"""
        try:
            import time
            
            root_meta_path = os.path.join(self.draft_folder_path, "root_meta_info.json")
            if not os.path.exists(root_meta_path):
                print(f"⚠️ root_meta_info.json 不存在: {root_meta_path}")
                return
            
            # 读取现有的根元信息
            with open(root_meta_path, 'r', encoding='utf-8') as f:
                root_meta = json.load(f)
            
            # 检查是否已存在此草稿
            existing_draft = None
            for draft in root_meta.get("all_draft_store", []):
                if draft.get("draft_name") == draft_name:
                    existing_draft = draft
                    break
            
            # 读取草稿元信息
            draft_meta_path = os.path.join(draft_path, "draft_meta_info.json")
            if os.path.exists(draft_meta_path):
                with open(draft_meta_path, 'r', encoding='utf-8') as f:
                    draft_meta = json.load(f)
            else:
                print(f"⚠️ 草稿元信息文件不存在: {draft_meta_path}")
                return
            
            # 准备草稿条目信息
            current_time = int(time.time() * 1000000)  # 微秒时间戳
            
            draft_entry = {
                "draft_cloud_last_action_download": True,
                "draft_cloud_purchase_info": "{\n}\n",
                "draft_cloud_template_id": "",
                "draft_cloud_tutorial_info": "{\n}\n", 
                "draft_cloud_videocut_purchase_info": "{\"template_type\":\"\",\"unlock_type\":\"\"}",
                "draft_cover": os.path.join(draft_path, "draft_cover.jpg"),
                "draft_fold_path": draft_path,
                "draft_id": draft_meta.get("draft_id", ""),
                "draft_is_ai_shorts": False,
                "draft_is_invisible": False,
                "draft_json_file": os.path.join(draft_path, "draft_info.json"), 
                "draft_name": draft_name,
                "draft_new_version": "",
                "draft_root_path": self.draft_folder_path,
                "draft_timeline_materials_size": draft_meta.get("draft_timeline_materials_size_", 0),
                "draft_type": "",
                "tm_draft_cloud_completed": "1755277121012",
                "tm_draft_cloud_modified": draft_meta.get("tm_draft_cloud_modified", current_time),
                "tm_draft_create": draft_meta.get("tm_draft_create", current_time),
                "tm_draft_modified": current_time,
                "tm_draft_removed": 0,
                "tm_duration": draft_meta.get("tm_duration", 40000000)
            }
            
            if existing_draft:
                # 更新现有草稿
                existing_draft.update(draft_entry)
                print(f"✅ 更新现有草稿索引: {draft_name}")
            else:
                # 添加新草稿到索引
                if "all_draft_store" not in root_meta:
                    root_meta["all_draft_store"] = []
                root_meta["all_draft_store"].append(draft_entry)
                print(f"✅ 添加新草稿到索引: {draft_name}")
            
            # 写回文件
            with open(root_meta_path, 'w', encoding='utf-8') as f:
                json.dump(root_meta, f, ensure_ascii=False, separators=(',', ':'))
            
            print(f"🎯 剪映根索引已更新，草稿现在应该可以立即被扫描到")
                
        except Exception as e:
            print(f"❌ 更新根索引时出错: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
    
    def fix_existing_draft_placeholders(self, draft_name):
        """修复已存在草稿中的路径占位符问题"""
        try:
            print(f"🔧 修复草稿 '{draft_name}' 中的路径占位符...")
            
            draft_path = os.path.join(self.draft_folder_path, draft_name)
            if not os.path.exists(draft_path):
                print(f"❌ 草稿文件夹不存在: {draft_path}")
                return False
            
            # 检查并修复各种草稿文件
            files_to_fix = [
                "draft_info.json",
                "draft_content.json", 
                "template.tmp",
                "template-2.tmp"
            ]
            
            placeholder = "##_draftpath_placeholder_0E685133-18CE-45ED-8CB8-2904A212EC80_##"
            fixed_files = []
            
            for filename in files_to_fix:
                file_path = os.path.join(draft_path, filename)
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        if placeholder in content:
                            # 替换占位符
                            new_content = content.replace(placeholder, draft_path)
                            
                            # 创建备份
                            backup_path = file_path + ".backup"
                            with open(backup_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                            
                            # 写入修复后的内容
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            
                            fixed_files.append(filename)
                            print(f"  ✅ 已修复: {filename}")
                        else:
                            print(f"  ℹ️ 无需修复: {filename}")
                    except Exception as e:
                        print(f"  ❌ 修复失败: {filename} - {e}")
            
            if fixed_files:
                # 更新元信息时间戳
                self.update_draft_meta_info(draft_path)
                print(f"✅ 成功修复 {len(fixed_files)} 个文件: {', '.join(fixed_files)}")
                print("🎯 现在草稿应该可以正常工作了!")
                return True
            else:
                print("ℹ️ 没有发现需要修复的占位符")
                return True
                
        except Exception as e:
            print(f"❌ 修复草稿时出错: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return False
    
    def fix_audio_track_rendering(self, script, audio_track_name):
        """修复音频轨道渲染配置，确保音频能正常播放"""
        try:
            if audio_track_name not in script.tracks:
                print(f"⚠️ 音频轨道不存在: {audio_track_name}")
                return
            
            track = script.tracks[audio_track_name]
            print(f"🔧 修复音频轨道渲染配置: {audio_track_name}")
            
            # 确保轨道本身的属性正确
            if hasattr(track, 'mute'):
                track.mute = False
            
            # 核心修复：直接操作导出的JSON数据来设置正确的渲染属性
            # 因为render_index等属性是在export_json时动态生成的
            def patch_export_json():
                # 保存原始的export_json方法
                original_export_json = track.export_json
                
                def patched_export_json():
                    json_data = original_export_json()
                    
                    # 计算全局最大render_index
                    max_render_index = 0
                    for other_track in script.tracks.values():
                        if hasattr(other_track, 'render_index'):
                            max_render_index = max(max_render_index, other_track.render_index)
                    
                    # 修复segments中的每个音频段
                    for i, segment_data in enumerate(json_data.get('segments', [])):
                        # 设置唯一的render_index
                        segment_data['render_index'] = max_render_index + i + 1
                        # 设置正确的track_render_index
                        segment_data['track_render_index'] = i
                        # 确保音频段可见
                        segment_data['visible'] = True
                        # 确保音量不为0
                        if segment_data.get('volume', 0) <= 0:
                            segment_data['volume'] = 1.0
                        # 确保音频增强关闭
                        segment_data['intensifies_audio'] = False
                        
                        print(f"  ✅ 修复音频段 {i+1}: render_index={segment_data['render_index']}, "
                              f"track_render_index={segment_data['track_render_index']}, "
                              f"volume={segment_data['volume']}")
                    
                    # 确保音频轨道的flag设置正确
                    json_data['flag'] = 0
                    json_data['attribute'] = 0
                    json_data['is_default_name'] = True
                    
                    return json_data
                
                # 临时替换export_json方法
                track.export_json = patched_export_json
                return original_export_json
            
            # 应用补丁
            original_method = patch_export_json()
            
            # 存储原始方法的引用，以便后续恢复（如果需要）
            track._original_export_json = original_method
            
            print(f"✅ 音频轨道渲染配置修复完成: {audio_track_name}")
            
        except Exception as e:
            print(f"❌ 修复音频轨道渲染配置时出错: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
    
    def save_script_file(self, script, draft_name):
        """保存ScriptFile到正确的文件位置"""
        print(f"    🔧 [DEBUG] save_script_file开始执行...")
        draft_path = os.path.join(self.draft_folder_path, draft_name)
        print(f"           草稿路径: {draft_path}")
        
        # 检查应该保存到哪个文件
        draft_content_path = os.path.join(draft_path, "draft_content.json")
        draft_info_path = os.path.join(draft_path, "draft_info.json")
        
        print(f"    🔧 [DEBUG] 检查文件存在性:")
        print(f"           draft_content.json: {os.path.exists(draft_content_path)}")
        print(f"           draft_info.json: {os.path.exists(draft_info_path)}")
        
        # 在保存前替换所有路径占位符
        self.replace_path_placeholders_in_script(script, draft_path)
        
        # 更新草稿元信息文件的时间戳
        self.update_draft_meta_info(draft_path)
        
        # 更新剪映根索引文件，确保新草稿能被扫描到
        self.update_root_meta_info(draft_name, draft_path)
        
        # 修复所有音频轨道渲染配置（包括背景音乐轨道）
        print(f"    🔧 [DEBUG] 在保存前修复所有音频轨道渲染配置...")
        audio_track_count = 0
        for track_name, track in script.tracks.items():
            if hasattr(track, 'track_type') and track.track_type.name == 'audio':
                print(f"    🔧 [DEBUG] 发现音频轨道: {track_name}")
                self.fix_audio_track_rendering(script, track_name)
                audio_track_count += 1
        print(f"    ✅ 已修复 {audio_track_count} 个音频轨道的渲染配置")
        
        # 关键修复：强制使用draft_info.json格式，解决JianYing自动删除草稿的问题
        print(f"    🔧 [DEBUG] 强制使用draft_info.json格式以兼容JianYing...")
        
        # 如果存在draft_content.json，将其重命名为draft_info.json
        if os.path.exists(draft_content_path) and not os.path.exists(draft_info_path):
            print(f"    🔧 [DEBUG] 将draft_content.json重命名为draft_info.json...")
            os.rename(draft_content_path, draft_info_path)
        
        # 始终保存到draft_info.json
        script.save_path = draft_info_path
        print(f"           设置save_path: {script.save_path}")
        script.save()
        print(f"    🔧 [DEBUG] script.save()调用完成")
        print(f"    💾 保存到 draft_info.json (强制兼容格式)")
        
        # 生成封面图（如果启用）
        if self.enable_cover_image:
            self.generate_cover_image(script, draft_path, draft_name)
    
    def generate_cover_image(self, script, draft_path, draft_name):
        """根据选择的样式生成草稿封面图"""
        try:
            print(f"    🖼️ 开始生成封面图...")
            print(f"    🎨 使用样式: {self.cover_image_style}")
            print(f"    🔧 [DEBUG] save_script_file调用完成，基于替换的视频片段，获取最后一帧来做为封面图")
            
            # 生成封面图文件路径
            cover_image_path = os.path.join(draft_path, "draft_cover.jpg")
            
            # 根据样式选择生成方法
            success = False
            if self.cover_image_style == "timeline_last_frame":
                success = self.generate_jianying_compatible_cover(draft_name, draft_path, cover_image_path, script)
            elif self.cover_image_style == "video_last_frame":
                success = self.generate_video_last_frame_cover(script, cover_image_path)
            elif self.cover_image_style == "ultrathink":
                success = self.generate_ultrathink_style_cover(draft_name, cover_image_path, script)
            else:
                print(f"    ❌ 未知的封面图样式: {self.cover_image_style}")
                return False
            
            # 如果成功生成封面图，尝试应用到剪映草稿系统
            if success:
                self.apply_cover_to_draft(draft_name, draft_path, cover_image_path)
            
            return success
                
        except Exception as e:
            print(f"    ❌ 生成封面图时出错: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return False
    
    def generate_timeline_last_frame_cover(self, draft_name, cover_image_path, script):
        """生成基于草稿时间线最后一帧的封面图"""
        try:
            # 获取草稿时间线信息
            timeline_info = self.get_draft_timeline_info(draft_name)
            
            if not timeline_info:
                print(f"    ⚠️ 无法获取时间线信息，回退到视频文件最后一帧")
                return self.generate_video_last_frame_cover(script, cover_image_path)
            
            video_file_path = timeline_info['video_file_path']
            extract_time = timeline_info['video_time_seconds']
            print(f"    📹 使用视频文件: {os.path.basename(video_file_path)}")
            print(f"    🎯 将截取草稿最后时刻 ({timeline_info['draft_duration_seconds']:.2f}s) 对应的视频时间: {extract_time:.2f}s")
            
            if self.extract_frame_at_time_with_imageio(video_file_path, cover_image_path, extract_time):
                print(f"    ✅ 封面图生成成功: draft_cover.jpg")
                return True
            else:
                print(f"    ❌ 封面图生成失败")
                return False
                
        except Exception as e:
            print(f"    ❌ 生成时间线封面图失败: {e}")
            return False
    
    def generate_video_last_frame_cover(self, script, cover_image_path):
        """生成基于视频文件最后一帧的封面图"""
        try:
            video_file_path = self.find_video_file_in_script(script)
            if not video_file_path:
                print(f"    ⚠️ 草稿中未找到视频文件，无法生成封面图")
                return False
            
            print(f"    📹 使用视频文件: {os.path.basename(video_file_path)}")
            print(f"    🎯 将截取视频文件的最后一帧")
            
            if self.extract_frame_at_time_with_imageio(video_file_path, cover_image_path, None):
                print(f"    ✅ 封面图生成成功: draft_cover.jpg")
                return True
            else:
                print(f"    ❌ 封面图生成失败")
                return False
                
        except Exception as e:
            print(f"    ❌ 生成视频封面图失败: {e}")
            return False
    
    def generate_ultrathink_style_cover(self, draft_name, cover_image_path, script):
        """生成剪映ultrathink样式兼容的封面图"""
        try:
            print(f"    🎨 使用剪映样式兼容模式")
            
            # 首先尝试时间线方式
            timeline_info = self.get_draft_timeline_info(draft_name)
            
            if timeline_info:
                video_file_path = timeline_info['video_file_path']
                extract_time = timeline_info['video_time_seconds']
                print(f"    📹 使用视频文件: {os.path.basename(video_file_path)}")
                print(f"    🎯 剪映样式：截取草稿最后时刻 ({timeline_info['draft_duration_seconds']:.2f}s) 对应的视频时间: {extract_time:.2f}s")
                
                if self.extract_frame_at_time_with_imageio(video_file_path, cover_image_path, extract_time):
                    print(f"    ✅ 剪映样式封面图生成成功: draft_cover.jpg")
                    print(f"    💡 提示: 如需完整的剪映ultrathink样式效果，建议在剪映中重新生成封面")
                    return True
            
            # 回退到视频最后一帧
            print(f"    ⚠️ 回退到视频文件最后一帧方式")
            return self.generate_video_last_frame_cover(script, cover_image_path)
                
        except Exception as e:
            print(f"    ❌ 生成剪映样式封面图失败: {e}")
            return False
    
    def generate_jianying_compatible_cover(self, draft_name, draft_path, cover_image_path, script):
        """生成剪映兼容的多轨道合成封面图"""
        try:
            print(f"    🎨 剪映兼容模式：分析草稿结构生成合成封面图")
            
            # 1. 分析草稿轨道结构
            draft_analysis = self.analyze_draft_composition(draft_name)
            if not draft_analysis:
                print(f"    ⚠️ 无法分析草稿结构，回退到时间线方式")
                return self.generate_timeline_last_frame_cover(draft_name, cover_image_path, script)
            
            # 2. 生成基础视频帧
            base_frame_success = False
            if draft_analysis.get('video_segments'):
                base_frame_success = self.generate_base_video_frame(draft_analysis, cover_image_path)
            
            if not base_frame_success:
                print(f"    ⚠️ 无法生成基础视频帧，回退到简单方式")
                return self.generate_timeline_last_frame_cover(draft_name, cover_image_path, script)
            
            # 3. 尝试合成其他轨道效果（贴纸、文本等）
            if draft_analysis.get('has_stickers') or draft_analysis.get('has_texts'):
                self.composite_additional_layers(draft_analysis, cover_image_path)
            
            print(f"    ✅ 剪映兼容封面图生成成功: draft_cover.jpg")
            return True
            
        except Exception as e:
            print(f"    ❌ 剪映兼容封面图生成失败: {e}")
            # 回退到简单的时间线方式
            return self.generate_timeline_last_frame_cover(draft_name, cover_image_path, script)
    
    def analyze_draft_composition(self, draft_name):
        """分析草稿的合成结构"""
        try:
            # 读取草稿文件 - 支持绝对路径
            if os.path.isabs(draft_name):
                # 如果draft_name是绝对路径，直接使用
                draft_info_path = os.path.join(draft_name, "draft_info.json")
            else:
                # 否则使用相对路径
                draft_info_path = os.path.join(self.draft_folder_path, draft_name, "draft_info.json")
            
            if not os.path.exists(draft_info_path):
                # 尝试其他可能的路径
                alt_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/三字阳章老师/draft_info.json"
                if os.path.exists(alt_path):
                    draft_info_path = alt_path
                    print(f"    📁 使用剪映草稿路径: {draft_info_path}")
                else:
                    return None
            
            with open(draft_info_path, 'r', encoding='utf-8') as f:
                draft_data = json.load(f)
            
            analysis = {
                'draft_duration': draft_data.get('duration', 40000000),
                'canvas_config': draft_data.get('canvas_config', {}),
                'video_segments': [],
                'text_segments': [],
                'sticker_segments': [],
                'has_stickers': False,
                'has_texts': False,
                'has_effects': False
            }
            
            # 分析轨道
            tracks = draft_data.get('tracks', [])
            for track in tracks:
                track_type = track.get('type', '')
                segments = track.get('segments', [])
                
                for segment in segments:
                    target_timerange = segment.get('target_timerange', {})
                    segment_start = target_timerange.get('start', 0)
                    segment_duration = target_timerange.get('duration', 0)
                    segment_end = segment_start + segment_duration
                    
                    # 检查片段是否可见且有效（不限制于最后时刻）
                    # 对于封面生成，我们需要考虑所有活跃的轨道内容
                    if segment_duration > 0 and segment.get('visible', True):  # 有持续时间且可见
                        if track_type == 'video':
                            analysis['video_segments'].append({
                                'segment': segment,
                                'material_id': segment.get('material_id'),
                                'track_info': track,
                                'start_time': segment_start,
                                'end_time': segment_end
                            })
                        elif track_type == 'text':
                            analysis['text_segments'].append({
                                'segment': segment,
                                'start_time': segment_start,
                                'end_time': segment_end
                            })
                            analysis['has_texts'] = True
                        elif track_type == 'sticker':
                            analysis['sticker_segments'].append({
                                'segment': segment,
                                'start_time': segment_start,
                                'end_time': segment_end
                            })
                            analysis['has_stickers'] = True
            
            print(f"    📊 草稿分析结果:")
            print(f"       视频片段: {len(analysis['video_segments'])}个")
            print(f"       文本片段: {len(analysis['text_segments'])}个")
            print(f"       贴纸片段: {len(analysis['sticker_segments'])}个")
            
            return analysis
            
        except Exception as e:
            print(f"    ❌ 分析草稿结构失败: {e}")
            return None
    
    def generate_base_video_frame(self, draft_analysis, cover_image_path):
        """生成基础视频帧"""
        try:
            video_segments = draft_analysis.get('video_segments', [])
            if not video_segments:
                return False
            
            # 查找在草稿结束时刻活跃的视频片段
            draft_duration = draft_analysis['draft_duration']
            main_segment = None
            
            # 优先选择在草稿最后时刻仍然活跃的片段
            for segment_info in video_segments:
                if segment_info['end_time'] >= draft_duration * 0.9:  # 90%之后仍活跃
                    main_segment = segment_info
                    break
            
            # 如果没有找到，使用最后结束的片段
            if not main_segment:
                main_segment = max(video_segments, key=lambda x: x['end_time'])
            
            segment_data = main_segment['segment']
            print(f"    🎬 选择视频片段: ID={segment_data.get('id', 'unknown')[:8]}... 结束时间={main_segment['end_time']/1000000:.1f}s")
            
            # 查找对应的视频文件
            video_file_path = None
            if hasattr(self, 'last_replaced_videos') and self.last_replaced_videos:
                video_file_path = self.last_replaced_videos[0]
            
            if not video_file_path or not os.path.exists(video_file_path):
                print(f"    ❌ 未找到视频文件")
                return False
            
            # 计算在草稿最后时刻，该视频片段对应的原视频时间点
            draft_duration = draft_analysis['draft_duration']
            target_timerange = segment_data.get('target_timerange', {})
            source_timerange = segment_data.get('source_timerange', {})
            
            target_start = target_timerange.get('start', 0)
            target_duration = target_timerange.get('duration', 0)
            source_start = source_timerange.get('start', 0)
            source_duration = source_timerange.get('duration', 0)
            
            if target_duration > 0 and source_duration > 0:
                # 计算草稿结束时刻在该片段中的进度
                time_in_segment = draft_duration - target_start
                progress_ratio = min(time_in_segment / target_duration, 1.0)
                
                # 计算对应的原视频时间点
                video_time_seconds = (source_start + source_duration * progress_ratio) / 1000000.0
            else:
                # 回退到简单的结束时间
                video_time_seconds = (draft_duration - 100000) / 1000000.0  # 稍微提前0.1秒
            
            print(f"    📹 使用视频文件: {os.path.basename(video_file_path)}")
            print(f"    🎯 提取时间点: {video_time_seconds:.2f}s")
            
            # 提取帧
            success = self.extract_frame_at_time_with_imageio(video_file_path, cover_image_path, video_time_seconds)
            if success:
                print(f"    ✅ 基础视频帧生成成功")
            
            return success
            
        except Exception as e:
            print(f"    ❌ 生成基础视频帧失败: {e}")
            return False
    
    def composite_additional_layers(self, draft_analysis, cover_image_path):
        """合成额外的图层（贴纸、文本等）"""
        try:
            # 为了实现真正的ultrathink多轨道合成，这里提供更详细的分析
            draft_duration = draft_analysis['draft_duration']
            
            print(f"    🎨 分析多轨道合成结构 (ultrathink模式)")
            
            # 分析在草稿结束时刻活跃的元素
            active_at_end = []
            
            # 检查视频轨道
            for video_seg in draft_analysis.get('video_segments', []):
                if video_seg['end_time'] >= draft_duration * 0.9:
                    clip_info = video_seg['segment'].get('clip', {})
                    scale = clip_info.get('scale', {'x': 1.0, 'y': 1.0})
                    transform = clip_info.get('transform', {'x': 0.0, 'y': 0.0})
                    alpha = clip_info.get('alpha', 1.0)
                    
                    active_at_end.append({
                        'type': 'video',
                        'id': video_seg['segment'].get('id', 'unknown')[:8],
                        'scale': f"{scale['x']:.2f}x",
                        'position': f"({transform['x']:.2f}, {transform['y']:.2f})",
                        'alpha': f"{alpha:.2f}"
                    })
            
            # 检查文本轨道
            for text_seg in draft_analysis.get('text_segments', []):
                if text_seg['end_time'] >= draft_duration * 0.9:
                    clip_info = text_seg['segment'].get('clip', {})
                    scale = clip_info.get('scale', {'x': 1.0, 'y': 1.0})
                    transform = clip_info.get('transform', {'x': 0.0, 'y': 0.0})
                    
                    active_at_end.append({
                        'type': 'text',
                        'id': text_seg['segment'].get('id', 'unknown')[:8],
                        'scale': f"{scale['x']:.2f}x",
                        'position': f"({transform['x']:.2f}, {transform['y']:.2f})"
                    })
            
            # 检查贴纸轨道
            for sticker_seg in draft_analysis.get('sticker_segments', []):
                if sticker_seg['end_time'] >= draft_duration * 0.9:
                    clip_info = sticker_seg['segment'].get('clip', {})
                    scale = clip_info.get('scale', {'x': 1.0, 'y': 1.0})
                    transform = clip_info.get('transform', {'x': 0.0, 'y': 0.0})
                    
                    active_at_end.append({
                        'type': 'sticker',
                        'id': sticker_seg['segment'].get('id', 'unknown')[:8],
                        'scale': f"{scale['x']:.2f}x",
                        'position': f"({transform['x']:.2f}, {transform['y']:.2f})"
                    })
            
            # 输出合成信息
            print(f"    📊 草稿结束时活跃元素: {len(active_at_end)}个")
            for element in active_at_end:
                print(f"       {element['type'].upper()}: {element['id']}... 缩放={element['scale']} 位置={element['position']}")
            
            # 由于完整的合成需要复杂的渲染引擎，目前建议用户在剪映中手动完善
            if len(active_at_end) > 1:
                print(f"    🌟 检测到多轨道叠加效果 - 建议在剪映中调整ultrathink风格")
            
            if draft_analysis.get('has_stickers'):
                print(f"    🎭 检测到贴纸图层")
            
            if draft_analysis.get('has_texts'):
                print(f"    📝 检测到文本图层")
            
            # 保存合成信息用于调试
            composition_info = {
                'active_elements': active_at_end,
                'draft_duration_seconds': draft_duration / 1000000.0,
                'total_video_segments': len(draft_analysis.get('video_segments', [])),
                'total_text_segments': len(draft_analysis.get('text_segments', [])),
                'total_sticker_segments': len(draft_analysis.get('sticker_segments', []))
            }
            
            import json
            info_path = cover_image_path.replace('.jpg', '_composition_info.json')
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(composition_info, f, indent=2, ensure_ascii=False)
            print(f"    📄 合成信息已保存: {os.path.basename(info_path)}")
            
        except Exception as e:
            print(f"    ⚠️ 合成额外图层时出错: {e}")
    
    def apply_cover_to_draft(self, draft_name, draft_path, cover_image_path):
        """将生成的封面图应用到剪映草稿系统"""
        try:
            print(f"    🔧 应用封面图到剪映草稿系统...")
            
            # 1. 确保cover图片存在
            if not os.path.exists(cover_image_path):
                print(f"    ❌ 封面图文件不存在: {cover_image_path}")
                return False
            
            # 2. 创建Resources/cover目录（如果不存在）
            resources_cover_dir = os.path.join(draft_path, "Resources", "cover")
            if not os.path.exists(resources_cover_dir):
                os.makedirs(resources_cover_dir, exist_ok=True)
                print(f"    📁 创建封面资源目录: {resources_cover_dir}")
            
            # 3. 生成新的封面图ID和文件名
            import uuid
            cover_id = str(uuid.uuid4()).upper()
            cover_filename = f"{cover_id}.jpg"
            cover_resource_path = os.path.join(resources_cover_dir, cover_filename)
            
            # 4. 复制封面图到资源目录
            shutil.copy2(cover_image_path, cover_resource_path)
            print(f"    📋 复制封面图到资源目录: {cover_filename}")
            
            # 5. 更新draft_info.json中的封面配置
            self.update_draft_cover_config(draft_name, draft_path, cover_id, cover_filename)
            
            print(f"    ✅ 封面图已成功应用到剪映草稿系统")
            return True
            
        except Exception as e:
            print(f"    ❌ 应用封面图到草稿系统失败: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return False
    
    def update_draft_cover_config(self, draft_name, draft_path, cover_id, cover_filename):
        """更新草稿的封面配置"""
        try:
            draft_info_path = os.path.join(draft_path, "draft_info.json")
            
            if not os.path.exists(draft_info_path):
                print(f"    ❌ 草稿配置文件不存在")
                return False
            
            # 读取草稿配置
            with open(draft_info_path, 'r', encoding='utf-8') as f:
                draft_data = json.load(f)
            
            # 备份原始文件
            backup_path = draft_info_path + ".cover_backup"
            shutil.copy2(draft_info_path, backup_path)
            
            # 更新封面配置
            if 'cover' not in draft_data:
                draft_data['cover'] = {}
            
            # 简化的封面配置更新
            draft_data['cover'].update({
                'sub_type': 'frame',
                'type': 'image'
            })
            
            # 保存更新后的配置
            with open(draft_info_path, 'w', encoding='utf-8') as f:
                json.dump(draft_data, f, ensure_ascii=False, separators=(',', ':'))
            
            print(f"    🔧 草稿封面配置已更新")
            return True
            
        except Exception as e:
            print(f"    ❌ 更新草稿封面配置失败: {e}")
            return False
    
    def test_jianying_cover_generation(self):
        """测试剪映封面图生成功能"""
        try:
            print(f"\n🧪 测试剪映封面图生成功能")
            
            # 测试路径
            test_draft_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/三字阳章老师"
            test_cover_path = "/Users/dada/Desktop/test_cover.jpg"
            
            if not os.path.exists(test_draft_path):
                print(f"❌ 测试草稿路径不存在: {test_draft_path}")
                return False
            
            # 设置测试参数
            self.enable_cover_image = True
            self.cover_image_style = "timeline_last_frame"
            self.last_replaced_videos = ["/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/examples/materials/part1/E狂.mp4"]
            
            # 生成封面图
            success = self.generate_jianying_compatible_cover("三字阳章老师", test_draft_path, test_cover_path, None)
            
            if success and os.path.exists(test_cover_path):
                print(f"✅ 测试成功！封面图已生成: {test_cover_path}")
                return True
            else:
                print(f"❌ 测试失败")
                return False
                
        except Exception as e:
            print(f"❌ 测试过程中出错: {e}")
            return False
    
    def find_video_file_in_script(self, script):
        """从ScriptFile中找到第一个视频文件路径"""
        try:
            # 方法1: 从script.materials.videos中查找
            if hasattr(script, 'materials') and hasattr(script.materials, 'videos'):
                for video_material in script.materials.videos:
                    if hasattr(video_material, 'path') and video_material.path:
                        video_path = video_material.path
                        # 如果是相对路径，需要转换为绝对路径
                        if not os.path.isabs(video_path):
                            video_path = os.path.abspath(video_path)
                        
                        if os.path.exists(video_path):
                            print(f"    🔧 [DEBUG] 从script.materials.videos找到视频: {video_path}")
                            return video_path
            
            print(f"    🔧 [DEBUG] script.materials.videos 中未找到有效视频文件")
            
            # 方法2: 从最近替换的视频文件中查找
            if hasattr(self, 'last_replaced_videos') and self.last_replaced_videos:
                for video_file in self.last_replaced_videos:
                    if os.path.exists(video_file):
                        print(f"    🔧 [DEBUG] 从最近替换的视频中找到: {video_file}")
                        return video_file
            
            # 方法3: 从素材文件夹中查找第一个视频文件
            if hasattr(self, 'materials_folder_path') and self.materials_folder_path:
                video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
                for root, dirs, files in os.walk(self.materials_folder_path):
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in video_extensions):
                            video_path = os.path.join(root, file)
                            print(f"    🔧 [DEBUG] 从素材文件夹找到视频: {video_path}")
                            return video_path
            
            print(f"    🔧 [DEBUG] 所有方法都未找到有效视频文件")
            return None
            
        except Exception as e:
            print(f"    🔧 [DEBUG] 查找视频文件时出错: {e}")
            return None
    
    def extract_frame_at_time_with_imageio(self, video_path, output_path, time_seconds=None):
        """使用imageio提取视频指定时间的帧，如果time_seconds为None则提取最后一帧"""
        try:
            import imageio
            
            # 读取视频
            reader = imageio.get_reader(video_path)
            
            # 获取视频帧数和帧率
            frame_count = reader.count_frames()
            if frame_count == 0:
                print(f"    ❌ 视频文件无有效帧")
                return False
            
            # 获取视频元数据
            meta = reader.get_meta_data()
            fps = meta.get('fps', 25)  # 默认25fps
            
            if time_seconds is None:
                # 如果没有指定时间，提取最后一帧
                frame_index = frame_count - 1
                print(f"    🎯 提取最后一帧 (帧索引: {frame_index})")
            else:
                # 根据时间计算帧索引
                frame_index = int(time_seconds * fps)
                frame_index = min(frame_index, frame_count - 1)  # 确保不超出范围
                frame_index = max(frame_index, 0)  # 确保不小于0
                print(f"    🎯 提取时间点 {time_seconds:.2f}s 的帧 (帧索引: {frame_index}, fps: {fps})")
            
            # 读取指定帧
            frame = reader.get_data(frame_index)
            
            # 保存为JPEG
            imageio.imwrite(output_path, frame, format='JPEG', quality=95)
            
            reader.close()
            return True
            
        except ImportError:
            print(f"    ⚠️ imageio库未安装，尝试使用ffmpeg...")
            return self.extract_frame_at_time_with_ffmpeg(video_path, output_path, time_seconds)
        except Exception as e:
            print(f"    ❌ imageio提取失败: {e}")
            print(f"    ⚠️ 尝试使用ffmpeg...")
            return self.extract_frame_at_time_with_ffmpeg(video_path, output_path, time_seconds)
    
    def extract_last_frame_with_imageio(self, video_path, output_path):
        """使用imageio提取视频最后一帧（向后兼容）"""
        return self.extract_frame_at_time_with_imageio(video_path, output_path, None)
    
    def extract_frame_at_time_with_ffmpeg(self, video_path, output_path, time_seconds=None):
        """使用ffmpeg提取视频指定时间的帧（fallback方案）"""
        try:
            import subprocess
            
            if time_seconds is None:
                # 如果没有指定时间，提取最后一帧
                cmd = [
                    'ffmpeg', '-sseof', '-1', '-i', video_path,
                    '-frames:v', '1', '-q:v', '2', '-y', output_path
                ]
                print(f"    🎯 使用ffmpeg提取最后一帧")
            else:
                # 提取指定时间的帧
                cmd = [
                    'ffmpeg', '-ss', str(time_seconds), '-i', video_path,
                    '-frames:v', '1', '-q:v', '2', '-y', output_path
                ]
                print(f"    🎯 使用ffmpeg提取时间点 {time_seconds:.2f}s 的帧")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(output_path):
                return True
            else:
                print(f"    ❌ ffmpeg执行失败: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print(f"    ❌ ffmpeg未安装，无法生成封面图")
            return False
        except Exception as e:
            print(f"    ❌ ffmpeg提取失败: {e}")
            return False
    
    def extract_last_frame_with_ffmpeg(self, video_path, output_path):
        """使用ffmpeg提取视频最后一帧（向后兼容）"""
        return self.extract_frame_at_time_with_ffmpeg(video_path, output_path, None)
    
    def add_audio_and_subtitle_with_api(self, draft_name, combination):
        """使用pyJianYingDraft库API添加音频和字幕"""
        try:
            print(f"    🎵 使用库API添加音频和字幕...")
            
            # 加载草稿为ScriptFile对象
            try:
                script = self.load_draft_as_script_file(draft_name)
                print(f"    ✅ 成功加载草稿为ScriptFile对象")
            except Exception as e:
                print(f"    ❌ 无法加载草稿为ScriptFile对象: {e}")
                print(f"    💡 这可能是因为草稿已加密（剪映6.0+版本）或文件结构不兼容")
                return False
            
            # 获取音频文件路径
            audio_file = combination['audios']
            audio_path = os.path.join(self.audios_folder_path, audio_file)
            
            if not os.path.exists(audio_path):
                print(f"    ❌ 音频文件不存在: {audio_path}")
                return False
            
            # 创建AudioMaterial对象
            try:
                print(f"    🔧 [DEBUG] 开始创建AudioMaterial，路径: {audio_path}")
                audio_material = draft.AudioMaterial(audio_path)
                print(f"    🔧 [DEBUG] AudioMaterial创建完成:")
                print(f"           material_id: {audio_material.material_id}")
                print(f"           duration: {audio_material.duration}微秒 ({audio_material.duration/1000000:.2f}秒)")
                print(f"           文件名: {audio_file}")
                
                print(f"    ✅ 创建AudioMaterial成功: {audio_file}")
            except Exception as e:
                print(f"    ❌ [DEBUG] 创建AudioMaterial失败: {e}")
                import traceback
                print(f"    🔧 [DEBUG] 异常详情: {traceback.format_exc()}")
                return False
            
            # 添加音频轨道（如果不存在）
            audio_track_name = "audio_track"
            try:
                print(f"    🔧 [DEBUG] 检查音频轨道: {audio_track_name}")
                print(f"    🔧 [DEBUG] 当前所有轨道: {list(script.tracks.keys())}")
                
                # 检查是否已有指定名称的音频轨道
                if audio_track_name not in script.tracks:
                    print(f"    🔧 [DEBUG] 音频轨道不存在，开始创建...")
                    script.add_track(draft.TrackType.audio, audio_track_name)
                    print(f"    🔧 [DEBUG] 音频轨道创建完成")
                    print(f"    ✅ 添加音频轨道: {audio_track_name}")
                else:
                    print(f"    🔧 [DEBUG] 音频轨道已存在")
                    print(f"    ✅ 使用现有音频轨道: {audio_track_name}")
                
                # 验证轨道创建结果
                if audio_track_name in script.tracks:
                    track = script.tracks[audio_track_name]
                    print(f"    🔧 [DEBUG] 轨道验证成功:")
                    print(f"           轨道类型: {track.track_type}")
                    print(f"           轨道名称: {track.name}")
                    print(f"           轨道ID: {track.track_id}")
                    print(f"           静音状态: {track.mute}")
                else:
                    print(f"    ❌ [DEBUG] 轨道验证失败: 轨道未在tracks中找到")
                    
            except Exception as e:
                print(f"    ❌ [DEBUG] 添加音频轨道失败: {e}")
                import traceback
                print(f"    🔧 [DEBUG] 异常详情: {traceback.format_exc()}")
                return False
            
            # 创建音频片段
            try:
                # 计算目标时长和源时长
                video_duration = script.duration
                audio_duration = audio_material.duration
                
                print(f"    📊 视频时长: {video_duration/1000000:.2f}s, 音频时长: {audio_duration/1000000:.2f}s")
                
                # 根据配置调整音频
                target_duration, speed_ratio = self.calculate_audio_adjustments(video_duration, audio_duration)
                
                # 创建音频片段
                print(f"    🔧 [DEBUG] 开始创建AudioSegment...")
                print(f"           目标时长: {target_duration}微秒 ({target_duration/1000000:.2f}秒)")
                print(f"           速度比例: {speed_ratio:.2f}")
                
                # 将微秒转换为秒
                target_duration_sec = target_duration / 1000000
                
                # 正确计算source_timerange：从音频文件中截取的部分
                if self.audio_longer_handling == "trim" and audio_duration > video_duration:
                    # 裁剪模式：从音频开头截取video_duration长度
                    source_duration_us = video_duration
                else:
                    # 其他模式：使用计算得到的target_duration
                    source_duration_us = min(audio_duration, target_duration)
                
                source_duration_sec = source_duration_us / 1000000
                
                print(f"    🔧 [DEBUG] AudioSegment参数:")
                print(f"           material: AudioMaterial对象 (id: {audio_material.material_id})")
                print(f"           target_timerange: 0s ~ {target_duration_sec}s")
                print(f"           source_timerange: 0s ~ {source_duration_sec}s")
                
                # 使用传统构造方式：先创建素材实例，再传入片段构造函数
                audio_segment = draft.AudioSegment(
                    audio_material,  # 直接传入material对象作为第一个参数
                    draft.trange("0s", f"{target_duration_sec}s"),  # target_timerange作为第二个参数
                    source_timerange=draft.trange("0s", f"{source_duration_sec}s") , # source_timerange作为关键字参数
                    volume=self.audio_volume / 100.0,  # 音量0-1
                )
                
                print(f"    🔧 [DEBUG] AudioSegment创建完成:")
                print(f"           segment_id: {audio_segment.segment_id}")
                print(f"           material_id: {audio_segment.material_id}")
                print(f"           target_timerange: {audio_segment.target_timerange.start}~{audio_segment.target_timerange.end}")
                print(f"           source_timerange: {audio_segment.source_timerange.start}~{audio_segment.source_timerange.end}")
                print(f"           volume: {audio_segment.volume}")
                print(f"           speed: {audio_segment.speed}")
                
                # 重要：使用add_material方法将AudioMaterial添加到script中
                script.add_material(audio_segment.material_instance)
                print(f"    🔧 [DEBUG] 使用add_material方法添加AudioMaterial到script中")
                
                # 应用音量设置
                print(f"    🔧 [DEBUG] 应用音频设置...")
                original_volume = audio_segment.volume
                if hasattr(self, 'audio_volume') and self.audio_volume != 100:
                    audio_segment.volume = self.audio_volume / 100.0
                    db_value = 20 * (self.audio_volume / 100 - 1) if self.audio_volume != 100 else 0
                    print(f"    🔧 [DEBUG] 音量调整: {original_volume} -> {audio_segment.volume} ({self.audio_volume}%)")
                    print(f"    🔊 设置音量: {self.audio_volume}% (≈{db_value:.1f}dB)")
                else:
                    print(f"    🔧 [DEBUG] 保持默认音量: {audio_segment.volume} (0dB)")
                
                # 应用淡入淡出效果
                fade_applied = False
                if hasattr(self, 'audio_fade_in') and hasattr(self, 'audio_fade_out'):
                    if self.audio_fade_in > 0 or self.audio_fade_out > 0:
                        print(f"    🔧 [DEBUG] 应用淡入淡出: 淡入{self.audio_fade_in}s, 淡出{self.audio_fade_out}s")
                        audio_segment.add_fade(f"{self.audio_fade_in}s", f"{self.audio_fade_out}s")
                        fade_applied = True
                        print(f"    🔧 [DEBUG] 淡入淡出效果已添加到audio_segment")
                        print(f"    🎚️ 设置淡入淡出: 淡入{self.audio_fade_in}s, 淡出{self.audio_fade_out}s")
                    else:
                        print(f"    🔧 [DEBUG] 无淡入淡出设置")
                else:
                    print(f"    🔧 [DEBUG] 淡入淡出属性不存在")
                
                # 检查fade对象
                if fade_applied:
                    if hasattr(audio_segment, 'fade') and audio_segment.fade:
                        print(f"    🔧 [DEBUG] fade对象存在:")
                        print(f"           fade_id: {audio_segment.fade.fade_id}")
                        print(f"           in_duration: {audio_segment.fade.in_duration}")
                        print(f"           out_duration: {audio_segment.fade.out_duration}")
                    else:
                        print(f"    ❌ [DEBUG] fade对象不存在或为None")
                
                # 应用速度调整
                if speed_ratio != 1.0:
                    print(f"    🔧 [DEBUG] 需要速度调整: {speed_ratio:.2f}x")
                    print(f"    ⚡ 需要速度调整: {speed_ratio:.2f}x")
                else:
                    print(f"    🔧 [DEBUG] 无需速度调整")
                
                # 添加片段到指定音频轨道
                print(f"    🔧 [DEBUG] 开始添加音频片段到轨道...")
                print(f"           轨道名称: {audio_track_name}")
                print(f"           片段ID: {audio_segment.segment_id}")
                
                script.add_segment(audio_segment, audio_track_name)
                print(f"    🔧 [DEBUG] add_segment调用完成")
                
                # 验证片段是否成功添加
                if audio_track_name in script.tracks:
                    track = script.tracks[audio_track_name]
                    segment_count = len(track.segments)
                    print(f"    🔧 [DEBUG] 轨道验证:")
                    print(f"           轨道存在: True")
                    print(f"           片段数量: {segment_count}")
                    if segment_count > 0:
                        last_segment = track.segments[-1]
                        print(f"           最后片段ID: {last_segment.segment_id}")
                        print(f"           最后片段volume: {last_segment.volume}")
                        print(f"           最后片段有fade: {hasattr(last_segment, 'fade') and last_segment.fade is not None}")
                else:
                    print(f"    ❌ [DEBUG] 轨道验证失败: 轨道不存在")
                
                print(f"    ✅ 添加音频片段到轨道: {audio_track_name}")
                
                # 修复音频轨道渲染配置，确保音频能正常播放
                self.fix_audio_track_rendering(script, audio_track_name)
                
                # 检查是否需要根据音频设置裁剪视频
                if self.audio_shorter_handling == "trim_video" and audio_duration < video_duration:
                    print(f"    🔧 [DEBUG] 音频比视频短，需要裁剪视频...")
                    original_duration = script.duration
                    script.duration = target_duration
                    print(f"    ✂️ 根据音频长度裁剪视频: {original_duration/1000000:.2f}s -> {script.duration/1000000:.2f}s")
                    
                    # 裁剪所有视频轨道的片段
                    for track_name, track in script.tracks.items():
                        if hasattr(track, 'track_type') and track.track_type.name == 'video':
                            for segment in track.segments:
                                if segment.end > script.duration:
                                    if segment.start < script.duration:
                                        # 部分重叠，裁剪片段
                                        segment.duration = script.duration - segment.start
                                        print(f"    🔧 [DEBUG] 裁剪视频片段 {segment.segment_id} 到 {segment.duration/1000000:.2f}s")
                                    else:
                                        # 完全超出，移除片段
                                        print(f"    🔧 [DEBUG] 移除超出时长的视频片段 {segment.segment_id}")
                                        track.segments.remove(segment)
                
            except Exception as e:
                print(f"    ❌ 创建音频片段失败: {e}")
                return False
            
            # 处理背景音乐
            if self.enable_background_music and 'bg_musics' in combination:
                bg_music_success = self.add_background_music_with_api(script, combination)
                if not bg_music_success:
                    print(f"    ⚠️ 背景音乐添加失败，但音频添加成功")
            
            # 处理字幕
            if self.enable_subtitles:
                success = self.add_subtitle_with_api(script, audio_path)
                if not success:
                    print(f"    ⚠️ 字幕添加失败，但音频添加成功")
            
            # 保存草稿
            try:
                print(f"    🔧 [DEBUG] 开始保存草稿...")
                print(f"           草稿名称: {draft_name}")
                print(f"           script对象: {type(script)}")
                
                # 最终验证草稿状态
                print(f"    🔧 [DEBUG] 保存前最终验证:")
                print(f"           总轨道数: {len(script.tracks)}")
                print(f"           轨道列表: {list(script.tracks.keys())}")
                if audio_track_name in script.tracks:
                    audio_track = script.tracks[audio_track_name]
                    print(f"           音频轨道片段数: {len(audio_track.segments)}")
                    if audio_track.segments:
                        seg = audio_track.segments[0]
                        print(f"           第一个音频片段volume: {seg.volume}")
                        print(f"           第一个音频片段有fade: {hasattr(seg, 'fade') and seg.fade is not None}")
                
                # 确保保存到正确的文件
                self.save_script_file(script, draft_name)
                print(f"    🔧 [DEBUG] save_script_file调用完成")
                print(f"    ✅ 草稿保存成功")
                return True
            except Exception as e:
                print(f"    ❌ [DEBUG] 保存草稿失败: {e}")
                import traceback
                print(f"    🔧 [DEBUG] 异常详情: {traceback.format_exc()}")
                return False
            
        except Exception as e:
            print(f"    ❌ 添加音频和字幕失败: {e}")
            return False
    
    def add_background_music_with_api(self, script, combination):
        """使用pyJianYingDraft库API添加背景音乐"""
        try:
            print(f"    🎶 添加背景音乐...")
            
            # 获取背景音乐文件路径
            bg_music_file = combination['bg_musics']
            bg_music_path = os.path.join(self.background_music_folder_path, bg_music_file)
            
            if not os.path.exists(bg_music_path):
                print(f"    ❌ 背景音乐文件不存在: {bg_music_path}")
                return False
            
            # 将背景音乐文件添加到script的materials中
            try:
                print(f"    🔧 [DEBUG] 创建背景音乐AudioMaterial，路径: {bg_music_path}")
                bg_music_material = draft.AudioMaterial(bg_music_path)
                print(f"    🔧 [DEBUG] 背景音乐AudioMaterial创建完成:")
                print(f"           material_id: {bg_music_material.material_id}")
                print(f"           duration: {bg_music_material.duration}微秒 ({bg_music_material.duration/1000000:.2f}秒)")
                print(f"           文件名: {bg_music_file}")
                
                print(f"    ✅ 创建背景音乐AudioMaterial成功: {bg_music_file}")
            except Exception as e:
                print(f"    ❌ [DEBUG] 创建背景音乐AudioMaterial失败: {e}")
                import traceback
                print(f"    🔧 [DEBUG] 异常详情: {traceback.format_exc()}")
                return False
            
            # 添加背景音乐轨道（如果不存在）
            bg_music_track_name = "background_music_track"
            try:
                print(f"    🔧 [DEBUG] 检查背景音乐轨道: {bg_music_track_name}")
                print(f"    🔧 [DEBUG] 当前所有轨道: {list(script.tracks.keys())}")
                
                # 检查是否已有指定名称的背景音乐轨道
                if bg_music_track_name not in script.tracks:
                    print(f"    🔧 [DEBUG] 背景音乐轨道不存在，开始创建...")
                    script.add_track(draft.TrackType.audio, bg_music_track_name)
                    print(f"    🔧 [DEBUG] 背景音乐轨道创建完成")
                    print(f"    ✅ 添加背景音乐轨道: {bg_music_track_name}")
                else:
                    print(f"    🔧 [DEBUG] 背景音乐轨道已存在")
                    print(f"    ✅ 使用现有背景音乐轨道: {bg_music_track_name}")
                
                # 验证轨道创建结果
                if bg_music_track_name in script.tracks:
                    track = script.tracks[bg_music_track_name]
                    print(f"    🔧 [DEBUG] 背景音乐轨道验证成功:")
                    print(f"           轨道类型: {track.track_type}")
                    print(f"           轨道名称: {track.name}")
                    print(f"           轨道ID: {track.track_id}")
                    print(f"           静音状态: {track.mute}")
                else:
                    print(f"    ❌ [DEBUG] 背景音乐轨道验证失败: 轨道未在tracks中找到")
                    
            except Exception as e:
                print(f"    ❌ [DEBUG] 添加背景音乐轨道失败: {e}")
                import traceback
                print(f"    🔧 [DEBUG] 异常详情: {traceback.format_exc()}")
                return False
            
            # 创建背景音乐片段
            try:
                # 计算目标时长和源时长
                video_duration = script.duration
                bg_music_duration = bg_music_material.duration
                
                print(f"    📊 视频时长: {video_duration/1000000:.2f}s, 背景音乐时长: {bg_music_duration/1000000:.2f}s")
                
                # 根据配置调整背景音乐
                target_duration, speed_ratio = self.calculate_background_music_adjustments(video_duration, bg_music_duration)
                
                # 添加详细的调试信息
                print(f"    🔧 [DEBUG] 背景音乐调整配置:")
                print(f"           较长处理方式: {self.bg_music_longer_handling}")
                print(f"           较短处理方式: {self.bg_music_shorter_handling}")
                print(f"           背景音乐 > 视频: {bg_music_duration > video_duration}")
                print(f"    🔧 [DEBUG] calculate_background_music_adjustments返回:")
                print(f"           target_duration: {target_duration}微秒 ({target_duration/1000000:.2f}秒)")
                print(f"           speed_ratio: {speed_ratio:.2f}")
                
                # 创建背景音乐片段
                print(f"    🔧 [DEBUG] 开始创建背景音乐AudioSegment...")
                
                # 将微秒转换为秒
                target_duration_sec = target_duration / 1000000
                
                # 正确计算source_timerange：从音频文件中截取的部分
                if self.bg_music_longer_handling == "trim" and bg_music_duration > video_duration:
                    # 裁剪模式：从音频开头截取video_duration长度
                    source_duration_us = video_duration
                else:
                    # 其他模式：使用计算得到的target_duration
                    source_duration_us = min(bg_music_duration, target_duration)
                
                source_duration_sec = source_duration_us / 1000000
                
                print(f"    🔧 [DEBUG] AudioSegment时长计算:")
                print(f"           target_duration_sec: {target_duration_sec}s (时间线播放时长)")
                print(f"           source_duration_us: {source_duration_us}微秒 ({source_duration_us/1000000:.2f}秒) (从音频文件截取长度)")
                print(f"           是否发生裁剪: {source_duration_us < bg_music_duration}")
                if source_duration_us < bg_music_duration:
                    print(f"           裁剪长度: {(bg_music_duration - source_duration_us)/1000000:.2f}秒")
                
                print(f"    🔧 [DEBUG] 背景音乐AudioSegment参数:")
                print(f"           material: AudioMaterial对象 (id: {bg_music_material.material_id})")
                print(f"           target_timerange: 0s ~ {target_duration_sec}s")
                print(f"           source_timerange: 0s ~ {source_duration_sec}s")
                
                # 使用传统构造方式：先创建素材实例，再传入片段构造函数
                bg_music_segment = draft.AudioSegment(
                    bg_music_material,  # 直接传入material对象作为第一个参数
                    draft.trange("0s", f"{target_duration_sec}s"),  # target_timerange作为第二个参数
                    source_timerange=draft.trange("0s", f"{source_duration_sec}s")  # source_timerange作为关键字参数
                )
                
                print(f"    🔧 [DEBUG] 背景音乐AudioSegment创建完成:")
                print(f"           segment_id: {bg_music_segment.segment_id}")
                print(f"           material_id: {bg_music_segment.material_id}")
                print(f"           target_timerange: {bg_music_segment.target_timerange.start}~{bg_music_segment.target_timerange.end}")
                print(f"           source_timerange: {bg_music_segment.source_timerange.start}~{bg_music_segment.source_timerange.end}")
                print(f"           volume: {bg_music_segment.volume}")
                print(f"           speed: {bg_music_segment.speed}")
                
                # 重要：使用add_material方法将背景音乐AudioMaterial添加到script中
                script.add_material(bg_music_segment.material_instance)
                print(f"    🔧 [DEBUG] 使用add_material方法添加背景音乐AudioMaterial到script中")
                
                # 应用背景音乐音量设置
                print(f"    🔧 [DEBUG] 应用背景音乐设置...")
                original_volume = bg_music_segment.volume
                if hasattr(self, 'bg_music_volume') and self.bg_music_volume != 100:
                    bg_music_segment.volume = self.bg_music_volume / 100.0
                    db_value = 20 * (self.bg_music_volume / 100 - 1) if self.bg_music_volume != 100 else 0
                    print(f"    🔧 [DEBUG] 背景音乐音量调整: {original_volume} -> {bg_music_segment.volume} ({self.bg_music_volume}%)")
                    print(f"    🔊 设置背景音乐音量: {self.bg_music_volume}% (≈{db_value:.1f}dB)")
                else:
                    print(f"    🔧 [DEBUG] 保持默认背景音乐音量: {bg_music_segment.volume} (0dB)")
                
                # 应用背景音乐淡入淡出效果
                fade_applied = False
                if hasattr(self, 'bg_music_fade_in') and hasattr(self, 'bg_music_fade_out'):
                    if self.bg_music_fade_in > 0 or self.bg_music_fade_out > 0:
                        print(f"    🔧 [DEBUG] 应用背景音乐淡入淡出: 淡入{self.bg_music_fade_in}s, 淡出{self.bg_music_fade_out}s")
                        bg_music_segment.add_fade(f"{self.bg_music_fade_in}s", f"{self.bg_music_fade_out}s")
                        fade_applied = True
                        print(f"    🔧 [DEBUG] 背景音乐淡入淡出效果已添加到bg_music_segment")
                        print(f"    🎚️ 设置背景音乐淡入淡出: 淡入{self.bg_music_fade_in}s, 淡出{self.bg_music_fade_out}s")
                    else:
                        print(f"    🔧 [DEBUG] 无背景音乐淡入淡出设置")
                else:
                    print(f"    🔧 [DEBUG] 背景音乐淡入淡出属性不存在")
                
                # 检查fade对象
                if fade_applied:
                    if hasattr(bg_music_segment, 'fade') and bg_music_segment.fade:
                        print(f"    🔧 [DEBUG] 背景音乐fade对象存在:")
                        print(f"           fade_id: {bg_music_segment.fade.fade_id}")
                        print(f"           in_duration: {bg_music_segment.fade.in_duration}")
                        print(f"           out_duration: {bg_music_segment.fade.out_duration}")
                    else:
                        print(f"    ❌ [DEBUG] 背景音乐fade对象不存在或为None")
                
                # 应用速度调整
                if speed_ratio != 1.0:
                    print(f"    🔧 [DEBUG] 背景音乐需要速度调整: {speed_ratio:.2f}x")
                    print(f"    ⚡ 背景音乐速度调整: {speed_ratio:.2f}x")
                else:
                    print(f"    🔧 [DEBUG] 背景音乐无需速度调整")
                
                # 添加片段到背景音乐轨道
                print(f"    🔧 [DEBUG] 开始添加背景音乐片段到轨道...")
                print(f"           轨道名称: {bg_music_track_name}")
                print(f"           片段ID: {bg_music_segment.segment_id}")
                
                script.add_segment(bg_music_segment, bg_music_track_name)
                print(f"    🔧 [DEBUG] 背景音乐add_segment调用完成")
                
                # 验证片段是否成功添加
                if bg_music_track_name in script.tracks:
                    track = script.tracks[bg_music_track_name]
                    segment_count = len(track.segments)
                    print(f"    🔧 [DEBUG] 背景音乐轨道验证:")
                    print(f"           轨道存在: True")
                    print(f"           片段数量: {segment_count}")
                    if segment_count > 0:
                        last_segment = track.segments[-1]
                        print(f"           最后片段ID: {last_segment.segment_id}")
                        print(f"           最后片段volume: {last_segment.volume}")
                        print(f"           最后片段有fade: {hasattr(last_segment, 'fade') and last_segment.fade is not None}")
                else:
                    print(f"    ❌ [DEBUG] 背景音乐轨道验证失败: 轨道不存在")
                
                print(f"    ✅ 添加背景音乐片段到轨道: {bg_music_track_name}")
                
                # 修复背景音乐轨道渲染配置，确保音频能正常播放
                self.fix_audio_track_rendering(script, bg_music_track_name)
                
                # 检查是否需要根据背景音乐设置裁剪视频
                if self.bg_music_shorter_handling == "trim_video" and bg_music_duration < video_duration:
                    print(f"    🔧 [DEBUG] 背景音乐比视频短，需要裁剪视频...")
                    original_duration = script.duration
                    script.duration = target_duration
                    print(f"    ✂️ 根据背景音乐长度裁剪视频: {original_duration/1000000:.2f}s -> {script.duration/1000000:.2f}s")
                    
                    # 裁剪所有视频轨道的片段
                    for track_name, track in script.tracks.items():
                        if hasattr(track, 'track_type') and track.track_type.name == 'video':
                            for segment in track.segments:
                                if segment.end > script.duration:
                                    if segment.start < script.duration:
                                        # 部分重叠，裁剪片段
                                        segment.duration = script.duration - segment.start
                                        print(f"    🔧 [DEBUG] 根据背景音乐裁剪视频片段 {segment.segment_id} 到 {segment.duration/1000000:.2f}s")
                                    else:
                                        # 完全超出，移除片段
                                        print(f"    🔧 [DEBUG] 移除超出背景音乐时长的视频片段 {segment.segment_id}")
                                        track.segments.remove(segment)
                elif self.bg_music_longer_handling == "trim" and bg_music_duration > video_duration:
                    print(f"    🔧 [DEBUG] 背景音乐比视频长，已在计算中裁剪背景音乐到视频长度")
                    print(f"    ✂️ 背景音乐裁剪: {bg_music_duration/1000000:.2f}s -> {target_duration/1000000:.2f}s")
                
                return True
                
            except Exception as e:
                print(f"    ❌ 创建背景音乐片段失败: {e}")
                return False
            
        except Exception as e:
            print(f"    ❌ 添加背景音乐失败: {e}")
            return False
    
    def calculate_background_music_adjustments(self, video_duration, bg_music_duration):
        """计算背景音乐调整参数"""
        try:
            if video_duration <= 0:
                return bg_music_duration, 1.0
            
            # 根据配置处理背景音乐长度
            if bg_music_duration > video_duration:
                # 背景音乐比视频长
                print(f"    🔧 [DEBUG] 背景音乐比视频长，处理方式: {self.bg_music_longer_handling}")
                if self.bg_music_longer_handling == "speed_up":
                    # 加速背景音乐以适应视频长度
                    speed_ratio = bg_music_duration / video_duration
                    print(f"    🔧 [DEBUG] 选择加速，速度比例: {speed_ratio:.2f}")
                    return video_duration, speed_ratio
                elif self.bg_music_longer_handling == "trim":
                    # 裁剪背景音乐以适应视频长度
                    print(f"    🔧 [DEBUG] 选择裁剪，将背景音乐从{bg_music_duration/1000000:.2f}s裁剪到{video_duration/1000000:.2f}s")
                    return video_duration, 1.0
                else:  # "none"
                    # 保持背景音乐原样
                    print(f"    🔧 [DEBUG] 选择无处理，保持背景音乐原样")
                    return bg_music_duration, 1.0
            else:
                # 背景音乐比视频短或相等
                if self.bg_music_shorter_handling == "trim_video":
                    # 将视频裁剪到背景音乐长度
                    return bg_music_duration, 1.0
                elif self.bg_music_shorter_handling == "slow_down":
                    # 减速背景音乐以适应视频长度
                    speed_ratio = bg_music_duration / video_duration
                    return video_duration, speed_ratio
                elif self.bg_music_shorter_handling == "allow_silence":
                    # 允许后面静音，保持背景音乐原样
                    return bg_music_duration, 1.0
                else:  # "none"
                    # 保持背景音乐原样
                    return bg_music_duration, 1.0
        except Exception as e:
            print(f"    ❌ 计算背景音乐调整参数失败: {e}")
            return bg_music_duration, 1.0
    
    def calculate_audio_adjustments(self, video_duration, audio_duration):
        """计算音频调整参数"""
        try:
            if video_duration <= 0:
                return audio_duration, 1.0
            
            # 根据配置处理音频长度
            if audio_duration > video_duration:
                # 音频比视频长
                if self.audio_longer_handling == "speed_up":
                    # 加速音频以适应视频长度
                    speed_ratio = audio_duration / video_duration
                    return video_duration, speed_ratio
                elif self.audio_longer_handling == "trim":
                    # 裁剪音频
                    return video_duration, 1.0
                else:
                    # 保持原样
                    return audio_duration, 1.0
                    
            elif audio_duration < video_duration:
                # 音频比视频短
                if self.audio_shorter_handling == "trim_video":
                    # 裁剪视频（返回音频长度）
                    return audio_duration, 1.0
                elif self.audio_shorter_handling == "slow_down":
                    # 减速音频以适应视频长度
                    speed_ratio = audio_duration / video_duration
                    return video_duration, speed_ratio
                else:
                    # 保持原样或允许静音
                    return audio_duration, 1.0
            
            return audio_duration, 1.0
            
        except Exception as e:
            print(f"    ⚠️ 计算音频调整参数失败: {e}")
            return audio_duration, 1.0
    
    def add_subtitle_with_api(self, script, audio_path):
        """使用库API添加字幕"""
        try:
            # 查找对应的SRT文件
            audio_name = os.path.splitext(os.path.basename(audio_path))[0]
            srt_file_path = os.path.join(os.path.dirname(audio_path), f"{audio_name}.srt")
            
            if not os.path.exists(srt_file_path):
                print(f"    💬 未找到字幕文件: {audio_name}.srt")
                return False
            
            print(f"    📝 找到字幕文件: {audio_name}.srt")
            
            # 使用库的import_srt方法导入字幕
            try:
                print(f"    🔧 [DEBUG] 当前字幕样式设置: {self.subtitle_style}")
                
                if self.subtitle_style == "white_bg_black_border":
                    print(f"    🔧 [DEBUG] 开始处理白底黑框样式...")
                    # 使用自定义样式 - 使用style_reference方法
                    style_objects = self.create_white_bg_black_border_style()
                    print(f"    🔧 [DEBUG] create_white_bg_black_border_style返回: {style_objects is not None}")
                    
                    if style_objects:
                        print(f"    🔧 [DEBUG] 开始创建style_reference TextSegment...")
                        
                        # 创建包含描边的TextSegment作为样式参考
                        # 竖屏从下向上16%的位置
                        # transform_y坐标系：-1(底部) 到 1(顶部)，0为中心
                        # 从底部向上16% = -1 + (16% * 2) = -1 + 0.32 = -0.68
                        custom_transform_y = -0.68  # 从底部向上16%
                        print(f"    🔧 [DEBUG] 白底黑框字幕位置: 从底部向上16% -> transform_y={custom_transform_y}")
                        
                        style_reference = draft.TextSegment(
                            "样式参考", 
                            draft.trange("0s", "1s"),  # 1秒的临时时间范围
                            style=style_objects['text_style'],
                            border=style_objects['border'],
                            clip_settings=draft.ClipSettings(transform_y=custom_transform_y)  # 字幕位置：从底部向上16%
                        )
                        
                        print(f"    🔧 [DEBUG] style_reference TextSegment创建完成:")
                        print(f"           文本: {style_reference.text}")
                        print(f"           样式字号: {style_reference.style.size}")
                        print(f"           样式颜色: {style_reference.style.color}")
                        print(f"           样式自动换行: {style_reference.style.auto_wrapping}")
                        print(f"           有描边: {style_reference.border is not None}")
                        if style_reference.border:
                            print(f"           描边颜色: {style_reference.border.color}")
                            print(f"           描边宽度: {style_reference.border.width}")
                        if style_reference.clip_settings:
                            transform_y_val = style_reference.clip_settings.transform_y
                            # 计算相对于底部的百分比位置
                            percent_from_bottom = (transform_y_val + 1) / 2 * 100
                            print(f"           位置Y: {transform_y_val:.3f} (从底部向上{percent_from_bottom:.1f}%)")
                        else:
                            print(f"           位置Y: None")
                        
                        print(f"    🔧 [DEBUG] 调用import_srt，参数:")
                        print(f"           srt_file_path: {srt_file_path}")
                        print(f"           track_name: subtitle")
                        print(f"           time_offset: 0s")
                        print(f"           style_reference: TextSegment对象")
                        print(f"           clip_settings: None (让其使用style_reference的设置)")
                        
                        # 关键：传递clip_settings=None让import_srt使用style_reference的clip_settings
                        script.import_srt(
                            srt_file_path,
                            track_name="subtitle",
                            time_offset="0s",
                            style_reference=style_reference,
                            clip_settings=None  # 这样才会使用style_reference的设置
                        )
                        print(f"    ✅ 字幕导入成功 (白字黑边样式)")
                        
                        # 检查导入后的轨道内容
                        print(f"    🔧 [DEBUG] 检查导入后的字幕轨道...")
                        if "subtitle" in script.tracks:
                            subtitle_track = script.tracks["subtitle"]
                            print(f"           轨道类型: {subtitle_track.track_type}")
                            print(f"           轨道片段数量: {len(subtitle_track.segments)}")
                            if subtitle_track.segments:
                                first_seg = subtitle_track.segments[0]
                                print(f"           第一个片段文本: {first_seg.text}")
                                print(f"           第一个片段字号: {first_seg.style.size}")
                                print(f"           第一个片段颜色: {first_seg.style.color}")
                                print(f"           第一个片段有描边: {first_seg.border is not None}")
                                if first_seg.border:
                                    print(f"           第一个片段描边颜色: {first_seg.border.color}")
                                    print(f"           第一个片段描边宽度: {first_seg.border.width}")
                        else:
                            print(f"    ❌ [DEBUG] 字幕轨道未找到!")
                    else:
                        print(f"    ❌ [DEBUG] 样式对象创建失败，使用默认样式")
                        # 样式创建失败，使用默认样式
                        script.import_srt(
                            srt_file_path,
                            track_name="subtitle",
                            time_offset="0s"
                        )
                        print(f"    ✅ 字幕导入成功 (默认样式)")
                else:
                    print(f"    🔧 [DEBUG] 使用默认字幕样式")
                    # 使用默认样式
                    script.import_srt(
                        srt_file_path,
                        track_name="subtitle",
                        time_offset="0s"
                    )
                    print(f"    ✅ 字幕导入成功 (默认样式)")
                
                return True
                
            except Exception as e:
                print(f"    ❌ 字幕导入失败: {e}")
                return False
            
        except Exception as e:
            print(f"    ❌ 字幕处理失败: {e}")
            return False
    
    def create_white_bg_black_border_style(self):
        """创建白字黑边字幕样式（白色文字 + 黑色描边）"""
        try:
            print(f"    🔧 [DEBUG] 开始创建白字黑边样式...")
            
            # 创建文本样式
            text_style = draft.TextStyle(
                size=12.0,  # 12字号
                color=(1.0, 1.0, 1.0),  # 白色文字 (R, G, B)
                align=1,  # 居中对齐
                auto_wrapping=True,  # 启用自动换行
                line_spacing=2  # 行间距
            )
            print(f"    🔧 [DEBUG] TextStyle创建完成:")
            print(f"           字号: {text_style.size}")
            print(f"           颜色: {text_style.color} (应为白色 1.0,1.0,1.0)")
            print(f"           对齐: {text_style.align} (1=居中)")
            print(f"           自动换行: {text_style.auto_wrapping}")
            print(f"           行间距: {text_style.line_spacing}")
            
            # 创建黑色描边
            text_border = draft.TextBorder(
                color=(0.0, 0.0, 0.0),  # 黑色描边
                width=40.0,  # 描边粗细为40
                alpha=1.0  # 描边不透明
            )
            print(f"    🔧 [DEBUG] TextBorder创建完成:")
            print(f"           描边颜色: {text_border.color} (应为黑色 0.0,0.0,0.0)")
            print(f"           描边宽度: {text_border.width} (原始40.0)")
            print(f"           描边透明度: {text_border.alpha}")
            
            result = {
                'text_style': text_style,
                'border': text_border,
                'background': None  # 不使用背景
            }
            print(f"    🔧 [DEBUG] 样式对象创建成功，返回包含text_style和border的字典")
            return result
        except Exception as e:
            print(f"    ❌ [DEBUG] 创建字幕样式失败: {e}")
            import traceback
            print(f"    🔧 [DEBUG] 异常详情: {traceback.format_exc()}")
            return None
    
    
    def get_actual_segment_duration(self, draft_info, material_id):
        """获取素材在时间线上的实际使用时长"""
        total_duration = 0
        
        try:
            if 'tracks' in draft_info:
                for track in draft_info['tracks']:
                    if track.get('type') == 'video' and 'segments' in track:
                        segments = track['segments']
                        
                        for segment in segments:
                            if segment.get('material_id') == material_id:
                                # 计算片段实际时长：target_timerange.duration
                                target_timerange = segment.get('target_timerange', {})
                                if 'duration' in target_timerange:
                                    total_duration += target_timerange['duration']
                                elif 'start' in target_timerange and 'end' in target_timerange:
                                    # 如果没有duration，用end-start计算
                                    total_duration += target_timerange['end'] - target_timerange['start']
            
            return total_duration if total_duration > 0 else None
            
        except Exception as e:
            print(f"    ⚠️ 获取片段实际时长失败: {e}")
            return None
    
    def get_video_segment_info(self, draft_name, video_file_path):
        """获取视频片段在草稿中的详细信息，包括时间范围"""
        try:
            # 读取草稿文件
            draft_info_path = os.path.join(self.draft_folder_path, draft_name, "draft_info.json")
            
            if not os.path.exists(draft_info_path):
                print(f"    ❌ 草稿文件不存在: {draft_info_path}")
                return None
            
            with open(draft_info_path, 'r', encoding='utf-8') as f:
                draft_data = json.load(f)
            
            # 从视频文件名找到对应的material_id
            video_filename = os.path.basename(video_file_path)
            material_id = None
            
            # 在materials.videos中查找
            if 'materials' in draft_data and 'videos' in draft_data['materials']:
                videos = draft_data['materials']['videos']
                for video in videos:
                    if video.get('material_name', '').endswith(video_filename):
                        material_id = video.get('id')
                        break
            
            if not material_id:
                print(f"    ❌ 在草稿中未找到视频文件 {video_filename} 对应的素材")
                return None
            
            # 在tracks中查找对应的视频片段
            segment_info = None
            if 'tracks' in draft_data:
                for track in draft_data['tracks']:
                    if track.get('type') == 'video' and 'segments' in track:
                        segments = track['segments']
                        for segment in segments:
                            if segment.get('material_id') == material_id:
                                # 找到了对应的片段
                                target_timerange = segment.get('target_timerange', {})
                                source_timerange = segment.get('source_timerange', {})
                                
                                segment_info = {
                                    'material_id': material_id,
                                    'target_start': target_timerange.get('start', 0),
                                    'target_duration': target_timerange.get('duration', 0),
                                    'source_start': source_timerange.get('start', 0),
                                    'source_duration': source_timerange.get('duration', 0),
                                }
                                
                                # 计算片段在时间线上的结束时间对应原视频的时间点
                                if segment_info['source_duration'] > 0 and segment_info['target_duration'] > 0:
                                    # 片段在原视频中的结束时间
                                    segment_info['source_end_time'] = (segment_info['source_start'] + segment_info['source_duration']) / 1000000.0
                                else:
                                    # 如果没有source_duration，使用target_duration
                                    segment_info['source_end_time'] = (segment_info['source_start'] + segment_info['target_duration']) / 1000000.0
                                
                                print(f"    🎯 找到视频片段信息:")
                                print(f"       时间线: {segment_info['target_start']/1000000:.2f}s - {(segment_info['target_start']+segment_info['target_duration'])/1000000:.2f}s")
                                print(f"       原视频: {segment_info['source_start']/1000000:.2f}s - {segment_info['source_end_time']:.2f}s")
                                
                                return segment_info
            
            print(f"    ❌ 在草稿轨道中未找到视频片段信息")
            return None
            
        except Exception as e:
            print(f"    ❌ 获取视频片段信息失败: {e}")
            return None
    
    def get_draft_timeline_info(self, draft_name):
        """获取草稿时间线信息，包括总时长和最后时刻的视频片段"""
        try:
            # 读取草稿文件
            draft_info_path = os.path.join(self.draft_folder_path, draft_name, "draft_info.json")
            
            if not os.path.exists(draft_info_path):
                print(f"    ❌ 草稿文件不存在: {draft_info_path}")
                return None
            
            with open(draft_info_path, 'r', encoding='utf-8') as f:
                draft_data = json.load(f)
            
            # 获取草稿总时长
            draft_duration = draft_data.get('duration', 0)
            
            # 找到在草稿最后时刻仍然活跃的视频片段
            last_video_segment = None
            last_video_material_id = None
            last_segment_end_time = 0
            
            if 'tracks' in draft_data:
                for track in draft_data['tracks']:
                    if track.get('type') == 'video' and 'segments' in track:
                        segments = track['segments']
                        
                        for segment in segments:
                            target_timerange = segment.get('target_timerange', {})
                            segment_start = target_timerange.get('start', 0)
                            segment_duration = target_timerange.get('duration', 0)
                            segment_end = segment_start + segment_duration
                            
                            # 找到结束时间最接近草稿总时长的视频片段
                            if segment_end >= last_segment_end_time and segment_end <= draft_duration:
                                last_segment_end_time = segment_end
                                last_video_material_id = segment.get('material_id')
                                last_video_segment = {
                                    'segment': segment,
                                    'material_id': last_video_material_id,
                                    'timeline_end': segment_end,
                                    'timeline_start': segment_start,
                                    'timeline_duration': segment_duration,
                                    'source_timerange': segment.get('source_timerange', {}),
                                    'target_timerange': target_timerange
                                }
            
            if not last_video_segment:
                print(f"    ❌ 未找到草稿最后时刻的视频片段")
                return None
            
            # 获取对应的视频文件路径
            video_file_path = None
            if 'materials' in draft_data and 'videos' in draft_data['materials']:
                videos = draft_data['materials']['videos']
                for video in videos:
                    if video.get('id') == last_video_material_id:
                        material_name = video.get('material_name', '')
                        # 尝试在最近替换的视频中找到
                        if hasattr(self, 'last_replaced_videos') and self.last_replaced_videos:
                            for video_path in self.last_replaced_videos:
                                if material_name in video_path or os.path.basename(video_path) in material_name:
                                    video_file_path = video_path
                                    break
                        break
            
            if not video_file_path:
                # 尝试从最近替换的视频中找一个
                if hasattr(self, 'last_replaced_videos') and self.last_replaced_videos:
                    video_file_path = self.last_replaced_videos[0]
                    print(f"    ⚠️ 使用最近替换的视频作为回退: {os.path.basename(video_file_path)}")
                else:
                    print(f"    ❌ 未找到最后视频片段对应的文件路径")
                    return None
            
            # 计算在原视频中的时间点
            source_start = last_video_segment['source_timerange'].get('start', 0)
            source_duration = last_video_segment['source_timerange'].get('duration', 0)
            timeline_duration = last_video_segment['timeline_duration']
            
            # 计算草稿结束时对应原视频的时间点
            if timeline_duration > 0 and source_duration > 0:
                # 计算在片段中的进度比例
                time_in_segment = draft_duration - last_video_segment['timeline_start']
                progress_ratio = min(time_in_segment / timeline_duration, 1.0)
                
                # 计算在原视频中的时间点
                video_time_seconds = (source_start + source_duration * progress_ratio) / 1000000.0
            elif source_duration > 0:
                # 如果timeline_duration为0，但source_duration不为0，使用source结束时间
                video_time_seconds = (source_start + source_duration) / 1000000.0
            else:
                # 都为0的情况，使用source_start
                video_time_seconds = source_start / 1000000.0
            
            timeline_info = {
                'draft_duration': draft_duration,
                'draft_duration_seconds': draft_duration / 1000000.0,
                'video_file_path': video_file_path,
                'video_time_seconds': video_time_seconds,
                'last_segment_info': last_video_segment
            }
            
            print(f"    🎯 草稿时间线信息:")
            print(f"       草稿总时长: {timeline_info['draft_duration_seconds']:.2f}s")
            print(f"       最后视频: {os.path.basename(video_file_path)}")
            print(f"       对应时间: {video_time_seconds:.2f}s")
            
            return timeline_info
            
        except Exception as e:
            print(f"    ❌ 获取草稿时间线信息失败: {e}")
            return None

    def get_video_file_info(self, video_path):
        """获取视频文件信息，使用pyJianYingDraft的VideoMaterial获取准确信息"""
        try:
            # 导入pyJianYingDraft
            import sys
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from pyJianYingDraft import VideoMaterial
            
            # 创建VideoMaterial实例获取准确信息
            video_material = VideoMaterial(video_path)
            
            video_info = {
                'duration': video_material.duration,  # VideoMaterial.duration已经是微秒
                'width': video_material.width,
                'height': video_material.height,
                'material_type': video_material.material_type
            }
            
            if self.debug:
                print(f"    🔍 DEBUG VideoMaterial: duration={video_material.duration} 微秒 = {video_material.duration/1000000:.3f}秒")
            
            return video_info
                
        except Exception as e:
            print(f"    ⚠️ 使用VideoMaterial获取文件信息失败: {e}")
            
        # 无论VideoMaterial是否成功，都用ffprobe验证时长
        try:
            import subprocess
            
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                import json
                info = json.loads(result.stdout)
                
                video_info = {}
                
                # 获取时长（微秒）
                if 'format' in info and 'duration' in info['format']:
                    duration_sec = float(info['format']['duration'])
                    video_info['duration'] = int(duration_sec * 1000000)
                
                # 获取分辨率
                for stream in info.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        if 'width' in stream:
                            video_info['width'] = stream['width']
                        if 'height' in stream:
                            video_info['height'] = stream['height']
                        break
                
                if self.debug:
                    print(f"    🔍 DEBUG ffprobe: duration={duration_sec}秒 = {video_info['duration']}微秒")
                
                return video_info
            else:
                return {'duration': 5000000}  # 默认5秒
                
        except Exception as e2:
            print(f"    ⚠️ ffprobe方法也失败: {e2}")
            return {'duration': 5000000}  # 默认5秒
    
    def run(self):
        """运行CLI工具"""
        try:
            self.print_header("剪映批量草稿复制与素材替换工具")
            print("🚀 支持part1/part2/part3/part4...无限扩展文件夹组合式素材替换")
            print("💡 支持顺序模式和随机裂变模式")
            print("🎯 自动批量复制草稿并替换对应素材")
            
            # 添加测试选项
            print(f"\n🧪 开发者选项")
            test_options = ["继续正常流程", "测试封面图生成功能"]
            test_idx, test_str = self.get_user_choice(test_options, "选择模式", default_index=0)
            
            if test_idx == 1:  # 测试封面图生成
                return self.test_jianying_cover_generation()
            
            # 1. 设置路径
            if not self.setup_paths():
                return
            
            # 2. 选择源草稿
            if not self.select_source_draft():
                return
            
            # 3. 设置素材文件夹
            if not self.setup_materials_folder():
                return
            
            # 4. 选择替换模式
            if not self.select_replacement_mode():
                return
            
            # 5. 选择时间线处理模式
            if not self.select_timeline_mode():
                return
            
            # 6. 创建文件夹并扫描素材
            if not self.create_part_folders_and_scan():
                return
            
            # 7. 批量处理草稿
            if not self.batch_process_drafts():
                return
            
            # 8. 文本替换（如果已启用）
            if self.enable_text_replacement:
                if not self.process_text_replacement():
                    print("⚠️ 文本替换过程中出现问题，但草稿创建已完成")
            
            self.print_header("处理完成")
            print("🎉 所有草稿已成功创建，可以在剪映中打开查看")
            
        except KeyboardInterrupt:
            print("\n\n👋 用户取消操作，再见!")
        except Exception as e:
            self.print_error(f"程序运行出错: {e}")
            import traceback
            traceback.print_exc()
    
    def setup_text_replacement(self):
        """设置文本替换功能"""
        self.print_section("文本替换配置")
        
        # 询问是否需要文本替换
        text_options = ["是", "否"]
        text_idx, text_str = self.get_user_choice(text_options, "是否需要文本替换", default_index=1)
        
        if text_idx == 1:  # 选择"否"
            self.enable_text_replacement = False
            return False
        
        self.enable_text_replacement = True
        print("✅ 启用文本替换功能")
        
        # 选择替换文本数量
        count_options = ["1段（标题）", "2段（标题+水印）"]
        count_idx, count_str = self.get_user_choice(count_options, "选择替换的文本数量", default_index=0)
        
        self.text_replacement_count = count_idx + 1
        print(f"✅ 文本替换数量: {self.text_replacement_count}段")
        
        # 设置文本文件夹路径
        if not self.setup_text_folder():
            return False
        
        # 设置文本文件路径
        if not self.setup_text_files():
            return False
        
        # 读取和解析文本内容
        if not self.load_text_contents():
            return False
        
        # 选择文本替换规则
        selection_options = ["按顺序然后循环", "随机"]
        selection_idx, selection_str = self.get_user_choice(selection_options, "文本选择规则", default_index=0)
        
        self.text_selection_mode = "sequential" if selection_idx == 0 else "random"
        print(f"✅ 文本选择规则: {selection_str}")
        
        return True
    
    def setup_text_folder(self):
        """设置文本文件夹路径"""
        print(f"\n📁 文本文件夹配置")
        
        # 默认文本文件夹路径：./materials/text
        default_text_path = os.path.join(self.materials_folder_path, "text")
        
        print(f"默认文本文件夹: {default_text_path}")
        
        if os.path.exists(default_text_path):
            self.text_folder_path = default_text_path
            print(f"✅ 找到默认文本文件夹")
        else:
            print(f"⚠️ 默认文本文件夹不存在")
            
            # 询问是否创建或使用其他路径
            create_options = [
                f"创建默认文本文件夹: {default_text_path}",
                "指定其他文本文件夹路径"
            ]
            create_idx, create_str = self.get_user_choice(create_options, "请选择")
            
            if create_idx == 0:
                # 创建默认文件夹
                try:
                    os.makedirs(default_text_path, exist_ok=True)
                    self.text_folder_path = default_text_path
                    print(f"✅ 已创建文本文件夹: {default_text_path}")
                except Exception as e:
                    print(f"❌ 创建文本文件夹失败: {e}")
                    return False
            else:
                # 指定其他路径
                custom_path = self.get_user_input("请输入文本文件夹路径")
                if os.path.exists(custom_path):
                    self.text_folder_path = custom_path
                    print(f"✅ 使用指定文本文件夹: {custom_path}")
                else:
                    print(f"❌ 指定的文本文件夹不存在: {custom_path}")
                    return False
        
        return True
    
    def configure_text_tracks_selection(self):
        """从源草稿中提取文本轨道，让用户选择要替换的轨道"""
        print(f"\n📋 选择要替换的文本轨道")
        
        # 从源草稿中提取文本轨道
        text_tracks = self.extract_text_tracks_from_draft(self.selected_draft)
        if not text_tracks:
            print("❌ 源草稿中没有找到文本轨道")
            return False
        
        print(f"📊 在源草稿 '{self.selected_draft}' 中找到 {len(text_tracks)} 个文本轨道:")
        
        # 显示所有文本轨道及其内容
        for i, track in enumerate(text_tracks):
            track_display_name = track['track_name'] if track['track_name'] else f"文本轨道{i+1}"
            print(f"\n  🎬 轨道{i+1}. 【{track_display_name}】({len(track['segments'])}个片段)")
            
            for j, segment in enumerate(track['segments']):
                preview = segment['text'][:40] + "..." if len(segment['text']) > 40 else segment['text']
                start_time_str = f"{segment['start_time']/1000000:.1f}s"
                duration_str = f"{segment['duration']/1000000:.1f}s"
                print(f"       📝 内容: \"{preview}\" (时间:{start_time_str}, 时长:{duration_str})")
        
        # 选择要替换的轨道
        selected_tracks = []
        
        for text_type in (['content'] if self.text_replacement_count == 1 else ['content', 'watermark']):
            type_name = "标题" if text_type == 'content' else "水印"
            
            print(f"\n🎯 选择要替换的{type_name}轨道:")
            
            # 创建清晰的选项，显示轨道内容
            track_options = []
            for i, track in enumerate(text_tracks):
                # 获取轨道名称
                track_display_name = track['track_name'] if track['track_name'] else f"文本轨道{i+1}"
                
                # 获取轨道的主要文本内容作为预览
                if track['segments']:
                    # 如果有多个片段，显示所有片段的简短预览
                    if len(track['segments']) == 1:
                        main_text = track['segments'][0]['text'][:25] + ("..." if len(track['segments'][0]['text']) > 25 else "")
                        track_options.append(f"轨道{i+1}【{track_display_name}】: \"{main_text}\"")
                    else:
                        # 多个片段时，显示第一个片段和片段数量
                        first_text = track['segments'][0]['text'][:20] + ("..." if len(track['segments'][0]['text']) > 20 else "")
                        track_options.append(f"轨道{i+1}【{track_display_name}】: \"{first_text}\" (+{len(track['segments'])-1}个片段)")
                else:
                    track_options.append(f"轨道{i+1}【{track_display_name}】: (无内容)")
            track_options.append("跳过此类型")
            
            track_idx, track_str = self.get_user_choice(track_options, f"选择{type_name}轨道")
            
            if track_idx < len(text_tracks):
                selected_track = text_tracks[track_idx]
                selected_tracks.append({
                    'type': text_type,
                    'track_index': track_idx,  # 在文本轨道数组中的索引
                    'original_track_index': selected_track['track_index'],  # 在所有轨道中的真实索引
                    'track_info': selected_track
                })
                # 显示选择的轨道及其内容，更清晰
                track_display_name = selected_track['track_name'] if selected_track['track_name'] else f"文本轨道{track_idx+1}"
                if selected_track['segments']:
                    if len(selected_track['segments']) == 1:
                        content_preview = selected_track['segments'][0]['text'][:30] + ("..." if len(selected_track['segments'][0]['text']) > 30 else "")
                        print(f"✅ 选择{type_name}轨道: 轨道{track_idx+1}【{track_display_name}】- \"{content_preview}\"")
                    else:
                        first_content = selected_track['segments'][0]['text'][:25] + ("..." if len(selected_track['segments'][0]['text']) > 25 else "")
                        print(f"✅ 选择{type_name}轨道: 轨道{track_idx+1}【{track_display_name}】- \"{first_content}\" (共{len(selected_track['segments'])}个片段)")
                else:
                    print(f"✅ 选择{type_name}轨道: 轨道{track_idx+1}【{track_display_name}】(无内容)")
            else:
                print(f"⏭️ 跳过{type_name}替换")
        
        if not selected_tracks:
            print("❌ 没有选择任何要替换的轨道")
            return False
        
        self.selected_text_tracks = selected_tracks
        return True
    
    def setup_text_files_simple(self):
        """设置文本文件路径（简化版，不展示内容）"""
        print(f"\n📄 文本文件配置")
        
        # 第一段文本（标题）
        default_content_file = os.path.join(self.text_folder_path, "content.txt")
        
        print(f"第一段文本（标题）:")
        print(f"  默认文件: {default_content_file}")
        
        use_default = True
        if os.path.exists(default_content_file):
            print(f"  ✅ 找到默认文件")
            custom_input = self.get_user_input("是否使用其他文件？(直接回车使用默认文件，或输入新路径)", allow_empty=True)
            if custom_input:
                if os.path.exists(custom_input):
                    self.text_files['content'] = custom_input
                    print(f"  ✅ 使用指定文件: {custom_input}")
                    use_default = False
                else:
                    print(f"  ❌ 指定文件不存在，使用默认文件")
        else:
            print(f"  ⚠️ 默认文件不存在")
            custom_content = self.get_user_input("请输入标题文本文件路径", allow_empty=False)
            if custom_content and os.path.exists(custom_content):
                self.text_files['content'] = custom_content
                print(f"  ✅ 使用指定文件: {custom_content}")
                use_default = False
            else:
                print(f"  ❌ 无法找到文件")
                return False
        
        if use_default:
            self.text_files['content'] = default_content_file
        
        # 第二段文本（水印）- 仅在选择2段时设置
        if self.text_replacement_count == 2:
            default_watermark_file = os.path.join(self.text_folder_path, "watermark.txt")
            
            print(f"\n第二段文本（水印）:")
            print(f"  默认文件: {default_watermark_file}")
            
            use_default_watermark = True
            if os.path.exists(default_watermark_file):
                print(f"  ✅ 找到默认文件")
                custom_input = self.get_user_input("是否使用其他文件？(直接回车使用默认文件，或输入新路径)", allow_empty=True)
                if custom_input:
                    if os.path.exists(custom_input):
                        self.text_files['watermark'] = custom_input
                        print(f"  ✅ 使用指定文件: {custom_input}")
                        use_default_watermark = False
                    else:
                        print(f"  ❌ 指定文件不存在，使用默认文件")
            else:
                print(f"  ⚠️ 默认文件不存在")
                custom_watermark = self.get_user_input("请输入水印文本文件路径", allow_empty=False)
                if custom_watermark and os.path.exists(custom_watermark):
                    self.text_files['watermark'] = custom_watermark
                    print(f"  ✅ 使用指定文件: {custom_watermark}")
                    use_default_watermark = False
                else:
                    print(f"  ❌ 无法找到文件")
                    return False
            
            if use_default_watermark:
                self.text_files['watermark'] = default_watermark_file
        
        return True

    def setup_text_files(self):
        """设置文本文件路径"""
        print(f"\n📄 文本文件配置")
        
        # 第一段文本（标题）
        default_content_file = os.path.join(self.text_folder_path, "content.txt")
        print(f"第一段文本（标题）默认文件: {default_content_file}")
        
        if os.path.exists(default_content_file):
            self.text_files['content'] = default_content_file
            print(f"✅ 找到默认标题文件")
        else:
            print(f"⚠️ 默认标题文件不存在")
            custom_content = self.get_user_input("请输入标题文本文件路径（留空跳过）", allow_empty=True)
            if custom_content and os.path.exists(custom_content):
                self.text_files['content'] = custom_content
                print(f"✅ 使用指定标题文件: {custom_content}")
            else:
                print(f"❌ 无法找到标题文本文件")
                return False
        
        # 第二段文本（水印）- 仅在选择2段时设置
        if self.text_replacement_count == 2:
            default_watermark_file = os.path.join(self.text_folder_path, "watermark.txt")
            print(f"第二段文本（水印）默认文件: {default_watermark_file}")
            
            if os.path.exists(default_watermark_file):
                self.text_files['watermark'] = default_watermark_file
                print(f"✅ 找到默认水印文件")
            else:
                print(f"⚠️ 默认水印文件不存在")
                custom_watermark = self.get_user_input("请输入水印文本文件路径（留空跳过）", allow_empty=True)
                if custom_watermark and os.path.exists(custom_watermark):
                    self.text_files['watermark'] = custom_watermark
                    print(f"✅ 使用指定水印文件: {custom_watermark}")
                else:
                    print(f"❌ 无法找到水印文本文件")
                    return False
        
        return True
    
    def load_text_contents(self):
        """读取和解析文本内容"""
        print(f"\n📖 读取文本内容")
        
        for text_type, file_path in self.text_files.items():
            try:
                print(f"📄 读取{text_type}文件: {file_path}")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 解析文本内容（支持#分割和空行分割）
                texts = self.parse_text_content(content)
                
                if texts:
                    self.text_contents[text_type] = texts
                    print(f"✅ 解析到 {len(texts)} 条{text_type}文本")
                    
                    # 显示前3条内容作为预览
                    for i, text in enumerate(texts[:3]):
                        preview = text[:50] + "..." if len(text) > 50 else text
                        print(f"  {i+1}. {preview}")
                    
                    if len(texts) > 3:
                        print(f"  ... 还有 {len(texts)-3} 条")
                else:
                    print(f"❌ {text_type}文件为空或格式不正确")
                    return False
                    
            except Exception as e:
                print(f"❌ 读取{text_type}文件失败: {e}")
                return False
        
        return True
    
    def parse_text_content(self, content):
        """解析文本内容，支持#分割和空行分割"""
        if not content.strip():
            return []
        
        # 首先尝试按 # 分割（支持#前后可能有空格或换行）
        if '#' in content:
            # 使用正则表达式处理#分割，支持#前后的空白字符
            import re
            texts = re.split(r'\s*#\s*', content)
            texts = [text.strip() for text in texts if text.strip()]
            if texts:
                print(f"    🔍 使用#分割模式，解析到 {len(texts)} 条文本")
                return texts
        
        # 然后尝试按空行分割（两个或多个连续换行符，中间可能有空格）
        import re
        texts = re.split(r'\n\s*\n', content)
        texts = [text.strip() for text in texts if text.strip()]
        
        if len(texts) > 1:
            print(f"    🔍 使用空行分割模式，解析到 {len(texts)} 条文本")
            return texts
        
        # 如果都没有分割符，返回整个内容作为单条文本
        texts = [content.strip()]
        print(f"    🔍 使用单条文本模式，解析到 {len(texts)} 条文本")
        return texts
    
    def process_text_replacement(self):
        """处理文本替换，按原始组合顺序进行，确保文字替换顺序不受失败影响"""
        try:
            self.print_section("执行文本替换")
            
            # 检查是否有组合映射表
            if not hasattr(self, 'draft_combination_mapping') or not self.draft_combination_mapping:
                print("❌ 没有找到组合映射表，无法进行文本替换")
                return False
            
            # 检查是否已选择文本轨道
            if not hasattr(self, 'selected_text_tracks') or not self.selected_text_tracks:
                print("❌ 没有选择要替换的文本轨道")
                return False
            
            replacement_count = 0
            skipped_count = 0
            total_combinations = len(self.draft_combination_mapping)
            
            print(f"📊 将按组合顺序进行文本替换，共 {total_combinations} 个组合")
            
            # 按原始组合顺序进行文本替换
            for mapping_info in self.draft_combination_mapping:
                combination_index = mapping_info['combination_index']
                combo_name = mapping_info['combo_name']
                actual_draft_name = mapping_info['actual_draft_name']
                is_success = mapping_info['success']
                
                print(f"\n🔄 处理组合 {combination_index}/{total_combinations}: {combo_name}")
                
                if not is_success or not actual_draft_name:
                    print(f"   ⏭️ 草稿创建失败，跳过文本替换，保持顺序")
                    skipped_count += 1
                    continue
                
                print(f"   🎯 草稿名称: {actual_draft_name}")
                
                # 提取草稿中的文本轨道
                text_tracks = self.extract_text_tracks_from_draft(actual_draft_name)
                if not text_tracks:
                    print(f"   ⚠️ 草稿中没有找到文本轨道，跳过")
                    skipped_count += 1
                    continue
                
                # 执行文本替换（使用配置阶段选择的轨道）
                if self.replace_text_in_draft(actual_draft_name, text_tracks):
                    replacement_count += 1
                    print(f"   ✅ 文本替换完成")
                else:
                    print(f"   ❌ 文本替换失败")
                    skipped_count += 1
            
            print(f"\n🎉 文本替换处理完成！")
            print(f"   ✅ 成功替换: {replacement_count} 个草稿")
            print(f"   ⏭️ 跳过处理: {skipped_count} 个组合")
            print(f"   📊 总计组合: {total_combinations} 个")
            print(f"   🔢 文字替换顺序: 严格按照组合顺序 1-{total_combinations}")
            
            return replacement_count > 0
            
        except Exception as e:
            print(f"❌ 文本替换过程出错: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return False
    
    def extract_text_tracks_from_draft(self, draft_name):
        """从草稿中提取文本轨道信息 (兼容多版本格式)"""
        try:
            # 使用兼容性方法获取草稿文件路径
            draft_file_path = self.get_compatible_draft_file_path(draft_name)
            
            if not draft_file_path:
                self.print_error(f"草稿文件不存在，已检查 draft_info.json 和 draft_content.json")
                return []
            
            if self.debug:
                self.print_success(f"找到草稿文件: {os.path.basename(draft_file_path)}")
            
            with open(draft_file_path, 'r', encoding='utf-8') as f:
                draft_data = json.load(f)
            
            # 获取素材信息
            materials = draft_data.get('materials', {})
            tracks = draft_data.get('tracks', [])
            
            text_tracks = []
            text_track_index = 0
            
            for track_index, track in enumerate(tracks):
                if not track or track.get('type') != 'text':
                    continue
                
                track_info = {
                    'track_index': track_index,
                    'text_track_index': text_track_index,
                    'track_id': track.get('id', ''),
                    'track_name': track.get('name', f'文本轨道 {text_track_index + 1}'),
                    'segments': [],
                    'track_attribute': track.get('attribute', 0),
                    'track_flag': track.get('flag', 0)
                }
                
                # 遍历轨道中的片段
                segments = track.get('segments', [])
                
                for segment_index, segment in enumerate(segments):
                    if not segment:
                        continue
                    
                    text_info = self.extract_text_from_segment(segment, materials)
                    if text_info:
                        text_info['segment_index'] = segment_index
                        text_info['track_index'] = track_index
                        text_info['text_track_index'] = text_track_index
                        track_info['segments'].append(text_info)
                
                text_tracks.append(track_info)
                text_track_index += 1
            
            return text_tracks
            
        except Exception as e:
            print(f"❌ 提取文本轨道失败: {e}")
            return []
    
    def extract_text_from_segment(self, segment, materials):
        """从片段数据中提取文本信息（基于extract_text_from_draft_info.py）"""
        if not segment or not materials:
            return None
        
        # 获取素材ID
        material_id = segment.get("material_id")
        if not material_id:
            return None
        
        # 在texts材料中查找对应的文本
        texts = materials.get("texts", [])
        if not texts:
            return None
        
        for text_material in texts:
            if not text_material:
                continue
            if text_material.get("id") == material_id:
                # 提取文本内容
                text_content = ""
                content_data = text_material.get("content", "")
                if content_data:
                    try:
                        if isinstance(content_data, str):
                            content_json = json.loads(content_data)
                        else:
                            content_json = content_data
                        text_content = content_json.get("text", "")
                    except:
                        text_content = str(content_data)
                
                if not text_content:
                    text_content = text_material.get("base_content", "")
                
                # 提取文本信息
                text_info = {
                    'material_id': material_id,
                    'text': text_content,
                    'segment_id': segment.get("id", ""),
                    'start_time': (segment.get("target_timerange") or {}).get("start", 0),
                    'duration': (segment.get("target_timerange") or {}).get("duration", 0),
                    'visible': segment.get("visible", True),
                }
                
                return text_info
        
        return None
    
    def select_text_tracks_to_replace(self, text_tracks):
        """选择要替换的文本轨道"""
        if not text_tracks:
            print("❌ 没有找到文本轨道")
            return False
        
        print(f"\n📋 找到 {len(text_tracks)} 个文本轨道:")
        
        # 显示所有文本轨道及其内容
        for i, track in enumerate(text_tracks):
            print(f"\n  {i+1}. 【{track['track_name']}】({len(track['segments'])}个片段)")
            
            for j, segment in enumerate(track['segments']):
                preview = segment['text'][:30] + "..." if len(segment['text']) > 30 else segment['text']
                start_time_str = f"{segment['start_time']/1000000:.1f}s"
                duration_str = f"{segment['duration']/1000000:.1f}s"
                print(f"     片段{j+1}: \"{preview}\" (时间:{start_time_str}, 时长:{duration_str})")
        
        # 选择要替换的轨道
        selected_tracks = []
        
        for text_type in (['content'] if self.text_replacement_count == 1 else ['content', 'watermark']):
            type_name = "标题" if text_type == 'content' else "水印"
            
            print(f"\n🎯 选择要替换的{type_name}轨道:")
            track_options = [f"轨道{i+1}: {track['track_name']}" for i, track in enumerate(text_tracks)]
            track_options.append("跳过此类型")
            
            track_idx, track_str = self.get_user_choice(track_options, f"选择{type_name}轨道")
            
            if track_idx < len(text_tracks):
                selected_track = text_tracks[track_idx]
                selected_tracks.append({
                    'type': text_type,
                    'track_index': track_idx,  # 在文本轨道数组中的索引
                    'original_track_index': selected_track['track_index'],  # 在所有轨道中的真实索引
                    'track_info': selected_track
                })
                print(f"✅ 选择{type_name}轨道: {track_str}")
            else:
                print(f"⏭️ 跳过{type_name}替换")
        
        if not selected_tracks:
            print("❌ 没有选择任何要替换的轨道")
            return False
        
        self.selected_text_tracks = selected_tracks
        return True
    
    def replace_text_in_draft(self, draft_name, text_tracks):
        """在草稿中执行文本替换 (兼容多版本格式)"""
        try:
            # 使用兼容性方法获取草稿文件路径
            draft_file_path = self.get_compatible_draft_file_path(draft_name)
            
            if not draft_file_path:
                self.print_error(f"草稿文件不存在，已检查 draft_info.json 和 draft_content.json")
                return False
            
            # 读取草稿文件
            with open(draft_file_path, 'r', encoding='utf-8') as f:
                draft_data = json.load(f)
            
            # 备份原文件
            backup_path = draft_file_path + ".text_backup"
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(draft_data, f, ensure_ascii=False, indent=2)
            
            replacement_success = False
            
            # 对每个选择的文本类型进行替换
            for selected_track in self.selected_text_tracks:
                text_type = selected_track['type']
                track_index = selected_track['track_index']
                source_track_info = selected_track['track_info']
                
                if text_type not in self.text_contents:
                    print(f"⚠️ 没有{text_type}文本内容，跳过")
                    continue
                
                # 获取要替换的新文本
                new_text = self.get_next_text_content(text_type, draft_name)
                if not new_text:
                    print(f"⚠️ 无法获取{text_type}的新文本内容")
                    continue
                
                # 在当前草稿的文本轨道中找到对应的轨道
                # 首先尝试按原始轨道索引匹配
                target_track = None
                original_track_index = selected_track.get('original_track_index', -1)
                match_method = ""
                
                # 方法1: 按原始轨道索引匹配（最准确）
                for track in text_tracks:
                    if track.get('track_index') == original_track_index:
                        target_track = track
                        match_method = f"原始轨道索引({original_track_index})"
                        break
                
                # 方法2: 如果方法1失败，按轨道名称匹配
                if not target_track:
                    for track in text_tracks:
                        if track['track_name'] == source_track_info['track_name']:
                            target_track = track
                            match_method = f"轨道名称({source_track_info['track_name']})"
                            break
                
                # 方法3: 如果都失败，按在文本轨道数组中的位置匹配（兜底）
                if not target_track and track_index < len(text_tracks):
                    target_track = text_tracks[track_index]
                    match_method = f"文本轨道位置({track_index})"
                
                if not target_track:
                    print(f"  ⚠️ 无法在当前草稿中找到匹配的{text_type}轨道")
                    continue
                
                print(f"  🎯 匹配{text_type}轨道: {match_method}")
                
                # 在draft_data中替换文本
                if self.update_text_in_draft_data(draft_data, target_track, new_text):
                    print(f"  ✅ {text_type}文本替换成功: \"{new_text[:30]}...\"")
                    replacement_success = True
                else:
                    print(f"  ❌ {text_type}文本替换失败")
            
            if replacement_success:
                # 保存修改后的草稿文件
                with open(draft_file_path, 'w', encoding='utf-8') as f:
                    json.dump(draft_data, f, ensure_ascii=False, indent=2)
                
                return True
            else:
                print("❌ 所有文本替换都失败了")
                return False
                
        except Exception as e:
            print(f"❌ 替换文本时出错: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return False
    
    def get_next_text_content(self, text_type, draft_name):
        """获取下一个要使用的文本内容"""
        if text_type not in self.text_contents:
            return None
        
        texts = self.text_contents[text_type]
        if not texts:
            return None
        
        # 根据选择模式决定使用哪个文本
        if self.text_selection_mode == "sequential":
            # 按顺序循环：使用草稿索引来确定使用哪个文本
            if not hasattr(self, 'draft_text_indices'):
                self.draft_text_indices = {}
            
            if text_type not in self.draft_text_indices:
                self.draft_text_indices[text_type] = 0
            
            index = self.draft_text_indices[text_type] % len(texts)
            self.draft_text_indices[text_type] += 1
            
            return texts[index]
        else:
            # 随机选择
            import random
            return random.choice(texts)
    
    def update_text_in_draft_data(self, draft_data, track_info, new_text):
        """在草稿数据中更新文本内容"""
        try:
            materials = draft_data.get('materials', {})
            texts = materials.get('texts', [])
            
            # 更新所有该轨道的文本片段
            for segment in track_info['segments']:
                material_id = segment['material_id']
                
                # 在materials中找到对应的文本材料并更新
                for text_material in texts:
                    if text_material and text_material.get('id') == material_id:
                        # 更新文本内容
                        content_data = text_material.get('content', '{}')
                        try:
                            if isinstance(content_data, str):
                                content_json = json.loads(content_data)
                            else:
                                content_json = content_data
                            
                            content_json['text'] = new_text
                            text_material['content'] = json.dumps(content_json, ensure_ascii=False)
                        except:
                            # 如果解析失败，直接设置content
                            text_material['content'] = json.dumps({'text': new_text}, ensure_ascii=False)
                        
                        # 同时更新base_content
                        text_material['base_content'] = new_text
                        break
            
            return True
            
        except Exception as e:
            print(f"❌ 更新文本数据时出错: {e}")
            return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='批量草稿复制与素材替换工具')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--fix-draft', type=str, help='修复指定草稿名称的路径占位符问题')
    parser.add_argument('--test-cover', action='store_true', help='测试封面图生成功能')
    args = parser.parse_args()
    
    processor = BatchDraftProcessor(debug=args.debug)
    
    # 如果指定了测试封面图
    if args.test_cover:
        print(f"🧪 测试模式：测试封面图生成功能")
        success = processor.test_jianying_cover_generation()
        if success:
            print("✅ 测试完成！")
        else:
            print("❌ 测试失败！")
        return
    
    # 如果指定了修复草稿
    if args.fix_draft:
        print(f"🔧 修复模式：修复草稿 '{args.fix_draft}'")
        success = processor.fix_existing_draft_placeholders(args.fix_draft)
        if success:
            print("✅ 修复完成！")
        else:
            print("❌ 修复失败！")
        return
    
    # 正常运行
    processor.run()


if __name__ == "__main__":
    main()