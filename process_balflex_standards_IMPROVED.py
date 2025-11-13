"""
Improved Balflex Standards Processor
Extracts standards and seat types from both product_type AND category
More intelligent mapping based on actual data patterns
"""

import json
import re
from collections import Counter


def extract_standard_from_product_type(product_type):
    """Extract standard from product type text (existing logic)"""
    if not product_type:
        return None

    product_upper = product_type.upper()

    # Specific patterns with details
    if 'JIS' in product_upper:
        match = re.search(r'JIS\s*\d+(?:-\d+)?', product_type, re.IGNORECASE)
        if match and 'JIS 60' not in match.group(0):
            return match.group(0)
        return 'JIS'

    if 'BSP' in product_upper:
        return 'BSP'

    if 'NPT' in product_upper or 'NPTF' in product_upper:
        return 'NPT'

    if 'JIC' in product_upper:
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


def extract_standard_from_category(product):
    """
    Intelligently derive standard from category based on actual data patterns
    Only applies when standard is not already present
    """
    category = product.get('category', '')
    product_type = product.get('product_type', '')

    if not category:
        return None

    # Check if product_type gives hints
    product_upper = product_type.upper()

    # === METRIC CATEGORY ===
    if category == 'Metric':
        # Check if it's actually JIS (already handled by product_type)
        if 'JIS' in product_upper or '60°' in product_type:
            return 'JIS'

        # Otherwise, Metric fittings are typically ISO 8434-1 or DIN 2353
        # ISO 8434-1 uses 24° cone, DIN 2353 uses 24° as well
        if '24°' in product_type or 'Light Serie' in product_type:
            return 'ISO 8434-1'

        # Default for Metric category
        return 'ISO 8434-1'

    # === BSP CATEGORY ===
    elif category == 'BSP':
        # BSP (British Standard Pipe)
        # Unless it's explicitly JIS, assign BSP
        if 'JIS' in product_upper:
            return 'JIS'
        return 'BSP'

    # === JIC 37 CATEGORY ===
    elif category == 'JIC 37':
        # JIC (Joint Industry Council) - 37° flare
        return 'JIC'

    # === ORFS CATEGORY ===
    elif category == 'ORFS':
        # ORFS (O-Ring Face Seal)
        # Note: Some ORFS products might have NPT threads
        if 'NPT' in product_upper:
            return 'NPT'
        return 'ORFS'

    # === NPT CATEGORY ===
    elif category == 'NPT':
        # NPT (National Pipe Thread)
        return 'NPT'

    # === FLANGE CATEGORY ===
    elif category == 'Flange':
        # Flanges are typically SAE standards (SAE J518)
        # But some might be ORFS with flange connection
        if 'ORFS' in product_upper or 'O-RING' in product_upper:
            return 'ORFS'
        return 'SAE J518'

    # === FERRULE CATEGORY ===
    elif category == 'Ferrule':
        # Ferrules/Sleeves - typically SAE J1453 or ISO standards
        # Being conservative - not assigning default standard
        # These need more context
        return None

    # === TEE CATEGORY ===
    elif category == 'Tee':
        # Tees can be various standards - check product type
        if 'JIS' in product_upper:
            return 'JIS'
        if 'SAE' in product_upper:
            return 'SAE'
        if 'BSP' in product_upper:
            return 'BSP'
        # Don't assign default
        return None

    # === ELBOW CATEGORY ===
    elif category == 'Elbow':
        # Elbows can be various standards - check product type
        if 'JIS' in product_upper:
            return 'JIS'
        if 'SAE' in product_upper:
            return 'SAE'
        if 'BSP' in product_upper:
            return 'BSP'
        if 'METRIC' in product_upper or '24°' in product_type:
            return 'ISO 8434-1'
        # Don't assign default
        return None

    return None


def extract_seat_type(product_type):
    """Extract seat type from product type"""
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


def enhance_seat_type_from_category(product):
    """
    Add seat type based on category and standard when missing
    """
    if product.get('seat_type'):
        return product.get('seat_type')

    category = product.get('category', '')
    standard = product.get('standard', '')

    # JIC 37 always uses 37° cone
    if category == 'JIC 37' or standard == 'JIC':
        return '37° Cone'

    # ORFS uses O-Ring Face Seal
    if category == 'ORFS' or standard == 'ORFS':
        return 'O-Ring'

    # ISO 8434-1 (Metric) typically uses 24° cone
    if standard == 'ISO 8434-1':
        return '24° Cone'

    # JIS typically uses 60° cone
    if standard == 'JIS':
        return '60° Cone'

    # Ferrules typically flat face
    if category == 'Ferrule':
        return 'Flat Face'

    return None


def process_balflex_standards():
    """Main processing function"""

    print("="*80)
    print("IMPROVED BALFLEX STANDARDS PROCESSOR")
    print("="*80)

    # Load data
    print("\n1. Loading data...")
    with open('data/balflex_fittings_ENHANCED.json', 'r', encoding='utf-8') as f:
        balflex_data = json.load(f)

    print(f"   Loaded: {len(balflex_data)} products")

    # Statistics tracking
    stats = {
        'total': len(balflex_data),
        'standard_before': 0,
        'standard_after': 0,
        'standard_from_product_type': 0,
        'standard_from_category': 0,
        'seat_type_before': 0,
        'seat_type_after': 0,
        'seat_type_from_product_type': 0,
        'seat_type_from_category': 0
    }

    # Count before
    stats['standard_before'] = sum(1 for p in balflex_data if p.get('standard'))
    stats['seat_type_before'] = sum(1 for p in balflex_data if p.get('seat_type'))

    print("\n2. Processing standards and seat types...")

    for product in balflex_data:
        original_standard = product.get('standard')
        original_seat = product.get('seat_type')

        # Process standard
        if not original_standard:
            # Try product_type first
            std_from_type = extract_standard_from_product_type(product.get('product_type', ''))
            if std_from_type:
                product['standard'] = std_from_type
                product['standard_source'] = 'product_type'
                stats['standard_from_product_type'] += 1
            else:
                # Try category
                std_from_cat = extract_standard_from_category(product)
                if std_from_cat:
                    product['standard'] = std_from_cat
                    product['standard_source'] = 'category'
                    stats['standard_from_category'] += 1
        else:
            product['standard_source'] = 'original'

        # Process seat type
        if not original_seat:
            # Try product_type first
            seat_from_type = extract_seat_type(product.get('product_type', ''))
            if seat_from_type:
                product['seat_type'] = seat_from_type
                product['seat_type_source'] = 'product_type'
                stats['seat_type_from_product_type'] += 1
            else:
                # Try category/standard
                seat_from_cat = enhance_seat_type_from_category(product)
                if seat_from_cat:
                    product['seat_type'] = seat_from_cat
                    product['seat_type_source'] = 'category'
                    stats['seat_type_from_category'] += 1
        else:
            product['seat_type_source'] = 'original'

    # Count after
    stats['standard_after'] = sum(1 for p in balflex_data if p.get('standard'))
    stats['seat_type_after'] = sum(1 for p in balflex_data if p.get('seat_type'))

    # Print statistics
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)

    print(f"\n📊 STANDARD İYİLEŞTİRMESİ:")
    print(f"   Önce:  {stats['standard_before']:4} / {stats['total']} ({stats['standard_before']/stats['total']*100:5.1f}%)")
    print(f"   Sonra: {stats['standard_after']:4} / {stats['total']} ({stats['standard_after']/stats['total']*100:5.1f}%)")
    print(f"   ---")
    print(f"   Product type'dan eklenen:  {stats['standard_from_product_type']:4}")
    print(f"   Kategori'den eklenen:      {stats['standard_from_category']:4}")
    print(f"   Toplam iyileştirme:        {stats['standard_after'] - stats['standard_before']:4} (+{(stats['standard_after'] - stats['standard_before'])/stats['total']*100:.1f}%)")

    print(f"\n📊 SEAT TYPE İYİLEŞTİRMESİ:")
    print(f"   Önce:  {stats['seat_type_before']:4} / {stats['total']} ({stats['seat_type_before']/stats['total']*100:5.1f}%)")
    print(f"   Sonra: {stats['seat_type_after']:4} / {stats['total']} ({stats['seat_type_after']/stats['total']*100:5.1f}%)")
    print(f"   ---")
    print(f"   Product type'dan eklenen:  {stats['seat_type_from_product_type']:4}")
    print(f"   Kategori'den eklenen:      {stats['seat_type_from_category']:4}")
    print(f"   Toplam iyileştirme:        {stats['seat_type_after'] - stats['seat_type_before']:4} (+{(stats['seat_type_after'] - stats['seat_type_before'])/stats['total']*100:.1f}%)")

    # Standard distribution
    standards = [p.get('standard') for p in balflex_data if p.get('standard')]
    std_counter = Counter(standards)

    print(f"\n📊 STANDARD DAĞILIMI (Sonra):")
    for std, count in sorted(std_counter.items(), key=lambda x: -x[1]):
        print(f"   {std:20}: {count:4} ({count/len(standards)*100:5.1f}%)")

    # Seat type distribution
    seats = [p.get('seat_type') for p in balflex_data if p.get('seat_type')]
    seat_counter = Counter(seats)

    print(f"\n📊 SEAT TYPE DAĞILIMI (Sonra):")
    for seat, count in sorted(seat_counter.items(), key=lambda x: -x[1]):
        print(f"   {seat:20}: {count:4} ({count/len(seats)*100:5.1f}%)")

    # Save
    output_file = 'data/balflex_fittings_IMPROVED.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(balflex_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved to: {output_file}")

    # Show examples
    print(f"\n📋 ÖRNEK İYİLEŞTİRMELER:")

    improved_products = [p for p in balflex_data if p.get('standard_source') in ['product_type', 'category']]

    for i, product in enumerate(improved_products[:5], 1):
        print(f"\n{i}. Reference: {product['reference']}")
        print(f"   Category: {product.get('category', 'N/A')}")
        print(f"   Product Type: {product.get('product_type', 'N/A')[:60]}...")
        print(f"   ✅ Standard: {product.get('standard', 'N/A')} (kaynak: {product.get('standard_source', 'N/A')})")
        if product.get('seat_type'):
            print(f"   ✅ Seat Type: {product.get('seat_type', 'N/A')} (kaynak: {product.get('seat_type_source', 'N/A')})")

    return balflex_data, stats


if __name__ == "__main__":
    data, stats = process_balflex_standards()

    print("\n" + "="*80)
    print("✅ İşlem tamamlandı!")
    print("="*80)
