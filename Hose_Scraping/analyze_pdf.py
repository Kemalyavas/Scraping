"""Analyze Balflex PDF to find all product series"""
import pdfplumber
import re
from collections import defaultdict

pdf_path = "data/BALFLEX-HOSES-CATALOGUE_HOSECAT.E.01.2023.pdf"

print("\n" + "="*70)
print("BALFLEX PDF ANALYSIS")
print("="*70)

# Search for product series names
series_found = defaultdict(int)
sae_standards = defaultdict(int)
din_standards = defaultdict(int)

with pdfplumber.open(pdf_path) as pdf:
    print(f"\nTotal pages: {len(pdf.pages)}")
    
    # Sample first 50 pages to find product names
    for i, page in enumerate(pdf.pages[:50]):
        text = page.extract_text()
        
        if not text:
            continue
        
        # Look for POWERSPIR, BALMASTER, etc.
        if 'POWERSPIR' in text.upper():
            series_found['POWERSPIR'] += 1
            print(f"\n📄 Page {i+1}: Found POWERSPIR")
            # Extract nearby text
            lines = text.split('\n')
            for j, line in enumerate(lines):
                if 'POWERSPIR' in line.upper():
                    context = '\n'.join(lines[max(0,j-2):min(len(lines),j+3)])
                    print(f"Context:\n{context}\n")
                    break
        
        if 'BALMASTER' in text.upper():
            series_found['BALMASTER'] += 1
            print(f"\n📄 Page {i+1}: Found BALMASTER")
        
        # Look for R12, R13, R15
        r_series = re.findall(r'SAE\s*100R(\d+)', text, re.IGNORECASE)
        for r in r_series:
            if r in ['12', '13', '15']:
                sae_standards[f'SAE 100R{r}'] += 1
        
        # Look for DIN EN 856
        din_matches = re.findall(r'DIN\s*EN\s*856', text, re.IGNORECASE)
        if din_matches:
            din_standards['DIN EN 856'] += len(din_matches)

print("\n" + "="*70)
print("SERIES FOUND:")
print("="*70)
for series, count in sorted(series_found.items()):
    print(f"  {series:30s}: {count} mentions")

print("\n" + "="*70)
print("SAE STANDARDS (R12/R13/R15):")
print("="*70)
for std, count in sorted(sae_standards.items()):
    print(f"  {std:30s}: {count} mentions")

print("\n" + "="*70)
print("DIN STANDARDS:")
print("="*70)
for std, count in sorted(din_standards.items()):
    print(f"  {std:30s}: {count} mentions")

# Now extract product tables
print("\n" + "="*70)
print("SEARCHING FOR PRODUCT TABLES:")
print("="*70)

products_with_r12_r13_r15 = []

for i, page in enumerate(pdf.pages):
    text = page.extract_text()
    if not text:
        continue
    
    # Look for pages with product specifications
    if re.search(r'R1[2-5]', text) and re.search(r'DN\d+', text):
        print(f"\n📄 Page {i+1}: Has R12/R13/R15 products with DN specs")
        
        # Try to extract table
        tables = page.extract_tables()
        if tables:
            print(f"  Found {len(tables)} tables on this page")
            for t_idx, table in enumerate(tables[:2]):  # Show first 2 tables
                print(f"\n  Table {t_idx+1} preview (first 3 rows):")
                for row in table[:3]:
                    print(f"    {row}")

print("\n" + "="*70)
