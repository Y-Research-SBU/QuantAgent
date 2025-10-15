import os
import random
from typing import Any, Dict, List, TypedDict

import pandas as pd
from IPython.display import Image, display
from langchain.chat_models import init_chat_model
from langchain_core.messages import AnyMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
# from langchain_community.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState

import default_config
from agent_state import IndicatorAgentState
from decision_agent import *
from graph_util import *
from graph_util import TechnicalTools
from indicator_agent import *
from pattern_agent import *
from trend_agent import *


class SetGraph:
    def __init__(
        self,
        agent_llm: ChatOpenAI,
        graph_llm: ChatOpenAI,
        toolkit: TechnicalTools,
        tool_nodes: Dict[str, ToolNode],
    ):
        self.agent_llm = agent_llm
        self.graph_llm = graph_llm
        self.toolkit = toolkit
        self.tool_nodes = tool_nodes

    def set_graph(self):
        # Create analyst nodes
        agent_nodes = {}
        tool_nodes = {}
        all_agents = ["indicator", "pattern", "trend"]

        # create nodes for indicator agent
        agent_nodes["indicator"] = create_indicator_agent(self.graph_llm, self.toolkit)
        tool_nodes["indicator"] = self.tool_nodes["indicator"]

        # create nodes for pattern agent
        agent_nodes["pattern"] = create_pattern_agent(
            self.agent_llm, self.graph_llm, self.toolkit
        )
        tool_nodes["pattern"] = self.tool_nodes["pattern"]

        # create nodes for trend agent
        agent_nodes["trend"] = create_trend_agent(
            self.agent_llm, self.graph_llm, self.toolkit
        )
        tool_nodes["trend"] = self.tool_nodes["trend"]

        # create nodes for decision agent
        # decision_agent_node = create_final_trade_decider(self.agent_llm)
        decision_agent_node = create_final_trade_decider(self.graph_llm)

        # create graph
        graph = StateGraph(IndicatorAgentState)

        # add agent nodes and associated tool nodes to graph
        for agent_type, cur_node in agent_nodes.items():
            graph.add_node(f"{agent_type.capitalize()} Agent", cur_node)
            graph.add_node(f"{agent_type}_tools", tool_nodes[agent_type])

        # add rest of the nodes
        graph.add_node("Decision Maker", decision_agent_node)

        # set start of graph
        graph.add_edge(START, "Indicator Agent")

        # add edges to graph
        for i, agent_type in enumerate(all_agents):
            current_agent = f"{agent_type.capitalize()} Agent"
            current_tools = f"{agent_type}_tools"

            if i == len(all_agents) - 1:
                graph.add_edge(current_agent, "Decision Maker")
            else:

                next_agent = f"{all_agents[i + 1].capitalize()} Agent"
                graph.add_edge(current_agent, next_agent)

        # Decision Maker Process
        graph.add_edge("Decision Maker", END)

        return graph.compile()
