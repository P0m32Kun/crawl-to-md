# 项目结构说明

本文件详细说明了项目中各个文件的作用，方便后期维护和更新。

## 项目根目录

- `README.md` - 项目说明文档，包含使用方法和功能介绍
- `.gitignore` - Git版本控制忽略规则，防止敏感信息和临时文件被提交
- `example.env` - 环境变量模板，用于指导用户配置API密钥等敏感信息
- `.env` - 实际的环境变量文件（不应被提交到版本控制系统）
- `PROJECT_STRUCTURE.md` - 本文件，说明项目结构

## scripts 目录

- `main.py` - 项目的主入口脚本
  - 处理命令行参数解析
  - 配置日志级别（支持--quiet和--verbose模式）
  - 初始化环境变量和配置
  - 调用爬虫功能执行网页爬取和处理

## src 目录

### src/api

- `__init__.py` - 包初始化文件
- `openai_client.py` - OpenAI API客户端实现
  - 提供单例模式的AsyncOpenAI客户端
  - 实现`optimize_markdown`函数，调用LLM优化Markdown内容
  - 支持自定义API基础URL，兼容第三方平台（如硅基流动）

### src/config

- `__init__.py` - 包初始化文件
- `settings.py` - 项目配置管理
  - 日志配置（`setup_logging`）：支持文件和控制台不同级别的日志
  - 环境变量加载（`ensure_env_loaded`）：从.env文件加载环境变量
  - 全局配置项：包含各种文档类型的关键词和提示词模板
  - 配置检查：确保必要的环境变量和配置项存在

### src/crawler

- `__init__.py` - 包初始化文件
- `core.py` - 爬虫核心功能实现
  - `DocCrawler`类：负责网页爬取、内容过滤和LLM处理
  - 使用crawl4ai库进行网页爬取和内容提取
  - 实现`fit_markdown`过滤，确保传递给LLM的是高质量Markdown
  - 提供`get_llm_prompt`方法生成针对不同文档类型的提示词
  - 实现`crawl_and_process_internal_links`方法处理批量URL

### src/utils

- `__init__.py` - 包初始化文件
- `file.py` - 文件操作工具函数
  - `get_valid_filename`：将URL转换为有效的文件名
  - `ensure_directory_exists`：确保目录存在
  - `save_markdown_to_file`：保存Markdown内容到文件
- `url.py` - URL处理工具函数
  - `normalize_url`：规范化URL格式
  - `is_same_domain`：判断URL是否属于同一域名
  - `get_urls_from_sitemap`：从网站地图获取URL列表

## 输出目录

- `output/` - 生成的Markdown文件输出目录
  - 按文档类型分类（如`cli`、`api_reference`等）
  - 文件名基于URL生成，确保唯一性
  - 不应被提交到版本控制系统

## 日志目录

- `logs/` - 日志文件目录
  - 包含详细的运行日志
  - 不应被提交到版本控制系统

## 核心功能流程

1. `scripts/main.py` 解析命令行参数并初始化环境
   - 支持`count`和`process`两种模式
   - 可配置日志级别、最大页面数、延时等参数

2. `src/crawler/core.py` 中的 `DocCrawler` 类实现爬取和处理功能
   - 优先从网站地图获取URL，失败则爬取内部链接
   - 使用crawl4ai库爬取网页并过滤为Markdown
   - 确保使用`fit_markdown`获取高质量内容

3. 通过 `src/api/openai_client.py` 调用LLM优化内容
   - 使用异步API调用提高效率
   - 根据文档类型和关注点生成专门的提示词
   - 指导LLM生成结构化、易读的Markdown内容

4. 使用 `src/utils/file.py` 中的函数保存处理后的Markdown文件
   - 生成基于URL的有效文件名
   - 确保输出目录存在
   - 保存为纯Markdown格式，不包含代码块标记

## 扩展和维护指南

### 添加新的文档类型

在 `src/config/settings.py` 中的 `ALL_KEYWORDS` 字典中添加新的文档类型和关键词。

### 修改LLM提示词

在 `src/crawler/core.py` 中的 `DocCrawler.get_llm_prompt` 方法中修改提示词模板。

### 更改输出格式

在 `src/utils/file.py` 中的 `save_markdown_to_file` 函数中修改输出格式。

### 调整日志配置

在 `src/config/settings.py` 中的 `setup_logging` 函数中修改日志配置。

### 添加新的API支持

在 `src/api/openai_client.py` 中扩展客户端功能，支持更多API选项或模型。
