# 视频封面图插入工具 (UltraThink)

## 功能说明

这个工具可以自动为视频文件添加封面图效果：
- 📸 提取视频最后一帧作为封面图
- 🎬 将封面图插入到视频开头
- ✨ 播放效果：先显示封面图，然后播放原始视频内容

## 安装要求

### 必需工具
- **Python 3.6+**
- **FFmpeg** (用于视频处理)

### FFmpeg 安装

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
1. 下载 FFmpeg: https://ffmpeg.org/download.html
2. 解压并添加到系统环境变量 PATH

## 使用方法

### 1. 运行脚本
```bash
cd examples
python video_cover_inserter.py
```

### 2. 交互式配置
脚本会引导你完成以下设置：

1. **输入视频文件夹路径**
   - 支持拖拽文件夹或手动输入路径
   - 自动验证路径有效性

2. **查看扫描结果**
   - 显示找到的所有视频文件
   - 支持格式：.mp4, .mov, .avi, .mkv, .flv, .wmv, .m4v

3. **配置封面图设置**
   - 选择封面图显示时长：1秒/2秒/3秒/5秒/自定义
   - 推荐：2秒（默认）

4. **确认处理**
   - 查看处理摘要
   - 确认开始批量处理

### 3. 处理结果

处理完成后会在原文件夹下创建 `processed_with_cover` 目录，包含：

- **处理后的视频**：`原文件名_with_cover.mp4`
- **独立封面图**：`原文件名_cover.jpg`

## 示例

```
原始文件夹结构：
📁 videos/
  ├── 视频1.mp4
  ├── 视频2.mov
  └── 视频3.mp4

处理后结构：
📁 videos/
  ├── 视频1.mp4
  ├── 视频2.mov  
  ├── 视频3.mp4
  └── 📁 processed_with_cover/
      ├── 视频1_with_cover.mp4    ← 带封面的视频
      ├── 视频1_cover.jpg         ← 封面图
      ├── 视频2_with_cover.mp4
      ├── 视频2_cover.jpg
      ├── 视频3_with_cover.mp4
      └── 视频3_cover.jpg
```

## 技术原理

1. **封面图提取**：使用FFmpeg从视频最后一秒提取高质量帧
2. **封面视频生成**：将静态图片转换为指定时长的视频片段
3. **视频合并**：将封面视频与原视频无缝拼接

## 注意事项

- ⚠️ 处理大文件需要足够的磁盘空间
- 📏 封面图会自动适配原视频分辨率
- 🎯 输出视频保持原始质量和帧率
- 🔄 支持批量处理，失败的文件会单独列出

## 故障排除

### FFmpeg 相关错误
```bash
# 检查 FFmpeg 是否正确安装
ffmpeg -version

# 如果提示命令不存在，重新安装 FFmpeg
```

### 权限错误
```bash
# macOS/Linux 给脚本执行权限
chmod +x video_cover_inserter.py
```

### 内存不足
- 处理大量或大尺寸视频时，确保有足够的系统内存
- 可以分批处理，减少同时处理的文件数量

## 自定义设置

可以修改脚本中的参数：

```python
# 默认封面图显示时长
self.cover_duration = 2.0  # 秒

# 支持的视频格式
self.video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.m4v']
```

## 效果预览

**处理前**：
- 视频直接播放原始内容

**处理后**：
- 0-2秒：显示封面图（最后一帧）
- 2秒后：播放原始视频内容
- 总时长 = 原时长 + 封面时长

这就是 **UltraThink 效果** - 给视频添加一个吸引眼球的开头！