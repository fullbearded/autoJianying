#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频预处理脚本 - 基于指定目录自动替换草稿素材
支持遍历指定目录，替换草稿中的素材文件并生成新草稿
"""

import os
import sys
import glob
import json
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pyJianYingDraft as draft
import platform


class VideoPreprocessCli:
    """视频预处理CLI工具"""
    
    def __init__(self):
        # 根据操作系统设置默认草稿文件夹路径
        if platform.system() == "Windows":
            self.draft_folder_path = os.path.expanduser("~/AppData/Local/JianyingPro/User Data/Projects/com.lveditor.draft")
        elif platform.system() == "Darwin":  # macOS
            self.draft_folder_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
        else:
            # Linux 或其他系统
            self.draft_folder_path = os.path.expanduser("~/JianyingPro/User Data/Projects/com.lveditor.draft")
        
        self.draft_folder = None
        self.template_draft = None
        self.source_directory = None
        self.supported_video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm']
        self.supported_image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
        self.supported_audio_extensions = ['.mp3', '.wav', '.aac', '.m4a', '.flac']
        
        # 时间线处理模式配置
        self.timeline_mode = None  # "speed_adjust", "crop_end", "crop_start", "crop_random", "keep_original"
    
    def print_header(self, title):
        """打印标题"""
        print(f"\n{'='*50}")
        print(f"  {title}")
        print(f"{'='*50}")
    
    def print_section(self, title):
        """打印章节"""
        print(f"\n{'-'*30}")
        print(f"  {title}")
        print(f"{'-'*30}")
    
    def print_success(self, message):
        """成功消息"""
        print(f"✅ {message}")
    
    def print_error(self, message):
        """错误消息"""
        print(f"❌ {message}")
    
    def print_warning(self, message):
        """警告消息"""
        print(f"⚠️  {message}")
    
    def get_user_input(self, prompt, allow_empty=False):
        """获取用户输入"""
        while True:
            try:
                user_input = input(f"{prompt}: ").strip()
                if user_input or allow_empty:
                    return user_input
                print("输入不能为空，请重新输入")
            except KeyboardInterrupt:
                print("\n用户取消操作")
                sys.exit(0)
    
    def get_user_choice(self, options, prompt):
        """获取用户选择"""
        while True:
            print(f"\n{prompt}:")
            for i, option in enumerate(options):
                print(f"  {i + 1}. {option}")
            print(f"  0. 退出")
            
            try:
                choice = int(self.get_user_input("请选择"))
                if choice == 0:
                    print("❌ 用户选择退出")
                    sys.exit(0)
                elif 1 <= choice <= len(options):
                    return choice - 1, options[choice - 1]
                else:
                    print("无效的选择，请重新输入")
            except ValueError:
                print("请输入有效的数字")
    
    def initialize_draft_folder(self):
        """初始化草稿文件夹"""
        self.print_section("初始化草稿文件夹")
        
        # 检查默认路径是否存在
        if os.path.exists(self.draft_folder_path):
            print(f"📁 使用默认草稿路径: {self.draft_folder_path}")
        else:
            # 让用户输入自定义路径
            self.print_warning("默认草稿路径不存在")
            custom_path = self.get_user_input("请输入草稿文件夹路径")
            if not os.path.exists(custom_path):
                self.print_error("指定路径不存在")
                return False
            self.draft_folder_path = custom_path
        
        try:
            self.draft_folder = draft.DraftFolder(self.draft_folder_path)
            self.print_success(f"草稿文件夹初始化成功")
            return True
        except Exception as e:
            self.print_error(f"草稿文件夹初始化失败: {e}")
            return False
    
    def select_template_draft(self):
        """选择模板草稿"""
        self.print_section("选择模板草稿")
        
        try:
            draft_list = self.draft_folder.list_drafts()
            # 过滤掉系统文件和demo草稿
            filtered_drafts = [d for d in draft_list if not d.startswith('.') and not d.startswith('pyJianYingDraft_Demo')]
            
            if not filtered_drafts:
                self.print_error("没有找到可用的草稿")
                return False
            
            print(f"📊 找到 {len(filtered_drafts)} 个可用草稿:")
            # 验证草稿结构并显示状态
            valid_drafts = []
            for i, draft_name in enumerate(filtered_drafts, 1):
                is_valid = self.validate_draft_structure(draft_name)
                status = "✅" if is_valid else "❌"
                print(f"  {i}. {draft_name} {status}")
                if is_valid:
                    valid_drafts.append((i-1, draft_name))
            
            if not valid_drafts:
                self.print_error("没有找到有效的草稿模板")
                self.print_warning("请确保草稿包含必要的文件结构")
                return False
            
            # 获取用户选择
            while True:
                try:
                    choice = int(self.get_user_input("请选择模板草稿编号")) - 1
                    if 0 <= choice < len(filtered_drafts):
                        # 检查选中的草稿是否有效
                        if any(idx == choice for idx, _ in valid_drafts):
                            self.template_draft = filtered_drafts[choice]
                            self.print_success(f"已选择模板草稿: {self.template_draft}")
                            return True
                        else:
                            print("❌ 选择的草稿结构无效，请选择有效的草稿")
                    else:
                        print("无效的编号，请重新输入")
                except ValueError:
                    print("请输入有效的数字")
                    
        except Exception as e:
            self.print_error(f"获取草稿列表失败: {e}")
            return False
    
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
            print(f"读取草稿文件失败: {e}")
            return None
    
    def validate_draft_structure(self, draft_name):
        """验证草稿结构是否有效"""
        try:
            draft_path = os.path.join(self.draft_folder_path, draft_name)
            if not os.path.exists(draft_path):
                return False
            
            # 检查是否有兼容的草稿文件
            draft_file_path = self.get_compatible_draft_file_path(draft_name)
            if not draft_file_path:
                return False
            
            # 尝试加载草稿信息
            draft_info = self.load_draft_info_from_file(draft_name)
            if not draft_info:
                return False
            
            # 检查是否有视频素材
            if not draft_info.get('video_materials'):
                return False
            
            return True
        except Exception:
            return False
    
    def select_source_directory(self):
        """选择源目录"""
        self.print_section("选择源素材目录")
        
        # 提供一些默认选项
        default_dirs = [
            "./examples/materials",
            "./readme_assets/tutorial",
            "自定义路径"
        ]
        
        print("可选的素材目录:")
        for i, dir_path in enumerate(default_dirs, 1):
            exists = "✅" if dir_path == "自定义路径" or os.path.exists(dir_path) else "❌"
            print(f"  {i}. {dir_path} {exists}")
        
        # 获取用户选择
        while True:
            try:
                choice = int(self.get_user_input("请选择素材目录编号")) - 1
                if choice == len(default_dirs) - 1:  # 自定义路径
                    custom_path = self.get_user_input("请输入自定义素材目录路径")
                    if os.path.exists(custom_path):
                        self.source_directory = custom_path
                        break
                    else:
                        print("指定路径不存在，请重新选择")
                elif 0 <= choice < len(default_dirs) - 1:
                    if os.path.exists(default_dirs[choice]):
                        self.source_directory = default_dirs[choice]
                        break
                    else:
                        print("所选路径不存在，请重新选择")
                else:
                    print("无效的编号，请重新输入")
            except ValueError:
                print("请输入有效的数字")
        
        self.print_success(f"已选择素材目录: {self.source_directory}")
        return True
    
    def select_timeline_mode(self):
        """选择时间线处理模式"""
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
    
    def scan_directory_files(self):
        """扫描目录下的文件"""
        self.print_section("扫描目录文件")
        
        video_files = []
        image_files = []
        audio_files = []
        
        try:
            # 递归扫描目录
            for root, dirs, files in os.walk(self.source_directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_ext = os.path.splitext(file)[1].lower()
                    
                    if file_ext in self.supported_video_extensions:
                        video_files.append(file_path)
                    elif file_ext in self.supported_image_extensions:
                        image_files.append(file_path)
                    elif file_ext in self.supported_audio_extensions:
                        audio_files.append(file_path)
            
            # 显示扫描结果
            print(f"🎬 视频文件: {len(video_files)} 个")
            for video in video_files[:5]:  # 只显示前5个
                print(f"  - {os.path.basename(video)}")
            if len(video_files) > 5:
                print(f"  ... 还有 {len(video_files) - 5} 个")
            
            print(f"🖼️ 图片文件: {len(image_files)} 个")
            for image in image_files[:5]:  # 只显示前5个
                print(f"  - {os.path.basename(image)}")
            if len(image_files) > 5:
                print(f"  ... 还有 {len(image_files) - 5} 个")
            
            print(f"🎵 音频文件: {len(audio_files)} 个")
            for audio in audio_files[:5]:  # 只显示前5个
                print(f"  - {os.path.basename(audio)}")
            if len(audio_files) > 5:
                print(f"  ... 还有 {len(audio_files) - 5} 个")
            
            return {
                'video': video_files,
                'image': image_files,
                'audio': audio_files
            }
            
        except Exception as e:
            self.print_error(f"扫描目录失败: {e}")
            return None
    
    def create_drafts_from_materials(self, materials):
        """基于素材创建草稿"""
        self.print_section("创建新草稿")
        
        if not any(materials.values()):
            self.print_warning("没有找到可用的素材文件")
            return False
        
        # 决定创建草稿的策略
        video_files = materials.get('video', [])
        
        if not video_files:
            self.print_warning("没有找到视频文件，无法创建草稿")
            return False
        
        success_count = 0
        total_count = len(video_files)
        
        print(f"📊 将基于 {total_count} 个视频文件创建草稿")
        
        # 确认是否继续
        confirm = self.get_user_input(f"确认创建 {total_count} 个草稿? (y/n)", allow_empty=True)
        if confirm.lower() not in ['y', 'yes', '']:
            print("❌ 用户取消操作")
            return False
        
        # 为每个视频文件创建一个草稿
        for i, video_file in enumerate(video_files, 1):
            print(f"\n🔄 处理视频 {i}/{total_count}: {os.path.basename(video_file)}")
            
            try:
                # 生成草稿名称
                video_basename = os.path.splitext(os.path.basename(video_file))[0]
                new_draft_name = f"{self.template_draft}_processed_{video_basename}"
                
                # 复制模板草稿
                success = self.copy_and_replace_draft(new_draft_name, video_file, materials)
                
                if success:
                    self.print_success(f"成功创建草稿: {new_draft_name}")
                    success_count += 1
                else:
                    self.print_error(f"创建草稿失败: {new_draft_name}")
                    
            except Exception as e:
                self.print_error(f"处理视频文件时出错: {e}")
        
        print(f"\n📊 处理完成: 成功 {success_count}/{total_count}")
        return success_count > 0
    
    def copy_single_draft(self, target_name):
        """复制单个草稿"""
        try:
            # 直接复制文件夹，避免 duplicate_as_template 的版本兼容性问题
            source_path = os.path.join(self.draft_folder_path, self.template_draft)
            target_path = os.path.join(self.draft_folder_path, target_name)
            
            # 如果目标已存在，先删除
            if os.path.exists(target_path):
                shutil.rmtree(target_path)
            
            # 复制整个草稿文件夹
            shutil.copytree(source_path, target_path)
            print(f"    📁 成功复制文件夹: {source_path} -> {target_path}")
            return True
        except Exception as e:
            print(f"    ❌ 复制草稿失败: {e}")
            return False
    
    def copy_and_replace_draft(self, new_draft_name, primary_video_file, all_materials):
        """复制草稿并替换素材"""
        print(f"    🔍 开始复制模板草稿: {self.template_draft}")
        
        try:
            # 检查新草稿名称是否已存在
            new_draft_path = os.path.join(self.draft_folder_path, new_draft_name)
            if os.path.exists(new_draft_path):
                print(f"    🗑️ 删除已存在的草稿: {new_draft_name}")
                shutil.rmtree(new_draft_path)
            
            # 复制草稿
            success = self.copy_single_draft(new_draft_name)
            if not success:
                return False
            
            print(f"    ✅ 成功创建草稿副本")
            
            # 验证复制后的文件结构
            draft_file_path = self.get_compatible_draft_file_path(new_draft_name)
            if not draft_file_path:
                print(f"    ❌ 复制后的草稿缺少必要文件")
                return False
            
            # 使用直接JSON替换方法
            print(f"    🎬 准备替换视频素材: {os.path.basename(primary_video_file)}")
            
            # 准备替换信息
            template_info = self.load_draft_info_from_file(self.template_draft)
            if not template_info or not template_info['video_materials']:
                print(f"    ❌ 模板草稿没有视频素材可替换")
                return False
            
            # 查找名为 "video.mp4" 的特定视频素材进行替换
            target_video = None
            for video in template_info['video_materials']:
                if video['name'] == 'video.mp4':
                    target_video = video
                    break
            
            if not target_video:
                print(f"    ❌ 模板草稿中未找到名为 'video.mp4' 的视频素材")
                print(f"    📋 可用的视频素材:")
                for video in template_info['video_materials']:
                    print(f"      - {video['name']} (id: {video['id']})")
                return False
            
            replacement = {
                'type': 'video',
                'original_name': target_video['name'],
                'original_id': target_video['id'],
                'new_file': primary_video_file,
                'new_name': os.path.basename(primary_video_file),
                'target_name': 'video.mp4'  # 特定目标名称
            }
            
            # 执行替换
            success = self.attempt_direct_json_replacement(new_draft_name, [replacement])
            
            if success:
                print(f"    ✅ 草稿处理完成")
                return True
            else:
                print(f"    ❌ 素材替换失败")
                return False
                
        except Exception as e:
            print(f"    ❌ 复制和替换草稿时出错: {e}")
            print(f"    🔍 错误类型: {type(e).__name__}")
            return False
    
    def attempt_direct_json_replacement(self, draft_name, replacements):
        """直接操作草稿文件进行素材替换 (兼容多版本格式)"""
        try:
            # 使用兼容性方法获取草稿文件路径
            draft_file_path = self.get_compatible_draft_file_path(draft_name)
            
            if not draft_file_path:
                print(f"    ❌ 草稿文件不存在，已检查 draft_info.json 和 draft_content.json")
                return False
            
            # 读取当前的草稿文件
            with open(draft_file_path, 'r', encoding='utf-8') as f:
                draft_info = json.load(f)
            
            # 备份原文件
            backup_path = draft_file_path + ".backup"
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(draft_info, f, ensure_ascii=False, indent=2)
            
            success_count = 0
            
            # 处理视频素材替换
            for replacement in replacements:
                if replacement['type'] == 'video':
                    if self.replace_video_material(draft_info, replacement, draft_name):
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
                
                # 使用更精确的匹配逻辑：只替换名为 "video.mp4" 的视频素材
                target_name = replacement.get('target_name', replacement['original_name'])
                
                for video in videos:
                    # 精确匹配：只替换指定名称的视频素材
                    video_name = video.get('material_name', '')
                    video_id = video.get('id', '')
                    
                    # 匹配条件：material_name 必须完全匹配目标名称
                    if video_name == target_name:
                        print(f"    🎯 找到目标视频素材: {video_name} (id: {video_id})")
                        
                        # 复制新文件到草稿materials目录，但保持原文件名以维持引用关系
                        original_filename = video_name  # 保持原始文件名
                        target_path = os.path.join(materials_dir, original_filename)
                        
                        # 备份原文件
                        if os.path.exists(target_path):
                            backup_path = target_path + ".backup"
                            shutil.copy2(target_path, backup_path)
                            print(f"    💾 备份原文件: {target_path} -> {backup_path}")
                        
                        # 复制新文件，但使用原文件名
                        shutil.copy2(replacement['new_file'], target_path)
                        print(f"    📁 复制文件: {replacement['new_file']} -> {target_path}")
                        
                        # 获取新视频文件的信息
                        try:
                            import pymediainfo
                            media_info = pymediainfo.MediaInfo.parse(replacement['new_file'])
                            video_track = None
                            for track in media_info.tracks:
                                if track.track_type == 'Video':
                                    video_track = track
                                    break
                            
                            if video_track:
                                new_duration = int(video_track.duration * 1000) if video_track.duration else video.get('duration', 0)
                                new_width = video_track.width or video.get('width', 1920)
                                new_height = video_track.height or video.get('height', 1080)
                                fps = video_track.frame_rate or 30.0
                            else:
                                new_duration = video.get('duration', 0)
                                new_width = video.get('width', 1920)
                                new_height = video.get('height', 1080)
                                fps = 30.0
                                
                        except ImportError:
                            print(f"    ⚠️ pymediainfo 不可用，使用默认值")
                            new_duration = video.get('duration', 0)
                            new_width = video.get('width', 1920)
                            new_height = video.get('height', 1080)
                            fps = 30.0
                        except Exception as e:
                            print(f"    ⚠️ 获取视频信息失败，使用默认值: {e}")
                            new_duration = video.get('duration', 0)
                            new_width = video.get('width', 1920)
                            new_height = video.get('height', 1080)
                            fps = 30.0
                        
                        # 获取原素材的时间线使用时长
                        original_timeline_duration = self.get_actual_segment_duration(draft_info, video_id)
                        if original_timeline_duration is None:
                            original_timeline_duration = video.get('duration', 0)
                            print(f"    ⚠️ 无法获取时间线时长，使用素材时长: {original_timeline_duration/1000000:.1f}s")
                        else:
                            print(f"    📐 原时间线时长: {original_timeline_duration/1000000:.1f}s")
                        
                        # 更新素材信息，但保持原始文件名
                        # 不改变 material_name，保持引用关系
                        video['path'] = target_path
                        video['duration'] = new_duration
                        video['width'] = new_width
                        video['height'] = new_height
                        video['fps'] = fps
                        
                        print(f"    ✅ 成功更新素材: {target_name} (保持原名称)")
                        print(f"        新视频信息: 时长 {new_duration/1000000:.1f}s, 分辨率 {new_width}x{new_height}")
                        
                        # 应用时间线处理
                        if self.timeline_mode and original_timeline_duration > 0:
                            self.apply_timeline_processing(draft_info, video_id, original_timeline_duration, new_duration)
                        
                        return True
            
            print(f"    ❌ 未找到要替换的素材: {target_name}")
            print(f"    📋 草稿中的视频素材列表:")
            for video in videos:
                print(f"      - {video.get('material_name', 'unknown')} (id: {video.get('id', 'unknown')})")
            return False
            
        except Exception as e:
            print(f"    ❌ 替换视频素材失败: {e}")
            return False
    
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
    
    def update_segments_speed(self, draft_info, material_id, speed_ratio, new_material_duration=None):
        """更新使用指定素材的片段速度"""
        try:
            if 'tracks' not in draft_info:
                return
            
            updated_segments = 0
            
            # 创建Speed对象并添加到speeds数组
            import uuid
            speed_id = str(uuid.uuid4()).replace('-', '')[:8]
            speed_obj = {
                "curve_speed": None,
                "id": speed_id,
                "mode": 0,
                "speed": speed_ratio,
                "type": "speed"
            }
            
            # 确保speeds数组存在
            if 'materials' not in draft_info:
                draft_info['materials'] = {}
            if 'speeds' not in draft_info['materials']:
                draft_info['materials']['speeds'] = []
            
            # 添加speed对象到speeds数组
            draft_info['materials']['speeds'].append(speed_obj)
            
            for track in draft_info['tracks']:
                if track.get('type') == 'video' and 'segments' in track:
                    segments = track['segments']
                    
                    for segment in segments:
                        # 检查片段是否使用了指定的素材
                        if segment.get('material_id') == material_id:
                            # 更新source_timerange以适应新素材时长
                            if new_material_duration and 'source_timerange' in segment:
                                # 保持source_timerange的start不变，只更新duration
                                source_start = segment['source_timerange'].get('start', 0)
                                segment['source_timerange']['duration'] = new_material_duration
                            
                            # 更新片段速度引用
                            segment['speed'] = speed_ratio
                            
                            # 更新extra_material_refs，添加speed_id引用
                            if 'extra_material_refs' not in segment:
                                segment['extra_material_refs'] = []
                            
                            # 添加新的speed引用
                            segment['extra_material_refs'].append(speed_id)
                            
                            updated_segments += 1
                            print(f"    🎬 更新片段速度: {speed_ratio:.2f}x (ID: {speed_id})")
            
            if updated_segments == 0:
                print(f"    ⚠️ 未找到使用素材 {material_id} 的片段")
                # 如果没有使用到，移除刚创建的speed对象
                draft_info['materials']['speeds'] = [s for s in draft_info['materials']['speeds'] if s['id'] != speed_id]
            
        except Exception as e:
            print(f"    ❌ 更新片段速度失败: {e}")
    
    def apply_timeline_processing(self, draft_info, material_id, original_duration, new_duration):
        """应用时间线处理逻辑"""
        try:
            print(f"    ⏱️ 时间线处理: 原时长 {original_duration/1000000:.1f}s, 新时长 {new_duration/1000000:.1f}s")
            
            if self.timeline_mode == "keep_original":
                print(f"    📝 保持原样，不进行时间线调整")
                return True
            
            # 计算时长差异
            duration_ratio = new_duration / original_duration
            
            if abs(duration_ratio - 1.0) < 0.01:  # 时长差异小于1%，不需要调整
                print(f"    ✅ 时长差异很小，无需调整")
                return True
            
            if self.timeline_mode == "speed_adjust":
                # 变速调整：调整播放速度以匹配原时长
                speed_ratio = duration_ratio  # 新素材长就加速，短就减速
                print(f"    🎛️ 应用变速调整: {speed_ratio:.2f}x")
                self.update_segments_speed(draft_info, material_id, speed_ratio, new_duration)
                
            elif self.timeline_mode in ["crop_end", "crop_start", "crop_random"]:
                if new_duration > original_duration:
                    # 新素材太长，需要裁剪
                    self.apply_crop_processing(draft_info, material_id, original_duration, new_duration, self.timeline_mode)
                else:
                    # 新素材太短，减速播放
                    speed_ratio = duration_ratio
                    print(f"    🐌 新素材较短，减速播放: {speed_ratio:.2f}x")
                    self.update_segments_speed(draft_info, material_id, speed_ratio, new_duration)
            
            return True
            
        except Exception as e:
            print(f"    ❌ 时间线处理失败: {e}")
            return False
    
    def apply_crop_processing(self, draft_info, material_id, target_duration, source_duration, crop_mode):
        """应用裁剪处理"""
        try:
            if 'tracks' not in draft_info:
                return
            
            import random
            
            for track in draft_info['tracks']:
                if track.get('type') == 'video' and 'segments' in track:
                    segments = track['segments']
                    
                    for segment in segments:
                        if segment.get('material_id') == material_id:
                            if 'source_timerange' not in segment:
                                segment['source_timerange'] = {'start': 0, 'duration': source_duration}
                            
                            source_range = segment['source_timerange']
                            
                            if crop_mode == "crop_end":
                                # 裁剪尾部：保持开始时间，缩短duration
                                source_range['duration'] = target_duration
                                print(f"    ✂️ 裁剪尾部: 保留前 {target_duration/1000000:.1f}s")
                                
                            elif crop_mode == "crop_start":
                                # 裁剪头部：调整开始时间
                                crop_amount = source_duration - target_duration
                                source_range['start'] = crop_amount
                                source_range['duration'] = target_duration
                                print(f"    ✂️ 裁剪头部: 跳过前 {crop_amount/1000000:.1f}s")
                                
                            elif crop_mode == "crop_random":
                                # 随机裁剪：随机选择开始位置
                                max_start = source_duration - target_duration
                                random_start = random.randint(0, int(max_start))
                                source_range['start'] = random_start
                                source_range['duration'] = target_duration
                                print(f"    ✂️ 随机裁剪: 从 {random_start/1000000:.1f}s 开始")
                            
        except Exception as e:
            print(f"    ❌ 裁剪处理失败: {e}")
    
    
    def run(self):
        """运行主程序"""
        self.print_header("视频预处理工具 - 基于目录的草稿生成")
        
        # 1. 初始化草稿文件夹
        if not self.initialize_draft_folder():
            return
        
        # 2. 选择模板草稿
        if not self.select_template_draft():
            return
        
        # 3. 选择源素材目录
        if not self.select_source_directory():
            return
        
        # 4. 选择时间线处理模式
        if not self.select_timeline_mode():
            return
        
        # 5. 扫描目录文件
        materials = self.scan_directory_files()
        if not materials:
            return
        
        # 6. 创建新草稿
        if not self.create_drafts_from_materials(materials):
            return
        
        self.print_success("视频预处理完成！")


def main():
    """主函数"""
    try:
        processor = VideoPreprocessCli()
        processor.run()
    except KeyboardInterrupt:
        print("\n\n❌ 用户中断程序")
    except Exception as e:
        print(f"\n\n❌ 程序运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()