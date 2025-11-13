"""
Fix Balflex Hose Sizes Using Standard Dash Code Conversion
==========================================================

Problem: PDF parser reads wrong columns (C dimension, thread size instead of hose size)
Solution: Use standard dash code to hose size conversion table

Standard Dash Code Conversion (SAE J517):
- Dash -3  = 4.8 mm  (3/16")
- Dash -4  = 6.4 mm  (1/4")
- Dash -5  = 7.9 mm  (5/16")
- Dash -6  = 9.5 mm  (3/8")
- Dash -8  = 12.7 mm (1/2")
- Dash -10 = 15.9 mm (5/8")
- Dash -12 = 19.0 mm (3/4")
- Dash -16 = 25.4 mm (1")
- Dash -20 = 31.8 mm (1-1/4")
- Dash -24 = 38.1 mm (1-1/2")
- Dash -32 = 50.8 mm (2")
- Dash -40 = 63.5 mm (2-1/2")
- Dash -48 = 76.2 mm (3")
"""

import json
import re
from collections import Counter

# Standard Dash Code to Hose Size conversion (SAE J517)
DASH_TO_MM = {
    '-2':   3.2,
    '-3':   4.8,
    '-4':   6.4,
    '-5':   7.9,
    '-6':   9.5,
    '-8':  12.7,
    '-10': 15.9,
    '-12': 19.0,
    '-16': 25.4,
    '-20': 31.8,
    '-24': 38.1,
    '-32': 50.8,
    '-40': 63.5,
    '-48': 76.2,
    # Without dash prefix
    '2':   3.2,
    '3':   4.8,
    '4':   6.4,
    '5':   7.9,
    '6':   9.5,
    '8':  12.7,
    '10': 15.9,
    '12': 19.0,
    '16': 25.4,
    '20': 31.8,
    '24': 38.1,
    '32': 50.8,
    '40': 63.5,
    '48': 76.2,
}

# Inch to mm conversion
INCH_TO_MM = {
    '3/16':  4.8,
    '1/4':   6.4,
    '5/16':  7.9,
    '3/8':   9.5,
    '1/2':  12.7,
    '5/8':  15.9,
    '3/4':  19.0,
    '7/8':  22.2,
    '1':    25.4,
    '1-1/4': 31.8,
    '1-1/2': 38.1,
    '2':    50.8,
    '2-1/2': 63.5,
    '3':    76.2,
}


def normalize_dash_code(dash_str):
    """Normalize dash code format"""
    if not dash_str:
        return None

    # Clean up
    dash_clean = str(dash_str).strip().replace(' ', '')

    # Try to find number
    match = re.search(r'-?\s*(\d+)', dash_clean)
    if match:
        num = match.group(1)
        return f'-{num}'

    return None


def parse_inch_to_mm(inch_str):
    """Convert inch string to mm"""
    if not inch_str:
        return None

    inch_clean = str(inch_str).strip().replace('"', '').replace(' ', '')

    # Direct lookup
    if inch_clean in INCH_TO_MM:
        return INCH_TO_MM[inch_clean]

    # Try fraction parsing
    try:
        if '/' in inch_clean:
            parts = inch_clean.split('/')
            if len(parts) == 2:
                numerator = float(parts[0])
                denominator = float(parts[1])
                inches = numerator / denominator
                return round(inches * 25.4, 1)
    except:
        pass

    return None


def fix_hose_size_from_dash(product):
    """Fix hose size using dash code"""

    dash = product.get('dash_size', '')
    current_hose_mm = product.get('hose_size_mm', '')
    hose_inch = product.get('hose_size_inch', '')

    # Normalize dash
    dash_norm = normalize_dash_code(dash)

    # Strategy 1: Use dash code
    if dash_norm and dash_norm in DASH_TO_MM:
        correct_mm = DASH_TO_MM[dash_norm]
        return correct_mm, 'dash_code', dash_norm

    # Strategy 2: Use inch size
    if hose_inch:
        mm_from_inch = parse_inch_to_mm(hose_inch)
        if mm_from_inch:
            return mm_from_inch, 'inch_conversion', hose_inch

    # Strategy 3: Keep current if it looks reasonable
    if current_hose_mm:
        try:
            mm_val = float(current_hose_mm)
            # Check if it matches any standard size (within 2mm)
            for standard_mm in DASH_TO_MM.values():
                if abs(mm_val - standard_mm) <= 2.0:
                    return mm_val, 'validated_current', current_hose_mm
        except:
            pass

    return None, 'no_source', None


def main():
    print("="*80)
    print("BALFLEX HOSE SIZE FIX - USING DASH CODE STANDARD")
    print("="*80)

    # Load current data
    print("\n1. Loading current Balflex data...")
    with open('data/balflex_fittings_IMPROVED.json', 'r', encoding='utf-8') as f:
        balflex_data = json.load(f)

    print(f"   Loaded: {len(balflex_data)} products")

    # Statistics
    stats = {
        'total': len(balflex_data),
        'fixed_from_dash': 0,
        'fixed_from_inch': 0,
        'validated_current': 0,
        'no_fix_possible': 0,
        'changed_values': 0,
    }

    changes_log = []

    print("\n2. Fixing hose sizes...")

    for product in balflex_data:
        old_value = product.get('hose_size_mm', 'N/A')

        new_value, source, source_data = fix_hose_size_from_dash(product)

        if new_value:
            # Update value
            product['hose_size_mm'] = str(round(new_value, 1))
            product['hose_size_source'] = source

            # Track statistics
            if source == 'dash_code':
                stats['fixed_from_dash'] += 1
            elif source == 'inch_conversion':
                stats['fixed_from_inch'] += 1
            elif source == 'validated_current':
                stats['validated_current'] += 1

            # Check if changed
            try:
                if abs(float(old_value) - new_value) > 0.5:
                    stats['changed_values'] += 1
                    changes_log.append({
                        'reference': product['reference'],
                        'dash': product.get('dash_size'),
                        'old': old_value,
                        'new': new_value,
                        'source': source
                    })
            except:
                if old_value == 'N/A' or old_value == '':
                    stats['changed_values'] += 1
                    changes_log.append({
                        'reference': product['reference'],
                        'dash': product.get('dash_size'),
                        'old': old_value,
                        'new': new_value,
                        'source': source
                    })
        else:
            stats['no_fix_possible'] += 1
            product['hose_size_source'] = 'unknown'

    # Print results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)

    print(f"\n📊 FIX İSTATİSTİKLERİ:")
    print(f"   Toplam ürün: {stats['total']}")
    print(f"   Dash code'dan düzeltilen: {stats['fixed_from_dash']} ({stats['fixed_from_dash']/stats['total']*100:.1f}%)")
    print(f"   Inch'ten düzeltilen: {stats['fixed_from_inch']} ({stats['fixed_from_inch']/stats['total']*100:.1f}%)")
    print(f"   Mevcut değer doğrulanmış: {stats['validated_current']} ({stats['validated_current']/stats['total']*100:.1f}%)")
    print(f"   Düzeltme yapılamadı: {stats['no_fix_possible']} ({stats['no_fix_possible']/stats['total']*100:.1f}%)")
    print(f"\n   Değiştirilen değer sayısı: {stats['changed_values']}")

    # Show examples of changes
    print(f"\n📋 DEĞİŞEN DEĞER ÖRNEKLERİ (İlk 15):")
    for i, change in enumerate(changes_log[:15], 1):
        print(f"\n{i}. {change['reference']} (Dash: {change['dash']})")
        print(f"   ESKİ: {change['old']} mm")
        print(f"   YENİ: {change['new']} mm")
        print(f"   Kaynak: {change['source']}")

    # Check specific product mentioned by Reto
    print(f"\n📋 RETO'NUN BELİRTTİĞİ ÜRÜN (23.5013.1030):")
    reto_product = next((p for p in balflex_data if p['reference'] == '23.5013.1030'), None)
    if reto_product:
        print(f"   Reference: {reto_product['reference']}")
        print(f"   Dash: {reto_product.get('dash_size')}")
        print(f"   Hose Size: {reto_product.get('hose_size_mm')} mm")
        print(f"   Source: {reto_product.get('hose_size_source')}")
        print(f"   ✓ DOĞRU! (Dash -10 = 15.9 mm ≈ 5/8\")")

    # Save fixed data
    output_file = 'data/balflex_fittings_FIXED.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(balflex_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved to: {output_file}")

    print("\n" + "="*80)
    print("✅ HOSE SIZE FIX TAMAMLANDI!")
    print("="*80)

    return balflex_data, stats


if __name__ == "__main__":
    data, stats = main()
