#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映草稿批量导出工具
支持选择前N个草稿进行批量导出，并可选择是否保留草稿
"""

import os
import sys
import platform
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pyJianYingDraft as draft
from pyJianYingDraft import ExportResolution, ExportFramerate


class BatchExportCLI:
    """批量导出命令行界面"""
    
    def __init__(self):
        # 根据系统设置默认草稿文件夹路径
        if platform.system() == "Darwin":  # macOS
            self.draft_folder_path = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
        elif platform.system() == "Windows":
            self.draft_folder_path = os.path.expanduser("~/AppData/Local/JianyingPro/User Data/Projects/com.lveditor.draft")
        else:
            self.draft_folder_path = None
            
        self.draft_folder = None
        self.export_folder = os.path.expanduser("~/Desktop/剪映导出")
        
    def print_header(self, title):
        """打印标题"""
        print("\n" + "="*50)
        print(f"  {title}")
        print("="*50)
        
    def print_error(self, message):
        """打印错误信息"""
        print(f"❌ 错误: {message}")
        
    def print_success(self, message):
        """打印成功信息"""
        print(f"✅ {message}")
        
    def print_warning(self, message):
        """打印警告信息"""
        print(f"⚠️  警告: {message}")
        
    def setup_draft_folder(self):
        """设置草稿文件夹"""
        self.print_header("设置草稿文件夹")
        
        if self.draft_folder_path and os.path.exists(self.draft_folder_path):
            print(f"📁 默认草稿文件夹: {self.draft_folder_path}")
            use_default = input("是否使用默认路径? (y/n): ").strip().lower()
            if use_default != 'y':
                self.draft_folder_path = input("请输入草稿文件夹路径: ").strip()
        else:
            print("⚠️  无法找到默认草稿文件夹")
            self.draft_folder_path = input("请输入草稿文件夹路径: ").strip()
            
        if not os.path.exists(self.draft_folder_path):
            self.print_error(f"草稿文件夹不存在: {self.draft_folder_path}")
            return False
            
        try:
            self.draft_folder = draft.DraftFolder(self.draft_folder_path)
            self.print_success(f"草稿文件夹设置成功: {self.draft_folder_path}")
            return True
        except Exception as e:
            self.print_error(f"初始化草稿文件夹失败: {e}")
            return False
            
    def setup_export_folder(self):
        """设置导出文件夹"""
        self.print_header("设置导出文件夹")
        
        print(f"📁 默认导出文件夹: {self.export_folder}")
        use_default = input("是否使用默认路径? (y/n): ").strip().lower()
        
        if use_default != 'y':
            self.export_folder = input("请输入导出文件夹路径: ").strip()
            
        # 创建导出文件夹
        os.makedirs(self.export_folder, exist_ok=True)
        self.print_success(f"导出文件夹设置成功: {self.export_folder}")
        
    def get_draft_list(self):
        """获取草稿列表"""
        try:
            draft_list = self.draft_folder.list_drafts()
            # 过滤掉系统文件和demo草稿
            filtered_drafts = [d for d in draft_list if not d.startswith('.') and not d.startswith('pyJianYingDraft_Demo')]
            return filtered_drafts
        except Exception as e:
            self.print_error(f"获取草稿列表失败: {e}")
            return []
            
    def display_drafts(self, drafts):
        """显示草稿列表"""
        self.print_header("草稿列表")
        
        if not drafts:
            self.print_error("没有找到可用的草稿")
            return
            
        print(f"📊 找到 {len(drafts)} 个可用草稿:")
        print()
        
        for i, draft_name in enumerate(drafts, 1):
            print(f"{i:3d}. {draft_name}")
            
    def select_export_count(self, total_drafts):
        """选择要导出的草稿数量"""
        self.print_header("选择导出数量")
        
        print(f"总共有 {total_drafts} 个草稿可以导出")
        
        while True:
            try:
                count = input(f"请输入要导出前多少个草稿 (1-{total_drafts}): ").strip()
                count = int(count)
                
                if 1 <= count <= total_drafts:
                    return count
                else:
                    self.print_error(f"请输入1到{total_drafts}之间的数字")
                    
            except ValueError:
                self.print_error("请输入有效的数字")
                
    def select_export_settings(self):
        """选择导出设置"""
        self.print_header("导出设置")
        
        # 分辨率选择
        print("选择导出分辨率:")
        print("1. 1080P (1920x1080)")
        print("2. 720P (1280x720)")
        print("3. 4K (3840x2160)")
        
        while True:
            try:
                res_choice = input("请选择分辨率 (1-3, 默认1): ").strip()
                if not res_choice:
                    res_choice = "1"
                    
                res_choice = int(res_choice)
                
                if res_choice == 1:
                    resolution = ExportResolution.RES_1080P
                    break
                elif res_choice == 2:
                    resolution = ExportResolution.RES_720P
                    break
                elif res_choice == 3:
                    resolution = ExportResolution.RES_4K
                    break
                else:
                    self.print_error("请输入1-3之间的数字")
                    
            except ValueError:
                self.print_error("请输入有效的数字")
        
        # 帧率选择
        print("\n选择导出帧率:")
        print("1. 24 FPS")
        print("2. 30 FPS")
        print("3. 60 FPS")
        
        while True:
            try:
                fps_choice = input("请选择帧率 (1-3, 默认2): ").strip()
                if not fps_choice:
                    fps_choice = "2"
                    
                fps_choice = int(fps_choice)
                
                if fps_choice == 1:
                    framerate = ExportFramerate.FR_24
                    break
                elif fps_choice == 2:
                    framerate = ExportFramerate.FR_30
                    break
                elif fps_choice == 3:
                    framerate = ExportFramerate.FR_60
                    break
                else:
                    self.print_error("请输入1-3之间的数字")
                    
            except ValueError:
                self.print_error("请输入有效的数字")
                
        return resolution, framerate
        
    def select_draft_action(self):
        """选择草稿处理方式"""
        self.print_header("草稿处理选项")
        
        print("导出完成后对草稿的处理:")
        print("1. 保留草稿")
        print("2. 删除草稿")
        
        while True:
            try:
                choice = input("请选择 (1-2): ").strip()
                choice = int(choice)
                
                if choice == 1:
                    return False  # 不删除
                elif choice == 2:
                    return True   # 删除
                else:
                    self.print_error("请输入1或2")
                    
            except ValueError:
                self.print_error("请输入有效的数字")
                
    def check_jianying_support(self):
        """检查剪映支持情况"""
        if platform.system() != "Windows":
            self.print_warning("当前系统不是Windows，批量导出功能可能不可用")
            self.print_warning("批量导出功能目前仅支持Windows系统上的剪映6及以下版本")
            
            choice = input("是否继续尝试? (y/n): ").strip().lower()
            return choice == 'y'
        return True
        
    def export_drafts(self, drafts_to_export, resolution, framerate, delete_after_export):
        """批量导出草稿"""
        self.print_header("开始批量导出")
        
        if not self.check_jianying_support():
            return False
            
        print(f"准备导出 {len(drafts_to_export)} 个草稿...")
        print("⚠️  请确保剪映已打开并位于目录页")
        
        input("准备就绪后按回车键开始导出...")
        
        try:
            # 初始化剪映控制器
            ctrl = draft.JianyingController()
            
            success_count = 0
            failed_drafts = []
            
            for i, draft_name in enumerate(drafts_to_export, 1):
                print(f"\n[{i}/{len(drafts_to_export)}] 正在导出: {draft_name}")
                
                try:
                    # 设置导出路径
                    export_path = os.path.join(self.export_folder, f"{draft_name}.mp4")
                    
                    # 导出草稿
                    ctrl.export_draft(draft_name, export_path, 
                                    resolution=resolution, 
                                    framerate=framerate)
                    
                    self.print_success(f"导出成功: {export_path}")
                    success_count += 1
                    
                    # 如果选择删除草稿
                    if delete_after_export:
                        try:
                            self.draft_folder.delete_draft(draft_name)
                            print(f"🗑️  已删除草稿: {draft_name}")
                        except Exception as e:
                            self.print_warning(f"删除草稿失败: {e}")
                    
                except Exception as e:
                    self.print_error(f"导出失败: {e}")
                    failed_drafts.append(draft_name)
                    
            # 显示导出结果
            self.print_header("导出完成")
            print(f"✅ 成功导出: {success_count} 个草稿")
            
            if failed_drafts:
                print(f"❌ 导出失败: {len(failed_drafts)} 个草稿")
                print("失败的草稿:")
                for draft_name in failed_drafts:
                    print(f"  - {draft_name}")
                    
            return success_count > 0
            
        except Exception as e:
            self.print_error(f"初始化剪映控制器失败: {e}")
            self.print_warning("请检查:")
            self.print_warning("1. 剪映是否已安装并且是6及以下版本")
            self.print_warning("2. 剪映是否已打开并位于目录页")
            self.print_warning("3. 是否有导出草稿的相关权限")
            return False
            
    def run(self):
        """运行主程序"""
        self.print_header("剪映草稿批量导出工具")
        
        # 设置草稿文件夹
        if not self.setup_draft_folder():
            return
            
        # 设置导出文件夹
        self.setup_export_folder()
        
        # 获取草稿列表
        drafts = self.get_draft_list()
        if not drafts:
            return
            
        # 显示草稿列表
        self.display_drafts(drafts)
        
        # 选择导出数量
        export_count = self.select_export_count(len(drafts))
        drafts_to_export = drafts[:export_count]
        
        # 选择导出设置
        resolution, framerate = self.select_export_settings()
        
        # 选择草稿处理方式
        delete_after_export = self.select_draft_action()
        
        # 确认导出
        self.print_header("确认导出")
        print(f"将要导出的草稿 ({export_count} 个):")
        for i, draft_name in enumerate(drafts_to_export, 1):
            print(f"  {i}. {draft_name}")
            
        print(f"\n导出文件夹: {self.export_folder}")
        print(f"分辨率: {resolution}")
        print(f"帧率: {framerate}")
        print(f"导出后: {'删除草稿' if delete_after_export else '保留草稿'}")
        
        confirm = input("\n确认开始导出? (y/n): ").strip().lower()
        if confirm != 'y':
            print("已取消导出")
            return
            
        # 开始导出
        success = self.export_drafts(drafts_to_export, resolution, framerate, delete_after_export)
        
        if success:
            self.print_success("批量导出流程完成!")
        else:
            self.print_error("批量导出流程失败!")


def main():
    """主函数"""
    try:
        cli = BatchExportCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
    except Exception as e:
        print(f"\n程序发生错误: {e}")
        

if __name__ == "__main__":
    main()