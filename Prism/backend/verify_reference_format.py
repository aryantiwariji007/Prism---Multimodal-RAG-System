
import sys
import logging
from pathlib import Path
from typing import Dict, List

# Add backend to path
backend_dir = Path(r"c:\Users\ASUS\Desktop\Prism for ScotAI\Prism\backend")
sys.path.insert(0, str(backend_dir))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.services.qa_service import DocumentQAService

class MockQAService(DocumentQAService):
    def __init__(self):
        self.document_metadata = {
            "file1": {"file_name": "Policy Report 2024.pdf", "file_type": "PDF"}
        }

def verify_context_format():
    print("--- Verifying Context Format ---")
    service = MockQAService()
    
    chunks = [
        {"file_id": "file1", "page": 5, "text": "This is some sample text from page 5."}
    ]
    
    context = service._build_context(chunks, max_length=1000)
    
    print("Generated Context:")
    print(context)
    
    expected_header = "[Section: Policy Report 2024 | Page 5]"
    
    if expected_header in context:
        print("\n✅ SUCCESS: Context header format is correct.")
    else:
        print(f"\n❌ FAIL: Expected '{expected_header}' not found.")

if __name__ == "__main__":
    verify_context_format()
