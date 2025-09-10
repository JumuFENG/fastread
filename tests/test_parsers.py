#!/usr/bin/env python3
"""
书源解析器测试脚本
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
from parsers.parser_loader import get_parser_for_source, get_parser_for_url

async def test_parsers():
    """测试解析器功能"""
    
    # 测试配置
    test_configs = [
        {
            'name': '笔趣阁',
            'url': 'https://www.biquge.com',
            'search_url': 'https://www.biquge.com/search?q={keyword}',
            'book_url_pattern': '',
            'chapter_url_pattern': '',
            'content_selector': '#content'
        },
        {
            'name': '起点中文网',
            'url': 'https://www.qidian.com',
            'search_url': 'https://www.qidian.com/search?kw={keyword}',
            'book_url_pattern': '',
            'chapter_url_pattern': '',
            'content_selector': '.read-content'
        },
        {
            'name': '未知书源',
            'url': 'https://unknown.com',
            'search_url': 'https://unknown.com/search?q={keyword}',
            'book_url_pattern': '',
            'chapter_url_pattern': '',
            'content_selector': '.content'
        }
    ]

    print("=== 书源解析器测试 ===\n")
    
    for config in test_configs:
        print(f"测试书源: {config['name']}")
        print(f"URL: {config['url']}")
        
        # 测试根据书源名称获取解析器
        parser = get_parser_for_source(config['name'], config)
        print(f"根据名称匹配的解析器: {parser.__class__.__name__}")
        
        # 测试根据URL获取解析器
        parser_by_url = get_parser_for_url(config['url'], config)
        print(f"根据URL匹配的解析器: {parser_by_url.__class__.__name__}")
        
        # 测试URL处理能力
        can_handle = parser.can_handle_url(config['url'])
        print(f"可以处理该URL: {can_handle}")
        
        print("-" * 50)
    
    # 测试特定URL匹配
    print("\n=== URL匹配测试 ===")
    test_urls = [
        'https://www.biquge.com/book/12345/',
        'https://book.qidian.com/info/1234567',
        'https://www.unknown-site.com/novel/123',
        'https://xbiquge.com/book/456/'
    ]
    
    base_config = {
        'name': 'test',
        'url': '',
        'search_url': '',
        'book_url_pattern': '',
        'chapter_url_pattern': '',
        'content_selector': '.content'
    }
    
    for url in test_urls:
        parser = get_parser_for_url(url, base_config)
        print(f"URL: {url}")
        print(f"匹配的解析器: {parser.__class__.__name__}")
        print(f"可以处理: {parser.can_handle_url(url)}")
        print("-" * 30)

async def test_crxs():
    test_configs = [
        {
            'name': 'crxs',
            'url': 'https://crxs.me',
            'search_url': 'https://crxs.me/fictions/keyword-{keyword}.html',
            'book_url_pattern': 'https://crxs.me/fiction/*.html',
            'chapter_url_pattern': 'https://crxs.me/fiction/*.html',
            'content_selector': '.fiction-body'
        }
    ]
    print("=== 书源解析器测试 ===\n")
    
    for config in test_configs:
        print(f"测试书源: {config['name']}")
        print(f"URL: {config['url']}")
        
        # 测试根据书源名称获取解析器
        parser = get_parser_for_source(config['name'], config)
        print(f"根据名称匹配的解析器: {parser.__class__.__name__}")
        
        # 测试根据URL获取解析器
        parser_by_url = get_parser_for_url(config['url'], config)
        print(f"根据URL匹配的解析器: {parser_by_url.__class__.__name__}")
        
        # 测试URL处理能力
        can_handle = parser.can_handle_url(config['url'])
        print(f"可以处理该URL: {can_handle}")
        
        print("-" * 50)

    # 测试特定URL匹配
    print("\n=== URL匹配测试 ===")
    test_urls = [
        'https://crxs.me/fiction/id-5fba2b883e655.html',
    ]
    
    base_config = test_configs[0]
    
    for url in test_urls:
        parser = get_parser_for_url(url, base_config)
        print(f"URL: {url}")
        print(f"匹配的解析器: {parser.__class__.__name__}")
        print(f"可以处理: {parser.can_handle_url(url)}")
        print("-" * 30)

    # sr = await parser.search_books('夫妻', -1)
    # print(sr, len(sr))
    # test_get_chapter_list
    test_book_url = 'https://crxs.me/fiction/id-5f2ec8dbd2cf6.html'
    binfo = await parser.get_book_info(test_book_url)
    print(binfo)
    # bchapters = await parser.get_chapter_list(test_book_url)
    # print(bchapters, len(bchapters))
    # test_chapter_url = 'https://crxs.me/fiction/id-dGhpc19pc19hX2ZpeGVkMGNSN3RPVmZiQ3ZHejFya3ArTVJxdUE9PQ==.html'
    # test_chapter_url = 'https://crxs.me/fiction/id-5f2ec8dbd2cf6.html'
    # chapter_content = await parser.get_chapter_content(test_chapter_url)
    # print(chapter_content)

async def test_ddyueshu():
    test_configs = [
        {
            'name': '顶点小说移动',
            'url': 'https://m.ddyueshu.cc',
            'search_url': '*',
            'book_url_pattern': 'https://m.ddyueshu.cc/wapbook/*.html',
            'chapter_url_pattern': 'https://m.ddyueshu.cc/wapbook/*.html',
            'content_selector': '#chaptercontent'
        }
    ]
    print("=== 书源解析器测试 ===\n")
    
    for config in test_configs:
        print(f"测试书源: {config['name']}")
        print(f"URL: {config['url']}")
        
        # 测试根据书源名称获取解析器
        parser = get_parser_for_source(config['name'], config)
        print(f"根据名称匹配的解析器: {parser.__class__.__name__}")
        
        # 测试根据URL获取解析器
        parser_by_url = get_parser_for_url(config['url'], config)
        print(f"根据URL匹配的解析器: {parser_by_url.__class__.__name__}")
        
        # 测试URL处理能力
        can_handle = parser.can_handle_url(config['url'])
        print(f"可以处理该URL: {can_handle}")
        
        print("-" * 50)

    # 测试特定URL匹配
    print("\n=== URL匹配测试 ===")
    test_urls = [
        'https://m.ddyueshu.cc/wapbook/14715.html',
        'https://m.ddyueshu.cc/wapbook/30053797_88380227.html',
    ]
    
    base_config = {
        'name': 'ddyueshu',
        'url': 'https://m.ddyueshu.cc',
        'search_url': '*',
        'book_url_pattern': 'https://m.ddyueshu.cc/wapbook/*.html',
        'chapter_url_pattern': 'https://m.ddyueshu.cc/wapbook/*.html',
        'content_selector': '#chaptercontent'
    }
    
    for url in test_urls:
        parser = get_parser_for_url(url, base_config)
        print(f"URL: {url}")
        print(f"匹配的解析器: {parser.__class__.__name__}")
        print(f"可以处理: {parser.can_handle_url(url)}")
        print("-" * 30)

    # test_get_chapter_list
    test_book_url = 'https://m.ddyueshu.cc/wapbook/30053797.html'
    # binfo = await parser.get_book_info(test_book_url)
    # print(binfo)
    bchapters = await parser.get_chapter_list(test_book_url)
    print(bchapters)
    # test_chapter_url = 'https://m.ddyueshu.cc/wapbook/30053797_88380227.html'
    # chapter_content = await parser.get_chapter_content(test_chapter_url)
    # print(chapter_content)

async def test_qidian():
    test_configs = [
        {
            'name': '起点中文网',
            'url': 'https://www.qidian.com',
            'search_url': 'https://www.qidian.com/search?kw={keyword}',
            'book_url_pattern': '',
            'chapter_url_pattern': '',
            'content_selector': '.read-content'
        }
    ]
    print("=== 书源解析器测试 ===\n")
    
    for config in test_configs:
        print(f"测试书源: {config['name']}")
        print(f"URL: {config['url']}")
        
        # 测试根据书源名称获取解析器
        parser = get_parser_for_source(config['name'], config)
        print(f"根据名称匹配的解析器: {parser.__class__.__name__}")
        
        # 测试根据URL获取解析器
        parser_by_url = get_parser_for_url(config['url'], config)
        print(f"根据URL匹配的解析器: {parser_by_url.__class__.__name__}")
        
        # 测试URL处理能力
        can_handle = parser.can_handle_url(config['url'])
        print(f"可以处理该URL: {can_handle}")
        
        print("-" * 50)

    # 测试特定URL匹配
    print("\n=== URL匹配测试 ===")
    test_urls = [
        'https://www.qidian.com/book/1045831749/',
    ]
    
    base_config = test_configs[0]
    
    for url in test_urls:
        parser = get_parser_for_url(url, base_config)
        print(f"URL: {url}")
        print(f"匹配的解析器: {parser.__class__.__name__}")
        print(f"可以处理: {parser.can_handle_url(url)}")
        print("-" * 30)

    # test_get_chapter_list
    test_book_url = 'https://www.qidian.com/book/1045831749/'
    binfo = await parser.get_book_info(test_book_url)
    print(binfo)
    # bchapters = await parser.get_chapter_list(test_book_url)
    # print(bchapters)
    # test_chapter_url = 'https://m.ddyueshu.cc/wapbook/30053797_88380227.html'
    # chapter_content = await parser.get_chapter_content(test_chapter_url)
    # print(chapter_content)

async def test_biquge():
    test_configs = [
        {
            'name': '笔趣阁',
            'url': 'https://www.biquuge.com/',
            'search_url': 'https://www.biquuge.com/search.php?q={keyword}',
            'book_url_pattern': 'https://www.biquuge.com/*',
            'chapter_url_pattern': 'https://www.biquuge.com/*.html',
            'content_selector': 'article'
        }
    ]
    print("=== 书源解析器测试 ===\n")
    
    for config in test_configs:
        print(f"测试书源: {config['name']}")
        print(f"URL: {config['url']}")
        
        # 测试根据书源名称获取解析器
        parser = get_parser_for_source(config['name'], config)
        print(f"根据名称匹配的解析器: {parser.__class__.__name__}")
        
        # 测试根据URL获取解析器
        parser_by_url = get_parser_for_url(config['url'], config)
        print(f"根据URL匹配的解析器: {parser_by_url.__class__.__name__}")
        
        # 测试URL处理能力
        can_handle = parser.can_handle_url(config['url'])
        print(f"可以处理该URL: {can_handle}")
        
        print("-" * 50)

    # 测试特定URL匹配
    print("\n=== URL匹配测试 ===")
    test_urls = [
        'https://www.biquuge.com/7/7934/',
    ]
    
    base_config = test_configs[0]
    
    for url in test_urls:
        parser = get_parser_for_url(url, base_config)
        print(f"URL: {url}")
        print(f"匹配的解析器: {parser.__class__.__name__}")
        print(f"可以处理: {parser.can_handle_url(url)}")
        print("-" * 30)

    # sr = await parser.search_books('三寸人间')
    # print(sr, len(sr))
    # test_book_url = 'https://www.biquuge.com/113/113633/'
    # binfo = await parser.get_book_info(test_book_url)
    # print(binfo.title, binfo.author, binfo.description, binfo.cover_url)
    # bchapters = await parser.get_chapter_list(test_book_url)
    # print(len(bchapters))
    test_chapter_url = 'https://www.biquuge.com/7/7934/1210968.html'
    chapter_content = await parser.get_chapter_content(test_chapter_url)
    print(chapter_content)

async def test_xszj():
    test_configs = [
        {
            'name': '小说之家',
            'url': 'https://xszj.org/',
            'search_url': 'https://xszj.org/s/?id=bVFt3muTSx7RVxvhABZ8&keyword={keyword}&code=5961',
            'book_url_pattern': 'https://xszj.org/b/*',
            'chapter_url_pattern': 'https://xszj.org/b/*/c/*',
            'content_selector': '#booktxt'
        }
    ]
    print("=== 书源解析器测试 ===\n")

    for config in test_configs:
        print(f"测试书源: {config['name']}")
        print(f"URL: {config['url']}")
        
        # 测试根据书源名称获取解析器
        parser = get_parser_for_source(config['name'], config)
        print(f"根据名称匹配的解析器: {parser.__class__.__name__}")
        
        # 测试根据URL获取解析器
        parser_by_url = get_parser_for_url(config['url'], config)
        print(f"根据URL匹配的解析器: {parser_by_url.__class__.__name__}")
        
        # 测试URL处理能力
        can_handle = parser.can_handle_url(config['url'])
        print(f"可以处理该URL: {can_handle}")
        
        print("-" * 50)

    # test_book_url = 'https://xszj.org/b/413589'
    # binfo = await parser.get_book_info(test_book_url)
    # print(binfo.title, binfo.author, binfo.description, binfo.cover_url)
    # bchapters = await parser.get_chapter_list(test_book_url)
    # print(len(bchapters))
    test_chapter_url = 'https://xszj.org/b/413589/c/15830987'
    chapter_content = await parser.get_chapter_content(test_chapter_url)
    print(chapter_content)


if __name__ == "__main__":
    asyncio.run(test_ddyueshu())
    # from urllib.parse import urlparse
    # next_sec = 'https://xszj.org/b/413589/c/5786882?page=2'
    # chapter_sec = 'https://xszj.org/b/413589/c/5786882'
    # nexturl = urlparse(next_sec)
    # cururl = urlparse(chapter_sec)
    # print(nexturl.query, cururl.query)
