#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from video_cover_inserter import VideoCoverInserter
import os
import json

def compare_video_params(original_info, output_info, video_path1, video_path2):
    """详细比较两个视频的参数"""
    print(f"\n🔍 详细参数对比:")
    print(f"   原视频: {os.path.basename(video_path1)}")
    print(f"   输出视频: {os.path.basename(video_path2)}")
    
    # 基本参数对比
    matches = {
        '分辨率': (original_info['width'], original_info['height']) == (output_info['width'], output_info['height']),
        '帧率': abs(original_info['fps'] - output_info['fps']) < 0.01,
        '视频编码器': original_info['video_codec'] == output_info['video_codec'],
        '像素格式': original_info['pixel_format'] == output_info['pixel_format'],
        '视频Profile': original_info.get('video_profile', '') == output_info.get('video_profile', ''),
    }
    
    # 音频参数对比
    if original_info['has_audio'] and output_info['has_audio']:
        matches['音频编码器'] = original_info['audio_codec'] == output_info['audio_codec']
        matches['采样率'] = original_info['sample_rate'] == output_info['sample_rate']
        matches['声道数'] = original_info['channels'] == output_info['channels']
        matches['声道布局'] = original_info.get('channel_layout', '') == output_info.get('channel_layout', '')
    
    # 显示对比结果
    all_match = True
    for param, is_match in matches.items():
        status = '✅' if is_match else '❌'
        print(f"   {status} {param}: ", end='')
        
        if param == '分辨率':
            print(f"{original_info['width']}x{original_info['height']} → {output_info['width']}x{output_info['height']}")
        elif param == '帧率':
            print(f"{original_info['fps']:.2f} → {output_info['fps']:.2f}")
        elif param == '视频编码器':
            print(f"{original_info['video_codec']} → {output_info['video_codec']}")
        elif param == '像素格式':
            print(f"{original_info['pixel_format']} → {output_info['pixel_format']}")
        elif param == '视频Profile':
            orig_profile = original_info.get('video_profile', '无')
            out_profile = output_info.get('video_profile', '无')
            print(f"{orig_profile} → {out_profile}")
        elif param == '音频编码器':
            print(f"{original_info['audio_codec']} → {output_info['audio_codec']}")
        elif param == '采样率':
            print(f"{original_info['sample_rate']}Hz → {output_info['sample_rate']}Hz")
        elif param == '声道数':
            print(f"{original_info['channels']} → {output_info['channels']}")
        elif param == '声道布局':
            orig_layout = original_info.get('channel_layout', '无')
            out_layout = output_info.get('channel_layout', '无')
            print(f"{orig_layout} → {out_layout}")
        
        if not is_match:
            all_match = False
    
    return all_match

def test_perfect_parameter_matching():
    """测试完美参数匹配功能"""
    print("🧪 测试完美参数匹配功能")
    print("=" * 70)
    
    inserter = VideoCoverInserter()
    
    # 1. 环境检查
    print("\n🔧 环境检查:")
    if not inserter.check_ffmpeg():
        print("   ❌ FFmpeg 不可用，测试终止")
        return
    
    # 2. 查找测试视频
    test_folder = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/examples/test_videos/"
    if not os.path.exists(test_folder):
        print(f"   ❌ 测试文件夹不存在: {test_folder}")
        return
        
    video_files = inserter.find_video_files(test_folder)
    if not video_files:
        print(f"   ❌ 没有找到测试视频")
        return
        
    test_video = video_files[0]
    print(f"   ✅ 测试视频: {os.path.basename(test_video)}")
    
    # 3. 获取原始视频的完整信息
    print(f"\n📊 获取原视频完整参数...")
    original_info = inserter.get_video_info(test_video)
    if not original_info:
        print("   ❌ 无法获取视频信息")
        return
        
    print(f"   📈 完整视频信息:")
    print(f"      分辨率: {original_info['width']}x{original_info['height']}")
    print(f"      帧率: {original_info['fps']:.2f}fps")
    print(f"      时长: {original_info['duration']:.2f}秒")
    print(f"      视频编码器: {original_info['video_codec']}")
    print(f"      视频Profile: {original_info.get('video_profile', '无')}")
    print(f"      视频Level: {original_info.get('video_level', '无')}")
    print(f"      像素格式: {original_info['pixel_format']}")
    print(f"      视频比特率: {original_info['video_bitrate']}")
    print(f"      时间基准: {original_info.get('time_base', '无')}")
    
    if original_info['has_audio']:
        print(f"      音频编码器: {original_info['audio_codec']}")
        print(f"      音频比特率: {original_info['audio_bitrate']}")
        print(f"      采样率: {original_info['sample_rate']}Hz")
        print(f"      声道数: {original_info['channels']}")
        print(f"      声道布局: {original_info.get('channel_layout', '无')}")
    else:
        print(f"      音频: 无")
    
    # 4. 创建输出文件夹
    output_folder = os.path.join(test_folder, "perfect_match_test")
    os.makedirs(output_folder, exist_ok=True)
    print(f"\n📁 输出文件夹: {output_folder}")
    
    # 5. 进行完美匹配测试
    print(f"\n🎬 开始完美匹配测试...")
    print(f"   使用前{inserter.cover_frames}帧模式")
    
    success = inserter.process_single_video(test_video, output_folder)
    
    if success:
        print(f"\n✅ 完美匹配测试成功！")
        
        # 6. 验证输出文件参数
        base_name = os.path.splitext(os.path.basename(test_video))[0]
        output_video = os.path.join(output_folder, f"{base_name}_with_cover.mp4")
        output_cover = os.path.join(output_folder, f"{base_name}_cover.jpg")
        
        if os.path.exists(output_video):
            # 文件大小对比
            original_size = os.path.getsize(test_video) / (1024 * 1024)
            output_size = os.path.getsize(output_video) / (1024 * 1024)
            print(f"\n📹 文件大小对比:")
            print(f"   原视频: {original_size:.2f} MB")
            print(f"   输出视频: {output_size:.2f} MB")
            print(f"   大小比例: {output_size/original_size:.2f}x")
            
            # 获取输出视频的完整信息
            output_info = inserter.get_video_info(output_video)
            if output_info:
                # 详细参数对比
                all_match = compare_video_params(original_info, output_info, test_video, output_video)
                
                if all_match:
                    print(f"\n🎉 参数匹配度: 100% 完美匹配！")
                    print(f"🏆 UltraThink效果已实现完美质量保持！")
                else:
                    print(f"\n⚠️ 参数匹配存在差异，需要进一步优化")
                
                # 时长验证
                expected_duration = original_info['duration'] + (inserter.cover_frames / original_info['fps'])
                actual_duration = output_info['duration']
                duration_diff = abs(actual_duration - expected_duration)
                
                print(f"\n⏱️ 时长验证:")
                print(f"   原视频时长: {original_info['duration']:.3f}秒")
                print(f"   封面图时长: {inserter.cover_frames / original_info['fps']:.3f}秒")
                print(f"   预期总时长: {expected_duration:.3f}秒")
                print(f"   实际总时长: {actual_duration:.3f}秒")
                print(f"   时长差异: {duration_diff:.3f}秒 {'✅' if duration_diff < 0.1 else '❌'}")
            else:
                print(f"   ❌ 无法获取输出视频信息")
        
        if os.path.exists(output_cover):
            cover_size = os.path.getsize(output_cover) / 1024
            print(f"🖼️ 封面图: {os.path.basename(output_cover)} ({cover_size:.1f} KB)")
            
        print(f"\n🎯 完美匹配测试完成！")
        print(f"📂 查看结果: {output_folder}")
        
    else:
        print(f"\n❌ 完美匹配测试失败")

if __name__ == "__main__":
    test_perfect_parameter_matching()