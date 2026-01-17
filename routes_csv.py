"""
routes_csv.py
CSV-based endpoints for draft, vault, and post queue management
Scaffold implementation - minimal wiring
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required
from datetime import datetime
import csv
import os
import json

# Create blueprint
csv_bp = Blueprint("csv", __name__)

# Base directory for CSV files
CSV_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# Ensure data directory exists
os.makedirs(CSV_DIR, exist_ok=True)

# CSV file paths
DRAFTS_CSV = os.path.join(CSV_DIR, "drafts.csv")
VAULT_CSV = os.path.join(CSV_DIR, "vault.csv")
POST_QUEUE_CSV = os.path.join(CSV_DIR, "post_queue.csv")
INVENTORY_CSV = os.path.join(CSV_DIR, "inventory.csv")


def ensure_csv_headers(filepath, headers):
    """Ensure CSV file exists with headers"""
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()


def append_to_csv(filepath, headers, data):
    """Append a row to CSV file"""
    ensure_csv_headers(filepath, headers)
    
    # Ensure all data keys match headers (fill missing with empty strings)
    row_data = {header: data.get(header, '') for header in headers}
    
    with open(filepath, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writerow(row_data)


def read_csv(filepath, headers):
    """Read all rows from CSV file"""
    ensure_csv_headers(filepath, headers)
    rows = []
    if os.path.exists(filepath):
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                # Add row index as id for reference
                row['_id'] = idx
                rows.append(row)
    return rows


def update_csv_row(filepath, headers, row_id, updates):
    """Update a specific row in CSV file by row index"""
    ensure_csv_headers(filepath, headers)
    
    rows = []
    if os.path.exists(filepath):
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    
    # Update the row
    if 0 <= row_id < len(rows):
        rows[row_id].update(updates)
        rows[row_id]['updated_at'] = datetime.now().isoformat()
        
        # Write back to file
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
        return True
    return False


def delete_csv_rows(filepath, headers, row_ids):
    """Delete rows from CSV file by row indices (sorted descending to avoid index shifting)"""
    ensure_csv_headers(filepath, headers)
    
    rows = []
    if os.path.exists(filepath):
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    
    # Sort row_ids in descending order to delete from end first
    sorted_ids = sorted([int(id) for id in row_ids], reverse=True)
    deleted_count = 0
    
    for row_id in sorted_ids:
        if 0 <= row_id < len(rows):
            rows.pop(row_id)
            deleted_count += 1
    
    # Write back to file
    if deleted_count > 0:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            if rows:  # Only write if there are rows left
                writer.writerows(rows)
    
    return deleted_count


# Universal CSV schema (same for drafts, vault, post_queue)
UNIVERSAL_HEADERS = [
    'title', 'description', 'price', 'cost', 'condition', 'item_type',
    'brand', 'size', 'color', 'shipping_cost', 'photos', 'created_at', 'updated_at'
]

POST_QUEUE_HEADERS = UNIVERSAL_HEADERS + ['platform']
INVENTORY_HEADERS = UNIVERSAL_HEADERS  # Same as universal headers


@csv_bp.route('/api/save-draft-csv', methods=['POST'])
@login_required
def save_draft_csv():
    """Save listing form data to drafts.csv"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Convert photos array to comma-separated string
        photos = data.get('photos', [])
        photos_str = ','.join(photos) if isinstance(photos, list) else str(photos) if photos else ''
        
        # Prepare CSV row with all required fields
        csv_row = {
            'title': str(data.get('title', '')),
            'description': str(data.get('description', '')),
            'price': str(data.get('price', '')),
            'cost': str(data.get('cost', '')),
            'condition': str(data.get('condition', '')),
            'item_type': str(data.get('item_type', '')),
            'brand': str(data.get('brand', '')),
            'size': str(data.get('size', '')),
            'color': str(data.get('color', '')),
            'shipping_cost': str(data.get('shipping_cost', '0')),
            'photos': photos_str,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Append to CSV
        append_to_csv(DRAFTS_CSV, UNIVERSAL_HEADERS, csv_row)
        
        return jsonify({
            'success': True,
            'message': 'Draft saved to CSV successfully'
        })
        
    except Exception as e:
        import logging
        import traceback
        logging.error(f"Save draft CSV error: {e}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@csv_bp.route('/api/save-vault-csv', methods=['POST'])
@login_required
def save_vault_csv():
    """Save listing form data to vault.csv"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Convert photos array to comma-separated string
        photos = data.get('photos', [])
        photos_str = ','.join(photos) if isinstance(photos, list) else str(photos) if photos else ''
        
        # Prepare CSV row with all required fields
        csv_row = {
            'title': str(data.get('title', '')),
            'description': str(data.get('description', '')),
            'price': str(data.get('price', '')),
            'cost': str(data.get('cost', '')),
            'condition': str(data.get('condition', '')),
            'item_type': str(data.get('item_type', '')),
            'brand': str(data.get('brand', '')),
            'size': str(data.get('size', '')),
            'color': str(data.get('color', '')),
            'shipping_cost': str(data.get('shipping_cost', '0')),
            'photos': photos_str,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Append to CSV
        append_to_csv(VAULT_CSV, UNIVERSAL_HEADERS, csv_row)
        
        return jsonify({
            'success': True,
            'message': 'Item saved to Collection Vault successfully'
        })
        
    except Exception as e:
        import logging
        import traceback
        logging.error(f"Save vault CSV error: {e}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@csv_bp.route('/api/post-listing', methods=['POST'])
@login_required
def post_listing():
    """Save listing to post_queue.csv with selected platform"""
    try:
        data = request.get_json()
        platform = data.get('platform', 'other')
        
        # Convert photos array to comma-separated string
        photos_str = ','.join(data.get('photos', [])) if isinstance(data.get('photos'), list) else data.get('photos', '')
        
        # Prepare CSV row
        csv_row = {
            'title': data.get('title', ''),
            'description': data.get('description', ''),
            'price': data.get('price', ''),
            'cost': data.get('cost', ''),
            'condition': data.get('condition', ''),
            'item_type': data.get('item_type', ''),
            'brand': data.get('brand', ''),
            'size': data.get('size', ''),
            'color': data.get('color', ''),
            'shipping_cost': data.get('shipping_cost', '0'),
            'photos': photos_str,
            'platform': platform,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Append to CSV
        append_to_csv(POST_QUEUE_CSV, POST_QUEUE_HEADERS, csv_row)
        
        return jsonify({
            'success': True,
            'message': f'Listing queued for {platform}',
            'platform': platform
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# INVENTORY CSV ENDPOINTS
# ============================================================================

@csv_bp.route('/api/inventory-csv', methods=['GET'])
@login_required
def get_inventory_csv():
    """Get all inventory items from CSV"""
    try:
        inventory_items = read_csv(INVENTORY_CSV, INVENTORY_HEADERS)
        return jsonify({
            'success': True,
            'items': inventory_items
        })
    except Exception as e:
        import logging
        import traceback
        logging.error(f"Get inventory CSV error: {e}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@csv_bp.route('/api/inventory-csv/update', methods=['PATCH'])
@login_required
def update_inventory_csv():
    """Update inventory items in CSV (bulk update)"""
    try:
        data = request.get_json()
        changes = data.get('changes', {})
        
        if not changes:
            return jsonify({'error': 'No changes provided'}), 400
        
        updated_count = 0
        for row_id_str, fields in changes.items():
            row_id = int(row_id_str)
            if update_csv_row(INVENTORY_CSV, INVENTORY_HEADERS, row_id, fields):
                updated_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Updated {updated_count} item(s)',
            'updated_count': updated_count
        })
    except Exception as e:
        import logging
        import traceback
        logging.error(f"Update inventory CSV error: {e}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@csv_bp.route('/api/inventory-csv/delete', methods=['DELETE'])
@login_required
def delete_inventory_csv():
    """Delete inventory items from CSV"""
    try:
        data = request.get_json()
        row_ids = data.get('row_ids', [])
        
        if not row_ids:
            return jsonify({'error': 'No row IDs provided'}), 400
        
        deleted_count = delete_csv_rows(INVENTORY_CSV, INVENTORY_HEADERS, row_ids)
        
        return jsonify({
            'success': True,
            'message': f'Deleted {deleted_count} item(s)',
            'deleted_count': deleted_count
        })
    except Exception as e:
        import logging
        import traceback
        logging.error(f"Delete inventory CSV error: {e}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@csv_bp.route('/api/inventory-csv/add', methods=['POST'])
@login_required
def add_inventory_csv():
    """Add new item to inventory CSV"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Convert photos array to comma-separated string
        photos = data.get('photos', [])
        photos_str = ','.join(photos) if isinstance(photos, list) else str(photos) if photos else ''
        
        # Prepare CSV row
        csv_row = {
            'title': str(data.get('title', '')),
            'description': str(data.get('description', '')),
            'price': str(data.get('price', '')),
            'cost': str(data.get('cost', '')),
            'condition': str(data.get('condition', '')),
            'item_type': str(data.get('item_type', '')),
            'brand': str(data.get('brand', '')),
            'size': str(data.get('size', '')),
            'color': str(data.get('color', '')),
            'shipping_cost': str(data.get('shipping_cost', '0')),
            'photos': photos_str,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Append to CSV
        append_to_csv(INVENTORY_CSV, INVENTORY_HEADERS, csv_row)
        
        return jsonify({
            'success': True,
            'message': 'Item added to inventory successfully'
        })
    except Exception as e:
        import logging
        import traceback
        logging.error(f"Add inventory CSV error: {e}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

