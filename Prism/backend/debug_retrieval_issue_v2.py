
import pickle
import sys
import numpy as np
from pathlib import Path
from typing import List, Dict

sys.path.append(str(Path.cwd()))
from app.services.vector_service import vector_service

output_file = Path("debug_retrieval_output.txt")

def log(msg):
    with open(output_file, "a", encoding='utf-8') as f:
        f.write(msg + "\n")
    print(msg)

# Clear previous output
if output_file.exists():
    output_file.unlink()

# Load metadata manually to search text
metadata_path = Path("data/vector_store/metadata.pkl")
if not metadata_path.exists():
    log("No metadata found.")
    sys.exit(1)

with open(metadata_path, "rb") as f:
    metadata = pickle.load(f)

search_terms = ["Manhours Office", "21,120"]
found_chunks = []

log(f"Searching {len(metadata)} chunks for terms: {search_terms}")

file_ids_found = set()

for chunk in metadata:
    text = chunk.get("text", "")
    found = False
    # Check if this looks like the table
    if "Manhours Office" in text and "2010" in text:
        found = True
    
    if found:
        file_ids_found.add(chunk.get("file_id"))
        found_chunks.append(chunk)
        log(f"\n--- MATCH FOUND (File: {chunk.get('file_id')}) ---")
        log(f"Preview: {text}...") # Print more text to see the table structure
        if "21,120" in text:
            log("!! Contains target value 21,120 !!")
        else:
            log("!! Target value 21,120 NOT found in this chunk !!")

log(f"\nTotal matches: {len(found_chunks)}")
log(f"Unique files: {file_ids_found}")

# Now try the actual vector search to see if it retrieves these chunks
query = "what are HSE hours for manhours office in 2010?"
log(f"\nPerforming vector search for: '{query}'")
results = vector_service.search(query, k=10)

log("\n--- Search Results ---")
for i, res in enumerate(results):
    score = res['score']
    text = res['chunk'].get('text', '')[:100].replace('\n', ' ')
    fid = res['chunk'].get('file_id')
    log(f"{i+1}. [Score: {score:.4f}] [File: {fid}] {text}...")
