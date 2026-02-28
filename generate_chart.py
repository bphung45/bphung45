"""
Fetches S&P 500 data and renders a dark-themed chart saved to assets/sp500.png.
Run by GitHub Actions on a schedule.
"""

import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import numpy as np
from datetime import datetime
import os

# ── Config ────────────────────────────────────────────────────────────────────
TICKER      = "^GSPC"
PERIOD      = "1d"       # Daily data
OUTPUT_PATH = "assets/sp500.png"

# ── Fetch data ────────────────────────────────────────────────────────────────
data = yf.download(TICKER, period=PERIOD, interval="1d", progress=False, auto_adjust=True)
closes = data["Close"].squeeze()
dates  = closes.index

# ── Derived values ────────────────────────────────────────────────────────────
latest     = float(closes.iloc[-1])
prev_close = float(closes.iloc[-2])
change     = latest - prev_close
pct_change = (change / prev_close) * 100
period_low  = float(closes.min())
period_high = float(closes.max())
is_up       = change >= 0

accent = "#00FF88" if is_up else "#FF4444"
arrow  = "▲" if is_up else "▼"

# ── Colours ───────────────────────────────────────────────────────────────────
BG      = "#0D1117"   # GitHub dark background
PANEL   = "#161B22"
GRID    = "#21262D"
TEXT    = "#E6EDF3"
SUBTEXT = "#8B949E"

# ── Figure ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 4), facecolor=BG)
ax.set_facecolor(BG)

# Gradient fill under the line
fill_color = "#00FF88" if is_up else "#FF4444"
ax.fill_between(dates, closes, closes.min() * 0.998,
                color=fill_color, alpha=0.08)

# Price line
ax.plot(dates, closes, color=accent, linewidth=1.8, zorder=3)

# Latest price dot
ax.scatter([dates[-1]], [latest], color=accent, s=40, zorder=5, linewidths=0)

# ── Grid ──────────────────────────────────────────────────────────────────────
ax.set_axisbelow(True)
ax.yaxis.grid(True, color=GRID, linewidth=0.6, linestyle="--")
ax.xaxis.grid(False)
for spine in ax.spines.values():
    spine.set_visible(False)

# ── Axes formatting ───────────────────────────────────────────────────────────
ax.tick_params(colors=SUBTEXT, labelsize=8, length=0)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.yaxis.tick_right()

# ── Header labels ─────────────────────────────────────────────────────────────
fig.text(0.02, 0.92, "S&P 500  ·  ^GSPC",
         color=TEXT, fontsize=11, fontweight="bold",
         fontfamily="monospace", transform=fig.transFigure)

fig.text(0.02, 0.76,
         f"{latest:,.2f}   {arrow} {abs(change):.2f}  ({abs(pct_change):.2f}%)",
         color=accent, fontsize=9, fontfamily="monospace",
         transform=fig.transFigure)

fig.text(0.02, 0.62,
         f"6mo low {period_low:,.0f}   ·   6mo high {period_high:,.0f}",
         color=SUBTEXT, fontsize=7.5, fontfamily="monospace",
         transform=fig.transFigure)

# Timestamp (bottom-right)
ts = datetime.utcnow().strftime("Updated %b %d, %Y %H:%M UTC")
fig.text(0.98, 0.04, ts, color=SUBTEXT, fontsize=6.5,
         fontfamily="monospace", ha="right", transform=fig.transFigure)

# ── Save ──────────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
plt.tight_layout(rect=[0, 0, 1, 0.68])
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight",
            facecolor=BG, edgecolor="none")
plt.close()

print(f"Chart saved → {OUTPUT_PATH}  |  {latest:,.2f}  {arrow} {pct_change:+.2f}%")