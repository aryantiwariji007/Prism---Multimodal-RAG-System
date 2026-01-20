
import sys
import pickle
from pathlib import Path

metadata_path = Path(r"c:\Users\ASUS\Desktop\Prism for ScotAI\Prism\backend\data\vector_store\metadata.pkl")

def check_metadata():
    if not metadata_path.exists():
        print("Metadata file not found.")
        return

    try:
        with open(metadata_path, "rb") as f:
            metadata = pickle.load(f)
            
        print(f"Total chunks in metadata: {len(metadata)}")
        
        qd040_chunks = [m for m in metadata if "QD040" in m.get('file_id', '')]
        print(f"QD040 chunks found: {len(qd040_chunks)}")
        
        if qd040_chunks:
            print("Sample chunk text:")
            print(qd040_chunks[0].get('text', '')[:100])
            
    except Exception as e:
        print(f"Error reading metadata: {e}")

if __name__ == "__main__":
    check_metadata()
