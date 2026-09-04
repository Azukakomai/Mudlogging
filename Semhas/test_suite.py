#!/usr/bin/env python3
"""
Automated Verification Test Suite — Mudlogging Petrophysical System
Validates mathematical calculations, boundary conditions, and latency targets.
"""

import sys
import os
import time
import math
import unittest
import numpy as np
import pandas as pd

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import compute_all
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

    def test_pixler_ratios(self):
        res = compute_all(self.sample_data)
        self.assertAlmostEqual(res['R1_C1_C2'].iloc[0], 45000.0 / 1200.0, places=4)
        self.assertAlmostEqual(res['R2_C1_C3'].iloc[0], 45000.0 / 300.0, places=4)
        self.assertAlmostEqual(res['R3_C2_C3'].iloc[0], 1200.0 / 300.0, places=4)
        self.assertAlmostEqual(res['R4_C1_IC4'].iloc[0], 45000.0 / 80.0, places=4)
        self.assertAlmostEqual(res['R5_C1_NC4'].iloc[0], 45000.0 / 100.0, places=4)

    def test_haworth_ratios(self):
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
        res = compute_all(self.sample_data)
        derived_tg = 46730.0
        expected_dryness = 45000.0 / derived_tg
        self.assertAlmostEqual(res['DRYNESS'].iloc[0], expected_dryness, places=4)

        carbon_weighted = 45000.0 + 2*1200.0 + 3*300.0 + 4*80.0 + 4*100.0 + 5*30.0 + 5*20.0
        expected_ci = derived_tg / carbon_weighted
        self.assertAlmostEqual(res['CARBON_INDEX'].iloc[0], expected_ci, places=4)

    def test_fluid_classification_majority_vote(self):
        res = compute_all(self.sample_data)
        self.assertEqual(res['ZONE'].iloc[0], 'Gas')

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
        self.assertEqual(len(computed), n_rows)


if __name__ == '__main__':
    unittest.main()
