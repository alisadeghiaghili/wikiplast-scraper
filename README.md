# WikiPlast Scraper

Stealth web scraper for [WikiPlast](https://wikiplast.ir) — Iran's largest plastics and petrochemical industry reference portal. Extracts 13,900+ data points into structured CSV files with full anti-detection capabilities.

## Extracted Data

| File | Rows | Description |
|------|------|-------------|
| `companies.csv` | 12,950 | Manufacturing companies — name, contact, website, rating, category, verification status |
| `individual_grades.csv` | 660 | Polymer grades — name, ID, petrochemical company, category |
| `petrochemicals.csv` | 54 | Petrochemical producers with their full product grade listings |
| `global_polymer_prices.csv` | 25 | International polymer prices (Platts + ICIS) across 7 regions |
| `global_chemical_prices.csv` | 11 | International chemical prices |
| `news.csv` | 48 | Industry news articles with titles, URLs, thumbnails |
| `articles.csv` | 46 | Technical articles on plastics manufacturing |
| `grades.csv` | 38 | Polymer category taxonomy (PE, PP, PS, PVC, PET, ABS, SBR, etc.) |
| `grade_details.csv` | 50 | Individual grade detail pages with related grade metadata |
| `products.csv` | 18 | Company product listings with images and view counts |

**Total: 13,900+ rows across 10 CSV files**

## Quick Start

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Full Extraction

```bash
python extract_data.py
```

### Run Individual Modules

```bash
# Companies only
python -c "from extractors import companies; companies.run()"

# Grades only
python -c "from extractors import grades; grades.run()"

# Global prices only
python -c "from extractors import global_prices; global_prices.run()"

# News and articles only
python -c "from extractors import news; news.run()"

# Petrochemicals only
python -c "from extractors import petrochemicals; petrochemicals.run()"

# Products only
python -c "from extractors import products; products.run()"
```

## Anti-Detection Features

The scraper is designed to avoid detection by the target website:

| Feature | Description |
|---------|-------------|
| **User-Agent Rotation** | Rotates through 7 real browser strings (Chrome, Firefox, Safari, Edge) |
| **Random Referer** | Fakes arrival from Google, Bing, or direct visit |
| **Accept-Language Variants** | Varies between Persian/English language combinations |
| **Browser Headers** | Includes `Sec-Fetch-*`, `Upgrade-Insecure-Requests`, `Cache-Control` |
| **Random Delays** | 1.0–3.5 second randomized delays between requests |
| **Session Persistence** | Reuses cookies across requests like a real browser |
| **Rate Limit Handling** | On 429: waits 10–30 seconds before retrying |
| **Block Recovery** | On 403: creates fresh session and waits before retrying |
| **Exponential Backoff** | Increases wait time on repeated failures |

## Project Structure

```
wikiplast-scraper/
├── extract_data.py          # Main orchestrator — runs all modules
├── config.py                # Stealth headers, delays, user agent pool
├── utils.py                 # Fetch with retry/backoff, CSV export, HTML parsing
├── requirements.txt         # Python dependencies
├── extractors/
│   ├── __init__.py
│   ├── companies.py         # Company directory scraper (12,950+ companies)
│   ├── grades.py            # Grade taxonomy + individual grade details
│   ├── petrochemicals.py    # Petrochemical company scraper
│   ├── global_prices.py     # Global polymer & chemical prices
│   ├── news.py              # News & articles scraper
│   └── products.py          # Company products scraper
└── data/                    # Output CSV files (auto-created)
    ├── companies.csv
    ├── individual_grades.csv
    ├── petrochemicals.csv
    ├── global_polymer_prices.csv
    ├── global_chemical_prices.csv
    ├── news.csv
    ├── articles.csv
    ├── grades.csv
    ├── grade_details.csv
    └── products.csv
```

## Data Schema

### companies.csv

| Column | Type | Description |
|--------|------|-------------|
| `company_id` | string | Unique company identifier |
| `name` | string | Company name (Persian) |
| `url` | string | Full URL to company page |
| `contact_person` | string | Primary contact name |
| `website` | string | Company website |
| `rating` | float | WikiPlast rating score |
| `logo_url` | string | Path to company logo |
| `verified` | boolean | Whether company is verified |
| `category` | string | Industry category |

### individual_grades.csv

| Column | Type | Description |
|--------|------|-------------|
| `grade_id` | string | Unique grade identifier |
| `name` | string | Grade name |
| `url` | string | Full URL to grade page |
| `petrochemical_company` | string | Producing company |
| `parent_category` | string | Parent polymer category |
| `subcategory_name` | string | Specific subcategory |

### global_polymer_prices.csv

| Column | Type | Description |
|--------|------|-------------|
| `product` | string | Polymer product name |
| `region` | string | Geographic region |
| `price_floor_usd` | string | Minimum price (USD/ton) |
| `price_ceiling_usd` | string | Maximum price (USD/ton) |
| `source` | string | Data source (Platts/ICIS) |

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`:
  - `requests>=2.31`
  - `beautifulsoup4>=4.12`
  - `lxml>=5.0`

## Rate Limiting

The scraper uses randomized delays between 1.0–3.5 seconds per request to avoid overwhelming the server. A full extraction typically takes 15–30 minutes depending on network conditions.

## License

MIT
