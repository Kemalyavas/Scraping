"""Merge old ORFS data with new improved data"""
import json

# Load new improved data
print("Loading new improved data...")
with open('data/heizmann_fittings_improved.json', 'r', encoding='utf-8') as f:
    new_data = json.load(f)

print(f"New data: {len(new_data)} products")

# Load old data
print("Loading old data...")
with open('data/heizmann_fittings.json', 'r', encoding='utf-8') as f:
    old_data = json.load(f)

print(f"Old data: {len(old_data)} products")

# Get ORFS from old data
orfs_old = [p for p in old_data if 'ORFS' in p.get('category', '')]
print(f"\nORFS products in old data: {len(orfs_old)}")

# Check if ORFS already in new data
orfs_new = [p for p in new_data if 'ORFS' in p.get('category', '')]
print(f"ORFS products in new data: {len(orfs_new)}")

# Merge: Keep all new data + add ORFS from old data if not in new
merged = new_data.copy()

if len(orfs_new) == 0:
    print("\n✅ Adding ORFS from old data...")
    merged.extend(orfs_old)
else:
    print("\n⚠️ ORFS already exists in new data, skipping merge")

print(f"\n📊 FINAL MERGED DATA:")
print(f"Total products: {len(merged)}")

# Analyze merged
from collections import Counter
cats = Counter(p['category'] for p in merged)
print(f"\nCategories:")
for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {count}")

# Thread extraction
with_thread = [p for p in merged if p.get('thread_type')]
print(f"\nThread extraction: {len(with_thread)}/{len(merged)} ({len(with_thread)/len(merged)*100:.1f}%)")

# Save merged
with open('data/heizmann_fittings_merged.json', 'w', encoding='utf-8') as f:
    json.dump(merged, f, ensure_ascii=False, indent=2)

print(f"\n✅ Saved to: data/heizmann_fittings_merged.json")
