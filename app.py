"""
Mudlogging Hydrocarbon Analysis — Desktop Application
=====================================================
Single-page Dash dashboard for Gas While Drilling (GWD) analysis.

Features:
  • Drag-and-drop CSV/TXT/XLSX upload via modal
  • Optional ground-truth CSV upload for evaluation
  • Automatic data parsing & cleaning
  • 16 petrophysical indicator computations
  • Interactive Plotly depth-log charts (5 tracks)
  • Majority-vote zone classification with colour overlay (Gas/Oil/Water/No Show)
  • Evaluation metrics: confusion matrix, accuracy, precision, recall, F1-Score
  • One-click CSV report download
  • Toggle between Raw Data and Computed Data views

Run:  python app.py
Build: pyinstaller --onefile --noconsole app.py
"""

import io
import base64
import webbrowser
import threading
import sys
import os

import pandas as pd
import numpy as np
import dash
from dash import dcc, html, dash_table, callback_context, no_update
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Local imports
from parser import parse_mudlog_file
from engine import compute_all
from evaluator import compute_evaluation


# ──────────────────────────────────────────────────────────────────────
#  App initialisation
# ──────────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
    title="MudLog Analyzer v1.0",
)

# Colour palette
CLR_BG       = "#0b0f19"
CLR_CARD     = "#111827"
CLR_ACCENT   = "#38bdf8"
CLR_ACCENT2  = "#818cf8"
CLR_TEXT     = "#e2e8f0"
CLR_MUTED    = "#64748b"
CLR_SUCCESS  = "#22c55e"
CLR_WARNING  = "#f59e0b"
CLR_DANGER   = "#ef4444"

ZONE_COLORS = {
    "Gas":     "#22c55e",
    "Oil":     "#ef4444",
    "Water":   "#3b82f6",
    "No Show": "#374151",
}


# ──────────────────────────────────────────────────────────────────────
#  Layout
# ──────────────────────────────────────────────────────────────────────

upload_modal = dbc.Modal(
    [
        dbc.ModalHeader(
            dbc.ModalTitle("Upload Files", style={"color": CLR_ACCENT}),
            close_button=True,
        ),
        dbc.ModalBody([
            # ─── Mudlog file upload ───
            html.Label("Mudlog Data File", style={"fontWeight": "600", "color": CLR_TEXT,
                                                   "marginBottom": "8px", "display": "block"}),
            dcc.Upload(
                id="upload-data",
                children=html.Div([
                    html.I(className="fas fa-cloud-upload-alt",
                           style={"fontSize": "40px", "color": CLR_ACCENT, "marginBottom": "8px"}),
                    html.Br(),
                    html.Span("Drag & Drop or ", style={"color": CLR_MUTED}),
                    html.A("Browse Files", style={"color": CLR_ACCENT, "cursor": "pointer",
                                                   "textDecoration": "underline"}),
                    html.Br(),
                    html.Small("Supports .csv, .txt, .xlsx", style={"color": CLR_MUTED}),
                ], style={"textAlign": "center", "padding": "30px 20px"}),
                style={
                    "border": f"2px dashed {CLR_ACCENT}",
                    "borderRadius": "12px",
                    "background": CLR_BG,
                    "cursor": "pointer",
                },
                multiple=False,
            ),
            html.Div(id="upload-status", style={"marginTop": "12px", "textAlign": "center"}),

            html.Hr(style={"borderColor": f"{CLR_MUTED}33", "margin": "20px 0"}),

            # ─── Ground truth file upload ───
            html.Label("Ground Truth File (Optional)",
                       style={"fontWeight": "600", "color": CLR_TEXT,
                              "marginBottom": "4px", "display": "block"}),
            html.Small("CSV with DEPTH and ZONE columns (Gas / Oil / Water). "
                       "Used to compute accuracy metrics.",
                       style={"color": CLR_MUTED, "display": "block", "marginBottom": "8px"}),
            dcc.Upload(
                id="upload-truth",
                children=html.Div([
                    html.I(className="fas fa-check-circle",
                           style={"fontSize": "32px", "color": CLR_SUCCESS, "marginBottom": "6px"}),
                    html.Br(),
                    html.Span("Drag & Drop or ", style={"color": CLR_MUTED}),
                    html.A("Browse", style={"color": CLR_SUCCESS, "cursor": "pointer",
                                            "textDecoration": "underline"}),
                    html.Br(),
                    html.Small(".csv format", style={"color": CLR_MUTED}),
                ], style={"textAlign": "center", "padding": "20px"}),
                style={
                    "border": f"2px dashed {CLR_SUCCESS}66",
                    "borderRadius": "12px",
                    "background": CLR_BG,
                    "cursor": "pointer",
                },
                multiple=False,
            ),
            html.Div(id="truth-upload-status", style={"marginTop": "12px", "textAlign": "center"}),
        ]),
    ],
    id="upload-modal",
    is_open=False,
    centered=True,
    size="lg",
    style={"backdropFilter": "blur(8px)"},
)

navbar = dbc.Navbar(
    dbc.Container([
        dbc.Row([
            dbc.Col(
                html.Div([
                    html.Span("⛽", style={"fontSize": "28px", "marginRight": "10px"}),
                    html.Span("MudLog", style={"fontWeight": "800", "fontSize": "22px",
                                                "color": CLR_TEXT}),
                    html.Span("Analyzer", style={"fontWeight": "300", "fontSize": "22px",
                                                  "color": CLR_ACCENT}),
                    html.Span(" v1.0", style={"fontWeight": "300", "fontSize": "14px",
                                               "color": CLR_MUTED, "marginLeft": "6px",
                                               "alignSelf": "flex-end", "paddingBottom": "2px"}),
                ], style={"display": "flex", "alignItems": "center"}),
                width="auto",
            ),
            dbc.Col(
                html.Div([
                    dbc.Button(
                        [html.I(className="fas fa-upload", style={"marginRight": "8px"}),
                         "Upload"],
                        id="btn-open-upload",
                        color="info",
                        outline=True,
                        size="sm",
                        className="me-2",
                        style={"borderRadius": "8px"},
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-play", style={"marginRight": "8px"}),
                         "Run Analysis"],
                        id="btn-run",
                        color="success",
                        size="sm",
                        className="me-2",
                        disabled=True,
                        style={"borderRadius": "8px"},
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-download", style={"marginRight": "8px"}),
                         "Export Report"],
                        id="btn-export",
                        color="warning",
                        outline=True,
                        size="sm",
                        disabled=True,
                        style={"borderRadius": "8px"},
                    ),
                ], style={"display": "flex", "alignItems": "center"}),
                width="auto",
            ),
        ], align="center", className="g-0 w-100", justify="between"),
    ], fluid=True),
    color=CLR_CARD,
    dark=True,
    style={"borderBottom": f"1px solid {CLR_MUTED}33", "padding": "10px 0"},
)

stats_row = dbc.Row(id="stats-row", className="g-3 mb-3", style={"display": "none"})

# ─── Data table with toggle button ───
data_table_card = dbc.Card(
    [
        dbc.CardHeader(
            html.Div([
                html.Div([
                    html.Span("📊 Data Preview",
                              style={"fontWeight": "600", "color": CLR_TEXT}),
                    html.Small(id="row-count-badge",
                               style={"marginLeft": "12px", "color": CLR_ACCENT}),
                ]),
                dbc.Button(
                    "Show Computed",
                    id="btn-toggle-table",
                    color="info",
                    outline=True,
                    size="sm",
                    disabled=True,
                    style={"borderRadius": "8px", "fontSize": "12px"},
                ),
            ], style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"}),
            style={"background": CLR_CARD, "borderBottom": f"1px solid {CLR_MUTED}33"},
        ),
        dbc.CardBody(
            html.Div(id="data-table-container",
                     children=html.P("Upload a file to see data preview.",
                                     style={"color": CLR_MUTED, "textAlign": "center",
                                            "padding": "40px"})),
            style={"background": CLR_BG, "padding": "0", "maxHeight": "400px",
                    "overflowY": "auto"},
        ),
    ],
    style={"background": CLR_CARD, "border": f"1px solid {CLR_MUTED}22",
           "borderRadius": "12px", "marginBottom": "16px"},
)

charts_area = html.Div(
    id="charts-container",
    children=html.Div([
        html.Div(style={"height": "200px"}),
        html.P("⛏️", style={"fontSize": "64px", "textAlign": "center", "margin": "0"}),
        html.H4("Ready to Analyze", style={"textAlign": "center", "color": CLR_TEXT,
                                            "fontWeight": "300"}),
        html.P("Upload a mudlogging CSV file and click 'Run Analysis' to begin.",
               style={"textAlign": "center", "color": CLR_MUTED, "maxWidth": "400px",
                       "margin": "12px auto"}),
    ]),
)

# ─── Evaluation results area ───
eval_area = html.Div(id="eval-container", children=[], style={"marginTop": "24px"})

app.layout = html.Div([
    # Font Awesome for icons
    html.Link(
        rel="stylesheet",
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css",
    ),
    # Google Font
    html.Link(
        rel="stylesheet",
        href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap",
    ),

    upload_modal,
    navbar,

    dbc.Container([
        html.Div(style={"height": "20px"}),
        stats_row,
        data_table_card,
        charts_area,
        eval_area,
        dcc.Download(id="download-report"),
    ], fluid=True, style={"padding": "0 24px 40px 24px"}),

    # Hidden stores
    dcc.Store(id="store-parsed",   data=None),
    dcc.Store(id="store-computed", data=None),
    dcc.Store(id="store-truth",    data=None),
    dcc.Store(id="store-table-mode", data="raw"),  # "raw" or "computed"

], style={
    "background": CLR_BG,
    "minHeight": "100vh",
    "fontFamily": "'Inter', sans-serif",
    "color": CLR_TEXT,
})


# ──────────────────────────────────────────────────────────────────────
#  Callbacks
# ──────────────────────────────────────────────────────────────────────

# --- Toggle upload modal ---
@app.callback(
    Output("upload-modal", "is_open"),
    [Input("btn-open-upload", "n_clicks")],
    [State("upload-modal", "is_open")],
    prevent_initial_call=True,
)
def toggle_modal(n, is_open):
    return not is_open


# --- Parse uploaded mudlog file ---
@app.callback(
    [Output("store-parsed", "data"),
     Output("upload-status", "children"),
     Output("btn-run", "disabled"),
     Output("upload-modal", "is_open", allow_duplicate=True)],
    [Input("upload-data", "contents")],
    [State("upload-data", "filename")],
    prevent_initial_call=True,
)
def parse_upload(contents, filename):
    if contents is None:
        return no_update, no_update, no_update, no_update

    try:
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)

        if filename.lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(decoded))
            # Apply same cleaning as parser
            df.columns = [str(c).strip().upper() for c in df.columns]
        else:
            text = decoded.decode("utf-8", errors="ignore")
            buf = io.StringIO(text)
            df = parse_mudlog_file(buf)

        # If parser wasn't used (xlsx), do minimal cleaning
        if 'DEPTH' not in df.columns:
            col_map = {'DEP': 'DEPTH', 'DEPTH_M': 'DEPTH'}
            df = df.rename(columns=col_map)

        required = ['DEPTH', 'C1', 'C2', 'C3', 'IC4', 'NC4', 'IC5', 'NC5']
        for c in required:
            if c not in df.columns:
                df[c] = 0.0

        for c in required:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0)
        if 'TG' in df.columns:
            df['TG'] = pd.to_numeric(df['TG'], errors='coerce').fillna(0.0)

        df = df.sort_values('DEPTH').reset_index(drop=True)

        status = dbc.Alert(
            f"✅ Loaded {filename} — {len(df)} depth rows",
            color="success",
            style={"borderRadius": "8px"},
        )
        return df.to_json(date_format="iso", orient="split"), status, False, False

    except Exception as e:
        status = dbc.Alert(
            f"❌ Error: {str(e)}", color="danger", style={"borderRadius": "8px"}
        )
        return no_update, status, True, no_update


# --- Parse uploaded ground truth file ---
@app.callback(
    [Output("store-truth", "data"),
     Output("truth-upload-status", "children")],
    [Input("upload-truth", "contents")],
    [State("upload-truth", "filename")],
    prevent_initial_call=True,
)
def parse_truth(contents, filename):
    if contents is None:
        return no_update, no_update

    try:
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        text = decoded.decode("utf-8", errors="ignore")
        df = pd.read_csv(io.StringIO(text))

        df.columns = [str(c).strip().upper() for c in df.columns]

        if 'DEPTH' not in df.columns or 'ZONE' not in df.columns:
            raise ValueError("Ground truth CSV must have 'DEPTH' and 'ZONE' columns.")

        df['DEPTH'] = pd.to_numeric(df['DEPTH'], errors='coerce')
        df = df.dropna(subset=['DEPTH']).reset_index(drop=True)

        # Normalise zone labels
        zone_map = {
            'GAS': 'Gas', 'OIL': 'Oil', 'WATER': 'Water',
            'NO SHOW': 'No Show', 'NOSHOW': 'No Show',
            'NO_SHOW': 'No Show', 'DRY': 'No Show',
        }
        df['ZONE'] = df['ZONE'].str.strip().str.upper().map(zone_map).fillna('No Show')
        df = df.sort_values('DEPTH').reset_index(drop=True)

        status = dbc.Alert(
            f"✅ Ground truth: {filename} — {len(df)} labelled intervals",
            color="success",
            style={"borderRadius": "8px"},
        )
        return df.to_json(date_format="iso", orient="split"), status

    except Exception as e:
        status = dbc.Alert(
            f"❌ Error: {str(e)}", color="danger", style={"borderRadius": "8px"}
        )
        return no_update, status


# --- Show data preview + stats ---
@app.callback(
    [Output("data-table-container", "children"),
     Output("row-count-badge", "children"),
     Output("stats-row", "children"),
     Output("stats-row", "style")],
    [Input("store-parsed", "data"),
     Input("store-computed", "data"),
     Input("btn-toggle-table", "n_clicks")],
    [State("store-table-mode", "data")],
    prevent_initial_call=True,
)
def show_preview(json_raw, json_computed, toggle_clicks, table_mode):
    ctx = callback_context
    triggered = ctx.triggered[0]["prop_id"] if ctx.triggered else ""

    # Determine which data to show
    if "btn-toggle-table" in triggered and json_computed is not None:
        # Toggle between raw and computed
        if table_mode == "raw":
            show_computed = True
        else:
            show_computed = False
    elif json_computed is not None and "store-computed" in triggered:
        show_computed = True
    else:
        show_computed = False

    if show_computed and json_computed is not None:
        df_display = pd.read_json(io.StringIO(json_computed), orient="split")
        badge_prefix = "Computed • "
    elif json_raw is not None:
        df_display = pd.read_json(io.StringIO(json_raw), orient="split")
        badge_prefix = "Raw • "
    else:
        return no_update, no_update, no_update, no_update

    # Stats cards (from raw data)
    df_raw = pd.read_json(io.StringIO(json_raw), orient="split") if json_raw else df_display
    depth_min = df_raw['DEPTH'].min()
    depth_max = df_raw['DEPTH'].max()
    c1_max    = df_raw['C1'].max()
    has_heavy = (df_raw[['C2', 'C3', 'IC4', 'NC4', 'IC5', 'NC5']].sum().sum()) > 0

    stats = [
        _stat_card("Depth Range", f"{depth_min:.0f} – {depth_max:.0f} m", "fas fa-ruler-vertical", CLR_ACCENT),
        _stat_card("Data Points", f"{len(df_raw):,}", "fas fa-database", CLR_ACCENT2),
        _stat_card("Peak C1", f"{c1_max:,.0f} ppm", "fas fa-fire", CLR_WARNING),
        _stat_card("Heavy Gases", "Present" if has_heavy else "None detected",
                   "fas fa-flask", CLR_SUCCESS if has_heavy else CLR_MUTED),
    ]

    # Determine columns to show
    if show_computed:
        display_cols = [c for c in df_display.columns if c != 'index']
    else:
        display_cols = [c for c in ['DEPTH', 'C1', 'C2', 'C3', 'IC4', 'NC4', 'IC5', 'NC5', 'TG']
                        if c in df_display.columns]

    preview = df_display[display_cols].head(50).round(4)

    table = dash_table.DataTable(
        data=preview.to_dict("records"),
        columns=[{"name": c, "id": c} for c in display_cols],
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": CLR_CARD,
            "color": CLR_ACCENT,
            "fontWeight": "600",
            "border": f"1px solid {CLR_MUTED}33",
            "fontSize": "12px",
            "whiteSpace": "nowrap",
        },
        style_cell={
            "backgroundColor": CLR_BG,
            "color": CLR_TEXT,
            "border": f"1px solid {CLR_MUTED}22",
            "padding": "6px 10px",
            "fontSize": "12px",
            "fontFamily": "'Inter', monospace",
            "maxWidth": "120px",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#0f172a"},
        ],
        page_size=50,
    )

    return table, f"{badge_prefix}{len(df_display):,} rows", stats, {"display": "flex"}


# --- Toggle table mode store ---
@app.callback(
    [Output("store-table-mode", "data"),
     Output("btn-toggle-table", "children"),
     Output("btn-toggle-table", "disabled")],
    [Input("btn-toggle-table", "n_clicks"),
     Input("store-computed", "data")],
    [State("store-table-mode", "data")],
    prevent_initial_call=True,
)
def toggle_table_mode(n_clicks, computed_data, current_mode):
    ctx = callback_context
    triggered = ctx.triggered[0]["prop_id"] if ctx.triggered else ""

    if "store-computed" in triggered and computed_data is not None:
        # Enable button when computed data arrives
        return "raw", "Show Computed", False

    if "btn-toggle-table" in triggered:
        if current_mode == "raw":
            return "computed", "Show Raw Data", False
        else:
            return "raw", "Show Computed", False

    return no_update, no_update, no_update


def _stat_card(label, value, icon, color):
    return dbc.Col(
        dbc.Card(
            dbc.CardBody(
                html.Div([
                    html.Div([
                        html.I(className=icon, style={"fontSize": "20px", "color": color}),
                    ], style={"marginBottom": "8px"}),
                    html.P(value, style={"fontSize": "20px", "fontWeight": "700",
                                         "color": CLR_TEXT, "margin": "0", "lineHeight": "1.2"}),
                    html.Small(label, style={"color": CLR_MUTED, "fontSize": "12px"}),
                ]),
                style={"padding": "16px"},
            ),
            style={
                "background": CLR_CARD,
                "border": f"1px solid {CLR_MUTED}22",
                "borderRadius": "12px",
                "borderLeft": f"3px solid {color}",
            },
        ),
        xs=12, sm=6, md=3,
    )


# --- Run analysis ---
@app.callback(
    [Output("store-computed", "data"),
     Output("charts-container", "children"),
     Output("btn-export", "disabled")],
    [Input("btn-run", "n_clicks")],
    [State("store-parsed", "data")],
    prevent_initial_call=True,
)
def run_analysis(n_clicks, json_data):
    if not n_clicks or json_data is None:
        return no_update, no_update, no_update

    df = pd.read_json(io.StringIO(json_data), orient="split")
    computed = compute_all(df)

    # Build charts
    charts = _build_log_charts(computed)

    return computed.to_json(date_format="iso", orient="split"), charts, False


# --- Evaluation panel ---
@app.callback(
    Output("eval-container", "children"),
    [Input("store-computed", "data")],
    [State("store-truth", "data")],
    prevent_initial_call=True,
)
def show_evaluation(json_computed, json_truth):
    if json_computed is None or json_truth is None:
        return []

    computed_df = pd.read_json(io.StringIO(json_computed), orient="split")
    truth_df = pd.read_json(io.StringIO(json_truth), orient="split")

    results = compute_evaluation(computed_df, truth_df)

    if results['matched_count'] == 0:
        return dbc.Alert(
            "⚠️ No depth intervals matched between predictions and ground truth. "
            "Ensure both files share overlapping DEPTH values.",
            color="warning",
            style={"borderRadius": "12px", "marginTop": "16px"},
        )

    return _build_eval_panel(results)


# --- Export CSV ---
@app.callback(
    Output("download-report", "data"),
    [Input("btn-export", "n_clicks")],
    [State("store-computed", "data")],
    prevent_initial_call=True,
)
def export_report(n_clicks, json_data):
    if not n_clicks or json_data is None:
        return no_update

    df = pd.read_json(io.StringIO(json_data), orient="split")
    return dcc.send_data_frame(df.to_csv, "mudlog_analysis_report.csv", index=False)


# ──────────────────────────────────────────────────────────────────────
#  Chart builder
# ──────────────────────────────────────────────────────────────────────

def _build_log_charts(df):
    """Creates the 5-track well-log style chart."""
    depth = df['DEPTH'].values

    fig = make_subplots(
        rows=1, cols=5,
        shared_yaxes=True,
        horizontal_spacing=0.02,
        column_widths=[0.25, 0.2, 0.2, 0.2, 0.15],
        subplot_titles=[
            "Raw Gas Components",
            "Pixler Ratios",
            "Haworth Ratios",
            "Composite Indicators",
            "Zone Classification",
        ],
    )

    # ── Track 1: Raw gases ──
    gas_traces = [
        ("C1",  "#38bdf8", "C1 (Methane)"),
        ("C2",  "#818cf8", "C2 (Ethane)"),
        ("C3",  "#f472b6", "C3 (Propane)"),
        ("IC4", "#fb923c", "iC4"),
        ("NC4", "#facc15", "nC4"),
        ("IC5", "#34d399", "iC5"),
        ("NC5", "#a78bfa", "nC5"),
    ]
    for col, color, name in gas_traces:
        vals = df[col].values
        if np.nanmax(vals) > 0 if len(vals) > 0 else False:
            fig.add_trace(
                go.Scatter(x=vals, y=depth, mode="lines", name=name,
                           line=dict(color=color, width=1.2),
                           fill="tozerox", fillcolor=color + "15"),
                row=1, col=1,
            )

    # Also add TG_USED as a thicker overlay
    fig.add_trace(
        go.Scatter(x=df['TG_USED'].values, y=depth, mode="lines",
                   name="TG (used)", line=dict(color="#e2e8f0", width=2, dash="dot")),
        row=1, col=1,
    )

    # ── Track 2: Pixler Ratios ──
    pixler_traces = [
        ("R1_C1_C2",  "#38bdf8", "C1/C2"),
        ("R2_C1_C3",  "#818cf8", "C1/C3"),
        ("R3_C2_C3",  "#f472b6", "C2/C3"),
    ]
    for col, color, name in pixler_traces:
        vals = df[col].replace([np.inf, -np.inf], np.nan).values
        fig.add_trace(
            go.Scatter(x=vals, y=depth, mode="lines", name=name,
                       line=dict(color=color, width=1.5)),
            row=1, col=2,
        )

    # ── Track 3: Haworth Ratios ──
    haworth_traces = [
        ("WH", "#22c55e", "Wetness (Wh%)"),
        ("BH", "#f59e0b", "Balance (Bh)"),
        ("CH", "#ef4444", "Character (Ch)"),
    ]
    for col, color, name in haworth_traces:
        vals = df[col].replace([np.inf, -np.inf], np.nan).values
        fig.add_trace(
            go.Scatter(x=vals, y=depth, mode="lines", name=name,
                       line=dict(color=color, width=1.5)),
            row=1, col=3,
        )

    # ── Track 4: Composite Indicators ──
    composite_traces = [
        ("DRYNESS",      "#38bdf8", "Dryness"),
        ("CARBON_INDEX", "#818cf8", "Carbon Index"),
        ("WBS",          "#f59e0b", "WBS"),
        ("GOW_NOTG",     "#ef4444", "GOW/TG"),
    ]
    for col, color, name in composite_traces:
        vals = df[col].replace([np.inf, -np.inf], np.nan).values
        fig.add_trace(
            go.Scatter(x=vals, y=depth, mode="lines", name=name,
                       line=dict(color=color, width=1.5)),
            row=1, col=4,
        )

    # ── Track 5: Zone classification colour band ──
    zone_vals = df['ZONE'].values
    zone_numeric = []
    zone_colors_list = []
    for z in zone_vals:
        if z == "Gas":
            zone_numeric.append(3)
            zone_colors_list.append(ZONE_COLORS["Gas"])
        elif z == "Oil":
            zone_numeric.append(2)
            zone_colors_list.append(ZONE_COLORS["Oil"])
        elif z == "Water":
            zone_numeric.append(1)
            zone_colors_list.append(ZONE_COLORS["Water"])
        else:
            zone_numeric.append(0)
            zone_colors_list.append(ZONE_COLORS["No Show"])

    # Use bar chart for zone bands
    fig.add_trace(
        go.Bar(
            x=zone_numeric,
            y=depth,
            orientation="h",
            marker=dict(color=zone_colors_list),
            name="Zone",
            hovertext=zone_vals,
            hoverinfo="text+y",
            showlegend=False,
            width=0.8,
        ),
        row=1, col=5,
    )

    # ── Layout styling ──
    total_depth = max(depth) - min(depth) if len(depth) > 1 else 100
    chart_height = max(800, int(total_depth * 0.6))
    chart_height = min(chart_height, 3000)

    fig.update_layout(
        height=chart_height,
        template="plotly_dark",
        paper_bgcolor=CLR_BG,
        plot_bgcolor="#0f172a",
        font=dict(family="Inter, sans-serif", size=11, color=CLR_TEXT),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=10),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=60, r=20, t=80, b=40),
    )

    # Invert Y-axis (depth increases downward) on all subplots
    for i in range(1, 6):
        yaxis = f"yaxis{i}" if i > 1 else "yaxis"
        fig.update_layout(**{yaxis: dict(autorange="reversed")})

    # Clean up x-axis labels
    fig.update_xaxes(title_text="PPM", row=1, col=1, type="log",
                     gridcolor=f"{CLR_MUTED}22")
    fig.update_xaxes(title_text="Ratio", row=1, col=2, type="log",
                     gridcolor=f"{CLR_MUTED}22")
    fig.update_xaxes(title_text="Value", row=1, col=3, type="log",
                     gridcolor=f"{CLR_MUTED}22")
    fig.update_xaxes(title_text="Value", row=1, col=4,
                     gridcolor=f"{CLR_MUTED}22")
    fig.update_xaxes(title_text="Zone", row=1, col=5,
                     showticklabels=False, gridcolor=f"{CLR_MUTED}22")

    fig.update_yaxes(title_text="Depth (m)", row=1, col=1,
                     gridcolor=f"{CLR_MUTED}22")

    # Add annotations for subplot titles (restyle)
    for ann in fig.layout.annotations:
        ann.font = dict(size=13, color=CLR_ACCENT, family="Inter, sans-serif")

    # Zone legend card
    zone_legend = html.Div([
        html.Div([
            html.Div(style={"width": "14px", "height": "14px", "borderRadius": "3px",
                            "backgroundColor": ZONE_COLORS["Gas"], "display": "inline-block",
                            "marginRight": "6px", "verticalAlign": "middle"}),
            html.Span("Gas", style={"fontSize": "12px", "marginRight": "16px"}),
            html.Div(style={"width": "14px", "height": "14px", "borderRadius": "3px",
                            "backgroundColor": ZONE_COLORS["Oil"], "display": "inline-block",
                            "marginRight": "6px", "verticalAlign": "middle"}),
            html.Span("Oil", style={"fontSize": "12px", "marginRight": "16px"}),
            html.Div(style={"width": "14px", "height": "14px", "borderRadius": "3px",
                            "backgroundColor": ZONE_COLORS["Water"], "display": "inline-block",
                            "marginRight": "6px", "verticalAlign": "middle"}),
            html.Span("Water", style={"fontSize": "12px", "marginRight": "16px"}),
            html.Div(style={"width": "14px", "height": "14px", "borderRadius": "3px",
                            "backgroundColor": ZONE_COLORS["No Show"], "display": "inline-block",
                            "marginRight": "6px", "verticalAlign": "middle"}),
            html.Span("No Show", style={"fontSize": "12px"}),
        ], style={"display": "flex", "alignItems": "center", "justifyContent": "center",
                  "padding": "12px", "background": CLR_CARD, "borderRadius": "8px",
                  "border": f"1px solid {CLR_MUTED}22", "marginBottom": "12px"}),
    ])

    # Zone summary stats
    zone_counts = pd.Series(zone_vals).value_counts()
    summary_items = []
    for zone_name in ["Gas", "Oil", "Water", "No Show"]:
        count = zone_counts.get(zone_name, 0)
        pct = (count / len(zone_vals) * 100) if len(zone_vals) > 0 else 0
        if count > 0:
            summary_items.append(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.Div(style={
                                "width": "8px", "height": "8px", "borderRadius": "50%",
                                "backgroundColor": ZONE_COLORS.get(zone_name, CLR_MUTED),
                                "display": "inline-block", "marginRight": "8px",
                            }),
                            html.Span(f"{zone_name}: ", style={"fontWeight": "600", "fontSize": "14px"}),
                            html.Span(f"{count} intervals ({pct:.1f}%)",
                                      style={"color": CLR_MUTED, "fontSize": "13px"}),
                        ], style={"padding": "10px 16px"}),
                        style={"background": CLR_CARD, "border": f"1px solid {CLR_MUTED}22",
                               "borderRadius": "8px"},
                    ),
                    width="auto",
                )
            )

    return html.Div([
        zone_legend,
        dbc.Row(summary_items, className="g-2 mb-3", justify="center"),
        dcc.Graph(figure=fig, config={"scrollZoom": True, "displayModeBar": True},
                  style={"borderRadius": "12px", "overflow": "hidden"}),
    ])


# ──────────────────────────────────────────────────────────────────────
#  Evaluation panel builder
# ──────────────────────────────────────────────────────────────────────

def _build_eval_panel(results):
    """Builds the evaluation metrics UI: confusion matrix heatmap + metrics cards."""

    labels = results['labels']
    cm = results['confusion_matrix']

    # ─── Confusion Matrix Heatmap ───
    # Annotate cells with counts
    annotations = []
    for i in range(len(labels)):
        for j in range(len(labels)):
            annotations.append(
                dict(
                    x=labels[j], y=labels[i],
                    text=str(cm[i][j]),
                    showarrow=False,
                    font=dict(color="white" if cm[i][j] > cm.max() * 0.5 else CLR_TEXT,
                              size=16, family="Inter, sans-serif"),
                )
            )

    cm_fig = go.Figure(data=go.Heatmap(
        z=cm,
        x=labels,
        y=labels,
        colorscale=[
            [0.0, "#1e293b"],
            [0.25, "#1e40af"],
            [0.5, "#3b82f6"],
            [0.75, "#38bdf8"],
            [1.0, "#22d3ee"],
        ],
        showscale=True,
        colorbar=dict(
            title="Count",
            titlefont=dict(color=CLR_TEXT, size=12),
            tickfont=dict(color=CLR_MUTED, size=10),
        ),
        hovertemplate="True: %{y}<br>Predicted: %{x}<br>Count: %{z}<extra></extra>",
    ))

    cm_fig.update_layout(
        title=dict(
            text="Confusion Matrix",
            font=dict(size=16, color=CLR_ACCENT, family="Inter, sans-serif"),
        ),
        xaxis=dict(title="Predicted Zone", side="bottom", color=CLR_TEXT,
                    tickfont=dict(size=12), titlefont=dict(size=13)),
        yaxis=dict(title="True Zone", autorange="reversed", color=CLR_TEXT,
                    tickfont=dict(size=12), titlefont=dict(size=13)),
        template="plotly_dark",
        paper_bgcolor=CLR_BG,
        plot_bgcolor=CLR_BG,
        font=dict(family="Inter, sans-serif"),
        height=400,
        margin=dict(l=80, r=40, t=60, b=80),
        annotations=annotations,
    )

    # ─── Per-class metrics table ───
    per_class = results['per_class']
    table_rows = []
    for label in labels:
        if label in per_class:
            m = per_class[label]
            table_rows.append({
                "Class": label,
                "Precision": f"{m['precision']:.4f}",
                "Recall": f"{m['recall']:.4f}",
                "F1-Score": f"{m['f1']:.4f}",
            })

    # Add macro average row
    table_rows.append({
        "Class": "Macro Average",
        "Precision": f"{results['macro_precision']:.4f}",
        "Recall": f"{results['macro_recall']:.4f}",
        "F1-Score": f"{results['macro_f1']:.4f}",
    })

    metrics_table = dash_table.DataTable(
        data=table_rows,
        columns=[
            {"name": "Class", "id": "Class"},
            {"name": "Precision", "id": "Precision"},
            {"name": "Recall", "id": "Recall"},
            {"name": "F1-Score", "id": "F1-Score"},
        ],
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": CLR_CARD,
            "color": CLR_ACCENT,
            "fontWeight": "700",
            "border": f"1px solid {CLR_MUTED}33",
            "fontSize": "13px",
            "textAlign": "center",
        },
        style_cell={
            "backgroundColor": CLR_BG,
            "color": CLR_TEXT,
            "border": f"1px solid {CLR_MUTED}22",
            "padding": "10px 16px",
            "fontSize": "14px",
            "fontFamily": "'Inter', monospace",
            "textAlign": "center",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#0f172a"},
            # Bold the macro average row
            {"if": {"filter_query": '{Class} = "Macro Average"'},
             "fontWeight": "700", "backgroundColor": f"{CLR_ACCENT}11",
             "borderTop": f"2px solid {CLR_ACCENT}44"},
        ],
    )

    # ─── Summary metric cards ───
    metric_cards = dbc.Row([
        _eval_metric_card("Accuracy", f"{results['accuracy']:.2%}",
                          "fas fa-bullseye", CLR_SUCCESS),
        _eval_metric_card("Macro Precision", f"{results['macro_precision']:.2%}",
                          "fas fa-crosshairs", CLR_ACCENT),
        _eval_metric_card("Macro Recall", f"{results['macro_recall']:.2%}",
                          "fas fa-search", CLR_WARNING),
        _eval_metric_card("Macro F1-Score", f"{results['macro_f1']:.2%}",
                          "fas fa-star", CLR_ACCENT2),
    ], className="g-3 mb-3")

    # ─── Assemble panel ───
    return html.Div([
        html.Hr(style={"borderColor": f"{CLR_MUTED}33", "margin": "24px 0"}),

        html.Div([
            html.I(className="fas fa-chart-bar",
                   style={"fontSize": "24px", "color": CLR_ACCENT, "marginRight": "12px"}),
            html.H5("Evaluation Metrics",
                     style={"color": CLR_TEXT, "fontWeight": "600", "margin": "0"}),
            html.Small(f"  •  {results['matched_count']} depth intervals compared",
                       style={"color": CLR_MUTED, "marginLeft": "12px"}),
        ], style={"display": "flex", "alignItems": "center", "marginBottom": "16px"}),

        metric_cards,

        dbc.Row([
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        dcc.Graph(figure=cm_fig,
                                  config={"displayModeBar": False},
                                  style={"borderRadius": "8px"}),
                        style={"padding": "8px"},
                    ),
                    style={"background": CLR_CARD, "border": f"1px solid {CLR_MUTED}22",
                           "borderRadius": "12px"},
                ),
                md=6,
            ),
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(
                        html.Span("Per-Class Performance",
                                  style={"fontWeight": "600", "color": CLR_TEXT}),
                        style={"background": CLR_CARD,
                               "borderBottom": f"1px solid {CLR_MUTED}33"},
                    ),
                    dbc.CardBody(
                        metrics_table,
                        style={"background": CLR_BG, "padding": "0"},
                    ),
                ], style={"background": CLR_CARD, "border": f"1px solid {CLR_MUTED}22",
                          "borderRadius": "12px"}),
                md=6,
            ),
        ], className="g-3"),
    ])


def _eval_metric_card(label, value, icon, color):
    return dbc.Col(
        dbc.Card(
            dbc.CardBody(
                html.Div([
                    html.Div([
                        html.I(className=icon, style={"fontSize": "18px", "color": color}),
                    ], style={"marginBottom": "6px"}),
                    html.P(value, style={"fontSize": "24px", "fontWeight": "800",
                                         "color": CLR_TEXT, "margin": "0",
                                         "lineHeight": "1.2"}),
                    html.Small(label, style={"color": CLR_MUTED, "fontSize": "11px"}),
                ]),
                style={"padding": "14px"},
            ),
            style={
                "background": CLR_CARD,
                "border": f"1px solid {CLR_MUTED}22",
                "borderRadius": "12px",
                "borderLeft": f"3px solid {color}",
            },
        ),
        xs=6, sm=3,
    )


# ──────────────────────────────────────────────────────────────────────
#  Entry point
# ──────────────────────────────────────────────────────────────────────

def open_browser():
    """Open the default browser after a short delay."""
    import time
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:8050")


if __name__ == "__main__":
    # Auto-open browser in a background thread
    threading.Thread(target=open_browser, daemon=True).start()

    app.run(debug=False, port=8050)
