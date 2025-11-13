import requests
from bs4 import BeautifulSoup

url = 'https://www.heizmann.ch/de/category/5/hochdruck-gummischlaeuche'
r = requests.get(url)
soup = BeautifulSoup(r.text, 'html.parser')

products = soup.find_all('div', class_='product-item')
print(f'Found {len(products)} product divs\n')

for i, p in enumerate(products, 1):
    title = p.find('h3')
    if title:
        print(f'{i:2}. {title.text.strip()}')
    else:
        print(f'{i:2}. (no title)')
