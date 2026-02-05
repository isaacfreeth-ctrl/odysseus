# 🎁 UK Ministerial Gifts & Hospitality Tracker

A Streamlit app for searching UK ministerial gift and hospitality declarations from 2024 onwards.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## Deploy to Streamlit Cloud

1. Push this folder to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Select `app.py` as the main file
5. Deploy!

## Files

| File | Description |
|------|-------------|
| `app.py` | Streamlit web interface |
| `uk_gifts_index.json` | Pre-built searchable index (391 gifts, 1,178 hospitality) |
| `build_index.py` | Script to rebuild the index from GOV.UK |
| `boolean_search.py` | Boolean query parser for advanced searches |
| `requirements.txt` | Python dependencies |

## Features

- **Search gifts**: Find declarations by donor, gift description, or country
- **Search hospitality**: Find by provider or hospitality type
- **Filter by minister**: Narrow results to specific ministers
- **Boolean search**: Use AND, OR, NOT, quotes for complex queries
- **Excel export**: Download search results

## Data Source

Data comes from the monthly **Register of Ministers' Gifts and Hospitality** published by the Cabinet Office:
- [GOV.UK Collection](https://www.gov.uk/government/collections/register-of-ministers-gifts-and-hospitality)

### Coverage

- **Gifts**: Declarations over £140 threshold
- **Hospitality**: Declarations above de minimis levels
- **Period**: 2024 onwards (both Sunak and Starmer governments)

## Updating the Index

To refresh the data with the latest declarations:

```bash
python build_index.py
```

This will:
1. Discover all monthly registers on GOV.UK
2. Download and parse each CSV
3. Save to `uk_gifts_index.json`

## Example Searches

| Search | What it finds |
|--------|---------------|
| `UAE` | Gifts/hospitality involving UAE |
| `Financial Times` | Media hospitality from FT |
| `France OR Germany` | European diplomatic gifts |
| `BBC OR Sky` | Broadcast media hospitality |
| `"football tickets"` | Exact phrase match |
| `dinner NOT lunch` | Dinners but not lunches |

## License

MIT License. Transparency data is Crown Copyright under Open Government Licence v3.0.
