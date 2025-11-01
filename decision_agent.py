# -*- coding: utf-8 -*-
"""
用于在高频交易（HFT）环境中做出最终交易决策的代理。
该代理结合指标、模式和趋势报告，发布LONG（做多）或SHORT（做空）订单。
"""


def create_final_trade_decider(llm):
    """
    创建一个交易决策代理节点。

    该代理使用大语言模型（LLM）综合分析指标、模式和趋势报告，
    并输出最终的交易决策（LONG或SHORT），包括决策理由和风险回报率。

    Args:
        llm: 用于生成决策的大语言模型实例。

    Returns:
        一个可执行的交易决策节点函数。
    """

    def trade_decision_node(state) -> dict:
        """
        根据当前状态生成最终交易决策。

        Args:
            state (dict): 当前代理状态，包含以下键：
                - indicator_report (str): 技术指标分析报告。
                - pattern_report (str): 图表模式分析报告。
                - trend_report (str): 市场趋势分析报告。
                - time_frame (str): 当前K线图的时间周期。
                - stock_name (str): 正在分析的股票名称。

        Returns:
            dict: 一个包含最终交易决策和相关信息的字典，格式如下：
                {
                    "final_trade_decision": str,  # LLM生成的最终决策内容
                    "messages": list,             # LLM的响应消息列表
                    "decision_prompt": str,       # 用于生成决策的完整提示
                }
        """
        indicator_report = state["indicator_report"]
        pattern_report = state["pattern_report"]
        trend_report = state["trend_report"]
        time_frame = state["time_frame"]
        stock_name = state["stock_name"]

        # --- 为LLM设计的系统提示 ---
        prompt = f"""你是一名高频量化交易（HFT）分析师，正在为 {stock_name} 的当前 {time_frame} K线图进行分析。你的任务是发布一个**立即执行的订单**：**LONG** 或 **SHORT**。⚠️ 由于高频交易的限制，禁止使用HOLD（持有）指令。

            你的决策应预测未来 **N根K线** 的市场走势，其中：
            - 例如：TIME_FRAME = 15分钟，N = 1 → 预测未来15分钟。
            - TIME_FRAME = 4小时，N = 1 → 预测未来4小时。

            你的决策必须基于以下三份报告的综合强度、一致性和时机：

            ---

            ### 1. 技术指标报告:
            - 评估动量指标（如MACD、ROC）和振荡器（如RSI、随机指标、威廉姆斯%R）。
            - **优先考虑强烈的方向性信号**，如MACD金叉/死叉、RSI背离、极端超买/超卖水平。
            - **忽略或降低中性或混合信号的权重**，除非多个指标信号一致。

            ---

            ### 2. 形态报告:
            - 仅在以下情况下根据看涨或看跌形态行动：
            - 形态**清晰可辨且基本完成**，并且
            - 根据价格和动量（如长影线、成交量激增、吞没形态），**突破或跌破已经发生**或极有可能发生。
            - **不要**基于早期或投机性形态行动。不要将盘整形态视为可交易机会，除非有其他报告的**突破确认**。

            ---

            ### 3. 趋势报告:
            - 分析价格与支撑位和阻力位的相互作用：
            - **向上倾斜的支撑线**表明买方兴趣。
            - **向下倾斜的阻力线**表明卖方压力。
            - 如果价格在趋势线之间压缩：
            - **仅在有强劲K线或指标确认的共识时**预测突破。
            - **不要**仅凭几何形状猜测突破方向。

            ---

            ### ✅ 决策策略

            1. 只对**已确认**的信号采取行动——避免新兴、投机或冲突的信号。
            2. 优先处理**三份报告（指标、形态和趋势）方向一致**的决策。
            3. 给予更高权重：
            - 近期的强劲动量（如MACD金叉、RSI突破）
            - 决定性的价格行为（如突破K线、拒绝长影线、支撑位反弹）
            4. 如果报告不一致：
            - 选择具有**更强和更近期确认**的方向。
            - 倾向于**有动量支持的信号**，而不是弱振荡器信号。
            5. ⚖️ 如果市场处于盘整或报告混合：
            - 默认遵循**主趋势线的斜率**（例如，在下降通道中选择SHORT）。
            - 不要猜测方向——选择**更具防御性**的一方。
            6. 根据当前波动性和趋势强度，建议一个介于**1.2至1.8之间**的合理**风险回报比**。

            ---
            ### 🧠 输出格式（JSON格式，供系统解析）:

            ```
            {{
            "forecast_horizon": "预测未来N根K线（例如：15分钟、1小时等）",
            "decision": "<LONG 或 SHORT>",
            "justification": "<基于报告的简洁、已确认的推理>",
            "risk_reward_ratio": "<介于1.2和1.8之间的浮点数>",
            }}

            --------
            **技术指标报告**
            {indicator_report}

            **形态报告**
            {pattern_report}

            **趋势报告**
            {trend_report}

        """

        # --- 调用LLM进行决策 ---
        response = llm.invoke(prompt)

        return {
            "final_trade_decision": response.content,
            "messages": [response],
            "decision_prompt": prompt,
        }

    return trade_decision_node
