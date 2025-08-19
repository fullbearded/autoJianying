#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接从剪映的 draft_info.json 文件中提取文本内容
适用于剪映6.0+版本的草稿格式
"""

import json
import sys
import os
from typing import List, Dict, Any, Optional


def format_time(microseconds: Optional[int]) -> str:
    """
    将微秒时间格式化为可读字符串
    
    Args:
        microseconds: 微秒时间
        
    Returns:
        格式化的时间字符串
    """
    if microseconds is None:
        return "未知"
    
    seconds = microseconds / 1_000_000
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    else:
        return f"{minutes:02d}:{secs:06.3f}"


def extract_text_from_segment(segment: Dict[str, Any], materials: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    从片段数据中提取文本信息
    
    Args:
        segment: 片段数据
        materials: 素材数据
        
    Returns:
        文本信息字典或None
    """
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
                'font_id': text_material.get("font_id", ""),
                'font_name': text_material.get("font_name", ""),
                'font_path': text_material.get("font_path", ""),
                'font_size': text_material.get("font_size", ""),
                'text_color': text_material.get("text_color", ""),
                'start_time': (segment.get("target_timerange") or {}).get("start", 0),
                'duration': (segment.get("target_timerange") or {}).get("duration", 0),
                'source_start': (segment.get("source_timerange") or {}).get("start", 0),
                'source_duration': (segment.get("source_timerange") or {}).get("duration", 0),
                'segment_id': segment.get("id", ""),
                'visible': segment.get("visible", True),
                'alpha': (segment.get("clip") or {}).get("alpha", 1.0),
                'transform': (segment.get("clip") or {}).get("transform", {}),
                'scale': (segment.get("clip") or {}).get("scale", {}),
                'rotation': (segment.get("clip") or {}).get("rotation", 0),
            }
            
            # 计算结束时间
            text_info['end_time'] = text_info['start_time'] + text_info['duration']
            
            # 格式化时间字符串
            text_info['start_time_str'] = format_time(text_info['start_time'])
            text_info['duration_str'] = format_time(text_info['duration'])
            text_info['end_time_str'] = format_time(text_info['end_time'])
            
            # 提取文本样式信息
            text_style = text_material.get("style", {})
            if text_style:
                style_info = {}
                if "size" in text_style:
                    style_info["size"] = text_style["size"]
                if "color" in text_style:
                    style_info["color"] = text_style["color"]
                if "align" in text_style:
                    style_info["align"] = text_style["align"]
                if "line_spacing" in text_style:
                    style_info["line_spacing"] = text_style["line_spacing"]
                if "letter_spacing" in text_style:
                    style_info["letter_spacing"] = text_style["letter_spacing"]
                
                if style_info:
                    text_info['style'] = style_info
            
            # 提取边框信息
            text_border = text_material.get("border", {})
            if text_border:
                text_info['border'] = text_border
            
            # 提取背景信息
            text_background = text_material.get("background", {})
            if text_background:
                text_info['background'] = text_background
            
            return text_info
    
    return None


def extract_text_content_from_draft_info(draft_folder_path: str, draft_name: str) -> Dict[str, Any]:
    """
    从剪映的 draft_info.json 文件中提取所有文本内容
    
    Args:
        draft_folder_path: 草稿文件夹路径
        draft_name: 草稿名称
        
    Returns:
        包含文本内容的字典
    """
    draft_info_path = os.path.join(draft_folder_path, draft_name, "draft_info.json")
    
    if not os.path.exists(draft_info_path):
        raise Exception(f"草稿文件不存在: {draft_info_path}")
    
    try:
        # 读取draft_info.json文件
        with open(draft_info_path, 'r', encoding='utf-8') as f:
            draft_data = json.load(f)
        
        result = {
            'draft_name': draft_name,
            'draft_path': draft_info_path,
            'text_tracks': [],
            'total_text_segments': 0,
            'duration': draft_data.get('duration', 0),
            'fps': draft_data.get('fps', 30.0),
            'canvas_config': draft_data.get('canvas_config', {}),
            'materials_count': {}
        }
        
        # 获取素材信息
        materials = draft_data.get('materials', {})
        
        # 统计素材数量
        for material_type, material_list in materials.items():
            if isinstance(material_list, list):
                result['materials_count'][material_type] = len(material_list)
        
        # 获取轨道信息
        tracks = draft_data.get('tracks', [])
        
        # 基本信息
        print(f"找到 {len(tracks)} 个轨道，其中包含 {len(materials.get('texts', []))} 个文本素材")
        
        text_track_index = 0
        for track_index, track in enumerate(tracks):
            if not track:
                continue
            # 检查是否为文本轨道
            track_type = track.get('type', '')
            if track_type == 'text':
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
                    
                    try:
                        text_info = extract_text_from_segment(segment, materials)
                        if text_info:
                            text_info['segment_index'] = segment_index
                            text_info['track_index'] = track_index
                            text_info['text_track_index'] = text_track_index
                            track_info['segments'].append(text_info)
                            result['total_text_segments'] += 1
                    except Exception as e:
                        print(f"警告: 处理文本轨道 {track_index} 的片段 {segment_index} 时出错: {str(e)}")
                        continue
                
                result['text_tracks'].append(track_info)
                text_track_index += 1
        
        result['text_track_count'] = text_track_index
        return result
        
    except json.JSONDecodeError as e:
        raise Exception(f"解析JSON文件失败: {str(e)}")
    except Exception as e:
        raise Exception(f"提取文本内容失败: {str(e)}")


def print_text_content(content_data: Dict[str, Any]):
    """
    打印文本内容到控制台
    
    Args:
        content_data: extract_text_content_from_draft_info返回的数据
    """
    print(f"=" * 60)
    print(f"草稿名称: {content_data['draft_name']}")
    print(f"草稿路径: {content_data['draft_path']}")
    print(f"草稿总时长: {format_time(content_data['duration'])}")
    print(f"帧率: {content_data['fps']} fps")
    
    canvas = content_data['canvas_config']
    if canvas:
        print(f"画布尺寸: {canvas.get('width', 'N/A')} x {canvas.get('height', 'N/A')}")
        print(f"画布比例: {canvas.get('ratio', 'N/A')}")
    
    print(f"文本轨道数量: {content_data['text_track_count']}")
    print(f"文本片段总数: {content_data['total_text_segments']}")
    
    # 打印素材统计
    materials_count = content_data['materials_count']
    if materials_count:
        print(f"\n素材统计:")
        for material_type, count in materials_count.items():
            if count > 0:
                print(f"  {material_type}: {count}")
    
    print(f"=" * 60)
    
    if content_data['text_track_count'] == 0:
        print("该草稿中没有找到文本轨道")
        return
    
    for track in content_data['text_tracks']:
        print(f"\n【{track['track_name']}】(轨道索引: {track['track_index']})")
        print(f"轨道ID: {track['track_id']}")
        print(f"片段数量: {len(track['segments'])}")
        print("-" * 40)
        
        if not track['segments']:
            print("  该轨道没有文本片段")
            continue
        
        for segment in track['segments']:
            print(f"  片段 {segment['segment_index'] + 1}:")
            print(f"    文本内容: \"{segment['text']}\"")
            print(f"    时间范围: {segment['start_time_str']} - {segment['end_time_str']}")
            print(f"    持续时间: {segment['duration_str']}")
            
            if segment.get('font_name'):
                print(f"    字体名称: {segment['font_name']}")
            
            if segment.get('font_id'):
                print(f"    字体ID: {segment['font_id']}")
            
            if segment.get('font_size'):
                print(f"    字体大小: {segment['font_size']}")
            
            if segment.get('text_color'):
                print(f"    文字颜色: {segment['text_color']}")
            
            if 'style' in segment:
                style = segment['style']
                style_parts = []
                if 'size' in style:
                    style_parts.append(f"大小:{style['size']}")
                if 'color' in style:
                    style_parts.append(f"颜色:{style['color']}")
                if 'align' in style:
                    style_parts.append(f"对齐:{style['align']}")
                if 'line_spacing' in style:
                    style_parts.append(f"行距:{style['line_spacing']}")
                if 'letter_spacing' in style:
                    style_parts.append(f"字距:{style['letter_spacing']}")
                if style_parts:
                    print(f"    样式: {', '.join(style_parts)}")
            
            if not segment.get('visible', True):
                print(f"    可见性: 隐藏")
            
            if segment.get('alpha', 1.0) != 1.0:
                print(f"    透明度: {segment['alpha']}")
            
            transform = segment.get('transform', {})
            if transform and (transform.get('x') != 0 or transform.get('y') != 0):
                print(f"    位置偏移: x={transform.get('x', 0)}, y={transform.get('y', 0)}")
            
            scale = segment.get('scale', {})
            if scale and (scale.get('x') != 1.0 or scale.get('y') != 1.0):
                print(f"    缩放: x={scale.get('x', 1.0)}, y={scale.get('y', 1.0)}")
            
            if segment.get('rotation', 0) != 0:
                print(f"    旋转: {segment['rotation']}度")
            
            print()


def save_to_file(content_data: Dict[str, Any], output_file: str):
    """
    将文本内容保存到文件
    
    Args:
        content_data: extract_text_content_from_draft_info返回的数据
        output_file: 输出文件路径
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"草稿名称: {content_data['draft_name']}\n")
            f.write(f"草稿总时长: {format_time(content_data['duration'])}\n")
            f.write(f"文本轨道数量: {content_data['text_track_count']}\n")
            f.write(f"文本片段总数: {content_data['total_text_segments']}\n")
            f.write("=" * 60 + "\n\n")
            
            for track in content_data['text_tracks']:
                f.write(f"【{track['track_name']}】\n")
                
                for segment in track['segments']:
                    f.write(f"片段 {segment['segment_index'] + 1}: \"{segment['text']}\"\n")
                    f.write(f"时间: {segment['start_time_str']} - {segment['end_time_str']} (持续: {segment['duration_str']})\n")
                    
                    if segment.get('font_name'):
                        f.write(f"字体: {segment['font_name']}\n")
                    
                    if 'style' in segment:
                        style = segment['style']
                        style_parts = []
                        if 'size' in style:
                            style_parts.append(f"大小:{style['size']}")
                        if 'color' in style:
                            style_parts.append(f"颜色:{style['color']}")
                        if style_parts:
                            f.write(f"样式: {', '.join(style_parts)}\n")
                    
                    f.write("\n")
                
                f.write("-" * 40 + "\n\n")
        
        print(f"文本内容已保存到: {output_file}")
        
    except Exception as e:
        print(f"保存文件失败: {str(e)}")


def main():
    """
    主函数
    """
    if len(sys.argv) < 3:
        print("使用方法:")
        print(f"  {sys.argv[0]} <草稿文件夹路径> <草稿名称> [输出文件路径]")
        print("\n示例:")
        print(f"  {sys.argv[0]} \"C:/Users/用户名/AppData/Local/JianyingPro/User Data/Projects/com.lveditor.draft\" \"我的草稿\"")
        print(f"  {sys.argv[0]} \"C:/Users/用户名/AppData/Local/JianyingPro/User Data/Projects/com.lveditor.draft\" \"我的草稿\" \"output.txt\"")
        print("\n注意:")
        print("  此脚本直接解析剪映的 draft_info.json 文件，适用于剪映6.0+版本")
        sys.exit(1)
    
    draft_folder_path = sys.argv[1]
    draft_name = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    # 检查草稿文件夹是否存在
    if not os.path.exists(draft_folder_path):
        print(f"错误: 草稿文件夹不存在: {draft_folder_path}")
        sys.exit(1)
    
    try:
        print("正在提取文本内容...")
        content_data = extract_text_content_from_draft_info(draft_folder_path, draft_name)
        
        # 打印到控制台
        print_text_content(content_data)
        
        # 保存到文件（如果指定了输出文件）
        if output_file:
            save_to_file(content_data, output_file)
        
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()