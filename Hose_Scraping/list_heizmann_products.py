import requests
from bs4 import BeautifulSoup
import re

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

url = 'https://www.heizmann.ch/de/category/5/hochdruck-gummischlaeuche'

try:
    r = session.get(url, timeout=10)
    print(f'Status: {r.status_code}\n')
    
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Find all product links
        links = soup.find_all('a', href=re.compile(r'/de/product/\d+/'))
        
        print(f'Found {len(links)} product links\n')
        
        seen = set()
        products = []
        
        for link in links:
            href = link.get('href')
            name = link.get_text(strip=True)
            
            if href not in seen and name and len(name) <= 50:
                products.append((name, href))
                seen.add(href)
        
        print(f'{len(products)} unique products:\n')
        for i, (name, href) in enumerate(products, 1):
            # Highlight ALFABIOTECH
            marker = " ⭐" if "ALFABIOTECH" in name.upper() else ""
            print(f'{i:2}. {name}{marker}')
            print(f'    {href}')
            
except Exception as e:
    print(f'Error: {e}')
