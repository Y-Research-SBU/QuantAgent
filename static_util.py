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

matplotlib.use("Agg")


def generate_kline_image(kline_data) -> dict:
    """
    Generate a candlestick (K-line) chart from OHLCV data, save it locally, and return a base64-encoded image.

    Args:
        kline_data (dict): Dictionary with keys including 'Datetime', 'Open', 'High', 'Low', 'Close'.
        filename (str): Name of the file to save the image locally (default: 'kline_chart.png').

    Returns:
        dict: Dictionary containing base64-encoded image string and local file path.
    """

    df = pd.DataFrame(kline_data)
    # take recent 40
    df = df.tail(40)

    df.to_csv("record.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")
    try:
        # df.index = pd.to_datetime(df["Datetime"])
        df.index = pd.to_datetime(df["Datetime"], format="%Y-%m-%d %H:%M:%S")

    except ValueError:
        print("ValueError at graph_util.py\n")

    # Save image locally
    fig, axlist = mpf.plot(
        df[["Open", "High", "Low", "Close"]],
        type="candle",
        style=color.my_color_style,
        figsize=(12, 6),
        returnfig=True,
        block=False,
    )
    axlist[0].set_ylabel("Price", fontweight="normal")
    axlist[0].set_xlabel("Datetime", fontweight="normal")

    fig.savefig(
        fname="kline_chart.png",
        dpi=600,
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.close(fig)
    # ---------- Encode to base64 -----------------
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=600, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)  # release memory

    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode("utf-8")

    return {
        "pattern_image": img_b64,
        "pattern_image_description": "Candlestick chart saved locally and returned as base64 string.",
    }


def generate_trend_image(kline_data) -> dict:
    """
    Generate a candlestick chart with trendlines from OHLCV data,
    save it locally as 'trend_graph.png', and return a base64-encoded image.

    Returns:
        dict: base64 image and description
    """
    data = pd.DataFrame(kline_data)
    candles = data.iloc[-50:].copy()

    candles["Datetime"] = pd.to_datetime(candles["Datetime"])
    candles.set_index("Datetime", inplace=True)

    # Trendline fit functions assumed to be defined outside this scope
    support_coefs_c, resist_coefs_c = fit_trendlines_single(candles["Close"])
    support_coefs, resist_coefs = fit_trendlines_high_low(
        candles["High"], candles["Low"], candles["Close"]
    )

    # Trendline values
    support_line_c = support_coefs_c[0] * np.arange(len(candles)) + support_coefs_c[1]
    resist_line_c = resist_coefs_c[0] * np.arange(len(candles)) + resist_coefs_c[1]
    support_line = support_coefs[0] * np.arange(len(candles)) + support_coefs[1]
    resist_line = resist_coefs[0] * np.arange(len(candles)) + resist_coefs[1]

    # Convert to time-anchored coordinates
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

    # Create addplot lines for close-based support/resistance
    apds = [
        mpf.make_addplot(support_line_c, color="blue", width=1, label="Close Support"),
        mpf.make_addplot(resist_line_c, color="red", width=1, label="Close Resistance"),
    ]

    # Generate figure with legend and save locally
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

    axlist[0].set_ylabel("Price", fontweight="normal")
    axlist[0].set_xlabel("Datetime", fontweight="normal")

    # save fig locally
    fig.savefig(
        "trend_graph.png", format="png", dpi=600, bbox_inches="tight", pad_inches=0.1
    )
    plt.close(fig)

    # Add legend manually
    axlist[0].legend(loc="upper left")

    # Save to base64
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)

    return {
        "trend_image": img_b64,
        "trend_image_description": "Trend-enhanced candlestick chart with support/resistance lines.",
    }
