# Mudlogging Pro — 21-Track Petrophysical Decision Support System
**Seminar Hasil (Semhas) Release** • *Universitas Gadjah Mada (UGM) Skripsi*

---

## 🌟 Overview
**Mudlogging Pro** is an interactive, high-performance web and Python petrophysical visualization dashboard designed to perform deterministic, rule-based **Gas While Drilling (GWD) Fluid Typing** across 21 dedicated vertical well log tracks with zero ML black-box reliance.

Built under the **SDLC 5-Phase Methodology**, this system delivers real-time calculation, interactive multi-track synchronized crosshair inspection, custom dynamic formula and column management, multi-format file ingestion, and publication-ready deliverable exports.

---

## 🚀 Key Features

### 1. 21-Track Continuous Well Log Visualization
- **Sticky Measured Depth (MD) Axis**: Locked reference depth scale for continuous vertical tracking.
- **Dedicated Track Columns**: Every hydrocarbon gas ($C_1 - C_5, TG$), Pixler ratio ($R_1 - R_5$), Haworth show indicator ($W_h, B_h, C_h$), composite parameters (Dryness, Carbon Index $C_i$, WBS, GOW, GOR), and fluid classification zone has its own individual graph.
- **Synchronized Depth Crosshairs**: Real-time synchronized horizontal tracking cursor with depth tooltips across all 21 tracks simultaneously.
- **Discrete Fluid Zone Facies Track**: Visual color-coded reservoir facies intervals for **Gas Pay** (emerald), **Oil Pay** (amber), **Water Sand** (indigo), and **No Show** (slate).

### 2. Dynamic Pipeline Controls (Configuration Dropdown)
- **Column Configuration & Display Manager**:
  - Toggle visibility of individual tracks with instant live layout updates.
  - Add custom computed columns with custom mathematical expressions and quick-insert variable tokens ($C_1 \dots C_5, TG, W_h, B_h$).
  - Remove or reorder columns.
- **Petrophysical Formula & Indicator Manager**:
  - Live formula editor for all 14 standard indicators.
  - Customizable boundary cutoff thresholds for Gas, Oil, and Water classifications.
  - Real-time calculation preview against active well log depth intervals.
- **Reset to Skripsi Baseline**: Instantly restore standard 21 indicators and default formulas.

### 3. Quick KPI Performance Bar
- **Measured Depth Span**: Start/end interval and total thickness in meters.
- **Dominant Reservoir Facies**: Automated majority classification across the well section.
- **Peak Methane ($C_1$)**: Maximum detected gas concentration in ppm.
- **Mean Gas Dryness ($C_1/TG$)**: Reservoir gas dryness percentage.
- **Active Payzone Thickness**: Cumulative net pay interval in meters.
- **Mean Hydrocarbon Wetness ($W_h$)**: Haworth wetness percentage.

### 4. Multi-Format Data Ingestion
- Drag-and-drop support for **ASCII LAS (2.0/3.0)**, **CSV**, **TXT**, and **Excel (.xlsx)** files.
- **1-Click Preset Benchmark Datasets**:
  - *Mahakam Basin* (Gas-dominant deltaic reservoir).
  - *North Sea* (Volatile oil / condensate reservoir).
  - *Skripsi Benchmark* (Standard synthetic test well spanning 1800m–3100m).

### 5. Export Suite
- **Computed CSV Dataset**: Full tabular data with all 16 derived ratios and fluid classifications.
- **High-Resolution PNG Snapshot**: Publication-quality multi-track log image.
- **Schema JSON Configuration**: Export/import custom column definitions and formula rules.
- **Print / Presentation Mode**: Formatted view optimized for presentation slides.

---

## 📂 Project Structure

```
Semhas/
├── index.html         # Main Single-Page Web Application
├── styles.css         # Modern dark glassmorphism design tokens & styles
├── engine.js          # Petrophysical math engine & safe expression parser
├── app.js             # State management, Chart.js lifecycle, sync crosshair, exports
├── server.py          # Zero-dependency local web server launcher
├── test_suite.py      # Automated calculation & latency unit test suite
└── README.md          # Project documentation
```

---

## 🏃 How to Run

### Method 1: Python Local Server (Recommended)
Open a terminal in the project directory and run:
```bash
python Semhas/server.py
```
This automatically hosts the application at `http://localhost:8050` and opens your default browser.

### Method 2: Direct Browser Opening
You can also directly open `Semhas/index.html` in any modern web browser (Chrome, Edge, Firefox, Safari) with zero setup required.

### Method 3: Run Automated Verification Tests
To verify mathematical accuracy and execute throughput latency benchmarks:
```bash
python Semhas/test_suite.py
```

---

## 🎓 Academic Thesis Details
- **Institution**: Universitas Gadjah Mada (UGM)
- **Topic**: Deterministic FluidTyping Decision Support System for Gas While Drilling
- **SDLC**: 5-Phase Software Development Life Cycle (Requirements, Design, Implementation, Verification, Packaging)
- **Target Throughput**: $\Delta t_{\text{total}} \le 5.0\text{ s}$ for $>3000\text{ m}$ well profiles
- **Usability Target**: $\overline{S} > 68.0 / 100$
