#!/usr/bin/env python
# scripts/main.py
import argparse
import asyncio
import os
import logging
import sys
import time
from datetime import datetime
from typing import List
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入自定义模块
try:
    from src.crawler.core import DocCrawler
    from src.config.settings import load_all_configs, config_check_passed, LOG_FILE, LOG_DIR, ensure_env_loaded
    from src.utils.url import get_urls_from_sitemap
    from src.utils.file import ensure_directory_exists
except ImportError as e:
    print(f"致命错误: 无法导入必要的模块。请确保项目结构正确。详情: {e}")
    sys.exit(1)

# 初始化日志记录器
logger = logging.getLogger('doc_crawler_main')

async def run_crawler(args):
    """根据参数初始化并运行爬虫"""
    start_time = time.time()
    logger.info(f"爬虫开始处理，时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"参数: {args}")

    # 创建基于文档类型的输出目录
    output_subdir = f"{args.doc_type}"
    if args.focus: output_subdir += f"_focus-{args.focus.replace(' ', '_')}"
    if args.tool_name: output_subdir += f"_tool-{args.tool_name.replace(' ', '_')}"
    
    # 设置输出目录
    output_base_dir = os.path.dirname(LOG_DIR)  # 将输出目录放在与 'logs' 同级的位置
    output_dir = os.path.join(output_base_dir, 'output', output_subdir)
    ensure_directory_exists(output_dir)
    logger.info(f"输出目录: {output_dir}")

    # 初始化爬虫实例
    crawler = DocCrawler(
        doc_type=args.doc_type,
        focus=args.focus,
        tool_name=args.tool_name,
        max_pages=args.max_pages,
        respect_robots_txt=not args.ignore_robots,  # 注意取反
        rate_limit_delay=(args.min_delay, args.max_delay)
    )

    urls_to_process: List[str] = []

    if args.mode == 'count':
        logger.info(f"模式: count - 统计相关 URL 数量: {args.url}")
        await crawler.count_crawlable_urls(args.url)
    elif args.mode == 'process':
        logger.info(f"模式: process - 爬取并处理内部链接: {args.url}")
        
        # 1. 尝试从网站地图获取 URL
        logger.info(f"尝试从网站地图获取 URL: {args.url}...")
        sitemap_urls = await get_urls_from_sitemap(args.url)

        if sitemap_urls:
            logger.info(f"在网站地图中找到 {len(sitemap_urls)} 个 URL。使用这些 URL 进行处理。")
            urls_to_process = sitemap_urls[:args.max_pages]  # 限制页面数量
        else:
            logger.warning("网站地图获取失败。回退到爬取初始页面的链接。")
            # 2. 回退: 从初始页面获取内部链接
            internal_urls, base_domain, _ = await crawler.get_internal_links(args.url)
            if not internal_urls:
                logger.error("从初始页面也没有找到内部链接。退出。")
                return
            logger.info(f"通过爬取找到 {len(internal_urls)} 个内部链接。使用这些链接进行处理。")
            urls_to_process = internal_urls[:args.max_pages]  # 限制页面数量

        if not urls_to_process:
            logger.error("没有要处理的 URL。")
            return

        # 处理收集到的 URL
        processed_results = await crawler.crawl_and_process_internal_links(
            urls_to_process,
            output_dir=output_dir,
            max_pages=args.max_pages,
            min_delay=args.min_delay,
            max_delay=args.max_delay
        )
        
        # 输出处理结果
        for result in processed_results:
            if result:  # 过滤掉None值
                logger.info(f"URL: {result['url']} -> 文件: {result['output']}")
    else:
        # 由于 argparse 的 choices 参数，这种情况应该不会发生
        logger.error(f"指定了无效的模式: {args.mode}")

    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"爬虫处理完成，耗时 {duration:.2f} 秒。")
    logger.info(f"日志文件位置: {LOG_FILE}")
    logger.info(f"输出文件位置: {output_dir}")

def main():
    """主函数"""
    # 1. 首先确保环境变量已加载
    ensure_env_loaded()

    # 2. 设置命令行参数解析
    parser = argparse.ArgumentParser(description="简易文档爬虫")
    
    # 核心参数
    parser.add_argument("url", help="要爬取的起始网址")
    parser.add_argument("mode", choices=['count', 'process'], help="操作模式：'count' 统计内部链接数量，'process' 爬取并处理页面")
    parser.add_argument("--doc_type", default="general", help="文档类型（如 'tutorial', 'api_reference', 'general'），用于选择关键词/提示词")

    # 内容处理参数（仅 'process' 模式需要）
    parser.add_argument("--extract_usage_only", action="store_true", help="仅提取用法相关内容（LLM根据关键词/关注点抽取）")
    parser.add_argument("--focus", help="可选：指定 LLM 抽取时关注的内容（如 '安装步骤'、'认证方式' 等）")
    parser.add_argument("--tool_name", help="可选：文档中涉及的具体工具或库名")

    # 爬取行为参数
    parser.add_argument("--max_pages", type=int, default=20, help="最多爬取并处理多少个内部页面")
    parser.add_argument("--min_delay", type=float, default=1.0, help="每次请求的最小延时（秒）")
    parser.add_argument("--max_delay", type=float, default=3.0, help="每次请求的最大延时（秒）")
    parser.add_argument("--ignore_robots", action="store_true", help="忽略 robots.txt 规则（谨慎使用，需尊重网站政策）")
    
    # 日志控制参数
    parser.add_argument("--quiet", action="store_true", help="安静模式，控制台只显示错误信息")
    parser.add_argument("--verbose", action="store_true", help="详细模式，显示所有调试信息")
    parser.add_argument("--no-debug-content", action="store_true", help="不在控制台显示内容过滤结果")

    # 3. 处理命令行参数并设置日志级别
    args = parser.parse_args()
    
    # 根据命令行参数设置日志级别
    file_log_level = logging.INFO  # 文件始终使用INFO级别
    console_log_level = logging.WARNING  # 默认控制台级别
    
    if args.quiet:
        console_log_level = logging.ERROR  # 安静模式，只显示错误
    elif args.verbose:
        console_log_level = logging.DEBUG  # 详细模式，显示所有调试信息
    
    # 设置是否显示内容过滤结果的环境变量
    if args.no_debug_content:
        os.environ['NO_DEBUG_CONTENT'] = 'true'
    
    # 加载配置并设置日志
    load_configs_success = load_all_configs(file_log_level=file_log_level, console_log_level=console_log_level)

    if not load_configs_success:
        # 日志应该已经由 load_all_configs 设置，即使它失败了
        logging.getLogger('doc_crawler_main').critical("配置加载失败，未通过基本检查。请查看日志和配置文件。退出。")
        sys.exit(1)

    # 运行异步函数
    try:
        asyncio.run(run_crawler(args))
    except KeyboardInterrupt:
        logging.getLogger('doc_crawler_main').info("爬虫进程被用户中断。")
    except Exception as e:
        logging.getLogger('doc_crawler_main').critical(f"发生意外错误: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
