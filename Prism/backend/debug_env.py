
import sys
import os

print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")
print("\nSys Path:")
for p in sys.path:
    print(p)

print("\nAttempting to import pdfplumber...")
try:
    import pdfplumber
    print(f"SUCCESS: pdfplumber imported from {pdfplumber.__file__}")
except ImportError as e:
    print(f"FAILURE: {e}")

print("\nAttempting to import pdfminer...")
try:
    import pdfminer
    print(f"SUCCESS: pdfminer imported from {pdfminer.__file__}")
except ImportError as e:
    print(f"FAILURE: {e}")
