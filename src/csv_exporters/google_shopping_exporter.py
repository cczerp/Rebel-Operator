"""
Google Shopping CSV Exporter
Converts universal listing format to Google Merchant Center feed format
"""

from typing import Dict, Any
from .base_exporter import BaseCSVExporter


class GoogleShoppingExporter(BaseCSVExporter):
    """Exporter for Google Shopping / Google Merchant Center feed"""

    def __init__(self):
        super().__init__()
        self.platform_name = "Google Shopping"

        # Google Shopping required fields
        self.required_fields = [
            'id', 'title', 'description', 'link', 'image_link',
            'price', 'availability', 'condition', 'brand'
        ]
        self.optional_fields = [
            'gtin', 'mpn', 'color', 'size', 'product_type',
            'google_product_category', 'additional_image_link',
            'item_group_id', 'shipping_weight'
        ]

    def get_field_mapping(self) -> Dict[str, str]:
        """Google Shopping field mapping"""
        return {
            'sku': 'id',
            'title': 'title',
            'description': 'description',
            'price': 'price',
            'condition': 'condition',
            'upc': 'gtin',
        }

    def transform_listing(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        """Transform universal listing to Google Shopping format"""

        # Parse photos
        photos = self.parse_photos(listing.get('photos', ''))

        # Parse attributes
        attributes = self.parse_attributes(listing.get('attributes', ''))

        # Get main photo and additional photos
        main_photo = self.get_photo_url(photos, 0)
        additional_photos = ','.join([self.get_photo_url(photos, i) for i in range(1, min(len(photos), 10)) if self.get_photo_url(photos, i)])

        # Build Google Shopping listing
        google_listing = {
            'id': listing.get('sku', listing.get('listing_uuid', '')),
            'title': listing.get('title', '')[:150],  # Max 150 chars
            'description': self._clean_description(listing.get('description', '')),
            'link': f"https://yourstore.com/products/{listing.get('sku', '')}",  # Customize with your store URL
            'image_link': main_photo,
            'additional_image_link': additional_photos,
            'price': f"{self.format_price(listing.get('price', 0))} USD",
            'availability': self._map_availability(listing.get('quantity', 0)),
            'condition': self._map_condition(listing.get('condition', '')),
            'brand': attributes.get('brand', 'Generic'),
            'gtin': listing.get('upc', ''),
            'mpn': listing.get('sku', ''),
            'color': attributes.get('color', ''),
            'size': attributes.get('size', ''),
            'product_type': self._map_category(listing.get('category', '')),
            'google_product_category': self._get_google_category(listing.get('category', '')),
            'item_group_id': attributes.get('item_group_id', ''),
            'shipping_weight': f"{attributes.get('weight', '1')} lb",
        }

        return google_listing

    def _clean_description(self, description: str) -> str:
        """Clean description for Google Shopping (max 5000 chars, no HTML)"""
        # Remove HTML tags
        import re
        clean = re.sub(r'<[^>]+>', '', description)
        return clean[:5000]

    def _map_availability(self, quantity: int) -> str:
        """Map quantity to Google Shopping availability"""
        if quantity > 0:
            return 'in stock'
        else:
            return 'out of stock'

    def _map_condition(self, condition: str) -> str:
        """Map universal condition to Google Shopping condition"""
        condition_map = {
            'new': 'new',
            'like_new': 'refurbished',
            'excellent': 'used',
            'very_good': 'used',
            'good': 'used',
            'fair': 'used',
            'poor': 'used',
            'used': 'used',
            'refurbished': 'refurbished',
        }
        return condition_map.get(condition.lower(), 'used')

    def _map_category(self, category: str) -> str:
        """Map universal category to product type"""
        category_map = {
            'clothing': 'Apparel & Accessories > Clothing',
            'shoes': 'Apparel & Accessories > Shoes',
            'accessories': 'Apparel & Accessories > Accessories',
            'jewelry': 'Apparel & Accessories > Jewelry',
            'electronics': 'Electronics',
            'home': 'Home & Garden',
            'toys': 'Toys & Games',
            'collectibles': 'Collectibles',
            'cards': 'Collectibles > Trading Cards',
            'sports': 'Sporting Goods',
            'books': 'Media > Books',
        }
        return category_map.get(category.lower(), 'Other')

    def _get_google_category(self, category: str) -> str:
        """Map to Google's product taxonomy (numerical ID or name)"""
        # These are examples - use actual Google product taxonomy IDs
        google_categories = {
            'clothing': '166',  # Apparel & Accessories > Clothing
            'shoes': '187',     # Apparel & Accessories > Shoes
            'jewelry': '188',   # Apparel & Accessories > Jewelry
            'electronics': '222',  # Electronics
            'home': '536',      # Home & Garden
            'toys': '1253',     # Toys & Games
            'collectibles': '102',  # Arts & Entertainment > Hobbies & Creative Arts > Collectibles
            'cards': '3908',    # Toys & Games > Games > Card Games > Trading Card Games
        }
        return google_categories.get(category.lower(), '')
