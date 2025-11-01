# -*- coding: utf-8 -*-
"""
基于Flask的Web界面，用于与多智能体交易分析系统进行交互。

该模块提供了以下功能：
- 实时市场数据获取（通过Yahoo Finance）。
- 交互式资产和时间周期选择。
- 动态图表生成和分析。
- API密钥管理。
- 自定义资产的持久化存储。
"""
import json
import os
import re
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import yfinance as yf
from flask import Flask, jsonify, render_template, request, send_file
from openai import OpenAI

import static_util
from trading_graph import TradingGraph

app = Flask(__name__)


class WebTradingAnalyzer:
    """
    Web交易分析器类，封装了所有与Web界面后端相关的功能。
    """
    def __init__(self):
        """初始化Web交易分析器。"""
        self.trading_graph = TradingGraph()
        self.data_dir = Path("data")

        # 确保数据目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 可用资产及其显示名称
        self.asset_mapping = {
            "SPX": "S&P 500", "BTC": "比特币", "GC": "黄金期货", "NQ": "纳斯达克期货",
            "CL": "原油", "ES": "E-mini S&P 500", "DJI": "道琼斯", "QQQ": "Invesco QQQ Trust",
            "VIX": "波动率指数", "DXY": "美元指数", "AAPL": "苹果公司", "TSLA": "特斯拉公司",
        }

        # Yahoo Finance 符号映射
        self.yfinance_symbols = {
            "SPX": "^GSPC", "BTC": "BTC-USD", "GC": "GC=F", "NQ": "NQ=F",
            "CL": "CL=F", "ES": "ES=F", "DJI": "^DJI", "QQQ": "QQQ",
            "VIX": "^VIX", "DXY": "DX-Y.NYB",
        }

        # Yahoo Finance 时间间隔映射
        self.yfinance_intervals = {
            "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m", "1h": "1h",
            "4h": "4h", "1d": "1d", "1w": "1wk", "1mo": "1mo",
        }

        # 加载持久化的自定义资产
        self.custom_assets_file = self.data_dir / "custom_assets.json"
        self.custom_assets = self.load_custom_assets()

    def fetch_yfinance_data_with_datetime(
        self,
        symbol: str,
        interval: str,
        start_datetime: datetime,
        end_datetime: datetime,
    ) -> pd.DataFrame:
        """
        使用datetime对象从Yahoo Finance获取精确时间范围的OHLCV数据。

        Args:
            symbol (str): 资产代码。
            interval (str): K线周期。
            start_datetime (datetime): 开始日期时间。
            end_datetime (datetime): 结束日期时间。

        Returns:
            pd.DataFrame: 包含OHLCV数据的DataFrame，如果获取失败则返回空DataFrame。
        """
        try:
            yf_symbol = self.yfinance_symbols.get(symbol, symbol)
            yf_interval = self.yfinance_intervals.get(interval, interval)

            print(
                f"正在从 {start_datetime} 到 {end_datetime} 获取 {yf_symbol} 的数据，时间间隔为 {yf_interval}"
            )

            df = yf.download(
                tickers=yf_symbol,
                start=start_datetime,
                end=end_datetime,
                interval=yf_interval,
                auto_adjust=True,
                prepost=False,
            )

            if df is None or df.empty:
                print(f"没有为 {symbol} 返回数据")
                return pd.DataFrame()

            df = df.reset_index()

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            column_mapping = {
                "Date": "Datetime", "Open": "Open", "High": "High",
                "Low": "Low", "Close": "Close", "Volume": "Volume",
            }

            existing_columns = {old: new for old, new in column_mapping.items() if old in df.columns}
            df = df.rename(columns=existing_columns)

            required_columns = ["Datetime", "Open", "High", "Low", "Close"]
            if not all(col in df.columns for col in required_columns):
                print(f"警告：缺少列。可用列：{list(df.columns)}")
                return pd.DataFrame()

            df = df[required_columns]
            df["Datetime"] = pd.to_datetime(df["Datetime"])

            print(f"成功获取 {len(df)} 条 {symbol} 的数据点")
            print(f"日期范围：{df['Datetime'].min()} 到 {df['Datetime'].max()}")

            return df

        except Exception as e:
            print(f"获取 {symbol} 数据时出错: {e}")
            return pd.DataFrame()

    def get_available_assets(self) -> list:
        """从资产映射字典中获取可用资产列表。"""
        return sorted(list(self.asset_mapping.keys()))

    def get_available_files(self, asset: str, timeframe: str) -> list:
        """获取特定资产和时间框架的可用数据文件。"""
        asset_dir = self.data_dir / asset.lower()
        if not asset_dir.exists():
            return []
        pattern = f"{asset}_{timeframe}_*.csv"
        files = list(asset_dir.glob(pattern))
        return sorted(files)

    def run_analysis(
        self, df: pd.DataFrame, asset_name: str, timeframe: str
    ) -> Dict[str, Any]:
        """
        在提供的DataFrame上运行交易分析。

        Args:
            df (pd.DataFrame): 包含OHLCV数据的DataFrame。
            asset_name (str): 资产名称。
            timeframe (str): 时间周期。

        Returns:
            Dict[str, Any]: 包含分析结果或错误信息的字典。
        """
        try:
            if len(df) > 49:
                df_slice = df.tail(49).iloc[:-3]
            else:
                df_slice = df.tail(45)

            required_columns = ["Datetime", "Open", "High", "Low", "Close"]
            if not all(col in df_slice.columns for col in required_columns):
                return {"success": False, "error": f"缺少必需列。可用列: {list(df_slice.columns)}"}

            df_slice = df_slice.reset_index(drop=True)

            df_slice_dict = {}
            for col in required_columns:
                if col == "Datetime":
                    df_slice_dict[col] = df_slice[col].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
                else:
                    df_slice_dict[col] = df_slice[col].tolist()

            p_image = static_util.generate_kline_image(df_slice_dict)
            t_image = static_util.generate_trend_image(df_slice_dict)

            initial_state = {
                "kline_data": df_slice_dict, "analysis_results": None, "messages": [],
                "time_frame": timeframe, "stock_name": asset_name,
                "pattern_image": p_image["pattern_image"], "trend_image": t_image["trend_image"],
            }

            final_state = self.trading_graph.graph.invoke(initial_state)

            return {"success": True, "final_state": final_state, "asset_name": asset_name, "timeframe": timeframe, "data_length": len(df_slice)}

        except Exception as e:
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "invalid api key" in error_msg.lower() or "401" in error_msg:
                return {"success": False, "error": "❌ API密钥无效：您提供的OpenAI API密钥无效或已过期。请在设置中检查您的API密钥，然后重试。"}
            elif "rate limit" in error_msg.lower() or "429" in error_msg:
                return {"success": False, "error": "⚠️ 速率限制超出：您已达到OpenAI API速率限制。请稍候重试。"}
            return {"success": False, "error": f"❌ 分析错误: {error_msg}"}

    def extract_analysis_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """为Web显示提取并格式化分析结果。"""
        if not results["success"]:
            return {"error": results["error"]}

        final_state = results["final_state"]

        technical_indicators = final_state.get("indicator_report", "")
        pattern_analysis = final_state.get("pattern_report", "")
        trend_analysis = final_state.get("trend_report", "")
        final_decision_raw = final_state.get("final_trade_decision", "")

        pattern_chart = final_state.get("pattern_image", "")
        trend_chart = final_state.get("trend_image", "")

        final_decision = {}
        if final_decision_raw:
            try:
                start = final_decision_raw.find("{")
                end = final_decision_raw.rfind("}") + 1
                if start != -1 and end != 0:
                    json_str = final_decision_raw[start:end]
                    decision_data = json.loads(json_str)
                    final_decision = {
                        "decision": decision_data.get("decision", "N/A"),
                        "risk_reward_ratio": decision_data.get("risk_reward_ratio", "N/A"),
                        "forecast_horizon": decision_data.get("forecast_horizon", "N/A"),
                        "justification": decision_data.get("justification", "N/A"),
                    }
                else:
                    final_decision = {"raw": final_decision_raw}
            except json.JSONDecodeError:
                final_decision = {"raw": final_decision_raw}

        return {
            "success": True, "asset_name": results["asset_name"], "timeframe": results["timeframe"],
            "data_length": results["data_length"], "technical_indicators": technical_indicators,
            "pattern_analysis": pattern_analysis, "trend_analysis": trend_analysis,
            "pattern_chart": pattern_chart, "trend_chart": trend_chart,
            "final_decision": final_decision,
        }

    def load_custom_assets(self) -> list:
        """从持久化的JSON文件加载自定义资产。"""
        try:
            if self.custom_assets_file.exists():
                with open(self.custom_assets_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            return []
        except Exception as e:
            print(f"加载自定义资产时出错: {e}")
            return []

    def save_custom_asset(self, symbol: str) -> bool:
        """持久化保存自定义资产符号（避免重复）。"""
        try:
            symbol = symbol.strip()
            if not symbol:
                return False
            if symbol in self.custom_assets:
                return True
            self.custom_assets.append(symbol)
            with open(self.custom_assets_file, "w", encoding="utf-8") as f:
                json.dump(self.custom_assets, f, indent=2)
            return True
        except Exception as e:
            print(f"保存自定义资产 '{symbol}' 时出错: {e}")
            return False

analyzer = WebTradingAnalyzer()

@app.route("/")
def index():
    """主着陆页 - 重定向到演示。"""
    return render_template("demo_new.html")

@app.route("/api/analyze", methods=["POST"])
def analyze():
    """API端点，用于执行交易分析。"""
    try:
        data = request.get_json()
        asset = data.get("asset")
        timeframe = data.get("timeframe")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        use_current_time = data.get("use_current_time", False)

        start_dt = datetime.strptime(f"{start_date} 00:00", "%Y-%m-%d %H:%M")
        end_dt = datetime.now() if use_current_time else datetime.strptime(f"{end_date} 23:59", "%Y-%m-%d %H:%M")

        df = analyzer.fetch_yfinance_data_with_datetime(asset, timeframe, start_dt, end_dt)
        if df.empty:
            return jsonify({"error": "指定参数无可用数据"})

        display_name = analyzer.asset_mapping.get(asset, asset)
        results = analyzer.run_analysis(df, display_name, timeframe)
        formatted_results = analyzer.extract_analysis_results(results)

        return jsonify(formatted_results)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/api/assets")
def get_assets():
    """API端点，获取可用资产列表。"""
    assets = analyzer.get_available_assets()
    asset_list = [{"code": asset, "name": analyzer.asset_mapping.get(asset, asset)} for asset in assets]
    asset_list.extend([{"code": custom, "name": custom} for custom in analyzer.custom_assets])
    return jsonify({"assets": asset_list})

@app.route("/api/save-custom-asset", methods=["POST"])
def save_custom_asset():
    """在服务器端持久化保存自定义资产符号。"""
    try:
        symbol = (request.get_json().get("symbol") or "").strip()
        if not symbol:
            return jsonify({"success": False, "error": "需要提供符号"}), 400
        if not analyzer.save_custom_asset(symbol):
            return jsonify({"success": False, "error": "保存符号失败"}), 500
        return jsonify({"success": True, "symbol": symbol})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)
    static_dir = Path("static")
    static_dir.mkdir(exist_ok=True)
    app.run(debug=True, host="127.0.0.1", port=5000)
