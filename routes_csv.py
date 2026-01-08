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


# Universal CSV schema (same for drafts, vault, post_queue)
UNIVERSAL_HEADERS = [
    'title', 'description', 'price', 'cost', 'condition', 'item_type',
    'brand', 'size', 'color', 'shipping_cost', 'photos', 'created_at', 'updated_at'
]

POST_QUEUE_HEADERS = UNIVERSAL_HEADERS + ['platform']


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

