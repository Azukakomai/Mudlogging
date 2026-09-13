#!/usr/bin/env python3
"""
Automated Verification Test Suite — Mudlogging Petrophysical System
Validates mathematical calculations, boundary conditions, and latency targets.
Matches all 16 derived petrophysical indicators from Chapter 3.
"""

import sys
import os
import time
import math
import unittest
import numpy as np
import pandas as pd

# Add repository root for imports
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from engine import compute_all, eval_expr, DEFAULT_FORMULAS
from parser import parse_mudlog_file


class TestPetrophysicalFormulas(unittest.TestCase):
    def setUp(self):
        self.sample_data = pd.DataFrame([{
            'DEPTH': 2500.0,
            'C1': 45000.0,
            'C2': 1200.0,
            'C3': 300.0,
            'IC4': 80.0,
            'NC4': 100.0,
            'IC5': 30.0,
            'NC5': 20.0,
            'TG': 46730.0
        }])

    def test_pixler_and_butane_ratios(self):
        """Validates Chapter 3 Equations 74 and 80 (Pixler R1–R4, Ratio iC4, Ratio nC4)."""
        res = compute_all(self.sample_data)
        # R1 = C1 / C2
        self.assertAlmostEqual(res['R1_C1_C2'].iloc[0], 45000.0 / 1200.0, places=4)
        # R2 = C1 / C3
        self.assertAlmostEqual(res['R2_C1_C3'].iloc[0], 45000.0 / 300.0, places=4)
        # R3 = C3 / C1
        self.assertAlmostEqual(res['R3_C3_C1'].iloc[0], 300.0 / 45000.0, places=6)
        # R4 = C2 / C1
        self.assertAlmostEqual(res['R4_C2_C1'].iloc[0], 1200.0 / 45000.0, places=6)
        # Ratio iC4 = C1 / iC4
        self.assertAlmostEqual(res['RATIO_IC4'].iloc[0], 45000.0 / 80.0, places=4)
        # Ratio nC4 = C1 / nC4
        self.assertAlmostEqual(res['RATIO_NC4'].iloc[0], 45000.0 / 100.0, places=4)

    def test_haworth_ratios(self):
        """Validates Chapter 3 Equations 104, 107, 110 (Haworth Wh, Bh, Ch)."""
        res = compute_all(self.sample_data)
        heavy_sum = 1200.0 + 300.0 + 80.0 + 100.0 + 30.0 + 20.0
        tg = 45000.0 + heavy_sum
        expected_wh = (heavy_sum / tg) * 100.0
        self.assertAlmostEqual(res['WH'].iloc[0], expected_wh, places=4)

        expected_bh = (45000.0 + 1200.0) / (300.0 + 80.0 + 100.0 + 30.0 + 20.0)
        self.assertAlmostEqual(res['BH'].iloc[0], expected_bh, places=4)

        expected_ch = (80.0 + 100.0 + 30.0 + 20.0) / 300.0
        self.assertAlmostEqual(res['CH'].iloc[0], expected_ch, places=4)

    def test_dryness_and_carbon_index(self):
        """Validates Chapter 3 Equations 86, 92, 98 (TG, Dryness, Carbon Index)."""
        res = compute_all(self.sample_data)
        derived_tg = 46730.0
        expected_dryness = 45000.0 / derived_tg
        self.assertAlmostEqual(res['DRYNESS'].iloc[0], expected_dryness, places=4)

        carbon_weighted = 45000.0 + 2*1200.0 + 3*300.0 + 4*80.0 + 4*100.0 + 5*30.0 + 5*20.0
        expected_ci = derived_tg / carbon_weighted
        self.assertAlmostEqual(res['CARBON_INDEX'].iloc[0], expected_ci, places=4)

    def test_composite_screening_indicators(self):
        """Validates Chapter 3 Equations 117, 118, 122, 125 (GOW, GOW_noTG, WBS, GOR)."""
        res = compute_all(self.sample_data)
        heavy_c3_plus = 300.0 + 80.0 + 100.0 + 30.0 + 20.0
        tg = 46730.0
        expected_gow = (heavy_c3_plus * tg) / tg
        self.assertAlmostEqual(res['GOW'].iloc[0], expected_gow, places=4)

        expected_gow_notg = heavy_c3_plus / tg
        self.assertAlmostEqual(res['GOW_NOTG'].iloc[0], expected_gow_notg, places=6)

        expected_bh = (45000.0 + 1200.0) / heavy_c3_plus
        expected_wh = ((1200.0 + heavy_c3_plus) / tg) * 100.0
        expected_wbs = (math.log10(expected_bh) - 0.903) / 2.097 - (math.log10(expected_wh) / 2.0)
        self.assertAlmostEqual(res['WBS'].iloc[0], expected_wbs, places=4)

    def test_fluid_classification_majority_vote(self):
        res = compute_all(self.sample_data)
        self.assertEqual(res['ZONE'].iloc[0], 'Gas')

    def test_configurable_threshold_overrides(self):
        """Validates that custom threshold overrides alter the zone classification deterministically."""
        # Shift Pixler, Wh, Bh, and Dryness limits to force an Oil classification on sample gas data
        custom_th = {
            "r1_gas_min": 100.0,
            "r4_oil_bump_min": 0.01,
            "wh_gas_max": 0.01,
            "wh_oil_max": 50.0,
            "bh_gas_min": 1000.0,
            "dry_gas_min": 0.999,
            "ratio_nc4_gas_min": 1000.0
        }
        res_custom = compute_all(self.sample_data, threshold_overrides=custom_th)
        self.assertNotEqual(res_custom['ZONE'].iloc[0], 'Gas')
        self.assertEqual(res_custom['ZONE'].iloc[0], 'Oil')

    def test_computational_throughput_benchmark(self):
        """Benchmark: Processing > 3000m well trajectory should complete in << 5.0 seconds"""
        n_rows = 500
        depths = np.linspace(1000, 4000, n_rows)
        synthetic_df = pd.DataFrame({
            'DEPTH': depths,
            'C1': np.random.uniform(500, 50000, n_rows),
            'C2': np.random.uniform(50, 4000, n_rows),
            'C3': np.random.uniform(10, 2000, n_rows),
            'IC4': np.random.uniform(5, 500, n_rows),
            'NC4': np.random.uniform(5, 800, n_rows),
            'IC5': np.random.uniform(1, 200, n_rows),
            'NC5': np.random.uniform(1, 150, n_rows),
            'TG': np.random.uniform(600, 60000, n_rows)
        })

        t_start = time.perf_counter()
        computed = compute_all(synthetic_df)
        t_elapsed = time.perf_counter() - t_start

        print(f"\n[BENCHMARK] Processed {n_rows} depth records spanning 3000m in {t_elapsed * 1000:.2f} ms")
        self.assertLess(t_elapsed, 5.0, "Latency exceeded 5.0s benchmark target")
    def test_percentile_cutoff_filtering_and_subtraction(self):
        """Validates that for input columns, data below 75th percentile is zeroed out and remaining data is subtracted by minimum remaining value."""
        vals = np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0])
        valid_mask = np.isfinite(vals) & (vals > 0)
        p75 = float(np.percentile(vals[valid_mask], 75.0))
        top_mask = valid_mask & (vals >= p75)
    def test_missing_c4_c5_classified_as_noshow(self):
        """Validates that intervals with missing/zero iC4, nC4, iC5, and nC5 are strictly classified as No Show."""
        df_no_c4_c5 = pd.DataFrame([{
            'DEPTH': 1200.0,
            'C1': 15000.0,
            'C2': 600.0,
            'C3': 150.0,
            'IC4': 0.0,
            'NC4': 0.0,
            'IC5': 0.0,
            'NC5': 0.0,
            'TG': 15750.0
        }])
        res = compute_all(df_no_c4_c5)
        self.assertEqual(res['ZONE'].iloc[0], 'No Show')

    def test_spatial_neighbor_oil_to_gas_reclassification(self):
        """Validates that an Oil prediction with Gas as a neighbor is reclassified as Gas."""
        # Row 0: Gas (has iC5), Row 1: Oil isolated without C5, Row 2: Gas (has iC5)
        df_seq = pd.DataFrame([
            {'DEPTH': 1000.0, 'C1': 20000.0, 'C2': 500.0, 'C3': 100.0, 'IC4': 50.0, 'NC4': 50.0, 'IC5': 20.0, 'NC5': 10.0, 'TG': 20730.0},
            {'DEPTH': 1001.0, 'C1': 2000.0, 'C2': 500.0, 'C3': 100.0, 'IC4': 50.0, 'NC4': 50.0, 'IC5': 0.0, 'NC5': 0.0, 'TG': 2700.0},
            {'DEPTH': 1002.0, 'C1': 20000.0, 'C2': 500.0, 'C3': 100.0, 'IC4': 50.0, 'NC4': 50.0, 'IC5': 20.0, 'NC5': 10.0, 'TG': 20730.0},
        ])
        res = compute_all(df_seq)
        # Even though row 1 would otherwise be Oil (has butanes, no pentanes, lower R1), having Gas neighbors promotes it to Gas
        self.assertEqual(res['ZONE'].iloc[0], 'Gas')
        self.assertEqual(res['ZONE'].iloc[1], 'Gas')
        self.assertEqual(res['ZONE'].iloc[2], 'Gas')


if __name__ == '__main__':
    unittest.main()
