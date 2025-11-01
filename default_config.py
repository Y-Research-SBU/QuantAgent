# -*- coding: utf-8 -*-
"""
默认配置文件
"""

DEFAULT_CONFIG = {
    # 用于单个代理（如指标、模式、趋势分析）的语言模型
    "agent_llm_model": "gpt-4o-mini",

    # 用于图逻辑和最终决策制定的语言模型
    "graph_llm_model": "gpt-4o",

    # 代理响应的温度（控制创造性，值越低越确定）
    "agent_llm_temperature": 0.1,

    # 图逻辑响应的温度
    "graph_llm_temperature": 0.1,

    # OpenAI API密钥（留空则从环境变量或Web界面读取）
    "api_key": "",
}
