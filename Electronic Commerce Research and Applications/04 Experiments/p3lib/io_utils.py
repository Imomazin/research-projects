"""Machine-readable result IO: JSON, CSV, Parquet."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List

import pandas as pd


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def write_json(obj: Any, path: str) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=False, default=float)


def write_table(rows: List[Dict[str, Any]], path_no_ext: str, parquet: bool = True) -> pd.DataFrame:
    ensure_dir(os.path.dirname(path_no_ext))
    df = pd.DataFrame(rows)
    df.to_csv(path_no_ext + ".csv", index=False)
    if parquet:
        try:
            df.to_parquet(path_no_ext + ".parquet", index=False)
        except Exception:
            pass
    return df
