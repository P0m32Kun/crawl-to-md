import os
import logging
import asyncio
from typing import Dict, Any, Optional, List, Set, Tuple
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, RateLimiter, BrowserConfig, CrawlResult, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

# 导入自定义模块
from src.api.openai_client import optimize_markdown
from src.utils.file import get_valid_filename, save_markdown_to_file
from src.utils.url import normalize_url, is_same_domain
from src.config.settings import ALL_KEYWORDS

# 默认排除的 HTML 标签
DEFAULT_EXCLUDED_TAGS = ['header', 'footer', 'nav', 'aside', 'script', 'style', 'form', 'iframe', 'button', 'input', 'select', 'textarea']

logger = logging.getLogger('doc_crawler_crawler')

class DocCrawler:
    """
    文档爬虫核心类，负责爬取网页、提取内容并处理
    """
    async def count_crawlable_urls(self, url: str):
        """
        统计指定URL下的所有可爬取内部链接数量，并打印结果
        """
        internal_links, base_domain, title = await self.get_internal_links(url)
        logger.info(f"统计了 {len(internal_links)} 个相关内部 URL: {url}。")
        for link in internal_links:
            logger.info(f"内部链接: {link}")
        return len(internal_links)

    async def crawl_and_process_internal_links(self, urls, output_dir, max_pages=20, min_delay=1.0, max_delay=3.0, extraction_strategy=None):
        """
        爬取并处理所有传入的内部链接，内容优化后保存为markdown文件
        :param urls: 需要处理的内部链接列表（字符串URL）
        :param output_dir: 输出目录
        :param max_pages: 最大处理页面数
        :param min_delay: 最小延迟（秒）
        :param max_delay: 最大延迟（秒）
        :param extraction_strategy: crawl4ai的内容抽取策略（如LLMExtractionStrategy），可选
        :return: 处理结果列表
        """
        import os
        import asyncio
        import time
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
        
        # 只处理前max_pages个链接
        urls = urls[:max_pages]
        os.makedirs(output_dir, exist_ok=True)
        results = []
        sem = asyncio.Semaphore(3)  # 控制并发数

        async def process_one(url):
            async with sem:
                await asyncio.sleep(min_delay)
                try:
                    # 配置CrawlerRunConfig，启用fit.markdown功能
                    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
                    from crawl4ai.content_filter_strategy import PruningContentFilter
                    
                    # 创建markdown生成器，使用PruningContentFilter进行内容过滤
                    md_generator = DefaultMarkdownGenerator(
                        content_filter=PruningContentFilter(threshold=0.6),
                        options={"ignore_links": False, "content_source": "cleaned_html"}
                    )
                    
                    # 创建运行配置
                    config = CrawlerRunConfig(
                        extraction_strategy=extraction_strategy if extraction_strategy is not None else None,
                        markdown_generator=md_generator,
                        word_count_threshold=100  # 降低阈值，确保捕获更多内容
                    )
                    
                    async with AsyncWebCrawler() as crawler:
                        crawl_result = await crawler.arun(url, config=config)
                        if not crawl_result.success:
                            logger.warning(f"爬取失败: {url}")
                            return None
                        # 优先使用crawl4ai抽取结果，否则用OpenAI优化
                        markdown = getattr(crawl_result, 'extracted_content', None)
                        if not markdown:
                            # 尝试获取fit_markdown内容（这是crawl4ai的主要内容提取功能）
                            fit_markdown = None
                            
                            # 先尝试从 result.markdown 获取 fit_markdown
                            if hasattr(crawl_result, 'markdown') and hasattr(crawl_result.markdown, 'fit_markdown'):
                                fit_markdown = crawl_result.markdown.fit_markdown
                            # 如果上面的方式不成功，尝试直接从 result 获取 fit_markdown
                            elif hasattr(crawl_result, 'fit_markdown'):
                                fit_markdown = crawl_result.fit_markdown
                            
                            # 如果没有fit_markdown，则尝试其他已过滤的内容
                            if not fit_markdown:
                                filtered_content = getattr(crawl_result, 'cleaned_markdown', None) or getattr(crawl_result, 'filtered_content', None)
                                content_to_process = filtered_content or getattr(crawl_result, 'html', None)
                                if not content_to_process:
                                    logger.warning(f"页面无有效内容: {url}")
                                    return None
                            else:
                                content_to_process = fit_markdown
                                
                            # 在控制台输出过滤后的内容，用于调试
                            # 仅在DEBUG级别时输出详细内容，或者环境变量未设置为禁止输出
                            if logging.getLogger().isEnabledFor(logging.DEBUG) and os.environ.get('NO_DEBUG_CONTENT') != 'true':
                                print("\n==== 传递给LLM的过滤后内容（前500字符）====")
                                print(content_to_process[:500] + ("..." if len(content_to_process) > 500 else ""))
                                print("==== 过滤后内容结束 ====\n")
                            
                            # 用OpenAI API优化内容
                            from src.api.openai_client import get_openai_client
                            # 根据内容类型调整提示语
                            if fit_markdown:
                                prompt = f"请将以下Markdown内容转换为结构化的中文markdown文档。直接输出内容，不要使用```markdown标记来包裹内容，因为输出将保存到.md文件中:\n{content_to_process[:4000]}"
                            else:
                                prompt = f"请将以下HTML内容转换为结构化的中文markdown文档。直接输出内容，不要使用```markdown标记来包裹内容，因为输出将保存到.md文件中:\n{content_to_process[:4000]}"
                            client = get_openai_client()
                            resp = await client.chat.completions.create(
                                model="Pro/deepseek-ai/DeepSeek-R1",
                                messages=[{"role": "user", "content": prompt}]
                            )
                            markdown = resp.choices[0].message.content
                        # 保存为markdown文件
                        safe_name = url.replace('://', '_').replace('/', '_').replace('?', '_') + ".md"
                        out_path = os.path.join(output_dir, safe_name)
                        with open(out_path, 'w', encoding='utf-8') as f:
                            f.write(markdown)
                        logger.info(f"已保存: {out_path}")
                        return {'url': url, 'output': out_path, 'status': 'success'}
                except Exception as e:
                    logger.error(f"处理失败: {url}, 错误: {e}")
                    return None
        tasks = [process_one(u) for u in urls]
        for coro in asyncio.as_completed(tasks):
            res = await coro
            if res:
                results.append(res)
        return results

    def __init__(self,
                 doc_type: str = 'general',
                 focus: Optional[str] = None,
                 tool_name: Optional[str] = None,
                 max_pages: int = 20,
                 respect_robots_txt: bool = True,
                 rate_limit_delay: Tuple[float, float] = (1.0, 3.0)):
        """
        初始化爬虫
        
        Args:
            doc_type: 文档类型，用于选择关键词
            focus: 关注点，用于 LLM 提取
            tool_name: 工具名称
            max_pages: 最大爬取页面数
            respect_robots_txt: 是否遵守 robots.txt
            rate_limit_delay: 请求延迟范围 (最小, 最大)
        """
        self.doc_type = doc_type
        self.focus = focus
        self.tool_name = tool_name
        self.max_pages = max_pages
        self.respect_robots_txt = respect_robots_txt
        self.keywords = ALL_KEYWORDS.get(self.doc_type, [])
        # 降低爬虫并发，增加请求间隔，防止被封/反爬
        self.rate_limiter = RateLimiter(rate_limit_delay[0], rate_limit_delay[1])  # 只传递延迟参数，避免不兼容
        self.processed_urls = set()
        self.markdown_generator = DefaultMarkdownGenerator()
        
        logger.info(f"爬虫初始化完成。文档类型: {doc_type}, 最大页面数: {max_pages}, 延迟: {rate_limit_delay}")

    async def get_internal_links(self, initial_url: str) -> Tuple[List[str], str, str]:
        """
        获取指定页面的所有内部链接
        Args:
            initial_url: 初始 URL
        Returns:
            (内部链接列表, 基础域名, 页面标题)
        """
        logger.info(f"获取内部链接: {initial_url}")
        internal_links = set()  # 用 set 去重
        title = ""
        
        # 解析 URL 获取基础域名
        parsed_url = urlparse(initial_url)
        base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"

        def is_valid_href(href):
            # 过滤锚点、js、mailto等无效链接
            if not href or href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
                return False
            return True

        def is_same_site(base_url, target_url):
            # 只允许同一站点
            return urlparse(base_url).netloc == urlparse(target_url).netloc

        try:
            # 配置爬虫
            browser_cfg = BrowserConfig(headless=True)
            async with AsyncWebCrawler(rate_limiter=self.rate_limiter, config=browser_cfg, 
                                      respect_robots_txt=self.respect_robots_txt) as crawler:
                logger.info(f"获取初始 URL: {initial_url}")
                # 爬取初始页面
                crawl_result = await crawler.arun(initial_url, max_depth=0)
                
                if not crawl_result.success:
                    logger.error(f"爬取初始 URL 失败: {initial_url}, 错误: {crawl_result.error_message}")
                    return [], base_domain, title
                
                # 解析 HTML
                # 优先使用 crawl_result.html，其次 cleaned_html，若都没有则报错
                html = getattr(crawl_result, 'html', None)
                if not html:
                    html = getattr(crawl_result, 'cleaned_html', None)
                if not html:
                    logger.error(f"CrawlResult 没有 html 或 cleaned_html 属性: {initial_url}")
                    return [], base_domain, title
                soup = BeautifulSoup(html, 'html.parser')
                
                # 提取标题
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.text.strip()
                
                # 兼容 crawl4ai 返回的字典列表或字符串列表，统一只返回字符串URL列表
                raw_links = crawl_result.links.get("internal", [])
                if raw_links and isinstance(raw_links[0], dict):
                    internal_links = [item.get("href") for item in raw_links if item.get("href")]
                else:
                    internal_links = raw_links
        except Exception as e:
            logger.error(f"获取内部链接异常: {e}")
            return [], base_domain, title
        return internal_links, base_domain, title
