"""
routes_cards.py
All card-collection related endpoints
"""

from flask import Blueprint, request, jsonify, render_template, make_response
from flask_login import login_required, current_user
from pathlib import Path
import json

# Create blueprint
cards_bp = Blueprint('cards', __name__)

# db will be set by init_routes() in web_app.py
db = None

def init_routes(database):
    """Initialize routes with database"""
    global db
    db = database


# =============================================================================
# CARD COLLECTION PAGE
# =============================================================================

@cards_bp.route('/cards')
@login_required
def cards_collection():
    """Render card collection management page."""
    return render_template('cards.html')


# =============================================================================
# ANALYZE CARD (Gemini-based)
# =============================================================================

@cards_bp.route('/api/analyze-card', methods=['POST'])
@login_required
def api_analyze_card():
    """Analyze uploaded photos to detect and classify cards."""
    try:
        from src.ai.gemini_classifier import analyze_card
        from src.schema.unified_listing import Photo
        
        data = request.get_json()
        photo_paths = data.get('photos', [])
        
        if not photo_paths:
            return jsonify({'error': 'No photos provided'}), 400
        
        photos = [Photo(local_path=path) for path in photo_paths]
        result = analyze_card(photos)
        
        if result.get('error'):
            return jsonify(result), 500
        
        return jsonify({'success': True, 'card_data': result})

    except Exception as e:
        print("Card analysis error:", str(e))
        return jsonify({'error': str(e)}), 500


# =============================================================================
# ADD CARD
# =============================================================================

@cards_bp.route('/api/cards/add', methods=['POST'])
@login_required
def api_add_card():
    """Add card to collection manually or using AI analysis."""
    try:
        from src.cards import (
            add_card_to_collection,
            create_card_from_ai_analysis,
            CardCollectionManager,
            UnifiedCard
        )
        from src.cards.storage_maps import suggest_storage_region

        data = request.get_json()
        use_storage_map = data.get('use_storage_map', False)

        # AI analysis path
        if data.get('ai_result'):
            ai_result = data['ai_result']
            photos = data.get('photos', [])
            storage_location = data.get('storage_location')
            
            # Get storage region if enabled
            storage_region = None
            if use_storage_map:
                # Determine franchise and card type
                franchise = ai_result.get('franchise') or ai_result.get('game_name') or ai_result.get('sport')
                card_type = ai_result.get('card_type', 'unknown')
                
                region, guidance = suggest_storage_region(
                    franchise=franchise,
                    card_type=card_type,
                    rarity=ai_result.get('rarity'),
                    is_rookie=ai_result.get('is_rookie_card', False),
                    grading_score=ai_result.get('grading_score')
                )
                
                if region:
                    storage_region = region.value

            # Create card with storage region if provided
            card = create_card_from_ai_analysis(
                ai_result,
                current_user.id,
                photos=photos,
                storage_location=storage_location,
                storage_region=storage_region
            )
            
            if not card:
                return jsonify({'error': 'Invalid card'}), 400
            
            manager = CardCollectionManager()
            card_id = manager.add_card(card)
            
            response_data = {'success': True, 'card_id': card_id}
            
            # Add guidance if storage map was used
            if use_storage_map and storage_region:
                from src.cards.storage_maps import get_storage_map_for_franchise, StorageRegion
                franchise = ai_result.get('franchise') or ai_result.get('game_name') or ai_result.get('sport')
                if franchise:
                    storage_map = get_storage_map_for_franchise(franchise)
                    if storage_map:
                        region_enum = StorageRegion(storage_region)
                        guidance = storage_map.get_guidance_text(region_enum)
                        response_data['storage_guidance'] = guidance
                        response_data['storage_region'] = storage_region
            
            return jsonify(response_data)

        # Manual path
        manager = CardCollectionManager()
        manual_data = data.get('manual_entry', data)

        card = UnifiedCard(
            card_type=manual_data.get('card_type', 'unknown'),
            title=manual_data.get('title', 'Unknown Card'),
            user_id=current_user.id,
            card_number=manual_data.get('card_number'),
            quantity=manual_data.get('quantity', 1),
            organization_mode=manual_data.get('organization_mode', 'by_set'),

            # TCG
            game_name=manual_data.get('game_name'),
            set_name=manual_data.get('set_name'),
            set_code=manual_data.get('set_code'),
            rarity=manual_data.get('rarity'),

            # Sports
            sport=manual_data.get('sport'),
            year=manual_data.get('year'),
            brand=manual_data.get('brand'),
            series=manual_data.get('series'),
            player_name=manual_data.get('player_name'),
            is_rookie_card=manual_data.get('is_rookie_card', False),

            # Grading
            grading_company=manual_data.get('grading_company'),
            grading_score=manual_data.get('grading_score'),

            # Value & org
            estimated_value=manual_data.get('estimated_value'),
            storage_location=manual_data.get('storage_location'),
            photos=manual_data.get('photos', []),
            notes=manual_data.get('notes'),
        )

        card_id = manager.add_card(card)
        return jsonify({'success': True, 'card_id': card_id})

    except Exception as e:
        print("Add card error:", str(e))
        return jsonify({'error': str(e)}), 500


# =============================================================================
# LIST CARDS
# =============================================================================

@cards_bp.route('/api/cards/list', methods=['GET'])
@login_required
def api_list_cards():
    """Return user cards with optional filters."""
    try:
        from src.cards import CardCollectionManager
        manager = CardCollectionManager()

        card_type = request.args.get('card_type')
        org_mode = request.args.get('organization_mode')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))

        cards = manager.get_user_cards(
            current_user.id,
            card_type=card_type,
            organization_mode=org_mode,
            limit=limit,
            offset=offset
        )

        return jsonify({
            'success': True,
            'cards': [c.to_dict() for c in cards],
            'count': len(cards)
        })

    except Exception as e:
        print("List cards error:", str(e))
        return jsonify({'error': str(e)}), 500


# =============================================================================
# ORGANIZED CARDS
# =============================================================================

@cards_bp.route('/api/cards/organized', methods=['GET'])
@login_required
def api_get_organized_cards():
    """Return cards grouped by organization mode."""
    try:
        from src.cards import CardCollectionManager
        manager = CardCollectionManager()

        org = request.args.get('organization_mode')
        card_type = request.args.get('card_type')

        if not org:
            return jsonify({'error': 'organization_mode is required'}), 400

        organized = manager.get_cards_by_organization(current_user.id, org, card_type=card_type)

        result = {
            category: [c.to_dict() for c in cards]
            for category, cards in organized.items()
        }

        return jsonify({'success': True, 'organized': result})

    except Exception as e:
        print("Organized cards error:", str(e))
        return jsonify({'error': str(e)}), 500


# =============================================================================
# SEARCH CARDS
# =============================================================================

@cards_bp.route('/api/cards/search', methods=['GET'])
@login_required
def api_search_cards():
    """Search cards by title, player, set, sport, etc."""
    try:
        from src.cards import CardCollectionManager
        manager = CardCollectionManager()

        query = request.args.get('q', '')
        card_type = request.args.get('card_type')

        if not query:
            return jsonify({'error': 'Search query required'}), 400

        cards = manager.search_cards(current_user.id, query, card_type=card_type)

        return jsonify({
            'success': True,
            'cards': [c.to_dict() for c in cards],
            'count': len(cards)
        })

    except Exception as e:
        print("Search cards error:", str(e))
        return jsonify({'error': str(e)}), 500


# =============================================================================
# EXPORT CARDS
# =============================================================================

@cards_bp.route('/api/cards/export', methods=['GET'])
@login_required
def api_export_cards():
    """Export user cards to CSV."""
    try:
        from src.cards import CardCollectionManager
        manager = CardCollectionManager()

        card_type = request.args.get('card_type')
        org_mode = request.args.get('organization_mode')

        csv_data = manager.export_to_csv(
            current_user.id,
            card_type=card_type,
            organization_mode=org_mode
        )

        if not csv_data:
            return jsonify({'error': 'No cards to export'}), 404

        response = make_response(csv_data)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=card_collection.csv'
        return response

    except Exception as e:
        print("Export error:", str(e))
        return jsonify({'error': str(e)}), 500


# =============================================================================
# IMPORT CARDS
# =============================================================================

@cards_bp.route('/api/cards/import', methods=['POST'])
@login_required
def api_import_cards():
    """Import cards from uploaded CSV."""
    try:
        from src.cards import CardCollectionManager

        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        csv_content = file.read().decode('utf-8')
        card_type = request.form.get('card_type')

        manager = CardCollectionManager()
        result = manager.import_from_csv(current_user.id, csv_content, card_type=card_type)

        return jsonify({
            'success': True,
            'imported': result['imported'],
            'errors': result['errors']
        })

    except Exception as e:
        print("Import error:", str(e))
        return jsonify({'error': str(e)}), 500


# =============================================================================
# SWITCH ORG MODE
# =============================================================================

@cards_bp.route('/api/cards/switch-organization', methods=['POST'])
@login_required
def api_switch_organization():
    """Switch organization mode for user cards."""
    try:
        from src.cards import CardCollectionManager
        manager = CardCollectionManager()

        data = request.get_json()
        new_mode = data.get('new_mode')
        card_type = data.get('card_type')

        valid_modes = [
            'by_set', 'by_year', 'by_sport', 'by_brand', 'by_game',
            'by_rarity', 'by_number', 'by_grading', 'by_value',
            'by_binder', 'custom'
        ]

        if new_mode not in valid_modes:
            return jsonify({'error': 'Invalid organization mode'}), 400

        manager.switch_organization_mode(current_user.id, new_mode, card_type=card_type)

        return jsonify({'success': True})

    except Exception as e:
        print("Switch org mode error:", str(e))
        return jsonify({'error': str(e)}), 500


# =============================================================================
# CARD STATS
# =============================================================================

@cards_bp.route('/api/cards/stats', methods=['GET'])
@login_required
def api_card_stats():
    """Get card collection statistics."""
    try:
        from src.cards import CardCollectionManager
        manager = CardCollectionManager()

        stats = manager.get_collection_stats(current_user.id)

        return jsonify({'success': True, 'stats': stats})

    except Exception as e:
        print("Stats error:", str(e))
        return jsonify({'error': str(e)}), 500


# =============================================================================
# VAULT OVERVIEW PAGE
# =============================================================================

@cards_bp.route('/vault')
@login_required
def vault_overview():
    """Render vault overview page showing both cards and coins."""
    return render_template('vault.html')


# =============================================================================
# CARDS VAULT PAGE
# =============================================================================

@cards_bp.route('/vault/cards')
@login_required
def vault_cards():
    """Render cards vault page."""
    return render_template('vault_cards.html')


# =============================================================================
# COINS VAULT PAGE
# =============================================================================

@cards_bp.route('/vault/coins')
@login_required
def vault_coins():
    """Render coins vault page."""
    return render_template('vault_coins.html')


# =============================================================================
# GET CARD
# =============================================================================

@cards_bp.route('/api/cards/<int:card_id>', methods=['GET'])
@login_required
def api_get_card(card_id):
    """Retrieve a specific card."""
    try:
        from src.cards import CardCollectionManager
        manager = CardCollectionManager()

        card = manager.get_card(card_id)
        if not card:
            return jsonify({'error': 'Not found'}), 404

        if card.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403

        return jsonify({'success': True, 'card': card.to_dict()})

    except Exception as e:
        print("Get card error:", str(e))
        return jsonify({'error': str(e)}), 500


# =============================================================================
# UPDATE CARD
# =============================================================================

@cards_bp.route('/api/cards/<int:card_id>', methods=['PUT'])
@login_required
def api_update_card(card_id):
    """Update a card."""
    try:
        from src.cards import CardCollectionManager
        manager = CardCollectionManager()

        card = manager.get_card(card_id)
        if not card:
            return jsonify({'error': 'Not found'}), 404

        if card.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403

        data = request.get_json()

        for field in [
            'title', 'quantity', 'storage_location', 'notes',
            'estimated_value', 'grading_company', 'grading_score'
        ]:
            if field in data:
                setattr(card, field, data[field])

        manager.update_card(card_id, card)

        return jsonify({'success': True})

    except Exception as e:
        print("Update card error:", str(e))
        return jsonify({'error': str(e)}), 500


# =============================================================================
# DELETE CARD
# =============================================================================

@cards_bp.route('/api/cards/<int:card_id>', methods=['DELETE'])
@login_required
def api_delete_card(card_id):
    """Delete a card."""
    try:
        from src.cards import CardCollectionManager
        manager = CardCollectionManager()

        card = manager.get_card(card_id)
        if not card:
            return jsonify({'error': 'Not found'}), 404

        if card.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403

        manager.delete_card(card_id)

        return jsonify({'success': True})

    except Exception as e:
        print("Delete card error:", str(e))
        return jsonify({'error': str(e)}), 500


# =============================================================================
# COIN VAULT API ENDPOINTS
# =============================================================================

@cards_bp.route('/api/coins/list', methods=['GET'])
@login_required
def api_list_coins():
    """Return user coins with optional filters."""
    try:
        # Return empty list - coin management not yet implemented
        # TODO: Implement coin storage and retrieval when coin system is built
        return jsonify({
            'success': True,
            'coins': [],
            'count': 0,
            'message': 'Coin management coming soon'
        })

    except Exception as e:
        print("List coins error:", str(e))
        return jsonify({'error': str(e)}), 500


@cards_bp.route('/api/coins/stats', methods=['GET'])
@login_required
def api_coin_stats():
    """Get coin collection statistics."""
    try:
        # Return zeros - coin management not yet implemented
        stats = {
            'total_coins': 0,
            'total_value': 0,
            'unique_types': 0,
            'graded_coins': 0
        }

        return jsonify({'success': True, 'stats': stats})

    except Exception as e:
        print("Stats error:", str(e))
        return jsonify({'error': str(e)}), 500


@cards_bp.route('/api/vault/stats', methods=['GET'])
@login_required
def api_vault_stats():
    """Get combined vault statistics for cards and coins."""
    try:
        # Get card stats with proper defaults
        card_stats = {'total_cards': 0, 'total_value': 0, 'unique_sets': 0, 'graded_cards': 0}
        try:
            from src.cards import CardCollectionManager
            manager = CardCollectionManager()
            raw_stats = manager.get_collection_stats(current_user.id)
            if raw_stats:
                # Ensure all values have defaults (handle None from DB)
                card_stats = {
                    'total_cards': raw_stats.get('total_cards') or 0,
                    'total_value': float(raw_stats.get('total_value') or 0),
                    'total_quantity': raw_stats.get('total_quantity') or 0,
                    'card_types': raw_stats.get('card_types') or 0,
                    'graded_cards': raw_stats.get('graded_cards') or 0
                }
        except Exception as e:
            print(f"Card stats error: {e}")

        # Mock coin stats for now (will be replaced when coin system is implemented)
        coin_stats = {
            'total_coins': 0,
            'coin_value': 0,
            'graded_coins': 0
        }

        # Calculate totals with proper null handling
        total_cards = card_stats.get('total_cards') or 0
        total_coins = coin_stats.get('total_coins') or 0
        card_value = card_stats.get('total_value') or 0
        coin_value = coin_stats.get('coin_value') or 0

        combined_stats = {
            'total_items': total_cards + total_coins,
            'total_value': card_value + coin_value,
            'cards': card_stats,
            'coins': coin_stats
        }

        return jsonify({'success': True, 'stats': combined_stats})

    except Exception as e:
        print("Vault stats error:", str(e))
        return jsonify({'error': str(e)}), 500
