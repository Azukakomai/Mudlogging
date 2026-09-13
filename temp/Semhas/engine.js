/**
 * Petrophysical Calculation Engine (JavaScript Engine)
 * Replicates and extends engine.py with exact mathematical formulas and safe dynamic evaluation.
 */

class PetrophysicalEngine {
  /**
   * Safe division returning fallback (default 0 or NaN) when denominator is 0
   */
  static safeDiv(num, den, fallback = 0) {
    if (den === 0 || isNaN(den) || !isFinite(den)) return fallback;
    const res = num / den;
    return isFinite(res) ? res : fallback;
  }

  /**
   * Compute all 16 derived indicators and majority-vote fluid zone classification
   * @param {Array<Object>} rawData - Array of row objects with DEPTH, C1, C2, C3, IC4, NC4, IC5, NC5, optional TG
   * @param {Object} customFormulaOverrides - Optional overrides for formula expressions
   * @returns {Array<Object>} Processed rows with all indicators
   */
  static computeAll(rawData, customFormulaOverrides = {}) {
    if (!Array.isArray(rawData) || rawData.length === 0) return [];

    return rawData.map(row => {
      const depth = parseFloat(row.DEPTH || row.depth || row.MD || row.md || 0);
      const c1 = Math.max(0, parseFloat(row.C1 || row.c1 || 0));
      const c2 = Math.max(0, parseFloat(row.C2 || row.c2 || 0));
      const c3 = Math.max(0, parseFloat(row.C3 || row.c3 || 0));
      const ic4 = Math.max(0, parseFloat(row.IC4 || row.ic4 || row.iC4 || 0));
      const nc4 = Math.max(0, parseFloat(row.NC4 || row.nc4 || row.nC4 || 0));
      const ic5 = Math.max(0, parseFloat(row.IC5 || row.ic5 || row.iC5 || 0));
      const nc5 = Math.max(0, parseFloat(row.NC5 || row.nc5 || row.nC5 || 0));
      
      const derivedTG = c1 + c2 + c3 + ic4 + nc4 + ic5 + nc5;
      const rawTG = parseFloat(row.TG || row.tg || 0);
      const tgUsed = (rawTG > 0) ? rawTG : derivedTG;

      // 1-5: Pixler Ratios & Inverses
      const r1 = this.safeDiv(c1, c2, 0);
      const r2 = this.safeDiv(c1, c3, 0);
      const r3 = this.safeDiv(c2, c3, 0);
      const r4 = this.safeDiv(c1, ic4, 0);
      const r5 = this.safeDiv(c1, nc4, 0);
      const c2_c1 = this.safeDiv(c2, c1, 0);
      const c3_c1 = this.safeDiv(c3, c1, 0);

      // 6-7: Dryness & Carbon Density Index
      const dryness = this.safeDiv(c1, derivedTG, 0) * 100.0;
      const carbonWeighted = c1 + (2 * c2) + (3 * c3) + (4 * ic4) + (4 * nc4) + (5 * ic5) + (5 * nc5);
      const carbonIndex = this.safeDiv(derivedTG, carbonWeighted, 0);

      // 8-10: Haworth Ratios (Wh, Bh, Ch)
      const heavySum = c2 + c3 + ic4 + nc4 + ic5 + nc5;
      const wh = this.safeDiv(heavySum, derivedTG, 0) * 100.0;
      
      const light = c1 + c2;
      const heavy = c3 + ic4 + nc4 + ic5 + nc5;
      const bh = this.safeDiv(light, heavy, 0);

      const butanePentane = ic4 + nc4 + ic5 + nc5;
      const ch = this.safeDiv(butanePentane, c3, 0);

      // 11-14: Composite Indicators (GOW, GOW_noTG, WBS, GOR)
      const gow = heavy * derivedTG;
      const gowNoTG = this.safeDiv(heavy, derivedTG, 0);

      let wbs = 0;
      if (bh > 0 && wh > 0) {
        const logBh = Math.log10(bh);
        const logWh = Math.log10(wh);
        const log8 = Math.log10(8);
        const log1000 = Math.log10(1000);
        const log100 = Math.log10(100);
        wbs = ((logBh - log8) / (log1000 - log8)) - (logWh / log100);
      }

      const gor = (tgUsed > 0.8 && tgUsed < 1.2 && c1 > 2000) ? 0 : 1;

      // 15: Fluid Classification Matrix (Majority-Vote)
      const zone = this.classifyZone({
        c1, c2, c3, ic4, nc4, ic5, nc5, derivedTG, tgUsed,
        wh, bh, ch, dryness, r1, wbs, gor, gowNoTG, heavySum
      });

      const processed = {
        DEPTH: depth,
        MD: depth,
        C1: c1,
        C2: c2,
        C3: c3,
        IC4: ic4,
        NC4: nc4,
        IC5: ic5,
        NC5: nc5,
        DERIVED_TG: derivedTG,
        TG_USED: tgUsed,
        TG: tgUsed,
        R1_C1_C2: r1,
        R2_C1_C3: r2,
        R3_C2_C3: r3,
        R4_C1_IC4: r4,
        R5_C1_NC4: r5,
        C2_C1: c2_c1,
        C3_C1: c3_c1,
        DRYNESS: dryness,
        CARBON_INDEX: carbonIndex,
        WH: wh,
        BH: bh,
        CH: ch,
        GOW: gow,
        GOW_NOTG: gowNoTG,
        WBS: wbs,
        GOR: gor,
        ZONE: zone
      };

      // Evaluate any custom formula overrides
      for (const [key, expr] of Object.entries(customFormulaOverrides)) {
        if (expr) {
          try {
            processed[key] = this.evaluateExpression(expr, processed);
          } catch (e) {
            processed[key] = 0;
          }
        }
      }

      return processed;
    });
  }

  /**
   * Deterministic majority-vote fluid zone classifier matching thesis logic
   */
  static classifyZone(ctx) {
    const {
      c1, c2, derivedTG, wh, bh, ch, dryness, r1, wbs, gor, gowNoTG, heavySum
    } = ctx;

    // 1. Background Noise / Low Gas Cutoff
    if (derivedTG < 300 || c1 < 200) {
      return 'No Show';
    }

    // 2. Pure Methane (Zero Heavy Gas Intervals)
    if (heavySum === 0) {
      return (c1 >= 2000) ? 'Gas' : 'No Show';
    }

    let gasVotes = 0;
    let oilVotes = 0;
    let waterVotes = 0;

    // Indicator 1: Haworth Wetness (Wh)
    if (!isNaN(wh)) {
      if (wh < 0.5) {
        if (c1 < 2000) return 'No Show';
        gasVotes++;
      } else if (wh < 17.5) {
        gasVotes++;
      } else if (wh <= 40.0) {
        oilVotes++;
      } else {
        waterVotes++;
      }
    }

    // Indicator 2: Haworth Balance (Bh)
    if (!isNaN(bh)) {
      if (bh >= 15.0) gasVotes++;
      else if (bh >= 0.5) oilVotes++;
      else waterVotes++;
    }

    // Indicator 3: Haworth Character (Ch)
    if (!isNaN(ch)) {
      if (ch < 0.5) gasVotes++;
      else oilVotes++;
    }

    // Indicator 4: Dryness Ratio (C1 / TG)
    const dryDec = dryness / 100.0;
    if (!isNaN(dryDec)) {
      if (dryDec >= 0.85) gasVotes++;
      else if (dryDec >= 0.50) oilVotes++;
      else waterVotes++;
    }

    // Indicator 5: Pixler C1/C2 (R1)
    if (c2 > 0) {
      if (r1 >= 15.0) gasVotes++;
      else if (r1 >= 2.0) oilVotes++;
      else waterVotes++;
    }

    // Indicator 6: Wetness-Balance Score (WBS)
    if (!isNaN(wbs)) {
      if (wbs > 0) gasVotes++;
      else if (wbs >= -0.5) oilVotes++;
      else waterVotes++;
    }

    // Indicator 7: Gas-Oil Ratio Index (GOR)
    if (gor === 0) gasVotes++;

    // Indicator 8: Normalized Heavy Gas (GOW_noTG)
    if (!isNaN(gowNoTG)) {
      if (gowNoTG < 0.015) gasVotes++;
      else if (gowNoTG <= 0.08) oilVotes++;
      else waterVotes++;
    }

    // Tally Votes
    const votes = { Gas: gasVotes, Oil: oilVotes, Water: waterVotes };
    const maxV = Math.max(gasVotes, oilVotes, waterVotes);

    if (maxV === 0) return 'No Show';

    if (gasVotes === maxV) return 'Gas';
    if (oilVotes === maxV) return 'Oil';
    return 'Water';
  }

  /**
   * Safe Math Expression Evaluator
   * Supports operators: +, -, *, /, ^, %, parentheses, log10, ln, sqrt, abs, min, max
   */
  static evaluateExpression(expr, variables) {
    if (!expr || typeof expr !== 'string') return 0;

    // Sanitize and replace variables with numeric values
    let sanitized = expr
      .replace(/\s+/g, '')
      .replace(/log10\(/g, 'Math.log10(')
      .replace(/ln\(/g, 'Math.log(')
      .replace(/sqrt\(/g, 'Math.sqrt(')
      .replace(/abs\(/g, 'Math.abs(')
      .replace(/\^/g, '**');

    // Create a safe mapping of variables
    const scope = {
      C1: variables.C1 || 0,
      C2: variables.C2 || 0,
      C3: variables.C3 || 0,
      IC4: variables.IC4 || 0,
      iC4: variables.IC4 || 0,
      NC4: variables.NC4 || 0,
      nC4: variables.NC4 || 0,
      IC5: variables.IC5 || 0,
      iC5: variables.IC5 || 0,
      NC5: variables.NC5 || 0,
      nC5: variables.NC5 || 0,
      TG: variables.TG || variables.DERIVED_TG || 0,
      Wh: variables.WH || 0,
      WH: variables.WH || 0,
      Bh: variables.BH || 0,
      BH: variables.BH || 0,
      Ch: variables.CH || 0,
      CH: variables.CH || 0,
      WBS: variables.WBS || 0,
      GOW: variables.GOW || 0,
      Dryness: variables.DRYNESS || 0,
      DEPTH: variables.DEPTH || 0,
      MD: variables.DEPTH || 0
    };

    // Sort variable names by descending length so iC4 replaces before C4/C1
    const sortedKeys = Object.keys(scope).sort((a, b) => b.length - a.length);
    for (const key of sortedKeys) {
      const regex = new RegExp(`\\b${key}\\b`, 'g');
      sanitized = sanitized.replace(regex, `(${scope[key]})`);
    }

    // Validate characters to prevent arbitrary script execution
    if (!/^[0-9+\-*/().,% Math.log10Math.sqrtMath.absMath.log*]+$/.test(sanitized)) {
      throw new Error('Invalid mathematical expression');
    }

    try {
      const func = new Function(`return (${sanitized});`);
      const val = func();
      return isFinite(val) && !isNaN(val) ? val : 0;
    } catch (err) {
      return 0;
    }
  }

  /**
   * Generates realistic synthetic benchmark dataset matching Skripsi field well
   */
  static generateBenchmarkDataset(type = 'synthetic') {
    const rows = [];

    if (type === 'mahakam') {
      // Mahakam Basin: Gas dominant deltaic sand-shale sequences
      let depth = 2200;
      for (let i = 0; i < 90; i++) {
        depth += 12.5;
        const isGasPay = (depth >= 2420 && depth <= 2680);
        const mult = isGasPay ? 3.5 : 0.4;
        const baseGas = (Math.sin(i / 4.0) * 6000 + 15000) * mult;

        const c1 = Math.max(20, baseGas * 0.88 + Math.random() * 800);
        const c2 = Math.max(2, baseGas * 0.08 + Math.random() * 150);
        const c3 = Math.max(0.5, baseGas * 0.025 + Math.random() * 50);
        const ic4 = Math.max(0.1, baseGas * 0.008 + Math.random() * 20);
        const nc4 = Math.max(0.1, baseGas * 0.005 + Math.random() * 15);
        const ic5 = Math.max(0.05, baseGas * 0.0015 + Math.random() * 8);
        const nc5 = Math.max(0.05, baseGas * 0.0005 + Math.random() * 5);
        const tg = c1 + c2 + c3 + ic4 + nc4 + ic5 + nc5;

        rows.push({
          DEPTH: depth,
          C1: Math.round(c1),
          C2: Math.round(c2),
          C3: Math.round(c3),
          IC4: parseFloat(ic4.toFixed(1)),
          NC4: parseFloat(nc4.toFixed(1)),
          IC5: parseFloat(ic5.toFixed(1)),
          NC5: parseFloat(nc5.toFixed(1)),
          TG: Math.round(tg)
        });
      }
    } else if (type === 'northsea') {
      // North Sea: Volatile oil / condensate reservoir with high heavies
      let depth = 2800;
      for (let i = 0; i < 95; i++) {
        depth += 10.0;
        const isOilPay = (depth >= 2950 && depth <= 3240);
        const mult = isOilPay ? 2.8 : 0.5;
        const baseGas = (Math.cos(i / 5.0) * 5000 + 12000) * mult;

        const c1 = Math.max(15, baseGas * 0.48 + Math.random() * 600);
        const c2 = Math.max(5, baseGas * 0.22 + Math.random() * 300);
        const c3 = Math.max(3, baseGas * 0.16 + Math.random() * 200);
        const ic4 = Math.max(1, baseGas * 0.06 + Math.random() * 90);
        const nc4 = Math.max(1, baseGas * 0.05 + Math.random() * 80);
        const ic5 = Math.max(0.2, baseGas * 0.02 + Math.random() * 30);
        const nc5 = Math.max(0.2, baseGas * 0.01 + Math.random() * 25);
        const tg = c1 + c2 + c3 + ic4 + nc4 + ic5 + nc5;

        rows.push({
          DEPTH: depth,
          C1: Math.round(c1),
          C2: Math.round(c2),
          C3: Math.round(c3),
          IC4: parseFloat(ic4.toFixed(1)),
          NC4: parseFloat(nc4.toFixed(1)),
          IC5: parseFloat(ic5.toFixed(1)),
          NC5: parseFloat(nc5.toFixed(1)),
          TG: Math.round(tg)
        });
      }
    } else {
      // Default Skripsi Benchmark (85 rows with gas and oil pay intervals)
      let depth = 1800;
      for (let i = 0; i < 85; i++) {
        depth += 15;
        const isPayzone = (depth >= 2100 && depth <= 2450) || (depth >= 2700 && depth <= 2880);
        const isGasZone = (depth >= 2100 && depth <= 2450);
        const mult = isPayzone ? 2.8 : 0.6;
        const baseGas = (Math.sin(i / 5.0) * 8000.0 + 12000.0) * mult;

        let c1, c2, c3, ic4, nc4, ic5, nc5;
        if (isGasZone) {
          c1 = Math.max(10, baseGas * 0.78 + Math.random() * 1200);
          c2 = Math.max(1, baseGas * 0.12 + Math.random() * 300);
          c3 = Math.max(0.5, baseGas * 0.06 + Math.random() * 180);
          ic4 = Math.max(0.1, baseGas * 0.02 + Math.random() * 60);
          nc4 = Math.max(0.1, baseGas * 0.015 + Math.random() * 40);
          ic5 = Math.max(0.05, baseGas * 0.003 + Math.random() * 15);
          nc5 = Math.max(0.05, baseGas * 0.002 + Math.random() * 10);
        } else {
          c1 = Math.max(10, baseGas * 0.55 + Math.random() * 800);
          c2 = Math.max(1, baseGas * 0.20 + Math.random() * 350);
          c3 = Math.max(0.5, baseGas * 0.14 + Math.random() * 220);
          ic4 = Math.max(0.1, baseGas * 0.05 + Math.random() * 80);
          nc4 = Math.max(0.1, baseGas * 0.04 + Math.random() * 60);
          ic5 = Math.max(0.05, baseGas * 0.012 + Math.random() * 20);
          nc5 = Math.max(0.05, baseGas * 0.008 + Math.random() * 15);
        }
        const tg = c1 + c2 + c3 + ic4 + nc4 + ic5 + nc5;

        rows.push({
          DEPTH: depth,
          C1: Math.round(c1),
          C2: Math.round(c2),
          C3: Math.round(c3),
          IC4: parseFloat(ic4.toFixed(1)),
          NC4: parseFloat(nc4.toFixed(1)),
          IC5: parseFloat(ic5.toFixed(1)),
          NC5: parseFloat(nc5.toFixed(1)),
          TG: Math.round(tg)
        });
      }
    }

    return this.computeAll(rows);
  }
}

// Export for Node/CommonJS or attach to browser window
if (typeof module !== 'undefined' && module.exports) {
  module.exports = PetrophysicalEngine;
} else if (typeof window !== 'undefined') {
  window.PetrophysicalEngine = PetrophysicalEngine;
}
