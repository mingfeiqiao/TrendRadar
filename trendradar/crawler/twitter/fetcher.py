# coding=utf-8
"""
Twitter/X 热搜爬虫

使用 twikit 调用 Twitter 内部 API 获取热搜趋势
"""

import asyncio
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from twikit import Client
    HAS_TWIKIT = True
except ImportError:
    HAS_TWIKIT = False
    Client = None


class TwitterFetcher:
    """
    Twitter/X 热搜数据获取器

    使用 twikit 库调用 Twitter 内部 API
    """

    def __init__(
        self,
        username: str = "",
        email: str = "",
        password: str = "",
        cookies_file: str = "config/twitter_cookies.json",
        proxy_url: str = "",
        trends_count: int = 20,
    ):
        """
        初始化 Twitter 爬虫

        Args:
            username: Twitter 用户名
            email: Twitter 邮箱
            password: Twitter 密码
            cookies_file: Cookie 缓存文件路径
            proxy_url: 代理地址
            trends_count: 获取热搜数量
        """
        if not HAS_TWIKIT:
            raise ImportError(
                "twikit 未安装，请运行: pip install twikit"
            )

        self.username = username or os.environ.get("TWITTER_USERNAME", "")
        self.email = email or os.environ.get("TWITTER_EMAIL", "")
        self.password = password or os.environ.get("TWITTER_PASSWORD", "")
        self.cookies_file = cookies_file
        self.proxy_url = proxy_url
        self.trends_count = trends_count

        self._client: Optional[Client] = None
        self._logged_in = False

    async def _get_client(self) -> Client:
        """获取或创建 Twitter 客户端"""
        if self._client is None:
            self._client = Client('zh-CN')
            if self.proxy_url:
                # twikit 支持代理配置
                self._client.set_proxy(self.proxy_url)
        return self._client

    async def _ensure_login(self) -> bool:
        """确保已登录"""
        if self._logged_in:
            return True

        client = await self._get_client()

        # 尝试加载已保存的 cookies
        if Path(self.cookies_file).exists():
            try:
                await client.load_cookies(self.cookies_file)
                self._logged_in = True
                print("[Twitter] 使用缓存的 Cookie 登录成功")
                return True
            except Exception as e:
                print(f"[Twitter] 加载 Cookie 失败: {e}")

        # 使用账号密码登录
        if not all([self.username, self.password]):
            print("[Twitter] 缺少登录凭据，请配置 TWITTER_USERNAME/EMAIL/PASSWORD 环境变量")
            return False

        try:
            await client.login(
                auth_info_1=self.username,
                auth_info_2=self.email,
                password=self.password,
                cookies_file=self.cookies_file,
            )
            self._logged_in = True
            print("[Twitter] 账号登录成功")
            return True
        except Exception as e:
            print(f"[Twitter] 登录失败: {e}")
            return False

    async def fetch_trends(self) -> Tuple[Dict, str, List]:
        """
        获取 Twitter 热搜趋势

        Returns:
            (results, source_name, failed_ids) 元组
            results 格式与 DataFetcher.crawl_websites() 兼容
        """
        results = {}
        failed_ids = []
        source_id = "twitter"
        source_name = "Twitter/X"

        if not await self._ensure_login():
            failed_ids.append(source_id)
            return results, source_name,_ids

        try:
            client = await self._get_client()
            trends = await client.get_trends('trending')

            print(f"[Twitter] 获取到 {len(trends)} 条热搜")

            for rank, trend in enumerate(trends[:self.trends_count], 1):
                # 提取趋势名称
                trend_name = getattr(trend, 'name', None) or str(trend)
                trend_url = getattr(trend, 'url', None) or f"https://twitter.com/search?q={trend_name}"

                results[trend_name] = {
                    "ranks": [rank],
                    "url": trend_url,
                    "mobileUrl": "",
                }

        except Exception as e:
            print(f"[Twitter] 获取热搜失败: {e}")
            failed_ids.append(source_id)

        return {source_id: results}, source_name, failed_ids

    def fetch_trends_sync(self) -> Tuple[Dict, str, List]:
        """同步版本的热搜获取方法"""
        return asyncio.run(self.fetch_trends())
