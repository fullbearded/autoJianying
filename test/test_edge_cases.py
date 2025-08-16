#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试边界情况 - 特别是接近目标时长的视频
"""

from batch_replace_materials import MaterialBatchReplacer
import os

def test_edge_case_videos():
    """测试边界情况的视频"""
    print("🧪 测试边界情况视频处理")
    print("=" * 60)
    
    draft_folder_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
    template_name = "阳章老师模版"
    materials_folder = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/test/materials"
    
    try:
        replacer = MaterialBatchReplacer(draft_folder_path, template_name)
        replacer.set_media_type(2)
        
        # 构造包含B经.mp4的测试组合（这是原来出错的视频）
        test_combination = {
            "part1": "B经.mp4",  # 这是引起错误的15.1s视频
            "part2": "B在.mp4",
            "part3": "B行.mp4"
        }
        
        print(f"🎯 测试组合（边界情况）:")
        for key, value in test_combination.items():
            video_path = os.path.join(materials_folder, key, value)
            if os.path.exists(video_path):
                duration = replacer.get_video_duration(video_path)
                print(f"  {key}: {value} (ffprobe时长: {duration:.3f}s)")
            else:
                print(f"  {key}: {value} (文件不存在)")
        
        # 执行边界情况测试
        output_name = f"边界测试_{int(__import__('time').time()) % 10000}"
        print(f"\n🔄 开始边界情况测试: {output_name}")
        
        success = replacer.create_draft_from_segments_fixed(
            test_combination, materials_folder, output_name
        )
        
        if success:
            print(f"\n✅ 边界情况测试成功!")
            return True
        else:
            print(f"\n❌ 边界情况测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_edge_case_videos()
    if success:
        print("\n🎉 所有边界情况测试通过!")
        print("📝 修复成功：精度问题和时长超出错误已解决")
    else:
        print("\n💥 边界情况测试失败")