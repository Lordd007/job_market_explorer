from __future__ import annotations

from typing import Optional, Tuple


def normalize_location(
    location: Optional[str] = None,
    city: Optional[str] = None,
    region: Optional[str] = None,
    country: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Normalize location details into (city, region, country).

    Priority:
      1) Explicit city/region/country values.
      2) Fallback to parsing a single ``location`` string.

    Accepted formats for ``location`` include:
      - "City"
      - "City, ST/Region"
      - "City, Region, Country"
      - "Remote"
    """

    # Prefer already-split fields
    if city or region or country:
        return city or None, region or None, country or None

    if not location:
        return None, None, None

    loc = location.strip()
    if not loc:
        return None, None, None

    if loc.lower() == "remote":
        return "Remote", None, None

    parts = [p.strip() for p in loc.split(",") if p.strip()]
    if len(parts) == 1:
        return parts[0], None, None
    if len(parts) == 2:
        return parts[0], parts[1], None
    # 3+ -> "City, Region, Country"
    return parts[0], parts[1], parts[-1]
