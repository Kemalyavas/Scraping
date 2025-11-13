"""
IMPROVED Heizmann Fittings Scraper
Properly extracts thread types, sizes, and DN from product table data
"""

import json
import requests
from bs4 import BeautifulSoup
import re
import time
import random
from typing import List, Dict


class ImprovedHeizmannScraper:
    """Scrapes Heizmann fittings with improved data extraction"""
    
    def __init__(self):
        self.base_url = "https://www.heizmann.ch"
        self.session = requests.Session()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        self._update_user_agent()
        
        self.products = []
        
        # 15 categories from user's file
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
            'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.heizmann.ch/'
        })
    
    def scrape(self) -> List[Dict]:
        """Scrape all fitting categories"""
        print("IMPROVED Heizmann Fittings Scraper")
        print("=" * 70)
        
        for category_name, category_url in self.categories:
            print(f"\nCategory: {category_name}")
            print("-" * 70)
            
            # Get product links
            product_links = self._get_product_links(category_url)
            print(f"Products found: {len(product_links)}")
            
            # Scrape each product
            for idx, (name, url) in enumerate(product_links, 1):
                time.sleep(random.uniform(2.0, 4.0))
                
                if idx % 10 == 0:
                    print(f"  [Pause after {idx} products...]")
                    time.sleep(random.uniform(8.0, 12.0))
                    self._update_user_agent()
                
                try:
                    variants = self._scrape_product_page(name, url, category_name)
                    self.products.extend(variants)
                    print(f"  {name}: {len(variants)} variants")
                except Exception as e:
                    print(f"  {name}: Error - {e}")
                    continue
            
            # Delay between categories
            time.sleep(random.uniform(3.0, 5.0))
        
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
        """Scrape product page for variants - IMPROVED VERSION"""
        variants = []
        
        try:
            full_url = f"{self.base_url}{url}"
            time.sleep(random.uniform(0.5, 1.5))
            
            response = self.session.get(full_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the main product data table
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                if len(rows) < 2:
                    continue
                
                # Parse header row to find column indices
                header_row = rows[0]
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
                
                # Find important column indices
                col_indices = {
                    'article': None,
                    'prod_nr': None,
                    'thread_g': None,
                    'thread_b': None,
                    'dn': None,
                    'size': None,
                    'sw': None,
                    'pressure': None,
                }
                
                for i, header in enumerate(headers):
                    header_lower = header.lower()
                    if 'art' in header_lower and 'nr' in header_lower:
                        col_indices['article'] = i
                    elif 'prod' in header_lower and 'nr' in header_lower:
                        col_indices['prod_nr'] = i
                    elif header in ['16G', '8G', 'G', 'BSP']:
                        col_indices['thread_g'] = i
                    elif header in ['16B', '8B', 'B', 'ORFS', 'JIC']:
                        col_indices['thread_b'] = i
                    elif 'dn' in header_lower:
                        col_indices['dn'] = i
                    elif 'sw' in header_lower:
                        col_indices['sw'] = i
                    elif 'bd' in header_lower or 'bar' in header_lower:
                        col_indices['pressure'] = i
                
                # Parse data rows
                for row in rows[1:]:
                    cells = row.find_all(['td', 'th'])
                    
                    if len(cells) < 3:
                        continue
                    
                    cell_texts = [cell.get_text(strip=True) for cell in cells]
                    
                    # Extract article number
                    article_number = None
                    if col_indices['article'] is not None and col_indices['article'] < len(cell_texts):
                        article_number = cell_texts[col_indices['article']]
                    
                    # Try to find article number in any cell if not found
                    if not article_number:
                        for text in cell_texts:
                            if re.match(r'^\d{6}', text):  # 6-digit article number
                                article_number = re.match(r'(\d{6})', text).group(1)
                                break
                    
                    if not article_number:
                        continue
                    
                    # Extract thread types
                    thread_g = None
                    thread_b = None
                    if col_indices['thread_g'] is not None and col_indices['thread_g'] < len(cell_texts):
                        thread_g = cell_texts[col_indices['thread_g']]
                    if col_indices['thread_b'] is not None and col_indices['thread_b'] < len(cell_texts):
                        thread_b = cell_texts[col_indices['thread_b']]
                    
                    # Determine primary thread type and size
                    thread_type = ""
                    size = ""
                    
                    if thread_g and thread_g != '-':
                        if 'G' in thread_g or 'BSP' in thread_g.upper():
                            thread_type = "BSP"
                            size = thread_g
                        elif 'NPT' in thread_g.upper():
                            thread_type = "NPT"
                            size = thread_g
                        elif 'M' in thread_g and 'x' in thread_g:
                            thread_type = "Metric"
                            size = thread_g
                    
                    if thread_b and thread_b != '-':
                        if 'UNF' in thread_b.upper() or 'UN' in thread_b.upper():
                            if not thread_type:  # Use if no other thread found
                                thread_type = "ORFS/UNF"
                                size = thread_b
                            elif thread_type == "BSP":  # Adapter: has both
                                thread_type = "BSP/ORFS"
                                size = f"{thread_g} / {thread_b}"
                        elif 'JIC' in thread_b.upper():
                            if not thread_type:
                                thread_type = "JIC"
                                size = thread_b
                    
                    # Extract DN
                    dn = ""
                    if col_indices['dn'] is not None and col_indices['dn'] < len(cell_texts):
                        dn = cell_texts[col_indices['dn']]
                    
                    # Extract SW (wrench size)
                    sw = ""
                    if col_indices['sw'] is not None and col_indices['sw'] < len(cell_texts):
                        sw = cell_texts[col_indices['sw']]
                    
                    # Extract pressure
                    pressure = ""
                    if col_indices['pressure'] is not None and col_indices['pressure'] < len(cell_texts):
                        pressure = cell_texts[col_indices['pressure']]
                    
                    # Fallback: detect thread type from category
                    if not thread_type:
                        if 'ORFS' in category:
                            thread_type = "ORFS"
                        elif 'Schneidring' in category:
                            thread_type = "Metric (Schneidring)"
                        elif 'JIC' in category.upper():
                            thread_type = "JIC"
                        elif 'BSP' in category or 'Pressarmaturen' in category:
                            thread_type = "BSP"
                    
                    variant = {
                        'supplier': 'Heizmann',
                        'category': category,
                        'model': model_name,
                        'article_number': article_number,
                        'reference': article_number,
                        'DN': dn,
                        'size': size,
                        'thread_type': thread_type,
                        'connection_type': '',
                        'material': '',
                        'sw': sw,
                        'pressure': pressure,
                        'url': full_url,
                    }
                    
                    variants.append(variant)
        
        except Exception as e:
            print(f"    Error parsing {url}: {e}")
        
        return variants
    
    def save(self, filename: str):
        """Save scraped products to JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.products, f, ensure_ascii=False, indent=2)
        print(f"\nSaved {len(self.products)} products to {filename}")


if __name__ == "__main__":
    scraper = ImprovedHeizmannScraper()
    products = scraper.scrape()
    scraper.save('data/heizmann_fittings_improved.json')
