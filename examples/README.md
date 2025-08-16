# pyJianYingDraft 示例代码

这个目录包含了 pyJianYingDraft 库的各种使用示例。

## 草稿复制工具

### 1. 交互式CLI工具 (`interactive_cli.py`) ⭐ 推荐

基于 `simple_copy_draft.py` 重新设计的交互式命令行工具，支持草稿复制和视频片段替换的完整工作流程。

**功能特色:**
- 🎯 菜单驱动的友好界面
- 📋 完整的草稿复制流程
- 🎥 基于materials数据的视频片段替换
- 📊 详细的草稿信息显示
- 🔧 智能路径检测和错误处理
- 💾 支持新版剪映 (draft_info.json)

**使用方法:**
```bash
# 启动交互式工具
python examples/interactive_cli.py
```

**主要功能:**
1. **选择源草稿** - 浏览和选择要复制的草稿
2. **复制草稿** - 执行草稿复制操作
3. **设置素材文件夹** - 配置视频替换素材
4. **替换视频素材** - 基于materials数据替换视频片段
5. **查看草稿信息** - 显示详细的草稿元数据
6. **设置路径** - 配置草稿文件夹路径

详细使用指南请参考：[interactive_cli_guide.md](interactive_cli_guide.md)

### 2. 完整版演示工具 (`copy_draft_demo.py`)

功能齐全的草稿复制演示工具，包含详细的步骤说明和错误处理。

**使用方法:**

```bash
# 交互式模式（如果支持）
python examples/copy_draft_demo.py

# 非交互模式，使用第一个可用草稿
python examples/copy_draft_demo.py --non-interactive

# 指定源草稿
python examples/copy_draft_demo.py --source-draft "草稿名称"

# 指定草稿文件夹路径
python examples/copy_draft_demo.py --draft-folder "/path/to/jianying/drafts"

# 指定目标草稿名称
python examples/copy_draft_demo.py --target-name "新草稿名称"
```

**命令行参数:**
- `--draft-folder`: 剪映草稿文件夹路径
- `--source-draft`: 指定要复制的源草稿名称
- `--target-name`: 指定目标草稿名称
- `--non-interactive`: 非交互模式，使用第一个可用草稿

### 3. 简化版复制工具 (`simple_copy_draft.py`)

专门用于指定草稿复制的轻量级工具，无交互式输入。

**使用方法:**

```bash
# 复制指定草稿
python examples/simple_copy_draft.py "源草稿名称"

# 复制并指定目标名称
python examples/simple_copy_draft.py "源草稿名称" --target-name "目标草稿名称"

# 列出所有可用草稿
python examples/simple_copy_draft.py --list dummy

# 指定草稿文件夹路径
python examples/simple_copy_draft.py "源草稿名称" --draft-folder "/path/to/jianying/drafts"
```

**命令行参数:**
- `source_draft`: 要复制的源草稿名称（必需）
- `--draft-folder`: 剪映草稿文件夹路径
- `--target-name`: 目标草稿名称（可选）
- `--list`: 列出所有可用草稿

## 使用示例

### 基本复制

```bash
# 复制草稿"我的项目"为"我的项目_备份"
python examples/simple_copy_draft.py "我的项目" --target-name "我的项目_备份"
```

### 批量操作

```bash
# 先列出所有草稿
python examples/simple_copy_draft.py --list dummy

# 复制多个草稿
python examples/simple_copy_draft.py "项目A"
python examples/simple_copy_draft.py "项目B"
python examples/simple_copy_draft.py "项目C"
```

## 其他工具和示例

### 4. 草稿信息读取器 (`draft_info_reader.py`)

专门用于读取和显示草稿详细信息的工具，支持新版剪映的 draft_info.json 格式。

**使用方法:**
```bash
# 查看指定草稿信息
python examples/draft_info_reader.py "草稿名称"

# 指定草稿文件夹路径
python examples/draft_info_reader.py "草稿名称" "/path/to/drafts"
```

**显示信息:**
- 📐 分辨率和宽高比
- ⏱️ 时长和帧率  
- 🎬 轨道统计
- 📦 素材统计
- 🎥 视频素材详情

### 5. 批量替换工具

- `batch_replace_materials.py`: 批量替换素材演示
- `demo_batch_replace.py`: 批量替换demo  
- `interactive_batch_replace.py`: 交互式批量替换

### 6. 配置和工具文件

这些文件提供了配置管理和辅助功能，主要由其他工具调用。

## 素材文件

`materials/` 目录包含了示例素材文件，用于演示和测试：
- `part1/`, `part2/`, `part3/`: 示例视频文件
- `background/`: 背景图片文件
- `videos/`, `audios/`, `images/`: 分类的素材文件夹

## 注意事项

1. **剪映版本兼容性**: 
   - 模板复制功能支持剪映 5.9 及以下版本
   - 剪映 6.0+ 使用了加密，模板复制可能报错但草稿仍会创建成功
   - 新建草稿功能支持所有版本

2. **路径设置**:
   - 默认草稿路径为 macOS 下的路径
   - Windows 用户需要修改为类似 `C:/Users/用户名/AppData/Local/JianyingPro/User Data/Projects/com.lveditor.draft`

3. **错误处理**:
   - 即使 API 报错，草稿可能仍然创建成功
   - 工具会自动检查草稿是否实际创建

## 常见问题

**Q: 提示"草稿文件夹路径不存在"怎么办？**
A: 使用 `--draft-folder` 参数指定正确的剪映草稿文件夹路径。

**Q: API 报错但草稿创建成功是正常的吗？**
A: 是的，这是因为新版剪映使用了加密。工具会自动检查并确认草稿是否真正创建成功。

**Q: 如何找到剪映草稿文件夹？**
A: 
- macOS: `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft`
- Windows: `%LOCALAPPDATA%/JianyingPro/User Data/Projects/com.lveditor.draft`