import requests
from bs4 import BeautifulSoup

# Try to access ALFABIOTECH 4K page directly
url = 'https://www.heizmann.ch/de/product/236/alfabiotech-4k'

try:
    r = requests.get(url, timeout=10)
    print(f'Status: {r.status_code}')
    
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Get page title
        title = soup.find('h1')
        print(f'Title: {title.text.strip() if title else "No title"}')
        
        # Look for tables
        tables = soup.find_all('table')
        print(f'\nFound {len(tables)} tables')
        
        # Check if page has product data
        if len(r.text) < 5000:
            print('\nPage seems very short - might be empty or redirect')
            print(f'Page length: {len(r.text)} characters')
        else:
            print(f'\nPage looks normal ({len(r.text)} characters)')
            
            # Try to find variant table
            for i, table in enumerate(tables):
                rows = table.find_all('tr')
                print(f'\nTable {i+1}: {len(rows)} rows')
                if rows and len(rows) > 0:
                    print(f'First row: {rows[0].text.strip()[:100]}')
    
except Exception as e:
    print(f'Error: {e}')
