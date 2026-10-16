"""Region routing by device market (ADR-001; ADR-002 rule 5; R4).

The region is decided by the market the device is registered in, never by
the nearest endpoint, so a travelling device still posts to its home region.
The table below is illustrative; in practice it is versioned configuration
reviewed with privacy counsel, and moving a market between regions is a
planned migration, not a config edit.
"""

from __future__ import annotations

REGIONS = ("EU", "US", "APAC")

MARKET_TO_REGION: dict[str, str] = {
    # European region
    "DE": "EU",
    "FR": "EU",
    "GB": "EU",
    "IT": "EU",
    "ES": "EU",
    "NL": "EU",
    "PL": "EU",
    "SE": "EU",
    # Americas region
    "US": "US",
    "CA": "US",
    "MX": "US",
    "BR": "US",
    # Asia-Pacific region
    "KR": "APAC",
    "JP": "APAC",
    "AU": "APAC",
    "IN": "APAC",
    "SG": "APAC",
    "VN": "APAC",
}


def region_for_market(market: str) -> str | None:
    return MARKET_TO_REGION.get(market.upper())
