#!/usr/bin/env python3
"""
简化版草稿复制工具
直接指定草稿进行复制，无交互式输入
"""

import os
import sys
import argparse
import time
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pyJianYingDraft as draft


def load_draft_info_from_file(draft_folder_path: str, draft_name: str):
    """从 draft_info.json 文件加载草稿信息"""
    draft_info_path = os.path.join(draft_folder_path, draft_name, "draft_info.json")
    
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
        
        return {
            'draft_name': draft_name,
            'canvas_config': canvas,
            'duration': duration,
            'fps': fps,
            'tracks': tracks_stats,
            'materials': materials_stats
        }
        
    except Exception as e:
        print(f"读取 draft_info.json 失败: {e}")
        return None


def copy_draft(draft_folder_path, source_name, target_name=None):
    """
    复制指定草稿
    
    Args:
        draft_folder_path: 剪映草稿文件夹路径
        source_name: 源草稿名称
        target_name: 目标草稿名称（可选）
    
    Returns:
        bool: 是否成功
    """
    print(f"开始复制草稿: {source_name}")
    
    try:
        # 初始化草稿文件夹管理器
        draft_folder = draft.DraftFolder(draft_folder_path)
        
        # 检查源草稿是否存在
        drafts = draft_folder.list_drafts()
        if source_name not in drafts:
            print(f"错误: 源草稿 '{source_name}' 不存在")
            print("可用的草稿:")
            for draft_name in drafts:
                if not draft_name.startswith('.'):
                    print(f"  - {draft_name}")
            return False
        
        # 生成目标草稿名称
        if not target_name:
            timestamp = int(time.time())
            target_name = f"{source_name}_复制版_{timestamp}"
        
        print(f"目标草稿: {target_name}")
        
        # 执行复制
        try:
            copied_script = draft_folder.duplicate_as_template(source_name, target_name)
            print("✓ 草稿复制API调用完成")
        except Exception as e:
            print(f"⚠ API报错: {e}")
            print("这是正常的，新版剪映使用了加密")
        
        # 检查是否实际创建成功
        time.sleep(1)  # 等待文件系统同步
        updated_drafts = draft_folder.list_drafts()
        
        if target_name in updated_drafts:
            print("✓ 草稿复制成功!")
            print(f"新草稿: {target_name}")
            
            # 尝试读取草稿详细信息
            draft_info = load_draft_info_from_file(draft_folder_path, target_name)
            if draft_info:
                print("✓ 成功读取草稿详细信息:")
                canvas = draft_info['canvas_config']
                if canvas:
                    print(f"  分辨率: {canvas.get('width', '?')}x{canvas.get('height', '?')}")
                if draft_info['duration']:
                    print(f"  时长: {draft_info['duration'] / 1000000:.2f}秒")
                if draft_info['tracks']:
                    track_summary = []
                    for track_type, count in draft_info['tracks'].items():
                        track_summary.append(f"{track_type}:{count}")
                    print(f"  轨道: {', '.join(track_summary)}")
            else:
                print("⚠ 无法读取草稿详细信息")
            
            # 检查草稿文件夹内容
            target_path = os.path.join(draft_folder_path, target_name)
            if os.path.exists(target_path):
                files = os.listdir(target_path)
                print(f"草稿文件夹包含 {len(files)} 个文件")
                key_files = [f for f in files if f.endswith(('.json', '.jpg', '.dat'))]
                if key_files:
                    print("包含关键文件:", ', '.join(key_files[:5]))
            
            return True
        else:
            print("✗ 草稿复制失败")
            return False
            
    except Exception as e:
        print(f"复制过程出错: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="简化版草稿复制工具")
    parser.add_argument("source_draft", help="要复制的源草稿名称")
    parser.add_argument("--draft-folder", 
                       default="/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft",
                       help="剪映草稿文件夹路径")
    parser.add_argument("--target-name", help="目标草稿名称（可选）")
    parser.add_argument("--list", action="store_true", help="列出所有可用草稿")
    
    args = parser.parse_args()
    
    # 检查路径是否存在
    if not os.path.exists(args.draft_folder):
        print(f"错误: 草稿文件夹路径不存在: {args.draft_folder}")
        return
    
    # 如果只是列出草稿
    if args.list:
        try:
            draft_folder = draft.DraftFolder(args.draft_folder)
            drafts = draft_folder.list_drafts()
            filtered_drafts = [d for d in drafts if not d.startswith('.') and not d.startswith('pyJianYingDraft_Demo')]
            
            print(f"找到 {len(filtered_drafts)} 个可用草稿:")
            for i, draft_name in enumerate(filtered_drafts, 1):
                print(f"  {i}. {draft_name}")
        except Exception as e:
            print(f"列出草稿失败: {e}")
        return
    
    # 执行复制
    success = copy_draft(args.draft_folder, args.source_draft, args.target_name)
    if success:
        print("\n✓ 复制完成! 你现在可以在剪映中打开新草稿进行编辑")
    else:
        print("\n✗ 复制失败")
        sys.exit(1)


if __name__ == "__main__":
    main()