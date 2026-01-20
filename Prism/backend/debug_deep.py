
import sys
from pathlib import Path

sys.path.append(str(Path.cwd()))
from app.services.folder_service import folder_service
from app.services.vector_service import vector_service

folder_id = "ec6d114f-f54c-428d-8b2c-9af8448f01c9"
target_file_id = "95ba984c-f426-4e7a-b1f2-a1e10f130e51_EPI HSE Exposure Hours 2021.pdf"

print(f"Checking folder {folder_id}...")
files = folder_service.get_files_in_folder(folder_id)
print(f"Count: {len(files)}")
print(f"Target file in folder: {target_file_id in files}")

if target_file_id not in files:
    print("CRITICAL: Target file NOT in folder list returned by service!")
    # Print some files to see what they look like
    print("Files in folder:", list(files)[:5])
else:
    print("Target file IS in folder list.")

print("\nChecking Vector Search recall...")
query = "what are HSE hours for manhours office in 2010?"
results = vector_service.search(query, k=5000)

found_rank = -1
for i, res in enumerate(results):
    fid = res['chunk'].get('file_id')
    if fid == target_file_id:
        found_rank = i
        print(f"Found target file at rank {i+1}")
        print(f"Score: {res['score']}")
        print(f"Text snippet: {res['chunk'].get('text')[:100]}")
        break  # Found at least one chunk

if found_rank == -1:
    print("CRITICAL: Target file NOT found in top 5000 vector search results!")
else:
    print(f"Target file found at rank {found_rank+1}")

