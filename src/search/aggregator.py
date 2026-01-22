"""
Multi-Platform Search Aggregator
=================================
Coordinates searches across multiple platforms and normalizes results.

This is the brain of Column 1 → Column 2 → Column 3 flow.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_searcher import SearchQuery, SearchResult
from .platform_searchers import get_searcher


@dataclass
class NormalizedResult:
    """
    Enhanced search result with normalization and comparison data.

    This is what powers Column 2 (Comparison & Normalization).
    """
    result: SearchResult                    # Original result
    total_price: float                      # Price + shipping
    normalized_price: float                 # After estimated fees
    price_per_condition: Optional[float] = None  # Value metric
    is_outlier: bool = False               # Suspiciously high/low
    similar_listings: List[SearchResult] = field(default_factory=list)
    comparison_notes: List[str] = field(default_factory=list)


@dataclass
class MarketIntelligence:
    """
    Market-level intelligence for Column 3 (Intelligence Panel).
    """
    query: str
    total_results: int
    average_price: float
    median_price: float
    price_range: Tuple[float, float]  # (min, max)
    volume_indicator: str  # "rare", "moderate", "saturated"
    platforms_found: List[str]
    best_value_result: Optional[SearchResult] = None
    condition_breakdown: Dict[str, int] = field(default_factory=dict)


class SearchAggregator:
    """
    Multi-platform search coordinator.

    Handles:
    - Parallel searches across platforms
    - Result deduplication
    - Price normalization
    - Market intelligence generation
    """

    # Platform fee estimates (% of sale price)
    PLATFORM_FEES = {
        'eBay': 0.135,      # ~13.5% final value fee
        'Etsy': 0.065,      # 6.5% transaction fee
        'Mercari': 0.10,    # 10% selling fee
        'TCGplayer': 0.108, # 10.8% seller fee
        'Poshmark': 0.20,   # 20% fee
        'Facebook': 0.05,   # 5% selling fee
    }

    def __init__(self, credentials_store: Optional[Dict[str, Dict]] = None):
        """
        Initialize aggregator.

        Args:
            credentials_store: Dict of platform credentials
                               {'ebay': {...}, 'etsy': {...}, ...}
        """
        self.credentials_store = credentials_store or {}

    def search_all_platforms(
        self,
        query: SearchQuery,
        enabled_platforms: Optional[List[str]] = None
    ) -> Tuple[List[SearchResult], MarketIntelligence]:
        """
        Search across multiple platforms in parallel.

        Args:
            query: Search query
            enabled_platforms: List of platform names to search (None = all available)

        Returns:
            Tuple of (all_results, market_intelligence)
        """
        if enabled_platforms is None:
            enabled_platforms = ['ebay', 'etsy', 'tcgplayer', 'mercari']

        all_results = []

        # Parallel search across platforms
        with ThreadPoolExecutor(max_workers=len(enabled_platforms)) as executor:
            future_to_platform = {}

            for platform in enabled_platforms:
                credentials = self.credentials_store.get(platform, {})
                searcher = get_searcher(platform, credentials)

                if searcher and searcher.is_available():
                    future = executor.submit(self._safe_search, searcher, query)
                    future_to_platform[future] = platform

            # Collect results as they complete
            for future in as_completed(future_to_platform):
                platform = future_to_platform[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                    print(f"✓ {platform}: {len(results)} results")
                except Exception as e:
                    print(f"✗ {platform}: {e}")

        # Generate market intelligence
        market_intel = self._generate_market_intelligence(query, all_results)

        return all_results, market_intel

    def _safe_search(self, searcher, query: SearchQuery) -> List[SearchResult]:
        """Safely execute search with error handling"""
        try:
            return searcher.search(query)
        except Exception as e:
            print(f"{searcher.platform_name} search failed: {e}")
            return []

    def normalize_results(self, results: List[SearchResult]) -> List[NormalizedResult]:
        """
        Normalize and enhance results with comparison data.

        This powers Column 2 (Comparison & Normalization).
        """
        normalized = []

        for result in results:
            # Calculate total and normalized prices
            total = result.total_price()
            estimated_fees = total * self.PLATFORM_FEES.get(result.platform, 0.1)
            normalized_price = total + estimated_fees

            # Detect outliers (very basic - can be improved)
            prices = [r.total_price() for r in results if r.platform == result.platform]
            if prices:
                avg = sum(prices) / len(prices)
                is_outlier = total < avg * 0.5 or total > avg * 2.0
            else:
                is_outlier = False

            # Find similar listings (same title similarity)
            similar = self._find_similar_listings(result, results)

            # Generate comparison notes
            notes = self._generate_comparison_notes(result, similar)

            normalized.append(NormalizedResult(
                result=result,
                total_price=total,
                normalized_price=normalized_price,
                is_outlier=is_outlier,
                similar_listings=similar,
                comparison_notes=notes,
            ))

        return normalized

    def _find_similar_listings(
        self,
        target: SearchResult,
        all_results: List[SearchResult],
        similarity_threshold: float = 0.6
    ) -> List[SearchResult]:
        """Find listings similar to target"""
        similar = []

        target_title_lower = target.title.lower()
        target_words = set(target_title_lower.split())

        for result in all_results:
            if result.listing_id == target.listing_id:
                continue

            # Simple word-based similarity
            result_words = set(result.title.lower().split())
            common_words = target_words & result_words
            union_words = target_words | result_words

            if union_words:
                similarity = len(common_words) / len(union_words)
                if similarity >= similarity_threshold:
                    similar.append(result)

        return similar[:5]  # Top 5 most similar

    def _generate_comparison_notes(
        self,
        result: SearchResult,
        similar: List[SearchResult]
    ) -> List[str]:
        """Generate human-readable comparison notes"""
        notes = []

        if not similar:
            return notes

        # Price comparisons
        similar_prices = [s.total_price() for s in similar]
        avg_similar = sum(similar_prices) / len(similar_prices)

        price_diff = result.total_price() - avg_similar
        if price_diff < -5:
            notes.append(f"${abs(price_diff):.2f} cheaper than similar listings")
        elif price_diff > 5:
            notes.append(f"${price_diff:.2f} more expensive than similar listings")

        # Condition comparisons
        if result.condition:
            better_condition = [s for s in similar if s.condition and
                              self._condition_score(s.condition) > self._condition_score(result.condition)]
            if better_condition:
                notes.append("Similar items available in better condition")

        # Cross-platform comparison
        other_platforms = {s.platform for s in similar if s.platform != result.platform}
        if other_platforms:
            notes.append(f"Also found on: {', '.join(other_platforms)}")

        return notes

    def _condition_score(self, condition: str) -> int:
        """Map condition to numeric score (higher = better)"""
        condition_lower = condition.lower()
        if 'new' in condition_lower or 'mint' in condition_lower:
            return 5
        elif 'excellent' in condition_lower or 'like new' in condition_lower:
            return 4
        elif 'good' in condition_lower:
            return 3
        elif 'fair' in condition_lower or 'acceptable' in condition_lower:
            return 2
        else:
            return 1

    def _generate_market_intelligence(
        self,
        query: SearchQuery,
        results: List[SearchResult]
    ) -> MarketIntelligence:
        """
        Generate market-level intelligence from results.

        This powers Column 3 (Intelligence Panel).
        """
        if not results:
            return MarketIntelligence(
                query=query.keywords,
                total_results=0,
                average_price=0,
                median_price=0,
                price_range=(0, 0),
                volume_indicator="none",
                platforms_found=[],
            )

        # Price statistics
        prices = [r.total_price() for r in results]
        prices_sorted = sorted(prices)

        avg_price = sum(prices) / len(prices)
        median_price = prices_sorted[len(prices_sorted) // 2]
        price_range = (min(prices), max(prices))

        # Volume indicator
        if len(results) < 10:
            volume = "rare"
        elif len(results) < 50:
            volume = "moderate"
        else:
            volume = "saturated"

        # Platforms found
        platforms = list(set(r.platform for r in results))

        # Best value (lowest price/condition ratio)
        best_value = None
        best_score = float('inf')
        for r in results:
            if r.condition:
                score = r.total_price() / max(self._condition_score(r.condition), 1)
                if score < best_score:
                    best_score = score
                    best_value = r

        # Condition breakdown
        condition_breakdown = {}
        for r in results:
            if r.condition:
                condition_breakdown[r.condition] = condition_breakdown.get(r.condition, 0) + 1

        return MarketIntelligence(
            query=query.keywords,
            total_results=len(results),
            average_price=avg_price,
            median_price=median_price,
            price_range=price_range,
            volume_indicator=volume,
            platforms_found=platforms,
            best_value_result=best_value,
            condition_breakdown=condition_breakdown,
        )
