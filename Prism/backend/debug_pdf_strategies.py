
import sys
import pdfplumber

# File path for the SDS document
file_path = r"c:\Users\ASUS\Desktop\Prism for ScotAI\Prism\backend\data\uploads\aacc01ae-c19c-427b-984f-48a682b44c84_MSDS TN321K (Black Toner).pdf"

def test_strategies():
    print(f"Testing strategies on: {file_path}")
    
    with pdfplumber.open(file_path) as pdf:
        page = pdf.pages[0] # Test first page (Issue seen on page 1)
        
        print("\n--- Strategy 1: Vertical 'lines', Horizontal 'lines' (Current) ---")
        tables_lines = page.extract_tables({"vertical_strategy": "lines", "horizontal_strategy": "lines"})
        if tables_lines:
            print(f"Found {len(tables_lines)} tables.")
            print("First row of first table:", tables_lines[0][0])
        else:
            print("No tables found.")

        print("\n--- Strategy 2: Vertical 'text', Horizontal 'text' ---")
        tables_text = page.extract_tables({"vertical_strategy": "text", "horizontal_strategy": "text"})
        if tables_text:
            print(f"Found {len(tables_text)} tables.")
            print("First row of first table:", tables_text[0][0])
        else:
            print("No tables found.")

        print("\n--- Plain Text Extraction (x_tolerance = 1) ---")
        text = page.extract_text(x_tolerance=1)
        print(text[:200])

if __name__ == "__main__":
    test_strategies()
