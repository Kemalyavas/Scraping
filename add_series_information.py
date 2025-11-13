"""
Add L/S Series Information to Balflex and Heizmann Products
Based on DIN 24° Light (L) and Heavy (S) series classification
"""

import json
import re

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

def extract_series_balflex(product):
    """
    Extract L or S series from Balflex product

    For Balflex, we need to infer from DN size:
    - For ISO 8434-1 standard, smaller DN typically = Light, larger DN = Heavy
    - But this is not reliable without the actual "Tube type" column

    NOTE: This is a heuristic and may not be 100% accurate.
    We need to re-parse the PDF to get the actual "Tube type" column.
    """

    # For now, return None - we need to re-parse the PDF
    return None, None

def main():
    print("=" * 80)
    print("ADDING L/S SERIES INFORMATION")
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
    for product in balflex_products:
        series, source = extract_series_balflex(product)
        if series:
            product['series'] = series
            product['series_source'] = source
            balflex_with_series += 1

    print(f"   Balflex: {balflex_with_series}/{len(balflex_products)} products with L/S series")
    print(f"   ⚠ WARNING: Balflex series detection needs PDF re-parsing for 'Tube type' column")

    # Save updated Balflex data
    with open('data/balflex_fittings_WITH_SERIES.json', 'w', encoding='utf-8') as f:
        json.dump(balflex_products, f, indent=2, ensure_ascii=False)

    print(f"   ✓ Saved to data/balflex_fittings_WITH_SERIES.json")

    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)

    # Count series distribution
    heizmann_L = sum(1 for p in heizmann_products if p.get('series') == 'L')
    heizmann_S = sum(1 for p in heizmann_products if p.get('series') == 'S')

    print(f"\nHeizmann Series Distribution:")
    print(f"  Light (L): {heizmann_L}")
    print(f"  Heavy (S): {heizmann_S}")
    print(f"  Unknown:   {len(heizmann_products) - heizmann_L - heizmann_S}")

    print(f"\n⚠ CRITICAL ISSUE:")
    print(f"  Balflex does NOT have L/S series information in current JSON data.")
    print(f"  We need to re-parse the Balflex PDF to extract 'Tube type' column (6L, 6S, 8L, 8S).")
    print(f"  Without this, we CANNOT properly match L vs S series products.")

if __name__ == "__main__":
    main()
