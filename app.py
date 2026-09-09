"""
MudLog Pro — Continuous Multi-Track Depth Log (Dash Python)
===========================================================
Interactive single-page Dash application featuring a clean, full-screen
continuous multi-track well log where every hydrocarbon gas, ratio,
and petrophysical indicator has its own dedicated track column.

Features:
  • Configuration Dropdown with dynamic pipeline controls
  • Petrophysical Formula & Indicator Manager Modal (edit formulas, live preview, threshold limits)
  • Column Configuration & Display Manager Modal (Show/Hide, Add New Column, Delete Column)
  • Real-time deterministic recomputation of well logs and fluid facies zones
  • Upload and CSV Export
"""

import io
import json
import base64
import webbrowser
import threading
import numpy as np
import pandas as pd

import dash
from dash import dcc, html, no_update, ctx
from dash.dependencies import Input, Output, State, ALL
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Local imports
from parser import parse_mudlog_file
from engine import compute_all, eval_expr, DEFAULT_FORMULAS


# ──────────────────────────────────────────────────────────────────────
#  Theme & Color Palette
# ──────────────────────────────────────────────────────────────────────
CLR_BG         = "#090d16"
CLR_SURFACE    = "#0f172a"
CLR_CARD       = "#111827"
CLR_BORDER     = "rgba(51, 65, 85, 0.5)"
CLR_ACCENT     = "#6366f1"  # Indigo
CLR_CYAN       = "#38bdf8"  # Sky/Cyan
CLR_SUCCESS    = "#10b981"  # Emerald
CLR_WARNING    = "#f59e0b"  # Amber
CLR_DANGER     = "#f43f5e"  # Rose
CLR_TEXT       = "#f1f5f9"  # Slate 100
CLR_MUTED      = "#94a3b8"  # Slate 400
CLR_DARK_MUTED = "#64748b"  # Slate 500

ZONE_COLORS = {
    "Gas":     "#10b981",
    "Oil":     "#f43f5e",
    "Water":   "#0284c7",
    "No Show": "#475569",
}

# Default 24-Track Continuous Multi-Track Specifications
DEFAULT_TRACK_SCHEMA = [
    {"id": "C1",           "key": "C1",           "name": "C1",      "unit": "ppm",   "color": "#38bdf8", "scale": "log",    "visible": True,  "is_custom": False},
    {"id": "C2",           "key": "C2",           "name": "C2",      "unit": "ppm",   "color": "#818cf8", "scale": "log",    "visible": True,  "is_custom": False},
    {"id": "C3",           "key": "C3",           "name": "C3",      "unit": "ppm",   "color": "#f472b6", "scale": "log",    "visible": True,  "is_custom": False},
    {"id": "IC4",          "key": "IC4",          "name": "iC4",     "unit": "ppm",   "color": "#fb923c", "scale": "log",    "visible": True,  "is_custom": False},
    {"id": "NC4",          "key": "NC4",          "name": "nC4",     "unit": "ppm",   "color": "#facc15", "scale": "log",    "visible": True,  "is_custom": False},
    {"id": "IC5",          "key": "IC5",          "name": "iC5",     "unit": "ppm",   "color": "#34d399", "scale": "log",    "visible": True,  "is_custom": False},
    {"id": "NC5",          "key": "NC5",          "name": "nC5",     "unit": "ppm",   "color": "#a78bfa", "scale": "log",    "visible": True,  "is_custom": False},
    {"id": "TG",           "key": "TG_USED",      "name": "TG",      "unit": "ppm",   "color": "#ffffff", "scale": "log",    "visible": True,  "is_custom": False},
    {"id": "R1_C1_C2",     "key": "R1_C1_C2",     "name": "C1/C2",   "unit": "ratio", "color": "#38bdf8", "scale": "log",    "visible": True,  "is_custom": False},
    {"id": "R2_C1_C3",     "key": "R2_C1_C3",     "name": "C1/C3",   "unit": "ratio", "color": "#818cf8", "scale": "log",    "visible": True,  "is_custom": False},
    {"id": "C2_C1",        "key": "C2_C1",        "name": "C2/C1",   "unit": "ratio", "color": "#38bdf8", "scale": "log",    "visible": True,  "is_custom": False},
    {"id": "C3_C1",        "key": "C3_C1",        "name": "C3/C1",   "unit": "ratio", "color": "#818cf8", "scale": "log",    "visible": True,  "is_custom": False},
    {"id": "R3_C2_C3",     "key": "R3_C2_C3",     "name": "C2/C3",   "unit": "ratio", "color": "#f472b6", "scale": "log",    "visible": True,  "is_custom": False},
    {"id": "R4_C1_IC4",    "key": "R4_C1_IC4",    "name": "C1/iC4",  "unit": "ratio", "color": "#fb923c", "scale": "log",    "visible": True,  "is_custom": False},
    {"id": "R5_C1_NC4",    "key": "R5_C1_NC4",    "name": "C1/nC4",  "unit": "ratio", "color": "#facc15", "scale": "log",    "visible": True,  "is_custom": False},
    {"id": "WH",           "key": "WH",           "name": "Wh%",     "unit": "%",     "color": "#22c55e", "scale": "linear", "visible": True,  "is_custom": False},
    {"id": "BH",           "key": "BH",           "name": "Bh",      "unit": "index", "color": "#f59e0b", "scale": "linear", "visible": True,  "is_custom": False},
    {"id": "CH",           "key": "CH",           "name": "Ch",      "unit": "index", "color": "#ef4444", "scale": "linear", "visible": True,  "is_custom": False},
    {"id": "DRYNESS",      "key": "DRYNESS",      "name": "Dryness", "unit": "ratio", "color": "#38bdf8", "scale": "linear", "visible": True,  "is_custom": False},
    {"id": "CARBON_INDEX", "key": "CARBON_INDEX", "name": "Ci",      "unit": "index", "color": "#818cf8", "scale": "linear", "visible": True,  "is_custom": False},
    {"id": "WBS",          "key": "WBS",          "name": "WBS",     "unit": "score", "color": "#f59e0b", "scale": "linear", "visible": True,  "is_custom": False},
    {"id": "GOW",          "key": "GOW",          "name": "GOW",     "unit": "index", "color": "#a78bfa", "scale": "log",    "visible": True,  "is_custom": False},
    {"id": "GOW_NOTG",     "key": "GOW_NOTG",     "name": "GOW/TG",  "unit": "ratio", "color": "#ef4444", "scale": "linear", "visible": True,  "is_custom": False},
    {"id": "GOR",          "key": "GOR",          "name": "GOR",     "unit": "flag",  "color": "#34d399", "scale": "linear", "visible": True,  "is_custom": False},
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
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap",
    ],
    suppress_callback_exceptions=True,
    title="Mudlogging",
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
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
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
            .var-tag {
                background: rgba(56, 189, 248, 0.12);
                color: #38bdf8;
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 6px;
                padding: 2px 8px;
                font-size: 11px;
                font-family: 'JetBrains Mono', monospace;
                cursor: pointer;
                transition: all 0.15s ease;
                display: inline-block;
                margin: 2px;
                user-select: none;
            }
            .var-tag:hover {
                background: rgba(56, 189, 248, 0.28);
                border-color: #38bdf8;
                transform: translateY(-1px);
            }
            .dropdown-menu {
                background-color: #0f172a !important;
                border: 1px solid rgba(51, 65, 85, 0.6) !important;
                border-radius: 10px !important;
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.6) !important;
            }
            .dropdown-item {
                color: #e2e8f0 !important;
                font-size: 12.5px !important;
                padding: 8px 16px !important;
                transition: background 0.15s ease;
            }
            .dropdown-item:hover {
                background-color: rgba(99, 102, 241, 0.2) !important;
                color: #ffffff !important;
            }
            .form-control, .form-select {
                background-color: #0b1120 !important;
                border: 1px solid rgba(51, 65, 85, 0.7) !important;
                color: #f1f5f9 !important;
                border-radius: 8px !important;
                font-size: 13px !important;
            }
            .form-control:focus, .form-select:focus {
                border-color: #6366f1 !important;
                box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.25) !important;
            }
            .nav-tabs .nav-link {
                color: #94a3b8 !important;
                border: none !important;
                border-bottom: 2px solid transparent !important;
                font-size: 13px !important;
                font-weight: 600 !important;
                padding: 8px 16px !important;
            }
            .nav-tabs .nav-link.active {
                background: transparent !important;
                color: #38bdf8 !important;
                border-bottom: 2px solid #38bdf8 !important;
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
#  Modal 1: Column Configuration & Display Manager (Show/Hide, Add, Remove)
# ──────────────────────────────────────────────────────────────────────
columns_modal = dbc.Modal(
    [
        dbc.ModalHeader(
            dbc.ModalTitle(
                html.Div([
                    html.I(className="fa-solid fa-table-columns me-2", style={"color": CLR_CYAN}),
                    "Column Configuration & Display Manager",
                ]),
                style={"color": CLR_TEXT, "fontSize": "16px", "fontWeight": "700"},
            ),
            close_button=True,
            style={"background": CLR_SURFACE, "borderBottom": f"1px solid {CLR_BORDER}"},
        ),
        dbc.ModalBody([
            dbc.Tabs(
                [
                    dbc.Tab(
                        label="Show / Hide Columns",
                        tab_id="tab-col-visibility",
                        children=[
                            html.Div([
                                html.Div([
                                    html.Span("Toggle individual tracks on the continuous well log:", style={"fontSize": "12px", "color": CLR_MUTED}),
                                    html.Div([
                                        dbc.Button("Select All", id="btn-col-select-all", color="secondary", outline=True, size="sm", className="me-2 py-1 px-2", style={"fontSize": "11px", "borderRadius": "6px"}),
                                        dbc.Button("Deselect All", id="btn-col-deselect-all", color="secondary", outline=True, size="sm", className="py-1 px-2", style={"fontSize": "11px", "borderRadius": "6px"}),
                                    ]),
                                ], className="d-flex justify-content-between align-items-center mb-3 mt-3"),
                                html.Div(id="column-checklist-container", style={"maxHeight": "320px", "overflowY": "auto", "paddingRight": "5px"}),
                            ]),
                        ],
                    ),
                    dbc.Tab(
                        label="Add New Column",
                        tab_id="tab-col-add",
                        children=[
                            html.Div([
                                html.Div([
                                    html.Label("Column Identifier Name", style={"fontSize": "12px", "fontWeight": "600", "color": CLR_TEXT, "marginBottom": "4px"}),
                                    dbc.Input(id="new-col-name-input", type="text", placeholder="e.g. C1_C4_Iso_Ratio or Custom_Dryness", className="mb-2"),
                                ]),
                                html.Div([
                                    html.Div([
                                        html.Label("Unit / Dimension", style={"fontSize": "12px", "fontWeight": "600", "color": CLR_TEXT, "marginBottom": "4px"}),
                                        dbc.Input(id="new-col-unit-input", type="text", placeholder="e.g. ratio, %, ppm, score", className="mb-2"),
                                    ], className="col-4 pe-2"),
                                    html.Div([
                                        html.Label("Scale Type", style={"fontSize": "12px", "fontWeight": "600", "color": CLR_TEXT, "marginBottom": "4px"}),
                                        dbc.Select(
                                            id="new-col-scale-select",
                                            options=[
                                                {"label": "Logarithmic Scale (log)", "value": "log"},
                                                {"label": "Linear Scale (linear)", "value": "linear"},
                                            ],
                                            value="log",
                                            className="mb-2",
                                        ),
                                    ], className="col-5 pe-2"),
                                    html.Div([
                                        html.Label("Track Color", style={"fontSize": "12px", "fontWeight": "600", "color": CLR_TEXT, "marginBottom": "4px"}),
                                        dbc.Input(id="new-col-color-input", type="color", value="#38bdf8", style={"height": "36px", "padding": "2px"}, className="mb-2"),
                                    ], className="col-3"),
                                ], className="row g-0"),
                                html.Div([
                                    html.Label("Computation Expression (Python / Math Syntax)", style={"fontSize": "12px", "fontWeight": "600", "color": CLR_TEXT, "marginBottom": "4px"}),
                                    dbc.Input(id="new-col-expr-input", type="text", placeholder="e.g. C1 / (IC4 + NC4 + 0.001)", style={"fontFamily": "'JetBrains Mono', monospace"}, className="mb-1"),
                                    html.Div([
                                        html.Span("Quick Insert: ", style={"fontSize": "11px", "color": CLR_MUTED, "marginRight": "4px"}),
                                        html.Span("C1", id={"type": "btn-newcol-token", "token": "C1"}, className="var-tag"),
                                        html.Span("C2", id={"type": "btn-newcol-token", "token": "C2"}, className="var-tag"),
                                        html.Span("C3", id={"type": "btn-newcol-token", "token": "C3"}, className="var-tag"),
                                        html.Span("IC4", id={"type": "btn-newcol-token", "token": "IC4"}, className="var-tag"),
                                        html.Span("NC4", id={"type": "btn-newcol-token", "token": "NC4"}, className="var-tag"),
                                        html.Span("IC5", id={"type": "btn-newcol-token", "token": "IC5"}, className="var-tag"),
                                        html.Span("NC5", id={"type": "btn-newcol-token", "token": "NC5"}, className="var-tag"),
                                        html.Span("TG", id={"type": "btn-newcol-token", "token": "TG"}, className="var-tag"),
                                        html.Span("WH", id={"type": "btn-newcol-token", "token": "WH"}, className="var-tag"),
                                        html.Span("BH", id={"type": "btn-newcol-token", "token": "BH"}, className="var-tag"),
                                    ], className="d-flex align-items-center flex-wrap mb-3"),
                                ]),
                                dbc.Button(
                                    [html.I(className="fa-solid fa-plus me-2"), "Add Graph Column"],
                                    id="btn-submit-new-column",
                                    color="primary",
                                    size="sm",
                                    style={"borderRadius": "8px", "fontWeight": "600", "background": "#6366f1", "border": "none"},
                                ),
                                html.Div(id="add-column-status", className="mt-2"),
                            ], className="py-3"),
                        ],
                    ),
                    dbc.Tab(
                        label="Remove Columns",
                        tab_id="tab-col-remove",
                        children=[
                            html.Div([
                                html.Div("Delete custom or non-essential columns from the current schema:", style={"fontSize": "12px", "color": CLR_MUTED, "marginBottom": "12px", "marginTop": "12px"}),
                                html.Div(id="remove-columns-container", style={"maxHeight": "320px", "overflowY": "auto"}),
                            ]),
                        ],
                    ),
                ],
                id="column-tabs",
                active_tab="tab-col-visibility",
            ),
        ], style={"background": CLR_SURFACE, "padding": "20px"}),
        dbc.ModalFooter([
            dbc.Button("Close", id="btn-close-col-modal", color="secondary", outline=True, size="sm", style={"borderRadius": "8px"}),
            dbc.Button(
                [html.I(className="fa-solid fa-floppy-disk me-2"), "Apply & Update Log Tracks"],
                id="btn-apply-columns",
                color="primary",
                size="sm",
                style={"borderRadius": "8px", "fontWeight": "600", "background": "#6366f1", "border": "none"},
            ),
        ], style={"background": CLR_SURFACE, "borderTop": f"1px solid {CLR_BORDER}"}),
    ],
    id="columns-modal",
    is_open=False,
    centered=True,
    size="lg",
    style={"backdropFilter": "blur(8px)"},
)


# ──────────────────────────────────────────────────────────────────────
#  Modal 2: Petrophysical Formula & Indicator Manager
# ──────────────────────────────────────────────────────────────────────
FORMULA_SELECT_OPTIONS = [
    {"label": "Haworth Wetness (Wh) — Richness Indicator", "value": "WH"},
    {"label": "Haworth Balance (Bh) — Gas-Oil Contact", "value": "BH"},
    {"label": "Haworth Character (Ch) — Fluid Confirmation", "value": "CH"},
    {"label": "Pixler R1 (C1 / C2) — Dry Gas Delineation", "value": "R1_C1_C2"},
    {"label": "Pixler R2 (C1 / C3) — Gas-Liquid Contact", "value": "R2_C1_C3"},
    {"label": "Pixler R3 (C2 / C3) — Heavy Multiplier", "value": "R3_C2_C3"},
    {"label": "Ratio 4 (C1 / iC4) — Iso-Butane Sensitivity", "value": "R4_C1_IC4"},
    {"label": "Ratio 5 (C1 / nC4) — Normal-Butane Sensitivity", "value": "R5_C1_NC4"},
    {"label": "Dryness Ratio (C1 / TG)", "value": "DRYNESS"},
    {"label": "Carbon Density Index (Ci)", "value": "CARBON_INDEX"},
    {"label": "Composite GOW", "value": "GOW"},
    {"label": "GOW No-TG (Normalized Heavy Fraction)", "value": "GOW_NOTG"},
    {"label": "Wetness-Balance Score (WBS)", "value": "WBS"},
    {"label": "Gas-Oil Ratio (GOR) Screening", "value": "GOR"},
]

formulas_modal = dbc.Modal(
    [
        dbc.ModalHeader(
            dbc.ModalTitle(
                html.Div([
                    html.I(className="fa-solid fa-square-root-variable me-2", style={"color": CLR_WARNING}),
                    "Petrophysical Formula & Indicator Manager",
                ]),
                style={"color": CLR_TEXT, "fontSize": "16px", "fontWeight": "700"},
            ),
            close_button=True,
            style={"background": CLR_SURFACE, "borderBottom": f"1px solid {CLR_BORDER}"},
        ),
        dbc.ModalBody([
            html.Div([
                html.Label("Select Petrophysical Indicator Formula to Edit", style={"fontSize": "12px", "fontWeight": "600", "color": CLR_TEXT, "marginBottom": "6px"}),
                dbc.Select(
                    id="formula-select",
                    options=FORMULA_SELECT_OPTIONS,
                    value="WH",
                    className="mb-3",
                ),

                html.Label("Mathematical Expression (Python / LaTeX Engine Syntax)", style={"fontSize": "12px", "fontWeight": "600", "color": CLR_TEXT, "marginBottom": "4px"}),
                dbc.Input(
                    id="formula-expr-input",
                    type="text",
                    value=DEFAULT_FORMULAS["WH"]["expr"],
                    style={"fontFamily": "'JetBrains Mono', monospace", "fontSize": "13px"},
                    className="mb-1",
                ),

                # Quick Variable Insert Tags
                html.Div([
                    html.Span("Insert Variable: ", style={"fontSize": "11px", "color": CLR_MUTED, "marginRight": "4px"}),
                    html.Span("C1", id={"type": "btn-formula-token", "token": "C1"}, className="var-tag"),
                    html.Span("C2", id={"type": "btn-formula-token", "token": "C2"}, className="var-tag"),
                    html.Span("C3", id={"type": "btn-formula-token", "token": "C3"}, className="var-tag"),
                    html.Span("IC4", id={"type": "btn-formula-token", "token": "IC4"}, className="var-tag"),
                    html.Span("NC4", id={"type": "btn-formula-token", "token": "NC4"}, className="var-tag"),
                    html.Span("IC5", id={"type": "btn-formula-token", "token": "IC5"}, className="var-tag"),
                    html.Span("NC5", id={"type": "btn-formula-token", "token": "NC5"}, className="var-tag"),
                    html.Span("TG", id={"type": "btn-formula-token", "token": "TG"}, className="var-tag"),
                    html.Span("log10(", id={"type": "btn-formula-token", "token": "log10("}, className="var-tag"),
                    html.Span("sqrt(", id={"type": "btn-formula-token", "token": "sqrt("}, className="var-tag"),
                ], className="d-flex align-items-center flex-wrap mb-3"),

                # Boundary Cutoff Thresholds Display
                html.Div([
                    html.Div("Deterministic Fluid Classification Thresholds", style={"fontSize": "11px", "fontWeight": "700", "color": CLR_MUTED, "marginBottom": "6px", "textTransform": "uppercase"}),
                    html.Div([
                        html.Div([
                            html.Span("🟢 Gas Zone Limit: ", style={"fontSize": "12px", "fontWeight": "600", "color": "#10b981"}),
                            html.Span(id="formula-thresh-gas", children=DEFAULT_FORMULAS["WH"]["gas"], style={"fontSize": "12px", "fontFamily": "'JetBrains Mono', monospace"}),
                        ], className="col-4"),
                        html.Div([
                            html.Span("🔴 Oil Zone Limit: ", style={"fontSize": "12px", "fontWeight": "600", "color": "#f43f5e"}),
                            html.Span(id="formula-thresh-oil", children=DEFAULT_FORMULAS["WH"]["oil"], style={"fontSize": "12px", "fontFamily": "'JetBrains Mono', monospace"}),
                        ], className="col-4"),
                        html.Div([
                            html.Span("🔵 Water Limit: ", style={"fontSize": "12px", "fontWeight": "600", "color": "#38bdf8"}),
                            html.Span(id="formula-thresh-water", children=DEFAULT_FORMULAS["WH"]["water"], style={"fontSize": "12px", "fontFamily": "'JetBrains Mono', monospace"}),
                        ], className="col-4"),
                    ], className="row g-2"),
                ], style={"background": "rgba(16, 26, 46, 0.6)", "border": f"1px solid {CLR_BORDER}", "borderRadius": "8px", "padding": "10px 14px", "marginBottom": "14px"}),

                # Live Evaluation Test Box
                html.Div([
                    html.Label("Live Verification on Well Log Sample Interval", style={"fontSize": "11px", "fontWeight": "700", "color": CLR_MUTED, "textTransform": "uppercase", "marginBottom": "4px"}),
                    html.Div(
                        id="formula-live-preview",
                        style={
                            "background": "#070c18",
                            "border": f"1px solid {CLR_BORDER}",
                            "borderRadius": "8px",
                            "padding": "10px 14px",
                            "fontSize": "12px",
                            "fontFamily": "'JetBrains Mono', monospace",
                            "color": "#38bdf8",
                            "minHeight": "48px",
                        },
                    ),
                ]),

                html.Div(id="formula-status-msg", className="mt-2"),
            ]),
        ], style={"background": CLR_SURFACE, "padding": "20px"}),
        dbc.ModalFooter([
            dbc.Button(
                [html.I(className="fa-solid fa-rotate-left me-1"), "Restore Skripsi Default"],
                id="btn-restore-formula-default",
                color="secondary",
                outline=True,
                size="sm",
                style={"borderRadius": "8px", "fontSize": "12px"},
            ),
            dbc.Button(
                [html.I(className="fa-solid fa-check-double me-1"), "Save & Recompute Log Curves"],
                id="btn-save-formula",
                color="primary",
                size="sm",
                style={"borderRadius": "8px", "fontSize": "12px", "fontWeight": "600", "background": "#6366f1", "border": "none"},
            ),
        ], style={"background": CLR_SURFACE, "borderTop": f"1px solid {CLR_BORDER}"}),
    ],
    id="formulas-modal",
    is_open=False,
    centered=True,
    size="lg",
    style={"backdropFilter": "blur(8px)"},
)


# ──────────────────────────────────────────────────────────────────────
#  Top Navbar with Configuration Dropdown
# ──────────────────────────────────────────────────────────────────────
navbar = html.Header(
    html.Div([
        # Brand
        html.Div([
            html.Div([
                html.I(className="fa-solid fa-gas-pump", style={"fontSize": "16px", "color": "#ffffff"}),
            ], style={
                "width": "32px", "height": "32px", "borderRadius": "8px",
                "background": "linear-gradient(135deg, #6366f1 0%, #10b981 100%)",
                "display": "flex", "alignItems": "center", "justifyContent": "center",
                "marginRight": "10px"
            }),
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

        # Controls (Configuration Dropdown + Upload Modal Button + Export CSV)
        html.Div([
            # Configuration Dropdown
            dbc.DropdownMenu(
                label="Configuration",
                children=[
                    dbc.DropdownMenuItem([
                        html.Div([
                            html.I(className="fa-solid fa-table-columns me-2", style={"color": CLR_CYAN}),
                            html.Span("Edit Columns", style={"fontWeight": "600"}),
                            html.Div("Hide, show, add or remove tracks", style={"fontSize": "10px", "color": CLR_MUTED}),
                        ]),
                    ], id="dropdown-item-columns"),
                    dbc.DropdownMenuItem([
                        html.Div([
                            html.I(className="fa-solid fa-square-root-variable me-2", style={"color": CLR_WARNING}),
                            html.Span("Edit Formulas", style={"fontWeight": "600"}),
                            html.Div("Customize petrophysical ratios", style={"fontSize": "10px", "color": CLR_MUTED}),
                        ]),
                    ], id="dropdown-item-formulas"),
                    dbc.DropdownMenuItem(divider=True),
                    dbc.DropdownMenuItem([
                        html.Div([
                            html.I(className="fa-solid fa-rotate-left me-2", style={"color": CLR_DANGER}),
                            html.Span("Reset to Skripsi Defaults"),
                            html.Div("Restore standard indicators & schema", style={"fontSize": "10px", "color": CLR_MUTED}),
                        ]),
                    ], id="dropdown-item-reset"),
                ],
                size="sm",
                color="secondary",
                className="me-2",
                toggle_style={"borderRadius": "8px", "fontSize": "12px", "fontWeight": "600", "borderColor": "rgba(51, 65, 85, 0.8)", "background": "rgba(30, 41, 59, 0.8)"},
            ),

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
    columns_modal,
    formulas_modal,
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

        # 3. Dynamic State Stores
        dcc.Store(id="store-raw", data=INIT_RAW_DF.to_json(orient="split", date_format="iso")),
        dcc.Store(id="store-computed", data=INIT_COMPUTED_DF.to_json(orient="split", date_format="iso")),
        dcc.Store(id="store-schema", data=DEFAULT_TRACK_SCHEMA),
        dcc.Store(id="store-formulas", data={k: v["expr"] for k, v in DEFAULT_FORMULAS.items()}),
        dcc.Store(id="store-custom-cols", data=[]),
        dcc.Download(id="download-report"),

    ], style={"width": "100%", "padding": "10px 18px 30px 18px"}),
], style={"background": CLR_BG, "minHeight": "100vh", "color": CLR_TEXT, "overflowX": "hidden"})


# ──────────────────────────────────────────────────────────────────────
#  Header Info Callback
# ──────────────────────────────────────────────────────────────────────
@app.callback(
    Output("track-header-info", "children"),
    [Input("store-computed", "data"),
     Input("store-schema", "data")]
)
def update_header_info(json_computed, schema):
    if not json_computed:
        return ""
    df = pd.read_json(io.StringIO(json_computed), orient="split")
    d_min = df["DEPTH"].min()
    d_max = df["DEPTH"].max()
    pts = len(df)
    active_count = sum(1 for s in (schema or []) if s.get("visible", True))
    return [
        html.I(className="fa-solid fa-ruler-vertical text-info me-1"),
        f"Depth: {d_min:.0f}m – {d_max:.0f}m ({d_max - d_min:.0f}m span • {pts} intervals) • {active_count} tracks active",
    ]


# ──────────────────────────────────────────────────────────────────────
#  Full Continuous Multi-Track Well Log Builder (Fits 100% Screen Width)
# ──────────────────────────────────────────────────────────────────────
@app.callback(
    Output("tracks-container", "children"),
    [Input("store-computed", "data"),
     Input("store-schema", "data")]
)
def render_full_continuous_tracks(json_computed, schema):
    if not json_computed:
        return html.Div("No data loaded.", style={"color": CLR_MUTED, "padding": "40px", "textAlign": "center"})

    df = pd.read_json(io.StringIO(json_computed), orient="split")
    filtered_df = df

    depth = filtered_df["DEPTH"].values
    grid_clr = "rgba(51, 65, 85, 0.22)"
    chart_height = 840

    track_specs = schema if schema else DEFAULT_TRACK_SCHEMA
    active_specs = [s for s in track_specs if s.get("visible", True) and s.get("key") in filtered_df.columns]
    has_zone = "ZONE" in filtered_df.columns
    total_cols = len(active_specs) + (1 if has_zone else 0)

    if total_cols == 0:
        return html.Div("No active tracks selected. Open Configuration > Edit Columns to enable tracks.", style={"color": CLR_MUTED, "padding": "40px", "textAlign": "center"})

    titles = [s.get("name", s.get("key")) for s in active_specs] + (["Zone"] if has_zone else [])

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

    for i, spec in enumerate(active_specs, start=1):
        col_key = spec.get("key")
        title = spec.get("name", col_key)
        color = spec.get("color", "#38bdf8")
        scale_type = spec.get("scale", "log")

        vals = filtered_df[col_key].replace([np.inf, -np.inf], np.nan).values.astype(float)
        x_plot = np.where(vals > 0, vals, np.nan) if scale_type == "log" else vals

        # Safe color parsing for fill rgba
        try:
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            fill_color = f"rgba({r}, {g}, {b}, 0.18)"
        except Exception:
            fill_color = "rgba(56, 189, 248, 0.18)"

        fig.add_trace(
            go.Scatter(
                x=x_plot, y=depth, mode="lines", name=title,
                line=dict(color=color, width=1.4),
                fill="tozerox", fillcolor=fill_color,
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
#  Dynamic Recomputation Callback (Raw Data + Formulas + Custom Columns)
# ──────────────────────────────────────────────────────────────────────
@app.callback(
    Output("store-computed", "data"),
    [Input("store-raw", "data"),
     Input("store-formulas", "data"),
     Input("store-custom-cols", "data")]
)
def recompute_dataset(json_raw, formulas, custom_cols):
    if not json_raw:
        return no_update
    df_raw = pd.read_json(io.StringIO(json_raw), orient="split")
    computed_df = compute_all(df_raw, formula_overrides=formulas, custom_columns=custom_cols)
    return computed_df.to_json(orient="split", date_format="iso")


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
     Output("upload-status", "children"),
     Output("upload-modal", "is_open", allow_duplicate=True)],
    [Input("upload-data", "contents")],
    [State("upload-data", "filename")],
    prevent_initial_call=True
)
def handle_mudlog_upload(contents, filename):
    if not contents:
        return no_update, no_update, no_update

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
        status_msg = dbc.Alert(f"✅ Successfully loaded {filename} ({len(df)} depth intervals).", color="success", style={"fontSize": "12px", "borderRadius": "8px"})

        return (
            df.to_json(orient="split", date_format="iso"),
            status_msg,
            False
        )
    except Exception as e:
        status_msg = dbc.Alert(f"❌ Error loading file: {str(e)}", color="danger", style={"fontSize": "12px", "borderRadius": "8px"})
        return no_update, status_msg, no_update


# ──────────────────────────────────────────────────────────────────────
#  Modal Toggles & Reset Defaults (Configuration Dropdown)
# ──────────────────────────────────────────────────────────────────────
@app.callback(
    Output("columns-modal", "is_open"),
    [Input("dropdown-item-columns", "n_clicks"),
     Input("btn-close-col-modal", "n_clicks"),
     Input("btn-apply-columns", "n_clicks")],
    [State("columns-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_columns_modal(n_open, n_close, n_apply, is_open):
    return not is_open


@app.callback(
    Output("formulas-modal", "is_open"),
    [Input("dropdown-item-formulas", "n_clicks"),
     Input("btn-save-formula", "n_clicks")],
    [State("formulas-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_formulas_modal(n_open, n_save, is_open):
    return not is_open


@app.callback(
    [Output("store-schema", "data", allow_duplicate=True),
     Output("store-formulas", "data", allow_duplicate=True),
     Output("store-custom-cols", "data", allow_duplicate=True)],
    [Input("dropdown-item-reset", "n_clicks")],
    prevent_initial_call=True
)
def reset_to_defaults(n_clicks):
    if not n_clicks:
        return no_update, no_update, no_update
    return (
        DEFAULT_TRACK_SCHEMA,
        {k: v["expr"] for k, v in DEFAULT_FORMULAS.items()},
        []
    )


# ──────────────────────────────────────────────────────────────────────
#  Callbacks: Edit Formulas Modal (Select, Token Insert, Live Preview, Save)
# ──────────────────────────────────────────────────────────────────────
@app.callback(
    [Output("formula-expr-input", "value"),
     Output("formula-thresh-gas", "children"),
     Output("formula-thresh-oil", "children"),
     Output("formula-thresh-water", "children")],
    [Input("formula-select", "value"),
     Input("btn-restore-formula-default", "n_clicks")],
    [State("store-formulas", "data")],
    prevent_initial_call=False
)
def sync_formula_selection(selected_key, n_restore, current_formulas):
    if not selected_key or selected_key not in DEFAULT_FORMULAS:
        selected_key = "WH"

    triggered = ctx.triggered_id
    if triggered == "btn-restore-formula-default":
        expr = DEFAULT_FORMULAS[selected_key]["expr"]
    else:
        expr = (current_formulas or {}).get(selected_key, DEFAULT_FORMULAS[selected_key]["expr"])

    gas_lim = DEFAULT_FORMULAS[selected_key].get("gas", "-")
    oil_lim = DEFAULT_FORMULAS[selected_key].get("oil", "-")
    wat_lim = DEFAULT_FORMULAS[selected_key].get("water", "-")

    return expr, gas_lim, oil_lim, wat_lim


@app.callback(
    Output("formula-expr-input", "value", allow_duplicate=True),
    [Input({"type": "btn-formula-token", "token": ALL}, "n_clicks")],
    [State("formula-expr-input", "value")],
    prevent_initial_call=True
)
def insert_formula_token(clicks, current_expr):
    if not ctx.triggered:
        return no_update
    prop_id = ctx.triggered[0]["prop_id"]
    token = json.loads(prop_id.rsplit(".", 1)[0])["token"]
    cur = current_expr or ""
    if cur and not cur.endswith((" ", "(", "+", "-", "*", "/", ",")):
        cur += " "
    return cur + token


@app.callback(
    Output("formula-live-preview", "children"),
    [Input("formula-expr-input", "value"),
     Input("formula-select", "value")],
    [State("store-computed", "data")]
)
def update_formula_live_preview(expr, selected_key, json_computed):
    if not expr or not json_computed:
        return "Expression is empty."

    try:
        df = pd.read_json(io.StringIO(json_computed), orient="split")
        sample_df = df.head(10).copy()
        res = eval_expr(expr, sample_df)
        if len(res) == 0:
            return "No data points to evaluate."

        valid = [v for v in res if not np.isnan(v)]
        if valid:
            mean_val = float(np.mean(valid))
            min_val = float(np.min(valid))
            max_val = float(np.max(valid))
            sample_val = float(valid[0])
            return f"✅ Valid Formula • First Interval: {sample_val:.4g} | Mean: {mean_val:.4g} (Min: {min_val:.4g}, Max: {max_val:.4g})"
        else:
            return "⚠️ Evaluated to NaN / zeroes on sample intervals."
    except Exception as e:
        return f"❌ Evaluation Error: {str(e)}"


@app.callback(
    [Output("store-formulas", "data"),
     Output("formula-status-msg", "children")],
    [Input("btn-save-formula", "n_clicks")],
    [State("formula-select", "value"),
     State("formula-expr-input", "value"),
     State("store-formulas", "data")],
    prevent_initial_call=True
)
def save_formula_override(n_clicks, selected_key, expr, current_formulas):
    if not n_clicks or not selected_key or not expr:
        return no_update, no_update

    formulas = dict(current_formulas or {})
    formulas[selected_key] = expr.strip()
    status = dbc.Alert(f"✅ Saved formula for {selected_key} and recomputed well log.", color="success", duration=3000, style={"fontSize": "12px", "borderRadius": "8px"})
    return formulas, status


# ──────────────────────────────────────────────────────────────────────
#  Callbacks: Column Configuration Modal (Checklist, Add, Delete, Apply)
# ──────────────────────────────────────────────────────────────────────
@app.callback(
    Output("column-checklist-container", "children"),
    [Input("columns-modal", "is_open"),
     Input("store-schema", "data")]
)
def render_column_checklist(is_open, schema):
    tracks = schema or DEFAULT_TRACK_SCHEMA
    rows = []
    for s in tracks:
        col_id = s.get("id")
        name = s.get("name", s.get("key"))
        unit = s.get("unit", "")
        color = s.get("color", "#38bdf8")
        vis = s.get("visible", True)

        row = html.Div([
            dbc.Checkbox(
                id={"type": "col-vis-check", "id": col_id},
                label=html.Span([
                    html.Span(style={"width": "10px", "height": "10px", "borderRadius": "50%", "background": color, "display": "inline-block", "marginRight": "8px"}),
                    html.Span(name, style={"fontWeight": "600", "color": CLR_TEXT, "marginRight": "6px"}),
                    html.Small(f"({unit})", style={"color": CLR_MUTED}) if unit else None,
                ], style={"fontSize": "12px"}),
                value=vis,
            ),
        ], className="col-6 mb-2")
        rows.append(row)

    return html.Div(rows, className="row g-2")


@app.callback(
    Output({"type": "col-vis-check", "id": ALL}, "value"),
    [Input("btn-col-select-all", "n_clicks"),
     Input("btn-col-deselect-all", "n_clicks")],
    [State({"type": "col-vis-check", "id": ALL}, "value")],
    prevent_initial_call=True
)
def select_deselect_all_columns(n_sel, n_desel, current_values):
    triggered = ctx.triggered_id
    if triggered == "btn-col-select-all":
        return [True] * len(current_values)
    elif triggered == "btn-col-deselect-all":
        return [False] * len(current_values)
    return no_update


@app.callback(
    Output("new-col-expr-input", "value", allow_duplicate=True),
    [Input({"type": "btn-newcol-token", "token": ALL}, "n_clicks")],
    [State("new-col-expr-input", "value")],
    prevent_initial_call=True
)
def insert_newcol_token(clicks, current_expr):
    if not ctx.triggered:
        return no_update
    prop_id = ctx.triggered[0]["prop_id"]
    token = json.loads(prop_id.rsplit(".", 1)[0])["token"]
    cur = current_expr or ""
    if cur and not cur.endswith((" ", "(", "+", "-", "*", "/", ",")):
        cur += " "
    return cur + token


@app.callback(
    [Output("store-schema", "data", allow_duplicate=True),
     Output("store-custom-cols", "data", allow_duplicate=True),
     Output("add-column-status", "children"),
     Output("new-col-name-input", "value"),
     Output("new-col-unit-input", "value"),
     Output("new-col-expr-input", "value")],
    [Input("btn-submit-new-column", "n_clicks")],
    [State("new-col-name-input", "value"),
     State("new-col-unit-input", "value"),
     State("new-col-scale-select", "value"),
     State("new-col-color-input", "value"),
     State("new-col-expr-input", "value"),
     State("store-schema", "data"),
     State("store-custom-cols", "data"),
     State("store-computed", "data")],
    prevent_initial_call=True
)
def add_new_custom_column(n_clicks, name, unit, scale, color, expr, schema, custom_cols, json_computed):
    if not n_clicks:
        return no_update, no_update, no_update, no_update, no_update, no_update

    if not name or not name.strip():
        return no_update, no_update, dbc.Alert("Please provide a valid column name.", color="warning", style={"fontSize": "12px"}), no_update, no_update, no_update

    if not expr or not expr.strip():
        return no_update, no_update, dbc.Alert("Please provide a mathematical computation expression.", color="warning", style={"fontSize": "12px"}), no_update, no_update, no_update

    col_key = name.strip().replace(" ", "_").upper()
    
    # Test formula evaluation
    try:
        df = pd.read_json(io.StringIO(json_computed), orient="split")
        test_res = eval_expr(expr.strip(), df.head(5))
    except Exception as e:
        return no_update, no_update, dbc.Alert(f"Invalid formula expression: {str(e)}", color="danger", style={"fontSize": "12px"}), no_update, no_update, no_update

    new_track = {
        "id": col_key,
        "key": col_key,
        "name": name.strip(),
        "unit": unit.strip() if unit else "",
        "color": color or "#38bdf8",
        "scale": scale or "log",
        "visible": True,
        "is_custom": True,
    }

    updated_schema = list(schema or DEFAULT_TRACK_SCHEMA)
    # If already exists, replace; else append
    existing_idx = next((i for i, s in enumerate(updated_schema) if s.get("key") == col_key), None)
    if existing_idx is not None:
        updated_schema[existing_idx] = new_track
    else:
        updated_schema.append(new_track)

    new_custom_item = {
        "key": col_key,
        "name": name.strip(),
        "unit": unit.strip() if unit else "",
        "color": color or "#38bdf8",
        "scale": scale or "log",
        "expr": expr.strip(),
    }
    updated_custom_cols = [c for c in (custom_cols or []) if c.get("key") != col_key]
    updated_custom_cols.append(new_custom_item)

    status = dbc.Alert(f"✅ Added column '{name}' successfully!", color="success", duration=3000, style={"fontSize": "12px"})
    return updated_schema, updated_custom_cols, status, "", "", ""


@app.callback(
    Output("remove-columns-container", "children"),
    [Input("columns-modal", "is_open"),
     Input("store-schema", "data")]
)
def render_remove_columns_list(is_open, schema):
    tracks = schema or DEFAULT_TRACK_SCHEMA
    items = []
    for s in tracks:
        col_id = s.get("id")
        name = s.get("name", s.get("key"))
        unit = s.get("unit", "")
        color = s.get("color", "#38bdf8")
        is_custom = s.get("is_custom", False)

        item = html.Div([
            html.Div([
                html.Span(style={"width": "10px", "height": "10px", "borderRadius": "50%", "background": color, "display": "inline-block", "marginRight": "8px"}),
                html.Span(name, style={"fontWeight": "600", "color": CLR_TEXT, "marginRight": "6px", "fontSize": "13px"}),
                html.Span("Custom" if is_custom else "Standard", className=f"badge {'bg-primary' if is_custom else 'bg-secondary'} me-2", style={"fontSize": "10px"}),
                html.Small(f"({unit})", style={"color": CLR_MUTED}) if unit else None,
            ], className="d-flex align-items-center"),
            dbc.Button(
                [html.I(className="fa-solid fa-trash-can me-1"), "Delete"],
                id={"type": "btn-delete-col", "id": col_id},
                color="danger",
                outline=True,
                size="sm",
                className="py-1 px-2",
                style={"fontSize": "11px", "borderRadius": "6px"},
            ),
        ], className="d-flex align-items-center justify-content-between p-2 mb-2 rounded", style={"background": "rgba(16, 26, 46, 0.6)", "border": f"1px solid {CLR_BORDER}"})
        items.append(item)

    return items if items else html.Div("No columns available to remove.", style={"color": CLR_MUTED, "fontSize": "12px"})


@app.callback(
    [Output("store-schema", "data", allow_duplicate=True),
     Output("store-custom-cols", "data", allow_duplicate=True)],
    [Input({"type": "btn-delete-col", "id": ALL}, "n_clicks")],
    [State("store-schema", "data"),
     State("store-custom-cols", "data")],
    prevent_initial_call=True
)
def delete_column(clicks, schema, custom_cols):
    if not ctx.triggered:
        return no_update, no_update

    prop_id = ctx.triggered[0]["prop_id"]
    target_id = json.loads(prop_id.rsplit(".", 1)[0])["id"]

    updated_schema = [s for s in (schema or []) if s.get("id") != target_id]
    updated_custom_cols = [c for c in (custom_cols or []) if c.get("key") != target_id]

    return updated_schema, updated_custom_cols


@app.callback(
    Output("store-schema", "data", allow_duplicate=True),
    [Input("btn-apply-columns", "n_clicks")],
    [State({"type": "col-vis-check", "id": ALL}, "value"),
     State({"type": "col-vis-check", "id": ALL}, "id"),
     State("store-schema", "data")],
    prevent_initial_call=True
)
def apply_column_visibility_changes(n_clicks, check_values, check_ids, schema):
    if not n_clicks or not check_ids:
        return no_update

    vis_map = {cid["id"]: val for cid, val in zip(check_ids, check_values)}
    updated_schema = list(schema or DEFAULT_TRACK_SCHEMA)

    for s in updated_schema:
        if s.get("id") in vis_map:
            s["visible"] = bool(vis_map[s["id"]])

    return updated_schema


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
