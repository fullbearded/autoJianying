# 媒体类型功能说明

## 📋 新增配置选项

系统新增了媒体类型选择功能，支持三种模式：

### 1. 图片模式 (media_type = 1)
- **用途**: 仅处理图片文件
- **支持格式**: `.jpg`, `.jpeg`, `.png`, `.bmp`
- **应用场景**: 
  - 图片轮播视频制作
  - 产品展示相册
  - 静态内容演示
  - 海报设计合成

### 2. 视频模式 (media_type = 2) [默认]
- **用途**: 仅处理视频文件
- **支持格式**: `.mp4`, `.avi`, `.mov`, `.mkv`
- **应用场景**:
  - 视频片段拼接
  - 多素材混剪
  - 短视频批量制作
  - 视频模板替换

### 3. 混合模式 (media_type = 3)
- **用途**: 同时处理图片和视频文件
- **支持格式**: 图片 + 视频的所有格式
- **应用场景**:
  - 图片+视频混合内容
  - 灵活的素材组合
  - 多媒体演示文稿
  - 复杂项目制作

## 🛠️ 技术实现

### 验证函数改进
```python
# 根据媒体类型检查不同的文件格式
if media_type == 1:  # 仅图片
    img_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
elif media_type == 2:  # 仅视频
    mp4_files = [f for f in files if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
else:  # 图片和视频
    media_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.mp4', '.avi', '.mov', '.mkv'))]
```

### 素材获取改进
```python
# 定义支持的文件扩展名
if media_type == 1:  # 仅图片
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
elif media_type == 2:  # 仅视频
    valid_extensions = ('.mp4', '.avi', '.mov', '.mkv')
else:  # 图片和视频
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.mp4', '.avi', '.mov', '.mkv')
```

### 草稿生成改进
```python
# 根据文件类型创建不同的素材
if file_ext in ['.jpg', '.jpeg', '.png', '.bmp']:
    # 图片文件 - 创建为VideoMaterial（剪映中图片也作为视频处理）
    media_material = draft.VideoMaterial(media_path)
else:
    # 视频文件
    media_material = draft.VideoMaterial(media_path)
```

## 📁 文件夹结构示例

### 图片模式
```
materials/
├── background/         (背景图片，始终为.jpg)
│   ├── bg1.jpg
│   └── bg2.jpg
├── part1/             (图片文件)
│   ├── image1.jpg
│   ├── image2.png
│   └── image3.bmp
├── part2/             (图片文件)
│   ├── photo1.jpeg
│   └── photo2.jpg
└── part3/             (图片文件)
    ├── pic1.png
    └── pic2.bmp
```

### 视频模式
```
materials/
├── background/         (背景图片，始终为.jpg)
│   ├── bg1.jpg
│   └── bg2.jpg
├── part1/             (视频文件)
│   ├── video1.mp4
│   ├── video2.avi
│   └── video3.mov
├── part2/             (视频文件)
│   ├── clip1.mp4
│   └── clip2.mkv
└── part3/             (视频文件)
    ├── scene1.mov
    └── scene2.mp4
```

### 混合模式
```
materials/
├── background/         (背景图片，始终为.jpg)
│   ├── bg1.jpg
│   └── bg2.jpg
├── part1/             (图片或视频)
│   ├── intro.jpg      (图片)
│   └── intro.mp4      (视频)
├── part2/             (图片或视频)
│   ├── content.png    (图片)
│   └── content.avi    (视频)
└── part3/             (图片或视频)
    ├── outro.bmp      (图片)
    └── outro.mov      (视频)
```

## ⚙️ 配置方法

### 1. 程序内设置
```python
from batch_replace_materials import MaterialBatchReplacer

replacer = MaterialBatchReplacer(draft_folder_path)
replacer.set_media_type(1)  # 1=图片, 2=视频, 3=混合
```

### 2. 交互式设置
```bash
python interactive_batch_replace.py
# 运行后会出现选择菜单
```

### 3. 默认设置
- 默认媒体类型：视频模式 (media_type = 2)
- 可在代码中修改 `self.settings["media_type"]` 的默认值

## 🎯 使用建议

### 图片模式适用于：
- 制作产品展示视频
- 创建照片幻灯片
- 设计演示文稿
- 制作静态广告内容

### 视频模式适用于：
- 视频剪辑和拼接
- 短视频批量生产
- 影视素材混剪
- 动态内容制作

### 混合模式适用于：
- 复杂的多媒体项目
- 需要图文并茂的内容
- 教学演示视频
- 营销宣传材料

## 🔧 注意事项

1. **背景文件夹**: 始终只支持 `.jpg` 格式的背景图片
2. **文件命名**: 建议使用有意义的文件名，便于管理
3. **文件大小**: 注意文件大小，过大的文件可能影响处理速度
4. **格式兼容**: 确保选择的媒体类型与实际文件格式匹配
5. **组合生成**: 生成的草稿数量仍然由最少文件数的文件夹决定

## 📊 测试验证

运行测试脚本验证功能：
```bash
python test_media_types.py
```

测试会自动验证：
- 三种媒体类型的文件识别
- 文件夹结构验证
- 素材文件获取
- 组合生成逻辑
- 文件类型标识

这个媒体类型功能大大扩展了系统的灵活性，使其能够适应各种不同的视频制作需求。