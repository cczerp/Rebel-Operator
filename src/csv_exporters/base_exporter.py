"""
Base CSV Exporter
Defines the interface for platform-specific CSV exporters
"""

import csv
import io
import json
from typing import List, Dict, Any
from abc import ABC, abstractmethod


class BaseCSVExporter(ABC):
    """Base class for all CSV exporters"""

    def __init__(self):
        self.platform_name = "Unknown"
        self.required_fields = []
        self.optional_fields = []

    @abstractmethod
    def get_field_mapping(self) -> Dict[str, str]:
        """
        Return mapping from universal field names to platform-specific field names

        Example:
        {
            'title': 'Product Title',
            'description': 'Product Description',
            'price': 'Price',
            ...
        }
        """
        pass

    @abstractmethod
    def transform_listing(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a universal listing into platform-specific format

        Args:
            listing: Universal listing format from database

        Returns:
            Dict with platform-specific field names and values
        """
        pass

    def export_to_csv(self, listings: List[Dict[str, Any]]) -> str:
        """
        Export listings to CSV string

        Args:
            listings: List of universal format listings

        Returns:
            CSV file content as string
        """
        if not listings:
            return ""

        # Transform all listings
        transformed = [self.transform_listing(listing) for listing in listings]

        # Get field names from first transformed listing
        if not transformed:
            return ""

        fieldnames = list(transformed[0].keys())

        # Write CSV to string buffer
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(transformed)

        return output.getvalue()

    def parse_photos(self, photos_field: str) -> List[str]:
        """Parse photos field (JSON array or comma-separated)"""
        if not photos_field:
            return []

        try:
            # Try parsing as JSON
            return json.loads(photos_field)
        except (json.JSONDecodeError, TypeError):
            # Fall back to comma-separated
            if isinstance(photos_field, str):
                return [p.strip() for p in photos_field.split(',') if p.strip()]
            return []

    def parse_attributes(self, attributes_field: str) -> Dict[str, Any]:
        """Parse attributes field (JSON object)"""
        if not attributes_field:
            return {}

        try:
            return json.loads(attributes_field)
        except (json.JSONDecodeError, TypeError):
            return {}

    def format_price(self, price: float) -> str:
        """Format price consistently"""
        if price is None:
            return "0.00"
        return f"{float(price):.2f}"

    def get_photo_url(self, photos: List[str], index: int = 0) -> str:
        """Get specific photo URL by index"""
        if photos and len(photos) > index:
            return photos[index]
        return ""
