
import sys
import pdfplumber

# File path for the HSE document
file_path = r"c:\Users\ASUS\Desktop\Prism for ScotAI\Prism\backend\data\uploads\976698a6-ecd7-437a-9501-cfb66d013c7b_EPI HSE Exposure Hours 2021.pdf"

def test_strategies():
    print(f"Testing strategies on: {file_path}")
    
    with pdfplumber.open(file_path) as pdf:
        page = pdf.pages[0] 
        
        print("\n--- Strategy 1: Vertical 'lines', Horizontal 'lines' ---")
        tables_lines = page.extract_tables({"vertical_strategy": "lines", "horizontal_strategy": "lines"})
        if tables_lines:
            print(f"Found {len(tables_lines)} tables.")
            print("First row of first table:", tables_lines[0][0])
        else:
            print("No tables found.")

if __name__ == "__main__":
    test_strategies()
