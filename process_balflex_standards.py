import json
import re

# Balflex data oku
with open('data/balflex_fittings_with_gender.json', 'r', encoding='utf-8') as f:
    balflex_data = json.load(f)

print(f"Toplam {len(balflex_data)} Balflex ürün")

# Product type'tan standard ve seat type çıkar
def extract_standard(product_type):
    """JIS, BSP, NPT, SAE, ORFS, ISO gibi standartları çıkar"""
    if not product_type:
        return None
    
    product_upper = product_type.upper()
    
    # Specific patterns
    if 'JIS' in product_upper:
        # JIS 8434-6 gibi detaylı varsa al, yoksa sadece JIS
        match = re.search(r'JIS\s*\d+(?:-\d+)?', product_type, re.IGNORECASE)
        if match and 'JIS 60' not in match.group(0):  # "JIS 60°" değil "JIS 8363" gibi
            return match.group(0)
        return 'JIS'
    
    if 'BSP' in product_upper:
        return 'BSP'
    
    if 'NPT' in product_upper or 'NPTF' in product_upper:
        return 'NPT'
    
    if 'JIC' in product_upper:
        # JIC 37° gibi detaylı varsa al
        match = re.search(r'JIC\s*\d+', product_type, re.IGNORECASE)
        if match and '37' not in match.group(0):
            return match.group(0)
        return 'JIC'
    
    if 'ORFS' in product_upper or 'O-RING FACE SEAL' in product_upper:
        return 'ORFS'
    
    if 'SAE' in product_upper:
        match = re.search(r'SAE\s*\d+', product_type, re.IGNORECASE)
        if match:
            return match.group(0)
        return 'SAE'
    
    if 'ISO' in product_upper:
        match = re.search(r'ISO\s*\d+(?:-\d+)?', product_type, re.IGNORECASE)
        if match:
            return match.group(0)
        return 'ISO'
    
    if 'DIN' in product_upper:
        match = re.search(r'DIN\s*\d+', product_type, re.IGNORECASE)
        if match:
            return match.group(0)
        return 'DIN'
    
    if 'KOMATSU' in product_upper:
        return 'KOMATSU'
    
    if 'CATERPILLAR' in product_upper or 'CAT' in product_upper:
        return 'CATERPILLAR'
    
    return None

def extract_seat_type(product_type):
    """60° Cone Seat, 74° Cone, Flat Face gibi seat type'ları çıkar"""
    if not product_type:
        return None
    
    # 60° Cone Seat, 74° Cone, etc.
    cone_match = re.search(r'\d+°\s*(?:Cone|Inner Cone|Innenkonus)', product_type, re.IGNORECASE)
    if cone_match:
        return cone_match.group(0)
    
    # Flat Face
    if 'flat face' in product_type.lower():
        return 'Flat Face'
    
    # O-Ring
    if 'o-ring' in product_type.lower() or 'oring' in product_type.lower():
        return 'O-Ring'
    
    return None

# Her ürüne ekle
for product in balflex_data:
    product_type = product.get('product_type', '')
    
    product['standard'] = extract_standard(product_type)
    product['seat_type'] = extract_seat_type(product_type)

# İstatistikler
standards_count = {}
seat_types_count = {}
no_standard = 0
no_seat = 0

for product in balflex_data:
    std = product.get('standard')
    seat = product.get('seat_type')
    
    if std:
        standards_count[std] = standards_count.get(std, 0) + 1
    else:
        no_standard += 1
    
    if seat:
        seat_types_count[seat] = seat_types_count.get(seat, 0) + 1
    else:
        no_seat += 1

print("\n=== STANDARDS ===")
for std, count in sorted(standards_count.items(), key=lambda x: -x[1]):
    print(f"{std}: {count}")
print(f"No Standard: {no_standard}")

print("\n=== SEAT TYPES ===")
for seat, count in sorted(seat_types_count.items(), key=lambda x: -x[1]):
    print(f"{seat}: {count}")
print(f"No Seat Type: {no_seat}")

# Kaydet
with open('data/balflex_fittings_ENHANCED.json', 'w', encoding='utf-8') as f:
    json.dump(balflex_data, f, indent=2, ensure_ascii=False)

print(f"\n✓ Kaydedildi: data/balflex_fittings_ENHANCED.json")

# Sample göster
print("\n=== SAMPLE (JIS) ===")
jis_products = [p for p in balflex_data if p.get('standard') == 'JIS'][:2]
for p in jis_products:
    print(f"\nRef: {p['reference']}")
    print(f"Product Type: {p['product_type']}")
    print(f"Standard: {p['standard']}")
    print(f"Seat Type: {p['seat_type']}")
    print(f"Gender: {p['gender']}")
    print(f"Thread Size: {p['thread_size']}")
