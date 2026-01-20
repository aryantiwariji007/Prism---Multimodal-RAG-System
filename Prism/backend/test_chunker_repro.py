
import sys
from pathlib import Path

# Add backend to path
sys.path.append(r"c:\Users\ASUS\Desktop\Prism for ScotAI\Prism\backend")

from ingestion.chunker import DocumentChunker

def test_chunker_table_structure():
    chunker = DocumentChunker(chunk_size=1000, chunk_overlap=0)
    
    # Mock table from PDF parser
    table_text = """
--- Table 1 ---
Statistics | 2010 | 2011 | 2012
Manhours Office | 21,120 | 26,400 | 29,992
Manhours Field Land | 54,764 | 45,022 | 98,784
--- End Table ---
"""
    
    print("Original Text:")
    print(table_text)
    
    chunks = chunker.chunk_text(table_text, "test_file_id")
    
    print("\nChunked Text (Chunk 0):")
    print(chunks[0]['text'])
    
    # Check if newlines are preserved
    if "\n" not in chunks[0]['text']:
        print("\nFAILURE: Newlines were removed! Table structure is flattened.")
    else:
        print("\nSUCCESS: Newlines preserved.")

    # Check if "2010" and "21,120" are still aligned (hard to check programmatically without visual, but string presence helps)
    if "Manhours Office | 21,120" in chunks[0]['text']:
        print("SUCCESS: Row content seems intact.")
    else:
        print("FAILURE: Row content disrupted (likely due to whitespace collapse).")

if __name__ == "__main__":
    test_chunker_table_structure()
