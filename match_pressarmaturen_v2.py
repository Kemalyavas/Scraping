import json
import re
from fuzzywuzzy import fuzz

# Load data
print("Loading data...")
with open('data/pressarmaturen_serie_x_FULL_SELENIUM.json', 'r', encoding='utf-8') as f:
    heizmann_data = json.load(f)

with open('data/balflex_fittings_ENHANCED.json', 'r', encoding='utf-8') as f:
    balflex_data = json.load(f)

print(f"Heizmann: {len(heizmann_data)} variants")
print(f"Balflex: {len(balflex_data)} products")

# Parse DN from identification field
def extract_dn_from_identification(ident):
    """DKM-K DN6 → 6"""
    if not ident:
        return None
    
    match = re.search(r'DN\s*(\d+)', ident, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None

# Parse thread size from identification
def extract_thread_from_identification(ident):
    """DKM-K DN6 M16X1,5 → M16X1.5"""
    if not ident:
        return None
    
    # M14X1.5, G1/4-19, etc.
    match = re.search(r'([MG]\d+[X/][\d.,-]+)', ident, re.IGNORECASE)
    if match:
        return match.group(1).replace(',', '.')
    return None

# Normalize standard names
def normalize_standard(std):
    """JIS 8363 → JIS, ISO 8434-6 → ISO"""
    if not std:
        return None
    
    std_upper = std.upper()
    
    # Extract base standard
    for base in ['JIS', 'BSP', 'NPT', 'JIC', 'ORFS', 'SAE', 'ISO', 'DIN']:
        if base in std_upper:
            return base
    
    return None

# Normalize seat type
def normalize_seat_type(seat):
    """60° Innenkonus → 60° Cone, 60° Cone Seat → 60° Cone"""
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

# Determine gender from connection type and identification
def determine_gender(heizmann_item):
    """Innengewinde → Female, Aussengewinde → Male"""
    connection = heizmann_item.get('connection_type', '')
    ident = heizmann_item.get('identification', '')
    model = heizmann_item.get('model', '')
    
    # Connection type based
    if connection:
        if 'innengewinde' in connection.lower() or 'innenkegel' in connection.lower():
            return 'Female'
        if 'aussengewinde' in connection.lower() or 'aussenkegel' in connection.lower():
            return 'Male'
    
    # Identification based
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

# Calculate match score
def calculate_match_score(heizmann_item, balflex_item):
    """
    Scoring system:
    - Standard match: 40 points (mandatory)
    - DN match: 30 points
    - Seat type match: 20 points
    - Gender match: 10 points
    Total: 100 points
    Minimum: 40 points (only standard)
    """
    score = 0
    reasons = []
    
    # Parse Heizmann data
    heizmann_dn = extract_dn_from_identification(heizmann_item.get('identification'))
    heizmann_std = normalize_standard(heizmann_item.get('standard'))
    heizmann_seat = normalize_seat_type(heizmann_item.get('seat_type'))
    heizmann_gender = determine_gender(heizmann_item)
    
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
    
    # 1. STANDARD (Mandatory - 40 points)
    if heizmann_std and balflex_std:
        if heizmann_std == balflex_std:
            score += 40
            reasons.append(f"Standard: {heizmann_std}")
        else:
            return 0, []  # No match if standards don't match
    elif not heizmann_std or not balflex_std:
        # If either doesn't have standard, skip this criterion but allow match
        pass
    
    # 2. DN (30 points)
    if heizmann_dn and balflex_dn:
        if heizmann_dn == balflex_dn:
            score += 30
            reasons.append(f"DN: {heizmann_dn}")
        elif abs(heizmann_dn - balflex_dn) <= 2:
            score += 15  # Partial match for close DN
            reasons.append(f"DN close: {heizmann_dn}≈{balflex_dn}")
    
    # 3. SEAT TYPE (20 points)
    if heizmann_seat and balflex_seat:
        if heizmann_seat == balflex_seat:
            score += 20
            reasons.append(f"Seat: {heizmann_seat}")
    
    # 4. GENDER (10 points)
    if heizmann_gender and balflex_gender:
        if heizmann_gender == balflex_gender:
            score += 10
            reasons.append(f"Gender: {heizmann_gender}")
        elif heizmann_gender != 'Unknown' and balflex_gender != 'Unknown':
            score -= 10  # Penalty for gender mismatch
            reasons.append(f"Gender mismatch: {heizmann_gender}≠{balflex_gender}")
    
    return score, reasons

# Match products
print("\nMatching products...")
matches = []

for heizmann_item in heizmann_data:
    best_match = None
    best_score = 0
    best_reasons = []
    
    for balflex_item in balflex_data:
        score, reasons = calculate_match_score(heizmann_item, balflex_item)
        
        if score > best_score and score >= 40:  # Minimum threshold
            best_score = score
            best_match = balflex_item
            best_reasons = reasons
    
    if best_match:
        matches.append({
            # Heizmann
            'Heizmann_Model': heizmann_item['model'],
            'Heizmann_Article': heizmann_item['article_number'],
            'Heizmann_Reference': heizmann_item['reference'],
            'Heizmann_DN': extract_dn_from_identification(heizmann_item.get('identification')),
            'Heizmann_Standard': heizmann_item.get('standard'),
            'Heizmann_Seat_Type': heizmann_item.get('seat_type'),
            'Heizmann_Connection': heizmann_item.get('connection_type'),
            'Heizmann_Identification': heizmann_item.get('identification'),
            'Heizmann_URL': heizmann_item['url'],
            
            # Balflex
            'Balflex_Reference': best_match['reference'],
            'Balflex_Article': best_match['article_number'],
            'Balflex_Product_Type': best_match.get('product_type'),
            'Balflex_DN_mm': best_match.get('hose_size_mm'),
            'Balflex_Standard': best_match.get('standard'),
            'Balflex_Seat_Type': best_match.get('seat_type'),
            'Balflex_Gender': best_match.get('gender'),
            'Balflex_Thread_Size': best_match.get('thread_size'),
            
            # Match info
            'Match_Score': best_score,
            'Match_Reasons': ', '.join(best_reasons)
        })

print(f"\n✓ Match bulunan: {len(matches)} / {len(heizmann_data)} ({len(matches)/len(heizmann_data)*100:.1f}%)")

# Score distribution
score_ranges = {'40-49': 0, '50-59': 0, '60-69': 0, '70-79': 0, '80-89': 0, '90-100': 0}
for match in matches:
    score = match['Match_Score']
    if 40 <= score < 50: score_ranges['40-49'] += 1
    elif 50 <= score < 60: score_ranges['50-59'] += 1
    elif 60 <= score < 70: score_ranges['60-69'] += 1
    elif 70 <= score < 80: score_ranges['70-79'] += 1
    elif 80 <= score < 90: score_ranges['80-89'] += 1
    elif 90 <= score <= 100: score_ranges['90-100'] += 1

print("\nScore distribution:")
for range_name, count in score_ranges.items():
    if count > 0:
        print(f"  {range_name}: {count} ({count/len(matches)*100:.1f}%)")

# Save to Excel
import pandas as pd

df = pd.DataFrame(matches)
df = df.sort_values('Match_Score', ascending=False)

output_file = 'data/balflex_heizmann_PRESSARMATUREN_MATCHED_V2.xlsx'
df.to_excel(output_file, index=False)

print(f"\n✓ Kaydedildi: {output_file}")
print(f"\nTop 5 matches:")
for i, row in df.head(5).iterrows():
    print(f"\n{i+1}. Score: {row['Match_Score']}")
    print(f"   Heizmann: {row['Heizmann_Model']} ({row['Heizmann_Article']})")
    print(f"   Balflex: {row['Balflex_Product_Type']} ({row['Balflex_Reference']})")
    print(f"   Reasons: {row['Match_Reasons']}")
