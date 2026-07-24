"""WikiPlast Data Extractor — Run all modules."""
import sys
import os
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from extractors import companies, petrochemicals, grades, global_prices, news, products


def run_all():
    start = time.time()
    print(f"WikiPlast Extractor started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = {}

    modules = [
        ("1/6 Companies", lambda: companies.run()),
        ("2/6 Petrochemicals", lambda: petrochemicals.run()),
        ("3/6 Grades", lambda: grades.run()),
        ("4/6 Global Prices", lambda: global_prices.run()),
        ("5/6 News & Articles", lambda: news.run()),
        ("6/6 Products", lambda: products.run()),
    ]

    for label, fn in modules:
        try:
            print(f"\n[{label}]")
            result = fn()
            if isinstance(result, tuple):
                for i, r in enumerate(result):
                    key = f"{label.split()[1]}_{i}" if len(result) > 1 else label.split()[1]
                    results[key] = r
            else:
                results[label.split()[1]] = result
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
        "files": {},
    }

    data_dir = "data"
    for fname in sorted(os.listdir(data_dir)):
        if fname.endswith(".csv"):
            fpath = os.path.join(data_dir, fname)
            with open(fpath, encoding="utf-8-sig") as f:
                import csv
                rows = list(csv.DictReader(f))
                summary["files"][fname] = len(rows)

    os.makedirs(data_dir, exist_ok=True)
    with open(os.path.join(data_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\nDuration: {elapsed:.1f}s")
    print("\nFiles extracted:")
    for fname, count in summary["files"].items():
        print(f"  {fname}: {count} rows")
    print(f"\nAll data saved to {data_dir}/")


if __name__ == "__main__":
    run_all()
