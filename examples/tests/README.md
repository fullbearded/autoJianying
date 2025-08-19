# Tests Directory

这个目录包含了所有测试文件和调试脚本，用于验证 pyJianYingDraft 项目的各种功能。

## 📁 目录结构

### 🧪 测试脚本
- `test_*.py` - 各种功能测试脚本
- `debug_*.py` - 调试和问题排查脚本  
- `diagnose_*.py` - 诊断工具

### 🎬 视频处理测试
- `video_cover_inserter_fixed.py` - 修复版本的视频封面插入器
- `test_videos/` - 测试用视频文件和输出结果

## 📋 主要测试文件说明

### 视频封面插入相关
- `test_frame_fix.py` - 测试帧数逻辑修复效果
- `test_mov_format.py` - 测试MOV格式处理
- `test_lossless_merge.py` - 测试无损合并功能
- `debug_audio_issue.py` - 调试音频处理时长问题
- `diagnose_bug.py` - 诊断视频时长压缩问题

### 其他功能测试
- `test_complete_workflow.py` - 完整工作流测试
- `test_audio_subtitle.py` - 音频字幕测试
- `test_perfect_match.py` - 完美匹配测试

## 🎯 使用方法

在 `/examples` 目录下运行测试：

```bash
# 切换到examples目录
cd /Users/dada/Desktop/0_SCYS/0_coding/github/pyJianYingDraft/examples

# 运行特定测试
python tests/test_frame_fix.py

# 运行视频封面插入修复版本
python tests/video_cover_inserter_fixed.py
```

## 📊 测试数据

`test_videos/` 目录包含：
- 测试用视频文件
- 各种测试的输出结果
- 调试和验证用的中间文件

这些文件帮助验证功能正确性和排查问题。