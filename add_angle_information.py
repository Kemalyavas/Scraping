"""
Add Angle Information to Products
==================================

Extract angle information (90°, 45°, straight) from product descriptions
for both Heizmann and Balflex products.
"""

import json
import re
from collections import Counter


def extract_angle_heizmann(product):
    """
    Extract angle from Heizmann product

    Patterns:
    - Model: "Pressnippel MSOF 90S" → 90°
    - Model: "Pressnippel MLOF 45S" → 45°
    - Model: "Pressnippel MLOF gerade" → Straight
    - Identification: "DKOS 90° DN32" → 90°
    """
    model = product.get('model', '')
    identification = product.get('identification', '')

    combined = f"{model} {identification}".upper()

    # Check for 90 degree
    if '90S' in model or '90°' in combined or '90 ' in combined:
        return '90°'

    # Check for 45 degree
    if '45S' in model or '45°' in combined or '45 ' in combined:
        return '45°'

    # Check for straight
    if 'GERADE' in combined or 'STRAIGHT' in combined:
        return 'Straight'

    # If contains "MLOF" or "MSOF" without angle, likely straight
    if ('MLOF' in model or 'MSOF' in model) and '90' not in model and '45' not in model:
        # Check if it explicitly says gerade
        if 'gerade' in model.lower():
            return 'Straight'

    return None


def extract_angle_balflex(product):
    """
    Extract angle from Balflex product

    Patterns:
    - Product Type: "90° Swept Female" → 90°
    - Product Type: "45° Swept Female" → 45°
    - Product Type: "Female Metric Light Serie 24°" → Straight (24° is seat, not fitting angle)
    - Category: "Elbow" → usually 90°
    """
    product_type = product.get('product_type', '')
    category = product.get('category', '')

    # Check for explicit angle mentions
    # 90° swept/elbow
    if ('90' in product_type and ('swept' in product_type.lower() or 'elbow' in product_type.lower())):
        return '90°'

    # 45° swept
    if ('45' in product_type and ('swept' in product_type.lower() or '°' in product_type)):
        return '45°'

    # Straight indicators
    if 'straight' in product_type.lower() or 'gerade' in product_type.lower():
        return 'Straight'

    # Category-based hints
    if category == 'Elbow':
        # Elbows are typically 90° unless specified
        if '45' in product_type:
            return '45°'
        return '90°'

    # If product mentions only seat angle (24°, 37°, 60°) but no fitting angle, it's straight
    # Pattern: "Female Metric Light Serie 24°" - this is seat angle, fitting is straight
    if re.search(r'\b(24|37|60)°\b', product_type) and 'swept' not in product_type.lower() and 'elbow' not in product_type.lower():
        # Check if there's no other angle mention
        if not re.search(r'\b(45|90)°?\b', product_type):
            return 'Straight'

    return None


def main():
    print("="*80)
    print("ADD ANGLE INFORMATION")
    print("="*80)

    # Load Heizmann data
    print("\n1. Processing Heizmann data...")
    with open('data/pressarmaturen_serie_x_ENHANCED.json', 'r', encoding='utf-8') as f:
        heizmann_data = json.load(f)

    heizmann_angles = Counter()
    for product in heizmann_data:
        angle = extract_angle_heizmann(product)
        product['angle'] = angle
        if angle:
            heizmann_angles[angle] += 1

    print(f"   Loaded: {len(heizmann_data)} products")
    print(f"\n   Açı dağılımı:")
    for angle, count in heizmann_angles.most_common():
        print(f"      {angle:15}: {count:4} ({count/len(heizmann_data)*100:5.1f}%)")

    no_angle_heiz = len(heizmann_data) - sum(heizmann_angles.values())
    print(f"      {'No angle':15}: {no_angle_heiz:4} ({no_angle_heiz/len(heizmann_data)*100:5.1f}%)")

    # Load Balflex data
    print("\n2. Processing Balflex data...")
    with open('data/balflex_fittings_FIXED.json', 'r', encoding='utf-8') as f:
        balflex_data = json.load(f)

    balflex_angles = Counter()
    for product in balflex_data:
        angle = extract_angle_balflex(product)
        product['angle'] = angle
        if angle:
            balflex_angles[angle] += 1

    print(f"   Loaded: {len(balflex_data)} products")
    print(f"\n   Açı dağılımı:")
    for angle, count in balflex_angles.most_common():
        print(f"      {angle:15}: {count:4} ({count/len(balflex_data)*100:5.1f}%)")

    no_angle_balf = len(balflex_data) - sum(balflex_angles.values())
    print(f"      {'No angle':15}: {no_angle_balf:4} ({no_angle_balf/len(balflex_data)*100:5.1f}%)")

    # Examples
    print(f"\n📋 HEIZMANN ÖRNEKLERİ:")
    for angle in ['90°', '45°', 'Straight']:
        examples = [p for p in heizmann_data if p.get('angle') == angle][:2]
        if examples:
            print(f"\n   {angle}:")
            for ex in examples:
                print(f"      {ex['article_number']}: {ex['model']}")

    print(f"\n📋 BALFLEX ÖRNEKLERİ:")
    for angle in ['90°', '45°', 'Straight']:
        examples = [p for p in balflex_data if p.get('angle') == angle][:2]
        if examples:
            print(f"\n   {angle}:")
            for ex in examples:
                print(f"      {ex['reference']}: {ex.get('product_type', 'N/A')[:50]}")

    # Save
    print(f"\n3. Saving enhanced data...")

    with open('data/pressarmaturen_serie_x_WITH_ANGLE.json', 'w', encoding='utf-8') as f:
        json.dump(heizmann_data, f, indent=2, ensure_ascii=False)
    print(f"   ✓ Heizmann saved")

    with open('data/balflex_fittings_WITH_ANGLE.json', 'w', encoding='utf-8') as f:
        json.dump(balflex_data, f, indent=2, ensure_ascii=False)
    print(f"   ✓ Balflex saved")

    print("\n" + "="*80)
    print("✅ ANGLE INFORMATION ADDED!")
    print("="*80)

    return heizmann_data, balflex_data


if __name__ == "__main__":
    heizmann, balflex = main()
