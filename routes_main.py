# -------------------------------------------------------------------------
# INDEX + MAIN PAGES
# -------------------------------------------------------------------------

@main.route("/")
def index():
    """Home page (guest landing or user dashboard)"""
    if not current_user.is_authenticated:
        return render_template("index.html", is_guest=True)
    return render_template("index.html", is_guest=False)


@main.route("/create")
def create_listing():
    """Create new listing (guests allowed for demo mode)"""
    is_guest = not current_user.is_authenticated
    draft_id = request.args.get("draft_id", type=int)
    return render_template("create.html", is_guest=is_guest, draft_id=draft_id)


@main.route("/drafts")
@login_required
def drafts():
    drafts_list = db.get_drafts(limit=100, user_id=current_user.id)
    return render_template("drafts.html", drafts=drafts_list)


@main.route("/listings")
@login_required
def listings():
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT l.*, GROUP_CONCAT(pl.platform || ':' || pl.status) AS platform_statuses
        FROM listings l
        LEFT JOIN platform_listings pl ON l.id = pl.listing_id
        WHERE l.status!='draft' AND l.user_id = ?
        GROUP BY l.id
        ORDER BY l.created_at DESC
        LIMIT 50
    """, (current_user.id,))
    listings_list = [dict(row) for row in cursor.fetchall()]
    return render_template("listings.html", listings=listings_list)


@main.route("/notifications")
@login_required
def notifications():
    if notification_manager:
        try:
            notifs = notification_manager.get_recent_notifications(limit=50)
            for n in notifs:
                if n.get("data") and isinstance(n["data"], str):
                    try:
                        n["data"] = json.loads(n["data"])
                    except:
                        n["data"] = {}
        except Exception as e:
            print("Notification error:", e)
            notifs = []
    else:
        notifs = []

    return render_template("notifications.html", notifications=notifs)


# -------------------------------------------------------------------------
# STORAGE SYSTEM
# -------------------------------------------------------------------------

@main.route("/storage")
@login_required
def storage():
    storage_map = db.get_storage_map(current_user.id)
    return render_template("storage.html", storage_map=storage_map)


@main.route("/storage/clothing")
@login_required
def storage_clothing():
    bins = db.get_storage_bins(current_user.id, bin_type="clothing")
    return render_template("storage_clothing.html", bins=bins)


@main.route("/storage/cards")
@login_required
def storage_cards():
    bins = db.get_storage_bins(current_user.id, bin_type="cards")

    # Auto-create default bin “A” if none exist
    if not bins:
        db.create_storage_bin(current_user.id, "A", "cards", "Default card bin")
        bins = db.get_storage_bins(current_user.id, bin_type="cards")

    return render_template("storage_cards.html", bins=bins)


@main.route("/storage/map")
@login_required
def storage_map():
    storage_map = db.get_storage_map(current_user.id)
    return render_template("storage_map.html", storage_map=storage_map)


# -------------------------------------------------------------------------
# STORAGE API ENDPOINTS
# -------------------------------------------------------------------------

@main.route("/api/storage/create-bin", methods=["POST"])
@login_required
def create_storage_bin():
    data = request.json
    try:
        bin_name = data["bin_name"]
        bin_type = data["bin_type"]
        desc = data.get("description")

        bin_id = db.create_storage_bin(current_user.id, bin_name, bin_type, desc)
        return jsonify({"success": True, "bin_id": bin_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main.route("/api/storage/create-section", methods=["POST"])
@login_required
def create_storage_section():
    data = request.json
    try:
        bin_id = int(data["bin_id"])
        name = data["section_name"]
        cap = data.get("capacity")

        sec_id = db.create_storage_section(bin_id, name, cap)
        return jsonify({"success": True, "section_id": sec_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main.route("/api/storage/add-item", methods=["POST"])
@login_required
def add_storage_item():
    data = request.json
    try:
        bin_id = int(data["bin_id"])
        section_id = int(data["section_id"]) if data.get("section_id") else None
        item_type = data.get("item_type")
        category = data.get("category")
        title = data.get("title")
        desc = data.get("description")
        qty = int(data.get("quantity", 1))
        photos = data.get("photos", [])
        notes = data.get("notes")

        # Fetch bin
        bins = db.get_storage_bins(current_user.id)
        b = next((x for x in bins if x["id"] == bin_id), None)
        if not b:
            return jsonify({"error": "Bin not found"}), 404

        section_name = None
        if section_id:
            sections = db.get_storage_sections(bin_id)
            s = next((x for x in sections if x["id"] == section_id), None)
            if s:
                section_name = s["section_name"]

        # Generate storage ID like: A-02-SHOES-0001
        storage_id = db.generate_storage_id(
            current_user.id, b["bin_name"], section_name, category
        )

        item_id = db.add_storage_item(
            current_user.id, storage_id, bin_id, section_id,
            item_type, category, title, desc, qty, photos, notes
        )

        return jsonify({"success": True, "item_id": item_id, "storage_id": storage_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@main.route("/api/storage/find", methods=["GET"])
@login_required
def find_storage_item():
    storage_id = request.args.get("storage_id")
    if not storage_id:
        return jsonify({"error": "storage_id required"}), 400

    item = db.find_storage_item(current_user.id, storage_id)
    if item:
        return jsonify({"success": True, "item": item})
    return jsonify({"error": "Item not found"}), 404


@main.route("/api/storage/items", methods=["GET"])
@login_required
def get_storage_items():
    bin_id = request.args.get("bin_id", type=int)
    sec_id = request.args.get("section_id", type=int)
    item_type = request.args.get("item_type")
    limit = request.args.get("limit", 100, type=int)

    items = db.get_storage_items(
        current_user.id,
        bin_id=bin_id,
        section_id=sec_id,
        item_type=item_type,
        limit=limit
    )
    return jsonify({"success": True, "items": items})
