#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试 pyJianYingDraft API - 查找正确的加载草稿方法
"""

import pyJianYingDraft as draft

def debug_draft_folder_api():
    """调试 DraftFolder 可用方法"""
    print("🔍 调试 pyJianYingDraft API")
    print("=" * 50)
    
    draft_folder_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
    
    try:
        folder = draft.DraftFolder(draft_folder_path)
        
        print("📋 DraftFolder 可用方法:")
        methods = [method for method in dir(folder) if not method.startswith('_')]
        for method in methods:
            print(f"  - {method}")
        
        print(f"\n🎬 测试获取草稿列表:")
        drafts = folder.list_drafts()
        print(f"找到 {len(drafts)} 个草稿: {drafts}")
        
        # 尝试加载阳章老师模版
        if '阳章老师模版' in drafts:
            print(f"✅ 找到目标草稿: 阳章老师模版")
            
            print(f"\n🔄 尝试使用 load_template 方法...")
            try:
                script = folder.load_template('阳章老师模版')
                print(f"✅ load_template 成功: {type(script)}")
                
                # 查看script的方法
                print(f"Script 可用方法:")
                script_methods = [method for method in dir(script) if not method.startswith('_')]
                for sm in script_methods:
                    print(f"  - {sm}")
                
                # 测试copy方法
                if hasattr(script, 'copy'):
                    print(f"\n🔄 测试 copy 方法...")
                    try:
                        test_copy = script.copy('测试复制草稿')
                        print(f"✅ copy 成功: {type(test_copy)}")
                        
                        # 测试replace_material_by_name
                        if hasattr(test_copy, 'replace_material_by_name'):
                            print(f"✅ 找到 replace_material_by_name 方法")
                        else:
                            print(f"❌ 没有 replace_material_by_name 方法")
                            
                    except Exception as e:
                        print(f"❌ copy 失败: {e}")
                
                return script
                
            except Exception as e:
                print(f"❌ load_template 失败: {e}")
        else:
            print(f"❌ 没有找到 阳章老师模版 草稿")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()
    
    return None


if __name__ == "__main__":
    script = debug_draft_folder_api()
    if script:
        print("\n🎉 找到了正确的加载方法!")
    else:
        print("\n💥 没有找到正确的加载方法")