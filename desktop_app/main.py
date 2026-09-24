"""
MudLog Desktop — Petrophysical Multi-Track Well Logging Software
================================================================
Classic Desktop Engineering & Spreadsheet Suite (Excel / WinLog / Retro CAD Style)
Created By Mohammad Azka Khairur Rahman

Features:
  - Classic Menubar, Formula Bar, Toolbar, and Multi-Tab Workspaces
  - Interactive Multi-Track Depth Log with Fluid Facies Zones
  - Excel-style Tabular Spreadsheet with Cell Inspection & Sorting
  - Real-time Petrophysical Formula & Indicator Manager
  - Column & Track Display Configuration Manager
  - Data Ingestion (CSV, TXT, Excel) & High-Resolution Export (CSV, PNG, PDF)
  - Synthetic Payzone Well Generator
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
    # Handle direct directory executions
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, current_dir)
    sys.path.insert(0, parent_dir)
    from engine import compute_all, eval_expr, DEFAULT_FORMULAS, DEFAULT_THRESHOLDS
    from parser import parse_mudlog_file


# ──────────────────────────────────────────────────────────────────────────────
#  Theme / Color Constants (Classic Windows / Office / Excel Aesthetic)
# ──────────────────────────────────────────────────────────────────────────────
APP_TITLE = "MudLog Pro — Multi-Track Well Logging & Petrophysical Analysis"
APP_VERSION = "2.4.0 Classic Edition"
APP_AUTHOR = "Created By Mohammad Azka Khairur Rahman"

# Classic Retro Windows / Excel 2003 Palette
COLOR_WIN_BG       = "#ECE9D8"   # Classic Windows XP/2000 System Gray
COLOR_PANEL_BG     = "#F0F0F0"   # Light Surface Gray
COLOR_BAR_BG       = "#E4E2D5"   # Toolbar Gray
COLOR_BORDER_DARK  = "#7A7A7A"   # Classic Inset Dark Border
COLOR_BORDER_LIGHT = "#FFFFFF"   # Classic Inset Light Border
COLOR_WHITE        = "#FFFFFF"
COLOR_BLACK        = "#000000"
COLOR_EXCEL_GREEN  = "#107C41"   # Excel Brand Green
COLOR_NAVY         = "#003366"   # Formal Classic Navy Blue
COLOR_TEXT_MAIN    = "#111111"
COLOR_TEXT_MUTED   = "#555555"

# Facies Colors
COLOR_GAS_ZONE     = "#FFD2D2"   # Soft Red / Pink for Gas
COLOR_OIL_ZONE     = "#D2F4D2"   # Soft Green for Oil
COLOR_GAS_BORDER   = "#D9383A"
COLOR_OIL_BORDER   = "#2E7D32"
COLOR_DRY_ZONE     = "#EFEFEF"   # Gray for Non-bearing

# Default Track Schema
DEFAULT_TRACK_SCHEMA = [
    {"id": "C1",           "key": "C1",           "name": "C1 (Methane)", "unit": "ppm",   "color": "#008000", "scale": "linear", "visible": True},
    {"id": "C2",           "key": "C2",           "name": "C2 (Ethane)",  "unit": "ppm",   "color": "#008000", "scale": "linear", "visible": True},
    {"id": "C3",           "key": "C3",           "name": "C3 (Propane)", "unit": "ppm",   "color": "#008000", "scale": "linear", "visible": True},
    {"id": "IC4",          "key": "IC4",          "name": "iC4 (Isobut)", "unit": "ppm",   "color": "#008000", "scale": "linear", "visible": True},
    {"id": "NC4",          "key": "NC4",          "name": "nC4 (Norbut)", "unit": "ppm",   "color": "#008000", "scale": "linear", "visible": True},
    {"id": "IC5",          "key": "IC5",          "name": "iC5 (Isopen)", "unit": "ppm",   "color": "#008000", "scale": "linear", "visible": True},
    {"id": "NC5",          "key": "NC5",          "name": "nC5 (Norpen)", "unit": "ppm",   "color": "#008000", "scale": "linear", "visible": True},
    {"id": "TG",           "key": "TG_USED",      "name": "TG (Total Gas)","unit": "ppm",  "color": "#006400", "scale": "linear", "visible": True},
    {"id": "R1_C1_C2",     "key": "R1_C1_C2",     "name": "Pixler R1",    "unit": "ratio", "color": "#000080", "scale": "linear", "visible": True},
    {"id": "R2_C1_C3",     "key": "R2_C1_C3",     "name": "Pixler R2",    "unit": "ratio", "color": "#000080", "scale": "linear", "visible": True},
    {"id": "R3_C3_C1",     "key": "R3_C3_C1",     "name": "Pixler R3",    "unit": "ratio", "color": "#000080", "scale": "linear", "visible": True},
    {"id": "R4_C2_C1",     "key": "R4_C2_C1",     "name": "Pixler R4",    "unit": "ratio", "color": "#000080", "scale": "linear", "visible": True},
    {"id": "WH",           "key": "WH",           "name": "Wh (Wetness)", "unit": "%",     "color": "#0000CD", "scale": "linear", "visible": True},
    {"id": "BH",           "key": "BH",           "name": "Bh (Balance)", "unit": "ratio", "color": "#0000CD", "scale": "linear", "visible": True},
    {"id": "CH",           "key": "CH",           "name": "Ch (Character)","unit":"ratio", "color": "#0000CD", "scale": "linear", "visible": True},
    {"id": "DRYNESS",      "key": "DRYNESS",      "name": "Dryness (DR)", "unit": "ratio", "color": "#8B4513", "scale": "linear", "visible": True},
    {"id": "GOW_NOTG",     "key": "GOW_NOTG",     "name": "GOW/TG",       "unit": "ratio", "color": "#B8860B", "scale": "linear", "visible": True},
    {"id": "WBS",          "key": "WBS",          "name": "WBS Score",    "unit": "score", "color": "#B8860B", "scale": "linear", "visible": True},
]


def generate_synthetic_mudlog():
    """Generates a realistic synthetic mudlog dataset with gas and oil payzones."""
    np.random.seed(42)
    rows = []
    depth = 1800.0
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
    df_raw = pd.DataFrame(rows)
    return df_raw


# ──────────────────────────────────────────────────────────────────────────────
#  Main Application Window Class
# ──────────────────────────────────────────────────────────────────────────────
class MudLogDesktopApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_TITLE} [{APP_VERSION}]")
        self.geometry("1240x800")
        self.minsize(980, 620)
        
        # State Data
        self.current_file_path = "Synthetic Demo Well [GWD-01]"
        self.raw_df = generate_synthetic_mudlog()
        self.formulas = {k: v["expr"] for k, v in DEFAULT_FORMULAS.items()}
        self.thresholds = dict(DEFAULT_THRESHOLDS)
        self.schema = [dict(s) for s in DEFAULT_TRACK_SCHEMA]
        self.percentile_cutoff = 75.0
        self.computed_df = compute_all(self.raw_df, formula_overrides=self.formulas, threshold_overrides=self.thresholds)

        # UI Setup
        self._setup_styles()
        self._create_menubar()
        self._create_toolbar()
        self._create_formula_bar()
        self._create_main_content()
        self._create_statusbar()

        # Render initial data
        self._refresh_all_views()

    def _setup_styles(self):
        """Configure ttk styles for formal Excel / retro software look."""
        self.configure(bg=COLOR_WIN_BG)
        style = ttk.Style(self)
        try:
            style.theme_use("winnative")
        except tk.TclError:
            try:
                style.theme_use("classic")
            except tk.TclError:
                pass

        # Notebook (Excel Sheet tabs style)
        style.configure("TNotebook", background=COLOR_WIN_BG, borderwidth=1)
        style.configure("TNotebook.Tab", background=COLOR_WIN_BG, padding=[12, 4], font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", COLOR_WHITE), ("active", "#F8F8F8")],
                  foreground=[("selected", COLOR_NAVY), ("active", "#000000")])

        # Treeview (Spreadsheet Grid Style)
        style.configure("Treeview",
                        background=COLOR_WHITE,
                        foreground=COLOR_TEXT_MAIN,
                        rowheight=22,
                        fieldbackground=COLOR_WHITE,
                        font=("Segoe UI", 9))
        style.configure("Treeview.Heading",
                        background=COLOR_BAR_BG,
                        foreground=COLOR_TEXT_MAIN,
                        font=("Segoe UI", 9, "bold"),
                        relief="raised")
        style.map("Treeview.Heading", background=[("active", "#D5D2C4")])

    def _create_menubar(self):
        """Creates formal desktop application menu bar."""
        menubar = tk.Menu(self, bg=COLOR_PANEL_BG, fg=COLOR_BLACK, relief="raised", bd=1)

        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Mudlog Data File... (CSV, TXT, Excel)", accelerator="Ctrl+O", command=self.open_file_dialog)
        file_menu.add_command(label="Load Synthetic Demo Payzone Well", accelerator="Ctrl+N", command=self.load_demo_data)
        file_menu.add_separator()
        file_menu.add_command(label="Export Calculated Log Table (CSV)...", accelerator="Ctrl+S", command=self.export_csv_dialog)
        file_menu.add_command(label="Export High-Res Multi-Track Plot (PNG/PDF)...", accelerator="Ctrl+P", command=self.export_plot_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", accelerator="Alt+F4", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Edit Menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Edit Petrophysical Formulas & Indicators...", accelerator="F2", command=self.open_formula_manager_dialog)
        edit_menu.add_command(label="Configure Columns & Tracks Display...", accelerator="F3", command=self.open_column_manager_dialog)
        edit_menu.add_separator()
        edit_menu.add_command(label="Reset to Skripsi Default Parameters", command=self.reset_defaults)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        # View Menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Switch to Multi-Track Depth Log", accelerator="F5", command=lambda: self.notebook.select(0))
        view_menu.add_command(label="Switch to Spreadsheet Data Table", accelerator="F6", command=lambda: self.notebook.select(1))
        view_menu.add_command(label="Switch to Fluid Facies Statistics", accelerator="F7", command=lambda: self.notebook.select(2))
        view_menu.add_separator()
        
        # Percentile sub-menu
        p_menu = tk.Menu(view_menu, tearoff=0)
        p_menu.add_radiobutton(label="Top 25% (P75 Cutoff - Recommended)", value=75, command=lambda: self.set_percentile_cutoff(75))
        p_menu.add_radiobutton(label="Top 10% (P90 Cutoff - Strong Shows)", value=90, command=lambda: self.set_percentile_cutoff(90))
        p_menu.add_radiobutton(label="Top 50% (P50 Cutoff - Median)", value=50, command=lambda: self.set_percentile_cutoff(50))
        p_menu.add_radiobutton(label="All Data Points (0% Cutoff)", value=0, command=lambda: self.set_percentile_cutoff(0))
        view_menu.add_cascade(label="Plot Peak Filter Cutoff", menu=p_menu)
        menubar.add_cascade(label="View", menu=view_menu)

        # Calculations Menu
        calc_menu = tk.Menu(menubar, tearoff=0)
        calc_menu.add_command(label="Recompute All Indicators & Fluid Facies", accelerator="F9", command=self.recompute_data)
        calc_menu.add_command(label="Recalculate Summary Statistics", command=self._refresh_statistics_view)
        menubar.add_cascade(label="Calculations", menu=calc_menu)

        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Petrophysical Ratios Reference Manual", command=self.show_formulas_help)
        help_menu.add_separator()
        help_menu.add_command(label="About MudLog Desktop...", accelerator="F1", command=self.show_about_dialog)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

        # Keyboard shortcuts
        self.bind("<Control-o>", lambda e: self.open_file_dialog())
        self.bind("<Control-n>", lambda e: self.load_demo_data())
        self.bind("<Control-s>", lambda e: self.export_csv_dialog())
        self.bind("<Control-p>", lambda e: self.export_plot_dialog())
        self.bind("<F2>", lambda e: self.open_formula_manager_dialog())
        self.bind("<F3>", lambda e: self.open_column_manager_dialog())
        self.bind("<F5>", lambda e: self.notebook.select(0))
        self.bind("<F6>", lambda e: self.notebook.select(1))
        self.bind("<F7>", lambda e: self.notebook.select(2))
        self.bind("<F9>", lambda e: self.recompute_data())
        self.bind("<F1>", lambda e: self.show_about_dialog())

    def _create_toolbar(self):
        """Creates classic retro beveled toolbar."""
        toolbar_frame = tk.Frame(self, bg=COLOR_BAR_BG, relief="raised", bd=2)
        toolbar_frame.pack(side=tk.TOP, fill=tk.X)

        # Toolbar button helper
        def make_tool_btn(parent, text, icon, cmd, tooltip=None):
            btn = tk.Button(parent, text=f"{icon} {text}", font=("Segoe UI", 8, "bold"),
                            bg=COLOR_WIN_BG, fg=COLOR_BLACK, relief="raised", bd=1,
                            padx=6, pady=2, cursor="hand2", command=cmd)
            btn.pack(side=tk.LEFT, padx=2, pady=3)
            return btn

        make_tool_btn(toolbar_frame, "Open File", "📂", self.open_file_dialog)
        make_tool_btn(toolbar_frame, "Export CSV", "💾", self.export_csv_dialog)
        make_tool_btn(toolbar_frame, "Export Chart", "📊", self.export_plot_dialog)

        sep1 = tk.Frame(toolbar_frame, width=2, bg=COLOR_BORDER_DARK, relief="sunken", bd=1)
        sep1.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=4)

        make_tool_btn(toolbar_frame, "Edit Formulas", "🧮", self.open_formula_manager_dialog)
        make_tool_btn(toolbar_frame, "Tracks & Cols", "📐", self.open_column_manager_dialog)
        make_tool_btn(toolbar_frame, "Recompute", "⚡", self.recompute_data)

        sep2 = tk.Frame(toolbar_frame, width=2, bg=COLOR_BORDER_DARK, relief="sunken", bd=1)
        sep2.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=4)

        # Percentile dropdown in toolbar
        lbl_p = tk.Label(toolbar_frame, text="Filter Cutoff:", font=("Segoe UI", 8), bg=COLOR_BAR_BG)
        lbl_p.pack(side=tk.LEFT, padx=(4, 2))

        self.p_var = tk.StringVar(value="P75 (Top 25%)")
        p_combo = ttk.Combobox(toolbar_frame, textvariable=self.p_var, values=["P75 (Top 25%)", "P90 (Top 10%)", "P50 (Top 50%)", "P0 (All Data)"], width=14, state="readonly")
        p_combo.pack(side=tk.LEFT, padx=2)
        p_combo.bind("<<ComboboxSelected>>", self._on_combo_percentile)

        sep3 = tk.Frame(toolbar_frame, width=2, bg=COLOR_BORDER_DARK, relief="sunken", bd=1)
        sep3.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=4)

        make_tool_btn(toolbar_frame, "Demo Well", "🔄", self.load_demo_data)
        make_tool_btn(toolbar_frame, "About", "ℹ️", self.show_about_dialog)

    def _create_formula_bar(self):
        """Creates an Excel / Google Docs style Formula & Depth Inspector Bar."""
        fx_frame = tk.Frame(self, bg=COLOR_PANEL_BG, relief="groove", bd=1, padx=4, pady=3)
        fx_frame.pack(side=tk.TOP, fill=tk.X)

        # Depth Cell Box
        lbl_box = tk.Label(fx_frame, text="WELL DEPTH:", font=("Segoe UI", 8, "bold"), bg=COLOR_PANEL_BG, fg=COLOR_NAVY)
        lbl_box.pack(side=tk.LEFT, padx=(2, 4))

        self.depth_entry_var = tk.StringVar(value="1815.0 m")
        depth_box = tk.Entry(fx_frame, textvariable=self.depth_entry_var, font=("Consolas", 9, "bold"), width=12,
                             bg=COLOR_WHITE, fg=COLOR_BLACK, relief="sunken", bd=1, justify="center")
        depth_box.pack(side=tk.LEFT, padx=2)

        # 'fx' symbol button
        btn_fx = tk.Label(fx_frame, text=" fx ", font=("Georgia", 10, "bold", "italic"), bg=COLOR_BAR_BG, fg="#880000",
                          relief="raised", bd=1, cursor="hand2")
        btn_fx.pack(side=tk.LEFT, padx=4)
        btn_fx.bind("<Button-1>", lambda e: self.open_formula_manager_dialog())

        # Formula text display
        self.formula_bar_var = tk.StringVar(value="WH = ((C2 + C3 + IC4 + NC4 + IC5 + NC5) / TG) * 100.0   |   BH = (C1 + C2) / (C3 + IC4 + NC4 + IC5 + NC5)")
        fx_entry = tk.Entry(fx_frame, textvariable=self.formula_bar_var, font=("Consolas", 9),
                            bg=COLOR_WHITE, fg=COLOR_BLACK, relief="sunken", bd=1)
        fx_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

        # Fluid Zone Badge in Formula Bar
        self.facies_badge_label = tk.Label(fx_frame, text=" ZONE: READY ", font=("Segoe UI", 8, "bold"),
                                           bg=COLOR_EXCEL_GREEN, fg=COLOR_WHITE, relief="solid", bd=1, padx=6)
        self.facies_badge_label.pack(side=tk.RIGHT, padx=4)

    def _create_main_content(self):
        """Creates the main tabbed workspace notebook."""
        main_container = tk.Frame(self, bg=COLOR_WIN_BG, padx=4, pady=4)
        main_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Multi-Track Depth Log
        self.tab_log = tk.Frame(self.notebook, bg=COLOR_WHITE)
        self.notebook.add(self.tab_log, text=" 📈 Multi-Track Depth Log ")

        # Tab 2: Spreadsheet Data Table (Excel View)
        self.tab_table = tk.Frame(self.notebook, bg=COLOR_WHITE)
        self.notebook.add(self.tab_table, text=" 📊 Spreadsheet Data (Excel View) ")

        # Tab 3: Fluid Facies Statistics & Payzones
        self.tab_stats = tk.Frame(self.notebook, bg=COLOR_PANEL_BG)
        self.notebook.add(self.tab_stats, text=" 📋 Fluid Facies & Petrophysical Summary ")

        # Tab 4: Formula & Indicator Inspector
        self.tab_formulas = tk.Frame(self.notebook, bg=COLOR_PANEL_BG)
        self.notebook.add(self.tab_formulas, text=" 🧮 Petrophysical Formula Inspector ")

        # Build subviews
        self._build_log_view()
        self._build_table_view()
        self._build_stats_view()
        self._build_formulas_view()

    def _create_statusbar(self):
        """Creates classic multi-pane sunken status bar with creator attribution."""
        status_frame = tk.Frame(self, bg=COLOR_BAR_BG, relief="groove", bd=1)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        def make_pane(parent, width, side=tk.LEFT):
            pane = tk.Label(parent, font=("Segoe UI", 8), bg=COLOR_BAR_BG, fg=COLOR_BLACK,
                            relief="sunken", bd=1, anchor="w", padx=6, pady=2, width=width)
            pane.pack(side=side, padx=1, pady=1, fill=tk.X if width is None else tk.NONE, expand=(width is None))
            return pane

        self.status_msg = make_pane(status_frame, None, side=tk.LEFT)
        self.status_depth = make_pane(status_frame, 32, side=tk.LEFT)
        self.status_tracks = make_pane(status_frame, 18, side=tk.LEFT)
        self.status_facies = make_pane(status_frame, 30, side=tk.LEFT)
        
        # Creator Attribution Pane (Rightmost, classic formal bold)
        self.status_author = tk.Label(status_frame, text=f" {APP_AUTHOR} ", font=("Segoe UI", 8, "bold"),
                                      bg="#DCD8C8", fg=COLOR_NAVY, relief="sunken", bd=1, padx=8, pady=2)
        self.status_author.pack(side=tk.RIGHT, padx=1, pady=1)

        self._update_status("Application ready. Synthetic demo well loaded.")

    def _update_status(self, msg):
        """Updates status bar panels."""
        self.status_msg.config(text=f"Ready: {msg}")
        if self.computed_df is not None and not self.computed_df.empty:
            d_min = self.computed_df["DEPTH"].min()
            d_max = self.computed_df["DEPTH"].max()
            n_pts = len(self.computed_df)
            self.status_depth.config(text=f"Depth: {d_min:.1f}m - {d_max:.1f}m ({n_pts} rows)")
            
            n_active = sum(1 for s in self.schema if s.get("visible", True))
            self.status_tracks.config(text=f"Active Tracks: {n_active}")

            if "ZONE" in self.computed_df.columns:
                z_counts = self.computed_df["ZONE"].value_counts().to_dict()
                gas_cnt = z_counts.get("Gas", 0)
                oil_cnt = z_counts.get("Oil", 0)
                dry_cnt = z_counts.get("Non-Bearing", 0)
                self.status_facies.config(text=f"Gas: {gas_cnt} | Oil: {oil_cnt} | Non-Bearing: {dry_cnt}")

    # ──────────────────────────────────────────────────────────────────────────
    #  Tab 1: Multi-Track Depth Log Builder
    # ──────────────────────────────────────────────────────────────────────────
    def _build_log_view(self):
        """Builds the continuous multi-track log view using embedded Matplotlib figure."""
        self.log_container = tk.Frame(self.tab_log, bg=COLOR_WHITE)
        self.log_container.pack(fill=tk.BOTH, expand=True)

        # Plot Canvas Placeholder
        self.fig = plt.Figure(figsize=(12, 7), dpi=100, facecolor="#F8F9FA")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.log_container)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Classic Matplotlib Toolbar
        self.mpl_toolbar_frame = tk.Frame(self.log_container, bg=COLOR_BAR_BG, relief="groove", bd=1)
        self.mpl_toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.mpl_toolbar = NavigationToolbar2Tk(self.canvas, self.mpl_toolbar_frame)
        self.mpl_toolbar.config(background=COLOR_BAR_BG)
        self.mpl_toolbar.update()

        # Connect hover / mouse motion event for dynamic depth crosshair
        self.canvas.mpl_connect("motion_notify_event", self._on_log_hover)

    def _render_multi_track_plot(self):
        """Renders the petrophysical multi-track log."""
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

        # Total subplots = Active Tracks + 1 Facies Zone Track
        n_tracks = len(active_schema)
        n_cols = n_tracks + 1  # Last column is Facies Zone Track
        width_ratios = [1.0] * n_tracks + [0.7]

        axes = self.fig.subplots(1, n_cols, sharey=True, gridspec_kw={"width_ratios": width_ratios, "wspace": 0.05})
        if n_cols == 1:
            axes = [axes]

        self.track_axes = axes

        # Invert Y-axis for depth logging (shallower at top, deeper at bottom)
        axes[0].set_ylim(d_max, d_min)
        axes[0].set_ylabel("DEPTH (m)", fontsize=9, fontweight="bold", color=COLOR_NAVY)

        # Plot each active track
        for idx, track in enumerate(active_schema):
            ax = axes[idx]
            col_key = track["key"]
            track_name = track["name"]
            unit = track["unit"]
            color = track.get("color", "#008000")

            if col_key in df.columns:
                raw_y = pd.to_numeric(df[col_key], errors="coerce").fillna(0.0).values
                
                # Apply percentile cutoff baseline if positive
                if self.percentile_cutoff > 0 and len(raw_y) > 0 and raw_y.max() > 0:
                    cutoff_val = np.percentile(raw_y[raw_y > 0], self.percentile_cutoff) if np.any(raw_y > 0) else 0.0
                    y_vals = np.where(raw_y >= cutoff_val, raw_y, 0.0)
                else:
                    y_vals = raw_y

                # Plot Curve
                ax.plot(y_vals, depth, color=color, linewidth=1.2, label=track_name)
                # Fill curve area for visual punch
                ax.fill_betweenx(depth, 0, y_vals, color=color, alpha=0.18)

                # Track scale limits
                val_max = np.nanmax(y_vals) if len(y_vals) > 0 else 1.0
                if val_max <= 0:
                    val_max = 1.0
                ax.set_xlim(0, val_max * 1.15)
            else:
                ax.set_xlim(0, 1)

            # Classic Engineering Grid and Header styling
            ax.set_title(f"{track_name}\n({unit})", fontsize=7.5, fontweight="bold", pad=4, color="#111111")
            ax.grid(True, which="both", color="#D0D0D0", linestyle="--", linewidth=0.5)
            ax.tick_params(axis="x", labelsize=6.5, rotation=45)
            ax.tick_params(axis="y", labelsize=7)
            ax.set_facecolor("#FFFFFF")

            # Remove inner y-axis labels
            if idx > 0:
                ax.tick_params(axis="y", labelleft=False)

        # Last column: Fluid Facies Zone Color Overlay Track
        ax_zone = axes[-1]
        ax_zone.set_title("FLUID\nFACIES", fontsize=7.5, fontweight="bold", pad=4, color=COLOR_NAVY)
        ax_zone.set_xlim(0, 1)
        ax_zone.set_xticks([])
        ax_zone.tick_params(axis="y", labelleft=False)
        ax_zone.set_facecolor("#FAFAFA")

        if "ZONE" in df.columns:
            zones = df["ZONE"].values
            n = len(df)
            for i in range(n):
                z = zones[i]
                d = depth[i]
                # Calculate interval slice
                half_step = 7.5
                if i > 0 and i < n - 1:
                    half_step = (depth[i+1] - depth[i-1]) / 4.0
                d_top = d - half_step
                d_bot = d + half_step

                if z == "Gas":
                    rect = mpatches.Rectangle((0, d_top), 1, d_bot - d_top, color="#F43F5E", alpha=0.85)
                    ax_zone.add_patch(rect)
                elif z == "Oil":
                    rect = mpatches.Rectangle((0, d_top), 1, d_bot - d_top, color="#10B981", alpha=0.85)
                    ax_zone.add_patch(rect)
                else:
                    rect = mpatches.Rectangle((0, d_top), 1, d_bot - d_top, color="#CBD5E1", alpha=0.35)
                    ax_zone.add_patch(rect)

        try:
            self.fig.subplots_adjust(top=0.91, bottom=0.08, left=0.06, right=0.98, wspace=0.08)
        except Exception:
            pass
        self.canvas.draw()

    def _on_log_hover(self, event):
        """Updates crosshair, depth box, and formula status on hover."""
        if event.inaxes is not None and event.ydata is not None:
            depth_val = float(event.ydata)
            self.depth_entry_var.set(f"{depth_val:.1f} m")
            
            if self.computed_df is not None and not self.computed_df.empty:
                df = self.computed_df
                # Find nearest depth row
                idx = (df["DEPTH"] - depth_val).abs().idxmin()
                row = df.loc[idx]
                zone = row.get("ZONE", "Unknown")
                c1 = row.get("C1", 0.0)
                tg = row.get("TG_USED", row.get("TG", 0.0))
                wh = row.get("WH", 0.0)

                # Update facies badge
                if zone == "Gas":
                    self.facies_badge_label.config(text=" 🔴 GAS PAYZONE ", bg="#D9383A", fg=COLOR_WHITE)
                elif zone == "Oil":
                    self.facies_badge_label.config(text=" 🟢 OIL PAYZONE ", bg="#2E7D32", fg=COLOR_WHITE)
                else:
                    self.facies_badge_label.config(text=" ⚪ NON-BEARING ", bg="#777777", fg=COLOR_WHITE)

                self.formula_bar_var.set(f"Depth: {row['DEPTH']:.1f}m | C1: {c1:.1f} ppm | TG: {tg:.1f} ppm | Wh: {wh:.1f}% | Facies: {zone}")

    # ──────────────────────────────────────────────────────────────────────────
    #  Tab 2: Spreadsheet Data Table (Excel View)
    # ──────────────────────────────────────────────────────────────────────────
    def _build_table_view(self):
        """Builds Excel-styled full tabular grid view."""
        table_container = tk.Frame(self.tab_table, bg=COLOR_WHITE)
        table_container.pack(fill=tk.BOTH, expand=True)

        # Excel-like Table Controls
        ctrl_bar = tk.Frame(table_container, bg=COLOR_BAR_BG, relief="groove", bd=1, padx=4, pady=3)
        ctrl_bar.pack(side=tk.TOP, fill=tk.X)

        tk.Label(ctrl_bar, text="Filter by Zone:", font=("Segoe UI", 8, "bold"), bg=COLOR_BAR_BG).pack(side=tk.LEFT, padx=4)
        self.table_filter_var = tk.StringVar(value="All Zones")
        filter_combo = ttk.Combobox(ctrl_bar, textvariable=self.table_filter_var, values=["All Zones", "Gas Only", "Oil Only", "Payzones Only (Gas + Oil)", "Non-Bearing Only"], width=22, state="readonly")
        filter_combo.pack(side=tk.LEFT, padx=4)
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self._populate_spreadsheet_table())

        btn_copy = tk.Button(ctrl_bar, text="📋 Copy Selection", font=("Segoe UI", 8), bg=COLOR_WIN_BG, relief="raised", bd=1, command=self._copy_table_selection)
        btn_copy.pack(side=tk.RIGHT, padx=4)

        # Treeview Spreadsheet Grid
        tree_frame = tk.Frame(table_container, bg=COLOR_WHITE)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)

        self.tree = ttk.Treeview(tree_frame, yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set, selectmode="extended")
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Setup Tag Colors for Facies
        self.tree.tag_configure("gas_row", background=COLOR_GAS_ZONE)
        self.tree.tag_configure("oil_row", background=COLOR_OIL_ZONE)
        self.tree.tag_configure("even_row", background="#F9FBFD")
        self.tree.tag_configure("odd_row", background=COLOR_WHITE)

        self.tree.bind("<ButtonRelease-1>", self._on_table_row_click)

    def _populate_spreadsheet_table(self):
        """Populates Treeview with current computed dataset."""
        # Clear existing items
        self.tree.delete(*self.tree.get_children())
        if self.computed_df is None or self.computed_df.empty:
            return

        df = self.computed_df.copy()

        # Apply Table Filter
        filter_mode = self.table_filter_var.get()
        if filter_mode == "Gas Only":
            df = df[df["ZONE"] == "Gas"]
        elif filter_mode == "Oil Only":
            df = df[df["ZONE"] == "Oil"]
        elif filter_mode == "Payzones Only (Gas + Oil)":
            df = df[df["ZONE"].isin(["Gas", "Oil"])]
        elif filter_mode == "Non-Bearing Only":
            df = df[df["ZONE"] == "Non-Bearing"]

        # Define columns
        cols = list(df.columns)
        self.tree["columns"] = ["ROW_NUM"] + cols
        self.tree["show"] = "headings"

        # Row Number Header (Excel Style 1, 2, 3...)
        self.tree.heading("ROW_NUM", text="#", anchor="center")
        self.tree.column("ROW_NUM", width=45, anchor="center", stretch=False)

        for col in cols:
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, width=80, anchor="e" if col != "ZONE" else "center")

        # Insert Rows
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
        """Selects a row and updates formula inspector."""
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            vals = item["values"]
            if vals and len(vals) > 1:
                depth = vals[1]
                zone = vals[-1] if "ZONE" in self.computed_df.columns else ""
                self.depth_entry_var.set(f"{depth} m")
                self.formula_bar_var.set(f"Row {vals[0]}: Depth {depth}m | Values: {vals[2:7]} | Facies: {zone}")

    def _copy_table_selection(self):
        """Copies selected rows to clipboard in tab-delimited Excel format."""
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
    #  Tab 3: Fluid Facies & Petrophysical Summary
    # ──────────────────────────────────────────────────────────────────────────
    def _build_stats_view(self):
        """Builds statistical dashboard breakdown."""
        self.stats_container = tk.Frame(self.tab_stats, bg=COLOR_PANEL_BG, padx=20, pady=20)
        self.stats_container.pack(fill=tk.BOTH, expand=True)

    def _refresh_statistics_view(self):
        """Refreshes summary statistics cards and tables."""
        for widget in self.stats_container.winfo_children():
            widget.destroy()

        if self.computed_df is None or self.computed_df.empty:
            tk.Label(self.stats_container, text="No dataset available.", bg=COLOR_PANEL_BG).pack()
            return

        df = self.computed_df
        d_min = df["DEPTH"].min()
        d_max = df["DEPTH"].max()
        n_pts = len(df)
        span = d_max - d_min

        # Header Title
        lbl_title = tk.Label(self.stats_container, text="Petrophysical Well Summary & Fluid Facies Breakdown",
                             font=("Segoe UI", 12, "bold"), bg=COLOR_PANEL_BG, fg=COLOR_NAVY)
        lbl_title.pack(anchor="w", pady=(0, 10))

        # 3 Top KPI Cards Frame
        kpi_frame = tk.Frame(self.stats_container, bg=COLOR_PANEL_BG)
        kpi_frame.pack(fill=tk.X, pady=(0, 15))

        def make_kpi(parent, title, val, subtext, color):
            card = tk.Frame(parent, bg=COLOR_WHITE, relief="groove", bd=2, padx=14, pady=10)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
            tk.Label(card, text=title, font=("Segoe UI", 8, "bold"), fg=COLOR_TEXT_MUTED, bg=COLOR_WHITE).pack(anchor="w")
            tk.Label(card, text=val, font=("Segoe UI", 16, "bold"), fg=color, bg=COLOR_WHITE).pack(anchor="w", pady=2)
            tk.Label(card, text=subtext, font=("Segoe UI", 8), fg=COLOR_TEXT_MUTED, bg=COLOR_WHITE).pack(anchor="w")

        z_counts = df["ZONE"].value_counts().to_dict() if "ZONE" in df.columns else {}
        gas_cnt = z_counts.get("Gas", 0)
        oil_cnt = z_counts.get("Oil", 0)
        dry_cnt = z_counts.get("Non-Bearing", 0)

        gas_pct = (gas_cnt / n_pts) * 100.0 if n_pts > 0 else 0
        oil_pct = (oil_cnt / n_pts) * 100.0 if n_pts > 0 else 0
        pay_cnt = gas_cnt + oil_cnt
        pay_pct = (pay_cnt / n_pts) * 100.0 if n_pts > 0 else 0

        make_kpi(kpi_frame, "TOTAL DEPTH INTERVAL", f"{span:.0f} m", f"{d_min:.1f}m - {d_max:.1f}m ({n_pts} samples)", COLOR_NAVY)
        make_kpi(kpi_frame, "IDENTIFIED GAS PAYZONES", f"{gas_cnt} Intervals", f"{gas_pct:.1f}% of Well Section", "#D9383A")
        make_kpi(kpi_frame, "IDENTIFIED OIL PAYZONES", f"{oil_cnt} Intervals", f"{oil_pct:.1f}% of Well Section", "#2E7D32")
        make_kpi(kpi_frame, "NET HYDROCARBON PAY", f"{pay_pct:.1f}% Net/Gross", f"{pay_cnt} Net Pay Samples", COLOR_EXCEL_GREEN)

        # Table of Summary Metrics
        summary_table_frame = tk.LabelFrame(self.stats_container, text=" Gas Components & Ratio Statistics ", font=("Segoe UI", 9, "bold"),
                                            bg=COLOR_PANEL_BG, relief="groove", bd=2, padx=10, pady=10)
        summary_table_frame.pack(fill=tk.BOTH, expand=True)

        cols_to_sum = [c for c in ["C1", "C2", "C3", "IC4", "NC4", "IC5", "NC5", "TG_USED", "WH", "BH", "CH", "DRYNESS", "R1_C1_C2"] if c in df.columns]
        stat_df = df[cols_to_sum].describe().T.reset_index()
        stat_df.rename(columns={"index": "Parameter", "mean": "Mean", "std": "StdDev", "min": "Min", "50%": "Median (P50)", "max": "Max"}, inplace=True)

        stat_tree = ttk.Treeview(summary_table_frame, columns=list(stat_df.columns), show="headings", height=8)
        for col in stat_df.columns:
            stat_tree.heading(col, text=col)
            stat_tree.column(col, width=100, anchor="e" if col != "Parameter" else "w")

        for _, row in stat_df.iterrows():
            vals = [row["Parameter"]] + [f"{float(v):.2f}" if isinstance(v, (int, float)) else str(v) for v in row[1:]]
            stat_tree.insert("", tk.END, values=vals)

        stat_tree.pack(fill=tk.BOTH, expand=True)

    # ──────────────────────────────────────────────────────────────────────────
    #  Tab 4: Formula & Indicator Inspector
    # ──────────────────────────────────────────────────────────────────────────
    def _build_formulas_view(self):
        """Builds the in-tab formula viewer and quick-edit workspace."""
        frame = tk.Frame(self.tab_formulas, bg=COLOR_PANEL_BG, padx=16, pady=16)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Active Petrophysical Formulas (Deterministic Chapter 3 Engine)",
                 font=("Segoe UI", 11, "bold"), bg=COLOR_PANEL_BG, fg=COLOR_NAVY).pack(anchor="w", pady=(0, 8))

        txt_frame = tk.Frame(frame, bg=COLOR_WHITE, relief="sunken", bd=2)
        txt_frame.pack(fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(txt_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.formula_text = tk.Text(txt_frame, font=("Consolas", 10), bg=COLOR_WHITE, fg=COLOR_BLACK,
                                    yscrollcommand=scroll.set, wrap="none", padx=8, pady=8)
        self.formula_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self.formula_text.yview)

        btn_row = tk.Frame(frame, bg=COLOR_PANEL_BG, pady=8)
        btn_row.pack(fill=tk.X)

        tk.Button(btn_row, text="🧮 Open Interactive Formula Editor Modal", font=("Segoe UI", 9, "bold"),
                  bg=COLOR_WIN_BG, relief="raised", bd=2, padx=10, pady=4,
                  command=self.open_formula_manager_dialog).pack(side=tk.LEFT)

    def _refresh_formulas_text(self):
        """Refreshes the formula text display."""
        self.formula_text.delete("1.0", tk.END)
        lines = [
            "================================================================================",
            "  MUDLOG PRO — AUDITABLE PETROPHYSICAL FORMULA ENGINE DEFINITIONS",
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
    #  Actions & Dialogs
    # ──────────────────────────────────────────────────────────────────────────
    def _refresh_all_views(self):
        """Refreshes all tabs and UI components."""
        self._render_multi_track_plot()
        self._populate_spreadsheet_table()
        self._refresh_statistics_view()
        self._refresh_formulas_text()
        self._update_status(f"Dataset active: {self.current_file_path}")

    def recompute_data(self):
        """Recomputes petrophysical indicators with current formulas and thresholds."""
        try:
            self.computed_df = compute_all(self.raw_df, formula_overrides=self.formulas, threshold_overrides=self.thresholds)
            self._refresh_all_views()
            messagebox.showinfo("Computation Complete", "All 16 petrophysical indicators and fluid facies zones have been successfully recomputed.", parent=self)
        except Exception as e:
            messagebox.showerror("Computation Error", f"Error during recomputation:\n{str(e)}", parent=self)

    def set_percentile_cutoff(self, p):
        """Updates percentile peak filter and re-renders multi-track log."""
        self.percentile_cutoff = float(p)
        self._render_multi_track_plot()
        self._update_status(f"Filter cutoff updated to P{int(p)}%")

    def _on_combo_percentile(self, event):
        val = self.p_var.get()
        if "75" in val:
            self.set_percentile_cutoff(75)
        elif "90" in val:
            self.set_percentile_cutoff(90)
        elif "50" in val:
            self.set_percentile_cutoff(50)
        else:
            self.set_percentile_cutoff(0)

    def load_demo_data(self):
        """Loads synthetic demonstration well with known payzones."""
        self.current_file_path = "Synthetic Demo Well [GWD-01]"
        self.raw_df = generate_synthetic_mudlog()
        self.computed_df = compute_all(self.raw_df, formula_overrides=self.formulas, threshold_overrides=self.thresholds)
        self._refresh_all_views()
        self._update_status("Loaded synthetic demonstration well (85 intervals, 2 payzones).")

    def open_file_dialog(self):
        """Opens file dialog for CSV, TXT, Excel mudlog files."""
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
            
            self.current_file_path = os.path.basename(fpath)
            self.raw_df = df_parsed
            self.computed_df = compute_all(self.raw_df, formula_overrides=self.formulas, threshold_overrides=self.thresholds)
            self._refresh_all_views()
            messagebox.showinfo("File Loaded", f"Successfully loaded and computed mudlog dataset from:\n{fpath}\n({len(df_parsed)} intervals)", parent=self)
        except Exception as e:
            messagebox.showerror("File Ingestion Error", f"Failed to parse mudlog file:\n{str(e)}", parent=self)

    def export_csv_dialog(self):
        """Exports computed dataframe to CSV."""
        if self.computed_df is None or self.computed_df.empty:
            messagebox.showwarning("Export", "No computed data to export.", parent=self)
            return

        fpath = filedialog.asksaveasfilename(
            parent=self,
            title="Export Calculated Log Table to CSV",
            defaultextension=".csv",
            filetypes=[("CSV (Comma Delimited) (*.csv)", "*.csv"), ("All Files (*.*)", "*.*")]
        )
        if not fpath:
            return

        try:
            self.computed_df.to_csv(fpath, index=False)
            messagebox.showinfo("Export Successful", f"Calculated well log table exported successfully to:\n{fpath}", parent=self)
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export CSV:\n{str(e)}", parent=self)

    def export_plot_dialog(self):
        """Exports high resolution plot image."""
        fpath = filedialog.asksaveasfilename(
            parent=self,
            title="Export Multi-Track Well Log Chart",
            defaultextension=".png",
            filetypes=[("PNG Image (*.png)", "*.png"), ("PDF Vector Document (*.pdf)", "*.pdf"), ("JPEG Image (*.jpg)", "*.jpg")]
        )
        if not fpath:
            return

        try:
            self.fig.savefig(fpath, dpi=300, bbox_inches="tight")
            messagebox.showinfo("Chart Exported", f"Multi-track plot successfully exported to:\n{fpath}", parent=self)
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export plot image:\n{str(e)}", parent=self)

    def reset_defaults(self):
        """Resets all formulas and track columns to Skripsi defaults."""
        if messagebox.askyesno("Reset Defaults", "Restore all petrophysical formulas and column track schemas to thesis defaults?", parent=self):
            self.formulas = {k: v["expr"] for k, v in DEFAULT_FORMULAS.items()}
            self.thresholds = dict(DEFAULT_THRESHOLDS)
            self.schema = [dict(s) for s in DEFAULT_TRACK_SCHEMA]
            self.computed_df = compute_all(self.raw_df, formula_overrides=self.formulas, threshold_overrides=self.thresholds)
            self._refresh_all_views()
            messagebox.showinfo("Reset", "Defaults successfully restored.", parent=self)

    # ──────────────────────────────────────────────────────────────────────────
    #  Modal Dialog: Formula & Indicator Manager
    # ──────────────────────────────────────────────────────────────────────────
    def open_formula_manager_dialog(self):
        """Opens interactive petrophysical formula manager modal."""
        dlg = tk.Toplevel(self)
        dlg.title("Petrophysical Formula & Indicator Manager")
        dlg.geometry("760x540")
        dlg.transient(self)
        dlg.grab_set()
        dlg.configure(bg=COLOR_WIN_BG)

        # Header
        hdr = tk.Frame(dlg, bg=COLOR_NAVY, padx=12, pady=10)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="🧮 Custom Petrophysical Formula & Indicator Manager",
                 font=("Segoe UI", 11, "bold"), fg=COLOR_WHITE, bg=COLOR_NAVY).pack(anchor="w")
        tk.Label(hdr, text="Edit math expressions for ratios. Variables: C1, C2, C3, IC4, NC4, IC5, NC5, TG",
                 font=("Segoe UI", 8), fg="#D0D0D0", bg=COLOR_NAVY).pack(anchor="w")

        body = tk.Frame(dlg, bg=COLOR_WIN_BG, padx=12, pady=12)
        body.pack(fill=tk.BOTH, expand=True)

        # Scrollable container for formula entries
        canvas = tk.Canvas(body, bg=COLOR_WHITE, relief="sunken", bd=1)
        scroll = ttk.Scrollbar(body, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=COLOR_WHITE)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        entry_vars = {}
        for key, default_meta in DEFAULT_FORMULAS.items():
            row_frame = tk.Frame(scroll_frame, bg=COLOR_WHITE, pady=6, padx=8)
            row_frame.pack(fill=tk.X, expand=True)

            tk.Label(row_frame, text=f"{key} — {default_meta.get('name', key)}",
                     font=("Segoe UI", 9, "bold"), bg=COLOR_WHITE, fg=COLOR_NAVY).pack(anchor="w")
            
            var = tk.StringVar(value=self.formulas.get(key, default_meta["expr"]))
            entry_vars[key] = var

            ent = tk.Entry(row_frame, textvariable=var, font=("Consolas", 10),
                           bg="#FAFAFA", fg=COLOR_BLACK, relief="groove", bd=1)
            ent.pack(fill=tk.X, expand=True, pady=2)

        # Footer Actions
        footer = tk.Frame(dlg, bg=COLOR_BAR_BG, relief="groove", bd=1, padx=10, pady=8)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        def save_formulas():
            for k, var in entry_vars.items():
                self.formulas[k] = var.get().strip()
            self.recompute_data()
            dlg.destroy()

        def restore_defaults():
            for k, default_meta in DEFAULT_FORMULAS.items():
                if k in entry_vars:
                    entry_vars[k].set(default_meta["expr"])

        tk.Button(footer, text="💾 Save & Recompute Well", font=("Segoe UI", 9, "bold"),
                  bg=COLOR_EXCEL_GREEN, fg=COLOR_WHITE, relief="raised", bd=2, padx=12, pady=4,
                  command=save_formulas).pack(side=tk.RIGHT, padx=4)

        tk.Button(footer, text="↺ Reset Defaults", font=("Segoe UI", 8),
                  bg=COLOR_WIN_BG, relief="raised", bd=1, padx=8, pady=4,
                  command=restore_defaults).pack(side=tk.RIGHT, padx=4)

        tk.Button(footer, text="Cancel", font=("Segoe UI", 8),
                  bg=COLOR_WIN_BG, relief="raised", bd=1, padx=8, pady=4,
                  command=dlg.destroy).pack(side=tk.LEFT, padx=4)

    # ──────────────────────────────────────────────────────────────────────────
    #  Modal Dialog: Column & Track Display Configuration
    # ──────────────────────────────────────────────────────────────────────────
    def open_column_manager_dialog(self):
        """Opens interactive column & track visibility manager dialog."""
        dlg = tk.Toplevel(self)
        dlg.title("Column & Track Display Configuration")
        dlg.geometry("580x520")
        dlg.transient(self)
        dlg.grab_set()
        dlg.configure(bg=COLOR_WIN_BG)

        hdr = tk.Frame(dlg, bg=COLOR_NAVY, padx=12, pady=10)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="📐 Column & Multi-Track Display Manager",
                 font=("Segoe UI", 11, "bold"), fg=COLOR_WHITE, bg=COLOR_NAVY).pack(anchor="w")
        tk.Label(hdr, text="Toggle which petrophysical tracks appear on the well log canvas.",
                 font=("Segoe UI", 8), fg="#D0D0D0", bg=COLOR_NAVY).pack(anchor="w")

        body = tk.Frame(dlg, bg=COLOR_WIN_BG, padx=12, pady=12)
        body.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(body, bg=COLOR_WHITE, relief="sunken", bd=1)
        scroll = ttk.Scrollbar(body, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=COLOR_WHITE)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        check_vars = []
        for track in self.schema:
            row_frame = tk.Frame(scroll_frame, bg=COLOR_WHITE, pady=4, padx=8)
            row_frame.pack(fill=tk.X, expand=True)

            var = tk.BooleanVar(value=track.get("visible", True))
            check_vars.append((track, var))

            chk = tk.Checkbutton(row_frame, text=f"{track['name']} ({track['unit']}) [Column: {track['key']}]",
                                 variable=var, font=("Segoe UI", 9), bg=COLOR_WHITE, anchor="w")
            chk.pack(side=tk.LEFT)

        footer = tk.Frame(dlg, bg=COLOR_BAR_BG, relief="groove", bd=1, padx=10, pady=8)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        def apply_changes():
            for track, var in check_vars:
                track["visible"] = var.get()
            self._render_multi_track_plot()
            self._update_status("Multi-track visibility updated.")
            dlg.destroy()

        def select_all(state):
            for _, var in check_vars:
                var.set(state)

        tk.Button(footer, text="Apply Changes", font=("Segoe UI", 9, "bold"),
                  bg=COLOR_NAVY, fg=COLOR_WHITE, relief="raised", bd=2, padx=12, pady=4,
                  command=apply_changes).pack(side=tk.RIGHT, padx=4)

        tk.Button(footer, text="Select All", font=("Segoe UI", 8),
                  bg=COLOR_WIN_BG, relief="raised", bd=1, padx=6, pady=4,
                  command=lambda: select_all(True)).pack(side=tk.LEFT, padx=2)

        tk.Button(footer, text="Deselect All", font=("Segoe UI", 8),
                  bg=COLOR_WIN_BG, relief="raised", bd=1, padx=6, pady=4,
                  command=lambda: select_all(False)).pack(side=tk.LEFT, padx=2)

    # ──────────────────────────────────────────────────────────────────────────
    #  Help & About Dialogs
    # ──────────────────────────────────────────────────────────────────────────
    def show_formulas_help(self):
        """Displays methodology help reference."""
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
        """Shows formal About dialog with creator credit."""
        dlg = tk.Toplevel(self)
        dlg.title("About MudLog Pro")
        dlg.geometry("480x360")
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()
        dlg.configure(bg=COLOR_WIN_BG)

        # Header Banner
        hdr = tk.Frame(dlg, bg=COLOR_NAVY, padx=16, pady=16)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="MudLog Pro Desktop Software", font=("Segoe UI", 14, "bold"), fg=COLOR_WHITE, bg=COLOR_NAVY).pack(anchor="w")
        tk.Label(hdr, text=f"Version {APP_VERSION} • Formal Engineering Edition", font=("Segoe UI", 9), fg="#D0D0D0", bg=COLOR_NAVY).pack(anchor="w")

        # Body
        body = tk.Frame(dlg, bg=COLOR_WIN_BG, padx=18, pady=16)
        body.pack(fill=tk.BOTH, expand=True)

        tk.Label(body, text="Deterministic Multi-Track Well Logging Suite", font=("Segoe UI", 10, "bold"), bg=COLOR_WIN_BG, fg=COLOR_TEXT_MAIN).pack(anchor="w", pady=(0, 4))
        tk.Label(body, text="Interactive hydrocarbon gas ratio calculation, multi-track continuous well log visualization, and fluid facies zone classification.",
                 font=("Segoe UI", 9), bg=COLOR_WIN_BG, fg=COLOR_TEXT_MUTED, wraplength=440, justify="left").pack(anchor="w", pady=(0, 12))

        # Attribution Card (Prominent Box)
        attr_frame = tk.Frame(body, bg=COLOR_WHITE, relief="groove", bd=2, padx=12, pady=10)
        attr_frame.pack(fill=tk.X, pady=6)

        tk.Label(attr_frame, text="APPLICATION CREATOR", font=("Segoe UI", 8, "bold"), fg=COLOR_NAVY, bg=COLOR_WHITE).pack(anchor="w")
        tk.Label(attr_frame, text="Mohammad Azka Khairur Rahman", font=("Segoe UI", 12, "bold"), fg=COLOR_EXCEL_GREEN, bg=COLOR_WHITE).pack(anchor="w", pady=2)
        tk.Label(attr_frame, text="Mudlogging & Petrophysical Analysis Research Software", font=("Segoe UI", 8), fg=COLOR_TEXT_MUTED, bg=COLOR_WHITE).pack(anchor="w")

        # OK button
        tk.Button(dlg, text="OK", font=("Segoe UI", 9, "bold"), bg=COLOR_WIN_BG, relief="raised", bd=2, width=10,
                  command=dlg.destroy).pack(side=tk.BOTTOM, pady=12)


# ──────────────────────────────────────────────────────────────────────────────
#  Application Entry Point
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = MudLogDesktopApp()
    app.mainloop()
