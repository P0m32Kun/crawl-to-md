# src/utils/file.py
import os
import re
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger('doc_crawler_utils')

def get_valid_filename(url: str) -> str:
    """
    u6839u636e URL u751fu6210u6709u6548u7684u6587u4ef6u540d
    
    Args:
        url: u8981u5904u7406u7684 URL
        
    Returns:
        u6709u6548u7684u6587u4ef6u540duff0cu5305u542b .md u540eu7f00
    """
    # u89e3u6790 URL u5e76u63d0u53d6u57dfu540du548cu8defu5f84
    parsed = urlparse(url)
    domain = parsed.netloc
    path = parsed.path
    
    # u5982u679cu8defu5f84u4ee5u659cu6760u7ed3u5c3euff0cu5219u6dfbu52a0 'index'
    if path.endswith('/'):
        path = path + 'index'
    elif not path:  # u5982u679cu8defu5f84u4e3au7a7a
        path = '/index'
    
    # u5408u5e76u57dfu540du548cu8defu5f84uff0cu66ffu6362u65e0u6548u5b57u7b26
    filename = domain + path
    
    # u66ffu6362u65e0u6548u5b57u7b26
    filename = re.sub(r'[^\w\-\.]', '_', filename)
    filename = re.sub(r'_+', '_', filename)  # u5c06u591au4e2au4e0bu5212u7ebfu538bu7f29u4e3au4e00u4e2a
    
    # u6dfbu52a0 .md u540eu7f00
    if not filename.endswith('.md'):
        filename = filename + '.md'
    
    return filename

def ensure_directory_exists(directory_path: str) -> None:
    """
    u786eu4fddu76eeu5f55u5b58u5728uff0cu5982u679cu4e0du5b58u5728u5219u521bu5efa
    
    Args:
        directory_path: u76eeu5f55u8defu5f84
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        logger.debug(f"u76eeu5f55u786eu8ba4u6216u521bu5efau6210u529f: {directory_path}")
    except Exception as e:
        logger.error(f"u521bu5efau76eeu5f55u65f6u51fau9519 {directory_path}: {e}")
        raise

def save_markdown_to_file(content: str, file_path: str) -> bool:
    """
    u5c06 Markdown u5185u5bb9u4fddu5b58u5230u6587u4ef6
    
    Args:
        content: Markdown u5185u5bb9
        file_path: u4fddu5b58u8defu5f84
        
    Returns:
        u662fu5426u4fddu5b58u6210u529f
    """
    try:
        # u786eu4fddu76eeu5f55u5b58u5728
        directory = os.path.dirname(file_path)
        ensure_directory_exists(directory)
        
        # u5199u5165u6587u4ef6
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"u5185u5bb9u5df2u4fddu5b58u5230u6587u4ef6: {file_path}")
        return True
    except Exception as e:
        logger.error(f"u4fddu5b58u5185u5bb9u5230u6587u4ef6u65f6u51fau9519 {file_path}: {e}")
        return False
