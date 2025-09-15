"""
书源解析器动态加载器
负责加载和管理所有书源解析器
"""

import os
import importlib
import inspect
import json
from typing import Dict, Type, Optional, List
from .base_parser import BaseBookSourceParser
from urllib.parse import urlparse


class ParserLoader:
    """解析器加载器"""

    def __init__(self):
        self._parsers: List[BaseBookSourceParser] = []
        self._loaded = False

    def load_parsers(self) -> None:
        """加载所有解析器"""
        if self._loaded:
            return

        # 获取项目根目录
        current_dir = os.path.dirname(os.path.dirname(__file__))
        sources_dir = os.path.join(current_dir, 'sources')

        # 检查sources目录是否存在
        if not os.path.exists(sources_dir):
            print("sources目录不存在，跳过扩展解析器加载")
            self._loaded = True
            return

        # 遍历sources目录下的所有Python文件
        for filename in os.listdir(sources_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                module_name = filename[:-3]  # 移除.py后缀

                try:
                    # 动态导入模块
                    module = importlib.import_module(f'sources.{module_name}')

                    # 查找继承自BaseBookSourceParser的类
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and
                            issubclass(obj, BaseBookSourceParser) and
                            obj != BaseBookSourceParser):
                            p = obj()
                            self._parsers.append(p)
                            print(f"加载扩展解析器: {p.get_parser_name()} -> {obj.__name__}")

                except Exception as e:
                    print(f"加载扩展解析器模块 {module_name} 失败: {e}")

        if os.path.isfile(os.path.join(sources_dir, 'sources.json')):
            print("加载sources/sources.json")
            with open(os.path.join(sources_dir, 'sources.json'), 'r', encoding='utf-8') as f:
                sources = json.load(f)
            for source_config in sources:
                self.create_base_parser(source_config, save=False)

        self._loaded = True
        print(f"共加载 {len(self._parsers)} 个扩展解析器")

    def get_parser(self, source_name: str) -> BaseBookSourceParser:
        """
        获取指定书源的解析器

        Args:
            source_name: 书源名称
            source_config: 书源配置

        Returns:
            解析器实例
        """
        self.load_parsers()

        # 尝试根据书源名称匹配特定解析器
        parser_key = source_name.lower().replace(' ', '').replace('-', '').replace('_', '')
        for parser in self._parsers:
            if parser_key in parser.get_parser_name():
                print(f"使用解析器: {parser.__class__.__name__} for {source_name}")
                return parser

    def create_base_parser(self, source_config: dict, save=True) -> BaseBookSourceParser:
        """
        创建基础解析器

        Args:
            source_config: 书源配置

        Returns:
            基础解析器实例
        """
        parser = BaseBookSourceParser(source_config)
        if save:
            current_dir = os.path.dirname(os.path.dirname(__file__))
            sources_dir = os.path.join(current_dir, 'sources')
            if not os.path.isdir(sources_dir):
                os.makedirs(sources_dir)
            jpath = os.path.join(sources_dir, 'sources.json')
            existing_sources = []
            if os.path.isfile(jpath):
                with open(jpath, 'r', encoding='utf-8') as f:
                    existing_sources = json.load(f)

            existing_sources.append(source_config)
            with open(jpath, 'w', encoding='utf-8') as f:
                json.dump(existing_sources, f, ensure_ascii=False, indent=4)
        self._parsers.append(parser)
        print(f"加载解析器: {parser.get_parser_name()} -> {BaseBookSourceParser.__name__}")
        return parser

    def get_parser_for_url(self, url: str) -> BaseBookSourceParser:
        """
        获取指定URL的解析器

        Args:
            url: 目标URL
            source_config: 书源配置

        Returns:
            解析器实例
        """
        self.load_parsers()
        for parser in self._parsers:
            if parser.can_handle_url(url):
                return parser

    def list_available_parsers(self) -> List[str]:
        """列出所有可用的解析器"""
        self.load_parsers()
        return self._parsers

    def reload_parsers(self) -> None:
        """重新加载所有解析器"""
        self._parsers.clear()
        self._loaded = False
        self.load_parsers()


# 全局解析器加载器实例
parser_loader = ParserLoader()


def list_available_parsers():
    """列出所有可用的解析器"""
    return parser_loader.list_available_parsers()

def get_parser_for_source(source_name: str, source_config: dict={}) -> BaseBookSourceParser:
    """
    为指定书源获取解析器的便捷函数

    Args:
        source_name: 书源名称
        source_config: 书源配置

    Returns:
        解析器实例
    """
    p = parser_loader.get_parser(source_name)
    if not p:
        p = parser_loader.create_base_parser(source_config)
    return p


def get_parser_for_url(url: str, source_config: dict={}) -> BaseBookSourceParser:
    """
    为指定URL获取解析器的便捷函数

    Args:
        url: 目标URL
        source_config: 书源配置

    Returns:
        解析器实例
    """
    p = parser_loader.get_parser_for_url(url)
    if not p:
        p = parser_loader.create_base_parser(source_config)
    return p
