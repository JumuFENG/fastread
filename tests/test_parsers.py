#!/usr/bin/env python3
"""
书源解析器测试脚本
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
from parsers.parser_loader import parser_loader, get_parser_for_source, get_parser_for_url

async def test_network(url):
    parser = parser_loader.create_base_parser({'name': 'test', 'url': url}, False)
    bk = await parser.get_book_info(url)
    print(bk.title, bk.author, bk.description, bk.cover_url)

async def test_base_parser():
    parser = get_parser_for_source('xbiquge77',{'name': 'xbiquge77', 'url': 'https://www.xbiquge77.com/'})
    test_book_url = 'https://www.xbiquge77.com/72862'
    # book_info = await parser.get_book_info(test_book_url)
    # print(book_info)
    bchapters = await parser.get_chapter_list(test_book_url)
    print(len(bchapters))
    test_chapter_url = 'https://www.xbiquge77.com/72862/1'
    chapter_content = await parser.get_chapter_content(test_chapter_url)
    print(chapter_content)

async def test_crxs():
    # parser = get_parser_for_source('crxs')
    parser = get_parser_for_url('https://crxs.me/fiction/id-68c3e12cdc235.html')
    # test_search
    # sr = await parser.search_books('夫妻', -1)
    # print(sr, len(sr))
    # test_get_chapter_list
    # test_book_url = 'https://crxs.me/fiction/id-5f2ec8dbd2cf6.html'
    test_book_url = 'https://crxs.me/fiction/id-68c3e12cdc235.html'
    # binfo = await parser.get_book_info(test_book_url)
    # print(binfo)
    bchapters = await parser.get_chapter_list(test_book_url)
    print(bchapters, len(bchapters))
    test_chapter_url = 'https://crxs.me/fiction/id-dGhpc19pc19hX2ZpeGVkMGNSN3RPVmZiQ3ZHejFya3ArTVJxdUE9PQ==.html'
    # test_chapter_url = 'https://crxs.me/fiction/id-5f2ec8dbd2cf6.html'
    chapter_content = await parser.get_chapter_content(test_chapter_url)
    print(chapter_content)

async def test_mddyueshu():
    parser = get_parser_for_source('mddyueshu', {})
    # test_get_chapter_list
    test_book_url = 'https://m.ddyueshu.cc/wapbook/30053797.html'
    # binfo = await parser.get_book_info(test_book_url)
    # print(binfo)
    # bchapters = await parser.get_chapter_list(test_book_url)
    # print(bchapters)
    uchapters = await parser.update_chapter_list(test_book_url, 525)
    print(len(uchapters))
    test_chapter_url = 'https://m.ddyueshu.cc/wapbook/30053797_88380227.html'
    chapter_content = await parser.get_chapter_content(test_chapter_url)
    print(chapter_content)


async def test_ddyueshu():
    parser = get_parser_for_source('ddyueshu', {})
    # test_book_url = 'https://www.ddyueshu.cc/59589_59589640/'
    # book_info = await parser.get_book_info(test_book_url)
    # print(book_info)
    # bchapters = await parser.get_chapter_list(test_book_url)
    # print(len(bchapters))
    test_chapter_url = 'https://www.ddyueshu.cc/59589_59589640/30890079.html'
    chapter_content = await parser.get_chapter_content(test_chapter_url)
    print(chapter_content)


async def test_biquge():
    parser = get_parser_for_source('biquuge', {})
    sr = await parser.search_books('三寸人间')
    print(sr, len(sr))
    test_book_url = 'https://www.biquuge.com/113/113633/'
    binfo = await parser.get_book_info(test_book_url)
    print(binfo.title, binfo.author, binfo.description, binfo.cover_url)
    bchapters = await parser.get_chapter_list(test_book_url)
    print(len(bchapters))
    uchapters = await parser.update_chapter_list(test_book_url, 888)
    print(len(uchapters))
    test_chapter_url = 'https://www.biquuge.com/7/7934/1210968.html'
    chapter_content = await parser.get_chapter_content(test_chapter_url)
    print(chapter_content)

async def test_xszj():
    parser = get_parser_for_source('xszj', {})
    test_book_url = 'https://xszj.org/b/413589'
    binfo = await parser.get_book_info(test_book_url)
    print(binfo.title, binfo.author, binfo.description, binfo.cover_url)
    bchapters = await parser.get_chapter_list(test_book_url)
    print(len(bchapters))
    uchapters = await parser.update_chapter_list(test_book_url, 1033)
    print(len(uchapters))
    test_chapter_url = 'https://xszj.org/b/413589/c/15830987'
    chapter_content = await parser.get_chapter_content(test_chapter_url)
    print(chapter_content)


async def test_jjwcx():
    parser = get_parser_for_source('jjwxc', {})
    test_book_url = 'https://www.jjwxc.net/onebook.php?novelid=8887715'
    book_info = await parser.get_book_info(test_book_url)
    print(book_info)
    bchapters = await parser.get_chapter_list(test_book_url)
    print(len(bchapters))
    test_chapter_url = 'https://www.jjwxc.net/onebook.php?novelid=8887715&chapterid=1'
    chapter_content = await parser.get_chapter_content(test_chapter_url)
    print(chapter_content)

async def test_luoxia():
    parser = get_parser_for_source('luoxia')
    # test_book_url = 'https://www.luoxia123.com/zhetian/'
    # book_info = await parser.get_book_info(test_book_url)
    # print(book_info)
    # bchapters = await parser.get_chapter_list(test_book_url)
    # print(len(bchapters))
    test_chapter_url = 'https://www.luoxia123.com/zhetian/203820.html'
    chapter_content = await parser.get_chapter_content(test_chapter_url)
    print(chapter_content)


async def test_uaa():
    parser = get_parser_for_source('uaa', {})
    # test_book_url = 'https://canovel.com/article/1147'
    # book_info = await parser.get_book_info(test_book_url)
    # print(book_info)
    # bchapters = await parser.get_chapter_list(test_book_url)
    # print(len(bchapters))
    test_chapter_url = 'https://yazhouse8.com/article/67851.html'
    chapter_content = await parser.get_chapter_content(test_chapter_url)
    print(chapter_content)

async def test_dybz():
    parser = get_parser_for_source('diyibanzhu')
    # test_book_url = 'https://m.diyibanzhu5.online/list/8266.html'
    # book_info = await parser.get_book_info(test_book_url)
    # print(book_info)
    # bchapters = await parser.get_chapter_list(test_book_url)
    # print(len(bchapters))
    test_chapter_url = 'https://m.diyibanzhu5.online/view/741511.html'
    chapter_content = await parser.get_chapter_content(test_chapter_url)
    print(chapter_content)

async def test_qidiy():
    parser = get_parser_for_source('qidiy')
    # test_book_url = 'http://www.qidiy.com/book/104934/'
    # book_info = await parser.get_book_info(test_book_url)
    # print(book_info)
    # bchapters = await parser.get_chapter_list(test_book_url)
    # print(len(bchapters))
    test_chapter_url = 'http://www.qidiy.com/book/104934/47845211.html'
    chapter_content = await parser.get_chapter_content(test_chapter_url)
    print(chapter_content)

async def test_jszj():
    parser = get_parser_for_source('jszj')
    sr = await parser.search_books('同事', 0)
    print(sr, len(sr))
    # test_book_url = 'http://www.jinshuzhijia.com/index.php/book/info/chuanyuedazhouwutangfengliu'
    # book_info = await parser.get_book_info(test_book_url)
    # print(book_info)
    # bchapters = await parser.get_chapter_list(test_book_url)
    # print(len(bchapters))
    # test_chapter_url = 'http://www.jinshuzhijia.com/index.php/book/read/728/222'
    # chapter_content = await parser.get_chapter_content(test_chapter_url)
    # print(chapter_content)

if __name__ == "__main__":
    # asyncio.run(test_network('https://www.xbiquge77.com/72862'))
    asyncio.run(test_base_parser())
    # asyncio.run(test_jszj())
    # asyncio.run(test_dybz())
    # from urllib.parse import urlparse
    # next_sec = 'https://xszj.org/b/413589/c/5786882?page=2'
    # chapter_sec = 'https://xszj.org/b/413589/c/5786882'
    # nexturl = urlparse(next_sec)
    # cururl = urlparse(chapter_sec)
    # print(nexturl.query, cururl.query)
