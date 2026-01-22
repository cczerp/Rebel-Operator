"""
Multi-Platform Search Module
=============================
Aggregated search across resale platforms.
"""

from .base_searcher import BasePlatformSearcher, SearchQuery, SearchResult, SearchCapability
from .platform_searchers import get_searcher, SEARCHER_REGISTRY
from .aggregator import SearchAggregator, NormalizedResult, MarketIntelligence

__all__ = [
    'BasePlatformSearcher',
    'SearchQuery',
    'SearchResult',
    'SearchCapability',
    'SearchAggregator',
    'NormalizedResult',
    'MarketIntelligence',
    'get_searcher',
    'SEARCHER_REGISTRY',
]
