"""
Discogs CSV Exporter
Converts universal listing format to Discogs inventory CSV format
"""

from typing import Dict, Any, List
from .base_exporter import BaseCSVExporter


class DiscogsExporter(BaseCSVExporter):
    """Exporter for Discogs inventory format"""

    def __init__(self):
        super().__init__()
        self.platform_name = "Discogs"
        self.required_fields = ['title', 'price']
        self.optional_fields = ['condition', 'description', 'quantity']

    def get_field_mapping(self) -> Dict[str, str]:
        """Discogs inventory field mapping"""
        return {
            'release_id': 'release_id',
            'title': 'title',
            'artist': 'artist',
            'format': 'format',
            'price': 'price',
            'media_condition': 'media_condition',
            'sleeve_condition': 'sleeve_condition',
            'comments': 'comments',
            'location': 'location',
            'quantity': 'quantity',
            'allow_offers': 'allow_offers',
        }

    def transform_listing(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        """Transform to Discogs inventory format"""
        attributes = self.parse_attributes(listing.get('attributes', ''))

        # Map condition to Discogs grading (M, NM, VG+, VG, G+, G, F, P)
        condition_map = {
            'new': 'M',
            'mint': 'M',
            'new with tags': 'M',
            'like new': 'NM',
            'near mint': 'NM',
            'excellent': 'VG+',
            'very good plus': 'VG+',
            'very good': 'VG',
            'good plus': 'G+',
            'good': 'G',
            'fair': 'F',
            'poor': 'P',
        }

        condition = listing.get('condition', '').lower()
        discogs_condition = condition_map.get(condition, 'VG')

        return {
            'release_id': attributes.get('discogs_id', '') or attributes.get('release_id', '') or '',
            'title': listing.get('title', '') or '',
            'artist': attributes.get('artist', '') or '',
            'format': attributes.get('format', '') or attributes.get('media_type', '') or '',
            'price': self.format_price(listing.get('price', 0)),
            'media_condition': discogs_condition,
            'sleeve_condition': discogs_condition,  # Default to same as media
            'comments': listing.get('description', '') or '',
            'location': listing.get('storage_location', '') or listing.get('sku', '') or '',
            'quantity': listing.get('quantity', 1) or 1,
            'allow_offers': 'true',
        }
