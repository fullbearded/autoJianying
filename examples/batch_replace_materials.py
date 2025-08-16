#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量素材替换系统
基于"4翰墨书院模版"进行素材替换和草稿生成
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import pyJianYingDraft as draft
import subprocess
import json

class MaterialBatchReplacer:
    """批量素材替换器"""
    
    def __init__(self, draft_folder_path: str, template_name: str = "4翰墨书院模版"):
        self.draft_folder_path = draft_folder_path
        self.template_name = template_name
        self.draft_folder = draft.DraftFolder(draft_folder_path)
        
        # 模板草稿中的素材映射
        self.template_materials = {
            "background": "background.jpg",
            "part1": "part1.mp4", 
            "part2": "part2.mp4",
            "part3": "part3.mp4",
            "voice": "voice.mp3",
            "bgm": "84b956ea9f1b80e536ff74446c26f6c9.mp3"
        }
        
        # 替换设置（默认配置）
        self.settings = {
            "speed_mode": 1,  # 1: 默认1倍速, 2: 按旧素材播放倍速
            "length_handle": 1,  # 1: 加速/减速保持时长, 2: 裁剪尾部, 3: 裁剪头部, 4: 随机裁剪, 5: 改变时间线
            "selection_mode": 1,  # 1: 顺序模式, 2: 随机模式
            "shuffle_order": False,  # False: 字母顺序, True: 随机顺序
            "delete_original": False,  # False: 不删除, True: 删除原文件
            "naming_mode": 2,  # 1: 参考草稿名, 2: 新素材名
            "media_type": 2  # 1: 图片, 2: 视频, 3: 图片和视频
        }
    
    def validate_folder_structure(self, parent_folder: str) -> Tuple[bool, str]:
        """验证文件夹结构"""
        if not os.path.exists(parent_folder):
            return False, f"指定的父文件夹不存在: {parent_folder}"
        
        # 获取子文件夹
        subfolders = [f for f in os.listdir(parent_folder) 
                     if os.path.isdir(os.path.join(parent_folder, f))]
        
        # 检查必需的文件夹
        required_folders = {"background", "part1", "part2", "part3"}
        missing_folders = required_folders - set(subfolders)
        
        if missing_folders:
            return False, f"缺少必需的文件夹: {', '.join(missing_folders)}"
        
        # 根据媒体类型设置检查文件夹
        media_type = self.settings["media_type"]
        
        # 检查每个文件夹中的文件
        for folder in ["background", "part1", "part2", "part3"]:
            folder_path = os.path.join(parent_folder, folder)
            if not os.path.exists(folder_path):
                return False, f"文件夹不存在: {folder}"
                
            files = os.listdir(folder_path)
            
            if folder == "background":
                jpg_files = [f for f in files if f.lower().endswith('.jpg')]
                if not jpg_files:
                    return False, f"{folder} 文件夹中没有找到 .jpg 文件"
            else:  # part1, part2, part3
                # 根据媒体类型检查不同的文件格式
                if media_type == 1:  # 仅图片
                    img_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
                    if not img_files:
                        return False, f"{folder} 文件夹中没有找到图片文件 (.jpg, .jpeg, .png, .bmp)"
                elif media_type == 2:  # 仅视频
                    mp4_files = [f for f in files if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
                    if not mp4_files:
                        return False, f"{folder} 文件夹中没有找到视频文件 (.mp4, .avi, .mov, .mkv)"
                else:  # 图片和视频
                    media_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.mp4', '.avi', '.mov', '.mkv'))]
                    if not media_files:
                        return False, f"{folder} 文件夹中没有找到媒体文件"
        
        # 检查是否有额外的素材文件夹（支持更多part文件夹）
        extra_parts = [f for f in subfolders if f.startswith('part') and f not in required_folders]
        if extra_parts:
            print(f"📁 发现额外的part文件夹: {', '.join(extra_parts)}")
            # 验证额外的part文件夹也有对应格式的文件
            for folder in extra_parts:
                folder_path = os.path.join(parent_folder, folder)
                files = os.listdir(folder_path)
                
                if media_type == 1:  # 仅图片
                    valid_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
                    if not valid_files:
                        return False, f"{folder} 文件夹中没有找到图片文件"
                elif media_type == 2:  # 仅视频
                    valid_files = [f for f in files if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
                    if not valid_files:
                        return False, f"{folder} 文件夹中没有找到视频文件"
                else:  # 图片和视频
                    valid_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.mp4', '.avi', '.mov', '.mkv'))]
                    if not valid_files:
                        return False, f"{folder} 文件夹中没有找到媒体文件"
        
        return True, "文件夹结构验证通过"
    
    def get_material_files(self, parent_folder: str) -> Dict[str, List[str]]:
        """获取各文件夹中的素材文件"""
        materials = {}
        media_type = self.settings["media_type"]
        
        # 定义支持的文件扩展名
        if media_type == 1:  # 仅图片
            valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
        elif media_type == 2:  # 仅视频
            valid_extensions = ('.mp4', '.avi', '.mov', '.mkv')
        else:  # 图片和视频
            valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.mp4', '.avi', '.mov', '.mkv')
        
        # 获取所有子文件夹
        subfolders = [f for f in os.listdir(parent_folder) 
                     if os.path.isdir(os.path.join(parent_folder, f))]
        
        # 处理background文件夹（仅在图片模式或混合模式下处理）
        if "background" in subfolders and media_type != 2:  # 不在纯视频模式下处理背景
            folder_path = os.path.join(parent_folder, "background")
            files = os.listdir(folder_path)
            # 背景文件夹通常包含图片
            materials["background"] = sorted([f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))])
        
        # 处理所有part文件夹（根据媒体类型）
        part_folders = [f for f in subfolders if f.startswith('part')]
        for folder in sorted(part_folders):  # 按名称排序确保一致性
            folder_path = os.path.join(parent_folder, folder)
            files = os.listdir(folder_path)
            materials[folder] = sorted([f for f in files if f.lower().endswith(valid_extensions)])
        
        return materials
    
    def create_replacement_combinations(self, materials: Dict[str, List[str]]) -> List[Dict[str, str]]:
        """创建替换组合（顺序模式）"""
        if not materials:
            return []
        
        # 找出最少的素材数量
        min_count = min(len(files) for files in materials.values() if files)
        
        combinations = []
        for i in range(min_count):
            combination = {}
            for folder, files in materials.items():
                if files:  # 确保文件列表不为空
                    combination[folder] = files[i % len(files)]  # 循环使用文件
            combinations.append(combination)
        
        return combinations
    
    def create_draft_from_template_replacement(self, combination: Dict[str, str], 
                                             parent_folder: str, output_name: str) -> bool:
        """基于模板替换方式创建新草稿"""
        try:
            print(f"  📋 使用模板替换方式创建草稿: {output_name}")
            
            # 加载模板草稿
            template_script = self.draft_folder.load_draft(self.template_name)
            if not template_script:
                print(f"❌ 无法加载模板草稿: {self.template_name}")
                return False
            
            # 复制模板创建新草稿
            new_script = template_script.copy(output_name)
            
            # 定义素材名称映射关系
            material_name_mapping = {
                "part1": "part1.mp4",
                "part2": "part2.mp4", 
                "part3": "part3.mp4",
                "background": "background.jpg"
            }
            
            # 定义模板时长要求
            template_durations = {
                "part1": 15.0,  # 15秒
                "part2": 10.0,  # 10秒
                "part3": 15.0   # 15秒
            }
            
            # 替换素材
            for part_folder, new_filename in combination.items():
                if part_folder in material_name_mapping:
                    original_material_name = material_name_mapping[part_folder]
                    new_material_path = os.path.join(parent_folder, part_folder, new_filename)
                    
                    # 检查新素材文件是否存在
                    if not os.path.exists(new_material_path):
                        print(f"      ⚠️  素材文件不存在，跳过: {new_material_path}")
                        continue
                    
                    file_ext = Path(new_filename).suffix.lower()
                    
                    try:
                        # 根据文件类型创建新素材
                        if file_ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                            # 图片素材
                            new_material = draft.VideoMaterial(new_material_path)
                            print(f"      🖼️  替换图片: {original_material_name} -> {new_filename}")
                        else:
                            # 视频素材 - 需要处理速度调整
                            if part_folder in template_durations:
                                # 获取新素材实际时长
                                new_duration = self.get_video_duration(new_material_path)
                                target_duration = template_durations[part_folder]
                                
                                if new_duration > 0:
                                    # 计算需要的播放速度
                                    required_speed = new_duration / target_duration
                                    limited_speed = max(0.1, min(required_speed, 5.0))
                                    
                                    print(f"      🎬 替换视频: {original_material_name} -> {new_filename}")
                                    print(f"           时长调整: {new_duration:.1f}s -> {target_duration:.1f}s (速度: {limited_speed:.2f}x)")
                                    
                                    # 创建带速度的视频素材
                                    new_material = draft.VideoMaterial(new_material_path)
                                else:
                                    print(f"      ⚠️  无法获取视频时长: {new_filename}")
                                    new_material = draft.VideoMaterial(new_material_path)
                            else:
                                new_material = draft.VideoMaterial(new_material_path)
                                print(f"      🎬 替换视频: {original_material_name} -> {new_filename}")
                        
                        # 执行素材替换
                        success = new_script.replace_material_by_name(original_material_name, new_material)
                        if success:
                            print(f"           ✅ 替换成功")
                        else:
                            print(f"           ⚠️  替换可能失败 (找不到原素材: {original_material_name})")
                            
                    except Exception as e:
                        print(f"      ❌ 替换素材失败 {original_material_name}: {e}")
                        continue
            
            # 保存新草稿
            new_script.save()
            print(f"✅ 成功创建草稿: {output_name}")
            return True
            
        except Exception as e:
            print(f"❌ 创建草稿失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_draft_from_segments_fixed(self, combination: Dict[str, str], 
                                       parent_folder: str, output_name: str) -> bool:
        """基于分段方式创建草稿 - 修复版本，使用独立轨道避免重叠"""
        try:
            print(f"  📋 使用分段方式创建草稿: {output_name}")
            
            # 创建新草稿
            script = self.draft_folder.create_draft(output_name, 1920, 1080)
            
            # 为每个part创建独立的视频轨道，避免时间线重叠
            part_track_mapping = {}
            part_folders = [key for key in combination.keys() if key.startswith('part')]
            part_folders.sort()
            
            for i, part in enumerate(part_folders):
                track_name = f"{part}轨道"
                script.add_track(draft.TrackType.video, track_name)
                part_track_mapping[part] = track_name
                print(f"      🎬 创建轨道: {track_name}")
            
            # 添加背景和音频轨道
            if "background" in combination:
                script.add_track(draft.TrackType.video, "背景", relative_index=0)
            script.add_track(draft.TrackType.audio, "语音")
            script.add_track(draft.TrackType.audio, "背景音乐")
            
            # 添加背景图片（如果存在且不是纯视频模式）
            if "background" in combination and self.settings["media_type"] != 2:
                bg_path = os.path.join(parent_folder, "background", combination["background"])
                bg_material = draft.VideoMaterial(bg_path)
                bg_segment = draft.VideoSegment(bg_material, draft.trange("0s", "40s"))
                script.add_segment(bg_segment, "背景")
                print(f"      🖼️  添加背景: {combination['background']}")
            
            # 定义模板时长
            template_durations = {
                "part1": 15.0,
                "part2": 10.0, 
                "part3": 15.0
            }
            
            # 为每个part创建片段，放在独立轨道上
            for part in part_folders:
                if part not in combination:
                    continue
                    
                media_path = os.path.join(parent_folder, part, combination[part])
                file_ext = Path(combination[part]).suffix.lower()
                track_name = part_track_mapping[part]
                
                if not os.path.exists(media_path):
                    print(f"      ⚠️  文件不存在，跳过: {media_path}")
                    continue
                
                # 创建素材并处理时长
                media_material = draft.VideoMaterial(media_path)
                target_duration = template_durations.get(part, 10.0)
                
                if file_ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                    # 图片处理
                    new_duration = target_duration
                    speed = 1.0
                    source_duration = target_duration
                    print(f"      🖼️  添加图片 {part}: {combination[part]} (时长: {new_duration}s)")
                else:
                    # 视频处理 - 获取精确时长并计算安全参数
                    try:
                        # 获取pyJianYingDraft内部精确时长（秒）
                        precise_duration = media_material.duration / 1000000.0
                        ffprobe_duration = self.get_video_duration(media_path)
                        
                        print(f"      📊 时长对比: ffprobe={ffprobe_duration:.3f}s, 内部={precise_duration:.3f}s")
                        
                        # 使用更保守的时长进行计算，选择较小值
                        safe_duration = min(ffprobe_duration, precise_duration) if ffprobe_duration > 0 else precise_duration
                        
                        if safe_duration > 0:
                            speed = safe_duration / target_duration
                            speed = max(0.1, min(speed, 5.0))
                            
                            # 计算截取时长 - 修复：对于加速情况，使用固定策略
                            if speed >= 1.0:
                                # 需要加速：使用全部可用素材，留最小安全边距
                                source_duration = safe_duration - 0.01  # 只留0.01秒边距
                                source_duration = max(0.1, source_duration)
                                print(f"           🎯 加速模式: 使用最大可用时长 {source_duration:.3f}s")
                            else:
                                # 需要减速：可以使用部分素材时长
                                source_duration = min(target_duration, safe_duration - 0.05)
                                source_duration = max(0.1, source_duration)
                                print(f"           🐌 减速模式: 使用部分时长 {source_duration:.3f}s")
                            
                            print(f"      🎬 添加视频 {part}: {combination[part]}")
                            print(f"           时长: {safe_duration:.3f}s -> {target_duration:.1f}s (速度: {speed:.2f}x)")
                            print(f"           安全截取: {source_duration:.3f}s (安全边距: {safe_duration-source_duration:.3f}s)")
                        else:
                            speed = 1.0
                            source_duration = target_duration
                            print(f"      🎬 添加视频 {part}: {combination[part]} (无法获取时长，使用默认)")
                    
                    except Exception as e:
                        speed = 1.0
                        source_duration = target_duration
                        print(f"      ⚠️  时长计算失败 {part}: {combination[part]} - {e}")
                    
                    new_duration = target_duration
                
                # 创建视频片段 - 每个part在自己的轨道上，从0开始
                print(f"           🔧 调试信息: 准备创建VideoSegment")
                print(f"              source_duration: {source_duration:.6f}s")
                print(f"              speed: {speed:.6f}x")
                print(f"              material.duration: {media_material.duration} microseconds ({media_material.duration/1000000:.6f}s)")
                
                try:
                    media_segment = draft.VideoSegment(
                        media_material,
                        draft.trange(f"0s", f"{source_duration:.6f}s"),
                        speed=speed
                    )
                except Exception as e:
                    print(f"              ❌ VideoSegment创建失败: {e}")
                    # 使用最保守的策略 - 不使用speed参数
                    material_duration_sec = media_material.duration / 1000000.0
                    ultra_safe_source = min(target_duration, material_duration_sec - 0.1)
                    ultra_safe_source = max(0.1, ultra_safe_source)
                    print(f"              🛡️  使用超保守策略: {ultra_safe_source:.6f}s (不使用速度调整)")
                    
                    media_segment = draft.VideoSegment(
                        media_material,
                        draft.trange(f"0s", f"{ultra_safe_source:.6f}s"),
                        # 不使用speed参数，让时间线处理
                    )
                
                # 在时间线上的位置 - 每个轨道从0开始，避免重叠
                media_segment.target_timerange = draft.trange(f"0s", f"{new_duration:.3f}s")
                
                # 添加到对应轨道
                script.add_segment(media_segment, track_name)
                print(f"           ✅ 添加到轨道: {track_name}")
            
            # 保存草稿
            script.save()
            print(f"✅ 成功创建草稿: {output_name}")
            return True
            
        except Exception as e:
            print(f"❌ 创建草稿失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def print_settings(self):
        """打印当前替换设置"""
        media_type_names = {1: "图片", 2: "视频", 3: "图片和视频"}
        
        print("\n📋 当前替换设置 (独立轨道方式):")
        print("-" * 50)
        print("1. 替换方式: 🎯 分段创建，独立轨道避免重叠")
        print("2. 时长处理: ✅ 新素材如果太长就加速，太短就减速，保证片段时长相同")
        print("3. 选取模式: 顺序模式（不重复）")
        print("4. 文件顺序: 不需要，就按字母顺序即可")
        print("5. 删除原文件: 不需要")
        print("6. 草稿命名: 新素材名")
        print("7. 文件夹数量: 无限制（支持任意数量的part文件夹）")
        print(f"8. 媒体类型: {media_type_names[self.settings['media_type']]}")
        print("\n🔧 模板素材映射:")
        print("   part1/ -> part1.mp4 (目标时长: 15.0秒)")
        print("   part2/ -> part2.mp4 (目标时长: 10.0秒)")
        print("   part3/ -> part3.mp4 (目标时长: 15.0秒)")
        print("   background/ -> background.jpg (背景图片)")
        
        # 显示支持的文件格式
        if self.settings["media_type"] == 1:
            print("   支持格式: .jpg, .jpeg, .png, .bmp")
        elif self.settings["media_type"] == 2:
            print("   支持格式: .mp4, .avi, .mov, .mkv")
        else:
            print("   支持格式: .jpg, .jpeg, .png, .bmp, .mp4, .avi, .mov, .mkv")
        print()
    
    def get_video_duration(self, video_path: str) -> float:
        """获取视频文件的实际时长（秒）
        
        Args:
            video_path (str): 视频文件路径
            
        Returns:
            float: 视频时长（秒），如果获取失败返回0
        """
        try:
            # 使用ffprobe获取视频信息
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # 尝试从format信息获取时长
                if 'format' in data and 'duration' in data['format']:
                    return float(data['format']['duration'])
                
                # 尝试从视频流获取时长
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video' and 'duration' in stream:
                        return float(stream['duration'])
            
            print(f"⚠️  无法获取视频时长: {video_path}")
            return 0.0
            
        except Exception as e:
            print(f"⚠️  获取视频时长失败 {video_path}: {e}")
            return 0.0
    
    def set_media_type(self, media_type: int):
        """设置媒体类型
        
        Args:
            media_type (int): 1=图片, 2=视频, 3=图片和视频
        """
        if media_type in [1, 2, 3]:
            self.settings["media_type"] = media_type
            media_type_names = {1: "图片", 2: "视频", 3: "图片和视频"}
            print(f"✅ 媒体类型已设置为: {media_type_names[media_type]}")
        else:
            print("❌ 无效的媒体类型，请选择 1(图片), 2(视频), 3(图片和视频)")
    
    def batch_replace(self, parent_folder: str) -> bool:
        """执行批量替换"""
        print(f"🚀 开始批量素材替换")
        print(f"模板草稿: {self.template_name}")
        print(f"素材文件夹: {parent_folder}")
        print("=" * 60)
        
        # 1. 验证文件夹结构
        print("📁 验证文件夹结构...")
        is_valid, message = self.validate_folder_structure(parent_folder)
        if not is_valid:
            print(f"❌ {message}")
            return False
        print(f"✅ {message}")
        
        # 2. 获取素材文件
        print("\n📄 扫描素材文件...")
        materials = self.get_material_files(parent_folder)
        for folder, files in materials.items():
            print(f"  {folder}: {len(files)} 个文件")
        
        # 3. 创建替换组合
        print("\n🔄 生成替换组合...")
        combinations = self.create_replacement_combinations(materials)
        print(f"  共生成 {len(combinations)} 个组合")
        
        # 4. 显示设置
        self.print_settings()
        
        # 5. 批量创建草稿
        print("🎬 开始创建草稿...")
        success_count = 0
        
        for i, combination in enumerate(combinations, 1):
            # 生成草稿名称（使用新素材名）
            if self.settings["naming_mode"] == 2:  # 新素材名
                # 使用part1的文件名作为基础名称
                base_name = Path(combination["part1"]).stem
                # 添加时间戳避免重复
                import time
                timestamp = int(time.time()) % 10000  # 使用最后4位时间戳
                output_name = f"{base_name}_{i:02d}_{timestamp}"
            else:  # 参考草稿名
                import time
                timestamp = int(time.time()) % 10000
                output_name = f"{self.template_name}_变体_{i:02d}_{timestamp}"
            
            print(f"\n  创建草稿 {i}/{len(combinations)}: {output_name}")
            if 'background' in combination:
                print(f"    background: {combination['background']}")
            for key, value in combination.items():
                if key.startswith('part'):
                    print(f"    {key}: {value}")
            
            if self.create_draft_from_segments_fixed(combination, parent_folder, output_name):
                success_count += 1
        
        print(f"\n🎉 批量替换完成!")
        print(f"✅ 成功创建 {success_count}/{len(combinations)} 个草稿")
        
        return success_count > 0

def main():
    """主函数"""
    # 配置路径
    draft_folder_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
    template_name = "4翰墨书院模版"
    
    # 示例素材文件夹路径（需要用户创建）
    materials_folder = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/test/materials"
    
    print("🎬 批量素材替换系统")
    print("=" * 60)
    print(f"模板草稿: {template_name}")
    
    # 创建替换器
    replacer = MaterialBatchReplacer(draft_folder_path, template_name)
    
    # 媒体类型选择菜单
    print("\n📋 媒体类型配置:")
    print("请选择要处理的媒体类型:")
    print("1. 图片 (.jpg, .jpeg, .png, .bmp)")
    print("2. 视频 (.mp4, .avi, .mov, .mkv) [默认]")
    print("3. 图片和视频 (混合模式)")
    
    # 由于在非交互环境中，使用默认值
    media_choice = 2  # 默认选择视频
    replacer.set_media_type(media_choice)
    
    print(f"\n请在以下路径创建素材文件夹结构:")
    print(f"  {materials_folder}/")
    print(f"  ├── background/     (放入 .jpg 文件)")
    
    if media_choice == 1:
        print(f"  ├── part1/          (放入图片文件)")
        print(f"  ├── part2/          (放入图片文件)")
        print(f"  ├── part3/          (放入图片文件)")
        print(f"  ├── part4/          (可选，放入图片文件)")
    elif media_choice == 2:
        print(f"  ├── part1/          (放入视频文件)")
        print(f"  ├── part2/          (放入视频文件)")
        print(f"  ├── part3/          (放入视频文件)")
        print(f"  ├── part4/          (可选，放入视频文件)")
    else:
        print(f"  ├── part1/          (放入图片或视频文件)")
        print(f"  ├── part2/          (放入图片或视频文件)")
        print(f"  ├── part3/          (放入图片或视频文件)")
        print(f"  ├── part4/          (可选，放入图片或视频文件)")
    
    print(f"  └── ...             (支持更多part文件夹)")
    print()
    
    # 检查素材文件夹是否存在
    if not os.path.exists(materials_folder):
        print(f"❌ 素材文件夹不存在: {materials_folder}")
        print("请先创建文件夹结构并放入素材文件")
        return
    
    try:
        # 执行批量替换
        replacer.batch_replace(materials_folder)
        
    except Exception as e:
        print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    main()