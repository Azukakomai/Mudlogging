## PROPOSAL SKRIPSI

## APLIKASI VISUALISASI DATA GAS WHILE DRILLING UNTUK PREDIKSI TIPE HIDROKARBON MENGGUNAKAN ALGORITMA DETERMINISTIK

## HYDROCARBONTYPE PREDICTIONUSING DETERMINISTICALGORITHMS GASWHILE DRILLING DATA VISUALIZATIONAPPLICATIONFOR

Mohammad Azka Khairur Rahman

23/511608/PA/21830

## DEPARTEMEN ILMU KOMPUTER DAN ELEKTRONIKA FAKULTAS MATEMATIKA DAN ILMU PENGETAHUAN ALAM PROGRAM STUDI ILMU KOMPUTER UNIVERSITAS GADJAH MADA YOGYAKARTA

## 2026


## APPROVAL PAGE

## BACHELOR RESEARCH PROPOSAL

## HYDROCARBON TYPE PREDICTION USING DETERMINISTIC ALGORITHMS GAS WHILE DRILLING DATA VISUALIZATION APPLICATION FOR

By:

Mohammad Azka Khairur Rahman

23/511608/PA/21830

Approved On 05 June 2026

Research Supervisor,

Dr. Techn. Khabib Mustofa, S.Si., M.Kom.


## PERNYATAAN

Dengan ini saya menyatakan bahwa dalam Skripsi ini tidak terdapat karya yang pernah diajukan untuk memperoleh gelar kesarjanaan di suatu Perguruan Tinggi, dan sepanjang pengetahuan sa- ya juga tidak terdapat karya atau pendapat yang ditulis atau diterbitkan oleh orang lain, kecuali yang secara tertulis diacu dalam naskah ini dan disebutkan dalam daftar pustaka.

Yogyakarta, 05 June 2026

Mohammad Azka Khairur Rahman


## LIST OF CONTENTS


## ABSTRACT

## Gas While Drilling Data Visualization Application for Hydrocarbon Type Prediction Using Deterministic Algorithms

## By

## Mohammad Azka Khairur Rahman 23/511608/PA/21830

Traditional manual hydrocarbon prediction using Gas While Drilling data has long been

hindered by inefficiencies and inaccuracies, largely due to human error and the complexity of multi-parameter data analysis. Petrophysical interpretation requires the integration of many variables such as porosity, permeability, resistivity, and saturation, which often makes manual evaluation inconsistent. This study seeks to overcome these limitations by developing a de- cision support system specifically designed to analyze and visualize Gas While Drilling data in a more intuitive manner. The proposed framework integrates deterministic algorithms with industry-standard petrophysical formulas to process raw well data. The processed data is then presented through intuitive graphical visualizations, enabling geoscientists to identify trends and anomalies more effectively. Furthermore, the system employs rule-based logic to compare derived parameters against established geological thresholds, allowing for a preliminary yet structured prediction of hydrocarbon presence. The system will be capable of distinguishing between hydrocarbon types (e.g., oil or gas) at varying depths, thereby providing more insights into subsurface conditions. This approach not only reduces the risk of human error but also enhances decision-making in exploration and reservoir characterization.

Keywords: Hydrocarbon Prediction, Data Visualization, Deterministic Algorithms, Decision Support System.


## CHAPTER I INTRODUCTION

## 1.1 Background

In the oil and gas industry, subsurface exploration carries immense capital risk (Soci- [URL 🔗](#page-0)

ety of Petroleum Engineers et al., 2007; Serra dan Serra, 2004). Drilling a single exploration or development well costs millions of dollars; thus, asset teams rely on continuous diagnostic tools to evaluate subsurface formations as drilling advances (Society of Petroleum Engineers et al., 2007). Globally, rotary drilling is a high-frequency, continuous operation, with thousan- ds of active wells being drilled around the clock across international basins (Serra dan Serra, 2004; Moore, 1986; Baker Hughes, 2024). Because drilling occurs continuously on such a massive operational scale, Gas While Drilling (GWD) analysis has become one of the most es- sential and widely deployed formation evaluation techniques (Serra dan Serra, 2004; Whittaker, [URL 🔗](#page-0)

[1991a).](#page-0)

the drilling mud stream as the drill bit cuts through rock layers, providing wellsite geologists with immediate indicators of reservoir fluid content (Whittaker, 1991a; Haworth et al., 1985). Accurate GWD interpretation enables engineers to confirm hydrocarbon-bearing pay zones qu- ickly or make the critical decision to halt drilling early, thereby saving millions of dollars by avoiding non-productive "dry holes" (Society of Petroleum Engineers et al., 2007; Serra dan Serra, 2004). [URL 🔗](#page-0)

Despite the critical necessity ofGWD evaluation during active operations, standard field

interpretation workflows remain overly constrained (Serra dan Serra, 2004; Doveton, 2014). In prevailing operational practices, wellsite engineers and petrophysicists typically rely on only two basic parameters—the classical Haworth Wetness Ratio (Wh) and Balance Ratio (Bh)—to evaluate gas shows and classify fluid boundaries (Whittaker, 1991a; Haworth et al., 1985). Re- lying solely on this narrow two-ratio pair frequently produces ambiguous or incomplete fluid characterizations, particularly in complex reservoirs with mixed fluid contacts, fluctuating pe- [URL 🔗](#page-0)

netration rates, or heavier hydrocarbon components (C4 and

two-variable evaluations (Mondol, 2015; Whittaker, 1991a; Haworth et al., 1985). By restri- [URL 🔗](#page-0)

cting evaluation to just

by modern multi-ratio models, including Pixler ratios, Character ratios, and composite gas-oil indicators (Pixler, 1969; Whittaker, 1991b; Society of Petroleum Engineers, 2007). [URL 🔗](#page-0)

To expand beyond this restricted evaluation and automate multi-parameter log ana-

lysis, exploration teams typically look to modern digital platforms (Mohaghegh, 2000; Mon- dol, 2015). While data-driven machine learning (ML) architectures have been explored for petrophysical prediction (Guan et al., 2022; Ibrahim et al., 2021; Dai et al., 2024), they act as opaque "black boxes" that fail to expose their internal reasoning (Mohaghegh, 2000). Strict industry guidelines, such as Society of Petroleum Engineers et al. (2007) reserve estimation [URL 🔗](#page-0)

GWD measures light-to-heavy hydrocarbon gas fractions (C1 through

C5)

released into

C5)

that are ignored in simple

Wh

and

Bh,

operators miss out on the valuable diagnostic depth offered


standards, require step-by-step physical documentation to certify petroleum reserves, meaning non-transparent AI models fail regulatory safety audits and cannot be accepted for official repor- ting (Mohaghegh, 2000; Society of Petroleum Engineers et al., 2007). Conversely, commercial enterprise software suites—such as SLB Techlog or AspenTech Geolog—offer comprehensive, physically grounded formation evaluation tools (Mondol, 2015; Wood, 2020). However, the- se enterprise suites are burdened by cost-prohibitive licensing fees (frequently exceeding tens of thousands of dollars per annual seat license) (Mondol, 2015; Wood, 2020). For smaller in- dependent operators, field consultants, wellsite service companies, and academic institutions that specifically require multi-ratio GWD visualization and hydrocarbon fluid typing, purcha- sing an entire multi-thousand-dollar enterprise suite just to access that specific functionality is financially unfeasible (Mondol, 2015; Doveton, 2014; Wood, 2020). [URL 🔗](#page-0)

This situation creates an operational gap: because drilling is conducted frequently and

continuously, asset teams urgently need a lightweight, cost-effective tool built specifically for comprehensive GWD visualization and deterministic hydrocarbon classification (Mondol, 2015; Doveton, 2014; Whittaker, 1991a). To address this need, this study proposes an open-source, web-based decision support system developed using Python (Dash and Plotly) (Mondol, 2015). By integrating classic Haworth wetness and balance ratios with expanded modern formulas in- to an automated deterministic pipeline, the system rapidly ingests raw mud logs, computes 16 derived gas ratios, classifies fluid zones, and renders interactive vertical area charts in secon- ds—providing multi-ratio cross-comparison without the financial burden of enterprise software licenses (Society of Petroleum Engineers et al., 2007; Mondol, 2015; Doveton, 2014; Whittaker, 1991a). [URL 🔗](#page-0)

## 1.1.1 Problem Statement

Because drilling operations are conducted continuously on a massive global scale, Gas

While Drilling (GWD) log evaluation is an essential diagnostic requirement; however, current field practices predominantly depend on a limited two-ratio framework (Haworth Wetness and Balance ratios) that yields ambiguous fluid predictions, while modern alternatives force engi- neers to choose between non-auditable "black-box" machine learning models or purchasing cost-prohibitive enterprise software suites (such as SLB Techlog or Aspen Geolog) simply to access multi-ratio GWD plotting and evaluation features. Consequently, there is an urgent need for a dedicated, open-source decision support platform that automates multi-ratio GWD data visualization and deterministic hydrocarbon classification in seconds, delivering full mathema- tical transparency and multi-parameter comparative insights without the burden of expensive corporate software licenses.


## 1.2 Research Objectives

To design, develop, and deploy an open-source, web-based deterministic decision sup-

port application specifically tailored for Gas While Drilling (GWD) log visualization and auto- mated hydrocarbon fluid classification, eliminating the necessity for costly commercial software licenses, non-transparent machine learning models, or oversimplified two-ratio evaluation pra- ctices.

To systematically resolve the challenges outlined in the problem statement, the specific

research objectives are formulated as follows:

To overcome the diagnostic limitations of relying solely on an oversimplified two-ratio

baseline, the first objective is to program a fully auditable deterministic calculation engine in Python. This engine directly ingests raw chromatographic gas fractions (C1 through C5) and automates the calculation of 16 derived petrophysical indicators, expanding beyond standard Wetness and Balance ratios to incorporate classic Pixler ratios, expanded Haworth Character ratios, and composite fluid indicators.

To address the barrier of expensive enterprise software suites and provide comprehen-

sive curve analysis, the second objective is to develop a dedicated, high-fidelity interactive dashboard using Dash and Plotly. That allow users to visually cross-compare legacy two-ratio curves with modern expanded ratio curves side-by-side without needing multi-thousand-dollar commercial licenses.

To satisfy the operational urgency of active, drilling environments, the third objective is

to optimize the software pipeline for high computational throughput. The system is engineered to execute the entire end-to-end processing pipeline—spanning file ingestion, data normaliza- tion, 16-parameter ratio computation, and multi-track visual rendering—in under 5 seconds across continuous well trajectories spanning thousands of meters of depth.

## 1.3 Research Benefits

The development of a dedicated, open-source GWD petrophysical application provides

direct contributions to active field operations, independent energy entities, and academic envi- ronments.

## 1.3.1 Industrial and Operational Impact

Cost Reduction and Targeted Feature Access By providing a free, web-accessible tool de- dicated specifically to comprehensive GWD processing and multi-ratio visual display, this sof- tware eliminates the requirement for smaller operators and field consultants to purchase multi- thousand-dollar enterprise licenses (such as SLB Techlog or Aspen Geolog) merely to execute routine GWD interpretations.


Capital Risk Mitigation and Multi-Ratio Accuracy Expanding standard formation evalua- tion from an oversimplified two-ratio baseline to an integrated 16-parameter deterministic fra- mework provides wellsite teams with significantly sharper fluid differentiation. Hard-coding proven physical equations directly into the software core ensures that every meter drilled is eva- luated against consistent mathematical criteria, helping companies protect capital by avoiding non-productive "dry holes".

## 1.3.2 Academic and Educational Contributions

Democratization of Petrophysical Tools Due to extreme licensing costs associated with en- terprise software platforms, university departments and independent researchers are frequently locked out of modern digital log evaluation tools. Deploying an open-source platform demo- cratizes access to multi-ratio petrophysical evaluation tools for classrooms and students.

Enhancement of Geoscience Education In academic settings, students often struggle to con- nect theoretical gas ratio formulas with actual visual log curves. This application provides a modern, interactive visual platform where students can observe log curve shifts across multiple vintage and modern ratio methods simultaneously as underlying gas parameters change.


## LITERATURE REVIEW CHAPTER II

## 2.1 Computational Approaches in Hydrocarbon Prediction

The interpretation of well log and mud log data has historically depended on the exper-

tise and judgment of individual petrophysicists. As reservoirs grow more complex and the volume of acquired data continues to expand, the limitations of purely manual interpretation have become increasingly apparent. Human analysis is inherently time-consuming, difficult to scale, and subject to variability between interpreters. Computational approaches address these limitations directly: they offer systematic, reproducible pipelines capable of processing large multi-well datasets with consistent logic and quantifiable uncertainty. Two broad paradigms ha- ve emerged as dominant methodological frameworks in this space — deterministic algorithmic approaches rooted in established physical laws, and data-driven approaches based on machine learning and deep learning architectures. Both have been demonstrated in the literature to provi- de meaningful uplift over manual interpretation alone, and an understanding of their respective strengths and constraints is essential for contextualizing the methodology of this study.

## 2.1.1 Deterministic and Algorithmic Approaches

Deterministic approaches to formation evaluation derive their outputs through the direct

application of explicit mathematical models to measured log data. The intellectual foundation of this paradigm can be traced to the seminal work of Archie (1942), who established the em- pirical relationship between a formation’s measured electrical resistivity, its porosity, and the saturation of its pore fluids. This equation, now universally known as Archie’s Law, provided the first rigorous quantitative framework for inferring subsurface fluid content from borehole measurements, and it remains a cornerstone of formation evaluation to this day. Subsequent decades brought additional deterministic models addressing shaly sand corrections (the Siman- doux equation), volumetric mineral decomposition, and the interpretation of nuclear and aco- ustic logs — all of which operate on the same fundamental principle: given a set of calibrated input measurements and known physical relationships, the output can be computed directly and reproduced exactly (Serra dan Serra, 2004; Doveton, 2014). [URL 🔗](#page-0)

A defining characteristic of deterministic methods is their full transparency. Every in-

termediate result can be audited, the sensitivity of the output to each input parameter can be quantified, and any experienced petrophysicist can trace the chain of reasoning from raw log reading to final reservoir classification. This auditability is not merely an academic advantage; it is often a regulatory and commercial requirement. The Society of Petroleum Engineers et al. (2007) standards for petroleum resource estimation, for instance, explicitly distinguish deter- ministic from probabilistic assessment procedures and require that the methodology underlying [URL 🔗](#page-0)


any reserves declaration be clearly documented and defensible. A code-based deterministic sys- tem — one in which Archie’s Law, shale volume corrections, and pay-zone criteria are encoded as explicit algorithmic rules — inherently satisfies this requirement (Doveton, 2014). [URL 🔗](#page-0)

The practical implementation of deterministic petrophysical logic in software has a long

history. Early systems encoded expert knowledge as lookup tables and threshold-based decision trees. More sophisticated modern implementations use layered conditional logic that integrates multiple log curves simultaneously — for instance, cross-referencing gamma ray for lithology discrimination, resistivity for fluid identification, and neutron-density crossplots for porosity calibration — to classify each depth interval. The transparency of such rule-based systems means that domain experts can inspect, challenge, and refine the underlying logic iteratively, which is particularly valuable in frontier basins where geological priors are poorly constrained. The primary limitation of purely deterministic approaches is their rigidity: the accuracy of the output is bounded by the validity of the underlying physical model, and classical equations like Archie’s Law carry known assumptions (clean formations, water-wet pores, homogeneous lithology) that are frequently violated in complex reservoirs (Serra dan Serra, 2004; Doveton, 2014). [URL 🔗](#page-0)

## 2.1.2 Machine Learning and Data-Driven Approaches

Parallel to deterministic methods, the application of machine learning (ML) and deep

learning (DL) to formation evaluation and hydrocarbon prediction has grown substantially sin- ce its early introduction to petroleum engineering. The conceptual groundwork for applying artificial intelligence techniques to oilfield problems was laid by Mohaghegh (2000), who de- monstrated that artificial neural networks could approximate complex, non-linear mappings between well log inputs and reservoir properties that resist explicit physical formulation. That early work catalysed a sustained research trajectory that has since expanded to include Random Forests, Support Vector Machines, gradient-boosted tree ensembles, and convolutional and re- current neural network architectures. [URL 🔗](#page-0)

The primary appeal of ML approaches is their ability to learn structure directly from

data without requiring the analyst to specify the functional form of the relationship between input and output. In heterogeneous reservoirs where the porosity–permeability relationship is non-stationary, where lithological facies change rapidly along the wellbore, or where the appli- cability of classical deterministic equations is uncertain, ML models can often achieve higher predictive accuracy than their physics-based counterparts. This has been demonstrated across a range of formation evaluation tasks. Ibrahim et al. (2021) showed that ML models trained on wireline log suites can predict in-situ geomechanical properties with strong accuracy, high- lighting the utility of data-driven methods in applications where direct measurement is prohi- bitively expensive. The task of reconstructing missing or degraded log intervals — a common practical problem in older wells or in wells where certain tools were not run — has similarly been addressed through DL architectures. Dai et al. (2024) introduced a flexible graph-neural- [URL 🔗](#page-0)


network approach, FlexLogNet, capable of predicting any arbitrary missing log from the remai- ning available logs within the same well, adaptively adjusting its input configuration to whatever data is present. Well-log completion methods of this type have become increasingly important as operators attempt to extract maximum value from legacy datasets containing incomplete log suites (Guan et al., 2022; Dai et al., 2024). [URL 🔗](#page-0)

Despite these demonstrated capabilities, ML and DL approaches carry inherent limita-

tions that are particularly consequential in a high-stakes petroleum context. The most widely cited of these is the interpretability problem: because complex neural networks and ensemble models derive their predictions through high-dimensional, non-linear transformations that are not straightforwardly human-readable, it can be difficult or impossible to explain why a specific prediction was generated. This opacity creates friction in professional and regulatory settings, where the basis for any reservoir characterization must be auditable (Mondol, 2015). A second major constraint is data dependency: supervised ML models require sufficient labelled training examples to generalise reliably to unseen wells. In frontier exploration areas, where few wells have been drilled and production data is scarce, the training data volumes required to fit complex models may simply not be available, limiting their practical applicability (Mohaghegh, 2000). A third concern is distribution shift: models trained on data from one geological province may perform poorly when applied to a different basin with distinct lithological characteristics, even if the surface log signatures appear superficially similar. [URL 🔗](#page-0)


## RESEARCH METHODOLOGY CHAPTER III

## 3.1 Research Design

This research develops a dedicated web-based decision support system to automate the

processing, multi-ratio comparative analysis, and visualization of Gas While Drilling (GWD) data, as well as deterministic hydrocarbon fluid classification. Because the system is delivered as an interactive software application, the development follows a standard Software Develo- pment Life Cycle (SDLC) adapted for scientific computing, structured across four consecutive phases:

- 1. Requirements Gathering: Identifying end-user needs, essential mud log data forma- ts, and workflow pain points by distributing structured requirements questionnaires (via Google Forms) to practicing geoscientists, wellsite engineers, and academic researchers.

- 2. System Architecture and UI/UX Design: Specifying the three-tier modular software architecture (Data Ingestion, Deterministic Logic Engine, and Interactive Plotly Dashbo- ard) and planning modal-based user workflows in Dash.

- 3. Deterministic Implementation (Data-Free Build Phase): Developing the data parsers, mathematical ratio pipelines, and decision-tree logic. Because the engine is purely deter- ministic—operating strictly on closed-form petrophysical formulas and explicit boundary thresholds—the system development requires no empirical training data or machine le- arning model fitting during construction. The algorithms are programmed and verified against exact mathematical benchmarks.

- 4. User-Driven Testing and Evaluation: Once the application build is complete, external validation is conducted by distributing the deployed platform to industry contacts, peer networks, and professional platform connections (e.g., LinkedIn). Evaluators run their own real-world well datasets through the software, compare the predicted fluid zones against their established well-test ground truth, and record the classification results using structured evaluation forms.

## 3.2 Software Structure

A primary objective of this application is to provide geoscientists with a comprehensive

comparative suite within a single dashboard. Different eras and regional standards in petroleum geology rely on varying interpretation methods. To allow users to cross-compare results from legacy frameworks with modern expanded indicators, the system integrates a wide array of both classical and updated formulas. The data pipeline takes parsed hydrocarbon gas curves (C1


through C5) and automatically computes 16 derived parameters alongside automated fluid-zone predictions.

## 3.2.1 Data Parsing & Ingestion Layer

The ingestion layer handles raw mud logging text files (.txt), spreadsheets (.xlsx),

and comma-separated values (.csv). It isolates data matrices through the following steps:

- 1. Metadata and Header Isolation: The parser scans the file line-by-line using keyword triggers (such as ~A or Depth) to bypass unstructured company metadata headers and locate the column index.

- 2. Data Normalization and Type Casting: Delimited text lines (tabs, commas, or spaces) are stripped of non-numeric formatting characters and converted into structured float ma- trices indexed continuously by measured depth (MD). Missing or null entries are handled systematically to prevent pipeline interrupts.

## 3.2.2 Petrophysical Indicators & System Decision Logic

Pixler Hydrocarbon Ratios The system evaluates light hydrocarbon fractions using the clas- sic ratio framework established by Pixler (1969) to distinguish dry gas intervals from productive oil-bearing formations: [URL 🔗](#page-0)

A very high C1/C2 ratio indicates dry methane gas, while lower values reflect increasing

concentrations of heavier, liquid-associated hydrocarbons (Pixler, 1969). [URL 🔗](#page-0)

Expanded Light-to-Heavy Butane Multipliers To utilize modern chromatographic logs that split butane into individual isomers, the engine tracks methane against specific butane paths:

Tracking isobutane (iC4) and normal butane (nC4) separately provides heightened sen-

sitivity to heavy, liquid-rich reservoir boundaries.


Total Gas Volume (TG) and Dryness Ratio When Total Gas (TG) is not pre-recorded in the uploaded log, the baseline is computed by summing all recorded hydrocarbon fractions (Moore, 1986): [URL 🔗](#page-0)

The Dryness Ratio is then computed to isolate the methane purity of the gas mixture:

Carbon-Weighted Density Index (Icarbon) To quantify carbon density across the gas stream, the system implements a weighted index where each alkane fraction is scaled by its carbon atom count:

Because liquid hydrocarbons contain longer carbon chains, a lower Icarbon value indicates

a shift toward heavier petroleum fluids.

Expanded Haworth Gas Ratios The system implements both standard and expanded forms of the Show Evaluation framework established by Haworth et al. (1985) and Whittaker (1991a), incorporating modern C4 and C5 fractions: [URL 🔗](#page-0)

These three expanded parameters form the core fluid-typing decision framework: Wet-

ness (Wh) evaluates fluid richness, Balance (Bh) delineates gas-liquid contacts, and Character (Ch) confirms fluid typing (Haworth et al., 1985; Whittaker, 1991a). [URL 🔗](#page-0)

Composite Fluid and Gas-Oil Ratio (GOR) Indicators To automate zone classification, the engine utilizes composite indicators that isolate heavy fractions (Whittaker, 1991b; Society of Petroleum Engineers, 2007): [URL 🔗](#page-0)


The GOWnoTG indicator decouples heavy gas composition from total gas fluctuations

caused by drilling mud weight changes or penetration rate variations. Additionally, the system calculates the combined Wetness-Balance Score (WBS):

A conditional Gas-Oil Ratio (GOR) screening index is applied based on established

engineering thresholds (Moore, 1986; Society of Petroleum Engineers, 2007): [URL 🔗](#page-0)

These multi-ratio outputs feed into a deterministic rule matrix (Mohaghegh, 2000) that [URL 🔗](#page-0)

classifies every depth increment into categorical zones: "Gas Zone," "Oil Zone," or "Water/Non- Productive Zone."

## 3.3 User Interface & Visualization Architecture

The frontend is constructed using the Dash Python Framework with dash-bootstrap-

components (dbc) to replace legacy, complex desktop interfaces with a responsive web da- shboard.

- Reactive Pipeline (app.callback): Callbacks detect file uploads or threshold cha- nges, executing the deterministic calculation engine in memory and updating visual gra- phs instantaneously without full page reloads.

- Modal File Ingestion (dcc.Upload & dbc.Modal): File parsing controls are conta- inerized inside modal dialogs to maintain a clean workspace.

- Multi-Track Plotly Visualizations: Processed indicators and zone classification flags are mapped to continuous vertical area tracks locked to measured depth (MD), replicating standardized wellsite mud logging templates.

## 3.4 System Validation and Performance Benchmarks

Because the core processing engine is strictly deterministic and operates on established

mathematical laws rather than stochastic machine learning models, validation focuses on three core software performance criteria: mathematical fidelity, computational throughput, and user system usability.


## 3.4.1 End-to-End Computational Throughput (< 5 Seconds)

In active drilling operations, operational decision windows are narrow. System efficien-

cy is evaluated by measuring the total latency (∆ttotal) spanning the entire automated pipeline:

The benchmark target requires ∆ttotal ≤ 5.0 seconds when processing dense mud logging data- sets spanning thousands of meters of depth (> 3000 m trajectories).

## 3.4.2 User Usability Evaluation

To validate the practical utility, interface clarity, and user satisfaction of the deployed

platform, system usability is evaluated through structured feedback sessions with practicing geoscientists, wellsite engineers, and peer researchers. After testing the application with real- world well logging datasets, each evaluator completes a structured evaluation form via Google Forms. The questionnaire consists of 10 targeted usability and functionality questions, with each item rated on a standard linear scale from 1 (poor) to 10 (excellent). An evaluator’s total usability score (Suser) is calculated by summing their ratings across all 10 items, yielding a possible total score ranging from 10 to 100 points:

where qi ∈ [1, 10] represents the individual score assigned to question i. The overall

system usability performance is measured by computing the average total score (S) across all N evaluators:

To confirm that the software delivers a highly intuitive and acceptable user experience,

the benchmark target for this research is established at a mean total usability score of S > 68.0 out of 100.


## CHAPTER IV

## Research Timeline

This chapter presents the planned schedule for the development and evaluation of the

hydrocarbon zone classification system, spanning five months from July to November. The work is organized into eight phases that follow the structure established in the methodology: literature consolidation, data preparation, algorithmic development, interface construction, tes- ting, and final documentation.

## 4.1 Phase Descriptions

## Literature Review & Finalization (July)

The opening phase consolidates the theoretical grounding of the research. This includes

a final review of the Pixler ratio framework Pixler (1969), the Haworth–Whittaker composite indicators Haworth et al. (1984, 1985), and existing mud logging interpretation workflows. Any gaps identified in the literature, particularly regarding the GOW, WBS, and GOR indicators are addressed before development begins. Deliverable: annotated bibliography and finalized Chapter 2. [URL 🔗](#page-0)

## Schema Definition (July–August)

The structural architecture of the data is formally established by defining the expected

column schema. This schema explicitly specifies the depth index alongside the seven requi- red alkane components: Methane (C1), Ethane (C2), Propane (C3), Iso-Butane (iC4), Normal- Butane (nC4), Iso-Pentane (iC5), and Normal-Pentane (nC5). Deliverable: Defined Schema Architecture

## System Architecture Design (July–August)

Before implementation begins, the three-layer architecture (parsing layer, logic layer, UI

layer) is designed in detail. This includes specifying the data flow between layers, the callback structure for the Dash application, and the classification threshold table for the majority-vote engine. Deliverable: architecture document and pseudocode for the classification pipeline.

## Data Parsing & Standardization Module (August)

The first implementation phase covers the ingestion pipeline described in Section 3.1:

file upload handling, column validation, null filtering, and z-score normalization. Deliverable: working parsing module.


## Algorithm & Classification Logic (August–September)

All fourteen hydrocarbon indicators (Pixler ratios, Haworth–Whittaker ratios, TG, GOW,

GOW No TG, WBS, GOR) are implemented and verified against hand-computed reference va- lues. The majority-vote classification engine is then built on top of the indicator outputs, along with the tie-breaking priority rule. Deliverable: fully tested indicator and classification modu- les.

## UI & Visualization Development (September)

The Dash application shell, upload modal, and results dashboard are built. Area charts of

each indicator trace and the colour-coded zone overlay are implemented in Plotly. The interface is validated against the parsed dataset from Phase 4. Deliverable: integrated Dash application with end-to-end data flow.

## System Testing & Evaluation (October)

The complete system is evaluated against the ground-truth well-test labels using the

classification metrics defined in Chapter 3: macro-averaged Accuracy, Precision, Recall, and F1-Score. The confusion matrix per zone class is computed, and performance on minority clas- ses (e.g. oil-bearing intervals) is examined in detail. Any misclassification patterns identified are traced back to individual indicators for potential threshold adjustment. Deliverable: evaluation results and performance tables for Chapter 4.

## Writing, Revision & Submission (October–November)

Concurrent with testing in October, revisions are done in response to supervisor fee-

dback. Chapter 4 (Results) and Chapter 5 (Discussion and Conclusion) are drafted once evalu- ation results are available. A full manuscript review is conducted in early November, followed by final proofreading and submission by the end of November. Deliverable: submitted thesis manuscript.

## 4.2 Gantt Chart

Table 4.1 presents the Gantt chart summarizing the timeline described above. The ho- [URL 🔗](#page-0)

rizontal axis spans twenty weeks divided into five monthly blocks (July through November). Each bar represents the planned active duration of its corresponding phase; overlapping bars indicate concurrent work.


*Figure 4.1: Planned research timeline, July–November 2025.*


## REFERENCES

- Archie, G. E. (1942). The electrical resistivity log as an aid in determining some reservoir characteristics. Transactions ofthe AIME, 146:54–62. doi:10.2118/942054-G. Foundational paper establishing the empirical relationship between formation resistivity, porosity, and fluid saturation. Verified via OnePetro and Semantic Scholar (Corpus ID: 13791882). [URL 🔗](http://dx.doi.org/10.2118/942054-G)

- Baker Hughes (2024). Worldwide rotary rig count and drilling statistics. rigcount.bakerhughes.com. Industry standard reference tracking thousands of active rotary drilling rigs operating worldwide. https://

- Dai, C., Si, X., dan Wu, X. (2024). FlexLogNet: A flexible deep learning-based well-log com- pletion method of adaptively using what you have to predict what you are missing. Computers & Geosciences, 191:105666. doi:10.1016/j.cageo.2024.105666. Verified via ScienceDirect and author CV (Georgia Tech). [URL 🔗](http://dx.doi.org/10.1016/j.cageo.2024.105666)

- Doveton, J. H. (2014). Principles ofMathematical Petrophysics. Oxford University Press, New York.

- Guan, Z., Tang, X., Ran, B., Guo, S., Zhang, J., Du, K., dan Jia, T. (2022). Machine-learning- based automatic well-log completion and generation: Examples from the Ordos Basin, China. Interpretation, 10(3):SJ91–SJ99. doi:10.1190/INT-2021-0228.1. Verified via GeoScience- World (SEG/Interpretation journal). [URL 🔗](http://dx.doi.org/10.1190/INT-2021-0228.1)

- Haworth, J. H., Sellens, M., dan Whittaker, A. (1985). Interpretation of hydrocarbon shows using light (C1–C5) hydrocarbon gases from mud-log data. AAPG Bulletin, 69(8):1305– 1310. doi:10.1306/AD462BDC-16F7-11D7-8645000102C1865D. [URL 🔗](http://dx.doi.org/10.1306/AD462BDC-16F7-11D7-8645000102C1865D)

- Haworth, J. H., Sellens, M. P., dan Gurvis, R. L. (1984). Reservoir characterization by analysis of light hydrocarbon shows. In Proceedings of the SPE Rocky Mountain Regional Meeting, Casper, Wyoming. SPE Paper No. 12914-MS.

- Ibrahim, A. F., Gowida, A., Ali, A., dan Elkatatny, S. (2021). Machine learning application to predict in-situ stresses from logging data. Scientific Reports, 11:23445. 021-02959-9. Verified via PubMed/PMC (PMC8648745). Open access. doi:10.1038/s41598-

- Mohaghegh, S. D. (2000). Virtual-intelligence applications in petroleum engineering: Part 1 — artificial neural networks. doi:10.2118/58046-JPT. Foundational reference on AI/expert-system methods in petroleum exploration; a well-cited, verified replacement for the unindexed ZEYBEK-1 preprint. Journal of Petroleum Technology, 52(9):64–73.

- Mondol, N. H. (2015). Well logging: Principles, applications and uncertainties. In Bjørlykke, K., editor, Petroleum Geoscience: From Sedimentary Environments to Rock Physics, pages


385–425. Springer, Berlin, Heidelberg. Verified via Springer Nature Link. Peer-reviewed book chapter.

- Moore, P. L. (1986). Drilling Practices Manual. PennWell Publishing Company, Tulsa, Okla- homa, 2nd edition.

- Pixler, B. O. (1969). Formation evaluation by analysis of hydrocarbon ratios. Journal ofPetro- leum Technology, 21(6):665–670. doi:10.2118/2254-PA. [URL 🔗](http://dx.doi.org/10.2118/2254-PA)

- Serra, O. dan Serra, L. (2004). Well Logging: Data Acquisition and Applications. Serralog, Méry Corbon, France.

- Society of Petroleum Engineers (2007). Petroleum Engineering Handbook: Volume V— Re- servoir Engineering and Petrophysics. Society of Petroleum Engineers, Richardson, TX. Provides industrial engineering thresholds and conditional logic parameters for Gas-Oil Ra- tio (GOR) classification during formatting valuation.

- Society of Petroleum Engineers, American Association of Petroleum Geologists, World Pe- troleum Council, Society of Petroleum Evaluation Engineers, dan Society of Exploration Geophysicists (2007). Petroleum Resources Management System. Society of Petroleum Engineers, Richardson, TX. The foundational PRMS document defining deterministic and probabilistic resource assessment procedures. Freely available at spe.org. Verified.

- Whittaker, A. (1991a). Mud Logging Handbook. Prentice Hall, Englewood Cliffs, NJ.

- Whittaker, A. (1991b). Mud Logging Handbook. Prentice Hall, Englewood Cliffs, NJ. Esta- blishes continuous composite screening evaluation curves including Gas-Oil-Water (GOW) fluid-typing relationships.

- Wood, D. A. (2020). Open-source python libraries for well-log data analysis and petro- physics: A practical review. Journal of Petroleum Science and Engineering, 195:107593. doi:10.1016/j.petrol.2020.107593. Discusses the high cost barriers of enterprise suites (Te- chlog, Geolog) and the growing necessity of open-source Python tools for log interpretation. [URL 🔗](http://dx.doi.org/10.1016/j.petrol.2020.107593)
