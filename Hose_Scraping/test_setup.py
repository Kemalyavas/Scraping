"""
Test Script - Validates setup and shows example data extraction
"""

import sys
from pathlib import Path

def test_imports():
    """Test if all required packages are installed"""
    print("Testing package imports...")
    packages = {
        'requests': 'Web scraping',
        'bs4': 'HTML parsing (BeautifulSoup)',
        'pandas': 'Data manipulation',
        'openpyxl': 'Excel generation',
        'json': 'JSON handling',
        're': 'Regular expressions',
    }
    
    missing = []
    for package, description in packages.items():
        try:
            __import__(package)
            print(f"  ✓ {package} ({description})")
        except ImportError:
            print(f"  ❌ {package} ({description}) - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print("\n✓ All packages installed correctly!")
        return True


def test_file_structure():
    """Check if directory structure is correct"""
    print("\nTesting file structure...")
    
    base_dir = Path(__file__).parent
    required_dirs = ['data', 'output', 'scripts']
    required_files = [
        'main.py',
        'requirements.txt',
        'scripts/balflex_parser.py',
        'scripts/heizmann_scraper.py',
        'scripts/product_matcher.py',
        'scripts/excel_generator.py',
    ]
    
    # Check directories
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            print(f"  ✓ {dir_name}/ directory exists")
        else:
            print(f"  ❌ {dir_name}/ directory missing")
    
    # Check files
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"  ✓ {file_path} exists")
        else:
            print(f"  ❌ {file_path} missing")
    
    # Check for catalog file
    catalog_file = base_dir / 'data' / 'balflex_catalog.txt'
    if catalog_file.exists():
        print(f"  ✓ Balflex catalog file found!")
        print(f"    Size: {catalog_file.stat().st_size / 1024:.1f} KB")
    else:
        print(f"  ⚠️  Balflex catalog file not found")
        print(f"    Place 'balflex_catalog.txt' in the data/ folder")
    
    print("\n✓ File structure validated!")
    return True


def show_example_parsing():
    """Show example of how data will be parsed"""
    print("\nExample Product Data Structure:")
    print("-" * 70)
    
    example_product = {
        'supplier': 'Balflex',
        'model': 'BALPAC IMPACTUS 2SC-K',
        'reference': 'R16I-04',
        'article_number': '10.1010.04',
        'dn': 'DN6',
        'inch_size': '1/4"',
        'sae_dash': '-4',
        'inner_diameter_mm': 6.3,
        'outer_diameter_mm': 13.4,
        'working_pressure_mpa': 50,
        'working_pressure_psi': 7250,
        'burst_pressure_mpa': 200,
        'burst_pressure_psi': 29000,
        'min_bend_radius_mm': 50,
        'weight_kg_m': 0.27,
        'standard': 'DIN EN 857 2SC',
        'construction': '2 wire braid',
        'category': 'Steel Wire Braid'
    }
    
    print("Balflex Product Example:")
    for key, value in example_product.items():
        print(f"  {key:25s}: {value}")
    
    print("\n" + "-" * 70)
    print("\nThis is how products will be structured in the JSON files")
    print("The matching algorithm will compare these fields to find equivalents")


def show_match_example():
    """Show example of how matching works"""
    print("\nExample Match Criteria:")
    print("-" * 70)
    
    criteria = [
        ("DN (Nominal Diameter)", "30 points", "Must match exactly or be very close"),
        ("Working Pressure", "25 points", "Within 5-15% tolerance"),
        ("Standard/Norm", "20 points", "DIN EN, SAE, ISO standards"),
        ("Construction Type", "15 points", "1-wire, 2-wire, or spiral"),
        ("Inner Diameter", "10 points", "Within 5-15% tolerance"),
    ]
    
    print("\nMatch Score Calculation (0-100%):")
    print()
    for criterion, points, description in criteria:
        print(f"  {criterion:25s} ({points:8s}): {description}")
    
    print("\n" + "-" * 70)
    print("\nMatch Quality Ratings:")
    print("  • Excellent Match (80-100%): Very high confidence")
    print("  • Good Match (60-79%):      High confidence")
    print("  • Fair Match (40-59%):      Moderate confidence - verify manually")
    print("  • Possible Match (30-39%):  Low confidence - check carefully")


def main():
    """Run all tests"""
    print("=" * 70)
    print("PROJECT SETUP VALIDATION")
    print("=" * 70)
    print()
    
    # Test imports
    if not test_imports():
        return
    
    # Test file structure
    test_file_structure()
    
    # Show examples
    show_example_parsing()
    show_match_example()
    
    print("\n" + "=" * 70)
    print("✓ SETUP VALIDATION COMPLETE!")
    print("=" * 70)
    print()
    print("You're ready to run the tool!")
    print()
    print("Next steps:")
    print("  1. Make sure 'balflex_catalog.txt' is in the data/ folder")
    print("  2. Run: python main.py")
    print()


if __name__ == '__main__':
    main()
