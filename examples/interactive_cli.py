#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量草稿复制与素材替换工具
支持part1/part2/part3文件夹组合式素材替换
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
    
    def __init__(self):
        self.draft_folder_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
        self.materials_folder_path = None
        self.selected_draft = None
        self.draft_folder = None
        self.material_combinations = []
        self.processing_mode = None  # "sequential" 或 "random"
        self.replacement_mode = None  # "video", "image", "all"
        
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
    
    def get_user_choice(self, options, prompt="请选择"):
        """获取用户选择"""
        while True:
            try:
                print(f"\n{prompt}:")
                for i, option in enumerate(options, 1):
                    print(f"  {i}. {option}")
                print(f"  0. 退出")
                
                choice = input("\n👉 输入选择: ").strip()
                
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
                sys.exit(0)
    
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
            "仅替换视频片段 (part1/part2/part3)",
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
    
    def create_part_folders_and_scan(self):
        """创建文件夹并扫描素材"""
        self.print_section("创建素材文件夹结构")
        
        # 根据替换模式决定需要处理的文件夹
        if self.replacement_mode == "video":
            folders_to_process = ['part1', 'part2', 'part3']
            file_extensions = ['*.mp4', '*.mov', '*.avi', '*.mkv']
        elif self.replacement_mode == "image":
            folders_to_process = ['background']
            file_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
        else:  # "all"
            folders_to_process = ['part1', 'part2', 'part3', 'background']
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
        self.generate_material_combinations(part_files)
        return True
    
    def generate_material_combinations(self, part_files):
        """生成素材组合"""
        self.print_section("生成素材组合")
        
        # 找到文件数量最少的文件夹（决定组合数量）
        min_count = min(len(files) for files in part_files.values())
        
        print(f"📊 各文件夹文件数量:")
        for folder, files in part_files.items():
            if folder == 'background':
                print(f"  {folder}: {len(files)} 个图片文件")
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
        
        # 生成组合
        self.material_combinations = []
        
        if self.processing_mode == "sequential":
            # 顺序模式：按文件名排序
            sorted_parts = {}
            for folder, files in part_files.items():
                sorted_parts[folder] = sorted(files)
            
            for i in range(min_count):
                combination = {}
                for folder in part_files.keys():
                    combination[folder] = sorted_parts[folder][i]
                self.material_combinations.append(combination)
        
        else:
            # 随机模式：打乱排序
            shuffled_parts = {}
            for folder, files in part_files.items():
                shuffled_files = files.copy()
                random.shuffle(shuffled_files)
                shuffled_parts[folder] = shuffled_files
            
            for i in range(min_count):
                combination = {}
                for folder in part_files.keys():
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
        for folder in ['part1', 'part2', 'part3', 'background']:
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
        for folder in ['part1', 'part2', 'part3', 'background']:
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
            print(f"    ⚠️ API报错: {e} (这是正常的，新版剪映加密)")
        
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
                return False
            
            # 执行替换
            return self.attempt_direct_json_replacement(draft_name, replacements)
            
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
            
            # 检查素材名称是否包含part1、part2、part3等关键词
            if 'part1' in video_name.lower():
                matching_folder = 'part1'
            elif 'part2' in video_name.lower():
                matching_folder = 'part2'
            elif 'part3' in video_name.lower():
                matching_folder = 'part3'
            
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
            
            # 分别处理视频和图片素材
            for replacement in replacements:
                if replacement['type'] == 'video':
                    if self.replace_video_material(draft_info, replacement, draft_name):
                        success_count += 1
                elif replacement['type'] == 'image':
                    if self.replace_image_material(draft_info, replacement, draft_name):
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
                        # 复制新文件到草稿materials目录
                        new_filename = replacement['new_name']
                        target_path = os.path.join(materials_dir, new_filename)
                        
                        shutil.copy2(replacement['new_file'], target_path)
                        
                        # 获取新文件的信息
                        new_file_info = self.get_video_file_info(replacement['new_file'])
                        
                        # 更新素材信息
                        video['material_name'] = new_filename
                        video['path'] = f"##_draftpath_placeholder_0E685133-18CE-45ED-8CB8-2904A212EC80_##/materials/video/{new_filename}"
                        
                        if new_file_info:
                            if 'duration' in new_file_info:
                                video['duration'] = new_file_info['duration']
                            if 'width' in new_file_info:
                                video['width'] = new_file_info['width']
                            if 'height' in new_file_info:
                                video['height'] = new_file_info['height']
                        
                        print(f"    ✅ 更新视频素材: {replacement['original_name']} → {new_filename}")
                        return True
            
            return False
            
        except Exception as e:
            print(f"    ❌ 替换视频素材失败 {replacement['original_name']}: {e}")
            return False
    
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
    
    def get_video_file_info(self, video_path):
        """获取视频文件信息"""
        try:
            import subprocess
            
            # 使用ffprobe获取视频信息
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
                
                return video_info
            else:
                return None
                
        except Exception as e:
            # 返回基础信息
            file_size = os.path.getsize(video_path)
            return {'duration': 5000000}  # 默认5秒
    
    def run(self):
        """运行CLI工具"""
        try:
            self.print_header("剪映批量草稿复制与素材替换工具")
            print("🚀 支持part1/part2/part3文件夹组合式素材替换")
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
            
            # 5. 创建文件夹并扫描素材
            if not self.create_part_folders_and_scan():
                return
            
            # 6. 批量处理草稿
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
    processor = BatchDraftProcessor()
    processor.run()


if __name__ == "__main__":
    main()