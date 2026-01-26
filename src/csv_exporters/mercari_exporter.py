"""
Mercari CSV Exporter
Converts universal listing format to Mercari-compatible CSV format
Note: Mercari doesn't have official CSV import, but this creates a format
that can be used for manual entry reference or third-party tools
"""

from typing import Dict, Any, List
from .base_exporter import BaseCSVExporter


class MercariExporter(BaseCSVExporter):
    """Exporter for Mercari listing format"""

    def __init__(self):
        super().__init__()
        self.platform_name = "Mercari"
        self.required_fields = ['title', 'price', 'description']
        self.optional_fields = ['condition', 'category', 'brand', 'photos']

    def get_field_mapping(self) -> Dict[str, str]:
        """Mercari field mapping"""
        return {
            'title': 'Title',
            'description': 'Description',
            'price': 'Price',
            'condition': 'Condition',
            'category': 'Category',
            'brand': 'Brand',
            'color': 'Color',
            'size': 'Size',
            'sku': 'SKU',
            'photo1': 'Photo 1',
            'photo2': 'Photo 2',
            'photo3': 'Photo 3',
            'photo4': 'Photo 4',
            'shipping_payer': 'Shipping Payer',
        }

    def transform_listing(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        """Transform to Mercari format"""
        photos = self.parse_photos(listing.get('photos', ''))
        attributes = self.parse_attributes(listing.get('attributes', ''))

        # Map condition to Mercari format
        condition_map = {
            'new': 'New',
            'new with tags': 'New',
            'like new': 'Like new',
            'excellent': 'Like new',
            'good': 'Good',
            'fair': 'Fair',
            'poor': 'Poor',
        }

        condition = listing.get('condition', '').lower()
        mercari_condition = condition_map.get(condition, 'Good')

        return {
            'Title': (listing.get('title', '') or '')[:40],  # Mercari has 40 char limit
            'Description': (listing.get('description', '') or '')[:1000],
            'Price': self.format_price(listing.get('price', 0)),
            'Condition': mercari_condition,
            'Category': listing.get('category', '') or '',
            'Brand': attributes.get('brand', '') or listing.get('brand', '') or '',
            'Color': attributes.get('color', '') or '',
            'Size': attributes.get('size', '') or '',
            'SKU': listing.get('sku', '') or '',
            'Photo 1': self.get_photo_url(photos, 0),
            'Photo 2': self.get_photo_url(photos, 1),
            'Photo 3': self.get_photo_url(photos, 2),
            'Photo 4': self.get_photo_url(photos, 3),
            'Shipping Payer': 'Seller',  # Most common on Mercari
        }
