"""
书源解析基类
提供通用的解析方法，可以被具体的书源解析类继承
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any
from bs4 import BeautifulSoup
import httpx
from urllib.parse import urljoin, urlparse
import re


class SearchResult:
    """搜索结果数据类"""
    def __init__(self, title: str, author: str, description: str, source_url: str, cover_url: str = None):
        self.title = title
        self.author = author
        self.description = description
        self.source_url = source_url
        self.cover_url = cover_url


class BookInfo:
    """书籍信息数据类"""
    def __init__(self, title: str, author: str, description: str = "", cover_url: str = ""):
        self.title = title
        self.author = author
        self.description = description
        self.cover_url = cover_url


class ChapterInfo:
    """章节信息数据类"""
    def __init__(self, title: str, url: str, chapter_number: int = 0):
        self.title = title
        self.url = url
        self.chapter_number = chapter_number


class BaseBookSourceParser(ABC):
    """书源解析基类"""

    def __init__(self, source_config: Dict[str, Any]):
        """
        初始化解析器

        Args:
            source_config: 书源配置字典，包含name, url, search_url等信息
        """
        self.name = source_config.get('name', '')
        self.base_url = source_config.get('url', '')
        self.search_url = source_config.get('search_url', '')
        self.book_url_pattern = source_config.get('book_url_pattern', '')
        self.chapter_url_pattern = source_config.get('chapter_url_pattern', '')
        self.content_selector = source_config.get('content_selector', '')

        # HTTP客户端配置
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

    async def search_books(self, keyword: str, limit: int = 10) -> List[SearchResult]:
        """
        搜索书籍

        Args:
            keyword: 搜索关键词
            limit: 返回结果数量限制

        Returns:
            搜索结果列表
        """
        try:
            search_url = self.get_search_url(keyword)
            async with httpx.AsyncClient(timeout=30.0) as client:
                books = []
                page_url = search_url
                while page_url:
                    response = await client.get(page_url, headers=self.headers)
                    response.raise_for_status()

                    soup = BeautifulSoup(response.text, 'html.parser')
                    books += await self.parse_search_results(soup)
                    if limit > 0 and len(books) >= limit:
                        break
                    page_url = self.get_next_search_page(soup, search_url)

                return books

        except Exception as e:
            print(f"搜索失败: {str(e)}")
            return []

    async def get_book_info(self, book_url: str) -> Optional[BookInfo]:
        """
        获取书籍详细信息

        Args:
            book_url: 书籍详情页URL

        Returns:
            书籍信息对象
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(book_url, headers=self.headers)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')
                return await self.parse_book_info(soup, book_url)

        except Exception as e:
            print(f"获取书籍信息失败: {str(e)}")
            return None

    async def get_chapter_list(self, book_url: str) -> List[ChapterInfo]:
        """
        获取章节列表

        Args:
            book_url: 书籍详情页URL

        Returns:
            章节信息列表
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                chapters = []
                next_page = book_url
                while next_page:
                    response = await client.get(next_page, headers=self.headers)
                    response.raise_for_status()

                    soup = BeautifulSoup(response.text, 'html.parser')
                    chap = await self.parse_chapter_list(soup, book_url, len(chapters))
                    chapters += chap
                    next_page = self.get_next_chapter_list_page(soup, book_url)
                return chapters
        except Exception as e:
            print(f"获取章节列表失败: {str(e)}")
            return []

    async def get_chapter_content(self, chapter_url: str) -> Optional[str]:
        """
        获取章节内容

        Args:
            chapter_url: 章节页面URL

        Returns:
            章节内容文本
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                content = ''
                chapter_sec = chapter_url
                while chapter_sec:
                    response = await client.get(chapter_sec, headers=self.headers)
                    response.raise_for_status()

                    soup = BeautifulSoup(response.text, 'html.parser')
                    content += await self.parse_chapter_content(soup)
                    chapter_sec = self.get_chapter_next_section(soup, chapter_url, chapter_sec)

                return content

        except Exception as e:
            print(f"获取章节内容失败: {str(e)}")
            return None

    def next_section_match(self, next_sec, cur_sec):
        """
        判断 next_sec 是否是 cur_sec 的下一部分。
        规则：
        - cur_sec: */30053797_88380227.html next_sec: */30053797_88380227_2.html
        - cur_sec: */30053797_88380227_2.html next_sec: */30053797_88380227_3.html
        """
        # 提取章节基准和序号
        def parse_sec(url):
            m = re.match(r'(.*?)(?:_(\d+))?$', url)
            if not m:
                return None, None
            base = m.group(1)
            idx = int(m.group(2)) if m.group(2) else 1
            return base, idx

        next_sec = next_sec.rstrip('.html')
        cur_sec = cur_sec.rstrip('.html')
        cur_base, cur_idx = parse_sec(cur_sec)
        next_base, next_idx = parse_sec(next_sec)
        if cur_base is None or next_base is None:
            return False
        return cur_base == next_base and next_idx == cur_idx + 1

    # 以下方法可以被子类重写以实现特定书源的解析逻辑
    def get_next_search_page(self, soup: BeautifulSoup, search_url: str) -> Optional[str]:
        """获取搜索结果的下一页链接，默认不支持分页"""
        return None

    def get_next_chapter_list_page(self, soup: BeautifulSoup, book_url: str) -> Optional[str]:
        """获取章节列表的下一页链接，默认不支持分页"""
        return None

    def get_chapter_next_section(self, soup: BeautifulSoup, chapter_url: str, chapter_sec: str) -> Optional[str]:
        """获取章节的下一部分链接，默认不支持多部分章节"""
        return None

    def get_search_url(self, keyword: str) -> str:
        """构建搜索URL"""
        if '{keyword}' in self.search_url:
            return self.search_url.format(keyword=keyword)
        return self.search_url + keyword

    @property
    def search_items_selectors(self) -> List[str]:
        return [
            '.book-item', '.search-item', '.result-item',
            '.book-list li', '.search-list li', '.result-list li',
            '.book', '.item', '.result'
        ]

    async def parse_search_results(self, soup: BeautifulSoup) -> List[SearchResult]:
        """
        解析搜索结果页面
        子类可以重写此方法实现特定的解析逻辑
        """
        results = []

        books = []
        for selector in self.search_items_selectors:
            books = soup.select(selector)
            if books:
                break

        for book in books:
            try:
                title = self.extract_title(book)
                author = self.extract_author(book)
                description = self.extract_description(book)
                book_url = self.extract_book_url(book)
                cover_url = self.extract_cover_url(book)

                if title and book_url:
                    results.append(SearchResult(
                        title=title,
                        author=author,
                        description=description,
                        source_url=book_url,
                        cover_url=cover_url
                    ))
            except Exception as e:
                print(f"解析搜索结果项失败: {e}")
                continue

        return results

    async def parse_book_info(self, soup: BeautifulSoup, book_url: str) -> Optional[BookInfo]:
        """
        解析书籍详情页面
        子类可以重写此方法实现特定的解析逻辑
        """
        try:
            title = self.extract_book_title(soup)
            author = self.extract_book_author(soup)
            description = self.extract_book_description(soup)
            cover_url = self.extract_book_cover(soup, book_url)

            return BookInfo(
                title=title,
                author=author,
                description=description,
                cover_url=cover_url
            )
        except Exception as e:
            print(f"解析书籍信息失败: {e}")
            return None

    @property
    def chapter_links_container_selectors(self) -> str:
        return [
            '.chapter-list', '.volume-list', '.catalog',
            '#catalog', '.book-catalog', '.novel-catalog',
            '.chapter', '.chapters', '.mulu'
        ]

    async def parse_chapter_list(self, soup: BeautifulSoup, book_url: str, chno:int=0) -> List[ChapterInfo]:
        """
        解析章节列表
        子类可以重写此方法实现特定的解析逻辑
        """
        chapters = []

        # 尝试找到章节列表容器
        links = []
        for container_selector in self.chapter_links_container_selectors:
            container = soup.select_one(container_selector)
            if container:
                links = container.find_all('a', href=True)
                break

        chapter_number = chno + 1
        for link in links:
            try:
                title = link.text.strip()
                href = link.get('href')

                if self.is_valid_chapter_link(title, href):
                    full_url = self.build_full_url(href, book_url)
                    chapters.append(ChapterInfo(
                        title=title,
                        url=full_url,
                        chapter_number=chapter_number
                    ))
                    chapter_number += 1

            except Exception as e:
                print(f"解析章节链接失败: {e}")
                continue

        return chapters

    async def parse_chapter_content(self, soup: BeautifulSoup) -> Optional[str]:
        """
        解析章节内容
        子类可以重写此方法实现特定的解析逻辑
        """
        # 使用配置的选择器
        if self.content_selector:
            content_element = soup.select_one(self.content_selector)
            if content_element:
                return self.clean_content_soup(content_element)

        # 通用内容选择器
        content_selectors = [
            '.content', '#content', '.chapter-content',
            '.text', '.txt', '.novel-content',
            '.book-content', '.read-content', '.chapter-text'
        ]

        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                return self.clean_content_soup(element)

        return None

    # 辅助方法

    @property
    def search_title_selectors(self) -> List[str]:
        return [
            'h3', 'h2', 'h1', '.title', '.name', 'a'
        ]

    def extract_title(self, element) -> str:
        """从元素中提取标题"""
        for selector in self.search_title_selectors:
            title_elem = element.select_one(selector)
            if title_elem and title_elem.text.strip():
                return title_elem.text.strip()
        return "未知标题"

    @property
    def search_author_selectors(self) -> List[str]:
        return [
            '.author', '.writer', '.by'
        ]

    def extract_author(self, element) -> str:
        """从元素中提取作者"""
        for selector in self.search_author_selectors:
            author_elem = element.select_one(selector)
            if author_elem and author_elem.text.strip():
                text = author_elem.text.strip()
                # 移除"作者："等前缀
                text = re.sub(r'^(作者[：:]?|by[：:]?)', '', text).strip()
                return text
        return "未知作者"

    @property
    def search_description_selectors(self) -> List[str]:
        return [
            '.description', '.desc', '.intro', '.summary'
        ]

    def extract_description(self, element) -> str:
        """从元素中提取描述"""
        for selector in self.search_description_selectors:
            desc_elem = element.select_one(selector)
            if desc_elem and desc_elem.text.strip():
                return desc_elem.text.strip()[:200]
        return ""

    def extract_book_url(self, element) -> str:
        """从元素中提取书籍URL"""
        for selector in self.search_title_selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                return self.build_full_url(title_elem.get('href'), self.base_url)

        link = element.find('a', href=True)
        if link:
            href = link.get('href')
            return self.build_full_url(href, self.base_url)
        return ""

    @property
    def search_cover_selectors(self) -> List[str]:
        return [
            '.cover img', '.book-cover img', 'img'
        ]

    def extract_cover_url(self, element) -> str:
        """从元素中提取封面URL"""
        for selector in self.search_cover_selectors:
            cover_elem = element.select_one(selector)
            if cover_elem and cover_elem.get('src'):
                return self.build_full_url(cover_elem.get('src'), self.base_url)
        return ""

    @property
    def book_title_selectors(self) -> List[str]:
        return [
            'h1', '.book-title', '.title', '#title',
            '.book-name', '.novel-title', 'h1.title',
            '.info h1', '.book-info h1'
        ]

    def extract_book_title(self, soup: BeautifulSoup) -> str:
        """提取书籍标题"""
        for selector in self.book_title_selectors:
            element = soup.select_one(selector)
            if element and element.text.strip():
                return element.text.strip()

        # 尝试从页面标题提取
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.text.strip()
            # 移除常见的网站后缀
            for suffix in ['_小说阅读网', '_起点中文网', '_纵横中文网', '_晋江文学城']:
                title = title.replace(suffix, '')
            return title

        return "未知标题"

    @property
    def book_author_selectors(self) -> List[str]:
        return [
            '.author', '.book-author', '#author',
            '.writer', '.novel-author', '.info .author'
        ]

    def extract_book_author(self, soup: BeautifulSoup) -> str:
        """提取书籍作者"""
        for selector in self.book_author_selectors:
            element = soup.select_one(selector)
            if element and element.text.strip():
                text = element.text.strip()
                # 移除"作者："等前缀
                text = re.sub(r'^(作者[：:]?)', '', text).strip()
                if text:
                    return text

        return "未知作者"

    @property
    def book_description_selectors(self) -> List[str]:
        return [
            '.description', '.book-description', '.intro',
            '.summary', '.book-intro', '.novel-intro',
            '.content-intro', '#intro'
        ]

    def extract_book_description(self, soup: BeautifulSoup) -> str:
        """提取书籍简介"""
        for selector in self.book_description_selectors:
            element = soup.select_one(selector)
            if element and element.text.strip():
                return element.text.strip()[:500]  # 限制长度

        return ""

    @property
    def book_cover_selectors(self) -> List[str]:
        return [
            '.cover img', '.book-cover img', '.novel-cover img',
            '.book-img img', '#cover img', 'img.cover', '#fmimg img'
        ]

    def extract_book_cover(self, soup: BeautifulSoup, base_url: str) -> str:
        """提取书籍封面"""
        for selector in self.book_cover_selectors:
            element = soup.select_one(selector)
            if element and element.get('src'):
                src = element.get('src')
                return self.build_full_url(src, base_url)

        return ""

    def is_valid_chapter_link(self, title: str, href: str) -> bool:
        """判断是否为有效的章节链接"""
        if not title or not href:
            return False

        # 过滤太长或太短的标题
        if len(title) > 200 or len(title) < 2:
            return False

        # 过滤明显不是章节的链接
        skip_keywords = [
            '首页', '书架', '排行', '分类', '搜索', '登录', '注册',
            '充值', '客服', '帮助', '关于', '联系', '广告',
            'javascript:', 'mailto:', '#','最新章节', '章节目录', '加入书签', '推荐本书',
            '上一页', '下一页', '返回', '首页', '书架'
        ]

        if any(keyword in title.lower() or keyword in href.lower() for keyword in skip_keywords):
            return False

        # 简单的章节标题检测
        if any(keyword in title for keyword in ['第', '章', 'Chapter', 'chapter', '卷']):
            return True
        elif title.isdigit() or any(char.isdigit() for char in title):
            # 包含数字的可能是章节
            return True

        return False

    def build_full_url(self, url: str, base_url: str) -> str:
        """构建完整URL"""
        if not url:
            return ""

        if url.startswith('http'):
            return url
        elif url.startswith('/'):
            return urljoin(base_url, url)
        else:
            return urljoin(base_url + '/', url)

    def clean_content_soup(self, soup: BeautifulSoup) -> str:
        """清理章节内容元素"""
        self.remove_ads(soup)
        content = self.extract_paragraphs(soup)
        return self.clean_content(content)

    def remove_ads(self, soup):
        """移除起点广告元素"""
        # 移除常见的广告标签
        ad_selectors = [
            '.ad', '.ads', '.advertisement',
            '.chapter-comment', '.comment',
            'script', 'style'
        ]

        for selector in ad_selectors:
            for ad in soup.select(selector):
                ad.decompose()

    def extract_paragraphs(self, element) -> str:
        """提取段落内容，保持段落分隔"""
        paragraphs = []

        # 查找所有p标签
        p_tags = element.find_all('p')

        if p_tags:
            # 如果有p标签，逐个提取文本
            for p in p_tags:
                text = p.get_text().strip()
                if text:  # 只添加非空段落
                    paragraphs.append(text)
        else:
            # 如果没有p标签，尝试其他块级元素
            block_tags = element.find_all(['div', 'br'])
            if block_tags:
                # 处理br标签分隔的内容
                content = str(element)
                # 将br标签替换为换行符
                content = re.sub(r'<br[^>]*>', '\n', content)
                # 移除其他HTML标签
                from bs4 import BeautifulSoup
                clean_soup = BeautifulSoup(content, 'html.parser')
                text = clean_soup.get_text()
                # 按行分割并过滤空行
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                paragraphs = lines
            else:
                # 最后的备选方案，直接获取文本
                text = element.get_text()
                paragraphs = [text.strip()] if text.strip() else []

        # 用双换行符连接段落
        return '\n\n'.join(paragraphs)

    @property
    def content_skip_text_patterns(self) -> List[str]:
        """默认的跳过文本模式"""
        return [
            r'^\s*$',  # 空行
            r'^\s*广告\s*$',  # 广告行
            r'^\s*推荐\s*$',  # 推荐行
            r'^\s*VIP\s*$',  # VIP行
            r'^\s*订阅\s*$',  # 订阅行
            r'^\s*本章未完，请翻页继续阅读.*$',  # 翻页提示
            r'^\s*未完待续.*$',  # 未完待续
            r'^\s*点击进入.*$',  # 点击进入
            r'^\s*更多免费章节.*$',  # 更多免费章节
        ]

    def clean_content(self, text: str) -> str:
        """清理章节内容"""
        if not text:
            return ""

        for pattern in self.content_skip_text_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # 清理多余的空白
        text = re.sub(r'\n\s*\n', '\n\n', text)  # 保留段落分隔
        text = re.sub(r'[ \t]+', ' ', text)  # 合并空格和制表符
        text = text.strip()

        return text

    @classmethod
    def get_parser_name(cls) -> str:
        """获取解析器名称，用于动态加载"""
        return cls.__name__.lower().replace('parser', '')

    def can_handle_url(self, url: str) -> bool:
        """判断是否可以处理指定URL"""
        if not url or not self.base_url:
            return False

        parsed_url = urlparse(url)
        parsed_base = urlparse(self.base_url)

        return parsed_url.netloc == parsed_base.netloc

    def bg_image_url(self, soup, ele_selctor) -> str:
        # 提取封面
        cover_elem = soup.select_one(ele_selctor)
        image_url = ""
        if cover_elem:
            style = cover_elem.get('style', '')
            # 使用正则表达式提取background-image中的URL
            match = re.search(r'background-image:\s*url\(["\']?(.*?)["\']?\)', style)
            if match:
                image_url = match.group(1)
        return image_url
