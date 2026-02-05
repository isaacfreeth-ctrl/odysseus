#!/usr/bin/env python3
"""
UK Ministerial Gifts & Hospitality Search

Search the pre-built index of UK ministerial gifts and hospitality declarations.
Supports Boolean operators: AND, OR, NOT, quotes, parentheses.

Usage:
    from uk_gifts_search import search_gifts, search_hospitality
    
    # Search gifts by donor/gift description
    results = search_gifts("France")
    
    # Search hospitality by provider
    results = search_hospitality("Financial Times")
    
    # Boolean search
    results = search_gifts("UAE OR Qatar")
    results = search_hospitality("(BBC OR Sky) AND dinner")
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

# Import Boolean search support
try:
    from boolean_search import boolean_match, is_boolean_query
except ImportError:
    # Fallback to simple matching
    def boolean_match(query, text):
        return query.lower() in text.lower()
    def is_boolean_query(query):
        return False

# Index cache
_index_cache = {"data": None, "loaded": False}


def load_index():
    """Load the pre-built gifts index."""
    
    if _index_cache["loaded"]:
        return _index_cache["data"]
    
    # Try local file
    index_path = Path(__file__).parent / "uk_gifts_index.json"
    
    if index_path.exists():
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                _index_cache["data"] = json.load(f)
                _index_cache["loaded"] = True
                return _index_cache["data"]
        except Exception as e:
            print(f"Error loading index: {e}")
            return None
    
    return None


def search_gifts(
    search_term: str,
    minister: Optional[str] = None,
    department: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    received_only: bool = False,
    given_only: bool = False
) -> Dict:
    """
    Search UK ministerial gift declarations.
    
    Args:
        search_term: Search query for donor/recipient and gift description.
                     Supports Boolean operators: AND, OR, NOT, quotes.
        minister: Filter by minister name (partial match)
        department: Filter by department (partial match)
        date_from: Filter gifts from this date (YYYY-MM-DD)
        date_to: Filter gifts until this date (YYYY-MM-DD)
        received_only: Only show gifts received
        given_only: Only show gifts given
    
    Returns:
        Dict with matches, summary stats, and metadata
    """
    index = load_index()
    if not index:
        return {"error": "Index not loaded", "matches": []}
    
    gifts = index.get("gifts", [])
    use_boolean = is_boolean_query(search_term)
    search_lower = search_term.lower()
    
    matches = []
    
    for g in gifts:
        # Build searchable text
        searchable = f"{g.get('donor_recipient', '')} {g.get('gift', '')}"
        
        # Check main search term
        if use_boolean:
            if not boolean_match(search_term, searchable):
                continue
        else:
            if search_lower not in searchable.lower():
                continue
        
        # Apply filters
        if minister and minister.lower() not in g.get("minister", "").lower():
            continue
        
        if department and department.lower() not in g.get("department", "").lower():
            continue
        
        if received_only and "received" not in g.get("given_or_received", "").lower():
            continue
        
        if given_only and "given" not in g.get("given_or_received", "").lower():
            continue
        
        if date_from:
            gift_date = g.get("date", "")
            if gift_date and gift_date < date_from:
                continue
        
        if date_to:
            gift_date = g.get("date", "")
            if gift_date and gift_date > date_to:
                continue
        
        matches.append(g)
    
    # Sort by date (newest first)
    matches.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    # Build summary
    ministers = {}
    departments = {}
    for m in matches:
        min_name = m.get("minister", "Unknown")
        ministers[min_name] = ministers.get(min_name, 0) + 1
        
        dept = m.get("department", "Unknown")
        departments[dept] = departments.get(dept, 0) + 1
    
    return {
        "query": search_term,
        "match_count": len(matches),
        "matches": matches,
        "by_minister": ministers,
        "by_department": departments,
        "metadata": index.get("metadata", {})
    }


def search_hospitality(
    search_term: str,
    minister: Optional[str] = None,
    department: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> Dict:
    """
    Search UK ministerial hospitality declarations.
    
    Args:
        search_term: Search query for hospitality provider and type.
                     Supports Boolean operators: AND, OR, NOT, quotes.
        minister: Filter by minister name (partial match)
        department: Filter by department (partial match)
        date_from: Filter from this date (YYYY-MM-DD)
        date_to: Filter until this date (YYYY-MM-DD)
    
    Returns:
        Dict with matches, summary stats, and metadata
    """
    index = load_index()
    if not index:
        return {"error": "Index not loaded", "matches": []}
    
    hospitality = index.get("hospitality", [])
    use_boolean = is_boolean_query(search_term)
    search_lower = search_term.lower()
    
    matches = []
    
    for h in hospitality:
        # Build searchable text
        searchable = f"{h.get('provider', '')} {h.get('hospitality_type', '')}"
        
        # Check main search term
        if use_boolean:
            if not boolean_match(search_term, searchable):
                continue
        else:
            if search_lower not in searchable.lower():
                continue
        
        # Apply filters
        if minister and minister.lower() not in h.get("minister", "").lower():
            continue
        
        if department and department.lower() not in h.get("department", "").lower():
            continue
        
        if date_from:
            hosp_date = h.get("date", "")
            if hosp_date and hosp_date < date_from:
                continue
        
        if date_to:
            hosp_date = h.get("date", "")
            if hosp_date and hosp_date > date_to:
                continue
        
        matches.append(h)
    
    # Sort by date (newest first)
    matches.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    # Build summary
    ministers = {}
    providers = {}
    for m in matches:
        min_name = m.get("minister", "Unknown")
        ministers[min_name] = ministers.get(min_name, 0) + 1
        
        prov = m.get("provider", "Unknown")
        providers[prov] = providers.get(prov, 0) + 1
    
    return {
        "query": search_term,
        "match_count": len(matches),
        "matches": matches,
        "by_minister": ministers,
        "by_provider": providers,
        "metadata": index.get("metadata", {})
    }


def get_all_ministers() -> List[str]:
    """Get list of all ministers in the index."""
    index = load_index()
    if not index:
        return []
    
    ministers = set()
    for g in index.get("gifts", []):
        if g.get("minister"):
            ministers.add(g["minister"])
    for h in index.get("hospitality", []):
        if h.get("minister"):
            ministers.add(h["minister"])
    
    return sorted(list(ministers))


def get_all_departments() -> List[str]:
    """Get list of all departments in the index."""
    index = load_index()
    if not index:
        return []
    
    depts = set()
    for g in index.get("gifts", []):
        if g.get("department"):
            depts.add(g["department"])
    for h in index.get("hospitality", []):
        if h.get("department"):
            depts.add(h["department"])
    
    return sorted(list(depts))


def get_index_stats() -> Dict:
    """Get statistics about the index."""
    index = load_index()
    if not index:
        return {"error": "Index not loaded"}
    
    return {
        "gift_count": len(index.get("gifts", [])),
        "hospitality_count": len(index.get("hospitality", [])),
        "ministers": len(get_all_ministers()),
        "departments": len(get_all_departments()),
        "metadata": index.get("metadata", {})
    }


# CLI for testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python uk_gifts_search.py <search_term>")
        print("\nIndex stats:")
        stats = get_index_stats()
        print(f"  Gifts: {stats.get('gift_count', 0)}")
        print(f"  Hospitality: {stats.get('hospitality_count', 0)}")
        print(f"  Ministers: {stats.get('ministers', 0)}")
        print(f"  Departments: {stats.get('departments', 0)}")
        sys.exit(0)
    
    query = " ".join(sys.argv[1:])
    
    print(f"Searching for '{query}'...")
    print()
    
    # Search gifts
    gift_results = search_gifts(query)
    print(f"=== GIFTS ({gift_results['match_count']} matches) ===")
    for g in gift_results["matches"][:10]:
        print(f"  {g['date']} | {g['minister']} | {g.get('gift', 'N/A')} from {g.get('donor_recipient', 'N/A')}")
    
    print()
    
    # Search hospitality
    hosp_results = search_hospitality(query)
    print(f"=== HOSPITALITY ({hosp_results['match_count']} matches) ===")
    for h in hosp_results["matches"][:10]:
        print(f"  {h['date']} | {h['minister']} | {h.get('hospitality_type', 'N/A')} from {h.get('provider', 'N/A')}")
