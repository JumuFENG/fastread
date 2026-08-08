# FastRead

基于FastAPI开发的类似Legado的web版阅读应用，支持在线阅读小说、管理书源、同步阅读进度等功能。

## 功能特性

- 📚 **书籍管理**: 支持导入、搜索、删除书籍
- 📖 **在线阅读**: 优雅的阅读界面，支持多种主题和字体设置
- 🔍 **书源管理**: 支持自定义书源，从多个网站搜索和导入书籍
- 🔗 **URL导入**: 支持直接通过书籍URL导入，智能识别书源
- 📦 **批量导入**: 支持批量URL导入，一次性添加多本书籍
- ⚡ **实时加载**: 章节内容按需实时获取，导入速度快
- 🚀 **智能预加载**: 自动预加载相邻章节，提升阅读体验
- 👤 **用户系统**: 用户注册登录，个人阅读进度同步
- 📱 **响应式设计**: 支持桌面端和移动端访问
- 🔍 **快速搜索**: 本地书籍搜索和在线书源搜索
- 📊 **阅读进度**: 自动保存和恢复阅读位置
- 🌐 **离线支持**: 支持网络状态检测和缓存内容

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，设置你的配置
```

### 3. 启动应用

```bash
python main.py
```

应用将在 http://localhost:8000 启动

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

- 更新检查通过 `{update_server}/api/products/4/latest` 查询（product_id=4），
  更新包从 `{update_server}/downloads/fastread/fastread-{version}.zip` 下载并覆盖程序文件。
- 更新服务器与更新模式可在 `config/config.json` 的 `client` 段配置：
  - `update_server`：默认 `https://prod.ailyf.cn`
  - `upgrade`：`auto`（启动后自动更新，默认）/ `manual`（界面顶部显示更新横幅，点击「立即更新」手动更新）
- 相关接口：`GET /api/update/check`、`POST /api/update/apply`。

## 项目结构

```
├── main.py                 # 应用入口
├── app/                    # 应用核心代码
│   ├── database.py         # 数据库模型和配置
│   ├── routers/            # API路由
│   │   ├── books.py        # 书籍管理
│   │   ├── reading.py      # 阅读进度
│   │   └── sources.py      # 书源管理
│   └── parsers/            # 书源解析器
├── data/                   # 本地数据（含 reader.db）
├── tools/                  # 工具脚本（如 migrate_db.py）
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

启动应用后访问 http://localhost:8000/docs 查看自动生成的API文档。

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

### 用户系统
- JWT认证
- 个人阅读历史
- 跨设备同步阅读进度

## 书源管理

### 添加书源的几种方式

#### 1. 通过Web界面添加
1. 启动应用后，点击导航栏的"书源管理"
2. 选择预设书源或自定义添加
3. 填写书源配置信息并测试
4. 保存书源

#### 2. 使用初始化脚本
```bash
# 快速添加示例书源
python init_sources.py
```

#### 3. 从JSON导入
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

如需支持特殊的网站结构，可以修改 `routers/sources.py` 中的解析逻辑：

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
- ✅ 支持取消批量导入## 实
时加载功能

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