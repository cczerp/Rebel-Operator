"""
Platform Listing Importer - Reverse Sync
=========================================
Imports existing listings FROM platforms INTO Rebel Operator.

Supports:
- API platforms: eBay, Etsy, Shopify, WooCommerce, TCGplayer
- CSV platforms: User uploads CSV exported from Poshmark, Mercari, etc.
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


# Platform importer registry
PLATFORM_IMPORTERS = {
    'ebay': eBayImporter,
    'etsy': EtsyImporter,
    'shopify': ShopifyImporter,
    # Add more as needed
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
