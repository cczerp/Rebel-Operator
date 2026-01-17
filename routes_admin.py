"""
routes_admin.py
Admin-only routes & admin API endpoints
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps

# Create blueprint
admin_bp = Blueprint("admin", __name__)

# db will be set by init_routes() in web_app.py
db = None

def init_routes(database):
    """Initialize routes with database"""
    global db
    db = database


# -------------------------------------------------------------------------
# Helper: Require admin
# -------------------------------------------------------------------------

def admin_required(f):
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            flash("Admin access required", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrapper


# -------------------------------------------------------------------------
# ADMIN DASHBOARD
# -------------------------------------------------------------------------

@admin_bp.route("/admin")
@admin_required
def admin_dashboard():
    stats = db.get_system_stats()
    users = db.get_all_users(include_inactive=True)
    recent_logs = db.get_activity_logs(limit=20)

    # Debug: Log user count
    print(f"DEBUG: Found {len(users)} users in database")
    for user in users:
        print(f"  - {user.get('username')} (ID: {user.get('id')}, Email: {user.get('email')})")

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        users=users,
        recent_activity=recent_logs
    )


# -------------------------------------------------------------------------
# ADMIN — USER LIST
# -------------------------------------------------------------------------

@admin_bp.route("/admin/users")
@admin_required
def admin_users():
    users = db.get_all_users(include_inactive=True)
    return render_template("admin/users.html", users=users)


# -------------------------------------------------------------------------
# ADMIN — USER DETAILS
# -------------------------------------------------------------------------

@admin_bp.route("/admin/user/<int:user_id>")
@admin_required
def admin_user_detail(user_id):
    user = db.get_user_by_id(user_id)
    if not user:
        flash("User not found", "error")
        return redirect(url_for("admin.admin_users"))

    # Get recent listings
    cursor = db._get_cursor()
    cursor.execute(
        "SELECT * FROM listings WHERE user_id = %s ORDER BY created_at DESC LIMIT 50",
        (user_id,)
    )
    listings = [dict(row) for row in cursor.fetchall()]

    # Get activity logs
    logs = db.get_activity_logs(user_id=user_id, limit=50)

    return render_template(
        "admin/user_detail.html",
        user=user,
        listings=listings,
        activity=logs
    )


# -------------------------------------------------------------------------
# ADMIN — ACTIVITY LOGS
# -------------------------------------------------------------------------

@admin_bp.route("/admin/activity")
@admin_required
def admin_activity():
    page = request.args.get("page", 1, type=int)
    limit = 50
    offset = (page - 1) * limit

    user_id = request.args.get("user_id", type=int)
    action = request.args.get("action")

    logs = db.get_activity_logs(user_id=user_id, action=action, limit=limit, offset=offset)

    return render_template("admin/activity.html", logs=logs, page=page)


# =========================================================================
# ADMIN API ENDPOINTS
# =========================================================================

# -------------------------------------------------------------------------
# Toggle admin
# -------------------------------------------------------------------------

@admin_bp.route("/api/admin/user/<int:user_id>/toggle-admin", methods=["POST"])
@admin_required
def api_toggle_admin(user_id):
    if user_id == current_user.id:
        return jsonify({"error": "You cannot change your own admin status"}), 400

    try:
        ok = db.toggle_user_admin(user_id)
        if not ok:
            return jsonify({"error": "User not found"}), 404

        db.log_activity(
            action="toggle_admin",
            user_id=current_user.id,
            resource_type="user",
            resource_id=user_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent")
        )

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------------------------
# Toggle active status
# -------------------------------------------------------------------------

@admin_bp.route("/api/admin/user/<int:user_id>/toggle-active", methods=["POST"])
@admin_required
def api_toggle_active(user_id):
    if user_id == current_user.id:
        return jsonify({"error": "You cannot deactivate your own account"}), 400

    try:
        ok = db.toggle_user_active(user_id)
        if not ok:
            return jsonify({"error": "User not found"}), 404

        db.log_activity(
            action="toggle_active",
            user_id=current_user.id,
            resource_type="user",
            resource_id=user_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent")
        )

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------------------------
# Delete user
# -------------------------------------------------------------------------

@admin_bp.route("/api/admin/user/<int:user_id>/delete", methods=["DELETE"])
@admin_required
def api_delete_user(user_id):

    if user_id == current_user.id:
        return jsonify({"error": "You cannot delete your own account"}), 400

    try:
        db.log_activity(
            action="delete_user",
            user_id=current_user.id,
            resource_type="user",
            resource_id=user_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent")
        )

        db.delete_user(user_id)
        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------------------------
# Debug: List all users (API)
# -------------------------------------------------------------------------

@admin_bp.route("/api/admin/debug/users", methods=["GET"])
@admin_required
def api_debug_users():
    """Debug endpoint to see all users in database"""
    try:
        users = db.get_all_users(include_inactive=True)
        return jsonify({
            "success": True,
            "count": len(users),
            "users": users
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------------------------
# PHOTO CURATION DASHBOARD
# -------------------------------------------------------------------------

@admin_bp.route("/admin/photo-curation")
@admin_required
def photo_curation():
    """Admin dashboard for curating artifact photos"""
    try:
        # Get all artifacts with pending photos
        artifacts_with_photos = db.get_artifacts_with_pending_photos()

        # Get stats
        stats = db.get_photo_curation_stats()

        return render_template('admin/photo_curation.html',
                             artifacts_with_photos=artifacts_with_photos,
                             stats=stats)
    except Exception as e:
        flash(f'Error loading photo curation dashboard: {str(e)}', 'error')
        return redirect(url_for('admin.admin_dashboard'))


# -------------------------------------------------------------------------
# HALL PHOTOS - Grouped by Franchise
# -------------------------------------------------------------------------

@admin_bp.route("/admin/hall-photos")
@admin_required
def hall_photos():
    """Admin page for reviewing Hall of Records pending photos - grouped by franchise"""
    try:
        # Get all artifacts with pending photos
        artifacts_with_photos = db.get_artifacts_with_pending_photos()

        # Group by franchise
        franchise_groups = {}
        for item in artifacts_with_photos:
            artifact = item['artifact']
            franchise = artifact.get('franchise') or 'Unknown'

            if franchise not in franchise_groups:
                franchise_groups[franchise] = []

            franchise_groups[franchise].append(item)

        # Sort franchises alphabetically
        sorted_franchises = sorted(franchise_groups.keys())

        return render_template('admin/hall_photos.html',
                             franchise_groups=franchise_groups,
                             sorted_franchises=sorted_franchises)
    except Exception as e:
        flash(f'Error loading Hall Photos: {str(e)}', 'error')
        return redirect(url_for('admin.admin_dashboard'))


# -------------------------------------------------------------------------
# Toggle Photo Selection (Admin)
# -------------------------------------------------------------------------

@admin_bp.route("/api/admin/toggle-photo-selection", methods=["POST"])
@admin_required
def api_toggle_photo_selection():
    """Toggle a photo's selection status for Hall of Records"""
    try:
        data = request.get_json()
        photo_id = data.get('photo_id')
        artifact_id = data.get('artifact_id')

        if not photo_id or not artifact_id:
            return jsonify({'error': 'Missing photo_id or artifact_id'}), 400

        cursor = db._get_cursor()

        # Get current selection status
        cursor.execute("""
            SELECT is_selected FROM pending_artifact_photos
            WHERE id = %s AND artifact_id = %s
        """, (photo_id, artifact_id))

        result = cursor.fetchone()
        if not result:
            return jsonify({'error': 'Photo not found'}), 404

        current_status = result['is_selected']
        new_status = not current_status

        # Update selection status
        cursor.execute("""
            UPDATE pending_artifact_photos
            SET is_selected = %s
            WHERE id = %s AND artifact_id = %s
        """, (new_status, photo_id, artifact_id))

        db.conn.commit()

        # If selected, add to public photos; if deselected, remove from public photos
        if new_status:
            # Get photo URL
            cursor.execute("""
                SELECT photo_url FROM pending_artifact_photos
                WHERE id = %s
            """, (photo_id,))
            photo = cursor.fetchone()

            if photo:
                db.select_artifact_photos(artifact_id, None, [photo_id])

        db.log_activity(
            action="toggle_photo_selection",
            user_id=current_user.id,
            resource_type="artifact_photo",
            resource_id=photo_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent")
        )

        return jsonify({
            'success': True,
            'new_status': new_status,
            'message': 'Published to Hall of Records' if new_status else 'Removed from Hall of Records'
        })

    except Exception as e:
        db.conn.rollback()
        return jsonify({'error': str(e)}), 500
