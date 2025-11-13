"""
Product Matcher
Compares and matches hydraulic hose products from Balflex and Heizmann
based on technical specifications
"""

import json
import re
from typing import List, Dict, Any, Tuple
from pathlib import Path


class ProductMatcher:
    """Match products from two suppliers based on specifications"""
    
    def __init__(self, balflex_file: str, heizmann_file: str):
        self.balflex_products = self._load_json(balflex_file)
        self.heizmann_products = self._load_json(heizmann_file)
        self.matches = []
    
    def _load_json(self, file_path: str) -> List[Dict]:
        """Load products from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {file_path} not found, returning empty list")
            return []
    
    def match_products(self) -> List[Dict[str, Any]]:
        """Find matching products between suppliers"""
        print("Starting product matching...")
        
        for balflex in self.balflex_products:
            best_match = None
            best_score = 0
            
            for heizmann in self.heizmann_products:
                score, reasons = self._calculate_match_score(balflex, heizmann)
                
                if score > best_score:
                    best_score = score
                    best_match = heizmann
                    best_reasons = reasons
            
            # Only include matches with score > 30% (reasonable threshold)
            if best_match and best_score >= 30:
                match = self._create_match_entry(balflex, best_match, best_score, best_reasons)
                self.matches.append(match)
        
        print(f"Found {len(self.matches)} product matches")
        return self.matches
    
    def _calculate_match_score(self, balflex: Dict, heizmann: Dict) -> Tuple[float, List[str]]:
        """
        Calculate match score (0-100) based on multiple criteria
        Returns: (score, list of matching reasons)
        """
        score = 0
        max_score = 0
        reasons = []
        
        # CRITICAL PRE-CHECK: Construction type compatibility
        # Textile hoses CANNOT match with steel wire hoses!
        balflex_const = balflex.get('construction', '').lower()
        heizmann_const = heizmann.get('construction', '').lower()
        
        # Reject incompatible construction types
        if balflex_const and heizmann_const:
            # Textile vs Wire = INCOMPATIBLE
            if ('textile' in balflex_const and 'wire' in heizmann_const):
                return 0, ["Construction mismatch: textile vs wire - INCOMPATIBLE"]
            
            if ('wire' in balflex_const and 'textile' in heizmann_const):
                return 0, ["Construction mismatch: wire vs textile - INCOMPATIBLE"]
            
            # Spiral vs non-spiral should be very low match
            if ('spiral' in balflex_const) != ('spiral' in heizmann_const):
                return 0, ["Construction mismatch: spiral vs non-spiral - INCOMPATIBLE"]
        
        # 1. DN (Nominal Diameter) - Most important (30 points)
        max_score += 30
        if balflex.get('dn') and heizmann.get('dn'):
            if balflex['dn'] == heizmann['dn']:
                score += 30
                reasons.append(f"DN match: {balflex['dn']}")
            # Partial match if DN numbers are close
            else:
                balflex_dn = int(balflex['dn'].replace('DN', ''))
                heizmann_dn = int(heizmann['dn'].replace('DN', ''))
                if abs(balflex_dn - heizmann_dn) <= 2:
                    score += 15
                    reasons.append(f"DN close: {balflex['dn']} ≈ {heizmann['dn']}")
        
        # 2. Working Pressure (25 points)
        max_score += 25
        balflex_pressure = balflex.get('working_pressure_mpa') or balflex.get('working_pressure_bar')
        heizmann_pressure = heizmann.get('working_pressure_mpa') or heizmann.get('working_pressure_bar')
        
        if balflex_pressure and heizmann_pressure:
            # Convert both to MPa for comparison
            # Balflex uses MPa, Heizmann uses bar
            # 1 MPa = 10 bar
            if 'working_pressure_bar' in balflex:
                balflex_pressure_mpa = balflex_pressure / 10.0
            else:
                balflex_pressure_mpa = balflex_pressure
            
            if 'working_pressure_bar' in heizmann:
                heizmann_pressure_mpa = heizmann_pressure / 10.0
            else:
                heizmann_pressure_mpa = heizmann_pressure
            
            pressure_diff_percent = abs(balflex_pressure_mpa - heizmann_pressure_mpa) / max(balflex_pressure_mpa, heizmann_pressure_mpa) * 100
            
            if pressure_diff_percent <= 5:
                score += 25
                reasons.append(f"Pressure match: {balflex_pressure_mpa:.1f} MPa ≈ {heizmann_pressure_mpa:.1f} MPa")
            elif pressure_diff_percent <= 15:
                score += 15
                reasons.append(f"Pressure similar: {balflex_pressure_mpa:.1f} MPa ≈ {heizmann_pressure_mpa:.1f} MPa")
            elif pressure_diff_percent <= 30:
                score += 8
        
        # 3. Standard/Norm (20 points) - FIXED: Compare EN numbers precisely
        max_score += 20
        balflex_std = balflex.get('standard', '').upper()
        heizmann_std = heizmann.get('standard', '').upper()
        
        if balflex_std and heizmann_std:
            # Extract EN standard numbers (853, 854, 856, 857)
            # EN 853 = Steel wire braid (1SN, 2SN)
            # EN 854 = Textile braid (1TE, 2TE, 3TE)
            # EN 856 = Spiral wire
            # EN 857 = Compact steel wire (1SC, 2SC)
            balflex_en_num = re.search(r'EN\s*(\d{3})', balflex_std)
            heizmann_en_num = re.search(r'EN\s*(\d{3})', heizmann_std)
            
            # Extract SAE numbers (R1, R2, R3, etc.)
            balflex_sae = re.search(r'SAE\s*\d+R(\d+)', balflex_std)
            heizmann_sae = re.search(r'SAE\s*\d+R(\d+)', heizmann_std)
            
            matched = False
            
            # Compare EN numbers precisely
            if balflex_en_num and heizmann_en_num:
                balflex_num = balflex_en_num.group(1)  # "857"
                heizmann_num = heizmann_en_num.group(1)  # "854"
                
                if balflex_num == heizmann_num:
                    score += 20
                    reasons.append(f"Standard match: EN {balflex_num}")
                    matched = True
                # EN 853 and EN 857 are both steel wire (some compatibility)
                elif (balflex_num in ['853', '857'] and heizmann_num in ['853', '857']):
                    score += 10
                    reasons.append(f"Standard compatible: EN {balflex_num} / EN {heizmann_num}")
                    matched = True
            
            # Compare SAE numbers precisely
            elif balflex_sae and heizmann_sae:
                balflex_sae_num = balflex_sae.group(1)
                heizmann_sae_num = heizmann_sae.group(1)
                
                if balflex_sae_num == heizmann_sae_num:
                    score += 20
                    reasons.append(f"Standard match: SAE 100R{balflex_sae_num}")
                    matched = True
            
            # Fallback: old method for other standards
            if not matched:
                balflex_std_clean = self._extract_standard_code(balflex_std)
                heizmann_std_clean = self._extract_standard_code(heizmann_std)
                
                if balflex_std_clean == heizmann_std_clean:
                    score += 20
                    reasons.append(f"Standard match: {balflex_std_clean}")
                elif balflex_std_clean in heizmann_std_clean or heizmann_std_clean in balflex_std_clean:
                    score += 10
                    reasons.append(f"Standard similar: {balflex_std_clean} / {heizmann_std_clean}")
        
        # 4. Construction type (15 points)
        max_score += 15
        balflex_const = balflex.get('construction', '').lower()
        heizmann_const = heizmann.get('construction', '').lower()
        
        if balflex_const and heizmann_const:
            # Check wire braid count
            if balflex_const == heizmann_const:
                score += 15
                reasons.append(f"Construction match: {balflex_const}")
            elif ('1 wire' in balflex_const and '1 wire' in heizmann_const) or \
                 ('2 wire' in balflex_const and '2 wire' in heizmann_const) or \
                 ('spiral' in balflex_const and 'spiral' in heizmann_const):
                score += 12
                reasons.append(f"Construction similar")
        
        # 5. Inner Diameter (10 points)
        max_score += 10
        if balflex.get('inner_diameter_mm') and heizmann.get('inner_diameter_mm'):
            dia_diff_percent = abs(balflex['inner_diameter_mm'] - heizmann['inner_diameter_mm']) / \
                              max(balflex['inner_diameter_mm'], heizmann['inner_diameter_mm']) * 100
            
            if dia_diff_percent <= 5:
                score += 10
                reasons.append(f"Inner diameter match")
            elif dia_diff_percent <= 15:
                score += 5
        
        # Normalize score to 0-100
        if max_score > 0:
            normalized_score = (score / max_score) * 100
        else:
            normalized_score = 0
        
        return normalized_score, reasons
    
    def _extract_standard_code(self, standard: str) -> str:
        """Extract clean standard code (e.g., 'DIN EN 857' from 'DIN EN 857 2SC')"""
        import re
        # Extract DIN EN XXX or SAE XXXRXX patterns
        patterns = [
            r'DIN\s*EN\s*\d+',
            r'SAE\s*\d+R\d+',
            r'EN\s*\d+',
            r'ISO\s*\d+',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, standard, re.IGNORECASE)
            if match:
                return match.group(0).replace(' ', '')
        
        return standard
    
    def _create_match_entry(self, balflex: Dict, heizmann: Dict, score: float, reasons: List[str]) -> Dict:
        """Create a match entry with relevant information"""
        return {
            'match_score': round(score, 1),
            'match_quality': self._score_to_quality(score),
            'match_reasons': ', '.join(reasons),
            
            # Balflex info
            'balflex_model': balflex.get('model', ''),
            'balflex_reference': balflex.get('reference', ''),
            'balflex_article_number': balflex.get('article_number', ''),
            'balflex_category': balflex.get('category', ''),
            
            # Heizmann info
            'heizmann_model': heizmann.get('model', ''),
            'heizmann_reference': heizmann.get('reference', ''),
            'heizmann_article_number': heizmann.get('article_number', ''),
            'heizmann_category': heizmann.get('category', ''),
            
            # Shared specs
            'dn': balflex.get('dn', '') or heizmann.get('dn', ''),
            'inch_size': balflex.get('inch_size', '') or heizmann.get('inch_size', ''),
            'working_pressure_mpa': balflex.get('working_pressure_mpa', heizmann.get('working_pressure_mpa', '')),
            'working_pressure_bar': balflex.get('working_pressure_bar', heizmann.get('working_pressure_bar', '')),
            'working_pressure_psi': balflex.get('working_pressure_psi', heizmann.get('working_pressure_psi', '')),
            'standard': balflex.get('standard', '') or heizmann.get('standard', ''),
            'construction': balflex.get('construction', '') or heizmann.get('construction', ''),
            
            # Individual specs for comparison
            'balflex_inner_diameter_mm': balflex.get('inner_diameter_mm', ''),
            'heizmann_inner_diameter_mm': heizmann.get('inner_diameter_mm', ''),
            'balflex_outer_diameter_mm': balflex.get('outer_diameter_mm', ''),
            'heizmann_outer_diameter_mm': heizmann.get('outer_diameter_mm', ''),
        }
    
    def _score_to_quality(self, score: float) -> str:
        """Convert numerical score to quality rating"""
        if score >= 80:
            return "Excellent Match"
        elif score >= 60:
            return "Good Match"
        elif score >= 40:
            return "Fair Match"
        else:
            return "Possible Match"
    
    def save_to_json(self, output_file: str):
        """Save matches to JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.matches, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(self.matches)} matches to {output_file}")


def main():
    """Test the matcher"""
    data_dir = Path(__file__).parent.parent / 'data'
    balflex_file = data_dir / 'balflex_products.json'
    heizmann_file = data_dir / 'heizmann_products.json'
    output_file = data_dir / 'product_matches.json'
    
    if not balflex_file.exists():
        print(f"Error: {balflex_file} not found!")
        print("Run balflex_parser.py first")
        return
    
    if not heizmann_file.exists():
        print(f"Error: {heizmann_file} not found!")
        print("Run heizmann_scraper.py first")
        return
    
    matcher = ProductMatcher(str(balflex_file), str(heizmann_file))
    matches = matcher.match_products()
    matcher.save_to_json(str(output_file))
    
    # Show summary
    print(f"\n=== Matching Summary ===")
    print(f"Total matches found: {len(matches)}")
    
    # Group by quality
    quality_counts = {}
    for match in matches:
        quality = match['match_quality']
        quality_counts[quality] = quality_counts.get(quality, 0) + 1
    
    print("\nMatches by quality:")
    for quality in ["Excellent Match", "Good Match", "Fair Match", "Possible Match"]:
        count = quality_counts.get(quality, 0)
        if count > 0:
            print(f"  {quality}: {count}")


if __name__ == '__main__':
    main()
