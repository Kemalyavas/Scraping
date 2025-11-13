from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import json

# Selenium driver - global (bir kere aç, hep kullan)
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--window-size=1920,1080')

driver = webdriver.Chrome(options=chrome_options)

def scrape_category_links(category_url):
    """Selenium ile 'Mehr anzeigen' butonuna tıklayarak tüm ürün linklerini çek"""
    
    driver.get(category_url)
    time.sleep(3)
    
    click_count = 0
    max_clicks = 30
    
    # "Mehr anzeigen" butonuna tıkla (varsa)
    while click_count < max_clicks:
        try:
            button = driver.find_element(By.ID, "show-more-button")
            
            if not button.is_displayed():
                break
            
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", button)
            click_count += 1
            time.sleep(4)
            
        except:
            break
    
    # Product linklerini topla
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    product_links = set()
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        if '/product/' in href:
            full_url = f"https://www.heizmann.ch{href}" if href.startswith('/') else href
            product_links.add(full_url)
    
    return list(product_links)


def scrape_product_details(product_url):
    """Selenium ile ürün detaylarını çek - ÖZELLİKLER + VARYANTLAR"""
    
    try:
        driver.get(product_url)
        time.sleep(1.2)
        
        # Model
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        h1 = soup.find('h1')
        model = h1.text.strip() if h1 else ''
        
        # PRODUKTDETAILS sekmesine tıkla (özellikler tablosu için)
        try:
            detail_tab = driver.find_element(By.XPATH, "//button[contains(text(), 'Produktdetails')]")
            driver.execute_script("arguments[0].click();", detail_tab)
            time.sleep(0.5)
        except:
            pass  # Sekme yoksa devam et
        
        # Şimdi sayfayı tekrar oku
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # ÖZELLİKLER (attribute-table div'lerinden)
        specifications = {}
        attribute_rows = soup.find_all('div', class_=lambda x: x and 'attribute-table' in x)
        
        for row in attribute_rows:
            label_div = row.find('div', class_=lambda x: x and 'pim-table-label' in x)
            value_div = row.find('div', class_=lambda x: x and 'pim-table-value' in x)
            
            if label_div and value_div:
                key = label_div.text.strip()
                value = value_div.text.strip()
                specifications[key] = value
        
        # Standart/Norm çıkar (Almanca)
        standard = specifications.get('Normen', '')
        seat_type = specifications.get('Dichtform', '')
        connection = specifications.get('Anschluss', '')
        
        # ARTIKELVARIANTEN sekmesine dön (varyant tablosu için)
        try:
            variant_tab = driver.find_element(By.XPATH, "//button[contains(text(), 'Artikelvarianten')]")
            driver.execute_script("arguments[0].click();", variant_tab)
            time.sleep(0.5)
        except:
            pass
        
        # Sayfayı tekrar oku
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # VARYANT TABLOSU (Artikelvarianten sekmesindeki - DN, size, thread vs.)
        variant_table = None
        for table in soup.find_all('table'):
            header_row = table.find('thead')
            if header_row and 'DN' in header_row.text:
                variant_table = table
                break
        
        if not variant_table:
            return []
        
        # Headers
        header_row = variant_table.find('thead').find('tr')
        if not header_row:
            return []
        
        header_cells = header_row.find_all('th')
        headers = [' '.join(th.text.split()) for th in header_cells]
        
        # Column indices
        dn_idx = next((i for i, h in enumerate(headers) if h == 'DN'), None)
        thread_idx = next((i for i, h in enumerate(headers) if h == 'm'), None)  # Thread size sütunu
        ident_idx = next((i for i, h in enumerate(headers) if 'Ident' in h or 'für' in h), None)
        article_idx = next((i for i, h in enumerate(headers) if 'Art. Nr.' in h), None)
        ref_idx = next((i for i, h in enumerate(headers) if 'Prod. Nr.' in h), None)
        ref_idx = next((i for i, h in enumerate(headers) if 'Prod. Nr.' in h or 'Ürün No.' in h), None)
        
        # Rows
        tbody = variant_table.find('tbody')
        if not tbody:
            return []
        
        products = []
        for row in tbody.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) < len(headers):
                continue
            
            product = {
                'model': model,
                'category': 'Pressarmaturen Serie X',
                'dn': cells[dn_idx].text.strip() if dn_idx is not None else None,
                'thread_size': cells[thread_idx].text.strip() if thread_idx is not None else None,
                'identification': cells[ident_idx].text.strip() if ident_idx is not None else None,
                'standard': standard,
                'seat_type': seat_type,
                'connection_type': connection,
                'article_number': cells[article_idx].text.strip() if article_idx is not None else None,
                'reference': cells[ref_idx].text.strip() if ref_idx is not None else None,
                'url': product_url
            }
            
            # Temizlik
            for key in ['dn', 'thread_size', 'identification', 'article_number', 'reference']:
                if product.get(key) == '' or product.get(key) == '-':
                    product[key] = None
            
            products.append(product)
        
        return products
        
    except Exception as e:
        print(f" ✗ HATA: {str(e)[:30]}")
        return []


# ============================================================================
# PRESSARMATUREN SERIE X - TÜM 12 KATEGORİ
# ============================================================================

subcategories = [
    ('Presshülsen', 'https://www.heizmann.ch/de/category/15/presshuelsen'),
    ('Pressnippel metrisch', 'https://www.heizmann.ch/de/category/16/pressnippel-metrisch'),
    ('Pressnippel BSP', 'https://www.heizmann.ch/de/category/17/pressnippel-bsp'),
    ('Pressnippel NPT', 'https://www.heizmann.ch/de/category/18/pressnippel-npt'),
    ('Pressnippel JIC', 'https://www.heizmann.ch/de/category/19/pressnippel-jic'),
    ('ORFS', 'https://www.heizmann.ch/de/category/20/orfs'),
    ('SMR', 'https://www.heizmann.ch/de/category/21/smr'),
    ('SAE 90°', 'https://www.heizmann.ch/de/category/22/sae-90'),
    ('Flansch 3000PSI', 'https://www.heizmann.ch/de/category/23/flansch-3000psi'),
    ('Flansch 6000PSI', 'https://www.heizmann.ch/de/category/24/flansch-6000psi'),
    ('System WEO', 'https://www.heizmann.ch/de/category/25/system-weo'),
    ('OD', 'https://www.heizmann.ch/de/category/26/od'),
]

print("="*80)
print("PRESSARMATUREN SERIE X - TAM SCRAPING (TEK SELENIUM SESSION)")
print("="*80)
print()

all_products = []

try:
    for cat_name, cat_url in subcategories:
        print(f"\n{'='*80}")
        print(f"KATEGORİ: {cat_name}")
        print(f"{'='*80}")
        
        # 1. Ürün linklerini çek
        print("1. Ürün linkleri çekiliyor...")
        product_urls = scrape_category_links(cat_url)
        print(f"   ✓ {len(product_urls)} ürün bulundu")
        
        # 2. Her ürünün detaylarını çek
        print("2. Ürün detayları çekiliyor...")
        for i, url in enumerate(product_urls, 1):
            product_name = url.split('/')[-1]
            print(f"   [{i}/{len(product_urls)}] {product_name}", end='', flush=True)
            
            products = scrape_product_details(url)
            
            if products:
                print(f" ✓ {len(products)} variant")
                all_products.extend(products)
            else:
                print(f" ✗ Tablo yok")
            
            time.sleep(0.3)  # Rate limiting

    print(f"\n\n{'='*80}")
    print(f"TOPLAM: {len(all_products)} ürün variant")
    print(f"{'='*80}")

    # Kaydet
    with open('data/pressarmaturen_serie_x_FULL_SELENIUM.json', 'w', encoding='utf-8') as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Kaydedildi: data/pressarmaturen_serie_x_FULL_SELENIUM.json")

    # Sample
    if all_products:
        print(f"\nSample ürün:")
        sample = all_products[0]
        print(f"  Article: {sample['article_number']}")
        print(f"  Model: {sample['model']}")
        print(f"  DN: {sample['dn']}")
        print(f"  Thread Size: {sample.get('thread_size', 'N/A')}")
        print(f"  Standard: {sample.get('standard', 'N/A')}")
        print(f"  Seat Type: {sample.get('seat_type', 'N/A')}")

    print(f"\n✓ Scraping tamamlandı!")
    
finally:
    driver.quit()
    print("\n✓ Tarayıcı kapatıldı")
