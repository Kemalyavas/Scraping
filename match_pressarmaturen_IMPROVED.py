"""
Improved Product Matching Algorithm
Uses enhanced Balflex and Heizmann data for better matching quality
"""

import json
import re
import pandas as pd
from collections import Counter


def normalize_standard(std):
    """
    Normalize standard names for matching
    ISO 8434-1 → ISO
    JIS 8363 → JIS
    SAE J518 → SAE
    """
    if not std:
        return None

    std_upper = std.upper()

    # Extract base standard
    for base in ['ISO', 'JIS', 'BSP', 'NPT', 'JIC', 'ORFS', 'SAE', 'DIN']:
        if base in std_upper:
            return base

    return None


def normalize_seat_type(seat):
    """
    Normalize seat type for matching
    60° Innenkonus → 60° Cone
    37° Cone Seat → 37° Cone
    """
    if not seat:
        return None

    # Extract degree
    match = re.search(r'(\d+)°', seat)
    if match:
        return f"{match.group(1)}° Cone"

    if 'flat' in seat.lower():
        return "Flat Face"

    if 'o-ring' in seat.lower() or 'oring' in seat.lower():
        return "O-Ring"

    return None


def determine_gender_heizmann(heizmann_item):
    """
    Determine gender from Heizmann product
    Innengewinde → Female
    Aussengewinde → Male
    """
    connection = heizmann_item.get('connection_type', '')
    ident = heizmann_item.get('identification', '')
    model = heizmann_item.get('model', '')

    # Connection type based
    if connection:
        if 'innengewinde' in connection.lower() or 'innenkegel' in connection.lower():
            return 'Female'
        if 'aussengewinde' in connection.lower() or 'aussenkegel' in connection.lower():
            return 'Male'

    # Model/identification based
    combined = f"{model} {ident}".lower()

    female_keywords = ['muffe', 'mutter', 'female', 'socket', 'coupler']
    male_keywords = ['nippel', 'stecker', 'male', 'plug', 'stem']

    for keyword in female_keywords:
        if keyword in combined:
            return 'Female'

    for keyword in male_keywords:
        if keyword in combined:
            return 'Male'

    return 'Unknown'


def calculate_match_score(heizmann_item, balflex_item):
    """
    Improved scoring system with better validation

    Scoring (total 100):
    - Standard match: 40 points (MANDATORY)
    - DN match: 30 points (exact) or 15 points (close ±2)
    - Seat type match: 20 points
    - Gender match: 10 points (penalty -10 for mismatch)

    Minimum score: 40 (only standard match)
    """
    score = 0
    reasons = []
    warnings = []

    # Parse Heizmann data (now using pre-extracted dn field)
    heizmann_dn = heizmann_item.get('dn')  # Already extracted
    heizmann_std = normalize_standard(heizmann_item.get('standard'))
    heizmann_seat = normalize_seat_type(heizmann_item.get('seat_type'))
    heizmann_gender = determine_gender_heizmann(heizmann_item)

    # Parse Balflex data
    balflex_dn = None
    if balflex_item.get('hose_size_mm'):
        try:
            balflex_dn = int(float(balflex_item['hose_size_mm']))
        except:
            pass

    balflex_std = normalize_standard(balflex_item.get('standard'))
    balflex_seat = normalize_seat_type(balflex_item.get('seat_type'))
    balflex_gender = balflex_item.get('gender')

    # === CRITERION 1: STANDARD (Mandatory - 40 points) ===
    if heizmann_std and balflex_std:
        if heizmann_std == balflex_std:
            score += 40
            reasons.append(f"Standard: {heizmann_std}")
        else:
            # Standards don't match - this is a poor match
            # But we still allow it with 0 standard points
            warnings.append(f"Standard mismatch: {heizmann_std}≠{balflex_std}")
            return 0, []  # Reject if standards explicitly don't match
    elif heizmann_std and not balflex_std:
        # Heizmann has standard but Balflex doesn't
        # This is acceptable but lower confidence
        warnings.append(f"Balflex missing standard (Heizmann: {heizmann_std})")
    elif not heizmann_std and balflex_std:
        # Balflex has standard but Heizmann doesn't
        warnings.append(f"Heizmann missing standard (Balflex: {balflex_std})")
    # If both missing, we can't validate standard match

    # === CRITERION 2: DN (30 points) ===
    if heizmann_dn and balflex_dn:
        if heizmann_dn == balflex_dn:
            score += 30
            reasons.append(f"DN: {heizmann_dn}")
        elif abs(heizmann_dn - balflex_dn) <= 2:
            # Close DN match (within 2mm tolerance)
            score += 15
            reasons.append(f"DN close: {heizmann_dn}≈{balflex_dn}")
        else:
            # DN mismatch is serious
            warnings.append(f"DN mismatch: {heizmann_dn}≠{balflex_dn}")
    elif heizmann_dn or balflex_dn:
        warnings.append(f"DN missing in one product")

    # === CRITERION 3: SEAT TYPE (20 points) ===
    if heizmann_seat and balflex_seat:
        if heizmann_seat == balflex_seat:
            score += 20
            reasons.append(f"Seat: {heizmann_seat}")
        else:
            warnings.append(f"Seat mismatch: {heizmann_seat}≠{balflex_seat}")
    elif heizmann_seat or balflex_seat:
        warnings.append(f"Seat type missing in one product")

    # === CRITERION 4: GENDER (10 points or -10 penalty) ===
    if heizmann_gender and balflex_gender:
        if heizmann_gender == balflex_gender:
            score += 10
            reasons.append(f"Gender: {heizmann_gender}")
        elif heizmann_gender != 'Unknown' and balflex_gender != 'Unknown':
            # Gender mismatch is a red flag
            score -= 10
            warnings.append(f"Gender mismatch: {heizmann_gender}≠{balflex_gender}")
    elif heizmann_gender or balflex_gender:
        warnings.append(f"Gender missing in one product")

    # Add warnings to reasons if any
    if warnings:
        reasons.append(f"⚠️ {'; '.join(warnings)}")

    return score, reasons


def match_products(heizmann_data, balflex_data, min_threshold=50):
    """
    Match Heizmann and Balflex products
    min_threshold: Minimum score to consider a match (default 50)
    """
    print(f"\nMatching products with minimum threshold: {min_threshold}...")
    matches = []

    for heizmann_item in heizmann_data:
        best_match = None
        best_score = 0
        best_reasons = []

        for balflex_item in balflex_data:
            score, reasons = calculate_match_score(heizmann_item, balflex_item)

            if score > best_score and score >= min_threshold:
                best_score = score
                best_match = balflex_item
                best_reasons = reasons

        if best_match:
            # Determine match quality
            if best_score >= 90:
                quality = "Excellent"
            elif best_score >= 70:
                quality = "Very Good"
            elif best_score >= 60:
                quality = "Good"
            elif best_score >= 50:
                quality = "Fair"
            else:
                quality = "Poor"

            matches.append({
                # Heizmann
                'Heizmann_Model': heizmann_item['model'],
                'Heizmann_Article': heizmann_item['article_number'],
                'Heizmann_Reference': heizmann_item['reference'],
                'Heizmann_DN': heizmann_item.get('dn'),
                'Heizmann_Standard': heizmann_item.get('standard'),
                'Heizmann_Seat_Type': heizmann_item.get('seat_type'),
                'Heizmann_Connection': heizmann_item.get('connection_type'),
                'Heizmann_Identification': heizmann_item.get('identification'),
                'Heizmann_Thread_Size': heizmann_item.get('thread_size'),
                'Heizmann_URL': heizmann_item['url'],

                # Balflex
                'Balflex_Reference': best_match['reference'],
                'Balflex_Article': best_match['article_number'],
                'Balflex_Category': best_match.get('category'),
                'Balflex_Product_Type': best_match.get('product_type'),
                'Balflex_DN_mm': best_match.get('hose_size_mm'),
                'Balflex_Standard': best_match.get('standard'),
                'Balflex_Seat_Type': best_match.get('seat_type'),
                'Balflex_Gender': best_match.get('gender'),
                'Balflex_Thread_Size': best_match.get('thread_size'),

                # Match info
                'Match_Score': best_score,
                'Match_Quality': quality,
                'Match_Reasons': ', '.join(best_reasons)
            })

    return matches


def analyze_and_save_matches(matches, heizmann_total, balflex_total):
    """Analyze matches and save to Excel"""

    print(f"\n{'='*80}")
    print("MATCHING RESULTS")
    print(f"{'='*80}")

    print(f"\n📊 OVERVIEW:")
    print(f"   Heizmann products: {heizmann_total}")
    print(f"   Balflex products: {balflex_total}")
    print(f"   Total matches found: {len(matches)}")
    print(f"   Match rate: {len(matches)/heizmann_total*100:.1f}% of Heizmann products")

    # Score distribution
    score_ranges = {
        'Excellent (90-100)': 0,
        'Very Good (70-89)': 0,
        'Good (60-69)': 0,
        'Fair (50-59)': 0,
        'Poor (<50)': 0
    }

    for match in matches:
        score = match['Match_Score']
        if score >= 90:
            score_ranges['Excellent (90-100)'] += 1
        elif score >= 70:
            score_ranges['Very Good (70-89)'] += 1
        elif score >= 60:
            score_ranges['Good (60-69)'] += 1
        elif score >= 50:
            score_ranges['Fair (50-59)'] += 1
        else:
            score_ranges['Poor (<50)'] += 1

    print(f"\n📊 MATCH QUALITY DISTRIBUTION:")
    for quality, count in score_ranges.items():
        if count > 0:
            percentage = count/len(matches)*100
            bar = '█' * int(percentage / 2)
            print(f"   {quality:25}: {count:4} ({percentage:5.1f}%) {bar}")

    # Standard match analysis
    standards_matched = Counter()
    for match in matches:
        heiz_std = normalize_standard(match.get('Heizmann_Standard'))
        balf_std = normalize_standard(match.get('Balflex_Standard'))
        if heiz_std and balf_std and heiz_std == balf_std:
            standards_matched[heiz_std] += 1

    print(f"\n📊 STANDARD MATCHES:")
    for std, count in standards_matched.most_common():
        print(f"   {std:15}: {count:4} matches")

    # Save to Excel
    df = pd.DataFrame(matches)
    df = df.sort_values('Match_Score', ascending=False)

    output_file = 'data/balflex_heizmann_PRESSARMATUREN_MATCHED_IMPROVED.xlsx'

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Matches', index=False)

    print(f"\n✅ Saved to: {output_file}")

    # Show top matches
    print(f"\n📋 TOP 10 MATCHES:")
    for i, (idx, row) in enumerate(df.head(10).iterrows(), 1):
        print(f"\n{i}. Score: {row['Match_Score']} ({row['Match_Quality']})")
        print(f"   Heizmann: {row['Heizmann_Article']} - {row['Heizmann_Model'][:50]}")
        print(f"   Balflex:  {row['Balflex_Reference']} - {row['Balflex_Product_Type'][:50] if row['Balflex_Product_Type'] else 'N/A'}")
        print(f"   Reasons:  {row['Match_Reasons'][:100]}")

    return df


def main():
    """Main execution"""
    print("="*80)
    print("IMPROVED PRODUCT MATCHING ALGORITHM")
    print("="*80)

    # Load enhanced data
    print("\n1. Loading enhanced data...")

    with open('data/pressarmaturen_serie_x_ENHANCED.json', 'r', encoding='utf-8') as f:
        heizmann_data = json.load(f)

    with open('data/balflex_fittings_IMPROVED.json', 'r', encoding='utf-8') as f:
        balflex_data = json.load(f)

    print(f"   Heizmann: {len(heizmann_data)} products")
    print(f"   Balflex: {len(balflex_data)} products")

    # Data quality check
    print("\n2. Data quality check...")
    heiz_with_dn = sum(1 for p in heizmann_data if p.get('dn'))
    heiz_with_std = sum(1 for p in heizmann_data if p.get('standard'))
    balf_with_dn = sum(1 for p in balflex_data if p.get('hose_size_mm'))
    balf_with_std = sum(1 for p in balflex_data if p.get('standard'))

    print(f"   Heizmann DN coverage: {heiz_with_dn}/{len(heizmann_data)} ({heiz_with_dn/len(heizmann_data)*100:.1f}%)")
    print(f"   Heizmann Standard coverage: {heiz_with_std}/{len(heizmann_data)} ({heiz_with_std/len(heizmann_data)*100:.1f}%)")
    print(f"   Balflex DN coverage: {balf_with_dn}/{len(balflex_data)} ({balf_with_dn/len(balflex_data)*100:.1f}%)")
    print(f"   Balflex Standard coverage: {balf_with_std}/{len(balflex_data)} ({balf_with_std/len(balflex_data)*100:.1f}%)")

    # Matching with improved threshold
    print("\n3. Running matching algorithm...")
    matches = match_products(heizmann_data, balflex_data, min_threshold=50)

    # Analyze and save
    print("\n4. Analyzing and saving results...")
    df = analyze_and_save_matches(matches, len(heizmann_data), len(balflex_data))

    print("\n" + "="*80)
    print("✅ MATCHING COMPLETED SUCCESSFULLY!")
    print("="*80)

    return df


if __name__ == "__main__":
    df = main()
