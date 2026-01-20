
import pickle
import sys
from pathlib import Path
from collections import Counter

# Add backend to path so we can unpickle if there are custom classes (though metadata is usually dicts)
sys.path.append(str(Path.cwd()))

metadata_path = Path("data/vector_store/metadata.pkl")

if not metadata_path.exists():
    print(f"No metadata found at {metadata_path}")
    sys.exit(1)

with open(metadata_path, "rb") as f:
    metadata = pickle.load(f)

print(f"Total chunks (vectors): {len(metadata)}")

# Count chunks per file
file_counts = Counter()
for chunk in metadata:
    # Try different keys that might hold the filename/id
    file_id = chunk.get("file_id") or chunk.get("source") or "unknown"
    file_counts[file_id] += 1

print(f"Total unique files: {len(file_counts)}")
print("\nTop 10 files by chunk count:")
for file_id, count in file_counts.most_common(10):
    print(f"- {file_id}: {count} chunks")
