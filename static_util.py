# -*- coding: utf-8 -*-
"""
静态图表生成工具模块。

该模块提供了用于生成K线图和带趋势线的K线图的函数。
这些函数是独立的，不属于任何类，主要用于数据可视化。
"""
import base64
import io

import matplotlib
import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np
import pandas as pd

import color_style as color
from graph_util import (
    fit_trendlines_high_low,
    fit_trendlines_single,
    get_line_points,
    split_line_into_segments,
)

# 设置matplotlib后端为'Agg'，避免在无GUI环境下出错
matplotlib.use("Agg")


def generate_kline_image(kline_data) -> dict:
    """
    根据OHLCV数据生成K线图，将其保存到本地，并返回Base64编码的图像。

    Args:
        kline_data (dict): 包含'Datetime', 'Open', 'High', 'Low', 'Close'键的字典。

    Returns:
        dict: 包含Base64编码图像字符串和图像描述的字典。
              例如：{'pattern_image': 'base64_string', 'pattern_image_description': '...'}
    """

    df = pd.DataFrame(kline_data)
    # 截取最近的40条数据
    df = df.tail(40)

    df.to_csv("record.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")
    try:
        df.index = pd.to_datetime(df["Datetime"], format="%Y-%m-%d %H:%M:%S")
    except ValueError:
        print("在 static_util.py 中处理时间戳时出现 ValueError\n")

    # 将图像保存到本地
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

    # ---------- 编码为 Base64 -----------------
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=600, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)  # 释放内存

    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode("utf-8")

    return {
        "pattern_image": img_b64,
        "pattern_image_description": "K线图已保存到本地并以Base64字符串形式返回。",
    }


def generate_trend_image(kline_data) -> dict:
    """
    根据OHLCV数据生成带趋势线的K线图，
    将其保存为本地文件'trend_graph.png'，并返回Base64编码的图像。

    Args:
        kline_data (dict): 包含'Datetime', 'Open', 'High', 'Low', 'Close'键的字典。

    Returns:
        dict: 包含Base64图像和描述的字典。
              例如：{'trend_image': 'base64_string', 'trend_image_description': '...'}
    """
    data = pd.DataFrame(kline_data)
    candles = data.iloc[-50:].copy()

    candles["Datetime"] = pd.to_datetime(candles["Datetime"])
    candles.set_index("Datetime", inplace=True)

    # 假设趋势线拟合函数在此作用域之外定义
    support_coefs_c, resist_coefs_c = fit_trendlines_single(candles["Close"])
    support_coefs, resist_coefs = fit_trendlines_high_low(
        candles["High"], candles["Low"], candles["Close"]
    )

    # 趋势线值
    support_line_c = support_coefs_c[0] * np.arange(len(candles)) + support_coefs_c[1]
    resist_line_c = resist_coefs_c[0] * np.arange(len(candles)) + resist_coefs_c[1]
    support_line = support_coefs[0] * np.arange(len(candles)) + support_coefs[1]
    resist_line = resist_coefs[0] * np.arange(len(candles)) + resist_coefs[1]

    # 转换为时间锚定的坐标
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

    # 为基于收盘价的支撑/阻力线创建addplot
    apds = [
        mpf.make_addplot(support_line_c, color="blue", width=1, label="收盘价支撑线"),
        mpf.make_addplot(resist_line_c, color="red", width=1, label="收盘价阻力线"),
    ]

    # 生成带图例的图表并保存到本地
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

    # 保存图表到本地
    fig.savefig(
        "trend_graph.png", format="png", dpi=600, bbox_inches="tight", pad_inches=0.1
    )
    plt.close(fig)

    # 手动添加图例
    axlist[0].legend(loc="upper left")

    # 保存为Base64
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)

    return {
        "trend_image": img_b64,
        "trend_image_description": "带支撑/阻力线的趋势增强K线图。",
    }
