import pdfplumber
import re

pdf_path = r'data/BALFLEX-HYDRAULIC-FITTINGS_HYFITCAT.012023 (1).pdf'

print("Analyzing PDF structure in detail...")
print("=" * 70)

with pdfplumber.open(pdf_path) as pdf:
    product_pages = []
    
    for page_num in range(len(pdf.pages)):
        page = pdf.pages[page_num]
        text = page.extract_text() or ""
        
        # Look for article numbers
        article_matches = re.findall(r'20\.\d{3}\.\d{2}[A-Z]?', text)
        
        # Look for tables
        tables = page.extract_tables()
        
        if article_matches or tables:
            product_pages.append({
                'page': page_num + 1,
                'articles_count': len(article_matches),
                'tables_count': len(tables),
                'sample_articles': article_matches[:3] if article_matches else []
            })
    
    print(f"\nFound {len(product_pages)} pages with potential products\n")
    
    # Print page ranges
    for info in product_pages[:20]:  # First 20 product pages
        print(f"Page {info['page']:3d}: {info['articles_count']:3d} articles, {info['tables_count']} tables - {info['sample_articles']}")
    
    if len(product_pages) > 20:
        print(f"\n... and {len(product_pages) - 20} more pages")
    
    print(f"\n✓ Total product pages: {len(product_pages)}")
    
    # Detailed look at a few pages
    print("\n" + "=" * 70)
    print("Detailed analysis of selected pages:")
    print("=" * 70)
    
    for page_idx in [19, 20, 50, 80]:  # Pages 20, 21, 51, 81
        if page_idx < len(pdf.pages):
            page = pdf.pages[page_idx]
            text = page.extract_text() or ""
            tables = page.extract_tables()
            
            print(f"\n--- Page {page_idx + 1} ---")
            
            # Extract category/title
            lines = text.split('\n')[:10]
            print("Top lines:", lines[:5])
            
            if tables:
                print(f"\nFound {len(tables)} table(s)")
                for t_idx, table in enumerate(tables):
                    print(f"\nTable {t_idx + 1}: {len(table)} rows")
                    if len(table) > 0:
                        print("Header:", table[0][:5])  # First 5 columns
                    if len(table) > 1:
                        print("Row 1:", table[1][:5])
                    if len(table) > 2:
                        print("Row 2:", table[2][:5])
