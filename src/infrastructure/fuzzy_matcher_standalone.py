"""
Standalone fuzzy matching utilities for data deduplication (without AWS Glue dependencies).
"""
import re
from typing import Dict, List, Any, Optional
from fuzzywuzzy import fuzz, process
import pandas as pd


class FuzzyMatcher:
    """Fuzzy matching utilities for data deduplication."""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
    
    def normalize_string(self, text: str) -> str:
        """Normalize string for better matching."""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove common prefixes/suffixes
        text = re.sub(r'^(the|a|an)\s+', '', text)
        text = re.sub(r'\s+(inc|llc|ltd|corp|corporation)\.?$', '', text)
        
        # Remove special characters and extra spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity score between two strings."""
        if not str1 or not str2:
            return 0.0
        
        # Normalize strings
        norm_str1 = self.normalize_string(str1)
        norm_str2 = self.normalize_string(str2)
        
        # Use multiple similarity metrics and take the maximum
        ratio = fuzz.ratio(norm_str1, norm_str2)
        partial_ratio = fuzz.partial_ratio(norm_str1, norm_str2)
        token_sort_ratio = fuzz.token_sort_ratio(norm_str1, norm_str2)
        token_set_ratio = fuzz.token_set_ratio(norm_str1, norm_str2)
        
        return max(ratio, partial_ratio, token_sort_ratio, token_set_ratio) / 100.0
    
    def find_duplicates(self, df: pd.DataFrame, match_columns: List[str], id_column: str) -> pd.DataFrame:
        """Find potential duplicate records using fuzzy matching."""
        # Convert to Pandas for fuzzy matching (for smaller datasets)
        pandas_df = df.copy()
        
        duplicates = []
        processed_ids = set()
        
        for i, row1 in pandas_df.iterrows():
            if row1[id_column] in processed_ids:
                continue
                
            matches = [row1[id_column]]
            
            for j, row2 in pandas_df.iterrows():
                if i >= j or row2[id_column] in processed_ids:
                    continue
                
                # Calculate similarity across all match columns
                similarities = []
                for col in match_columns:
                    if col in pandas_df.columns:
                        sim = self.calculate_similarity(str(row1[col]), str(row2[col]))
                        similarities.append(sim)
                
                if similarities and max(similarities) >= self.similarity_threshold:
                    matches.append(row2[id_column])
            
            if len(matches) > 1:
                # Mark all but the first as duplicates
                for match_id in matches[1:]:
                    duplicates.append({
                        'duplicate_id': match_id,
                        'master_id': matches[0],
                        'similarity_score': max(similarities) if similarities else 0.0,
                        'match_columns': match_columns
                    })
                    processed_ids.add(match_id)
            
            processed_ids.add(row1[id_column])
        
        # Convert back to DataFrame
        if duplicates:
            return pd.DataFrame(duplicates)
        else:
            # Return empty DataFrame with correct schema
            return pd.DataFrame(columns=['duplicate_id', 'master_id', 'similarity_score', 'match_columns'])