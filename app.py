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
import ml_model


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
CLR_ML       = "#a78bfa"  # violet accent for ML elements

ZONE_COLORS = {
    "Gas":     "#22c55e",
    "Oil":     "#ef4444",
    "Water":   "#3b82f6",
    "No Show": "#374151",
}

# ──────────────────────────────────────────────────────────────────────
#  Pre-train ML models at startup (runs once, ~1-2 s on sbkdeep data)
# ──────────────────────────────────────────────────────────────────────
try:
    _ML_META = ml_model.train_all()
except Exception as _ml_err:
    _ML_META = {}
    print(f"[ML] Warning: could not pre-train models: {_ml_err}")


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

                    # ML model selector
                    html.Div([
                        html.I(className="fas fa-robot",
                               style={"color": CLR_ML, "marginRight": "6px", "fontSize": "13px"}),
                        dcc.Dropdown(
                            id="ml-model-selector",
                            options=[
                                {"label": "🌲 Random Forest",      "value": "Random Forest"},
                                {"label": "🚀 Gradient Boosting", "value": "Gradient Boosting"},
                            ],
                            value="Random Forest",
                            clearable=False,
                            style={
                                "width": "185px",
                                "fontSize": "13px",
                                "backgroundColor": CLR_BG,
                                "color": CLR_TEXT,
                                "border": f"1px solid {CLR_ML}66",
                                "borderRadius": "8px",
                            },
                            className="dark-dropdown",
                        ),
                    ], style={"display": "flex", "alignItems": "center",
                              "marginRight": "12px"}),

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

charts_area = html.Div(
    id="charts-container",
    children=html.Div([
        html.Div(style={"height": "200px"}),
        html.P("⛏️", style={"fontSize": "64px", "textAlign": "center", "margin": "0"}),
        html.H4("Ready to Analyze", style={"textAlign": "center", "color": CLR_TEXT,
                                            "fontWeight": "300"}),
        html.P("Upload a mudlogging CSV file to begin — analysis runs automatically.",
               style={"textAlign": "center", "color": CLR_MUTED, "maxWidth": "400px",
                       "margin": "12px auto"}),
    ]),
)

# ─── Evaluation results area ───
eval_area = html.Div(id="eval-container", children=[], style={"marginTop": "24px"})

# ─── ML Dashboard placeholder ───
ml_placeholder = html.Div([
    html.Div(style={"height": "200px"}),
    html.P("🤖", style={"fontSize": "64px", "textAlign": "center", "margin": "0"}),
    html.H4("ML Classifier Ready", style={"textAlign": "center", "color": CLR_TEXT,
                                           "fontWeight": "300"}),
    html.P("Upload a mudlog file on the Analysis tab — ML predictions will appear here automatically.",
           style={"textAlign": "center", "color": CLR_MUTED, "maxWidth": "440px",
                   "margin": "12px auto"}),
    # Simple inline training status badge (no function call needed)
    dbc.Card(
        dbc.CardBody([
            html.I(className="fas fa-check-circle",
                   style={"color": CLR_SUCCESS, "marginRight": "8px"}),
            html.Span(
                f"Models pre-trained on sbkdeep-001  •  "
                f"{_ML_META.get('training_samples', 0):,} samples  •  "
                f"{_ML_META.get('n_features', 0)} features" if _ML_META
                else "⚠️ Training failed — check sbkdeep-001_mudlogg.csv path",
                style={"fontSize": "13px", "color": CLR_TEXT},
            ),
        ], style={"padding": "14px", "textAlign": "center"}),
        style={"background": CLR_CARD, "border": f"1px solid {CLR_SUCCESS}33",
               "borderRadius": "12px", "maxWidth": "520px", "margin": "24px auto"},
    ),
], id="ml-placeholder")

ml_dashboard_area = html.Div(id="ml-dashboard", children=ml_placeholder)


# ─── Tab styling helpers ───
_TAB_STYLE = {
    "backgroundColor": CLR_CARD,
    "color": CLR_MUTED,
    "border": f"1px solid {CLR_MUTED}22",
    "borderBottom": "none",
    "borderRadius": "8px 8px 0 0",
    "padding": "10px 22px",
    "fontWeight": "500",
    "fontSize": "14px",
    "cursor": "pointer",
}
_TAB_SELECTED_STYLE = {
    **_TAB_STYLE,
    "backgroundColor": CLR_BG,
    "color": CLR_ACCENT,
    "borderTop": f"2px solid {CLR_ACCENT}",
}
_TAB_ML_STYLE = {**_TAB_STYLE, "color": CLR_ML}
_TAB_ML_SELECTED_STYLE = {
    **_TAB_SELECTED_STYLE,
    "color": CLR_ML,
    "borderTop": f"2px solid {CLR_ML}",
}

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

        # ─── Main Tab Navigation ───
        dcc.Tabs(
            id="main-tabs",
            value="tab-analysis",
            children=[
                dcc.Tab(
                    label="📊 Analysis",
                    value="tab-analysis",
                    style=_TAB_STYLE,
                    selected_style=_TAB_SELECTED_STYLE,
                    children=[
                        html.Div(style={"height": "16px"}),
                        charts_area,
                        eval_area,
                    ],
                ),
                dcc.Tab(
                    label="🤖 ML Classifier",
                    value="tab-ml",
                    style=_TAB_ML_STYLE,
                    selected_style=_TAB_ML_SELECTED_STYLE,
                    children=[
                        html.Div(style={"height": "16px"}),
                        ml_dashboard_area,
                    ],
                ),
            ],
            style={"marginBottom": "0"},
            colors={
                "border": f"{CLR_MUTED}22",
                "primary": CLR_ACCENT,
                "background": CLR_BG,
            },
        ),

        dcc.Download(id="download-report"),
    ], fluid=True, style={"padding": "0 24px 40px 24px"}),

    # Hidden stores
    dcc.Store(id="store-parsed",    data=None),
    dcc.Store(id="store-computed",  data=None),
    dcc.Store(id="store-truth",     data=None),
    dcc.Store(id="store-ml-result", data=None),

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
     Output("upload-modal", "is_open", allow_duplicate=True)],
    [Input("upload-data", "contents")],
    [State("upload-data", "filename")],
    prevent_initial_call=True,
)
def parse_upload(contents, filename):
    if contents is None:
        return no_update, no_update, no_update

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
            f"✅ Loaded {filename} — {len(df)} depth rows. Running analysis…",
            color="success",
            style={"borderRadius": "8px"},
        )
        return df.to_json(date_format="iso", orient="split"), status, False

    except Exception as e:
        status = dbc.Alert(
            f"❌ Error: {str(e)}", color="danger", style={"borderRadius": "8px"}
        )
        return no_update, status, no_update


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


# --- Show summary stats on file upload ---
@app.callback(
    [Output("stats-row", "children"),
     Output("stats-row", "style")],
    [Input("store-parsed", "data")],
    prevent_initial_call=True,
)
def show_stats(json_raw):
    if json_raw is None:
        return no_update, {"display": "none"}

    df_raw = pd.read_json(io.StringIO(json_raw), orient="split")
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

    return stats, {"display": "flex"}


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


# --- Run analysis (auto-triggered on upload) ---
@app.callback(
    [Output("store-computed", "data"),
     Output("charts-container", "children"),
     Output("btn-export", "disabled")],
    [Input("store-parsed", "data")],
    prevent_initial_call=True,
)
def run_analysis(json_data):
    if json_data is None:
        return no_update, no_update, no_update

    df = pd.read_json(io.StringIO(json_data), orient="split")
    computed = compute_all(df)

    # Build charts panel with side-by-side track row as default
    charts = _build_charts_panel(computed, mode="side_by_side")

    return computed.to_json(date_format="iso", orient="split"), charts, False


# --- Switch Chart View (Side-by-Side Track Row vs Separate Cards vs Grouped) ---
@app.callback(
    Output("charts-wrapper", "children"),
    [Input("chart-view-mode", "value")],
    [State("store-computed", "data")],
    prevent_initial_call=True,
)
def switch_chart_view(mode, json_computed):
    if not json_computed:
        return no_update
    df = pd.read_json(io.StringIO(json_computed), orient="split")
    if mode == "grouped":
        return _build_log_charts(df)
    elif mode == "separate":
        return _build_separate_column_charts(df)
    else:
        return _build_side_by_side_row_charts(df)


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


# ─── ML Prediction callback (triggered by computed data OR model selector) ───
@app.callback(
    Output("store-ml-result", "data"),
    [Input("store-computed", "data"),
     Input("ml-model-selector", "value")],
    prevent_initial_call=True,
)
def run_ml_prediction(json_computed, model_name):
    if json_computed is None:
        return no_update
    if not model_name:
        model_name = "Random Forest"
    try:
        df = pd.read_json(io.StringIO(json_computed), orient="split")
        zone_ml = ml_model.predict(df, model_name)
        df["ZONE_ML"] = zone_ml
        return df[["DEPTH", "ZONE", "ZONE_ML"]].to_json(date_format="iso", orient="split")
    except Exception as e:
        print(f"[ML] Prediction error: {e}")
        return no_update


# ─── ML Dashboard renderer ───
@app.callback(
    Output("ml-dashboard", "children"),
    [Input("store-ml-result", "data"),
     Input("ml-model-selector", "value")],
    [State("store-computed", "data")],
    prevent_initial_call=True,
)
def render_ml_dashboard(json_ml, model_name, json_computed):
    if json_ml is None or json_computed is None:
        return no_update
    if not model_name:
        model_name = "Random Forest"
    try:
        ml_df = pd.read_json(io.StringIO(json_ml), orient="split")
        return _build_ml_dashboard(ml_df, model_name)
    except Exception as e:
        return dbc.Alert(f"❌ ML Dashboard error: {e}", color="danger",
                         style={"borderRadius": "12px", "marginTop": "16px"})


# ──────────────────────────────────────────────────────────────────────
#  ML Dashboard builder functions
# ──────────────────────────────────────────────────────────────────────

def _build_ml_training_badge() -> list:
    """Compact training summary shown in the placeholder and at top of ML dashboard."""
    if not _ML_META:
        return [dbc.Alert("⚠️ ML models could not be trained. Check sbkdeep-001_mudlogg.csv path.",
                          color="warning", style={"borderRadius": "10px"})]

    cards = []
    for model_name, model_info in _ML_META.get("models", {}).items():
        cv_acc = model_info.get("cv_accuracy_mean", 0)
        cv_std = model_info.get("cv_accuracy_std", 0)
        color = CLR_ML if "Forest" in model_name else CLR_ACCENT2
        cards.append(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-brain",
                                   style={"color": color, "fontSize": "20px", "marginBottom": "8px"}),
                            html.Div(model_name,
                                     style={"fontWeight": "700", "color": CLR_TEXT,
                                            "fontSize": "14px", "marginBottom": "4px"}),
                            html.Div(f"CV Accuracy: {cv_acc:.1%} ± {cv_std:.1%}",
                                     style={"color": color, "fontSize": "15px",
                                            "fontWeight": "600"}),
                            html.Div(f"Train: {model_info.get('train_accuracy', 0):.1%}",
                                     style={"color": CLR_MUTED, "fontSize": "12px",
                                            "marginTop": "2px"}),
                        ]),
                    ], style={"padding": "16px", "textAlign": "center"}),
                    style={"background": CLR_CARD, "border": f"1px solid {color}44",
                           "borderRadius": "12px", "borderLeft": f"3px solid {color}"},
                ),
                md=6,
            )
        )

    dist_items = []
    for zone, count in _ML_META.get("class_distribution", {}).items():
        total = _ML_META.get("training_samples", 1)
        pct = count / total * 100 if total > 0 else 0
        dist_items.append(
            html.Span([
                html.Div(style={
                    "width": "10px", "height": "10px", "borderRadius": "2px",
                    "backgroundColor": ZONE_COLORS.get(zone, CLR_MUTED),
                    "display": "inline-block", "marginRight": "5px",
                }),
                html.Span(f"{zone}: {count} ({pct:.0f}%) ",
                          style={"fontSize": "12px", "color": CLR_MUTED, "marginRight": "12px"}),
            ])
        )

    summary = dbc.Card(
        dbc.CardBody([
            html.Div([
                html.I(className="fas fa-database",
                       style={"color": CLR_ACCENT, "marginRight": "8px"}),
                html.Span(f"Training Data: sbkdeep-001  •  "
                          f"{_ML_META.get('training_samples', 0):,} samples  •  "
                          f"{_ML_META.get('n_features', 0)} features  •  "
                          f"5-fold cross-validation",
                          style={"fontSize": "13px", "color": CLR_TEXT}),
            ], style={"marginBottom": "10px"}),
            html.Div(dist_items, style={"display": "flex", "flexWrap": "wrap",
                                        "alignItems": "center"}),
        ], style={"padding": "14px"}),
        style={"background": CLR_CARD, "border": f"1px solid {CLR_ACCENT}22",
               "borderRadius": "12px", "marginBottom": "12px"},
    )
    return [summary, dbc.Row(cards, className="g-3")]


def _build_feature_importance_chart(model_name: str) -> go.Figure:
    """Horizontal bar chart of feature importances."""
    importances = ml_model.get_feature_importances(model_name)
    if not importances:
        return go.Figure()

    # Show top 15
    importances = importances[:15]
    features = [p[0] for p in reversed(importances)]
    values   = [p[1] for p in reversed(importances)]

    # Colour by magnitude
    max_v = max(values) if values else 1
    bar_colors = []
    for v in values:
        ratio = v / max_v
        if ratio > 0.6:
            bar_colors.append(CLR_ML)
        elif ratio > 0.3:
            bar_colors.append(CLR_ACCENT2)
        else:
            bar_colors.append(CLR_MUTED)

    fig = go.Figure(go.Bar(
        x=values,
        y=features,
        orientation="h",
        marker=dict(
            color=bar_colors,
            line=dict(color="rgba(0,0,0,0)", width=0),
        ),
        hovertemplate="%{y}: %{x:.4f}<extra></extra>",
    ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=CLR_BG,
        plot_bgcolor="#0f172a",
        height=420,
        margin=dict(l=130, r=20, t=30, b=40),
        font=dict(family="Inter, sans-serif", size=11, color=CLR_TEXT),
        xaxis=dict(title="Importance Score", gridcolor=_hex_to_rgba(CLR_MUTED, 0.15)),
        yaxis=dict(tickfont=dict(size=11)),
        showlegend=False,
    )
    return fig


def _build_zone_comparison_chart(ml_df: pd.DataFrame) -> go.Figure:
    """Side-by-side depth log: Rule-based ZONE vs ML ZONE."""
    depth = ml_df["DEPTH"].values
    zone_rb  = ml_df["ZONE"].values
    zone_ml  = ml_df["ZONE_ML"].values

    def _encode(zones):
        nums, clrs = [], []
        for z in zones:
            if z == "Gas":
                nums.append(3); clrs.append(ZONE_COLORS["Gas"])
            elif z == "Oil":
                nums.append(2); clrs.append(ZONE_COLORS["Oil"])
            elif z == "Water":
                nums.append(1); clrs.append(ZONE_COLORS["Water"])
            else:
                nums.append(0); clrs.append(ZONE_COLORS["No Show"])
        return nums, clrs

    rb_nums,  rb_clrs  = _encode(zone_rb)
    ml_nums,  ml_clrs  = _encode(zone_ml)

    # Agreement overlay — highlight disagreements
    disagree_mask = zone_rb != zone_ml
    agree_pct = (~disagree_mask).mean() * 100

    fig = make_subplots(
        rows=1, cols=2,
        shared_yaxes=True,
        horizontal_spacing=0.04,
        subplot_titles=["Rule-Based Expert System", "ML Classifier Prediction"],
    )

    # Rule-based track
    fig.add_trace(go.Bar(
        x=rb_nums, y=depth, orientation="h",
        marker=dict(color=rb_clrs),
        name="Rule-Based",
        hovertext=zone_rb, hoverinfo="text+y",
        showlegend=False, width=0.9,
    ), row=1, col=1)

    # ML track
    fig.add_trace(go.Bar(
        x=ml_nums, y=depth, orientation="h",
        marker=dict(color=ml_clrs),
        name="ML",
        hovertext=zone_ml, hoverinfo="text+y",
        showlegend=False, width=0.9,
    ), row=1, col=2)

    total_depth = max(depth) - min(depth) if len(depth) > 1 else 100
    chart_height = max(600, min(int(total_depth * 0.5), 2200))

    fig.update_layout(
        height=chart_height,
        template="plotly_dark",
        paper_bgcolor=CLR_BG,
        plot_bgcolor="#0f172a",
        font=dict(family="Inter, sans-serif", size=11, color=CLR_TEXT),
        margin=dict(l=60, r=20, t=60, b=40),
        title=dict(
            text=f"Zone Comparison  •  Agreement: {agree_pct:.1f}%",
            font=dict(size=14, color=CLR_ML, family="Inter, sans-serif"),
            x=0.5, xanchor="center",
        ),
    )
    fig.update_xaxes(showticklabels=False)
    for i in [1, 2]:
        yaxis_key = "yaxis" if i == 1 else "yaxis2"
        fig.update_layout(**{yaxis_key: dict(autorange="reversed")})
    fig.update_yaxes(title_text="Depth (m)", row=1, col=1,
                     gridcolor=_hex_to_rgba(CLR_MUTED, 0.15))
    for ann in fig.layout.annotations:
        ann.font = dict(size=13, color=CLR_ACCENT, family="Inter, sans-serif")

    return fig


def _build_ml_dashboard(ml_df: pd.DataFrame, model_name: str) -> html.Div:
    """Full ML dashboard: training summary, feature importance, comparison charts, metrics."""
    from sklearn.metrics import (
        confusion_matrix, accuracy_score,
        precision_score, recall_score, f1_score,
    )

    y_rb  = ml_df["ZONE"].values
    y_ml  = ml_df["ZONE_ML"].values

    present_labels = sorted(
        set(y_rb) | set(y_ml),
        key=lambda x: ["Gas", "Oil", "Water", "No Show"].index(x)
                      if x in ["Gas", "Oil", "Water", "No Show"] else 99,
    )

    agree_pct  = float((y_rb == y_ml).mean() * 100)
    acc        = float(accuracy_score(y_rb, y_ml))
    macro_prec = float(precision_score(y_rb, y_ml, labels=present_labels,
                                       average="macro", zero_division=0))
    macro_rec  = float(recall_score(y_rb, y_ml, labels=present_labels,
                                    average="macro", zero_division=0))
    macro_f1   = float(f1_score(y_rb, y_ml, labels=present_labels,
                                average="macro", zero_division=0))
    cm = confusion_matrix(y_rb, y_ml, labels=present_labels)

    # ─── Agreement metric cards ───
    agree_cards = dbc.Row([
        _eval_metric_card("Agreement",      f"{agree_pct:.1f}%",  "fas fa-handshake",  CLR_ML),
        _eval_metric_card("Accuracy",       f"{acc:.2%}",         "fas fa-bullseye",   CLR_SUCCESS),
        _eval_metric_card("Macro Precision",f"{macro_prec:.2%}",  "fas fa-crosshairs", CLR_ACCENT),
        _eval_metric_card("Macro F1-Score", f"{macro_f1:.2%}",    "fas fa-star",       CLR_ACCENT2),
    ], className="g-3 mb-3")

    # ─── Feature importance chart ───
    fi_fig = _build_feature_importance_chart(model_name)
    fi_card = dbc.Card([
        dbc.CardHeader(
            html.Span([
                html.I(className="fas fa-chart-bar",
                       style={"color": CLR_ML, "marginRight": "8px"}),
                html.Span(f"Feature Importances — {model_name}",
                          style={"fontWeight": "600", "color": CLR_TEXT}),
            ]),
            style={"background": CLR_CARD, "borderBottom": f"1px solid {CLR_MUTED}33"},
        ),
        dbc.CardBody(
            dcc.Graph(figure=fi_fig, config={"displayModeBar": False},
                      style={"borderRadius": "8px"}),
            style={"background": CLR_BG, "padding": "8px"},
        ),
    ], style={"background": CLR_CARD, "border": f"1px solid {CLR_ML}22",
              "borderRadius": "12px"})

    # ─── Confusion matrix vs rule-based ───
    annotations_cm = []
    for i in range(len(present_labels)):
        for j in range(len(present_labels)):
            annotations_cm.append(dict(
                x=present_labels[j], y=present_labels[i],
                text=str(cm[i][j]),
                showarrow=False,
                font=dict(color="white" if cm[i][j] > cm.max() * 0.5 else CLR_TEXT,
                          size=14, family="Inter, sans-serif"),
            ))

    cm_fig = go.Figure(data=go.Heatmap(
        z=cm, x=present_labels, y=present_labels,
        colorscale=[[0, "#1e293b"], [0.33, "#4c1d95"], [0.66, "#7c3aed"], [1.0, "#a78bfa"]],
        showscale=True,
        colorbar=dict(title="Count", titlefont=dict(color=CLR_TEXT, size=12),
                      tickfont=dict(color=CLR_MUTED, size=10)),
        hovertemplate="Rule-Based: %{y}<br>ML Prediction: %{x}<br>Count: %{z}<extra></extra>",
    ))
    cm_fig.update_layout(
        title=dict(text="ML vs Rule-Based Confusion Matrix",
                   font=dict(size=14, color=CLR_ML, family="Inter, sans-serif")),
        xaxis=dict(title="ML Prediction", side="bottom", color=CLR_TEXT,
                   tickfont=dict(size=12), titlefont=dict(size=13)),
        yaxis=dict(title="Rule-Based", autorange="reversed", color=CLR_TEXT,
                   tickfont=dict(size=12), titlefont=dict(size=13)),
        template="plotly_dark",
        paper_bgcolor=CLR_BG, plot_bgcolor=CLR_BG,
        font=dict(family="Inter, sans-serif"),
        height=380, margin=dict(l=80, r=40, t=50, b=80),
        annotations=annotations_cm,
    )

    # ─── Per-class table ───
    prec_arr = precision_score(y_rb, y_ml, labels=present_labels, average=None, zero_division=0)
    rec_arr  = recall_score(y_rb,  y_ml, labels=present_labels, average=None, zero_division=0)
    f1_arr   = f1_score(y_rb,    y_ml, labels=present_labels, average=None, zero_division=0)

    table_rows = []
    for idx, label in enumerate(present_labels):
        table_rows.append({
            "Class":     label,
            "Precision": f"{prec_arr[idx]:.4f}",
            "Recall":    f"{rec_arr[idx]:.4f}",
            "F1-Score":  f"{f1_arr[idx]:.4f}",
        })
    table_rows.append({
        "Class":     "Macro Average",
        "Precision": f"{macro_prec:.4f}",
        "Recall":    f"{macro_rec:.4f}",
        "F1-Score":  f"{macro_f1:.4f}",
    })

    metrics_table = dash_table.DataTable(
        data=table_rows,
        columns=[
            {"name": "Class",     "id": "Class"},
            {"name": "Precision", "id": "Precision"},
            {"name": "Recall",    "id": "Recall"},
            {"name": "F1-Score",  "id": "F1-Score"},
        ],
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": CLR_CARD, "color": CLR_ML,
            "fontWeight": "700", "border": f"1px solid {CLR_MUTED}33",
            "fontSize": "13px", "textAlign": "center",
        },
        style_cell={
            "backgroundColor": CLR_BG, "color": CLR_TEXT,
            "border": f"1px solid {CLR_MUTED}22",
            "padding": "10px 16px", "fontSize": "14px",
            "fontFamily": "'Inter', monospace", "textAlign": "center",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#0f172a"},
            {"if": {"filter_query": '{Class} = "Macro Average"'},
             "fontWeight": "700", "backgroundColor": f"{CLR_ML}11",
             "borderTop": f"2px solid {CLR_ML}44"},
        ],
    )

    # ─── Disagreement table (depth intervals where ML ≠ rule-based) ───
    disagree_df = ml_df[ml_df["ZONE"] != ml_df["ZONE_ML"]].copy()
    disagree_rows = []
    for _, row in disagree_df.head(50).iterrows():
        disagree_rows.append({
            "Depth (m)": f"{row['DEPTH']:.1f}",
            "Rule-Based": row["ZONE"],
            "ML Prediction": row["ZONE_ML"],
        })

    disagree_pct = len(disagree_df) / len(ml_df) * 100 if len(ml_df) > 0 else 0

    disagree_table = dash_table.DataTable(
        data=disagree_rows,
        columns=[
            {"name": "Depth (m)",     "id": "Depth (m)"},
            {"name": "Rule-Based",    "id": "Rule-Based"},
            {"name": "ML Prediction", "id": "ML Prediction"},
        ],
        page_size=12,
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": CLR_CARD, "color": CLR_WARNING,
            "fontWeight": "700", "border": f"1px solid {CLR_MUTED}33",
            "fontSize": "13px", "textAlign": "center",
        },
        style_cell={
            "backgroundColor": CLR_BG, "color": CLR_TEXT,
            "border": f"1px solid {CLR_MUTED}22",
            "padding": "9px 14px", "fontSize": "13px",
            "fontFamily": "'Inter', monospace", "textAlign": "center",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#0f172a"},
        ],
    )

    # ─── Zone comparison depth chart ───
    comp_fig = _build_zone_comparison_chart(ml_df)

    return html.Div([
        # Training summary
        dbc.Card(
            dbc.CardBody([
                html.Div([
                    html.I(className="fas fa-robot",
                           style={"fontSize": "20px", "color": CLR_ML, "marginRight": "10px"}),
                    html.H5("Machine Learning Dashboard",
                            style={"color": CLR_TEXT, "fontWeight": "600", "margin": "0"}),
                    html.Small(f"  •  Model: {model_name}  •  "
                               f"{len(ml_df):,} depth intervals predicted",
                               style={"color": CLR_MUTED, "marginLeft": "10px"}),
                ], style={"display": "flex", "alignItems": "center", "marginBottom": "16px"}),
                html.Div(_build_ml_training_badge()),
            ], style={"padding": "20px"}),
            style={"background": CLR_CARD, "border": f"1px solid {CLR_ML}22",
                   "borderRadius": "12px", "marginBottom": "20px"},
        ),

        # Agreement metric cards
        html.Div([
            html.Hr(style={"borderColor": f"{CLR_ML}33", "margin": "4px 0 16px 0"}),
            html.Div([
                html.I(className="fas fa-balance-scale",
                       style={"color": CLR_ML, "fontSize": "18px", "marginRight": "10px"}),
                html.Span("ML vs Rule-Based Comparison",
                          style={"fontWeight": "600", "color": CLR_TEXT, "fontSize": "15px"}),
                html.Small(" — metrics compare ML output against the deterministic expert system",
                           style={"color": CLR_MUTED, "marginLeft": "8px"}),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "14px"}),
            agree_cards,
        ]),

        # Feature importance + confusion matrix side by side
        dbc.Row([
            dbc.Col(fi_card, md=6),
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(
                        html.Span([
                            html.I(className="fas fa-th",
                                   style={"color": CLR_ML, "marginRight": "8px"}),
                            html.Span("Confusion Matrix vs Expert System",
                                      style={"fontWeight": "600", "color": CLR_TEXT}),
                        ]),
                        style={"background": CLR_CARD,
                               "borderBottom": f"1px solid {CLR_MUTED}33"},
                    ),
                    dbc.CardBody(
                        dcc.Graph(figure=cm_fig, config={"displayModeBar": False},
                                  style={"borderRadius": "8px"}),
                        style={"background": CLR_BG, "padding": "8px"},
                    ),
                ], style={"background": CLR_CARD, "border": f"1px solid {CLR_ML}22",
                           "borderRadius": "12px"}),
                md=6,
            ),
        ], className="g-3 mb-3"),

        # Per-class metrics table
        dbc.Card([
            dbc.CardHeader(
                html.Span([
                    html.I(className="fas fa-table",
                           style={"color": CLR_ML, "marginRight": "8px"}),
                    html.Span("Per-Class Performance (ML vs Rule-Based)",
                              style={"fontWeight": "600", "color": CLR_TEXT}),
                ]),
                style={"background": CLR_CARD, "borderBottom": f"1px solid {CLR_MUTED}33"},
            ),
            dbc.CardBody(metrics_table, style={"background": CLR_BG, "padding": "0"}),
        ], style={"background": CLR_CARD, "border": f"1px solid {CLR_ML}22",
                  "borderRadius": "12px", "marginBottom": "20px"}),

        # Zone comparison depth chart
        dbc.Card([
            dbc.CardHeader(
                html.Span([
                    html.I(className="fas fa-columns",
                           style={"color": CLR_ML, "marginRight": "8px"}),
                    html.Span("Depth-by-Depth Zone Comparison",
                              style={"fontWeight": "600", "color": CLR_TEXT}),
                    html.Small(" — scroll to explore full depth range",
                               style={"color": CLR_MUTED, "marginLeft": "8px"}),
                ]),
                style={"background": CLR_CARD, "borderBottom": f"1px solid {CLR_MUTED}33"},
            ),
            dbc.CardBody([
                # Zone legend
                html.Div([
                    html.Div(style={"width": "12px", "height": "12px", "borderRadius": "3px",
                                    "backgroundColor": ZONE_COLORS["Gas"],
                                    "display": "inline-block", "marginRight": "5px",
                                    "verticalAlign": "middle"}),
                    html.Span("Gas ", style={"fontSize": "12px", "marginRight": "14px"}),
                    html.Div(style={"width": "12px", "height": "12px", "borderRadius": "3px",
                                    "backgroundColor": ZONE_COLORS["Oil"],
                                    "display": "inline-block", "marginRight": "5px",
                                    "verticalAlign": "middle"}),
                    html.Span("Oil ", style={"fontSize": "12px", "marginRight": "14px"}),
                    html.Div(style={"width": "12px", "height": "12px", "borderRadius": "3px",
                                    "backgroundColor": ZONE_COLORS["Water"],
                                    "display": "inline-block", "marginRight": "5px",
                                    "verticalAlign": "middle"}),
                    html.Span("Water ", style={"fontSize": "12px", "marginRight": "14px"}),
                    html.Div(style={"width": "12px", "height": "12px", "borderRadius": "3px",
                                    "backgroundColor": ZONE_COLORS["No Show"],
                                    "display": "inline-block", "marginRight": "5px",
                                    "verticalAlign": "middle"}),
                    html.Span("No Show", style={"fontSize": "12px"}),
                ], style={"display": "flex", "alignItems": "center",
                          "justifyContent": "center", "marginBottom": "12px"}),
                html.Div(
                    dcc.Graph(figure=comp_fig,
                              config={"scrollZoom": True, "displayModeBar": True},
                              style={"borderRadius": "10px"}),
                    style={"overflowX": "auto"},
                ),
            ], style={"background": CLR_BG, "padding": "16px"}),
        ], style={"background": CLR_CARD, "border": f"1px solid {CLR_ML}22",
                  "borderRadius": "12px", "marginBottom": "20px"}),

        # Disagreement table
        dbc.Card([
            dbc.CardHeader(
                html.Span([
                    html.I(className="fas fa-exclamation-triangle",
                           style={"color": CLR_WARNING, "marginRight": "8px"}),
                    html.Span(f"Disagreements: {len(disagree_df)} intervals ({disagree_pct:.1f}%)",
                              style={"fontWeight": "600", "color": CLR_TEXT}),
                    html.Small(" — depth rows where ML and rule-based disagree (first 50 shown)",
                               style={"color": CLR_MUTED, "marginLeft": "8px"}),
                ]),
                style={"background": CLR_CARD, "borderBottom": f"1px solid {CLR_MUTED}33"},
            ),
            dbc.CardBody(disagree_table, style={"background": CLR_BG, "padding": "0"}),
        ], style={"background": CLR_CARD, "border": f"1px solid {CLR_WARNING}22",
                  "borderRadius": "12px", "marginBottom": "20px"}),
    ])


# ──────────────────────────────────────────────────────────────────────
#  Chart builder
# ──────────────────────────────────────────────────────────────────────

def _hex_to_rgba(hex_color, alpha=0.08):
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


def _build_charts_panel(df, mode="side_by_side"):
    view_selector = dbc.RadioItems(
        id="chart-view-mode",
        options=[
            {"label": "📐 Side-by-Side Track Row", "value": "side_by_side"},
            {"label": "📊 Separate Column Cards", "value": "separate"},
            {"label": "📑 Grouped Category Tracks", "value": "grouped"},
        ],
        value=mode,
        inline=True,
        className="btn-group",
        inputClassName="btn-check",
        labelClassName="btn btn-outline-info btn-sm",
        labelCheckedClassName="active",
    )

    header = dbc.CardHeader(
        html.Div([
            html.Div([
                html.Span("📈 Depth Log Visualization",
                          style={"fontWeight": "600", "color": CLR_TEXT, "fontSize": "15px"}),
                html.Small(" — Side-by-side multi-track row view & interactive zone analysis",
                           style={"color": CLR_MUTED, "marginLeft": "8px"}),
            ]),
            view_selector,
        ], style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"}),
        style={"background": CLR_CARD, "borderBottom": f"1px solid {CLR_MUTED}33", "padding": "12px 16px"},
    )

    if mode == "grouped":
        chart_content = _build_log_charts(df)
    elif mode == "separate":
        chart_content = _build_separate_column_charts(df)
    else:
        chart_content = _build_side_by_side_row_charts(df)

    return dbc.Card(
        [
            header,
            dbc.CardBody(
                html.Div(id="charts-wrapper", children=chart_content),
                style={"background": CLR_BG, "padding": "16px"},
            ),
        ],
        style={"background": CLR_CARD, "border": f"1px solid {CLR_MUTED}22",
               "borderRadius": "12px", "marginBottom": "24px"},
    )


def _build_side_by_side_row_charts(df):
    """
    Renders every column as a narrow individual Plotly graph, placed in a
    horizontal flex row inside an overflow-x:auto scrolling container.
    This produces a classical mud-log side-by-side track layout.
    """
    depth = df['DEPTH'].values
    grid_clr = _hex_to_rgba(CLR_MUTED, 0.18)

    total_depth = max(depth) - min(depth) if len(depth) > 1 else 100
    chart_height = max(600, min(int(total_depth * 0.55), 2000))

    column_specs = [
        # (col_key, display_title, color, scale_type)
        ("C1",           "C1",         "#38bdf8", "log"),
        ("C2",           "C2",         "#818cf8", "log"),
        ("C3",           "C3",         "#f472b6", "log"),
        ("IC4",          "iC4",        "#fb923c", "log"),
        ("NC4",          "nC4",        "#facc15", "log"),
        ("IC5",          "iC5",        "#34d399", "log"),
        ("NC5",          "nC5",        "#a78bfa", "log"),
        ("TG_USED",      "TG",         "#e2e8f0", "log"),
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

    active_specs = [(k, t, c, s) for (k, t, c, s) in column_specs if k in df.columns]

    track_divs = []

    for idx, (col_key, title, color, scale_type) in enumerate(active_specs):
        is_first = (idx == 0)
        vals = df[col_key].replace([np.inf, -np.inf], np.nan).values.astype(float)
        x_plot = np.where(vals > 0, vals, np.nan) if scale_type == "log" else vals

        track_w = 115 if is_first else 90   # first track wider to fit depth labels
        l_margin = 48 if is_first else 4

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_plot, y=depth,
            mode="lines",
            line=dict(color=color, width=1.4),
            fill="tozerox",
            fillcolor=_hex_to_rgba(color, 0.25),
            showlegend=False,
            hovertemplate=f"Depth: %{{y:.1f}} m<br>{title}: %{{x:.4g}}<extra></extra>",
        ))
        fig.update_layout(
            height=chart_height,
            width=track_w,
            autosize=False,
            template="plotly_dark",
            paper_bgcolor=CLR_BG,
            plot_bgcolor="#070c18",
            font=dict(family="Inter, sans-serif", size=8, color=CLR_TEXT),
            margin=dict(l=l_margin, r=3, t=26, b=10),
            title=dict(
                text=title,
                font=dict(size=9, color=color, family="Inter, sans-serif"),
                x=0.5, xanchor="center", pad=dict(t=2),
            ),
            xaxis=dict(
                type="log" if scale_type == "log" else "linear",
                gridcolor=grid_clr,
                tickfont=dict(size=7, color=CLR_MUTED),
                nticks=3,
                showgrid=True,
                zeroline=False,
                showline=True,
                linecolor=_hex_to_rgba(CLR_MUTED, 0.4),
            ),
            yaxis=dict(
                autorange="reversed",
                gridcolor=grid_clr,
                showticklabels=is_first,
                tickfont=dict(size=8, color=CLR_MUTED),
                showgrid=True,
                zeroline=False,
                title=dict(
                    text="Depth (m)" if is_first else "",
                    font=dict(size=9, color=CLR_MUTED),
                ),
                showline=True,
                linecolor=_hex_to_rgba(CLR_MUTED, 0.4),
            ),
        )

        track_divs.append(
            html.Div(
                dcc.Graph(
                    figure=fig,
                    responsive=False,
                    config={"scrollZoom": True, "displayModeBar": False},
                    style={"display": "block"},
                ),
                style={
                    "display":       "inline-block",
                    "flexShrink":    "0",
                    "width":         f"{track_w}px",
                    "borderRight":   f"1px solid {_hex_to_rgba(CLR_MUTED, 0.25)}",
                    "verticalAlign": "top",
                }
            )
        )

    # ── Zone classification track ──
    if 'ZONE' in df.columns:
        zone_vals = df['ZONE'].values
        zone_numeric, zone_clrs = [], []
        for z in zone_vals:
            if z == "Gas":     zone_numeric.append(3); zone_clrs.append(ZONE_COLORS["Gas"])
            elif z == "Oil":   zone_numeric.append(2); zone_clrs.append(ZONE_COLORS["Oil"])
            elif z == "Water": zone_numeric.append(1); zone_clrs.append(ZONE_COLORS["Water"])
            else:              zone_numeric.append(0); zone_clrs.append(ZONE_COLORS["No Show"])

        zone_fig = go.Figure(go.Bar(
            x=zone_numeric, y=depth, orientation="h",
            marker=dict(color=zone_clrs),
            hovertext=zone_vals, hoverinfo="text+y",
            showlegend=False, width=0.9,
        ))
        zone_fig.update_layout(
            height=chart_height,
            width=55,
            autosize=False,
            template="plotly_dark",
            paper_bgcolor=CLR_BG,
            plot_bgcolor="#070c18",
            margin=dict(l=3, r=3, t=26, b=10),
            title=dict(
                text="Zone",
                font=dict(size=9, color=CLR_WARNING, family="Inter, sans-serif"),
                x=0.5, xanchor="center",
            ),
            xaxis=dict(showticklabels=False, zeroline=False),
            yaxis=dict(autorange="reversed", showticklabels=False,
                       gridcolor=grid_clr, showgrid=True, zeroline=False),
        )
        track_divs.append(
            html.Div(
                dcc.Graph(
                    figure=zone_fig,
                    responsive=False,
                    config={"displayModeBar": False},
                    style={"display": "block"},
                ),
                style={
                    "display":    "inline-block",
                    "flexShrink": "0",
                    "width":      "55px",
                    "verticalAlign": "top",
                }
            )
        )

    # ── Zone legend bar ──
    legend = html.Div([
        *[
            html.Span([
                html.Div(style={
                    "width": "10px", "height": "10px", "borderRadius": "2px",
                    "backgroundColor": ZONE_COLORS[z],
                    "display": "inline-block", "marginRight": "4px",
                    "verticalAlign": "middle",
                }),
                html.Span(z, style={"fontSize": "11px", "marginRight": "12px",
                                    "color": CLR_MUTED}),
            ])
            for z in ["Gas", "Oil", "Water", "No Show"]
        ]
    ], style={
        "display": "flex", "alignItems": "center", "justifyContent": "center",
        "marginBottom": "8px", "flexWrap": "wrap",
    })

    scroll_container = html.Div(
        track_divs,
        style={
            "display":         "flex",
            "flexDirection":   "row",
            "alignItems":      "flex-start",
            "overflowX":       "auto",
            "overflowY":       "auto",
            "backgroundColor": "#070c18",
            "borderRadius":    "8px",
            "border":          f"1px solid {_hex_to_rgba(CLR_MUTED, 0.2)}",
            "padding":         "0",
            "maxHeight":       f"{chart_height + 60}px",
        }
    )

    return html.Div([legend, scroll_container])


def _build_separate_column_charts(df):
    """Creates a responsive multi-card grid where every single column is an individual graph that wraps cleanly."""
    depth = df['DEPTH'].values
    grid_clr = _hex_to_rgba(CLR_MUTED, 0.15)

    column_specs = [
        # (col_key, title, color, scale_type)
        ("C1",           "C1 (Methane)",   "#38bdf8", "log"),
        ("C2",           "C2 (Ethane)",    "#818cf8", "log"),
        ("C3",           "C3 (Propane)",   "#f472b6", "log"),
        ("IC4",          "iC4",            "#fb923c", "log"),
        ("NC4",          "nC4",            "#facc15", "log"),
        ("IC5",          "iC5",            "#34d399", "log"),
        ("NC5",          "nC5",            "#a78bfa", "log"),
        ("TG_USED",      "Total Gas",      "#e2e8f0", "log"),
        ("R1_C1_C2",     "C1/C2 Ratio",    "#38bdf8", "log"),
        ("R2_C1_C3",     "C1/C3 Ratio",    "#818cf8", "log"),
        ("R3_C2_C3",     "C2/C3 Ratio",    "#f472b6", "log"),
        ("R4_C1_IC4",    "C1/iC4 Ratio",   "#fb923c", "log"),
        ("R5_C1_NC4",    "C1/nC4 Ratio",   "#facc15", "log"),
        ("WH",           "Wh (Wetness)",   "#22c55e", "linear"),
        ("BH",           "Bh (Balance)",   "#f59e0b", "linear"),
        ("CH",           "Ch (Character)", "#ef4444", "linear"),
        ("DRYNESS",      "Dryness",        "#38bdf8", "linear"),
        ("CARBON_INDEX", "Carbon Index",   "#818cf8", "linear"),
        ("WBS",          "WBS Score",      "#f59e0b", "linear"),
        ("GOW",          "GOW Indicator",  "#a78bfa", "log"),
        ("GOW_NOTG",     "GOW / TG Ratio", "#ef4444", "linear"),
        ("GOR",          "GOR Index",      "#34d399", "linear"),
    ]

    cols = []
    for col_key, title, color, scale_type in column_specs:
        if col_key not in df.columns:
            continue

        vals = df[col_key].replace([np.inf, -np.inf], np.nan).values.astype(float)
        x_plot = np.where(vals > 0, vals, np.nan) if scale_type == "log" else vals

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_plot, y=depth, mode="lines", name=title,
            line=dict(color=color, width=1.8),
            fill="tozerox", fillcolor=_hex_to_rgba(color, 0.12),
            hovertemplate=f"Depth: %{{y:.1f}}m<br>{title}: %{{x:.3f}}<extra></extra>",
        ))

        fig.update_layout(
            title=dict(text=title, font=dict(size=12, color=CLR_ACCENT, family="Inter, sans-serif")),
            height=380,
            autosize=True,
            template="plotly_dark",
            paper_bgcolor=CLR_BG,
            plot_bgcolor="#0f172a",
            font=dict(family="Inter, sans-serif", size=10, color=CLR_TEXT),
            showlegend=False,
            margin=dict(l=50, r=15, t=35, b=35),
            xaxis=dict(type="log" if scale_type == "log" else "linear", gridcolor=grid_clr, tickfont=dict(size=9)),
            yaxis=dict(autorange="reversed", title=dict(text="Depth (m)", font=dict(size=10)), gridcolor=grid_clr, tickfont=dict(size=9)),
            uirevision="depth_sync",
        )

        card = dbc.Card([
            dbc.CardHeader(
                html.Span(title, style={"fontWeight": "600", "fontSize": "13px", "color": CLR_TEXT}),
                style={"background": CLR_CARD, "borderBottom": f"1px solid {CLR_MUTED}33", "padding": "8px 12px", "borderLeft": f"3px solid {color}"}
            ),
            dbc.CardBody(
                dcc.Graph(
                    figure=fig,
                    responsive=True,
                    config={"scrollZoom": True, "displayModeBar": False},
                    style={"width": "100%", "height": "380px"}
                ),
                style={"background": CLR_BG, "padding": "0"}
            )
        ], style={"background": CLR_CARD, "border": f"1px solid {CLR_MUTED}22", "borderRadius": "10px", "height": "100%"})

        cols.append(dbc.Col(card, xs=12, sm=6, md=4, lg=3, className="mb-3"))

    # Zone classification card
    zone_vals = df['ZONE'].values if 'ZONE' in df.columns else np.array(["No Show"] * len(df))
    zone_numeric, zone_colors_list = [], []
    for z in zone_vals:
        if z == "Gas":
            zone_numeric.append(3); zone_colors_list.append(ZONE_COLORS["Gas"])
        elif z == "Oil":
            zone_numeric.append(2); zone_colors_list.append(ZONE_COLORS["Oil"])
        elif z == "Water":
            zone_numeric.append(1); zone_colors_list.append(ZONE_COLORS["Water"])
        else:
            zone_numeric.append(0); zone_colors_list.append(ZONE_COLORS["No Show"])

    zone_fig = go.Figure(go.Bar(
        x=zone_numeric, y=depth, orientation="h",
        marker=dict(color=zone_colors_list),
        name="Zone", hovertext=zone_vals, hoverinfo="text+y",
        showlegend=False, width=0.8
    ))
    zone_fig.update_xaxes(showticklabels=False, gridcolor=grid_clr)
    zone_fig.update_yaxes(autorange="reversed", title=dict(text="Depth (m)", font=dict(size=10)), gridcolor=grid_clr)
    zone_fig.update_layout(
        title=dict(text="Zone Classification", font=dict(size=12, color=CLR_WARNING, family="Inter, sans-serif")),
        height=380,
        autosize=True,
        template="plotly_dark",
        paper_bgcolor=CLR_BG,
        plot_bgcolor="#0f172a",
        font=dict(family="Inter, sans-serif", size=10, color=CLR_TEXT),
        margin=dict(l=50, r=15, t=35, b=35),
    )

    zone_card = dbc.Card([
        dbc.CardHeader(
            html.Span("Zone Classification Log", style={"fontWeight": "600", "fontSize": "13px", "color": CLR_TEXT}),
            style={"background": CLR_CARD, "borderBottom": f"1px solid {CLR_MUTED}33", "padding": "8px 12px", "borderLeft": f"3px solid {CLR_WARNING}"}
        ),
        dbc.CardBody(
            dcc.Graph(
                figure=zone_fig,
                responsive=True,
                config={"scrollZoom": True, "displayModeBar": False},
                style={"width": "100%", "height": "380px"}
            ),
            style={"background": CLR_BG, "padding": "0"}
        )
    ], style={"background": CLR_CARD, "border": f"1px solid {CLR_MUTED}22", "borderRadius": "10px", "height": "100%"})

    cols.append(dbc.Col(zone_card, xs=12, sm=6, md=4, lg=3, className="mb-3"))

    return dbc.Row(cols, className="g-3")




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
                           fill="tozerox", fillcolor=_hex_to_rgba(color, 0.08)),
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
        autosize=True,
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
    grid_clr = _hex_to_rgba(CLR_MUTED, 0.15)
    fig.update_xaxes(title_text="PPM", row=1, col=1, type="log",
                     gridcolor=grid_clr)
    fig.update_xaxes(title_text="Ratio", row=1, col=2, type="log",
                     gridcolor=grid_clr)
    fig.update_xaxes(title_text="Value", row=1, col=3, type="log",
                     gridcolor=grid_clr)
    fig.update_xaxes(title_text="Value", row=1, col=4,
                     gridcolor=grid_clr)
    fig.update_xaxes(title_text="Zone", row=1, col=5,
                     showticklabels=False, gridcolor=grid_clr)

    fig.update_yaxes(title_text="Depth (m)", row=1, col=1,
                     gridcolor=grid_clr)

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
        dcc.Graph(
            figure=fig,
            responsive=True,
            config={"scrollZoom": True, "displayModeBar": True},
            style={"borderRadius": "12px", "width": "100%", "height": f"{chart_height}px"},
        ),
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
