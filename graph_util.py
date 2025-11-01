# -*- coding: utf-8 -*-
"""
该模块提供用于图（Graph）的技术分析工具和辅助函数。

包含以下功能：
- 生成带趋势线的K线图。
- 生成常规的K线图。
- 计算多种技术指标（RSI, MACD, Stochastic Oscillator, ROC, Williams %R）。
- 趋势线拟合的辅助函数。
"""

import base64
import io
from typing import Annotated

import matplotlib
import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np
import pandas as pd
import talib
from langchain_core.tools import tool

import color_style as color

# 设置matplotlib后端为'Agg'，避免在无GUI环境下出错
matplotlib.use("Agg")


def check_trend_line(support: bool, pivot: int, slope: float, y: np.array):
    """
    检查趋势线是否有效。

    Args:
        support (bool): True表示支撑线，False表示阻力线。
        pivot (int): 趋势线的枢轴点索引。
        slope (float): 趋势线的斜率。
        y (np.array): 价格数据数组。

    Returns:
        float: 如果趋势线无效，返回-1.0；否则返回误差的平方和。
    """
    # 计算通过枢轴点和给定斜率的截距
    intercept = -slope * pivot + y.iloc[pivot]

    # 计算趋势线上的值
    line_vals = slope * np.arange(len(y)) + intercept

    # 计算价格与趋势线之间的差异
    diffs = line_vals - y

    # 检查趋势线是否有效
    if support and diffs.max() > 1e-5:
        return -1.0  # 支撑线不能在价格之上
    elif not support and diffs.min() < -1e-5:
        return -1.0  # 阻力线不能在价格之下

    # 返回误差的平方和
    err = (diffs**2.0).sum()
    return err


def optimize_slope(support: bool, pivot: int, init_slope: float, y: np.array):
    """
    优化趋势线的斜率以最小化误差。

    Args:
        support (bool): True表示支撑线，False表示阻力线。
        pivot (int): 枢轴点索引。
        init_slope (float): 初始斜率。
        y (np.array): 价格数据数组。

    Returns:
        tuple: 包含优化后的斜率和截距的元组。
    """
    # 定义斜率变化的单位
    slope_unit = (y.max() - y.min()) / len(y)

    # 优化变量
    opt_step = 1.0
    min_step = 0.0001
    curr_step = opt_step

    # 从最佳拟合线的斜率开始
    best_slope = init_slope
    best_err = check_trend_line(support, pivot, init_slope, y)
    assert best_err >= 0.0, "初始斜率不应导致无效的趋势线"

    get_derivative = True
    derivative = None
    while curr_step > min_step:

        if get_derivative:
            # 数值微分，以确定斜率调整方向
            slope_change = best_slope + slope_unit * min_step
            test_err = check_trend_line(support, pivot, slope_change, y)
            derivative = test_err - best_err

            if test_err < 0.0:
                slope_change = best_slope - slope_unit * min_step
                test_err = check_trend_line(support, pivot, slope_change, y)
                derivative = best_err - test_err

            if test_err < 0.0:
                raise Exception("导数计算失败，请检查数据。")

            get_derivative = False

        if derivative > 0.0:
            test_slope = best_slope - slope_unit * curr_step
        else:
            test_slope = best_slope + slope_unit * curr_step

        test_err = check_trend_line(support, pivot, test_slope, y)
        if test_err < 0 or test_err >= best_err:
            curr_step *= 0.5
        else:
            best_err = test_err
            best_slope = test_slope
            get_derivative = True

    return (best_slope, -best_slope * pivot + y.iloc[pivot])


def fit_trendlines_single(data: np.array):
    """
    拟合单条趋势线（支撑线和阻力线）。

    Args:
        data (np.array): 价格数据数组。

    Returns:
        tuple: 包含支撑线和阻力线系数的元组。
    """
    x = np.arange(len(data))
    coefs = np.polyfit(x, data, 1)
    line_points = coefs[0] * x + coefs[1]

    upper_pivot = (data - line_points).argmax()
    lower_pivot = (data - line_points).argmin()

    support_coefs = optimize_slope(True, lower_pivot, coefs[0], data)
    resist_coefs = optimize_slope(False, upper_pivot, coefs[0], data)

    return (support_coefs, resist_coefs)


def fit_trendlines_high_low(high: np.array, low: np.array, close: np.array):
    """
    根据最高价和最低价拟合趋势线。

    Args:
        high (np.array): 最高价数组。
        low (np.array): 最低价数组。
        close (np.array): 收盘价数组。

    Returns:
        tuple: 包含支撑线和阻力线系数的元组。
    """
    x = np.arange(len(close))
    coefs = np.polyfit(x, close, 1)
    line_points = coefs[0] * x + coefs[1]

    upper_pivot = (high - line_points).argmax()
    lower_pivot = (low - line_points).argmin()

    support_coefs = optimize_slope(True, lower_pivot, coefs[0], low)
    resist_coefs = optimize_slope(False, upper_pivot, coefs[0], high)

    return (support_coefs, resist_coefs)


def get_line_points(candles, line_points):
    """
    将趋势线点转换为mplfinance所需的格式。
    """
    idx = candles.index
    line_i = len(candles) - len(line_points)
    assert line_i >= 0
    points = []
    for i in range(line_i, len(candles)):
        points.append((idx[i], line_points[i - line_i]))
    return points


def split_line_into_segments(line_points):
    """
    将趋势线点分割成段，以便绘制。
    """
    return [[line_points[i], line_points[i + 1]] for i in range(len(line_points) - 1)]


class TechnicalTools:
    """
    包含用于技术分析的工具集合的类。
    所有工具都设计为静态方法，并使用@tool装饰器。
    """

    @staticmethod
    @tool
    def generate_trend_image(
        kline_data: Annotated[
            dict,
            "包含OHLCV数据的字典，键为'Datetime', 'Open', 'High', 'Low', 'Close'。",
        ]
    ) -> dict:
        """
        根据OHLCV数据生成带趋势线的K线图，
        将其保存为本地文件'trend_graph.png'，并返回Base64编码的图像。

        Returns:
            dict: 包含Base64图像和描述的字典。
        """
        data = pd.DataFrame(kline_data)
        candles = data.iloc[-50:].copy()

        candles["Datetime"] = pd.to_datetime(candles["Datetime"])
        candles.set_index("Datetime", inplace=True)

        support_coefs_c, resist_coefs_c = fit_trendlines_single(candles["Close"])
        support_coefs, resist_coefs = fit_trendlines_high_low(
            candles["High"], candles["Low"], candles["Close"]
        )

        support_line_c = support_coefs_c[0] * np.arange(len(candles)) + support_coefs_c[1]
        resist_line_c = resist_coefs_c[0] * np.arange(len(candles)) + resist_coefs_c[1]
        support_line = support_coefs[0] * np.arange(len(candles)) + support_coefs[1]
        resist_line = resist_coefs[0] * np.arange(len(candles)) + resist_coefs[1]

        s_seq = get_line_points(candles, support_line)
        r_seq = get_line_points(candles, resist_line)
        s_seq2 = get_line_points(candles, support_line_c)
        r_seq2 = get_line_points(candles, resist_line_c)

        s_segments = split_line_into_segments(s_seq)
        r_segments = split_line_into_segments(r_seq)
        s2_segments = split_line_into_segments(s_seq2)
        r2_segments = split_line_into_segments(r_seq2)

        all_segments = s_segments + r_segments + s2_segments + r2_segments
        colors = (
            ["white"] * len(s_segments)
            + ["white"] * len(r_segments)
            + ["blue"] * len(s2_segments)
            + ["red"] * len(r2_segments)
        )

        apds = [
            mpf.make_addplot(support_line_c, color="blue", width=1, label="收盘价支撑线"),
            mpf.make_addplot(resist_line_c, color="red", width=1, label="收盘价阻力线"),
        ]

        fig, axlist = mpf.plot(
            candles,
            type="candle",
            style=color.my_color_style,
            addplot=apds,
            alines=dict(alines=all_segments, colors=colors, linewidths=1),
            returnfig=True,
            figsize=(12, 6),
            block=False,
        )

        axlist[0].set_ylabel("价格", fontweight="normal")
        axlist[0].set_xlabel("日期时间", fontweight="normal")

        fig.savefig(
            "trend_graph.png",
            format="png",
            dpi=600,
            bbox_inches="tight",
            pad_inches=0.1,
        )
        plt.close(fig)

        axlist[0].legend(loc="upper left")

        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode("utf-8")
        plt.close(fig)

        return {
            "trend_image": img_b64,
            "trend_image_description": "带支撑/阻力线的趋势增强K线图。",
        }

    @staticmethod
    @tool
    def generate_kline_image(
        kline_data: Annotated[
            dict,
            "包含OHLCV数据的字典，键为'Datetime', 'Open', 'High', 'Low', 'Close'。",
        ],
    ) -> dict:
        """
        根据OHLCV数据生成K线图，将其保存到本地，并返回Base64编码的图像。

        Args:
            kline_data (dict): 包含'Datetime', 'Open', 'High', 'Low', 'Close'键的字典。

        Returns:
            dict: 包含Base64编码图像字符串和本地文件路径的字典。
        """
        df = pd.DataFrame(kline_data)
        df = df.tail(40)

        df.to_csv("record.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")
        try:
            df.index = pd.to_datetime(df["Datetime"], format="%Y-%m-%d %H:%M:%S")
        except ValueError:
            print("graph_util.py中出现ValueError\n")

        fig, axlist = mpf.plot(
            df[["Open", "High", "Low", "Close"]],
            type="candle",
            style=color.my_color_style,
            figsize=(12, 6),
            returnfig=True,
            block=False,
        )
        axlist[0].set_ylabel("价格", fontweight="normal")
        axlist[0].set_xlabel("日期时间", fontweight="normal")

        fig.savefig(
            fname="kline_chart.png",
            dpi=600,
            bbox_inches="tight",
            pad_inches=0.1,
        )
        plt.close(fig)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=600, bbox_inches="tight", pad_inches=0.1)
        plt.close(fig)

        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode("utf-8")

        return {
            "pattern_image": img_b64,
            "pattern_image_description": "K线图已保存到本地并以Base64字符串形式返回。",
        }

    @staticmethod
    @tool
    def compute_rsi(
        kline_data: Annotated[
            dict,
            "包含'Close'键的字典，其值为浮点数收盘价列表。",
        ],
        period: Annotated[int, "RSI计算的回溯期（默认为14）"] = 14,
    ) -> dict:
        """
        使用TA-Lib计算相对强弱指数（RSI）。

        Args:
            kline_data (dict): 至少包含'Close'键的字典，其值为浮点数列表。
            period (int): RSI计算的回溯期（默认为14）。

        Returns:
            dict: 包含键'rsi'和RSI值列表的字典。
        """
        df = pd.DataFrame(kline_data)
        rsi = talib.RSI(df["Close"], timeperiod=period)
        return {"rsi": rsi.fillna(0).round(2).tolist()[-28:]}

    @staticmethod
    @tool
    def compute_macd(
        kline_data: Annotated[
            dict,
            "包含'Close'键的字典，其值为浮点数收盘价列表。",
        ],
        fastperiod: Annotated[int, "快速EMA周期"] = 12,
        slowperiod: Annotated[int, "慢速EMA周期"] = 26,
        signalperiod: Annotated[int, "信号线EMA周期"] = 9,
    ) -> dict:
        """
        使用TA-Lib计算移动平均收敛散度（MACD）。

        Args:
            kline_data (dict): 包含'Close'键的字典，其值为浮点数列表。
            fastperiod (int): 快速EMA周期。
            slowperiod (int): 慢速EMA周期。
            signalperiod (int): 信号线EMA周期。

        Returns:
            dict: 包含'macd', 'macd_signal', 'macd_hist'值列表的字典。
        """
        df = pd.DataFrame(kline_data)
        macd, macd_signal, macd_hist = talib.MACD(
            df["Close"],
            fastperiod=fastperiod,
            slowperiod=slowperiod,
            signalperiod=signalperiod,
        )
        return {
            "macd": macd.fillna(0).round(2).tolist(),
            "macd_signal": macd_signal.fillna(0).round(2).tolist()[-28:],
            "macd_hist": macd_hist.fillna(0).round(2).tolist()[-28:],
        }

    @staticmethod
    @tool
    def compute_stoch(
        kline_data: Annotated[
            dict,
            "包含'High', 'Low', 'Close'键的字典，其值为浮点数列表。",
        ]
    ) -> dict:
        """
        使用TA-Lib计算随机振荡器（Stochastic Oscillator）的%K和%D值。

        Args:
            kline_data (dict): 包含'High', 'Low', 'Close'键的字典，其值为浮点数列表。

        Returns:
            dict: 包含'stoch_k'和'stoch_d'键的字典，其值为%K和%D值列表。
        """
        df = pd.DataFrame(kline_data)
        stoch_k, stoch_d = talib.STOCH(
            df["High"],
            df["Low"],
            df["Close"],
            fastk_period=14,
            slowk_period=3,
            slowd_period=3,
        )
        return {
            "stoch_k": stoch_k.fillna(0).round(2).tolist()[-28:],
            "stoch_d": stoch_d.fillna(0).round(2).tolist()[-28:],
        }

    @staticmethod
    @tool
    def compute_roc(
        kline_data: Annotated[
            dict,
            "包含'Close'键的字典，其值为浮点数收盘价列表。",
        ],
        period: Annotated[int, "计算ROC的周期数（默认为10）"] = 10,
    ) -> dict:
        """
        使用TA-Lib计算变动率指标（ROC）。

        Args:
            kline_data (dict): 包含'Close'键的字典，其值为浮点数列表。
            period (int): 计算ROC的周期数（默认为10）。

        Returns:
            dict: 包含'roc'键和ROC值列表的字典。
        """
        df = pd.DataFrame(kline_data)
        roc = talib.ROC(df["Close"], timeperiod=period)
        return {"roc": roc.fillna(0).round(2).tolist()[-28:]}

    @staticmethod
    @tool
    def compute_willr(
        kline_data: Annotated[
            dict,
            "包含'High', 'Low', 'Close'键的字典，其值为浮点数列表。",
        ],
        period: Annotated[int, "威廉姆斯%R的回溯期"] = 14,
    ) -> dict:
        """
        使用TA-Lib计算威廉姆斯%R指标（Williams %R）。

        Args:
            kline_data (dict): 包含'High', 'Low', 'Close'键的字典。
            period (int): 威廉姆斯%R的回溯期。

        Returns:
            dict: 包含'willr'键和威廉姆斯%R值列表的字典。
        """
        df = pd.DataFrame(kline_data)
        willr = talib.WILLR(df["High"], df["Low"], df["Close"], timeperiod=period)
        return {"willr": willr.fillna(0).round(2).tolist()[-28:]}
