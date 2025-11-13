"""Debug PDF structure to understand table format"""
import pdfplumber

pdf_path = "data/BALFLEX-HOSES-CATALOGUE_HOSECAT.E.01.2023.pdf"

# Check page 49 where we know POWERSPIR R13 is
page_num = 49

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[page_num - 1]
    
    print(f"\n=== PAGE {page_num} DEBUG ===\n")
    
    # Extract text
    text = page.extract_text()
    print("TEXT (first 500 chars):")
    print(text[:500])
    print("\n" + "="*70 + "\n")
    
    # Extract tables
    tables = page.extract_tables()
    print(f"Number of tables: {len(tables)}")
    
    if tables:
        for i, table in enumerate(tables):
            print(f"\n--- TABLE {i+1} ---")
            print(f"Rows: {len(table)}, Columns: {len(table[0]) if table else 0}")
            print("\nFirst 5 rows:")
            for j, row in enumerate(table[:5]):
                print(f"Row {j}: {row}")
