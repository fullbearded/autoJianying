#!/usr/bin/env python3
"""
完整的草稿复制demo
演示如何使用pyJianYingDraft复制现有草稿到新草稿
"""

import os
import sys
import argparse
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
        
        # 统计片段数
        total_segments = 0
        if 'tracks' in draft_info:
            for track in draft_info['tracks']:
                segments = track.get('segments', [])
                total_segments += len(segments)
        
        return {
            'draft_name': draft_name,
            'canvas_config': canvas,
            'duration': duration,
            'fps': fps,
            'tracks': tracks_stats,
            'materials': materials_stats,
            'total_segments': total_segments
        }
        
    except Exception as e:
        print(f"读取 draft_info.json 失败: {e}")
        return None


def main():
    """主函数：演示完整的草稿复制流程"""
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="pyJianYingDraft 草稿复制Demo")
    parser.add_argument("--draft-folder", 
                       default="/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft",
                       help="剪映草稿文件夹路径")
    parser.add_argument("--source-draft", 
                       help="指定要复制的源草稿名称（可选，不指定则显示列表选择）")
    parser.add_argument("--target-name", 
                       help="指定目标草稿名称（可选，不指定则自动生成）")
    parser.add_argument("--non-interactive", action="store_true",
                       help="非交互模式，使用第一个可用草稿")
    
    args = parser.parse_args()
    
    draft_folder_path = args.draft_folder
    
    print("=== pyJianYingDraft 草稿复制Demo ===")
    print(f"草稿文件夹路径: {draft_folder_path}")
    
    # 检查路径是否存在
    if not os.path.exists(draft_folder_path):
        print(f"错误: 草稿文件夹路径不存在: {draft_folder_path}")
        print("请使用 --draft-folder 参数指定正确的剪映草稿文件夹路径")
        print("例如: python copy_draft_demo.py --draft-folder '/path/to/your/jianying/drafts'")
        return
    
    try:
        # 1. 初始化草稿文件夹管理器
        print("\n1. 初始化草稿文件夹管理器...")
        draft_folder = draft.DraftFolder(draft_folder_path)
        
        # 2. 列出现有草稿
        print("\n2. 列出现有草稿...")
        drafts = draft_folder.list_drafts()
        
        if not drafts:
            print("没有找到现有草稿，将创建一个示例草稿")
            create_sample_draft(draft_folder)
            drafts = draft_folder.list_drafts()
        
        # 过滤掉系统文件和之前demo创建的草稿
        filtered_drafts = [d for d in drafts if not d.startswith('.') and not d.startswith('pyJianYingDraft_Demo')]
        
        if not filtered_drafts:
            print("没有找到有效的草稿，将创建一个示例草稿")
            create_sample_draft(draft_folder)
            drafts = draft_folder.list_drafts()
            filtered_drafts = [d for d in drafts if not d.startswith('.') and not d.startswith('pyJianYingDraft_Demo')]
        
        print(f"找到 {len(filtered_drafts)} 个可用草稿:")
        for i, draft_name in enumerate(filtered_drafts):
            print(f"  {i+1}. {draft_name}")
        
        # 3. 选择要复制的草稿
        print("\n3. 选择要复制的草稿:")
        
        if args.source_draft:
            # 命令行指定了源草稿
            if args.source_draft in filtered_drafts:
                source_draft_name = args.source_draft
                print(f"使用命令行指定的草稿: {source_draft_name}")
            else:
                print(f"错误: 指定的草稿 '{args.source_draft}' 不存在")
                print("可用的草稿:")
                for i, draft_name in enumerate(filtered_drafts):
                    print(f"  {i+1}. {draft_name}")
                return
        elif args.non_interactive:
            # 非交互模式，使用第一个
            source_draft_name = filtered_drafts[0]
            print(f"非交互模式，使用第一个草稿: {source_draft_name}")
        else:
            # 交互模式选择
            if sys.stdin.isatty():
                # 在真正的终端中运行，支持交互
                while True:
                    try:
                        choice = input(f"请输入草稿编号 (1-{len(filtered_drafts)}) 或直接回车使用第一个: ").strip()
                        
                        if choice == "":
                            source_draft_name = filtered_drafts[0]
                            print(f"使用默认选择: {source_draft_name}")
                            break
                        elif choice.isdigit():
                            index = int(choice) - 1
                            if 0 <= index < len(filtered_drafts):
                                source_draft_name = filtered_drafts[index]
                                print(f"选择了: {source_draft_name}")
                                break
                            else:
                                print(f"无效的编号，请输入 1-{len(filtered_drafts)} 之间的数字")
                        else:
                            print("请输入有效的数字")
                    except KeyboardInterrupt:
                        print("\n用户取消操作")
                        return
                    except EOFError:
                        print("\n输入中断，使用默认选择")
                        source_draft_name = filtered_drafts[0]
                        break
            else:
                # 在非交互环境中运行，使用第一个
                source_draft_name = filtered_drafts[0]
                print(f"检测到非交互环境，使用第一个草稿: {source_draft_name}")
        
        # 生成目标草稿名称
        import time
        timestamp = int(time.time())
        if args.target_name:
            target_draft_name = args.target_name
        else:
            target_draft_name = f"{source_draft_name}_复制版_{timestamp}"
        
        print(f"\n4. 准备复制草稿...")
        print(f"源草稿: {source_draft_name}")
        print(f"目标草稿: {target_draft_name}")
        
        # 5. 执行草稿复制
        print("\n5. 执行草稿复制...")
        copied_script = None
        copy_success = False
        
        try:
            # 尝试使用duplicate_as_template方法复制草稿
            copied_script = draft_folder.duplicate_as_template(source_draft_name, target_draft_name)
            print(f"✓ 模板复制API调用成功!")
            copy_success = True
        except Exception as e:
            print(f"⚠ 模板复制API报错: {e}")
            # 检查草稿是否实际创建成功
            print("检查草稿是否实际创建成功...")
            
            # 等待一下再检查
            import time
            time.sleep(1)
            
            updated_drafts = draft_folder.list_drafts()
            if target_draft_name in updated_drafts:
                print("✓ 尽管API报错，草稿实际上创建成功了!")
                copy_success = True  # 草稿存在就表示成功
                try:
                    # 尝试加载创建的草稿
                    copied_script = draft_folder.load_template(target_draft_name)
                    print("✓ 成功加载复制的草稿")
                except Exception as load_error:
                    print(f"⚠ 无法加载草稿详细信息: {load_error}")
                    print("但草稿文件夹已存在，复制仍然成功")
                    # 即使无法加载，也不影响复制成功的判断
            else:
                print("✗ 草稿确实创建失败")
        
        if copy_success:
            # 6. 显示复制后的草稿信息
            print("\n6. 复制后的草稿信息:")
            
            # 优先尝试从draft_info.json读取信息
            draft_info = load_draft_info_from_file(draft_folder_path, target_draft_name)
            
            if draft_info:
                print("✓ 成功从 draft_info.json 读取草稿信息")
                print(f"草稿名称: {draft_info['draft_name']}")
                
                canvas = draft_info['canvas_config']
                if canvas:
                    print(f"分辨率: {canvas.get('width', '?')}x{canvas.get('height', '?')}")
                    if 'ratio' in canvas:
                        print(f"宽高比: {canvas['ratio']}")
                
                if draft_info['duration']:
                    print(f"时长: {draft_info['duration'] / 1000000:.2f}秒")
                
                if draft_info['fps']:
                    print(f"帧率: {draft_info['fps']} fps")
                
                if draft_info['tracks']:
                    print(f"轨道统计:")
                    for track_type, count in draft_info['tracks'].items():
                        print(f"  {track_type}: {count}条轨道")
                
                if draft_info['materials']:
                    print(f"素材统计:")
                    material_count = 0
                    for material_type, count in draft_info['materials'].items():
                        if count > 0:
                            print(f"  {material_type}: {count}个")
                            material_count += count
                    if material_count > 0:
                        print(f"总素材数: {material_count}")
                
                if draft_info['total_segments']:
                    print(f"总片段数: {draft_info['total_segments']}")
                    
            elif copied_script:
                # 如果无法读取draft_info.json，尝试使用原始方法
                print("⚠ 无法读取 draft_info.json，尝试使用API方法")
                try:
                    print(f"草稿名称: {copied_script.draft_name}")
                    print(f"分辨率: {copied_script.canvas_config['width']}x{copied_script.canvas_config['height']}")
                    print(f"时长: {copied_script.duration / 1000000:.2f}秒")
                    
                    # 显示轨道信息
                    print(f"轨道数量: {len(copied_script.tracks)}")
                    for track_type, tracks in copied_script.tracks.items():
                        if tracks:
                            print(f"  {track_type}: {len(tracks)}条轨道")
                    
                    # 显示素材信息
                    materials = copied_script.materials
                    if hasattr(materials, '__len__') and len(materials) > 0:
                        print(f"素材数量: {len(materials)}")
                        if hasattr(materials, 'items'):
                            for material_id, material in list(materials.items())[:3]:  # 显示前3个素材
                                material_type = type(material).__name__
                                if hasattr(material, 'path'):
                                    print(f"  {material_type}: {material.path}")
                                else:
                                    print(f"  {material_type}: {material_id}")
                            
                            if len(materials) > 3:
                                print(f"  ... 还有 {len(materials)-3} 个素材")
                    else:
                        print("没有找到素材信息")
                        
                except Exception as info_error:
                    print(f"显示草稿详细信息时出错: {info_error}")
            else:
                print("草稿复制成功，但无法加载详细信息")
                print(f"草稿名称: {target_draft_name}")
                print("尝试手动检查 draft_info.json 文件...")
            
            # 7. 验证复制结果
            print("\n7. 验证复制结果...")
            final_drafts = draft_folder.list_drafts()
            if target_draft_name in final_drafts:
                print("✓ 草稿复制验证成功!")
                print(f"新草稿已添加到草稿列表: {target_draft_name}")
                
                # 检查草稿文件夹内容
                target_path = os.path.join(draft_folder_path, target_draft_name)
                if os.path.exists(target_path):
                    files = os.listdir(target_path)
                    print(f"草稿文件夹包含 {len(files)} 个文件")
                    key_files = [f for f in files if f.endswith(('.json', '.jpg', '.dat'))]
                    if key_files:
                        print("包含关键文件:", ', '.join(key_files[:5]))
                        
                # 高级功能演示：素材替换
                print("\n8. 高级功能演示：素材替换...")
                if copied_script:
                    demonstrate_material_replacement(copied_script)
                else:
                    print("由于无法加载草稿对象，跳过素材替换演示")
                    print("素材替换功能在支持的剪映版本中可用")
            else:
                print("✗ 草稿复制验证失败!")
                
        else:
            # 模板复制失败，尝试创建新草稿演示
            print("\n检测到剪映版本可能使用了加密，尝试创建新草稿演示...")
            
            try:
                # 生成新的草稿名称避免冲突
                import random
                new_timestamp = int(time.time()) + random.randint(1, 1000)
                demo_draft_name = f"pyJianYingDraft_Demo_{new_timestamp}"
                
                # 创建一个新的草稿来演示功能
                print(f"\n5b. 创建新草稿演示: {demo_draft_name}")
                copied_script = draft_folder.create_draft(demo_draft_name, 1920, 1080)
                
                # 添加基本轨道
                copied_script.add_track(draft.TrackType.video)
                copied_script.add_track(draft.TrackType.audio)
                copied_script.add_track(draft.TrackType.text)
                
                # 尝试添加示例视频（如果存在）
                sample_video = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/readme_assets/tutorial/video.mp4"
                if os.path.exists(sample_video):
                    video_seg = draft.VideoSegment(sample_video, draft.trange("0s", "5s"))
                    copied_script.add_segment(video_seg)
                    print("✓ 添加了示例视频片段")
                
                # 尝试添加示例音频（如果存在）
                sample_audio = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/readme_assets/tutorial/audio.mp3"
                if os.path.exists(sample_audio):
                    audio_seg = draft.AudioSegment(sample_audio, draft.trange("0s", "5s"))
                    copied_script.add_segment(audio_seg)
                    print("✓ 添加了示例音频片段")
                
                # 添加文字片段
                text_seg = draft.TextSegment("演示文本", draft.trange("1s", "4s"))
                copied_script.add_segment(text_seg)
                print("✓ 添加了文字片段")
                
                # 保存草稿
                copied_script.save()
                print(f"✓ 新草稿创建并保存成功!")
                
                target_draft_name = demo_draft_name  # 更新target_draft_name用于后续验证
                
                # 验证demo草稿创建
                print("\n验证demo草稿创建...")
                final_drafts = draft_folder.list_drafts()
                if target_draft_name in final_drafts:
                    print("✓ Demo草稿创建验证成功!")
                    print(f"Demo草稿已添加到草稿列表: {target_draft_name}")
                    
                    # 高级功能演示：素材替换
                    print("\n高级功能演示：素材替换...")
                    if copied_script:
                        demonstrate_material_replacement(copied_script)
                    else:
                        print("Demo草稿已创建但无法演示素材替换")
                else:
                    print("✗ Demo草稿创建验证失败!")
                
            except Exception as create_error:
                print(f"✗ 创建新草稿也失败: {create_error}")
                print("请检查:")
                print("  1. 草稿文件夹路径是否正确")
                print("  2. 是否有足够的权限访问草稿文件夹")
                print("  3. pyJianYingDraft库是否正确安装")
                return
        
        print("\n=== Demo完成 ===")
        print("你现在可以在剪映中打开新创建的草稿进行编辑")
        
    except Exception as e:
        print(f"Demo执行出错: {e}")
        print("请检查:")
        print("1. 草稿文件夹路径是否正确")
        print("2. 是否有足够的权限访问草稿文件夹")
        print("3. 剪映是否已正确安装")


def create_sample_draft(draft_folder):
    """创建一个示例草稿用于演示"""
    print("创建示例草稿...")
    
    try:
        # 创建一个简单的草稿
        script = draft_folder.create_draft("示例草稿", 1920, 1080)
        
        # 添加视频轨道
        script.add_track(draft.TrackType.video)
        
        # 添加音频轨道
        script.add_track(draft.TrackType.audio)
        
        # 添加文字轨道
        script.add_track(draft.TrackType.text)
        
        # 保存草稿
        script.save()
        print("✓ 示例草稿创建成功")
        
    except Exception as e:
        print(f"✗ 示例草稿创建失败: {e}")


def demonstrate_material_replacement(script):
    """演示素材替换功能"""
    try:
        materials = script.materials
        if not hasattr(materials, '__len__') or len(materials) == 0:
            print("没有素材可供替换演示")
            return
        
        # 获取第一个素材
        if hasattr(materials, 'keys'):
            first_material_id = list(materials.keys())[0]
            first_material = materials[first_material_id]
        else:
            # 如果materials不是字典类型，尝试其他方式获取
            print("素材对象结构:", type(materials))
            if hasattr(materials, '__iter__'):
                for material in materials:
                    first_material = material
                    break
            else:
                first_material = materials
        
        print(f"原始素材: {type(first_material).__name__}")
        if hasattr(first_material, 'path'):
            print(f"路径: {first_material.path}")
        
        # 注意：这里只是演示API调用，实际替换需要真实的素材文件
        print("素材替换功能可用，但需要实际的素材文件路径")
        print("示例代码:")
        print("  new_material = draft.VideoMaterial('新视频.mp4')")
        print("  script.replace_material_by_name('旧视频.mp4', new_material)")
        
    except Exception as e:
        print(f"素材替换演示出错: {e}")


if __name__ == "__main__":
    main()
