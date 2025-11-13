"""Display matching results summary"""
import json
from collections import Counter

# Load matches
with open('data/product_matches.json', encoding='utf-8') as f:
    matches = json.load(f)

print('\n' + '='*60)
print('HYDRAULIC HOSE MATCHING RESULTS')
print('='*60)
print(f'\nTotal Matches: {len(matches)}')

# Quality distribution
quality_counts = Counter(m['match_quality'] for m in matches)
print('\nMatch Quality Distribution:')
for quality in ['Excellent Match', 'Good Match', 'Fair Match', 'Possible Match']:
    count = quality_counts.get(quality, 0)
    pct = count/len(matches)*100 if matches else 0
    print(f'  {quality:20s}: {count:3d} ({pct:5.1f}%)')

# Show sample excellent match
print('\n' + '-'*60)
print('SAMPLE EXCELLENT MATCH:')
print('-'*60)
excellent = [m for m in matches if m['match_quality'] == 'Excellent Match']
if excellent:
    ex = excellent[0]
    print(f"Balflex:  {ex['balflex_model']} {ex['balflex_reference']} (DN{ex['dn']}, {ex.get('standard', 'N/A')})")
    print(f"          Article: {ex['balflex_article_number']}")
    print(f"Heizmann: {ex['heizmann_model']} {ex['heizmann_reference']} (DN{ex['dn']}, {ex.get('standard', 'N/A')})")
    print(f"          Article: {ex['heizmann_article_number']}")
    print(f"Score:    {ex['match_score']:.1f}%")
    print(f"Reasons:  {', '.join(ex['match_reasons'])}")

# Show sample good match
print('\n' + '-'*60)
print('SAMPLE GOOD MATCH:')
print('-'*60)
good = [m for m in matches if m['match_quality'] == 'Good Match']
if good:
    ex = good[0]
    print(f"Balflex:  {ex['balflex_model']} {ex['balflex_reference']} (DN{ex['dn']}, {ex.get('standard', 'N/A')})")
    print(f"          Article: {ex['balflex_article_number']}")
    print(f"Heizmann: {ex['heizmann_model']} {ex['heizmann_reference']} (DN{ex['dn']}, {ex.get('standard', 'N/A')})")
    print(f"          Article: {ex['heizmann_article_number']}")
    print(f"Score:    {ex['match_score']:.1f}%")
    print(f"Reasons:  {', '.join(ex['match_reasons'])}")

# Standards coverage
print('\n' + '-'*60)
print('STANDARDS COVERAGE:')
print('-'*60)
matches_with_std = sum(1 for m in matches if m.get('standard'))
print(f"Matches with standards: {matches_with_std}/{len(matches)} ({matches_with_std/len(matches)*100:.1f}%)")

print('\n' + '='*60)
print('✓ Excel report saved to: output/product_comparison.xlsx')
print('='*60 + '\n')
