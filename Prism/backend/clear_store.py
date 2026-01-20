
import os
from pathlib import Path

data_dir = Path(r"c:\Users\ASUS\Desktop\Prism for ScotAI\Prism\backend\data\vector_store")

def clear_vector_store():
    files = ["faiss_index.bin", "metadata.pkl"]
    for f in files:
        p = data_dir / f
        if p.exists():
            try:
                os.remove(p)
                print(f"Deleted {p}")
            except Exception as e:
                print(f"Failed to delete {p}: {e}")
        else:
            print(f"{f} not found.")

if __name__ == "__main__":
    clear_vector_store()
