#!/usr/bin/env python3
"""Minimal UK Gifts Index Builder - Fast version"""

import json
import csv
import io
import re
import requests
from datetime import datetime
from collections import defaultdict
from pathlib import Path

def main():
    print("Building UK Gifts Index...")
    
    # Step 1: Find the monthly consolidated registers
    print("\n1. Finding publications...")
    r = requests.get('https://www.gov.uk/api/search.json', params={
        'q': 'Register Ministers Gifts Hospitality',
        'filter_format': 'transparency',
        'count': 20
    }, timeout=30)
    
    pubs = []
    for res in r.json().get('results', []):
        title = res.get('title', '')
        if 'register' in title.lower() and 'gift' in title.lower() and ('2024' in title or '2025' in title):
            pubs.append({'title': title, 'link': res.get('link', '')})
    
    print(f"   Found {len(pubs)} registers")
    
    # Step 2: Get CSVs from each publication
    print("\n2. Getting CSV URLs...")
    all_csvs = []
    
    for pub in pubs:
        print(f"   Processing: {pub['title'][:50]}...")
        try:
            api_url = f"https://www.gov.uk/api/content{pub['link']}"
            r = requests.get(api_url, timeout=30)
            data = r.json()
            
            # Get attachments
            for att in data.get('details', {}).get('attachments', []):
                url = att.get('url', '')
                title = att.get('title', '').lower()
                
                if '.csv' in url:
                    dtype = 'gift' if 'gift' in title else ('hospitality' if 'hospitality' in title else None)
                    if dtype:
                        all_csvs.append({'url': url, 'type': dtype, 'title': att.get('title', ''), 'pub': pub['title']})
        except Exception as e:
            print(f"   Error: {e}")
    
    # Dedupe
    seen = set()
    csvs = [c for c in all_csvs if c['url'] not in seen and not seen.add(c['url'])]
    print(f"   Found {len(csvs)} unique CSVs")
    
    # Step 3: Download and parse CSVs
    print("\n3. Parsing CSVs...")
    gifts = []
    hospitality = []
    
    for i, c in enumerate(csvs):
        print(f"   [{i+1}/{len(csvs)}] {c['title'][:50]}...")
        try:
            r = requests.get(c['url'], timeout=60)
            content = r.content.decode('utf-8-sig', errors='replace')
            reader = csv.DictReader(io.StringIO(content))
            
            for row in reader:
                row_l = {k.lower().strip(): (v.strip() if v else '') for k, v in row.items() if k}
                
                minister = row_l.get('minister', '')
                if not minister or minister.lower() == 'nil return':
                    continue
                
                if c['type'] == 'gift':
                    gifts.append({
                        'type': 'gift',
                        'department': row_l.get('department', ''),
                        'minister': minister,
                        'date': row_l.get('date', ''),
                        'gift': row_l.get('gift', ''),
                        'given_or_received': row_l.get('given or received', ''),
                        'donor_recipient': row_l.get('who gift was given to or received from', ''),
                        'value': row_l.get('value (£)', ''),
                        'outcome': row_l.get('outcome (received gifts only)', ''),
                        'source': c['pub']
                    })
                else:
                    hospitality.append({
                        'type': 'hospitality',
                        'department': row_l.get('department', ''),
                        'minister': minister,
                        'date': row_l.get('date', ''),
                        'provider': row_l.get('individual or organisation that offered hospitality', ''),
                        'hospitality_type': row_l.get('type of hospitality received', ''),
                        'accompanied': row_l.get('accompanied by guest', ''),
                        'value': row_l.get('value of hospitality (£)', ''),
                        'source': c['pub']
                    })
        except Exception as e:
            print(f"      Error: {e}")
    
    print(f"\n   Raw: {len(gifts)} gifts, {len(hospitality)} hospitality")
    
    # Dedupe
    seen_g = set()
    unique_gifts = []
    for g in gifts:
        key = (g['minister'], g['date'], g.get('gift', ''), g.get('donor_recipient', ''))
        if key not in seen_g:
            seen_g.add(key)
            unique_gifts.append(g)
    
    seen_h = set()
    unique_hosp = []
    for h in hospitality:
        key = (h['minister'], h['date'], h.get('provider', ''), h.get('hospitality_type', ''))
        if key not in seen_h:
            seen_h.add(key)
            unique_hosp.append(h)
    
    print(f"   Unique: {len(unique_gifts)} gifts, {len(unique_hosp)} hospitality")
    
    # Build indexes
    gift_idx = defaultdict(list)
    for i, g in enumerate(unique_gifts):
        text = f"{g.get('donor_recipient', '')} {g.get('gift', '')}".lower()
        for w in text.split():
            if len(w) > 2:
                gift_idx[w].append(i)
    
    hosp_idx = defaultdict(list)
    for i, h in enumerate(unique_hosp):
        text = f"{h.get('provider', '')} {h.get('hospitality_type', '')}".lower()
        for w in text.split():
            if len(w) > 2:
                hosp_idx[w].append(i)
    
    # Save
    index = {
        'metadata': {
            'created': datetime.now().isoformat(),
            'gift_count': len(unique_gifts),
            'hospitality_count': len(unique_hosp),
            'coverage': '2024-present'
        },
        'gifts': unique_gifts,
        'hospitality': unique_hosp,
        'gift_index': dict(gift_idx),
        'hospitality_index': dict(hosp_idx)
    }
    
    out = Path(__file__).parent / 'uk_gifts_index.json'
    with open(out, 'w') as f:
        json.dump(index, f, indent=2)
    
    print(f"\n4. Saved to {out} ({out.stat().st_size / 1024:.1f} KB)")
    
    # Show samples
    print("\nSample gifts:")
    for g in unique_gifts[:3]:
        print(f"  • {g['minister']}: '{g.get('gift', 'N/A')}' from {g.get('donor_recipient', 'N/A')}")
    
    print("\nSample hospitality:")
    for h in unique_hosp[:3]:
        print(f"  • {h['minister']}: {h.get('hospitality_type', 'N/A')} from {h.get('provider', 'N/A')}")

if __name__ == '__main__':
    main()
