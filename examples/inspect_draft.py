#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
草稿元素信息查看工具
用于分析和展示剪映草稿的详细信息，包括轨道、片段、素材等
"""

import os
import sys
import json
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pyJianYingDraft as draft


class DraftInspector:
    """草稿检查器"""
    
    def __init__(self):
        self.draft_folder_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
        self.draft_folder = None
    
    def print_header(self, title):
        """打印标题"""
        print("\n" + "=" * 80)
        print(f"🔍 {title}")
        print("=" * 80)
    
    def print_section(self, title):
        """打印章节标题"""
        print(f"\n📋 {title}")
        print("-" * 60)
    
    def print_subsection(self, title):
        """打印子章节标题"""
        print(f"\n📄 {title}")
        print("-" * 40)
    
    def setup_draft_folder(self, custom_path=None):
        """设置草稿文件夹"""
        if custom_path:
            self.draft_folder_path = custom_path
        
        if not os.path.exists(self.draft_folder_path):
            print(f"❌ 草稿文件夹不存在: {self.draft_folder_path}")
            return False
        
        try:
            self.draft_folder = draft.DraftFolder(self.draft_folder_path)
            print(f"✅ 成功加载草稿文件夹: {self.draft_folder_path}")
            return True
        except Exception as e:
            print(f"❌ 初始化草稿文件夹失败: {e}")
            return False
    
    def list_drafts(self):
        """列出所有草稿"""
        try:
            draft_list = self.draft_folder.list_drafts()
            # 过滤掉系统文件
            filtered_drafts = [d for d in draft_list if not d.startswith('.')]
            
            self.print_section("可用草稿列表")
            print(f"📁 草稿文件夹: {self.draft_folder_path}")
            print(f"📊 找到 {len(filtered_drafts)} 个草稿:")
            
            for i, draft_name in enumerate(filtered_drafts, 1):
                # 尝试获取草稿基本信息
                try:
                    draft_info = self.load_draft_info_from_file(draft_name)
                    if draft_info:
                        canvas = draft_info['canvas_config']
                        duration_sec = draft_info['duration'] / 1000000 if draft_info['duration'] else 0
                        track_count = len(draft_info.get('tracks', []))
                        material_count = sum(len(materials) for materials in draft_info.get('materials', {}).values())
                        
                        print(f"  {i:2d}. {draft_name}")
                        print(f"      分辨率: {canvas.get('width', '?')}x{canvas.get('height', '?')}")
                        print(f"      时长: {duration_sec:.1f}s")
                        print(f"      轨道数: {track_count}")
                        print(f"      素材数: {material_count}")
                    else:
                        print(f"  {i:2d}. {draft_name} (信息读取失败)")
                except Exception as e:
                    print(f"  {i:2d}. {draft_name} (错误: {str(e)[:50]}...)")
            
            return filtered_drafts
            
        except Exception as e:
            print(f"❌ 列出草稿失败: {e}")
            return []
    
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
            tracks = draft_info.get('tracks', [])
            
            # 统计素材信息
            materials = draft_info.get('materials', {})
            
            return {
                'draft_name': draft_name,
                'canvas_config': canvas,
                'duration': duration,
                'fps': fps,
                'tracks': tracks,
                'materials': materials,
                'raw_data': draft_info
            }
            
        except Exception as e:
            print(f"读取 draft_info.json 失败: {e}")
            return None
    
    def inspect_draft_details(self, draft_name):
        """详细检查草稿信息"""
        self.print_header(f"草稿详细信息: {draft_name}")
        
        # 加载草稿信息
        draft_info = self.load_draft_info_from_file(draft_name)
        if not draft_info:
            print("❌ 无法加载草稿信息")
            return False
        
        # 基本信息
        self.print_section("基本信息")
        canvas = draft_info['canvas_config']
        duration_sec = draft_info['duration'] / 1000000 if draft_info['duration'] else 0
        
        print(f"草稿名称: {draft_name}")
        print(f"分辨率: {canvas.get('width', '?')} x {canvas.get('height', '?')}")
        print(f"总时长: {duration_sec:.2f} 秒 ({draft_info['duration']} 微秒)")
        print(f"帧率: {draft_info['fps']} fps")
        
        # 轨道信息
        self.inspect_tracks(draft_info['tracks'])
        
        # 素材信息
        self.inspect_materials(draft_info['materials'])
        
        # 其他元数据
        self.inspect_metadata(draft_info['raw_data'])
        
        return True
    
    def inspect_tracks(self, tracks):
        """检查轨道信息"""
        self.print_section("轨道信息")
        
        if not tracks:
            print("❌ 没有找到轨道信息")
            return
        
        print(f"轨道总数: {len(tracks)}")
        
        # 按类型统计轨道
        track_types = {}
        for track in tracks:
            track_type = track.get('type', 'unknown')
            track_types[track_type] = track_types.get(track_type, 0) + 1
        
        print("轨道类型统计:")
        for track_type, count in track_types.items():
            print(f"  {track_type}: {count} 条")
        
        # 详细轨道信息
        for i, track in enumerate(tracks):
            track_type = track.get('type', 'unknown')
            track_id = track.get('id', 'N/A')
            segments = track.get('segments', [])
            
            self.print_subsection(f"轨道 {i+1}: {track_type}")
            print(f"ID: {track_id}")
            print(f"属性: {track.get('attribute', 'N/A')}")
            print(f"标志: {track.get('flag', 'N/A')}")
            print(f"片段数: {len(segments)}")
            
            # 片段信息
            if segments:
                print("片段详情:")
                for j, segment in enumerate(segments):
                    self.inspect_segment(j+1, segment, track_type)
    
    def inspect_segment(self, index, segment, track_type):
        """检查片段信息"""
        segment_id = segment.get('id', 'N/A')
        material_id = segment.get('material_id', 'N/A')
        
        # 时间范围
        source_timerange = segment.get('source_timerange', {})
        target_timerange = segment.get('target_timerange', {})
        
        source_start = source_timerange.get('start', 0) / 1000000
        source_duration = source_timerange.get('duration', 0) / 1000000
        target_start = target_timerange.get('start', 0) / 1000000
        target_duration = target_timerange.get('duration', 0) / 1000000
        
        print(f"    片段 {index}:")
        print(f"      ID: {segment_id}")
        print(f"      素材ID: {material_id}")
        print(f"      源时间: {source_start:.2f}s - {source_start + source_duration:.2f}s (时长: {source_duration:.2f}s)")
        print(f"      目标时间: {target_start:.2f}s - {target_start + target_duration:.2f}s (时长: {target_duration:.2f}s)")
        print(f"      速度: {segment.get('speed', 1.0)}x")
        print(f"      可见: {'是' if segment.get('visible', True) else '否'}")
        
        # 特定类型的额外信息
        if track_type == 'audio':
            volume = segment.get('volume', 1.0)
            print(f"      音量: {volume:.2f} ({volume * 100:.0f}%)")
            
        elif track_type == 'video':
            clip = segment.get('clip', {})
            transform = clip.get('transform', {})
            scale = clip.get('scale', {})
            print(f"      位置: x={transform.get('x', 0):.3f}, y={transform.get('y', 0):.3f}")
            print(f"      缩放: x={scale.get('x', 1):.3f}, y={scale.get('y', 1):.3f}")
            print(f"      透明度: {clip.get('alpha', 1.0):.2f}")
            
        elif track_type == 'text':
            print(f"      文本片段")
        
        # 特效和滤镜
        extra_refs = segment.get('extra_material_refs', [])
        if extra_refs:
            print(f"      额外素材引用: {len(extra_refs)} 个")
    
    def inspect_materials(self, materials):
        """检查素材信息"""
        self.print_section("素材信息")
        
        if not materials:
            print("❌ 没有找到素材信息")
            return
        
        total_materials = sum(len(material_list) for material_list in materials.values())
        print(f"素材总数: {total_materials}")
        
        # 按类型展示素材
        for material_type, material_list in materials.items():
            if not material_list:
                continue
                
            self.print_subsection(f"{material_type.upper()} 素材 ({len(material_list)} 个)")
            
            for i, material in enumerate(material_list):
                if isinstance(material, dict):
                    self.inspect_material_item(i+1, material, material_type)
    
    def inspect_material_item(self, index, material, material_type):
        """检查单个素材项"""
        material_id = material.get('id', 'N/A')
        material_name = material.get('material_name', material.get('name', 'N/A'))
        path = material.get('path', 'N/A')
        
        print(f"  素材 {index}:")
        print(f"    ID: {material_id}")
        print(f"    名称: {material_name}")
        print(f"    路径: {path}")
        
        # 特定类型的信息
        if material_type in ['videos', 'images']:
            width = material.get('width', 'N/A')
            height = material.get('height', 'N/A')
            print(f"    尺寸: {width} x {height}")
            
        if material_type in ['videos', 'audios']:
            duration = material.get('duration', 0)
            duration_sec = duration / 1000000 if duration else 0
            print(f"    时长: {duration_sec:.2f}s ({duration} 微秒)")
        
        if material_type == 'texts':
            text_content = material.get('text', 'N/A')
            font_title = material.get('font_title', 'N/A')
            font_size = material.get('font_size', 'N/A')
            text_color = material.get('text_color', 'N/A')
            print(f"    内容: {text_content[:50]}{'...' if len(text_content) > 50 else ''}")
            print(f"    字体: {font_title}")
            print(f"    大小: {font_size}")
            print(f"    颜色: {text_color}")
        
        # 资源ID（用于特效、贴纸等）
        resource_id = material.get('resource_id', '')
        if resource_id:
            print(f"    资源ID: {resource_id}")
    
    def inspect_metadata(self, raw_data):
        """检查其他元数据"""
        self.print_section("其他元数据")
        
        # 特效
        effects = raw_data.get('effects', [])
        if effects:
            print(f"特效数量: {len(effects)}")
            for i, effect in enumerate(effects[:5]):  # 只显示前5个
                effect_id = effect.get('id', 'N/A')
                effect_type = effect.get('type', 'N/A')
                print(f"  特效 {i+1}: {effect_type} (ID: {effect_id})")
            if len(effects) > 5:
                print(f"  ... 还有 {len(effects) - 5} 个特效")
        
        # 转场
        transitions = raw_data.get('transitions', [])
        if transitions:
            print(f"转场数量: {len(transitions)}")
        
        # 滤镜
        filters = raw_data.get('filters', [])
        if filters:
            print(f"滤镜数量: {len(filters)}")
        
        # 贴纸
        stickers = raw_data.get('stickers', [])
        if stickers:
            print(f"贴纸数量: {len(stickers)}")
        
        # 速度控制
        speeds = raw_data.get('speeds', [])
        if speeds:
            print(f"速度控制数量: {len(speeds)}")
            for i, speed in enumerate(speeds[:3]):  # 只显示前3个
                speed_value = speed.get('speed', 'N/A')
                speed_id = speed.get('id', 'N/A')
                print(f"  速度 {i+1}: {speed_value}x (ID: {speed_id})")
        
        # 其他关键字段
        interesting_fields = [
            'keyframe_graph_list', 'relation_graph', 'draft_fold_path',
            'draft_id', 'draft_name_rename_to', 'platform'
        ]
        
        for field in interesting_fields:
            if field in raw_data:
                value = raw_data[field]
                if isinstance(value, (list, dict)):
                    print(f"{field}: {type(value).__name__} (长度: {len(value)})")
                else:
                    print(f"{field}: {value}")
    
    def inspect_material_usage(self, draft_name):
        """分析素材使用情况"""
        self.print_header(f"素材使用分析: {draft_name}")
        
        draft_info = self.load_draft_info_from_file(draft_name)
        if not draft_info:
            print("❌ 无法加载草稿信息")
            return False
        
        materials = draft_info['materials']
        tracks = draft_info['tracks']
        
        # 创建素材ID到素材信息的映射
        material_map = {}
        for material_type, material_list in materials.items():
            for material in material_list:
                if isinstance(material, dict):
                    material_id = material.get('id')
                    if material_id:
                        material_map[material_id] = {
                            'type': material_type,
                            'name': material.get('material_name', material.get('name', 'N/A')),
                            'info': material
                        }
        
        # 分析素材使用情况
        material_usage = {}
        for track in tracks:
            track_type = track.get('type', 'unknown')
            segments = track.get('segments', [])
            
            for segment in segments:
                material_id = segment.get('material_id')
                if material_id and material_id in material_map:
                    if material_id not in material_usage:
                        material_usage[material_id] = {
                            'material': material_map[material_id],
                            'usage_count': 0,
                            'total_duration': 0,
                            'segments': []
                        }
                    
                    # 计算使用时长
                    target_timerange = segment.get('target_timerange', {})
                    duration = target_timerange.get('duration', 0)
                    
                    material_usage[material_id]['usage_count'] += 1
                    material_usage[material_id]['total_duration'] += duration
                    material_usage[material_id]['segments'].append({
                        'track_type': track_type,
                        'segment_id': segment.get('id'),
                        'duration': duration
                    })
        
        # 显示使用情况
        self.print_section("素材使用统计")
        print(f"总素材数: {len(material_map)}")
        print(f"已使用素材数: {len(material_usage)}")
        print(f"未使用素材数: {len(material_map) - len(material_usage)}")
        
        # 已使用素材详情
        if material_usage:
            self.print_subsection("已使用素材详情")
            for material_id, usage in material_usage.items():
                material = usage['material']
                total_duration_sec = usage['total_duration'] / 1000000
                
                print(f"素材: {material['name']} ({material['type']})")
                print(f"  使用次数: {usage['usage_count']}")
                print(f"  总使用时长: {total_duration_sec:.2f}s")
                print(f"  片段分布: {', '.join(set(seg['track_type'] for seg in usage['segments']))}")
        
        # 未使用素材
        unused_materials = set(material_map.keys()) - set(material_usage.keys())
        if unused_materials:
            self.print_subsection("未使用素材")
            for material_id in unused_materials:
                material = material_map[material_id]
                print(f"  {material['name']} ({material['type']})")
        
        return True
    
    def save_inspection_report(self, draft_name, output_file=None):
        """保存检查报告到文件"""
        if not output_file:
            output_file = f"draft_inspection_{draft_name}.txt"
        
        # 重定向输出到文件
        import sys
        original_stdout = sys.stdout
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                sys.stdout = f
                self.inspect_draft_details(draft_name)
                self.inspect_material_usage(draft_name)
            
            sys.stdout = original_stdout
            print(f"✅ 检查报告已保存到: {output_file}")
            return True
            
        except Exception as e:
            sys.stdout = original_stdout
            print(f"❌ 保存报告失败: {e}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='草稿元素信息查看工具')
    parser.add_argument('--draft-folder', '-d', help='草稿文件夹路径')
    parser.add_argument('--draft-name', '-n', help='要检查的草稿名称')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有草稿')
    parser.add_argument('--usage', '-u', action='store_true', help='分析素材使用情况')
    parser.add_argument('--save', '-s', help='保存检查报告到文件')
    
    args = parser.parse_args()
    
    # 创建检查器
    inspector = DraftInspector()
    
    # 设置草稿文件夹
    if not inspector.setup_draft_folder(args.draft_folder):
        return
    
    # 列出草稿
    if args.list or not args.draft_name:
        drafts = inspector.list_drafts()
        if not args.draft_name and drafts:
            print("\n💡 使用 --draft-name 参数指定要检查的草稿")
            print("   例如: python inspect_draft.py --draft-name '草稿名称'")
        return
    
    # 检查特定草稿
    if args.draft_name:
        if args.save:
            inspector.save_inspection_report(args.draft_name, args.save)
        else:
            inspector.inspect_draft_details(args.draft_name)
            
            if args.usage:
                inspector.inspect_material_usage(args.draft_name)


if __name__ == "__main__":
    main()