<<<<<<< HEAD
# crawl-to-md
基于AI的网页内容爬取与优化工具
=======
# 网页内容爬取与优化工具

基于crawl4ai的网页内容爬取工具，可自动提取网页内容，过滤为Markdown格式，并通过LLM进行内容优化，最终保存为结构化的Markdown文档。

## 功能特点

- 支持从网站地图(sitemap.xml)自动获取URL
- 智能提取网页内容并过滤为Markdown格式
- 使用大语言模型(LLM)优化内容结构和表达
- 支持自定义文档类型和内容关注点
- 遵守robots.txt协议，模拟人工操作避免被反爬
- 灵活的日志级别控制，支持安静模式和详细模式

## 环境配置

### 使用uv管理Python环境

本项目推荐使用[uv](https://github.com/astral-sh/uv)作为Python包管理工具，它比传统的pip更快速、更可靠。

```bash
# 安装uv (如果尚未安装)
curl -sSf https://astral.sh/uv/install.sh | bash

# 创建虚拟环境并安装依赖
uv venv
uv pip install -r requirements.txt
```

### 环境变量配置

复制example.env文件并重命名为.env，然后根据需要修改配置：

```bash
cp example.env .env
```

必须配置的环境变量：

- `OPENAI_API_KEY`: OpenAI API密钥
- `OPENAI_API_BASE`: API基础URL，使用兼容OpenAI API的第三方平台时需要设置

## 使用方法

### 基本用法

```bash
# 使用uv运行脚本
uv run scripts/main.py [URL] [MODE] [OPTIONS]
```

### 参数说明

- `URL`: 要爬取的起始网址
- `MODE`: 操作模式
  - `count`: 统计内部链接数量
  - `process`: 爬取并处理页面内容

### 常用选项

- `--doc_type TYPE`: 文档类型，如'tutorial'、'api_reference'、'general'等
- `--focus FOCUS`: 指定LLM抽取时关注的内容，如'安装步骤'、'认证方式'等
- `--tool_name NAME`: 文档中涉及的具体工具或库名
- `--max_pages N`: 最多爬取并处理多少个内部页面，默认20
- `--min_delay SEC`: 每次请求的最小延时(秒)，默认1.0
- `--max_delay SEC`: 每次请求的最大延时(秒)，默认3.0
- `--ignore_robots`: 忽略robots.txt规则(谨慎使用)

### 日志控制选项

- `--quiet`: 安静模式，控制台只显示错误信息
- `--verbose`: 详细模式，显示所有调试信息
- `--no-debug-content`: 不在控制台显示内容过滤结果

## 示例

```bash
# 爬取并处理网站的CLI文档，最多处理5个页面，使用安静模式
uv run scripts/main.py https://example.com/docs process --doc_type cli --max_pages 5 --quiet

# 统计网站内部链接数量
uv run scripts/main.py https://example.com count

# 爬取API参考文档，关注认证方式
uv run scripts/main.py https://example.com/api process --doc_type api_reference --focus "认证方式"
```

## 输出文件

处理后的Markdown文件将保存在`output/[doc_type]/`目录下，文件名基于URL生成。

## 注意事项

- 请尊重网站的robots.txt规则和使用政策
- 适当设置请求延时，避免对目标网站造成过大负载
- API密钥等敏感信息应妥善保管，不要提交到版本控制系统
>>>>>>> 1c3cde4 (Initial commit: 网页爬取与优化工具基础框架)
