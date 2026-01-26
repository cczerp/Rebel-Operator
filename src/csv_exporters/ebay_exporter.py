"""
eBay CSV Exporter
Converts universal listing format to eBay File Exchange CSV format
"""

from typing import Dict, Any, List
from .base_exporter import BaseCSVExporter


class EbayExporter(BaseCSVExporter):
    """Exporter for eBay File Exchange format"""

    def __init__(self):
        super().__init__()
        self.platform_name = "eBay"
        self.required_fields = ['title', 'price']
        self.optional_fields = ['description', 'quantity', 'condition', 'category', 'sku', 'photos']

    def get_field_mapping(self) -> Dict[str, str]:
        """eBay File Exchange field mapping"""
        return {
            'action': 'Action',
            'title': 'Title',
            'description': 'Description',
            'price': 'StartPrice',
            'quantity': 'Quantity',
            'condition': 'ConditionID',
            'category': 'Category',
            'sku': 'CustomLabel',
            'format': 'Format',
            'duration': 'Duration',
            'location': 'Location',
            'shipping_type': 'ShippingType',
            'shipping_service': 'ShippingService-1:Option',
            'shipping_cost': 'ShippingService-1:Cost',
            'photo1': 'PicURL',
        }

    def transform_listing(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        """Transform to eBay File Exchange format"""
        photos = self.parse_photos(listing.get('photos', ''))
        attributes = self.parse_attributes(listing.get('attributes', ''))

        # Map condition to eBay ConditionID
        condition_map = {
            'new': '1000',
            'new with tags': '1000',
            'new without tags': '1500',
            'new with defects': '1750',
            'like new': '2000',
            'excellent': '2500',
            'very good': '3000',
            'good': '4000',
            'acceptable': '5000',
            'fair': '5000',
            'poor': '6000',
            'for parts': '7000',
        }

        condition = listing.get('condition', '').lower()
        condition_id = condition_map.get(condition, '3000')  # Default to "Very Good"

        return {
            'Action': 'Add',
            'Title': (listing.get('title', '') or '')[:80],
            'Description': listing.get('description', '') or '',
            'StartPrice': self.format_price(listing.get('price', 0)),
            'Quantity': listing.get('quantity', 1) or 1,
            'ConditionID': condition_id,
            'Category': listing.get('category', '') or '',
            'CustomLabel': listing.get('sku', '') or '',
            'Format': 'FixedPrice',
            'Duration': 'GTC',
            'Location': listing.get('storage_location', '') or '',
            'ShippingType': 'Flat',
            'ShippingService-1:Option': 'USPSPriority',
            'ShippingService-1:Cost': self.format_price(listing.get('shipping_cost', 0) or 0),
            'PicURL': self.get_photo_url(photos, 0),
        }
