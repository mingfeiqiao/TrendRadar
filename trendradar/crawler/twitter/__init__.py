# coding=utf-8
"""
Twitter 热搜爬虫模块

使用 twikit 调用 Twitter 内部 API 获取热搜趋势
"""

from .fetcher import TwitterFetcher

__all__ = ["TwitterFetcher"]
