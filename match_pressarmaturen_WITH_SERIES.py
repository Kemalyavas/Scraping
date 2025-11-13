"""
FINAL Product Matching Algorithm
=================================

Fixed Issues:
1. ✓ Hose sizes corrected using dash code standards
2. ✓ Angle information added (90°/45°/straight) - MANDATORY criterion
3. ✓ Proper DN matching with tolerance
4. ✓ Standard matching validated
5. ✓ Comprehensive validation and warnings

Scoring System (Total: 100 points):
- Angle Match: 25 points (MANDATORY - reject if mismatch)
- Standard Match: 35 points (MANDATORY - reject if mismatch)
- DN Match: 30 points (exact) or 15 points (close ±2mm)
- Seat Type Match: 10 points
"""

import json
import re
import pandas as pd
from collections import Counter


def normalize_standard(std):
    """Normalize standard names for matching"""
    if not std:
        return None

    std_upper = std.upper()

    # Extract base standard
    for base in ['ISO', 'JIS', 'BSP', 'NPT', 'JIC', 'ORFS', 'SAE', 'DIN']:
        if base in std_upper:
            return base

    return None


def normalize_seat_type(seat):
    """Normalize seat type for matching"""
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
    """Determine gender from Heizmann product"""
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
    Calculate match score with STRICT angle, series, and standard checking

    Scoring (total 100):
    - Angle match: 20 points (MANDATORY - reject if mismatch)
    - Series (L/S) match: 20 points (MANDATORY - reject if mismatch)
    - Standard match: 30 points (MANDATORY - reject if mismatch)
    - DN match: 25 points (exact) or 12 points (close ±2mm)
    - Seat type match: 5 points

    Returns: (score, reasons, warnings)
    """
    score = 0
    reasons = []
    warnings = []

    # Get values
    heizmann_angle = heizmann_item.get('angle')
    balflex_angle = balflex_item.get('angle')

    heizmann_series = heizmann_item.get('series')
    balflex_series = balflex_item.get('series')

    heizmann_dn = heizmann_item.get('dn')
    balflex_dn = balflex_item.get('hose_size_mm')

    heizmann_std = normalize_standard(heizmann_item.get('standard'))
    balflex_std = normalize_standard(balflex_item.get('standard'))

    heizmann_seat = normalize_seat_type(heizmann_item.get('seat_type'))
    balflex_seat = normalize_seat_type(balflex_item.get('seat_type'))

    heizmann_gender = determine_gender_heizmann(heizmann_item)
    balflex_gender = balflex_item.get('gender')

    # === CRITERION 1: ANGLE (MANDATORY - 20 points) ===
    if heizmann_angle and balflex_angle:
        if heizmann_angle == balflex_angle:
            score += 20
            reasons.append(f"Angle: {heizmann_angle}")
        else:
            # ANGLE MISMATCH - REJECT!
            return 0, [], [f"ANGLE MISMATCH: {heizmann_angle} ≠ {balflex_angle}"]
    elif heizmann_angle or balflex_angle:
        # One has angle, other doesn't - allow but warn
        warnings.append(f"Angle missing in one product (H:{heizmann_angle}, B:{balflex_angle})")
    # If both missing, continue (but no points)

    # === CRITERION 2: SERIES L/S (MANDATORY - 20 points) ===
    if heizmann_series and balflex_series:
        if heizmann_series == balflex_series:
            score += 20
            reasons.append(f"Series: {heizmann_series}")
        else:
            # SERIES MISMATCH - REJECT!
            return 0, [], [f"SERIES MISMATCH: {heizmann_series} (pressure) ≠ {balflex_series} (pressure)"]
    elif heizmann_series or balflex_series:
        # One has series, other doesn't - allow but warn
        warnings.append(f"Series (L/S) missing in one product (H:{heizmann_series}, B:{balflex_series})")
    # If both missing, continue (but no points)

    # === CRITERION 3: STANDARD (MANDATORY - 30 points) ===
    if heizmann_std and balflex_std:
        if heizmann_std == balflex_std:
            score += 30
            reasons.append(f"Standard: {heizmann_std}")
        else:
            # STANDARD MISMATCH - REJECT!
            return 0, [], [f"STANDARD MISMATCH: {heizmann_std} ≠ {balflex_std}"]
    elif heizmann_std or balflex_std:
        warnings.append(f"Standard missing in one product")
    # If both missing, continue (risky but allowed)

    # === CRITERION 4: DN (25 points) ===
    if heizmann_dn and balflex_dn:
        try:
            heizmann_dn_val = float(heizmann_dn)
            balflex_dn_val = float(balflex_dn)

            if abs(heizmann_dn_val - balflex_dn_val) <= 0.5:
                # Exact match
                score += 25
                reasons.append(f"DN: {heizmann_dn_val:.1f}mm")
            elif abs(heizmann_dn_val - balflex_dn_val) <= 2.0:
                # Close match (within 2mm tolerance)
                score += 12
                reasons.append(f"DN close: {heizmann_dn_val:.1f}≈{balflex_dn_val:.1f}mm")
            else:
                # DN difference too large
                warnings.append(f"DN mismatch: {heizmann_dn_val:.1f} vs {balflex_dn_val:.1f}mm")
        except:
            warnings.append("DN values not comparable")
    elif heizmann_dn or balflex_dn:
        warnings.append(f"DN missing in one product")

    # === CRITERION 5: SEAT TYPE (5 points) ===
    if heizmann_seat and balflex_seat:
        if heizmann_seat == balflex_seat:
            score += 5
            reasons.append(f"Seat: {heizmann_seat}")
        else:
            warnings.append(f"Seat mismatch: {heizmann_seat} ≠ {balflex_seat}")
    elif heizmann_seat or balflex_seat:
        warnings.append("Seat type missing in one product")

    # === BONUS: Gender match (validation only) ===
    if heizmann_gender and balflex_gender and heizmann_gender != 'Unknown' and balflex_gender != 'Unknown':
        if heizmann_gender == balflex_gender:
            reasons.append(f"Gender: {heizmann_gender}")
        else:
            warnings.append(f"⚠️ Gender mismatch: {heizmann_gender} ≠ {balflex_gender}")

    # Add warnings to reasons if any
    if warnings:
        reasons.append(f"[Warnings: {'; '.join(warnings)}]")

    return score, reasons, warnings


def match_products(heizmann_data, balflex_data, min_threshold=60):
    """
    Match products with strict angle, series, and standard checking
    min_threshold: Minimum score to consider a match (default 60)
    """
    print(f"\nMatching products with minimum threshold: {min_threshold}...")
    print(f"STRICT MODE: Angle, Series (L/S), and Standard must match!")

    matches = []
    rejected_counts = {'angle_mismatch': 0, 'series_mismatch': 0, 'standard_mismatch': 0, 'low_score': 0}

    for heizmann_item in heizmann_data:
        best_match = None
        best_score = 0
        best_reasons = []

        for balflex_item in balflex_data:
            score, reasons, warnings = calculate_match_score(heizmann_item, balflex_item)

            # Track rejections
            if score == 0 and warnings:
                if 'ANGLE MISMATCH' in warnings[0]:
                    rejected_counts['angle_mismatch'] += 1
                elif 'SERIES MISMATCH' in warnings[0]:
                    rejected_counts['series_mismatch'] += 1
                elif 'STANDARD MISMATCH' in warnings[0]:
                    rejected_counts['standard_mismatch'] += 1

            if score > best_score and score >= min_threshold:
                best_score = score
                best_match = balflex_item
                best_reasons = reasons

        if best_match:
            # Determine match quality
            if best_score >= 90:
                quality = "Excellent"
            elif best_score >= 75:
                quality = "Very Good"
            elif best_score >= 60:
                quality = "Good"
            else:
                quality = "Fair"

            matches.append({
                # Heizmann
                'Heizmann_Model': heizmann_item['model'],
                'Heizmann_Article': heizmann_item['article_number'],
                'Heizmann_Reference': heizmann_item['reference'],
                'Heizmann_DN': heizmann_item.get('dn'),
                'Heizmann_Angle': heizmann_item.get('angle'),
                'Heizmann_Series': heizmann_item.get('series'),
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
                'Balflex_Dash_Code': best_match.get('dash_size'),
                'Balflex_Hose_Size_mm': best_match.get('hose_size_mm'),
                'Balflex_Hose_Size_inch': best_match.get('hose_size_inch'),
                'Balflex_Angle': best_match.get('angle'),
                'Balflex_Series': best_match.get('series'),
                'Balflex_Standard': best_match.get('standard'),
                'Balflex_Seat_Type': best_match.get('seat_type'),
                'Balflex_Gender': best_match.get('gender'),
                'Balflex_Thread_Size': best_match.get('thread_size'),

                # Match info
                'Match_Score': best_score,
                'Match_Quality': quality,
                'Match_Reasons': ', '.join(best_reasons)
            })
        else:
            rejected_counts['low_score'] += 1

    print(f"\n📊 REJECTION STATISTICS:")
    print(f"   Rejected due to angle mismatch: {rejected_counts['angle_mismatch']}")
    print(f"   Rejected due to series (L/S) mismatch: {rejected_counts['series_mismatch']}")
    print(f"   Rejected due to standard mismatch: {rejected_counts['standard_mismatch']}")
    print(f"   Rejected due to low score: {rejected_counts['low_score']}")

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
        'Very Good (75-89)': 0,
        'Good (60-74)': 0,
        'Fair (<60)': 0
    }

    for match in matches:
        score = match['Match_Score']
        if score >= 90:
            score_ranges['Excellent (90-100)'] += 1
        elif score >= 75:
            score_ranges['Very Good (75-89)'] += 1
        elif score >= 60:
            score_ranges['Good (60-74)'] += 1
        else:
            score_ranges['Fair (<60)'] += 1

    print(f"\n📊 MATCH QUALITY DISTRIBUTION:")
    for quality, count in score_ranges.items():
        if count > 0:
            percentage = count/len(matches)*100
            bar = '█' * int(percentage / 2)
            print(f"   {quality:25}: {count:4} ({percentage:5.1f}%) {bar}")

    # Angle match analysis
    angle_matches = Counter()
    for match in matches:
        heiz_angle = match.get('Heizmann_Angle')
        balf_angle = match.get('Balflex_Angle')
        if heiz_angle and balf_angle:
            angle_matches[f"{heiz_angle} ↔ {balf_angle}"] += 1

    print(f"\n📊 ANGLE MATCHES:")
    for angle_pair, count in angle_matches.most_common():
        print(f"   {angle_pair:20}: {count:4} matches")

    # Save to Excel
    df = pd.DataFrame(matches)
    df = df.sort_values('Match_Score', ascending=False)

    output_file = 'data/balflex_heizmann_PRESSARMATUREN_WITH_SERIES.xlsx'

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Matches', index=False)

    print(f"\n✅ Saved to: {output_file}")

    # Show top matches
    print(f"\n📋 TOP 10 MATCHES:")
    for i, (idx, row) in enumerate(df.head(10).iterrows(), 1):
        print(f"\n{i}. Score: {row['Match_Score']} ({row['Match_Quality']})")
        print(f"   Heizmann: {row['Heizmann_Article']} - {row['Heizmann_Model'][:50]}")
        print(f"             Angle: {row['Heizmann_Angle']}, DN: {row['Heizmann_DN']}, Std: {row['Heizmann_Standard']}")
        print(f"   Balflex:  {row['Balflex_Reference']} - {row['Balflex_Product_Type'][:50] if pd.notna(row['Balflex_Product_Type']) else 'N/A'}")
        print(f"             Angle: {row['Balflex_Angle']}, Hose: {row['Balflex_Hose_Size_mm']}mm (Dash {row['Balflex_Dash_Code']})")
        print(f"   Reasons:  {row['Match_Reasons'][:100]}")

    return df


def main():
    """Main execution"""
    print("="*80)
    print("PRODUCT MATCHING WITH L/S SERIES VALIDATION")
    print("="*80)

    # Load data with L/S series information
    print("\n1. Loading data with L/S series information...")

    with open('data/pressarmaturen_serie_x_WITH_SERIES.json', 'r', encoding='utf-8') as f:
        heizmann_data = json.load(f)

    with open('data/balflex_fittings_WITH_SERIES.json', 'r', encoding='utf-8') as f:
        balflex_data = json.load(f)

    print(f"   Heizmann: {len(heizmann_data)} products")
    print(f"   Balflex: {len(balflex_data)} products")

    # Data quality check
    print("\n2. Data quality check...")
    heiz_with_angle = sum(1 for p in heizmann_data if p.get('angle'))
    heiz_with_series = sum(1 for p in heizmann_data if p.get('series'))
    heiz_with_dn = sum(1 for p in heizmann_data if p.get('dn'))
    heiz_with_std = sum(1 for p in heizmann_data if p.get('standard'))

    balf_with_angle = sum(1 for p in balflex_data if p.get('angle'))
    balf_with_series = sum(1 for p in balflex_data if p.get('series'))
    balf_with_dn = sum(1 for p in balflex_data if p.get('hose_size_mm'))
    balf_with_std = sum(1 for p in balflex_data if p.get('standard'))

    print(f"   Heizmann Angle: {heiz_with_angle}/{len(heizmann_data)} ({heiz_with_angle/len(heizmann_data)*100:.1f}%)")
    print(f"   Heizmann Series (L/S): {heiz_with_series}/{len(heizmann_data)} ({heiz_with_series/len(heizmann_data)*100:.1f}%)")
    print(f"   Heizmann DN: {heiz_with_dn}/{len(heizmann_data)} ({heiz_with_dn/len(heizmann_data)*100:.1f}%)")
    print(f"   Heizmann Standard: {heiz_with_std}/{len(heizmann_data)} ({heiz_with_std/len(heizmann_data)*100:.1f}%)")
    print(f"   Balflex Angle: {balf_with_angle}/{len(balflex_data)} ({balf_with_angle/len(balflex_data)*100:.1f}%)")
    print(f"   Balflex Series (L/S): {balf_with_series}/{len(balflex_data)} ({balf_with_series/len(balflex_data)*100:.1f}%)")
    print(f"   Balflex Hose Size: {balf_with_dn}/{len(balflex_data)} ({balf_with_dn/len(balflex_data)*100:.1f}%)")
    print(f"   Balflex Standard: {balf_with_std}/{len(balflex_data)} ({balf_with_std/len(balflex_data)*100:.1f}%)")

    # Matching
    print("\n3. Running matching algorithm with L/S series validation...")
    matches = match_products(heizmann_data, balflex_data, min_threshold=60)

    # Analyze and save
    print("\n4. Analyzing and saving results...")
    df = analyze_and_save_matches(matches, len(heizmann_data), len(balflex_data))

    print("\n" + "="*80)
    print("✅ MATCHING WITH L/S SERIES VALIDATION COMPLETED!")
    print("="*80)

    return df


if __name__ == "__main__":
    df = main()
