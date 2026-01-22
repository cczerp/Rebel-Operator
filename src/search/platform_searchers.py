"""
Platform Search Implementations
================================
Concrete searcher implementations for each supported platform.

COMPLIANCE:
- eBay: Official Finding API (public, no auth required for basic search)
- Etsy: Official Open API v3 (requires API key)
- TCGplayer: Public catalog API
- Mercari: Public listings (no official API, scraper-friendly)
- Facebook Marketplace: No external search allowed
"""

import requests
from typing import List, Optional, Dict, Any
from datetime import datetime
from .base_searcher import (
    BasePlatformSearcher,
    SearchQuery,
    SearchResult,
    SearchCapability
)


class eBaySearcher(BasePlatformSearcher):
    """
    eBay Finding API searcher.

    Uses official eBay Finding API (public, no auth required for basic search).
    https://developer.ebay.com/devzone/finding/Concepts/FindingAPIGuide.html
    """

    BASE_URL = "https://svcs.ebay.com/services/search/FindingService/v1"

    def get_platform_name(self) -> str:
        return "eBay"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.API_SEARCH

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search eBay using Finding API"""
        results = []

        # eBay Finding API parameters
        params = {
            'OPERATION-NAME': 'findItemsAdvanced',
            'SERVICE-VERSION': '1.0.0',
            'SECURITY-APPNAME': self.credentials.get('app_id', 'TESTAPPID'),  # Use credentials or test ID
            'RESPONSE-DATA-FORMAT': 'JSON',
            'REST-PAYLOAD': '',
            'keywords': query.keywords,
            'paginationInput.entriesPerPage': min(query.limit, 100),
            'sortOrder': self._map_sort(query.sort_by),
        }

        # Add price filters if specified
        if query.min_price is not None:
            params['itemFilter(0).name'] = 'MinPrice'
            params['itemFilter(0).value'] = str(query.min_price)

        if query.max_price is not None:
            filter_idx = 1 if query.min_price is not None else 0
            params[f'itemFilter({filter_idx}).name'] = 'MaxPrice'
            params[f'itemFilter({filter_idx}).value'] = str(query.max_price)

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Parse eBay response
            search_result = data.get('findItemsAdvancedResponse', [{}])[0]
            items = search_result.get('searchResult', [{}])[0].get('item', [])

            for item in items:
                results.append(self._parse_item(item))

        except Exception as e:
            print(f"eBay search error: {e}")

        return results

    def _parse_item(self, item: Dict) -> SearchResult:
        """Parse eBay Finding API item into SearchResult"""
        item_id = item.get('itemId', [''])[0]
        title = item.get('title', [''])[0]

        # Price parsing
        price_info = item.get('sellingStatus', [{}])[0].get('currentPrice', [{}])[0]
        price = float(price_info.get('__value__', 0))

        # Shipping
        shipping_info = item.get('shippingInfo', [{}])[0]
        shipping_cost_info = shipping_info.get('shippingServiceCost', [{}])[0]
        shipping_cost = float(shipping_cost_info.get('__value__', 0)) if shipping_cost_info else 0.0

        # Image
        thumbnail = item.get('galleryURL', [''])[0]

        # URL
        url = item.get('viewItemURL', [''])[0]

        # Condition
        condition_info = item.get('condition', [{}])[0]
        condition = condition_info.get('conditionDisplayName', [''])[0]

        # Time
        time_str = item.get('listingInfo', [{}])[0].get('startTime', [''])[0]
        time_posted = None
        if time_str:
            try:
                time_posted = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            except:
                pass

        return SearchResult(
            platform="eBay",
            listing_id=item_id,
            url=url,
            title=title,
            price=price,
            shipping_cost=shipping_cost if shipping_cost > 0 else None,
            condition=condition,
            thumbnail_url=thumbnail,
            time_posted=time_posted,
            location=item.get('location', [''])[0],
        )

    def _map_sort(self, sort_by: str) -> str:
        """Map generic sort to eBay sort"""
        mapping = {
            'lowest_price': 'PricePlusShippingLowest',
            'newest': 'StartTimeNewest',
            'best_value': 'PricePlusShippingLowest',
            'most_listings': 'BestMatch',
        }
        return mapping.get(sort_by, 'BestMatch')


class EtsySearcher(BasePlatformSearcher):
    """
    Etsy Open API v3 searcher.

    Requires API key in credentials.
    https://developers.etsy.com/documentation/reference#operation/findShops
    """

    BASE_URL = "https://openapi.etsy.com/v3/application/listings/active"

    def get_platform_name(self) -> str:
        return "Etsy"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.API_SEARCH

    def requires_auth(self) -> bool:
        return True

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search Etsy using Open API v3"""
        results = []

        if not self.credentials.get('api_key'):
            print("Etsy search requires API key")
            return results

        headers = {
            'x-api-key': self.credentials['api_key']
        }

        params = {
            'keywords': query.keywords,
            'limit': min(query.limit, 100),
            'sort_on': self._map_sort(query.sort_by),
        }

        if query.min_price is not None:
            params['min_price'] = query.min_price

        if query.max_price is not None:
            params['max_price'] = query.max_price

        try:
            response = requests.get(self.BASE_URL, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            for item in data.get('results', []):
                results.append(self._parse_item(item))

        except Exception as e:
            print(f"Etsy search error: {e}")

        return results

    def _parse_item(self, item: Dict) -> SearchResult:
        """Parse Etsy API item into SearchResult"""
        price = float(item.get('price', {}).get('amount', 0)) / 100  # Etsy returns cents

        return SearchResult(
            platform="Etsy",
            listing_id=str(item.get('listing_id')),
            url=item.get('url', ''),
            title=item.get('title', ''),
            price=price,
            shipping_cost=None,  # Would need separate shipping API call
            condition=None,  # Most Etsy items are handmade/new
            thumbnail_url=item.get('images', [{}])[0].get('url_75x75') if item.get('images') else None,
            quantity_available=item.get('quantity', 1),
        )

    def _map_sort(self, sort_by: str) -> str:
        """Map generic sort to Etsy sort"""
        mapping = {
            'lowest_price': 'price',
            'newest': 'created',
            'best_value': 'score',
            'most_listings': 'score',
        }
        return mapping.get(sort_by, 'score')


class TCGplayerSearcher(BasePlatformSearcher):
    """
    TCGplayer public catalog API.

    Great for trading cards search.
    """

    BASE_URL = "https://api.tcgplayer.com/catalog/products"

    def get_platform_name(self) -> str:
        return "TCGplayer"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.API_SEARCH

    def requires_auth(self) -> bool:
        return True  # Requires bearer token

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search TCGplayer catalog"""
        results = []

        if not self.credentials.get('bearer_token'):
            print("TCGplayer search requires bearer token")
            return results

        headers = {
            'Authorization': f'Bearer {self.credentials["bearer_token"]}'
        }

        params = {
            'productName': query.keywords,
            'limit': min(query.limit, 100),
        }

        try:
            response = requests.get(self.BASE_URL, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            for item in data.get('results', []):
                results.append(self._parse_item(item))

        except Exception as e:
            print(f"TCGplayer search error: {e}")

        return results

    def _parse_item(self, item: Dict) -> SearchResult:
        """Parse TCGplayer item into SearchResult"""
        product_id = item.get('productId')
        url = f"https://www.tcgplayer.com/product/{product_id}"

        return SearchResult(
            platform="TCGplayer",
            listing_id=str(product_id),
            url=url,
            title=item.get('name', ''),
            price=float(item.get('marketPrice', 0)),
            condition=None,
            thumbnail_url=item.get('imageUrl'),
        )


class MercariSearcher(BasePlatformSearcher):
    """
    Mercari public search (no official API).

    Mercari doesn't have a public API, but their search is accessible.
    This would require careful implementation to respect their ToS.
    """

    def get_platform_name(self) -> str:
        return "Mercari"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.SCRAPER_FRIENDLY

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Mercari search implementation.

        Note: This is a placeholder. Real implementation would need to:
        1. Respect Mercari's robots.txt
        2. Use public API if one becomes available
        3. Add rate limiting
        4. Handle Cloudflare/bot detection gracefully
        """
        # TODO: Implement Mercari search if/when compliant method is available
        print("Mercari search not yet implemented")
        return []


class FacebookMarketplaceSearcher(BasePlatformSearcher):
    """
    Facebook Marketplace - No external search allowed.

    Facebook does not permit external search automation.
    """

    def get_platform_name(self) -> str:
        return "Facebook Marketplace"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.NO_EXTERNAL_SEARCH

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """Facebook Marketplace does not support external search"""
        return []


class ShopifySearcher(BasePlatformSearcher):
    """
    Shopify stores are individual - no unified search.

    Each Shopify store has its own domain. There's no central
    Shopify marketplace to search across all stores.
    """

    def get_platform_name(self) -> str:
        return "Shopify"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.NO_EXTERNAL_SEARCH

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """Cannot search across all Shopify stores"""
        return []


# Searcher registry
SEARCHER_REGISTRY = {
    'ebay': eBaySearcher,
    'etsy': EtsySearcher,
    'tcgplayer': TCGplayerSearcher,
    'mercari': MercariSearcher,
    'facebook': FacebookMarketplaceSearcher,
    'shopify': ShopifySearcher,
}


def get_searcher(platform: str, credentials: Optional[Dict] = None) -> Optional[BasePlatformSearcher]:
    """
    Get searcher instance for platform.

    Args:
        platform: Platform name (lowercase)
        credentials: Optional credentials dict

    Returns:
        Searcher instance or None if not available
    """
    searcher_class = SEARCHER_REGISTRY.get(platform.lower())
    if searcher_class:
        return searcher_class(credentials)
    return None
