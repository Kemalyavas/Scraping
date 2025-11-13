"""
Balflex Fittings PDF Parser
Extracts hydraulic fittings from Balflex catalog
"""

import pdfplumber
import re
import json
from typing import List, Dict

class BalflexFittingsParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.products = []
    
    def parse(self) -> List[Dict]:
        """Parse Balflex fittings PDF"""
        print("Parsing Balflex Fittings PDF...")
        print("=" * 70)
        
        with pdfplumber.open(self.pdf_path) as pdf:
            print(f"Total pages: {len(pdf.pages)}\n")
            
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    self._parse_page(page, page_num)
                    
                    if page_num % 20 == 0:
                        print(f"  Processed {page_num}/{len(pdf.pages)} pages...")
                
                except Exception as e:
                    continue
        
        print(f"\n✓ Extracted {len(self.products)} fittings from PDF")
        return self.products
    
    def _parse_page(self, page, page_num: int):
        """Parse a single page for fitting products"""
        
        text = page.extract_text()
        if not text:
            return
        
        # Look for Balflex article numbers (20.XXX.XX, 23.XXXX.XXXX, etc.)
        if not re.search(r'\d{2}\.\d{3,4}\.\d{2,4}', text) and 'REFERENCE' not in text:
            return
        
        # Extract product type/category from page header
        category = self._extract_category(text)
        
        # Get tables
        tables = page.extract_tables()
        
        for table in tables:
            if not table or len(table) < 2:
                continue
            
            # Parse table
            products = self._parse_table(table, category, page_num)
            self.products.extend(products)
    
    def _extract_category(self, text: str) -> str:
        """Extract fitting category from page text"""
        
        # Common fitting types
        categories = [
            "Ferrule",
            "JIC 37",
            "ORFS",
            "Flange",
            "BSP",
            "NPT",
            "Metric",
            "Adapter",
            "Elbow",
            "Tee",
            "Cross",
        ]
        
        for cat in categories:
            if cat.upper() in text.upper():
                return cat
        
        return "Fitting"
    
    def _parse_table(self, table: List[List], category: str, page_num: int) -> List[Dict]:
        """Parse product table"""
        
        products = []
        
        # Find header row (contains REFERENCE or dash)
        header_row = 0
        for i, row in enumerate(table[:5]):
            row_text = ' '.join([str(cell) for cell in row if cell])
            if 'REFERENCE' in row_text.upper() or 'dash' in row_text.lower():
                header_row = i
                break
        
        # Parse data rows
        for row in table[header_row + 1:]:
            if not row or len(row) < 3:
                continue
            
            # Skip empty rows
            if all(cell is None or str(cell).strip() == '' for cell in row):
                continue
            
            product = self._extract_from_row(row, category)
            if product:
                products.append(product)
        
        return products
    
    def _extract_from_row(self, row: List, category: str) -> Dict:
        """Extract fitting data from table row"""
        
        try:
            # Convert all cells to strings
            cells = [str(cell).strip() if cell else "" for cell in row]
            
            # Find REFERENCE (article number like 20.204.03)
            reference = ""
            dash_size = ""
            hose_mm = ""
            hose_inch = ""
            
            for cell in cells:
                # Article number pattern (20.XXX.XX, 23.XXXX.XXXX, etc.)
                if re.match(r'\d{2}\.\d{3,4}\.\d{2,4}[A-Z]?', cell):
                    reference = cell
                
                # Dash size (-4, -6, etc.)
                if re.match(r'-\s*\d+', cell):
                    dash_size = cell.strip()
                
                # Hose size in mm
                if re.match(r'\d+[\.,]\d+$', cell) and float(cell.replace(',', '.')) < 100:
                    hose_mm = cell.replace(',', '.')
                
                # Hose size in inches
                if re.match(r'\d+/\d+"|\d+\.\d+/\d+"', cell):
                    hose_inch = cell.replace('"', '').strip()
            
            # Must have at least reference
            if not reference:
                return None
            
            # Determine thread type from category
            thread_type = ""
            if "JIC" in category.upper():
                thread_type = "JIC 37°"
            elif "ORFS" in category.upper():
                thread_type = "ORFS"
            elif "BSP" in category.upper():
                thread_type = "BSP"
            elif "NPT" in category.upper():
                thread_type = "NPT"
            elif "METRIC" in category.upper():
                thread_type = "Metric"
            
            # Determine connection type
            connection_type = ""
            if "FERRULE" in category.upper():
                connection_type = "Ferrule"
            elif "ELBOW" in category.upper():
                connection_type = "Elbow"
            elif "TEE" in category.upper():
                connection_type = "Tee"
            elif "ADAPTER" in category.upper():
                connection_type = "Adapter"
            elif "FLANGE" in category.upper():
                connection_type = "Flange"
            
            return {
                'supplier': 'Balflex',
                'category': category,
                'reference': reference,
                'article_number': reference,
                'dash_size': dash_size,
                'hose_size_mm': hose_mm,
                'hose_size_inch': hose_inch,
                'thread_type': thread_type,
                'connection_type': connection_type,
            }
        
        except Exception as e:
            return None
    
    def save_to_json(self, filename: str):
        """Save products to JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.products, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Saved to {filename}")


if __name__ == "__main__":
    parser = BalflexFittingsParser('data/BALFLEX-HYDRAULIC-FITTINGS_HYFITCAT.012023 (1).pdf')
    products = parser.parse()
    parser.save_to_json('data/balflex_fittings.json')
    
    print(f"\n{'=' * 70}")
    print(f"Summary: {len(products)} fittings extracted")
    
    if products:
        print(f"\nSample product:")
        import json
        print(json.dumps(products[0], indent=2, ensure_ascii=False))
