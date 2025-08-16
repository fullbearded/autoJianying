#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试模板替换方式的批量素材替换
"""

from batch_replace_materials import MaterialBatchReplacer

def test_template_replacement():
    """测试模板替换方式"""
    print("🚀 测试模板替换方式的批量素材替换")
    print("=" * 60)
    
    # 使用真实路径
    draft_folder_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
    template_name = "阳章老师模版"
    materials_folder = "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/test/materials"
    
    try:
        # 创建批量替换器
        replacer = MaterialBatchReplacer(draft_folder_path, template_name)
        
        # 设置为视频模式
        replacer.set_media_type(2)
        
        print(f"\n📁 素材文件夹: {materials_folder}")
        
        # 验证文件夹结构
        is_valid, message = replacer.validate_folder_structure(materials_folder)
        print(f"📋 验证结果: {message}")
        
        if not is_valid:
            print("❌ 验证失败，停止测试")
            return False
        
        # 获取素材文件
        materials = replacer.get_material_files(materials_folder)
        print(f"\n📄 发现素材:")
        for folder, files in materials.items():
            print(f"  {folder}: {files[:3]}")  # 只显示前3个
        
        # 创建替换组合
        combinations = replacer.create_replacement_combinations(materials)
        print(f"\n🔄 生成 {len(combinations)} 个组合")
        
        if combinations:
            # 测试第一个组合
            combination = combinations[0]
            test_output_name = f"模板替换测试_{int(__import__('time').time()) % 10000}"
            
            print(f"\n🎯 测试组合: {test_output_name}")
            for key, value in combination.items():
                print(f"  {key}: {value}")
            
            # 执行分段方式创建（修复版本）
            print(f"\n🔄 开始分段创建（独立轨道）...")
            success = replacer.create_draft_from_segments_fixed(
                combination, materials_folder, test_output_name
            )
            
            if success:
                print(f"\n✅ 分段创建成功!")
                return True
            else:
                print(f"\n❌ 分段创建失败")
                return False
        else:
            print("❌ 没有找到可用的替换组合")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_template_replacement()
    if success:
        print("\n🎉 模板替换测试通过!")
        print("📝 现在应该可以避免时间线重叠问题了")
    else:
        print("\n💥 模板替换测试失败")