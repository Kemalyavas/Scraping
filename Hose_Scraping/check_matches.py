import json

matches = json.load(open('data/product_matches.json', encoding='utf-8'))

print(f'Total matches: {len(matches)}\n')

# Check for BALMASTER and POWERSPIR
balmaster_matches = [m for m in matches if 'BALMASTER' in m['balflex_model']]
powerspir_matches = [m for m in matches if 'POWERSPIR' in m['balflex_model']]

print(f'BALMASTER matches: {len(balmaster_matches)}')
print(f'POWERSPIR matches: {len(powerspir_matches)}\n')

if balmaster_matches:
    print('=== BALMASTER MATCHES ===')
    for m in balmaster_matches[:5]:
        print(f"\n{m['balflex_model']} ({m['standard']})")
        print(f"  -> {m['heizmann_model']}")
        print(f"  Match Quality: {m['match_quality']}")

if powerspir_matches:
    print('\n=== POWERSPIR MATCHES ===')
    for m in powerspir_matches[:5]:
        print(f"\n{m['balflex_model']} ({m['standard']})")
        print(f"  -> {m['heizmann_model']}")
        print(f"  Match Quality: {m['match_quality']}")
