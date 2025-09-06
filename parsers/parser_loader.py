"""
书源解析器动态加载器
负责加载和管理所有书源解析器
"""

import os
import importlib
import inspect
from typing import Dict, Type, Optional, List
from .base_parser import BaseBookSourceParser


class ParserLoader:
    """解析器加载器"""
    
    def __init__(self):
        self._parsers: Dict[str, Type[BaseBookSourceParser]] = {}
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
                            
                            parser_name = obj.get_parser_name()
                            if isinstance(parser_name, (list, tuple)):
                                for pn in parser_name:
                                    self._parsers[pn] = obj
                            else:
                                self._parsers[parser_name] = obj
                            print(f"加载扩展解析器: {parser_name} -> {obj.__name__}")
                            
                except Exception as e:
                    print(f"加载扩展解析器模块 {module_name} 失败: {e}")
        
        self._loaded = True
        print(f"共加载 {len(self._parsers)} 个扩展解析器")
    
    def get_parser(self, source_name: str, source_config: dict) -> BaseBookSourceParser:
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
        
        for key, parser_class in self._parsers.items():
            if key in parser_key or parser_key in key:
                print(f"使用特定解析器: {parser_class.__name__} for {source_name}")
                return parser_class(source_config)
        
        # 如果没有找到特定解析器，使用基础解析器
        print(f"使用基础解析器 for {source_name}")
        return BaseBookSourceParser(source_config)
    
    def get_parser_by_url(self, url: str, source_config: dict) -> BaseBookSourceParser:
        """
        根据URL获取最适合的解析器
        
        Args:
            url: 目标URL
            source_config: 书源配置
            
        Returns:
            解析器实例
        """
        self.load_parsers()
        
        # 尝试找到能处理该URL的特定解析器
        for parser_class in self._parsers.values():
            temp_parser = parser_class(source_config)
            if temp_parser.can_handle_url(url):
                print(f"根据URL使用特定解析器: {parser_class.__name__}")
                return temp_parser
        
        # 如果没有找到特定解析器，使用基础解析器
        print(f"根据URL使用基础解析器")
        return BaseBookSourceParser(source_config)
    
    def list_available_parsers(self) -> List[str]:
        """列出所有可用的解析器"""
        self.load_parsers()
        return list(self._parsers.keys())
    
    def reload_parsers(self) -> None:
        """重新加载所有解析器"""
        self._parsers.clear()
        self._loaded = False
        self.load_parsers()


# 全局解析器加载器实例
parser_loader = ParserLoader()


def get_parser_for_source(source_name: str, source_config: dict) -> BaseBookSourceParser:
    """
    为指定书源获取解析器的便捷函数
    
    Args:
        source_name: 书源名称
        source_config: 书源配置
        
    Returns:
        解析器实例
    """
    return parser_loader.get_parser(source_name, source_config)


def get_parser_for_url(url: str, source_config: dict) -> BaseBookSourceParser:
    """
    为指定URL获取解析器的便捷函数
    
    Args:
        url: 目标URL
        source_config: 书源配置
        
    Returns:
        解析器实例
    """
    return parser_loader.get_parser_by_url(url, source_config)