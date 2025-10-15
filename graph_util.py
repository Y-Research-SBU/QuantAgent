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

matplotlib.use("Agg")


# helper function for trending graph
def check_trend_line(support: bool, pivot: int, slope: float, y: np.array):
    # compute sum of differences between line and prices,
    # return negative val if invalid

    # Find the intercept of the line going through pivot point with given slope
    intercept = -slope * pivot + y.iloc[pivot]

    line_vals = slope * np.arange(len(y)) + intercept

    diffs = line_vals - y

    # Check to see if the line is valid, return -1 if it is not valid.
    if support and diffs.max() > 1e-5:
        return -1.0
    elif not support and diffs.min() < -1e-5:
        return -1.0

    # Squared sum of diffs between data and line
    err = (diffs**2.0).sum()
    return err


def optimize_slope(support: bool, pivot: int, init_slope: float, y: np.array):
    # Amount to change slope by. Multiplyed by opt_step
    slope_unit = (y.max() - y.min()) / len(y)

    # Optmization variables
    opt_step = 1.0
    min_step = 0.0001
    curr_step = opt_step  # current step

    # Initiate at the slope of the line of best fit
    best_slope = init_slope
    best_err = check_trend_line(support, pivot, init_slope, y)
    assert best_err >= 0.0  # Shouldn't ever fail with initial slope

    get_derivative = True
    derivative = None
    while curr_step > min_step:

        if get_derivative:
            # Numerical differentiation, increase slope by very small amount
            # to see if error increases/decreases.
            # Gives us the direction to change slope.
            slope_change = best_slope + slope_unit * min_step
            test_err = check_trend_line(support, pivot, slope_change, y)
            derivative = test_err - best_err

            # If increasing by a small amount fails,
            # try decreasing by a small amount
            if test_err < 0.0:
                slope_change = best_slope - slope_unit * min_step
                test_err = check_trend_line(support, pivot, slope_change, y)
                derivative = best_err - test_err

            if test_err < 0.0:  # Derivative failed, give up
                raise Exception("Derivative failed. Check your data. ")

            get_derivative = False

        if derivative > 0.0:  # Increasing slope increased error
            test_slope = best_slope - slope_unit * curr_step
        else:  # Increasing slope decreased error
            test_slope = best_slope + slope_unit * curr_step

        test_err = check_trend_line(support, pivot, test_slope, y)
        if test_err < 0 or test_err >= best_err:
            # slope failed/didn't reduce error
            curr_step *= 0.5  # Reduce step size
        else:  # test slope reduced error
            best_err = test_err
            best_slope = test_slope
            get_derivative = True  # Recompute derivative

    # Optimize done, return best slope and intercept
    return (best_slope, -best_slope * pivot + y.iloc[pivot])


def fit_trendlines_single(data: np.array):
    # find line of best fit (least squared)
    # coefs[0] = slope,  coefs[1] = intercept
    x = np.arange(len(data))
    coefs = np.polyfit(x, data, 1)

    # Get points of line.
    line_points = coefs[0] * x + coefs[1]

    # Find upper and lower pivot points
    upper_pivot = (data - line_points).argmax()
    lower_pivot = (data - line_points).argmin()

    # Optimize the slope for both trend lines
    support_coefs = optimize_slope(True, lower_pivot, coefs[0], data)
    resist_coefs = optimize_slope(False, upper_pivot, coefs[0], data)

    return (support_coefs, resist_coefs)


def fit_trendlines_high_low(high: np.array, low: np.array, close: np.array):
    x = np.arange(len(close))
    coefs = np.polyfit(x, close, 1)
    # coefs[0] = slope,  coefs[1] = intercept
    line_points = coefs[0] * x + coefs[1]
    upper_pivot = (high - line_points).argmax()
    lower_pivot = (low - line_points).argmin()

    support_coefs = optimize_slope(True, lower_pivot, coefs[0], low)
    resist_coefs = optimize_slope(False, upper_pivot, coefs[0], high)

    return (support_coefs, resist_coefs)


def get_line_points(candles, line_points):
    # Place line points in tuples for matplotlib finance
    # https://github.com/matplotlib/mplfinance/blob/master/examples/using_lines.ipynb
    idx = candles.index
    line_i = len(candles) - len(line_points)
    assert line_i >= 0
    points = []
    for i in range(line_i, len(candles)):
        points.append((idx[i], line_points[i - line_i]))
    return points


def split_line_into_segments(line_points):
    return [[line_points[i], line_points[i + 1]] for i in range(len(line_points) - 1)]


# Calculate MACD using TA-Lib
# Typical parameters: fastperiod=12, slowperiod=26, signalperiod=9


class TechnicalTools:

    @staticmethod
    @tool
    def generate_trend_image(
        kline_data: Annotated[
            dict,
            "Dictionary containing OHLCV data with keys 'Datetime', 'Open', 'High', 'Low', 'Close'.",
        ]
    ) -> dict:
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
        support_line_c = (
            support_coefs_c[0] * np.arange(len(candles)) + support_coefs_c[1]
        )
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
            mpf.make_addplot(
                support_line_c, color="blue", width=1, label="Close Support"
            ),
            mpf.make_addplot(
                resist_line_c, color="red", width=1, label="Close Resistance"
            ),
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
            "trend_graph.png",
            format="png",
            dpi=600,
            bbox_inches="tight",
            pad_inches=0.1,
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

    @staticmethod
    @tool
    def generate_kline_image(
        kline_data: Annotated[
            dict,
            "Dictionary containing OHLCV data with keys 'Datetime', 'Open', 'High', 'Low', 'Close'.",
        ],
    ) -> dict:
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

    @staticmethod
    @tool
    def compute_rsi(
        kline_data: Annotated[
            dict,
            "Dictionary with a 'Close' key containing a list of float closing prices.",
        ],
        period: Annotated[
            int, "Lookback period for RSI calculation (default is 14)"
        ] = 14,
    ) -> dict:
        """
        Compute the Relative Strength Index (RSI) using TA-Lib.

        Args:
            data (dict): Dictionary containing at least a 'Close' key with a list of float values.
            period (int): Lookback period for RSI calculation (default is 14).

        Returns:
            dict: A dictionary with a single key 'rsi' mapping to a list of RSI values.
        """
        df = pd.DataFrame(kline_data)
        rsi = talib.RSI(df["Close"], timeperiod=period)
        return {"rsi": rsi.fillna(0).round(2).tolist()[-28:]}

    @staticmethod
    @tool
    def compute_macd(
        kline_data: Annotated[
            dict,
            "Dictionary with a 'Close' key containing a list of float closing prices.",
        ],
        fastperiod: Annotated[int, "Fast EMA period"] = 12,
        slowperiod: Annotated[int, "Slow EMA period"] = 26,
        signalperiod: Annotated[int, "Signal line EMA period"] = 9,
    ) -> dict:
        """
        Compute the Moving Average Convergence Divergence (MACD) using TA-Lib.

        Args:
            kline_data (dict): Dictionary containing a 'Close' key with list of float values.
            fastperiod (int): Fast EMA period.
            slowperiod (int): Slow EMA period.
            signalperiod (int): Signal line EMA period.

        Returns:
            dict: Dictionary containing 'macd', 'macd_signal', and 'macd_hist' as lists of values.
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
            "Dictionary with 'High', 'Low', and 'Close' keys, each mapping to lists of float values.",
        ]
    ) -> dict:
        """
        Compute the Stochastic Oscillator %K and %D using TA-Lib.

        Args:
            kline_data (dict): Dictionary with 'High', 'Low', and 'Close' keys, each mapping to lists of float values.

        Returns:
            dict: A dictionary with keys 'stoch_k' and 'stoch_d',
                each mapping to a list representing %K and %D values.
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
            "Dictionary with a 'Close' key containing a list of float closing prices.",
        ],
        period: Annotated[
            int, "Number of periods over which to calculate ROC (default is 10)"
        ] = 10,
    ) -> dict:
        """
        Compute the Rate of Change (ROC) indicator using TA-Lib.

        Args:
            kline_data (dict): Dictionary containing a 'Close' key with a list of float values.
            period (int): Number of periods over which to calculate ROC (default is 10).

        Returns:
            dict: A dictionary with a single key 'roc' mapping to a list of ROC values.
        """

        df = pd.DataFrame(kline_data)
        roc = talib.ROC(df["Close"], timeperiod=period)
        return {"roc": roc.fillna(0).round(2).tolist()[-28:]}

    @staticmethod
    @tool
    def compute_willr(
        kline_data: Annotated[
            dict,
            "Dictionary with 'High', 'Low', and 'Close' keys containing float lists.",
        ],
        period: Annotated[int, "Lookback period for Williams %R"] = 14,
    ) -> dict:
        """
        Compute the Williams %R indicator using TA-Lib.

        Args:
            kline_data (dict): Dictionary with 'High', 'Low', and 'Close' keys.
            period (int): Lookback period for Williams %R calculation.

        Returns:
            dict: Dictionary with key 'willr' mapping to the list of Williams %R values.
        """
        # print("-------------------------CALLED COMPUTE WILLR--------------------------\n")
        df = pd.DataFrame(kline_data)
        willr = talib.WILLR(df["High"], df["Low"], df["Close"], timeperiod=period)
        return {"willr": willr.fillna(0).round(2).tolist()[-28:]}
