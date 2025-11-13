# Hydraulic Hose Product Comparison Tool

## Project Overview

This tool extracts, compares, and matches hydraulic hose products from two suppliers:

- **Balflex**: Data from PDF catalogs
- **Heizmann**: Data from website (https://www.heizmann.ch)

## Purpose

Find equivalent products between suppliers based on technical specifications like:

- Nominal diameter (DN)
- Pressure rating (MPa/bar/PSI)
- Standards compliance (DIN EN, SAE, ISO)
- Construction type (wire braid count)
- Temperature range

## Project Structure

```
Project_Scraping/
├── data/
│   ├── balflex_catalog.txt          # Source catalog data
│   ├── balflex_products.json        # Parsed Balflex products
│   └── heizmann_products.json       # Scraped Heizmann products
├── output/
│   └── product_comparison.xlsx      # Final comparison Excel
├── scripts/
│   ├── balflex_parser.py           # Parse Balflex catalog
│   ├── heizmann_scraper.py         # Scrape Heizmann website
│   ├── product_matcher.py          # Match products
│   └── excel_generator.py          # Generate Excel report
├── requirements.txt
└── main.py                         # Main execution script
```

## Setup Instructions

1. Install Python dependencies: `pip install -r requirements.txt`
2. Place Balflex catalog TXT file in `data/` folder
3. Run: `python main.py`

## Output

Excel file with columns:

- Balflex Model
- Balflex Article Number
- Heizmann Model
- Heizmann Article Number
- DN (Diameter)
- Pressure Rating
- Standard/Norm
- Construction Type
- Match Confidence (%)
- Notes

## Timeline Estimate

- Hoses comparison: 2-3 days
- Fittings (future): 3-4 days
