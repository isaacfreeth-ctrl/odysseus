# 🎁 UK Ministerial Gifts & Hospitality Tracker

A tool for searching UK ministerial gift and hospitality declarations from 2024 onwards.

## Features

- **Pre-indexed data**: Instant search across 391 gifts and 1,178 hospitality declarations
- **Boolean search**: Support for AND, OR, NOT, quotes, and parentheses
- **Multiple search modes**: Search by donor/provider, minister, department, or gift type
- **Regularly updated**: Build script to refresh data from GOV.UK

## Data Source

Data comes from the consolidated **Register of Ministers' Gifts and Hospitality** published monthly by the Cabinet Office on GOV.UK:
- [GOV.UK Transparency Publications](https://www.gov.uk/search/transparency-and-freedom-of-information-releases?content_purpose_subgroup=transparency)

### What's Included

**Gifts** (threshold: >£140):
- Minister name and department
- Gift description
- Donor/recipient
- Given or received
- Value and outcome (retained/donated/etc.)

**Hospitality** (above de minimis levels):
- Minister name and department
- Provider (individual or organisation)
- Type of hospitality (lunch, dinner, tickets, etc.)
- Value
- Whether accompanied by guest

## Usage

### Python API

```python
from uk_gifts_core import search_uk_gifts, search_uk_hospitality

# Search gifts
results = search_uk_gifts("UAE")
for gift in results["gifts"]:
    print(f"{gift['minister']}: {gift['gift']} from {gift['donor_recipient']}")

# Search hospitality
results = search_uk_hospitality("Financial Times")
for h in results["hospitality"]:
    print(f"{h['minister']}: {h['hospitality_type']} from {h['provider']}")

# Boolean search
results = search_uk_gifts("France OR Germany")
results = search_uk_hospitality("(BBC OR Sky) AND dinner")

# Get all declarations for a minister
from uk_gifts_core import get_minister_gifts
results = get_minister_gifts("Keir Starmer")
print(f"Gifts: {results['gift_count']}, Hospitality: {results['hospitality_count']}")
```

### Building/Updating the Index

```bash
python build_gifts_fast.py
```

This will:
1. Discover all monthly gift registers on GOV.UK
2. Download and parse each CSV file
3. Deduplicate and save to `uk_gifts_index.json`

## Files

| File | Description |
|------|-------------|
| `uk_gifts_core.py` | Main search module |
| `uk_gifts_index.json` | Pre-built searchable index |
| `build_gifts_fast.py` | Script to rebuild the index |
| `boolean_search.py` | Boolean query parser (shared with lobbying tracker) |

## Integration with Lobbying Tracker

This module follows the same patterns as the UK meetings module in the European Lobbying Tracker. You can add it to your `__init__.py`:

```python
from uk_gifts_core import (
    search_uk_gifts,
    search_uk_hospitality,
    search_uk_gifts_and_hospitality,
    get_minister_gifts,
)

JURISDICTIONS["uk_gifts"] = {
    "id": "uk_gifts",
    "name": "UK Ministerial Gifts",
    "flag": "🇬🇧",
    "search_fn": search_uk_gifts,
    "has_financial_data": True,
    "note": "Ministerial gifts over £140. Monthly consolidated register.",
    "default_enabled": True,
}

JURISDICTIONS["uk_hospitality"] = {
    "id": "uk_hospitality",
    "name": "UK Ministerial Hospitality",
    "flag": "🇬🇧",
    "search_fn": search_uk_hospitality,
    "has_financial_data": True,
    "note": "Ministerial hospitality above de minimis. Monthly consolidated register.",
    "default_enabled": True,
}
```

## Example Searches

```python
# Who received gifts from Gulf states?
search_uk_gifts("UAE OR Qatar OR Saudi OR Kuwait OR Bahrain OR Oman")

# Which ministers received hospitality from media organisations?
search_uk_hospitality("BBC OR Sky OR ITV OR Channel 4 OR Financial Times")

# Football/sports hospitality
search_uk_hospitality("Arsenal OR Chelsea OR football OR Premier League")

# Tech company gifts
search_uk_gifts("Google OR Microsoft OR Apple OR Meta OR Amazon")
```

## Notes

- **Coverage**: 2024 onwards (both governments)
- **Update frequency**: Monthly registers published with ~1 month lag
- **Nil returns**: Filtered out during indexing
- **Deduplication**: Records appearing in multiple registers are deduplicated

## License

MIT License - transparency data is Crown Copyright under Open Government Licence v3.0.
