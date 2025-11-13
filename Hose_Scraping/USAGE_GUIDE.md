# Quick Start Guide

## Setup (First Time Only)

### 1. Install Python

Make sure Python 3.8+ is installed on your system.

### 2. Install Dependencies

Open PowerShell in this folder and run:

```powershell
pip install -r requirements.txt
```

### 3. Prepare Balflex Catalog

- Place your Balflex catalog TXT file in the `data/` folder
- Rename it to: `balflex_catalog.txt`

## Running the Tool

### Run Everything (Recommended)

```powershell
python main.py
```

This will:

1. Parse Balflex catalog
2. Scrape Heizmann website
3. Match products
4. Generate Excel report

### Run Individual Steps

If you need to run steps separately:

```powershell
# Step 1: Parse Balflex catalog only
python scripts/balflex_parser.py

# Step 2: Scrape Heizmann website only
python scripts/heizmann_scraper.py

# Step 3: Match products only
python scripts/product_matcher.py

# Step 4: Generate Excel only
python scripts/excel_generator.py
```

## Output

The final Excel file will be saved to:

```
output/product_comparison.xlsx
```

## Excel File Structure

### Sheet 1: Summary

- Total matches
- Match quality breakdown
- Category statistics

### Sheet 2: Product Comparison

Columns include:

- Match Score % (how confident the match is)
- Match Quality (Excellent/Good/Fair/Possible)
- Match Reasons (why these products match)
- Balflex Model, Reference, Article Number
- Heizmann Model, Reference, Article Number
- Technical specs (DN, pressure, standard, etc.)

## Understanding Match Quality

- **Excellent Match (80-100%)**: Very high confidence - likely the same product
- **Good Match (60-79%)**: High confidence - probably equivalent
- **Fair Match (40-59%)**: Moderate confidence - review manually
- **Possible Match (30-39%)**: Low confidence - verify carefully

## Troubleshooting

### "balflex_catalog.txt not found"

→ Make sure you placed the catalog file in the `data/` folder with the correct name

### "No module named 'requests'"

→ Run: `pip install -r requirements.txt`

### Website scraping fails

→ Check your internet connection
→ The website might be temporarily down - try again later

### No matches found

→ Make sure both Balflex and Heizmann data were extracted successfully
→ Check the JSON files in the `data/` folder

## Time Estimates

- Parsing Balflex catalog: ~10 seconds
- Scraping Heizmann website: ~2-5 minutes (depends on website speed)
- Matching products: ~30 seconds
- Generating Excel: ~5 seconds

**Total time: ~5-10 minutes**

## Tips for Best Results

1. **Review matches manually**: Don't rely solely on the match score
2. **Start with Excellent matches**: These are most likely correct
3. **Check technical specs**: Verify DN, pressure, and standards match
4. **Look for article numbers**: Sometimes products have direct equivalents
5. **Note construction differences**: 1-wire vs 2-wire braids matter

## Next Steps

After getting the Excel file:

1. Sort by "Match Score %" (highest first)
2. Review the top matches
3. Verify specifications match your needs
4. Contact suppliers for confirmation if needed
5. Share results with your employer

## Support

If you encounter issues:

1. Check the error message carefully
2. Try running individual steps to isolate the problem
3. Check the JSON files in `data/` to see what data was extracted
4. Make sure all dependencies are installed correctly
