# Data Integration

This folder contains the occupation linkage used for the Strategic Organization study.

## Files

- `Strategic_Organization_Integrated_Dataset.xlsx` contains the original 200 participant records, occupation mappings, ILO GenAI exposure categories, analytical exposure recodes and capability indices.
- `ISCO08_Career_Interest_Crosswalk.csv` maps all non-missing career-interest labels to ISCO-08 unit groups.
- `ISCO08_Current_Function_Crosswalk.csv` records current-job-function coding. Broad sector/category labels are intentionally left unmapped.
- The workbook also contains `Career Crosswalk`, `Current Function Crosswalk`, `ILO Exposure Lookup`, `Integration Method` and `Validation` sheets.

## Primary linkage decision

Career Interest is the main occupational linkage because 198 of 200 participants report a granular career interest and all 198 non-missing values can be mapped. Current Job Function is retained for exploratory analysis only because most responses are broad functional categories.

## Exposure variable

The primary exposure measure is the official ILO 2025 GenAI occupational exposure category for the mapped ISCO-08 unit group.

The 0–5 exposure ordinal in the workbook is a project-created analytical recode:

- 0 = Not Exposed
- 1 = Minimal Exposure
- 2 = Exposed: Gradient 1
- 3 = Exposed: Gradient 2
- 4 = Exposed: Gradient 3
- 5 = Exposed: Gradient 4

It must not be described as an ILO continuous exposure score.

## Source

ILO/NASK 2025 GenAI occupational exposure dataset:
https://github.com/pgmyrek/2025_GenAI_scores_ISCO08/blob/main/Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx
