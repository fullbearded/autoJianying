#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取并打印剪映草稿列表
"""

import pyJianYingDraft as draft

def main():
    # 剪映草稿文件夹路径
    draft_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
    
    try:
        # 初始化草稿文件夹管理器
        draft_folder = draft.DraftFolder(draft_path)
        
        # 获取草稿列表
        draft_list = draft_folder.list_drafts()
        
        # 打印结果
        print(f"草稿文件夹路径: {draft_path}")
        print(f"找到 {len(draft_list)} 个草稿:")
        print("-" * 50)
        
        if draft_list:
            for i, draft_name in enumerate(draft_list, 1):
                print(f"{i:2d}. {draft_name}")
        else:
            print("没有找到任何草稿")
            
    except FileNotFoundError as e:
        print(f"错误: {e}")
        print("请检查草稿文件夹路径是否正确")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main()