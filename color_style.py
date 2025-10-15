import mplfinance as mpf

font = {
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"],
    "font.weight": "normal",
    "font.size": 15,
}

my_color_style = mpf.make_mpf_style(
    marketcolors=mpf.make_marketcolors(
        down="#A02128",  # color for bullish candles
        up="#006340",  # color for bearish candles
        edge="none",  # use candle fill color for edge
        wick="black",  # color of the wicks
        volume="in",  # default volume coloring
    ),
    gridstyle="-",
    facecolor="white",  # background color
    rc=font,
)
