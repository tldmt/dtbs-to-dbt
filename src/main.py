import json
import argparse

from pathlib import Path

from collect import collect, DEFAULT_EXCLUDE
from dbt_sources import write_dbt_sources

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"

def main() -> None:

    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="whether or not to save the result as JSON")
    parser.add_argument("--sources", action="store_true", help="whether to store or not results as DBT sources in YAML")
    parser.add_argument("--include", nargs="+", default=[], help="collect only catalogs, schemas and tables whose name contains any of these words")
    parser.add_argument("--exclude", nargs="*", default=DEFAULT_EXCLUDE, help=f"skip catalogs, schemas and tables whose name contains any of these words (default: {' '.join(DEFAULT_EXCLUDE)}; pass empty to disable)")
    args = parser.parse_args()

    content = collect(args.include, args.exclude)

    if args.json:
        path = OUTPUT_DIR / "json" / "catalogs.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        print(f"\nJSON saved to {path}")

    if args.sources:
        written = write_dbt_sources(content, OUTPUT_DIR / "yml")
        print(f"\n{len(written)} dbt sources YAML files saved to {OUTPUT_DIR / 'yml'}")


if __name__ == "__main__":
    main()
