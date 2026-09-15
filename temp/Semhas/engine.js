/**
 * Petrophysical Calculation Engine (JavaScript Engine)
 * Replicates and extends engine.py with exact mathematical formulas,
 * configurable thresholds, and deterministic majority-vote zone classification.
 */

const DEFAULT_THRESHOLDS = {
  // Noise, C4/C5 Detection Limits and Pure Methane Cutoffs
  tg_noise: 300.0,
  c1_noise: 200.0,
  c1_pure_gas: 2000.0,
  c4_c5_detection_limit: 0.05,
  // Haworth Wetness (Wh) Limits (%)
  wh_gas_min: 0.5,
  wh_gas_max: 17.5,
  wh_oil_max: 40.0,
  // Haworth Balance (Bh) Limits
  bh_gas_min: 15.0,
  bh_oil_min: 0.5,
  // Haworth Character (Ch) Cutoff
  ch_gas_max: 0.5,
  // Dryness (DR = C1 / TG) Limits
  dry_gas_min: 0.85,
  dry_oil_min: 0.50,
  // Pixler R1 (C1 / C2) Limits
  r1_gas_min: 15.0,
  r1_oil_min: 2.0,
  // Pixler R4 (C2 / C1) Bump Limit for Oil
  r4_oil_bump_min: 0.067,
  // Expanded Butane Ratio (C1 / nC4) Spike for Gas
  ratio_nc4_gas_min: 100.0,
  // Wetness-Balance Score (WBS) Limits
  wbs_gas_min: 0.0,
  wbs_oil_min: -0.5,
  // Normalized Heavy Gas (GOW_noTG) Limits
  gow_notg_gas_max: 0.015,
  gow_notg_oil_max: 0.08,
};

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
   * @param {Object} thresholdOverrides - Optional overrides for classification thresholds
   * @returns {Array<Object>} Processed rows with all indicators and ZONE
   */
  static computeAll(rawData, customFormulaOverrides = {}, thresholdOverrides = {}) {
    if (!Array.isArray(rawData) || rawData.length === 0) return [];

    const processed = rawData.map(row => {
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

      // 1-6: Pixler Ratios & Normalized Hydrocarbon Multipliers
      const r1 = this.safeDiv(c1, c2, 0);
      const r2 = this.safeDiv(c1, c3, 0);
      const r3_c3_c1 = this.safeDiv(c3, c1, 0);
      const r4_c2_c1 = this.safeDiv(c2, c1, 0);
      const r3_c2_c3 = this.safeDiv(c2, c3, 0);
      const ratio_ic4 = this.safeDiv(c1, ic4, 0);
      const ratio_nc4 = this.safeDiv(c1, nc4, 0);

      // 7-9: Dryness & Carbon Density Index
      const dryness = this.safeDiv(c1, tgUsed, 0);
      const carbonWeighted = c1 + (2 * c2) + (3 * c3) + (4 * ic4) + (4 * nc4) + (5 * ic5) + (5 * nc5);
      const carbonIndex = this.safeDiv(tgUsed, carbonWeighted, 0);

      // 10-12: Haworth Ratios (Wh, Bh, Ch)
      const heavySum = c2 + c3 + ic4 + nc4 + ic5 + nc5;
      const wh = this.safeDiv(heavySum, tgUsed, 0) * 100.0;
      
      const light = c1 + c2;
      const heavyC3Plus = c3 + ic4 + nc4 + ic5 + nc5;
      const bh = this.safeDiv(light, heavyC3Plus, 0);

      const butanePentane = ic4 + nc4 + ic5 + nc5;
      const ch = this.safeDiv(butanePentane, c3, 0);

      // 13-16: Composite Indicators (GOW, GOW_noTG, WBS, GOR)
      const gow = this.safeDiv(heavyC3Plus * tgUsed, derivedTG, 0);
      const gowNoTG = this.safeDiv(heavyC3Plus, derivedTG, 0);

      let wbs = 0;
      if (bh > 0 && wh > 0) {
        const logBh = Math.log10(bh);
        const logWh = Math.log10(wh);
        wbs = ((logBh - 0.903) / 2.097) - (logWh / 2.0);
      }

      const gor = (tgUsed > 0.8 && tgUsed < 1.2 && c1 > 2000) ? 0 : 1;

      const item = {
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
        R3_C3_C1: r3_c3_c1,
        R4_C2_C1: r4_c2_c1,
        C3_C1: r3_c3_c1,
        C2_C1: r4_c2_c1,
        R3_C2_C3: r3_c2_c3,
        RATIO_IC4: ratio_ic4,
        R4_C1_IC4: ratio_ic4,
        RATIO_NC4: ratio_nc4,
        R5_C1_NC4: ratio_nc4,
        DRYNESS: dryness,
        CARBON_INDEX: carbonIndex,
        WH: wh,
        BH: bh,
        CH: ch,
        GOW: gow,
        GOW_NOTG: gowNoTG,
        WBS: wbs,
        GOR: gor,
        ZONE: "Non-Bearing"
      };

      // Evaluate any custom formula overrides
      for (const [key, expr] of Object.entries(customFormulaOverrides)) {
        if (expr) {
          try {
            item[key] = this.evaluateExpression(expr, item);
          } catch (e) {
            item[key] = 0;
          }
        }
      }

      return item;
    });

    // Compute deterministic majority-vote zone classifications with spatial continuity
    const zones = this._classifyZones(processed, thresholdOverrides);
    for (let i = 0; i < processed.length; i++) {
      processed[i].ZONE = zones[i];
    }

    return processed;
  }

  /**
   * Deterministic majority-vote fluid zone classifier matching Chapter 3 criteria & engine.py
   */
  static _classifyZones(rows, thresholds = {}) {
    const th = Object.assign({}, DEFAULT_THRESHOLDS, thresholds);
    const n = rows.length;
    const rawZones = [];

    const tg_noise = parseFloat(th.tg_noise || 300.0);
    const c1_noise = parseFloat(th.c1_noise || 200.0);
    const det_lim = parseFloat(th.c4_c5_detection_limit || 0.05);

    const wh_gas_min = parseFloat(th.wh_gas_min || 0.5);
    const wh_gas_max = parseFloat(th.wh_gas_max || 17.5);
    const wh_oil_max = parseFloat(th.wh_oil_max || 40.0);

    const bh_gas_min = parseFloat(th.bh_gas_min || 15.0);
    const bh_oil_min = parseFloat(th.bh_oil_min || 0.5);

    const ch_gas_max = parseFloat(th.ch_gas_max || 0.5);

    const dry_gas_min = parseFloat(th.dry_gas_min || 0.85);
    const dry_oil_min = parseFloat(th.dry_oil_min || 0.50);

    const r1_gas_min = parseFloat(th.r1_gas_min || 15.0);
    const r1_oil_min = parseFloat(th.r1_oil_min || 2.0);

    const r4_oil_bump_min = parseFloat(th.r4_oil_bump_min || 0.067);
    const ratio_nc4_gas_min = parseFloat(th.ratio_nc4_gas_min || 100.0);

    const wbs_gas_min = parseFloat(th.wbs_gas_min || 0.0);
    const wbs_oil_min = parseFloat(th.wbs_oil_min || -0.5);

    const gow_notg_gas_max = parseFloat(th.gow_notg_gas_max || 0.015);
    const gow_notg_oil_max = parseFloat(th.gow_notg_oil_max || 0.08);

    for (let i = 0; i < n; i++) {
      const r = rows[i];
      const c1 = r.C1;
      const c2 = r.C2;
      const c3 = r.C3;
      const ic4 = r.IC4 || 0;
      const nc4 = r.NC4 || 0;
      const ic5 = r.IC5 || 0;
      const nc5 = r.NC5 || 0;
      const tg = r.DERIVED_TG || (c1 + c2 + c3 + ic4 + nc4 + ic5 + nc5);

      // 1. Base Hydrocarbon Continuity Gate:
      // If C1, C2, or C3 is missing, NaN, or <= 0 -> Non-Bearing (bypasses voting)
      if (c1 <= 0 || c2 <= 0 || c3 <= 0 || isNaN(c1) || isNaN(c2) || isNaN(c3) || !isFinite(c1) || !isFinite(c2) || !isFinite(c3)) {
        rawZones.push("Non-Bearing");
        continue;
      }

      // 2. Background Noise / Baseline Cutoff:
      if (tg < tg_noise && c1 < c1_noise) {
        rawZones.push("Non-Bearing");
        continue;
      }

      // 3. Check presence of Butanes (iC4, nC4) and Pentanes (iC5, nC5)
      const has_ic4 = (ic4 > det_lim) && isFinite(ic4);
      const has_nc4 = (nc4 > det_lim) && isFinite(nc4);
      const has_ic5 = (ic5 > det_lim) && isFinite(ic5);
      const has_nc5 = (nc5 > det_lim) && isFinite(nc5);

      const has_c4 = has_ic4 || has_nc4;
      const has_c5 = has_ic5 || has_nc5;

      // STRICT RULE: Must have ic4, nc4, ic5, or nc5 data present to assign Gas or Oil.
      // If all C4 & C5 channels are missing / zero / below detection limit -> Non-Bearing
      if (!has_c4 && !has_c5) {
        rawZones.push("Non-Bearing");
        continue;
      }

      let gas_votes = 0;
      let oil_votes = 0;

      // --- Rule 1: Hydrocarbon Speciation (iC4, nC4, iC5, nC5) ---
      if (has_c4 && !has_c5) {
        oil_votes += 4;
      } else if (has_c5) {
        gas_votes += 3;
      }

      if (ic4 <= det_lim && nc4 > det_lim && c1 > 0) {
        const r_nc4_check = c1 / nc4;
        if (r_nc4_check >= ratio_nc4_gas_min) {
          gas_votes += 1;
        }
      }

      // --- Rule 2: C1, C2, C3 Spike & TG Spike ---
      if (c1 >= 1000 && c2 > 0 && c3 > 0) {
        gas_votes += 2;
      }
      if (tg >= 1500) {
        gas_votes += 2;
      } else if (tg > 0 && tg < 1500) {
        oil_votes += 1;
      }

      // --- Rule 3: Pixler R1 (C1/C2) & Pixler R4 (C2/C1 Bump) ---
      if (c2 > 0 && c1 > 0) {
        const r1 = c1 / c2;
        const r4 = c2 / c1;
        if (r1 >= r1_gas_min && r4 < r4_oil_bump_min) {
          gas_votes += 2;
        } else if (r1 >= r1_oil_min && r1 < r1_gas_min) {
          oil_votes += 2;
        }

        if (r4 >= r4_oil_bump_min) {
          oil_votes += 2;
        }
      }

      // --- Rule 4: Spike in Ratio nC4 (C1 / nC4) ---
      if (nc4 > 0 && c1 > 0) {
        const r_nc4 = c1 / nc4;
        if (r_nc4 >= ratio_nc4_gas_min) {
          gas_votes += 2;
        }
      }

      // --- Rule 5: Haworth Wetness (Wh) ---
      const wh = r.WH;
      if (!isNaN(wh) && isFinite(wh) && wh > 0) {
        if (wh >= wh_gas_min && wh < wh_gas_max) {
          gas_votes += 2;
        } else if (wh >= wh_gas_max && wh <= wh_oil_max) {
          oil_votes += 2;
        }
      }

      // --- Rule 6: Haworth Balance (Bh) ---
      const bh = r.BH;
      if (!isNaN(bh) && isFinite(bh) && bh > 0) {
        if (bh >= bh_gas_min) {
          gas_votes += 2;
        } else if (bh >= bh_oil_min && bh < bh_gas_min) {
          oil_votes += 2;
        }
      }

      // --- Rule 7: Haworth Character (Ch) ---
      const ch = r.CH;
      if (!isNaN(ch) && isFinite(ch) && ch > 0) {
        if (ch < ch_gas_max) {
          gas_votes += 1;
        } else {
          oil_votes += 1;
        }
      }

      // --- Rule 8: Dryness Ratio (C1 / TG) ---
      const dry = r.DRYNESS;
      if (!isNaN(dry) && isFinite(dry) && dry > 0 && c1 > 0 && tg > 0) {
        if (dry >= dry_gas_min) {
          gas_votes += 1;
        } else if (dry >= dry_oil_min) {
          oil_votes += 1;
        }
      }

      // --- Rule 9: Normalized Heavy Gas (GOW_noTG) ---
      const gow_n = r.GOW_NOTG;
      if (!isNaN(gow_n) && isFinite(gow_n) && gow_n > 0) {
        if (gow_n < gow_notg_gas_max) {
          gas_votes += 1;
        } else if (gow_n <= gow_notg_oil_max) {
          oil_votes += 1;
        }
      }

      // --- Rule 10: Wetness-Balance Score (WBS) ---
      const wbs = r.WBS;
      if (!isNaN(wbs) && isFinite(wbs) && wbs !== 0.0) {
        if (wbs > wbs_gas_min) {
          gas_votes += 1;
        } else if (wbs >= wbs_oil_min) {
          oil_votes += 1;
        }
      }

      // --- Decision matrix (Gas vs Oil vs Non-Bearing) ---
      if (gas_votes > oil_votes && gas_votes > 0) {
        rawZones.push("Gas");
      } else if (oil_votes > gas_votes && oil_votes > 0) {
        rawZones.push("Oil");
      } else if (gas_votes === oil_votes && gas_votes > 0) {
        rawZones.push(has_c5 ? "Gas" : "Oil");
      } else {
        rawZones.push("Non-Bearing");
      }
    }

    // -----------------------------------------------------------------------
    // Spatial Cluster & Neighbor Rule:
    // Any connected pay package containing Gas is consolidated to solid Gas.
    // -----------------------------------------------------------------------
    const adjustedZones = [...rawZones];
    const nPts = adjustedZones.length;

    // 1. Cluster-level propagation: any continuous pay package with Gas becomes solid Gas
    let start = null;
    for (let i = 0; i < nPts; i++) {
      if (adjustedZones[i] === "Gas" || adjustedZones[i] === "Oil") {
        if (start === null) start = i;
      } else {
        if (start !== null) {
          const end = i;
          const cluster = adjustedZones.slice(start, end);
          if (cluster.includes("Gas")) {
            for (let k = start; k < end; k++) {
              if (adjustedZones[k] === "Oil") adjustedZones[k] = "Gas";
            }
          }
          start = null;
        }
      }
    }
    if (start !== null) {
      const cluster = adjustedZones.slice(start, nPts);
      if (cluster.includes("Gas")) {
        for (let k = start; k < nPts; k++) {
          if (adjustedZones[k] === "Oil") adjustedZones[k] = "Gas";
        }
      }
    }

    // 2. Secondary neighborhood smoothing pass (within +/-3 samples)
    for (let i = 0; i < nPts; i++) {
      if (adjustedZones[i] === "Oil") {
        const wStart = Math.max(0, i - 3);
        const wEnd = Math.min(nPts, i + 4);
        const surrounding = adjustedZones.slice(wStart, wEnd);
        if (surrounding.includes("Gas")) {
          adjustedZones[i] = "Gas";
        }
      }
    }

    return adjustedZones;
  }

  /**
   * Safe Math Expression Evaluator
   * Supports operators: +, -, *, /, ^, %, parentheses, log10, ln, sqrt, abs, min, max
   */
  static evaluateExpression(expr, variables) {
    if (!expr || typeof expr !== 'string') return 0;

    let sanitized = expr
      .replace(/\s+/g, '')
      .replace(/log10\(/g, 'Math.log10(')
      .replace(/ln\(/g, 'Math.log(')
      .replace(/sqrt\(/g, 'Math.sqrt(')
      .replace(/abs\(/g, 'Math.abs(')
      .replace(/\^/g, '**');

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

    const sortedKeys = Object.keys(scope).sort((a, b) => b.length - a.length);
    for (const key of sortedKeys) {
      const regex = new RegExp(`\\b${key}\\b`, 'g');
      sanitized = sanitized.replace(regex, `(${scope[key]})`);
    }

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
  module.exports = { PetrophysicalEngine, DEFAULT_THRESHOLDS };
}
if (typeof window !== 'undefined') {
  window.PetrophysicalEngine = PetrophysicalEngine;
  window.DEFAULT_THRESHOLDS = DEFAULT_THRESHOLDS;
}
