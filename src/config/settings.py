# src/config/settings.py
import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# 全局变量
ALL_KEYWORDS = {}
ALL_PROMPTS = {}
LOG_DIR = ""
LOG_FILE = ""
config_check_passed = False

# 日志配置
def setup_logging(log_level=logging.INFO, console_level=logging.WARNING):
    """设置日志系统
    
    Args:
        log_level: 文件日志级别，默认INFO级别
        console_level: 控制台日志级别，默认WARNING级别
    """
    global LOG_DIR, LOG_FILE
    
    # 确保日志目录存在
    project_root = Path(__file__).parent.parent.parent
    LOG_DIR = os.path.join(project_root, 'logs')
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # 设置日志文件路径
    LOG_FILE = os.path.join(LOG_DIR, 'crawler.log')
    
    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # 设置为最低级别，让处理器决定过滤级别
    
    # 清除现有处理器，避免重复
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    # 文件处理器 - 详细日志
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(log_level)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)
    
    # 控制台处理器 - 简洁日志，只显示重要信息
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)  # 只显示WARNING及以上级别
    console_format = logging.Formatter('%(levelname)s: %(message)s')  # 简化的格式
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    # 特定模块的日志记录器
    logger = logging.getLogger('doc_crawler_config')
    logger.info(f"Logging configured. Log file: {LOG_FILE}")
    logger.debug(f"setup_logging completed. LOG_DIR={LOG_DIR}, LOG_FILE={LOG_FILE}")
    
    return logger

# 环境变量加载
def ensure_env_loaded() -> bool:
    """确保环境变量已加载"""
    # 尝试从.env文件加载环境变量
    env_path = os.path.join(Path(__file__).parent.parent.parent, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print("Info: .env file loaded.")
        return True
    else:
        print("Warning: .env file not found at {}".format(env_path))
        return False

# 配置文件加载
def load_json_config(file_name: str) -> Dict[str, Any]:
    """加载JSON配置文件"""
    logger = logging.getLogger('doc_crawler_config')
    project_root = Path(__file__).parent.parent.parent
    
    # 首先尝试从data目录加载
    data_path = os.path.join(project_root, 'data', file_name)
    if os.path.exists(data_path):
        config_path = data_path
    else:
        # 回退到项目根目录
        config_path = os.path.join(project_root, file_name)
    
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            logger.info(f"Successfully loaded configuration file: {config_path}")
            return config
    except Exception as e:
        logger.error(f"Error loading configuration file {config_path}: {e}")
        return {}

# 主配置加载函数
def load_all_configs(file_log_level=logging.INFO, console_log_level=logging.WARNING) -> bool:
    """加载所有配置并设置日志
    
    Args:
        file_log_level: 文件日志级别，默认INFO
        console_log_level: 控制台日志级别，默认WARNING
    """
    global ALL_KEYWORDS, ALL_PROMPTS, config_check_passed
    
    logger = setup_logging(log_level=file_log_level, console_level=console_log_level)
    logger.info("Loading configurations...")
    
    # 加载关键词和提示词配置
    ALL_KEYWORDS = load_json_config('keywords.json')
    ALL_PROMPTS = load_json_config('prompts.json')
    
    # 验证配置
    keywords_loaded = bool(ALL_KEYWORDS)
    prompts_loaded = bool(ALL_PROMPTS)
    logger.debug(f"JSON loaded. Keywords found: {keywords_loaded}, Prompts found: {prompts_loaded}")
    
    # 初始化OpenAI客户端（现在在api模块中处理）
    logger.debug("Initializing OpenAI client...")
    api_key_exists = bool(os.getenv("OPENAI_API_KEY"))
    api_base_exists = bool(os.getenv("OPENAI_API_BASE"))
    logger.debug(f"OpenAI API Key found: {api_key_exists}, API Base found: {api_base_exists}")
    
    if api_key_exists and api_base_exists:
        logger.info("OpenAI client initialized successfully.")
    else:
        logger.error("OpenAI client initialization failed. Missing API key or base URL.")
        return False
    
    # 配置验证
    logger.debug("Performing configuration validation...")
    config_check_passed = keywords_loaded and prompts_loaded and api_key_exists and api_base_exists
    logger.info(f"Configuration loading complete. Essential checks passed: {config_check_passed}")
    
    return config_check_passed
