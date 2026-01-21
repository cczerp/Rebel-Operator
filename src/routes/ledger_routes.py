"""
Ledger Routes - Master Ledger System
=====================================
API routes for managing and exporting the 4 master ledgers.
"""

from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from typing import Dict, Any
import io
from datetime import datetime

from ..ledgers import (
    InventoryMasterExporter,
    SalesLedgerExporter,
    ShippingLedgerExporter,
    DraftListingsExporter,
    export_ledger,
)
from ..database.db import get_db


ledger_bp = Blueprint('ledger_bp', __name__)


# ============================================================================
# EXPORT ENDPOINTS
# ============================================================================

@ledger_bp.route("/api/ledgers/export/<ledger_type>", methods=["GET"])
@login_required
def export_ledger_api(ledger_type: str):
    """
    Export ledger to CSV file.

    Path:
        ledger_type: 'inventory', 'sales', 'shipping', or 'drafts'

    Query params:
        format: 'download' (default) or 'inline'
        Filters vary by ledger type (see docs)

    Response:
        CSV file download
    """
    try:
        # Get filters from query params
        filters = {}

        # Common filters
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')

        # Ledger-specific filters
        if ledger_type == 'inventory':
            if request.args.get('status'):
                filters['status'] = request.args.get('status')
            if request.args.get('category'):
                filters['category'] = request.args.get('category')
            if request.args.get('storage_location'):
                filters['storage_location'] = request.args.get('storage_location')

        elif ledger_type == 'sales':
            if request.args.get('platform'):
                filters['platform'] = request.args.get('platform')
            if request.args.get('payout_status'):
                filters['payout_status'] = request.args.get('payout_status')

        elif ledger_type == 'shipping':
            if request.args.get('carrier'):
                filters['carrier'] = request.args.get('carrier')
            if request.args.get('delivery_status'):
                filters['delivery_status'] = request.args.get('delivery_status')
            if request.args.get('issue_reported'):
                filters['issue_reported'] = True

        elif ledger_type == 'drafts':
            if request.args.get('status'):
                filters['status'] = request.args.get('status')
            if request.args.get('primary_platform'):
                filters['primary_platform'] = request.args.get('primary_platform')
            if request.args.get('min_completeness'):
                filters['min_completeness'] = int(request.args.get('min_completeness'))

        # Export CSV
        csv_content = export_ledger(ledger_type, current_user.id, filters)

        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{ledger_type}_ledger_{timestamp}.csv"

        # Return as download
        return send_file(
            io.BytesIO(csv_content.encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Export error: {e}")
        return jsonify({"error": f"Export failed: {str(e)}"}), 500


@ledger_bp.route("/api/ledgers/export/all", methods=["GET"])
@login_required
def export_all_ledgers():
    """
    Export all 4 ledgers as separate CSV files in a ZIP.

    Query params:
        Same filters as individual exports

    Response:
        ZIP file containing 4 CSV files
    """
    try:
        import zipfile

        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Export each ledger
            ledgers = ['inventory', 'sales', 'shipping', 'drafts']
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            for ledger_type in ledgers:
                try:
                    csv_content = export_ledger(ledger_type, current_user.id)
                    filename = f"{ledger_type}_ledger_{timestamp}.csv"
                    zip_file.writestr(filename, csv_content)
                except Exception as e:
                    current_app.logger.error(f"Failed to export {ledger_type}: {e}")

        zip_buffer.seek(0)

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"all_ledgers_{timestamp}.zip"
        )

    except Exception as e:
        current_app.logger.error(f"Export all error: {e}")
        return jsonify({"error": f"Export failed: {str(e)}"}), 500


# ============================================================================
# STATS & SUMMARY ENDPOINTS
# ============================================================================

@ledger_bp.route("/api/ledgers/stats", methods=["GET"])
@login_required
def get_ledger_stats():
    """
    Get summary statistics for all ledgers.

    Response:
        {
            "inventory": {
                "total_items": 150,
                "available": 45,
                "listed": 80,
                "sold": 25,
                "total_value": 4500.00
            },
            "sales": {
                "total_sales": 250,
                "total_revenue": 12500.00,
                "total_profit": 5600.00,
                "avg_profit_per_sale": 22.40
            },
            "shipping": {
                "total_shipments": 240,
                "in_transit": 5,
                "delivered": 230,
                "issues": 5
            },
            "drafts": {
                "total_drafts": 60,
                "ready_to_publish": 30,
                "avg_completeness": 75.5
            }
        }
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        stats = {}

        # Inventory stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_items,
                COUNT(*) FILTER (WHERE status = 'available') as available,
                COUNT(*) FILTER (WHERE status = 'listed') as listed,
                COUNT(*) FILTER (WHERE status = 'sold') as sold,
                SUM(cost_basis * quantity) as total_value
            FROM inventory_master
            WHERE user_id = %s
        """, (current_user.id,))
        inv_row = cursor.fetchone()
        stats['inventory'] = {
            "total_items": inv_row[0],
            "available": inv_row[1],
            "listed": inv_row[2],
            "sold": inv_row[3],
            "total_value": float(inv_row[4]) if inv_row[4] else 0.0
        }

        # Sales stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_sales,
                SUM(gross_sale_amount) as total_revenue,
                SUM(profit) as total_profit,
                AVG(profit) as avg_profit_per_sale
            FROM sales_ledger
            WHERE user_id = %s
        """, (current_user.id,))
        sales_row = cursor.fetchone()
        stats['sales'] = {
            "total_sales": sales_row[0],
            "total_revenue": float(sales_row[1]) if sales_row[1] else 0.0,
            "total_profit": float(sales_row[2]) if sales_row[2] else 0.0,
            "avg_profit_per_sale": float(sales_row[3]) if sales_row[3] else 0.0
        }

        # Shipping stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_shipments,
                COUNT(*) FILTER (WHERE delivery_status = 'in_transit') as in_transit,
                COUNT(*) FILTER (WHERE delivery_status = 'delivered') as delivered,
                COUNT(*) FILTER (WHERE issue_reported = TRUE) as issues
            FROM shipping_ledger
            WHERE user_id = %s
        """, (current_user.id,))
        ship_row = cursor.fetchone()
        stats['shipping'] = {
            "total_shipments": ship_row[0],
            "in_transit": ship_row[1],
            "delivered": ship_row[2],
            "issues": ship_row[3]
        }

        # Draft stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_drafts,
                COUNT(*) FILTER (WHERE completeness_score >= 90) as ready_to_publish,
                AVG(completeness_score) as avg_completeness
            FROM draft_listings
            WHERE user_id = %s
        """, (current_user.id,))
        draft_row = cursor.fetchone()
        stats['drafts'] = {
            "total_drafts": draft_row[0],
            "ready_to_publish": draft_row[1],
            "avg_completeness": float(draft_row[2]) if draft_row[2] else 0.0
        }

        cursor.close()
        conn.close()

        return jsonify(stats)

    except Exception as e:
        current_app.logger.error(f"Stats error: {e}")
        return jsonify({"error": str(e)}), 500


@ledger_bp.route("/api/ledgers/<ledger_type>/count", methods=["GET"])
@login_required
def get_ledger_count(ledger_type: str):
    """
    Get count of records in a ledger.

    Path:
        ledger_type: 'inventory', 'sales', 'shipping', or 'drafts'

    Response:
        {"count": 150}
    """
    try:
        table_map = {
            'inventory': 'inventory_master',
            'sales': 'sales_ledger',
            'shipping': 'shipping_ledger',
            'drafts': 'draft_listings'
        }

        table = table_map.get(ledger_type.lower())
        if not table:
            return jsonify({"error": "Invalid ledger type"}), 400

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE user_id = %s", (current_user.id,))
        count = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return jsonify({"count": count})

    except Exception as e:
        current_app.logger.error(f"Count error: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# ID GENERATION ENDPOINTS
# ============================================================================

@ledger_bp.route("/api/ledgers/generate-id/<id_type>", methods=["GET"])
@login_required
def generate_ledger_id(id_type: str):
    """
    Generate next sequential ID for a ledger.

    Path:
        id_type: 'master_item', 'transaction', 'shipment', or 'draft'

    Response:
        {"id": "INV-2024-0001"}
    """
    try:
        function_map = {
            'master_item': 'generate_master_item_id',
            'transaction': 'generate_transaction_id',
            'shipment': 'generate_shipment_id',
            'draft': 'generate_draft_id'
        }

        func_name = function_map.get(id_type.lower())
        if not func_name:
            return jsonify({"error": "Invalid ID type"}), 400

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(f"SELECT {func_name}(%s)", (current_user.id,))
        generated_id = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return jsonify({"id": generated_id})

    except Exception as e:
        current_app.logger.error(f"ID generation error: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# PROFIT ANALYSIS ENDPOINTS
# ============================================================================

@ledger_bp.route("/api/ledgers/sales/profit-by-platform", methods=["GET"])
@login_required
def get_profit_by_platform():
    """
    Get profit breakdown by platform.

    Query params:
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)

    Response:
        {
            "ebay": {
                "revenue": 5000.00,
                "profit": 2000.00,
                "num_sales": 50
            },
            "poshmark": {...}
        }
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        query = """
            SELECT
                platform,
                SUM(gross_sale_amount) as revenue,
                SUM(profit) as profit,
                COUNT(*) as num_sales
            FROM sales_ledger
            WHERE user_id = %s
        """
        params = [current_user.id]

        if request.args.get('start_date'):
            query += " AND sale_date >= %s"
            params.append(request.args.get('start_date'))

        if request.args.get('end_date'):
            query += " AND sale_date <= %s"
            params.append(request.args.get('end_date'))

        query += " GROUP BY platform ORDER BY profit DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        result = {}
        for row in rows:
            result[row[0]] = {
                "revenue": float(row[1]) if row[1] else 0.0,
                "profit": float(row[2]) if row[2] else 0.0,
                "num_sales": row[3]
            }

        cursor.close()
        conn.close()

        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"Profit analysis error: {e}")
        return jsonify({"error": str(e)}), 500


@ledger_bp.route("/api/ledgers/sales/monthly-profit", methods=["GET"])
@login_required
def get_monthly_profit():
    """
    Get monthly profit over time.

    Query params:
        months: Number of months to look back (default: 12)

    Response:
        [
            {"month": "2024-01", "revenue": 5000.00, "profit": 2000.00},
            {"month": "2024-02", "revenue": 6000.00, "profit": 2500.00},
            ...
        ]
    """
    try:
        months = int(request.args.get('months', 12))

        conn = get_db()
        cursor = conn.cursor()

        query = """
            SELECT
                TO_CHAR(sale_date, 'YYYY-MM') as month,
                SUM(gross_sale_amount) as revenue,
                SUM(profit) as profit,
                COUNT(*) as num_sales
            FROM sales_ledger
            WHERE user_id = %s
              AND sale_date >= CURRENT_DATE - INTERVAL '%s months'
            GROUP BY TO_CHAR(sale_date, 'YYYY-MM')
            ORDER BY month DESC
        """

        cursor.execute(query, (current_user.id, months))
        rows = cursor.fetchall()

        result = [
            {
                "month": row[0],
                "revenue": float(row[1]) if row[1] else 0.0,
                "profit": float(row[2]) if row[2] else 0.0,
                "num_sales": row[3]
            }
            for row in rows
        ]

        cursor.close()
        conn.close()

        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"Monthly profit error: {e}")
        return jsonify({"error": str(e)}), 500
