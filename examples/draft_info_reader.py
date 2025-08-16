#!/usr/bin/env python3
"""
新版剪映草稿信息读取器
支持从 draft_info.json 读取草稿信息
"""

import json
import os
from typing import Dict, Any, Optional


class DraftInfoReader:
    """新版剪映草稿信息读取器"""
    
    def __init__(self, draft_folder_path: str, draft_name: str):
        self.draft_folder_path = draft_folder_path
        self.draft_name = draft_name
        self.draft_path = os.path.join(draft_folder_path, draft_name)
        self.draft_info_path = os.path.join(self.draft_path, "draft_info.json")
        self._draft_info = None
    
    def load_draft_info(self) -> Optional[Dict[str, Any]]:
        """加载草稿信息"""
        try:
            if os.path.exists(self.draft_info_path):
                with open(self.draft_info_path, 'r', encoding='utf-8') as f:
                    self._draft_info = json.load(f)
                return self._draft_info
            else:
                print(f"警告: draft_info.json 不存在: {self.draft_info_path}")
                return None
        except Exception as e:
            print(f"读取 draft_info.json 失败: {e}")
            return None
    
    def get_canvas_config(self) -> Optional[Dict[str, Any]]:
        """获取画布配置"""
        if not self._draft_info:
            self.load_draft_info()
        
        if self._draft_info:
            return self._draft_info.get('canvas_config')
        return None
    
    def get_duration(self) -> Optional[int]:
        """获取时长（微秒）"""
        if not self._draft_info:
            self.load_draft_info()
        
        if self._draft_info:
            return self._draft_info.get('duration')
        return None
    
    def get_fps(self) -> Optional[float]:
        """获取帧率"""
        if not self._draft_info:
            self.load_draft_info()
        
        if self._draft_info:
            return self._draft_info.get('fps')
        return None
    
    def get_tracks_info(self) -> Dict[str, int]:
        """获取轨道信息统计"""
        if not self._draft_info:
            self.load_draft_info()
        
        track_stats = {}
        if self._draft_info and 'tracks' in self._draft_info:
            tracks = self._draft_info['tracks']
            for track in tracks:
                track_type = track.get('type', 'unknown')
                if track_type not in track_stats:
                    track_stats[track_type] = 0
                track_stats[track_type] += 1
        
        return track_stats
    
    def get_materials_info(self) -> Dict[str, int]:
        """获取素材信息统计"""
        if not self._draft_info:
            self.load_draft_info()
        
        material_stats = {}
        if self._draft_info and 'materials' in self._draft_info:
            materials = self._draft_info['materials']
            for material_type, material_list in materials.items():
                if isinstance(material_list, list) and material_list:
                    material_stats[material_type] = len(material_list)
        
        return material_stats
    
    def get_segments_count(self) -> int:
        """获取片段总数"""
        if not self._draft_info:
            self.load_draft_info()
        
        segment_count = 0
        if self._draft_info and 'tracks' in self._draft_info:
            tracks = self._draft_info['tracks']
            for track in tracks:
                segments = track.get('segments', [])
                segment_count += len(segments)
        
        return segment_count
    
    def get_basic_info(self) -> Dict[str, Any]:
        """获取基本信息摘要"""
        canvas = self.get_canvas_config()
        duration = self.get_duration()
        fps = self.get_fps()
        tracks = self.get_tracks_info()
        materials = self.get_materials_info()
        segments = self.get_segments_count()
        
        return {
            'draft_name': self.draft_name,
            'canvas_config': canvas,
            'duration': duration,
            'duration_seconds': duration / 1000000 if duration else None,
            'fps': fps,
            'tracks': tracks,
            'materials': materials,
            'total_segments': segments,
            'draft_path': self.draft_path
        }
    
    def print_info(self):
        """打印草稿信息"""
        info = self.get_basic_info()
        
        print(f"草稿名称: {info['draft_name']}")
        
        if info['canvas_config']:
            canvas = info['canvas_config']
            print(f"分辨率: {canvas.get('width', '?')}x{canvas.get('height', '?')}")
            print(f"宽高比: {canvas.get('ratio', '?')}")
        
        if info['duration_seconds']:
            print(f"时长: {info['duration_seconds']:.2f}秒")
        
        if info['fps']:
            print(f"帧率: {info['fps']} fps")
        
        if info['tracks']:
            print(f"轨道统计:")
            for track_type, count in info['tracks'].items():
                print(f"  {track_type}: {count}条轨道")
        
        if info['materials']:
            print(f"素材统计:")
            for material_type, count in info['materials'].items():
                if count > 0:
                    print(f"  {material_type}: {count}个")
        
        if info['total_segments']:
            print(f"总片段数: {info['total_segments']}")


def read_draft_info(draft_folder_path: str, draft_name: str) -> Optional[Dict[str, Any]]:
    """便捷函数：读取草稿信息"""
    reader = DraftInfoReader(draft_folder_path, draft_name)
    return reader.get_basic_info()


def main():
    """测试函数"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python draft_info_reader.py <草稿名称> [草稿文件夹路径]")
        print("示例: python draft_info_reader.py '阳章老师模版'")
        return
    
    draft_name = sys.argv[1]
    draft_folder_path = sys.argv[2] if len(sys.argv) > 2 else "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
    
    print(f"=== 草稿信息读取器 ===")
    print(f"草稿文件夹: {draft_folder_path}")
    print(f"草稿名称: {draft_name}")
    print()
    
    reader = DraftInfoReader(draft_folder_path, draft_name)
    
    if not os.path.exists(reader.draft_path):
        print(f"错误: 草稿不存在: {reader.draft_path}")
        return
    
    if not os.path.exists(reader.draft_info_path):
        print(f"错误: draft_info.json 不存在: {reader.draft_info_path}")
        return
    
    reader.print_info()


if __name__ == "__main__":
    main()