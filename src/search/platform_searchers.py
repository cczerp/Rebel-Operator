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
from urllib.parse import quote_plus
import json
import re
import os

# Disable proxy to allow direct connections
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

# Configure requests session to bypass proxy
session = requests.Session()
session.trust_env = False  # Don't use environment proxy settings

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("[WARNING] BeautifulSoup4 not installed. Public search platforms will not work.")
    print("[WARNING] Install with: pip install beautifulsoup4")

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

        # Get App ID from credentials or environment variable
        app_id = self.credentials.get('app_id') or os.environ.get('EBAY_PROD_APP_ID')
        if not app_id:
            print("eBay search error: No App ID found in credentials or EBAY_PROD_APP_ID env var")
            return results

        # eBay Finding API parameters
        params = {
            'OPERATION-NAME': 'findItemsAdvanced',
            'SERVICE-VERSION': '1.0.0',
            'SECURITY-APPNAME': app_id,
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
            response = session.get(self.BASE_URL, params=params, timeout=10)
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
            response = session.get(self.BASE_URL, headers=headers, params=params, timeout=10)
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
            response = session.get(self.BASE_URL, headers=headers, params=params, timeout=10)
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
    Mercari public search.

    Mercari has public listings accessible without authentication.
    Their search returns JSON embedded in the page HTML.
    """

    def get_platform_name(self) -> str:
        return "Mercari"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.SCRAPER_FRIENDLY

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search Mercari public listings"""
        if not HAS_BS4:
            print("BeautifulSoup4 required for Mercari search")
            return []

        results = []

        try:
            # Build search URL
            search_url = f"https://www.mercari.com/search/?keyword={quote_plus(query.keywords)}"

            # Add filters
            if query.min_price:
                search_url += f"&price_min={int(query.min_price)}"
            if query.max_price:
                search_url += f"&price_max={int(query.max_price)}"

            # Sort mapping
            sort_map = {
                'newest': 'created_time',
                'lowest_price': 'price_low_to_high',
            }
            if query.sort_by in sort_map:
                search_url += f"&sort={sort_map[query.sort_by]}"

            # Make request with proper User-Agent
            headers = {
                'User-Agent': 'RebelOperator/1.0 (Search Aggregator; +https://rebeloperator.com)'
            }

            response = session.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Mercari embeds JSON data in the page
            script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
            if script_tag:
                data = json.loads(script_tag.string)

                # Navigate to listings
                items = data.get('props', {}).get('pageProps', {}).get('initialState', {}).get('items', {}).get('data', [])

                for item in items[:query.limit]:
                    results.append(self._parse_item(item))

        except Exception as e:
            print(f"Mercari search error: {e}")

        return results

    def _parse_item(self, item: Dict) -> SearchResult:
        """Parse Mercari item from JSON"""
        item_id = item.get('id', '')

        return SearchResult(
            platform="Mercari",
            listing_id=item_id,
            url=f"https://www.mercari.com/us/item/{item_id}/",
            title=item.get('name', ''),
            price=float(item.get('price', 0)),
            shipping_cost=float(item.get('shipping_payer', {}).get('shipping_fee', 0)) if item.get('shipping_payer') else None,
            condition=item.get('item_condition', {}).get('name'),
            thumbnail_url=item.get('photos', [{}])[0].get('thumbnail') if item.get('photos') else None,
        )


class PoshmarkSearcher(BasePlatformSearcher):
    """
    Poshmark public search.

    Poshmark has public listings accessible via search URLs.
    """

    def get_platform_name(self) -> str:
        return "Poshmark"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.SCRAPER_FRIENDLY

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search Poshmark public listings"""
        if not HAS_BS4:
            print("BeautifulSoup4 required for Poshmark search")
            return []

        results = []

        try:
            # Build search URL
            search_url = f"https://poshmark.com/search?query={quote_plus(query.keywords)}"

            # Add filters
            if query.min_price:
                search_url += f"&price_from={int(query.min_price)}"
            if query.max_price:
                search_url += f"&price_to={int(query.max_price)}"

            # Sort
            sort_map = {
                'newest': 'just_in',
                'lowest_price': 'price_low_to_high',
            }
            if query.sort_by in sort_map:
                search_url += f"&sort_by={sort_map[query.sort_by]}"

            headers = {
                'User-Agent': 'RebelOperator/1.0 (Search Aggregator; +https://rebeloperator.com)'
            }

            response = session.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find listing cards
            listing_cards = soup.find_all('div', {'data-test': 'tile'})[:query.limit]

            for card in listing_cards:
                try:
                    # Extract data from card
                    link = card.find('a', href=True)
                    if not link:
                        continue

                    url = f"https://poshmark.com{link['href']}"

                    # Extract listing ID from URL
                    listing_id = re.search(r'/listing/([^/]+)', url)
                    listing_id = listing_id.group(1) if listing_id else ''

                    # Title
                    title_elem = card.find('div', {'data-test': 'tile-title'})
                    title = title_elem.text.strip() if title_elem else ''

                    # Price
                    price_elem = card.find('div', {'data-test': 'tile-price'})
                    price_text = price_elem.text.strip() if price_elem else '$0'
                    price = float(re.sub(r'[^\d.]', '', price_text))

                    # Image
                    img = card.find('img')
                    thumbnail = img.get('src') or img.get('data-src') if img else None

                    results.append(SearchResult(
                        platform="Poshmark",
                        listing_id=listing_id,
                        url=url,
                        title=title,
                        price=price,
                        thumbnail_url=thumbnail,
                    ))

                except Exception as e:
                    print(f"Error parsing Poshmark listing: {e}")
                    continue

        except Exception as e:
            print(f"Poshmark search error: {e}")

        return results


class GrailedSearcher(BasePlatformSearcher):
    """
    Grailed public search.

    Grailed has a GraphQL API that's publicly accessible.
    """

    def get_platform_name(self) -> str:
        return "Grailed"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.SCRAPER_FRIENDLY

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search Grailed using their public GraphQL API"""
        results = []

        try:
            # Grailed uses GraphQL
            graphql_url = "https://www.grailed.com/api/listings"

            params = {
                'query': query.keywords,
                'page': 1,
                'hits_per_page': min(query.limit, 40),
            }

            # Add filters
            if query.min_price:
                params['filters[price_from]'] = int(query.min_price)
            if query.max_price:
                params['filters[price_to]'] = int(query.max_price)

            # Sort
            sort_map = {
                'newest': 'created_at',
                'lowest_price': 'price',
            }
            if query.sort_by in sort_map:
                params['sort'] = sort_map[query.sort_by]

            headers = {
                'User-Agent': 'RebelOperator/1.0 (Search Aggregator; +https://rebeloperator.com)',
                'Accept': 'application/json'
            }

            response = session.get(graphql_url, params=params, headers=headers, timeout=15)
            response.raise_for_status()

            data = response.json()
            items = data.get('data', [])

            for item in items:
                results.append(self._parse_item(item))

        except Exception as e:
            print(f"Grailed search error: {e}")

        return results

    def _parse_item(self, item: Dict) -> SearchResult:
        """Parse Grailed item"""
        listing_id = str(item.get('id', ''))

        return SearchResult(
            platform="Grailed",
            listing_id=listing_id,
            url=f"https://www.grailed.com/listings/{listing_id}",
            title=item.get('title', ''),
            price=float(item.get('price', 0)),
            condition=item.get('condition', ''),
            thumbnail_url=item.get('cover_photo', {}).get('url') if item.get('cover_photo') else None,
        )


class DepopSearcher(BasePlatformSearcher):
    """
    Depop public search.

    Depop has public listings accessible via their API.
    """

    def get_platform_name(self) -> str:
        return "Depop"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.SCRAPER_FRIENDLY

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search Depop public listings"""
        results = []

        try:
            # Depop has a public API endpoint
            api_url = "https://webapi.depop.com/api/v2/search/products/"

            params = {
                'search': query.keywords,
                'limit': min(query.limit, 50),
            }

            # Add price filters
            if query.min_price:
                params['priceFrom'] = int(query.min_price)
            if query.max_price:
                params['priceTo'] = int(query.max_price)

            headers = {
                'User-Agent': 'RebelOperator/1.0 (Search Aggregator; +https://rebeloperator.com)'
            }

            response = session.get(api_url, params=params, headers=headers, timeout=15)
            response.raise_for_status()

            data = response.json()
            products = data.get('products', [])

            for product in products:
                results.append(self._parse_item(product))

        except Exception as e:
            print(f"Depop search error: {e}")

        return results

    def _parse_item(self, item: Dict) -> SearchResult:
        """Parse Depop product"""
        listing_id = str(item.get('id', ''))
        slug = item.get('slug', '')

        return SearchResult(
            platform="Depop",
            listing_id=listing_id,
            url=f"https://www.depop.com/products/{slug}/",
            title=item.get('description', ''),
            price=float(item.get('price', {}).get('priceAmount', 0)),
            condition=item.get('condition', ''),
            thumbnail_url=item.get('preview', {}).get('640') if item.get('preview') else None,
        )


class BonanzaSearcher(BasePlatformSearcher):
    """
    Bonanza public search.

    Bonanza has public listings accessible via search URLs.
    """

    def get_platform_name(self) -> str:
        return "Bonanza"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.SCRAPER_FRIENDLY

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search Bonanza public listings"""
        if not HAS_BS4:
            print("BeautifulSoup4 required for Bonanza search")
            return []

        results = []

        try:
            # Build search URL
            search_url = f"https://www.bonanza.com/listings/search?q={quote_plus(query.keywords)}"

            # Add filters
            if query.min_price:
                search_url += f"&min_price={int(query.min_price)}"
            if query.max_price:
                search_url += f"&max_price={int(query.max_price)}"

            headers = {
                'User-Agent': 'RebelOperator/1.0 (Search Aggregator; +https://rebeloperator.com)'
            }

            response = session.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find listing items
            items = soup.find_all('div', class_='item_image')[:query.limit]

            for item_div in items:
                try:
                    link = item_div.find('a', href=True)
                    if not link:
                        continue

                    url = link['href']
                    if not url.startswith('http'):
                        url = f"https://www.bonanza.com{url}"

                    # Extract ID from URL
                    listing_id = re.search(r'/(\d+)-', url)
                    listing_id = listing_id.group(1) if listing_id else ''

                    # Title from link or nearby element
                    title = link.get('title', '') or link.text.strip()

                    # Find price
                    price_elem = item_div.find_next('span', class_='price')
                    if price_elem:
                        price_text = price_elem.text.strip()
                        price = float(re.sub(r'[^\d.]', '', price_text))
                    else:
                        price = 0.0

                    # Image
                    img = link.find('img')
                    thumbnail = img.get('src') or img.get('data-src') if img else None

                    results.append(SearchResult(
                        platform="Bonanza",
                        listing_id=listing_id,
                        url=url,
                        title=title,
                        price=price,
                        thumbnail_url=thumbnail,
                    ))

                except Exception as e:
                    print(f"Error parsing Bonanza listing: {e}")
                    continue

        except Exception as e:
            print(f"Bonanza search error: {e}")

        return results


class ReverbSearcher(BasePlatformSearcher):
    """
    Reverb API searcher.

    Reverb has an official public API for music gear.
    Requires personal access token.
    https://reverb.com/page/api
    """

    BASE_URL = "https://api.reverb.com/api/listings"

    def get_platform_name(self) -> str:
        return "Reverb"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.API_SEARCH

    def requires_auth(self) -> bool:
        return True

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search Reverb using API"""
        results = []

        if not self.credentials.get('api_token'):
            print("Reverb search requires API token")
            return []

        try:
            headers = {
                'Authorization': f'Bearer {self.credentials["api_token"]}',
                'Accept': 'application/hal+json',
                'Accept-Version': '3.0'
            }

            params = {
                'query': query.keywords,
                'per_page': min(query.limit, 100),
            }

            # Add price filters
            if query.min_price:
                params['price_min'] = int(query.min_price)
            if query.max_price:
                params['price_max'] = int(query.max_price)

            response = session.get(self.BASE_URL, headers=headers, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()
            listings = data.get('listings', [])

            for listing in listings:
                results.append(self._parse_item(listing))

        except Exception as e:
            print(f"Reverb search error: {e}")

        return results

    def _parse_item(self, item: Dict) -> SearchResult:
        """Parse Reverb listing"""
        return SearchResult(
            platform="Reverb",
            listing_id=str(item.get('id', '')),
            url=item.get('_links', {}).get('web', {}).get('href', ''),
            title=item.get('title', ''),
            price=float(item.get('price', {}).get('amount', 0)),
            shipping_cost=float(item.get('shipping', {}).get('us_rate', 0)) if item.get('shipping') else None,
            condition=item.get('condition', {}).get('display_name'),
            thumbnail_url=item.get('photos', [{}])[0].get('_links', {}).get('thumbnail', {}).get('href') if item.get('photos') else None,
        )


class DiscogsSearcher(BasePlatformSearcher):
    """
    Discogs API searcher.

    Discogs has an official API for vinyl, CDs, and music collectibles.
    https://www.discogs.com/developers
    """

    BASE_URL = "https://api.discogs.com/database/search"

    def get_platform_name(self) -> str:
        return "Discogs"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.API_SEARCH

    def requires_auth(self) -> bool:
        return False  # Can use without auth, but has lower rate limits

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search Discogs database"""
        results = []

        try:
            headers = {
                'User-Agent': 'RebelOperator/1.0 +https://rebeloperator.com'
            }

            # Add auth if available
            if self.credentials.get('consumer_key') and self.credentials.get('consumer_secret'):
                headers['Authorization'] = f"Discogs key={self.credentials['consumer_key']}, secret={self.credentials['consumer_secret']}"

            params = {
                'q': query.keywords,
                'per_page': min(query.limit, 100),
            }

            response = session.get(self.BASE_URL, headers=headers, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()
            items = data.get('results', [])

            for item in items:
                results.append(self._parse_item(item))

        except Exception as e:
            print(f"Discogs search error: {e}")

        return results

    def _parse_item(self, item: Dict) -> SearchResult:
        """Parse Discogs search result"""
        return SearchResult(
            platform="Discogs",
            listing_id=str(item.get('id', '')),
            url=item.get('uri', ''),
            title=item.get('title', ''),
            price=0.0,  # Discogs search doesn't include prices, need marketplace API
            thumbnail_url=item.get('thumb', ''),
        )


class RubyLaneSearcher(BasePlatformSearcher):
    """
    Ruby Lane public search.

    Ruby Lane is an antiques and collectibles marketplace with public listings.
    """

    def get_platform_name(self) -> str:
        return "Ruby Lane"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.SCRAPER_FRIENDLY

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search Ruby Lane public listings"""
        if not HAS_BS4:
            print("BeautifulSoup4 required for Ruby Lane search")
            return []

        results = []

        try:
            # Build search URL
            search_url = f"https://www.rubylane.com/search/all?q={quote_plus(query.keywords)}"

            headers = {
                'User-Agent': 'RebelOperator/1.0 (Search Aggregator; +https://rebeloperator.com)'
            }

            response = session.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find listing items
            items = soup.find_all('div', class_='item-box')[:query.limit]

            for item_div in items:
                try:
                    link = item_div.find('a', href=True)
                    if not link:
                        continue

                    url = link['href']
                    if not url.startswith('http'):
                        url = f"https://www.rubylane.com{url}"

                    # Extract ID from URL
                    listing_id = re.search(r'/item/(\d+)', url)
                    listing_id = listing_id.group(1) if listing_id else ''

                    # Title
                    title_elem = item_div.find('div', class_='item-title')
                    title = title_elem.text.strip() if title_elem else ''

                    # Price
                    price_elem = item_div.find('span', class_='item-price')
                    if price_elem:
                        price_text = price_elem.text.strip()
                        price = float(re.sub(r'[^\d.]', '', price_text))
                    else:
                        price = 0.0

                    # Image
                    img = item_div.find('img')
                    thumbnail = img.get('src') or img.get('data-src') if img else None

                    results.append(SearchResult(
                        platform="Ruby Lane",
                        listing_id=listing_id,
                        url=url,
                        title=title,
                        price=price,
                        thumbnail_url=thumbnail,
                    ))

                except Exception as e:
                    print(f"Error parsing Ruby Lane listing: {e}")
                    continue

        except Exception as e:
            print(f"Ruby Lane search error: {e}")

        return results


class VintedSearcher(BasePlatformSearcher):
    """
    Vinted public search.

    Vinted is a secondhand fashion marketplace with public listings.
    """

    def get_platform_name(self) -> str:
        return "Vinted"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.SCRAPER_FRIENDLY

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search Vinted public listings"""
        results = []

        try:
            # Vinted has a public API endpoint
            api_url = "https://www.vinted.com/api/v2/catalog/items"

            params = {
                'search_text': query.keywords,
                'per_page': min(query.limit, 96),
            }

            # Add price filters
            if query.min_price:
                params['price_from'] = int(query.min_price)
            if query.max_price:
                params['price_to'] = int(query.max_price)

            headers = {
                'User-Agent': 'RebelOperator/1.0 (Search Aggregator; +https://rebeloperator.com)'
            }

            response = session.get(api_url, params=params, headers=headers, timeout=15)
            response.raise_for_status()

            data = response.json()
            items = data.get('items', [])

            for item in items:
                results.append(self._parse_item(item))

        except Exception as e:
            print(f"Vinted search error: {e}")

        return results

    def _parse_item(self, item: Dict) -> SearchResult:
        """Parse Vinted item"""
        return SearchResult(
            platform="Vinted",
            listing_id=str(item.get('id', '')),
            url=item.get('url', ''),
            title=item.get('title', ''),
            price=float(item.get('price', 0)),
            condition=item.get('status', ''),
            thumbnail_url=item.get('photo', {}).get('url') if item.get('photo') else None,
        )


class TheRealRealSearcher(BasePlatformSearcher):
    """
    The RealReal public search.

    The RealReal is a luxury consignment marketplace with public listings.
    """

    def get_platform_name(self) -> str:
        return "The RealReal"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.SCRAPER_FRIENDLY

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search The RealReal public listings"""
        if not HAS_BS4:
            print("BeautifulSoup4 required for The RealReal search")
            return []

        results = []

        try:
            # Build search URL
            search_url = f"https://www.therealreal.com/products?query={quote_plus(query.keywords)}"

            headers = {
                'User-Agent': 'RebelOperator/1.0 (Search Aggregator; +https://rebeloperator.com)'
            }

            response = session.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find product cards
            items = soup.find_all('div', {'data-test': 'product-card'})[:query.limit]

            for item_div in items:
                try:
                    link = item_div.find('a', href=True)
                    if not link:
                        continue

                    url = link['href']
                    if not url.startswith('http'):
                        url = f"https://www.therealreal.com{url}"

                    # Extract ID from URL
                    listing_id = re.search(r'/products/([^/]+)', url)
                    listing_id = listing_id.group(1) if listing_id else ''

                    # Title
                    title_elem = item_div.find('h3') or item_div.find('div', {'data-test': 'product-title'})
                    title = title_elem.text.strip() if title_elem else ''

                    # Price
                    price_elem = item_div.find('span', {'data-test': 'product-price'})
                    if price_elem:
                        price_text = price_elem.text.strip()
                        price = float(re.sub(r'[^\d.]', '', price_text))
                    else:
                        price = 0.0

                    # Image
                    img = item_div.find('img')
                    thumbnail = img.get('src') or img.get('data-src') if img else None

                    results.append(SearchResult(
                        platform="The RealReal",
                        listing_id=listing_id,
                        url=url,
                        title=title,
                        price=price,
                        thumbnail_url=thumbnail,
                    ))

                except Exception as e:
                    print(f"Error parsing The RealReal listing: {e}")
                    continue

        except Exception as e:
            print(f"The RealReal search error: {e}")

        return results


class ChairishSearcher(BasePlatformSearcher):
    """
    Chairish public search.

    Chairish is a furniture and home decor marketplace with public listings.
    """

    def get_platform_name(self) -> str:
        return "Chairish"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.SCRAPER_FRIENDLY

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search Chairish public listings"""
        if not HAS_BS4:
            print("BeautifulSoup4 required for Chairish search")
            return []

        results = []

        try:
            # Build search URL
            search_url = f"https://www.chairish.com/search?query={quote_plus(query.keywords)}"

            headers = {
                'User-Agent': 'RebelOperator/1.0 (Search Aggregator; +https://rebeloperator.com)'
            }

            response = session.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find product cards
            items = soup.find_all('div', class_='product-card')[:query.limit]

            for item_div in items:
                try:
                    link = item_div.find('a', href=True)
                    if not link:
                        continue

                    url = link['href']
                    if not url.startswith('http'):
                        url = f"https://www.chairish.com{url}"

                    # Extract ID from URL
                    listing_id = re.search(r'/product/(\d+)', url)
                    listing_id = listing_id.group(1) if listing_id else ''

                    # Title
                    title_elem = item_div.find('div', class_='product-title') or item_div.find('h2')
                    title = title_elem.text.strip() if title_elem else ''

                    # Price
                    price_elem = item_div.find('span', class_='price')
                    if price_elem:
                        price_text = price_elem.text.strip()
                        price = float(re.sub(r'[^\d.]', '', price_text))
                    else:
                        price = 0.0

                    # Image
                    img = item_div.find('img')
                    thumbnail = img.get('src') or img.get('data-src') if img else None

                    results.append(SearchResult(
                        platform="Chairish",
                        listing_id=listing_id,
                        url=url,
                        title=title,
                        price=price,
                        thumbnail_url=thumbnail,
                    ))

                except Exception as e:
                    print(f"Error parsing Chairish listing: {e}")
                    continue

        except Exception as e:
            print(f"Chairish search error: {e}")

        return results


class AmazonSearcher(BasePlatformSearcher):
    """
    Amazon Product Advertising API searcher.

    Requires AWS credentials and Associate Tag.
    https://webservices.amazon.com/paapi5/documentation/
    """

    def get_platform_name(self) -> str:
        return "Amazon"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.API_SEARCH

    def requires_auth(self) -> bool:
        return True

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Search Amazon using Product Advertising API.

        Note: This is a simplified implementation. Full implementation
        would require HMAC-SHA256 signing of requests.
        """
        results = []

        if not self.credentials.get('access_key'):
            print("Amazon search requires PA-API credentials")
            return []

        # Amazon PA-API 5.0 implementation would go here
        # Requires complex request signing, so skipping full implementation
        # for now. This is a placeholder showing the structure.

        print("Amazon PA-API 5.0 requires complex request signing - implement when credentials are available")

        return results


class FashionphileSearcher(BasePlatformSearcher):
    """
    Fashionphile public search.

    Fashionphile is a luxury handbag consignment marketplace.
    """

    def get_platform_name(self) -> str:
        return "Fashionphile"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.SCRAPER_FRIENDLY

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search Fashionphile public listings"""
        if not HAS_BS4:
            print("BeautifulSoup4 required for Fashionphile search")
            return []

        results = []

        try:
            # Build search URL
            search_url = f"https://www.fashionphile.com/shop?search={quote_plus(query.keywords)}"

            headers = {
                'User-Agent': 'RebelOperator/1.0 (Search Aggregator; +https://rebeloperator.com)'
            }

            response = session.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find product items
            items = soup.find_all('div', class_='product-item')[:query.limit]

            for item_div in items:
                try:
                    link = item_div.find('a', href=True)
                    if not link:
                        continue

                    url = link['href']
                    if not url.startswith('http'):
                        url = f"https://www.fashionphile.com{url}"

                    # Extract ID from URL
                    listing_id = re.search(r'/(\d+)', url)
                    listing_id = listing_id.group(1) if listing_id else ''

                    # Title
                    title_elem = item_div.find('div', class_='product-name')
                    title = title_elem.text.strip() if title_elem else ''

                    # Price
                    price_elem = item_div.find('span', class_='product-price')
                    if price_elem:
                        price_text = price_elem.text.strip()
                        price = float(re.sub(r'[^\d.]', '', price_text))
                    else:
                        price = 0.0

                    # Image
                    img = item_div.find('img')
                    thumbnail = img.get('src') or img.get('data-src') if img else None

                    results.append(SearchResult(
                        platform="Fashionphile",
                        listing_id=listing_id,
                        url=url,
                        title=title,
                        price=price,
                        thumbnail_url=thumbnail,
                    ))

                except Exception as e:
                    print(f"Error parsing Fashionphile listing: {e}")
                    continue

        except Exception as e:
            print(f"Fashionphile search error: {e}")

        return results


class RebagSearcher(BasePlatformSearcher):
    """Rebag public search - luxury handbags"""

    def get_platform_name(self) -> str:
        return "Rebag"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.SCRAPER_FRIENDLY

    def search(self, query: SearchQuery) -> List[SearchResult]:
        if not HAS_BS4:
            return []
        results = []
        try:
            search_url = f"https://shop.rebag.com/search?q={quote_plus(query.keywords)}"
            headers = {'User-Agent': 'RebelOperator/1.0 (Search Aggregator; +https://rebeloperator.com)'}
            response = session.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.find_all('div', class_='product-tile')[:query.limit]
            for item_div in items:
                try:
                    link = item_div.find('a', href=True)
                    if not link:
                        continue
                    url = link['href']
                    if not url.startswith('http'):
                        url = f"https://shop.rebag.com{url}"
                    listing_id = re.search(r'/products/([^/]+)', url)
                    listing_id = listing_id.group(1) if listing_id else ''
                    title_elem = item_div.find('div', class_='product-name')
                    title = title_elem.text.strip() if title_elem else ''
                    price_elem = item_div.find('span', class_='price')
                    price = float(re.sub(r'[^\d.]', '', price_elem.text.strip())) if price_elem else 0.0
                    img = item_div.find('img')
                    thumbnail = img.get('src') or img.get('data-src') if img else None
                    results.append(SearchResult(
                        platform="Rebag", listing_id=listing_id, url=url,
                        title=title, price=price, thumbnail_url=thumbnail
                    ))
                except Exception as e:
                    print(f"Error parsing Rebag listing: {e}")
                    continue
        except Exception as e:
            print(f"Rebag search error: {e}")
        return results


class ThredUpSearcher(BasePlatformSearcher):
    """ThredUp public search - secondhand fashion"""

    def get_platform_name(self) -> str:
        return "ThredUp"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.SCRAPER_FRIENDLY

    def search(self, query: SearchQuery) -> List[SearchResult]:
        if not HAS_BS4:
            return []
        results = []
        try:
            search_url = f"https://www.thredup.com/search?search_tags={quote_plus(query.keywords)}"
            headers = {'User-Agent': 'RebelOperator/1.0 (Search Aggregator; +https://rebeloperator.com)'}
            response = session.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.find_all('article', class_='product-card')[:query.limit]
            for item_div in items:
                try:
                    link = item_div.find('a', href=True)
                    if not link:
                        continue
                    url = link['href']
                    if not url.startswith('http'):
                        url = f"https://www.thredup.com{url}"
                    listing_id = re.search(r'/product/(\d+)', url)
                    listing_id = listing_id.group(1) if listing_id else ''
                    title_elem = item_div.find('div', class_='product-title')
                    title = title_elem.text.strip() if title_elem else ''
                    price_elem = item_div.find('span', class_='sale-price')
                    price = float(re.sub(r'[^\d.]', '', price_elem.text.strip())) if price_elem else 0.0
                    img = item_div.find('img')
                    thumbnail = img.get('src') or img.get('data-src') if img else None
                    results.append(SearchResult(
                        platform="ThredUp", listing_id=listing_id, url=url,
                        title=title, price=price, thumbnail_url=thumbnail
                    ))
                except Exception as e:
                    print(f"Error parsing ThredUp listing: {e}")
                    continue
        except Exception as e:
            print(f"ThredUp search error: {e}")
        return results


class CurtsySearcher(BasePlatformSearcher):
    """Curtsy public search - women's fashion"""

    def get_platform_name(self) -> str:
        return "Curtsy"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.SCRAPER_FRIENDLY

    def search(self, query: SearchQuery) -> List[SearchResult]:
        results = []
        try:
            # Curtsy has a public API
            api_url = "https://api.curtsy.com/v2/items/search"
            params = {'q': query.keywords, 'limit': min(query.limit, 50)}
            headers = {'User-Agent': 'RebelOperator/1.0 (Search Aggregator; +https://rebeloperator.com)'}
            response = session.get(api_url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            items = data.get('items', [])
            for item in items:
                results.append(SearchResult(
                    platform="Curtsy",
                    listing_id=str(item.get('id', '')),
                    url=f"https://www.curtsy.com/items/{item.get('id')}",
                    title=item.get('title', ''),
                    price=float(item.get('price', 0)),
                    thumbnail_url=item.get('thumbnail_url')
                ))
        except Exception as e:
            print(f"Curtsy search error: {e}")
        return results


class COMCSearcher(BasePlatformSearcher):
    """COMC public search - sports cards"""

    def get_platform_name(self) -> str:
        return "COMC"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.SCRAPER_FRIENDLY

    def search(self, query: SearchQuery) -> List[SearchResult]:
        if not HAS_BS4:
            return []
        results = []
        try:
            search_url = f"https://www.comc.com/Cards/Search/{quote_plus(query.keywords)}"
            headers = {'User-Agent': 'RebelOperator/1.0 (Search Aggregator; +https://rebeloperator.com)'}
            response = session.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.find_all('div', class_='card-item')[:query.limit]
            for item_div in items:
                try:
                    link = item_div.find('a', href=True)
                    if not link:
                        continue
                    url = link['href']
                    if not url.startswith('http'):
                        url = f"https://www.comc.com{url}"
                    listing_id = re.search(r'/(\d+)', url)
                    listing_id = listing_id.group(1) if listing_id else ''
                    title = link.get('title', '') or item_div.find('span', class_='card-title').text.strip() if item_div.find('span', class_='card-title') else ''
                    price_elem = item_div.find('span', class_='price')
                    price = float(re.sub(r'[^\d.]', '', price_elem.text.strip())) if price_elem else 0.0
                    img = item_div.find('img')
                    thumbnail = img.get('src') or img.get('data-src') if img else None
                    results.append(SearchResult(
                        platform="COMC", listing_id=listing_id, url=url,
                        title=title, price=price, thumbnail_url=thumbnail
                    ))
                except Exception as e:
                    print(f"Error parsing COMC listing: {e}")
                    continue
        except Exception as e:
            print(f"COMC search error: {e}")
        return results


class SportlotsSearcher(BasePlatformSearcher):
    """Sportlots public search - vintage sports cards"""

    def get_platform_name(self) -> str:
        return "Sportlots"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.SCRAPER_FRIENDLY

    def search(self, query: SearchQuery) -> List[SearchResult]:
        if not HAS_BS4:
            return []
        results = []
        try:
            search_url = f"https://www.sportlots.com/search/{quote_plus(query.keywords)}"
            headers = {'User-Agent': 'RebelOperator/1.0 (Search Aggregator; +https://rebeloperator.com)'}
            response = session.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.find_all('tr', class_='listing-row')[:query.limit]
            for item_tr in items:
                try:
                    link = item_tr.find('a', href=True)
                    if not link:
                        continue
                    url = link['href']
                    if not url.startswith('http'):
                        url = f"https://www.sportlots.com{url}"
                    listing_id = re.search(r'lot=(\d+)', url)
                    listing_id = listing_id.group(1) if listing_id else ''
                    title = link.text.strip()
                    price_elem = item_tr.find('td', class_='price')
                    price = float(re.sub(r'[^\d.]', '', price_elem.text.strip())) if price_elem else 0.0
                    results.append(SearchResult(
                        platform="Sportlots", listing_id=listing_id, url=url,
                        title=title, price=price, thumbnail_url=None
                    ))
                except Exception as e:
                    print(f"Error parsing Sportlots listing: {e}")
                    continue
        except Exception as e:
            print(f"Sportlots search error: {e}")
        return results


class MySlabsSearcher(BasePlatformSearcher):
    """MySlabs public search - graded cards"""

    def get_platform_name(self) -> str:
        return "MySlabs"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.SCRAPER_FRIENDLY

    def search(self, query: SearchQuery) -> List[SearchResult]:
        if not HAS_BS4:
            return []
        results = []
        try:
            search_url = f"https://myslabs.com/search?q={quote_plus(query.keywords)}"
            headers = {'User-Agent': 'RebelOperator/1.0 (Search Aggregator; +https://rebeloperator.com)'}
            response = session.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.find_all('div', class_='slab-card')[:query.limit]
            for item_div in items:
                try:
                    link = item_div.find('a', href=True)
                    if not link:
                        continue
                    url = link['href']
                    if not url.startswith('http'):
                        url = f"https://myslabs.com{url}"
                    listing_id = re.search(r'/(\d+)', url)
                    listing_id = listing_id.group(1) if listing_id else ''
                    title_elem = item_div.find('div', class_='slab-title')
                    title = title_elem.text.strip() if title_elem else ''
                    price_elem = item_div.find('span', class_='slab-price')
                    price = float(re.sub(r'[^\d.]', '', price_elem.text.strip())) if price_elem else 0.0
                    img = item_div.find('img')
                    thumbnail = img.get('src') or img.get('data-src') if img else None
                    results.append(SearchResult(
                        platform="MySlabs", listing_id=listing_id, url=url,
                        title=title, price=price, thumbnail_url=thumbnail
                    ))
                except Exception as e:
                    print(f"Error parsing MySlabs listing: {e}")
                    continue
        except Exception as e:
            print(f"MySlabs search error: {e}")
        return results


class AbeBooksSearcher(BasePlatformSearcher):
    """AbeBooks public search - rare books"""

    def get_platform_name(self) -> str:
        return "AbeBooks"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.SCRAPER_FRIENDLY

    def search(self, query: SearchQuery) -> List[SearchResult]:
        if not HAS_BS4:
            return []
        results = []
        try:
            search_url = f"https://www.abebooks.com/servlet/SearchResults?kn={quote_plus(query.keywords)}"
            headers = {'User-Agent': 'RebelOperator/1.0 (Search Aggregator; +https://rebeloperator.com)'}
            response = session.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.find_all('div', class_='result-item')[:query.limit]
            for item_div in items:
                try:
                    link = item_div.find('a', class_='title', href=True)
                    if not link:
                        continue
                    url = link['href']
                    if not url.startswith('http'):
                        url = f"https://www.abebooks.com{url}"
                    listing_id = re.search(r'tn=(\d+)', url)
                    listing_id = listing_id.group(1) if listing_id else ''
                    title = link.text.strip()
                    price_elem = item_div.find('p', class_='item-price')
                    price = float(re.sub(r'[^\d.]', '', price_elem.text.strip())) if price_elem else 0.0
                    img = item_div.find('img', class_='book-img')
                    thumbnail = img.get('src') or img.get('data-src') if img else None
                    results.append(SearchResult(
                        platform="AbeBooks", listing_id=listing_id, url=url,
                        title=title, price=price, thumbnail_url=thumbnail
                    ))
                except Exception as e:
                    print(f"Error parsing AbeBooks listing: {e}")
                    continue
        except Exception as e:
            print(f"AbeBooks search error: {e}")
        return results


class BiblioSearcher(BasePlatformSearcher):
    """Biblio public search - books"""

    def get_platform_name(self) -> str:
        return "Biblio"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.SCRAPER_FRIENDLY

    def search(self, query: SearchQuery) -> List[SearchResult]:
        if not HAS_BS4:
            return []
        results = []
        try:
            search_url = f"https://www.biblio.com/search.php?keyisbn={quote_plus(query.keywords)}"
            headers = {'User-Agent': 'RebelOperator/1.0 (Search Aggregator; +https://rebeloperator.com)'}
            response = session.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.find_all('div', class_='book-item')[:query.limit]
            for item_div in items:
                try:
                    link = item_div.find('a', class_='title', href=True)
                    if not link:
                        continue
                    url = link['href']
                    if not url.startswith('http'):
                        url = f"https://www.biblio.com{url}"
                    listing_id = re.search(r'/(\d+)/', url)
                    listing_id = listing_id.group(1) if listing_id else ''
                    title = link.text.strip()
                    price_elem = item_div.find('span', class_='price')
                    price = float(re.sub(r'[^\d.]', '', price_elem.text.strip())) if price_elem else 0.0
                    img = item_div.find('img')
                    thumbnail = img.get('src') or img.get('data-src') if img else None
                    results.append(SearchResult(
                        platform="Biblio", listing_id=listing_id, url=url,
                        title=title, price=price, thumbnail_url=thumbnail
                    ))
                except Exception as e:
                    print(f"Error parsing Biblio listing: {e}")
                    continue
        except Exception as e:
            print(f"Biblio search error: {e}")
        return results


class CarousellSearcher(BasePlatformSearcher):
    """Carousell public search - Southeast Asia marketplace"""

    def get_platform_name(self) -> str:
        return "Carousell"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.SCRAPER_FRIENDLY

    def search(self, query: SearchQuery) -> List[SearchResult]:
        results = []
        try:
            # Carousell has a public API
            api_url = "https://www.carousell.com/api-service/filter/cf/4.0/search/"
            params = {'query': query.keywords, 'count': min(query.limit, 50)}
            headers = {'User-Agent': 'RebelOperator/1.0 (Search Aggregator; +https://rebeloperator.com)'}
            response = session.get(api_url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            items = data.get('data', {}).get('results', [])
            for item in items:
                results.append(SearchResult(
                    platform="Carousell",
                    listing_id=str(item.get('id', '')),
                    url=f"https://www.carousell.com/p/{item.get('id')}",
                    title=item.get('title', ''),
                    price=float(item.get('price', 0)),
                    thumbnail_url=item.get('photos', [{}])[0].get('thumbnail_url') if item.get('photos') else None
                ))
        except Exception as e:
            print(f"Carousell search error: {e}")
        return results


class WallapopSearcher(BasePlatformSearcher):
    """Wallapop public search - European classifieds"""

    def get_platform_name(self) -> str:
        return "Wallapop"

    def get_search_capability(self) -> SearchCapability:
        return SearchCapability.SCRAPER_FRIENDLY

    def search(self, query: SearchQuery) -> List[SearchResult]:
        results = []
        try:
            # Wallapop has a public search API
            api_url = "https://api.wallapop.com/api/v3/general/search"
            params = {'keywords': query.keywords, 'start': 0, 'end': min(query.limit, 40)}
            headers = {'User-Agent': 'RebelOperator/1.0 (Search Aggregator; +https://rebeloperator.com)'}
            response = session.get(api_url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            items = data.get('search_objects', [])
            for item in items:
                results.append(SearchResult(
                    platform="Wallapop",
                    listing_id=str(item.get('id', '')),
                    url=f"https://us.wallapop.com/item/{item.get('web_slug')}",
                    title=item.get('title', ''),
                    price=float(item.get('price', 0)),
                    thumbnail_url=item.get('images', [{}])[0].get('medium') if item.get('images') else None
                ))
        except Exception as e:
            print(f"Wallapop search error: {e}")
        return results


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
    # Official APIs (6)
    'ebay': eBaySearcher,
    'etsy': EtsySearcher,
    'tcgplayer': TCGplayerSearcher,
    'reverb': ReverbSearcher,
    'discogs': DiscogsSearcher,
    'amazon': AmazonSearcher,  # Requires PA-API credentials

    # Public Search (20)
    'mercari': MercariSearcher,
    'poshmark': PoshmarkSearcher,
    'grailed': GrailedSearcher,
    'depop': DepopSearcher,
    'bonanza': BonanzaSearcher,
    'rubylane': RubyLaneSearcher,
    'vinted': VintedSearcher,
    'therealreal': TheRealRealSearcher,
    'chairish': ChairishSearcher,
    'fashionphile': FashionphileSearcher,
    'rebag': RebagSearcher,
    'thredup': ThredUpSearcher,
    'curtsy': CurtsySearcher,
    'comc': COMCSearcher,
    'sportlots': SportlotsSearcher,
    'myslabs': MySlabsSearcher,
    'abebooks': AbeBooksSearcher,
    'biblio': BiblioSearcher,
    'carousell': CarousellSearcher,
    'wallapop': WallapopSearcher,

    # Unavailable
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
