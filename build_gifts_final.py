#!/usr/bin/env python3
"""
UK Ministerial Gifts & Hospitality Index Builder - Optimized Version

Builds index incrementally, saving after each month to avoid timeout.
"""

import json
import csv
import io
import requests
from pathlib import Path
from datetime import datetime
from collections import defaultdict

GOVUK_CONTENT_URL = "https://www.gov.uk/api/content"
OUTPUT_PATH = Path(__file__).parent / "uk_gifts_index.json"

# Monthly register publication paths - order matters for incremental processing
REGISTER_PATHS = [
    ("/government/publications/register-of-ministers-gifts-and-hospitality-november-2024", "November 2024"),
    ("/government/publications/register-of-ministers-gifts-and-hospitality-december-2024", "December 2024"),
    ("/government/publications/register-of-ministers-gifts-and-hospitality-january-2025", "January 2025"),
    ("/government/publications/register-of-ministers-gifts-and-hospitality-february-2025", "February 2025"),
    ("/government/publications/register-of-ministers-gifts-and-hospitality-march-2025", "March 2025"),
    ("/government/publications/register-of-ministers-gifts-and-hospitality-april-2025", "April 2025"),
    ("/government/publications/register-of-ministers-gifts-and-hospitality-may-2025", "May 2025"),
    ("/government/publications/register-of-ministers-gifts-and-hospitality-june-2025", "June 2025"),
    ("/government/publications/register-of-ministers-gifts-and-hospitality-july-2025", "July 2025"),
    ("/government/publications/register-of-ministers-gifts-and-hospitality-august-2025", "August 2025"),
    ("/government/publications/register-of-ministers-gifts-and-hospitality-september-2025", "September 2025"),
    ("/government/publications/register-of-ministers-gifts-and-hospitality-october-2025", "October 2025"),
    ("/government/publications/register-of-ministers-gifts-and-hospitality-november-2025", "November 2025"),
    ("/government/publications/register-of-ministers-gifts-and-hospitality-december-2025", "December 2025"),
]


def get_csv_urls(pub_path):
    """Get CSV URLs from a register publication."""
    url = f"{GOVUK_CONTENT_URL}{pub_path}"
    
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 404:
            return []
        response.raise_for_status()
        data = response.json()
    except:
        return []
    
    csv_urls = []
    for att in data.get("details", {}).get("attachments", []):
        att_url = att.get("url", "")
        att_title = att.get("title", "").lower()
        
        if ".csv" not in att_url.lower():
            continue
        
        if att_url.startswith("/"):
            att_url = "https://www.gov.uk" + att_url
        
        url_lower = att_url.lower()
        
        if "gift" in att_title or "gift" in url_lower:
            csv_urls.append((att_url, "gift"))
        elif "hospitality" in att_title or "hospitality" in url_lower:
            csv_urls.append((att_url, "hospitality"))
    
    return csv_urls


def parse_csv(url, data_type):
    """Parse a gift or hospitality CSV."""
    records = []
    
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        content = response.content.decode('utf-8-sig', errors='replace')
        
        for row in csv.DictReader(io.StringIO(content)):
            r = {k.lower().strip(): (v.strip() if v else "") for k, v in row.items() if k}
            
            minister = r.get("minister", "")
            if not minister or minister.lower() == "nil return":
                continue
            
            if data_type == "gift":
                records.append({
                    "type": "gift",
                    "department": r.get("department", ""),
                    "minister": minister,
                    "date": r.get("date", ""),
                    "gift": r.get("gift", ""),
                    "given_or_received": r.get("given or received", ""),
                    "donor_recipient": r.get("who gift was given to or received from", ""),
                    "value": r.get("value (£)", "") or r.get("value", ""),
                    "outcome": r.get("outcome (received gifts only)", "")
                })
            else:
                records.append({
                    "type": "hospitality",
                    "department": r.get("department", ""),
                    "minister": minister,
                    "date": r.get("date", ""),
                    "provider": r.get("individual or organisation that offered hospitality", ""),
                    "hospitality_type": r.get("type of hospitality received", ""),
                    "accompanied": r.get("accompanied by guest", ""),
                    "value": r.get("value of hospitality (£)", "")
                })
    except:
        pass
    
    return records


def build_indexes(gifts, hospitality):
    """Build search indexes."""
    donor_idx = defaultdict(list)
    for i, g in enumerate(gifts):
        text = f"{g.get('donor_recipient', '')} {g.get('gift', '')}".lower()
        for word in text.split():
            if len(word) > 2 and word.isalpha():
                donor_idx[word].append(i)
    
    provider_idx = defaultdict(list)
    for i, h in enumerate(hospitality):
        text = f"{h.get('provider', '')}".lower()
        for word in text.split():
            if len(word) > 2 and word.isalpha():
                provider_idx[word].append(i)
    
    return dict(donor_idx), dict(provider_idx)


def main():
    print("Building UK Gifts & Hospitality Index")
    print("=" * 50)
    
    all_gifts = []
    all_hospitality = []
    seen_gifts = set()
    seen_hosp = set()
    months_processed = []
    
    for pub_path, month_name in REGISTER_PATHS:
        print(f"\n{month_name}...", end=" ", flush=True)
        
        csv_urls = get_csv_urls(pub_path)
        if not csv_urls:
            print("not found")
            continue
        
        month_gifts = 0
        month_hosp = 0
        
        for csv_url, data_type in csv_urls:
            records = parse_csv(csv_url, data_type)
            
            for r in records:
                r["source_month"] = month_name
                
                if data_type == "gift":
                    key = (r["minister"], r["date"], r.get("gift", ""), r.get("donor_recipient", ""))
                    if key not in seen_gifts:
                        seen_gifts.add(key)
                        all_gifts.append(r)
                        month_gifts += 1
                else:
                    key = (r["minister"], r["date"], r.get("provider", ""), r.get("hospitality_type", ""))
                    if key not in seen_hosp:
                        seen_hosp.add(key)
                        all_hospitality.append(r)
                        month_hosp += 1
        
        months_processed.append(month_name)
        print(f"+{month_gifts} gifts, +{month_hosp} hospitality")
    
    # Build indexes
    print("\nBuilding search indexes...", end=" ", flush=True)
    gift_idx, hosp_idx = build_indexes(all_gifts, all_hospitality)
    print("done")
    
    # Save
    index = {
        "metadata": {
            "created": datetime.now().isoformat(),
            "gift_count": len(all_gifts),
            "hospitality_count": len(all_hospitality),
            "months_processed": months_processed,
            "coverage": "November 2024 onwards"
        },
        "gifts": all_gifts,
        "hospitality": all_hospitality,
        "gift_index": gift_idx,
        "hospitality_index": hosp_idx
    }
    
    print("Saving...", end=" ", flush=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(index, f)
    print("done")
    
    file_size = OUTPUT_PATH.stat().st_size / 1024
    
    print("\n" + "=" * 50)
    print(f"COMPLETE: {len(all_gifts)} gifts, {len(all_hospitality)} hospitality")
    print(f"File: {OUTPUT_PATH.name} ({file_size:.0f} KB)")
    
    # Show samples
    print("\nSample gifts:")
    for g in all_gifts[:3]:
        print(f"  • {g['minister']}: {g.get('gift', 'N/A')} from {g.get('donor_recipient', 'N/A')}")
    
    print("\nSample hospitality:")
    for h in all_hospitality[:3]:
        print(f"  • {h['minister']}: {h.get('hospitality_type', 'N/A')} from {h.get('provider', 'N/A')}")


if __name__ == "__main__":
    main()
