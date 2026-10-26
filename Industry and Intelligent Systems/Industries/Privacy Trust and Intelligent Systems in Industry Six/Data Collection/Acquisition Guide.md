# Original data acquisition

## Directly reproducible from UCI

Dataset numbers: AI4I 601, SECOM 179, Steel Plates 198, RT IoT 942. Use **Download Datasets.py** with `pip install pandas ucimlrepo`. Download to a local folder named `Local Data` and retain the emitted audit record. Large N BaIoT (UCI 442; approximately 1.7 GB) requires deliberate local acquisition.

## Industry-specific full datasets

Bosch CNC: https://github.com/boschresearch/CNC_Machining ; actual multi-machine production recordings. Clone the official source and retain machine/site grouping and recording times.

HAI/HAIEnd: https://github.com/icsdataset/hai ; industrial-control testbed attack sequences. Follow repository directions for Git LFS and version-specific licence.

TON IoT: https://research.unsw.edu.au/projects/toniot-datasets ; academic research use permitted; seek author permission for commercial use.

Edge IIoTset: https://ieee-dataport.org/8939 ; access subject to IEEE DataPort's terms.

CIC IoT: https://www.unb.ca/cic/datasets/iotdataset-2023.html ; real lab IoT devices and 33 attack types; verify provider terms.

N BaIoT: https://archive.ics.uci.edu/dataset/442 ; real infected devices; CC BY 4.0.

RT IoT: https://archive.ics.uci.edu/dataset/942 ; UCI download code provided; CC BY 4.0.

NASA: https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/ ; simulated engine degradation, review donor citation and usage instructions.

SWaT: https://www.sutd.edu.sg/itrust/itrust-labs/datasets/terms-of-usage/ ; requires access request and **prohibits redistribution**. Never upload it to GitHub.

## Integrity and research validity

Log download time, SHA-256, schema, licensing, event chronology and machine/client identity. A registry entry is not a downloaded dataset. Large files remain outside regular Git history until separately acquired in a compliant data store. Do not treat arbitrary simulated data splits as actual federation across industrial plants.

## Bosch CNC measured vibration data and machine-based federation

Original repository: https://github.com/boschresearch/CNC_Machining

The original data are sampled at 2 kHz across three physical CNC machines, fifteen operations and annotated normal/abnormal processes. Dataset: CC BY 4.0; companion utility code: BSD-3-Clause. Cite Tnani, Feil and Diepold, "Smart Data Collection System for Brownfield CNC Milling Machines", https://doi.org/10.1016/j.procir.2022.04.022.

Retrieve the original repository with `git clone https://github.com/boschresearch/CNC_Machining`, preserve the exact upstream commit SHA and run:

    python -m pip install "numpy>=1.26,<3" "pandas>=2,<3" "scipy>=1.12,<2" "h5py>=3.11,<4"
    python "Data Collection/Prepare Bosch CNC Features.py" --data-root "/path/to/CNC_Machining/data" --output-dir "Local Data"

The derived feature table retains machine, operation, label, timeframe, source SHA and non-identifying sensor statistics. Raw HDF5 recordings stay in the original external source. A source file is an observed recording from a known machine, but not evidence of distinct companies.

Recommended external validity: leave one machine out for cross-machine evaluation; where feasible reserve an entire later timeframe for temporal testing. Group repeated process recordings to avoid adjacent-window leakage. Any training on single-source AI4I, SECOM, steel, power or gas turbine data must be described as simulated federation. Do not present dataset-size or machine-count increases as evidence of real multinational collaborative learning.
