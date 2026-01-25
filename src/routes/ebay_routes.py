"""
eBay OAuth Routes
=================
Flask routes for eBay OAuth integration.

Routes:
- /ebay/connect - Initiates OAuth flow
- /ebay/callback - Handles OAuth callback
- /ebay/disconnect - Removes connection
- /ebay/status - Check connection status
"""

import os
import secrets
from flask import Blueprint, request, redirect, session, jsonify, render_template, flash
from flask_login import login_required, current_user

from ..ebay.oauth_client import get_ebay_oauth_client
from ..ebay.token_manager import eBayTokenManager


# Create blueprint
ebay_bp = Blueprint('ebay', __name__, url_prefix='/ebay')

# db will be set by init_routes() in web_app.py
db = None
token_manager = None


def init_routes(database):
    """Initialize routes with database"""
    global db, token_manager
    db = database
    token_manager = eBayTokenManager(db)


# =============================================================================
# EBAY OAUTH ROUTES
# =============================================================================

@ebay_bp.route('/connect')
@login_required
def connect():
    """
    Initiate eBay OAuth flow.

    Redirects user to eBay authorization page.
    """
    try:
        # Get environment (sandbox or production)
        environment = request.args.get('env', os.getenv('EBAY_ENV', 'sandbox'))

        if environment not in ['sandbox', 'production']:
            flash('Invalid environment specified', 'error')
            return redirect('/settings')

        # Generate state token for CSRF protection
        state_token = secrets.token_urlsafe(32)
        session['ebay_oauth_state'] = state_token
        session['ebay_oauth_env'] = environment

        # Get eBay OAuth client
        oauth_client = get_ebay_oauth_client(environment)

        # Generate authorization URL
        auth_url = oauth_client.get_authorization_url(state=state_token)

        print(f"[INFO] Redirecting user {current_user.id} to eBay OAuth ({environment})")

        return redirect(auth_url)

    except Exception as e:
        print(f"[ERROR] eBay connect error: {e}")
        flash(f'Failed to connect to eBay: {str(e)}', 'error')
        return redirect('/settings')


@ebay_bp.route('/callback')
@login_required
def callback():
    """
    Handle eBay OAuth callback.

    Exchanges authorization code for access tokens and saves them.
    """
    try:
        # Get authorization code and state from query parameters
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        error_description = request.args.get('error_description')

        # Handle OAuth errors
        if error:
            print(f"[ERROR] eBay OAuth error: {error} - {error_description}")
            flash(f'eBay authorization failed: {error_description}', 'error')
            return redirect('/settings')

        # Validate state token (CSRF protection)
        session_state = session.get('ebay_oauth_state')
        if not state or state != session_state:
            print(f"[ERROR] State mismatch - CSRF attack detected")
            flash('Invalid state token. Please try again.', 'error')
            return redirect('/settings')

        # Get environment from session
        environment = session.get('ebay_oauth_env', 'sandbox')

        # Clear session data
        session.pop('ebay_oauth_state', None)
        session.pop('ebay_oauth_env', None)

        if not code:
            flash('No authorization code received from eBay', 'error')
            return redirect('/settings')

        # Get OAuth client
        oauth_client = get_ebay_oauth_client(environment)

        # Exchange code for tokens
        print(f"[INFO] Exchanging authorization code for tokens...")
        token_response = oauth_client.exchange_code_for_tokens(code)

        # Get eBay user info (optional, for display)
        try:
            ebay_user_info = oauth_client.get_user_info(token_response['access_token'])
        except Exception as e:
            print(f"[WARNING] Could not fetch eBay user info: {e}")
            ebay_user_info = None

        # Save tokens to database
        success = token_manager.save_tokens(
            user_id=current_user.id,
            access_token=token_response['access_token'],
            refresh_token=token_response['refresh_token'],
            expires_in=token_response['expires_in'],
            environment=environment,
            scopes=oauth_client.REQUIRED_SCOPES,
            ebay_user_info=ebay_user_info
        )

        if success:
            ebay_username = ebay_user_info.get('username', 'your eBay account') if ebay_user_info else 'your eBay account'
            flash(f'Successfully connected to {ebay_username} ({environment})!', 'success')
            print(f"[SUCCESS] User {current_user.id} connected to eBay ({environment})")
        else:
            flash('Failed to save eBay tokens. Please try again.', 'error')

        return redirect('/settings')

    except Exception as e:
        print(f"[ERROR] eBay callback error: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Failed to complete eBay authorization: {str(e)}', 'error')
        return redirect('/settings')


@ebay_bp.route('/disconnect', methods=['POST'])
@login_required
def disconnect():
    """
    Disconnect eBay account.

    Removes OAuth tokens from database.
    """
    try:
        # Get environment
        environment = request.form.get('env', os.getenv('EBAY_ENV', 'sandbox'))

        if environment not in ['sandbox', 'production']:
            return jsonify({'error': 'Invalid environment'}), 400

        # Delete tokens
        success = token_manager.delete_tokens(current_user.id, environment)

        if success:
            print(f"[INFO] User {current_user.id} disconnected from eBay ({environment})")
            return jsonify({'success': True, 'message': f'Disconnected from eBay ({environment})'})
        else:
            return jsonify({'error': 'Failed to disconnect'}), 500

    except Exception as e:
        print(f"[ERROR] eBay disconnect error: {e}")
        return jsonify({'error': str(e)}), 500


@ebay_bp.route('/status')
@login_required
def status():
    """
    Check eBay connection status for current user.

    Returns JSON with connection status for both sandbox and production.
    """
    try:
        # Check both environments
        sandbox_connected = token_manager.has_valid_tokens(current_user.id, 'sandbox')
        production_connected = token_manager.has_valid_tokens(current_user.id, 'production')

        # Get user info if connected
        sandbox_info = None
        production_info = None

        if sandbox_connected:
            sandbox_info = token_manager.get_ebay_user_info(current_user.id, 'sandbox')

        if production_connected:
            production_info = token_manager.get_ebay_user_info(current_user.id, 'production')

        return jsonify({
            'success': True,
            'sandbox': {
                'connected': sandbox_connected,
                'ebay_username': sandbox_info.get('ebay_username') if sandbox_info else None,
                'ebay_user_id': sandbox_info.get('ebay_user_id') if sandbox_info else None
            },
            'production': {
                'connected': production_connected,
                'ebay_username': production_info.get('ebay_username') if production_info else None,
                'ebay_user_id': production_info.get('ebay_user_id') if production_info else None
            }
        })

    except Exception as e:
        print(f"[ERROR] eBay status error: {e}")
        return jsonify({'error': str(e)}), 500


@ebay_bp.route('/test-connection')
@login_required
def test_connection():
    """
    Test eBay API connection with current tokens.

    Makes a simple API call to verify tokens work.
    """
    try:
        environment = request.args.get('env', os.getenv('EBAY_ENV', 'sandbox'))

        # Get tokens
        tokens = token_manager.get_tokens(current_user.id, environment)

        if not tokens:
            return jsonify({
                'success': False,
                'error': f'No {environment} tokens found. Please connect to eBay first.'
            }), 401

        # Try to get user info as a test
        oauth_client = get_ebay_oauth_client(environment)
        user_info = oauth_client.get_user_info(tokens['access_token'])

        return jsonify({
            'success': True,
            'environment': environment,
            'ebay_username': user_info.get('username'),
            'message': 'eBay connection is working!'
        })

    except Exception as e:
        print(f"[ERROR] eBay test connection error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# SETTINGS PAGE INTEGRATION
# =============================================================================

@ebay_bp.route('/settings-panel')
@login_required
def settings_panel():
    """
    Render eBay settings panel for inclusion in settings page.

    Returns HTML fragment.
    """
    try:
        # Get connection status
        sandbox_connected = token_manager.has_valid_tokens(current_user.id, 'sandbox')
        production_connected = token_manager.has_valid_tokens(current_user.id, 'production')

        sandbox_info = token_manager.get_ebay_user_info(current_user.id, 'sandbox') if sandbox_connected else None
        production_info = token_manager.get_ebay_user_info(current_user.id, 'production') if production_connected else None

        return render_template(
            'ebay_settings_panel.html',
            sandbox_connected=sandbox_connected,
            production_connected=production_connected,
            sandbox_info=sandbox_info,
            production_info=production_info,
            current_env=os.getenv('EBAY_ENV', 'sandbox')
        )

    except Exception as e:
        print(f"[ERROR] eBay settings panel error: {e}")
        return f'<div class="alert alert-danger">Error loading eBay settings: {str(e)}</div>'


# =============================================================================
# DIAGNOSTIC ENDPOINTS
# =============================================================================

@ebay_bp.route('/diagnose')
@login_required
def diagnose():
    """
    Diagnose eBay API connectivity and configuration.

    Tests both Browse API (client_credentials) and user OAuth tokens.
    Returns detailed diagnostic information.
    """
    import base64

    diagnostics = {
        "credentials": {},
        "browse_api": {},
        "finding_api": {},
        "user_oauth": {},
        "recommendations": []
    }

    # Check environment variables
    app_id = os.environ.get("EBAY_PROD_APP_ID")
    cert_id = os.environ.get("EBAY_PROD_CERT_ID")
    b64_upper = os.environ.get("EBAY_PROD_B64")
    b64_lower = os.environ.get("EBAY_PROD_b64")

    diagnostics["credentials"]["EBAY_PROD_APP_ID"] = "set" if app_id else "not set"
    diagnostics["credentials"]["EBAY_PROD_CERT_ID"] = "set" if cert_id else "not set"
    diagnostics["credentials"]["EBAY_PROD_B64"] = "set" if b64_upper else "not set"
    diagnostics["credentials"]["EBAY_PROD_b64_lowercase"] = "set" if b64_lower else "not set"

    if b64_lower and not b64_upper:
        diagnostics["recommendations"].append(
            "EBAY_PROD_b64 is set with lowercase - this will work but consider renaming to EBAY_PROD_B64"
        )

    # Test Browse API token
    try:
        from ..ebay.ebay_auth import get_ebay_token
        token = get_ebay_token()
        diagnostics["browse_api"]["token"] = "obtained successfully"
        diagnostics["browse_api"]["token_preview"] = token[:20] + "..." if token else None

        # Test a simple search
        from ..ebay.ebay_search import search_ebay
        test_result = search_ebay("iPhone", limit=3)
        diagnostics["browse_api"]["test_search_query"] = "iPhone"
        diagnostics["browse_api"]["test_search_total"] = test_result.get("total", 0)
        diagnostics["browse_api"]["test_search_items_returned"] = len(test_result.get("items", []))

        if test_result.get("total", 0) == 0:
            diagnostics["browse_api"]["status"] = "working but no results"
            diagnostics["recommendations"].append(
                "Browse API returns 0 results. Check if Browse API is enabled in your eBay Developer Portal."
            )
        else:
            diagnostics["browse_api"]["status"] = "fully working"

    except Exception as e:
        diagnostics["browse_api"]["status"] = "error"
        diagnostics["browse_api"]["error"] = str(e)
        diagnostics["recommendations"].append(f"Browse API error: {str(e)}")

    # Test Finding API (uses app_id directly)
    try:
        from ..search.platform_searchers import eBaySearcher
        from ..search.base_searcher import SearchQuery

        credentials = {"app_id": app_id} if app_id else {}
        searcher = eBaySearcher(credentials)
        query = SearchQuery(keywords="iPhone", limit=3)
        results = searcher.search(query)

        diagnostics["finding_api"]["status"] = "working" if results else "no results"
        diagnostics["finding_api"]["test_search_items"] = len(results)

        if results:
            diagnostics["finding_api"]["sample_title"] = results[0].title[:50] if results[0].title else None

        if not results and app_id:
            diagnostics["recommendations"].append(
                "Finding API returned no results. Check if your App ID is correct and app is approved."
            )

    except Exception as e:
        diagnostics["finding_api"]["status"] = "error"
        diagnostics["finding_api"]["error"] = str(e)

    # Check user OAuth tokens
    try:
        production_connected = token_manager.has_valid_tokens(current_user.id, 'production')
        sandbox_connected = token_manager.has_valid_tokens(current_user.id, 'sandbox')

        diagnostics["user_oauth"]["production_connected"] = production_connected
        diagnostics["user_oauth"]["sandbox_connected"] = sandbox_connected

        if production_connected:
            info = token_manager.get_ebay_user_info(current_user.id, 'production')
            diagnostics["user_oauth"]["production_username"] = info.get("ebay_username") if info else None

    except Exception as e:
        diagnostics["user_oauth"]["error"] = str(e)

    # Summary
    if diagnostics["browse_api"].get("status") == "fully working":
        diagnostics["summary"] = "Everything is working correctly!"
    elif diagnostics["finding_api"].get("status") == "working":
        diagnostics["summary"] = "Finding API works. Browse API may need to be enabled in eBay Developer Portal."
        diagnostics["recommendations"].append(
            "Consider using multi-platform search (/api/search/multi-platform) which uses the Finding API."
        )
    else:
        diagnostics["summary"] = "Both APIs have issues. Check your credentials and eBay app settings."

    return jsonify(diagnostics)


# =============================================================================
# ACCOUNT EVENTS WEBHOOK
# =============================================================================

@ebay_bp.route('/account-events', methods=['POST'])
def ebay_account_events():
    """
    Handle eBay account events webhook.

    Simply returns 200 OK as requested.
    """
    return "", 200
