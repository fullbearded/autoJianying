#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
读取复合草稿并获取元素信息
"""

import os
import json
import pyJianYingDraft as draft

def read_json_file(file_path):
    """安全读取JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取 {file_path} 失败: {e}")
        return None

def analyze_draft_structure(draft_path):
    """分析草稿文件结构"""
    print(f"📁 草稿文件结构分析:")
    print("-" * 40)
    
    # 检查主要文件
    main_files = [
        'draft_info.json',
        'draft_meta_info.json', 
        'template.json',
        'draft_content.json'
    ]
    
    for file_name in main_files:
        file_path = os.path.join(draft_path, file_name)
        if os.path.exists(file_path):
            print(f"✅ {file_name}")
        else:
            print(f"❌ {file_name}")
    
    # 检查材料文件夹
    materials_path = os.path.join(draft_path, 'materials')
    if os.path.exists(materials_path):
        print(f"✅ materials/ 文件夹")
        for sub_folder in ['video', 'audio']:
            sub_path = os.path.join(materials_path, sub_folder)
            if os.path.exists(sub_path):
                files = os.listdir(sub_path)
                print(f"   - {sub_folder}: {len(files)} 个文件")
    
    # 检查子草稿
    subdraft_path = os.path.join(draft_path, 'subdraft')
    if os.path.exists(subdraft_path):
        subdrafts = os.listdir(subdraft_path)
        print(f"✅ subdraft/ 文件夹: {len(subdrafts)} 个子草稿")
        return subdrafts
    
    return []

def analyze_draft_info(draft_path):
    """分析草稿基本信息"""
    info_file = os.path.join(draft_path, 'draft_info.json')
    template_file = os.path.join(draft_path, 'template.json')
    
    print(f"📋 草稿基本信息:")
    print("-" * 40)
    
    # 读取草稿信息
    if os.path.exists(info_file):
        info_data = read_json_file(info_file)
        if info_data:
            print(f"草稿名称: {info_data.get('draft_name', 'N/A')}")
            print(f"创建时间: {info_data.get('tm_create', 'N/A')}")
            print(f"修改时间: {info_data.get('tm_update', 'N/A')}")
    
    # 读取模板信息
    if os.path.exists(template_file):
        template_data = read_json_file(template_file)
        if template_data:
            print(f"模板ID: {template_data.get('template_id', 'N/A')}")
            print(f"模板版本: {template_data.get('version', 'N/A')}")

def analyze_subdraft(draft_path, subdraft_id):
    """分析单个子草稿"""
    subdraft_path = os.path.join(draft_path, 'subdraft', subdraft_id)
    content_file = os.path.join(subdraft_path, 'draft_content.json')
    
    if not os.path.exists(content_file):
        return None
    
    content_data = read_json_file(content_file)
    if not content_data:
        return None
    
    # 分析轨道信息
    tracks = content_data.get('tracks', [])
    track_info = {
        'video_tracks': 0,
        'audio_tracks': 0,
        'text_tracks': 0,
        'total_segments': 0
    }
    
    for track in tracks:
        track_type = track.get('type', '')
        segments = track.get('segments', [])
        track_info['total_segments'] += len(segments)
        
        if track_type == 'video':
            track_info['video_tracks'] += 1
        elif track_type == 'audio':
            track_info['audio_tracks'] += 1
        elif track_type == 'text':
            track_info['text_tracks'] += 1
    
    # 分析素材信息
    materials = content_data.get('materials', {})
    material_info = {
        'videos': len(materials.get('videos', [])),
        'audios': len(materials.get('audios', [])),
        'texts': len(materials.get('texts', []))
    }
    
    return {
        'tracks': track_info,
        'materials': material_info,
        'duration': content_data.get('duration', 0)
    }

def main():
    # 剪映草稿文件夹路径
    draft_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
    draft_name = "4翰墨书院模版"
    full_draft_path = os.path.join(draft_path, draft_name)
    
    try:
        if not os.path.exists(full_draft_path):
            print(f"错误: 找不到名为 '{draft_name}' 的草稿")
            return
        
        print(f"正在分析草稿: {draft_name}")
        print("=" * 60)
        
        # 分析文件结构
        subdrafts = analyze_draft_structure(full_draft_path)
        print()
        
        # 分析基本信息
        analyze_draft_info(full_draft_path)
        print()
        
        # 分析子草稿
        if subdrafts:
            print(f"🎬 子草稿分析 (前5个):")
            print("-" * 40)
            
            for i, subdraft_id in enumerate(subdrafts[:5]):
                print(f"\n子草稿 {i+1} ({subdraft_id[:8]}...):")
                info = analyze_subdraft(full_draft_path, subdraft_id)
                if info:
                    print(f"  时长: {info['duration'] / 1000000:.2f} 秒")
                    print(f"  轨道: 视频{info['tracks']['video_tracks']} | 音频{info['tracks']['audio_tracks']} | 文本{info['tracks']['text_tracks']}")
                    print(f"  片段: 总计{info['tracks']['total_segments']}个")
                    print(f"  素材: 视频{info['materials']['videos']} | 音频{info['materials']['audios']} | 文本{info['materials']['texts']}")
                else:
                    print("  无法读取内容")
            
            if len(subdrafts) > 5:
                print(f"\n... 还有 {len(subdrafts) - 5} 个子草稿")
        
        print()
        print("✅ 复合草稿分析完成")
        
    except Exception as e:
        print(f"发生错误: {e}")
        print(f"错误类型: {type(e).__name__}")

if __name__ == "__main__":
    main()