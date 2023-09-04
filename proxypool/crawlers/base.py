import asyncio
from abc import ABC, abstractmethod
from tenacity import RetryError, retry
from httpx import AsyncClient, ConnectError, ReadTimeout
from loguru import logger
from proxypool.config import config
from fake_headers import Headers


class BaseCrawler(ABC):
  urls = []

  @abstractmethod
  def parse(self, html: str):
    ...

  @retry(stop=3, retry=lambda x: x is None, wait=2000)
  async def fetch(self, url: str, **kwargs) -> str:
    try:
      headers = Headers(True).generate()
      kwargs.setdefault('timeout', config.spider.timeout)
      kwargs.setdefault('verify', False)
      kwargs.setdefault('headers', headers)
      async with AsyncClient(**kwargs) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        resp.encoding = 'utf-8'
        return resp.text
    except (ConnectError, ReadTimeout):
      return ''
    
  def process(self, html: str, url: str):
    """
    used for parse html
    """
    for proxy in self.parse(html):
      logger.info(f'Fetched proxy {proxy.string()} from {url}')
      yield proxy
  
  async def crawl(self):
    """
    Crawl main method
    """
    try:
      for url in self.urls:
        logger.info(f'fetching {url}')
        html = await self.fetch(url)
        if not html:
          continue
        await asyncio.sleep(.5)
        yield self.process(html, url)
    except RetryError:
      logger.error(f'Crawler {self} crawled proxy unsuccessfully, please check if target url is valid or network issue')
