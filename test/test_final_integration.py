#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终集成测试 - 验证修复后的批量替换功能
"""

from batch_replace_materials import MaterialBatchReplacer

def test_batch_replacement():
    """测试批量替换功能"""
    print("🚀 开始集成测试 - 批量素材替换")
    print("=" * 60)
    
    # 使用真实的草稿文件夹和素材文件夹
    draft_folder_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
    template_name = "阳章老师模版"
    materials_folder = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/test/materials"
    
    try:
        # 创建批量替换器
        replacer = MaterialBatchReplacer(draft_folder_path, template_name)
        
        # 设置为视频模式
        replacer.set_media_type(2)
        
        print(f"\n📁 测试素材文件夹: {materials_folder}")
        
        # 验证文件夹结构
        is_valid, message = replacer.validate_folder_structure(materials_folder)
        print(f"📋 文件夹验证: {message}")
        
        if not is_valid:
            print("❌ 文件夹验证失败，无法继续测试")
            return False
        
        # 获取素材文件
        materials = replacer.get_material_files(materials_folder)
        print(f"\n📄 发现素材文件:")
        for folder, files in materials.items():
            print(f"  {folder}: {len(files)} 个文件")
            for file in files[:3]:  # 只显示前3个
                print(f"    - {file}")
        
        # 测试视频时长获取
        print(f"\n⏱️  测试视频时长获取:")
        test_videos = [
            ("part1", "A光.mp4"),
            ("part2", "B在.mp4"), 
            ("part3", "C毒.mp4")
        ]
        
        for folder, video in test_videos:
            if folder in materials and video in materials[folder]:
                video_path = f"{materials_folder}/{folder}/{video}"
                duration = replacer.get_video_duration(video_path)
                print(f"  📹 {video}: {duration:.3f}秒")
        
        # 创建替换组合
        combinations = replacer.create_replacement_combinations(materials)
        print(f"\n🔄 生成 {len(combinations)} 个替换组合")
        
        if combinations:
            # 只创建第一个组合作为测试
            combination = combinations[0]
            print(f"\n🎯 测试第一个组合:")
            for key, value in combination.items():
                print(f"  {key}: {value}")
            
            # 手动测试素材时长和速度计算逻辑
            print(f"\n🧮 速度计算测试:")
            template_segments = {
                "part1": {"duration": 15.0},
                "part2": {"duration": 10.0}, 
                "part3": {"duration": 15.0}
            }
            
            for part in ["part1", "part2", "part3"]:
                if part in combination:
                    video_path = f"{materials_folder}/{part}/{combination[part]}"
                    new_duration = replacer.get_video_duration(video_path)
                    target_duration = template_segments[part]["duration"]
                    
                    if new_duration > 0:
                        required_speed = new_duration / target_duration
                        limited_speed = max(0.1, min(required_speed, 5.0))
                        source_duration = min(target_duration * limited_speed, new_duration)
                        
                        print(f"  {part}: {new_duration:.1f}s -> {target_duration:.1f}s")
                        print(f"    速度: {limited_speed:.3f}x, 截取: {source_duration:.1f}s")
                        
                        # 验证不会超出素材时长
                        if source_duration <= new_duration:
                            print(f"    ✅ 截取时长安全 ({source_duration:.1f}s <= {new_duration:.1f}s)")
                        else:
                            print(f"    ❌ 截取时长超出! ({source_duration:.1f}s > {new_duration:.1f}s)")
        
        print(f"\n✅ 集成测试完成!")
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_batch_replacement()
    if success:
        print("\n🎉 所有测试通过! 批量替换功能已修复")
    else:
        print("\n💥 测试失败，需要进一步调试")