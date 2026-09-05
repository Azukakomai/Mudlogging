# Empirical Classification & System Benchmarks

## 1. Primary Classification Metrics

### Overall Accuracy : 80% – 85%
* **Why?**
  * Mud logging and Gas While Drilling (GWD) datasets contain inherent operational noise (gas recycling, mud contamination, lag depth uncertainties, and differential degasser extraction efficiency).
  * An overall accuracy benchmark of $\ge 80\%$ confirms strong, dependable alignment between early automated surface fluid predictions and post-drilling Wireline Formation Tester (RFT/MDT) or production testing records across the entire wellbore interval.

---

### Macro-Averaged F1-Score ($\text{Macro-}F_1$) : 75% – 80% (0.75 – 0.80)
* **Why?**
  * Subsurface well logs are severely **class-imbalanced**; non-productive shale and water-bearing intervals frequently account for 70%–85% of total drilled depth, while valuable hydrocarbon pay zones (Gas/Oil) make up only 15%–30%.
  * Standard accuracy can be misleadingly high simply by correctly guessing background rock. Macro-$F_1$ treats all 3 classes equally without sample weighting, ensuring that thin, highly valuable hydrocarbon reservoir intervals are not overlooked or masked by the dominant non-productive background.

---

### Precision : 75% – 80%
* **Why?**
  * Precision measures confidence in positive flags (i.e., when the system declares a depth interval as "Gas" or "Oil", what percentage actually is reservoir pay).
  * Maintaining high precision ($\ge 75\%$) prevents costly false alarms, ensuring drilling teams do not waste rig time or initiate unnecessary casing, testing, or coring operations on non-productive intervals.

---

### Recall (Sensitivity) : 75% – 80%
* **Why?**
  * Recall measures the system's ability to catch true hydrocarbon zones without missing them.
  * In active drilling, missing a gas reservoir is a serious safety and economic risk (potential kick/blowout hazard or bypassed pay). A recall target of $\ge 75\%$–$80\%$ ensures the majority voting engine captures almost all viable pay occurrences.

---

## 2. Per-Class Benchmark Breakdown

### Gas Zone Recall & F1 : 80% – 85%
* **Why?**
  * Methane ($C_1$) and light hydrocarbons liberate readily at the surface with strong chromatographic peaks.
  * Because gas kicks present critical well-control implications, this class warrants the highest sensitivity (recall) benchmark.

### Oil Zone Recall & F1 : 70% – 75%
* **Why?**
  * Heavier hydrocarbon fractions ($C_3$–$C_5$) have lower volatility, undergo slower degasser extraction, and produce subtler gas ratio spikes compared to dry/wet gas.
  * Given the more complex chromatographic signature in heavy/medium oils, a 70%–75% benchmark is realistic, robust, and aligns with academic literature for deterministic multi-ratio engines.

### Water / Non-Productive Zone F1 : 85% – 90%
* **Why?**
  * Non-productive background shale and water wet sands exhibit distinctly flat gas curves and high dryness ratios.
  * High precision and recall ensure clear separation between barren baseline formations and active hydrocarbon anomalies.

---

## 3. Operational Performance Benchmark

### Computational Latency ($\Delta t_{\text{total}}$) : $\le 5.0$ seconds
* **Why?**
  * Wellsite operations and real-time gas monitoring require rapid decision turnaround.
  * Processing, computing all 16 ratio indicators, and rendering interactive area tracks across deep wells ($> 3000\text{ m}$ depth, tens of thousands of data rows) in under 5 seconds guarantees real-time operational fluency without browser lag.
