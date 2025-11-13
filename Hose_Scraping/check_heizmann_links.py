import requests
from bs4 import BeautifulSoup
import re

url = 'https://www.heizmann.ch/de/category/5/hochdruck-gummischlaeuche'
r = requests.get(url)
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
    print(f'{i:2}. {name} ({href})')
