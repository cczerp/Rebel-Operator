"""
Master Ledger CSV Exporters
============================
Export functions for all 4 master ledgers.
"""

import csv
import io
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

from ..database.db import get_db


class LedgerCSVExporter:
    """Base class for ledger CSV exporters"""

    @staticmethod
    def _format_decimal(value: Optional[Decimal]) -> str:
        """Format decimal for CSV"""
        if value is None:
            return ""
        return f"{float(value):.2f}"

    @staticmethod
    def _format_date(value: Optional[datetime]) -> str:
        """Format datetime for CSV"""
        if value is None:
            return ""
        return value.strftime("%Y-%m-%d")

    @staticmethod
    def _format_datetime(value: Optional[datetime]) -> str:
        """Format datetime with time for CSV"""
        if value is None:
            return ""
        return value.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _parse_json(value: Optional[str], default=None) -> Any:
        """Parse JSON string safely"""
        if not value:
            return default or []
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return default or []


# ============================================================================
# 1️⃣ INVENTORY MASTER LEDGER EXPORTER
# ============================================================================

class InventoryMasterExporter(LedgerCSVExporter):
    """Export Inventory Master Ledger to CSV"""

    COLUMNS = [
        'MasterItemID',
        'SKU',
        'AutoSKU',
        'Title',
        'Description',
        'Price',
        'Category',
        'Subcategory',
        'Brand',
        'Model',
        'Color',
        'Size',
        'Condition',
        'Measurements',        # JSON
        'Variants',            # JSON array
        'Quantity',
        'StorageLocation',
        'Status',
        'CostBasis',
        'Currency',
        'PlatformListingIDs',  # JSON
        'Photos',              # JSON array
        'Notes',
        'AcquiredDate',
        'CreatedAt',
        'UpdatedAt',
    ]

    @staticmethod
    def export_to_csv(user_id: int, filters: Optional[Dict] = None) -> str:
        """
        Export inventory master ledger to CSV string.

        Args:
            user_id: User ID
            filters: Optional filters (status, category, etc.)

        Returns:
            CSV string
        """
        db = get_db()
        cursor = db._get_cursor()

        # Build query with filters
        query = """
            SELECT
                master_item_id,
                sku,
                auto_sku,
                title,
                description,
                price,
                category,
                subcategory,
                brand,
                model,
                color,
                size,
                condition,
                measurements,
                variants,
                quantity,
                storage_location,
                status,
                cost_basis,
                currency,
                platform_listing_ids,
                photos,
                notes,
                acquired_date,
                created_at,
                updated_at
            FROM inventory_master
            WHERE user_id = %s::INTEGER
        """
        params = [user_id]

        if filters:
            if filters.get('status'):
                query += " AND status = %s"
                params.append(filters['status'])
            if filters.get('category'):
                query += " AND category = %s"
                params.append(filters['category'])
            if filters.get('storage_location'):
                query += " AND storage_location = %s"
                params.append(filters['storage_location'])

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(InventoryMasterExporter.COLUMNS)

        for row in rows:
            writer.writerow([
                row[0],  # master_item_id
                row[1] or "",  # sku
                "TRUE" if row[2] else "FALSE",  # auto_sku
                row[3] or "",  # title
                row[4] or "",  # description
                InventoryMasterExporter._format_decimal(row[5]),  # price
                row[6] or "",  # category
                row[7] or "",  # subcategory
                row[8] or "",  # brand
                row[9] or "",  # model
                row[10] or "",  # color
                row[11] or "",  # size
                row[12] or "",  # condition
                row[13] or "",  # measurements (JSON)
                row[14] or "",  # variants (JSON)
                row[15] or 1,  # quantity
                row[16] or "",  # storage_location
                row[17] or "available",  # status
                InventoryMasterExporter._format_decimal(row[18]),  # cost_basis
                row[19] or "USD",  # currency
                row[20] or "",  # platform_listing_ids
                row[21] or "",  # photos
                row[22] or "",  # notes
                InventoryMasterExporter._format_date(row[23]),  # acquired_date
                InventoryMasterExporter._format_datetime(row[24]),  # created_at
                InventoryMasterExporter._format_datetime(row[25]),  # updated_at
            ])

        cursor.close()

        return output.getvalue()


# ============================================================================
# 2️⃣ SALES & REVENUE LEDGER EXPORTER
# ============================================================================

class SalesLedgerExporter(LedgerCSVExporter):
    """Export Sales & Revenue Ledger to CSV"""

    COLUMNS = [
        'TransactionID',
        'MasterItemID',
        'Platform',
        'PlatformOrderID',
        'PlatformListingID',
        'SaleDate',
        'PayoutDate',
        'Currency',
        'GrossSaleAmount',
        'PlatformFees',
        'PaymentProcessingFees',
        'ShippingCost',
        'ShippingCharged',
        'TaxCollected',
        'NetPayout',
        'CostBasis',
        'COGS',  # Same as CostBasis but explicit for accounting
        'Profit',
        'BuyerUsername',
        'BuyerLocation',
        'PayoutStatus',
        'ShippingLabelURL',
        'ItemStorageLocation',
        'DelistingScheduledAt',
        'DelistedAt',
        'AutoDelisted',
        'Notes',
    ]

    @staticmethod
    def export_to_csv(user_id: int, filters: Optional[Dict] = None) -> str:
        """
        Export sales ledger to CSV string.

        Args:
            user_id: User ID
            filters: Optional filters (platform, date_range, etc.)

        Returns:
            CSV string
        """
        db = get_db()
        cursor = db._get_cursor()

        query = """
            SELECT
                transaction_id,
                master_item_id,
                platform,
                platform_order_id,
                platform_listing_id,
                sale_date,
                payout_date,
                currency,
                gross_sale_amount,
                platform_fees,
                payment_processing_fees,
                shipping_cost,
                shipping_charged,
                tax_collected,
                net_payout,
                cost_basis,
                cogs,
                profit,
                buyer_username,
                buyer_location,
                payout_status,
                shipping_label_url,
                item_storage_location,
                delisting_scheduled_at,
                delisted_at,
                auto_delisted,
                notes
            FROM sales_ledger
            WHERE user_id = %s::INTEGER
        """
        params = [user_id]

        if filters:
            if filters.get('platform'):
                query += " AND platform = %s"
                params.append(filters['platform'])
            if filters.get('start_date'):
                query += " AND sale_date >= %s"
                params.append(filters['start_date'])
            if filters.get('end_date'):
                query += " AND sale_date <= %s"
                params.append(filters['end_date'])
            if filters.get('payout_status'):
                query += " AND payout_status = %s"
                params.append(filters['payout_status'])

        query += " ORDER BY sale_date DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(SalesLedgerExporter.COLUMNS)

        for row in rows:
            writer.writerow([
                row[0],  # transaction_id
                row[1] or "",  # master_item_id
                row[2],  # platform
                row[3] or "",  # platform_order_id
                row[4] or "",  # platform_listing_id
                SalesLedgerExporter._format_datetime(row[5]),  # sale_date
                SalesLedgerExporter._format_datetime(row[6]),  # payout_date
                row[7] or "USD",  # currency
                SalesLedgerExporter._format_decimal(row[8]),  # gross_sale_amount
                SalesLedgerExporter._format_decimal(row[9]),  # platform_fees
                SalesLedgerExporter._format_decimal(row[10]),  # payment_processing_fees
                SalesLedgerExporter._format_decimal(row[11]),  # shipping_cost
                SalesLedgerExporter._format_decimal(row[12]),  # shipping_charged
                SalesLedgerExporter._format_decimal(row[13]),  # tax_collected
                SalesLedgerExporter._format_decimal(row[14]),  # net_payout
                SalesLedgerExporter._format_decimal(row[15]),  # cost_basis
                SalesLedgerExporter._format_decimal(row[16]),  # cogs
                SalesLedgerExporter._format_decimal(row[17]),  # profit
                row[18] or "",  # buyer_username
                row[19] or "",  # buyer_location
                row[20] or "",  # payout_status
                row[21] or "",  # shipping_label_url
                row[22] or "",  # item_storage_location
                SalesLedgerExporter._format_datetime(row[23]),  # delisting_scheduled_at
                SalesLedgerExporter._format_datetime(row[24]),  # delisted_at
                "TRUE" if row[25] else "FALSE",  # auto_delisted
                row[26] or "",  # notes
            ])

        cursor.close()

        return output.getvalue()


# ============================================================================
# 3️⃣ SHIPPING & FULFILLMENT LEDGER EXPORTER
# ============================================================================

class ShippingLedgerExporter(LedgerCSVExporter):
    """Export Shipping & Fulfillment Ledger to CSV"""

    COLUMNS = [
        'ShipmentID',
        'MasterItemID',
        'TransactionID',
        'Carrier',
        'ServiceType',
        'TrackingNumber',
        'LabelSource',
        'ShippingLabelURL',
        'LabelFormat',
        'LabelCreatedDate',
        'ShipDate',
        'ExpectedDeliveryDate',
        'ActualDeliveryDate',
        'ShippingCost',
        'InsuranceCost',
        'Currency',
        'WeightOz',
        'Dimensions',
        'PackageType',
        'DeliveryStatus',
        'DeliveryProof',
        'IssueReported',
        'IssueType',
        'IssueResolution',
        'InsuranceClaimFiled',
        'ClaimAmount',
        'ShipToAddress',
        'ShipFromAddress',
        'Notes',
    ]

    @staticmethod
    def export_to_csv(user_id: int, filters: Optional[Dict] = None) -> str:
        """
        Export shipping ledger to CSV string.

        Args:
            user_id: User ID
            filters: Optional filters (carrier, status, etc.)

        Returns:
            CSV string
        """
        db = get_db()
        cursor = db._get_cursor()

        query = """
            SELECT
                shipment_id,
                master_item_id,
                transaction_id,
                carrier,
                service_type,
                tracking_number,
                label_source,
                label_created_date,
                ship_date,
                expected_delivery_date,
                actual_delivery_date,
                shipping_cost,
                insurance_cost,
                currency,
                weight_oz,
                dimensions,
                package_type,
                delivery_status,
                delivery_proof,
                issue_reported,
                issue_type,
                issue_resolution,
                insurance_claim_filed,
                claim_amount,
                ship_to_address,
                ship_from_address,
                notes
            FROM shipping_ledger
            WHERE user_id = %s::INTEGER
        """
        params = [user_id]

        if filters:
            if filters.get('carrier'):
                query += " AND carrier = %s"
                params.append(filters['carrier'])
            if filters.get('delivery_status'):
                query += " AND delivery_status = %s"
                params.append(filters['delivery_status'])
            if filters.get('issue_reported'):
                query += " AND issue_reported = TRUE"

        query += " ORDER BY ship_date DESC NULLS LAST"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(ShippingLedgerExporter.COLUMNS)

        for row in rows:
            writer.writerow([
                row[0],  # shipment_id
                row[1] or "",  # master_item_id
                row[2] or "",  # transaction_id
                row[3],  # carrier
                row[4] or "",  # service_type
                row[5] or "",  # tracking_number
                row[6] or "",  # label_source
                ShippingLedgerExporter._format_date(row[7]),  # label_created_date
                ShippingLedgerExporter._format_date(row[8]),  # ship_date
                ShippingLedgerExporter._format_date(row[9]),  # expected_delivery_date
                ShippingLedgerExporter._format_date(row[10]),  # actual_delivery_date
                ShippingLedgerExporter._format_decimal(row[11]),  # shipping_cost
                ShippingLedgerExporter._format_decimal(row[12]),  # insurance_cost
                row[13] or "USD",  # currency
                ShippingLedgerExporter._format_decimal(row[14]),  # weight_oz
                row[15] or "",  # dimensions
                row[16] or "",  # package_type
                row[17] or "",  # delivery_status
                row[18] or "",  # delivery_proof
                "TRUE" if row[19] else "FALSE",  # issue_reported
                row[20] or "",  # issue_type
                row[21] or "",  # issue_resolution
                "TRUE" if row[22] else "FALSE",  # insurance_claim_filed
                ShippingLedgerExporter._format_decimal(row[23]),  # claim_amount
                row[24] or "",  # ship_to_address
                row[25] or "",  # ship_from_address
                row[26] or "",  # notes
            ])

        cursor.close()

        return output.getvalue()


# ============================================================================
# 4️⃣ DRAFT LISTINGS LEDGER EXPORTER ⭐
# ============================================================================

class DraftListingsExporter(LedgerCSVExporter):
    """Export Draft Listings Ledger to CSV"""

    COLUMNS = [
        'DraftID',
        'MasterItemID',
        'TargetPlatforms',         # JSON array
        'PrimaryPlatform',
        'Title',
        'Description',
        'Price',
        'Quantity',
        'Condition',
        'Category',
        'Subcategory',
        'Brand',
        'Model',
        'Size',
        'Color',
        'Material',
        'Photos',                  # JSON array
        'PrimaryPhotoIndex',
        'Keywords',                # JSON array
        'SearchTerms',             # JSON array
        'ShippingPrice',
        'ShippingService',
        'ShipsFromLocation',
        'HandlingTimeDays',
        'ReturnsAccepted',
        'ReturnPeriodDays',
        'CompletenessScore',
        'Status',
        'ReadyForPlatforms',       # JSON array
        'PublishedToPlatforms',    # JSON
        'AIEnhanced',
        'AIProvider',
        'Notes',
        'CreatedAt',
        'UpdatedAt',
        'PublishedAt',
    ]

    @staticmethod
    def export_to_csv(user_id: int, filters: Optional[Dict] = None) -> str:
        """
        Export draft listings to CSV string.

        Args:
            user_id: User ID
            filters: Optional filters (status, platform, completeness)

        Returns:
            CSV string
        """
        db = get_db()
        cursor = db._get_cursor()

        query = """
            SELECT
                draft_id,
                master_item_id,
                target_platforms,
                primary_platform,
                title,
                description,
                price,
                quantity,
                condition,
                category,
                subcategory,
                brand,
                model,
                size,
                color,
                material,
                photos,
                primary_photo_index,
                keywords,
                search_terms,
                shipping_price,
                shipping_service,
                ships_from_location,
                handling_time_days,
                returns_accepted,
                return_period_days,
                completeness_score,
                status,
                ready_for_platforms,
                published_to_platforms,
                ai_enhanced,
                ai_provider,
                notes,
                created_at,
                updated_at,
                published_at
            FROM draft_listings
            WHERE user_id = %s::INTEGER
        """
        params = [user_id]

        if filters:
            if filters.get('status'):
                query += " AND status = %s"
                params.append(filters['status'])
            if filters.get('primary_platform'):
                query += " AND primary_platform = %s"
                params.append(filters['primary_platform'])
            if filters.get('min_completeness'):
                query += " AND completeness_score >= %s"
                params.append(filters['min_completeness'])

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(DraftListingsExporter.COLUMNS)

        for row in rows:
            writer.writerow([
                row[0],  # draft_id
                row[1] or "",  # master_item_id
                row[2] or "",  # target_platforms
                row[3] or "",  # primary_platform
                row[4],  # title
                row[5] or "",  # description
                DraftListingsExporter._format_decimal(row[6]),  # price
                row[7],  # quantity
                row[8] or "",  # condition
                row[9] or "",  # category
                row[10] or "",  # subcategory
                row[11] or "",  # brand
                row[12] or "",  # model
                row[13] or "",  # size
                row[14] or "",  # color
                row[15] or "",  # material
                row[16] or "",  # photos
                row[17] or 0,  # primary_photo_index
                row[18] or "",  # keywords
                row[19] or "",  # search_terms
                DraftListingsExporter._format_decimal(row[20]),  # shipping_price
                row[21] or "",  # shipping_service
                row[22] or "",  # ships_from_location
                row[23] or "",  # handling_time_days
                "TRUE" if row[24] else "FALSE",  # returns_accepted
                row[25] or 30,  # return_period_days
                row[26] or 0,  # completeness_score
                row[27] or "draft",  # status
                row[28] or "",  # ready_for_platforms
                row[29] or "",  # published_to_platforms
                "TRUE" if row[30] else "FALSE",  # ai_enhanced
                row[31] or "",  # ai_provider
                row[32] or "",  # notes
                DraftListingsExporter._format_datetime(row[33]),  # created_at
                DraftListingsExporter._format_datetime(row[34]),  # updated_at
                DraftListingsExporter._format_datetime(row[35]),  # published_at
            ])

        cursor.close()

        return output.getvalue()


# ============================================================================
# 5️⃣ INVOICES LEDGER EXPORTER
# ============================================================================

class InvoicesExporter(LedgerCSVExporter):
    """Export Invoices Ledger to CSV"""

    COLUMNS = [
        'InvoiceID',
        'InvoiceNumber',
        'MasterItemID',
        'InvoiceDate',
        'DueDate',
        'BuyerName',
        'BuyerEmail',
        'BuyerPhone',
        'BuyerAddress',
        'Items',  # JSON
        'Subtotal',
        'TaxRate',
        'TaxAmount',
        'ShippingAmount',
        'DiscountAmount',
        'TotalAmount',
        'PaymentMethod',
        'PaymentStatus',
        'PaidAmount',
        'PaidDate',
        'PDFUrl',
        'PDFGenerated',
        'SentVia',
        'SentAt',
        'Status',
        'InventoryMarkedSold',
        'Notes',
        'Terms',
        'CreatedAt',
        'UpdatedAt',
    ]

    @staticmethod
    def export_to_csv(user_id: int, filters: Optional[Dict] = None) -> str:
        """
        Export invoices ledger to CSV string.

        Args:
            user_id: User ID
            filters: Optional filters (status, payment_status, etc.)

        Returns:
            CSV string
        """
        db = get_db()
        cursor = db._get_cursor()

        # Build query with filters
        query = """
            SELECT
                invoice_id,
                invoice_number,
                master_item_id,
                invoice_date,
                due_date,
                buyer_name,
                buyer_email,
                buyer_phone,
                buyer_address,
                items,
                subtotal,
                tax_rate,
                tax_amount,
                shipping_amount,
                discount_amount,
                total_amount,
                payment_method,
                payment_status,
                paid_amount,
                paid_date,
                pdf_url,
                pdf_generated,
                sent_via,
                sent_at,
                status,
                inventory_marked_sold,
                notes,
                terms,
                created_at,
                updated_at
            FROM invoices
            WHERE user_id = %s::INTEGER
        """

        params = [user_id]
        conditions = []

        if filters:
            if 'status' in filters:
                conditions.append("status = %s")
                params.append(filters['status'])
            if 'payment_status' in filters:
                conditions.append("payment_status = %s")
                params.append(filters['payment_status'])
            if 'payment_method' in filters:
                conditions.append("payment_method = %s")
                params.append(filters['payment_method'])
            if 'start_date' in filters:
                conditions.append("invoice_date >= %s")
                params.append(filters['start_date'])
            if 'end_date' in filters:
                conditions.append("invoice_date <= %s")
                params.append(filters['end_date'])

        if conditions:
            query += " AND " + " AND ".join(conditions)

        query += " ORDER BY invoice_date DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Write CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(InvoicesExporter.COLUMNS)

        for row in rows:
            writer.writerow([
                row[0] or "",  # invoice_id
                row[1] or "",  # invoice_number
                row[2] or "",  # master_item_id
                InvoicesExporter._format_date(row[3]),  # invoice_date
                InvoicesExporter._format_date(row[4]),  # due_date
                row[5] or "",  # buyer_name
                row[6] or "",  # buyer_email
                row[7] or "",  # buyer_phone
                row[8] or "",  # buyer_address
                row[9] or "",  # items (JSON)
                InvoicesExporter._format_decimal(row[10]),  # subtotal
                float(row[11]) if row[11] else "",  # tax_rate
                InvoicesExporter._format_decimal(row[12]),  # tax_amount
                InvoicesExporter._format_decimal(row[13]),  # shipping_amount
                InvoicesExporter._format_decimal(row[14]),  # discount_amount
                InvoicesExporter._format_decimal(row[15]),  # total_amount
                row[16] or "",  # payment_method
                row[17] or "",  # payment_status
                InvoicesExporter._format_decimal(row[18]),  # paid_amount
                InvoicesExporter._format_date(row[19]),  # paid_date
                row[20] or "",  # pdf_url
                "TRUE" if row[21] else "FALSE",  # pdf_generated
                row[22] or "",  # sent_via
                InvoicesExporter._format_datetime(row[23]),  # sent_at
                row[24] or "",  # status
                "TRUE" if row[25] else "FALSE",  # inventory_marked_sold
                row[26] or "",  # notes
                row[27] or "",  # terms
                InvoicesExporter._format_datetime(row[28]),  # created_at
                InvoicesExporter._format_datetime(row[29]),  # updated_at
            ])

        cursor.close()

        return output.getvalue()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def export_ledger(ledger_type: str, user_id: int, filters: Optional[Dict] = None) -> str:
    """
    Export any ledger type to CSV.

    Args:
        ledger_type: 'inventory', 'sales', 'shipping', 'drafts', or 'invoices'
        user_id: User ID
        filters: Optional filters

    Returns:
        CSV string

    Raises:
        ValueError: If ledger_type is invalid
    """
    exporters = {
        'inventory': InventoryMasterExporter,
        'sales': SalesLedgerExporter,
        'shipping': ShippingLedgerExporter,
        'drafts': DraftListingsExporter,
        'invoices': InvoicesExporter,
    }

    exporter_class = exporters.get(ledger_type.lower())
    if not exporter_class:
        raise ValueError(f"Invalid ledger type: {ledger_type}. Must be one of: {list(exporters.keys())}")

    return exporter_class.export_to_csv(user_id, filters)


def export_ledger_for_platform(ledger_type: str, user_id: int, platform: str, filters: Optional[Dict] = None) -> str:
    """
    Export ledger data formatted for a specific platform's CSV schema.

    Args:
        ledger_type: 'inventory', 'sales', 'shipping', 'drafts', or 'invoices'
        user_id: User ID
        platform: Platform key (e.g., 'ebay', 'poshmark', 'discogs')
        filters: Optional filters

    Returns:
        CSV string in platform-specific format

    Raises:
        ValueError: If ledger_type or platform is invalid
    """
    from ..csv_exporters import get_exporter

    # Get the platform exporter
    try:
        exporter = get_exporter(platform)
    except ValueError as e:
        raise ValueError(f"Invalid platform: {platform}. {str(e)}")

    # Get ledger data in raw format
    db = get_db()
    cursor = db._get_cursor()

    # Build query based on ledger type
    # Cast user_id to INTEGER to handle potential type mismatches
    if ledger_type == 'inventory':
        query = """
            SELECT
                id,
                master_item_id as listing_uuid,
                sku,
                title,
                description,
                price,
                cost_basis as cost,
                category,
                subcategory,
                brand,
                model,
                color,
                size,
                condition,
                measurements,
                quantity,
                storage_location,
                status,
                photos,
                notes,
                created_at,
                updated_at
            FROM inventory_master
            WHERE user_id = %s::INTEGER
        """
    elif ledger_type == 'drafts':
        query = """
            SELECT
                id,
                draft_id as listing_uuid,
                COALESCE(master_item_id, draft_id) as sku,
                title,
                description,
                price,
                0 as cost,
                category,
                subcategory,
                brand,
                model,
                color,
                size,
                condition,
                '{}' as measurements,
                quantity,
                ships_from_location as storage_location,
                status,
                photos,
                notes,
                created_at,
                updated_at
            FROM draft_listings
            WHERE user_id = %s::INTEGER
        """
    else:
        # For other ledger types, fall back to internal format
        # since they don't map well to product listings
        return export_ledger(ledger_type, user_id, filters)

    params = [user_id]

    # Apply filters
    if filters:
        if filters.get('status'):
            query += " AND status = %s"
            params.append(filters['status'])
        if filters.get('category'):
            query += " AND category = %s"
            params.append(filters['category'])

    query += " ORDER BY created_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()

    if not rows:
        # Return empty CSV with just headers
        return exporter.export_to_csv([])

    # Convert rows to list of dicts for the platform exporter
    columns = [desc[0] for desc in cursor.description] if hasattr(cursor, 'description') else []

    # Build column list manually based on query
    if ledger_type == 'inventory':
        columns = ['id', 'listing_uuid', 'sku', 'title', 'description', 'price', 'cost',
                   'category', 'subcategory', 'brand', 'model', 'color', 'size', 'condition',
                   'measurements', 'quantity', 'storage_location', 'status', 'photos', 'notes',
                   'created_at', 'updated_at']
    elif ledger_type == 'drafts':
        columns = ['id', 'listing_uuid', 'sku', 'title', 'description', 'price', 'cost',
                   'category', 'subcategory', 'brand', 'model', 'color', 'size', 'condition',
                   'measurements', 'quantity', 'storage_location', 'status', 'photos', 'notes',
                   'created_at', 'updated_at']

    listings = []
    for row in rows:
        listing = {}
        for i, col in enumerate(columns):
            val = row[i]
            # Handle datetime objects
            if isinstance(val, datetime):
                val = val.isoformat()
            # Handle Decimal
            elif isinstance(val, Decimal):
                val = float(val)
            listing[col] = val
        listings.append(listing)

    # Use the platform exporter to generate CSV
    return exporter.export_to_csv(listings)
