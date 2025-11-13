"""
Heizmann Scraper - FIXED VERSION
Visits product pages and extracts actual article numbers and standards from variant tables
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from typing import List, Dict
from pathlib import Path


class HeizmannScraper:
    """Scrape Heizmann - extracts real product data from variant tables"""
    
    def __init__(self):
        self.base_url = "https://www.heizmann.ch"
        self.products = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape(self) -> List[Dict]:
        """Main scraping"""
        print("Heizmann: Scraping actual product data...")
        
        # Get hose product links from main category page
        main_url = "/de/category/5/hochdruck-gummischlaeuche"
        hose_products = self._get_hose_product_links(main_url)
        print(f"Found {len(hose_products)} hose product pages\n")
        
        # Visit each product page and scrape variant tables
        for name, url in hose_products:
            print(f"Scraping: {name}")
            time.sleep(0.5)  # Be polite to the server
            
            variants = self._scrape_product_page(name, url)
            self.products.extend(variants)
            print(f"  -> Extracted {len(variants)} variants")
        
        return self.products
    
    def _get_hose_product_links(self, category_url: str) -> List[tuple]:
        """Get product page links from category"""
        products = []
        
        try:
            url = f"{self.base_url}{category_url}"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all product links with "/de/product/" pattern
            links = soup.find_all('a', href=re.compile(r'/de/product/\d+/'))
            
            seen = set()
            for link in links:
                href = link.get('href')
                name = link.get_text(strip=True)
                
                # Only product names (not too long, not just numbers)
                if href not in seen and name and len(name) <= 50 and not name.isdigit():
                    products.append((name, href))
                    seen.add(href)
            
        except Exception as e:
            print(f"Error getting product links: {e}")
        
        return products
    
    def _scrape_product_page(self, model_name: str, url: str) -> List[Dict]:
        """Scrape product page to extract variant table with article numbers"""
        variants = []
        
        try:
            full_url = f"{self.base_url}{url}"
            response = self.session.get(full_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # EXTRACT STANDARD/NORM from product description
            standard = self._extract_standard_from_page(soup, model_name)
            
            # Find variant links showing article numbers
            variant_links = soup.find_all('a', href=re.compile(r'/de/variant/\d+/'))
            
            # Method 1: Parse variant links with surrounding context
            if variant_links:
                for link in variant_links[:15]:  # Limit to first 15
                    article_number = link.get_text(strip=True)
                    
                    # Only process if it looks like an article number
                    if not re.match(r'\d{5,7}', article_number):
                        continue
                    
                    # Get the parent row to extract DN and other specs
                    parent_row = link.find_parent('tr')
                    if parent_row:
                        cells = parent_row.find_all('td')
                        variant = self._extract_variant_from_cells(cells, model_name, article_number, full_url, standard)
                        if variant:
                            variants.append(variant)
            
            # Method 2: Fallback - parse tables with DN columns
            if not variants:
                tables = soup.find_all('table')
                
                for table in tables:
                    header_row = table.find('tr')
                    if not header_row:
                        continue
                    
                    header_text = header_row.get_text()
                    if 'DN' not in header_text and 'Zoll' not in header_text:
                        continue
                    
                    # Parse table rows
                    rows = table.find_all('tr')[1:]  # Skip header
                    
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) < 3:
                            continue
                        
                        # Extract article number from row
                        article_number = ""
                        for cell in cells:
                            link = cell.find('a', href=re.compile(r'/de/variant/'))
                            if link:
                                article_number = link.get_text(strip=True)
                                break
                        
                        variant = self._extract_variant_from_cells(cells, model_name, article_number, full_url, standard)
                        if variant:
                            variants.append(variant)
            
            # Method 3: Single product page (no variants table)
            if not variants:
                variant = self._extract_single_product(soup, model_name, full_url, standard)
                if variant:
                    variants.append(variant)
        
        except Exception as e:
            print(f"  Error scraping {model_name}: {e}")
        
        return variants
    
    def _extract_standard_from_page(self, soup, model_name: str) -> str:
        """Extract Standard/Norm information from product page or infer from model name"""
        try:
            # MAPPING: Heizmann model names to actual standards
            # Based on industry standards for hydraulic hoses
            model_to_standard = {
                '1SN': 'DIN EN 853 1SN',       # SAE 100R1AT equivalent
                '2SN': 'DIN EN 853 2SN',       # SAE 100R2AT equivalent
                '1SC': 'DIN EN 853 1SC',       # Compact version
                '2SC': 'DIN EN 853 2SC',       # Compact version
                '2TE': 'DIN EN 857 2TE',       # 2 textile braids
                '1TE': 'DIN EN 857 1TE',       # 1 textile braid
                '3TE': 'DIN EN 857 3TE',       # 3 textile braids
                '4SP': 'DIN EN 856 4SP',       # 4 spiral wire
                '4SH': 'DIN EN 856 4SH',       # 4 spiral high pressure
                '3SPT': 'DIN EN 856 3SPT',     # 3 spiral textile-covered
                'AT3': 'SAE 100R3',            # Textile braid low pressure
                'AT7': 'SAE 100R7',            # Thermoplastic medium pressure
                'AT8': 'SAE 100R8',            # Thermoplastic high pressure
                'COMP': 'DIN EN 853',          # Compact hose
                'ULTRA': 'DIN EN 853',         # Ultra-compact hose
                'FLP2': 'SAE 100R2',           # Flame-resistant version
                'ALFABIOTECH4K': 'DIN EN 856 4SP',  # 4 spiral wire
                'ALFABIOTECH6K': 'DIN EN 856 4SH',  # 4 spiral high pressure
                'ALFABIOTECH5K': 'DIN EN 856 4SP',  # 4 spiral wire
                'R1': 'SAE 100R1',
                'R2': 'SAE 100R2',
                'R3': 'SAE 100R3',
                'R5': 'SAE 100R5',
                'R6': 'SAE 100R6',
                'R7': 'SAE 100R7',
                'R8': 'SAE 100R8',
                'R12': 'SAE 100R12',
                'R13': 'SAE 100R13',
            }
            
            # Clean model name (remove spaces, hyphens)
            clean_model = model_name.strip().upper().replace('-', '').replace(' ', '')
            
            # Try exact match first
            if clean_model in model_to_standard:
                return model_to_standard[clean_model]
            
            # Try partial match (e.g., "2TE-04" contains "2TE")
            for key, value in model_to_standard.items():
                if key in clean_model:
                    return value
            
            # Fallback: try to find standards in page text
            page_text = soup.get_text()
            standard_patterns = [
                r'SAE\s*\d+R\d+[A-Z]*',           # SAE 100R2, SAE 100R2AT
                r'DIN\s*EN\s*\d{3,4}\s*[A-Z0-9]*',  # DIN EN 857 2TE, DIN EN 853 1SN
                r'EN\s*\d{3,4}\s*[A-Z0-9]+',        # EN 857 2TE (needs at least one letter/number after)
                r'ISO\s*\d{4,}',                    # ISO 1436 (at least 4 digits)
            ]
            
            for pattern in standard_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    clean_match = re.sub(r'\s+', ' ', match).strip()
                    # More strict validation:
                    # - Avoid DN patterns like "DN 16"
                    # - Must be at least 6 characters
                    # - If it starts with EN, it must have more than just a number
                    if (clean_match and 
                        'DN' not in clean_match.upper() and 
                        len(clean_match) >= 6 and
                        not re.match(r'^EN\s*\d+\s*$', clean_match, re.IGNORECASE)):
                        return clean_match
            
            return ""
            
        except Exception as e:
            print(f"    Warning: Error extracting standard: {str(e)}")
            return ""
    
    def _extract_single_product(self, soup, model_name: str, url: str, standard: str) -> Dict:
        """Extract data from single product page (no variants table)"""
        try:
            # Look for key product data in page
            page_text = soup.get_text()
            
            # Try to find DN from page text (look for "DN 12" or "DN12" pattern)
            dn_match = re.search(r'DN[:\s]*(\d+)', page_text)
            dn = f"DN{dn_match.group(1)}" if dn_match else ""
            
            # Try to find article number (Produktnummer or Artikelnummer)
            article_match = re.search(r'(?:Produktnummer|Artikelnummer)[:\s]*([A-Z0-9\-]+)', page_text)
            article_number = article_match.group(1) if article_match else ""
            
            # Try to find working pressure
            pressure_bar = None
            pressure_match = re.search(r'Betriebsdruck[:\s]*(\d+)\s*bar', page_text)
            if pressure_match:
                pressure_bar = int(pressure_match.group(1))
            
            # Try to find diameters
            inner_dia = None
            outer_dia = None
            dia_match = re.search(r'Ø\s*Innen[:\s]*(\d+[\.,]\d+)\s*mm', page_text)
            if dia_match:
                inner_dia = float(dia_match.group(1).replace(',', '.'))
            
            dia_match = re.search(r'Ø\s*Aussen[:\s]*(\d+[\.,]\d+)\s*mm', page_text)
            if dia_match:
                outer_dia = float(dia_match.group(1).replace(',', '.'))
            
            # If we have at least DN, create a product entry
            if dn:
                construction = self._determine_construction(model_name, standard)
                
                return {
                    'supplier': 'Heizmann',
                    'model': model_name,
                    'category': 'Hochdruck-Gummischläuche',
                    'source_url': url,
                    'dn': dn,
                    'article_number': article_number,
                    'product_number': article_number,
                    'reference': article_number,
                    'inner_diameter_mm': inner_dia,
                    'outer_diameter_mm': outer_dia,
                    'working_pressure_bar': pressure_bar,
                    'standard': standard,
                    'construction': construction,
                }
        
        except Exception as e:
            pass
        
        return None
    
    def _determine_construction(self, model_name: str, standard: str) -> str:
        """Determine construction type from model name and standard"""
        name_upper = model_name.upper()
        std_upper = standard.upper()
        combined = f"{name_upper} {std_upper}"
        
        # 4-wire spiral constructions
        if '4SP' in combined or '4SH' in combined or 'SPIRAL' in combined:
            return 'spiral wire'
        
        # 2-wire braid constructions
        elif '2SC' in combined or '2SN' in combined:
            return '2 wire braid'
        
        # 1-wire braid constructions
        elif '1SC' in combined or '1SN' in combined:
            return '1 wire braid'
        
        # Textile braid constructions
        elif '2TE' in combined:
            return '2 textile braid'
        elif '1TE' in combined or '3TE' in combined:
            return '1 textile braid'
        
        # SAE R-series classifications
        elif 'R1' in combined:
            return '1 wire braid'
        elif 'R2' in combined:
            return '2 wire braid'
        elif 'R3' in combined or 'R6' in combined:
            return 'textile braid'
        elif 'R5' in combined or 'R8' in combined:
            return 'textile'
        
        # Default fallback
        else:
            return 'wire braid'
    
    def _extract_variant_from_cells(self, cells, model_name: str, article_number: str, url: str, standard: str = "") -> Dict:
        """Extract product variant from table cells - FIXED FOR HEIZMANN STRUCTURE"""
        try:
            # Get all text from cells
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            
            # HEIZMANN TABLE STRUCTURE (from debug output):
            # Cell 0: Empty checkbox
            # Cell 1: DN (as number: 6, 8, 10, 12, etc.)
            # Cell 2: Zoll-Code (inch code: 4, 5, 6, etc. or negative numbers)
            # Cell 3: Ø Innen (inner diameter in mm)
            # Cell 4: Ø Aussen (outer diameter in mm)
            # Cell 5: BR (bend radius in mm)
            # Cell 6: BD (burst pressure in bar)
            # Cell 7: PD (working pressure in bar)
            # Cell 8: Gewicht (weight in kg)
            # Cell 9: Prod. Nr. (product number like 2TE-04)
            # Cell 10: Art. Nr. (article number like 484321)
            
            # Extract DN from cell 1
            dn = ""
            if len(cell_texts) > 1 and cell_texts[1].isdigit():
                dn = f"DN{cell_texts[1]}"
            
            # Extract inch code from cell 2
            inch_size = ""
            if len(cell_texts) > 2:
                inch_code = cell_texts[2]
                if re.match(r'-?\d+$', inch_code):
                    # Convert inch code to fraction (simplified)
                    code_num = abs(int(inch_code))
                    if code_num <= 32:
                        inch_size = f"{code_num}/16\""
            
            # Extract inner diameter from cell 3
            inner_dia = None
            if len(cell_texts) > 3:
                try:
                    inner_dia = float(cell_texts[3].replace(',', '.'))
                except:
                    pass
            
            # Extract outer diameter from cell 4
            outer_dia = None
            if len(cell_texts) > 4:
                try:
                    outer_dia = float(cell_texts[4].replace(',', '.'))
                except:
                    pass
            
            # Extract bend radius from cell 5
            bend_radius = None
            if len(cell_texts) > 5:
                try:
                    bend_radius = float(cell_texts[5].replace(',', '.'))
                except:
                    pass
            
            # Extract burst pressure from cell 6
            burst_pressure = None
            if len(cell_texts) > 6:
                try:
                    burst_pressure = int(cell_texts[6])
                except:
                    pass
            
            # Extract working pressure from cell 7
            working_pressure = None
            if len(cell_texts) > 7:
                try:
                    working_pressure = int(cell_texts[7])
                except:
                    pass
            
            # Extract product number from cell 9 (contains model designation)
            product_number = ""
            if len(cell_texts) > 9:
                product_number = cell_texts[9]
            
            # Create variant dict
            variant = {
                'supplier': 'Heizmann',
                'model': model_name,
                'category': 'Hochdruck-Gummischläuche',
                'source_url': url
            }
            
            if dn:
                variant['dn'] = dn
            
            if article_number and re.match(r'\d{5,7}', article_number):
                variant['article_number'] = article_number
            
            if product_number:
                variant['product_number'] = product_number
            
            if inch_size:
                variant['inch_size'] = inch_size
            
            if inner_dia:
                variant['inner_diameter_mm'] = inner_dia
            
            if outer_dia:
                variant['outer_diameter_mm'] = outer_dia
            
            if bend_radius:
                variant['bend_radius_mm'] = bend_radius
            
            if working_pressure:
                variant['working_pressure_bar'] = working_pressure
            
            if burst_pressure:
                variant['burst_pressure_bar'] = burst_pressure
            
            # Add the standard/norm extracted from the product page
            if standard:
                variant['standard'] = standard
            
            # Add construction type based on model and standard
            variant['construction'] = self._determine_construction(model_name, standard)
            
            # Add reference field (required by matcher)
            variant['reference'] = product_number if product_number else model_name
            
            # Must have at least DN and article number to be valid
            return variant if (dn and article_number) else None
            
        except Exception as e:
            print(f"  DEBUG: Exception in extraction: {e}")
            return None
    
    def save_to_json(self, output_file: str):
        """Save to JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.products, f, indent=2, ensure_ascii=False)
        
        print(f"\nSaved {len(self.products)} Heizmann products")


def main():
    """Test"""
    output_file = Path(__file__).parent.parent / 'data' / 'heizmann_products.json'
    
    scraper = HeizmannScraper()
    products = scraper.scrape()
    scraper.save_to_json(str(output_file))
    
    print(f"\n=== Summary ===")
    print(f"Total products: {len(products)}")
    
    # Show sample
    if products:
        print("\nSample product:")
        print(json.dumps(products[0], indent=2))
    
    # Count by model
    models = {}
    for p in products:
        m = p.get('model', 'Unknown')
        models[m] = models.get(m, 0) + 1
    
    print(f"\nBy model:")
    for model, count in sorted(models.items()):
        print(f"  {model}: {count}")


if __name__ == '__main__':
    main()
