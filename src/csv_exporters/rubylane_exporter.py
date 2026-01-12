"""
Ruby Lane CSV Exporter
Converts universal listing format to Ruby Lane's CSV import format
"""

from typing import Dict, Any
from .base_exporter import BaseCSVExporter


class RubyLaneExporter(BaseCSVExporter):
    """Exporter for Ruby Lane CSV import"""

    def __init__(self):
        super().__init__()
        self.platform_name = "Ruby Lane"

        # Ruby Lane CSV columns
        self.required_fields = [
            'Item Title', 'Description', 'Price', 'Quantity',
            'Category', 'Subcategory', 'Condition'
        ]
        self.optional_fields = [
            'SKU', 'Brand', 'Material', 'Color', 'Size',
            'Year', 'Origin', 'Image URL 1', 'Image URL 2',
            'Image URL 3', 'Image URL 4', 'Image URL 5'
        ]

    def get_field_mapping(self) -> Dict[str, str]:
        """Ruby Lane field mapping"""
        return {
            'title': 'Item Title',
            'description': 'Description',
            'price': 'Price',
            'quantity': 'Quantity',
            'category': 'Category',
            'condition': 'Condition',
            'sku': 'SKU',
        }

    def transform_listing(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        """Transform universal listing to Ruby Lane format"""

        # Parse photos
        photos = self.parse_photos(listing.get('photos', ''))

        # Parse attributes
        attributes = self.parse_attributes(listing.get('attributes', ''))

        # Build Ruby Lane listing
        rubylane_listing = {
            'Item Title': listing.get('title', '')[:200],
            'Description': listing.get('description', ''),
            'Price': self.format_price(listing.get('price', 0)),
            'Quantity': listing.get('quantity', 1),
            'Category': self._map_category(listing.get('category', '')),
            'Subcategory': attributes.get('subcategory', ''),
            'Condition': self._map_condition(listing.get('condition', '')),
            'SKU': listing.get('sku', ''),
            'Brand': attributes.get('brand', ''),
            'Material': attributes.get('material', ''),
            'Color': attributes.get('color', ''),
            'Size': attributes.get('size', ''),
            'Year': attributes.get('year', ''),
            'Origin': attributes.get('origin', ''),
        }

        # Add up to 5 photos
        for i in range(5):
            photo_key = f'Image URL {i+1}'
            rubylane_listing[photo_key] = self.get_photo_url(photos, i)

        return rubylane_listing

    def _map_category(self, category: str) -> str:
        """Map universal category to Ruby Lane category"""
        category_map = {
            'collectibles': 'Collectibles',
            'antiques': 'Antiques',
            'jewelry': 'Jewelry',
            'vintage': 'Vintage',
            'art': 'Art',
            'furniture': 'Furniture',
            'dolls': 'Dolls & Bears',
            'toys': 'Toys & Games',
            'china': 'China & Dinnerware',
            'glass': 'Glass',
            'pottery': 'Pottery & Porcelain',
            'cards': 'Collectibles',
        }
        return category_map.get(category.lower(), 'Collectibles')

    def _map_condition(self, condition: str) -> str:
        """Map universal condition to Ruby Lane condition"""
        condition_map = {
            'new': 'Mint',
            'like_new': 'Excellent',
            'excellent': 'Excellent',
            'very_good': 'Very Good',
            'good': 'Good',
            'fair': 'Fair',
            'poor': 'Poor',
        }
        return condition_map.get(condition.lower(), 'Good')
