"""
Standalone mud-log side-by-side viewer.
Run:  python view_sbs.py
Opens a self-contained HTML with all tracks in one scrollable row.
"""

import sys, os, webbrowser
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Locate the CSV ──────────────────────────────────────────────────────────
CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "ap-1_explo_mud_log.csv")
OUT_HTML = os.path.join(os.path.dirname(__file__), "mudlog_sbs.html")

sys.path.insert(0, os.path.dirname(__file__))
from parser import parse_mudlog_file
from engine import compute_all

print(f"Reading {CSV_PATH} …")
df_raw = parse_mudlog_file(CSV_PATH)
print(f"  parsed {len(df_raw):,} rows")

df = compute_all(df_raw)
print(f"  computed {len(df.columns)} columns")

# ── Column layout ───────────────────────────────────────────────────────────
column_specs = [
    ("C1",           "C1",         "#38bdf8", "log"),
    ("C2",           "C2",         "#818cf8", "log"),
    ("C3",           "C3",         "#f472b6", "log"),
    ("IC4",          "iC4",        "#fb923c", "log"),
    ("NC4",          "nC4",        "#facc15", "log"),
    ("IC5",          "iC5",        "#34d399", "log"),
    ("NC5",          "nC5",        "#a78bfa", "log"),
    ("TG_USED",      "Total Gas",  "#e2e8f0", "log"),
    ("R1_C1_C2",     "C1/C2",      "#38bdf8", "log"),
    ("R2_C1_C3",     "C1/C3",      "#818cf8", "log"),
    ("R3_C2_C3",     "C2/C3",      "#f472b6", "log"),
    ("R4_C1_IC4",    "C1/iC4",     "#fb923c", "log"),
    ("R5_C1_NC4",    "C1/nC4",     "#facc15", "log"),
    ("WH",           "Wh%",        "#22c55e", "linear"),
    ("BH",           "Bh",         "#f59e0b", "linear"),
    ("CH",           "Ch",         "#ef4444", "linear"),
    ("DRYNESS",      "Dryness",    "#38bdf8", "linear"),
    ("CARBON_INDEX", "Ci",         "#818cf8", "linear"),
    ("WBS",          "WBS",        "#f59e0b", "linear"),
    ("GOW",          "GOW",        "#a78bfa", "log"),
    ("GOW_NOTG",     "GOW/TG",     "#ef4444", "linear"),
    ("GOR",          "GOR",        "#34d399", "linear"),
]

depth = df["DEPTH"].values
active = [(k, t, c, s) for (k, t, c, s) in column_specs if k in df.columns]
has_zone = "ZONE" in df.columns
total_cols = len(active) + (1 if has_zone else 0)

print(f"  building {total_cols} track columns …")

# ── Build subplot figure ────────────────────────────────────────────────────
titles = [t for _, t, _, _ in active] + (["Zone"] if has_zone else [])
col_widths = [130] * len(active) + ([55] if has_zone else [])

fig = make_subplots(
    rows=1,
    cols=total_cols,
    shared_yaxes=True,
    horizontal_spacing=0.003,
    subplot_titles=titles,
    column_widths=col_widths,   # proportional widths
)

GRID_CLR = "rgba(148,163,184,0.18)"
BG       = "#070c18"
CARD_BG  = "#0d1526"

for i, (col_key, title, color, scale_type) in enumerate(active, start=1):
    vals   = df[col_key].replace([np.inf, -np.inf], np.nan).values.astype(float)
    x_plot = np.where(vals > 0, vals, np.nan) if scale_type == "log" else vals

    def rgba(hex_c, a):
        h = hex_c.lstrip("#")
        r, g, b = (int(h[j:j+2], 16) for j in (0, 2, 4))
        return f"rgba({r},{g},{b},{a})"

    fig.add_trace(
        go.Scatter(
            x=x_plot, y=depth, mode="lines", name=title,
            line=dict(color=color, width=1.3),
            fill="tozerox", fillcolor=rgba(color, 0.22),
            showlegend=False,
            hovertemplate=f"Depth: %{{y:.1f}} m<br>{title}: %{{x:.4g}}<extra></extra>",
        ),
        row=1, col=i,
    )
    xname = "xaxis" if i == 1 else f"xaxis{i}"
    fig.update_layout(**{
        xname: dict(
            type="log" if scale_type == "log" else "linear",
            gridcolor=GRID_CLR,
            tickfont=dict(size=7, color="#94a3b8"),
            nticks=3,
            showgrid=True,
            zeroline=False,
        )
    })

# Zone track
ZONE_COLORS = {"Gas": "#22c55e", "Oil": "#f59e0b", "Water": "#38bdf8", "No Show": "#334155"}
if has_zone:
    ci   = total_cols
    zv   = df["ZONE"].values
    znr  = [3 if z=="Gas" else 2 if z=="Oil" else 1 if z=="Water" else 0 for z in zv]
    zclr = [ZONE_COLORS.get(z, ZONE_COLORS["No Show"]) for z in zv]
    fig.add_trace(
        go.Bar(x=znr, y=depth, orientation="h",
               marker=dict(color=zclr),
               hovertext=zv, hoverinfo="text+y",
               showlegend=False, width=0.9),
        row=1, col=ci,
    )
    fig.update_layout(**{f"xaxis{ci}": dict(showticklabels=False, zeroline=False)})

# ── Global layout ───────────────────────────────────────────────────────────
total_depth  = max(depth) - min(depth)
chart_height = max(700, min(int(total_depth * 0.55), 2200))
chart_width  = sum(col_widths) + 80   # pixel total

fig.update_layout(
    height      = chart_height,
    width       = chart_width,
    autosize    = False,
    template    = "plotly_dark",
    paper_bgcolor = BG,
    plot_bgcolor  = "#070c18",
    font        = dict(family="Inter, sans-serif", size=9, color="#e2e8f0"),
    margin      = dict(l=60, r=20, t=60, b=30),
    title       = dict(
        text="<b>Mud Log — Side-by-Side Track View</b>",
        font=dict(size=14, color="#e2e8f0"),
        x=0.01,
    ),
)

for i in range(1, total_cols + 1):
    yk = "yaxis" if i == 1 else f"yaxis{i}"
    fig.update_layout(**{yk: dict(
        autorange="reversed",
        gridcolor=GRID_CLR,
        showgrid=True,
        zeroline=False,
        tickfont=dict(size=8),
    )})

fig.update_yaxes(title_text="Depth (m)", row=1, col=1)

for ann in fig.layout.annotations:
    ann.font = dict(size=9, color="#94a3b8")

# ── Write & open ────────────────────────────────────────────────────────────
print(f"  writing -> {OUT_HTML}")
fig.write_html(
    OUT_HTML,
    full_html=True,
    include_plotlyjs="cdn",
    config={"scrollZoom": True, "responsive": False},
)
print("Done — opening browser …")
webbrowser.open(f"file:///{OUT_HTML.replace(os.sep, '/')}")
