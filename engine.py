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

def _safe_div(numerator, denominator):
    """Element-wise division that returns NaN where denominator is zero."""
    with np.errstate(divide='ignore', invalid='ignore'):
        result = np.where(denominator != 0, numerator / denominator, np.nan)
    return result


# ---------------------------------------------------------------------------
#  Core computation
# ---------------------------------------------------------------------------

def compute_all(df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes a cleaned DataFrame with columns:
        DEPTH, C1, C2, C3, IC4, NC4, IC5, NC5  (and optionally TG)
    Returns a new DataFrame with all original columns plus 16 derived columns.
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
    #  1–5. Pixler Hydrocarbon Ratios
    # ------------------------------------------------------------------
    out['R1_C1_C2']  = _safe_div(C1, C2)
    out['R2_C1_C3']  = _safe_div(C1, C3)
    out['R3_C2_C3']  = _safe_div(C2, C3)
    out['R4_C1_IC4'] = _safe_div(C1, IC4)
    out['R5_C1_NC4'] = _safe_div(C1, NC4)

    # ------------------------------------------------------------------
    #  6. Total Gas Volume — use uploaded TG if available, else derive
    # ------------------------------------------------------------------
    derived_tg = C1 + C2 + C3 + IC4 + NC4 + IC5 + NC5

    if 'TG' in out.columns and out['TG'].notna().any() and (out['TG'] > 0).any():
        TG = out['TG'].values.astype(float)
        # Where TG is zero/missing, fall back to derived
        TG = np.where(TG > 0, TG, derived_tg)
    else:
        TG = derived_tg

    out['DERIVED_TG'] = derived_tg
    out['TG_USED']    = TG

    # ------------------------------------------------------------------
    #  7. Dryness Ratio
    # ------------------------------------------------------------------
    out['DRYNESS'] = _safe_div(C1, TG)

    # ------------------------------------------------------------------
    #  8. Carbon Index (TG Sum)
    # ------------------------------------------------------------------
    carbon_weighted = C1 + 2*C2 + 3*C3 + 4*IC4 + 4*NC4 + 5*IC5 + 5*NC5
    out['CARBON_INDEX'] = _safe_div(derived_tg, carbon_weighted)

    # ------------------------------------------------------------------
    #  9. Expanded Wetness Ratio (Wh)
    # ------------------------------------------------------------------
    heavy_sum = C2 + C3 + IC4 + NC4 + IC5 + NC5
    out['WH'] = _safe_div(heavy_sum, TG) * 100.0

    # ------------------------------------------------------------------
    # 10. Expanded Balance Ratio (Bh)
    # ------------------------------------------------------------------
    light = C1 + C2
    heavy = C3 + IC4 + NC4 + IC5 + NC5
    out['BH'] = _safe_div(light, heavy)

    # ------------------------------------------------------------------
    # 11. Expanded Character Ratio (Ch)
    # ------------------------------------------------------------------
    butane_pentane = IC4 + NC4 + IC5 + NC5
    out['CH'] = _safe_div(butane_pentane, C3)

    # ------------------------------------------------------------------
    # 12. GOW indicator
    # ------------------------------------------------------------------
    out['GOW'] = heavy * TG

    # ------------------------------------------------------------------
    # 13. GOW without TG multiplier
    # ------------------------------------------------------------------
    out['GOW_NOTG'] = _safe_div(heavy, TG)

    # ------------------------------------------------------------------
    # 14. Wetness-Balance Score (WBS)
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # 15. GOR flag (simplified Gas-Oil Ratio index)
    # ------------------------------------------------------------------
    gor = np.where((TG > 0.8) & (TG < 1.2) & (C1 > 2000), 0, 1)
    out['GOR'] = gor

    # ------------------------------------------------------------------
    # 16. Zone Classification — majority-vote expert matrix
    # ------------------------------------------------------------------
    out['ZONE'] = _classify_zones(out)

    return out


# ---------------------------------------------------------------------------
#  Majority-vote zone classifier
# ---------------------------------------------------------------------------

def _classify_zones(df: pd.DataFrame) -> pd.Series:
    """
    Applies rule-based expert matrix per depth row.
    Each rule casts a 'Gas', 'Oil', or 'Water' vote.
    Majority wins; ties broken: Gas > Oil > Water.

    A row with ALL gas components == 0 (no show) is labelled "No Show".
    """
    n = len(df)
    zones = []

    Wh  = df['WH'].values
    Bh  = df['BH'].values
    Ch  = df['CH'].values
    Wbs = df['WBS'].values
    Dry = df['DRYNESS'].values
    Gor = df['GOR'].values
    C1  = df['C1'].values
    C2  = df['C2'].values
    C3  = df['C3'].values
    IC4 = df['IC4'].values
    NC4 = df['NC4'].values
    IC5 = df['IC5'].values
    NC5 = df['NC5'].values

    for i in range(n):
        # If there are absolutely no gas components, mark "No Show"
        total_components = C2[i] + C3[i] + IC4[i] + NC4[i] + IC5[i] + NC5[i]
        if total_components == 0 and C1[i] == 0:
            zones.append("No Show")
            continue

        gas_votes = 0
        oil_votes = 0
        water_votes = 0

        # --- Wetness rule ---
        wh = Wh[i]
        if not np.isnan(wh):
            if wh < 17.5:
                gas_votes += 1
            elif wh > 80.0:
                # Extremely wet — likely water-bearing
                water_votes += 1
            else:
                oil_votes += 1

        # --- Balance rule ---
        bh = Bh[i]
        if not np.isnan(bh):
            if bh > 100:
                gas_votes += 1
            elif bh < 2.0:
                # Very low balance — water indicator
                water_votes += 1
            else:
                oil_votes += 1

        # --- Character rule ---
        ch = Ch[i]
        if not np.isnan(ch):
            if ch < 0.5:
                gas_votes += 1
            else:
                oil_votes += 1

        # --- WBS rule ---
        wbs = Wbs[i]
        if not np.isnan(wbs):
            if wbs > 0:
                gas_votes += 1
            elif wbs < -0.5:
                # Strongly negative WBS — water indicator
                water_votes += 1
            else:
                oil_votes += 1

        # --- Dryness rule ---
        dry = Dry[i]
        if not np.isnan(dry):
            if dry > 0.95:
                gas_votes += 1
            elif dry < 0.5:
                # Very low dryness — water indicator
                water_votes += 1
            else:
                oil_votes += 1

        # --- GOR rule ---
        if Gor[i] == 0:
            gas_votes += 1

        # --- Determine winner ---
        if total_components == 0:
            # Only C1 present, no heavier gases → dry gas
            zones.append("Gas")
        else:
            # Pick the highest vote count; ties broken Gas > Oil > Water
            votes = {"Gas": gas_votes, "Oil": oil_votes, "Water": water_votes}
            winner = max(votes, key=lambda k: (votes[k], -list(votes.keys()).index(k)))
            zones.append(winner)

    return pd.Series(zones, index=df.index)
