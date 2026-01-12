"""
Poshmark CSV Exporter
Converts universal listing format to Poshmark's bulk upload CSV format
"""

from typing import Dict, Any
from .base_exporter import BaseCSVExporter


class PoshmarkExporter(BaseCSVExporter):
    """Exporter for Poshmark CSV bulk upload"""

    def __init__(self):
        super().__init__()
        self.platform_name = "Poshmark"

        # Poshmark CSV columns
        self.required_fields = [
            'title', 'description', 'price', 'category',
            'subcategory', 'size', 'brand', 'condition'
        ]
        self.optional_fields = [
            'color', 'quantity', 'sku', 'image1', 'image2',
            'image3', 'image4', 'image5', 'image6', 'image7', 'image8'
        ]

    def get_field_mapping(self) -> Dict[str, str]:
        """Poshmark field mapping"""
        return {
            'title': 'title',
            'description': 'description',
            'price': 'price',
            'category': 'category',
            'condition': 'condition',
            'quantity': 'quantity',
            'sku': 'sku',
        }

    def transform_listing(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        """Transform universal listing to Poshmark format"""

        # Parse photos
        photos = self.parse_photos(listing.get('photos', ''))

        # Parse attributes
        attributes = self.parse_attributes(listing.get('attributes', ''))

        # Build Poshmark listing
        poshmark_listing = {
            'title': listing.get('title', '')[:80],  # Poshmark max 80 chars
            'description': listing.get('description', '')[:10000],  # Max 10k chars
            'price': self.format_price(listing.get('price', 0)),
            'category': self._map_category(listing.get('category', '')),
            'subcategory': attributes.get('subcategory', ''),
            'size': attributes.get('size', ''),
            'brand': attributes.get('brand', 'Unknown'),
            'condition': self._map_condition(listing.get('condition', '')),
            'color': attributes.get('color', ''),
            'quantity': listing.get('quantity', 1),
            'sku': listing.get('sku', ''),
        }

        # Add up to 8 photos
        for i in range(8):
            photo_key = f'image{i+1}'
            poshmark_listing[photo_key] = self.get_photo_url(photos, i)

        return poshmark_listing

    def _map_category(self, category: str) -> str:
        """Map universal category to Poshmark category"""
        category_map = {
            'clothing': 'Women',
            'mens_clothing': 'Men',
            'shoes': 'Shoes',
            'accessories': 'Accessories',
            'jewelry': 'Jewelry',
            'bags': 'Bags',
            'home': 'Home',
            'electronics': 'Electronics',
            'toys': 'Toys',
            'collectibles': 'Other',
            'cards': 'Other',
            'sports_cards': 'Other',
        }
        return category_map.get(category.lower(), 'Other')

    def _map_condition(self, condition: str) -> str:
        """Map universal condition to Poshmark condition"""
        condition_map = {
            'new': 'New with tags',
            'like_new': 'Like new',
            'excellent': 'Good',
            'good': 'Good',
            'fair': 'Fair',
            'poor': 'Poor',
            'nwt': 'New with tags',
            'nwot': 'New without tags',
        }
        return condition_map.get(condition.lower(), 'Good')
