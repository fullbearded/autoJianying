#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映草稿批量导出工具
支持选择前N个草稿进行批量导出，并可选择是否保留草稿
"""

import os
import sys
import platform
import time
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
        
        # 自动化延迟设置 (秒)
        self.automation_delay = 2.0  # 操作间默认延迟
        self.long_delay = 5.0       # 长操作延迟
        self.short_delay = 1.0      # 短操作延迟
        
        # 错误处理设置
        self.auto_skip_missing = True   # 自动跳过不存在的草稿
        self.show_smart_suggestions = True  # 显示智能建议
        
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
            
    def setup_automation_delays(self):
        """设置自动化延迟"""
        self.print_header("自动化延迟设置")
        
        print(f"⏱️  当前延迟设置:")
        print(f"   - 默认操作延迟: {self.automation_delay}秒")
        print(f"   - 长操作延迟: {self.long_delay}秒")
        print(f"   - 短操作延迟: {self.short_delay}秒")
        
        adjust = input("是否需要调整延迟设置? (y/n): ").strip().lower()
        
        if adjust == 'y':
            try:
                new_delay = input(f"请输入默认操作延迟 (当前: {self.automation_delay}秒): ").strip()
                if new_delay:
                    self.automation_delay = float(new_delay)
                    
                new_long = input(f"请输入长操作延迟 (当前: {self.long_delay}秒): ").strip()
                if new_long:
                    self.long_delay = float(new_long)
                    
                new_short = input(f"请输入短操作延迟 (当前: {self.short_delay}秒): ").strip()
                if new_short:
                    self.short_delay = float(new_short)
                    
                self.print_success("延迟设置已更新")
            except ValueError:
                self.print_warning("输入无效，使用默认延迟设置")
        
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
            
            # 验证草稿有效性
            valid_drafts = []
            invalid_drafts = []
            
            for draft_name in filtered_drafts:
                try:
                    # 检查草稿文件夹是否包含必要文件
                    draft_path = os.path.join(self.draft_folder.folder_path, draft_name)
                    if os.path.exists(os.path.join(draft_path, "draft_content.json")):
                        valid_drafts.append(draft_name)
                    else:
                        invalid_drafts.append(draft_name)
                except:
                    invalid_drafts.append(draft_name)
            
            if invalid_drafts:
                print(f"⚠️  发现 {len(invalid_drafts)} 个无效草稿，将自动跳过:")
                for draft_name in invalid_drafts:
                    print(f"  - {draft_name}")
                print()
            
            return valid_drafts
            
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
        
        # 使用默认帧率 30 FPS
        framerate = ExportFramerate.FR_30
        print("\n🎬 使用默认帧率: 30 FPS")
                
        return resolution, framerate
        
    def select_error_handling_mode(self):
        """选择错误处理模式"""
        self.print_header("错误处理设置")
        
        print("当遇到草稿不存在等错误时:")
        print("1. 自动跳过继续下一个 (推荐)")
        print("2. 每次询问用户操作")
        
        while True:
            try:
                choice = input("请选择错误处理模式 (1-2, 默认1): ").strip()
                if not choice:
                    choice = "1"
                    
                choice = int(choice)
                
                if choice == 1:
                    self.auto_skip_missing = True
                    print("✅ 已设置为自动跳过模式")
                    break
                elif choice == 2:
                    self.auto_skip_missing = False 
                    print("✅ 已设置为询问模式")
                    break
                else:
                    self.print_error("请输入1或2")
                    
            except ValueError:
                self.print_error("请输入有效的数字")
    
    def select_draft_action(self):
        """选择草稿处理方式"""
        self.print_header("草稿处理选项")
        
        print("导出完成后对草稿的处理:")
        print("1. 保留草稿")
        print("2. 删除草稿")
        print("⚠️  注意: 删除草稿后无法恢复，请谨慎选择")
        
        while True:
            try:
                choice = input("请选择 (1-2): ").strip()
                choice = int(choice)
                
                if choice == 1:
                    return False  # 不删除
                elif choice == 2:
                    # 二次确认删除操作
                    print("\n⚠️  您选择了删除草稿，此操作不可恢复!")
                    confirm = input("请再次确认是否要删除导出成功的草稿? (y/n): ").lower().strip()
                    if confirm in ['y', 'yes', '是']:
                        return True   # 删除
                    else:
                        print("已取消删除，将保留草稿")
                        return False  # 不删除
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
        
    def safe_return_to_home(self, ctrl):
        """安全回到目录页"""
        try:
            print("🔄 尝试回到目录页...")
            # 确保重新获取窗口状态
            ctrl.get_window()
            # 尝试回到主页
            ctrl.switch_to_home()
            print("✅ 已成功回到目录页")
            return True
        except Exception as e:
            self.print_warning(f"自动回到目录页失败: {e}")
            self.print_warning("请手动回到剪映目录页后继续")
            return False
    
    def should_auto_skip(self, error_msg):
        """判断是否应该自动跳过该错误"""
        auto_skip_errors = [
            "未找到名为",  # 草稿不存在
            "草稿不存在",
            "DraftNotFound",  # 异常类型
            "文件夹不存在", 
            "路径不存在",
            "draft not found",
            "file not found",
            "no such file"
        ]
        
        error_str = str(error_msg).lower()
        for skip_error in auto_skip_errors:
            if skip_error.lower() in error_str:
                return True
        return False
    
    def should_auto_retry(self, error_msg):
        """判断是否应该自动重试该错误"""
        retry_errors = [
            "导出按钮",  # UI元素未找到，可能需要重试
            "导出窗口",
            "剪映窗口未找到",
            "timeout",
            "超时",
            "网络",
            "connection"
        ]
        
        error_str = str(error_msg).lower()  
        for retry_error in retry_errors:
            if retry_error.lower() in error_str:
                return True
        return False
    
    def handle_export_interruption(self, ctrl, draft_name, error):
        """处理导出中断"""
        self.print_error(f"导出 {draft_name} 时发生错误: {error}")
        
        # 检查是否为可自动跳过的错误
        if self.should_auto_skip(error) and self.auto_skip_missing:
            print(f"🔄 检测到草稿不存在错误，自动跳过继续下一个")
            # 尝试回到目录页
            self.safe_return_to_home(ctrl)
            return 'continue'
        
        # 检查是否为可自动重试的错误
        if self.should_auto_retry(error):
            print(f"🔄 检测到可重试错误，建议重试")
            # 尝试回到目录页
            self.safe_return_to_home(ctrl)
            print(f"💡 建议操作: 重试当前草稿")
        
        # 尝试自动回到目录页
        if not self.safe_return_to_home(ctrl):
            # 如果自动回退失败，询问用户
            print(f"\n⚠️  导出 {draft_name} 失败，需要回到目录页继续后续操作")
            print("请手动回到剪映目录页，然后选择操作:")
        else:
            # 自动回退成功，询问用户后续操作
            print(f"⚠️  导出 {draft_name} 失败，已回到目录页")
        
        # 提供智能建议
        if self.should_auto_retry(error):
            print("💡 建议: 这是一个临时性错误，建议选择重试 (r)")
        else:
            print("💡 建议: 可能是草稿或设置问题，建议跳过继续 (c)")
            
        while True:
            choice = input("请选择: (c)继续下一个 / (r)重试当前 / (s)停止批量导出: ").lower().strip()
            if choice in ['c', 'continue', '继续']:
                return 'continue'
            elif choice in ['r', 'retry', '重试']:
                return 'retry'
            elif choice in ['s', 'stop', '停止']:
                return 'stop'
            else:
                print("请输入 c(继续) / r(重试) / s(停止)")
    
    def export_single_draft(self, ctrl, draft_name, export_path, resolution, framerate):
        """导出单个草稿，包含重试逻辑"""
        max_retries = 2
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    print(f"🔄 第 {attempt + 1} 次尝试导出 {draft_name}")
                    # 重试前先确保回到目录页
                    if not self.safe_return_to_home(ctrl):
                        return False
                    time.sleep(self.automation_delay)
                
                print(f"⏱️  等待 {self.automation_delay}秒 (自动化延迟)...")
                time.sleep(self.automation_delay)
                
                # 导出草稿
                print(f"🚀 开始导出草稿...")
                ctrl.export_draft(draft_name, export_path, 
                                resolution=resolution, 
                                framerate=framerate)
                
                print(f"⏱️  等待 {self.long_delay}秒 (导出后延迟)...")
                time.sleep(self.long_delay)
                
                return True
                
            except KeyboardInterrupt:
                print(f"\n⚠️  用户中断了 {draft_name} 的导出")
                raise
            except Exception as e:
                if attempt < max_retries:
                    self.print_warning(f"导出尝试 {attempt + 1} 失败: {e}")
                    self.print_warning(f"将进行第 {attempt + 2} 次尝试...")
                    
                    # 尝试回到目录页准备重试
                    self.safe_return_to_home(ctrl)
                    time.sleep(self.short_delay)
                else:
                    # 所有重试都失败了
                    raise e
        
        return False
    
    def export_drafts(self, drafts_to_export, resolution, framerate, delete_after_export):
        """批量导出草稿"""
        self.print_header("开始批量导出")
        
        if not self.check_jianying_support():
            return False
            
        print(f"准备导出 {len(drafts_to_export)} 个草稿...")
        print("⚠️  请确保剪映已打开并位于目录页")
        print("💡 导出过程中如遇问题，脚本会尝试自动回到目录页继续")
        
        input("准备就绪后按回车键开始导出...")
        
        try:
            # 初始化剪映控制器
            ctrl = draft.JianyingController()
            
            success_count = 0
            failed_drafts = []
            skipped_drafts = []
            
            i = 0
            while i < len(drafts_to_export):
                draft_name = drafts_to_export[i]
                print(f"\n[{i+1}/{len(drafts_to_export)}] 正在处理: {draft_name}")
                
                try:
                    # 设置导出路径
                    export_path = os.path.join(self.export_folder, f"{draft_name}.mp4")
                    
                    # 导出单个草稿
                    if self.export_single_draft(ctrl, draft_name, export_path, resolution, framerate):
                        self.print_success(f"导出成功: {export_path}")
                        success_count += 1
                        
                        # 如果选择删除草稿
                        if delete_after_export:
                            try:
                                print(f"⏱️  等待 {self.short_delay}秒后删除草稿...")
                                time.sleep(self.short_delay)
                                
                                # 确保草稿文件夹存在再删除
                                if self.draft_folder.has_draft(draft_name):
                                    self.draft_folder.remove(draft_name)
                                    print(f"🗑️  已删除草稿: {draft_name}")
                                    
                                    # 验证删除是否成功
                                    if self.draft_folder.has_draft(draft_name):
                                        self.print_warning(f"草稿 {draft_name} 删除可能未成功，请检查")
                                    else:
                                        print(f"✅ 确认草稿 {draft_name} 已完全删除")
                                else:
                                    self.print_warning(f"草稿 {draft_name} 不存在，无法删除")
                                    
                            except PermissionError as e:
                                self.print_warning(f"删除草稿失败 - 权限不足: {e}")
                                self.print_warning("可能剪映仍在使用该草稿，请关闭剪映后手动删除")
                            except Exception as e:
                                self.print_warning(f"删除草稿失败: {e}")
                                self.print_warning(f"草稿路径: {os.path.join(self.draft_folder.folder_path, draft_name)}")
                        
                        # 成功后移到下一个
                        i += 1
                    else:
                        # 导出失败，进入中断处理流程
                        action = self.handle_export_interruption(ctrl, draft_name, "多次重试均失败")
                        if action == 'continue':
                            failed_drafts.append(draft_name)
                            i += 1
                        elif action == 'retry':
                            # 保持当前索引，重新尝试
                            continue
                        elif action == 'stop':
                            # 停止批量导出
                            self.print_warning("用户选择停止批量导出")
                            skipped_drafts.extend(drafts_to_export[i+1:])
                            break
                    
                except KeyboardInterrupt:
                    print(f"\n⚠️  用户中断操作")
                    # 处理中断
                    action = self.handle_export_interruption(ctrl, draft_name, "用户中断")
                    if action == 'continue':
                        failed_drafts.append(draft_name)
                        i += 1
                    elif action == 'retry':
                        continue
                    elif action == 'stop':
                        self.print_warning("用户选择停止批量导出")
                        skipped_drafts.extend(drafts_to_export[i+1:])
                        break
                        
                except Exception as e:
                    # 处理其他异常
                    action = self.handle_export_interruption(ctrl, draft_name, str(e))
                    if action == 'continue':
                        failed_drafts.append(draft_name)
                        i += 1
                    elif action == 'retry':
                        continue
                    elif action == 'stop':
                        self.print_warning("用户选择停止批量导出")
                        skipped_drafts.extend(drafts_to_export[i+1:])
                        break
                        
            # 显示导出结果
            self.print_header("导出完成")
            print(f"✅ 成功导出: {success_count} 个草稿")
            
            if failed_drafts:
                print(f"❌ 导出失败: {len(failed_drafts)} 个草稿")
                print("失败的草稿:")
                for draft_name in failed_drafts:
                    print(f"  - {draft_name}")
            
            if skipped_drafts:
                print(f"⏭️  跳过导出: {len(skipped_drafts)} 个草稿")
                print("跳过的草稿:")
                for draft_name in skipped_drafts:
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
        
        # 设置自动化延迟
        self.setup_automation_delays()
        
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
        
        # 选择错误处理模式
        self.select_error_handling_mode()
        
        # 选择草稿处理方式
        delete_after_export = self.select_draft_action()
        
        # 确认导出
        self.print_header("确认导出")
        print(f"将要导出的草稿 ({export_count} 个):")
        for i, draft_name in enumerate(drafts_to_export, 1):
            print(f"  {i}. {draft_name}")
            
        print(f"\n导出文件夹: {self.export_folder}")
        print(f"分辨率: {resolution}")
        print(f"帧率: {framerate} (默认)")
        print(f"导出后: {'删除草稿' if delete_after_export else '保留草稿'}")
        print(f"错误处理: {'自动跳过' if self.auto_skip_missing else '询问用户'}")
        print(f"自动化延迟: {self.automation_delay}秒 / {self.long_delay}秒 / {self.short_delay}秒")
        
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