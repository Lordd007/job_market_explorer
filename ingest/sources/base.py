from __future__ import annotations
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Iterable, Dict, Any, Optional

@dataclass
class JobDoc:
    board_id: str
    job_id: str
    title: str
    location: str
    absolute_url: str
    departments: str = ""
    offices: str = ""
    updated_at: str = ""
    content_html: str | None = None

class SourceAdapter(ABC):
    name: str

    def __init__(self, *, request_delay: float = 0.25):
        self.request_delay = request_delay

    @abstractmethod
    def resolve_board(self, company: str, candidates: Iterable[str]) -> Optional[str]:
        ...

    @abstractmethod
    def fetch_jobs(self, board_id: str) -> Iterable[Dict[str, Any]]:
        ...

    @abstractmethod
    def normalize(self, board_id: str, raw: Dict[str, Any]) -> JobDoc:
        ...
