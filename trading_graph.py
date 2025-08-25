"""
TradingGraph: Orchestrates the multi-agent trading system using LangChain and LangGraph.
Initializes LLMs, toolkits, and agent nodes for indicator, pattern, and trend analysis.
"""
from typing import Dict
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from default_config import DEFAULT_CONFIG
from graph_util import TechnicalTools
from graph_setup import SetGraph

class TradingGraph:
    """
    Main orchestrator for the multi-agent trading system.
    Sets up LLMs, toolkits, and agent nodes for indicator, pattern, and trend analysis.
    """
    def __init__(self, config=None):
        # --- Configuration and LLMs ---
        self.config = config if config is not None else DEFAULT_CONFIG.copy()
        
        # Initialize LLMs with config values
        self.agent_llm = ChatOpenAI(
            model=self.config.get("agent_llm_model", "gpt-4o-mini"),
            temperature=self.config.get("agent_llm_temperature", 0.1)
        )
        self.graph_llm = ChatOpenAI(
            model=self.config.get("graph_llm_model", "gpt-4o"),
            temperature=self.config.get("graph_llm_temperature", 0.1)
        )
        self.toolkit = TechnicalTools()

        # --- Create tool nodes for each agent ---
        self.tool_nodes = self._set_tool_nodes()

        # --- Graph logic and setup ---
        self.graph_setup = SetGraph(
            self.agent_llm,
            self.graph_llm,
            self.toolkit,
            self.tool_nodes,
        )
        
        # --- The main LangGraph graph object ---
        self.graph = self.graph_setup.set_graph()
    
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
            "trend": ToolNode(
                [
                    self.toolkit.generate_trend_image
                ]
            )
        }
    
    def refresh_llms(self):
        """
        Refresh the LLM objects with the current API key from environment.
        This is called when the API key is updated.
        """
        # Recreate LLM objects with current environment API key and config values
        self.agent_llm = ChatOpenAI(
            model=self.config.get("agent_llm_model", "gpt-4o-mini"),
            temperature=self.config.get("agent_llm_temperature", 0.1)
        )
        self.graph_llm = ChatOpenAI(
            model=self.config.get("graph_llm_model", "gpt-4o"),
            temperature=self.config.get("graph_llm_temperature", 0.1)
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