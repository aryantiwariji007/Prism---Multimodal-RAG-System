
import sys
from pathlib import Path
import logging

# Setup Text/Output encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

# Add backend to path
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from ingestion.parse_pdf import parse_pdf
from ingestion.chunker import document_chunker

# File path
file_path = r"c:\Users\ASUS\Desktop\Prism for ScotAI\Prism\backend\data\uploads\976698a6-ecd7-437a-9501-cfb66d013c7b_EPI HSE Exposure Hours 2021.pdf"

def analyze_chunks():
    output_file = backend_dir / "debug_chunk_output.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Analyzing file: {file_path}\n")
        
        # 1. Parse
        chunks = parse_pdf(file_path, file_id="test_file")
        f.write(f"Parsed {len(chunks)} pages.\n")
        
        # 2. Chunk
        final_chunks = document_chunker.chunk_document_pages(chunks)
        f.write(f"Created {len(final_chunks)} chunks.\n")
        
        target_found = False
        
        for i, c in enumerate(final_chunks):
            text = c['text']
            # Look for 2015 and Total Hours in the same chunk
            if "2015" in text and "Total Hours" in text:
                f.write(f"\n--- MATCHING CHUNK {i} ---\n")
                f.write(text)
                f.write("\n" + "-" * 30 + "\n")
                target_found = True
                
        if not target_found:
            f.write("\n[WARNING] No chunk contains both '2015' and 'Total Hours'. Table might be split.\n")
            # Dump all chunks for inspection
            f.write("\n--- ALL CHUNKS ---\n")
            for i, c in enumerate(final_chunks):
                 f.write(f"\n[Chunk {i}]\n{c['text']}\n")

    print(f"Output written to {output_file}")

if __name__ == "__main__":
    analyze_chunks()
