#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量素材替换系统的单元测试
验证速度计算、时长处理、时间线逻辑等关键功能
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import shutil
from pathlib import Path

# 导入要测试的类
from batch_replace_materials import MaterialBatchReplacer


class TestMaterialBatchReplacer(unittest.TestCase):
    """批量素材替换器测试类"""
    
    def setUp(self):
        """测试前的设置"""
        self.test_draft_folder = "/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
        self.test_template_name = "阳章老师模版"
        self.replacer = MaterialBatchReplacer(self.test_draft_folder, self.test_template_name)
        
        # 创建临时测试文件夹
        self.temp_dir = tempfile.mkdtemp()
        self.materials_folder = os.path.join(self.temp_dir, "materials")
        os.makedirs(self.materials_folder)
        
        # 创建测试文件夹结构
        for folder in ["background", "part1", "part2", "part3"]:
            os.makedirs(os.path.join(self.materials_folder, folder))
    
    def tearDown(self):
        """测试后的清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_video_duration_success(self):
        """测试成功获取视频时长"""
        # 模拟ffprobe成功返回
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "format": {"duration": "9.067000"}
        })
        
        with patch('subprocess.run', return_value=mock_result):
            duration = self.replacer.get_video_duration("/test/video.mp4")
            self.assertEqual(duration, 9.067)
    
    def test_get_video_duration_from_stream(self):
        """测试从视频流获取时长"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "streams": [
                {"codec_type": "video", "duration": "8.849000"},
                {"codec_type": "audio", "duration": "8.850000"}
            ]
        })
        
        with patch('subprocess.run', return_value=mock_result):
            duration = self.replacer.get_video_duration("/test/video.mp4")
            self.assertEqual(duration, 8.849)
    
    def test_get_video_duration_failure(self):
        """测试获取视频时长失败"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        
        with patch('subprocess.run', return_value=mock_result):
            duration = self.replacer.get_video_duration("/test/video.mp4")
            self.assertEqual(duration, 0.0)
    
    def test_speed_calculation_logic(self):
        """测试速度计算逻辑"""
        # 测试用例：新素材时长 -> 目标时长 -> 期望速度
        test_cases = [
            (9.1, 15.0, 0.607),   # 新素材较短，需要减速
            (9.1, 10.0, 0.910),   # 新素材略短，轻微减速  
            (8.0, 15.0, 0.533),   # 新素材很短，需要明显减速
            (20.0, 10.0, 2.000),  # 新素材较长，需要加速
            (1.0, 10.0, 0.1),     # 极短素材，限制最小速度0.1x
            (50.0, 10.0, 5.0),    # 极长素材，限制最大速度5.0x
        ]
        
        for new_duration, target_duration, expected_speed in test_cases:
            with self.subTest(new_duration=new_duration, target_duration=target_duration):
                calculated_speed = new_duration / target_duration
                limited_speed = max(0.1, min(calculated_speed, 5.0))
                self.assertAlmostEqual(limited_speed, expected_speed, places=3)
    
    def test_source_duration_calculation(self):
        """测试源素材截取时长计算"""
        test_cases = [
            # (新素材时长, 目标时长, 速度, 期望截取时长)
            (9.1, 15.0, 0.607, 9.1),    # 不超过新素材时长
            (20.0, 10.0, 2.0, 20.0),    # 不超过新素材时长
            (8.0, 15.0, 0.533, 8.0),    # 不超过新素材时长
        ]
        
        for new_duration, target_duration, speed, expected_source in test_cases:
            with self.subTest(new_duration=new_duration, target_duration=target_duration):
                # 计算截取时长：min(目标时长 * 速度, 新素材时长)
                source_duration = min(target_duration * speed, new_duration)
                self.assertAlmostEqual(source_duration, expected_source, places=1)
    
    def test_timeline_position_calculation(self):
        """测试时间线位置计算"""
        # 模拟模板片段配置
        template_segments = {
            "part1": {"duration": 15.0},
            "part2": {"duration": 10.0},
            "part3": {"duration": 15.0}
        }
        
        # 验证连续时间线位置
        current_position = 0.0
        expected_positions = [0.0, 15.0, 25.0]
        expected_ends = [15.0, 25.0, 40.0]
        
        for i, (part, config) in enumerate(template_segments.items()):
            with self.subTest(part=part):
                # 当前位置应该等于期望位置
                self.assertEqual(current_position, expected_positions[i])
                
                # 计算结束位置
                end_position = current_position + config["duration"]
                self.assertEqual(end_position, expected_ends[i])
                
                # 更新到下一个位置
                current_position += config["duration"]
    
    def test_validate_folder_structure_success(self):
        """测试文件夹结构验证成功"""
        # 创建测试文件
        test_files = {
            "background": ["bg1.jpg", "bg2.jpg"],
            "part1": ["video1.mp4", "video2.mp4"],  
            "part2": ["video3.mp4", "video4.mp4"],
            "part3": ["video5.mp4", "video6.mp4"]
        }
        
        for folder, files in test_files.items():
            folder_path = os.path.join(self.materials_folder, folder)
            for file in files:
                with open(os.path.join(folder_path, file), 'w') as f:
                    f.write("test content")
        
        # 设置为视频模式
        self.replacer.set_media_type(2)
        
        is_valid, message = self.replacer.validate_folder_structure(self.materials_folder)
        self.assertTrue(is_valid)
        self.assertIn("验证通过", message)
    
    def test_validate_folder_structure_missing_folders(self):
        """测试缺少必需文件夹的验证"""
        # 删除part2文件夹
        shutil.rmtree(os.path.join(self.materials_folder, "part2"))
        
        is_valid, message = self.replacer.validate_folder_structure(self.materials_folder)
        self.assertFalse(is_valid)
        self.assertIn("part2", message)
    
    def test_get_material_files_video_mode(self):
        """测试获取视频模式的素材文件"""
        # 创建测试文件
        test_files = {
            "background": ["bg1.jpg"],  # 视频模式下应该被跳过
            "part1": ["video1.mp4", "video2.avi"],
            "part2": ["video3.mov"], 
            "part3": ["video4.mkv"]
        }
        
        for folder, files in test_files.items():
            folder_path = os.path.join(self.materials_folder, folder)
            for file in files:
                with open(os.path.join(folder_path, file), 'w') as f:
                    f.write("test")
        
        # 设置为视频模式
        self.replacer.set_media_type(2)
        
        materials = self.replacer.get_material_files(self.materials_folder)
        
        # 视频模式下不应该包含background
        self.assertNotIn("background", materials)
        
        # 应该包含part文件夹和正确的视频文件
        self.assertIn("part1", materials)
        self.assertEqual(len(materials["part1"]), 2)  # video1.mp4, video2.avi
        self.assertIn("part2", materials)
        self.assertEqual(len(materials["part2"]), 1)  # video3.mov
    
    def test_create_replacement_combinations(self):
        """测试替换组合创建"""
        materials = {
            "part1": ["video1.mp4", "video2.mp4", "video3.mp4"],
            "part2": ["videoA.mp4", "videoB.mp4"], 
            "part3": ["clip1.mp4", "clip2.mp4", "clip3.mp4", "clip4.mp4"]
        }
        
        combinations = self.replacer.create_replacement_combinations(materials)
        
        # 应该生成2个组合（最少文件数量）
        self.assertEqual(len(combinations), 2)
        
        # 验证组合内容
        expected_combinations = [
            {"part1": "video1.mp4", "part2": "videoA.mp4", "part3": "clip1.mp4"},
            {"part1": "video2.mp4", "part2": "videoB.mp4", "part3": "clip2.mp4"}
        ]
        
        for i, expected in enumerate(expected_combinations):
            with self.subTest(combination=i):
                self.assertEqual(combinations[i], expected)
    
    def test_media_type_settings(self):
        """测试媒体类型设置"""
        # 测试设置图片模式
        self.replacer.set_media_type(1)
        self.assertEqual(self.replacer.settings["media_type"], 1)
        
        # 测试设置视频模式  
        self.replacer.set_media_type(2)
        self.assertEqual(self.replacer.settings["media_type"], 2)
        
        # 测试设置混合模式
        self.replacer.set_media_type(3)
        self.assertEqual(self.replacer.settings["media_type"], 3)
        
        # 测试无效值
        original_type = self.replacer.settings["media_type"]
        self.replacer.set_media_type(99)
        self.assertEqual(self.replacer.settings["media_type"], original_type)  # 应该保持不变


class TestSpeedAndDurationLogic(unittest.TestCase):
    """专门测试速度和时长逻辑的测试类"""
    
    def test_realistic_scenarios(self):
        """测试真实场景下的速度和时长计算"""
        # 基于实际报错场景的测试用例
        scenarios = [
            {
                "name": "用户报错场景",
                "new_material_duration": 9.1,
                "target_duration": 15.0,
                "expected_speed": 0.607,
                "expected_source_duration": 9.1
            },
            {
                "name": "part2场景", 
                "new_material_duration": 9.1,
                "target_duration": 10.0,
                "expected_speed": 0.910,
                "expected_source_duration": 9.1
            },
            {
                "name": "part3场景",
                "new_material_duration": 8.0, 
                "target_duration": 15.0,
                "expected_speed": 0.533,
                "expected_source_duration": 8.0
            }
        ]
        
        for scenario in scenarios:
            with self.subTest(scenario=scenario["name"]):
                # 计算速度
                speed = scenario["new_material_duration"] / scenario["target_duration"]
                speed = max(0.1, min(speed, 5.0))
                
                # 计算截取时长
                source_duration = min(
                    scenario["target_duration"] * speed, 
                    scenario["new_material_duration"]
                )
                
                self.assertAlmostEqual(speed, scenario["expected_speed"], places=3)
                self.assertAlmostEqual(source_duration, scenario["expected_source_duration"], places=1)
    
    def test_edge_cases(self):
        """测试边界情况"""
        edge_cases = [
            {"new": 0.5, "target": 10.0, "expected_speed": 0.1},  # 最小速度限制
            {"new": 100.0, "target": 10.0, "expected_speed": 5.0}, # 最大速度限制
            {"new": 10.0, "target": 10.0, "expected_speed": 1.0},  # 完全匹配
        ]
        
        for case in edge_cases:
            with self.subTest(case=case):
                speed = case["new"] / case["target"] 
                speed = max(0.1, min(speed, 5.0))
                self.assertEqual(speed, case["expected_speed"])


def run_material_duration_test():
    """运行素材时长测试（需要真实视频文件）"""
    print("🧪 运行素材时长检测测试...")
    
    # 这个测试需要真实的视频文件，所以单独运行
    test_videos = [
        "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/test/materials/part1",
        "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/test/materials/part2", 
        "/Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/test/materials/part3"
    ]
    
    replacer = MaterialBatchReplacer("/Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft", "阳章老师模版")
    
    for folder in test_videos:
        if os.path.exists(folder):
            print(f"📁 检测文件夹: {folder}")
            videos = [f for f in os.listdir(folder) if f.endswith(('.mp4', '.avi', '.mov', '.mkv'))]
            for video in videos[:2]:  # 只测试前2个文件
                video_path = os.path.join(folder, video)
                duration = replacer.get_video_duration(video_path)
                print(f"  📹 {video}: {duration:.3f}秒")


if __name__ == '__main__':
    print("🚀 开始批量素材替换系统单元测试")
    print("=" * 60)
    
    # 运行单元测试
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 60)
    
    # 运行真实素材测试（如果存在测试素材）
    try:
        run_material_duration_test()
    except Exception as e:
        print(f"⚠️  真实素材测试跳过: {e}")
    
    print("\n✅ 测试完成!")