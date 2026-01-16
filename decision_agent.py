"""
Agent for final trading decision synthesis in high-frequency trading (HFT) context.
Combines indicator, pattern, and trend analysis to make actionable trading recommendations.
"""
from langchain_core.prompts import ChatPromptTemplate
import json

def create_decision_agent(llm, tools):
    """
    Create a decision synthesis agent node for HFT. The agent combines all analysis results to make final trading decisions.
    """
    def decision_agent_node(state):
        time_frame = state['time_frame']
        stock_name = state['stock_name']
        
        # 获取各个分析结果
        indicator_report = state.get("indicator_report", "No indicator analysis available")
        pattern_report = state.get("pattern_report", "No pattern analysis available")
        trend_report = state.get("trend_report", "No trend analysis available")
        
        # --- 根据交易策略调整提示词 ---
        trading_strategy = state.get('trading_strategy', 'high_frequency')
        
        if trading_strategy == 'low_frequency':
            # 低频交易策略提示词
            system_prompt = (
                "你是一位资深的低频交易决策专家，持有周期以月为单位，最长可达半年。"
                "基于以下综合分析报告，做出最终的交易决策。请用中文回答。\n\n"
                "股票代码: {stock_name}\n"
                "时间周期: {time_frame}\n\n"
                "技术指标分析:\n{indicator_report}\n\n"
                "形态分析:\n{pattern_report}\n\n"
                "趋势分析:\n{trend_report}\n\n"
                "请按照以下JSON格式提供你的最终决策（用中文填写）:\n"
                "{{\n"
                '  "decision": "买入/卖出/持有",\n'
                '  "confidence": "高/中/低",\n'
                '  "risk_reward_ratio": "X:Y",\n'
                '  "forecast_horizon": "1-6个月",\n'
                '  "justification": "详细的中文理由说明，重点关注长期趋势和基本面因素"\n'
                "}}\n\n"
                "请综合考虑所有三种分析类型，为低频交易提供可操作的中文见解，重点关注长期趋势和基本面因素。"
            )
        else:
            # 高频交易策略提示词
            system_prompt = (
                "你是一位资深的高频交易决策专家，最短持有2天，最长持有1个月。"
                "基于以下综合分析报告，做出最终的交易决策。请用中文回答。\n\n"
                "股票代码: {stock_name}\n"
                "时间周期: {time_frame}\n\n"
                "技术指标分析:\n{indicator_report}\n\n"
                "形态分析:\n{pattern_report}\n\n"
                "趋势分析:\n{trend_report}\n\n"
                "请按照以下JSON格式提供你的最终决策（用中文填写）:\n"
                "{{\n"
                '  "decision": "买入/卖出/持有",\n'
                '  "confidence": "高/中/低",\n'
                '  "risk_reward_ratio": "X:Y",\n'
                '  "forecast_horizon": "预测时间段",\n'
                '  "justification": "详细的中文理由说明"\n'
                "}}\n\n"
                "请综合考虑所有三种分析类型，为高频交易提供可操作的中文见解。"
            )
            
        # 创建提示词模板
        decision_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                system_prompt
            )
        ])
        
        try:
            final_response = (decision_prompt | llm).invoke({
                "stock_name": stock_name,
                "time_frame": time_frame,
                "indicator_report": indicator_report,
                "pattern_report": pattern_report,
                "trend_report": trend_report
            })
            
            decision_content = final_response.content if hasattr(final_response, 'content') else str(final_response)
            
        except Exception as e:
            # 更健壮的错误处理
            try:
                error_msg = str(e)
                if isinstance(error_msg, bytes):
                    error_msg = error_msg.decode('utf-8', errors='replace')
                else:
                    error_msg = error_msg.encode('utf-8', errors='replace').decode('utf-8')
            except:
                error_msg = "Unknown encoding error"
                
            decision_content = json.dumps({
                "decision": "HOLD",
                "confidence": "LOW", 
                "risk_reward_ratio": "1:1",
                "forecast_horizon": "Unknown",
                "justification": f"Error generating decision: {error_msg}"
            }, indent=2, ensure_ascii=False)

        # 更新state并返回
        state.update({
            "messages": state.get("messages", []),
            "final_trade_decision": decision_content,
        })
        
        return state

    return decision_agent_node
