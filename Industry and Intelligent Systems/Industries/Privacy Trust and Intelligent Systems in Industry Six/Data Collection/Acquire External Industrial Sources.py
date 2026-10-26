"""Fetch the Bosch CNC and HAI source repositories at pinned commits and verify them.

Raw recordings are kept outside this repository (Bosch: 1.8 GB of HDF5; HAI: 187 MB of
compressed CSV). Derived tables committed under Datasets are rebuilt from these sources with
Prepare Bosch CNC Features.py and Prepare HAI Window Features.py.

Usage:
    python "Acquire External Industrial Sources.py" --target "/path/outside/repository"
"""
import argparse
import hashlib
import subprocess
from pathlib import Path

SOURCES = {
    "bosch": {"url": "https://github.com/boschresearch/CNC_Machining",
              "commit": "d60581d6a3ab6015dcc5488c3d76112bb8e1bcb1", "paths": ["data"]},
    "hai": {"url": "https://github.com/icsdataset/hai",
            "commit": "2a814cebc9a66b06c9e5cd545e2d72e65d383737", "paths": ["hai-21.03", "README.md"]},
}
HAI_SHA256 = {  # values recorded in Datasets/HAI Industrial Control/HAI Acquisition Audit.json
    "test1.csv.gz", "test2.csv.gz", "test3.csv.gz", "test4.csv.gz", "test5.csv.gz",
}


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--target", required=True)
    args = cli.parse_args()
    root = Path(args.target)
    root.mkdir(parents=True, exist_ok=True)
    for name, spec in SOURCES.items():
        folder = root / name
        if not folder.exists():
            run(["git", "clone", "--filter=blob:none", "--no-checkout", spec["url"], str(folder)])
        run(["git", "fetch", "--depth", "1", "origin", spec["commit"]], cwd=folder)
        run(["git", "checkout", spec["commit"], "--", *spec["paths"]], cwd=folder)
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=folder, capture_output=True, text=True).stdout.strip()
        print(name, "checked out at", spec["commit"], "(clone HEAD", head + ")")
    count = len(list((root / "bosch" / "data").glob("M*/OP*/*/*.h5")))
    if count != 1702:
        raise SystemExit(f"Bosch recordings: expected 1702, found {count}")
    for file in sorted(HAI_SHA256):
        path = root / "hai" / "hai-21.03" / file
        print(file, hashlib.sha256(path.read_bytes()).hexdigest())
    print("Bosch recordings verified:", count)


if __name__ == "__main__":
    main()
