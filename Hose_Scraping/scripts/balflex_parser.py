"""
Balflex Catalog Parser - Fixed Version
Scans entire catalog and extracts ALL product rows
"""

import re
import json
from typing import List, Dict, Any
from pathlib import Path


class BalflexParser:
    """Parse Balflex catalog - finds all product rows with article numbers"""
    
    def __init__(self, catalog_file: str):
        self.catalog_file = catalog_file
        self.products = []
        
    def parse(self) -> List[Dict[str, Any]]:
        """Scan entire catalog for product rows"""
        with open(self.catalog_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Handle European decimal format (6,3 -> 6.3)
        content = re.sub(r'(\d),(\d)', r'\1.\2', content)
        
        # Parse all product rows
        self.products = self._parse_all_product_rows(content)
        
        return self.products
    
    def _parse_all_product_rows(self, content: str) -> List[Dict[str, Any]]:
        """Find every product row in the catalog"""
        products = []
        lines = content.split('\n')
        
        current_model = None
        current_standard = None
        
        for i, line in enumerate(lines):
            # Track current product model/series name
            model_patterns = [
                r'BALPAC\s+[A-Z0-9\s\-]+',
                r'FORZA\s+[A-Z0-9\s]+',
                r'TEXMASTER\s+\d*',
                r'BALFLON\s+[A-Z0-9\s]+',
                r'BALMASTER\s+[A-Z0-9\s]+',
                r'POWERSPIR\s+[A-Z0-9\s]+'
            ]
            
            for pattern in model_patterns:
                model_match = re.search(pattern, line, re.IGNORECASE)
                if model_match:
                    potential = model_match.group(0).strip()
                    if len(potential) > 5:
                        current_model = potential
                        break
            
            # Track standards
            std_match = re.search(r'(DIN\s+EN\s+\d+|SAE\s+100R\d+[A-Z]*|EN\s+\d+/\d+)', line, re.IGNORECASE)
            if std_match:
                current_standard = std_match.group(1).strip()
            
            # Find product data rows with article number (10.XXXX.XX format)
            # Pattern: REFERENCE  ARTICLE  DN/INCH  INCH  DASH  INNER_DIA  OUTER_DIA  PRESSURE  ...
            # Note: DN is optional - some products only have inch sizes
            row_match = re.match(
                r'\s*([A-Z0-9\-]+)\s+(10\.\d+\.?\d*)\s+(DN\d+|)\s*([^\s]+)\s+([\-\d]+)\s+([\d\.]+)\s+([\d\.]+)',
                line
            )
            
            if row_match:
                reference = row_match.group(1)
                article_number = row_match.group(2)
                dn = row_match.group(3) if row_match.group(3) else ""  # DN might be empty
                inch_size = row_match.group(4)
                sae_dash = row_match.group(5)
                inner_dia = float(row_match.group(6))
                outer_dia = float(row_match.group(7))
                
                # Extract all numbers from the line
                all_numbers = re.findall(r'[\d\.]+', line)
                
                # Determine model if not set
                if not current_model:
                    current_model = self._extract_model_from_reference(reference)
                
                # Determine construction type
                construction = self._determine_construction(reference, current_model)
                
                product = {
                    'supplier': 'Balflex',
                    'model': current_model,
                    'reference': reference,
                    'article_number': article_number,
                    'dn': dn,
                    'inch_size': inch_size,
                    'sae_dash': sae_dash,
                    'inner_diameter_mm': inner_dia,
                    'outer_diameter_mm': outer_dia,
                    'standard': current_standard or "",
                    'construction': construction,
                    'category': self._determine_category(construction)
                }
                
                # Extract pressure and other values
                # Typical order: ... INNER OUTER PRESSURE_MPa PRESSURE_PSI BURST_MPa BURST_PSI BEND_RAD WEIGHT
                try:
                    # Find position of inner diameter in numbers list
                    inner_str = str(inner_dia)
                    if inner_str in all_numbers:
                        idx = all_numbers.index(inner_str)
                        
                        # Working pressure (usually 2 positions after outer dia)
                        if idx + 2 < len(all_numbers):
                            product['working_pressure_mpa'] = float(all_numbers[idx + 2])
                        
                        # PSI pressure
                        if idx + 3 < len(all_numbers):
                            product['working_pressure_psi'] = int(float(all_numbers[idx + 3]))
                        
                        # Burst pressure MPa
                        if idx + 4 < len(all_numbers):
                            product['burst_pressure_mpa'] = float(all_numbers[idx + 4])
                        
                        # Burst pressure PSI
                        if idx + 5 < len(all_numbers):
                            product['burst_pressure_psi'] = int(float(all_numbers[idx + 5]))
                        
                        # Min bend radius
                        if idx + 6 < len(all_numbers):
                            product['min_bend_radius_mm'] = int(float(all_numbers[idx + 6]))
                        
                        # Weight
                        if idx + 7 < len(all_numbers):
                            product['weight_kg_m'] = float(all_numbers[idx + 7])
                except:
                    pass  # If extraction fails, product still has basic info
                
                products.append(product)
        
        return products
    
    def _extract_model_from_reference(self, reference: str) -> str:
        """Extract model from reference code"""
        # Examples: 2TE-04 -> 2TE, R16I-04 -> R16I
        match = re.match(r'([A-Z0-9]+)[\-\.]', reference)
        return match.group(1) if match else reference
    
    def _determine_construction(self, reference: str, model: str) -> str:
        """Determine hose construction type"""
        ref_upper = (reference or "").upper()
        model_upper = (model or "").upper()
        combined = ref_upper + " " + model_upper
        
        if '4SP' in combined or '4SH' in combined or 'SPIRAL' in combined:
            return 'spiral wire'
        elif '2SC' in combined or '2SN' in combined or 'R16' in combined:
            return '2 wire braid'
        elif '2TE' in combined:
            return '1 textile braid'
        elif '3TE' in combined or 'R3' in combined:
            return '2 textile braid'
        elif '1SC' in combined or '1SN' in combined or '1TE' in combined:
            return '1 wire braid'
        elif 'TEXTILE' in combined or 'TEXMASTER' in combined:
            return '1 textile braid'
        else:
            return 'wire braid'
    
    def _determine_category(self, construction: str) -> str:
        """Determine product category"""
        if 'spiral' in construction.lower():
            return 'Spiral Wire'
        elif 'wire' in construction.lower():
            return 'Steel Wire Braid'
        elif 'textile' in construction.lower():
            return 'Textile Braid'
        else:
            return 'Hydraulic Hose'
    
    def save_to_json(self, output_file: str):
        """Save to JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.products, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(self.products)} Balflex products to {output_file}")


def main():
    """Test parser"""
    catalog_file = Path(__file__).parent.parent / 'data' / 'balflex_catalog.txt'
    output_file = Path(__file__).parent.parent / 'data' / 'balflex_products.json'
    
    if not catalog_file.exists():
        print(f"Error: {catalog_file} not found!")
        return
    
    parser = BalflexParser(str(catalog_file))
    products = parser.parse()
    parser.save_to_json(str(output_file))
    
    print(f"\n=== Summary ===")
    print(f"Total products: {len(products)}")
    
    # Group by model
    models = {}
    for p in products:
        m = p.get('model', 'Unknown')
        models[m] = models.get(m, 0) + 1
    
    print(f"\nBy model:")
    for model, count in sorted(models.items()):
        print(f"  {model}: {count}")


if __name__ == '__main__':
    main()
