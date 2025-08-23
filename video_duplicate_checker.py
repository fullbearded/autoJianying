#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频文件重复检测脚本
功能：
1. 遍历目录下所有视频文件
2. 计算MD5值检测完全重复
3. 解析中文+数字文件名结构，检测相似重复
4. 生成对比报告
5. 提供交互式删除功能
"""

import os
import hashlib
import re
import datetime
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
import difflib

class VideoFile:
    """视频文件信息类"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.file_size = os.path.getsize(file_path)
        self.create_time = os.path.getctime(file_path)
        self.modify_time = os.path.getmtime(file_path)
        self.md5_hash = None
        self.chinese_prefix = None
        self.number_suffix = None
        self._parse_filename()
    
    def _parse_filename(self):
        """解析文件名的中文前缀和数字后缀"""
        name_without_ext = os.path.splitext(self.file_name)[0]
        
        # 更复杂的匹配模式，处理各种格式
        patterns = [
            # 匹配以数字结尾的文件名，如："斧"毛笔字楷书写法。红石书院271
            r'^(.+?)(\d+)$',
            # 匹配中间有数字的情况，如：视频1_final
            r'^(.+?)(\d+)(.*)$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, name_without_ext)
            if match:
                if len(match.groups()) >= 2:
                    # 提取主要部分作为前缀（去掉末尾的数字）
                    prefix_part = match.group(1)
                    number_part = match.group(2)
                    
                    # 清理前缀：去除末尾的特殊字符和空格
                    prefix_part = re.sub(r'[.\s]+$', '', prefix_part)
                    
                    # 只有当前缀包含中文字符时才认为是有效的中文前缀
                    if re.search(r'[\u4e00-\u9fa5]', prefix_part):
                        self.chinese_prefix = prefix_part
                        self.number_suffix = int(number_part)
                        break
    
    def calculate_md5(self) -> str:
        """计算文件MD5值"""
        if self.md5_hash is not None:
            return self.md5_hash
        
        hash_md5 = hashlib.md5()
        with open(self.file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        
        self.md5_hash = hash_md5.hexdigest()
        return self.md5_hash
    
    def get_create_time_str(self) -> str:
        """获取创建时间字符串"""
        return datetime.datetime.fromtimestamp(self.create_time).strftime('%Y-%m-%d %H:%M:%S')
    
    def __str__(self):
        return f"VideoFile(name={self.file_name}, size={self.file_size}, create_time={self.get_create_time_str()})"

class VideoDuplicateChecker:
    """视频重复检测器"""
    
    # 支持的视频格式
    VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg'}
    
    def __init__(self, debug_mode: bool = False):
        self.video_files: List[VideoFile] = []
        self.md5_duplicates: Dict[str, List[VideoFile]] = defaultdict(list)
        self.name_similar_groups: List[List[VideoFile]] = []
        self.debug_mode = debug_mode
    
    def scan_directory(self, directory: str) -> None:
        """扫描目录下的所有视频文件"""
        print(f"正在扫描目录: {directory}")
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                
                if file_ext in self.VIDEO_EXTENSIONS:
                    try:
                        video_file = VideoFile(file_path)
                        self.video_files.append(video_file)
                        if self.debug_mode:
                            print(f"发现视频文件: {file}")
                            if video_file.chinese_prefix:
                                print(f"  解析结果: 前缀='{video_file.chinese_prefix}', 数字={video_file.number_suffix}")
                            else:
                                print(f"  无法解析中文前缀")
                        else:
                            print(f"发现视频文件: {file}")
                    except Exception as e:
                        print(f"处理文件 {file} 时出错: {e}")
        
        print(f"总共发现 {len(self.video_files)} 个视频文件")
        
        if self.debug_mode:
            self.print_parsing_debug_info()
    
    def print_parsing_debug_info(self) -> None:
        """打印文件名解析调试信息"""
        print("\n" + "="*50)
        print("文件名解析调试信息")
        print("="*50)
        
        prefix_groups = defaultdict(list)
        no_prefix_files = []
        
        for video_file in self.video_files:
            if video_file.chinese_prefix:
                prefix_groups[video_file.chinese_prefix].append(video_file)
            else:
                no_prefix_files.append(video_file)
        
        print(f"\n有中文前缀的文件组 ({len(prefix_groups)} 组):")
        for prefix, files in prefix_groups.items():
            print(f"  前缀: '{prefix}' - {len(files)} 个文件")
            for file in files:
                print(f"    - {file.file_name} (数字: {file.number_suffix})")
        
        print(f"\n无法解析前缀的文件 ({len(no_prefix_files)} 个):")
        for file in no_prefix_files[:10]:  # 只显示前10个
            print(f"  - {file.file_name}")
        
        if len(no_prefix_files) > 10:
            print(f"  ... 还有 {len(no_prefix_files) - 10} 个文件")
    
    def calculate_all_md5(self) -> None:
        """计算所有视频文件的MD5值"""
        print("正在计算MD5值...")
        
        for i, video_file in enumerate(self.video_files):
            print(f"计算进度: {i+1}/{len(self.video_files)} - {video_file.file_name}")
            try:
                md5_hash = video_file.calculate_md5()
                self.md5_duplicates[md5_hash].append(video_file)
            except Exception as e:
                print(f"计算 {video_file.file_name} MD5时出错: {e}")
        
        # 保留只有重复文件的组
        self.md5_duplicates = {k: v for k, v in self.md5_duplicates.items() if len(v) > 1}
        print(f"发现 {len(self.md5_duplicates)} 个MD5重复组")
    
    def find_name_similar_groups(self, similarity_threshold: float = 0.85) -> None:
        """查找文件名相似的组"""
        print("正在检测文件名相似的重复文件...")
        
        # 按中文前缀分组，但需要更严格的判断
        prefix_groups = defaultdict(list)
        for video_file in self.video_files:
            if video_file.chinese_prefix:
                prefix_groups[video_file.chinese_prefix].append(video_file)
        
        # 找出有多个文件的组，但要检查是否真的相似
        for prefix, files in prefix_groups.items():
            if len(files) > 1:
                # 进一步检查：如果前缀完全相同，还要检查完整文件名的相似度
                valid_groups = []
                processed = set()
                
                for i, file1 in enumerate(files):
                    if file1.file_name in processed:
                        continue
                    
                    similar_group = [file1]
                    processed.add(file1.file_name)
                    
                    for j, file2 in enumerate(files[i+1:], i+1):
                        if file2.file_name in processed:
                            continue
                        
                        # 计算完整文件名的相似度
                        name1 = os.path.splitext(file1.file_name)[0]
                        name2 = os.path.splitext(file2.file_name)[0]
                        similarity = difflib.SequenceMatcher(None, name1, name2).ratio()
                        
                        # 更严格的判断：相似度要高，且文件大小差异不能太大
                        size_ratio = min(file1.file_size, file2.file_size) / max(file1.file_size, file2.file_size)
                        
                        if similarity >= similarity_threshold and size_ratio >= 0.8:
                            similar_group.append(file2)
                            processed.add(file2.file_name)
                    
                    if len(similar_group) > 1:
                        # 按数字后缀排序
                        similar_group.sort(key=lambda x: x.number_suffix if x.number_suffix else 0)
                        valid_groups.append(similar_group)
                
                self.name_similar_groups.extend(valid_groups)
        
        # 对于没有中文前缀的文件，使用更严格的字符串相似度检测
        no_prefix_files = [f for f in self.video_files if not f.chinese_prefix]
        similar_groups = []
        processed = set()
        
        for i, file1 in enumerate(no_prefix_files):
            if file1.file_name in processed:
                continue
            
            similar_group = [file1]
            processed.add(file1.file_name)
            
            for j, file2 in enumerate(no_prefix_files[i+1:], i+1):
                if file2.file_name in processed:
                    continue
                
                # 计算文件名相似度（去除扩展名）
                name1 = os.path.splitext(file1.file_name)[0]
                name2 = os.path.splitext(file2.file_name)[0]
                similarity = difflib.SequenceMatcher(None, name1, name2).ratio()
                
                # 更严格的判断：高相似度 + 文件大小相近
                size_ratio = min(file1.file_size, file2.file_size) / max(file1.file_size, file2.file_size)
                
                if similarity >= similarity_threshold and size_ratio >= 0.8:
                    similar_group.append(file2)
                    processed.add(file2.file_name)
            
            if len(similar_group) > 1:
                similar_groups.append(similar_group)
        
        self.name_similar_groups.extend(similar_groups)
        print(f"发现 {len(self.name_similar_groups)} 个文件名相似组")
    
    def generate_report(self) -> Dict:
        """生成检测报告"""
        report = {
            'scan_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_files': len(self.video_files),
            'md5_duplicate_groups': len(self.md5_duplicates),
            'name_similar_groups': len(self.name_similar_groups),
            'md5_duplicates': [],
            'name_similar': [],
            'statistics': {
                'total_duplicate_files': 0,
                'total_waste_size': 0
            }
        }
        
        # MD5重复文件信息
        for md5_hash, files in self.md5_duplicates.items():
            group_info = {
                'md5': md5_hash,
                'count': len(files),
                'files': []
            }
            
            # 按创建时间排序，最早的在前面
            files.sort(key=lambda x: x.create_time)
            
            for file in files:
                file_info = {
                    'path': file.file_path,
                    'name': file.file_name,
                    'size': file.file_size,
                    'create_time': file.get_create_time_str(),
                    'is_oldest': file == files[0]
                }
                group_info['files'].append(file_info)
            
            report['md5_duplicates'].append(group_info)
            report['statistics']['total_duplicate_files'] += len(files) - 1
            report['statistics']['total_waste_size'] += files[0].file_size * (len(files) - 1)
        
        # 文件名相似文件信息
        for group in self.name_similar_groups:
            group_info = {
                'chinese_prefix': group[0].chinese_prefix if group[0].chinese_prefix else '无',
                'count': len(group),
                'files': []
            }
            
            # 按创建时间排序
            group.sort(key=lambda x: x.create_time)
            
            for file in group:
                file_info = {
                    'path': file.file_path,
                    'name': file.file_name,
                    'size': file.file_size,
                    'create_time': file.get_create_time_str(),
                    'md5': file.md5_hash,
                    'is_oldest': file == group[0]
                }
                group_info['files'].append(file_info)
            
            report['name_similar'].append(group_info)
        
        return report
    
    def print_report(self, report: Dict) -> None:
        """打印检测报告"""
        print("\n" + "="*80)
        print("视频文件重复检测报告")
        print("="*80)
        print(f"扫描时间: {report['scan_time']}")
        print(f"总文件数: {report['total_files']}")
        print(f"MD5重复组数: {report['md5_duplicate_groups']}")
        print(f"文件名相似组数: {report['name_similar_groups']}")
        print(f"重复文件数: {report['statistics']['total_duplicate_files']}")
        print(f"浪费空间: {report['statistics']['total_waste_size'] / 1024 / 1024:.2f} MB")
        
        if report['md5_duplicates']:
            print("\n" + "-"*50)
            print("MD5完全重复文件:")
            for i, group in enumerate(report['md5_duplicates'], 1):
                print(f"\n组 {i}: {group['count']} 个文件 (MD5: {group['md5'][:8]}...)")
                for file in group['files']:
                    oldest_mark = " [最早]" if file['is_oldest'] else ""
                    print(f"  - {file['name']} ({file['size']} bytes, {file['create_time']}){oldest_mark}")
        
        if report['name_similar']:
            print("\n" + "-"*50)
            print("文件名相似文件:")
            for i, group in enumerate(report['name_similar'], 1):
                print(f"\n组 {i}: {group['count']} 个文件 (前缀: {group['chinese_prefix']})")
                for file in group['files']:
                    oldest_mark = " [最早]" if file['is_oldest'] else ""
                    md5_info = f" MD5: {file['md5'][:8]}..." if file['md5'] else ""
                    print(f"  - {file['name']} ({file['size']} bytes, {file['create_time']}){oldest_mark}{md5_info}")
    
    def save_report(self, report: Dict, output_file: str) -> None:
        """保存报告到JSON文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n报告已保存到: {output_file}")
    
    def interactive_delete(self) -> None:
        """交互式删除重复文件"""
        print("\n" + "="*80)
        print("交互式删除重复文件")
        print("="*80)
        
        deleted_files = []
        deleted_size = 0
        
        # 处理MD5完全重复的文件
        if self.md5_duplicates:
            print("\n处理MD5完全重复的文件:")
            for i, (md5_hash, files) in enumerate(self.md5_duplicates.items(), 1):
                print(f"\n组 {i}: {len(files)} 个文件 (MD5: {md5_hash[:8]}...)")
                
                # 按创建时间排序，最早的在前面
                files.sort(key=lambda x: x.create_time)
                oldest_file = files[0]
                duplicate_files = files[1:]
                
                print(f"保留最早文件: {oldest_file.file_name} ({oldest_file.get_create_time_str()})")
                print("可删除的重复文件:")
                for j, file in enumerate(duplicate_files, 1):
                    print(f"  {j}. {file.file_name} ({file.get_create_time_str()}) - {file.file_size} bytes")
                
                # 询问用户是否删除
                while True:
                    choice = input(f"\n是否删除这 {len(duplicate_files)} 个重复文件? (y/n/s=跳过): ").lower().strip()
                    if choice in ['y', 'yes', '是']:
                        # 删除重复文件
                        for file in duplicate_files:
                            try:
                                os.remove(file.file_path)
                                deleted_files.append(file.file_path)
                                deleted_size += file.file_size
                                print(f"已删除: {file.file_name}")
                            except Exception as e:
                                print(f"删除 {file.file_name} 失败: {e}")
                        break
                    elif choice in ['n', 'no', '否']:
                        print("跳过删除")
                        break
                    elif choice in ['s', 'skip', '跳过']:
                        print("跳过此组")
                        break
                    else:
                        print("请输入 y(是)/n(否)/s(跳过)")
        
        # 处理文件名相似的文件（需要用户判断）
        if self.name_similar_groups:
            print(f"\n处理文件名相似的文件 ({len(self.name_similar_groups)} 组):")
            print("注意: 这些文件只是名称相似，请仔细确认是否为重复文件!")
            
            for i, group in enumerate(self.name_similar_groups, 1):
                print(f"\n组 {i}: {len(group)} 个文件")
                print(f"中文前缀: {group[0].chinese_prefix if group[0].chinese_prefix else '无'}")
                
                # 按创建时间排序
                group.sort(key=lambda x: x.create_time)
                oldest_file = group[0]
                similar_files = group[1:]
                
                # 显示所有文件的详细信息
                for j, file in enumerate(group):
                    oldest_mark = " [最早]" if file == oldest_file else ""
                    md5_info = f" MD5: {file.md5_hash[:8]}..." if file.md5_hash else ""
                    print(f"  {j+1}. {file.file_name} ({file.get_create_time_str()}) - {file.file_size} bytes{oldest_mark}{md5_info}")
                
                while True:
                    choice = input(f"\n是否删除除最早文件外的 {len(similar_files)} 个相似文件? (y/n/s=跳过/v=查看详情): ").lower().strip()
                    if choice in ['y', 'yes', '是']:
                        # 删除相似文件
                        for file in similar_files:
                            try:
                                os.remove(file.file_path)
                                deleted_files.append(file.file_path)
                                deleted_size += file.file_size
                                print(f"已删除: {file.file_name}")
                            except Exception as e:
                                print(f"删除 {file.file_name} 失败: {e}")
                        break
                    elif choice in ['n', 'no', '否']:
                        print("跳过删除")
                        break
                    elif choice in ['s', 'skip', '跳过']:
                        print("跳过此组")
                        break
                    elif choice in ['v', 'view', '查看']:
                        # 显示文件路径
                        print("文件路径详情:")
                        for j, file in enumerate(group):
                            oldest_mark = " [最早]" if file == oldest_file else ""
                            print(f"  {j+1}. {file.file_path}{oldest_mark}")
                    else:
                        print("请输入 y(是)/n(否)/s(跳过)/v(查看详情)")
        
        # 显示删除统计
        print(f"\n删除统计:")
        print(f"删除文件数: {len(deleted_files)}")
        print(f"释放空间: {deleted_size / 1024 / 1024:.2f} MB")
        
        if deleted_files:
            # 保存删除日志
            log_file = f"deleted_files_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"删除时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"删除文件数: {len(deleted_files)}\n")
                f.write(f"释放空间: {deleted_size / 1024 / 1024:.2f} MB\n\n")
                f.write("删除的文件列表:\n")
                for file_path in deleted_files:
                    f.write(f"{file_path}\n")
            print(f"删除日志已保存到: {log_file}")

def main():
    """主函数"""
    print("视频文件重复检测工具")
    print("="*50)
    
    # 获取扫描目录
    directory = input("请输入要扫描的目录路径: ").strip().strip('"')
    if not os.path.exists(directory):
        print("目录不存在!")
        return
    
    # 询问是否开启调试模式
    debug_choice = input("是否开启调试模式(显示文件名解析详情)? (y/n): ").lower().strip()
    debug_mode = debug_choice in ['y', 'yes', '是']
    
    # 询问相似度阈值
    similarity_input = input("请输入文件名相似度阈值(0.1-1.0, 默认0.85, 越高越严格): ").strip()
    try:
        similarity_threshold = float(similarity_input) if similarity_input else 0.85
        similarity_threshold = max(0.1, min(1.0, similarity_threshold))
    except ValueError:
        similarity_threshold = 0.85
        print("输入无效，使用默认阈值0.85")
    
    # 创建检测器实例
    checker = VideoDuplicateChecker(debug_mode)
    
    try:
        # 扫描目录
        checker.scan_directory(directory)
        
        if not checker.video_files:
            print("未发现任何视频文件!")
            return
        
        # 计算MD5
        checker.calculate_all_md5()
        
        # 查找相似文件名
        checker.find_name_similar_groups(similarity_threshold)
        
        # 生成报告
        report = checker.generate_report()
        
        # 打印报告
        checker.print_report(report)
        
        # 保存报告
        output_file = os.path.join(directory, f"video_duplicate_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        checker.save_report(report, output_file)
        
        # 询问是否进行交互式删除
        if (report['md5_duplicate_groups'] > 0 or report['name_similar_groups'] > 0):
            print("\n" + "="*80)
            while True:
                choice = input("是否进行交互式删除重复文件? (y/n): ").lower().strip()
                if choice in ['y', 'yes', '是']:
                    checker.interactive_delete()
                    break
                elif choice in ['n', 'no', '否']:
                    print("跳过删除操作")
                    break
                else:
                    print("请输入 y(是) 或 n(否)")
        else:
            print("\n未发现重复文件，无需删除操作")
        
    except Exception as e:
        print(f"处理过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()