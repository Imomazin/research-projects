"""Reassemble the losslessly segmented SECOM industrial sensor matrix."""
from pathlib import Path
import hashlib

root = Path(__file__).resolve().parent.parent
folder = root / "Datasets" / "Semiconductor Segments"
target = root / "Datasets" / "Semiconductor Sensors Rebuilt.txt"
parts = sorted(folder.glob("Part *.txt"))
assert len(parts) == 13, "Incomplete SECOM source segments"
count = 0
digest = hashlib.sha256()
with target.open("wb") as writer:
    for file in parts:
        data = file.read_bytes()
        digest.update(data)
        writer.write(data)
        for line in data.decode("utf-8").splitlines():
            if line.strip():
                assert len(line.split()) == 590, "Unexpected sensor width"
                count += 1
labels = [row for row in (folder / "Labels.txt").read_text().splitlines() if row.strip()]
assert count == 1567 and len(labels) == 1567, "Row alignment mismatch"
assert sum(row.split()[0] == "1" for row in labels) == 104, "Label mismatch"
print(f"Validated {count} observations; SHA-256 {digest.hexdigest()}")
