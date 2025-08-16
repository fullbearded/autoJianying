# 测试脚本使用说明

本目录包含了用于测试和演示 pyJianYingDraft 功能的脚本。

## 脚本列表

### 1. list_drafts.py
**功能**: 获取并显示剪映草稿文件夹中的所有草稿列表

**使用方法**:
```bash
python list_drafts.py
```

**说明**: 
- 脚本会自动读取指定的剪映草稿文件夹路径
- 列出所有找到的草稿名称，按编号排序显示
- 显示草稿总数和详细列表
- 如果路径不存在会显示错误信息

**输出示例**:
```
草稿文件夹路径: /Users/dada/Movies/JianyingPro/User Data/Projects/com.lveditor.draft
找到 18 个草稿:
--------------------------------------------------
 1. 花枝秋实
 2. 8月13日
 3. 老悦娃子
 ...
```

### 2. inspect_draft.py
**功能**: 读取指定草稿并获取详细的元素信息（适用于标准草稿）

**使用方法**:
```bash
python inspect_draft.py
```

**说明**:
- 分析草稿的基本信息（时长等）
- 提取素材元数据（贴纸、花字效果的resource_id等）
- 统计各类轨道数量和片段数量
- 仅支持剪映5.9及以下版本的未加密草稿

### 3. inspect_complex_draft.py
**功能**: 分析复合草稿结构（适用于模板草稿和复杂项目）

**使用方法**:
```bash
python inspect_complex_draft.py
```

**说明**:
- 分析草稿的文件结构
- 读取草稿基本信息和模板信息
- 分析子草稿（subdraft）的内容
- 适用于有多个子草稿的复杂模板

**输出示例**:
```
📁 草稿文件结构分析:
✅ draft_info.json
✅ template.json
✅ materials/ 文件夹
✅ subdraft/ 文件夹: 28 个子草稿
```

### 4. inspect_materials.py
**功能**: 详细分析草稿中的材料文件和资源文件

**使用方法**:
```bash
python inspect_materials.py
```

**说明**:
- 分析 materials/ 文件夹中的所有媒体文件
- 显示文件大小、类型和数量统计
- 分析 Resources/ 文件夹结构
- 提供文件类型和大小的统计信息

**输出示例**:
```
📁 Materials 文件夹详细信息:
materials/
  video/
    📄 part1.mp4 (13.4 MB) .mp4
    📄 background.jpg (556.1 KB) .jpg
  audio/
    📄 voice.mp3 (382.4 KB) .mp3
```

### 5. setup_materials_folder.py
**功能**: 创建批量素材替换所需的文件夹结构

**使用方法**:
```bash
python setup_materials_folder.py
```

**说明**:
- 自动创建 materials/ 文件夹及子文件夹结构
- 为每个文件夹生成使用说明
- 检查现有文件数量和类型
- 预估可生成的草稿数量

**文件夹结构**:
```
materials/
├── background/     (放入 .jpg 背景图片)
├── part1/          (放入 .mp4 视频文件)
├── part2/          (放入 .mp4 视频文件)
└── part3/          (放入 .mp4 视频文件)
```

### 6. demo_batch_replace.py
**功能**: 批量素材替换演示脚本，创建示例文件并展示使用流程

**使用方法**:
```bash
python demo_batch_replace.py
```

**说明**:
- 交互式演示批量替换功能
- 自动创建示例素材文件用于测试
- 展示完整的使用流程
- 提供清理功能

### 7. test_unlimited_parts.py
**功能**: 测试无限制part文件夹功能，验证系统对多个part文件夹的支持

**使用方法**:
```bash
python test_unlimited_parts.py
```

**说明**:
- 创建包含5个part文件夹的测试结构
- 验证文件夹验证功能
- 测试材料文件获取和组合生成
- 展示超出原有3个part限制的能力

### 8. test_media_types.py
**功能**: 测试不同媒体类型功能，验证图片、视频和混合模式

**使用方法**:
```bash
python test_media_types.py
```

**说明**:
- 测试图片模式（仅处理图片文件）
- 测试视频模式（仅处理视频文件）  
- 测试混合模式（图片和视频混合）
- 验证文件格式识别和组合生成
- 自动创建测试素材并清理

### 9. interactive_batch_replace.py
**功能**: 交互式批量素材替换，支持用户选择媒体类型

**使用方法**:
```bash
python interactive_batch_replace.py
```

**说明**:
- 提供媒体类型选择菜单
- 根据选择显示相应的文件夹结构指南
- 展示不同模式的使用场景
- 交互式确认和错误处理

### 10. config_manager.py
**功能**: 配置管理器，管理系统的所有配置选项

**使用方法**:
```bash
python config_manager.py
```

**说明**:
- 加载和保存JSON配置文件
- 提供配置的读取、修改和验证功能
- 支持路径验证和配置摘要显示
- 可作为其他脚本的配置后端

### 11. config_editor.py
**功能**: 交互式配置编辑器，可视化编辑所有配置选项

**使用方法**:
```bash
python config_editor.py
```

**说明**:
- 提供友好的菜单界面
- 支持编辑路径、替换设置、模板配置等
- 实时验证配置有效性
- 支持配置保存和重置

### 12. config_batch_replace.py
**功能**: 基于配置文件的批量素材替换系统

**使用方法**:
```bash
python config_batch_replace.py
```

**说明**:
- 从JSON配置文件读取所有设置
- 无需修改代码即可调整参数
- 支持配置验证和错误提示
- 显示详细的配置信息

### 13. batch_replace_materials.py
**功能**: 基于"4翰墨书院模版"进行批量素材替换和草稿生成

**使用方法**:
```bash
# 1. 先运行设置脚本创建文件夹结构
python setup_materials_folder.py

# 2. 将素材文件放入对应文件夹

# 3. 运行批量替换
python batch_replace_materials.py
```

**说明**:
- 以"4翰墨书院模版"为基础模板
- 支持批量替换背景图片和3个视频片段
- 验证文件夹结构和文件数量限制
- 按顺序模式生成多个草稿变体
- 自动处理时长匹配和命名规则

**替换设置**:
- 播放速度: 默认1倍速
- 时长处理: 加速/减速保持时间线不变
- 选取模式: 顺序模式（不重复）
- 文件顺序: 字母顺序
- 命名规则: 使用新素材名
- 媒体类型: 视频（默认）

**功能特性**:
- 支持任意数量的part文件夹（part1, part2, part3, part4...）
- 自动识别额外的part文件夹
- 生成草稿数量 = 最少文件数量的文件夹
- 多媒体类型支持：
  - 图片模式：.jpg, .jpeg, .png, .bmp
  - 视频模式：.mp4, .avi, .mov, .mkv
  - 混合模式：图片和视频文件混合处理

**自定义路径**:
如需修改草稿文件夹路径，编辑脚本中的 `draft_path` 变量：
```python
draft_path = "你的剪映草稿文件夹路径"
```

## 使用流程

### 配置系统使用流程
1. **查看当前配置**:
   ```bash
   python config_manager.py
   ```

2. **编辑配置**:
   ```bash
   python config_editor.py
   ```
   - 设置草稿文件夹路径
   - 设置素材文件夹路径
   - 选择媒体类型和其他参数

3. **执行批量替换**:
   ```bash
   python config_batch_replace.py
   ```

### 传统批量素材替换流程
1. **设置文件夹结构**:
   ```bash
   python setup_materials_folder.py
   ```

2. **添加素材文件**:
   - 将 .jpg 背景图片放入 `materials/background/` 
   - 将 .mp4 视频文件分别放入 `materials/part1/`、`materials/part2/`、`materials/part3/`

3. **执行批量替换**:
   ```bash
   python batch_replace_materials.py
   ```

4. **检查结果**: 在剪映中查看生成的新草稿

## 运行环境要求

- Python 3.8+
- 已安装 pyJianYingDraft 库：`pip install pyJianYingDraft`
- 确保剪映草稿文件夹路径正确

## 常见问题

**Q: 提示"错误: 根文件夹 xxx 不存在"怎么办？**
A: 检查剪映草稿文件夹路径是否正确，可以在剪映的`全局设置` → `草稿位置`中查看正确路径。

**Q: 显示"没有找到任何草稿"？**
A: 可能是路径正确但文件夹为空，或者草稿被移动到其他位置。

**Q: 在 macOS/Linux 上使用有什么限制？**
A: 可以正常获取草稿列表和进行草稿生成，但不支持自动导出功能（仅Windows支持）。