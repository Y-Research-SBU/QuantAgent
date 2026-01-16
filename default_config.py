import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取LLM提供商设置
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "deepseek")

# 根据提供商设置默认模型
if LLM_PROVIDER == "deepseek":
    DEFAULT_AGENT_MODEL = "deepseek-chat"
    DEFAULT_GRAPH_MODEL = "deepseek-chat"
else:  # openai
    DEFAULT_AGENT_MODEL = "gpt-4o-mini"
    DEFAULT_GRAPH_MODEL = "gpt-4o"

DEFAULT_CONFIG = {
    "llm_provider": LLM_PROVIDER,
    "agent_llm_model": DEFAULT_AGENT_MODEL,
    "graph_llm_model": DEFAULT_GRAPH_MODEL,
    "agent_llm_temperature": 0.1,
    "graph_llm_temperature": 0.1,
    "api_key": "sk-",  # OpenAI API key
    "anthropic_api_key": "sk-",  # Anthropic API key (optional, can also use ANTHROPIC_API_KEY env var)
    "qwen_api_key": "sk-",  # Qwen API key (optional, can also use DASHSCOPE_API_KEY env var)
}
