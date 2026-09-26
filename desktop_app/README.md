# MudLog Pro — Desktop Software Edition

**Created By Mohammad Azka Khairur Rahman**

A standalone desktop software application for **Petrophysical Multi-Track Well Logging, Continuous Gas Ratio Computation, and Deterministic Fluid Facies Zone Classification**.

---

## 🎨 Modern Google Sheets & Excel 365 Architecture

### 📑 1. Google Sheets Multi-Tab Workspaces (Bottom Bar)
- **Multi-Well / Multi-Dataset Tabs**: Located at the bottom of the screen just like Google Sheets. Each sheet tab holds an independent well dataset, formula configuration, and petrophysical analysis session.
- **`➕` Add Sheet Button**: Effortlessly create new blank well sheets or load different datasets side-by-side.
- **Tab Context Menu**: Right-click any tab to `Rename`, `Duplicate`, `Load File into Sheet`, `Detach`, or `Close`.
- **Double-Click to Rename**: Double-click any sheet tab to quickly rename it.

### 🪟 2. Drag & Drop Tab Detach (Standalone Floating Windows)
- **Drag-to-Tear-Off**: Click and drag any bottom tab outside the main application window to pop it into its own independent floating window!
- **One-Click Detach (`↗`)**: Click the `↗` icon on any tab or inside the workspace to undock it instantly.
- **One-Click Re-attach (`↙`)**: Click `↙ Re-attach to Main Window` to bring the detached well window back into the main bottom tab bar seamlessly.

### 📊 3. Modern Spreadsheet & Log Sub-Views
Inside each well workspace, switch smoothly between:
1. `📈 Multi-Track Depth Log`: High-resolution continuous multi-track curves (C1–C5, TG, Pixler R1–R4, Haworth Wh/Bh/Ch, GOW, WBS) and Fluid Facies colored overlay track (Gas / Oil / Non-Bearing) with optimized compact header spacing.
2. `📊 Spreadsheet Grid (Excel View)`: Modern tabular spreadsheet view with row numbers (`#`), soft pastel facies tints (Rose for Gas, Mint for Oil), zone filter, and Excel TSV clipboard copying.
3. `📋 Fluid Facies & Petrophysical Summary`: Modern executive KPI cards (Depth interval, Gas payzones, Oil payzones, Net/Gross ratio) and statistical parameter distribution table.
4. `🧮 Petrophysical Formula Engine`: Auditable equations and threshold reference with direct modal editor.

### 🏛️ 4. Microsoft Excel Emerald Header & Ribbon
- **Excel Forest Green Title Bar** (`#107C41`) with active well indicator pill.
- **Office 365 Flat Action Ribbon**: Quick access for file opening, CSV/plot exports, formula customization, track schema manager, and peak filter cutoffs.
- **Excel Formula Bar (`fx`)**: Name box / Depth coordinate cell, signature `fx` button, live formula input, and real-time fluid facies zone pill badge.

---

## 🚀 How to Run

### Quick Windows One-Click:
Double-click [`run.bat`](file:///c:/Users/moham/Documents/Skripsi/Mudlogging/desktop_app/run.bat).

### Terminal / Command Line:
```powershell
cd desktop_app
py main.py
```
