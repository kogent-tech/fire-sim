"""Download Robert Shiller's published U.S. stock market dataset.

Source: http://www.econ.yale.edu/~shiller/data.htm
"""
import argparse
from pathlib import Path

import requests

SHILLER_URL = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"
RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
RAW_FILE = RAW_DIR / "ie_data.xls"


def fetch(dest: Path = RAW_FILE, url: str = SHILLER_URL) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    return dest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=RAW_FILE)
    parser.add_argument("--url", default=SHILLER_URL)
    args = parser.parse_args()
    path = fetch(args.dest, args.url)
    print(f"Downloaded {path} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
