# 书源解析器基础模块
# 包含基础解析器和动态加载器

from .base_parser import BaseBookSourceParser, SearchResult, BookInfo, ChapterInfo
from .parser_loader import ParserLoader, get_parser_for_source, get_parser_for_url

__all__ = [
    'BaseBookSourceParser',
    'SearchResult', 
    'BookInfo',
    'ChapterInfo',
    'ParserLoader',
    'get_parser_for_source',
    'get_parser_for_url'
]