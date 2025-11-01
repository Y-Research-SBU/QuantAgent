"""
TradingGraph: Orchestrates the multi-agent trading system using LangChain and LangGraph.
Initializes LLMs, toolkits, and agent nodes for indicator, pattern, and trend analysis.
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
    Main orchestrator for the multi-agent trading system.
    Sets up LLMs, toolkits, and agent nodes for indicator, pattern, and trend analysis.
    """

    def __init__(self, config=None):
        # --- Configuration and LLMs ---
        self.config = config if config is not None else DEFAULT_CONFIG.copy()
        self.toolkit = TechnicalTools()

        # --- Create tool nodes for each agent ---
        self.tool_nodes = self._set_tool_nodes()

        # --- Graph logic and setup ---
        self.refresh_llms()  # Initial setup of LLMs and graph

    def _get_api_key(self):
        """
        Get API key with proper validation and error handling.

        Returns:
            str: The OpenAI API key

        Raises:
            ValueError: If API key is missing or invalid
        """
        # First check if API key is provided in config
        api_key = self.config.get("api_key")

        # If not in config, check environment variable
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY")

        # Validate the API key
        if not api_key:
            raise ValueError(
                "OpenAI API key not found. Please set it using one of these methods:\n"
                "1. Set environment variable: export OPENAI_API_KEY='your-key-here'\n"
                "2. Update the config with: config['api_key'] = 'your-key-here'\n"
                "3. Use the web interface to update the API key"
            )

        if api_key == "your-openai-api-key-here" or api_key == "":
            raise ValueError(
                "Please replace the placeholder API key with your actual OpenAI API key. "
                "You can get one from: https://platform.openai.com/api-keys"
            )

        return api_key

    def _set_tool_nodes(self) -> Dict[str, ToolNode]:
        """
        Define tool nodes for each agent type (indicator, pattern, trend).
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

    def _get_base_url(self):
        """Get API base_url."""
        return self.config.get("base_url") or os.environ.get("OPENAI_BASE_URL")

    def refresh_llms(self):
        """
        Refresh the LLM objects with the current API key from environment.
        This is called when the API key is updated.
        """
        # Get the current API key with validation
        api_key = self._get_api_key()
        base_url = self._get_base_url()

        llm_params = {"api_key": api_key}
        if base_url:
            llm_params["base_url"] = base_url

        # Recreate LLM objects with explicit API key and config values
        self.agent_llm = ChatOpenAI(
            model=self.config.get("agent_llm_model", "gpt-4o-mini"),
            temperature=self.config.get("agent_llm_temperature", 0.1),
            **llm_params,
        )
        self.graph_llm = ChatOpenAI(
            model=self.config.get("graph_llm_model", "gpt-4o"),
            temperature=self.config.get("graph_llm_temperature", 0.1),
            **llm_params,
        )

        # Recreate the graph setup with new LLMs
        self.graph_setup = SetGraph(
            self.agent_llm,
            self.graph_llm,
            self.toolkit,
            self.tool_nodes,
        )

        # Recreate the main graph
        self.graph = self.graph_setup.set_graph()
