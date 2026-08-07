# ⛽ MudLog Analyzer — Deterministic Mudlogging Analysis Dashboard

A desktop petrophysical dashboard for **Gas While Drilling (GWD)** mudlogging data analysis and deterministic hydrocarbon zone classification.

Built with Python, Dash, Bootstrap, and Plotly, this application provides automated data parsing, 16 petrophysical indicator computations, auditable physics-based zone classification, interactive multi-track depth logs, and comprehensive evaluation against ground-truth well test results.

---

## 🌟 Key Features

- **Multi-Format Ingestion**: Drag-and-drop parsing for `.csv`, `.txt`, and `.xlsx` mudlog files. Automatically standardizes column headers and cleans invalid readings.
- **16 Petrophysical Indicators**: Computes hydrocarbon gas ratios (Pixler & Haworth), gas dryness, carbon index, wetness/balance/character indicators, and total gas metrics.
- **Deterministic Expert System**: Pure physics-based, auditable rule-engine for classifying depth intervals into **Gas**, **Oil**, **Water**, or **No Show**.
- **Interactive Multi-Track Visualizations**: High-density depth-log charts featuring:
  - 📐 **Side-by-Side Track Row**: Continuous horizontal multi-track scrollable log view.
  - 📊 **Separate Column Cards**: Responsive grid of individual gas/ratio charts.
  - 📑 **Grouped Category Tracks**: Traditional 5-track well-log layout with color-coded zone overlay.
- **Ground-Truth Evaluation**: Optional upload of well-testing ground-truth CSV data to compute:
  - Confusion Matrix (4×4 multi-class heatmap)
  - Accuracy, Precision, Recall, and Macro F1-Score
  - Per-class performance breakdown
- **One-Click Export**: Download complete computed petrophysical reports as CSV.

---

## 🛠️ Project Structure

```
Mudlogging/
├── app.py              # Main Dash desktop web application & UI layout
├── engine.py           # Petrophysical engine (16 indicator formulas & rule engine)
├── evaluator.py        # Evaluation metrics module (confusion matrix, precision/recall/F1)
├── parser.py           # Rig site log file ingestion & data cleaning module
├── view_sbs.py         # Standalone HTML side-by-side mudlog track renderer
├── requirements.txt    # Application dependencies
└── README.MD           # Project documentation
```

---

## 📐 Petrophysical Engine Formulas

The deterministic engine (`engine.py`) evaluates depth intervals using standard hydrocarbon evaluation equations:

### 1. Pixler Ratios
- **C1 / C2 Ratio ($R_1$)**: $\frac{\text{C1}}{\text{C2}}$
- **C1 / C3 Ratio ($R_2$)**: $\frac{\text{C1}}{\text{C3}}$
- **C2 / C3 Ratio ($R_3$)**: $\frac{\text{C2}}{\text{C3}}$
- **C1 / iC4 Ratio ($R_4$)**: $\frac{\text{C1}}{\text{iC4}}$
- **C1 / nC4 Ratio ($R_5$)**: $\frac{\text{C1}}{\text{nC4}}$

### 2. Haworth Wetness, Balance, and Character Ratios
- **Wetness Ratio ($W_h\%$)**: $\frac{\text{C2} + \text{C3} + \text{iC4} + \text{nC4} + \text{iC5} + \text{nC5}}{\text{TG}} \times 100$
- **Balance Ratio ($B_h$)**: $\frac{\text{C1} + \text{C2}}{\text{C3} + \text{iC4} + \text{nC4} + \text{iC5} + \text{nC5}}$
- **Character Ratio ($C_h$)**: $\frac{\text{iC4} + \text{nC4} + \text{iC5} + \text{nC5}}{\text{C3}}$

### 3. Composite Indicators
- **Gas Dryness**: $\frac{\text{C1}}{\text{Derived TG}}$
- **Carbon Index**: Weighted heavy gas composition indicator.
- **Gas-Oil-Water (GOW) Ratio**: Multi-gas ratio indicating fluid type.

---

## 🚀 Getting Started

### Prerequisites

Python 3.10+ installed on Windows, macOS, or Linux.

### Installation

1. Clone or navigate to the repository directory:
   ```bash
   cd Mudlogging
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

Launch the desktop interface:
```bash
python app.py
```

The application will start a local server at `http://127.0.0.1:8051` and automatically open your default browser.

---

## 📦 Building Standalone Executable

To compile into a standalone Windows `.exe` application without python environment requirements:

```bash
pyinstaller --onefile --noconsole app.py
```

The compiled binary will be available in the `dist/` directory.

---

## 📄 License

This software is developed for mudlogging research and petrophysical analysis.