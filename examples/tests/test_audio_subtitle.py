#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试音频和字幕添加功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pyJianYingDraft as draft


def test_audio_subtitle_api():
    """测试音频和字幕API功能"""
    
    print("🧪 测试音频和字幕API功能")
    print("=" * 50)
    
    # 设置草稿文件夹路径
    draft_folder_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
    
    if not os.path.exists(draft_folder_path):
        print(f"❌ 草稿文件夹不存在: {draft_folder_path}")
        print("💡 请修改draft_folder_path为你的实际草稿文件夹路径")
        return False
    
    try:
        # 初始化草稿文件夹
        draft_folder = draft.DraftFolder(draft_folder_path)
        print(f"✅ 成功连接草稿文件夹")
        
        # 列出草稿
        drafts = draft_folder.list_drafts()
        available_drafts = [d for d in drafts if not d.startswith('.')]
        
        if not available_drafts:
            print("❌ 没有找到可用的草稿")
            return False
        
        print(f"📁 找到 {len(available_drafts)} 个草稿:")
        for i, draft_name in enumerate(available_drafts[:5]):  # 只显示前5个
            print(f"  {i+1}. {draft_name}")
        
        # 选择第一个草稿进行测试
        test_draft = available_drafts[0]
        print(f"\n🎯 使用草稿进行测试: {test_draft}")
        
        # 测试加载草稿为ScriptFile对象
        try:
            script = draft_folder.load_template(test_draft)
            print(f"✅ 成功加载草稿为ScriptFile对象")
            print(f"   草稿时长: {script.duration/1000000:.2f}s")
            print(f"   轨道数: {len(script.tracks)}")
            
            # 显示现有轨道类型
            track_types = [track.type.name for track in script.tracks]
            print(f"   轨道类型: {', '.join(set(track_types))}")
            
        except Exception as e:
            print(f"❌ 无法加载草稿为ScriptFile对象: {e}")
            print(f"💡 这可能是因为草稿已加密（剪映6.0+版本）")
            return False
        
        # 测试AudioMaterial创建
        test_audio_paths = [
            "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/examples/materials/audios/test.mp3",
            "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/examples/materials/audios/audio1.mp3",
            "/System/Library/Sounds/Ping.aiff"  # macOS系统音效
        ]
        
        audio_material = None
        for audio_path in test_audio_paths:
            if os.path.exists(audio_path):
                try:
                    audio_material = draft.AudioMaterial(audio_path)
                    print(f"✅ 成功创建AudioMaterial: {os.path.basename(audio_path)}")
                    print(f"   音频时长: {audio_material.duration/1000000:.2f}s")
                    break
                except Exception as e:
                    print(f"⚠️ 创建AudioMaterial失败 {os.path.basename(audio_path)}: {e}")
        
        if not audio_material:
            print("❌ 无法创建AudioMaterial，请确保有可用的音频文件")
            print("💡 你可以将测试音频文件放在以下位置:")
            for path in test_audio_paths:
                print(f"   - {path}")
            return False
        
        # 测试音频轨道添加
        try:
            # 检查是否已有音频轨道
            audio_tracks = [track for track in script.tracks if track.type == draft.TrackType.audio]
            if not audio_tracks:
                script.add_track(draft.TrackType.audio)
                print(f"✅ 添加音频轨道成功")
            else:
                print(f"✅ 已存在音频轨道")
                
        except Exception as e:
            print(f"❌ 添加音频轨道失败: {e}")
            return False
        
        # 测试音频片段创建
        try:
            audio_segment = draft.AudioSegment(
                material=audio_material,
                target_timerange=draft.trange("0s", "5s"),
                source_timerange=draft.trange("0s", "5s")
            )
            print(f"✅ 创建音频片段成功")
            
            # 设置音量
            audio_segment.volume = 0.8  # 80%音量
            print(f"✅ 设置音量: 80%")
            
        except Exception as e:
            print(f"❌ 创建音频片段失败: {e}")
            return False
        
        # 测试字幕导入（如果有SRT文件）
        test_srt_paths = [
            "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/examples/materials/audios/test.srt",
            "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/examples/materials/audios/subtitle.srt"
        ]
        
        for srt_path in test_srt_paths:
            if os.path.exists(srt_path):
                try:
                    script.import_srt(
                        srt_path,
                        track_name="test_subtitle",
                        time_offset="0s"
                    )
                    print(f"✅ 字幕导入成功: {os.path.basename(srt_path)}")
                    break
                except Exception as e:
                    print(f"⚠️ 字幕导入失败 {os.path.basename(srt_path)}: {e}")
        else:
            print("💬 没有找到测试字幕文件，跳过字幕测试")
            print("💡 你可以创建测试SRT文件:")
            for path in test_srt_paths:
                print(f"   - {path}")
        
        print(f"\n✅ API功能测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程出错: {e}")
        return False


def create_sample_srt():
    """创建示例SRT文件用于测试"""
    srt_content = """1
00:00:00,000 --> 00:00:03,000
这是第一条字幕

2
00:00:03,000 --> 00:00:06,000
这是第二条字幕

3
00:00:06,000 --> 00:00:09,000
这是第三条字幕
"""
    
    # 创建audios目录
    audios_dir = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/examples/materials/audios"
    os.makedirs(audios_dir, exist_ok=True)
    
    srt_path = os.path.join(audios_dir, "test.srt")
    
    try:
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        print(f"✅ 创建示例SRT文件: {srt_path}")
        return srt_path
    except Exception as e:
        print(f"❌ 创建SRT文件失败: {e}")
        return None


if __name__ == "__main__":
    print("🎵 音频和字幕功能测试工具")
    print("=" * 60)
    
    # 创建示例SRT文件
    create_sample_srt()
    
    # 运行API测试
    success = test_audio_subtitle_api()
    
    if success:
        print("\n🎉 测试成功！音频和字幕API功能正常")
    else:
        print("\n💥 测试失败，请检查错误信息")
    
    print("\n💡 提示:")
    print("1. 确保草稿文件夹路径正确")
    print("2. 确保有可用的非加密草稿（剪映5.9及以下版本）") 
    print("3. 准备测试音频文件（MP3、WAV等格式）")
    print("4. 准备测试字幕文件（SRT格式）")