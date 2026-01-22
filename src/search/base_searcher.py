"""
Base Platform Searcher
======================
Abstract base class for all platform search implementations.

Unlike importers (which pull YOUR listings), searchers query
PUBLIC marketplace data to find items available for purchase.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class SearchCapability(Enum):
    """What types of searches a platform supports"""
    API_SEARCH = "api_search"           # Official search API (eBay, Etsy)
    SCRAPER_FRIENDLY = "scraper_friendly"  # Publicly accessible, no API (Mercari)
    NO_EXTERNAL_SEARCH = "no_external_search"  # Cannot search externally


@dataclass
class SearchQuery:
    """Standardized search query across all platforms"""
    keywords: str                           # Primary search terms
    item_type: Optional[str] = None        # Card, Coin, Slabbed, Raw, Sealed, Other
    condition: Optional[List[str]] = None  # New, Used, NM, LP, MP, HP
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    sort_by: str = "newest"                # lowest_price, best_value, newest, most_listings
    limit: int = 50                        # Max results per platform


@dataclass
class SearchResult:
    """
    Standardized search result from any platform.

    This is the raw data - Column 1 in the UI.
    Normalization happens in the aggregator.
    """
    # Identity
    platform: str              # eBay, Mercari, Etsy, etc.
    listing_id: str           # Platform's unique ID
    url: str                  # Direct link to listing

    # Core data
    title: str
    price: float              # Listed price (not normalized)
    shipping_cost: Optional[float] = None
    condition: Optional[str] = None  # As-listed condition

    # Media
    thumbnail_url: Optional[str] = None
    photos: List[str] = None

    # Metadata
    seller_name: Optional[str] = None
    seller_rating: Optional[float] = None
    time_posted: Optional[datetime] = None
    location: Optional[str] = None

    # Additional data
    description: Optional[str] = None
    quantity_available: int = 1
    accepts_offers: bool = False

    # Platform-specific extras
    extras: Dict[str, Any] = None

    def __post_init__(self):
        if self.photos is None:
            self.photos = []
        if self.extras is None:
            self.extras = {}

    def total_price(self) -> float:
        """Price + shipping"""
        return self.price + (self.shipping_cost or 0.0)


class BasePlatformSearcher(ABC):
    """Base class for all platform search implementations"""

    def __init__(self, credentials: Optional[Dict[str, Any]] = None):
        """
        Initialize searcher.

        Args:
            credentials: Optional API credentials (not always needed for public search)
        """
        self.credentials = credentials or {}
        self.platform_name = self.get_platform_name()
        self.search_capability = self.get_search_capability()

    @abstractmethod
    def get_platform_name(self) -> str:
        """Return platform name (e.g., 'eBay', 'Mercari')"""
        pass

    @abstractmethod
    def get_search_capability(self) -> SearchCapability:
        """Return what type of search this platform supports"""
        pass

    @abstractmethod
    def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Execute search query on platform.

        Args:
            query: Standardized search query

        Returns:
            List of search results

        Raises:
            Exception: If search fails
        """
        pass

    def is_available(self) -> bool:
        """Check if this searcher is available/configured"""
        return self.search_capability != SearchCapability.NO_EXTERNAL_SEARCH

    def requires_auth(self) -> bool:
        """Does this platform require authentication to search?"""
        return False  # Override if platform requires auth
