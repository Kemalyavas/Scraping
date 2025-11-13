import pandas as pd
import json

# Read Excel file
excel_file = 'output/product_comparison.xlsx'
df = pd.read_excel(excel_file, sheet_name='Product Comparison')

# Convert to JSON
matches = df.to_dict('records')

# Save to JSON
with open('data/excel_matches.json', 'w', encoding='utf-8') as f:
    json.dump(matches, f, indent=2, ensure_ascii=False)

print(f'✓ Converted {len(matches)} matches from Excel to JSON')
print(f'\nFirst 3 matches:')
for i, match in enumerate(matches[:3], 1):
    print(f'\n{i}. {match.get("Balflex Model", "?")} <-> {match.get("Heizmann Model", "?")}')
    print(f'   DN: {match.get("DN", "?")} | Match: {match.get("Match Quality", "?")}')
    print(f'   Balflex Ref: {match.get("Balflex Reference", "?")}')
    print(f'   Heizmann Ref: {match.get("Heizmann Reference", "?")}')

# Show some ALFABIOTECH matches
print('\n' + '='*70)
print('ALFABIOTECH Matches:')
print('='*70)

alfa_matches = [m for m in matches if 'ALFABIOTECH' in str(m.get('Heizmann Model', ''))]
print(f'\nTotal ALFABIOTECH matches: {len(alfa_matches)}')

for i, m in enumerate(alfa_matches[:5], 1):
    print(f'\n{i}. Balflex: {m.get("Balflex Model")} ({m.get("Standard")})')
    print(f'   Heizmann: {m.get("Heizmann Model")}')
    print(f'   DN: {m.get("DN")} | {m.get("Inch Size")}')
    print(f'   Match: {m.get("Match Quality")} (Score: {m.get("Match Score")})')
