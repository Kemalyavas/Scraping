import json

# Load data
heizmann = json.load(open('data/heizmann_products.json', encoding='utf-8'))
matches = json.load(open('data/excel_matches.json', encoding='utf-8'))

print('='*80)
print('MANUEL KONTROL - Heizmann Resimleri')
print('='*80)

# 1. ALFABIOTECH 5K EVOLUTION
print('\n' + '='*80)
print('1. ALFABIOTECH 5K MINETUFF S-EVOLUTION')
print('='*80)
print('\nHEIZMANN RESİMDEN:')
print('  Normen: ISO 18752')
print('  Einlage: 4 oder 6 Stahldrahtspiralen')
print('  WP: 35 MPa (5000 PSI)')
print('\nBİZİM HEIZMANN DATA:')
alfa5k = [p for p in heizmann if 'ALFABIOTECH 5K EVOLUTION' in p['model']]
if alfa5k:
    print(f'  Total variants: {len(alfa5k)}')
    sample = alfa5k[0]
    print(f'  Model: {sample["model"]}')
    print(f'  Standard: {sample.get("standard", "N/A")}')
    print(f'  Construction: {sample.get("construction", "N/A")}')
    print(f'  DN örneği: {sample["dn"]}')
    
print('\nEXCEL MATCHES:')
alfa5k_matches = [m for m in matches if 'ALFABIOTECH 5K EVOLUTION' in str(m.get('Heizmann Model', ''))]
print(f'  Total matches: {len(alfa5k_matches)}')
if alfa5k_matches:
    for i, m in enumerate(alfa5k_matches[:3], 1):
        print(f'  {i}. {m["Balflex Model"]} ({m.get("DN")}) -> Match: {m["Match Quality"]}')

# 2. FLP2R SUPERTUFF
print('\n' + '='*80)
print('2. FLP2R-08SUPERTUFF (FXP2R SUPERTUFF)')
print('='*80)
print('\nHEIZMANN RESİMDEN:')
print('  Produktnummer: FLP2R-08SUPERTUFF')
print('  Artikelnummer: 487365')
print('  DN: 12')
print('  Betriebsdruck: 350 bar')
print('  Normen: SAE 100 R16, EN 857 2SC, MSHA IC-152/7')
print('  Einlage: 2 Stahldrahtgeflechte')

print('\nBİZİM HEIZMANN DATA:')
flp2r = [p for p in heizmann if p.get('article_number') == '487365']
if flp2r:
    print(f'  ✓ BULUNDU!')
    print(f'  Model: {flp2r[0]["model"]}')
    print(f'  DN: {flp2r[0]["dn"]}')
    print(f'  Working Pressure: {flp2r[0].get("working_pressure_bar", "N/A")} bar')
    print(f'  Standard: {flp2r[0].get("standard", "N/A")}')
else:
    # Try by model name
    flp2r_model = [p for p in heizmann if 'FLP2R' in p['model'] or 'FXP2R' in p['model']]
    if flp2r_model:
        print(f'  Model ile bulundu: {len(flp2r_model)} variants')
        print(f'  Model: {flp2r_model[0]["model"]}')
    else:
        print('  ❌ BULUNAMADI - Scraper çekmemiş!')

print('\nEXCEL MATCHES:')
flp2r_matches = [m for m in matches if 'FLP2R' in str(m.get('Heizmann Model', '')) or 'FXP2R' in str(m.get('Heizmann Model', ''))]
print(f'  Total matches: {len(flp2r_matches)}')

# 3. FLP2 TWIN
print('\n' + '='*80)
print('3. ALFAGOMMA FLEXOPAK 2 TWIN (FLP2 TWIN)')
print('='*80)
print('\nHEIZMANN RESİMDEN:')
print('  Normen: EN 857 2SC, SAE 100 R16, ISO 11237')
print('  Einlage: 2 Stahldrahtgeflechte')
print('  Max WP: ... MPa')

print('\nBİZİM HEIZMANN DATA:')
flp2_twin = [p for p in heizmann if 'FLP2 TWIN' in p['model']]
if flp2_twin:
    print(f'  Total variants: {len(flp2_twin)}')
    sample = flp2_twin[0]
    print(f'  Model: {sample["model"]}')
    print(f'  DN: {sample["dn"]}')
    print(f'  Working Pressure: {sample.get("working_pressure_bar", "N/A")} bar')
    print(f'  Standard: {sample.get("standard", "N/A")}')
else:
    print('  ❌ BULUNAMADI!')

print('\nEXCEL MATCHES:')
twin_matches = [m for m in matches if 'FLP2 TWIN' in str(m.get('Heizmann Model', ''))]
print(f'  Total matches: {len(twin_matches)}')
if twin_matches:
    for i, m in enumerate(twin_matches[:3], 1):
        print(f'  {i}. {m["Balflex Model"]} ({m.get("DN")}) -> {m["Match Quality"]}')

print('\n' + '='*80)
print('SONUÇ')
print('='*80)
print('✓ = Scraper çekti ve match buldu')
print('❌ = Scraper çekemedi')
print('='*80)
