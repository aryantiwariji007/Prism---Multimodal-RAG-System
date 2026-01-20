
import sys
from pathlib import Path

# Add backend to path
sys.path.append(r"c:\Users\ASUS\Desktop\Prism for ScotAI\Prism\backend")

from ingestion.parse_pdf import parse_document

def verify_pdf_parsing():
    # Use the existing uploaded file path we found in the metadata
    file_path = r"c:\Users\ASUS\Desktop\Prism for ScotAI\Prism\backend\data\uploads\a2efacae-4a09-4947-b0c5-503a80698e66_EPI HSE Exposure Hours 2021.pdf"
    
    print(f"Parsing file: {file_path}")
    
    try:
        chunks = parse_document(file_path, "verify_test_id")
        
        # Check first chunk for table content
        if chunks:
            text = chunks[0]['text']
            print("\n--- Parsed Text Snippet ---\n")
            print(text[:2000]) # Print first 2000 chars
            
            # Check for the specific issue: "51,67221,120" (merged columns)
            # We want to see "51,672 21,120" or similar separation
            
            if "51,67221,120" in text:
                print("\nFAILURE: Columns are still merged (51,67221,120 found).")
            elif "51,672" in text and "21,120" in text:
                 # Check strict adjacency
                 import re
                 if re.search(r"51,672\s+21,120", text):
                     print("\nSUCCESS: Columns are separated by whitespace.")
                 else:
                     print("\nWARNING: Numbers found but check whitespace manually.")
            else:
                 print("\nINCONCLUSIVE: Could not find specific test numbers in snippet.")

        else:
            print("No chunks returned.")
            
    except Exception as e:
        print(f"Error parsing: {e}")

if __name__ == "__main__":
    verify_pdf_parsing()
