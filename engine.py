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

# Default formula definitions matching thesis / Chapter 3 petrophysical standard
DEFAULT_FORMULAS = {
    "C1": {
        "name": "Methane Gas Channel (C1)",
        "expr": "C1",
        "gas": "C1 >= 2000",
        "oil": "500 <= C1 < 2000",
        "water": "C1 < 500",
    },
    "WH": {
        "name": "Haworth Wetness Ratio (Wh)",
        "expr": "((C2 + C3 + IC4 + NC4 + IC5 + NC5) / TG) * 100.0",
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
    "R3_C3_C1": {
        "name": "Pixler R3 (C3 / C1)",
        "expr": "C3 / C1",
        "gas": "R3 < 0.033",
        "oil": "0.033 <= R3 <= 0.25",
        "water": "R3 > 0.25",
    },
    "R4_C2_C1": {
        "name": "Pixler R4 (C2 / C1)",
        "expr": "C2 / C1",
        "gas": "R4 < 0.067",
        "oil": "0.067 <= R4 <= 0.50",
        "water": "R4 > 0.50",
    },
    "RATIO_IC4": {
        "name": "Expanded Ratio iC4 (C1 / iC4)",
        "expr": "C1 / IC4",
        "gas": "Ratio_iC4 > 150.0",
        "oil": "15.0 <= Ratio_iC4 <= 150.0",
        "water": "Ratio_iC4 < 15.0",
    },
    "RATIO_NC4": {
        "name": "Expanded Ratio nC4 (C1 / nC4)",
        "expr": "C1 / NC4",
        "gas": "Ratio_nC4 > 100.0",
        "oil": "10.0 <= Ratio_nC4 <= 100.0",
        "water": "Ratio_nC4 < 10.0",
    },
    "TG": {
        "name": "Total Gas Volume (TG)",
        "expr": "C1 + C2 + C3 + IC4 + NC4 + IC5 + NC5",
        "gas": "TG >= 2000",
        "oil": "500 <= TG < 2000",
        "water": "TG < 500",
    },
    "DRYNESS": {
        "name": "Dryness Ratio (DR = C1 / TG)",
        "expr": "C1 / TG",
        "gas": "DR >= 0.85",
        "oil": "0.50 <= DR < 0.85",
        "water": "DR < 0.50",
    },
    "CARBON_INDEX": {
        "name": "Carbon Density Index (Icarbon)",
        "expr": "TG / (C1 + 2*C2 + 3*C3 + 4*IC4 + 4*NC4 + 5*IC5 + 5*NC5)",
        "gas": "Icarbon > 0.85",
        "oil": "0.40 <= Icarbon <= 0.85",
        "water": "Icarbon < 0.40",
    },
    "GOW": {
        "name": "Composite GOW",
        "expr": "((C3 + IC4 + NC4 + IC5 + NC5) * TG) / (C1 + C2 + C3 + IC4 + NC4 + IC5 + NC5)",
        "gas": "GOW < 500",
        "oil": "500 <= GOW <= 15000",
        "water": "GOW > 15000",
    },
    "GOW_NOTG": {
        "name": "GOW No-TG (Normalized Heavy Fraction)",
        "expr": "(C3 + IC4 + NC4 + IC5 + NC5) / (C1 + C2 + C3 + IC4 + NC4 + IC5 + NC5)",
        "gas": "GOW_noTG < 0.015",
        "oil": "0.015 <= GOW_noTG <= 0.08",
        "water": "GOW_noTG > 0.08",
    },
    "WBS": {
        "name": "Wetness-Balance Score (WBS)",
        "expr": "(log10(BH) - 0.903) / 2.097 - log10(WH) / 2",
        "gas": "WBS > 0",
        "oil": "-0.5 <= WBS <= 0",
        "water": "WBS < -0.5",
    },
    "GOR": {
        "name": "Gas-Oil Ratio (GOR) Screening",
        "expr": "where((TG > 0.8) & (TG < 1.2) & (C1 > 2000), 0, 1)",
        "gas": "GOR == 0 (Dry Gas Screening)",
        "oil": "GOR == 1 (Associated Gas / Oil)",
        "water": "Undefined",
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
        'log10': lambda x: np.where(np.asarray(x, dtype=float) > 0, np.log10(np.where(np.asarray(x, dtype=float) > 0, np.asarray(x, dtype=float), 1.0)), np.nan),
        'log': lambda x: np.where(np.asarray(x, dtype=float) > 0, np.log(np.where(np.asarray(x, dtype=float) > 0, np.asarray(x, dtype=float), 1.0)), np.nan),
        'sqrt': lambda x: np.where(np.asarray(x, dtype=float) >= 0, np.sqrt(np.where(np.asarray(x, dtype=float) >= 0, np.asarray(x, dtype=float), 0.0)), np.nan),
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
        # Common casing & aliases
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

    # Ensure TG fallback
    if 'TG' not in context:
        if 'TG_USED' in context:
            context['TG'] = context['TG_USED']
            context['tg'] = context['TG_USED']
        elif 'DERIVED_TG' in context:
            context['TG'] = context['DERIVED_TG']
            context['tg'] = context['DERIVED_TG']
        elif 'C1' in context and 'C2' in context and 'C3' in context:
            calc_tg = (
                context['C1'] + context['C2'] + context['C3'] +
                context.get('IC4', 0.0) + context.get('NC4', 0.0) +
                context.get('IC5', 0.0) + context.get('NC5', 0.0)
            )
            context['TG'] = calc_tg
            context['tg'] = calc_tg
            context['DERIVED_TG'] = calc_tg
            context['derived_tg'] = calc_tg

    # Specific aliases
    if 'RATIO_IC4' in context:
        context['Ratio_iC4'] = context['RATIO_IC4']
        context['R4_C1_IC4'] = context['RATIO_IC4']
    if 'RATIO_NC4' in context:
        context['Ratio_nC4'] = context['RATIO_NC4']
        context['R5_C1_NC4'] = context['RATIO_NC4']

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
    IC4 = out['IC4'].values.astype(float) if 'IC4' in out.columns else np.zeros(len(out))
    NC4 = out['NC4'].values.astype(float) if 'NC4' in out.columns else np.zeros(len(out))
    IC5 = out['IC5'].values.astype(float) if 'IC5' in out.columns else np.zeros(len(out))
    NC5 = out['NC5'].values.astype(float) if 'NC5' in out.columns else np.zeros(len(out))

    # ------------------------------------------------------------------
    #  Base Total Gas Volume (TG) — Indicator 7
    # ------------------------------------------------------------------
    derived_tg = C1 + C2 + C3 + IC4 + NC4 + IC5 + NC5

    if 'TG' in out.columns and out['TG'].notna().any() and (out['TG'] > 0).any():
        TG = out['TG'].values.astype(float)
        TG = np.where(TG > 0, TG, derived_tg)
    else:
        TG = derived_tg

    out['DERIVED_TG'] = derived_tg
    out['TG_USED']    = TG
    out['TG']         = TG

    # ------------------------------------------------------------------
    #  Pixler & Butane Ratios (Indicators 1–6)
    # ------------------------------------------------------------------
    # 1. R1 = C1 / C2
    out['R1_C1_C2']  = _safe_div(C1, C2)
    # 2. R2 = C1 / C3
    out['R2_C1_C3']  = _safe_div(C1, C3)
    # 3. R3 = C3 / C1
    out['R3_C3_C1']  = _safe_div(C3, C1)
    out['C3_C1']     = out['R3_C3_C1']
    # 4. R4 = C2 / C1
    out['R4_C2_C1']  = _safe_div(C2, C1)
    out['C2_C1']     = out['R4_C2_C1']
    # Legacy alias support
    out['R3_C2_C3']  = _safe_div(C2, C3)
    # 5. Ratio iC4 = C1 / iC4
    out['RATIO_IC4'] = _safe_div(C1, IC4)
    out['R4_C1_IC4'] = out['RATIO_IC4']
    # 6. Ratio nC4 = C1 / nC4
    out['RATIO_NC4'] = _safe_div(C1, NC4)
    out['R5_C1_NC4'] = out['RATIO_NC4']

    # ------------------------------------------------------------------
    #  Standard Petrophysical Indicators (Indicators 8–16)
    # ------------------------------------------------------------------
    # 8. Dryness Ratio (DR = C1 / TG)
    out['DRYNESS'] = _safe_div(C1, TG)

    # 9. Carbon-Weighted Density Index (Icarbon)
    carbon_weighted = C1 + 2*C2 + 3*C3 + 4*IC4 + 4*NC4 + 5*IC5 + 5*NC5
    out['CARBON_INDEX'] = _safe_div(TG, carbon_weighted)

    # 10. Haworth Wetness (Wh)
    heavy_sum = C2 + C3 + IC4 + NC4 + IC5 + NC5
    out['WH'] = _safe_div(heavy_sum, TG) * 100.0

    # 11. Haworth Balance (Bh)
    light = C1 + C2
    heavy_c3_plus = C3 + IC4 + NC4 + IC5 + NC5
    out['BH'] = _safe_div(light, heavy_c3_plus)

    # 12. Haworth Character (Ch)
    butane_pentane = IC4 + NC4 + IC5 + NC5
    out['CH'] = _safe_div(butane_pentane, C3)

    # 13. Composite GOW = ((C3 + iC4 + iC5 + nC4 + nC5) * TG) / (C1 + C2 + C3 + iC4 + iC5 + nC4 + nC5)
    out['GOW'] = _safe_div(heavy_c3_plus * TG, derived_tg)

    # 14. GOW No-TG = (C3 + iC4 + iC5 + nC4 + nC5) / (C1 + C2 + C3 + iC4 + iC5 + nC4 + nC5)
    out['GOW_NOTG'] = _safe_div(heavy_c3_plus, derived_tg)

    # 15. Wetness-Balance Score (WBS)
    Bh = out['BH'].values.astype(float)
    Wh = out['WH'].values.astype(float)
    with np.errstate(divide='ignore', invalid='ignore'):
        log_bh  = np.where(Bh > 0, np.log10(Bh), np.nan)
        log_wh  = np.where(Wh > 0, np.log10(Wh), np.nan)
        wbs = (log_bh - 0.903) / 2.097 - (log_wh / 2.0)
    out['WBS'] = wbs

    # 16. Gas-Oil Ratio (GOR) Screening
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
