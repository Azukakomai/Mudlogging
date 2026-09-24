# MudLog Pro — Desktop Software Edition

**Created By Mohammad Azka Khairur Rahman**

A standalone, formal desktop software application for **Petrophysical Multi-Track Well Logging, Continuous Gas Ratio Computation, and Deterministic Fluid Facies Zone Classification**.

---

## 🏛️ Design & Aesthetics
Designed with a classic, formal engineering and spreadsheet software aesthetic inspired by **Microsoft Excel, Google Docs, WinLog, and classic Windows 2000/XP CAD suites**:
- **Classic Menubar & Accelerator Shortcuts** (`File`, `Edit`, `View`, `Calculations`, `Help`)
- **Excel-Style Formula & Depth Inspector Bar** with real-time zone indicator badge
- **Beveled & Relief Toolbars** with quick access buttons
- **Multi-Tab Workspaces (Classic Sheet Tabs)**:
  1. `📈 Multi-Track Depth Log`: High-resolution continuous multi-track curves (C1–C5, TG, Pixler R1–R4, Haworth Wh/Bh/Ch, GOW, WBS) and Fluid Facies colored overlay track (Gas / Oil / Non-Bearing).
  2. `📊 Spreadsheet Data (Excel View)`: Tabular spreadsheet view with alternating row colors, row indices, sorting, facies highlights, and Excel TSV clipboard copying.
  3. `📋 Fluid Facies & Petrophysical Summary`: Statistical summary cards (Gas payzone intervals, Oil payzone intervals, Net/Gross ratio, parameter percentiles).
  4. `🧮 Petrophysical Formula Inspector`: Auditable equations and threshold reference.
- **Classic Multi-Pane Sunken Status Bar**: Showing depth span, row count, active tracks, facies count, and creator attribution.

---

## 🚀 How to Run

### Quick Windows One-Click:
Double-click [`run.bat`](file:///c:/Users/moham/Documents/Skripsi/Mudlogging/desktop_app/run.bat).

### Terminal / Command Line:
```powershell
cd desktop_app
py main.py
```

---

## ⚙️ Key Features
- **File Ingestion**: Load `.csv`, `.txt`, `.xlsx`, and `.xls` files directly.
- **Live Formula Customization**: Edit formulas and recompute log curves in real-time.
- **Track Display Manager**: Show/hide any individual petrophysical track column.
- **Percentile Peak Filtering**: Filter curve baselines by P75, P90, P50, or show raw curves (P0).
- **Export Options**: Export calculated tables to CSV, or export multi-track charts to high-resolution PNG, PDF, or JPG.
