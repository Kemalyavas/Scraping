"""
Heizmann Fittings Scraper
Scrapes hydraulic fittings from 15+ categories
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
import random
from typing import List, Dict

class HeizmannFittingsScraper:
    def __init__(self):
        self.base_url = "https://www.heizmann.ch"
        self.session = requests.Session()
        
        # Rotate User-Agents to avoid detection
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        self._update_user_agent()
        
        self.products = []
        self.request_count = 0
        
        # 15 fitting categories
        self.categories = [
            ("Pressarmaturen Serie X", "/de/category/14/pressarmaturen-serie-x"),
            ("Pressarmaturen Serie IX Edelstahl", "/de/category/8332/pressarmaturen-serie-ix-edelstahl"),
            ("Pressarmaturen Serie HPE/HP (Interlock)", "/de/category/27/pressarmaturen-serie-hpe-hp-interlock"),
            ("Pressarmaturen Serie XJ (700Bar)", "/de/category/40/pressarmaturen-serie-xj-700bar"),
            ("Schneidring-Rohrverschraubungen", "/de/category/88/schneidring-rohrverschraubungen"),
            ("ORFS Verschraubungen", "/de/category/46/orfs-verschraubungen"),
            ("Adapter", "/de/category/60/adapter"),
            ("Flansche", "/de/category/76/flansche"),
            ("System WEO", "/de/category/73/system-weo"),
            ("Messtechnik", "/de/category/114/messtechnik"),
            ("Leitungszubehör", "/de/category/108/leitungszubehoer"),
            ("Rohrtechnik", "/de/category/128/rohrtechnik"),
            ("Staub- & Gewindeschutz", "/de/category/84/staub-gewindeschutz"),
            ("Hydraulik-Dichtungen", "/de/category/154/hydraulik-dichtungen"),
            ("Sortimente", "/de/category/162/sortimente"),
        ]
    
    def _update_user_agent(self):
        """Rotate User-Agent"""
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def scrape(self) -> List[Dict]:
        """Scrape all fitting categories"""
        print("Heizmann Fittings Scraper")
        print("=" * 70)
        
        for category_name, category_url in self.categories:
            print(f"\nCategory: {category_name}")
            print("-" * 70)
            
            # Longer delay between categories + rotate UA
            time.sleep(random.uniform(3.0, 5.0))
            self._update_user_agent()
            
            # Get product links from category
            product_links = self._get_product_links(category_url)
            print(f"Found {len(product_links)} products")
            
            # Scrape each product
            for idx, (name, url) in enumerate(product_links, 1):
                # Variable delay between products (2-4 seconds)
                time.sleep(random.uniform(2.0, 4.0))
                
                # Longer pause every 10 products
                if idx % 10 == 0:
                    print(f"  [Pause after {idx} products - avoiding rate limit...]")
                    time.sleep(random.uniform(8.0, 12.0))
                    self._update_user_agent()
                
                try:
                    variants = self._scrape_product_page(name, url, category_name)
                    self.products.extend(variants)
                    print(f"  {name}: {len(variants)} variants")
                except Exception as e:
                    print(f"  {name}: Error - {e}")
                    continue
        
        print(f"\n{'=' * 70}")
        print(f"Total products scraped: {len(self.products)}")
        return self.products
    
    def _get_product_links(self, category_url: str) -> List[tuple]:
        """Get all product links from category page"""
        products = []
        
        try:
            url = f"{self.base_url}{category_url}"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find product links
            links = soup.find_all('a', href=re.compile(r'/de/product/\d+/'))
            
            seen = set()
            for link in links:
                href = link.get('href')
                name = link.get_text(strip=True)
                
                if href not in seen and name and len(name) <= 100:
                    products.append((name, href))
                    seen.add(href)
        
        except Exception as e:
            print(f"  Error getting links: {e}")
        
        return products
    
    def _scrape_product_page(self, model_name: str, url: str, category: str) -> List[Dict]:
        """Scrape product page for variants"""
        variants = []
        
        try:
            full_url = f"{self.base_url}{url}"
            
            # Add small random delay before request
            time.sleep(random.uniform(0.5, 1.5))
            
            response = self.session.get(full_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Method 1: Variant links (tables)
            variant_links = soup.find_all('a', href=re.compile(r'/de/variant/\d+/'))
            
            if variant_links:
                for link in variant_links[:50]:
                    article_number = link.get_text(strip=True)
                    
                    if not re.match(r'\d{5,7}', article_number):
                        continue
                    
                    parent_row = link.find_parent('tr')
                    if parent_row:
                        cells = parent_row.find_all('td')
                        variant = self._extract_from_cells(cells, model_name, article_number, full_url, category)
                        if variant:
                            variants.append(variant)
            
            # Method 2: Single product page (no table)
            if not variants:
                variant = self._extract_single_product(soup, model_name, full_url, category)
                if variant:
                    variants.append(variant)
        
        except Exception as e:
            print(f"    Error: {e}")
        
        return variants
    
    def _extract_from_cells(self, cells, model_name: str, article_number: str, url: str, category: str) -> Dict:
        """Extract fitting data from table cells"""
        
        if len(cells) < 3:
            return None
        
        try:
            # Extract text from all cells
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            
            # Find DN, size, thread info
            dn = ""
            size = ""
            thread_type = ""
            connection_type = ""
            material = ""
            
            for text in cell_texts:
                # DN pattern
                if re.match(r'DN\s*\d+', text, re.IGNORECASE):
                    dn = text
                
                # Size patterns (1/4", M16x1.5, etc.)
                if re.search(r'\d+/\d+"', text):  # 1/4"
                    size = text
                elif re.search(r'M\d+', text):  # M16x1.5
                    size = text
                
                # Thread types
                if any(t in text.upper() for t in ['BSP', 'NPT', 'JIC', 'ORFS', 'METRIC', 'UNF']):
                    thread_type = text
                
                # Connection types
                if any(c in text.upper() for c in ['MALE', 'FEMALE', 'ELBOW', 'TEE', 'STRAIGHT']):
                    connection_type = text
                
                # Material
                if any(m in text.upper() for m in ['STEEL', 'STAINLESS', 'BRASS', 'EDELSTAHL']):
                    material = text
            
            return {
                'supplier': 'Heizmann',
                'category': category,
                'model': model_name,
                'article_number': article_number,
                'reference': article_number,
                'dn': dn,
                'size': size,
                'thread_type': thread_type,
                'connection_type': connection_type,
                'material': material,
                'source_url': url,
            }
        
        except Exception as e:
            return None
    
    def _extract_single_product(self, soup, model_name: str, url: str, category: str) -> Dict:
        """Extract from single product page (no variant table)"""
        
        try:
            page_text = soup.get_text()
            
            # Find article number
            article_match = re.search(r'(?:Produktnummer|Artikelnummer)[:\s]*([A-Z0-9\-\.]+)', page_text)
            article_number = article_match.group(1) if article_match else model_name
            
            # Find DN
            dn_match = re.search(r'DN[:\s]*(\d+)', page_text)
            dn = f"DN{dn_match.group(1)}" if dn_match else ""
            
            # Find thread/size
            size_match = re.search(r'(\d+/\d+"|\d+"\s|M\d+x[\d\.]+)', page_text)
            size = size_match.group(1).strip() if size_match else ""
            
            # Thread type
            thread_type = ""
            for t in ['BSP', 'NPT', 'JIC', 'ORFS', 'METRIC', 'UNF']:
                if t in page_text.upper():
                    thread_type = t
                    break
            
            return {
                'supplier': 'Heizmann',
                'category': category,
                'model': model_name,
                'article_number': article_number,
                'reference': article_number,
                'dn': dn,
                'size': size,
                'thread_type': thread_type,
                'connection_type': '',
                'material': '',
                'source_url': url,
            }
        
        except:
            return None
    
    def save_to_json(self, filename: str):
        """Save products to JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.products, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Saved to {filename}")


if __name__ == "__main__":
    scraper = HeizmannFittingsScraper()
    products = scraper.scrape()
    scraper.save_to_json('data/heizmann_fittings.json')
    
    print(f"\n{'=' * 70}")
    print(f"Summary: {len(products)} fittings scraped from 15 categories")
