# -*- coding: utf-8 -*-
"""
K线图颜色和字体样式配置
"""

import mplfinance as mpf

# 定义图表使用的字体样式
font = {
    "font.family": "sans-serif",  # 字体族
    "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"],  # 无衬线字体列表
    "font.weight": "normal",  # 字体粗细
    "font.size": 15,  # 字体大小
}

# 自定义K线图的颜色风格
my_color_style = mpf.make_mpf_style(
    marketcolors=mpf.make_marketcolors(
        down="#A02128",  # 下跌蜡烛（熊市）的颜色
        up="#006340",  # 上涨蜡烛（牛市）的颜色
        edge="none",  # 烛心边缘颜色，"none"表示使用填充色
        wick="black",  # 影线颜色
        volume="in",  # 成交量颜色，"in"表示继承K线颜色
    ),
    gridstyle="-",  # 网格线样式
    facecolor="white",  # 图表背景色
    rc=font,  # 应用上面定义的字体配置
)
