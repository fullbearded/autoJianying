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


class BatchDraftProcessor:
    """批量草稿处理器"""
    
    def __init__(self, debug=False):
        self.debug = debug  # 调试模式
        self.draft_folder_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
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
        
    def print_header(self, title):
        """打印标题"""
        print("\n" + "=" * 70)
        print(f"🎬 {title}")
        print("=" * 70)
    
    def print_section(self, title):
        """打印章节标题"""
        print(f"\n📋 {title}")
        print("-" * 50)
    
    def print_success(self, message):
        """打印成功信息"""
        print(f"✅ {message}")
    
    def print_warning(self, message):
        """打印警告信息"""
        print(f"⚠️  {message}")
    
    def print_error(self, message):
        """打印错误信息"""
        print(f"❌ {message}")
    
    def get_user_input(self, prompt, allow_empty=False):
        """获取用户输入"""
        while True:
            try:
                user_input = input(f"{prompt}: ").strip()
                if user_input or allow_empty:
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
        if not os.path.exists(self.draft_folder_path):
            self.print_error("草稿文件夹不存在!")
            new_path = self.get_user_input("请输入正确的草稿文件夹路径")
            if os.path.exists(new_path):
                self.draft_folder_path = new_path
                self.print_success("草稿文件夹路径已更新")
            else:
                self.print_error("路径仍然无效，请检查后重试")
                return False
        
        try:
            self.draft_folder = draft.DraftFolder(self.draft_folder_path)
            return True
        except Exception as e:
            self.print_error(f"初始化草稿文件夹失败: {e}")
            return False
    
    def load_draft_info_from_file(self, draft_name):
        """从 draft_info.json 文件加载草稿信息"""
        draft_info_path = os.path.join(self.draft_folder_path, draft_name, "draft_info.json")
        
        if not os.path.exists(draft_info_path):
            return None
        
        try:
            with open(draft_info_path, 'r', encoding='utf-8') as f:
                draft_info = json.load(f)
            
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
            # 过滤掉系统文件和demo草稿
            filtered_drafts = [d for d in draft_list if not d.startswith('.') and not d.startswith('pyJianYingDraft_Demo')]
            
            if not filtered_drafts:
                self.print_error("没有找到可用的草稿")
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
            return False
    
    def setup_materials_folder(self):
        """设置素材文件夹"""
        self.print_section("设置素材文件夹")
        
        # 尝试自动检测materials文件夹
        possible_paths = [
            os.path.join(project_root, "examples", "materials"),
            os.path.join(project_root, "materials"),
            os.path.join(os.path.dirname(__file__), "materials")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.materials_folder_path = path
                print(f"✅ 自动检测到素材文件夹: {path}")
                break
        
        if not self.materials_folder_path:
            custom_path = self.get_user_input("请输入素材文件夹路径", allow_empty=True)
            if custom_path and os.path.exists(custom_path):
                self.materials_folder_path = custom_path
            else:
                self.print_error("必须设置有效的素材文件夹路径")
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
        """格式化组合显示"""
        parts = []
        # 动态获取所有part文件夹，按数字排序
        sorted_folders = sorted([k for k in combination.keys() if k.startswith('part')], 
                               key=lambda x: int(x[4:]) if x[4:].isdigit() else 999)
        
        # 添加background文件夹（如果存在）
        if 'background' in combination:
            sorted_folders.append('background')
        
        # 添加audios文件夹（如果存在）
        if 'audios' in combination:
            sorted_folders.append('audios')
        
        # 添加bg_musics文件夹（如果存在）
        if 'bg_musics' in combination:
            sorted_folders.append('bg_musics')
        
        for folder in sorted_folders:
            if folder in combination:
                parts.append(combination[folder])
        return " + ".join(parts)
    
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
        
        # 批量处理
        for i, combination in enumerate(self.material_combinations, 1):
            print(f"\n🔄 处理组合 {i}/{total_combinations}: {combination}")
            
            # 生成新草稿名称（使用汉字组合）
            combo_name = self.generate_chinese_combo_name(combination)
            base_target_name = f"{self.selected_draft}_{combo_name}"
            
            # 检查名称是否重复，如果重复则添加序号
            target_name = base_target_name
            counter = 1
            while target_name in used_names:
                target_name = f"{base_target_name}_{counter}"
                counter += 1
            used_names.add(target_name)
            
            try:
                # 复制草稿
                print(f"  📋 复制草稿: {target_name}")
                success = self.copy_single_draft(target_name)
                
                if success:
                    # 替换素材
                    print(f"  🔄 替换素材...")
                    replacement_success = self.replace_materials_for_draft(target_name, combination)
                    
                    if replacement_success:
                        successful_drafts.append(target_name)
                        print(f"  ✅ 组合 {i} 处理成功")
                    else:
                        failed_drafts.append((target_name, "素材替换失败"))
                        print(f"  ❌ 组合 {i} 素材替换失败")
                else:
                    failed_drafts.append((target_name, "草稿复制失败"))
                    print(f"  ❌ 组合 {i} 草稿复制失败")
                
            except Exception as e:
                failed_drafts.append((target_name, str(e)))
                print(f"  ❌ 组合 {i} 处理出错: {e}")
        
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
        """直接操作 draft_info.json 进行素材替换"""
        try:
            draft_info_path = os.path.join(self.draft_folder_path, draft_name, "draft_info.json")
            
            if not os.path.exists(draft_info_path):
                print(f"    ❌ draft_info.json 不存在: {draft_info_path}")
                return False
            
            # 读取当前的 draft_info.json
            with open(draft_info_path, 'r', encoding='utf-8') as f:
                draft_info = json.load(f)
            
            # 备份原文件
            backup_path = draft_info_path + ".backup"
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
                # 保存更新后的 draft_info.json
                with open(draft_info_path, 'w', encoding='utf-8') as f:
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
            
            self.print_header("处理完成")
            print("🎉 所有草稿已成功创建，可以在剪映中打开查看")
            
        except KeyboardInterrupt:
            print("\n\n👋 用户取消操作，再见!")
        except Exception as e:
            self.print_error(f"程序运行出错: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='批量草稿复制与素材替换工具')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--fix-draft', type=str, help='修复指定草稿名称的路径占位符问题')
    args = parser.parse_args()
    
    processor = BatchDraftProcessor(debug=args.debug)
    
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