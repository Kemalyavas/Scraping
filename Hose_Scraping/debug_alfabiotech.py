import requests
from bs4 import BeautifulSoup
import re

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

url = 'https://www.heizmann.ch/de/product/236/alfabiotech-4k'

try:
    r = session.get(url, timeout=10)
    print(f'Status: {r.status_code}\n')
    
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Get title
        title = soup.find('h1')
        print(f'Title: {title.text.strip() if title else "No title"}\n')
        
        # Check for variant links
        variant_links = soup.find_all('a', href=re.compile(r'/de/variant/\d+/'))
        print(f'Variant links: {len(variant_links)}')
        
        if variant_links:
            print('First 3 variant links:')
            for link in variant_links[:3]:
                print(f'  {link.get_text(strip=True)} -> {link.get("href")}')
        
        # Check for tables with DN
        tables = soup.find_all('table')
        print(f'\nTables: {len(tables)}')
        
        for i, table in enumerate(tables[:3]):
            header = table.find('tr')
            if header:
                header_text = header.get_text()[:100]
                print(f'  Table {i+1} header: {header_text}')
                
                has_dn = 'DN' in header_text or 'Zoll' in header_text
                print(f'    Has DN/Zoll: {has_dn}')
                
                rows = table.find_all('tr')
                print(f'    Rows: {len(rows)}')
        
        # Save HTML for manual inspection
        with open('alfabiotech_page.html', 'w', encoding='utf-8') as f:
            f.write(r.text)
        print('\n✓ Saved page HTML to alfabiotech_page.html')
        
except Exception as e:
    print(f'Error: {e}')
