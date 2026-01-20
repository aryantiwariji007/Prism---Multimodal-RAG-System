
import pickle
import sys
from pathlib import Path
from collections import Counter

sys.path.append(str(Path.cwd()))
metadata_path = Path("data/vector_store/metadata.pkl")

if not metadata_path.exists():
    print("NO_METADATA")
    sys.exit(0)

with open(metadata_path, "rb") as f:
    data = pickle.load(f)

print(f"COUNT:{len(data)}")

counts = Counter()
for x in data:
    fid = x.get("file_id") or "unknown"
    counts[fid] += 1

print(f"FILES:{len(counts)}")
# Print first 5
for fid, c in counts.most_common(5):
    print(f"FILE:{fid}: {c}")
