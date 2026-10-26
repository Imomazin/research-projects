# Semiconductor manufacturing data

The UCI SECOM dataset, McCann and Johnston (2008), DOI https://doi.org/10.24432/C54305, is licensed CC BY 4.0.

Original dataset: https://archive.ics.uci.edu/dataset/179/secom

Raw mirror: https://github.com/Be1an001/semiconductor-pass-fail-prediction-python/tree/main/data

The complete original sensor data are stored as 13 lossless, sequential parts, named Part A.txt through Part M.txt, split only at record boundaries. Concatenate in alphabetical order to recreate the source sensor matrix. The original labels and metadata are stored in this directory.

Records: 1,567, with 590 sensor values each. Label records: 1,567. Failures: 104. This dataset provides no verified independent factory identifiers. Use temporal holdouts when timestamps allow and clearly flag simulated-client federation.

Reconstruction script: Data Collection/Rebuild Semiconductor.py.
