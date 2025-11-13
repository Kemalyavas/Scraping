"""
Fittings Matcher - Compares Balflex and Heizmann fittings
Matches based on: thread type, dash size, connection type, dimensions
"""

import json
import re
from typing import List, Dict, Tuple
from difflib import SequenceMatcher


class FittingsMatcher:
    """Match fittings from Balflex and Heizmann based on specifications"""
    
    def __init__(self, balflex_file: str, heizmann_file: str):
        self.balflex_fittings = self._load_json(balflex_file)
        self.heizmann_fittings = self._load_json(heizmann_file)
        self.matches = []
        
    def _load_json(self, filepath: str) -> List[Dict]:
        """Load fittings from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def match(self) -> List[Dict]:
        """Find matches between Balflex and Heizmann fittings"""
        print(f"\nMatching {len(self.balflex_fittings)} Balflex fittings with {len(self.heizmann_fittings)} Heizmann fittings...")
        print("=" * 70)
        
        # Exclude non-fitting categories from Heizmann
        excluded_categories = [
            'Staub- & Gewindeschutz',  # Dust caps, not fittings
            'Hydraulik-Dichtungen',     # Seals/gaskets, not fittings  
            'Sortimente',               # Assortment kits
            'Rohrtechnik',              # Pipe/tube stock material
            'System WEO',               # Quick coupling system, not standard fittings
            'Messtechnik',              # Measurement equipment
        ]
        
        # Also exclude specific problematic models
        excluded_models = ['KLR', 'Schellen', 'Schelle']
        
        valid_heizmann = [
            f for f in self.heizmann_fittings 
            if f.get('category') not in excluded_categories
            and not any(excl in f.get('model', '') for excl in excluded_models)
        ]
        
        print(f"Filtering out non-fitting categories: {len(self.heizmann_fittings) - len(valid_heizmann)} excluded")
        print(f"Matching against {len(valid_heizmann)} valid Heizmann fittings")
        
        for bal_fitting in self.balflex_fittings:
            best_match = None
            best_score = 0
            
            for heiz_fitting in valid_heizmann:
                score = self._calculate_match_score(bal_fitting, heiz_fitting)
                
                if score > best_score and score >= 45:  # Minimum 45% match (thread+size required)
                    best_score = score
                    best_match = heiz_fitting
            
            if best_match:
                self.matches.append({
                    'balflex_reference': bal_fitting.get('reference', ''),
                    'balflex_category': bal_fitting.get('category', ''),
                    'balflex_dash_size': bal_fitting.get('dash_size', ''),
                    'balflex_hose_mm': bal_fitting.get('hose_size_mm', ''),
                    'balflex_hose_inch': bal_fitting.get('hose_size_inch', ''),
                    'balflex_thread': bal_fitting.get('thread_type', ''),
                    'balflex_connection': bal_fitting.get('connection_type', ''),
                    
                    'heizmann_article': best_match.get('article_number', ''),
                    'heizmann_category': best_match.get('category', ''),
                    'heizmann_size': best_match.get('size', ''),
                    'heizmann_dn': best_match.get('DN', ''),
                    'heizmann_thread': best_match.get('thread_type', ''),
                    'heizmann_connection': best_match.get('connection_type', ''),
                    'heizmann_material': best_match.get('material', ''),
                    
                    'match_score': round(best_score, 1),
                    'match_reason': self._get_match_reason(bal_fitting, best_match)
                })
        
        print(f"\n✓ Found {len(self.matches)} matches")
        return self.matches
    
    def _calculate_match_score(self, balflex: Dict, heizmann: Dict) -> float:
        """Calculate match score between two fittings (0-100)"""
        score = 0
        
        # Thread type matching (40 points) - MOST IMPORTANT
        if self._threads_match(balflex.get('thread_type', ''), heizmann.get('thread_type', '')):
            score += 40
        
        # Dash size / DN matching (30 points)
        if self._sizes_match(balflex, heizmann):
            score += 30
        
        # Hose size matching (15 points)
        if self._hose_sizes_match(balflex, heizmann):
            score += 15
        
        # Connection type matching (10 points) - Optional
        if self._connections_match(balflex.get('connection_type', ''), heizmann.get('connection_type', '')):
            score += 10
        
        # Category matching (5 points)
        if self._categories_match(balflex.get('category', ''), heizmann.get('category', '')):
            score += 5
        
        return score
    
    def _threads_match(self, balflex_thread: str, heizmann_thread: str) -> bool:
        """Check if thread types match"""
        if not balflex_thread or not heizmann_thread:
            return False
        
        bal = balflex_thread.upper()
        heiz = heizmann_thread.upper()
        
        # Exact match
        if bal == heiz:
            return True
        
        # Thread type equivalents
        thread_groups = [
            ['JIC', 'JIC 37', 'JIC 37°', 'SAE J514'],
            ['ORFS', 'O-RING FACE SEAL'],
            ['BSP', 'BSPP', 'BSPT', 'G'],
            ['NPT', 'NPTF'],
            ['METRIC', 'M', 'DIN'],
        ]
        
        for group in thread_groups:
            if any(t in bal for t in group) and any(t in heiz for t in group):
                return True
        
        # Size-based thread matching (e.g., "9/16-18 UNF" contains JIC info)
        if 'UNF' in heiz or 'UN' in heiz:
            if 'JIC' in bal:
                return True
        
        return False
    
    def _connections_match(self, balflex_conn: str, heizmann_conn: str) -> bool:
        """Check if connection types match"""
        if not balflex_conn or not heizmann_conn:
            return False
        
        bal = balflex_conn.upper()
        heiz = heizmann_conn.upper()
        
        # Exact match
        if bal == heiz:
            return True
        
        # Connection type equivalents
        conn_groups = [
            ['FERRULE', 'HOSE END', 'SLEEVE'],
            ['ELBOW', '90', 'BEND'],
            ['TEE', 'T', 'THREE-WAY'],
            ['ADAPTER', 'ADAPTOR', 'COUPLING'],
            ['FLANGE', 'FLANSCH'],
            ['STRAIGHT', 'STRIGHT', 'DIRECT'],
        ]
        
        for group in conn_groups:
            if any(c in bal for c in group) and any(c in heiz for c in group):
                return True
        
        return False
    
    def _sizes_match(self, balflex: Dict, heizmann: Dict) -> bool:
        """Check if sizes/DN match"""
        # Extract dash size from Balflex (e.g., "- 4" -> 4)
        bal_dash = balflex.get('dash_size', '')
        dash_num = None
        if bal_dash:
            match = re.search(r'-\s*(\d+)', bal_dash)
            if match:
                dash_num = int(match.group(1))
        
        # Extract DN from Heizmann (both 'DN' and 'dn' fields)
        heiz_dn = heizmann.get('DN', '') or heizmann.get('dn', '')
        dn_num = None
        if heiz_dn:
            match = re.search(r'DN\s*(\d+)', heiz_dn, re.IGNORECASE)
            if match:
                dn_num = int(match.group(1))
        
        # Dash to DN conversion (approximation)
        # -4 ≈ DN6, -6 ≈ DN10, -8 ≈ DN12, -10 ≈ DN16, -12 ≈ DN20
        dash_to_dn = {
            3: 5,
            4: 6,
            5: 8,
            6: 10,
            8: 12,
            10: 16,
            12: 20,
            16: 25,
            20: 32,
            24: 40,
            32: 50,
        }
        
        if dash_num and dn_num:
            expected_dn = dash_to_dn.get(dash_num)
            if expected_dn:
                # Allow ±2 tolerance
                return abs(expected_dn - dn_num) <= 2
        
        # Also check size field (e.g., "1/4"" in Heizmann)
        heiz_size = heizmann.get('size', '')
        bal_hose_inch = balflex.get('hose_size_inch', '')
        
        if heiz_size and bal_hose_inch:
            if heiz_size.strip().replace('"', '') == bal_hose_inch.strip().replace('"', ''):
                return True
        
        return False
    
    def _hose_sizes_match(self, balflex: Dict, heizmann: Dict) -> bool:
        """Check if hose sizes match"""
        bal_mm = balflex.get('hose_size_mm', '')
        bal_inch = balflex.get('hose_size_inch', '')
        heiz_size = heizmann.get('size', '')
        
        # Compare inch sizes
        if bal_inch and heiz_size:
            bal_clean = bal_inch.replace('"', '').replace(' ', '').strip()
            heiz_clean = heiz_size.replace('"', '').replace(' ', '').strip()
            if bal_clean == heiz_clean:
                return True
        
        return False
    
    def _categories_match(self, balflex_cat: str, heizmann_cat: str) -> bool:
        """Check if categories are compatible"""
        if not balflex_cat or not heizmann_cat:
            return False
        
        bal = balflex_cat.upper()
        heiz = heizmann_cat.upper()
        
        # Direct match
        if bal in heiz or heiz in bal:
            return True
        
        # Category similarities
        if 'FERRULE' in bal and ('FERRULE' in heiz or 'HOSE END' in heiz):
            return True
        if 'JIC' in bal and 'JIC' in heiz:
            return True
        if 'ORFS' in bal and 'ORFS' in heiz:
            return True
        if 'FLANGE' in bal and ('FLANGE' in heiz or 'FLANSCH' in heiz):
            return True
        
        return False
    
    def _get_match_reason(self, balflex: Dict, heizmann: Dict) -> str:
        """Generate human-readable match reason"""
        reasons = []
        
        if self._threads_match(balflex.get('thread_type', ''), heizmann.get('thread_type', '')):
            reasons.append(f"Thread: {balflex.get('thread_type', 'N/A')} ↔ {heizmann.get('thread_type', 'N/A')}")
        
        if self._connections_match(balflex.get('connection_type', ''), heizmann.get('connection_type', '')):
            reasons.append(f"Connection: {balflex.get('connection_type', 'N/A')} ↔ {heizmann.get('connection_type', 'N/A')}")
        
        if self._sizes_match(balflex, heizmann):
            reasons.append(f"Size: {balflex.get('dash_size', 'N/A')} ↔ {heizmann.get('DN', 'N/A')}")
        
        return " | ".join(reasons) if reasons else "General compatibility"
    
    def save_matches(self, output_file: str):
        """Save matches to JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.matches, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Saved matches to {output_file}")
    
    def generate_excel_report(self, output_file: str):
        """Generate Excel report of matches"""
        try:
            import pandas as pd
            
            if not self.matches:
                print("No matches to export")
                return
            
            # Create DataFrame
            df = pd.DataFrame(self.matches)
            
            # Reorder columns for better readability
            column_order = [
                'balflex_reference',
                'heizmann_article',
                'match_score',
                'balflex_category',
                'heizmann_category',
                'balflex_dash_size',
                'heizmann_dn',
                'balflex_hose_mm',
                'balflex_hose_inch',
                'heizmann_size',
                'balflex_thread',
                'heizmann_thread',
                'balflex_connection',
                'heizmann_connection',
                'heizmann_material',
                'match_reason'
            ]
            
            df = df[[col for col in column_order if col in df.columns]]
            
            # Sort by match score
            df = df.sort_values('match_score', ascending=False)
            
            # Save to Excel
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Fittings Matches', index=False)
                
                # Auto-adjust column widths
                worksheet = writer.sheets['Fittings Matches']
                for idx, col in enumerate(df.columns):
                    max_length = max(
                        df[col].astype(str).apply(len).max(),
                        len(col)
                    )
                    worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
            
            print(f"\n✓ Saved Excel report to {output_file}")
            print(f"  Total matches: {len(self.matches)}")
            print(f"  Average match score: {df['match_score'].mean():.1f}%")
            
        except ImportError:
            print("pandas and openpyxl required for Excel export")
            print("Install with: pip install pandas openpyxl")


if __name__ == "__main__":
    # Run matching
    matcher = FittingsMatcher(
        'data/balflex_fittings.json',
        'data/heizmann_fittings.json'
    )
    
    matches = matcher.match()
    
    # Save results
    matcher.save_matches('data/fittings_matches.json')
    matcher.generate_excel_report('data/fittings_comparison.xlsx')
    
    print("\n" + "=" * 70)
    print("Matching complete!")
    print("=" * 70)
