import json

# Load Excel matches
matches = json.load(open('data/excel_matches.json', encoding='utf-8'))

print('='*80)
print('MANUEL KONTROL - Resimlerden gördüğümüz ürünler')
print('='*80)

# 1. ALFABIOTECH 5K EVOLUTION kontrolü (resimde gördüm)
print('\n1. ALFABIOTECH 5K EVOLUTION (Heizmann)')
alfa_5k = [m for m in matches if 'ALFABIOTECH 5K EVOLUTION' in str(m.get('Heizmann Model', ''))]
print(f'   Total matches: {len(alfa_5k)}')
if alfa_5k:
    print(f'   Örnek: {alfa_5k[0]["Balflex Model"]} <-> {alfa_5k[0]["Heizmann Model"]}')
    print(f'   DN: {alfa_5k[0].get("DN")}, Standard: {alfa_5k[0].get("Standard")}')

# 2. 3SPT SUPERFOREST kontrolü
print('\n2. 3SPT SUPERFOREST (Heizmann)')
superforest = [m for m in matches if 'SUPERFOREST' in str(m.get('Heizmann Model', ''))]
print(f'   Total matches: {len(superforest)}')
if superforest:
    print(f'   Örnek: {superforest[0]["Balflex Model"]} <-> {superforest[0]["Heizmann Model"]}')
    print(f'   DN: {superforest[0].get("DN")}')

# 3. BALMASTER kontrolü (Balflex tarafında)
print('\n3. BALMASTER BESTFLEX 4SP (Balflex)')
balmaster = [m for m in matches if 'BALMASTER' in str(m.get('Balflex Model', ''))]
print(f'   Total matches: {len(balmaster)}')
if balmaster:
    print(f'   Örnek: {balmaster[0]["Balflex Model"]} <-> {balmaster[0]["Heizmann Model"]}')
    print(f'   DN: {balmaster[0].get("DN")}, Standard: {balmaster[0].get("Standard")}')

# 4. POWERSPIR kontrolü
print('\n4. POWERSPIR BESTFLEX (Balflex)')
powerspir = [m for m in matches if 'POWERSPIR' in str(m.get('Balflex Model', ''))]
print(f'   Total matches: {len(powerspir)}')
if powerspir:
    print(f'   Örnek: {powerspir[0]["Balflex Model"]} <-> {powerspir[0]["Heizmann Model"]}')
    print(f'   DN: {powerspir[0].get("DN")}')

# 5. FLP2 TWIN kontrolü (resimde var)
print('\n5. FLP2 TWIN (Heizmann)')
flp2_twin = [m for m in matches if 'FLP2 TWIN' in str(m.get('Heizmann Model', ''))]
print(f'   Total matches: {len(flp2_twin)}')
if flp2_twin:
    for i, m in enumerate(flp2_twin[:2], 1):
        print(f'   {i}. {m["Balflex Model"]} ({m.get("DN")}) <-> {m["Heizmann Model"]}')

print('\n' + '='*80)
print('ŞİMDİ HEIZMANN WEB SİTESİNDEN BİR ÜRÜN SEÇ, BEN KONTROL EDEYİM')
print('='*80)
print('\nÖrneğin:')
print('- ALFABIOTECH 5K EVOLUTION DN16 (5/8")')
print('- 3SPT SUPERFOREST DN12 (1/2")')
print('- FLP2 TWIN DN10 (3/8")')
print('\nHangisini kontrol edelim? Heizmann sitesinden bir tane seç,')
print('ben de Excel\'deki datayı göstereyim, eşleşiyor mu bakalım.')
