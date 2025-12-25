"""Base collector class for all data sources."""

from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CollectedArticle:
    """Standardized article data from any source."""

    source_type: str
    source_name: str
    title: str
    url: str
    content: Optional[str] = None
    country_code: Optional[str] = None
    published_at: Optional[datetime] = None


class BaseCollector(ABC):
    """Abstract base class for data collectors."""

    source_type: str = "unknown"

    @abstractmethod
    async def collect(self) -> List[CollectedArticle]:
        """Collect articles from the data source.

        Returns:
            List of collected articles
        """
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the collector is properly configured.

        Returns:
            True if the collector can run, False otherwise
        """
        pass
