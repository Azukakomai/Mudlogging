"""
Petrophysical Engine — Deterministic Indicator Calculations & Zone Classification.

Implements all 16 derived indicators from the thesis methodology:
  Pixler ratios (R1–R5), Derived TG, Dryness, Carbon Index (TG Sum),
  Haworth ratios (Wh, Bh, Ch), GOW, GOW_noTG, WBS, GOR, and Zone Classification.

Every formula is an explicit, auditable physics equation — no black-box ML.
"""

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
#  Utility: safe division (returns NaN instead of raising on zero-divisor)
# ---------------------------------------------------------------------------

# Divide function
def _safe_div(numerator, denominator):
    """Element-wise division that returns NaN where denominator is zero."""
    with np.errstate(divide='ignore', invalid='ignore'):
        result = np.where(denominator != 0, numerator / denominator, np.nan)
    return result


# ---------------------------------------------------------------------------
#  Core computation
# ---------------------------------------------------------------------------

# Default formula definitions matching thesis / petrophysical standard
DEFAULT_FORMULAS = {
    "WH": {
        "name": "Haworth Wetness Ratio (Wh)",
        "expr": "((C2 + C3 + IC4 + NC4 + IC5 + NC5) / DERIVED_TG) * 100.0",
        "gas": "Wh < 17.5",
        "oil": "17.5 <= Wh <= 40.0",
        "water": "Wh > 40.0",
    },
    "BH": {
        "name": "Haworth Balance Ratio (Bh)",
        "expr": "(C1 + C2) / (C3 + IC4 + NC4 + IC5 + NC5)",
        "gas": "Bh >= 15.0",
        "oil": "0.5 <= Bh < 15.0",
        "water": "Bh < 0.5",
    },
    "CH": {
        "name": "Haworth Character Ratio (Ch)",
        "expr": "(IC4 + NC4 + IC5 + NC5) / C3",
        "gas": "Ch < 0.5",
        "oil": "Ch >= 0.5",
        "water": "Undefined",
    },
    "R1_C1_C2": {
        "name": "Pixler R1 (C1 / C2)",
        "expr": "C1 / C2",
        "gas": "R1 >= 15.0",
        "oil": "2.0 <= R1 < 15.0",
        "water": "R1 < 2.0",
    },
    "R2_C1_C3": {
        "name": "Pixler R2 (C1 / C3)",
        "expr": "C1 / C3",
        "gas": "R2 > 30.0",
        "oil": "4.0 <= R2 <= 30.0",
        "water": "R2 < 4.0",
    },
    "R3_C2_C3": {
        "name": "Pixler R3 (C2 / C3)",
        "expr": "C2 / C3",
        "gas": "R3 < 0.5",
        "oil": "0.5 <= R3 <= 5.0",
        "water": "R3 > 5.0",
    },
    "R4_C1_IC4": {
        "name": "Ratio 4 (C1 / iC4)",
        "expr": "C1 / IC4",
        "gas": "R4 > 150.0",
        "oil": "15.0 <= R4 <= 150.0",
        "water": "R4 < 15.0",
    },
    "R5_C1_NC4": {
        "name": "Ratio 5 (C1 / nC4)",
        "expr": "C1 / NC4",
        "gas": "R5 > 100.0",
        "oil": "10.0 <= R5 <= 100.0",
        "water": "R5 < 10.0",
    },
    "DRYNESS": {
        "name": "Dryness Ratio (C1 / TG)",
        "expr": "C1 / DERIVED_TG",
        "gas": "Dry >= 0.85",
        "oil": "0.50 <= Dry < 0.85",
        "water": "Dry < 0.50",
    },
    "CARBON_INDEX": {
        "name": "Carbon Density Index (Ci)",
        "expr": "DERIVED_TG / (C1 + 2*C2 + 3*C3 + 4*IC4 + 4*NC4 + 5*IC5 + 5*NC5)",
        "gas": "> 0.85",
        "oil": "0.40 - 0.85",
        "water": "< 0.40",
    },
    "GOW": {
        "name": "Composite GOW",
        "expr": "(C3 + IC4 + NC4 + IC5 + NC5) * DERIVED_TG",
        "gas": "GOW < 500",
        "oil": "500 <= GOW <= 15000",
        "water": "GOW > 15000",
    },
    "GOW_NOTG": {
        "name": "GOW No-TG (Normalized Heavy Fraction)",
        "expr": "(C2 + C3 + IC4 + NC4 + IC5 + NC5) / DERIVED_TG",
        "gas": "< 0.015",
        "oil": "0.015 - 0.08",
        "water": "> 0.08",
    },
    "WBS": {
        "name": "Wetness-Balance Score (WBS)",
        "expr": "((log10(BH) - log10(8)) / (log10(1000) - log10(8))) - (log10(WH) / log10(100))",
        "gas": "WBS > 0",
        "oil": "-0.5 <= WBS <= 0",
        "water": "WBS < -0.5",
    },
    "GOR": {
        "name": "Gas-Oil Ratio (GOR)",
        "expr": "where((TG_USED > 0.8) & (TG_USED < 1.2) & (C1 > 2000), 0, 1)",
        "gas": "> 5000",
        "oil": "500 - 5000",
        "water": "< 500",
    },
}


def eval_expr(expr: str, df: pd.DataFrame):
    """
    Safely evaluate a mathematical expression against DataFrame column arrays.
    Supports variables (C1, C2, C3, iC4, nC4, iC5, nC5, TG, DERIVED_TG, etc.)
    and math operations log10, log, sqrt, abs, exp, where.
    """
    if not expr or not isinstance(expr, str):
        return np.full(len(df), np.nan)

    clean_expr = expr.strip()
    if not clean_expr:
        return np.full(len(df), np.nan)

    context = {
        'log10': lambda x: np.where(np.asarray(x, dtype=float) > 0, np.log10(np.asarray(x, dtype=float)), np.nan),
        'log': lambda x: np.where(np.asarray(x, dtype=float) > 0, np.log(np.asarray(x, dtype=float)), np.nan),
        'sqrt': lambda x: np.where(np.asarray(x, dtype=float) >= 0, np.sqrt(np.asarray(x, dtype=float)), np.nan),
        'abs': np.abs,
        'exp': np.exp,
        'where': np.where,
        'np': np,
    }

    for col in df.columns:
        vals = pd.to_numeric(df[col], errors='coerce').fillna(0.0).values.astype(float)
        context[col] = vals
        context[col.upper()] = vals
        context[col.lower()] = vals
        # Common casing
        if col.upper() == 'IC4':
            context['iC4'] = vals
        elif col.upper() == 'NC4':
            context['nC4'] = vals
        elif col.upper() == 'IC5':
            context['iC5'] = vals
        elif col.upper() == 'NC5':
            context['nC5'] = vals
        elif col.upper() == 'DERIVED_TG':
            context['derived_tg'] = vals
        elif col.upper() == 'TG_USED':
            context['TG'] = vals
            context['tg'] = vals

    if 'TG' not in context:
        if 'TG_USED' in context:
            context['TG'] = context['TG_USED']
        elif 'DERIVED_TG' in context:
            context['TG'] = context['DERIVED_TG']

    try:
        res = eval(clean_expr, {"__builtins__": {}}, context)
        if isinstance(res, (int, float)):
            res = np.full(len(df), float(res))
        elif not isinstance(res, np.ndarray):
            res = np.array(res, dtype=float)
        return res
    except Exception as e:
        raise ValueError(f"Expression evaluation error: {str(e)}")


def compute_all(df: pd.DataFrame, formula_overrides: dict = None, custom_columns: list = None) -> pd.DataFrame:
    """
    Takes a cleaned DataFrame with columns:
        DEPTH, C1, C2, C3, IC4, NC4, IC5, NC5 (and optionally TG)
    Accepts optional formula_overrides {key: expr_str} and custom_columns [{key, expr}].
    Returns a new DataFrame with all original columns plus derived columns & Zone.
    """
    out = df.copy()

    C1  = out['C1'].values.astype(float)
    C2  = out['C2'].values.astype(float)
    C3  = out['C3'].values.astype(float)
    IC4 = out['IC4'].values.astype(float)
    NC4 = out['NC4'].values.astype(float)
    IC5 = out['IC5'].values.astype(float)
    NC5 = out['NC5'].values.astype(float)

    # ------------------------------------------------------------------
    #  Base Derived TG
    # ------------------------------------------------------------------
    derived_tg = C1 + C2 + C3 + IC4 + NC4 + IC5 + NC5

    if 'TG' in out.columns and out['TG'].notna().any() and (out['TG'] > 0).any():
        TG = out['TG'].values.astype(float)
        TG = np.where(TG > 0, TG, derived_tg)
    else:
        TG = derived_tg

    out['DERIVED_TG'] = derived_tg
    out['TG_USED']    = TG

    # ------------------------------------------------------------------
    #  Pixler & Ratio Defaults
    # ------------------------------------------------------------------
    out['R1_C1_C2']  = _safe_div(C1, C2)
    out['R2_C1_C3']  = _safe_div(C1, C3)
    out['R3_C2_C3']  = _safe_div(C2, C3)
    out['R4_C1_IC4'] = _safe_div(C1, IC4)
    out['R5_C1_NC4'] = _safe_div(C1, NC4)
    out['C2_C1']     = _safe_div(C2, C1)
    out['C3_C1']     = _safe_div(C3, C1)

    # ------------------------------------------------------------------
    #  Standard Petrophysical Indicators
    # ------------------------------------------------------------------
    out['DRYNESS'] = _safe_div(C1, derived_tg)
    carbon_weighted = C1 + 2*C2 + 3*C3 + 4*IC4 + 4*NC4 + 5*IC5 + 5*NC5
    out['CARBON_INDEX'] = _safe_div(derived_tg, carbon_weighted)

    heavy_sum = C2 + C3 + IC4 + NC4 + IC5 + NC5
    out['WH'] = _safe_div(heavy_sum, derived_tg) * 100.0

    light = C1 + C2
    heavy = C3 + IC4 + NC4 + IC5 + NC5
    out['BH'] = _safe_div(light, heavy)

    butane_pentane = IC4 + NC4 + IC5 + NC5
    out['CH'] = _safe_div(butane_pentane, C3)

    out['GOW'] = heavy * derived_tg
    out['GOW_NOTG'] = _safe_div(heavy, derived_tg)

    Bh = out['BH'].values.astype(float)
    Wh = out['WH'].values.astype(float)

    with np.errstate(divide='ignore', invalid='ignore'):
        log_bh  = np.where(Bh > 0, np.log10(Bh), np.nan)
        log_wh  = np.where(Wh > 0, np.log10(Wh), np.nan)
        log_8   = np.log10(8)
        log_1000 = np.log10(1000)
        log_100  = np.log10(100)
        wbs = (log_bh - log_8) / (log_1000 - log_8) - log_wh / log_100

    out['WBS'] = wbs
    gor = np.where((TG > 0.8) & (TG < 1.2) & (C1 > 2000), 0, 1)
    out['GOR'] = gor

    # ------------------------------------------------------------------
    #  Apply Dynamic Formula Overrides if provided
    # ------------------------------------------------------------------
    if formula_overrides:
        for key, expr in formula_overrides.items():
            if expr and isinstance(expr, str) and expr.strip():
                try:
                    out[key] = eval_expr(expr, out)
                except Exception:
                    pass

    # ------------------------------------------------------------------
    #  Apply Custom User Columns if provided
    # ------------------------------------------------------------------
    if custom_columns:
        for item in custom_columns:
            col_key = item.get('key')
            col_expr = item.get('expr')
            if col_key and col_expr:
                try:
                    out[col_key] = eval_expr(col_expr, out)
                except Exception:
                    out[col_key] = np.nan

    # ------------------------------------------------------------------
    #  Zone Classification — majority-vote expert matrix
    # ------------------------------------------------------------------
    out['ZONE'] = _classify_zones(out)

    return out


# ---------------------------------------------------------------------------
#  Majority-vote zone classifier
# ---------------------------------------------------------------------------

def _classify_zones(df: pd.DataFrame) -> pd.Series:
    """
    Applies rule-based expert decision logic per depth row.
    Cross-references Haworth (Wh, Bh, Ch), Dryness, Pixler (C1/C2), WBS, GOR, and GOW_noTG.
    Outputs: 'No Show', 'Gas', 'Oil', or 'Water'.
    """
    n = len(df)
    zones = []

    Wh       = df['WH'].values.astype(float)
    Bh       = df['BH'].values.astype(float)
    Ch       = df['CH'].values.astype(float)
    Wbs      = df['WBS'].values.astype(float)
    Dry      = df['DRYNESS'].values.astype(float)
    Gow_notg = df['GOW_NOTG'].values.astype(float) if 'GOW_NOTG' in df.columns else np.full(n, np.nan)
    Gor      = df['GOR'].values.astype(int) if 'GOR' in df.columns else np.ones(n, dtype=int)

    C1  = df['C1'].values.astype(float)
    C2  = df['C2'].values.astype(float)
    C3  = df['C3'].values.astype(float)
    IC4 = df['IC4'].values.astype(float)
    NC4 = df['NC4'].values.astype(float)
    IC5 = df['IC5'].values.astype(float)
    NC5 = df['NC5'].values.astype(float)

    if 'DERIVED_TG' in df.columns:
        derived_tg = df['DERIVED_TG'].values.astype(float)
    else:
        derived_tg = C1 + C2 + C3 + IC4 + NC4 + IC5 + NC5

    heavy_sum = C2 + C3 + IC4 + NC4 + IC5 + NC5

    for i in range(n):
        tg = derived_tg[i]
        c1 = C1[i]

        # 1. Background Noise / Low Gas Cutoff:
        if tg < 300 or c1 < 200:
            zones.append("No Show")
            continue

        # 2. Zero Heavy Gas Intervals (Pure Methane):
        if heavy_sum[i] == 0:
            if c1 >= 2000:
                zones.append("Gas")
            else:
                zones.append("No Show")
            continue

        gas_votes = 0
        oil_votes = 0
        water_votes = 0

        # --- Indicator 1: Haworth Wetness (Wh) ---
        wh = Wh[i]
        if not np.isnan(wh):
            if wh < 0.5:
                if c1 < 2000:
                    zones.append("No Show")
                    continue
                else:
                    gas_votes += 1
            elif wh < 17.5:
                gas_votes += 1
            elif wh <= 40.0:
                oil_votes += 1
            else:
                water_votes += 1

        # --- Indicator 2: Haworth Balance (Bh) ---
        bh = Bh[i]
        if not np.isnan(bh):
            if bh >= 15.0:
                gas_votes += 1
            elif bh >= 0.5:
                oil_votes += 1
            else:
                water_votes += 1

        # --- Indicator 3: Haworth Character (Ch) ---
        ch = Ch[i]
        if not np.isnan(ch):
            if ch < 0.5:
                gas_votes += 1
            else:
                oil_votes += 1

        # --- Indicator 4: Dryness Ratio (C1 / TG) ---
        dry = Dry[i]
        if not np.isnan(dry):
            if dry >= 0.85:
                gas_votes += 1
            elif dry >= 0.50:
                oil_votes += 1
            else:
                water_votes += 1

        # --- Indicator 5: Pixler C1/C2 (R1) ---
        c2 = C2[i]
        if c2 > 0:
            r1 = c1 / c2
            if r1 >= 15.0:
                gas_votes += 1
            elif r1 >= 2.0:
                oil_votes += 1
            else:
                water_votes += 1

        # --- Indicator 6: Wetness-Balance Score (WBS) ---
        wbs = Wbs[i]
        if not np.isnan(wbs):
            if wbs > 0:
                gas_votes += 1
            elif wbs >= -0.5:
                oil_votes += 1
            else:
                water_votes += 1

        # --- Indicator 7: Gas-Oil Ratio Index (GOR) ---
        if Gor[i] == 0:
            gas_votes += 1

        # --- Indicator 8: Normalized Heavy Gas (GOW_noTG) ---
        gow_n = Gow_notg[i]
        if not np.isnan(gow_n):
            if gow_n < 0.015:
                gas_votes += 1
            elif gow_n <= 0.08:
                oil_votes += 1
            else:
                water_votes += 1

        # --- Determine winning class from expert matrix votes ---
        votes = {"Gas": gas_votes, "Oil": oil_votes, "Water": water_votes}
        max_v = max(votes.values())
        if max_v == 0:
            zones.append("No Show")
        else:
            winners = [k for k, v in votes.items() if v == max_v]
            if "Gas" in winners:
                zones.append("Gas")
            elif "Oil" in winners:
                zones.append("Oil")
            else:
                zones.append("Water")

    return pd.Series(zones, index=df.index)
