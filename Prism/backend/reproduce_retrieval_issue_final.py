
import sys
import logging
from pathlib import Path
import time

# Setup simple logging
logging.basicConfig(level=logging.INFO)

sys.path.append(str(Path.cwd()))
from app.services.qa_service import qa_service
from app.services.vector_service import vector_service

folder_id = "1aec18b0-9e33-43e7-acaf-78090c31a555" # Quality
target_file_id = "e3a31f4c-5488-48fd-9c61-a731fa715969_QF033_Agents Questionnaire.docx"
question = "what are EPI's information to agents or agencies"

print(f"Asking question: '{question}' in folder: {folder_id}")

# 1. Check Vector Retrieval Rank
print("\n--- Step 1: Vector Search Rank ---")
search_k = 5000
candidates = vector_service.search(question, k=search_k)
print(f"Total candidates retrieved: {len(candidates)}")

target_ranks = []
for i, cand in enumerate(candidates):
    if cand["chunk"]["file_id"] == target_file_id:
        target_ranks.append((i, cand["score"]))

if target_ranks:
    print(f"Target file found at ranks: {target_ranks}")
else:
    print("Target file NOT found in top 5000 vector results!")

# 2. Check Folder Filtering count
print("\n--- Step 2: Folder Filtering ---")
filtered_candidates = []
from app.services.folder_service import folder_service
folder_files = folder_service.get_files_in_folder(folder_id)
# Manual filter logic from qa_service
allowed_files = set(folder_files)
for cand in candidates:
    if cand["chunk"]["file_id"] in allowed_files:
        filtered_candidates.append(cand)

print(f"Candidates after folder limit: {len(filtered_candidates)}")
# Check where target is in filtered list
filtered_ranks = []
for i, cand in enumerate(filtered_candidates):
    if cand["chunk"]["file_id"] == target_file_id:
        filtered_ranks.append(i)

if filtered_ranks:
    print(f"Target file ranks in filtered list: {filtered_ranks}")
else:
    print("Target file filtered out (should not happen if in folder)!")

# 3. Check Keyword Rescue Logic
print("\n--- Step 3: Keyword Rescue ---")
query_terms = [t for t in question.split() if len(t) > 2 and (t[0].isupper() or t.isdigit())]
print(f"Query terms identified: {query_terms}")

rescued = []
not_rescued = []
for cand in filtered_candidates:
    text = cand["chunk"].get("text", "")
    if any(term in text for term in query_terms):
        rescued.append(cand)
    else:
        not_rescued.append(cand)

print(f"Rescued count: {len(rescued)}")
final_candidates = rescued + not_rescued
final_candidates = final_candidates[:250]

# Check if target survived
survived = False
for cand in final_candidates:
    if cand["chunk"]["file_id"] == target_file_id:
        survived = True
        break

if survived:
    print("\nSUCCESS: Target file SURVIVED the pre-reranking cut!")
else:
    print("\nFAILURE: Target file was CUT before reranking.")
    if filtered_ranks:
        print(f"It was at rank {filtered_ranks[0]} in the folder list.")
    print("If it had been rescued, it would have survived.")

