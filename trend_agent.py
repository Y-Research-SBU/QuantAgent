# -*- coding: utf-8 -*-
"""
用于高频交易（HFT）环境中的趋势分析代理。
该代理使用大语言模型（LLM）和工具包生成并解释带趋势线的图表，以进行短期预测。
"""

import json
import time
import copy

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from openai import RateLimitError


def invoke_with_retry(call_fn, *args, retries=3, wait_sec=4):
    """
    带重试机制的函数调用，用于处理速率限制或其他错误。

    Args:
        call_fn: 要调用的函数。
        *args: 传递给函数的参数。
        retries (int): 最大重试次数。
        wait_sec (int): 每次重试前的等待秒数。

    Returns:
        函数的返回结果。

    Raises:
        RuntimeError: 在多次重试后仍失败时抛出。
    """
    for attempt in range(retries):
        try:
            result = call_fn(*args)
            return result
        except RateLimitError:
            print(
                f"达到速率限制，将在 {wait_sec} 秒后重试（第 {attempt + 1}/{retries} 次尝试）..."
            )
        except Exception as e:
            print(
                f"其他错误: {e}, 将在 {wait_sec} 秒后重试（第 {attempt + 1}/{retries} 次尝试）..."
            )
        if attempt < retries - 1:
            time.sleep(wait_sec)
    raise RuntimeError("超过最大重试次数")


def create_trend_agent(tool_llm, graph_llm, toolkit):
    """
    创建一个用于高频交易的趋势分析代理节点。

    该代理首先检查状态中是否存在预计算的趋势图像。如果不存在，则调用工具生成图像。
    然后，它使用视觉分析模型解释带趋势线的K线图，并生成趋势分析报告。

    Args:
        tool_llm: 用于工具调用决策的大语言模型。
        graph_llm: 用于视觉分析和最终报告生成的大语言模型。
        toolkit: 包含`generate_trend_image`等工具的工具包。

    Returns:
        一个可执行的趋势分析代理节点函数。
    """

    def trend_agent_node(state):
        """
        执行趋势分析的核心逻辑节点。

        此函数按以下步骤操作：
        1. 检查状态中是否存在`trend_image`。
        2. 如果图像不存在，则调用`generate_trend_image`工具生成带趋势线的K线图。
        3. 如果图像存在，则使用视觉模型进行分析，解读支撑/阻力线和价格行为。
        4. LLM根据图表生成一份关于短期趋势（上升、下降或横盘）的预测报告。

        Args:
            state (dict): 当前代理状态，包含`messages`、`kline_data`等。

        Returns:
            dict: 更新后的状态字典，包含`trend_report`、趋势图像信息和更新后的`messages`。
        """
        tools = [toolkit.generate_trend_image]
        time_frame = state["time_frame"]
        trend_image_b64 = state.get("trend_image")
        messages = []

        if not trend_image_b64:
            print("在状态中未找到预计算的趋势图像，使用工具生成...")

            system_prompt = (
                "你是一名在高频交易环境中工作的K线趋势形态识别助理。"
                "你必须首先使用提供的`kline_data`调用`generate_trend_image`工具。"
                "图表生成后，分析图像中的支撑/阻力趋势线和已知的K线形态。"
                "只有在生成并分析图像后，才能对短期趋势（上升、下降或横盘）进行预测。"
                "在生成和分析图像之前，不要做出任何预测。"
            )

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(
                    content=f"这是最近的K线数据：\n{json.dumps(state['kline_data'], indent=2)}"
                ),
            ]

            chain = tool_llm.bind_tools(tools)
            ai_response = invoke_with_retry(chain.invoke, messages)
            messages.append(ai_response)

            if hasattr(ai_response, "tool_calls"):
                for call in ai_response.tool_calls:
                    tool_name = call["name"]
                    tool_args = call["args"]
                    tool_args["kline_data"] = copy.deepcopy(state["kline_data"])
                    tool_fn = next(t for t in tools if t.name == tool_name)
                    tool_result = tool_fn.invoke(tool_args)
                    trend_image_b64 = tool_result.get("trend_image")
                    messages.append(
                        ToolMessage(
                            tool_call_id=call["id"], content=json.dumps(tool_result)
                        )
                    )
        else:
            print("使用状态中预计算的趋势图像")

        if trend_image_b64:
            image_prompt = [
                {
                    "type": "text",
                    "text": (
                        f"这张K线图（{time_frame}周期）包含了自动生成的趋势线：**蓝线**是支撑线，**红线**是阻力线，两者均根据近期收盘价计算得出。\n\n"
                        "请分析价格与这些线的相互作用——K线是在线上反弹、突破，还是在两者之间压缩？\n\n"
                        "根据趋势线的斜率、间距和近期的K线行为，预测可能的短期趋势：**上升**、**下降**或**横盘**。"
                        "请从预测、推理和信号三个方面支持你的预测。"
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{trend_image_b64}"},
                },
            ]

            final_response = invoke_with_retry(
                graph_llm.invoke,
                [
                    SystemMessage(
                        content="你是一名在高频交易环境中工作的K线趋势形态识别助理。"
                        "你的任务是分析带有支撑和阻力趋势线的K线图。"
                    ),
                    HumanMessage(content=image_prompt),
                ],
            )
        else:
            final_response = invoke_with_retry(chain.invoke, messages)

        return {
            "messages": messages + [final_response],
            "trend_report": final_response.content,
            "trend_image": trend_image_b64,
            "trend_image_filename": "trend_graph.png",
            "trend_image_description": (
                "带支撑/阻力线的趋势增强K线图"
                if trend_image_b64
                else None
            ),
        }

    return trend_agent_node
