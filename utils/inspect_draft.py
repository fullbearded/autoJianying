#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
读取草稿并获取元素信息
"""

import pyJianYingDraft as draft

def main():
    # 剪映草稿文件夹路径
    draft_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
    draft_name = "4翰墨书院模版"
    
    try:
        # 初始化草稿文件夹管理器
        draft_folder = draft.DraftFolder(draft_path)
        
        # 检查草稿是否存在
        if not draft_folder.has_draft(draft_name):
            print(f"错误: 找不到名为 '{draft_name}' 的草稿")
            available_drafts = draft_folder.list_drafts()
            print(f"可用草稿: {available_drafts}")
            return
        
        print(f"正在读取草稿: {draft_name}")
        print("=" * 60)
        
        # 加载草稿模板
        script = draft_folder.load_template(draft_name)
        
        # 获取基本信息
        print(f"草稿名称: {draft_name}")
        print(f"草稿时长: {script.duration / draft.SEC:.2f} 秒")
        print()
        
        # 提取素材元数据
        print("📋 提取素材元数据:")
        print("-" * 40)
        script.inspect_material()
        print()
        
        # 获取轨道信息
        print("🎬 轨道信息:")
        print("-" * 40)
        
        # 视频轨道
        try:
            video_tracks = []
            i = 0
            while True:
                try:
                    track = script.get_imported_track(draft.TrackType.video, index=i)
                    video_tracks.append(track)
                    print(f"视频轨道 {i}: {track.segments_count} 个片段")
                    i += 1
                except:
                    break
            print(f"总共 {len(video_tracks)} 个视频轨道")
        except Exception as e:
            print(f"获取视频轨道信息时出错: {e}")
        
        # 音频轨道
        try:
            audio_tracks = []
            i = 0
            while True:
                try:
                    track = script.get_imported_track(draft.TrackType.audio, index=i)
                    audio_tracks.append(track)
                    print(f"音频轨道 {i}: {track.segments_count} 个片段")
                    i += 1
                except:
                    break
            print(f"总共 {len(audio_tracks)} 个音频轨道")
        except Exception as e:
            print(f"获取音频轨道信息时出错: {e}")
        
        # 文本轨道
        try:
            text_tracks = []
            i = 0
            while True:
                try:
                    track = script.get_imported_track(draft.TrackType.text, index=i)
                    text_tracks.append(track)
                    print(f"文本轨道 {i}: {track.segments_count} 个片段")
                    i += 1
                except:
                    break
            print(f"总共 {len(text_tracks)} 个文本轨道")
        except Exception as e:
            print(f"获取文本轨道信息时出错: {e}")
        
        print()
        print("✅ 草稿信息获取完成")
        
    except FileNotFoundError as e:
        print(f"错误: {e}")
        print("请检查草稿文件夹路径是否正确")
    except Exception as e:
        print(f"发生错误: {e}")
        print(f"错误类型: {type(e).__name__}")

if __name__ == "__main__":
    main()