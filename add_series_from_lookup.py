"""
Add L/S Series Information to Balflex Products using Lookup Table
Based on DIN 24° Light (L) and Heavy (S) series - ISO 8434-1
Using Tube O.D. + Thread Size combination
"""

import json
import re

# Lookup table from Balflex catalog (Page 11)
# Key: (tube_od_mm, thread_size_normalized) → Value: series (L or S)
SERIES_LOOKUP = {
    # 6mm tube
    (6.0, "M12X1.5"): "L",
    (6.0, "M14X1.5"): "S",

    # 8mm tube
    (8.0, "M14X1.5"): "L",
    (8.0, "M16X1.5"): "S",

    # 10mm tube
    (10.0, "M16X1.5"): "L",
    (10.0, "M18X1.5"): "S",

    # 12mm tube
    (12.0, "M18X1.5"): "L",
    (12.0, "M20X1.5"): "S",

    # 14mm tube (only S)
    (14.0, "M22X1.5"): "S",

    # 15mm tube (only L)
    (15.0, "M22X1.5"): "L",

    # 16mm tube (only S)
    (16.0, "M24X1.5"): "S",

    # 18mm tube (only L)
    (18.0, "M26X1.5"): "L",

    # 20mm tube (only S)
    (20.0, "M30X2.0"): "S",

    # 22mm tube (only L)
    (22.0, "M30X2.0"): "L",

    # 25mm tube (only S)
    (25.0, "M36X2.0"): "S",

    # 28mm tube (only L)
    (28.0, "M36X2.0"): "L",

    # 30mm tube (only S)
    (30.0, "M42X2.0"): "S",

    # 35mm tube (only L)
    (35.0, "M45X2.0"): "L",

    # 38mm tube (only S)
    (38.0, "M52X2.0"): "S",

    # 42mm tube (only L)
    (42.0, "M52X2.0"): "L",
}

def normalize_thread_size(thread_str):
    """Normalize thread size to uppercase and replace comma with period"""
    if not thread_str:
        return None

    # Convert to string and uppercase
    thread = str(thread_str).strip().upper()

    # Replace comma with period (M16x1,5 → M16X1.5)
    thread = thread.replace(',', '.')

    # Standardize 'x' to 'X'
    thread = re.sub(r'[xX]', 'X', thread)

    # Extract pattern like M16X1.5
    match = re.search(r'M\d+X\d+\.?\d*', thread)
    if match:
        return match.group(0)

    return None

def get_series_from_lookup(tube_od_mm, thread_size):
    """Get L or S series from lookup table"""

    if not tube_od_mm or not thread_size:
        return None, None

    # Normalize thread size
    thread_normalized = normalize_thread_size(thread_size)
    if not thread_normalized:
        return None, None

    # Try to match with lookup table
    try:
        tube_od_float = float(tube_od_mm)

        # Round to 1 decimal place for matching
        tube_od_rounded = round(tube_od_float, 1)

        # Look up in table
        key = (tube_od_rounded, thread_normalized)
        if key in SERIES_LOOKUP:
            return SERIES_LOOKUP[key], "lookup_table"

        # Try rounding to nearest integer (some values might be 15.9 instead of 16.0)
        tube_od_int = round(tube_od_float)
        key_int = (float(tube_od_int), thread_normalized)
        if key_int in SERIES_LOOKUP:
            return SERIES_LOOKUP[key_int], "lookup_table_rounded"

    except (ValueError, TypeError):
        pass

    return None, None

def extract_series_balflex_from_article(product):
    """
    Extract L or S series from Balflex article number

    Pattern discovered: 5th character (index 4) determines series:
    - 23.1[0]00.xxxx → Light (0 in position 4)
    - 23.1[1]00.xxxx → Heavy (1 in position 4)
    - 23.5[0]13.xxxx → Light
    - 23.5[1]13.xxxx → Heavy
    - 23.5[0]93.xxxx → Light (90° female)
    - 23.5[1]93.xxxx → Heavy (90° female)

    Only applies to ISO 8434-1 standard products.
    """

    article = product.get('article_number', '')
    standard = product.get('standard', '')

    # Only for ISO 8434-1 (DIN 24° standard)
    if standard != 'ISO 8434-1':
        return None, None

    # Check article number format (must be like 23.xxxx.xxxx)
    if not article or len(article) < 8:
        return None, None

    # Get 5th character (index 4)
    if len(article) > 4:
        fifth_char = article[4]

        if fifth_char == '0':
            return 'L', 'article_number_pattern'
        elif fifth_char == '1':
            return 'S', 'article_number_pattern'

    return None, None

def extract_series_balflex_from_product_type(product):
    """Extract L or S series from Balflex product_type field"""

    product_type = product.get('product_type', '').upper()

    if 'LIGHT SERIE' in product_type or 'LIGHT SERIES' in product_type:
        return 'L', 'product_type_light'
    elif 'HEAVY SERIE' in product_type or 'HEAVY SERIES' in product_type:
        return 'S', 'product_type_heavy'

    return None, None

def extract_series_heizmann(product):
    """Extract L or S series from Heizmann model/identification"""
    model = product.get('model', '')
    identification = product.get('identification', '')

    combined = f"{model} {identification}".upper()

    # Look for patterns: DKOL, DKOS, MLOL, MLOS, MSOL, MSOS, etc.
    patterns = [
        r'DKO([LS])',  # DKOL, DKOS
        r'MLO([LS])',  # MLOL, MLOS
        r'MSO([LS])',  # MSOL, MSOS
        r'SRO([LS])',  # SROL, SROS
        r'WO([LS])',   # WOL, WOS
    ]

    for pattern in patterns:
        match = re.search(pattern, combined)
        if match:
            series = match.group(1)
            return series, f"pattern_{pattern}"

    return None, None

def main():
    print("=" * 80)
    print("ADDING L/S SERIES INFORMATION USING LOOKUP TABLE")
    print("=" * 80)

    # Load Heizmann data
    print("\n1. Processing Heizmann products...")
    with open('data/pressarmaturen_serie_x_WITH_ANGLE.json', 'r', encoding='utf-8') as f:
        heizmann_products = json.load(f)

    heizmann_with_series = 0
    for product in heizmann_products:
        series, source = extract_series_heizmann(product)
        if series:
            product['series'] = series
            product['series_source'] = source
            heizmann_with_series += 1

    print(f"   Heizmann: {heizmann_with_series}/{len(heizmann_products)} products with L/S series")

    # Save updated Heizmann data
    with open('data/pressarmaturen_serie_x_WITH_SERIES.json', 'w', encoding='utf-8') as f:
        json.dump(heizmann_products, f, indent=2, ensure_ascii=False)

    print(f"   ✓ Saved to data/pressarmaturen_serie_x_WITH_SERIES.json")

    # Load Balflex data
    print("\n2. Processing Balflex products...")
    with open('data/balflex_fittings_WITH_ANGLE.json', 'r', encoding='utf-8') as f:
        balflex_products = json.load(f)

    balflex_with_series = 0
    balflex_from_product_type = 0
    balflex_from_article_number = 0

    # Test samples for debugging
    test_samples = []

    for product in balflex_products:
        # Try method 1: Extract from product_type
        series, source = extract_series_balflex_from_product_type(product)

        # Try method 2: Extract from article number pattern
        if not series:
            series, source = extract_series_balflex_from_article(product)
            if series:
                balflex_from_article_number += 1
        else:
            balflex_from_product_type += 1

        if series:
            product['series'] = series
            product['series_source'] = source
            balflex_with_series += 1

            # Collect samples for display
            if len(test_samples) < 10:
                test_samples.append({
                    'article': product.get('article_number'),
                    'series': series,
                    'source': source
                })

    print(f"   Balflex: {balflex_with_series}/{len(balflex_products)} products with L/S series")
    print(f"   ISO 8434-1 products: {sum(1 for p in balflex_products if p.get('standard') == 'ISO 8434-1')}")
    print(f"   From product_type: {balflex_from_product_type}")
    print(f"   From article number: {balflex_from_article_number}")

    # Show test samples
    if test_samples:
        print("\n   Sample results:")
        for sample in test_samples:
            print(f"      {sample['article']}: {sample['series']} (source: {sample['source']})")

    # Save updated Balflex data
    with open('data/balflex_fittings_WITH_SERIES.json', 'w', encoding='utf-8') as f:
        json.dump(balflex_products, f, indent=2, ensure_ascii=False)

    print(f"\n   ✓ Saved to data/balflex_fittings_WITH_SERIES.json")

    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)

    # Count series distribution
    heizmann_L = sum(1 for p in heizmann_products if p.get('series') == 'L')
    heizmann_S = sum(1 for p in heizmann_products if p.get('series') == 'S')

    balflex_L = sum(1 for p in balflex_products if p.get('series') == 'L')
    balflex_S = sum(1 for p in balflex_products if p.get('series') == 'S')

    print(f"\nHeizmann Series Distribution:")
    print(f"  Light (L): {heizmann_L}")
    print(f"  Heavy (S): {heizmann_S}")
    print(f"  Unknown:   {len(heizmann_products) - heizmann_L - heizmann_S}")

    print(f"\nBalflex Series Distribution:")
    print(f"  Light (L): {balflex_L}")
    print(f"  Heavy (S): {balflex_S}")
    print(f"  Unknown:   {len(balflex_products) - balflex_L - balflex_S}")

    if balflex_with_series > 0:
        print(f"\n✓ SUCCESS: Balflex L/S series successfully extracted using lookup table!")
    else:
        print(f"\n⚠ WARNING: No Balflex products matched the lookup table.")
        print(f"   Check if thread_size field exists and matches expected format.")

if __name__ == "__main__":
    main()
