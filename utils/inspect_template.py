#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查指定模板草稿的内容
"""

import os
from config_manager import ConfigManager
from inspect_complex_draft import analyze_draft_structure, analyze_draft_info, analyze_subdraft
from inspect_materials import analyze_materials, analyze_resources

def inspect_template_from_config():
    """从配置文件中读取模板名称并检查"""
    
    # 读取配置
    config_manager = ConfigManager()
    template_name = config_manager.get("template.name", "")
    draft_folder_path = config_manager.get("paths.draft_folder", "")
    
    if not template_name:
        print("❌ 配置文件中未设置模板名称")
        return
    
    if not draft_folder_path:
        print("❌ 配置文件中未设置草稿文件夹路径")
        return
    
    full_draft_path = os.path.join(draft_folder_path, template_name)
    
    print(f"🎬 检查模板草稿: {template_name}")
    print("=" * 60)
    print(f"草稿路径: {full_draft_path}")
    
    if not os.path.exists(full_draft_path):
        print(f"❌ 模板草稿不存在: {template_name}")
        return
    
    try:
        # 分析文件结构
        print(f"\n📁 文件结构分析:")
        print("-" * 40)
        subdrafts = analyze_draft_structure(full_draft_path)
        
        # 分析基本信息
        print(f"\n📋 基本信息:")
        print("-" * 40)
        analyze_draft_info(full_draft_path)
        
        # 分析材料文件
        print(f"\n📦 材料文件分析:")
        print("-" * 40)
        analyze_materials(full_draft_path)
        
        # 分析资源文件
        print(f"\n📂 资源文件分析:")
        print("-" * 40)
        analyze_resources(full_draft_path)
        
        # 分析子草稿（如果存在）
        if subdrafts:
            print(f"\n🎭 子草稿分析 (前3个):")
            print("-" * 40)
            
            for i, subdraft_id in enumerate(subdrafts[:3]):
                print(f"\n子草稿 {i+1} ({subdraft_id[:8]}...):")
                info = analyze_subdraft(full_draft_path, subdraft_id)
                if info:
                    print(f"  时长: {info['duration'] / 1000000:.2f} 秒")
                    print(f"  轨道: 视频{info['tracks']['video_tracks']} | 音频{info['tracks']['audio_tracks']} | 文本{info['tracks']['text_tracks']}")
                    print(f"  片段: 总计{info['tracks']['total_segments']}个")
                    print(f"  素材: 视频{info['materials']['videos']} | 音频{info['materials']['audios']} | 文本{info['materials']['texts']}")
                else:
                    print("  无法读取内容")
            
            if len(subdrafts) > 3:
                print(f"\n... 还有 {len(subdrafts) - 3} 个子草稿")
        
        print(f"\n✅ 模板 '{template_name}' 分析完成")
        
        # 总结模板特点
        print(f"\n📊 模板特点总结:")
        print("-" * 40)
        
        # 检查是否有主draft_content.json
        main_draft = os.path.join(full_draft_path, "draft_content.json")
        if os.path.exists(main_draft):
            print("✅ 标准草稿结构（有主draft_content.json）")
            print("   适用于: 标准模板模式")
        else:
            print("⚠️  复合草稿结构（无主draft_content.json）")
            print("   适用于: 复杂模板，可能需要特殊处理")
        
        # 检查材料文件夹
        materials_path = os.path.join(full_draft_path, "materials")
        if os.path.exists(materials_path):
            video_files = []
            audio_files = []
            
            # 统计视频文件
            video_path = os.path.join(materials_path, "video")
            if os.path.exists(video_path):
                video_files = [f for f in os.listdir(video_path) if f.lower().endswith(('.mp4', '.avi', '.mov'))]
            
            # 统计音频文件
            audio_path = os.path.join(materials_path, "audio")
            if os.path.exists(audio_path):
                audio_files = [f for f in os.listdir(audio_path) if f.lower().endswith(('.mp3', '.wav', '.m4a'))]
            
            print(f"📹 包含视频素材: {len(video_files)} 个")
            print(f"🎵 包含音频素材: {len(audio_files)} 个")
        
        # 建议使用方式
        print(f"\n💡 使用建议:")
        print("-" * 40)
        print("1. 确保配置文件中模板名称正确")
        print("2. 根据模板中的素材类型准备替换素材")
        print("3. 使用config_batch_replace.py进行批量替换")
        
        if subdrafts:
            print("4. 此模板为复合结构，可能需要特殊的处理方式")
        
    except Exception as e:
        print(f"❌ 分析模板时出错: {e}")
        print(f"错误类型: {type(e).__name__}")

def main():
    """主函数"""
    inspect_template_from_config()

if __name__ == "__main__":
    main()