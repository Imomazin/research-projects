"""Rebuild Datasets/Source Register.csv from the committed data and recorded provenance.

Quantities that can be computed (rows, attributes, missing share, class distribution,
SHA-256) are computed from the committed files through the study loaders. Provenance fields
come from the acquisition audits and source documentation listed in each row.
"""
import csv
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "Experiments" / "Private Risk Control" / "Private Risk Control Library.py"
spec = importlib.util.spec_from_file_location("private_risk_control", LIB)
L = importlib.util.module_from_spec(spec)
sys.modules["private_risk_control"] = L
spec.loader.exec_module(L)

ACQUIRED = {
    "maintenance": dict(name="AI4I 2020 Predictive Maintenance", ident="UCI 601", org="UCI Machine Learning Repository (donor S. Matzka)",
                        citation="Matzka 2020, AI4I conference, pp. 69-74", doi="10.24432/C5HS5C", acquired="2026-10-26 (earlier commit)",
                        version="Public GitHub mirror of the UCI file; values unchanged", url="https://archive.ics.uci.edu/dataset/601",
                        licence="CC BY 4.0", redistribution="Permitted with attribution", evidence="Synthetic",
                        relevance="Machine failure prediction for a milling process (synthetic)", outcome="Machine failure (binary)",
                        clients="None; clients are simulated", temporal="None", scenarios="Simulated Dirichlet federation; i.i.d. test",
                        limitations="Synthetic generator; failure modes deterministic in source; must exclude TWF, HDF, PWF, OSF, RNF"),
    "steel": dict(name="Steel Plates Faults", ident="UCI 198", org="UCI Machine Learning Repository (Buscema, Terzi, Tastle)",
                  citation="Buscema, Terzi, Tastle 2010 [dataset]", doi="10.24432/C5J88N", acquired="2026-10-26 (earlier commit)",
                  version="Mirror SabareeswaranC/steel-plate-fault-classification commit f1adcca; file identical (SHA-256 checked)",
                  url="https://archive.ics.uci.edu/dataset/198", licence="CC BY 4.0", redistribution="Permitted with attribution",
                  evidence="Observed industrial measurements", relevance="Surface defect classification of steel plates",
                  outcome="Seven defect classes collapsed from one-hot flags (mirror script asserts one flag per row)",
                  clients="None; clients are simulated", temporal="None", scenarios="Simulated federation; selective classification",
                  limitations="Single source; mirror spells K_Scatch as K_Scratch"),
    "semiconductor": dict(name="SECOM", ident="UCI 179", org="UCI Machine Learning Repository (McCann, Johnston)",
                          citation="McCann and Johnston 2008 [dataset]", doi="10.24432/C54305", acquired="2026-10-26 (earlier commit)",
                          version="Thirteen lossless row segments of the UCI matrix plus labels", url="https://archive.ics.uci.edu/dataset/179",
                          licence="CC BY 4.0", redistribution="Permitted with attribution", evidence="Observed industrial measurements",
                          relevance="Semiconductor pass or fail yield prediction", outcome="Fail (binary)",
                          clients="None; clients are simulated", temporal="Label timestamps exist but are not used",
                          scenarios="Simulated federation; i.i.d. test", limitations="104 failures; 590 sensors with missing values"),
    "power": dict(name="Combined Cycle Power Plant", ident="UCI 294", org="UCI Machine Learning Repository (Tüfekci, Kaya)",
                  citation="Tüfekci 2014, Int J Electr Power Energy Syst 60", doi="10.24432/C5002N", acquired="2026-10-26 (earlier commit)",
                  version="Mirror YungChunLu/UCI-Power-Plant data.csv after row and schema checks", url="https://archive.ics.uci.edu/dataset/294",
                  licence="CC BY 4.0", redistribution="Permitted with attribution", evidence="Observed plant measurements",
                  relevance="Net electrical output regression (MW)", outcome="PE (MW)", clients="None; clients are simulated",
                  temporal="Source rows shuffled; no chronology", scenarios="Simulated federation; prediction intervals",
                  limitations="Four predictors; one plant"),
    "gas": dict(name="Gas Turbine CO and NOx Emissions", ident="UCI 551", org="UCI Machine Learning Repository (Kaya, Tüfekci, Uzun)",
                citation="Kaya, Tüfekci, Uzun 2019, Turk J Elec Eng Comp Sci 27(6):4783-4796", doi="10.24432/C5WC95",
                acquired="2026-10-26 (earlier commit)", version="Five original annual files with SHA-256 audit",
                url="https://archive.ics.uci.edu/dataset/551", licence="CC BY 4.0", redistribution="Permitted with attribution",
                evidence="Observed turbine measurements", relevance="NOx emission regression (mg/m3)", outcome="NOX (mg/m3)",
                clients="None; clients are simulated", temporal="Annual files 2011-2015",
                scenarios="Federation on 2011-2013; out-of-period tests 2014 and 2015; recalibration on 2014",
                limitations="Single turbine; 2015 was inspected in the pilot, so it is not a blind test"),
    "iot": dict(name="RT-IoT2022", ident="UCI 942", org="UCI Machine Learning Repository (Sharmila, Nagapadma)",
                citation="Sharmila and Nagapadma 2023, Cybersecurity 6", doi="10.24432/C5P338", acquired="2026-10-26 (earlier commit)",
                version="Original UCI ZIP with SHA-256 audit", url="https://archive.ics.uci.edu/dataset/942", licence="CC BY 4.0",
                redistribution="Permitted with attribution", evidence="Observed IoT testbed traffic with generated attacks",
                relevance="Network intrusion detection for connected devices", outcome="Attack (binary; benign = Thing_Speak, MQTT_Publish, Wipro_bulb)",
                clients="None verified; clients are simulated", temporal="No flow timestamps used",
                scenarios="Simulated federation; i.i.d. test", limitations="Attacks are the majority class; not manufacturing traffic"),
    "bosch": dict(name="Bosch CNC Machining", ident="GitHub boschresearch/CNC_Machining (UCI 752)", org="Bosch Research / Technical University of Munich",
                  citation="Tnani, Feil, Diepold 2022, Procedia CIRP 107:131-136", doi="10.1016/j.procir.2022.04.022",
                  acquired="2026-10-26", version="Commit d60581d6a3ab6015dcc5488c3d76112bb8e1bcb1; 1,702 HDF5 recordings (UCI lists 2,700 instances)",
                  url="https://github.com/boschresearch/CNC_Machining", licence="CC BY 4.0 (data); BSD-3-Clause (code)",
                  redistribution="Derived feature table committed; raw HDF5 kept outside the repository (1.8 GB)",
                  evidence="Observed vibration of three production CNC machines", relevance="Process anomaly detection on machine tools",
                  outcome="Anomaly (bad process label, binary)", clients="Three physical machines M01, M02, M03 (not companies)",
                  temporal="Six-month timeframes Feb 2019 to Aug 2021", scenarios="Machine federation; later-period test; leave-one-machine-out",
                  limitations="70 anomalies; 9 on M03; one feature row per recording"),
    "hai": dict(name="HAI 21.03 industrial control security", ident="GitHub icsdataset/hai, version 21.03", org="HAI dataset authors (Shin, Lee, Yun, Min); provider listed as ETRI in the earlier register",
                citation="Shin, Lee, Yun, Min 2021, CSET '21, pp. 36-40", doi="10.1145/3474718.3474719", acquired="2026-10-26",
                version="Commit 2a814cebc9a66b06c9e5cd545e2d72e65d383737; attack files test1-test5",
                url="https://github.com/icsdataset/hai", licence="CC BY-SA 4.0",
                redistribution="Derived window table committed under CC BY-SA 4.0; raw files kept outside the repository",
                evidence="Hardware-in-the-loop testbed with scripted attacks", relevance="Attack detection in boiler, turbine and water-treatment control",
                outcome="Attack window (binary; any attacked second in 30 s)", clients="Recording sessions test1-test3 (one testbed, not plants)",
                temporal="Chronological sessions July 2020", scenarios="Session federation; later sessions test4-test5; event detection delay",
                limitations="Testbed; normal-only training files not used; 50 attack events"),
}
NOT_ACQUIRED = [
    ("TON_IoT", "UNSW Canberra", "https://research.unsw.edu.au/projects/toniot-datasets", "Academic use; commercial use needs permission",
     "Not acquired: host unreachable from the execution environment; would duplicate the IoT intrusion role of RT-IoT2022"),
    ("Edge-IIoTset", "IEEE DataPort", "https://ieee-dataport.org/8939", "Registration required; verify redistribution",
     "Not acquired: host unreachable and registration required; cited as related federated intrusion benchmark"),
    ("CIC IoT 2023", "Canadian Institute for Cybersecurity", "https://www.unb.ca/cic/datasets/iotdataset-2023.html", "Provider conditions",
     "Not acquired: host unreachable; consumer IoT devices rather than industrial production"),
    ("N-BaIoT", "UCI 442", "https://archive.ics.uci.edu/dataset/442", "CC BY 4.0",
     "Not acquired: host unreachable; about 1.7 GB of consumer IoT traffic with no added industrial validation purpose"),
    ("NASA turbofan (C-MAPSS)", "NASA PCoE", "https://www.nasa.gov/intelligent-systems-division/", "Confirm donor conditions",
     "Not acquired: host unreachable; simulated degradation duplicates the synthetic role of AI4I"),
    ("SWaT", "SUTD iTrust", "https://www.sutd.edu.sg/itrust/itrust-labs/datasets/terms-of-usage/", "No redistribution; signed agreement",
     "Not requested: licence forbids public storage; HAI covers the industrial control role"),
]
COLUMNS = ["Dataset", "Identifier", "Source organisation", "Original citation", "DOI", "Acquisition date", "Version or commit",
           "Download status", "Source URL", "Licence", "Redistribution", "Observed or synthetic", "Industrial relevance",
           "Observations", "Attributes", "Outcome", "Missing share", "Class distribution", "Natural clients",
           "Temporal information", "Supported evaluation scenarios", "Known limitations", "SHA-256 of committed files",
           "Validation outcome"]


def main():
    rows = []
    for key, meta in ACQUIRED.items():
        task = L.load_task(key)
        X = task.X.to_numpy(dtype=float)
        if task.kind == "binary":
            dist = f"positive {int(task.y.sum())} of {len(task.y)} ({task.y.mean():.2%})"
        elif task.kind == "multiclass":
            dist = "; ".join(f"{n} {int((task.y == i).sum())}" for i, n in enumerate(task.class_names))
        else:
            dist = f"mean {task.y.mean():.2f}, SD {task.y.std():.2f} {task.unit}"
        rows.append({"Dataset": meta["name"], "Identifier": meta["ident"], "Source organisation": meta["org"],
                     "Original citation": meta["citation"], "DOI": meta["doi"], "Acquisition date": meta["acquired"],
                     "Version or commit": meta["version"], "Download status": "Committed and verified",
                     "Source URL": meta["url"], "Licence": meta["licence"], "Redistribution": meta["redistribution"],
                     "Observed or synthetic": meta["evidence"], "Industrial relevance": meta["relevance"],
                     "Observations": len(task.y), "Attributes": int(task.X.shape[1]), "Outcome": meta["outcome"],
                     "Missing share": f"{np.isnan(X).mean():.4%}", "Class distribution": dist,
                     "Natural clients": meta["clients"], "Temporal information": meta["temporal"],
                     "Supported evaluation scenarios": meta["scenarios"], "Known limitations": meta["limitations"],
                     "SHA-256 of committed files": json.dumps(task.hashes),
                     "Validation outcome": "Passed loader checks and Test Private Risk Control.py"})
    for name, org, url, licence, reason in NOT_ACQUIRED:
        rows.append({c: "" for c in COLUMNS} | {"Dataset": name, "Source organisation": org, "Source URL": url,
                                                 "Licence": licence, "Download status": reason,
                                                 "Validation outcome": "Not applicable"})
    out = ROOT / "Datasets" / "Source Register.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)
    print("rows", len(rows))


if __name__ == "__main__":
    main()
