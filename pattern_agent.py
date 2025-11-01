# -*- coding: utf-8 -*-
"""
用于K线形态识别的代理模块。

该代理负责分析K线图，识别经典的技术分析形态，并生成分析报告。
"""

import copy
import json
import time

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from openai import RateLimitError


def invoke_tool_with_retry(tool_fn, tool_args, retries=3, wait_sec=4):
    """
    带重试机制的工具调用函数。

    如果工具未能返回图像，将进行重试。

    Args:
        tool_fn: 要调用的工具函数。
        tool_args: 工具函数的参数。
        retries (int): 最大重试次数。
        wait_sec (int): 每次重试前的等待秒数。

    Returns:
        dict: 工具函数的返回结果。

    Raises:
        RuntimeError: 在多次重试后仍未能生成图像时抛出。
    """
    for attempt in range(retries):
        result = tool_fn.invoke(tool_args)
        img_b64 = result.get("pattern_image")
        if img_b64:
            return result
        print(
            f"工具未返回图像，将在 {wait_sec} 秒后重试（第 {attempt + 1}/{retries} 次尝试）..."
        )
        time.sleep(wait_sec)
    raise RuntimeError("工具在多次重试后未能生成图像")


def create_pattern_agent(tool_llm, graph_llm, toolkit):
    """
    创建一个用于K线形态识别的代理节点。

    该代理首先检查状态中是否存在预先计算的图像。如果不存在，则使用工具生成图像。
    然后，它使用视觉分析模型来识别图像中的经典技术分析形态。

    Args:
        tool_llm: 用于工具调用决策的大语言模型。
        graph_llm: 用于视觉分析和最终报告生成的大语言模型。
        toolkit: 包含`generate_kline_image`等工具的工具包。

    Returns:
        一个可执行的形态识别代理节点函数。
    """

    def pattern_agent_node(state):
        """
        执行形态识别的核心逻辑节点。

        此函数按以下步骤操作：
        1. 检查状态中是否存在`pattern_image`。
        2. 如果图像不存在，则调用`generate_kline_image`工具生成K线图。
        3. 如果图像存在（无论是预计算的还是新生成的），则使用视觉模型进行分析。
        4. LLM将图像与预定义的经典形态列表进行比较，并生成一份详细的分析报告。

        Args:
            state (dict): 当前代理状态，包含`messages`、`kline_data`等。

        Returns:
            dict: 更新后的状态字典，包含`pattern_report`和更新后的`messages`。
        """
        tools = [toolkit.generate_kline_image]
        time_frame = state["time_frame"]
        pattern_text = """
        请参考以下经典的K线形态：

        1.  反转头肩形（Inverse Head and Shoulders）：三个低谷，中间最低，形态对称，通常预示上升趋势。
        2.  双重底（Double Bottom）：两个相似的低点，中间有反弹，形成'W'形。
        3.  圆形底（Rounded Bottom）：价格逐渐下跌后逐渐回升，形成'U'形。
        4.  隐藏基地（Hidden Base）：横盘整理后突然向上突破。
        5.  下降楔形（Falling Wedge）：价格向下收窄，通常向上突破。
        6.  上升楔形（Rising Wedge）：价格缓慢上升但收敛，常向下突破。
        7.  上升三角形（Ascending Triangle）：支撑线上升，顶部阻力平坦，常向上突破。
        8.  下降三角形（Descending Triangle）：阻力线下降，底部支撑平坦，通常向下突破。
        9.  看涨旗形（Bullish Flag）：急剧上涨后短暂向下盘整，然后继续上涨。
        10. 看跌旗形（Bearish Flag）：急剧下跌后短暂向上盘整，然后继续下跌。
        11. 矩形（Rectangle）：价格在水平支撑和阻力之间波动。
        12. 岛形反转（Island Reversal）：两个方向相反的价格缺口形成孤立的价格岛屿。
        13. V形反转（V-shaped Reversal）：急剧下跌后迅速回升，反之亦然。
        14. 圆形顶/底（Rounded Top / Rounded Bottom）：逐渐见顶或见底，形成弧形形态。
        15. 扩展三角形（Expanding Triangle）：高点和低点越来越宽，表明波动剧烈。
        16. 对称三角形（Symmetrical Triangle）：高点和低点向顶点收敛，通常随后会突破。
        """

        pattern_image_b64 = state.get("pattern_image")

        def invoke_with_retry(call_fn, *args, retries=3, wait_sec=8):
            for attempt in range(retries):
                try:
                    return call_fn(*args)
                except RateLimitError:
                    print(
                        f"达到速率限制，将在 {wait_sec} 秒后重试（第 {attempt + 1}/{retries} 次尝试）..."
                    )
                    time.sleep(wait_sec)
                except Exception as e:
                    print(
                        f"其他错误: {e}, 将在 {wait_sec} 秒后重试（第 {attempt + 1}/{retries} 次尝试）..."
                    )
                    time.sleep(wait_sec)
            raise RuntimeError("超过最大重试次数")

        messages = state.get("messages", [])

        if not pattern_image_b64:
            print("在状态中未找到预计算的形态图像，使用工具生成...")

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "你是一名交易形态识别助理，任务是识别经典的高频交易形态。"
                        "你可以使用工具：generate_kline_image。"
                        "通过提供`kline_data`等适当参数来使用它。\n\n"
                        "图表生成后，将其与经典形态描述进行比较，并确定是否存在任何已知形态。",
                    ),
                    MessagesPlaceholder(variable_name="messages"),
                ]
            ).partial(kline_data=json.dumps(state["kline_data"], indent=2))

            chain = prompt | tool_llm.bind_tools(tools)
            ai_response = invoke_with_retry(chain.invoke, messages)
            messages.append(ai_response)

            if hasattr(ai_response, "tool_calls"):
                for call in ai_response.tool_calls:
                    tool_name = call["name"]
                    tool_args = call["args"]
                    tool_args["kline_data"] = copy.deepcopy(state["kline_data"])
                    tool_fn = next(t for t in tools if t.name == tool_name)
                    tool_result = invoke_tool_with_retry(tool_fn, tool_args)
                    pattern_image_b64 = tool_result.get("pattern_image")
                    messages.append(
                        ToolMessage(
                            tool_call_id=call["id"], content=json.dumps(tool_result)
                        )
                    )
        else:
            print("使用状态中预计算的形态图像")

        if pattern_image_b64:
            image_prompt = [
                {
                    "type": "text",
                    "text": (
                        f"这是一张根据近期OHLC市场数据生成的 {time_frame} K线图。\n\n"
                        f"{pattern_text}\n\n"
                        "判断该图表是否与所列出的任何形态匹配。"
                        "请明确指出匹配的形态名称，并根据结构、趋势和对称性解释你的理由。"
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{pattern_image_b64}"},
                },
            ]

            final_response = invoke_with_retry(
                graph_llm.invoke,
                [
                    SystemMessage(content="你是一名负责分析K线图的交易形态识别助理。"),
                    HumanMessage(content=image_prompt),
                ],
            )
        else:
            final_response = invoke_with_retry(chain.invoke, messages)

        return {
            "messages": messages + [final_response],
            "pattern_report": final_response.content,
        }

    return pattern_agent_node
