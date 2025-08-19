# 配置文件说明

## 📋 配置文件结构

### settings.json
主配置文件，包含系统的所有配置选项。

## 🔧 配置项说明

### 1. 路径配置 (paths)
```json
{
  "paths": {
    "draft_folder": "剪映草稿文件夹路径",
    "materials_folder": "素材文件夹路径", 
    "output_folder": "输出文件夹路径（可选）"
  }
}
```

**说明**:
- `draft_folder`: 剪映草稿文件夹的绝对路径
- `materials_folder`: 存放替换素材的文件夹路径
- `output_folder`: 导出文件的存放路径（预留）

### 2. 模板配置 (template)
```json
{
  "template": {
    "name": "模板草稿名称",
    "materials": {
      "background": "背景图片文件名",
      "part1": "第一部分视频文件名",
      "part2": "第二部分视频文件名",
      "part3": "第三部分视频文件名",
      "voice": "语音文件名",
      "bgm": "背景音乐文件名"
    }
  }
}
```

### 3. 替换设置 (replacement_settings)

#### 播放速度设置 (speed_mode)
- `1`: 默认按照1倍速播放
- `2`: 默认按照对应的旧素材在时间线上的播放倍速

#### 长度处理方式 (length_handle) 
- `1`: 加速/减速保持时长，时间线不变
- `2`: 裁剪尾部，减速补齐
- `3`: 裁剪头部，减速补齐  
- `4`: 随机裁剪，减速补齐
- `5`: 按原速播放，改变时间线

#### 选取模式 (selection_mode)
- `1`: 顺序模式（不重复）
- `2`: 随机模式（打乱排序）

#### 文件顺序 (shuffle_order)
- `false`: 按字母顺序
- `true`: 随机顺序

#### 删除原文件 (delete_original)
- `false`: 不删除
- `true`: 删除

#### 命名方式 (naming_mode)
- `1`: 使用草稿名
- `2`: 使用新素材名

#### 媒体类型 (media_type)
- `1`: 仅图片 (.jpg, .jpeg, .png, .bmp)
- `2`: 仅视频 (.mp4, .avi, .mov, .mkv)
- `3`: 混合模式（图片+视频）

### 4. 高级设置 (advanced_settings)

```json
{
  "advanced_settings": {
    "segment_duration": {
      "value": "10s",
      "description": "每个片段的默认时长"
    },
    "background_duration": {
      "value": "30s", 
      "description": "背景图片的默认时长"
    },
    "max_part_folders": {
      "value": 0,
      "description": "最大part文件夹数量限制，0表示无限制"
    }
  }
}
```

### 5. UI设置 (ui_settings)

```json
{
  "ui_settings": {
    "language": {
      "value": "zh-CN",
      "options": {
        "zh-CN": "简体中文",
        "en-US": "English"
      }
    },
    "show_progress": {
      "value": true,
      "description": "是否显示处理进度"
    }
  }
}
```

## 🛠️ 配置管理工具

### config_manager.py
配置管理器，提供配置的读取、修改和保存功能。

**主要功能**:
- 加载和保存配置文件
- 获取和设置配置值
- 验证路径配置
- 打印配置摘要

### config_editor.py
交互式配置编辑器。

**使用方法**:
```bash
python config_editor.py
```

**功能菜单**:
1. 查看当前配置
2. 编辑路径配置
3. 编辑替换设置
4. 编辑模板配置
5. 编辑高级设置
6. 验证配置
7. 保存配置
8. 重置为默认配置

### config_batch_replace.py
基于配置文件的批量替换系统。

**使用方法**:
```bash
python config_batch_replace.py
```

## 📝 配置文件示例

### 基本配置示例
```json
{
  "paths": {
    "draft_folder": "/Users/username/Movies/JianyingPro/User Data/Projects/com.lveditor.draft",
    "materials_folder": "/Users/username/Desktop/materials"
  },
  "template": {
    "name": "我的模板"
  },
  "replacement_settings": {
    "media_type": {
      "value": 2,
      "description": "媒体类型选择"
    },
    "naming_mode": {
      "value": 2,
      "description": "新草稿标题命名方式"
    }
  }
}
```

## 🔧 自定义配置

### 1. 修改默认路径
编辑 `paths` 部分的路径设置：
```json
{
  "paths": {
    "draft_folder": "你的剪映草稿文件夹路径",
    "materials_folder": "你的素材文件夹路径"
  }
}
```

### 2. 修改默认设置
编辑 `replacement_settings` 中的 `value` 字段：
```json
{
  "replacement_settings": {
    "media_type": {
      "value": 1
    }
  }
}
```

### 3. 添加新的支持格式
编辑 `advanced_settings`：
```json
{
  "advanced_settings": {
    "supported_video_formats": {
      "value": [".mp4", ".avi", ".mov", ".mkv", ".wmv"]
    }
  }
}
```

## ⚠️  注意事项

1. **路径格式**: 使用绝对路径，在Windows上注意使用正斜杠或双反斜杠
2. **配置备份**: 修改前建议备份原配置文件
3. **语法检查**: 确保JSON格式正确，注意逗号和引号
4. **权限问题**: 确保对配置文件有读写权限

## 🔄 配置迁移

### 备份配置
```bash
cp config/settings.json config/settings_backup.json
```

### 恢复配置
```bash
cp config/settings_backup.json config/settings.json
```

### 重置配置
删除配置文件，程序会自动创建默认配置：
```bash
rm config/settings.json
```