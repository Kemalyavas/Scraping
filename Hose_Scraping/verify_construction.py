"""Verify construction types are assigned"""
import json

with open('data/heizmann_products.json', encoding='utf-8') as f:
    data = json.load(f)

samples = [p for p in data if p['model'] in ['1SN', '2SN', '2TE', 'AT3', 'FLP2']]

print('\n=== Construction Types ===\n')
print(f"{'Model':<15} {'Standard':<25} {'Construction':<20}")
print('-' * 60)
for p in samples[:10]:
    model = p['model']
    standard = p.get('standard', 'N/A')
    construction = p.get('construction', 'MISSING')
    print(f"{model:<15} {standard:<25} {construction:<20}")
