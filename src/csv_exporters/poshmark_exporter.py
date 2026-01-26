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

        # Poshmark CSV columns - must match exact template headers (capitalized)
        self.required_fields = [
            'Title', 'Description', 'Price', 'Category',
            'Size', 'Brand', 'Condition', 'Color'
        ]
        self.optional_fields = [
            'Quantity', 'SKU', 'Image1', 'Image2',
            'Image3', 'Image4', 'Image5', 'Image6', 'Image7', 'Image8'
        ]

    def get_field_mapping(self) -> Dict[str, str]:
        """Poshmark field mapping - maps database fields to Poshmark headers"""
        return {
            'title': 'Title',
            'description': 'Description',
            'price': 'Price',
            'category': 'Category',
            'size': 'Size',
            'brand': 'Brand',
            'condition': 'Condition',
            'color': 'Color',
            'quantity': 'Quantity',
            'sku': 'SKU',
        }

    def transform_listing(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        """Transform universal listing to Poshmark format"""

        # Parse photos
        photos = self.parse_photos(listing.get('photos', ''))

        # Parse attributes (for brand, size, color stored in JSON)
        attributes = self.parse_attributes(listing.get('attributes', ''))

        # Get brand, size, color - check both direct fields and attributes
        brand = listing.get('brand') or attributes.get('brand', 'Unknown')
        size = listing.get('size') or attributes.get('size', '')
        color = listing.get('color') or attributes.get('color', '')
        subcategory = listing.get('subcategory') or attributes.get('subcategory', '')

        # Build category with subcategory if available (Poshmark format: "Category > Subcategory")
        category = self._map_category(listing.get('category', ''))
        if subcategory:
            category = f"{category} > {subcategory}"

        # Build Poshmark listing with proper capitalized field names
        poshmark_listing = {
            'Title': (listing.get('title', '') or '')[:80],  # Poshmark max 80 chars
            'Description': (listing.get('description', '') or '')[:10000],  # Max 10k chars
            'Price': self.format_price(listing.get('price', 0)),
            'Category': category,
            'Size': size or 'OS',  # Default to One Size if not specified
            'Brand': brand,
            'Condition': self._map_condition(listing.get('condition', '')),
            'Color': color,
            'Quantity': listing.get('quantity', 1) or 1,
            'SKU': listing.get('sku', '') or '',
        }

        # Add up to 8 photos with capitalized field names
        for i in range(8):
            photo_key = f'Image{i+1}'
            poshmark_listing[photo_key] = self.get_photo_url(photos, i)

        return poshmark_listing

    def _map_category(self, category: str) -> str:
        """Map universal category to Poshmark category"""
        if not category:
            return 'Other'
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
        if not condition:
            return 'Good'
        condition_map = {
            'new': 'New with tags',
            'like_new': 'Like new',
            'excellent': 'Excellent',
            'good': 'Good',
            'fair': 'Fair',
            'poor': 'Poor',
            'nwt': 'New with tags',
            'nwot': 'New without tags',
        }
        return condition_map.get(condition.lower(), 'Good')
