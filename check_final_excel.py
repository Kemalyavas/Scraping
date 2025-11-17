import pandas as pd

df = pd.read_excel('balflex_heizmann_PRESSARMATUREN_FINAL.xlsx')

print("="*60)
print("EXCEL DOSYASI ANALİZİ - RETO'NUN HATALARINI KONTROL")
print("="*60)

print(f"\n📊 TOPLAM: {len(df)} eşleşme\n")

# 1. AÇI KONTROLÜ
print("="*60)
print("1️⃣ AÇI (ANGLE) KONTROLÜ")
print("="*60)
heizmann_angle_count = df['Heizmann_Angle'].notna().sum()
balflex_angle_count = df['Balflex_Angle'].notna().sum()

print(f"✓ Heizmann Angle dolu: {heizmann_angle_count} / {len(df)} ({heizmann_angle_count/len(df)*100:.1f}%)")
print(f"✓ Balflex Angle dolu: {balflex_angle_count} / {len(df)} ({balflex_angle_count/len(df)*100:.1f}%)")

# Açı uyumsuzluğu kontrolü
angle_mismatch = df[(df['Heizmann_Angle'].notna()) & (df['Balflex_Angle'].notna()) & 
                    (df['Heizmann_Angle'] != df['Balflex_Angle'])]
print(f"\n⚠️ Açı uyumsuzluğu: {len(angle_mismatch)} adet")
if len(angle_mismatch) > 0:
    print("\nİlk 3 uyumsuzluk:")
    for i, row in angle_mismatch.head(3).iterrows():
        print(f"  - {row['Heizmann_Article']}: Heizmann {row['Heizmann_Angle']} ≠ Balflex {row['Balflex_Angle']}")

# 2. DN/HOSE SIZE KONTROLÜ
print("\n" + "="*60)
print("2️⃣ DN / HOSE SIZE KONTROLÜ")
print("="*60)
heizmann_dn_count = df['Heizmann_DN'].notna().sum()
balflex_hose_count = df['Balflex_Hose_Size_mm'].notna().sum()

print(f"✓ Heizmann DN dolu: {heizmann_dn_count} / {len(df)} ({heizmann_dn_count/len(df)*100:.1f}%)")
print(f"✓ Balflex Hose Size (mm) dolu: {balflex_hose_count} / {len(df)} ({balflex_hose_count/len(df)*100:.1f}%)")

# DN uyumsuzluğu kontrolü (±2mm tolerans dışı)
dn_mismatch = df[(df['Heizmann_DN'].notna()) & (df['Balflex_Hose_Size_mm'].notna()) & 
                 (abs(df['Heizmann_DN'] - df['Balflex_Hose_Size_mm']) > 2)]
print(f"\n⚠️ DN uyumsuzluğu (>2mm fark): {len(dn_mismatch)} adet")
if len(dn_mismatch) > 0:
    print("\nİlk 5 uyumsuzluk:")
    for i, row in dn_mismatch.head(5).iterrows():
        diff = abs(row['Heizmann_DN'] - row['Balflex_Hose_Size_mm'])
        print(f"  - {row['Heizmann_Article']}: Heizmann {row['Heizmann_DN']}mm ≠ Balflex {row['Balflex_Hose_Size_mm']}mm (fark: {diff:.1f}mm)")

# 3. DASH CODE KONTROLÜ
print("\n" + "="*60)
print("3️⃣ DASH CODE KONTROLÜ")
print("="*60)
dash_count = df['Balflex_Dash_Code'].notna().sum()
print(f"✓ Balflex Dash Code dolu: {dash_count} / {len(df)} ({dash_count/len(df)*100:.1f}%)")

# 4. SCORE DAĞILIMI
print("\n" + "="*60)
print("4️⃣ MATCH QUALITY DAĞILIMI")
print("="*60)
quality_counts = df['Match_Quality'].value_counts()
for quality, count in quality_counts.items():
    print(f"  {quality}: {count} ({count/len(df)*100:.1f}%)")

# 5. RETO'NUN ÖRNEĞİNİ KONTROL ET
print("\n" + "="*60)
print("5️⃣ RETO'NUN ÖRNEĞİ (Article: 485695)")
print("="*60)
reto_example = df[df['Heizmann_Article'] == 485695]
if len(reto_example) > 0:
    row = reto_example.iloc[0]
    print(f"✓ Bulundu!")
    print(f"  Heizmann Model: {row['Heizmann_Model']}")
    print(f"  Heizmann Angle: {row['Heizmann_Angle']}")
    print(f"  Heizmann DN: {row['Heizmann_DN']}mm")
    print(f"  Balflex Product: {row['Balflex_Product_Type']}")
    print(f"  Balflex Angle: {row['Balflex_Angle']}")
    print(f"  Balflex Hose Size: {row['Balflex_Hose_Size_mm']}mm")
    print(f"  Match Score: {row['Match_Score']}")
    print(f"  Match Quality: {row['Match_Quality']}")
else:
    print("❌ Bulunamadı!")

# 6. ÖRNEK MÜKEMMEL EŞLEŞMELERİ GÖSTER
print("\n" + "="*60)
print("6️⃣ ÖRNEK MÜKEMMEL EŞLEŞMELER (Score=100)")
print("="*60)
perfect = df[df['Match_Score'] == 100].head(3)
for i, row in perfect.iterrows():
    print(f"\n✓ {row['Heizmann_Article']} - {row['Heizmann_Model']}")
    print(f"  Heizmann: DN={row['Heizmann_DN']}, Angle={row['Heizmann_Angle']}, Standard={row['Heizmann_Standard']}")
    print(f"  Balflex: Size={row['Balflex_Hose_Size_mm']}, Angle={row['Balflex_Angle']}, Standard={row['Balflex_Standard']}")
    print(f"  Reasons: {row['Match_Reasons']}")

print("\n" + "="*60)
print("✅ ANALİZ TAMAMLANDI")
print("="*60)
