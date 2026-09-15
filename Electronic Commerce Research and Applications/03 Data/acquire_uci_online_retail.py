from pathlib import Path
from ucimlrepo import fetch_ucirepo

OUT = Path("data/raw/uci-online-retail")
OUT.mkdir(parents=True, exist_ok=True)

dataset = fetch_ucirepo(id=352)

# UCI exposes the dataset through its repository client. Preserve the fetched
# feature table exactly and keep any later cleaning in a separate processed step.
dataset.data.features.to_csv(OUT / "online_retail_features.csv", index=False)
dataset.variables.to_csv(OUT / "variables.csv", index=False)

print(f"Saved UCI Online Retail source tables to {OUT}")
print("Do not overwrite these source files during cleaning or causal feature engineering.")
