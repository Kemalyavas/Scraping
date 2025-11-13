"""
Main Execution Script
Runs the complete hydraulic hose comparison pipeline
"""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent / 'scripts'))

from scripts.balflex_pdf_parser import BalflexPDFParser
from scripts.heizmann_scraper import HeizmannScraper
from scripts.product_matcher import ProductMatcher
from scripts.excel_generator import ExcelGenerator


def main():
    """Run the complete pipeline"""
    
    print("=" * 70)
    print("HYDRAULIC HOSE PRODUCT COMPARISON TOOL")
    print("Comparing products from Balflex and Heizmann")
    print("=" * 70)
    print()
    
    # Define file paths
    data_dir = Path(__file__).parent / 'data'
    output_dir = Path(__file__).parent / 'output'
    
    catalog_file = data_dir / 'BALFLEX-HOSES-CATALOGUE_HOSECAT.E.01.2023.pdf'
    balflex_json = data_dir / 'balflex_products.json'
    heizmann_json = data_dir / 'heizmann_products.json'
    matches_json = data_dir / 'product_matches.json'
    output_excel = output_dir / 'product_comparison.xlsx'
    
    # Ensure directories exist
    data_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    # Step 1: Parse Balflex catalog
    print("STEP 1: Parsing Balflex Catalog PDF")
    print("-" * 70)
    
    if not catalog_file.exists():
        print(f"❌ Error: {catalog_file} not found!")
        print()
        print("Please place the Balflex catalog PDF file in the 'data/' folder")
        print("Expected filename: BALFLEX-HOSES-CATALOGUE_HOSECAT.E.01.2023.pdf")
        return
    
    try:
        parser = BalflexPDFParser(str(catalog_file))
        balflex_products = parser.parse()
        parser.save_to_json(str(balflex_json))
        print(f"✓ Successfully parsed {len(balflex_products)} Balflex products from PDF")
    except Exception as e:
        print(f"❌ Error parsing Balflex catalog: {e}")
        return
    
    print()
    
    # Step 2: Scrape Heizmann website
    print("STEP 2: Scraping Heizmann Website")
    print("-" * 70)
    print("This may take several minutes...")
    print()
    
    try:
        scraper = HeizmannScraper()
        heizmann_products = scraper.scrape()
        scraper.save_to_json(str(heizmann_json))
        print(f"✓ Successfully scraped {len(heizmann_products)} Heizmann products")
    except Exception as e:
        print(f"❌ Error scraping Heizmann website: {e}")
        print("Tip: Check your internet connection and try again")
        return
    
    print()
    
    # Step 3: Match products
    print("STEP 3: Matching Products")
    print("-" * 70)
    
    try:
        matcher = ProductMatcher(str(balflex_json), str(heizmann_json))
        matches = matcher.match_products()
        matcher.save_to_json(str(matches_json))
        
        # Show match quality breakdown
        quality_counts = {}
        for match in matches:
            quality = match['match_quality']
            quality_counts[quality] = quality_counts.get(quality, 0) + 1
        
        print()
        print("Match Quality Breakdown:")
        for quality in ["Excellent Match", "Good Match", "Fair Match", "Possible Match"]:
            count = quality_counts.get(quality, 0)
            if count > 0:
                percentage = count / len(matches) * 100 if matches else 0
                print(f"  {quality}: {count} ({percentage:.1f}%)")
        
        print(f"✓ Successfully matched {len(matches)} products")
    except Exception as e:
        print(f"❌ Error matching products: {e}")
        return
    
    print()
    
    # Step 4: Generate Excel report
    print("STEP 4: Generating Excel Report")
    print("-" * 70)
    
    try:
        generator = ExcelGenerator(str(matches_json))
        generator.generate_excel(str(output_excel))
        print(f"✓ Excel report generated successfully!")
    except Exception as e:
        print(f"❌ Error generating Excel: {e}")
        return
    
    print()
    print("=" * 70)
    print("✓ PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print()
    print(f"Output file: {output_excel}")
    print()
    print("Summary:")
    print(f"  • Balflex products: {len(balflex_products)}")
    print(f"  • Heizmann products: {len(heizmann_products)}")
    print(f"  • Matched products: {len(matches)}")
    print()
    print("Next steps:")
    print("  1. Open the Excel file to review matches")
    print("  2. Verify high-confidence matches (Excellent/Good)")
    print("  3. Manually review Fair/Possible matches")
    print("  4. Share results with your employer")
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Process interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
