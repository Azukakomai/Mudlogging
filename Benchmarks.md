# Empirical Classification & System Benchmarks

## 1. Primary Classification Metrics

### Overall Accuracy : 80% – 85%
* **What is it?**
  * The percentage of all depth intervals (across Gas, Oil, and Water/Non-productive zones) that the system classifies correctly compared to the total number of evaluated intervals.
  * Formula: $\text{Accuracy} = \frac{\text{Total Correct Predictions}}{\text{Total Depth Intervals}}$
* **Why this benchmark?**
  * Mud logging and Gas While Drilling (GWD) datasets contain inherent operational noise (gas recycling, mud contamination, lag depth uncertainties, and differential degasser extraction efficiency).
  * An overall accuracy benchmark of $\ge 80\%$ confirms strong, dependable alignment between early automated surface fluid predictions and post-drilling Wireline Formation Tester (RFT/MDT) or production testing records across the entire wellbore interval.

---

### Macro-Averaged F1-Score ($\text{Macro-}F_1$) : 75% – 80% (0.75 – 0.80)
* **What is it?**
  * The unweighted average of the F1-Scores calculated individually for each of the 3 reservoir fluid classes ($\text{Gas}$, $\text{Oil}$, and $\text{Water/Non-productive}$).
  * Formula: $\text{Macro-}F_1 = \frac{F_{1,\text{Gas}} + F_{1,\text{Oil}} + F_{1,\text{Water}}}{3}$
* **Why this benchmark?**
  * Subsurface well logs are severely **class-imbalanced**; non-productive shale and water-bearing intervals frequently account for 70%–85% of total drilled depth, while valuable hydrocarbon pay zones (Gas/Oil) make up only 15%–30%.
  * Standard accuracy can be misleadingly high simply by correctly guessing background rock. Macro-$F_1$ treats all 3 classes equally without sample weighting, ensuring that thin, highly valuable hydrocarbon reservoir intervals are not overlooked or masked by the dominant non-productive background.

---

### Precision (Positive Predictive Value) : 75% – 80%
* **What is it?**
  * Out of all the depth intervals that the system *flags* as a specific fluid type (e.g., predicted as "Oil"), the percentage that actually turns out to be that true fluid type.
  * Formula: $\text{Precision}_c = \frac{TP_c}{TP_c + FP_c}$
* **Why this benchmark?**
  * Precision measures confidence in positive detections.
  * Maintaining high precision ($\ge 75\%$) prevents costly false alarms, ensuring drilling teams do not waste rig time or initiate unnecessary casing, testing, or coring operations on non-productive intervals.

---

### Recall (Sensitivity / True Positive Rate) : 75% – 80%
* **What is it?**
  * Out of all the actual, existing fluid intervals in the ground (e.g., all real pay zones confirmed by wireline/production data), the percentage that the system successfully detects and captures.
  * Formula: $\text{Recall}_c = \frac{TP_c}{TP_c + FN_c}$
* **Why this benchmark?**
  * Recall measures the system's ability to catch true hydrocarbon zones without missing them.
  * In active drilling, missing a gas reservoir is a serious safety and economic risk (potential kick/blowout hazard or bypassed pay). A recall target of $\ge 75\%$–$80\%$ ensures the majority voting engine captures almost all viable pay occurrences.

---

### Class F1-Score : 70% – 85% (per class)
* **What is it?**
  * The harmonic balance between Precision and Recall for a specific class. It penalizes extreme imbalances (such as very high recall with terrible precision).
  * Formula: $F_{1,c} = 2 \times \frac{\text{Precision}_c \times \text{Recall}_c}{\text{Precision}_c + \text{Recall}_c}$
* **Why this benchmark?**
  * It provides a single, balanced quality score for each fluid type, ensuring that detection is both reliable (high precision) and complete (high recall).

---

## 2. Per-Class Benchmark Breakdown

### Gas Zone (Target $F_1$: 80% – 85%, Recall: $\ge 80\%$)
* **What is it?**
  * Classification performance specifically on methane-rich, low-density hydrocarbon gas reservoir intervals.
* **Why this benchmark?**
  * Methane ($C_1$) and light hydrocarbons liberate readily at the surface with strong chromatographic peaks.
  * Because gas kicks present critical well-control implications, this class warrants the highest sensitivity (recall) benchmark.

### Oil Zone (Target $F_1$: 70% – 75%, Recall: $\ge 70\%$)
* **What is it?**
  * Classification performance on liquid petroleum reservoir intervals characterized by heavier alkane signatures ($C_2$ through $C_5$).
* **Why this benchmark?**
  * Heavier hydrocarbon fractions ($C_3$–$C_5$) have lower volatility, undergo slower degasser extraction, and produce subtler gas ratio spikes compared to dry/wet gas.
  * Given the more complex chromatographic signature in heavy/medium oils, a 70%–75% benchmark is realistic, robust, and aligns with academic literature for deterministic multi-ratio engines.

### Water / Non-Productive Zone (Target $F_1$: 85% – 90%, Recall: $\ge 85\%$)
* **What is it?**
  * Classification performance on non-reservoir formations, barren shales, tight zones, and water-wet sands.
* **Why this benchmark?**
  * Non-productive background formations exhibit distinctly flat gas curves and high dryness ratios.
  * High precision and recall ensure clear separation between barren baseline formations and active hydrocarbon anomalies.

---

## 3. Operational Performance Benchmark

### Computational Latency ($\Delta t_{\text{total}}$) : $\le 5.0$ seconds
* **What is it?**
  * The total wall-clock time required for the application to parse uploaded raw GWD files, calculate all 16 petrophysical ratio indicators, run the classification logic, and render the interactive log tracks.
  * Formula: $\Delta t_{\text{total}} = t_{\text{ingest}} + t_{\text{compute}} + t_{\text{render}}$
* **Why this benchmark?**
  * Wellsite operations and real-time gas monitoring require rapid decision turnaround.
  * Processing, computing all 16 ratio indicators, and rendering interactive area tracks across deep wells ($> 3000\text{ m}$ depth, tens of thousands of data rows) in under 5 seconds guarantees real-time operational fluency without browser lag.
