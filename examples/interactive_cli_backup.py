#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式CLI工具 - 剪映草稿复制与素材替换
基于 simple_copy_draft.py 重新设计，支持复制草稿后替换视频片段
"""

import os
import sys
import json
import time
import glob
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pyJianYingDraft as draft


class InteractiveDraftCLI:
    """交互式草稿复制和素材替换工具"""
    
    def __init__(self):
        self.draft_folder_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
        self.materials_folder_path = None
        self.selected_draft = None
        self.copied_draft_name = None
        self.draft_folder = None
        
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
    
    def get_user_choice(self, options, prompt="请选择", allow_back=False):
        """获取用户选择"""
        while True:
            try:
                print(f"\n{prompt}:")
                for i, option in enumerate(options, 1):
                    print(f"  {i}. {option}")
                if allow_back:
                    print(f"  b. 返回上级菜单")
                print(f"  0. 退出")
                
                choice = input("\n👉 输入选择: ").strip().lower()
                
                if choice == '0':
                    print("\n👋 再见!")
                    sys.exit(0)
                elif choice == 'b' and allow_back:
                    return -1, None
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(options):
                    return choice_num - 1, options[choice_num - 1]
                else:
                    print("❌ 选择超出范围，请重新输入")
            except ValueError:
                print("❌ 请输入有效的数字或字母")
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
    
    def list_and_select_draft(self):
        """列出并选择草稿"""
        self.print_header("选择源草稿")
        
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
            
            choice_idx, choice_str = self.get_user_choice(draft_options, "选择要复制的源草稿", allow_back=True)
            
            if choice_idx == -1:
                return False
            
            self.selected_draft = filtered_drafts[choice_idx]
            self.print_success(f"已选择源草稿: {self.selected_draft}")
            return True
            
        except Exception as e:
            self.print_error(f"列出草稿失败: {e}")
            return False
    
    def copy_draft(self):
        """复制选定的草稿"""
        if not self.selected_draft:
            self.print_error("未选择源草稿")
            return False
        
        self.print_header("复制草稿")
        
        # 生成默认目标名称
        timestamp = int(time.time())
        default_name = f"{self.selected_draft}_复制版_{timestamp}"
        
        print(f"源草稿: {self.selected_draft}")
        target_name = self.get_user_input(f"输入目标草稿名称 (回车使用默认: {default_name})", allow_empty=True)
        
        if not target_name:
            target_name = default_name
        
        print(f"目标草稿: {target_name}")
        
        try:
            # 执行复制
            print("\n⏳ 正在复制草稿...")
            copied_script = self.draft_folder.duplicate_as_template(self.selected_draft, target_name)
            self.print_warning("模板复制API可能报错，这是正常的（新版剪映加密）")
        except Exception as e:
            self.print_warning(f"API报错: {e}")
            print("检查草稿是否实际创建成功...")
        
        # 检查是否实际创建成功
        time.sleep(1)  # 等待文件系统同步
        updated_drafts = self.draft_folder.list_drafts()
        
        if target_name in updated_drafts:
            self.print_success("草稿复制成功!")
            self.copied_draft_name = target_name
            
            # 显示复制后的草稿信息
            draft_info = self.load_draft_info_from_file(target_name)
            if draft_info:
                self.print_success("成功读取草稿详细信息:")
                canvas = draft_info['canvas_config']
                if canvas:
                    print(f"  📐 分辨率: {canvas.get('width', '?')}x{canvas.get('height', '?')}")
                if draft_info['duration']:
                    print(f"  ⏱️  时长: {draft_info['duration'] / 1000000:.2f}秒")
                if draft_info['tracks']:
                    track_summary = []
                    for track_type, count in draft_info['tracks'].items():
                        track_summary.append(f"{track_type}:{count}")
                    print(f"  🎞️  轨道: {', '.join(track_summary)}")
                
                video_count = len(draft_info['video_materials'])
                if video_count > 0:
                    print(f"  🎥 视频素材: {video_count}个")
                    for i, video in enumerate(draft_info['video_materials'][:3]):
                        print(f"    {i+1}. {video['name']} ({video['width']}x{video['height']})")
                    if video_count > 3:
                        print(f"    ... 还有 {video_count-3} 个视频")
            
            return True
        else:
            self.print_error("草稿复制失败")
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
                self.print_warning("未设置素材文件夹，将跳过素材替换")
                return False
        
        # 扫描素材文件
        video_files = []
        for ext in ['*.mp4', '*.mov', '*.avi', '*.mkv']:
            video_files.extend(glob.glob(os.path.join(self.materials_folder_path, "**", ext), recursive=True))
        
        if video_files:
            print(f"📁 素材文件夹: {self.materials_folder_path}")
            print(f"🎥 找到 {len(video_files)} 个视频文件")
            for i, video_file in enumerate(video_files[:5]):
                rel_path = os.path.relpath(video_file, self.materials_folder_path)
                print(f"  {i+1}. {rel_path}")
            if len(video_files) > 5:
                print(f"  ... 还有 {len(video_files)-5} 个文件")
            return True
        else:
            self.print_warning("素材文件夹中没有找到视频文件")
            return False
    
    def replace_video_materials(self):
        """替换视频素材"""
        if not self.copied_draft_name:
            self.print_error("没有可用的复制草稿")
            return False
        
        if not self.materials_folder_path:
            if not self.setup_materials_folder():
                return False
        
        self.print_header("替换视频素材")
        
        # 获取复制草稿的信息
        draft_info = self.load_draft_info_from_file(self.copied_draft_name)
        if not draft_info:
            self.print_error("无法读取草稿信息")
            return False
        
        video_materials = draft_info['video_materials']
        if not video_materials:
            self.print_warning("草稿中没有视频素材")
            return False
        
        print(f"📝 草稿 '{self.copied_draft_name}' 中的视频素材:")
        for i, video in enumerate(video_materials):
            duration_sec = video['duration'] / 1000000 if video['duration'] else 0
            print(f"  {i+1}. {video['name']} ({video['width']}x{video['height']}, {duration_sec:.1f}s)")
        
        # 获取可用的替换素材
        video_files = []
        for ext in ['*.mp4', '*.mov', '*.avi', '*.mkv']:
            video_files.extend(glob.glob(os.path.join(self.materials_folder_path, "**", ext), recursive=True))
        
        if not video_files:
            self.print_error("素材文件夹中没有视频文件")
            return False
        
        print(f"\n📁 可用的替换素材:")
        video_options = []
        for video_file in video_files:
            rel_path = os.path.relpath(video_file, self.materials_folder_path)
            file_size = os.path.getsize(video_file)
            size_mb = file_size / (1024 * 1024)
            video_options.append(f"{rel_path} ({size_mb:.1f}MB)")
        
        # 替换流程
        replacements = []
        
        print(f"\n🔄 开始配置素材替换:")
        for i, video in enumerate(video_materials):
            print(f"\n替换素材 {i+1}: {video['name']}")
            
            choice_idx, choice_str = self.get_user_choice(
                video_options + ["跳过此素材"], 
                f"选择替换 '{video['name']}' 的新素材"
            )
            
            if choice_idx < len(video_files):
                selected_file = video_files[choice_idx]
                replacements.append({
                    'original_name': video['name'],
                    'original_id': video['id'],
                    'new_file': selected_file,
                    'new_name': os.path.basename(selected_file)
                })
                self.print_success(f"将用 {os.path.basename(selected_file)} 替换 {video['name']}")
            else:
                print(f"跳过替换 {video['name']}")
        
        if not replacements:
            self.print_warning("没有配置任何替换")
            return False
        
        # 执行替换
        print(f"\n🔄 执行素材替换...")
        try:
            # 这里需要实现实际的替换逻辑
            # 由于新版剪映的加密限制，这里提供一个概念性的实现
            
            self.print_warning("注意: 由于新版剪映使用了加密，素材替换功能受限")
            print("📋 替换计划:")
            for replacement in replacements:
                print(f"  • {replacement['original_name']} → {replacement['new_name']}")
            
            print("\n💡 建议的替换方式:")
            print("1. 在剪映中打开复制的草稿")
            print("2. 手动替换对应的素材文件")
            print("3. 或使用支持的剪映版本 (5.9及以下) 进行自动替换")
            
            # 为兼容版本提供替换代码框架
            if self.attempt_material_replacement(replacements):
                self.print_success("素材替换完成!")
                return True
            else:
                self.print_warning("自动替换失败，请手动替换")
                return False
                
        except Exception as e:
            self.print_error(f"替换过程出错: {e}")
            return False
    
    def attempt_material_replacement(self, replacements):
        """尝试执行素材替换"""
        # 首先尝试传统方法（支持未加密版本）
        if self.attempt_traditional_replacement(replacements):
            return True
        
        # 如果传统方法失败，尝试直接操作 draft_info.json
        print("\n🔄 尝试直接操作 draft_info.json 进行替换...")
        return self.attempt_direct_json_replacement(replacements)
    
    def attempt_traditional_replacement(self, replacements):
        """尝试传统的素材替换方法（仅支持未加密版本）"""
        try:
            # 尝试加载草稿进行替换
            script = self.draft_folder.load_template(self.copied_draft_name)
            
            success_count = 0
            for replacement in replacements:
                try:
                    # 创建新的素材对象
                    new_material = draft.VideoMaterial(replacement['new_file'])
                    
                    # 尝试替换
                    script.replace_material_by_name(replacement['original_name'], new_material)
                    success_count += 1
                    print(f"✅ 成功替换: {replacement['original_name']}")
                    
                except Exception as e:
                    print(f"❌ 替换失败 {replacement['original_name']}: {e}")
            
            if success_count > 0:
                # 保存草稿
                script.save()
                print(f"✅ 保存完成，成功替换 {success_count}/{len(replacements)} 个素材")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"⚠️  传统方法失败 (版本不兼容): {e}")
            return False
    
    def attempt_direct_json_replacement(self, replacements):
        """直接操作 draft_info.json 进行素材替换"""
        try:
            draft_info_path = os.path.join(self.draft_folder_path, self.copied_draft_name, "draft_info.json")
            
            if not os.path.exists(draft_info_path):
                print(f"❌ draft_info.json 不存在: {draft_info_path}")
                return False
            
            # 读取当前的 draft_info.json
            with open(draft_info_path, 'r', encoding='utf-8') as f:
                draft_info = json.load(f)
            
            # 备份原文件
            backup_path = draft_info_path + ".backup"
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(draft_info, f, ensure_ascii=False, indent=2)
            print(f"✅ 已创建备份: {os.path.basename(backup_path)}")
            
            success_count = 0
            
            # 复制新的视频文件到materials目录
            materials_dir = os.path.join(self.draft_folder_path, self.copied_draft_name, "materials", "video")
            if not os.path.exists(materials_dir):
                os.makedirs(materials_dir, exist_ok=True)
            
            # 更新 draft_info.json 中的视频素材信息
            if 'materials' in draft_info and 'videos' in draft_info['materials']:
                videos = draft_info['materials']['videos']
                
                for replacement in replacements:
                    # 查找要替换的视频素材
                    for video in videos:
                        if video.get('material_name') == replacement['original_name']:
                            try:
                                # 复制新文件到草稿materials目录
                                new_filename = replacement['new_name']
                                target_path = os.path.join(materials_dir, new_filename)
                                
                                import shutil
                                shutil.copy2(replacement['new_file'], target_path)
                                print(f"✅ 复制文件: {new_filename}")
                                
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
                                
                                success_count += 1
                                print(f"✅ 更新素材信息: {replacement['original_name']} → {new_filename}")
                                break
                                
                            except Exception as e:
                                print(f"❌ 替换失败 {replacement['original_name']}: {e}")
            
            if success_count > 0:
                # 保存更新后的 draft_info.json
                with open(draft_info_path, 'w', encoding='utf-8') as f:
                    json.dump(draft_info, f, ensure_ascii=False, indent=2)
                
                print(f"✅ 直接素材替换完成! 成功替换 {success_count}/{len(replacements)} 个素材")
                print(f"💾 已更新 draft_info.json")
                print(f"📁 新素材已复制到草稿materials目录")
                return True
            else:
                print("❌ 没有成功替换任何素材")
                return False
                
        except Exception as e:
            print(f"❌ 直接JSON替换失败: {e}")
            return False
    
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
                print(f"⚠️  无法获取视频信息: {video_path}")
                return None
                
        except Exception as e:
            print(f"⚠️  获取视频信息时出错: {e}")
            # 返回基础信息
            file_size = os.path.getsize(video_path)
            return {'duration': 5000000}  # 默认5秒
    
    def main_menu(self):
        """主菜单"""
        while True:
            self.print_header("剪映草稿复制与素材替换工具")
            
            status_info = []
            if self.selected_draft:
                status_info.append(f"源草稿: {self.selected_draft}")
            if self.copied_draft_name:
                status_info.append(f"复制草稿: {self.copied_draft_name}")
            if self.materials_folder_path:
                status_info.append(f"素材文件夹: {os.path.basename(self.materials_folder_path)}")
            
            if status_info:
                print("📊 当前状态:")
                for info in status_info:
                    print(f"  • {info}")
            
            options = [
                "选择源草稿",
                "复制草稿",
                "设置素材文件夹",
                "替换视频素材",
                "查看草稿信息",
                "设置路径"
            ]
            
            choice_idx, choice_str = self.get_user_choice(options, "选择操作")
            
            if choice_idx == 0:  # 选择源草稿
                self.list_and_select_draft()
            elif choice_idx == 1:  # 复制草稿
                if self.selected_draft:
                    self.copy_draft()
                else:
                    self.print_error("请先选择源草稿")
            elif choice_idx == 2:  # 设置素材文件夹
                self.setup_materials_folder()
            elif choice_idx == 3:  # 替换视频素材
                if self.copied_draft_name:
                    self.replace_video_materials()
                else:
                    self.print_error("请先复制草稿")
            elif choice_idx == 4:  # 查看草稿信息
                self.view_draft_info()
            elif choice_idx == 5:  # 设置路径
                if not self.setup_paths():
                    continue
    
    def view_draft_info(self):
        """查看草稿信息"""
        self.print_header("草稿信息查看")
        
        if self.copied_draft_name:
            draft_names = [self.copied_draft_name]
            if self.selected_draft and self.selected_draft != self.copied_draft_name:
                draft_names.append(self.selected_draft)
        elif self.selected_draft:
            draft_names = [self.selected_draft]
        else:
            self.print_error("没有选择任何草稿")
            return
        
        for draft_name in draft_names:
            self.print_section(f"草稿: {draft_name}")
            draft_info = self.load_draft_info_from_file(draft_name)
            
            if draft_info:
                canvas = draft_info['canvas_config']
                print(f"📐 分辨率: {canvas.get('width', '?')}x{canvas.get('height', '?')}")
                if 'ratio' in canvas:
                    print(f"📏 宽高比: {canvas['ratio']}")
                
                if draft_info['duration']:
                    print(f"⏱️  时长: {draft_info['duration'] / 1000000:.2f}秒")
                
                if draft_info['fps']:
                    print(f"🎞️  帧率: {draft_info['fps']} fps")
                
                if draft_info['tracks']:
                    print(f"🎬 轨道统计:")
                    for track_type, count in draft_info['tracks'].items():
                        print(f"  • {track_type}: {count}条")
                
                if draft_info['materials']:
                    print(f"📦 素材统计:")
                    for material_type, count in draft_info['materials'].items():
                        if count > 0:
                            print(f"  • {material_type}: {count}个")
                
                if draft_info['video_materials']:
                    print(f"🎥 视频素材详情:")
                    for i, video in enumerate(draft_info['video_materials']):
                        duration_sec = video['duration'] / 1000000 if video['duration'] else 0
                        print(f"  {i+1}. {video['name']}")
                        print(f"     分辨率: {video['width']}x{video['height']}")
                        print(f"     时长: {duration_sec:.2f}秒")
                        if video['path']:
                            print(f"     路径: {video['path']}")
            else:
                self.print_error("无法读取草稿信息")
        
        input("\n按回车键返回...")
    
    def run(self):
        """运行CLI工具"""
        try:
            self.print_header("欢迎使用剪映草稿复制与素材替换工具")
            print("🚀 基于 simple_copy_draft.py 重新设计")
            print("💡 支持复制草稿后替换视频片段")
            print("📱 兼容新版剪映 (支持 draft_info.json)")
            
            if not self.setup_paths():
                return
            
            self.main_menu()
            
        except KeyboardInterrupt:
            print("\n\n👋 用户取消操作，再见!")
        except Exception as e:
            self.print_error(f"程序运行出错: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    cli = InteractiveDraftCLI()
    cli.run()


if __name__ == "__main__":
    main()