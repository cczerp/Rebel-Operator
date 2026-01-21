"""
Import Routes - Reverse Sync
=============================
API routes for importing listings FROM platforms INTO Rebel Operator.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from typing import Dict, Any
import json

from ..importers import (
    import_listings_from_platform,
    import_listings_from_csv,
    ImportService,
    get_supported_platforms,
    validate_csv_format,
)
from ..database.db import get_connection


import_bp = Blueprint('import_bp', __name__)


@import_bp.route("/api/import/csv", methods=["POST"])
@login_required
def import_csv_route():
    """
    Import listings from CSV file.

    Request:
        - file: CSV file (multipart/form-data)
        - platform: Platform name (poshmark, mercari, grailed, etc.)

    Response:
        {
            "success": true,
            "imported": 15,
            "errors": ["Row 10: Invalid price", ...]
        }
    """
    try:
        # Check file uploaded
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        if not file or not file.filename:
            return jsonify({"error": "No file selected"}), 400

        if not file.filename.endswith('.csv'):
            return jsonify({"error": "File must be a CSV"}), 400

        # Get platform
        platform = request.form.get('platform', '').lower()
        if not platform:
            return jsonify({"error": "Platform parameter required"}), 400

        # Validate platform is supported
        supported = get_supported_platforms()
        if platform not in supported:
            return jsonify({
                "error": f"Platform '{platform}' not supported for CSV import",
                "supported_platforms": supported
            }), 400

        # Import listings
        imported_count, errors = import_listings_from_csv(
            user_id=current_user.id,
            platform=platform,
            csv_file=file
        )

        return jsonify({
            "success": True,
            "imported": imported_count,
            "errors": errors
        })

    except Exception as e:
        current_app.logger.error(f"CSV import error: {e}")
        return jsonify({"error": f"Import failed: {str(e)}"}), 500


@import_bp.route("/api/import/platform", methods=["POST"])
@login_required
def import_from_platform():
    """
    Import listings from platform via API.

    Request:
        {
            "platform": "ebay",
            "limit": 50  // optional, max listings to import
        }

    Response:
        {
            "success": true,
            "imported": 25,
            "errors": ["Failed to fetch listing 123", ...]
        }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Request body required"}), 400

        platform = data.get('platform', '').lower()
        if not platform:
            return jsonify({"error": "Platform parameter required"}), 400

        limit = data.get('limit')
        if limit is not None:
            try:
                limit = int(limit)
                if limit < 1 or limit > 500:
                    return jsonify({"error": "Limit must be between 1 and 500"}), 400
            except (ValueError, TypeError):
                return jsonify({"error": "Limit must be a number"}), 400

        # Get platform credentials from database
        credentials = _get_platform_credentials(current_user.id, platform)
        if not credentials:
            return jsonify({
                "error": f"No credentials found for platform '{platform}'",
                "help": "Please configure platform credentials in Settings → Platform Integrations"
            }), 400

        # Import listings
        imported_count, errors = import_listings_from_platform(
            user_id=current_user.id,
            platform=platform,
            credentials=credentials,
            limit=limit
        )

        return jsonify({
            "success": True,
            "imported": imported_count,
            "errors": errors
        })

    except Exception as e:
        current_app.logger.error(f"Platform import error: {e}")
        return jsonify({"error": f"Import failed: {str(e)}"}), 500


@import_bp.route("/api/import/supported-platforms", methods=["GET"])
@login_required
def get_supported_import_platforms():
    """
    Get list of platforms that support import.

    Response:
        {
            "api_platforms": ["ebay", "etsy", "shopify"],
            "csv_platforms": ["poshmark", "mercari", "grailed", "bonanza"]
        }
    """
    try:
        service = ImportService(current_user.id)

        return jsonify({
            "api_platforms": service.get_supported_api_platforms(),
            "csv_platforms": service.get_supported_csv_platforms()
        })

    except Exception as e:
        current_app.logger.error(f"Error getting supported platforms: {e}")
        return jsonify({"error": str(e)}), 500


@import_bp.route("/api/import/history", methods=["GET"])
@login_required
def get_import_history():
    """
    Get import history for current user.

    Query params:
        - platform: Filter by platform (optional)
        - limit: Max results (default: 50)

    Response:
        {
            "imports": [
                {
                    "id": 123,
                    "title": "Vintage Nike Hoodie",
                    "platform_source": "ebay",
                    "imported_at": "2026-01-21T10:30:00Z"
                },
                ...
            ]
        }
    """
    try:
        platform = request.args.get('platform')
        limit = int(request.args.get('limit', 50))

        conn = get_connection()
        cursor = conn.cursor()

        if platform:
            query = """
                SELECT id, title, platform_source, imported_at, price
                FROM listings
                WHERE user_id = %s AND platform_source = %s
                ORDER BY imported_at DESC
                LIMIT %s
            """
            cursor.execute(query, (current_user.id, platform, limit))
        else:
            query = """
                SELECT id, title, platform_source, imported_at, price
                FROM listings
                WHERE user_id = %s AND platform_source IS NOT NULL
                ORDER BY imported_at DESC
                LIMIT %s
            """
            cursor.execute(query, (current_user.id, limit))

        imports = []
        for row in cursor.fetchall():
            imports.append({
                "id": row[0],
                "title": row[1],
                "platform_source": row[2],
                "imported_at": row[3].isoformat() if row[3] else None,
                "price": row[4]
            })

        cursor.close()
        conn.close()

        return jsonify({"imports": imports})

    except Exception as e:
        current_app.logger.error(f"Error fetching import history: {e}")
        return jsonify({"error": str(e)}), 500


@import_bp.route("/api/import/validate-csv", methods=["POST"])
@login_required
def validate_csv_route():
    """
    Validate CSV format without importing.

    Request:
        - file: CSV file
        - platform: Platform name

    Response:
        {
            "valid": true,
            "message": "CSV format is valid",
            "preview": ["row1", "row2", "row3"]
        }
    """
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        platform = request.form.get('platform', '').lower()

        if not platform:
            return jsonify({"error": "Platform parameter required"}), 400

        # Read CSV content
        csv_content = file.read().decode('utf-8')
        file.seek(0)  # Reset for preview

        # Validate format
        is_valid, message = validate_csv_format(csv_content, platform)

        # Get preview (first 3 rows)
        preview = []
        for i, line in enumerate(csv_content.split('\n')[:4]):
            if line.strip():
                preview.append(line)

        return jsonify({
            "valid": is_valid,
            "message": message,
            "preview": preview
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Helper Functions
# ============================================================================

def _get_platform_credentials(user_id: int, platform: str) -> Dict[str, Any]:
    """
    Get platform credentials from database.

    Args:
        user_id: User ID
        platform: Platform name

    Returns:
        Dictionary of credentials or empty dict if not found
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT username, password, credentials_json
            FROM marketplace_credentials
            WHERE user_id = %s AND platform = %s
        """, (user_id, platform))

        row = cursor.fetchone()
        if not row:
            return {}

        credentials = {
            'username': row[0],
            'password': row[1],
        }

        # Parse JSON credentials if present
        if row[2]:
            try:
                json_creds = json.loads(row[2])
                credentials.update(json_creds)
            except json.JSONDecodeError:
                pass

        return credentials

    finally:
        cursor.close()
        conn.close()
