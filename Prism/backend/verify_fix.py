
import sys
import logging
from pathlib import Path

# Setup simple logging
logging.basicConfig(level=logging.INFO)

sys.path.append(str(Path.cwd()))
from app.services.qa_service import qa_service

folder_id = "1aec18b0-9e33-43e7-acaf-78090c31a555" # Quality
question = "what are EPI's information to agents or agencies"

print(f"Asking question: '{question}' in folder: {folder_id}")

result = qa_service.answer_question(
    question=question,
    folder_id=folder_id
)

if result["success"]:
    print("\nAnswer:")
    print(result["answer"])
    print("\nSources:")
    for source in result.get("sources", []):
        print(f" - {source['file_name']} (Page {source['page']})")
    print(f"\nChunks used: {result.get('chunks_used')}")
else:
    print(f"\nFailed: {result.get('error')}")
    if "answer" in result:
        print(f"Partial Answer: {result['answer']}")
