# 书源解析器基础框架

## 概述

这个文件夹包含书源解析器的基础框架，提供了通用的解析能力和动态加载机制。

## 文件说明

### `base_parser.py`
- 包含 `BaseBookSourceParser` 基类
- 提供通用的HTTP请求和HTML解析方法
- 定义了标准的解析接口
- 包含丰富的辅助方法和错误处理

### `parser_loader.py`
- 包含 `ParserLoader` 动态加载器
- 负责发现和加载 `sources` 文件夹中的扩展解析器
- 提供解析器匹配和选择逻辑
- 支持按名称和URL匹配解析器

## 架构设计

### 核心组件

1. **基础解析器** (`BaseBookSourceParser`)
   - 提供通用解析方法
   - 处理HTTP请求和响应
   - 实现基本的HTML解析逻辑
   - 可被扩展解析器继承和重写

2. **动态加载器** (`ParserLoader`)
   - 扫描 `sources` 文件夹
   - 动态导入扩展解析器
   - 管理解析器注册和匹配
   - 提供解析器选择策略

### 工作流程

1. 系统启动时，`ParserLoader` 扫描 `sources` 文件夹
2. 自动导入所有继承自 `BaseBookSourceParser` 的解析器类
3. 根据书源名称或URL匹配最合适的解析器
4. 如果没有找到特定解析器，使用基础解析器

### 扩展机制

扩展解析器应该：
1. 继承 `BaseBookSourceParser` 类
2. 实现 `get_parser_name()` 方法返回唯一标识
3. 实现 `can_handle_url()` 方法判断URL匹配
4. 可选择性重写解析方法以实现特定逻辑

## 使用方法

### 获取解析器

```python
from parsers import get_parser_for_source, get_parser_for_url

# 根据书源名称获取解析器
parser = get_parser_for_source('笔趣阁', source_config)

# 根据URL获取解析器
parser = get_parser_for_url('https://www.biquge.com/book/123/', source_config)
```

### 使用解析器

```python
# 搜索书籍
results = await parser.search_books('斗破苍穹', limit=10)

# 获取书籍信息
book_info = await parser.get_book_info(book_url)

# 获取章节列表
chapters = await parser.get_chapter_list(book_url)

# 获取章节内容
content = await parser.get_chapter_content(chapter_url)
```

## 配置说明

解析器需要的配置参数：

```python
source_config = {
    'name': '书源名称',
    'url': '书源基础URL',
    'search_url': '搜索URL模板',
    'book_url_pattern': '书籍URL模式',
    'chapter_url_pattern': '章节URL模式',
    'content_selector': '内容CSS选择器'
}
```

## 扩展开发

要开发新的扩展解析器：

1. 在 `sources` 文件夹创建新的Python文件
2. 继承 `BaseBookSourceParser` 类
3. 实现必需的方法
4. 系统会自动发现和加载

详细的开发指南请参考 `sources/README.md`。

## 注意事项

- 基础框架随主项目发布
- 扩展解析器位于 `sources` 文件夹，可能作为独立项目管理
- 系统设计为向后兼容，即使没有扩展解析器也能正常工作
- 所有解析器都支持热重载，无需重启应用