#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试需要加速的视频情况
"""

from batch_replace_materials import MaterialBatchReplacer
import os

def test_speedup_cases():
    """测试需要加速处理的视频"""
    print("🧪 测试加速情况视频处理")
    print("=" * 60)
    
    draft_folder_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
    template_name = "阳章老师模版"
    materials_folder = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/test/materials"
    
    try:
        replacer = MaterialBatchReplacer(draft_folder_path, template_name)
        replacer.set_media_type(2)
        
        # 测试需要加速的组合（长视频适配短模板时长）
        speedup_cases = [
            {
                "name": "D规测试",
                "combination": {
                    "part1": "D武.mp4",  # 7.082s -> 15s (减速)
                    "part2": "D规.mp4",  # 13.189s -> 10s (加速，这是出错的)
                    "part3": "D故.mp4"   
                }
            },
            {
                "name": "E兽测试", 
                "combination": {
                    "part1": "E狂.mp4",  # 7.035s -> 15s (减速)
                    "part2": "E兽.mp4",  # 13.444s -> 10s (加速，这是出错的)
                    "part3": "E伐.mp4"
                }
            }
        ]
        
        for case in speedup_cases:
            print(f"\n🎯 {case['name']}:")
            combination = case['combination']
            
            # 显示视频信息
            for key, value in combination.items():
                video_path = os.path.join(materials_folder, key, value)
                if os.path.exists(video_path):
                    duration = replacer.get_video_duration(video_path)
                    target = {"part1": 15.0, "part2": 10.0, "part3": 15.0}[key]
                    speed_needed = duration / target
                    action = "加速" if speed_needed > 1.0 else "减速"
                    print(f"  {key}: {value} ({duration:.3f}s -> {target}s, 需要{action} {speed_needed:.2f}x)")
                else:
                    print(f"  {key}: {value} (文件不存在)")
            
            # 执行测试
            output_name = f"{case['name']}_{int(__import__('time').time()) % 10000}"
            print(f"\n🔄 开始测试: {output_name}")
            
            try:
                success = replacer.create_draft_from_segments_fixed(
                    combination, materials_folder, output_name
                )
                
                if success:
                    print(f"✅ {case['name']} 成功!")
                else:
                    print(f"❌ {case['name']} 失败")
            except Exception as e:
                print(f"❌ {case['name']} 异常: {e}")
        
        return True
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_speedup_cases()
    if success:
        print("\n🎉 加速情况测试完成!")
    else:
        print("\n💥 加速情况测试失败")