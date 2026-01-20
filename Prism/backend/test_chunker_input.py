
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, r"c:\Users\ASUS\Desktop\Prism for ScotAI\Prism\backend")

from ingestion.chunker import document_chunker

def test_multipage_chunking():
    # Mock 2 pages of text
    pages = [
        {"text": "Page 1 content " * 50, "file_id": "test_file", "page": 1},
        {"text": "Page 2 content " * 50, "file_id": "test_file", "page": 2}
    ]
    
    chunks = document_chunker.chunk_document_pages(pages)
    
    print(f"Total chunks: {len(chunks)}")
    
    chunk_ids = [c["chunk_id"] for c in chunks]
    print(f"Chunk IDs: {chunk_ids}")
    
    # Verify uniqueness
    assert len(chunk_ids) == len(set(chunk_ids)), "Duplicate chunk IDs found!"
    
    # Verify sequence
    expected_ids = list(range(len(chunks)))
    assert chunk_ids == expected_ids, f"Chunk IDs are not sequential! Expected {expected_ids}, got {chunk_ids}"
    
    print("SUCCESS: Chunk IDs are unique and sequential.")

if __name__ == "__main__":
    test_multipage_chunking()
