#!/usr/bin/env python3
"""
UK Ministerial Gifts & Hospitality Search

Search the pre-built index of ministerial gifts and hospitality declarations.
Supports Boolean search operators: AND, OR, NOT, quotes, parentheses.

Usage:
    from uk_gifts_core import search_uk_gifts, search_uk_hospitality
    
    # Search gifts
    results = search_uk_gifts("UAE")
    
    # Search hospitality  
    results = search_uk_hospitality("Financial Times")
    
    # Boolean search
    results = search_uk_gifts("France OR Germany")
    results = search_uk_hospitality("(BBC OR Sky) AND dinner")
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Try to import boolean search
try:
    from boolean_search import boolean_match, is_boolean_query
    BOOLEAN_AVAILABLE = True
except ImportError:
    BOOLEAN_AVAILABLE = False
    def is_boolean_query(q): return False
    def boolean_match(q, t): return q.lower() in t.lower()


# Cache for loaded index
_gifts_index_cache = {"data": None, "loaded": False}

# Remote URL for index (update with your GitHub raw URL)
UK_GIFTS_INDEX_URL = "https://raw.githubusercontent.com/IsaacFigworthy/telemachus/main/uk_gifts_index.json"


def load_gifts_index():
    """Load the pre-built UK gifts index."""
    
    if _gifts_index_cache["loaded"]:
        return _gifts_index_cache["data"]
    
    # Try local file first
    local_path = Path(__file__).parent / "uk_gifts_index.json"
    
    if local_path.exists():
        try:
            with open(local_path, 'r', encoding='utf-8') as f:
                _gifts_index_cache["data"] = json.load(f)
                _gifts_index_cache["loaded"] = True
                print(f"  Loaded UK gifts index ({_gifts_index_cache['data']['metadata']['gift_count']} gifts, "
                      f"{_gifts_index_cache['data']['metadata']['hospitality_count']} hospitality)")
                return _gifts_index_cache["data"]
        except Exception as e:
            print(f"  Error loading local index: {e}")
    
    # Try remote URL
    try:
        import requests
        response = requests.get(UK_GIFTS_INDEX_URL, timeout=30)
        response.raise_for_status()
        _gifts_index_cache["data"] = response.json()
        _gifts_index_cache["loaded"] = True
        print(f"  Loaded UK gifts index from remote")
        return _gifts_index_cache["data"]
    except Exception as e:
        print(f"  Could not load UK gifts index: {e}")
        return None


def search_uk_gifts(search_term: str, minister: str = None) -> dict:
    """
    Search UK ministerial gift declarations.
    
    Args:
        search_term: Donor name, gift description, or country to search for.
                     Supports Boolean operators: AND, OR, NOT, quotes, parentheses.
        minister: Optional - filter to specific minister
    
    Returns:
        dict with matching gifts, counts, and summary
        
    Examples:
        search_uk_gifts("UAE")
        search_uk_gifts("France OR Germany")
        search_uk_gifts("President", minister="Sir Keir Starmer")
    """
    print(f"Searching UK gifts for '{search_term}'...")
    
    index = load_gifts_index()
    if not index:
        return None
    
    use_boolean = BOOLEAN_AVAILABLE and is_boolean_query(search_term)
    search_lower = search_term.lower()
    
    matches = []
    
    for gift in index["gifts"]:
        # Build searchable text from donor and gift description
        searchable = f"{gift.get('donor_recipient', '')} {gift.get('gift', '')}".lower()
        
        # Check if matches query
        if use_boolean:
            if not boolean_match(search_term, searchable):
                continue
        else:
            if search_lower not in searchable:
                continue
        
        # Filter by minister if specified
        if minister and minister.lower() not in gift.get("minister", "").lower():
            continue
        
        matches.append(gift)
    
    # Build summary
    ministers = defaultdict(int)
    departments = defaultdict(int)
    
    for m in matches:
        ministers[m.get("minister", "Unknown")] += 1
        departments[m.get("department", "Unknown")] += 1
    
    result = {
        "search_term": search_term,
        "match_count": len(matches),
        "gifts": matches,
        "by_minister": dict(ministers),
        "by_department": dict(departments),
        "coverage": index["metadata"].get("coverage", "Unknown"),
        "index_created": index["metadata"].get("created", "Unknown")
    }
    
    print(f"  Found {len(matches)} matching gifts")
    
    return result


def search_uk_hospitality(search_term: str, minister: str = None) -> dict:
    """
    Search UK ministerial hospitality declarations.
    
    Args:
        search_term: Provider name or hospitality type to search for.
                     Supports Boolean operators: AND, OR, NOT, quotes, parentheses.
        minister: Optional - filter to specific minister
    
    Returns:
        dict with matching hospitality records, counts, and summary
        
    Examples:
        search_uk_hospitality("Financial Times")
        search_uk_hospitality("BBC OR Sky")
        search_uk_hospitality("dinner", minister="Jonathan Reynolds")
    """
    print(f"Searching UK hospitality for '{search_term}'...")
    
    index = load_gifts_index()
    if not index:
        return None
    
    use_boolean = BOOLEAN_AVAILABLE and is_boolean_query(search_term)
    search_lower = search_term.lower()
    
    matches = []
    
    for hosp in index["hospitality"]:
        # Build searchable text from provider and hospitality type
        searchable = f"{hosp.get('provider', '')} {hosp.get('hospitality_type', '')}".lower()
        
        # Check if matches query
        if use_boolean:
            if not boolean_match(search_term, searchable):
                continue
        else:
            if search_lower not in searchable:
                continue
        
        # Filter by minister if specified
        if minister and minister.lower() not in hosp.get("minister", "").lower():
            continue
        
        matches.append(hosp)
    
    # Build summary
    ministers = defaultdict(int)
    departments = defaultdict(int)
    providers = defaultdict(int)
    
    for m in matches:
        ministers[m.get("minister", "Unknown")] += 1
        departments[m.get("department", "Unknown")] += 1
        providers[m.get("provider", "Unknown")] += 1
    
    result = {
        "search_term": search_term,
        "match_count": len(matches),
        "hospitality": matches,
        "by_minister": dict(ministers),
        "by_department": dict(departments),
        "by_provider": dict(providers),
        "coverage": index["metadata"].get("coverage", "Unknown"),
        "index_created": index["metadata"].get("created", "Unknown")
    }
    
    print(f"  Found {len(matches)} matching hospitality records")
    
    return result


def search_uk_gifts_and_hospitality(search_term: str, minister: str = None) -> dict:
    """
    Search both gifts and hospitality together.
    
    Useful for finding all transparency declarations involving a specific 
    organisation or individual.
    """
    gifts = search_uk_gifts(search_term, minister)
    hospitality = search_uk_hospitality(search_term, minister)
    
    return {
        "search_term": search_term,
        "gifts": gifts,
        "hospitality": hospitality,
        "total_matches": (gifts["match_count"] if gifts else 0) + 
                        (hospitality["match_count"] if hospitality else 0)
    }


def get_minister_gifts(minister_name: str) -> dict:
    """Get all gifts for a specific minister."""
    
    index = load_gifts_index()
    if not index:
        return None
    
    minister_lower = minister_name.lower()
    
    gifts = [g for g in index["gifts"] 
             if minister_lower in g.get("minister", "").lower()]
    
    hospitality = [h for h in index["hospitality"]
                   if minister_lower in h.get("minister", "").lower()]
    
    return {
        "minister": minister_name,
        "gift_count": len(gifts),
        "hospitality_count": len(hospitality),
        "gifts": gifts,
        "hospitality": hospitality
    }


def get_gifts_summary() -> dict:
    """Get overall summary of the gifts index."""
    
    index = load_gifts_index()
    if not index:
        return None
    
    # Count by minister
    gift_by_minister = defaultdict(int)
    hosp_by_minister = defaultdict(int)
    
    for g in index["gifts"]:
        gift_by_minister[g.get("minister", "Unknown")] += 1
    
    for h in index["hospitality"]:
        hosp_by_minister[h.get("minister", "Unknown")] += 1
    
    return {
        "total_gifts": index["metadata"]["gift_count"],
        "total_hospitality": index["metadata"]["hospitality_count"],
        "coverage": index["metadata"]["coverage"],
        "index_created": index["metadata"]["created"],
        "gifts_by_minister": dict(gift_by_minister),
        "hospitality_by_minister": dict(hosp_by_minister)
    }


# Test
if __name__ == "__main__":
    print("Testing UK Gifts Search")
    print("=" * 50)
    
    # Test gift search
    print("\n1. Searching gifts for 'UAE'...")
    results = search_uk_gifts("UAE")
    if results:
        for g in results["gifts"][:3]:
            print(f"  • {g['minister']}: {g.get('gift', 'N/A')} from {g.get('donor_recipient', 'N/A')}")
    
    # Test hospitality search
    print("\n2. Searching hospitality for 'Financial Times'...")
    results = search_uk_hospitality("Financial Times")
    if results:
        for h in results["hospitality"][:3]:
            print(f"  • {h['minister']}: {h.get('hospitality_type', 'N/A')} from {h.get('provider', 'N/A')}")
    
    # Test minister lookup
    print("\n3. Getting all gifts for Keir Starmer...")
    results = get_minister_gifts("Keir Starmer")
    if results:
        print(f"  Gifts: {results['gift_count']}, Hospitality: {results['hospitality_count']}")
    
    # Summary
    print("\n4. Index summary...")
    summary = get_gifts_summary()
    if summary:
        print(f"  Total gifts: {summary['total_gifts']}")
        print(f"  Total hospitality: {summary['total_hospitality']}")
        print(f"  Coverage: {summary['coverage']}")
