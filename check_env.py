"""
Quick sanity check: confirms EODHD_API_KEY (and the other keys) are actually
loading from .env before we chase a phantom bug in data_fetcher.py.

Run in the same folder as your .env file:
    python3 check_env.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

for var in ["EODHD_API_KEY", "GROQ_API_KEY", "ANTHROPIC_API_KEY"]:
    value = os.environ.get(var)
    if value:
        print(f"{var}: found, starts with {value[:6]}...")
    else:
        print(f"{var}: NOT FOUND - check your .env file")