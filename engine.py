"""
Petrophysical Engine — Deterministic Indicator Calculations & Zone Classification.

Implements all 16 derived indicators from the thesis methodology:
  Pixler ratios (R1–R5), Derived TG, Dryness, Carbon Index (TG Sum),
  Haworth ratios (Wh, Bh, Ch), GOW, GOW_noTG, WBS, GOR, and Zone Classification.

Every formula is an explicit, auditable physics equation — no black-box ML.
"""

# pyrefly: ignore [missing-import]
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
        "non_bearing": "C1 < 500",
    },
    "WH": {
        "name": "Haworth Wetness Ratio (Wh)",
        "expr": "((C2 + C3 + IC4 + NC4 + IC5 + NC5) / TG) * 100.0",
        "gas": "0.5 <= Wh < 17.5",
        "oil": "17.5 <= Wh <= 40.0",
        "non_bearing": "Wh < 0.5 or Wh == 0",
    },
    "BH": {
        "name": "Haworth Balance Ratio (Bh)",
        "expr": "(C1 + C2) / (C3 + IC4 + NC4 + IC5 + NC5)",
        "gas": "Bh >= 15.0",
        "oil": "0.5 <= Bh < 15.0",
        "non_bearing": "Bh == 0 or Undefined",
    },
    "CH": {
        "name": "Haworth Character Ratio (Ch)",
        "expr": "(IC4 + NC4 + IC5 + NC5) / C3",
        "gas": "0 < Ch < 0.5",
        "oil": "Ch >= 0.5",
        "non_bearing": "Ch == 0",
    },
    "R1_C1_C2": {
        "name": "Pixler R1 (C1 / C2)",
        "expr": "C1 / C2",
        "gas": "R1 >= 15.0",
        "oil": "2.0 <= R1 < 15.0",
        "non_bearing": "R1 == 0 or Undefined",
    },
    "R2_C1_C3": {
        "name": "Pixler R2 (C1 / C3)",
        "expr": "C1 / C3",
        "gas": "R2 > 30.0",
        "oil": "4.0 <= R2 <= 30.0",
        "non_bearing": "R2 == 0",
    },
    "R3_C3_C1": {
        "name": "Pixler R3 (C3 / C1)",
        "expr": "C3 / C1",
        "gas": "0 < R3 < 0.033",
        "oil": "0.033 <= R3 <= 0.25",
        "non_bearing": "R3 == 0",
    },
    "R4_C2_C1": {
        "name": "Pixler R4 (C2 / C1)",
        "expr": "C2 / C1",
        "gas": "0 < R4 < 0.067",
        "oil": "0.067 <= R4 <= 0.50",
        "non_bearing": "R4 == 0",
    },
    "RATIO_IC4": {
        "name": "Expanded Ratio iC4 (C1 / iC4)",
        "expr": "C1 / IC4",
        "gas": "Ratio_iC4 > 150.0",
        "oil": "15.0 <= Ratio_iC4 <= 150.0",
        "non_bearing": "Ratio_iC4 == 0",
    },
    "RATIO_NC4": {
        "name": "Expanded Ratio nC4 (C1 / nC4)",
        "expr": "C1 / NC4",
        "gas": "Ratio_nC4 > 100.0",
        "oil": "10.0 <= Ratio_nC4 <= 100.0",
        "non_bearing": "Ratio_nC4 == 0",
    },
    "TG": {
        "name": "Total Gas Volume (TG)",
        "expr": "C1 + C2 + C3 + IC4 + NC4 + IC5 + NC5",
        "gas": "TG >= 1500",
        "oil": "500 <= TG < 1500",
        "non_bearing": "TG < 500",
    },
    "DRYNESS": {
        "name": "Dryness Ratio (DR = C1 / TG)",
        "expr": "C1 / TG",
        "gas": "DR >= 0.85",
        "oil": "0.50 <= DR < 0.85",
        "non_bearing": "DR == 0 or No Gas",
    },
    "CARBON_INDEX": {
        "name": "Carbon Density Index (Icarbon)",
        "expr": "TG / (C1 + 2*C2 + 3*C3 + 4*IC4 + 4*NC4 + 5*IC5 + 5*NC5)",
        "gas": "Icarbon > 0.85",
        "oil": "0.40 <= Icarbon <= 0.85",
        "non_bearing": "Icarbon == 0",
    },
    "GOW": {
        "name": "Composite GOW",
        "expr": "((C3 + IC4 + NC4 + IC5 + NC5) * TG) / (C1 + C2 + C3 + IC4 + NC4 + IC5 + NC5)",
        "gas": "0 < GOW < 500",
        "oil": "500 <= GOW <= 15000",
        "non_bearing": "GOW == 0",
    },
    "GOW_NOTG": {
        "name": "GOW No-TG (Normalized Heavy Fraction)",
        "expr": "(C3 + IC4 + NC4 + IC5 + NC5) / (C1 + C2 + C3 + IC4 + NC4 + IC5 + NC5)",
        "gas": "0 < GOW_noTG < 0.015",
        "oil": "0.015 <= GOW_noTG <= 0.08",
        "non_bearing": "GOW_noTG == 0",
    },
    "WBS": {
        "name": "Wetness-Balance Score (WBS)",
        "expr": "(log10(BH) - 0.903) / 2.097 - log10(WH) / 2",
        "gas": "WBS > 0",
        "oil": "-0.5 <= WBS <= 0",
        "non_bearing": "WBS == 0 or Undefined",
    },
    "GOR": {
        "name": "Gas-Oil Ratio (GOR) Screening",
        "expr": "where((TG > 0.8) & (TG < 1.2) & (C1 > 2000), 0, 1)",
        "gas": "GOR == 0 (Dry Gas Screening)",
        "oil": "GOR == 1 (Associated Gas / Oil)",
        "non_bearing": "Undefined",
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


# ---------------------------------------------------------------------------
#  Default Fluid Classification Thresholds (Chapter 3 Standard)
# ---------------------------------------------------------------------------
DEFAULT_THRESHOLDS = {
    # Noise, C4/C5 Detection Limits and Pure Methane Cutoffs
    "tg_noise": 300.0,
    "c1_noise": 200.0,
    "c1_pure_gas": 2000.0,
    "c4_c5_detection_limit": 0.05,
    # Haworth Wetness (Wh) Limits (%)
    "wh_gas_min": 0.5,
    "wh_gas_max": 17.5,
    "wh_oil_max": 40.0,
    # Haworth Balance (Bh) Limits
    "bh_gas_min": 15.0,
    "bh_oil_min": 0.5,
    # Haworth Character (Ch) Cutoff
    "ch_gas_max": 0.5,
    # Dryness (DR = C1 / TG) Limits
    "dry_gas_min": 0.85,
    "dry_oil_min": 0.50,
    # Pixler R1 (C1 / C2) Limits
    "r1_gas_min": 15.0,
    "r1_oil_min": 2.0,
    # Pixler R4 (C2 / C1) Bump Limit for Oil
    "r4_oil_bump_min": 0.067,
    # Expanded Butane Ratio (C1 / nC4) Spike for Gas
    "ratio_nc4_gas_min": 100.0,
    # Wetness-Balance Score (WBS) Limits
    "wbs_gas_min": 0.0,
    "wbs_oil_min": -0.5,
    # Normalized Heavy Gas (GOW_noTG) Limits
    "gow_notg_gas_max": 0.015,
    "gow_notg_oil_max": 0.08,
}


def compute_all(df: pd.DataFrame, formula_overrides: dict = None, custom_columns: list = None, threshold_overrides: dict = None) -> pd.DataFrame:
    """
    Takes a cleaned DataFrame with columns:
        DEPTH, C1, C2, C3, IC4, NC4, IC5, NC5 (and optionally TG)
    Accepts optional formula_overrides, custom_columns, and threshold_overrides.
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
    out['ZONE'] = _classify_zones(out, thresholds=threshold_overrides)

    return out


# ---------------------------------------------------------------------------
#  Majority-vote zone classifier with configurable threshold limits
# ---------------------------------------------------------------------------

def _classify_zones(df: pd.DataFrame, thresholds: dict = None) -> pd.Series:
    """
    Applies rule-based expert decision logic per depth row matching Chapter 3 criteria:
    Three Facies Classes: Gas, Oil, Non-Bearing (Water dropped per user instruction).
    
    Rules:
      1. Both Oil and Gas strictly require heavier hydrocarbon fractions (iC4, nC4, iC5, nC5) > 0.05 ppm.
      2. If all hydrocarbon inputs or generated columns are zero/missing/undefined, that indicator casts
         a Non-Bearing vote (0 votes for Gas, 0 votes for Oil).
      3. Gas: Has iC5/nC5 pentanes, C1-C3 and TG spikes, normal Pixler R1 & R4, Ratio nC4 spike.
      4. Oil: Has iC4/nC4 but NO iC5/nC5, moderate TG, reverse spike in R1, bump in R4, heavier Wh/Bh.
      5. Non-Bearing: Background gas or absent C4-C5 data.
      6. Spatial continuity: Any connected pay package containing Gas is consolidated to solid Gas.
    """
    th = dict(DEFAULT_THRESHOLDS)
    if thresholds and isinstance(thresholds, dict):
        th.update(thresholds)

    tg_noise = float(th.get("tg_noise", 300.0))
    c1_noise = float(th.get("c1_noise", 200.0))
    det_lim = float(th.get("c4_c5_detection_limit", 0.05))

    wh_gas_min = float(th.get("wh_gas_min", 0.5))
    wh_gas_max = float(th.get("wh_gas_max", 17.5))
    wh_oil_max = float(th.get("wh_oil_max", 40.0))

    bh_gas_min = float(th.get("bh_gas_min", 15.0))
    bh_oil_min = float(th.get("bh_oil_min", 0.5))

    ch_gas_max = float(th.get("ch_gas_max", 0.5))

    dry_gas_min = float(th.get("dry_gas_min", 0.85))
    dry_oil_min = float(th.get("dry_oil_min", 0.50))

    r1_gas_min = float(th.get("r1_gas_min", 15.0))
    r1_oil_min = float(th.get("r1_oil_min", 2.0))

    r4_oil_bump_min = float(th.get("r4_oil_bump_min", 0.067))
    ratio_nc4_gas_min = float(th.get("ratio_nc4_gas_min", 100.0))

    wbs_gas_min = float(th.get("wbs_gas_min", 0.0))
    wbs_oil_min = float(th.get("wbs_oil_min", -0.5))

    gow_notg_gas_max = float(th.get("gow_notg_gas_max", 0.015))
    gow_notg_oil_max = float(th.get("gow_notg_oil_max", 0.08))

    n = len(df)
    zones = []

    Wh       = df['WH'].values.astype(float) if 'WH' in df.columns else np.full(n, np.nan)
    Bh       = df['BH'].values.astype(float) if 'BH' in df.columns else np.full(n, np.nan)
    Ch       = df['CH'].values.astype(float) if 'CH' in df.columns else np.full(n, np.nan)
    Wbs      = df['WBS'].values.astype(float) if 'WBS' in df.columns else np.full(n, np.nan)
    Dry      = df['DRYNESS'].values.astype(float) if 'DRYNESS' in df.columns else np.full(n, np.nan)
    Gow_notg = df['GOW_NOTG'].values.astype(float) if 'GOW_NOTG' in df.columns else np.full(n, np.nan)

    C1  = df['C1'].values.astype(float) if 'C1' in df.columns else np.zeros(n)
    C2  = df['C2'].values.astype(float) if 'C2' in df.columns else np.zeros(n)
    C3  = df['C3'].values.astype(float) if 'C3' in df.columns else np.zeros(n)
    IC4 = df['IC4'].values.astype(float) if 'IC4' in df.columns else np.zeros(n)
    NC4 = df['NC4'].values.astype(float) if 'NC4' in df.columns else np.zeros(n)
    IC5 = df['IC5'].values.astype(float) if 'IC5' in df.columns else np.zeros(n)
    NC5 = df['NC5'].values.astype(float) if 'NC5' in df.columns else np.zeros(n)

    if 'DERIVED_TG' in df.columns:
        derived_tg = df['DERIVED_TG'].values.astype(float)
    elif 'TG' in df.columns:
        derived_tg = df['TG'].values.astype(float)
    else:
        derived_tg = C1 + C2 + C3 + IC4 + NC4 + IC5 + NC5

    for i in range(n):
        tg = derived_tg[i]
        c1 = C1[i]
        c2 = C2[i]
        c3 = C3[i]
        ic4 = IC4[i]
        nc4 = NC4[i]
        ic5 = IC5[i]
        nc5 = NC5[i]

        # 1. Base Hydrocarbon Continuity Gate:
        # If C1, C2, or C3 is missing, NaN, or <= 0 -> Non-Bearing (bypasses voting)
        if (c1 <= 0 or c2 <= 0 or c3 <= 0 or not np.isfinite(c1) or not np.isfinite(c2) or not np.isfinite(c3)):
            zones.append("Non-Bearing")
            continue

        # 2. Background Noise / Baseline Cutoff:
        if (tg < tg_noise and c1 < c1_noise):
            zones.append("Non-Bearing")
            continue

        # 3. Check presence of Butanes (iC4, nC4) and Pentanes (iC5, nC5)
        has_ic4 = (ic4 > det_lim) and np.isfinite(ic4)
        has_nc4 = (nc4 > det_lim) and np.isfinite(nc4)
        has_ic5 = (ic5 > det_lim) and np.isfinite(ic5)
        has_nc5 = (nc5 > det_lim) and np.isfinite(nc5)

        has_c4 = has_ic4 or has_nc4
        has_c5 = has_ic5 or has_nc5

        # STRICT RULE: Must have ic4, nc4, ic5, or nc5 data present to assign Gas or Oil.
        # If all C4 & C5 channels are missing / zero / below detection limit -> Non-Bearing
        if not has_c4 and not has_c5:
            zones.append("Non-Bearing")
            continue

        gas_votes = 0
        oil_votes = 0

        # --- Rule 1: Hydrocarbon Speciation (iC4, nC4, iC5, nC5) ---
        if has_c4 and not has_c5:
            # Classic Oil fingerprint: present iC4/nC4, but absence of iC5/nC5
            oil_votes += 4
        elif has_c5:
            # Gas fingerprint: includes light pentane traces (iC5 and/or nC5)
            gas_votes += 3

        # Special case: nothing in ic4 sometimes, but spike in nc4 ratio
        if ic4 <= det_lim and nc4 > det_lim and c1 > 0:
            r_nc4_check = c1 / nc4
            if r_nc4_check >= ratio_nc4_gas_min:
                gas_votes += 1

        # --- Rule 2: C1, C2, C3 Spike & TG Spike ---
        if c1 >= 1000 and c2 > 0 and c3 > 0:
            gas_votes += 2
        if tg >= 1500:
            gas_votes += 2
        elif 0 < tg < 1500:
            oil_votes += 1

        # --- Rule 3: Pixler R1 (C1/C2) & Pixler R4 (C2/C1 Bump) ---
        # If c2 <= 0 or c1 <= 0, value is 0/undefined -> Non-Bearing (0 votes)
        if c2 > 0 and c1 > 0:
            r1 = c1 / c2
            r4 = c2 / c1
            if r1 >= r1_gas_min and r4 < r4_oil_bump_min:
                # Normal Gas trend for R1 and R4
                gas_votes += 2
            elif r1_oil_min <= r1 < r1_gas_min:
                # Reverse spike in R1 -> Oil
                oil_votes += 2

            if r4 >= r4_oil_bump_min:
                # Bump in R4 (C2/C1) -> Oil
                oil_votes += 2

        # --- Rule 4: Spike in Ratio nC4 (C1 / nC4) ---
        # If nc4 <= 0, value is 0 -> Non-Bearing (0 votes)
        if nc4 > 0 and c1 > 0:
            r_nc4 = c1 / nc4
            if r_nc4 >= ratio_nc4_gas_min:
                gas_votes += 2

        # --- Rule 5: Haworth Wetness (Wh) & Wh% Spike ---
        # If wh <= 0 or NaN -> Non-Bearing (0 votes)
        wh = Wh[i]
        if not np.isnan(wh) and wh > 0:
            if wh_gas_min <= wh < wh_gas_max:
                # Active Wh% spike for Gas
                gas_votes += 2
            elif wh_gas_max <= wh <= wh_oil_max:
                oil_votes += 2

        # --- Rule 6: Haworth Balance (Bh) Reverse Dip ---
        # If bh <= 0 or NaN -> Non-Bearing (0 votes)
        bh = Bh[i]
        if not np.isnan(bh) and bh > 0:
            if bh >= bh_gas_min:
                gas_votes += 2
            elif bh_oil_min <= bh < bh_gas_min:
                oil_votes += 2

        # --- Rule 7: Haworth Character (Ch) Spike ---
        # If ch <= 0 or NaN -> Non-Bearing (0 votes)
        ch = Ch[i]
        if not np.isnan(ch) and ch > 0:
            if ch < ch_gas_max:
                gas_votes += 1
            else:
                oil_votes += 1

        # --- Rule 8: Dryness Ratio (C1 / TG) ---
        # If dry <= 0 or NaN or c1 <= 0 or tg <= 0 -> Non-Bearing (0 votes)
        dry = Dry[i]
        if not np.isnan(dry) and dry > 0 and c1 > 0 and tg > 0:
            if dry >= dry_gas_min:
                gas_votes += 1
            elif dry >= dry_oil_min:
                oil_votes += 1

        # --- Rule 9: Normalized Heavy Gas (GOW_noTG) ---
        # If gow_n <= 0 or NaN -> Non-Bearing (0 votes)
        gow_n = Gow_notg[i]
        if not np.isnan(gow_n) and gow_n > 0:
            if gow_n < gow_notg_gas_max:
                gas_votes += 1
            elif gow_n <= gow_notg_oil_max:
                oil_votes += 1

        # --- Rule 10: Wetness-Balance Score (WBS) ---
        # If wbs == 0 or NaN -> Non-Bearing (0 votes)
        wbs = Wbs[i]
        if not np.isnan(wbs) and np.isfinite(wbs) and wbs != 0.0:
            if wbs > wbs_gas_min:
                gas_votes += 1
            elif wbs >= wbs_oil_min:
                oil_votes += 1

        # --- Decision matrix (Gas vs Oil vs Non-Bearing) ---
        if gas_votes > oil_votes and gas_votes > 0:
            zones.append("Gas")
        elif oil_votes > gas_votes and oil_votes > 0:
            zones.append("Oil")
        elif gas_votes == oil_votes and gas_votes > 0:
            if has_c5:
                zones.append("Gas")
            else:
                zones.append("Oil")
        else:
            zones.append("Non-Bearing")

    # -----------------------------------------------------------------------
    # Spatial Cluster & Neighbor Rule:
    # If an active continuous hydrocarbon package (contiguous non-"Non-Bearing" intervals)
    # contains any "Gas" prediction, then ALL "Oil" predictions in that same contiguous
    # package are switched to "Gas" regardless of individual point votes.
    # -----------------------------------------------------------------------
    adjusted_zones = list(zones)
    n_pts = len(adjusted_zones)

    # 1. Cluster-level propagation: any continuous pay package with Gas becomes solid Gas
    start = None
    for i in range(n_pts):
        if adjusted_zones[i] in ("Gas", "Oil"):
            if start is None:
                start = i
        else:
            if start is not None:
                end = i  # segment is start..end-1
                cluster = adjusted_zones[start:end]
                if "Gas" in cluster:
                    for k in range(start, end):
                        if adjusted_zones[k] == "Oil":
                            adjusted_zones[k] = "Gas"
                start = None
    if start is not None:
        cluster = adjusted_zones[start:n_pts]
        if "Gas" in cluster:
            for k in range(start, n_pts):
                if adjusted_zones[k] == "Oil":
                    adjusted_zones[k] = "Gas"

    # 2. Secondary neighborhood smoothing pass (within +/-3 samples)
    for i in range(n_pts):
        if adjusted_zones[i] == "Oil":
            w_start = max(0, i - 3)
            w_end = min(n_pts, i + 4)
            surrounding = adjusted_zones[w_start:w_end]
            if "Gas" in surrounding:
                adjusted_zones[i] = "Gas"

    return pd.Series(adjusted_zones, index=df.index)
