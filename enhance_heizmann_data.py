"""
Enhance Heizmann Data
Extract DN and thread_size from identification field
"""

import json
import re
from collections import Counter


def extract_dn_from_identification(ident):
    """
    Extract DN from identification field
    Examples:
      "CES DN6" → 6
      "DN10 Ø12" → 10
      "DKM-K DN6" → 6
    """
    if not ident:
        return None

    match = re.search(r'DN\s*(\d+)', ident, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def extract_thread_size_from_identification(ident):
    """
    Extract thread size from identification field
    Examples:
      "M14X1.5" → "M14X1.5"
      "G1/4-19" → "G1/4-19"
      "1/2-20 UNF" → "1/2-20"
    """
    if not ident:
        return None

    # Metric threads: M14X1.5, M16X1,5
    metric_match = re.search(r'M\d+[Xx][\d.,]+', ident, re.IGNORECASE)
    if metric_match:
        return metric_match.group(0).replace(',', '.')

    # BSP/BSPP threads: G1/4, G1/2
    bsp_match = re.search(r'G\d+/\d+', ident, re.IGNORECASE)
    if bsp_match:
        return bsp_match.group(0)

    # UNF/UNC threads: 1/2-20, 3/4-16
    unf_match = re.search(r'\d+/\d+-\d+', ident)
    if unf_match:
        return unf_match.group(0)

    # NPT threads: 1/4 NPT, 1/2 NPT
    npt_match = re.search(r'(\d+/\d+)\s*NPT', ident, re.IGNORECASE)
    if npt_match:
        return f"{npt_match.group(1)} NPT"

    return None


def extract_thread_size_from_thread_size_field(thread_field):
    """
    Extract thread size from the dedicated thread_size field
    This field might have the actual thread size value
    """
    if not thread_field or thread_field == '' or thread_field == '-':
        return None

    # If it's already a valid thread size, return it
    if re.match(r'M\d+[Xx][\d.]+|G\d+/\d+|\d+/\d+', thread_field):
        return thread_field.replace(',', '.')

    return None


def enhance_heizmann_data():
    """Main enhancement function"""

    print("="*80)
    print("HEIZMANN DATA ENHANCEMENT")
    print("="*80)

    # Load data
    print("\n1. Loading data...")
    with open('data/pressarmaturen_serie_x_FULL_SELENIUM.json', 'r', encoding='utf-8') as f:
        heizmann_data = json.load(f)

    print(f"   Loaded: {len(heizmann_data)} products")

    # Statistics
    stats = {
        'total': len(heizmann_data),
        'dn_before': 0,
        'dn_after': 0,
        'dn_from_identification': 0,
        'thread_before': 0,
        'thread_after': 0,
        'thread_from_identification': 0,
        'thread_from_field': 0
    }

    # Count before
    stats['dn_before'] = sum(1 for p in heizmann_data if p.get('dn'))
    stats['thread_before'] = sum(1 for p in heizmann_data if p.get('thread_size'))

    print("\n2. Enhancing data...")

    for product in heizmann_data:
        # DN extraction
        if not product.get('dn'):
            dn = extract_dn_from_identification(product.get('identification'))
            if dn:
                product['dn'] = dn
                product['dn_source'] = 'identification'
                stats['dn_from_identification'] += 1
        else:
            product['dn_source'] = 'original'

        # Thread size extraction
        if not product.get('thread_size') or product.get('thread_size') == '':
            # Try identification first
            thread_from_ident = extract_thread_size_from_identification(product.get('identification'))
            if thread_from_ident:
                product['thread_size'] = thread_from_ident
                product['thread_size_source'] = 'identification'
                stats['thread_from_identification'] += 1
            else:
                # Try the thread_size field (maybe it has data we missed)
                thread_from_field = extract_thread_size_from_thread_size_field(product.get('thread_size'))
                if thread_from_field:
                    product['thread_size'] = thread_from_field
                    product['thread_size_source'] = 'field'
                    stats['thread_from_field'] += 1
        else:
            product['thread_size_source'] = 'original'

    # Count after
    stats['dn_after'] = sum(1 for p in heizmann_data if p.get('dn'))
    stats['thread_after'] = sum(1 for p in heizmann_data if p.get('thread_size') and p.get('thread_size') != '')

    # Print statistics
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)

    print(f"\n📊 DN İYİLEŞTİRMESİ:")
    print(f"   Önce:  {stats['dn_before']:4} / {stats['total']} ({stats['dn_before']/stats['total']*100:5.1f}%)")
    print(f"   Sonra: {stats['dn_after']:4} / {stats['total']} ({stats['dn_after']/stats['total']*100:5.1f}%)")
    print(f"   ---")
    print(f"   Identification'dan çıkarılan: {stats['dn_from_identification']:4}")
    print(f"   Toplam iyileştirme:           {stats['dn_after'] - stats['dn_before']:4} (+{(stats['dn_after'] - stats['dn_before'])/stats['total']*100:.1f}%)")

    print(f"\n📊 THREAD SIZE İYİLEŞTİRMESİ:")
    print(f"   Önce:  {stats['thread_before']:4} / {stats['total']} ({stats['thread_before']/stats['total']*100:5.1f}%)")
    print(f"   Sonra: {stats['thread_after']:4} / {stats['total']} ({stats['thread_after']/stats['total']*100:5.1f}%)")
    print(f"   ---")
    print(f"   Identification'dan çıkarılan: {stats['thread_from_identification']:4}")
    print(f"   Field'dan çıkarılan:          {stats['thread_from_field']:4}")
    print(f"   Toplam iyileştirme:           {stats['thread_after'] - stats['thread_before']:4} (+{(stats['thread_after'] - stats['thread_before'])/stats['total']*100:.1f}%)")

    # DN distribution
    dn_values = [p.get('dn') for p in heizmann_data if p.get('dn')]
    if dn_values:
        dn_counter = Counter(dn_values)
        print(f"\n📊 DN DAĞILIMI (Top 15):")
        for dn, count in dn_counter.most_common(15):
            print(f"   DN{dn:2}: {count:3} ürün")

    # Thread type distribution
    thread_values = [p.get('thread_size') for p in heizmann_data if p.get('thread_size')]
    if thread_values:
        thread_counter = Counter(thread_values)
        print(f"\n📊 THREAD SIZE DAĞILIMI (Top 15):")
        for thread, count in thread_counter.most_common(15):
            print(f"   {thread:15}: {count:3} ürün")

    # Save
    output_file = 'data/pressarmaturen_serie_x_ENHANCED.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(heizmann_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved to: {output_file}")

    # Show examples
    print(f"\n📋 ÖRNEK İYİLEŞTİRMELER:")

    improved_dn = [p for p in heizmann_data if p.get('dn_source') == 'identification']
    improved_thread = [p for p in heizmann_data if p.get('thread_size_source') == 'identification']

    print(f"\nDN Örnekleri:")
    for i, product in enumerate(improved_dn[:5], 1):
        print(f"{i}. {product['reference']}: '{product.get('identification')}' → DN{product.get('dn')}")

    print(f"\nThread Size Örnekleri:")
    for i, product in enumerate(improved_thread[:5], 1):
        print(f"{i}. {product['reference']}: '{product.get('identification')}' → {product.get('thread_size')}")

    return heizmann_data, stats


if __name__ == "__main__":
    data, stats = enhance_heizmann_data()

    print("\n" + "="*80)
    print("✅ İşlem tamamlandı!")
    print("="*80)
