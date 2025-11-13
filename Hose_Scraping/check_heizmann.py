import json

data = json.load(open('data/heizmann_products.json', encoding='utf-8'))

print(f'Total Heizmann: {len(data)}')

alfa = [p for p in data if 'ALFABIOTECH' in p['model']]
print(f'ALFABIOTECH: {len(alfa)}')

if alfa:
    print('\nALFABIOTECH models:')
    models = set([p['model'] for p in alfa])
    for m in sorted(models):
        print(f'  {m}')
    
    print('\nSample:')
    print(json.dumps(alfa[0], indent=2, ensure_ascii=False))

# Check all model names
print('\n=== ALL HEIZMANN MODELS ===')
all_models = set([p['model'] for p in data])
for m in sorted(all_models):
    count = len([p for p in data if p['model'] == m])
    print(f'{count:3}  {m}')
