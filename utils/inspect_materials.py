#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细分析草稿中的材料文件
"""

import os
from pathlib import Path

def analyze_materials(draft_path):
    """分析材料文件夹"""
    materials_path = os.path.join(draft_path, 'materials')
    
    if not os.path.exists(materials_path):
        print("❌ 没有找到 materials 文件夹")
        return
    
    print("📁 Materials 文件夹详细信息:")
    print("=" * 50)
    
    for root, dirs, files in os.walk(materials_path):
        level = root.replace(materials_path, '').count(os.sep)
        indent = ' ' * 2 * level
        relative_path = os.path.relpath(root, materials_path)
        
        if relative_path == '.':
            print(f"{indent}materials/")
        else:
            print(f"{indent}{os.path.basename(root)}/")
        
        # 显示文件信息
        sub_indent = ' ' * 2 * (level + 1)
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            
            # 转换文件大小为可读格式
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            
            # 获取文件扩展名
            ext = Path(file).suffix.lower()
            
            print(f"{sub_indent}📄 {file} ({size_str}) {ext}")

def analyze_resources(draft_path):
    """分析资源文件夹"""
    resources_path = os.path.join(draft_path, 'Resources')
    
    if not os.path.exists(resources_path):
        print("❌ 没有找到 Resources 文件夹")
        return
    
    print("\n📁 Resources 文件夹详细信息:")
    print("=" * 50)
    
    for root, dirs, files in os.walk(resources_path):
        level = root.replace(resources_path, '').count(os.sep)
        indent = ' ' * 2 * level
        relative_path = os.path.relpath(root, resources_path)
        
        if relative_path == '.':
            print(f"{indent}Resources/")
        else:
            print(f"{indent}{os.path.basename(root)}/")
        
        # 只显示文件数量，不显示具体文件（避免输出过长）
        if files:
            sub_indent = ' ' * 2 * (level + 1)
            print(f"{sub_indent}📁 {len(files)} 个文件")
            
            # 统计文件类型
            extensions = {}
            total_size = 0
            for file in files:
                ext = Path(file).suffix.lower()
                extensions[ext] = extensions.get(ext, 0) + 1
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
            
            # 显示统计信息
            if total_size < 1024 * 1024:
                size_str = f"{total_size / 1024:.1f} KB"
            else:
                size_str = f"{total_size / (1024 * 1024):.1f} MB"
            
            print(f"{sub_indent}📊 总大小: {size_str}")
            
            for ext, count in extensions.items():
                if ext:
                    print(f"{sub_indent}   {ext}: {count} 个")

def main():
    # 剪映草稿文件夹路径
    draft_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
    draft_name = "4翰墨书院模版"
    full_draft_path = os.path.join(draft_path, draft_name)
    
    try:
        if not os.path.exists(full_draft_path):
            print(f"错误: 找不到名为 '{draft_name}' 的草稿")
            return
        
        print(f"正在分析草稿材料: {draft_name}")
        print("=" * 60)
        
        # 分析材料文件夹
        analyze_materials(full_draft_path)
        
        # 分析资源文件夹
        analyze_resources(full_draft_path)
        
        print("\n✅ 材料分析完成")
        
    except Exception as e:
        print(f"发生错误: {e}")
        print(f"错误类型: {type(e).__name__}")

if __name__ == "__main__":
    main()