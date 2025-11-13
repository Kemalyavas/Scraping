import json

data = json.load(open('data/balflex_products.json', encoding='utf-8'))

balmaster = [p for p in data if 'BALMASTER' in p['model']]
powerspir = [p for p in data if 'POWERSPIR' in p['model']]

print(f'BALMASTER: {len(balmaster)}')
print(f'POWERSPIR: {len(powerspir)}')

print('\nPOWERSPIR models:')
models = set([p['model'] for p in powerspir])
for m in sorted(models):
    print(f'  {m}')

if balmaster:
    print('\nBALMASTER sample:')
    print(json.dumps(balmaster[0], indent=2, ensure_ascii=False))

if powerspir:
    # Check for R12, R13, R15
    r12 = [p for p in powerspir if 'R12' in p['standard'] or 'R12' in p['model']]
    r13 = [p for p in powerspir if 'R13' in p['standard'] or 'R13' in p['model']]
    r15 = [p for p in powerspir if 'R15' in p['standard'] or 'R15' in p['model']]
    
    print(f'\nR12 products: {len(r12)}')
    print(f'R13 products: {len(r13)}')
    print(f'R15 products: {len(r15)}')
