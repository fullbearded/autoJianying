# 📑 文件索引

快速查找和定位项目中的文件。

## 🔍 按功能分类

### 🎯 推荐使用（新用户必看）
| 文件名 | 功能 | 优先级 |
|--------|------|--------|
| `QUICK_START.md` | 5分钟快速开始指南 | ⭐⭐⭐ |
| `config_editor.py` | 配置编辑器 | ⭐⭐⭐ |
| `config_batch_replace.py` | 主要批量替换工具 | ⭐⭐⭐ |
| `setup_materials_folder.py` | 文件夹结构创建 | ⭐⭐ |

### 📋 配置管理
| 文件名 | 功能 | 使用场景 |
|--------|------|----------|
| `config/settings.json` | 主配置文件 | 存储所有系统设置 |
| `config_manager.py` | 配置管理器 | 查看配置状态 |
| `config_editor.py` | 配置编辑器 | 修改系统配置 |
| `config/README.md` | 配置说明 | 了解配置选项 |

### 🎬 批量替换工具
| 文件名 | 功能 | 特点 |
|--------|------|------|
| `config_batch_replace.py` | 配置驱动替换 | 推荐使用，功能完整 |
| `interactive_batch_replace.py` | 交互式替换 | 临时参数调整 |
| `batch_replace_materials.py` | 基础替换工具 | 原始版本，需修改代码 |

### 📁 文件管理
| 文件名 | 功能 | 用途 |
|--------|------|------|
| `setup_materials_folder.py` | 创建文件夹结构 | 初始化项目 |
| `list_drafts.py` | 列出草稿 | 查看可用模板 |
| `materials/` | 素材文件夹 | 存放替换素材 |

### 🔍 草稿分析工具
| 文件名 | 功能 | 适用草稿类型 |
|--------|------|-------------|
| `inspect_draft.py` | 标准草稿分析 | 简单草稿 |
| `inspect_complex_draft.py` | 复合草稿分析 | 复杂模板草稿 |
| `inspect_materials.py` | 素材文件分析 | 所有草稿 |

### 🧪 测试和演示
| 文件名 | 功能 | 测试内容 |
|--------|------|----------|
| `test_media_types.py` | 媒体类型测试 | 图片/视频/混合模式 |
| `test_unlimited_parts.py` | 扩展功能测试 | 多part文件夹支持 |
| `demo_batch_replace.py` | 演示脚本 | 完整流程演示 |

### 📖 文档说明
| 文件名 | 内容 | 详细程度 |
|--------|------|----------|
| `README.md` | 主要说明文档 | 详细完整 |
| `DIRECTORY_GUIDE.md` | 目录文件说明 | 详细完整 |
| `QUICK_START.md` | 快速开始指南 | 简洁实用 |
| `FEATURES.md` | 功能特性说明 | 技术细节 |
| `MEDIA_TYPES.md` | 媒体类型说明 | 专项功能 |
| `FILE_INDEX.md` | 文件索引（本文件） | 快速查找 |

---

## 🚀 使用流程文件映射

### 首次使用流程
1. `QUICK_START.md` → 了解快速开始
2. `config_editor.py` → 配置系统
3. `setup_materials_folder.py` → 创建文件夹
4. `config_batch_replace.py` → 执行替换

### 日常使用流程
1. `config_manager.py` → 检查配置
2. `config_batch_replace.py` → 执行替换

### 问题排查流程
1. `list_drafts.py` → 检查草稿
2. `inspect_complex_draft.py` → 分析模板
3. `test_media_types.py` → 验证功能
4. `config_editor.py` → 调整配置

### 开发测试流程
1. `demo_batch_replace.py` → 演示功能
2. `test_*.py` → 运行测试
3. `inspect_*.py` → 分析结果

---

## 🔧 按技术特性分类

### 核心功能文件
```
batch_replace_materials.py      # 基础批量替换引擎
config_batch_replace.py         # 配置驱动版本
interactive_batch_replace.py    # 交互式版本
```

### 配置系统文件
```
config/settings.json           # JSON配置文件
config_manager.py              # 配置管理API
config_editor.py               # 配置编辑界面
```

### 媒体类型支持
```
test_media_types.py            # 媒体类型测试
MEDIA_TYPES.md                 # 媒体类型说明
```

### 扩展功能文件
```
test_unlimited_parts.py        # 无限制part测试
FEATURES.md                    # 功能特性说明
```

---

## 📊 文件重要性评级

### ⭐⭐⭐ 核心必需文件
- `config_batch_replace.py` - 主要工具
- `config_editor.py` - 配置编辑
- `config/settings.json` - 配置文件
- `QUICK_START.md` - 快速指南

### ⭐⭐ 重要工具文件
- `setup_materials_folder.py` - 文件夹创建
- `config_manager.py` - 配置管理
- `list_drafts.py` - 草稿列表
- `README.md` - 详细文档

### ⭐ 辅助工具文件
- `interactive_batch_replace.py` - 交互式工具
- `inspect_*.py` - 分析工具
- `demo_batch_replace.py` - 演示工具
- 其他文档文件

---

## 🎯 新用户推荐阅读顺序

1. **了解项目**: `QUICK_START.md` (5分钟)
2. **配置系统**: `config_editor.py` (3分钟)
3. **准备素材**: `setup_materials_folder.py` (2分钟)
4. **执行替换**: `config_batch_replace.py` (1分钟)
5. **深入了解**: `DIRECTORY_GUIDE.md` (10分钟)

## 🔧 开发者推荐阅读顺序

1. **系统架构**: `README.md`
2. **技术特性**: `FEATURES.md`
3. **媒体处理**: `MEDIA_TYPES.md`
4. **代码结构**: `batch_replace_materials.py`
5. **配置系统**: `config_manager.py`
6. **测试验证**: `test_*.py`

---

**最后更新**: 2024-12-20