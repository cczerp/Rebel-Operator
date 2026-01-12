"""
Ecrater CSV Exporter
Converts universal listing format to Ecrater's CSV import format
"""

from typing import Dict, Any
from .base_exporter import BaseCSVExporter


class EcraterExporter(BaseCSVExporter):
    """Exporter for Ecrater CSV import"""

    def __init__(self):
        super().__init__()
        self.platform_name = "Ecrater"

        # Ecrater CSV columns
        self.required_fields = [
            'Title', 'Description', 'Price', 'Quantity',
            'Category', 'Brand', 'Condition'
        ]
        self.optional_fields = [
            'SKU', 'UPC', 'Weight', 'Shipping Price',
            'Image1', 'Image2', 'Image3', 'Image4', 'Image5'
        ]

    def get_field_mapping(self) -> Dict[str, str]:
        """Ecrater field mapping"""
        return {
            'title': 'Title',
            'description': 'Description',
            'price': 'Price',
            'quantity': 'Quantity',
            'category': 'Category',
            'condition': 'Condition',
            'sku': 'SKU',
            'upc': 'UPC',
        }

    def transform_listing(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        """Transform universal listing to Ecrater format"""

        # Parse photos
        photos = self.parse_photos(listing.get('photos', ''))

        # Parse attributes
        attributes = self.parse_attributes(listing.get('attributes', ''))

        # Build Ecrater listing
        ecrater_listing = {
            'Title': listing.get('title', '')[:100],
            'Description': listing.get('description', ''),
            'Price': self.format_price(listing.get('price', 0)),
            'Quantity': listing.get('quantity', 1),
            'Category': self._map_category(listing.get('category', '')),
            'Brand': attributes.get('brand', 'Unbranded'),
            'Condition': self._map_condition(listing.get('condition', '')),
            'SKU': listing.get('sku', ''),
            'UPC': listing.get('upc', ''),
            'Weight': attributes.get('weight', '1.0'),
            'Shipping Price': '0.00',  # Can be customized
        }

        # Add up to 5 photos
        for i in range(5):
            photo_key = f'Image{i+1}'
            ecrater_listing[photo_key] = self.get_photo_url(photos, i)

        return ecrater_listing

    def _map_category(self, category: str) -> str:
        """Map universal category to Ecrater category"""
        category_map = {
            'clothing': 'Clothing, Shoes & Accessories',
            'shoes': 'Clothing, Shoes & Accessories',
            'accessories': 'Clothing, Shoes & Accessories',
            'jewelry': 'Jewelry & Watches',
            'electronics': 'Electronics',
            'home': 'Home & Garden',
            'toys': 'Toys & Hobbies',
            'collectibles': 'Collectibles',
            'cards': 'Collectibles > Trading Cards',
            'sports': 'Sporting Goods',
            'books': 'Books',
            'music': 'Music',
        }
        return category_map.get(category.lower(), 'Everything Else')

    def _map_condition(self, condition: str) -> str:
        """Map universal condition to Ecrater condition"""
        condition_map = {
            'new': 'New',
            'like_new': 'Like New',
            'excellent': 'Very Good',
            'good': 'Good',
            'fair': 'Acceptable',
            'poor': 'Poor',
            'used': 'Used',
        }
        return condition_map.get(condition.lower(), 'Used')
