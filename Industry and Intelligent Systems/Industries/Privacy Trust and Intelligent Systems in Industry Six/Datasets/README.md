# Datasets and source attribution

## Source licences

AI4I maintenance (UCI 601), SECOM semiconductor data (UCI 179) and Steel Plates Faults (UCI 198) are CC BY 4.0 on the UCI repository. Cite respective original DOIs 10.24432/C5HS5C, 10.24432/C54305 and 10.24432/C5J88N.

Actual dataset transfers in this project use public GitHub mirrors, with primary repository metadata as authority for licensing and original attribution. AI4I mirror: https://github.com/tayyabrehman96/XAI-PdMNet-Bench-Industry-5.0/tree/main/data/ai4i. Steel fault mirror: https://github.com/SabareeswaranC/steel-plate-fault-classification/tree/main/data. SECOM mirror: https://github.com/Be1an001/semiconductor-pass-fail-prediction-python/tree/main/data.

AI4I has 10,000 examples and 14 fields; it is synthetic. Its binary machine failure label must never be predicted using the downstream failure-mode flags TWF, HDF, PWF, OSF or RNF.

SECOM has 1,567 production measurements with 590 recorded sensor values and companion pass/fail outcomes; it contains missing values. The original dataset metadata also uses a 591-attribute counting convention. Where mirrored raw files are not present, use the UCI downloader.

Steel Plates Faults has 1,941 observed quality records. The mirrored CSV recodes the seven source outcome flags into a single class label. Verify correspondence against UCI's original data.

## External dataset rules

The larger Bosch, HAI, TON IoT, CIC IoT, Edge IIoTset, N BaIoT and NASA holdings require source-specific download procedures. SWaT cannot be redistributed under iTrust's dataset conditions; obtain separate authorised access.

Every dataset included in an experiment must have an acquisition date, immutable source/version, SHA-256 checksum, licence, measurement schema, cohort definition, split file and preprocessing code.

## Combined Cycle Power Plant (added 26 October 2026)

Original: UCI repository dataset 294, DOI 10.24432/C5002N; CC BY 4.0. Original researchers Pınar Tüfekci and Heysem Kaya. The dataset contains 9,568 observed hourly power-plant performance records with four predictors (AT, V, AP, RH) and continuous target PE (MW). The committed CSV is taken from the public mirror https://github.com/YungChunLu/UCI-Power-Plant/blob/master/data.csv; line endings were converted to LF without changing field values. Integrity checked: 9,568 rows, five columns, all numerical, PE ranges 420.26–495.76. The source provided shuffled observations; dates and facility IDs are unavailable. Use regression-specific evaluation and simulated clients only; never describe the records as independent industrial sites or naturally chronological partitions.

## Gas Turbine Emissions (registered 26 October 2026)

UCI dataset 551, DOI 10.24432/C5WC95, CC BY 4.0, includes 36,733 observed hourly turbine measurements in five annual CSV files. Download via UCI with the supplied downloader. The source describes chronology within original year files, but no independent industrial clients. Model targets CO or NOx separately, excluding other outcome targets as appropriate to each prediction question. Raw files have not yet been committed.

## Research corpus as of 26 October 2026

The full project now stores 182,926 source observations, including 49,809 measured industrial-production observations, 123,117 IoT testbed network records and 10,000 synthetic maintenance records. These are separate prediction tasks and must never be treated as interchangeable data from independent factories.

The newly committed gas-turbine source consists of five original UCI annual files, with source hashes in Datasets/Gas Turbine Annual Records/Acquisition Audit.json. The original RT-IoT2022 UCI source is stored as a ZIP with source hashes and label counts in Datasets/IoT Intrusion Source/Acquisition Audit.json. Both are CC BY 4.0. The Research Corpus Manifest.json distinguishes observed and synthetic evidence, experimental tasks, file locations and critical external-validity restrictions.
