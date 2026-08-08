# FastRead

基于FastAPI开发的类似Legado的阅读应用，在「读」之外还能「写」：在线阅读小说、管理多形态书源、AI续写与正文改写。

## 功能特性

- ✍️ **AI 续写与创作**: 在最新章节末尾一键续写剧情；选中任意段落即可 AI 简化/扩写/重写，支持自定义创作模板（任意 OpenAI 兼容 API 可接入）
- 🎭 **正文改写与插入**: 就地改写或插入新段落，与在线章节无缝混排
- 🔄 **敏感词自动替换**: 自定义词汇映射，阅读时自动替换
- 📝 **摘录管理**: 选句即存、随读随摘，可集中回顾
- 🧩 **三态书源系统**: 书源可用 Python 模块、JS 代码段（Node 执行，贴近 Legado 风格）或 CSS 选择器 JSON 配置三种方式定义
- 🧠 **智能书源识别**: 粘贴 URL 自动匹配书源；批量导入带进度显示、可随时取消
- 📚 **书籍管理**: 导入、搜索、删除，章节全量缓存后可离线精读
- 📖 **在线阅读**: 七种主题（含夜间模式）、字体/字号/行距自定义、键盘快捷键（←/→ 切章、Esc 收面板）、目录导航
- ⚡ **实时加载 + 智能预加载**: 章节按需实时获取并缓存，相邻章节自动预加载，翻页无感
- 📊 **阅读进度**: 自动保存与恢复，阅读历史可回溯
- 📱 **响应式设计**: 桌面端与移动端自适应，移动端滚动自动隐藏导航
- 🌐 **离线支持**: Service Worker 缓存页面壳，网络状态实时提示
- 🖥️ **桌面版与自动更新**: PyQt6 桌面客户端、Windows 安装器、macOS/Linux 启动器，内置版本检查与自动更新

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动应用

```bash
python main.py
```

应用将在 http://localhost:8777 启动（端口在 `config/config.json` 的 `client.port` 配置）

## 桌面版与安装

### 桌面版运行（macOS / Linux）

本地开发目录下可直接用 Python 运行桌面窗口（需先安装 PyQt6）：

```bash
pip install PyQt6 PyQt6-WebEngine
python desktop.py
```

安装桌面启动器（自动创建 `/Applications/FastRead.app` 或 Linux `.desktop` 菜单项）：

```bash
bash scripts/install_boot_service.sh          # 仅桌面启动器
bash scripts/install_boot_service.sh --service   # 额外注册开机自启后台服务 (crontab @reboot)
```

### Windows 安装器

在 Windows 上执行 `scripts\build_installer.bat` 生成 `dist\fastread_installer.exe`，
运行安装程序时可选「注册为后台服务并开机自启」，不勾选则仅部署程序并创建桌面快捷方式。

## 自动更新

- 更新模式可在设置页配置：
  - `upgrade`：`auto`（启动后自动更新，默认）/ `manual`（界面顶部显示更新横幅）/ `off`（不检查更新）；

## 项目结构

```
├── main.py                 # 应用入口
├── desktop.py              # 桌面版（PyQt6 + WebView）
├── app/                    # 应用核心代码
│   ├── database.py         # 数据库模型和配置
│   ├── lofig.py            # 配置与日志（VERSION 在此）
│   ├── routers/            # API路由
│   │   ├── books.py        # 书籍管理
│   │   ├── reading.py      # 阅读进度
│   │   ├── sources.py      # 书源管理
│   │   └── updates.py      # 自动更新
│   └── parsers/            # 书源解析器
├── config/                 # 运行时配置（config.json，git忽略）
├── data/                   # 本地数据（含 reader.db，git忽略）
├── sources/                # 书源定义（git忽略）
├── scripts/                # 安装器/启动器/Windows服务
├── tools/                  # 工具脚本（如 migrate_db.py、make_icons.py）
├── templates/              # HTML模板
│   ├── base.html           # 基础模板
│   ├── index.html          # 首页
│   └── reader.html         # 阅读器
└── static/                 # 静态资源
    ├── css/
    ├── js/
    └── images/
```

## API文档

启动应用后访问 http://localhost:8777/docs 查看自动生成的API文档。

## 主要功能

### 书籍管理
- 从书源搜索和导入书籍
- 直接通过URL导入书籍（支持智能书源识别）
- 批量URL导入，一次性添加多本书籍
- 查看书籍详情和章节列表
- 删除不需要的书籍

### 阅读器功能
- 章节导航和目录
- 阅读设置（字体大小、行间距、主题等）
- 键盘快捷键支持
- 自动保存阅读进度

### 书源系统
- 支持自定义书源配置
- 多书源搜索
- 后台异步导入书籍内容

## 书源管理

### 添加书源的几种方式

#### 1. 通过Web界面添加
1. 启动应用后，点击导航栏的"书源管理"
2. 选择预设书源或自定义添加
3. 填写书源配置信息并测试
4. 保存书源

#### 2. 从JSON导入
在书源管理界面，可以导入JSON格式的书源配置：
```json
{
  "name": "书源名称",
  "url": "https://example.com",
  "search_url": "https://example.com/search?q={keyword}",
}
```

### 书源配置说明

- **name**: 书源显示名称
- **url**: 网站首页地址
- **search_url**: 搜索页面URL，使用 `{keyword}` 作为关键词占位符
- **book_url_pattern**: 书籍详情页URL模式（可选）
- **chapter_url_pattern**: 章节页面URL模式（可选）
- **content_selector**: CSS选择器，用于提取章节正文内容

### 书源测试

添加书源后，建议进行测试：
1. 在书源管理界面点击"测试"按钮
2. 检查搜索功能是否正常
3. 验证内容选择器是否正确

## 开发说明

### 自定义书源解析

如需支持特殊的网站结构，可以参考 `app/parsers/` 中的书源解析器实现：

```python
# 在 import_book_task 函数中自定义解析规则
def parse_book_info(soup, source):
    # 根据不同书源调整解析逻辑
    if 'example.com' in source.url:
        title = soup.select_one('.custom-title').text
        # ... 其他自定义解析
    else:
        # 默认解析逻辑
        title = soup.find('h1').text
    return title, author, description
```

### 自定义主题

在 `static/css/style.css` 中添加新的主题类：

```css
.theme-custom {
    background-color: #your-bg-color;
    color: #your-text-color;
}
```

## 注意事项

- 请遵守相关网站的robots.txt和使用条款
- 建议设置合理的请求间隔，避免对目标网站造成压力
- 本项目仅供学习交流使用

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## URL导入功能

### 单本书籍导入
1. 点击搜索书籍，切换到"URL导入"标签
2. 选择对应的书源（或启用智能识别）
3. 粘贴书籍详情页URL
4. 点击导入按钮

### 批量导入
1. 在批量导入区域输入多个URL（每行一个）
2. 启用智能识别或选择统一书源
3. 点击批量导入按钮
4. 系统会逐个导入并显示进度

### 智能书源识别
- 系统会根据URL自动匹配对应的书源
- 支持精确匹配和模糊匹配
- 自动选择最合适的书源进行导入

### 支持的功能
- ✅ URL格式验证
- ✅ 智能书源识别
- ✅ 批量导入进度显示
- ✅ 剪贴板快速粘贴
- ✅ 导入结果实时反馈
- ✅ 支持取消批量导入

## 实时加载功能

### 工作原理
- **快速导入**: 导入书籍时只获取基本信息和章节列表，不下载内容
- **按需加载**: 阅读时实时从源网站获取章节内容
- **智能缓存**: 可选择性缓存章节内容，减少重复请求
- **预加载**: 自动预加载相邻章节，提升阅读流畅度

### 优势
- ✅ 导入速度快：几秒钟即可完成书籍导入
- ✅ 存储空间小：不占用大量本地存储
- ✅ 内容最新：始终获取最新的章节内容
- ✅ 网络优化：智能预加载和缓存策略

### 使用体验
- 📖 **无感知加载**: 章节切换时自动获取内容
- 🔄 **重试机制**: 网络异常时支持重试
- 📶 **离线提示**: 网络状态实时显示
- ⚙️ **预加载控制**: 可手动控制预加载范围

### 性能优化
- 并行预加载相邻章节
- 智能内容清理和格式化
- 请求头优化，模拟真实浏览器
- 超时和错误处理机制