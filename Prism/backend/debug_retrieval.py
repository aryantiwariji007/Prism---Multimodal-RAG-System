
import json
import glob
from pathlib import Path

def inspect_chunks():
    processed_dir = Path("c:/Users/ASUS/Desktop/Prism for ScotAI/Prism/backend/data/processed")
    
    # Pattern to match the potential file IDs
    # The file_id is derived from the stem of the original filename
    patterns = [
        "*EPI*Supplier*Questionnaire*.json",
        "*QF006*.json"
    ]
    
    files_found = 0
    for pattern in patterns:
        for file_path in processed_dir.glob(pattern):
            files_found += 1
            print(f"\n--- Inspecting: {file_path.name} ---")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    chunks = data.get("chunks", [])
                    metadata = data.get("metadata", {})
                    print(f"Metadata: {metadata}")
                    print(f"Total chunks: {len(chunks)}")
                    
                    found_section_4 = False
                    for i, chunk in enumerate(chunks):
                        text = chunk.get("text", "")
                        # Case insensitive search for Section 4 or OHS
                        if "section 4" in text.lower() or "occupational health" in text.lower():
                            print(f"\n[Chunk {i}] (Matches 'Section 4' or 'Occupational Health'):")
                            print("-" * 40)
                            print(text[:500] + "..." if len(text) > 500 else text) 
                            print("-" * 40)
                            found_section_4 = True
                            
                    if not found_section_4:
                        print("\nWARNING: 'Section 4' not found in any chunk!")
                        # Print first few chunks to see what it looks like
                        print("\nFirst 3 chunks sample:")
                        for i in range(min(3, len(chunks))):
                            print(f"[Chunk {i}]: {chunks[i].get('text', '')[:200]}...")

            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    if files_found == 0:
        print("No matching processed files found.")

if __name__ == "__main__":
    inspect_chunks()
