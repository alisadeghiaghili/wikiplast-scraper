"""WikiPlast Scraper — Main Orchestrator"""
import sys
import os
import json
import time
from datetime import datetime

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(__file__))

from extractors import companies, petrochemicals, grades, global_prices, news, products


def run_all():
    """Run all extractors in sequence."""
    start = time.time()
    print(f"WikiPlast Scraper started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = {}

    try:
        print("\n[1/6] Companies Directory")
        results["companies"] = companies.run()
    except Exception as e:
        print(f"  ERROR: {e}")

    try:
        print("\n[2/6] Petrochemical Companies")
        results["petrochemicals"] = petrochemicals.run()
    except Exception as e:
        print(f"  ERROR: {e}")

    try:
        print("\n[3/6] Grade Taxonomy & Details")
        results["grades"] = grades.run()
    except Exception as e:
        print(f"  ERROR: {e}")

    try:
        print("\n[4/6] Global Prices")
        results["global_prices"] = global_prices.run()
    except Exception as e:
        print(f"  ERROR: {e}")

    try:
        print("\n[5/6] News & Articles")
        results["news"], results["articles"] = news.run()
    except Exception as e:
        print(f"  ERROR: {e}")

    try:
        print("\n[6/6] Company Products")
        results["products"] = products.run()
    except Exception as e:
        print(f"  ERROR: {e}")

    # Summary
    elapsed = time.time() - start
    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)

    summary = {
        "extracted_at": datetime.now().isoformat(),
        "duration_seconds": round(elapsed, 1),
        "counts": {},
    }

    for key, data in results.items():
        if data is None:
            summary["counts"][key] = 0
        elif isinstance(data, tuple):
            summary["counts"][key] = sum(len(d) if d else 0 for d in data)
        elif isinstance(data, list):
            summary["counts"][key] = len(data)
        else:
            summary["counts"][key] = 0

    os.makedirs("data", exist_ok=True)
    with open("data/summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\nDuration: {elapsed:.1f}s")
    for k, v in summary["counts"].items():
        print(f"  {k}: {v} rows")
    print(f"\nSummary saved to data/summary.json")
    print("All data saved to data/ directory")

    return summary


if __name__ == "__main__":
    run_all()
