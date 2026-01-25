"""
search_routes.py
================
Multi-platform search aggregation endpoints.

Provides:
- /search - Search results page
- /api/search/multi-platform - Execute aggregated search
- /api/search/platforms - Get available platforms for user
"""

from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from typing import Dict, List, Optional
import json
import os
import requests

from ..search import (
    SearchAggregator,
    SearchQuery,
    SearchResult,
    get_searcher,
    SEARCHER_REGISTRY
)

# Create blueprint
search_bp = Blueprint('search', __name__)

# db will be set by init_routes() in web_app.py
db = None


def init_routes(database):
    """Initialize routes with database"""
    global db
    db = database


# =============================================================================
# SEARCH PAGE
# =============================================================================

@search_bp.route('/search')
@login_required
def search_page():
    """Render multi-platform search page."""
    return render_template('search.html')


# =============================================================================
# MULTI-PLATFORM SEARCH API
# =============================================================================

@search_bp.route('/api/search/multi-platform', methods=['POST'])
@login_required
def api_search_multi_platform():
    """
    Execute aggregated search across multiple platforms.

    Request body:
    {
        "keywords": "Pokemon Charizard",
        "item_type": "Card",
        "condition": ["NM", "LP"],
        "min_price": 10,
        "max_price": 500,
        "sort_by": "lowest_price",
        "platforms": ["ebay", "tcgplayer", "etsy"],
        "limit": 50
    }

    Response:
    {
        "success": true,
        "results": [...],
        "normalized_results": [...],
        "market_intelligence": {...}
    }
    """
    try:
        data = request.get_json()

        # Build search query
        query = SearchQuery(
            keywords=data.get('keywords', ''),
            item_type=data.get('item_type'),
            condition=data.get('condition'),
            min_price=data.get('min_price'),
            max_price=data.get('max_price'),
            sort_by=data.get('sort_by', 'newest'),
            limit=data.get('limit', 50),
        )

        if not query.keywords:
            return jsonify({'error': 'Keywords required'}), 400

        # Get user's platform credentials
        credentials_store = _get_user_credentials(current_user.id)

        # Initialize aggregator
        aggregator = SearchAggregator(credentials_store=credentials_store)

        # Get enabled platforms
        enabled_platforms = data.get('platforms')
        if enabled_platforms:
            enabled_platforms = [p.lower() for p in enabled_platforms]

        # Execute search
        results, market_intel = aggregator.search_all_platforms(
            query=query,
            enabled_platforms=enabled_platforms
        )

        # Normalize results for comparison
        normalized_results = aggregator.normalize_results(results)

        # Save to search history (optional)
        _save_search_history(current_user.id, query, len(results))

        return jsonify({
            'success': True,
            'query': query.keywords,
            'total_results': len(results),
            'results': [_serialize_result(r) for r in results],
            'normalized_results': [_serialize_normalized(n) for n in normalized_results],
            'market_intelligence': _serialize_market_intel(market_intel),
        })

    except Exception as e:
        print(f"Search error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# =============================================================================
# AVAILABLE PLATFORMS API
# =============================================================================

def _has_app_level_credentials(platform_id: str) -> bool:
    """
    Check if app-level credentials are configured via environment variables.

    These platforms should be selected by default since they work without
    user-specific credentials.
    """
    env_checks = {
        'ebay': lambda: bool(os.environ.get('EBAY_PROD_B64') or
                            (os.environ.get('EBAY_PROD_APP_ID') and os.environ.get('EBAY_PROD_CERT_ID'))),
        'etsy': lambda: bool(os.environ.get('ETSY_API_KEY')),
        'discogs': lambda: bool(os.environ.get('DISCOGS_CONSUMER_KEY') and os.environ.get('DISCOGS_CONSUMER_SECRET')),
        'reverb': lambda: bool(os.environ.get('REVERB_TOKEN')),
    }

    check_fn = env_checks.get(platform_id.lower())
    return check_fn() if check_fn else False


@search_bp.route('/api/search/platforms', methods=['GET'])
@login_required
def api_get_available_platforms():
    """
    Get list of platforms available for search based on user's credentials.

    Response:
    {
        "platforms": [
            {
                "name": "eBay",
                "id": "ebay",
                "available": true,
                "requires_auth": false
            },
            ...
        ]
    }
    """
    try:
        credentials_store = _get_user_credentials(current_user.id)
        platforms = []

        for platform_id, searcher_class in SEARCHER_REGISTRY.items():
            try:
                credentials = credentials_store.get(platform_id, {})
                searcher = searcher_class(credentials)

                is_available = searcher.is_available()
                requires_auth = searcher.requires_auth()

                # If it requires auth, check if user has credentials
                has_credentials = bool(credentials) if requires_auth else True

                # Check if platform has app-level credentials (should be selected by default)
                has_app_creds = _has_app_level_credentials(platform_id)

                platforms.append({
                    'name': searcher.platform_name,
                    'id': platform_id,
                    'available': is_available and has_credentials,
                    'requires_auth': requires_auth,
                    'has_credentials': has_credentials,
                    'default_selected': has_app_creds and is_available,
                })
            except Exception as searcher_error:
                print(f"Error loading {platform_id} searcher: {searcher_error}")
                # Skip this platform but continue with others
                continue

        return jsonify({
            'success': True,
            'platforms': platforms
        })

    except Exception as e:
        print(f"Platform list error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# =============================================================================
# EBAY SEARCH API
# =============================================================================

@search_bp.route('/api/search/ebay')
@login_required
def api_search_ebay():
    """
    Search eBay using Buy Browse API with pagination and filters.

    Query parameters:
    - q: Search query (required)
    - limit: Number of results (1-200, default 10)
    - offset: Results offset (default 0)
    - min_price: Minimum price filter
    - max_price: Maximum price filter
    - condition: Condition filter ("new", "used", etc.)

    Response:
    {
        "query": "search term",
        "total": 1234,
        "limit": 10,
        "offset": 0,
        "next_offset": 10,
        "items": [
            {
                "platform": "ebay",
                "platform_item_id": "123456789",
                "title": "Item Title",
                "price": 29.99,
                "currency": "USD",
                "condition": "New",
                "image": "https://...",
                "url": "https://...",
                "seller": "sellername",
                "location": "US",
                "shipping_cost": 5.99
            }
        ]
    }
    """
    try:
        from ..ebay.ebay_search import search_ebay

        q = request.args.get("q", "").strip()
        if not q:
            return jsonify({"error": "missing query parameter 'q'"}), 400

        limit = request.args.get("limit", 10, type=int)
        offset = request.args.get("offset", 0, type=int)
        min_price = request.args.get("min_price", type=float)
        max_price = request.args.get("max_price", type=float)
        condition = request.args.get("condition", type=str)

        results = search_ebay(
            q,
            limit=limit,
            offset=offset,
            min_price=min_price,
            max_price=max_price,
            condition=condition
        )
        return jsonify(results)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except requests.RequestException as e:
        print(f"eBay API error: {e}")
        return jsonify({"error": "eBay API request failed"}), 502
    except Exception as e:
        print(f"eBay search error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500


# =============================================================================
# ETSY SEARCH API
# =============================================================================

@search_bp.route('/api/search/etsy')
@login_required
def api_search_etsy():
    """
    Search Etsy using Etsy API with pagination and filters.

    Query parameters:
    - q: Search query (required)
    - limit: Number of results (1-100, default 10)
    - offset: Results offset (default 0)
    - min_price: Minimum price filter (in dollars)
    - max_price: Maximum price filter (in dollars)

    Response:
    {
        "query": "search term",
        "total": 1234,
        "limit": 10,
        "offset": 0,
        "next_offset": 10,
        "items": [
            {
                "platform": "etsy",
                "platform_item_id": "123456789",
                "title": "Handmade Item",
                "price": 29.99,
                "currency": "USD",
                "image": "https://...",
                "url": "https://...",
                "seller": "shopname",
                "shop_name": "shopname"
            }
        ]
    }
    """
    try:
        from ..etsy.etsy_search import search_etsy

        q = request.args.get("q", "").strip()
        if not q:
            return jsonify({"error": "missing query parameter 'q'"}), 400

        limit = request.args.get("limit", 10, type=int)
        offset = request.args.get("offset", 0, type=int)
        min_price = request.args.get("min_price", type=float)
        max_price = request.args.get("max_price", type=float)

        results = search_etsy(
            q,
            limit=limit,
            offset=offset,
            min_price=min_price,
            max_price=max_price
        )
        return jsonify(results)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except requests.RequestException as e:
        print(f"Etsy API error: {e}")
        return jsonify({"error": "Etsy API request failed"}), 502
    except Exception as e:
        print(f"Etsy search error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_user_credentials(user_id) -> Dict[str, Dict]:
    """
    Fetch user's platform credentials from database.

    Returns:
        Dict of platform credentials: {'ebay': {...}, 'etsy': {...}}
    """
    if not db:
        return {}

    cursor = None
    try:
        cursor = db._get_cursor()
        cursor.execute("""
            SELECT platform, credentials_json
            FROM marketplace_credentials
            WHERE user_id = %s
        """, (user_id,))

        credentials_store = {}
        for row in cursor.fetchall():
            platform = row['platform'].lower() if isinstance(row, dict) else row[0].lower()
            credentials = row['credentials_json'] if isinstance(row, dict) else row[1]
            if credentials:
                if isinstance(credentials, str):
                    credentials = json.loads(credentials)
                credentials_store[platform] = credentials

        return credentials_store

    except Exception as e:
        print(f"Error fetching credentials: {e}")
        return {}
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass


def _save_search_history(user_id: int, query: SearchQuery, result_count: int):
    """Save search to history for analytics (optional)"""
    if not db:
        return

    try:
        cursor = db._get_cursor()
        cursor.execute("""
            INSERT INTO search_history (user_id, keywords, filters, result_count, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (
            user_id,
            query.keywords,
            json.dumps({
                'item_type': query.item_type,
                'condition': query.condition,
                'price_range': [query.min_price, query.max_price],
            }),
            result_count
        ))
        db.conn.commit()
        cursor.close()
    except Exception as e:
        print(f"Error saving search history: {e}")
        # Don't fail the request if history save fails


def _serialize_result(result: SearchResult) -> Dict:
    """Serialize SearchResult to JSON-compatible dict"""
    return {
        'platform': result.platform,
        'listing_id': result.listing_id,
        'url': result.url,
        'title': result.title,
        'price': result.price,
        'shipping_cost': result.shipping_cost,
        'total_price': result.total_price(),
        'condition': result.condition,
        'thumbnail_url': result.thumbnail_url,
        'photos': result.photos,
        'seller_name': result.seller_name,
        'seller_rating': result.seller_rating,
        'time_posted': result.time_posted.isoformat() if result.time_posted else None,
        'location': result.location,
        'quantity_available': result.quantity_available,
        'accepts_offers': result.accepts_offers,
    }


def _serialize_normalized(normalized) -> Dict:
    """Serialize NormalizedResult to JSON-compatible dict"""
    return {
        'result': _serialize_result(normalized.result),
        'total_price': normalized.total_price,
        'normalized_price': normalized.normalized_price,
        'price_per_condition': normalized.price_per_condition,
        'is_outlier': normalized.is_outlier,
        'similar_count': len(normalized.similar_listings),
        'comparison_notes': normalized.comparison_notes,
    }


def _serialize_market_intel(intel) -> Dict:
    """Serialize MarketIntelligence to JSON-compatible dict"""
    return {
        'query': intel.query,
        'total_results': intel.total_results,
        'average_price': round(intel.average_price, 2),
        'median_price': round(intel.median_price, 2),
        'price_range': [round(intel.price_range[0], 2), round(intel.price_range[1], 2)],
        'volume_indicator': intel.volume_indicator,
        'platforms_found': intel.platforms_found,
        'best_value': _serialize_result(intel.best_value_result) if intel.best_value_result else None,
        'condition_breakdown': intel.condition_breakdown,
    }
