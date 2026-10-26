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
