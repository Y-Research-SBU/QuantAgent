# -*- coding: utf-8 -*-
"""
TradingGraph: 使用LangChain和LangGraph协调多智能体交易系统。

该模块负责初始化大语言模型（LLM）、工具包以及用于指标、形态和趋势分析的代理节点。
"""

import os
from typing import Dict

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode

from default_config import DEFAULT_CONFIG
from graph_setup import SetGraph
from graph_util import TechnicalTools


class TradingGraph:
    """
    多智能体交易系统的主要协调器。

    该类负责设置LLM、工具包以及用于指标、形态和趋势分析的代理节点，
    并最终构建可执行的分析图。
    """

    def __init__(self, config=None):
        """
        初始化TradingGraph。

        Args:
            config (dict, optional): 自定义配置字典。如果未提供，则使用默认配置。
        """
        # --- 配置和LLM ---
        self.config = config if config is not None else DEFAULT_CONFIG.copy()

        # 获取并验证API密钥
        api_key = self._get_api_key()

        # 使用明确的API密钥初始化LLM
        self.agent_llm = ChatOpenAI(
            model=self.config.get("agent_llm_model", "gpt-4o-mini"),
            temperature=self.config.get("agent_llm_temperature", 0.1),
            api_key=api_key,
        )
        self.graph_llm = ChatOpenAI(
            model=self.config.get("graph_llm_model", "gpt-4o"),
            temperature=self.config.get("graph_llm_temperature", 0.1),
            api_key=api_key,
        )
        self.toolkit = TechnicalTools()

        # --- 为每个代理创建工具节点 ---
        self.tool_nodes = self._set_tool_nodes()

        # --- 图逻辑和设置 ---
        self.graph_setup = SetGraph(
            self.agent_llm,
            self.graph_llm,
            self.toolkit,
            self.tool_nodes,
        )

        # --- 主要的LangGraph图对象 ---
        self.graph = self.graph_setup.set_graph()

    def _get_api_key(self):
        """
        获取并验证API密钥。

        Returns:
            str: OpenAI API密钥。

        Raises:
            ValueError: 如果API密钥缺失或无效。
        """
        # 首先检查配置中是否提供了API密钥
        api_key = self.config.get("api_key")

        # 如果配置中没有，则检查环境变量
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY")

        # 验证API密钥
        if not api_key:
            raise ValueError(
                "未找到OpenAI API密钥。请使用以下方法之一设置：\n"
                "1. 设置环境变量: export OPENAI_API_KEY='your-key-here'\n"
                "2. 更新配置: config['api_key'] = 'your-key-here'\n"
                "3. 使用Web界面更新API密钥"
            )

        if api_key == "your-openai-api-key-here" or api_key == "":
            raise ValueError(
                "请将占位符API密钥替换为您的实际OpenAI API密钥。"
                "您可以从以下地址获取：https://platform.openai.com/api-keys"
            )

        return api_key

    def _set_tool_nodes(self) -> Dict[str, ToolNode]:
        """
        为每种类型的代理（指标、形态、趋势）定义工具节点。

        Returns:
            dict: 包含为每个代理配置的ToolNode的字典。
        """
        return {
            "indicator": ToolNode(
                [
                    self.toolkit.compute_macd,
                    self.toolkit.compute_roc,
                    self.toolkit.compute_rsi,
                    self.toolkit.compute_stoch,
                    self.toolkit.compute_willr,
                ]
            ),
            "pattern": ToolNode(
                [
                    self.toolkit.generate_kline_image,
                ]
            ),
            "trend": ToolNode([self.toolkit.generate_trend_image]),
        }

    def refresh_llms(self):
        """
        使用当前环境中的API密钥刷新LLM对象。

        当API密钥更新时调用此方法。
        """
        # 获取并验证当前API密钥
        api_key = self._get_api_key()

        # 使用明确的API密钥和配置值重新创建LLM对象
        self.agent_llm = ChatOpenAI(
            model=self.config.get("agent_llm_model", "gpt-4o-mini"),
            temperature=self.config.get("agent_llm_temperature", 0.1),
            api_key=api_key,
        )
        self.graph_llm = ChatOpenAI(
            model=self.config.get("graph_llm_model", "gpt-4o"),
            temperature=self.config.get("graph_llm_temperature", 0.1),
            api_key=api_key,
        )

        # 使用新的LLM重新创建图设置
        self.graph_setup = SetGraph(
            self.agent_llm,
            self.graph_llm,
            self.toolkit,
            self.tool_nodes,
        )

        # 重新创建主图
        self.graph = self.graph_setup.set_graph()

    def update_api_key(self, api_key: str):
        """
        更新配置中的API密钥并刷新LLM。

        当通过Web界面更新API密钥时，会调用此方法。

        Args:
            api_key (str): 新的OpenAI API密钥。
        """
        # 更新配置中的API密钥
        self.config["api_key"] = api_key

        # 同时更新环境变量以保持一致性
        os.environ["OPENAI_API_KEY"] = api_key

        # 使用新的API密钥刷新LLM
        self.refresh_llms()
