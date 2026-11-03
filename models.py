"""
InvestIQ Phase 2 - Database Models

Supabase already provides and manages its own `auth.users` table - we don't
duplicate it here. Our tables just reference the Supabase user's UUID
(from the verified JWT's "sub" claim) as a plain string column, without a
hard foreign-key constraint across schemas (keeps this simple; Supabase's
own Row Level Security can enforce stricter integrity later if needed).

Two tables:
  - portfolios: named, saved holdings lists (JSON column for {ticker: weight})
  - saved_reports: cached full report output (single-asset or portfolio)
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, JSON

from database import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)  # Supabase auth.users UUID
    name = Column(String, nullable=False)
    holdings = Column(JSON, nullable=False)  # [{"ticker": "AAPL", "weight": 0.5}, ...]
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SavedReport(Base):
    __tablename__ = "saved_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)  # Supabase auth.users UUID
    report_type = Column(String, nullable=False)  # "single" or "portfolio"
    tickers = Column(JSON, nullable=False)  # list of tickers involved
    report_data = Column(JSON, nullable=False)  # the full response payload, as-is
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))