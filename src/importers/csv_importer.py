"""
CSV Listing Importer
====================
Import listings from platform CSV exports.

Supported Platforms (20):
    Fashion: Poshmark, Mercari, Grailed, Depop, Vinted, Kidizen, Threadup, Tradesy, Curtsy
    Marketplaces: eBay, Bonanza, Facebook, OfferUp, Craigslist
    Collectibles: TCGplayer, Reverb
    E-commerce: Etsy, Shopify, WooCommerce, Square, Amazon

Usage:
    importer = CSVImporter(platform='poshmark')
    listings, errors = importer.import_from_csv(csv_file)
"""

import csv
import io
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

from ..schema.unified_listing import (
    UnifiedListing,
    Photo,
    Price,
    ListingCondition,
    Category,
    ItemSpecifics,
)


class CSVImporter:
    """Import listings from platform CSV exports"""

    # Platform-specific CSV field mappings
    FIELD_MAPPINGS = {
        'poshmark': {
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
            'images': ['Image1', 'Image2', 'Image3', 'Image4', 'Image5', 'Image6', 'Image7', 'Image8'],
        },
        'mercari': {
            'title': 'Title',
            'description': 'Description',
            'price': 'Price',
            'category': 'Category',
            'brand': 'Brand',
            'condition': 'Condition',
            'images': ['Photo1', 'Photo2', 'Photo3', 'Photo4'],
        },
        'grailed': {
            'title': 'Product Name',
            'description': 'Description',
            'price': 'Price',
            'category': 'Category',
            'size': 'Size',
            'brand': 'Designer',
            'condition': 'Condition',
            'color': 'Color',
            'images': ['Photo 1', 'Photo 2', 'Photo 3', 'Photo 4', 'Photo 5'],
        },
        'bonanza': {
            'title': 'Title',
            'description': 'Description',
            'price': 'Price',
            'quantity': 'Quantity',
            'category': 'Category',
            'condition': 'Condition',
            'sku': 'SKU',
            'brand': 'Brand',
            'color': 'Color',
            'size': 'Size',
            'images': ['Image1', 'Image2', 'Image3', 'Image4', 'Image5', 'Image6', 'Image7', 'Image8'],
        },
        'depop': {
            'title': 'Product name',
            'description': 'Description',
            'price': 'Price',
            'category': 'Category',
            'subcategory': 'Subcategory',
            'size': 'Size',
            'brand': 'Brand',
            'condition': 'Condition',
            'color': 'Colour',
            'images': ['Image 1', 'Image 2', 'Image 3', 'Image 4'],
        },
        'vinted': {
            'title': 'Title',
            'description': 'Description',
            'price': 'Price',
            'category': 'Category',
            'size': 'Size',
            'brand': 'Brand',
            'condition': 'Status',
            'color': 'Color',
            'images': ['Photo1', 'Photo2', 'Photo3', 'Photo4', 'Photo5'],
        },
        'kidizen': {
            'title': 'Title',
            'description': 'Description',
            'price': 'Price',
            'category': 'Category',
            'size': 'Size',
            'brand': 'Brand',
            'condition': 'Condition',
            'color': 'Color',
            'gender': 'Gender',
            'images': ['Image1', 'Image2', 'Image3', 'Image4', 'Image5', 'Image6'],
        },
        'ebay': {
            'title': 'Title',
            'description': 'Description',
            'price': 'StartPrice',
            'quantity': 'Quantity',
            'category': 'Category',
            'condition': 'ConditionDescription',
            'sku': 'CustomLabel',
            'brand': 'Brand',
            'upc': 'UPC',
            'images': ['PicURL', 'PicURL2', 'PicURL3', 'PicURL4', 'PicURL5', 'PicURL6', 'PicURL7', 'PicURL8'],
        },
        'etsy': {
            'title': 'Title',
            'description': 'Description',
            'price': 'Price',
            'quantity': 'Quantity',
            'category': 'Category',
            'tags': 'Tags',
            'sku': 'SKU',
            'materials': 'Materials',
            'images': ['Image1', 'Image2', 'Image3', 'Image4', 'Image5', 'Image6', 'Image7', 'Image8', 'Image9', 'Image10'],
        },
        'facebook': {
            'title': 'title',
            'description': 'description',
            'price': 'price',
            'condition': 'condition',
            'brand': 'brand',
            'category': 'product_type',
            'images': ['image_link', 'additional_image_link'],
        },
        'offerup': {
            'title': 'Title',
            'description': 'Description',
            'price': 'Price',
            'category': 'Category',
            'condition': 'Condition',
            'images': ['Photo1', 'Photo2', 'Photo3', 'Photo4', 'Photo5'],
        },
        'tcgplayer': {
            'title': 'Product Name',
            'description': 'Description',
            'price': 'Price',
            'quantity': 'Quantity',
            'condition': 'Condition',
            'sku': 'SKU',
            'set_name': 'Set Name',
            'card_number': 'Card Number',
            'language': 'Language',
        },
        'shopify': {
            'title': 'Title',
            'description': 'Body (HTML)',
            'price': 'Variant Price',
            'quantity': 'Variant Inventory Qty',
            'sku': 'Variant SKU',
            'brand': 'Vendor',
            'category': 'Type',
            'tags': 'Tags',
            'images': ['Image Src'],
        },
        'woocommerce': {
            'title': 'Name',
            'description': 'Description',
            'price': 'Regular price',
            'quantity': 'Stock',
            'sku': 'SKU',
            'category': 'Categories',
            'tags': 'Tags',
            'images': ['Images'],
        },
        'square': {
            'title': 'Item Name',
            'description': 'Description',
            'price': 'Price',
            'category': 'Category',
            'sku': 'SKU',
            'quantity': 'Current Quantity',
            'images': ['Image URL'],
        },
        'threadup': {
            'title': 'Title',
            'description': 'Description',
            'price': 'Price',
            'category': 'Category',
            'size': 'Size',
            'brand': 'Brand',
            'condition': 'Condition',
            'color': 'Color',
            'images': ['Image1', 'Image2', 'Image3', 'Image4'],
        },
        'reverb': {
            'title': 'Title',
            'description': 'Description',
            'price': 'Price',
            'category': 'Category',
            'brand': 'Brand',
            'condition': 'Condition',
            'make': 'Make',
            'model': 'Model',
            'year': 'Year',
            'sku': 'SKU',
            'upc': 'UPC',
            'images': ['Photo1', 'Photo2', 'Photo3', 'Photo4', 'Photo5'],
        },
        'craigslist': {
            'title': 'Title',
            'description': 'Description',
            'price': 'Price',
            'category': 'Category',
            'location': 'Location',
            'images': ['Image1', 'Image2', 'Image3', 'Image4'],
        },
        'amazon': {
            'title': 'item-name',
            'description': 'item-description',
            'price': 'price',
            'quantity': 'quantity',
            'sku': 'sku',
            'brand': 'brand-name',
            'category': 'product-type',
            'upc': 'external-product-id',
            'images': ['main-image-url', 'other-image-url1', 'other-image-url2'],
        },
        'tradesy': {
            'title': 'Title',
            'description': 'Description',
            'price': 'Price',
            'category': 'Category',
            'size': 'Size',
            'brand': 'Brand',
            'condition': 'Condition',
            'color': 'Color',
            'images': ['Image1', 'Image2', 'Image3', 'Image4', 'Image5'],
        },
        'curtsy': {
            'title': 'Title',
            'description': 'Description',
            'price': 'Price',
            'category': 'Category',
            'size': 'Size',
            'brand': 'Brand',
            'condition': 'Condition',
            'color': 'Color',
            'images': ['Photo1', 'Photo2', 'Photo3', 'Photo4'],
        },
    }

    # Condition mappings per platform
    CONDITION_MAPPINGS = {
        'poshmark': {
            'New with tags': ListingCondition.NEW_WITH_TAGS,
            'New without tags': ListingCondition.NEW_WITHOUT_TAGS,
            'Like new': ListingCondition.EXCELLENT,
            'Good': ListingCondition.GOOD,
            'Fair': ListingCondition.FAIR,
            'Poor': ListingCondition.POOR,
        },
        'mercari': {
            'New': ListingCondition.NEW_WITH_TAGS,
            'Like New': ListingCondition.EXCELLENT,
            'Good': ListingCondition.GOOD,
            'Fair': ListingCondition.FAIR,
            'Poor': ListingCondition.POOR,
        },
        'grailed': {
            'New/Never Worn': ListingCondition.NEW_WITH_TAGS,
            'New': ListingCondition.NEW_WITHOUT_TAGS,
            'Gently Used': ListingCondition.EXCELLENT,
            'Used': ListingCondition.GOOD,
            'Well Worn': ListingCondition.FAIR,
            'Damaged': ListingCondition.POOR,
        },
        'bonanza': {
            'New with tags': ListingCondition.NEW_WITH_TAGS,
            'New': ListingCondition.NEW_WITHOUT_TAGS,
            'Pre-owned': ListingCondition.GOOD,
            'Used': ListingCondition.GOOD,
            'For parts or not working': ListingCondition.POOR,
        },
        'depop': {
            'Brand New': ListingCondition.NEW_WITH_TAGS,
            'Like New': ListingCondition.EXCELLENT,
            'Excellent': ListingCondition.EXCELLENT,
            'Good': ListingCondition.GOOD,
            'Fair': ListingCondition.FAIR,
            'Poor': ListingCondition.POOR,
        },
        'vinted': {
            'New with tag': ListingCondition.NEW_WITH_TAGS,
            'New without tag': ListingCondition.NEW_WITHOUT_TAGS,
            'Very good': ListingCondition.EXCELLENT,
            'Good': ListingCondition.GOOD,
            'Satisfactory': ListingCondition.FAIR,
        },
        'kidizen': {
            'New with tags': ListingCondition.NEW_WITH_TAGS,
            'New without tags': ListingCondition.NEW_WITHOUT_TAGS,
            'Excellent used condition': ListingCondition.EXCELLENT,
            'Good used condition': ListingCondition.GOOD,
            'Play condition': ListingCondition.FAIR,
        },
        'ebay': {
            'New with tags': ListingCondition.NEW_WITH_TAGS,
            'New without tags': ListingCondition.NEW_WITHOUT_TAGS,
            'New': ListingCondition.NEW_WITHOUT_TAGS,
            'Like New': ListingCondition.EXCELLENT,
            'Used': ListingCondition.GOOD,
            'Good': ListingCondition.GOOD,
            'Acceptable': ListingCondition.FAIR,
            'For parts or not working': ListingCondition.POOR,
        },
        'etsy': {
            'new': ListingCondition.NEW_WITH_TAGS,
            'like_new': ListingCondition.EXCELLENT,
            'good': ListingCondition.GOOD,
            'fair': ListingCondition.FAIR,
        },
        'facebook': {
            'new': ListingCondition.NEW_WITH_TAGS,
            'used - like new': ListingCondition.EXCELLENT,
            'used - good': ListingCondition.GOOD,
            'used - fair': ListingCondition.FAIR,
        },
        'offerup': {
            'New': ListingCondition.NEW_WITH_TAGS,
            'Like new': ListingCondition.EXCELLENT,
            'Good': ListingCondition.GOOD,
            'Fair': ListingCondition.FAIR,
            'Poor': ListingCondition.POOR,
        },
        'tcgplayer': {
            'Near Mint': ListingCondition.EXCELLENT,
            'Lightly Played': ListingCondition.GOOD,
            'Moderately Played': ListingCondition.FAIR,
            'Heavily Played': ListingCondition.POOR,
            'Damaged': ListingCondition.POOR,
        },
        'shopify': {
            'new': ListingCondition.NEW_WITH_TAGS,
            'used': ListingCondition.GOOD,
            'refurbished': ListingCondition.GOOD,
        },
        'woocommerce': {
            'new': ListingCondition.NEW_WITH_TAGS,
            'used': ListingCondition.GOOD,
            'refurbished': ListingCondition.GOOD,
        },
        'square': {
            'New': ListingCondition.NEW_WITH_TAGS,
            'Used': ListingCondition.GOOD,
            'Refurbished': ListingCondition.GOOD,
        },
        'threadup': {
            'New with tags': ListingCondition.NEW_WITH_TAGS,
            'New without tags': ListingCondition.NEW_WITHOUT_TAGS,
            'Like new': ListingCondition.EXCELLENT,
            'Excellent': ListingCondition.EXCELLENT,
            'Good': ListingCondition.GOOD,
            'Fair': ListingCondition.FAIR,
        },
        'reverb': {
            'Brand New': ListingCondition.NEW_WITH_TAGS,
            'Mint': ListingCondition.NEW_WITHOUT_TAGS,
            'Excellent': ListingCondition.EXCELLENT,
            'Very Good': ListingCondition.GOOD,
            'Good': ListingCondition.GOOD,
            'Fair': ListingCondition.FAIR,
            'Poor': ListingCondition.POOR,
            'Non-functioning': ListingCondition.POOR,
        },
        'craigslist': {
            'new': ListingCondition.NEW_WITH_TAGS,
            'like new': ListingCondition.EXCELLENT,
            'good': ListingCondition.GOOD,
            'fair': ListingCondition.FAIR,
        },
        'amazon': {
            'New': ListingCondition.NEW_WITH_TAGS,
            'Used - Like New': ListingCondition.EXCELLENT,
            'Used - Very Good': ListingCondition.EXCELLENT,
            'Used - Good': ListingCondition.GOOD,
            'Used - Acceptable': ListingCondition.FAIR,
        },
        'tradesy': {
            'New with tags': ListingCondition.NEW_WITH_TAGS,
            'New without tags': ListingCondition.NEW_WITHOUT_TAGS,
            'Excellent': ListingCondition.EXCELLENT,
            'Good': ListingCondition.GOOD,
            'Fair': ListingCondition.FAIR,
        },
        'curtsy': {
            'New with tags': ListingCondition.NEW_WITH_TAGS,
            'New without tags': ListingCondition.NEW_WITHOUT_TAGS,
            'Excellent': ListingCondition.EXCELLENT,
            'Good': ListingCondition.GOOD,
            'Fair': ListingCondition.FAIR,
        },
    }

    def __init__(self, platform: str):
        """
        Initialize CSV importer for specific platform.

        Args:
            platform: Platform name (poshmark, mercari, grailed, etc.)
        """
        self.platform = platform.lower()
        self.field_mapping = self.FIELD_MAPPINGS.get(self.platform, {})
        self.condition_mapping = self.CONDITION_MAPPINGS.get(self.platform, {})

        if not self.field_mapping:
            raise ValueError(f"Platform '{platform}' not supported for CSV import")

    def import_from_file(self, csv_file) -> Tuple[List[UnifiedListing], List[str]]:
        """
        Import listings from uploaded CSV file.

        Args:
            csv_file: File object from request.files

        Returns:
            Tuple of (successfully_imported_listings, error_messages)
        """
        # Read CSV content
        csv_content = csv_file.read().decode('utf-8')
        return self.import_from_string(csv_content)

    def import_from_string(self, csv_content: str) -> Tuple[List[UnifiedListing], List[str]]:
        """
        Import listings from CSV string.

        Args:
            csv_content: CSV content as string

        Returns:
            Tuple of (successfully_imported_listings, error_messages)
        """
        imported = []
        errors = []

        try:
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(csv_content))

            row_num = 1
            for row in csv_reader:
                row_num += 1
                try:
                    listing = self._transform_row(row)
                    imported.append(listing)
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")

        except Exception as e:
            errors.append(f"CSV parsing error: {str(e)}")

        return imported, errors

    def _transform_row(self, row: Dict[str, str]) -> UnifiedListing:
        """Transform CSV row to UnifiedListing"""

        # Extract fields using platform-specific mapping
        title = row.get(self.field_mapping.get('title', ''), '').strip()
        description = row.get(self.field_mapping.get('description', ''), '').strip()

        # Price
        price_str = row.get(self.field_mapping.get('price', ''), '0')
        price_str = price_str.replace('$', '').replace(',', '').strip()
        try:
            price_amount = float(price_str)
        except ValueError:
            price_amount = 0.0

        # Quantity
        quantity_str = row.get(self.field_mapping.get('quantity', ''), '1')
        try:
            quantity = int(quantity_str)
        except ValueError:
            quantity = 1

        # Condition
        condition_str = row.get(self.field_mapping.get('condition', ''), '')
        condition = self.condition_mapping.get(condition_str, ListingCondition.GOOD)

        # SKU
        sku = row.get(self.field_mapping.get('sku', ''), '')

        # Images
        image_fields = self.field_mapping.get('images', [])
        photos = []
        for img_field in image_fields:
            img_url = row.get(img_field, '').strip()
            if img_url:
                photos.append(Photo(url=img_url))

        # Item specifics
        brand = row.get(self.field_mapping.get('brand', ''), '')
        size = row.get(self.field_mapping.get('size', ''), '')
        color = row.get(self.field_mapping.get('color', ''), '')

        item_specifics = ItemSpecifics(
            brand=brand if brand else None,
            size=size if size else None,
            color=color if color else None,
        )

        # Category
        category_str = row.get(self.field_mapping.get('category', ''), '')
        category = None
        if category_str:
            # Parse category (e.g., "Women > Dresses" or "Women")
            parts = [p.strip() for p in category_str.split('>')]
            category = Category(
                primary=parts[0] if len(parts) > 0 else None,
                subcategory=parts[1] if len(parts) > 1 else None,
            )

        # Validation
        if not title:
            raise ValueError("Title is required")

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
            category=category,
            platform_source=self.platform,  # Track import source
        )

    def get_sample_csv(self) -> str:
        """
        Get sample CSV format for this platform.

        Returns:
            Sample CSV string with headers and one example row
        """
        if self.platform == 'poshmark':
            return """Title,Description,Price,Category,Size,Brand,Condition,Color,Quantity,SKU,Image1,Image2,Image3
"Sample Item","Great condition item",45.00,"Women > Tops","M","Nike","Like new","Blue",1,"SKU123","https://example.com/img1.jpg","",""
"""
        elif self.platform == 'mercari':
            return """Title,Description,Price,Category,Brand,Condition,Photo1,Photo2
"Sample Item","Great condition item",45.00,"Women's Tops","Nike","Like New","https://example.com/img1.jpg",""
"""
        else:
            # Generic format
            headers = ','.join(self.field_mapping.values() if isinstance(self.field_mapping.values(), list) else ['Title', 'Description', 'Price'])
            return f"{headers}\n"


def get_supported_platforms() -> List[str]:
    """Get list of platforms that support CSV import"""
    return list(CSVImporter.FIELD_MAPPINGS.keys())


def validate_csv_format(csv_content: str, platform: str) -> Tuple[bool, str]:
    """
    Validate CSV format for platform.

    Args:
        csv_content: CSV content string
        platform: Platform name

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        importer = CSVImporter(platform)
        csv_reader = csv.DictReader(io.StringIO(csv_content))

        # Check headers
        headers = csv_reader.fieldnames
        if not headers:
            return False, "CSV file has no headers"

        # Check required fields exist
        required_fields = [importer.field_mapping.get('title'), importer.field_mapping.get('price')]
        missing_fields = [field for field in required_fields if field and field not in headers]

        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"

        return True, "CSV format is valid"

    except Exception as e:
        return False, f"Validation error: {str(e)}"
