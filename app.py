"""
MudLog Pro — Continuous Multi-Track Depth Log (Dash Python)
===========================================================
Interactive single-page Dash application featuring a clean, full-screen
continuous multi-track well log where every hydrocarbon gas, ratio,
and petrophysical indicator has its own dedicated track column.

Tracks Included:
  • Raw Gases: C1, C2, C3, iC4, nC4, iC5, nC5, Total Gas (TG)
  • Pixler & Gas Ratios: C1/C2 (R1), C1/C3 (R2), C2/C1, C3/C1, C2/C3 (R3), C1/iC4 (R4), C1/nC4 (R5)
  • Haworth Ratios: Wh% (Wetness), Bh (Balance), Ch (Character)
  • Composite Indicators: Dryness, Carbon Index (Ci), WBS, GOW, GOW/TG, GOR
  • Classification: Fluid Zone (Gas, Oil, Water, No Show)

All tracks are engineered to fit 100% within the screen width with zero horizontal scroll.

Run: py app.py
"""

import io
import base64
import webbrowser
import threading
import numpy as np
import pandas as pd

import dash
from dash import dcc, html, no_update
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Local imports
from parser import parse_mudlog_file
from engine import compute_all


# ──────────────────────────────────────────────────────────────────────
#  Theme & Color Palette
# ──────────────────────────────────────────────────────────────────────
CLR_BG       = "#090d16"
CLR_SURFACE  = "#0f172a"
CLR_CARD     = "#111827"
CLR_BORDER   = "rgba(51, 65, 85, 0.5)"
CLR_ACCENT   = "#6366f1"  # Indigo
CLR_CYAN     = "#38bdf8"  # Sky/Cyan
CLR_SUCCESS  = "#10b981"  # Emerald
CLR_WARNING  = "#f59e0b"  # Amber
CLR_DANGER   = "#f43f5e"  # Rose
CLR_TEXT     = "#f1f5f9"  # Slate 100
CLR_MUTED    = "#94a3b8"  # Slate 400
CLR_DARK_MUTED = "#64748b" # Slate 500

ZONE_COLORS = {
    "Gas":     "#10b981",
    "Oil":     "#f43f5e",
    "Water":   "#0284c7",
    "No Show": "#475569",
}

# Complete List of Continuous Multi-Track Specifications (All 24 Indicators)
CONTINUOUS_TRACK_SPECS = [
    # (col_key, title, color, scale_type)
    ("C1",           "C1",        "#38bdf8", "log"),
    ("C2",           "C2",        "#818cf8", "log"),
    ("C3",           "C3",        "#f472b6", "log"),
    ("IC4",          "iC4",       "#fb923c", "log"),
    ("NC4",          "nC4",       "#facc15", "log"),
    ("IC5",          "iC5",       "#34d399", "log"),
    ("NC5",          "nC5",       "#a78bfa", "log"),
    ("TG_USED",      "TG",        "#ffffff", "log"),
    ("R1_C1_C2",     "C1/C2",     "#38bdf8", "log"),
    ("R2_C1_C3",     "C1/C3",     "#818cf8", "log"),
    ("C2_C1",        "C2/C1",     "#38bdf8", "log"),
    ("C3_C1",        "C3/C1",     "#818cf8", "log"),
    ("R3_C2_C3",     "C2/C3",     "#f472b6", "log"),
    ("R4_C1_IC4",    "C1/iC4",    "#fb923c", "log"),
    ("R5_C1_NC4",    "C1/nC4",    "#facc15", "log"),
    ("WH",           "Wh%",       "#22c55e", "linear"),
    ("BH",           "Bh",        "#f59e0b", "linear"),
    ("CH",           "Ch",        "#ef4444", "linear"),
    ("DRYNESS",      "Dryness",   "#38bdf8", "linear"),
    ("CARBON_INDEX", "Ci",        "#818cf8", "linear"),
    ("WBS",          "WBS",       "#f59e0b", "linear"),
    ("GOW",          "GOW",       "#a78bfa", "log"),
    ("GOW_NOTG",     "GOW/TG",    "#ef4444", "linear"),
    ("GOR",          "GOR",       "#34d399", "linear"),
]



# ──────────────────────────────────────────────────────────────────────
#  Mock Dataset Generator (Realistic Gas While Drilling with Payzones)
# ──────────────────────────────────────────────────────────────────────
def generate_initial_mudlog_data():
    """Generates realistic synthetic GWD dataset with target payzones."""
    np.random.seed(42)
    rows = []
    depth = 1800
    for i in range(85):
        depth += 15
        base_gas = np.sin(i / 5.0) * 8000.0 + 12000.0
        is_payzone = (2100 <= depth <= 2450) or (2700 <= depth <= 2880)
        multiplier = 2.8 if is_payzone else 0.6

        c1 = max(10.0, (base_gas * 0.75 + np.random.uniform(0, 1500)) * multiplier)
        c2 = max(1.0, (base_gas * 0.14 + np.random.uniform(0, 400)) * multiplier)
        c3 = max(0.5, (base_gas * 0.07 + np.random.uniform(0, 250)) * multiplier)
        ic4 = max(0.1, (base_gas * 0.02 + np.random.uniform(0, 80)) * multiplier)
        nc4 = max(0.1, (base_gas * 0.015 + np.random.uniform(0, 60)) * multiplier)
        ic5 = max(0.05, (base_gas * 0.003 + np.random.uniform(0, 20)) * multiplier)
        nc5 = max(0.05, (base_gas * 0.002 + np.random.uniform(0, 15)) * multiplier)
        tg = c1 + c2 + c3 + ic4 + nc4 + ic5 + nc5

        rows.append({
            "DEPTH": depth,
            "C1": round(c1, 1),
            "C2": round(c2, 1),
            "C3": round(c3, 1),
            "IC4": round(ic4, 1),
            "NC4": round(nc4, 1),
            "IC5": round(ic5, 1),
            "NC5": round(nc5, 1),
            "TG": round(tg, 1),
        })

    raw_df = pd.DataFrame(rows)
    computed_df = compute_all(raw_df)
    return raw_df, computed_df


INIT_RAW_DF, INIT_COMPUTED_DF = generate_initial_mudlog_data()


# ──────────────────────────────────────────────────────────────────────
#  App Initialisation & External Assets
# ──────────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css",
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap",
    ],
    suppress_callback_exceptions=True,
    title="MudLog Pro — Continuous Depth Track Log",
)

server = app.server

# Custom HTML index template for Dark Glassmorphism, Google Fonts, and Screen-Fitting styles
app.index_string = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
        <style>
            body {
                font-family: 'Inter', sans-serif !important;
                background-color: #090d16 !important;
                color: #f1f5f9 !important;
                margin: 0;
                overflow-x: hidden;
            }
            .glass-card {
                background: rgba(15, 23, 42, 0.8) !important;
                backdrop-filter: blur(12px) !important;
                border: 1px solid rgba(51, 65, 85, 0.5) !important;
                border-radius: 14px !important;
                transition: all 0.2s ease-in-out;
            }
            .glass-card:hover {
                border-color: rgba(99, 102, 241, 0.45) !important;
            }
            /* Scrollbars */
            ::-webkit-scrollbar {
                width: 6px;
                height: 6px;
            }
            ::-webkit-scrollbar-track {
                background: #0f172a;
            }
            ::-webkit-scrollbar-thumb {
                background: #334155;
                border-radius: 4px;
            }
            ::-webkit-scrollbar-thumb:hover {
                background: #475569;
            }
        </style>
    </head>
    <body class="bg-dark text-light">
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""


# ──────────────────────────────────────────────────────────────────────
#  Modal for Uploading Files
# ──────────────────────────────────────────────────────────────────────
upload_modal = dbc.Modal(
    [
        dbc.ModalHeader(
            dbc.ModalTitle(
                html.Div([
                    html.I(className="fas fa-cloud-arrow-up me-2", style={"color": CLR_CYAN}),
                    "Upload Mudlog Data File",
                ]),
                style={"color": CLR_TEXT, "fontSize": "16px", "fontWeight": "700"},
            ),
            close_button=True,
            style={"background": CLR_SURFACE, "borderBottom": f"1px solid {CLR_BORDER}"},
        ),
        dbc.ModalBody([
            html.Div([
                html.Label("Mudlog Well Log Data File", style={"fontWeight": "600", "color": CLR_TEXT, "fontSize": "13px", "marginBottom": "6px", "display": "block"}),
                dcc.Upload(
                    id="upload-data",
                    children=html.Div([
                        html.I(className="fas fa-file-waveform", style={"fontSize": "32px", "color": CLR_CYAN, "marginBottom": "6px"}),
                        html.Br(),
                        html.Span("Drag & Drop or ", style={"color": CLR_MUTED, "fontSize": "13px"}),
                        html.A("Browse File", style={"color": CLR_CYAN, "fontWeight": "600", "cursor": "pointer", "textDecoration": "underline"}),
                        html.Br(),
                        html.Small("Supports .csv, .txt, .xlsx with DEPTH, C1, C2, C3, iC4, nC4, iC5, nC5", style={"color": CLR_DARK_MUTED, "fontSize": "11px"}),
                    ], style={"textAlign": "center", "padding": "26px 16px"}),
                    style={
                        "border": f"2px dashed {CLR_CYAN}",
                        "borderRadius": "12px",
                        "background": CLR_BG,
                        "cursor": "pointer",
                        "marginBottom": "10px",
                    },
                    multiple=False,
                ),
                html.Div(id="upload-status"),
            ]),
        ], style={"background": CLR_SURFACE, "padding": "20px"}),
    ],
    id="upload-modal",
    is_open=False,
    centered=True,
    size="lg",
    style={"backdropFilter": "blur(8px)"},
)


# ──────────────────────────────────────────────────────────────────────
#  Top Navbar
# ──────────────────────────────────────────────────────────────────────
navbar = html.Header(
    html.Div([
        # Brand
        html.Div([
            html.H1(
                "Mudlogging",
                style={
                    "fontSize": "1.25rem",
                    "fontWeight": "800",
                    "letterSpacing": "-0.02em",
                    "color": "#38bdf8",
                    "margin": "0",
                    "textTransform": "capitalize",
                },
            ),
        ], style={"display": "flex", "alignItems": "center"}),

        # Controls (Upload Modal Button + Export CSV)
        html.Div([
            dbc.Button(
                [html.I(className="fa-solid fa-upload me-2"), "Upload File"],
                id="btn-open-upload",
                color="info",
                outline=True,
                size="sm",
                className="me-2 px-3",
                style={"borderRadius": "8px", "fontSize": "12px", "fontWeight": "600", "borderColor": "rgba(56, 189, 248, 0.5)"},
            ),
            dbc.Button(
                [html.I(className="fa-solid fa-download me-2"), "Export CSV"],
                id="btn-export",
                color="primary",
                size="sm",
                className="px-3",
                style={"borderRadius": "8px", "fontSize": "12px", "fontWeight": "600", "background": "#6366f1", "border": "none"},
            ),
        ], style={"display": "flex", "alignItems": "center"}),
    ], className="d-flex align-items-center justify-content-between",
       style={"maxWidth": "100%", "padding": "10px 20px"}),
    style={"background": "rgba(15, 23, 42, 0.95)", "borderBottom": f"1px solid {CLR_BORDER}", "position": "sticky", "top": "0", "zIndex": "100", "backdropFilter": "blur(12px)"},
)


# ──────────────────────────────────────────────────────────────────────
#  App Layout
# ──────────────────────────────────────────────────────────────────────
app.layout = html.Div([
    upload_modal,
    navbar,

    # Main Body Container (Full Width Responsive with Padding)
    html.Div([
        # 1. Legend and Depth Header Bar
        html.Div([
            html.Div([
                html.Span("Fluid Zone Overlay:", style={"fontSize": "11px", "fontWeight": "600", "color": CLR_MUTED, "marginRight": "10px"}),
                html.Span([html.Span(style={"width": "10px", "height": "10px", "borderRadius": "2px", "background": "#10b981", "display": "inline-block", "marginRight": "4px"}), "Gas"], className="me-3", style={"fontSize": "11px", "fontWeight": "600", "color": "#10b981"}),
                html.Span([html.Span(style={"width": "10px", "height": "10px", "borderRadius": "2px", "background": "#f43f5e", "display": "inline-block", "marginRight": "4px"}), "Oil"], className="me-3", style={"fontSize": "11px", "fontWeight": "600", "color": "#f43f5e"}),
                html.Span([html.Span(style={"width": "10px", "height": "10px", "borderRadius": "2px", "background": "#0284c7", "display": "inline-block", "marginRight": "4px"}), "Water"], className="me-3", style={"fontSize": "11px", "fontWeight": "600", "color": "#38bdf8"}),
                html.Span([html.Span(style={"width": "10px", "height": "10px", "borderRadius": "2px", "background": "#475569", "display": "inline-block", "marginRight": "4px"}), "No Show"], style={"fontSize": "11px", "fontWeight": "600", "color": "#94a3b8"}),
            ], className="d-flex align-items-center flex-wrap"),

            html.Div(id="track-header-info", className="d-none d-md-flex align-items-center text-muted", style={"fontSize": "11px"}),
        ], className="glass-card px-3 py-2 mb-2 d-flex align-items-center justify-content-between flex-wrap gap-2"),

        # 2. Dedicated Full-Screen Continuous Multi-Track Well Log
        html.Div(id="tracks-container"),

        # 3. Hidden Data Stores & Download Component
        dcc.Store(id="store-raw", data=INIT_RAW_DF.to_json(orient="split", date_format="iso")),
        dcc.Store(id="store-computed", data=INIT_COMPUTED_DF.to_json(orient="split", date_format="iso")),
        dcc.Download(id="download-report"),

    ], style={"width": "100%", "padding": "10px 18px 30px 18px"}),
], style={"background": CLR_BG, "minHeight": "100vh", "color": CLR_TEXT, "overflowX": "hidden"})


# ──────────────────────────────────────────────────────────────────────
#  Data Filtering Utility
# ──────────────────────────────────────────────────────────────────────
def filter_df_by_depth(df: pd.DataFrame, depth_filter: str) -> pd.DataFrame:
    if df is None or len(df) == 0:
        return df
    if depth_filter == "target":
        return df[(df["DEPTH"] >= 2100) & (df["DEPTH"] <= 2450)].reset_index(drop=True)
    elif depth_filter == "upper":
        return df[df["DEPTH"] < 2100].reset_index(drop=True)
    elif depth_filter == "lower":
        return df[df["DEPTH"] > 2450].reset_index(drop=True)
    return df


# ──────────────────────────────────────────────────────────────────────
#  Header Info Callback
# ──────────────────────────────────────────────────────────────────────
@app.callback(
    Output("track-header-info", "children"),
    [Input("store-computed", "data")]
)
def update_header_info(json_computed):
    if not json_computed:
        return ""
    df = pd.read_json(io.StringIO(json_computed), orient="split")
    d_min = df["DEPTH"].min()
    d_max = df["DEPTH"].max()
    pts = len(df)
    return [
        html.I(className="fa-solid fa-ruler-vertical text-info me-1"),
        f"Depth: {d_min:.0f}m – {d_max:.0f}m ({d_max - d_min:.0f}m span • {pts} intervals) • All 23 individual tracks fitted to screen width",
    ]


# ──────────────────────────────────────────────────────────────────────
#  Full Continuous Multi-Track Well Log Builder (Fits 100% Screen Width)
# ──────────────────────────────────────────────────────────────────────
@app.callback(
    Output("tracks-container", "children"),
    [Input("store-computed", "data")]
)
def render_full_continuous_tracks(json_computed):
    if not json_computed:
        return html.Div("No data loaded.", style={"color": CLR_MUTED, "padding": "40px", "textAlign": "center"})

    df = pd.read_json(io.StringIO(json_computed), orient="split")
    filtered_df = df

    depth = filtered_df["DEPTH"].values
    grid_clr = "rgba(51, 65, 85, 0.22)"
    chart_height = 840

    active_specs = [s for s in CONTINUOUS_TRACK_SPECS if s[0] in filtered_df.columns]
    has_zone = "ZONE" in filtered_df.columns
    total_cols = len(active_specs) + (1 if has_zone else 0)

    if total_cols == 0:
        return html.Div("No valid track data available.", style={"color": CLR_MUTED, "padding": "20px"})

    titles = [s[1] for s in active_specs] + (["Zone"] if has_zone else [])

    # Proportional column widths totaling 1.0 (fitting 100% of the screen width)
    raw_widths = [1.0] * len(active_specs) + ([0.7] if has_zone else [])
    w_sum = sum(raw_widths)
    norm_widths = [w / w_sum for w in raw_widths]

    fig = make_subplots(
        rows=1,
        cols=total_cols,
        shared_yaxes=True,
        horizontal_spacing=0.0035,
        subplot_titles=titles,
        column_widths=norm_widths,
    )

    for i, (col_key, title, color, scale_type) in enumerate(active_specs, start=1):
        vals = filtered_df[col_key].replace([np.inf, -np.inf], np.nan).values.astype(float)
        x_plot = np.where(vals > 0, vals, np.nan) if scale_type == "log" else vals

        fig.add_trace(
            go.Scatter(
                x=x_plot, y=depth, mode="lines", name=title,
                line=dict(color=color, width=1.4),
                fill="tozerox", fillcolor=f"rgba({int(color[1:3],16)}, {int(color[3:5],16)}, {int(color[5:7],16)}, 0.18)",
                showlegend=False,
                hovertemplate=f"Depth: %{{y:.1f}}m<br>{title}: %{{x:.3g}}<extra></extra>",
            ),
            row=1, col=i,
        )
        xname = "xaxis" if i == 1 else f"xaxis{i}"
        fig.update_layout(**{xname: dict(
            type="log" if scale_type == "log" else "linear",
            gridcolor=grid_clr,
            tickfont=dict(size=7, color=CLR_MUTED),
            nticks=3,
            showgrid=True,
            zeroline=False,
        )})

    if has_zone:
        ci = total_cols
        zv = filtered_df["ZONE"].values
        znr = [3 if z == "Gas" else 2 if z == "Oil" else 1 if z == "Water" else 0 for z in zv]
        zclr = [ZONE_COLORS.get(z, ZONE_COLORS["No Show"]) for z in zv]
        fig.add_trace(
            go.Bar(
                x=znr, y=depth, orientation="h",
                marker=dict(color=zclr),
                hovertext=zv, hoverinfo="text+y",
                showlegend=False, width=0.9
            ),
            row=1, col=ci,
        )
        fig.update_layout(**{f"xaxis{ci}": dict(showticklabels=False, zeroline=False, gridcolor=grid_clr)})

    # Invert Y-axis for well depth on all subplots
    fig.update_yaxes(autorange="reversed", gridcolor=grid_clr, title_text="Depth (m)", row=1, col=1, tickfont=dict(size=8.5, color=CLR_TEXT))
    for c_idx in range(2, total_cols + 1):
        fig.update_layout(**{f"yaxis{c_idx}": dict(autorange="reversed", gridcolor=grid_clr, showgrid=True, zeroline=False, tickfont=dict(size=7.5, color=CLR_MUTED))})

    fig.update_layout(
        height=chart_height,
        autosize=True,
        template="plotly_dark",
        paper_bgcolor=CLR_BG,
        plot_bgcolor="#070c18",
        font=dict(family="Inter, sans-serif", size=8.5, color=CLR_TEXT),
        margin=dict(l=55, r=15, t=40, b=25),
        hovermode="y unified",
    )

    for ann in fig.layout.annotations:
        ann.font = dict(size=9.5, color="#818cf8", family="Inter, sans-serif", weight="bold")

    return html.Div([
        dcc.Graph(
            figure=fig,
            responsive=True,
            config={"scrollZoom": True, "displayModeBar": True},
            style={"width": "100%", "height": f"{chart_height}px"},
        ),
    ], className="glass-card p-3")


# ──────────────────────────────────────────────────────────────────────
#  Callbacks: Upload Modal & File Parsing
# ──────────────────────────────────────────────────────────────────────
@app.callback(
    Output("upload-modal", "is_open"),
    [Input("btn-open-upload", "n_clicks")],
    [State("upload-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_upload_modal(n_clicks, is_open):
    return not is_open


@app.callback(
    [Output("store-raw", "data"),
     Output("store-computed", "data"),
     Output("upload-status", "children"),
     Output("upload-modal", "is_open", allow_duplicate=True)],
    [Input("upload-data", "contents")],
    [State("upload-data", "filename")],
    prevent_initial_call=True
)
def handle_mudlog_upload(contents, filename):
    if not contents:
        return no_update, no_update, no_update, no_update

    try:
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)

        if filename.lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(decoded))
            df.columns = [str(c).strip().upper() for c in df.columns]
        else:
            text = decoded.decode("utf-8", errors="ignore")
            buf = io.StringIO(text)
            df = parse_mudlog_file(buf)

        if "DEPTH" not in df.columns:
            for alias in ["DEP", "DEPTH_M", "DEPT"]:
                if alias in df.columns:
                    df = df.rename(columns={alias: "DEPTH"})
                    break

        required = ["DEPTH", "C1", "C2", "C3", "IC4", "NC4", "IC5", "NC5"]
        for c in required:
            if c not in df.columns:
                df[c] = 0.0
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

        if "TG" in df.columns:
            df["TG"] = pd.to_numeric(df["TG"], errors="coerce").fillna(0.0)

        df = df.sort_values("DEPTH").reset_index(drop=True)
        computed_df = compute_all(df)

        status_msg = dbc.Alert(f"✅ Successfully loaded {filename} ({len(df)} depth intervals).", color="success", style={"fontSize": "12px", "borderRadius": "8px"})

        return (
            df.to_json(orient="split", date_format="iso"),
            computed_df.to_json(orient="split", date_format="iso"),
            status_msg,
            False
        )
    except Exception as e:
        status_msg = dbc.Alert(f"❌ Error loading file: {str(e)}", color="danger", style={"fontSize": "12px", "borderRadius": "8px"})
        return no_update, no_update, status_msg, no_update


# ──────────────────────────────────────────────────────────────────────
#  Callback: Export CSV Report
# ──────────────────────────────────────────────────────────────────────
@app.callback(
    Output("download-report", "data"),
    [Input("btn-export", "n_clicks")],
    [State("store-computed", "data")],
    prevent_initial_call=True
)
def export_csv_report(n_clicks, json_computed):
    if not n_clicks or not json_computed:
        return no_update

    df = pd.read_json(io.StringIO(json_computed), orient="split")
    return dcc.send_data_frame(df.to_csv, "mudlog_depth_track_report.csv", index=False)


# ──────────────────────────────────────────────────────────────────────
#  Entry Point
# ──────────────────────────────────────────────────────────────────────
def open_browser():
    """Auto open browser on startup."""
    import time
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:8051")


if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(debug=False, port=8051)
