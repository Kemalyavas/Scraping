"""
Balflex PDF Parser - Extract products directly from PDF
Replaces the old TXT-based parser with proper PDF parsing
"""

import pdfplumber
import re
import json
from typing import List, Dict
from pathlib import Path


class BalflexPDFParser:
    """Parse Balflex catalog PDF and extract product specifications"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.products = []
    
    def parse(self) -> List[Dict]:
        """Main parsing function"""
        print("Parsing Balflex PDF catalog...")
        
        with pdfplumber.open(self.pdf_path) as pdf:
            print(f"Total pages: {len(pdf.pages)}")
            
            # Parse each page
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    self._parse_page(page, page_num)
                except Exception as e:
                    # Skip problematic pages
                    if page_num % 20 == 0:
                        print(f"  Processed {page_num} pages...")
                    continue
        
        print(f"\n✓ Extracted {len(self.products)} products from PDF")
        return self.products
    
    def _parse_page(self, page, page_num: int):
        """Parse a single page for product tables"""
        
        # Extract tables from page
        tables = page.extract_tables()
        
        if not tables:
            return
        
        # Get page text to find model name
        try:
            text = page.extract_text()
            if not text:
                return
        except:
            return
        
        # Find model name from page
        model_name = self._extract_model_name(text)
        standard = self._extract_standard(text, model_name)
        
        if not model_name:
            return
        
        # Parse each table
        for table in tables:
            products = self._parse_product_table(table, model_name, standard, page_num)
            self.products.extend(products)
    
    def _extract_model_name(self, text: str) -> str:
        """Extract model name from page text"""
        
        # Look for known model patterns
        models = [
            'POWERSPIR BESTFLEX',
            'BALMASTER BESTFLEX',
            'BALPAC IMPACTUS',
            'TEXMASTER',
            'BALFLON',
            'FORZA',
            'MULTIFLEX',
            'MULTIPURPOSE',
        ]
        
        for model in models:
            if model in text.upper():
                # Get the full line with model name
                lines = text.split('\n')
                for line in lines:
                    if model in line.upper():
                        # Clean up the model name
                        return line.strip().split('\n')[0]
        
        return ""
    
    def _extract_standard(self, text: str, model_line: str = "") -> str:
        """Extract standard/norm from page text"""
        
        # If we have model line, look for standard in nearby lines
        if model_line:
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if model_line.strip() in line:
                    # Check next 2 lines for standard
                    for next_line in lines[i:i+3]:
                        # Look for DIN EN first (more specific)
                        match = re.search(r'DIN\s*EN\s*\d+\s*[A-Z0-9]+', next_line, re.IGNORECASE)
                        if match:
                            return re.sub(r'\s+', ' ', match.group(0)).strip()
                        
                        # Then SAE
                        match = re.search(r'SAE\s*(?:J517\s*)?100R\d+[A-Z]*', next_line, re.IGNORECASE)
                        if match:
                            std = re.sub(r'\s+', ' ', match.group(0)).strip()
                            # Remove J517 if present
                            std = re.sub(r'J517\s*', '', std)
                            return std
                    break
        
        # Fallback: look for any standard in text
        patterns = [
            r'DIN\s*EN\s*\d+\s*[A-Z0-9]+',
            r'SAE\s*(?:J517\s*)?100R\d+[A-Z]*',
            r'ISO\s*\d+',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                std = re.sub(r'\s+', ' ', match.group(0)).strip()
                std = re.sub(r'J517\s*', '', std)
                return std
        
        return ""
    
    def _parse_product_table(self, table: List[List], model_name: str, standard: str, page_num: int) -> List[Dict]:
        """Parse product table and extract variants"""
        
        products = []
        
        if not table or len(table) < 2:
            return products
        
        # Balflex tables usually have 1-2 header rows, then data
        # Look for row with "REFERENCE" or "#" in first columns
        data_start_row = 2  # Usually data starts at row 2
        
        # Verify this is a product table (has REFERENCE and DN)
        has_reference = False
        has_dn = False
        
        # Check all rows for REFERENCE and DN (they might be in different rows)
        all_text = ' '.join([' '.join([str(cell) for cell in row if cell]) for row in table[:5]])
        
        if 'REFERENCE' in all_text.upper():
            has_reference = True
        if 'DN' in all_text.upper():
            has_dn = True
        
        if not (has_reference and has_dn):
            return products
        
        # Get column indices (fixed structure for Balflex)
        col_indices = self._find_column_indices([])
        
        # Parse data rows (skip first 2 header rows)
        for row in table[data_start_row:]:
            if not row or len(row) < 3:
                continue
            
            # Skip rows that look like headers
            first_cell = str(row[0]).upper() if row[0] else ""
            if 'REFERENCE' in first_cell or first_cell == '':
                continue
            
            product = self._extract_product_from_row(row, col_indices, model_name, standard)
            if product:
                products.append(product)
        
        return products
    
    def _find_column_indices(self, headers: List) -> Dict[str, int]:
        """Find column indices for important fields"""
        
        indices = {}
        
        # Balflex PDF table structure (observed):
        # Col 0: REFERENCE (4SP-04-F)
        # Col 1: # (10.1008.04F) - article number
        # Col 2: DN (DN6)
        # Col 3: inch (1/4")
        # Col 4: SAE Dash (-4)
        # Col 5: Inner diameter mm (6.5)
        # Col 6: Outer diameter mm (17,4)
        # Col 7: Working pressure (45,0 6600) - MPa and PSI combined
        # Col 8: Burst pressure MPa (180,0)
        # Col 9: Burst pressure PSI (26400)
        # Col 10: Bend radius (150)
        # Col 11: Weight (0,70)
        
        # Use fixed indices based on Balflex format
        indices['reference'] = 0
        indices['article'] = 1
        indices['dn'] = 2
        indices['inch'] = 3
        indices['sae_dash'] = 4
        indices['inner_dia'] = 5
        indices['outer_dia'] = 6
        indices['working_pressure'] = 7
        indices['burst_pressure'] = 8
        indices['bend_radius'] = 10
        
        return indices
    
    def _extract_product_from_row(self, row: List, col_indices: Dict, model_name: str, standard: str) -> Dict:
        """Extract product data from table row"""
        
        # Skip if row is too short
        if len(row) < 8:
            return None
        
        product = {
            'supplier': 'Balflex',
            'model': model_name,
        }
        
        # Extract reference (Col 0: "4SP-04-F")
        if 'reference' in col_indices and col_indices['reference'] < len(row):
            ref = self._clean_cell(row[col_indices['reference']])
            if ref:
                product['reference'] = ref
        
        # Extract article number (Col 1: "10.1008.04F")  
        if 'article' in col_indices and col_indices['article'] < len(row):
            article = self._clean_cell(row[col_indices['article']])
            if article:
                product['article_number'] = article
        
        # Extract DN (Col 2: "DN6")
        if 'dn' in col_indices and col_indices['dn'] < len(row):
            dn = self._clean_cell(row[col_indices['dn']])
            if dn:
                # Extract DN number
                dn_match = re.search(r'DN\s*(\d+)', dn.upper())
                if dn_match:
                    product['dn'] = f"DN{dn_match.group(1)}"
                elif dn.isdigit():
                    product['dn'] = f"DN{dn}"
        
        # Extract inch size (Col 3: "1/4\"")
        if 'inch' in col_indices and col_indices['inch'] < len(row):
            inch = self._clean_cell(row[col_indices['inch']])
            if inch:
                product['inch_size'] = inch
        
        # Extract inner diameter (Col 5: "6.5")
        if 'inner_dia' in col_indices and col_indices['inner_dia'] < len(row):
            inner = self._extract_float(row[col_indices['inner_dia']])
            if inner:
                product['inner_diameter_mm'] = inner
        
        # Extract outer diameter (Col 6: "17,4")
        if 'outer_dia' in col_indices and col_indices['outer_dia'] < len(row):
            outer = self._extract_float(row[col_indices['outer_dia']])
            if outer:
                product['outer_diameter_mm'] = outer
        
        # Extract working pressure (Col 7: "45,0 6600" - take first number as MPa)
        if 'working_pressure' in col_indices and col_indices['working_pressure'] < len(row):
            wp_cell = str(row[col_indices['working_pressure']])
            # Take first number (MPa)
            wp = self._extract_float(wp_cell.split()[0] if ' ' in wp_cell else wp_cell)
            if wp:
                product['working_pressure_mpa'] = wp
        
        # Extract burst pressure (Col 8: "180,0")
        if 'burst_pressure' in col_indices and col_indices['burst_pressure'] < len(row):
            bp = self._extract_float(row[col_indices['burst_pressure']])
            if bp:
                product['burst_pressure_mpa'] = bp
        
        # Add standard
        if standard:
            product['standard'] = standard
        
        # Determine construction type
        product['construction'] = self._determine_construction(model_name, standard)
        
        # Only return if we have minimum required fields
        if product.get('dn') and product.get('article_number'):
            return product
        
        return None
    
    def _clean_cell(self, cell) -> str:
        """Clean cell content"""
        if cell is None:
            return ""
        return str(cell).strip().replace('\n', ' ')
    
    def _extract_float(self, cell) -> float:
        """Extract float from cell, handling European decimals"""
        if cell is None:
            return None
        
        text = str(cell).strip()
        
        # Handle European decimal (comma)
        text = text.replace(',', '.')
        
        # Extract first number
        match = re.search(r'(\d+\.?\d*)', text)
        if match:
            try:
                return float(match.group(1))
            except:
                return None
        
        return None
    
    def _determine_construction(self, model_name: str, standard: str) -> str:
        """Determine construction type from model and standard"""
        
        combined = f"{model_name} {standard}".upper()
        
        if '4SP' in combined or '4SH' in combined or 'SPIRAL' in combined:
            return 'spiral wire'
        elif 'R12' in combined or 'R13' in combined or 'R15' in combined:
            return 'spiral wire'
        elif '2SC' in combined or '2SN' in combined:
            return '2 wire braid'
        elif '1SC' in combined or '1SN' in combined:
            return '1 wire braid'
        elif 'TEXTILE' in combined or 'TEXMASTER' in combined:
            return 'textile braid'
        else:
            return 'wire braid'
    
    def save_to_json(self, output_file: str):
        """Save products to JSON file"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.products, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(self.products)} Balflex products to {output_file}")


if __name__ == "__main__":
    # Parse PDF
    parser = BalflexPDFParser("data/BALFLEX-HOSES-CATALOGUE_HOSECAT.E.01.2023.pdf")
    products = parser.parse()
    
    # Save to JSON
    parser.save_to_json("data/balflex_products.json")
    
    # Show summary
    print("\n=== Summary ===")
    print(f"Total products: {len(products)}")
    
    if products:
        print("\nSample product:")
        print(json.dumps(products[0], indent=2))
        
        # Group by model
        from collections import Counter
        models = Counter(p['model'] for p in products)
        print("\nBy model:")
        for model, count in models.most_common(10):
            print(f"  {model}: {count}")
