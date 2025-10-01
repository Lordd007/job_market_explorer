from typing import Iterable, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class JobDoc:
    title: str
    company: str
    description_text: str
    url: Optional[str]
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    posted_at_iso: Optional[str] = None
    source: str = "unknown"

class SourceAdapter:
    name: str
    def fetch(self, days: int = 7) -> Iterable[JobDoc]:
        """Yield JobDoc objects from the last N days."""
        raise NotImplementedError
