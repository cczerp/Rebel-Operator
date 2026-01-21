"""
Listing Import Service
======================
Coordinates importing listings from platforms into Rebel Operator.

Handles:
- API imports (eBay, Etsy, Shopify, etc.)
- CSV imports (Poshmark, Mercari, Grailed, etc.)
- Deduplication
- Database persistence
- Progress tracking
"""

from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import json

from .platform_importers import get_importer, PLATFORM_IMPORTERS
from .csv_importer import CSVImporter
from ..schema.unified_listing import UnifiedListing
from ..database.db import get_connection


class ImportService:
    """Service for importing listings from platforms"""

    def __init__(self, user_id: int):
        """
        Initialize import service.

        Args:
            user_id: User ID who is importing
        """
        self.user_id = user_id

    def import_from_platform_api(
        self,
        platform: str,
        credentials: Dict[str, Any],
        limit: Optional[int] = None
    ) -> Tuple[int, List[str]]:
        """
        Import listings from platform via API.

        Args:
            platform: Platform name (ebay, etsy, shopify, etc.)
            credentials: Platform API credentials
            limit: Maximum number of listings to import

        Returns:
            Tuple of (num_imported, error_messages)
        """
        errors = []

        # Check if platform supports API import
        if platform.lower() not in PLATFORM_IMPORTERS:
            return 0, [f"Platform '{platform}' does not support API import"]

        try:
            # Get platform importer
            importer = get_importer(platform, credentials)
            if not importer:
                return 0, [f"Could not create importer for platform '{platform}'"]

            # Fetch and transform listings
            print(f"📥 Importing listings from {platform}...")
            listings, fetch_errors = importer.import_listings(limit=limit)
            errors.extend(fetch_errors)

            if not listings:
                return 0, errors + ["No listings found to import"]

            # Save to database
            imported_count = 0
            for listing in listings:
                try:
                    # Set import metadata
                    listing.imported_at = datetime.now()

                    # Check for duplicates
                    if self._is_duplicate(listing):
                        print(f"⏭️  Skipping duplicate: {listing.title[:50]}...")
                        continue

                    # Save to database
                    listing_id = self._save_listing(listing)
                    if listing_id:
                        imported_count += 1
                        print(f"✅ Imported: {listing.title[:50]}... (ID: {listing_id})")
                    else:
                        errors.append(f"Failed to save listing: {listing.title[:50]}")

                except Exception as e:
                    errors.append(f"Error saving listing '{listing.title[:30]}': {str(e)}")

            print(f"\n✅ Import complete: {imported_count}/{len(listings)} listings imported")
            return imported_count, errors

        except Exception as e:
            return 0, [f"Import failed: {str(e)}"]

    def import_from_csv(
        self,
        platform: str,
        csv_file
    ) -> Tuple[int, List[str]]:
        """
        Import listings from CSV file.

        Args:
            platform: Platform name (poshmark, mercari, grailed, etc.)
            csv_file: Uploaded CSV file object

        Returns:
            Tuple of (num_imported, error_messages)
        """
        errors = []

        try:
            # Create CSV importer
            importer = CSVImporter(platform)

            # Parse CSV and transform
            print(f"📥 Importing listings from {platform} CSV...")
            listings, parse_errors = importer.import_from_file(csv_file)
            errors.extend(parse_errors)

            if not listings:
                return 0, errors + ["No valid listings found in CSV"]

            # Save to database
            imported_count = 0
            for listing in listings:
                try:
                    # Set import metadata
                    listing.imported_at = datetime.now()

                    # Check for duplicates
                    if self._is_duplicate(listing):
                        print(f"⏭️  Skipping duplicate: {listing.title[:50]}...")
                        continue

                    # Save to database
                    listing_id = self._save_listing(listing)
                    if listing_id:
                        imported_count += 1
                        print(f"✅ Imported: {listing.title[:50]}... (ID: {listing_id})")
                    else:
                        errors.append(f"Failed to save listing: {listing.title[:50]}")

                except Exception as e:
                    errors.append(f"Error saving listing '{listing.title[:30]}': {str(e)}")

            print(f"\n✅ Import complete: {imported_count}/{len(listings)} listings imported")
            return imported_count, errors

        except ValueError as e:
            return 0, [str(e)]
        except Exception as e:
            return 0, [f"CSV import failed: {str(e)}"]

    def _is_duplicate(self, listing: UnifiedListing) -> bool:
        """
        Check if listing already exists in database.

        Checks:
        1. Same platform_source + platform_listing_id
        2. Same SKU (if provided)
        3. Similar title + price

        Args:
            listing: Listing to check

        Returns:
            True if duplicate exists, False otherwise
        """
        conn = get_connection()
        cursor = conn.cursor()

        try:
            # Check 1: Same platform + platform listing ID
            if listing.platform_source and listing.platform_listing_id:
                cursor.execute("""
                    SELECT id FROM listings
                    WHERE user_id = %s
                      AND platform_source = %s
                      AND platform_listing_id = %s
                """, (self.user_id, listing.platform_source, listing.platform_listing_id))

                if cursor.fetchone():
                    return True

            # Check 2: Same SKU
            if listing.sku:
                cursor.execute("""
                    SELECT id FROM listings
                    WHERE user_id = %s
                      AND sku = %s
                """, (self.user_id, listing.sku))

                if cursor.fetchone():
                    return True

            # Check 3: Similar title + price (fuzzy match)
            cursor.execute("""
                SELECT id FROM listings
                WHERE user_id = %s
                  AND LOWER(title) = LOWER(%s)
                  AND ABS(price - %s) < 0.01
            """, (self.user_id, listing.title, listing.price.amount))

            if cursor.fetchone():
                return True

            return False

        finally:
            cursor.close()
            conn.close()

    def _save_listing(self, listing: UnifiedListing) -> Optional[int]:
        """
        Save listing to database.

        Args:
            listing: Listing to save

        Returns:
            Listing ID if successful, None otherwise
        """
        conn = get_connection()
        cursor = conn.cursor()

        try:
            # Prepare data
            photos_json = json.dumps([
                {'url': p.url, 'local_path': p.local_path, 'is_primary': p.is_primary}
                for p in listing.photos
            ])

            platform_statuses = {}
            if listing.platform_source:
                platform_statuses[listing.platform_source] = 'imported'

            # Insert listing
            cursor.execute("""
                INSERT INTO listings (
                    user_id,
                    listing_uuid,
                    title,
                    description,
                    price,
                    cost,
                    condition,
                    photos,
                    quantity,
                    sku,
                    storage_location,
                    platform_statuses,
                    platform_source,
                    platform_listing_id,
                    imported_at,
                    created_at,
                    updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                )
                RETURNING id
            """, (
                self.user_id,
                listing.listing_uuid if hasattr(listing, 'listing_uuid') else None,
                listing.title,
                listing.description,
                listing.price.amount,
                listing.cost.amount if listing.cost else 0.0,
                listing.condition.value,
                photos_json,
                listing.quantity,
                listing.sku,
                listing.storage_location,
                json.dumps(platform_statuses),
                listing.platform_source,
                listing.platform_listing_id,
                listing.imported_at,
            ))

            listing_id = cursor.fetchone()[0]
            conn.commit()

            # TODO: Save item_specifics, category, seo_data to separate tables

            return listing_id

        except Exception as e:
            conn.rollback()
            print(f"Database error: {e}")
            return None

        finally:
            cursor.close()
            conn.close()

    def get_supported_api_platforms(self) -> List[str]:
        """Get list of platforms that support API import"""
        return list(PLATFORM_IMPORTERS.keys())

    def get_supported_csv_platforms(self) -> List[str]:
        """Get list of platforms that support CSV import"""
        from .csv_importer import get_supported_platforms
        return get_supported_platforms()


def import_listings_from_platform(
    user_id: int,
    platform: str,
    credentials: Dict[str, Any],
    limit: Optional[int] = None
) -> Tuple[int, List[str]]:
    """
    Convenience function to import listings from platform API.

    Args:
        user_id: User ID
        platform: Platform name
        credentials: Platform credentials
        limit: Max listings to import

    Returns:
        Tuple of (num_imported, error_messages)
    """
    service = ImportService(user_id)
    return service.import_from_platform_api(platform, credentials, limit)


def import_listings_from_csv(
    user_id: int,
    platform: str,
    csv_file
) -> Tuple[int, List[str]]:
    """
    Convenience function to import listings from CSV.

    Args:
        user_id: User ID
        platform: Platform name
        csv_file: Uploaded CSV file

    Returns:
        Tuple of (num_imported, error_messages)
    """
    service = ImportService(user_id)
    return service.import_from_csv(platform, csv_file)
