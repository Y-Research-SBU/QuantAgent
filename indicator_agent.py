# -*- coding: utf-8 -*-
"""
用于高频交易（HFT）环境中的技术指标分析代理。
该代理使用大语言模型（LLM）和工具包来计算和解释MACD、RSI、ROC、随机振荡器和威廉姆斯%R等指标。
"""

import copy
import json

from langchain_core.messages import ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def create_indicator_agent(llm, toolkit):
    """
    为高频交易（HFT）创建一个指标分析代理节点。

    该代理利用大语言模型（LLM）和一组专门的技术指标工具来分析OHLCV（开盘价、最高价、最低价、收盘价、成交量）数据。
    它的主要职责是调用工具计算关键指标，并根据这些指标生成一份综合分析报告。

    Args:
        llm: 用于驱动代理决策的大语言模型实例。
        toolkit: 包含技术指标计算工具（如compute_macd, compute_rsi等）的工具包。

    Returns:
        一个可执行的指标代理节点函数。
    """

    def indicator_agent_node(state):
        """
        执行指标分析的核心逻辑节点。

        此函数按以下步骤操作：
        1. 定义并绑定可用的技术指标工具。
        2. 构建一个系统提示，指示LLM扮演HFT分析师的角色，并使用提供的工具分析K线数据。
        3. 第一次调用LLM，生成工具调用请求。
        4. 执行工具调用，并将结果作为ToolMessage附加到消息历史中。
        5. 第二次调用LLM，此时LLM接收到工具调用的结果，并生成最终的分析报告。

        Args:
            state (dict): 当前代理状态，必须包含以下键：
                - messages (list): 聊天消息历史。
                - kline_data (dict): OHLCV格式的K线数据。
                - time_frame (str): K线数据的时间周期。

        Returns:
            dict: 一个更新后的状态字典，包含：
                - messages (list): 更新后的消息历史，包括最终的AI响应。
                - indicator_report (str): 由LLM生成的最终技术指标分析报告。
        """
        # --- 工具定义 ---
        tools = [
            toolkit.compute_macd,
            toolkit.compute_rsi,
            toolkit.compute_roc,
            toolkit.compute_stoch,
            toolkit.compute_willr,
        ]
        time_frame = state["time_frame"]
        # --- 为LLM设计的系统提示 ---
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是一名在时间敏感条件下操作的高频交易（HFT）分析助理。"
                    "你必须分析技术指标以支持快节奏的交易执行。\n\n"
                    "你可以使用以下工具：compute_rsi, compute_macd, compute_roc, compute_stoch, 和 compute_willr。"
                    "通过提供适当的参数（如 `kline_data` 和相应的时间周期）来使用它们。\n\n"
                    f"⚠️ 提供的OHLC数据来自 {time_frame} 时间间隔，反映了近期的市场行为。"
                    "你必须快速准确地解释这些数据。\n\n"
                    "这是OHLC数据：\n{kline_data}。\n\n"
                    "调用必要的工具，并分析结果。\n",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        ).partial(kline_data=json.dumps(state["kline_data"], indent=2))

        chain = prompt | llm.bind_tools(tools)
        messages = state["messages"]

        # --- 步骤1：请求工具调用 ---
        ai_response = chain.invoke(messages)
        messages.append(ai_response)

        # --- 步骤2：收集工具结果 ---
        if hasattr(ai_response, "tool_calls"):
            for call in ai_response.tool_calls:
                tool_name = call["name"]
                tool_args = call["args"]
                # 始终提供kline_data
                tool_args["kline_data"] = copy.deepcopy(state["kline_data"])
                # 按名称查找工具
                tool_fn = next(t for t in tools if t.name == tool_name)
                tool_result = tool_fn.invoke(tool_args)
                # 将结果附加为ToolMessage
                messages.append(
                    ToolMessage(
                        tool_call_id=call["id"], content=json.dumps(tool_result)
                    )
                )

        # --- 步骤3：使用工具结果再次运行链 ---
        final_response = chain.invoke(messages)

        return {
            "messages": messages + [final_response],
            "indicator_report": final_response.content,
        }

    return indicator_agent_node
