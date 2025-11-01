# -*- coding: utf-8 -*-
"""
该模块负责构建和连接多智能体图（Graph）。
"""

from typing import Dict

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from agent_state import IndicatorAgentState
from decision_agent import create_final_trade_decider
from graph_util import TechnicalTools
from indicator_agent import create_indicator_agent
from pattern_agent import create_pattern_agent
from trend_agent import create_trend_agent


class SetGraph:
    """
    设置和构建多智能体交易分析图的类。

    该类负责初始化所有必要的代理节点、工具节点，并将它们连接起来，
    形成一个有序的、可执行的分析流程。
    """

    def __init__(
        self,
        agent_llm: ChatOpenAI,
        graph_llm: ChatOpenAI,
        toolkit: TechnicalTools,
        tool_nodes: Dict[str, ToolNode],
    ):
        """
        初始化SetGraph类。

        Args:
            agent_llm (ChatOpenAI): 用于单个分析代理（如模式、趋势）的大语言模型。
            graph_llm (ChatOpenAI): 用于图逻辑和最终决策代理的大语言模型。
            toolkit (TechnicalTools): 包含技术分析工具的工具包。
            tool_nodes (Dict[str, ToolNode]): 包含为每个代理定义的工具节点的字典。
        """
        self.agent_llm = agent_llm
        self.graph_llm = graph_llm
        self.toolkit = toolkit
        self.tool_nodes = tool_nodes

    def set_graph(self):
        """
        构建并编译交易分析图。

        该方法执行以下操作：
        1. 创建指标、模式和趋势分析代理节点。
        2. 创建与这些代理关联的工具节点。
        3. 创建最终的交易决策代理节点。
        4. 将所有节点添加到StateGraph中。
        5. 定义节点之间的执行流程（边），从指标代理开始，依次经过模式和趋势代理，
           最后由决策者输出结果。
        6. 编译图并返回可执行实例。

        Returns:
            CompiledGraph: 一个编译完成、可执行的LangGraph实例。
        """
        # 创建分析师节点
        agent_nodes = {}
        tool_nodes = {}
        all_agents = ["indicator", "pattern", "trend"]

        # 创建指标代理节点
        agent_nodes["indicator"] = create_indicator_agent(self.graph_llm, self.toolkit)
        tool_nodes["indicator"] = self.tool_nodes["indicator"]

        # 创建模式代理节点
        agent_nodes["pattern"] = create_pattern_agent(
            self.agent_llm, self.graph_llm, self.toolkit
        )
        tool_nodes["pattern"] = self.tool_nodes["pattern"]

        # 创建趋势代理节点
        agent_nodes["trend"] = create_trend_agent(
            self.agent_llm, self.graph_llm, self.toolkit
        )
        tool_nodes["trend"] = self.tool_nodes["trend"]

        # 创建决策代理节点
        decision_agent_node = create_final_trade_decider(self.graph_llm)

        # 创建图
        graph = StateGraph(IndicatorAgentState)

        # 将代理节点及其关联的工具节点添加到图中
        for agent_type, cur_node in agent_nodes.items():
            graph.add_node(f"{agent_type.capitalize()} Agent", cur_node)
            graph.add_node(f"{agent_type}_tools", tool_nodes[agent_type])

        # 添加其余节点
        graph.add_node("Decision Maker", decision_agent_node)

        # 设置图的起点
        graph.add_edge(START, "Indicator Agent")

        # 添加图的边
        for i, agent_type in enumerate(all_agents):
            current_agent = f"{agent_type.capitalize()} Agent"

            if i == len(all_agents) - 1:
                # 最后一个代理连接到决策者
                graph.add_edge(current_agent, "Decision Maker")
            else:
                # 连接到下一个代理
                next_agent = f"{all_agents[i + 1].capitalize()} Agent"
                graph.add_edge(current_agent, next_agent)

        # 决策者流程
        graph.add_edge("Decision Maker", END)

        # 编译并返回图
        return graph.compile()
