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
