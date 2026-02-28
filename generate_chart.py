"""
Fetches today's intraday S&P 500 data (1-min bars) and renders a
dark-themed candlestick chart saved to assets/sp500.png.
- All times displayed in Eastern Time (ET)
- Vertical lines at each hour mark
- Pre-market and after-hours regions lightly shaded
"""

import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from datetime import datetime, time
import pytz
import os

# ── Config ────────────────────────────────────────────────────────────────────
TICKER      = "^GSPC"
OUTPUT_PATH = "assets/sp500.png"
ET          = pytz.timezone("America/New_York")

MARKET_OPEN  = time(9, 30)
MARKET_CLOSE = time(16, 0)

# ── Fetch today's 1-min intraday data ─────────────────────────────────────────
data = yf.download(TICKER, period="1d", interval="1m", progress=False, auto_adjust=True)

if data.empty:
    print("No intraday data returned — market may be closed.")
    exit(0)

# ── Convert index to ET ───────────────────────────────────────────────────────
data.index = data.index.tz_convert(ET)

opens  = data["Open"].squeeze().values
highs  = data["High"].squeeze().values
lows   = data["Low"].squeeze().values
closes = data["Close"].squeeze().values
times  = data.index.to_pydatetime()

# ── Derived values ────────────────────────────────────────────────────────────
latest      = float(closes[-1])
open_price  = float(opens[0])
change      = latest - open_price
pct_change  = (change / open_price) * 100
day_low     = float(min(lows))
day_high    = float(max(highs))
is_up       = change >= 0

accent  = "#00FF88" if is_up else "#FF4444"
arrow   = "▲" if is_up else "▼"

# Candle colours
BULL    = "#00FF88"   # close > open
BEAR    = "#FF4444"   # close < open
DOJI    = "#8B949E"   # open == close

# ── Colours ───────────────────────────────────────────────────────────────────
BG       = "#0D1117"
GRID     = "#21262D"
TEXT     = "#E6EDF3"
SUBTEXT  = "#8B949E"
OOH_FILL = "#FFFFFF"  # out-of-hours shading colour

# ── Figure ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 8), facecolor=BG)
ax.set_facecolor(BG)

# ── Out-of-hours shading ──────────────────────────────────────────────────────
# Shade any region before 9:30 or after 16:00
for i, t in enumerate(times):
    t_time = t.time()
    if t_time < MARKET_OPEN or t_time >= MARKET_CLOSE:
        ax.axvspan(
            mdates.date2num(t) - 0.0003,
            mdates.date2num(t) + 0.0003,
            color=OOH_FILL, alpha=0.04, linewidth=0, zorder=0
        )

# Cleaner approach: shade the full pre-market and after-hours blocks
pre_end = None
post_start = None
for t in times:
    if t.time() >= MARKET_OPEN and pre_end is None:
        pre_end = t
    if t.time() >= MARKET_CLOSE and post_start is None:
        post_start = t

if pre_end and times[0] < pre_end:
    ax.axvspan(mdates.date2num(times[0]), mdates.date2num(pre_end),
               color=OOH_FILL, alpha=0.04, zorder=0, linewidth=0)

if post_start:
    ax.axvspan(mdates.date2num(post_start), mdates.date2num(times[-1]),
               color=OOH_FILL, alpha=0.04, zorder=0, linewidth=0)

# ── Candlesticks ──────────────────────────────────────────────────────────────
candle_width = 0.0004   # in matplotlib date units (~seconds fraction)

for i, (t, o, h, l, c) in enumerate(zip(times, opens, highs, lows, closes)):
    x = mdates.date2num(t)

    if c > o:
        color = BULL
    elif c < o:
        color = BEAR
    else:
        color = DOJI

    # Wick (high-low line)
    ax.plot([x, x], [l, h], color=color, linewidth=0.6, zorder=2)

    # Body (open-close rectangle)
    body_bottom = min(o, c)
    body_height = abs(c - o) if abs(c - o) > 0 else 0.2  # doji minimum height
    rect = mpatches.Rectangle(
        (x - candle_width / 2, body_bottom),
        candle_width, body_height,
        facecolor=color, edgecolor=color,
        linewidth=0, zorder=3
    )
    ax.add_patch(rect)

# ── Open price reference line ─────────────────────────────────────────────────
ax.axhline(y=open_price, color=SUBTEXT, linewidth=0.5,
           linestyle="--", alpha=0.4, zorder=1)

# ── Hourly vertical lines ─────────────────────────────────────────────────────
seen_hours = set()
for t in times:
    hour_mark = t.replace(minute=0, second=0, microsecond=0)
    if hour_mark not in seen_hours:
        seen_hours.add(hour_mark)
        ax.axvline(x=mdates.date2num(hour_mark), color=GRID,
                   linewidth=0.7, linestyle="-", alpha=0.8, zorder=1)

# ── Grid ──────────────────────────────────────────────────────────────────────
ax.set_axisbelow(True)
ax.yaxis.grid(True, color=GRID, linewidth=0.4, linestyle="--", alpha=0.6)
ax.xaxis.grid(False)
for spine in ax.spines.values():
    spine.set_visible(False)

# ── Axes formatting ───────────────────────────────────────────────────────────
ax.tick_params(colors=SUBTEXT, labelsize=7.5, length=0)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%-I:%M %p", tz=ET))
ax.xaxis.set_major_locator(mdates.HourLocator(interval=1, tz=ET))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.yaxis.tick_right()
ax.set_xlim(mdates.date2num(times[0]), mdates.date2num(times[-1]))

# Rotate x labels
plt.setp(ax.get_xticklabels(), rotation=0, ha="center")

# ── Header labels ─────────────────────────────────────────────────────────────
today_str = datetime.now(ET).strftime("%b %d, %Y")

fig.text(0.02, 0.93, f"S&P 500  ·  ^GSPC  ·  {today_str}",
         color=TEXT, fontsize=20, fontweight="bold",
         fontfamily="monospace", transform=fig.transFigure)

fig.text(0.02, 0.90,
         f"{latest:,.2f}   {arrow} {abs(change):.2f}  ({abs(pct_change):.2f}%)",
         color=accent, fontsize=12, fontfamily="monospace",
         transform=fig.transFigure)

fig.text(0.02, 0.87,
         f"open {open_price:,.2f}   ·   low {day_low:,.0f}   ·   high {day_high:,.0f}",
         color=SUBTEXT, fontsize=10, fontfamily="monospace",
         transform=fig.transFigure)

# Timestamp bottom-right
ts = datetime.now(ET).strftime("Updated %-I:%M %p ET")
fig.text(0.98, 0.02, ts, color=SUBTEXT, fontsize=6.5,
         fontfamily="monospace", ha="right", transform=fig.transFigure)

# ── Save ──────────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
plt.tight_layout(rect=[0, 0, 1, 0.85])
plt.savefig(OUTPUT_PATH, dpi=200, bbox_inches="tight",
            facecolor=BG, edgecolor="none")
plt.close()

print(f"Chart saved → {OUTPUT_PATH}  |  {latest:,.2f}  {arrow} {pct_change:+.2f}%")