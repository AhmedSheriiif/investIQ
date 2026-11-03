"""
Pulls EODHD's full, authoritative list of tickers on the Egyptian Exchange (EGX)
and searches it for a company name or symbol fragment. Settles "does this
ticker actually exist on EODHD" definitively instead of guessing.

Uses raw requests (not the official eodhd library) - see the comment in
data_fetcher.py's fetch_from_eodhd() for why: the library calls sys.exit(1)
on certain error responses instead of raising a catchable exception.

Run locally (needs EODHD_API_KEY in .env):
    python3 list_egx_tickers.py VERT
    python3 list_egx_tickers.py          # lists all EGX tickers, no filter
"""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("EODHD_API_KEY")
if not api_key:
    raise SystemExit("EODHD_API_KEY not set in .env")

resp = requests.get(
    "https://eodhd.com/api/exchange-symbol-list/EGX",
    params={"api_token": api_key, "fmt": "json"},
    timeout=15,
)

if resp.status_code != 200:
    raise SystemExit(f"EODHD returned HTTP {resp.status_code}: {resp.text[:300]}")

symbols = resp.json()

if not isinstance(symbols, list):
    raise SystemExit(f"Unexpected response shape: {symbols}")

query = sys.argv[1].upper() if len(sys.argv) > 1 else None

print(f"Total EGX tickers on EODHD: {len(symbols)}\n")

matches = []
for s in symbols:
    code = s.get("Code", "")
    name = s.get("Name", "")
    if query is None or query in code.upper() or query in name.upper():
        matches.append(s)

if query:
    print(f"Matches for '{query}': {len(matches)}\n")

for s in matches:
    print(f"  {s.get('Code'):12s} {s.get('Name')}")

# if len(matches) > 50:
#     print(f"  ... and {len(matches) - 50} more")