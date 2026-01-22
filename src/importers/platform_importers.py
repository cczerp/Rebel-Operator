"""
Platform Listing Importer - Reverse Sync
=========================================
Imports existing listings FROM platforms INTO Rebel Operator.

Supports 2-Way API Sync (14 platforms):
- E-commerce: Shopify, WooCommerce, Square, eBay
- Handmade/Creative: Etsy, Pinterest
- Fashion/Streetwear: Depop
- Social Commerce: Facebook Shops, Google Shopping
- Sneakers/Hype: StockX, GOAT
- Live Selling: Whatnot
- Tech: Swappa
- Luxury Watches: Chrono24

For CSV-only platforms: User uploads CSV exported from platform
"""

import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from abc import ABC, abstractmethod

from ..schema.unified_listing import (
    UnifiedListing,
    Photo,
    Price,
    ListingCondition,
    Category,
    ItemSpecifics,
    SEOData,
)


class BasePlatformImporter(ABC):
    """Base class for all platform importers"""

    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize importer with platform credentials.

        Args:
            credentials: Platform-specific credentials (API keys, tokens, etc.)
        """
        self.credentials = credentials

    @abstractmethod
    def fetch_listings(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch listings from platform.

        Args:
            limit: Maximum number of listings to fetch (None = all)

        Returns:
            List of platform-specific listing dictionaries
        """
        pass

    @abstractmethod
    def transform_to_unified(self, platform_data: Dict[str, Any]) -> UnifiedListing:
        """
        Transform platform-specific listing to UnifiedListing format.

        Args:
            platform_data: Platform-specific listing data

        Returns:
            UnifiedListing object
        """
        pass

    def import_listings(self, limit: Optional[int] = None) -> Tuple[List[UnifiedListing], List[str]]:
        """
        Fetch and transform listings from platform.

        Args:
            limit: Maximum number of listings to import

        Returns:
            Tuple of (successfully_imported_listings, error_messages)
        """
        imported = []
        errors = []

        try:
            # Fetch listings from platform
            platform_listings = self.fetch_listings(limit=limit)

            # Transform each listing
            for platform_data in platform_listings:
                try:
                    unified_listing = self.transform_to_unified(platform_data)
                    imported.append(unified_listing)
                except Exception as e:
                    listing_id = platform_data.get('id', 'unknown')
                    errors.append(f"Failed to transform listing {listing_id}: {str(e)}")

        except Exception as e:
            errors.append(f"Failed to fetch listings: {str(e)}")

        return imported, errors


class eBayImporter(BasePlatformImporter):
    """Import listings from eBay via Trading API"""

    def fetch_listings(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch active listings from eBay"""
        import requests

        # Get OAuth access token
        client_id = self.credentials.get('client_id')
        client_secret = self.credentials.get('client_secret')
        refresh_token = self.credentials.get('refresh_token')

        # Refresh access token
        auth_response = requests.post(
            "https://api.ebay.com/identity/v1/oauth2/token",
            auth=(client_id, client_secret),
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            },
            timeout=10
        )

        if auth_response.status_code != 200:
            raise Exception(f"eBay auth failed: {auth_response.text}")

        access_token = auth_response.json().get('access_token')

        # Fetch inventory items
        url = "https://api.ebay.com/sell/inventory/v1/inventory_item"
        if limit:
            url += f"?limit={limit}"

        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"eBay fetch failed: {response.text}")

        data = response.json()
        return data.get('inventoryItems', [])

    def transform_to_unified(self, platform_data: Dict[str, Any]) -> UnifiedListing:
        """Transform eBay listing to UnifiedListing"""

        product = platform_data.get('product', {})
        availability = platform_data.get('availability', {})
        ship_availability = availability.get('shipToLocationAvailability', {})

        # Extract basic info
        title = product.get('title', '')
        description = product.get('description', '')

        # Price (from offers if available, otherwise 0)
        price_amount = 0.0
        # Note: Full price might be in offers, would need separate API call

        # Quantity
        quantity = ship_availability.get('quantity', 1)

        # Condition mapping
        condition_map = {
            'NEW': ListingCondition.NEW_WITH_TAGS,
            'LIKE_NEW': ListingCondition.EXCELLENT,
            'NEW_OTHER': ListingCondition.NEW_WITHOUT_TAGS,
            'USED_EXCELLENT': ListingCondition.EXCELLENT,
            'USED_VERY_GOOD': ListingCondition.GOOD,
            'USED_GOOD': ListingCondition.GOOD,
            'USED_ACCEPTABLE': ListingCondition.FAIR,
            'FOR_PARTS_OR_NOT_WORKING': ListingCondition.POOR,
        }

        condition_str = platform_data.get('condition', 'USED_GOOD')
        condition = condition_map.get(condition_str, ListingCondition.GOOD)

        # Images
        image_urls = product.get('imageUrls', [])
        photos = [Photo(url=url) for url in image_urls]

        # Item specifics from aspects
        aspects = product.get('aspects', {})
        item_specifics = ItemSpecifics(
            brand=aspects.get('Brand', [''])[0] if 'Brand' in aspects else None,
            model=aspects.get('Model', [''])[0] if 'Model' in aspects else None,
            color=aspects.get('Color', [''])[0] if 'Color' in aspects else None,
            size=aspects.get('Size', [''])[0] if 'Size' in aspects else None,
        )

        # SKU
        sku = platform_data.get('sku', '')

        return UnifiedListing(
            title=title,
            description=description,
            price=Price(amount=price_amount),
            cost=Price(amount=0.0),
            condition=condition,
            photos=photos,
            quantity=quantity,
            sku=sku,
            item_specifics=item_specifics,
            platform_source='ebay',  # Track where it came from
            platform_listing_id=sku,  # eBay uses SKU as identifier
        )


class EtsyImporter(BasePlatformImporter):
    """Import listings from Etsy via API v3"""

    def fetch_listings(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch active listings from Etsy"""
        import requests

        api_key = self.credentials.get('api_key')
        shop_id = self.credentials.get('shop_id')

        url = f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/active"
        if limit:
            url += f"?limit={limit}"

        response = requests.get(
            url,
            headers={"x-api-key": api_key},
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"Etsy fetch failed: {response.text}")

        data = response.json()
        return data.get('results', [])

    def transform_to_unified(self, platform_data: Dict[str, Any]) -> UnifiedListing:
        """Transform Etsy listing to UnifiedListing"""

        # Extract basic info
        title = platform_data.get('title', '')
        description = platform_data.get('description', '')
        price_amount = float(platform_data.get('price', {}).get('amount', 0)) / 100  # Etsy uses cents
        quantity = platform_data.get('quantity', 1)

        # Condition mapping
        # Etsy doesn't have standardized conditions
        condition = ListingCondition.GOOD

        # Would need separate API call to get images
        photos = []

        # SKU
        sku = platform_data.get('sku', '')

        # Category
        category_id = platform_data.get('taxonomy_id')

        return UnifiedListing(
            title=title,
            description=description,
            price=Price(amount=price_amount),
            cost=Price(amount=0.0),
            condition=condition,
            photos=photos,
            quantity=quantity,
            sku=sku,
            platform_source='etsy',
            platform_listing_id=str(platform_data.get('listing_id', '')),
        )


class ShopifyImporter(BasePlatformImporter):
    """Import products from Shopify via Admin API"""

    def fetch_listings(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch products from Shopify"""
        import requests

        store_url = self.credentials.get('store_url')
        access_token = self.credentials.get('access_token')

        # Ensure URL format
        if not store_url.startswith('https://'):
            store_url = f"https://{store_url}"
        if not store_url.endswith('.myshopify.com'):
            store_url = f"{store_url}.myshopify.com"

        url = f"{store_url}/admin/api/2024-01/products.json"
        if limit:
            url += f"?limit={limit}"

        response = requests.get(
            url,
            headers={"X-Shopify-Access-Token": access_token},
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"Shopify fetch failed: {response.text}")

        data = response.json()
        return data.get('products', [])

    def transform_to_unified(self, platform_data: Dict[str, Any]) -> UnifiedListing:
        """Transform Shopify product to UnifiedListing"""

        # Shopify has variants - we'll import the first variant
        variants = platform_data.get('variants', [])
        first_variant = variants[0] if variants else {}

        # Extract basic info
        title = platform_data.get('title', '')
        description = platform_data.get('body_html', '')
        price_amount = float(first_variant.get('price', 0))
        quantity = first_variant.get('inventory_quantity', 1)

        # SKU
        sku = first_variant.get('sku', '')

        # Images
        images = platform_data.get('images', [])
        photos = [Photo(url=img.get('src')) for img in images]

        # Extract brand and other specs from options/tags
        tags = platform_data.get('tags', '').split(',')

        return UnifiedListing(
            title=title,
            description=description,
            price=Price(amount=price_amount),
            cost=Price(amount=0.0),
            condition=ListingCondition.NEW_WITH_TAGS,  # Assume new for Shopify
            photos=photos,
            quantity=quantity,
            sku=sku,
            platform_source='shopify',
            platform_listing_id=str(platform_data.get('id', '')),
        )


class WooCommerceImporter(BasePlatformImporter):
    """Import products from WooCommerce via REST API"""

    def fetch_listings(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch products from WooCommerce"""
        import requests
        from requests.auth import HTTPBasicAuth

        site_url = self.credentials.get('site_url')
        consumer_key = self.credentials.get('consumer_key')
        consumer_secret = self.credentials.get('consumer_secret')

        # Ensure URL format
        if not site_url.startswith('http'):
            site_url = f"https://{site_url}"

        url = f"{site_url}/wp-json/wc/v3/products"
        params = {'per_page': limit if limit else 100, 'status': 'publish'}

        response = requests.get(
            url,
            auth=HTTPBasicAuth(consumer_key, consumer_secret),
            params=params,
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"WooCommerce fetch failed: {response.text}")

        return response.json()

    def transform_to_unified(self, platform_data: Dict[str, Any]) -> UnifiedListing:
        """Transform WooCommerce product to UnifiedListing"""

        title = platform_data.get('name', '')
        description = platform_data.get('description', '')
        price_amount = float(platform_data.get('regular_price', 0) or 0)
        quantity = platform_data.get('stock_quantity', 1) or 1
        sku = platform_data.get('sku', '')

        # Images
        images = platform_data.get('images', [])
        photos = [Photo(url=img.get('src')) for img in images]

        # Condition - WooCommerce doesn't have standard condition field
        condition = ListingCondition.NEW_WITH_TAGS

        return UnifiedListing(
            title=title,
            description=description,
            price=Price(amount=price_amount),
            cost=Price(amount=0.0),
            condition=condition,
            photos=photos,
            quantity=quantity,
            sku=sku,
            platform_source='woocommerce',
            platform_listing_id=str(platform_data.get('id', '')),
        )


class SquareImporter(BasePlatformImporter):
    """Import catalog items from Square via Catalog API"""

    def fetch_listings(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch catalog items from Square"""
        import requests

        access_token = self.credentials.get('access_token')

        url = "https://connect.squareup.com/v2/catalog/list"
        params = {'types': 'ITEM'}
        if limit:
            params['limit'] = limit

        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Square-Version": "2024-01-18"
            },
            params=params,
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"Square fetch failed: {response.text}")

        data = response.json()
        return data.get('objects', [])

    def transform_to_unified(self, platform_data: Dict[str, Any]) -> UnifiedListing:
        """Transform Square catalog item to UnifiedListing"""

        item_data = platform_data.get('item_data', {})
        title = item_data.get('name', '')
        description = item_data.get('description', '')

        # Get first variation for price
        variations = item_data.get('variations', [])
        first_variation = variations[0] if variations else {}
        variation_data = first_variation.get('item_variation_data', {})
        price_money = variation_data.get('price_money', {})
        price_amount = float(price_money.get('amount', 0)) / 100  # Square uses cents

        photos = []
        sku = first_variation.get('item_variation_data', {}).get('sku', '')

        return UnifiedListing(
            title=title,
            description=description,
            price=Price(amount=price_amount),
            cost=Price(amount=0.0),
            condition=ListingCondition.NEW_WITH_TAGS,
            photos=photos,
            quantity=1,
            sku=sku,
            platform_source='square',
            platform_listing_id=platform_data.get('id', ''),
        )


class DepopImporter(BasePlatformImporter):
    """Import listings from Depop via API (requires approval)"""

    def fetch_listings(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch listings from Depop"""
        import requests

        api_key = self.credentials.get('api_key')

        # Note: Depop API endpoints may vary - contact business@depop.com
        url = "https://api.depop.com/v1/products"
        if limit:
            url += f"?limit={limit}"

        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"Depop fetch failed: {response.text}")

        data = response.json()
        return data.get('products', [])

    def transform_to_unified(self, platform_data: Dict[str, Any]) -> UnifiedListing:
        """Transform Depop listing to UnifiedListing"""

        title = platform_data.get('title', '')
        description = platform_data.get('description', '')
        price_amount = float(platform_data.get('price', 0))

        # Photos
        photos_data = platform_data.get('pictures', [])
        photos = [Photo(url=pic.get('url')) for pic in photos_data]

        # Condition mapping
        condition_map = {
            'brand_new': ListingCondition.NEW_WITH_TAGS,
            'like_new': ListingCondition.LIKE_NEW,
            'used': ListingCondition.GOOD,
        }
        condition = condition_map.get(platform_data.get('condition', 'used'), ListingCondition.GOOD)

        return UnifiedListing(
            title=title,
            description=description,
            price=Price(amount=price_amount),
            cost=Price(amount=0.0),
            condition=condition,
            photos=photos,
            quantity=1,
            platform_source='depop',
            platform_listing_id=str(platform_data.get('id', '')),
        )


class PinterestImporter(BasePlatformImporter):
    """Import pins from Pinterest via Pins API v5"""

    def fetch_listings(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch pins from Pinterest"""
        import requests

        access_token = self.credentials.get('access_token')

        url = "https://api.pinterest.com/v5/pins"
        params = {'page_size': limit if limit else 25}

        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"Pinterest fetch failed: {response.text}")

        data = response.json()
        return data.get('items', [])

    def transform_to_unified(self, platform_data: Dict[str, Any]) -> UnifiedListing:
        """Transform Pinterest pin to UnifiedListing"""

        title = platform_data.get('title', '')
        description = platform_data.get('description', '')

        # Pinterest pins don't always have prices
        price_amount = 0.0
        link_data = platform_data.get('link', '')

        # Media
        media = platform_data.get('media', {})
        image_url = media.get('images', {}).get('original', {}).get('url', '')
        photos = [Photo(url=image_url)] if image_url else []

        return UnifiedListing(
            title=title,
            description=description,
            price=Price(amount=price_amount),
            cost=Price(amount=0.0),
            condition=ListingCondition.GOOD,
            photos=photos,
            quantity=1,
            platform_source='pinterest',
            platform_listing_id=platform_data.get('id', ''),
        )


class FacebookShopsImporter(BasePlatformImporter):
    """Import products from Facebook Shops via Graph API"""

    def fetch_listings(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch products from Facebook catalog"""
        import requests

        catalog_id = self.credentials.get('catalog_id')
        access_token = self.credentials.get('access_token')

        url = f"https://graph.facebook.com/v18.0/{catalog_id}/products"
        params = {
            'access_token': access_token,
            'fields': 'id,name,description,price,availability,condition,image_url,url',
            'limit': limit if limit else 100
        }

        response = requests.get(url, params=params, timeout=30)

        if response.status_code != 200:
            raise Exception(f"Facebook fetch failed: {response.text}")

        data = response.json()
        return data.get('data', [])

    def transform_to_unified(self, platform_data: Dict[str, Any]) -> UnifiedListing:
        """Transform Facebook product to UnifiedListing"""

        title = platform_data.get('name', '')
        description = platform_data.get('description', '')

        # Parse price (format: "19.99 USD")
        price_str = platform_data.get('price', '0')
        price_amount = float(price_str.split()[0]) if price_str else 0.0

        # Condition
        condition_map = {
            'new': ListingCondition.NEW_WITH_TAGS,
            'refurbished': ListingCondition.LIKE_NEW,
            'used': ListingCondition.GOOD,
        }
        condition = condition_map.get(platform_data.get('condition', 'new'), ListingCondition.NEW_WITH_TAGS)

        # Photos
        image_url = platform_data.get('image_url', '')
        photos = [Photo(url=image_url)] if image_url else []

        return UnifiedListing(
            title=title,
            description=description,
            price=Price(amount=price_amount),
            cost=Price(amount=0.0),
            condition=condition,
            photos=photos,
            quantity=1,
            platform_source='facebook',
            platform_listing_id=platform_data.get('id', ''),
        )


class GoogleShoppingImporter(BasePlatformImporter):
    """Import products from Google Merchant Center"""

    def fetch_listings(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch products from Google Merchant Center"""
        import requests

        merchant_id = self.credentials.get('merchant_id')
        access_token = self.credentials.get('access_token')

        url = f"https://shoppingcontent.googleapis.com/content/v2.1/{merchant_id}/products"
        params = {'maxResults': limit if limit else 250}

        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"Google Shopping fetch failed: {response.text}")

        data = response.json()
        return data.get('resources', [])

    def transform_to_unified(self, platform_data: Dict[str, Any]) -> UnifiedListing:
        """Transform Google Shopping product to UnifiedListing"""

        title = platform_data.get('title', '')
        description = platform_data.get('description', '')

        # Parse price
        price_data = platform_data.get('price', {})
        price_amount = float(price_data.get('value', 0))

        # Condition
        condition_map = {
            'new': ListingCondition.NEW_WITH_TAGS,
            'refurbished': ListingCondition.LIKE_NEW,
            'used': ListingCondition.GOOD,
        }
        condition = condition_map.get(platform_data.get('condition', 'new'), ListingCondition.NEW_WITH_TAGS)

        # Photos
        image_link = platform_data.get('imageLink', '')
        photos = [Photo(url=image_link)] if image_link else []

        return UnifiedListing(
            title=title,
            description=description,
            price=Price(amount=price_amount),
            cost=Price(amount=0.0),
            condition=condition,
            photos=photos,
            quantity=1,
            platform_source='google',
            platform_listing_id=platform_data.get('id', ''),
        )


class StockXImporter(BasePlatformImporter):
    """Import listings from StockX (requires API access)"""

    def fetch_listings(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch listings from StockX"""
        import requests

        # Note: StockX API access is typically for institutional partners
        # This is a placeholder - actual API endpoints may vary
        api_key = self.credentials.get('api_key')

        url = "https://api.stockx.com/v1/portfolio"
        headers = {
            "x-api-key": api_key,
            "Accept": "application/json"
        }

        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            raise Exception(f"StockX fetch failed: {response.text}")

        data = response.json()
        return data.get('Portfolio', {}).get('Items', [])

    def transform_to_unified(self, platform_data: Dict[str, Any]) -> UnifiedListing:
        """Transform StockX listing to UnifiedListing"""

        product = platform_data.get('product', {})
        title = product.get('title', '')
        description = product.get('description', '')

        # StockX uses market pricing
        market = platform_data.get('market', {})
        price_amount = float(market.get('lastSale', 0))

        # Photos
        media = product.get('media', {})
        image_url = media.get('imageUrl', '')
        photos = [Photo(url=image_url)] if image_url else []

        return UnifiedListing(
            title=title,
            description=description,
            price=Price(amount=price_amount),
            cost=Price(amount=0.0),
            condition=ListingCondition.NEW_WITH_TAGS,  # StockX typically sells new
            photos=photos,
            quantity=1,
            platform_source='stockx',
            platform_listing_id=product.get('id', ''),
        )


class GOATImporter(BasePlatformImporter):
    """Import listings from GOAT (requires API access)"""

    def fetch_listings(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch listings from GOAT"""
        import requests

        # Note: GOAT API access requires partnership
        api_key = self.credentials.get('api_key')

        url = "https://api.goat.com/api/v1/sellers/products"
        headers = {"Authorization": f"Bearer {api_key}"}
        params = {'limit': limit if limit else 100}

        response = requests.get(url, headers=headers, params=params, timeout=30)

        if response.status_code != 200:
            raise Exception(f"GOAT fetch failed: {response.text}")

        data = response.json()
        return data.get('products', [])

    def transform_to_unified(self, platform_data: Dict[str, Any]) -> UnifiedListing:
        """Transform GOAT listing to UnifiedListing"""

        title = platform_data.get('name', '')
        description = platform_data.get('story_html', '')
        price_amount = float(platform_data.get('retail_price_cents', 0)) / 100

        # Photos
        main_picture = platform_data.get('main_picture_url', '')
        photos = [Photo(url=main_picture)] if main_picture else []

        # Item specifics
        item_specifics = ItemSpecifics(
            brand=platform_data.get('brand_name'),
            color=platform_data.get('color'),
            size=platform_data.get('size'),
        )

        return UnifiedListing(
            title=title,
            description=description,
            price=Price(amount=price_amount),
            cost=Price(amount=0.0),
            condition=ListingCondition.NEW_WITH_TAGS,
            photos=photos,
            quantity=1,
            item_specifics=item_specifics,
            platform_source='goat',
            platform_listing_id=str(platform_data.get('id', '')),
        )


class WhatnotImporter(BasePlatformImporter):
    """Import listings from Whatnot (live selling platform)"""

    def fetch_listings(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch listings from Whatnot"""
        import requests

        # Note: Whatnot API access requires seller partnership
        api_key = self.credentials.get('api_key')

        url = "https://api.whatnot.com/v1/listings"
        headers = {"Authorization": f"Bearer {api_key}"}
        params = {'limit': limit if limit else 50}

        response = requests.get(url, headers=headers, params=params, timeout=30)

        if response.status_code != 200:
            raise Exception(f"Whatnot fetch failed: {response.text}")

        data = response.json()
        return data.get('listings', [])

    def transform_to_unified(self, platform_data: Dict[str, Any]) -> UnifiedListing:
        """Transform Whatnot listing to UnifiedListing"""

        title = platform_data.get('title', '')
        description = platform_data.get('description', '')
        price_amount = float(platform_data.get('starting_bid', 0))

        # Photos
        images = platform_data.get('images', [])
        photos = [Photo(url=img) for img in images]

        return UnifiedListing(
            title=title,
            description=description,
            price=Price(amount=price_amount),
            cost=Price(amount=0.0),
            condition=ListingCondition.GOOD,
            photos=photos,
            quantity=1,
            platform_source='whatnot',
            platform_listing_id=str(platform_data.get('id', '')),
        )


class SwappaImporter(BasePlatformImporter):
    """Import listings from Swappa (tech marketplace)"""

    def fetch_listings(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch listings from Swappa"""
        import requests

        # Swappa API requires approval
        api_key = self.credentials.get('api_key')

        url = "https://api.swappa.com/v1/listings"
        headers = {"Authorization": f"Bearer {api_key}"}
        params = {'limit': limit if limit else 100}

        response = requests.get(url, headers=headers, params=params, timeout=30)

        if response.status_code != 200:
            raise Exception(f"Swappa fetch failed: {response.text}")

        data = response.json()
        return data.get('listings', [])

    def transform_to_unified(self, platform_data: Dict[str, Any]) -> UnifiedListing:
        """Transform Swappa listing to UnifiedListing"""

        title = platform_data.get('title', '')
        description = platform_data.get('description', '')
        price_amount = float(platform_data.get('price', 0))

        # Photos
        photos_data = platform_data.get('photos', [])
        photos = [Photo(url=photo.get('url')) for photo in photos_data]

        # Condition
        condition_map = {
            'mint': ListingCondition.LIKE_NEW,
            'good': ListingCondition.GOOD,
            'fair': ListingCondition.FAIR,
        }
        condition = condition_map.get(platform_data.get('condition', 'good'), ListingCondition.GOOD)

        # Item specifics
        item_specifics = ItemSpecifics(
            brand=platform_data.get('manufacturer'),
            model=platform_data.get('model'),
        )

        return UnifiedListing(
            title=title,
            description=description,
            price=Price(amount=price_amount),
            cost=Price(amount=0.0),
            condition=condition,
            photos=photos,
            quantity=1,
            item_specifics=item_specifics,
            platform_source='swappa',
            platform_listing_id=str(platform_data.get('id', '')),
        )


class Chrono24Importer(BasePlatformImporter):
    """Import listings from Chrono24 (luxury watch marketplace)"""

    def fetch_listings(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch listings from Chrono24"""
        import requests

        # Chrono24 API for dealers
        api_key = self.credentials.get('api_key')
        dealer_id = self.credentials.get('dealer_id')

        url = f"https://api.chrono24.com/v1/dealers/{dealer_id}/listings"
        headers = {"Authorization": f"Bearer {api_key}"}
        params = {'limit': limit if limit else 100}

        response = requests.get(url, headers=headers, params=params, timeout=30)

        if response.status_code != 200:
            raise Exception(f"Chrono24 fetch failed: {response.text}")

        data = response.json()
        return data.get('listings', [])

    def transform_to_unified(self, platform_data: Dict[str, Any]) -> UnifiedListing:
        """Transform Chrono24 listing to UnifiedListing"""

        title = platform_data.get('title', '')
        description = platform_data.get('description', '')

        # Price
        price_data = platform_data.get('price', {})
        price_amount = float(price_data.get('amount', 0))

        # Photos
        images = platform_data.get('images', [])
        photos = [Photo(url=img.get('url')) for img in images]

        # Condition
        condition_map = {
            'unworn': ListingCondition.NEW_WITHOUT_TAGS,
            'very_good': ListingCondition.EXCELLENT,
            'good': ListingCondition.GOOD,
            'fair': ListingCondition.FAIR,
        }
        condition = condition_map.get(platform_data.get('condition', 'good'), ListingCondition.GOOD)

        # Item specifics
        item_specifics = ItemSpecifics(
            brand=platform_data.get('brand'),
            model=platform_data.get('model'),
        )

        return UnifiedListing(
            title=title,
            description=description,
            price=Price(amount=price_amount),
            cost=Price(amount=0.0),
            condition=condition,
            photos=photos,
            quantity=1,
            item_specifics=item_specifics,
            platform_source='chrono24',
            platform_listing_id=str(platform_data.get('id', '')),
        )


# Platform importer registry
PLATFORM_IMPORTERS = {
    'ebay': eBayImporter,
    'etsy': EtsyImporter,
    'shopify': ShopifyImporter,
    'woocommerce': WooCommerceImporter,
    'square': SquareImporter,
    'depop': DepopImporter,
    'pinterest': PinterestImporter,
    'facebook': FacebookShopsImporter,
    'facebook shops': FacebookShopsImporter,
    'google shopping': GoogleShoppingImporter,
    'google': GoogleShoppingImporter,
    'stockx': StockXImporter,
    'goat': GOATImporter,
    'whatnot': WhatnotImporter,
    'swappa': SwappaImporter,
    'chrono24': Chrono24Importer,
}


def get_importer(platform: str, credentials: Dict[str, Any]) -> Optional[BasePlatformImporter]:
    """
    Get importer instance for specified platform.

    Args:
        platform: Platform name (ebay, etsy, shopify, etc.)
        credentials: Platform credentials

    Returns:
        Platform importer instance or None if not supported
    """
    importer_class = PLATFORM_IMPORTERS.get(platform.lower())
    if importer_class:
        return importer_class(credentials)
    return None
