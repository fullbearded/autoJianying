#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析阳章老师模版的详细内容
"""

import json
import os

def analyze_yangzhang_template():
    """分析阳章老师模版"""
    
    # 模板路径
    template_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/阳章老师模版"
    draft_info_path = os.path.join(template_path, "draft_info.json")
    
    print("🎬 阳章老师模版详细分析")
    print("=" * 60)
    
    try:
        with open(draft_info_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 基本信息
        print("📋 基本信息:")
        print("-" * 40)
        canvas_config = data.get('canvas_config', {})
        print(f"分辨率: {canvas_config.get('width', 'N/A')} x {canvas_config.get('height', 'N/A')}")
        print(f"画布比例: {canvas_config.get('ratio', 'N/A')}")
        print(f"总时长: {data.get('duration', 0) / 1000000:.2f} 秒")
        print(f"帧率: {data.get('fps', 'N/A')} fps")
        
        # 素材分析
        print(f"\n📦 素材分析:")
        print("-" * 40)
        materials = data.get('materials', {})
        
        # 视频素材
        videos = materials.get('videos', [])
        print(f"视频素材: {len(videos)} 个")
        for i, video in enumerate(videos, 1):
            name = video.get('material_name', 'N/A')
            duration = video.get('duration', 0) / 1000000
            width = video.get('width', 'N/A')
            height = video.get('height', 'N/A')
            path = video.get('path', 'N/A')
            print(f"  {i}. {name}")
            print(f"     时长: {duration:.2f}秒, 分辨率: {width}x{height}")
            print(f"     路径: {path}")
        
        # 音频素材
        audios = materials.get('audios', [])
        print(f"\n音频素材: {len(audios)} 个")
        for i, audio in enumerate(audios, 1):
            name = audio.get('name', 'N/A')
            duration = audio.get('duration', 0) / 1000000
            path = audio.get('path', 'N/A')
            print(f"  {i}. {name}")
            print(f"     时长: {duration:.2f}秒")
            print(f"     路径: {path}")
        
        # 轨道分析
        print(f"\n🎭 轨道结构:")
        print("-" * 40)
        tracks = data.get('tracks', [])
        for i, track in enumerate(tracks):
            track_type = track.get('type', 'unknown')
            segments = track.get('segments', [])
            attribute = track.get('attribute', 0)
            
            print(f"轨道 {i+1}: {track_type} (属性: {attribute})")
            print(f"  片段数量: {len(segments)}")
            
            for j, segment in enumerate(segments):
                target_range = segment.get('target_timerange', {})
                start = target_range.get('start', 0) / 1000000
                duration = target_range.get('duration', 0) / 1000000
                end = start + duration
                speed = segment.get('speed', 1.0)
                
                # 查找对应的素材名称
                material_id = segment.get('material_id', '')
                material_name = "unknown"
                
                # 在视频素材中查找
                for video in videos:
                    if video.get('id') == material_id:
                        material_name = video.get('material_name', 'unknown')
                        break
                
                # 在音频素材中查找
                for audio in audios:
                    if audio.get('id') == material_id:
                        material_name = audio.get('name', 'unknown')
                        break
                
                print(f"    片段 {j+1}: {material_name}")
                print(f"      时间: {start:.2f}s - {end:.2f}s (时长: {duration:.2f}s)")
                print(f"      播放速度: {speed:.2f}x")
        
        # 时间线分析
        print(f"\n⏱️  时间线分析:")
        print("-" * 40)
        
        # 分析每个轨道的时间安排
        print("轨道时间安排:")
        for i, track in enumerate(tracks):
            track_type = track.get('type', 'unknown')
            segments = track.get('segments', [])
            
            if segments:
                total_duration = 0
                for segment in segments:
                    target_range = segment.get('target_timerange', {})
                    duration = target_range.get('duration', 0) / 1000000
                    total_duration = max(total_duration, 
                                       (target_range.get('start', 0) + target_range.get('duration', 0)) / 1000000)
                
                print(f"  {track_type} 轨道 {i+1}: 总长度 {total_duration:.2f}秒")
        
        # 素材路径总结
        print(f"\n📁 素材路径总结:")
        print("-" * 40)
        print("模板中引用的素材文件:")
        all_paths = set()
        
        for video in videos:
            path = video.get('path', '')
            if path:
                filename = os.path.basename(path)
                all_paths.add(filename)
                print(f"  📹 {filename}")
        
        for audio in audios:
            path = audio.get('path', '')
            if path:
                filename = os.path.basename(path)
                all_paths.add(filename)
                print(f"  🎵 {filename}")
        
        # 替换建议
        print(f"\n💡 批量替换建议:")
        print("-" * 40)
        print("基于分析结果，建议配置以下素材文件夹结构:")
        print()
        print("materials/")
        print("├── background/")
        print("│   └── (放入 background.jpg 的替换图片)")
        print("├── part1/")
        print("│   └── (放入 part1.mp4 的替换视频)")
        print("├── part2/")
        print("│   └── (放入 part2.mp4 的替换视频)")
        print("├── part3/")
        print("│   └── (放入 part3.mp4 的替换视频)")
        print("├── voice/")
        print("│   └── (放入 voice.mp3 的替换音频)")
        print("└── music/")
        print("    └── (放入 music.MP3 的替换音频)")
        
        print(f"\n⚙️  推荐配置:")
        print("-" * 40)
        print("• 媒体类型: 混合模式 (图片+视频)")
        print("• 命名方式: 新素材名")
        print("• 时长处理: 加速/减速保持时间线不变")
        print("• 选取模式: 顺序模式")
        
        print(f"\n✅ 模板分析完成!")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")

def main():
    """主函数"""
    analyze_yangzhang_template()

if __name__ == "__main__":
    main()