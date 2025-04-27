# src/api/openai_client.py
import os
import logging
from openai import AsyncOpenAI
from typing import Optional, Dict, Any, List

logger = logging.getLogger('doc_crawler_api')

# 全局客户端实例
_openai_client = None

def get_openai_client() -> AsyncOpenAI:
    """
    获取或创建 OpenAI 客户端实例
    使用单例模式确保只创建一个客户端实例
    """
    global _openai_client
    
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        api_base = os.getenv("OPENAI_API_BASE")
        
        if not api_key or not api_base:
            logger.error("OpenAI API 密钥或基础 URL 未设置")
            raise ValueError("OpenAI API 密钥或基础 URL 未设置")
        
        _openai_client = AsyncOpenAI(api_key=api_key, base_url=api_base)
        logger.debug("OpenAI 客户端已初始化")
    
    return _openai_client

import random
import asyncio

async def optimize_markdown(markdown_content: str, instruction: str, model: str = "Pro/deepseek-ai/DeepSeek-R1", llm_semaphore: asyncio.Semaphore = asyncio.Semaphore(1)) -> Optional[str]:
    """
    使用 OpenAI API 优化和翻译 Markdown 内容，并限制并发，增加请求延迟，防止被封/反爬
    
    Args:
        markdown_content: 原始 Markdown 内容
        instruction: 给 LLM 的指令
        model: 使用的模型名称
        llm_semaphore: 控制并发的信号量
    Returns:
        优化后的 Markdown 内容，如果失败则返回 None
    """
    if not markdown_content or markdown_content.isspace():
        logger.warning("传入的 Markdown 内容为空或只包含空白字符")
        return None
    
    try:
        async with llm_semaphore:
            client = get_openai_client()
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一个专业的文档优化助手，擅长将技术文档转换为结构化的中文内容。"}, 
                    {"role": "user", "content": f"{instruction}\n\n原始 Markdown 内容如下：\n\n{markdown_content}"}
                ],
                temperature=0.5,  # 可以调整温度以获得更确定性或创造性的结果
            )
            # 增加延迟，防止触发反爬
            await asyncio.sleep(random.uniform(2.0, 4.0))
            if response.choices and response.choices[0].message and response.choices[0].message.content:
                optimized_content = response.choices[0].message.content
                logger.info("LLM 优化/翻译成功")
                return optimized_content.strip()  # 移除首尾空白
            else:
                logger.error(f"LLM 响应格式无效或内容为空。响应: {response}")
                return None
    except Exception as e:
        logger.error(f"调用 LLM API 时出错: {e}")
        return None
