"""
Bonanza CSV Exporter
Converts universal listing format to Bonanza's bulk import CSV format
"""

from typing import Dict, Any
from .base_exporter import BaseCSVExporter


class BonanzaExporter(BaseCSVExporter):
    """Exporter for Bonanza CSV bulk import"""

    def __init__(self):
        super().__init__()
        self.platform_name = "Bonanza"

        # Bonanza CSV columns
        self.required_fields = [
            'title', 'description', 'price', 'quantity',
            'category', 'item_condition'
        ]
        self.optional_fields = [
            'sku', 'upc', 'brand', 'color', 'size',
            'shipping_price', 'image_url_1', 'image_url_2',
            'image_url_3', 'image_url_4', 'image_url_5',
            'image_url_6', 'image_url_7', 'image_url_8'
        ]

    def get_field_mapping(self) -> Dict[str, str]:
        """Bonanza field mapping"""
        return {
            'title': 'title',
            'description': 'description',
            'price': 'price',
            'quantity': 'quantity',
            'category': 'category',
            'condition': 'item_condition',
            'sku': 'sku',
            'upc': 'upc',
        }

    def transform_listing(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        """Transform universal listing to Bonanza format"""

        # Parse photos
        photos = self.parse_photos(listing.get('photos', ''))

        # Parse attributes
        attributes = self.parse_attributes(listing.get('attributes', ''))

        # Build Bonanza listing
        bonanza_listing = {
            'title': listing.get('title', '')[:80],  # Max 80 chars
            'description': listing.get('description', ''),
            'price': self.format_price(listing.get('price', 0)),
            'quantity': listing.get('quantity', 1),
            'category': self._map_category(listing.get('category', '')),
            'item_condition': self._map_condition(listing.get('condition', '')),
            'sku': listing.get('sku', ''),
            'upc': listing.get('upc', ''),
            'brand': attributes.get('brand', ''),
            'color': attributes.get('color', ''),
            'size': attributes.get('size', ''),
            'shipping_price': '0.00',  # Free shipping or customize
        }

        # Add up to 8 photos
        for i in range(8):
            photo_key = f'image_url_{i+1}'
            bonanza_listing[photo_key] = self.get_photo_url(photos, i)

        return bonanza_listing

    def _map_category(self, category: str) -> str:
        """Map universal category to Bonanza category"""
        category_map = {
            'clothing': 'Clothing, Shoes & Accessories > Women\'s Clothing',
            'mens_clothing': 'Clothing, Shoes & Accessories > Men\'s Clothing',
            'shoes': 'Clothing, Shoes & Accessories > Shoes',
            'accessories': 'Clothing, Shoes & Accessories > Accessories',
            'jewelry': 'Jewelry & Watches',
            'electronics': 'Consumer Electronics',
            'home': 'Home & Garden',
            'toys': 'Toys & Hobbies',
            'collectibles': 'Collectibles',
            'cards': 'Collectibles > Trading Cards',
            'sports_cards': 'Collectibles > Trading Cards > Sports Cards',
            'antiques': 'Antiques',
            'books': 'Books',
            'music': 'Music',
        }
        return category_map.get(category.lower(), 'Everything Else')

    def _map_condition(self, condition: str) -> str:
        """Map universal condition to Bonanza condition"""
        condition_map = {
            'new': 'New',
            'like_new': 'Like New',
            'excellent': 'Very Good',
            'very_good': 'Very Good',
            'good': 'Good',
            'fair': 'Acceptable',
            'poor': 'For Parts or Not Working',
            'used': 'Used',
            'refurbished': 'Refurbished',
        }
        return condition_map.get(condition.lower(), 'Used')
