# src/utils/url.py
import logging
import requests
from typing import List, Optional, Tuple, Set
from urllib.parse import urlparse, urljoin
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

logger = logging.getLogger('doc_crawler')

def normalize_url(url: str) -> str:
    """
    标准化 URL，去除末尾斜杠（保留根域名的斜杠）
    
    Args:
        url: 要标准化的 URL
        
    Returns:
        标准化后的 URL
    """
    if url.endswith('/') and url != 'https://' and url != 'http://':
        return url.rstrip('/')
    return url

def is_same_domain(url1: str, url2: str) -> bool:
    """
    判断两个 URL 是否属于同一域名
    
    Args:
        url1: 第一个 URL
        url2: 第二个 URL
        
    Returns:
        如果两个 URL 属于同一域名，则返回 True，否则返回 False
    """
    domain1 = urlparse(url1).netloc
    domain2 = urlparse(url2).netloc
    return domain1 == domain2

async def get_urls_from_sitemap(base_url: str) -> List[str]:
    """
    从网站的 sitemap.xml 获取 URL 列表
    
    Args:
        base_url: 网站基础 URL
        
    Returns:
        从 sitemap 中提取的 URL 列表，如果无法获取则返回空列表
    """
    parsed_url = urlparse(base_url)
    domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
    sitemap_url = f"{domain}/sitemap.xml"
    
    logger.info(f"Processing sitemap: {sitemap_url}")
    urls = []
    
    try:
        response = requests.get(sitemap_url, timeout=10)
        response.raise_for_status()
        
        # 解析 XML
        root = ET.fromstring(response.content)
        
        # 查找所有 URL 元素 (考虑不同的命名空间)
        namespaces = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        for url_elem in root.findall('.//sm:url', namespaces) or root.findall('.//url'):
            loc_elem = url_elem.find('./sm:loc', namespaces) or url_elem.find('./loc')
            if loc_elem is not None and loc_elem.text:
                urls.append(loc_elem.text)
        
        logger.info(f"Found {len(urls)} URLs in sitemap")
        return urls
    except requests.exceptions.HTTPError as e:
        logger.warning(f"HTTP error fetching {sitemap_url}: {e.response.status_code} - {e.response.reason}")
    except Exception as e:
        logger.warning(f"Error processing sitemap {sitemap_url}: {e}")
    
    logger.warning(f"Could not find or parse sitemap for {base_url}. No URLs extracted.")
    return []
