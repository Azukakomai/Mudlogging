"""
MudLog Pro — Petrophysical Multi-Track Well Logging Software
============================================================
Modern Multi-Workspace Spreadsheet Suite (Microsoft Excel & Google Sheets Design)
Created By Mohammad Azka Khairur Rahman

Features:
  - Google Sheets style Multi-Workspace Bottom Tabs (Independent Wells / Datasets)
  - Drag-to-detach tab or ↗ button to undock into a standalone floating window
  - ↙ Re-attach detached windows back into the main app tab bar
  - Excel Forest Green Header & Modern Flat Ribbon
  - Dynamic Formula Bar (fx) & Depth Cell Inspector
  - High-Resolution Multi-Track Depth Log with Fluid Facies Overlay
  - Modern Tabular Spreadsheet Grid with Column Sorting, Facies Highlights & TSV Copy
  - Executive Petrophysical KPI Cards & Summary Dashboard
  - Live Formula Engine & Column Track Configuration Manager
  - Multi-Format Data Ingestion (CSV, TXT, Excel) & Export (CSV, PNG, PDF)
"""

import os
import sys
import io
import json
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

# Matplotlib integration for Tkinter
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Local petrophysical imports
try:
    from engine import compute_all, eval_expr, DEFAULT_FORMULAS, DEFAULT_THRESHOLDS
    from parser import parse_mudlog_file
except ImportError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, current_dir)
    sys.path.insert(0, parent_dir)
    from engine import compute_all, eval_expr, DEFAULT_FORMULAS, DEFAULT_THRESHOLDS
    from parser import parse_mudlog_file


# ──────────────────────────────────────────────────────────────────────────────
#  Theme / Color Constants (Modern Excel / Google Sheets Aesthetic)
# ──────────────────────────────────────────────────────────────────────────────
APP_TITLE = "MudLog Pro — Multi-Track Well Logging & Petrophysical Analysis"
APP_VERSION = "3.2 Google Sheets Multi-Tab Edition"
APP_AUTHOR = "Created By Mohammad Azka Khairur Rahman"

# Modern Excel Emerald & Office Fluent Palette
COLOR_EXCEL_PRIMARY = "#107C41"   # Excel Signature Forest Green
COLOR_EXCEL_DARK    = "#0B5C2F"   # Deep Green (Header / Active State)
COLOR_EXCEL_LIGHT   = "#E8F5E9"   # Soft Green Tint
COLOR_EXCEL_ACCENT  = "#10B981"   # Emerald Accent

COLOR_APP_BG        = "#F3F4F6"   # Modern Soft Slate Background
COLOR_SURFACE       = "#FFFFFF"   # Pure White Card / Surface
COLOR_TOOLBAR_BG    = "#FFFFFF"   # Clean White Ribbon Toolbar
COLOR_BORDER        = "#E5E7EB"   # Clean 1px Border (Gray 200)
COLOR_BORDER_DARK   = "#CBD5E1"   # Gray 300
COLOR_TEXT_MAIN     = "#1F2937"   # Gray 800 (Primary Text)
COLOR_TEXT_MUTED    = "#6B7280"   # Gray 500 (Secondary Text)
COLOR_TEXT_WHITE    = "#FFFFFF"   # White Text

# Facies Colors (Modern Soft Pastels for Tables & Vibrant for Charts)
COLOR_GAS_BG        = "#FEE2E2"   # Soft Rose Tint for Gas Rows
COLOR_GAS_TEXT      = "#991B1B"   # Dark Rose Text
COLOR_GAS_ACCENT    = "#EF4444"   # Vibrant Red for Chart Overlay

COLOR_OIL_BG        = "#DCFCE7"   # Soft Mint Tint for Oil Rows
COLOR_OIL_TEXT      = "#166534"   # Dark Green Text
COLOR_OIL_ACCENT    = "#10B981"   # Vibrant Emerald for Chart Overlay

COLOR_DRY_BG        = "#F1F5F9"   # Slate 100 for Non-Bearing
COLOR_DRY_TEXT      = "#475569"   # Slate 600 Text
COLOR_DRY_ACCENT    = "#CBD5E1"   # Gray for Chart Overlay

# Default Track Schema with Vibrant Modern Palette and Compact Track Titles
DEFAULT_TRACK_SCHEMA = [
    {"id": "C1",           "key": "C1",           "name": "C1\n(ppm)",       "unit": "ppm",   "color": "#059669", "scale": "linear", "visible": True},
    {"id": "C2",           "key": "C2",           "name": "C2\n(ppm)",       "unit": "ppm",   "color": "#0284C7", "scale": "linear", "visible": True},
    {"id": "C3",           "key": "C3",           "name": "C3\n(ppm)",       "unit": "ppm",   "color": "#2563EB", "scale": "linear", "visible": True},
    {"id": "IC4",          "key": "IC4",          "name": "iC4\n(ppm)",      "unit": "ppm",   "color": "#4F46E5", "scale": "linear", "visible": True},
    {"id": "NC4",          "key": "NC4",          "name": "nC4\n(ppm)",      "unit": "ppm",   "color": "#7C3AED", "scale": "linear", "visible": True},
    {"id": "IC5",          "key": "IC5",          "name": "iC5\n(ppm)",      "unit": "ppm",   "color": "#9333EA", "scale": "linear", "visible": True},
    {"id": "NC5",          "key": "NC5",          "name": "nC5\n(ppm)",      "unit": "ppm",   "color": "#C026D3", "scale": "linear", "visible": True},
    {"id": "TG",           "key": "TG_USED",      "name": "TG\n(ppm)",       "unit": "ppm",   "color": "#047857", "scale": "linear", "visible": True},
    {"id": "R1_C1_C2",     "key": "R1_C1_C2",     "name": "Pixler R1\n(ratio)","unit":"ratio","color": "#0D9488", "scale": "linear", "visible": True},
    {"id": "R2_C1_C3",     "key": "R2_C1_C3",     "name": "Pixler R2\n(ratio)","unit":"ratio","color": "#0891B2", "scale": "linear", "visible": True},
    {"id": "R3_C3_C1",     "key": "R3_C3_C1",     "name": "Pixler R3\n(ratio)","unit":"ratio","color": "#2563EB", "scale": "linear", "visible": True},
    {"id": "R4_C2_C1",     "key": "R4_C2_C1",     "name": "Pixler R4\n(ratio)","unit":"ratio","color": "#4338CA", "scale": "linear", "visible": True},
    {"id": "WH",           "key": "WH",           "name": "Wh\n(%)",         "unit": "%",     "color": "#6366F1", "scale": "linear", "visible": True},
    {"id": "BH",           "key": "BH",           "name": "Bh\n(ratio)",     "unit": "ratio", "color": "#8B5CF6", "scale": "linear", "visible": True},
    {"id": "CH",           "key": "CH",           "name": "Ch\n(ratio)",     "unit": "ratio", "color": "#A855F7", "scale": "linear", "visible": True},
    {"id": "DRYNESS",      "key": "DRYNESS",      "name": "Dryness\n(ratio)","unit": "ratio", "color": "#D97706", "scale": "linear", "visible": True},
    {"id": "GOW_NOTG",     "key": "GOW_NOTG",     "name": "GOW/TG\n(ratio)", "unit": "ratio", "color": "#E11D48", "scale": "linear", "visible": True},
    {"id": "WBS",          "key": "WBS",          "name": "WBS\n(score)",    "unit": "score", "color": "#BE185D", "scale": "linear", "visible": True},
]


def generate_synthetic_mudlog(seed=42, well_name="GWD-01", base_depth=1800.0):
    """Generates a realistic synthetic mudlog dataset with gas and oil payzones."""
    np.random.seed(seed)
    rows = []
    depth = base_depth
    for i in range(85):
        depth += 15.0
        base_gas = np.sin(i / 5.0) * 8000.0 + 12000.0
        is_payzone = (2100.0 <= depth <= 2450.0) or (2700.0 <= depth <= 2880.0)
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
            "DEPTH": round(depth, 1),
            "C1": round(c1, 1),
            "C2": round(c2, 1),
            "C3": round(c3, 1),
            "IC4": round(ic4, 1),
            "NC4": round(nc4, 1),
            "IC5": round(ic5, 1),
            "NC5": round(nc5, 1),
            "TG": round(tg, 1),
        })
    return pd.DataFrame(rows)


# ──────────────────────────────────────────────────────────────────────────────
#  WellState — Shared mutable data model (survives detach / reattach)
# ──────────────────────────────────────────────────────────────────────────────
class WellState:
    """Holds all mutable data for one well tab. Views share this object so
    detached windows stay in sync without Tkinter reparenting."""
    def __init__(self, sheet_id, sheet_name, file_path, raw_df):
        self.sheet_id   = sheet_id
        self.sheet_name = sheet_name
        self.file_path  = file_path
        self.raw_df     = raw_df
        self.formulas   = {k: v["expr"] for k, v in DEFAULT_FORMULAS.items()}
        self.thresholds = dict(DEFAULT_THRESHOLDS)
        self.schema     = [dict(s) for s in DEFAULT_TRACK_SCHEMA]
        self.percentile_cutoff = 75.0
        self.computed_df = compute_all(raw_df,
                                       formula_overrides=self.formulas,
                                       threshold_overrides=self.thresholds)
        # Views that are currently rendering this state (docked + detached)
        self.views: list = []
        self.is_detached = False
        self.detached_window = None

    def recompute(self):
        self.computed_df = compute_all(self.raw_df,
                                       formula_overrides=self.formulas,
                                       threshold_overrides=self.thresholds)
        for v in list(self.views):
            try:
                v.refresh_workspace()
            except Exception:
                pass


# ──────────────────────────────────────────────────────────────────────────────
#  WellWorkspace Class (View — renders one WellState in a parent widget)
# ──────────────────────────────────────────────────────────────────────────────
class WellWorkspace(tk.Frame):
    """Pure view — renders a WellState inside any parent (main host or Toplevel)."""
    
    def __init__(self, parent, app_controller, state: 'WellState'):
        super().__init__(parent, bg=COLOR_APP_BG)
        self.app   = app_controller
        self.state = state
        # Register this view with the state so recompute() can update it
        state.views.append(self)

        # Convenience aliases so existing code keeps working
        self.sheet_id   = state.sheet_id
        self.sheet_name = state.sheet_name
        self.file_path  = state.file_path

        self.current_view_idx = 0
        self._build_ui()
        self.refresh_workspace()

    # ── transparent attribute forwarding to WellState ─────────────────────────
    @property
    def raw_df(self):         return self.state.raw_df
    @raw_df.setter
    def raw_df(self, v):      self.state.raw_df = v

    @property
    def formulas(self):       return self.state.formulas
    @formulas.setter
    def formulas(self, v):    self.state.formulas = v

    @property
    def thresholds(self):     return self.state.thresholds
    @thresholds.setter
    def thresholds(self, v):  self.state.thresholds = v

    @property
    def schema(self):         return self.state.schema
    @schema.setter
    def schema(self, v):      self.state.schema = v

    @property
    def percentile_cutoff(self):      return self.state.percentile_cutoff
    @percentile_cutoff.setter
    def percentile_cutoff(self, v):   self.state.percentile_cutoff = v

    @property
    def computed_df(self):    return self.state.computed_df
    @computed_df.setter
    def computed_df(self, v): self.state.computed_df = v

    def destroy(self):
        """Unregister from state before destroying."""
        if self in self.state.views:
            self.state.views.remove(self)
        super().destroy()

    def _build_ui(self):
        """Constructs the view switcher and sub-view containers."""
        # Top Sub-Navigation Header inside Workspace
        self.nav_header = tk.Frame(self, bg=COLOR_SURFACE, padx=10, pady=6, highlightthickness=1,
                                   highlightbackground=COLOR_BORDER, highlightcolor=COLOR_BORDER)
        self.nav_header.pack(side=tk.TOP, fill=tk.X)

        # View selector segmented pill buttons
        self.view_btns_frame = tk.Frame(self.nav_header, bg="#F3F4F6", padx=3, pady=3,
                                        highlightthickness=1, highlightbackground=COLOR_BORDER)
        self.view_btns_frame.pack(side=tk.LEFT)

        self.view_buttons = []
        view_specs = [
            ("📈 Multi-Track Depth Log", 0),
            ("📊 Spreadsheet Grid (Excel View)", 1),
            ("📋 Facies & Petrophysical Summary", 2),
            ("🧮 Formula Engine", 3),
        ]

        for label, idx in view_specs:
            btn = tk.Button(self.view_btns_frame, text=label, font=("Segoe UI", 9, "bold" if idx == 0 else "normal"),
                            bg=COLOR_SURFACE if idx == 0 else "#F3F4F6",
                            fg=COLOR_EXCEL_PRIMARY if idx == 0 else COLOR_TEXT_MAIN,
                            activebackground=COLOR_SURFACE, activeforeground=COLOR_EXCEL_PRIMARY,
                            relief="flat", bd=0, padx=12, pady=4, cursor="hand2",
                            command=lambda i=idx: self.switch_view(i))
            btn.pack(side=tk.LEFT, padx=1)
            self.view_buttons.append(btn)

        # Right side: Tear-Off / Detach into standalone window button
        self.btn_detach = tk.Button(self.nav_header, text="↗ Detach to Separate Window", font=("Segoe UI", 9, "bold"),
                                    bg=COLOR_SURFACE, fg=COLOR_EXCEL_PRIMARY, relief="flat", bd=0, padx=10, pady=4,
                                    highlightthickness=1, highlightbackground=COLOR_BORDER, cursor="hand2",
                                    command=self.toggle_detach)
        self.btn_detach.pack(side=tk.RIGHT, padx=4)
        self.btn_detach.bind("<Enter>", lambda e: self.btn_detach.config(bg=COLOR_EXCEL_LIGHT))
        self.btn_detach.bind("<Leave>", lambda e: self.btn_detach.config(bg=COLOR_SURFACE))

        # View Containers (Stack)
        self.content_container = tk.Frame(self, bg=COLOR_APP_BG)
        self.content_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.view_frames = []
        for _ in range(4):
            vf = tk.Frame(self.content_container, bg=COLOR_SURFACE)
            self.view_frames.append(vf)

        # Subviews
        self._build_log_subview(self.view_frames[0])
        self._build_table_subview(self.view_frames[1])
        self._build_stats_subview(self.view_frames[2])
        self._build_formulas_subview(self.view_frames[3])

        # Show initial view
        self.switch_view(0)

    def switch_view(self, idx):
        """Switches the active subview inside this workspace."""
        self.current_view_idx = idx
        for i, vf in enumerate(self.view_frames):
            if i == idx:
                vf.pack(fill=tk.BOTH, expand=True)
            else:
                vf.pack_forget()

        # Update button highlights
        for i, btn in enumerate(self.view_buttons):
            if i == idx:
                btn.config(bg=COLOR_SURFACE, fg=COLOR_EXCEL_PRIMARY, font=("Segoe UI", 9, "bold"))
            else:
                btn.config(bg="#F3F4F6", fg=COLOR_TEXT_MAIN, font=("Segoe UI", 9, "normal"))

    # ──────────────────────────────────────────────────────────────────────────
    #  View 1: Multi-Track Depth Log
    # ──────────────────────────────────────────────────────────────────────────
    def _build_log_subview(self, parent):
        self.log_container = tk.Frame(parent, bg=COLOR_SURFACE)
        self.log_container.pack(fill=tk.BOTH, expand=True)

        self.fig = plt.Figure(figsize=(12, 7), dpi=100, facecolor="#FFFFFF")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.log_container)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.mpl_toolbar_frame = tk.Frame(self.log_container, bg="#F8FAFC", highlightthickness=1,
                                          highlightbackground=COLOR_BORDER, highlightcolor=COLOR_BORDER)
        self.mpl_toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.mpl_toolbar = NavigationToolbar2Tk(self.canvas, self.mpl_toolbar_frame)
        self.mpl_toolbar.config(background="#F8FAFC")
        self.mpl_toolbar.update()

        self._hover_cid = self.canvas.mpl_connect("motion_notify_event", self._on_log_hover)

    def render_multi_track_plot(self):
        """Renders petrophysical multi-track log with clean header spacing."""
        self.fig.clear()
        if self.computed_df is None or self.computed_df.empty:
            self.canvas.draw()
            return

        active_schema = [s for s in self.schema if s.get("visible", True)]
        if not active_schema:
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, "No active tracks selected.\nUse Edit -> Configure Columns & Tracks.",
                    ha="center", va="center", fontsize=12, color=COLOR_TEXT_MUTED)
            self.canvas.draw()
            return

        df = self.computed_df
        depth = df["DEPTH"].values
        d_min, d_max = depth.min(), depth.max()

        n_tracks = len(active_schema)
        n_cols = n_tracks + 1
        width_ratios = [1.0] * n_tracks + [0.7]

        axes = self.fig.subplots(1, n_cols, sharey=True, gridspec_kw={"width_ratios": width_ratios, "wspace": 0.05})
        if n_cols == 1:
            axes = [axes]

        axes[0].set_ylim(d_max, d_min)
        axes[0].set_ylabel("DEPTH (m)", fontsize=9, fontweight="bold", color=COLOR_EXCEL_PRIMARY)

        for idx, track in enumerate(active_schema):
            ax = axes[idx]
            col_key = track["key"]
            track_name = track["name"]
            color = track.get("color", "#059669")

            if col_key in df.columns:
                raw_y = pd.to_numeric(df[col_key], errors="coerce").fillna(0.0).values
                
                if self.percentile_cutoff > 0 and len(raw_y) > 0 and raw_y.max() > 0:
                    cutoff_val = np.percentile(raw_y[raw_y > 0], self.percentile_cutoff) if np.any(raw_y > 0) else 0.0
                    y_vals = np.where(raw_y >= cutoff_val, raw_y, 0.0)
                else:
                    y_vals = raw_y

                ax.plot(y_vals, depth, color=color, linewidth=1.3, label=track_name)
                ax.fill_betweenx(depth, 0, y_vals, color=color, alpha=0.14)

                val_max = np.nanmax(y_vals) if len(y_vals) > 0 else 1.0
                if val_max <= 0:
                    val_max = 1.0
                ax.set_xlim(0, val_max * 1.15)
            else:
                ax.set_xlim(0, 1)

            # Clean track titles (compact font to prevent horizontal overlap)
            ax.set_title(track_name, fontsize=7.0, fontweight="bold", pad=4, color=COLOR_TEXT_MAIN)
            ax.grid(True, which="both", color="#E2E8F0", linestyle="--", linewidth=0.5)
            ax.tick_params(axis="x", labelsize=6.5, rotation=45, colors=COLOR_TEXT_MUTED)
            ax.tick_params(axis="y", labelsize=7, colors=COLOR_TEXT_MUTED)
            ax.set_facecolor("#FFFFFF")
            for spine in ax.spines.values():
                spine.set_color("#CBD5E1")
                spine.set_linewidth(0.8)

            if idx > 0:
                ax.tick_params(axis="y", labelleft=False)

        # Facies Overlay Track
        ax_zone = axes[-1]
        ax_zone.set_title("FLUID\nFACIES", fontsize=7.0, fontweight="bold", pad=4, color=COLOR_EXCEL_PRIMARY)
        ax_zone.set_xlim(0, 1)
        ax_zone.set_xticks([])
        ax_zone.tick_params(axis="y", labelleft=False)
        ax_zone.set_facecolor("#F8FAFC")
        for spine in ax_zone.spines.values():
            spine.set_color("#CBD5E1")
            spine.set_linewidth(0.8)

        if "ZONE" in df.columns:
            zones = df["ZONE"].values
            n = len(df)
            for i in range(n):
                z = zones[i]
                d = depth[i]
                half_step = 7.5
                if i > 0 and i < n - 1:
                    half_step = (depth[i+1] - depth[i-1]) / 4.0
                d_top = d - half_step
                d_bot = d + half_step

                if z == "Gas":
                    rect = mpatches.Rectangle((0, d_top), 1, d_bot - d_top, color=COLOR_GAS_ACCENT, alpha=0.85)
                    ax_zone.add_patch(rect)
                elif z == "Oil":
                    rect = mpatches.Rectangle((0, d_top), 1, d_bot - d_top, color=COLOR_OIL_ACCENT, alpha=0.85)
                    ax_zone.add_patch(rect)
                else:
                    rect = mpatches.Rectangle((0, d_top), 1, d_bot - d_top, color=COLOR_DRY_ACCENT, alpha=0.35)
                    ax_zone.add_patch(rect)

        try:
            self.fig.subplots_adjust(top=0.91, bottom=0.08, left=0.05, right=0.98, wspace=0.07)
        except Exception:
            pass
        self.canvas.draw()

    def _on_log_hover(self, event):
        """Hover tracker for crosshair updates (only updates main formula bar if docked)."""
        if event.inaxes is not None and event.ydata is not None:
            depth_val = float(event.ydata)
            # Only update the main app formula bar when this view is docked
            if not self.state.is_detached:
                self.app.update_formula_bar_hover(self, depth_val)

    # ──────────────────────────────────────────────────────────────────────────
    #  View 2: Spreadsheet Data Table
    # ──────────────────────────────────────────────────────────────────────────
    def _build_table_subview(self, parent):
        table_container = tk.Frame(parent, bg=COLOR_SURFACE)
        table_container.pack(fill=tk.BOTH, expand=True)

        ctrl_bar = tk.Frame(table_container, bg="#F8FAFC", padx=8, pady=5, highlightthickness=1,
                            highlightbackground=COLOR_BORDER, highlightcolor=COLOR_BORDER)
        ctrl_bar.pack(side=tk.TOP, fill=tk.X)

        tk.Label(ctrl_bar, text="Filter by Zone:", font=("Segoe UI", 9, "bold"), bg="#F8FAFC", fg=COLOR_TEXT_MAIN).pack(side=tk.LEFT, padx=(4, 6))
        self.table_filter_var = tk.StringVar(value="All Zones")
        filter_combo = ttk.Combobox(ctrl_bar, textvariable=self.table_filter_var,
                                    values=["All Zones", "Gas Only", "Oil Only", "Payzones Only (Gas + Oil)", "Non-Bearing Only"],
                                    width=24, state="readonly")
        filter_combo.pack(side=tk.LEFT, padx=4)
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.populate_spreadsheet_table())

        btn_copy = tk.Button(ctrl_bar, text="📋 Copy Selection (TSV)", font=("Segoe UI", 9),
                             bg=COLOR_SURFACE, fg=COLOR_TEXT_MAIN, relief="flat", bd=0, padx=10, pady=3,
                             highlightthickness=1, highlightbackground=COLOR_BORDER, cursor="hand2",
                             command=self.copy_table_selection)
        btn_copy.pack(side=tk.RIGHT, padx=4)

        tree_frame = tk.Frame(table_container, bg=COLOR_SURFACE)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)

        self.tree = ttk.Treeview(tree_frame, yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set, selectmode="extended")
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tree.tag_configure("gas_row", background=COLOR_GAS_BG, foreground=COLOR_GAS_TEXT)
        self.tree.tag_configure("oil_row", background=COLOR_OIL_BG, foreground=COLOR_OIL_TEXT)
        self.tree.tag_configure("even_row", background="#F8FAFC", foreground=COLOR_TEXT_MAIN)
        self.tree.tag_configure("odd_row", background=COLOR_SURFACE, foreground=COLOR_TEXT_MAIN)

        self.tree.bind("<ButtonRelease-1>", self._on_table_row_click)

    def populate_spreadsheet_table(self):
        """Populates Treeview with computed data."""
        self.tree.delete(*self.tree.get_children())
        if self.computed_df is None or self.computed_df.empty:
            return

        df = self.computed_df.copy()
        filter_mode = self.table_filter_var.get()
        if filter_mode == "Gas Only":
            df = df[df["ZONE"] == "Gas"]
        elif filter_mode == "Oil Only":
            df = df[df["ZONE"] == "Oil"]
        elif filter_mode == "Payzones Only (Gas + Oil)":
            df = df[df["ZONE"].isin(["Gas", "Oil"])]
        elif filter_mode == "Non-Bearing Only":
            df = df[df["ZONE"] == "Non-Bearing"]

        cols = list(df.columns)
        self.tree["columns"] = ["ROW_NUM"] + cols
        self.tree["show"] = "headings"

        self.tree.heading("ROW_NUM", text="#", anchor="center")
        self.tree.column("ROW_NUM", width=50, anchor="center", stretch=False)

        for col in cols:
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, width=85, anchor="e" if col != "ZONE" else "center")

        for i, row in df.iterrows():
            vals = []
            for col in cols:
                v = row[col]
                if isinstance(v, float):
                    vals.append(f"{v:.2f}")
                else:
                    vals.append(str(v))

            zone = row.get("ZONE", "")
            if zone == "Gas":
                tag = "gas_row"
            elif zone == "Oil":
                tag = "oil_row"
            else:
                tag = "even_row" if i % 2 == 0 else "odd_row"

            self.tree.insert("", tk.END, values=[i + 1] + vals, tags=(tag,))

    def _on_table_row_click(self, event):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            vals = item["values"]
            if vals and len(vals) > 1:
                depth = float(vals[1])
                self.app.update_formula_bar_hover(self, depth)

    def copy_table_selection(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Copy", "Please select one or more rows to copy.", parent=self)
            return

        lines = []
        for item_id in selected:
            vals = self.tree.item(item_id)["values"]
            lines.append("\t".join(str(v) for v in vals))

        tsv_data = "\n".join(lines)
        self.clipboard_clear()
        self.clipboard_append(tsv_data)
        messagebox.showinfo("Copied", f"Copied {len(selected)} rows to clipboard in Excel spreadsheet format.", parent=self)

    # ──────────────────────────────────────────────────────────────────────────
    #  View 3: Facies & Statistics Summary
    # ──────────────────────────────────────────────────────────────────────────
    def _build_stats_subview(self, parent):
        self.stats_container = tk.Frame(parent, bg=COLOR_APP_BG, padx=20, pady=20)
        self.stats_container.pack(fill=tk.BOTH, expand=True)

    def refresh_statistics_view(self):
        for widget in self.stats_container.winfo_children():
            widget.destroy()

        if self.computed_df is None or self.computed_df.empty:
            tk.Label(self.stats_container, text="No dataset available.", bg=COLOR_APP_BG).pack()
            return

        df = self.computed_df
        d_min = df["DEPTH"].min()
        d_max = df["DEPTH"].max()
        n_pts = len(df)
        span = d_max - d_min

        hdr_frame = tk.Frame(self.stats_container, bg=COLOR_APP_BG)
        hdr_frame.pack(fill=tk.X, pady=(0, 12))

        tk.Label(hdr_frame, text=f"{self.sheet_name} — Petrophysical Well Summary & Fluid Facies Breakdown",
                 font=("Segoe UI", 13, "bold"), bg=COLOR_APP_BG, fg=COLOR_TEXT_MAIN).pack(side=tk.LEFT)

        kpi_frame = tk.Frame(self.stats_container, bg=COLOR_APP_BG)
        kpi_frame.pack(fill=tk.X, pady=(0, 16))

        def make_kpi(parent, title, val, subtext, color, border_accent):
            card = tk.Frame(parent, bg=COLOR_SURFACE, padx=16, pady=12,
                            highlightthickness=1, highlightbackground=COLOR_BORDER)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

            accent_stripe = tk.Frame(card, bg=border_accent, width=4)
            accent_stripe.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

            content_box = tk.Frame(card, bg=COLOR_SURFACE)
            content_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            tk.Label(content_box, text=title, font=("Segoe UI", 8, "bold"), fg=COLOR_TEXT_MUTED, bg=COLOR_SURFACE).pack(anchor="w")
            tk.Label(content_box, text=val, font=("Segoe UI", 17, "bold"), fg=color, bg=COLOR_SURFACE).pack(anchor="w", pady=2)
            tk.Label(content_box, text=subtext, font=("Segoe UI", 8), fg=COLOR_TEXT_MUTED, bg=COLOR_SURFACE).pack(anchor="w")

        z_counts = df["ZONE"].value_counts().to_dict() if "ZONE" in df.columns else {}
        gas_cnt = z_counts.get("Gas", 0)
        oil_cnt = z_counts.get("Oil", 0)
        gas_pct = (gas_cnt / n_pts) * 100.0 if n_pts > 0 else 0
        oil_pct = (oil_cnt / n_pts) * 100.0 if n_pts > 0 else 0
        pay_cnt = gas_cnt + oil_cnt
        pay_pct = (pay_cnt / n_pts) * 100.0 if n_pts > 0 else 0

        make_kpi(kpi_frame, "TOTAL DEPTH INTERVAL", f"{span:.0f} m", f"{d_min:.1f}m - {d_max:.1f}m ({n_pts} samples)", COLOR_TEXT_MAIN, "#3B82F6")
        make_kpi(kpi_frame, "GAS PAYZONES", f"{gas_cnt} Intervals", f"{gas_pct:.1f}% of Well Section", "#DC2626", "#EF4444")
        make_kpi(kpi_frame, "OIL PAYZONES", f"{oil_cnt} Intervals", f"{oil_pct:.1f}% of Well Section", "#16A34A", "#10B981")
        make_kpi(kpi_frame, "NET HYDROCARBON PAY", f"{pay_pct:.1f}% Net/Gross", f"{pay_cnt} Net Pay Samples", COLOR_EXCEL_PRIMARY, COLOR_EXCEL_PRIMARY)

        summary_card = tk.Frame(self.stats_container, bg=COLOR_SURFACE, padx=16, pady=14,
                                highlightthickness=1, highlightbackground=COLOR_BORDER)
        summary_card.pack(fill=tk.BOTH, expand=True)

        tk.Label(summary_card, text="Gas Components & Ratio Distribution Statistics", font=("Segoe UI", 10, "bold"),
                 bg=COLOR_SURFACE, fg=COLOR_TEXT_MAIN).pack(anchor="w", pady=(0, 8))

        cols_to_sum = [c for c in ["C1", "C2", "C3", "IC4", "NC4", "IC5", "NC5", "TG_USED", "WH", "BH", "CH", "DRYNESS", "R1_C1_C2"] if c in df.columns]
        stat_df = df[cols_to_sum].describe().T.reset_index()
        stat_df.rename(columns={"index": "Parameter", "mean": "Mean", "std": "StdDev", "min": "Min", "50%": "Median (P50)", "max": "Max"}, inplace=True)

        stat_tree = ttk.Treeview(summary_card, columns=list(stat_df.columns), show="headings", height=8)
        for col in stat_df.columns:
            stat_tree.heading(col, text=col)
            stat_tree.column(col, width=100, anchor="e" if col != "Parameter" else "w")

        for _, row in stat_df.iterrows():
            vals = [row["Parameter"]] + [f"{float(v):.2f}" if isinstance(v, (int, float)) else str(v) for v in row[1:]]
            stat_tree.insert("", tk.END, values=vals)

        stat_tree.pack(fill=tk.BOTH, expand=True)

    # ──────────────────────────────────────────────────────────────────────────
    #  View 4: Formula & Indicator Inspector
    # ──────────────────────────────────────────────────────────────────────────
    def _build_formulas_subview(self, parent):
        frame = tk.Frame(parent, bg=COLOR_APP_BG, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        header_row = tk.Frame(frame, bg=COLOR_APP_BG)
        header_row.pack(fill=tk.X, pady=(0, 10))

        tk.Label(header_row, text="Active Petrophysical Formulas (Deterministic Engine)",
                 font=("Segoe UI", 12, "bold"), bg=COLOR_APP_BG, fg=COLOR_TEXT_MAIN).pack(side=tk.LEFT)

        btn_edit = tk.Button(header_row, text="🧮 Open Formula Editor Modal", font=("Segoe UI", 9, "bold"),
                             bg=COLOR_EXCEL_PRIMARY, fg=COLOR_TEXT_WHITE, relief="flat", bd=0, padx=12, pady=5,
                             cursor="hand2", command=self.app.open_formula_manager_dialog)
        btn_edit.pack(side=tk.RIGHT)

        card = tk.Frame(frame, bg=COLOR_SURFACE, highlightthickness=1, highlightbackground=COLOR_BORDER)
        card.pack(fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(card)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.formula_text = tk.Text(card, font=("Consolas", 10), bg=COLOR_SURFACE, fg=COLOR_TEXT_MAIN,
                                    yscrollcommand=scroll.set, wrap="none", padx=12, pady=12, relief="flat", bd=0)
        self.formula_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self.formula_text.yview)

    def refresh_formulas_text(self):
        self.formula_text.delete("1.0", tk.END)
        lines = [
            "================================================================================",
            f"  MUDLOG PRO — AUDITABLE FORMULA DEFINITIONS FOR [{self.sheet_name.upper()}]",
            "================================================================================",
            "",
        ]
        for key, expr in self.formulas.items():
            meta = DEFAULT_FORMULAS.get(key, {})
            name = meta.get("name", key)
            lines.append(f"• [{key}] {name}:")
            lines.append(f"    Formula Expression : {expr}")
            lines.append(f"    Gas Classification : {meta.get('gas', 'N/A')}")
            lines.append(f"    Oil Classification : {meta.get('oil', 'N/A')}")
            lines.append(f"    Non-Bearing Limits : {meta.get('non_bearing', 'N/A')}")
            lines.append("-" * 80)

        self.formula_text.insert(tk.END, "\n".join(lines))

    # ──────────────────────────────────────────────────────────────────────────
    #  General Workspace Actions
    # ──────────────────────────────────────────────────────────────────────────
    def refresh_workspace(self):
        """Refreshes all subviews of this workspace view."""
        self.render_multi_track_plot()
        self.populate_spreadsheet_table()
        self.refresh_statistics_view()
        self.refresh_formulas_text()

    def recompute(self):
        """Delegates full recompute to WellState (updates all views)."""
        self.state.recompute()

    def toggle_detach(self):
        """Detaches or re-attaches this workspace to a separate floating window."""
        if not self.state.is_detached:
            self.app.detach_workspace(self.state)
        else:
            self.app.reattach_workspace(self.state)


# ──────────────────────────────────────────────────────────────────────────────
#  Detached Floating Window Class
# ──────────────────────────────────────────────────────────────────────────────
class DetachedWellWindow(tk.Toplevel):
    """Standalone Toplevel window that renders a WellState independently.
    Tkinter does not allow moving Frames between windows, so we create a
    brand-new WellWorkspace view here that shares the same WellState object."""

    def __init__(self, app_controller, state: 'WellState'):
        super().__init__(app_controller)
        self.app   = app_controller
        self.state = state

        self.title(f"MudLog Pro — [{state.sheet_name}] ↗ ({state.file_path})")
        self.geometry("1140x780")
        self.configure(bg=COLOR_APP_BG)

        # ── Top bar ──────────────────────────────────────────────────────────
        top_bar = tk.Frame(self, bg=COLOR_EXCEL_PRIMARY, padx=12, pady=7)
        top_bar.pack(side=tk.TOP, fill=tk.X)

        self.title_lbl = tk.Label(top_bar,
            text=f"📊 MudLog Pro  •  Detached Well Window  [{state.sheet_name}]",
            font=("Segoe UI", 10, "bold"), fg=COLOR_TEXT_WHITE, bg=COLOR_EXCEL_PRIMARY)
        self.title_lbl.pack(side=tk.LEFT)

        btn_reattach = tk.Button(top_bar, text="↙ Re-attach to Main Window",
            font=("Segoe UI", 9, "bold"),
            bg=COLOR_EXCEL_DARK, fg=COLOR_TEXT_WHITE, relief="flat", bd=0,
            padx=12, pady=3, cursor="hand2", command=self.reattach)
        btn_reattach.pack(side=tk.RIGHT, padx=(8, 0))
        btn_reattach.bind("<Enter>", lambda e: btn_reattach.config(bg="#064E3B"))
        btn_reattach.bind("<Leave>", lambda e: btn_reattach.config(bg=COLOR_EXCEL_DARK))

        # ── Formula bar (simple, scoped to this window) ───────────────────────
        fx_bar = tk.Frame(self, bg=COLOR_SURFACE, padx=8, pady=4,
                          highlightthickness=1, highlightbackground=COLOR_BORDER)
        fx_bar.pack(side=tk.TOP, fill=tk.X)

        tk.Label(fx_bar, text="DEPTH", font=("Segoe UI", 8, "bold"),
                 bg="#F9FAFB", fg=COLOR_EXCEL_PRIMARY, padx=6).pack(side=tk.LEFT)
        self._depth_var = tk.StringVar(value="—")
        tk.Entry(fx_bar, textvariable=self._depth_var, font=("Consolas", 9, "bold"),
                 width=10, bg="#FFFFFF", fg=COLOR_TEXT_MAIN, relief="flat", bd=0,
                 justify="center").pack(side=tk.LEFT, padx=4, pady=2)

        tk.Label(fx_bar, text=" fx ", font=("Georgia", 11, "bold", "italic"),
                 bg=COLOR_EXCEL_LIGHT, fg=COLOR_EXCEL_PRIMARY, padx=6, pady=2).pack(side=tk.LEFT, padx=(4, 6))

        self._formula_var = tk.StringVar(value="Hover over the log to inspect values")
        tk.Entry(fx_bar, textvariable=self._formula_var, font=("Consolas", 9),
                 bg=COLOR_SURFACE, fg=COLOR_TEXT_MAIN, relief="flat", bd=0
                 ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6, pady=3)

        self._badge = tk.Label(fx_bar, text=" ZONE: READY ", font=("Segoe UI", 8, "bold"),
                               bg=COLOR_EXCEL_LIGHT, fg=COLOR_EXCEL_DARK, padx=10, pady=3)
        self._badge.pack(side=tk.RIGHT, padx=4)

        # ── Status bar (bottom of detached window) ────────────────────────────
        det_status = tk.Frame(self, bg=COLOR_EXCEL_PRIMARY, padx=8, pady=3)
        det_status.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Label(det_status,
                 text=f" 📄 {state.sheet_name}  •  {state.file_path} ",
                 font=("Segoe UI", 9), bg=COLOR_EXCEL_PRIMARY, fg=COLOR_TEXT_WHITE
                 ).pack(side=tk.LEFT)
        tk.Label(det_status, text=f" {APP_AUTHOR} ",
                 font=("Segoe UI", 9, "bold"), bg=COLOR_EXCEL_DARK, fg="#A7F3D0",
                 padx=10, pady=2).pack(side=tk.RIGHT)

        # ── New WellWorkspace view inside THIS Toplevel ───────────────────────
        self.view = WellWorkspace(self, app_controller, state)
        self.view.pack(fill=tk.BOTH, expand=True)
        # Override the btn_detach text
        self.view.btn_detach.config(text="↙ Re-attach to Main Window")
        # Wire hover callback to our local formula bar instead of main app bar
        self.view.canvas.mpl_disconnect(self.view._hover_cid)
        self.view._hover_cid = self.view.canvas.mpl_connect(
            "motion_notify_event", self._on_hover)

        self.protocol("WM_DELETE_WINDOW", self.reattach)

    def _on_hover(self, event):
        if event.inaxes is None or event.ydata is None:
            return
        depth_val = float(event.ydata)
        self._depth_var.set(f"{depth_val:.1f} m")
        df = self.state.computed_df
        if df is None or df.empty:
            return
        idx = (df["DEPTH"] - depth_val).abs().idxmin()
        row = df.loc[idx]
        zone = row.get("ZONE", "—")
        c1   = row.get("C1", 0.0)
        tg   = row.get("TG_USED", row.get("TG", 0.0))
        wh   = row.get("WH", 0.0)
        if zone == "Gas":
            self._badge.config(text=" 🔴 GAS PAYZONE ", bg=COLOR_GAS_BG, fg=COLOR_GAS_TEXT)
        elif zone == "Oil":
            self._badge.config(text=" 🟢 OIL PAYZONE ", bg=COLOR_OIL_BG, fg=COLOR_OIL_TEXT)
        else:
            self._badge.config(text=" ⚪ NON-BEARING ", bg=COLOR_DRY_BG, fg=COLOR_DRY_TEXT)
        self._formula_var.set(
            f"[{self.state.sheet_name}] Depth: {row['DEPTH']:.1f}m | "
            f"C1: {c1:.1f} ppm | TG: {tg:.1f} ppm | Wh: {wh:.1f}% | Zone: {zone}")

    def reattach(self):
        """Destroy this window and signal the main app to reattach."""
        self.app.reattach_workspace(self.state)


# ──────────────────────────────────────────────────────────────────────────────
#  Main Application Window Class (Host for Google Sheets Multi-Tab Engine)
# ──────────────────────────────────────────────────────────────────────────────
class MudLogDesktopApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_TITLE} [{APP_VERSION}]")
        self.geometry("1280x860")
        self.minsize(1020, 660)

        # Multi-Workspace State
        # self.workspaces  : list of WellState objects
        # self._views      : sheet_id -> WellWorkspace view (docked)
        self.workspaces: list = []
        self._views: dict = {}
        self.active_workspace_idx = 0
        self.sheet_counter = 1

        # Drag-and-drop state for tab tear-off
        self._drag_data = {"tab_idx": None, "start_x": 0, "start_y": 0, "dragging": False}

        # UI Construction — IMPORTANT: statusbar and sheets bar MUST be packed
        # as side=BOTTOM before workspace_host gets expand=True, otherwise the
        # pack manager gives all remaining space to the host and hides the bars.
        self._setup_styles()
        self._create_top_header_banner()
        self._create_menubar()
        self._create_modern_ribbon()
        self._create_formula_bar()
        self._create_statusbar()              # pack BOTTOM first
        self._create_sheets_bottom_tab_bar()  # pack BOTTOM second
        self._create_workspace_viewport()     # pack fill+expand LAST

        # Initialize Default Sheet 1
        self.add_new_sheet(name="Well 1 (Demo GWD-01)", seed=42, file_path="Synthetic Demo Well [GWD-01]")

    def _setup_styles(self):
        """Configure clean ttk styles."""
        self.configure(bg=COLOR_APP_BG)
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self.style.configure("Treeview",
                             background=COLOR_SURFACE,
                             foreground=COLOR_TEXT_MAIN,
                             rowheight=26,
                             fieldbackground=COLOR_SURFACE,
                             font=("Segoe UI", 9),
                             borderwidth=0)
        self.style.configure("Treeview.Heading",
                             background="#F8FAFC",
                             foreground=COLOR_TEXT_MAIN,
                             font=("Segoe UI", 9, "bold"),
                             relief="flat",
                             padding=[6, 6],
                             borderwidth=1)
        self.style.map("Treeview.Heading", background=[("active", "#E2E8F0")])
        self.style.map("Treeview",
                       background=[("selected", COLOR_EXCEL_LIGHT)],
                       foreground=[("selected", COLOR_EXCEL_DARK)])

        self.style.configure("TCombobox", padding=4, relief="flat", font=("Segoe UI", 9))

    def _create_top_header_banner(self):
        """Creates signature Excel Green Title Bar."""
        header_bar = tk.Frame(self, bg=COLOR_EXCEL_PRIMARY, height=42, padx=14, pady=6)
        header_bar.pack(side=tk.TOP, fill=tk.X)

        left_box = tk.Frame(header_bar, bg=COLOR_EXCEL_PRIMARY)
        left_box.pack(side=tk.LEFT, fill=tk.Y)

        logo_lbl = tk.Label(left_box, text=" 📊 ", font=("Segoe UI", 12), bg=COLOR_EXCEL_DARK, fg=COLOR_TEXT_WHITE, padx=4, pady=2)
        logo_lbl.pack(side=tk.LEFT, padx=(0, 8))

        title_lbl = tk.Label(left_box, text="MudLog Pro", font=("Segoe UI", 12, "bold"), fg=COLOR_TEXT_WHITE, bg=COLOR_EXCEL_PRIMARY)
        title_lbl.pack(side=tk.LEFT)

        sub_lbl = tk.Label(left_box, text="— Google Sheets Multi-Workspace Edition", font=("Segoe UI", 9), fg="#D1FAE5", bg=COLOR_EXCEL_PRIMARY)
        sub_lbl.pack(side=tk.LEFT, padx=(6, 0))

        self.file_pill = tk.Label(header_bar, text=" 📄 Loading Workspace... ",
                                  font=("Segoe UI", 9, "bold"), bg=COLOR_EXCEL_DARK, fg=COLOR_TEXT_WHITE, padx=12, pady=3)
        self.file_pill.pack(side=tk.LEFT, padx=25)

        author_pill = tk.Label(header_bar, text=f" {APP_AUTHOR} ",
                               font=("Segoe UI", 9, "bold"), bg="#064E3B", fg="#A7F3D0", padx=10, pady=3)
        author_pill.pack(side=tk.RIGHT)

    def _create_menubar(self):
        """Application Menu Bar."""
        menubar = tk.Menu(self, bg=COLOR_SURFACE, fg=COLOR_TEXT_MAIN, relief="flat", bd=0)

        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0, bg=COLOR_SURFACE, fg=COLOR_TEXT_MAIN)
        file_menu.add_command(label="Open Mudlog Data in Active Sheet... (CSV, TXT, Excel)", accelerator="Ctrl+O", command=self.open_file_dialog)
        file_menu.add_command(label="Open Mudlog Data in New Sheet Tab...", accelerator="Ctrl+Shift+O", command=lambda: self.open_file_dialog(in_new_tab=True))
        file_menu.add_command(label="Add New Blank Well Sheet", accelerator="Ctrl+T", command=lambda: self.add_new_sheet())
        file_menu.add_command(label="Load Demo Payzone Well in New Sheet", command=self.add_demo_sheet)
        file_menu.add_separator()
        file_menu.add_command(label="Export Active Sheet Table (CSV)...", accelerator="Ctrl+S", command=self.export_csv_dialog)
        file_menu.add_command(label="Export Multi-Track Chart (PNG/PDF)...", accelerator="Ctrl+P", command=self.export_plot_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", accelerator="Alt+F4", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Edit Menu
        edit_menu = tk.Menu(menubar, tearoff=0, bg=COLOR_SURFACE, fg=COLOR_TEXT_MAIN)
        edit_menu.add_command(label="Edit Petrophysical Formulas & Indicators...", accelerator="F2", command=self.open_formula_manager_dialog)
        edit_menu.add_command(label="Configure Columns & Tracks Display...", accelerator="F3", command=self.open_column_manager_dialog)
        edit_menu.add_separator()
        edit_menu.add_command(label="Rename Active Sheet Tab...", command=self.rename_active_sheet)
        edit_menu.add_command(label="Duplicate Active Sheet Tab...", command=self.duplicate_active_sheet)
        edit_menu.add_command(label="Close Active Sheet Tab", accelerator="Ctrl+W", command=self.close_active_sheet)
        edit_menu.add_separator()
        edit_menu.add_command(label="Reset Sheet to Skripsi Default Parameters", command=self.reset_defaults)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        # View Menu
        view_menu = tk.Menu(menubar, tearoff=0, bg=COLOR_SURFACE, fg=COLOR_TEXT_MAIN)
        view_menu.add_command(label="Switch to Multi-Track Depth Log", accelerator="F5", command=lambda: self.get_active_workspace().switch_view(0))
        view_menu.add_command(label="Switch to Spreadsheet Data Table", accelerator="F6", command=lambda: self.get_active_workspace().switch_view(1))
        view_menu.add_command(label="Switch to Fluid Facies Statistics", accelerator="F7", command=lambda: self.get_active_workspace().switch_view(2))
        view_menu.add_separator()
        view_menu.add_command(label="Detach Active Sheet to Standalone Window ↗", command=lambda: self.get_active_workspace().toggle_detach())
        menubar.add_cascade(label="View", menu=view_menu)

        # Calculations Menu
        calc_menu = tk.Menu(menubar, tearoff=0, bg=COLOR_SURFACE, fg=COLOR_TEXT_MAIN)
        calc_menu.add_command(label="Recompute Active Sheet Indicators", accelerator="F9", command=self.recompute_active_sheet)
        calc_menu.add_command(label="Recompute ALL Sheets", command=self.recompute_all_sheets)
        menubar.add_cascade(label="Calculations", menu=calc_menu)

        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0, bg=COLOR_SURFACE, fg=COLOR_TEXT_MAIN)
        help_menu.add_command(label="Petrophysical Ratios Reference Manual", command=self.show_formulas_help)
        help_menu.add_separator()
        help_menu.add_command(label="About MudLog Pro...", accelerator="F1", command=self.show_about_dialog)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

        # Keyboard shortcuts
        self.bind("<Control-o>", lambda e: self.open_file_dialog())
        self.bind("<Control-O>", lambda e: self.open_file_dialog(in_new_tab=True))
        self.bind("<Control-t>", lambda e: self.add_new_sheet())
        self.bind("<Control-w>", lambda e: self.close_active_sheet())
        self.bind("<Control-s>", lambda e: self.export_csv_dialog())
        self.bind("<Control-p>", lambda e: self.export_plot_dialog())
        self.bind("<F2>", lambda e: self.open_formula_manager_dialog())
        self.bind("<F3>", lambda e: self.open_column_manager_dialog())
        self.bind("<F5>", lambda e: self.get_active_workspace().switch_view(0))
        self.bind("<F6>", lambda e: self.get_active_workspace().switch_view(1))
        self.bind("<F7>", lambda e: self.get_active_workspace().switch_view(2))
        self.bind("<F9>", lambda e: self.recompute_active_sheet())
        self.bind("<F1>", lambda e: self.show_about_dialog())

    def _create_modern_ribbon(self):
        """Clean Office 365 / Sheets style Action Ribbon."""
        ribbon_frame = tk.Frame(self, bg=COLOR_TOOLBAR_BG, padx=10, pady=5, highlightthickness=1,
                                highlightbackground=COLOR_BORDER, highlightcolor=COLOR_BORDER)
        ribbon_frame.pack(side=tk.TOP, fill=tk.X)

        def make_ribbon_btn(parent, text, icon, cmd, is_primary=False):
            bg_col = COLOR_EXCEL_PRIMARY if is_primary else COLOR_TOOLBAR_BG
            fg_col = COLOR_TEXT_WHITE if is_primary else COLOR_TEXT_MAIN
            active_bg = COLOR_EXCEL_DARK if is_primary else "#F3F4F6"

            btn = tk.Button(parent, text=f"{icon}  {text}", font=("Segoe UI", 9, "bold" if is_primary else "normal"),
                            bg=bg_col, fg=fg_col, activebackground=active_bg, activeforeground=fg_col,
                            relief="flat", bd=0, padx=10, pady=5, cursor="hand2", command=cmd,
                            highlightthickness=1, highlightbackground=COLOR_BORDER if not is_primary else COLOR_EXCEL_PRIMARY)
            btn.pack(side=tk.LEFT, padx=3)

            if not is_primary:
                btn.bind("<Enter>", lambda e: btn.config(bg="#F3F4F6"))
                btn.bind("<Leave>", lambda e: btn.config(bg=COLOR_TOOLBAR_BG))
            else:
                btn.bind("<Enter>", lambda e: btn.config(bg=COLOR_EXCEL_DARK))
                btn.bind("<Leave>", lambda e: btn.config(bg=COLOR_EXCEL_PRIMARY))
            return btn

        # Actions
        make_ribbon_btn(ribbon_frame, "Open File", "📂", self.open_file_dialog)
        make_ribbon_btn(ribbon_frame, "New Sheet", "➕", self.add_new_sheet)
        make_ribbon_btn(ribbon_frame, "Export CSV", "💾", self.export_csv_dialog)
        make_ribbon_btn(ribbon_frame, "Export Chart", "📊", self.export_plot_dialog)

        sep1 = tk.Frame(ribbon_frame, width=1, bg=COLOR_BORDER)
        sep1.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=4)

        make_ribbon_btn(ribbon_frame, "Recompute Well", "⚡", self.recompute_active_sheet, is_primary=True)
        make_ribbon_btn(ribbon_frame, "Edit Formulas", "🧮", self.open_formula_manager_dialog)
        make_ribbon_btn(ribbon_frame, "Tracks & Cols", "📐", self.open_column_manager_dialog)

        sep2 = tk.Frame(ribbon_frame, width=1, bg=COLOR_BORDER)
        sep2.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=4)

        # Percentile dropdown
        lbl_p = tk.Label(ribbon_frame, text="Peak Filter:", font=("Segoe UI", 9, "bold"), bg=COLOR_TOOLBAR_BG, fg=COLOR_TEXT_MUTED)
        lbl_p.pack(side=tk.LEFT, padx=(4, 4))

        self.p_var = tk.StringVar(value="P75 (Top 25%)")
        p_combo = ttk.Combobox(ribbon_frame, textvariable=self.p_var, values=["P75 (Top 25%)", "P90 (Top 10%)", "P50 (Top 50%)", "P0 (All Data)"], width=14, state="readonly")
        p_combo.pack(side=tk.LEFT, padx=2)
        p_combo.bind("<<ComboboxSelected>>", self._on_combo_percentile)

        # Right side
        btn_about = make_ribbon_btn(ribbon_frame, "About", "ℹ️", self.show_about_dialog)
        btn_about.pack(side=tk.RIGHT, padx=2)

        btn_demo = make_ribbon_btn(ribbon_frame, "Demo Well", "🔄", self.add_demo_sheet)
        btn_demo.pack(side=tk.RIGHT, padx=2)

    def _create_formula_bar(self):
        """Excel / Google Sheets Formula Bar (fx) & Depth Inspector."""
        fx_frame = tk.Frame(self, bg=COLOR_SURFACE, padx=8, pady=5, highlightthickness=1,
                            highlightbackground=COLOR_BORDER, highlightcolor=COLOR_BORDER)
        fx_frame.pack(side=tk.TOP, fill=tk.X)

        name_box_frame = tk.Frame(fx_frame, bg="#F9FAFB", highlightthickness=1, highlightbackground=COLOR_BORDER_DARK)
        name_box_frame.pack(side=tk.LEFT, padx=(2, 6))

        tk.Label(name_box_frame, text="DEPTH", font=("Segoe UI", 8, "bold"), bg="#F9FAFB", fg=COLOR_EXCEL_PRIMARY, padx=6).pack(side=tk.LEFT)

        self.depth_entry_var = tk.StringVar(value="1815.0 m")
        depth_box = tk.Entry(name_box_frame, textvariable=self.depth_entry_var, font=("Consolas", 9, "bold"), width=10,
                             bg="#FFFFFF", fg=COLOR_TEXT_MAIN, relief="flat", bd=0, justify="center")
        depth_box.pack(side=tk.LEFT, padx=4, pady=2)

        btn_fx = tk.Label(fx_frame, text=" fx ", font=("Georgia", 11, "bold", "italic"), bg=COLOR_EXCEL_LIGHT, fg=COLOR_EXCEL_PRIMARY,
                          relief="flat", cursor="hand2", padx=6, pady=2)
        btn_fx.pack(side=tk.LEFT, padx=(2, 6))
        btn_fx.bind("<Button-1>", lambda e: self.open_formula_manager_dialog())

        entry_wrap = tk.Frame(fx_frame, bg=COLOR_SURFACE, highlightthickness=1, highlightbackground=COLOR_BORDER)
        entry_wrap.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        self.formula_bar_var = tk.StringVar(value="WH = ((C2 + C3 + IC4 + NC4 + IC5 + NC5) / TG) * 100.0   |   BH = (C1 + C2) / (C3 + IC4 + NC4 + IC5 + NC5)")
        fx_entry = tk.Entry(entry_wrap, textvariable=self.formula_bar_var, font=("Consolas", 9),
                            bg=COLOR_SURFACE, fg=COLOR_TEXT_MAIN, relief="flat", bd=0)
        fx_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6, pady=3)

        self.facies_badge_label = tk.Label(fx_frame, text=" ZONE: READY ", font=("Segoe UI", 8, "bold"),
                                           bg=COLOR_EXCEL_LIGHT, fg=COLOR_EXCEL_DARK, padx=10, pady=3)
        self.facies_badge_label.pack(side=tk.RIGHT, padx=4)

    def _create_workspace_viewport(self):
        """Host container where the active docked workspace is shown."""
        self.workspace_host = tk.Frame(self, bg=COLOR_APP_BG)
        self.workspace_host.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def _create_sheets_bottom_tab_bar(self):
        """Creates Google Sheets style multi-tab bar at the bottom with drag-and-drop tear off."""
        self.sheets_bar = tk.Frame(self, bg="#E5E7EB", height=38, padx=6, pady=3,
                                   highlightthickness=1, highlightbackground=COLOR_BORDER)
        self.sheets_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Left: Add Sheet (+) Button (Signature Google Sheets style)
        btn_add = tk.Button(self.sheets_bar, text=" ➕ ", font=("Segoe UI", 10, "bold"),
                            bg=COLOR_SURFACE, fg=COLOR_EXCEL_PRIMARY, relief="flat", bd=0, padx=8, pady=3,
                            cursor="hand2", highlightthickness=1, highlightbackground=COLOR_BORDER,
                            command=lambda: self.add_new_sheet())
        btn_add.pack(side=tk.LEFT, padx=(2, 6))
        btn_add.bind("<Enter>", lambda e: btn_add.config(bg=COLOR_EXCEL_LIGHT))
        btn_add.bind("<Leave>", lambda e: btn_add.config(bg=COLOR_SURFACE))

        # Scrollable / Packable Container for Sheet Tabs
        self.tabs_container = tk.Frame(self.sheets_bar, bg="#E5E7EB")
        self.tabs_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _create_statusbar(self):
        """Bottom Status Bar."""
        status_frame = tk.Frame(self, bg=COLOR_EXCEL_PRIMARY, padx=10, pady=3)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        def make_pane(parent, width=None, side=tk.LEFT):
            pane = tk.Label(parent, font=("Segoe UI", 9), bg=COLOR_EXCEL_PRIMARY, fg=COLOR_TEXT_WHITE,
                            anchor="w", padx=8, pady=1, width=width)
            pane.pack(side=side, padx=4, fill=tk.X if width is None else tk.NONE, expand=(width is None))
            return pane

        self.status_msg = make_pane(status_frame, None, side=tk.LEFT)
        self.status_depth = make_pane(status_frame, 32, side=tk.LEFT)
        self.status_tracks = make_pane(status_frame, 18, side=tk.LEFT)
        self.status_facies = make_pane(status_frame, 34, side=tk.LEFT)
        
        self.status_author = tk.Label(status_frame, text=f" {APP_AUTHOR} ", font=("Segoe UI", 9, "bold"),
                                      bg=COLOR_EXCEL_DARK, fg="#A7F3D0", padx=10, pady=2)
        self.status_author.pack(side=tk.RIGHT, padx=2)

    # ──────────────────────────────────────────────────────────────────────────
    #  Google Sheets Multi-Tab Management & Drag-to-Tear-Off
    # ──────────────────────────────────────────────────────────────────────────
    def add_new_sheet(self, name=None, raw_df=None, file_path=None, seed=None):
        """Creates a new workspace tab (WellState + WellWorkspace view)."""
        self.sheet_counter += 1
        sheet_id   = f"sheet_{self.sheet_counter}"
        sheet_name = name if name else f"Sheet {len(self.workspaces) + 1}"

        if seed is None:
            seed = np.random.randint(100, 9999)
        if raw_df is None:
            raw_df = generate_synthetic_mudlog(
                seed=seed,
                well_name=f"Well-{self.sheet_counter}",
                base_depth=1500.0 + (len(self.workspaces) * 300.0))
        if file_path is None:
            file_path = f"Dataset_{sheet_name}.csv"

        state = WellState(sheet_id, sheet_name, file_path, raw_df)
        ws    = WellWorkspace(self.workspace_host, self, state)
        # Store the state so tab management works on state objects
        self.workspaces.append(state)
        self._views[state.sheet_id] = ws
        self.switch_to_sheet(len(self.workspaces) - 1)
        self.render_sheet_tabs()
        return state

    def add_demo_sheet(self):
        """Adds a demo well sheet."""
        n = len(self.workspaces) + 1
        ws = self.add_new_sheet(name=f"Demo Well {n}", raw_df=generate_synthetic_mudlog(seed=42 + n*13), file_path=f"Synthetic Demo [GWD-0{n}]")
        messagebox.showinfo("Demo Sheet Added", f"Created new workspace tab: '{ws.sheet_name}' with synthetic payzone data.", parent=self)

    def switch_to_sheet(self, idx):
        """Switches the active docked sheet tab."""
        if not self.workspaces:
            return

        idx = max(0, min(idx, len(self.workspaces) - 1))
        self.active_workspace_idx = idx

        # Hide other docked views, show active one
        for i, state in enumerate(self.workspaces):
            view = self._views.get(state.sheet_id)
            if view is None:
                continue
            if not state.is_detached:
                if i == idx:
                    view.pack(fill=tk.BOTH, expand=True)
                else:
                    view.pack_forget()

        active_state = self.get_active_workspace()
        if active_state:
            self.file_pill.config(
                text=f" 📄 {active_state.sheet_name} • {active_state.file_path} ")
            self.update_status(
                f"Active workspace: {active_state.sheet_name} ({active_state.file_path})")
            view = self._views.get(active_state.sheet_id)
            if view:
                view.refresh_workspace()

        self.render_sheet_tabs()

    def get_active_workspace(self) -> 'WellState | None':
        """Returns the currently active WellState."""
        if 0 <= self.active_workspace_idx < len(self.workspaces):
            return self.workspaces[self.active_workspace_idx]
        return None

    def render_sheet_tabs(self):
        """Renders Google Sheets style bottom tab buttons."""
        for widget in self.tabs_container.winfo_children():
            widget.destroy()

        for idx, state in enumerate(self.workspaces):
            is_active   = (idx == self.active_workspace_idx)
            is_detached = state.is_detached

            tab_bg = (COLOR_SURFACE  if (is_active and not is_detached) else
                      "#F9FAFB"      if not is_detached else "#E2E8F0")
            tab_fg = (COLOR_EXCEL_PRIMARY if (is_active and not is_detached)
                      else COLOR_TEXT_MAIN)

            tab_frame = tk.Frame(self.tabs_container, bg=tab_bg, padx=8, pady=4,
                                 highlightthickness=1,
                                 highlightbackground=(
                                     COLOR_EXCEL_PRIMARY if (is_active and not is_detached)
                                     else COLOR_BORDER_DARK))
            tab_frame.pack(side=tk.LEFT, padx=2)

            # Google-Sheets style green top accent line on active tab
            if is_active and not is_detached:
                tk.Frame(tab_frame, bg=COLOR_EXCEL_PRIMARY, height=3
                         ).pack(side=tk.TOP, fill=tk.X, pady=(0, 2))

            content_box = tk.Frame(tab_frame, bg=tab_bg)
            content_box.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

            icon_text = "🪟" if is_detached else "📄"
            lbl_icon = tk.Label(content_box, text=icon_text,
                                font=("Segoe UI", 9), bg=tab_bg)
            lbl_icon.pack(side=tk.LEFT, padx=(0, 4))

            lbl_name = tk.Label(
                content_box,
                text=state.sheet_name + (" ↗" if is_detached else ""),
                font=("Segoe UI", 9, "bold" if is_active else "normal"),
                bg=tab_bg, fg=tab_fg, cursor="hand2")
            lbl_name.pack(side=tk.LEFT, padx=(0, 6))

            # Bind clicks / drag to the whole tab
            for w in (tab_frame, content_box, lbl_icon, lbl_name):
                w.bind("<Button-1>",        lambda e, i=idx: self._on_tab_press(e, i))
                w.bind("<B1-Motion>",        self._on_tab_drag)
                w.bind("<ButtonRelease-1>", lambda e, i=idx: self._on_tab_release(e, i))
                w.bind("<Double-Button-1>", lambda e, i=idx: self.rename_sheet_dialog(i))
                w.bind("<Button-3>",        lambda e, i=idx: self._show_tab_context_menu(e, i))

            # Detach ↗ / Re-attach ↙ button
            detach_text = " ↙ " if is_detached else " ↗ "
            btn_det = tk.Label(content_box, text=detach_text,
                               font=("Segoe UI", 8, "bold"),
                               bg=tab_bg, fg=COLOR_TEXT_MUTED, cursor="hand2")
            btn_det.pack(side=tk.LEFT, padx=2)
            btn_det.bind("<Button-1>",
                         lambda e, s=state: (
                             self.reattach_workspace(s) if s.is_detached
                             else self.detach_workspace(s)))

            # Close ✕ button
            if len(self.workspaces) > 1:
                btn_close = tk.Label(content_box, text=" ✕ ",
                                     font=("Segoe UI", 8),
                                     bg=tab_bg, fg=COLOR_TEXT_MUTED, cursor="hand2")
                btn_close.pack(side=tk.LEFT, padx=(2, 0))
                btn_close.bind("<Button-1>", lambda e, i=idx: self.close_sheet(i))
                btn_close.bind("<Enter>",    lambda e, b=btn_close: b.config(fg="#DC2626"))
                btn_close.bind("<Leave>",    lambda e, b=btn_close: b.config(fg=COLOR_TEXT_MUTED))

    # ──────────────────────────────────────────────────────────────────────────
    #  Drag and Drop Tab Tear-Off Interaction
    # ──────────────────────────────────────────────────────────────────────────
    def _on_tab_press(self, event, idx):
        self.switch_to_sheet(idx)
        self._drag_data["tab_idx"] = idx
        self._drag_data["start_x"] = event.x_root
        self._drag_data["start_y"] = event.y_root
        self._drag_data["dragging"] = False

    def _on_tab_drag(self, event):
        dx = abs(event.x_root - self._drag_data["start_x"])
        dy = abs(event.y_root - self._drag_data["start_y"])
        if dx > 15 or dy > 15:
            self._drag_data["dragging"] = True

    def _on_tab_release(self, event, idx):
        if self._drag_data["dragging"]:
            # If dragged outside main app window boundaries, detach into its own floating window!
            app_x = self.winfo_rootx()
            app_y = self.winfo_rooty()
            app_w = self.winfo_width()
            app_h = self.winfo_height()

            cur_x = event.x_root
            cur_y = event.y_root

            # Detach if released outside the app window bounds
            if (cur_x < app_x or cur_x > (app_x + app_w) or
                    cur_y < app_y or cur_y > (app_y + app_h)):
                state = self.workspaces[idx]
                if not state.is_detached:
                    self.detach_workspace(state)
        self._drag_data["dragging"] = False

    def detach_workspace(self, state: 'WellState'):
        """Pops a WellState into its own standalone DetachedWellWindow."""
        if state.is_detached:
            return

        # Hide the docked view
        docked_view = self._views.get(state.sheet_id)
        if docked_view:
            docked_view.pack_forget()

        state.is_detached = True
        detached_win = DetachedWellWindow(self, state)
        state.detached_window = detached_win

        # Switch main window to first remaining docked tab
        remaining = [i for i, s in enumerate(self.workspaces) if not s.is_detached]
        if remaining:
            self.switch_to_sheet(remaining[0])
        else:
            self.render_sheet_tabs()

        self.update_status(f"Detached '{state.sheet_name}' into standalone window.")

    def reattach_workspace(self, state: 'WellState'):
        """Closes the detached window and makes the tab docked again."""
        if not state.is_detached:
            return

        # Destroy the floating window (and the WellWorkspace view inside it)
        if state.detached_window:
            # Remove the detached view from state.views so it isn't refreshed
            det_view = state.detached_window.view
            if det_view in state.views:
                state.views.remove(det_view)
            state.detached_window.destroy()
            state.detached_window = None

        state.is_detached = False

        # Make sure a fresh docked view exists (it was never destroyed)
        docked_view = self._views.get(state.sheet_id)
        if docked_view is None:
            docked_view = WellWorkspace(self.workspace_host, self, state)
            self._views[state.sheet_id] = docked_view

        idx = self.workspaces.index(state)
        self.switch_to_sheet(idx)
        self.update_status(f"Re-attached '{state.sheet_name}' back to main window.")

    def _show_tab_context_menu(self, event, idx):
        """Right click context menu on sheet tab."""
        state = self.workspaces[idx]
        menu = tk.Menu(self, tearoff=0, bg=COLOR_SURFACE, fg=COLOR_TEXT_MAIN)
        menu.add_command(label=f"Rename '{state.sheet_name}'...",
                         command=lambda: self.rename_sheet_dialog(idx))

        if not state.is_detached:
            menu.add_command(label="Detach to Separate Window ↗",
                             command=lambda s=state: self.detach_workspace(s))
        else:
            menu.add_command(label="Re-attach to Main Window ↙",
                             command=lambda s=state: self.reattach_workspace(s))

        menu.add_command(label="Duplicate Sheet",
                         command=lambda: self.duplicate_sheet(idx))
        menu.add_command(label="Load File into this Sheet...",
                         command=lambda: self.open_file_dialog(target_workspace_idx=idx))

        if len(self.workspaces) > 1:
            menu.add_separator()
            menu.add_command(label="Close Sheet ✕",
                             command=lambda: self.close_sheet(idx))

        menu.tk_popup(event.x_root, event.y_root)

    def rename_sheet_dialog(self, idx):
        state = self.workspaces[idx]
        new_name = simpledialog.askstring(
            "Rename Sheet", "Enter new name for sheet tab:",
            initialvalue=state.sheet_name, parent=self)
        if new_name and new_name.strip():
            state.sheet_name = new_name.strip()
            self.render_sheet_tabs()
            if state is self.get_active_workspace():
                self.file_pill.config(
                    text=f" 📄 {state.sheet_name} • {state.file_path} ")
            if state.detached_window:
                state.detached_window.title(
                    f"MudLog Pro — [{state.sheet_name}] ↗ ({state.file_path})")
                state.detached_window.title_lbl.config(
                    text=f"📊 MudLog Pro  •  Detached Well Window  [{state.sheet_name}]")

    def rename_active_sheet(self):
        self.rename_sheet_dialog(self.active_workspace_idx)

    def duplicate_sheet(self, idx):
        src = self.workspaces[idx]
        new_state = self.add_new_sheet(
            name=f"{src.sheet_name} (Copy)",
            raw_df=src.raw_df.copy(),
            file_path=src.file_path)
        new_state.formulas        = dict(src.formulas)
        new_state.thresholds      = dict(src.thresholds)
        new_state.schema          = [dict(s) for s in src.schema]
        new_state.percentile_cutoff = src.percentile_cutoff
        new_state.recompute()
        messagebox.showinfo("Duplicated",
            f"Duplicated sheet '{src.sheet_name}' into new tab.", parent=self)

    def duplicate_active_sheet(self):
        self.duplicate_sheet(self.active_workspace_idx)

    def close_sheet(self, idx):
        if len(self.workspaces) <= 1:
            messagebox.showwarning("Close Sheet",
                "Cannot close the last remaining sheet tab.", parent=self)
            return

        state = self.workspaces[idx]
        if messagebox.askyesno("Close Sheet",
                f"Close and remove sheet '{state.sheet_name}'?", parent=self):
            if state.detached_window:
                state.detached_window.destroy()
            view = self._views.pop(state.sheet_id, None)
            if view:
                try:
                    view.destroy()
                except Exception:
                    pass
            self.workspaces.pop(idx)
            self.switch_to_sheet(max(0, idx - 1))

    def close_active_sheet(self):
        self.close_sheet(self.active_workspace_idx)

    # ──────────────────────────────────────────────────────────────────────────
    #  Hover & Formula Bar Updates
    # ──────────────────────────────────────────────────────────────────────────
    def update_formula_bar_hover(self, workspace: 'WellWorkspace', depth_val: float):
        """Updates top formula bar when hovering in a docked workspace view."""
        self.depth_entry_var.set(f"{depth_val:.1f} m")
        df = workspace.computed_df
        if df is None or df.empty:
            return
        row_idx = (df["DEPTH"] - depth_val).abs().idxmin()
        row = df.loc[row_idx]
        zone = row.get("ZONE", "Unknown")
        c1 = row.get("C1", 0.0)
        tg = row.get("TG_USED", row.get("TG", 0.0))
        wh = row.get("WH", 0.0)

        if zone == "Gas":
            self.facies_badge_label.config(
                text=" 🔴 GAS PAYZONE ", bg=COLOR_GAS_BG, fg=COLOR_GAS_TEXT)
        elif zone == "Oil":
            self.facies_badge_label.config(
                text=" 🟢 OIL PAYZONE ", bg=COLOR_OIL_BG, fg=COLOR_OIL_TEXT)
        else:
            self.facies_badge_label.config(
                text=" ⚪ NON-BEARING ", bg=COLOR_DRY_BG, fg=COLOR_DRY_TEXT)

        self.formula_bar_var.set(
            f"[{workspace.sheet_name}] Depth: {row['DEPTH']:.1f}m | "
            f"C1: {c1:.1f} ppm | TG: {tg:.1f} ppm | Wh: {wh:.1f}% | Zone: {zone}")

    def update_status(self, msg):
        """Updates main status bar."""
        self.status_msg.config(text=f"✓ Ready: {msg}")
        state = self.get_active_workspace()
        if state and state.computed_df is not None and not state.computed_df.empty:
            d_min = state.computed_df["DEPTH"].min()
            d_max = state.computed_df["DEPTH"].max()
            n_pts = len(state.computed_df)
            self.status_depth.config(
                text=f"Depth: {d_min:.1f}m - {d_max:.1f}m ({n_pts} rows)")

            n_active = sum(1 for s in state.schema if s.get("visible", True))
            self.status_tracks.config(text=f"Active Tracks: {n_active}")

            if "ZONE" in state.computed_df.columns:
                z_counts = state.computed_df["ZONE"].value_counts().to_dict()
                gas_cnt  = z_counts.get("Gas", 0)
                oil_cnt  = z_counts.get("Oil", 0)
                dry_cnt  = z_counts.get("Non-Bearing", 0)
                self.status_facies.config(
                    text=f"Gas: {gas_cnt} | Oil: {oil_cnt} | Non-Bearing: {dry_cnt}")

    # ──────────────────────────────────────────────────────────────────────────
    #  Actions & Dialogs
    # ──────────────────────────────────────────────────────────────────────────
    def recompute_active_sheet(self):
        state = self.get_active_workspace()
        if state:
            state.recompute()
            self.update_status(f"Recomputed {state.sheet_name}.")
            messagebox.showinfo("Computation Complete",
                f"Petrophysical indicators and facies recomputed for '{state.sheet_name}'.",
                parent=self)

    def recompute_all_sheets(self):
        for state in self.workspaces:
            state.recompute()
        self.update_status("Recomputed all open sheets.")
        messagebox.showinfo("Complete",
            f"Recomputed all {len(self.workspaces)} workspace sheets.", parent=self)

    def _on_combo_percentile(self, event):
        val = self.p_var.get()
        p = 75 if "75" in val else (90 if "90" in val else (50 if "50" in val else 0))
        state = self.get_active_workspace()
        if state:
            state.percentile_cutoff = float(p)
            view = self._views.get(state.sheet_id)
            if view:
                view.render_multi_track_plot()
            self.update_status(f"Filter cutoff updated to P{p}% for {state.sheet_name}.")

    def open_file_dialog(self, in_new_tab=False, target_workspace_idx=None):
        fpath = filedialog.askopenfilename(
            parent=self,
            title="Open Mudlog Data File",
            filetypes=[
                ("Supported Mudlog Files (*.csv;*.txt;*.xlsx;*.xls)", "*.csv;*.txt;*.xlsx;*.xls"),
                ("CSV Files (*.csv)", "*.csv"),
                ("Text Log Files (*.txt)", "*.txt"),
                ("Excel Workbooks (*.xlsx;*.xls)", "*.xlsx;*.xls"),
                ("All Files (*.*)", "*.*")
            ]
        )
        if not fpath:
            return

        try:
            df_parsed = parse_mudlog_file(fpath)
            if df_parsed.empty:
                raise ValueError("Parsed mudlog dataframe is empty or invalid.")

            fname = os.path.basename(fpath)
            if in_new_tab:
                self.add_new_sheet(name=fname[:20], raw_df=df_parsed, file_path=fname)
            else:
                if target_workspace_idx is not None:
                    target_state = self.workspaces[target_workspace_idx]
                else:
                    target_state = self.get_active_workspace()
                if target_state:
                    target_state.file_path = fname
                    target_state.raw_df    = df_parsed
                    target_state.recompute()
                    self.file_pill.config(
                        text=f" 📄 {target_state.sheet_name} • {fname} ")

            self.update_status(f"Loaded {fname} ({len(df_parsed)} intervals).")
            messagebox.showinfo("File Loaded",
                f"Successfully loaded mudlog data from:\n{fname}\n({len(df_parsed)} intervals)",
                parent=self)
        except Exception as e:
            messagebox.showerror("File Ingestion Error",
                f"Failed to parse mudlog file:\n{str(e)}", parent=self)

    def export_csv_dialog(self):
        state = self.get_active_workspace()
        if not state or state.computed_df is None or state.computed_df.empty:
            messagebox.showwarning("Export",
                "No computed data in active sheet to export.", parent=self)
            return

        fpath = filedialog.asksaveasfilename(
            parent=self,
            title=f"Export [{state.sheet_name}] Calculated Log Table to CSV",
            defaultextension=".csv",
            filetypes=[("CSV (Comma Delimited) (*.csv)", "*.csv"),
                       ("All Files (*.*)", "*.*")])
        if not fpath:
            return

        try:
            state.computed_df.to_csv(fpath, index=False)
            messagebox.showinfo("Export Successful",
                f"Table from '{state.sheet_name}' exported to:\n{fpath}", parent=self)
        except Exception as e:
            messagebox.showerror("Export Error",
                f"Failed to export CSV:\n{str(e)}", parent=self)

    def export_plot_dialog(self):
        state = self.get_active_workspace()
        view  = self._views.get(state.sheet_id) if state else None
        if not view:
            return

        fpath = filedialog.asksaveasfilename(
            parent=self,
            title=f"Export [{state.sheet_name}] Multi-Track Well Log Chart",
            defaultextension=".png",
            filetypes=[("PNG Image (*.png)", "*.png"),
                       ("PDF Vector Document (*.pdf)", "*.pdf"),
                       ("JPEG Image (*.jpg)", "*.jpg")])
        if not fpath:
            return

        try:
            view.fig.savefig(fpath, dpi=300, bbox_inches="tight")
            messagebox.showinfo("Chart Exported",
                f"Multi-track plot from '{state.sheet_name}' exported to:\n{fpath}",
                parent=self)
        except Exception as e:
            messagebox.showerror("Export Error",
                f"Failed to export plot:\n{str(e)}", parent=self)

    def reset_defaults(self):
        state = self.get_active_workspace()
        if not state:
            return
        if messagebox.askyesno("Reset Defaults",
                f"Restore all formulas and track schemas for '{state.sheet_name}' to thesis defaults?",
                parent=self):
            state.formulas   = {k: v["expr"] for k, v in DEFAULT_FORMULAS.items()}
            state.thresholds = dict(DEFAULT_THRESHOLDS)
            state.schema     = [dict(s) for s in DEFAULT_TRACK_SCHEMA]
            state.recompute()
            messagebox.showinfo("Reset",
                f"Defaults restored for '{state.sheet_name}'.", parent=self)

    def open_formula_manager_dialog(self):
        state = self.get_active_workspace()
        if not state:
            return
        # Use state directly — the dialog reads/writes WellState attributes
        ws = state   # alias for the code below (minimal change)

        dlg = tk.Toplevel(self)
        dlg.title(f"Formula & Indicator Manager — [{ws.sheet_name}]")
        dlg.geometry("780x560")
        dlg.transient(self)
        dlg.grab_set()
        dlg.configure(bg=COLOR_APP_BG)

        hdr = tk.Frame(dlg, bg=COLOR_EXCEL_PRIMARY, padx=16, pady=12)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text=f"🧮 Custom Petrophysical Formula Manager — [{ws.sheet_name}]",
                 font=("Segoe UI", 12, "bold"), fg=COLOR_TEXT_WHITE, bg=COLOR_EXCEL_PRIMARY).pack(anchor="w")
        tk.Label(hdr, text="Variables: C1, C2, C3, IC4, NC4, IC5, NC5, TG",
                 font=("Segoe UI", 9), fg="#D1FAE5", bg=COLOR_EXCEL_PRIMARY).pack(anchor="w", pady=(2, 0))

        body = tk.Frame(dlg, bg=COLOR_APP_BG, padx=16, pady=14)
        body.pack(fill=tk.BOTH, expand=True)

        card = tk.Frame(body, bg=COLOR_SURFACE, highlightthickness=1, highlightbackground=COLOR_BORDER)
        card.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(card, bg=COLOR_SURFACE, relief="flat", bd=0, highlightthickness=0)
        scroll = ttk.Scrollbar(card, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=COLOR_SURFACE)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        entry_vars = {}
        for key, default_meta in DEFAULT_FORMULAS.items():
            row_frame = tk.Frame(scroll_frame, bg=COLOR_SURFACE, pady=6, padx=12)
            row_frame.pack(fill=tk.X, expand=True)

            tk.Label(row_frame, text=f"{key} — {default_meta.get('name', key)}",
                     font=("Segoe UI", 9, "bold"), bg=COLOR_SURFACE, fg=COLOR_EXCEL_PRIMARY).pack(anchor="w")
            
            var = tk.StringVar(value=ws.formulas.get(key, default_meta["expr"]))
            entry_vars[key] = var

            ent_wrap = tk.Frame(row_frame, bg=COLOR_SURFACE, highlightthickness=1, highlightbackground=COLOR_BORDER)
            ent_wrap.pack(fill=tk.X, expand=True, pady=2)

            ent = tk.Entry(ent_wrap, textvariable=var, font=("Consolas", 10),
                           bg="#F9FAFB", fg=COLOR_TEXT_MAIN, relief="flat", bd=0)
            ent.pack(fill=tk.X, expand=True, padx=6, pady=4)

        footer = tk.Frame(dlg, bg=COLOR_SURFACE, padx=14, pady=10, highlightthickness=1, highlightbackground=COLOR_BORDER)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        def save_formulas():
            for k, var in entry_vars.items():
                ws.formulas[k] = var.get().strip()
            ws.recompute()   # WellState.recompute() updates all views
            dlg.destroy()

        def restore_defaults():
            for k, default_meta in DEFAULT_FORMULAS.items():
                if k in entry_vars:
                    entry_vars[k].set(default_meta["expr"])

        btn_save = tk.Button(footer, text="💾 Save & Recompute Sheet", font=("Segoe UI", 9, "bold"),
                             bg=COLOR_EXCEL_PRIMARY, fg=COLOR_TEXT_WHITE, relief="flat", bd=0, padx=14, pady=6,
                             cursor="hand2", command=save_formulas)
        btn_save.pack(side=tk.RIGHT, padx=4)

        btn_reset = tk.Button(footer, text="↺ Reset Defaults", font=("Segoe UI", 9),
                              bg=COLOR_APP_BG, fg=COLOR_TEXT_MAIN, relief="flat", bd=0, padx=10, pady=6,
                              cursor="hand2", command=restore_defaults)
        btn_reset.pack(side=tk.RIGHT, padx=4)

        btn_cancel = tk.Button(footer, text="Cancel", font=("Segoe UI", 9),
                               bg=COLOR_APP_BG, fg=COLOR_TEXT_MAIN, relief="flat", bd=0, padx=10, pady=6,
                               cursor="hand2", command=dlg.destroy)
        btn_cancel.pack(side=tk.LEFT, padx=4)

    def open_column_manager_dialog(self):
        state = self.get_active_workspace()
        if not state:
            return
        ws = state  # alias

        dlg = tk.Toplevel(self)
        dlg.title(f"Column & Track Display — [{ws.sheet_name}]")
        dlg.geometry("600x540")
        dlg.transient(self)
        dlg.grab_set()
        dlg.configure(bg=COLOR_APP_BG)

        hdr = tk.Frame(dlg, bg=COLOR_EXCEL_PRIMARY, padx=16, pady=12)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text=f"📐 Column & Multi-Track Display — [{ws.sheet_name}]",
                 font=("Segoe UI", 12, "bold"), fg=COLOR_TEXT_WHITE, bg=COLOR_EXCEL_PRIMARY).pack(anchor="w")
        tk.Label(hdr, text="Toggle which tracks appear on the depth log canvas.",
                 font=("Segoe UI", 9), fg="#D1FAE5", bg=COLOR_EXCEL_PRIMARY).pack(anchor="w", pady=(2, 0))

        body = tk.Frame(dlg, bg=COLOR_APP_BG, padx=16, pady=14)
        body.pack(fill=tk.BOTH, expand=True)

        card = tk.Frame(body, bg=COLOR_SURFACE, highlightthickness=1, highlightbackground=COLOR_BORDER)
        card.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(card, bg=COLOR_SURFACE, relief="flat", bd=0, highlightthickness=0)
        scroll = ttk.Scrollbar(card, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=COLOR_SURFACE)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        check_vars = []
        for track in ws.schema:
            row_frame = tk.Frame(scroll_frame, bg=COLOR_SURFACE, pady=4, padx=12)
            row_frame.pack(fill=tk.X, expand=True)

            var = tk.BooleanVar(value=track.get("visible", True))
            check_vars.append((track, var))

            chk = tk.Checkbutton(row_frame, text=f"{track['key']} — {track['name'].replace(chr(10), ' ')}",
                                 variable=var, font=("Segoe UI", 9), bg=COLOR_SURFACE, fg=COLOR_TEXT_MAIN,
                                 activebackground=COLOR_SURFACE, selectcolor="#FFFFFF", anchor="w")
            chk.pack(side=tk.LEFT)

        footer = tk.Frame(dlg, bg=COLOR_SURFACE, padx=14, pady=10, highlightthickness=1, highlightbackground=COLOR_BORDER)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        def apply_changes():
            for track, var in check_vars:
                track["visible"] = var.get()
            # Re-render all active views for this state
            for v in list(ws.views):
                try:
                    v.render_multi_track_plot()
                except Exception:
                    pass
            self.update_status(f"Track visibility updated for {ws.sheet_name}.")
            dlg.destroy()

        btn_apply = tk.Button(footer, text="Apply Changes", font=("Segoe UI", 9, "bold"),
                              bg=COLOR_EXCEL_PRIMARY, fg=COLOR_TEXT_WHITE, relief="flat", bd=0, padx=14, pady=6,
                              cursor="hand2", command=apply_changes)
        btn_apply.pack(side=tk.RIGHT, padx=4)

        btn_all = tk.Button(footer, text="Select All", font=("Segoe UI", 9),
                            bg=COLOR_APP_BG, fg=COLOR_TEXT_MAIN, relief="flat", bd=0, padx=8, pady=6,
                            cursor="hand2", command=lambda: [v.set(True) for _, v in check_vars])
        btn_all.pack(side=tk.LEFT, padx=2)

        btn_none = tk.Button(footer, text="Deselect All", font=("Segoe UI", 9),
                             bg=COLOR_APP_BG, fg=COLOR_TEXT_MAIN, relief="flat", bd=0, padx=8, pady=6,
                             cursor="hand2", command=lambda: [v.set(False) for _, v in check_vars])
        btn_none.pack(side=tk.LEFT, padx=2)

    def show_formulas_help(self):
        msg = (
            "PETROPHYSICAL RATIOS & FLUID TYPING REFERENCE\n\n"
            "• Haworth Wetness Ratio (Wh):\n"
            "  Wh = ((C2 + C3 + iC4 + nC4 + iC5 + nC5) / TG) * 100\n"
            "  Gas: 0.5 <= Wh < 17.5 | Oil: 17.5 <= Wh <= 40.0\n\n"
            "• Haworth Balance Ratio (Bh):\n"
            "  Bh = (C1 + C2) / (C3 + iC4 + nC4 + iC5 + nC5)\n"
            "  Gas: Bh >= 15.0 | Oil: 0.5 <= Bh < 15.0\n\n"
            "• Pixler R1 Ratio:\n"
            "  R1 = C1 / C2\n"
            "  Gas: R1 >= 15.0 | Oil: 2.0 <= R1 < 15.0\n\n"
            "• Gas Dryness Ratio (DR):\n"
            "  DR = C1 / TG\n"
            "  Gas: DR >= 0.85 | Oil: DR < 0.85"
        )
        messagebox.showinfo("Methodology Reference", msg, parent=self)

    def show_about_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("About MudLog Pro")
        dlg.geometry("520x400")
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()
        dlg.configure(bg=COLOR_APP_BG)

        hdr = tk.Frame(dlg, bg=COLOR_EXCEL_PRIMARY, padx=18, pady=16)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="MudLog Pro Desktop Software", font=("Segoe UI", 14, "bold"), fg=COLOR_TEXT_WHITE, bg=COLOR_EXCEL_PRIMARY).pack(anchor="w")
        tk.Label(hdr, text=f"Version {APP_VERSION} • Google Sheets Multi-Workspace Edition", font=("Segoe UI", 9), fg="#D1FAE5", bg=COLOR_EXCEL_PRIMARY).pack(anchor="w", pady=(2, 0))

        body = tk.Frame(dlg, bg=COLOR_APP_BG, padx=18, pady=16)
        body.pack(fill=tk.BOTH, expand=True)

        tk.Label(body, text="Deterministic Multi-Track Well Logging Suite", font=("Segoe UI", 10, "bold"), bg=COLOR_APP_BG, fg=COLOR_TEXT_MAIN).pack(anchor="w", pady=(0, 4))
        tk.Label(body, text="Independent Multi-Tab well workspaces (Google Sheets style), drag-and-drop window tear-off, continuous logging, and fluid facies zone classification.",
                 font=("Segoe UI", 9), bg=COLOR_APP_BG, fg=COLOR_TEXT_MUTED, wraplength=480, justify="left").pack(anchor="w", pady=(0, 12))

        attr_frame = tk.Frame(body, bg=COLOR_SURFACE, padx=16, pady=12, highlightthickness=1, highlightbackground=COLOR_BORDER)
        attr_frame.pack(fill=tk.X, pady=4)

        tk.Label(attr_frame, text="RESEARCH SOFTWARE CREATOR", font=("Segoe UI", 8, "bold"), fg=COLOR_EXCEL_PRIMARY, bg=COLOR_SURFACE).pack(anchor="w")
        tk.Label(attr_frame, text="Mohammad Azka Khairur Rahman", font=("Segoe UI", 13, "bold"), fg=COLOR_TEXT_MAIN, bg=COLOR_SURFACE).pack(anchor="w", pady=2)
        tk.Label(attr_frame, text="Mudlogging & Petrophysical Analysis Research Software", font=("Segoe UI", 8), fg=COLOR_TEXT_MUTED, bg=COLOR_SURFACE).pack(anchor="w")

        btn_ok = tk.Button(dlg, text="OK", font=("Segoe UI", 9, "bold"), bg=COLOR_EXCEL_PRIMARY, fg=COLOR_TEXT_WHITE,
                           relief="flat", bd=0, padx=18, pady=6, cursor="hand2", command=dlg.destroy)
        btn_ok.pack(side=tk.BOTTOM, pady=14)


# ──────────────────────────────────────────────────────────────────────────────
#  Application Entry Point
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = MudLogDesktopApp()
    app.mainloop()
