
import pickle
import sys
import numpy as np
from pathlib import Path
from typing import List, Dict

sys.path.append(str(Path.cwd()))
from app.services.vector_service import vector_service

# Load metadata manually to search text
metadata_path = Path("data/vector_store/metadata.pkl")
if not metadata_path.exists():
    print("No metadata found.")
    sys.exit(1)

with open(metadata_path, "rb") as f:
    metadata = pickle.load(f)

search_terms = ["HSE Exposure Hours", "Manhours Office", "21,120"]
found_chunks = []

print(f"Searching {len(metadata)} chunks for terms: {search_terms}")

file_ids_found = set()

for chunk in metadata:
    text = chunk.get("text", "")
    found = False
    for term in search_terms:
        if term.lower() in text.lower():
            found = True
            break
    
    if found:
        file_ids_found.add(chunk.get("file_id"))
        found_chunks.append(chunk)
        print(f"\n--- MATCH FOUND (File: {chunk.get('file_id')}) ---")
        print(f"Preview: {text[:200]}...")
        if "21,120" in text:
            print("!! Contains target value 21,120 !!")

print(f"\nTotal matches: {len(found_chunks)}")
print(f"Unique files: {file_ids_found}")

# Now try the actual vector search to see if it retrieves these chunks
query = "what are HSE hours for manhours office in 2010?"
print(f"\nPerforming vector search for: '{query}'")
results = vector_service.search(query, k=5)

print("\n--- Search Results ---")
for i, res in enumerate(results):
    score = res['score']
    text = res['chunk'].get('text', '')[:100].replace('\n', ' ')
    fid = res['chunk'].get('file_id')
    print(f"{i+1}. [Score: {score:.4f}] [File: {fid}] {text}...")
