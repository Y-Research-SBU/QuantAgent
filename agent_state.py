# -*- coding: utf-8 -*-
from typing import Annotated, List, TypedDict

from langchain_core.messages import BaseMessage


class IndicatorAgentState(TypedDict):
    """
    用于表示AI代理状态的类型字典。

    Attributes:
        kline_data (dict): 用于计算技术指标的OHLCV（开盘价、最高价、最低价、收盘价、成交量）数据字典。
        time_frame (str): K线数据的时间周期。
        stock_name (str): 用于生成提示的股票名称。
        rsi (List[float]): 相对强弱指数（RSI）的值列表。
        macd (List[float]): MACD指标线的值列表。
        macd_signal (List[float]): MACD信号线的值列表。
        macd_hist (List[float]): MACD柱状图的值列表。
        stoch_k (List[float]): 随机振荡器（Stochastic Oscillator）的%K值列表。
        stoch_d (List[float]): 随机振荡器（Stochastic Oscillator）的%D值列表。
        roc (List[float]): 变动率指标（ROC）的值列表。
        willr (List[float]): 威廉姆斯百分比范围（Williams %R）的值列表。
        indicator_report (str): 指标代理生成的最终摘要报告，供下游代理使用。
        pattern_image (str): 用于模式识别代理的Base64编码的K线图。
        pattern_image_filename (str): 保存的K线图图像的本地文件路径。
        pattern_image_description (str): 生成的K线图的简要描述。
        pattern_report (str): 模式代理生成的最终摘要报告，供下游代理使用。
        trend_image (str): 用于趋势识别代理的带趋势注释的K线图（Base64编码）。
        trend_image_filename (str): 保存的带趋势线增强的K线图图像的本地文件路径。
        trend_image_description (str): 图表的简要描述，包括支撑/阻力线的存在和视觉特征。
        trend_report (str): 最终的趋势分析摘要，描述结构、方向偏见和技术观察，供下游代理使用。
        analysis_results (str): 分析或决策的计算结果。
        messages (List[BaseMessage]): 用于构建LLM提示的聊天消息列表。
        decision_prompt (str): 用于反思的决策提示。
        final_trade_decision (str): 在分析指标后做出的最终买入或卖出决策。
    """

    kline_data: Annotated[
        dict, "用于计算技术指标的OHLCV字典"
    ]
    time_frame: Annotated[str, "提供的K线数据的时间周期"]
    stock_name: Annotated[dict, "用于提示的股票名称"]

    # 指标代理工具输出值（每个指标明确添加）
    rsi: Annotated[List[float], "相对强弱指数（RSI）值"]
    macd: Annotated[List[float], "MACD线值"]
    macd_signal: Annotated[List[float], "MACD信号线值"]
    macd_hist: Annotated[List[float], "MACD柱状图值"]
    stoch_k: Annotated[List[float], "随机振荡器%K值"]
    stoch_d: Annotated[List[float], "随机振荡器%D值"]
    roc: Annotated[List[float], "变动率（ROC）值"]
    willr: Annotated[List[float], "威廉姆斯%R值"]
    indicator_report: Annotated[
        str, "供下游代理使用的最终指标代理摘要报告"
    ]

    # 模式代理
    pattern_image: Annotated[
        str, "供模式识别代理使用的Base64编码的K线图"
    ]
    pattern_image_filename: Annotated[
        str, "保存的K线图图像的本地文件路径"
    ]
    pattern_image_description: Annotated[
        str, "生成的K线图像的简要描述"
    ]
    pattern_report: Annotated[
        str, "供下游代理使用的最终模式代理摘要报告"
    ]

    # 趋势代理
    trend_image: Annotated[
        str,
        "供趋势识别代理使用的带趋势注释的K线图（Base64编码）",
    ]
    trend_image_filename: Annotated[
        str, "保存的带趋势线增强的K线图图像的本地文件路径"
    ]
    trend_image_description: Annotated[
        str,
        "图表的简要描述，包括支撑/阻力线的存在和视觉特征",
    ]
    trend_report: Annotated[
        str,
        "最终趋势分析摘要，描述结构、方向偏见和技术观察，供下游代理使用",
    ]

    # 最终分析和消息传递上下文
    analysis_results: Annotated[str, "分析或决策的计算结果"]
    messages: Annotated[
        List[BaseMessage], "用于构建LLM提示的聊天消息列表"
    ]
    decision_prompt: Annotated[str, "用于反思的决策提示"]
    final_trade_decision: Annotated[
        str, "分析指标后做出的最终买入或卖出决策"
    ]
