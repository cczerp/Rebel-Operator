# routes_main.py
"""
Main application routes (everything except card collection).
Blueprint: main
"""

import os
import uuid
import json
from pathlib import Path
from datetime import datetime
import csv
import base64
from io import StringIO, BytesIO

from flask import (
    Blueprint, render_template, request, jsonify, redirect,
    url_for, flash, session, send_file, Response
)
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from PIL import Image

from app_core import app, db, admin_required, notification_manager, User
from src.schema.unified_listing import UnifiedListing, Price, Photo, ListingCondition, ItemSpecifics
from src.adapters.poshmark_adapter import PoshmarkAdapter
from src.adapters.all_platforms import (
    EtsyAdapter, ShopifyAdapter, RubyLaneAdapter,
    WooCommerceAdapter, FacebookShopsAdapter
)

main = Blueprint("main", __name__)

# -------------------------------------------------------------------------
# PLATFORM CONFIG
# -------------------------------------------------------------------------
PLATFORM_CONFIG = {
    'poshmark': {
        'type': 'csv',
        'name': 'Poshmark',
        'instructions': [
            '1. Log into your Poshmark account',
            '2. Go to https://poshmark.com/sell/bulk',
            '3. Upload the CSV file',
            '4. Review and publish your listings'
        ]
    },
    'rubylane': {
        'type': 'csv',
        'name': 'Ruby Lane',
        'instructions': [
            '1. Log into Ruby Lane Seller Portal',
            '2. Open Bulk Upload',
            '3. Upload CSV',
            '4. Review items'
        ]
    },
    'threadup': {
        'type': 'csv',
        'name': 'ThredUp',
        'instructions': [
            '1. Login to ThredUp',
            '2. Go to Bulk Listing Tool',
            '3. Upload CSV'
        ]
    },
    'depop': {
        'type': 'csv',
        'name': 'Depop',
        'instructions': [
            'Depop does not support CSV uploads.',
            'Use the exported CSV fields to copy/paste into Depop app.'
        ]
    },
    'etsy': {'type': 'api', 'name': 'Etsy', 'requires_credentials': True},
    'shopify': {'type': 'api', 'name': 'Shopify', 'requires_credentials': True},
    'facebook': {'type': 'api', 'name': 'Facebook Shops', 'requires_credentials': True},
    'woocommerce': {'type': 'api', 'name': 'WooCommerce', 'requires_credentials': True},
}

# -------------------------------------------------------------------------
# UTIL — Convert DB listing → UnifiedListing
# -------------------------------------------------------------------------
def convert_listing_to_unified(listing_dict: dict) -> UnifiedListing:
    photos = []
    if listing_dict.get('photos'):
        photo_paths = json.loads(listing_dict['photos']) if isinstance(listing_dict['photos'], str) else listing_dict['photos']
        for i, p in enumerate(photo_paths):
            url = p if p.startswith("http") else f"/uploads/{Path(p).name}"
            photos.append(Photo(url=url, local_path=p, is_primary=(i == 0)))

    condition_map = {
        'new': ListingCondition.NEW,
        'like_new': ListingCondition.LIKE_NEW,
        'excellent': ListingCondition.EXCELLENT,
        'good': ListingCondition.GOOD,
        'fair': ListingCondition.FAIR,
        'poor': ListingCondition.POOR
    }

    condition = condition_map.get(listing_dict.get('condition', 'good'), ListingCondition.GOOD)

    return UnifiedListing(
        title=listing_dict.get("title", ""),
        description=listing_dict.get("description", ""),
        price=Price(amount=float(listing_dict.get("price", 0))),
        condition=condition,
        photos=photos,
        item_specifics=ItemSpecifics(
            brand=listing_dict.get("brand"),
            size=listing_dict.get("size"),
            color=listing_dict.get("color"),
            material=listing_dict.get("material"),
        ),
        sku=listing_dict.get("sku")
    )

# -------------------------------------------------------------------------
# AUTH ROUTES
# -------------------------------------------------------------------------
@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        data = request.json if request.is_json else request.form
        username = data.get("username")
        password = data.get("password")

        user = db.get_user_by_username(username)
        if user and check_password_hash(user["password_hash"], password):

            # inactive?
            if not user.get("is_active", True):
                msg = "Your account has been deactivated."
                if request.is_json:
                    return jsonify({"error": msg}), 401
                flash(msg, "error")
                return render_template("login.html")

            u = User(
                user["id"],
                user["username"],
                user["email"],
                user.get("is_admin", False),
                user.get("is_active", True)
            )

            login_user(u, remember=True)
            db.update_last_login(user["id"])

            db.log_activity(
                action="login",
                user_id=user["id"],
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent")
            )

            if request.is_json:
                return jsonify({"success": True, "redirect": url_for("main.index")})

            return redirect(url_for("main.index"))

        # invalid
        msg = "Invalid username or password"
        if request.is_json:
            return jsonify({"error": msg}), 401

        flash(msg, "error")

    return render_template("login.html")


@main.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        data = request.json if request.is_json else request.form
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not username or not email or not password:
            msg = "All fields are required."
            if request.is_json:
                return jsonify({"error": msg}), 400
            flash(msg, "error")
            return render_template("register.html")

        if len(password) < 6:
            msg = "Password must be at least 6 characters."
            if request.is_json:
                return jsonify({"error": msg}), 400
            flash(msg, "error")
            return render_template("register.html")

        if db.get_user_by_username(username):
            msg = "Username already exists."
            if request.is_json:
                return jsonify({"error": msg}), 400

            flash(msg, "error")
            return render_template("register.html")

        if db.get_user_by_email(email):
            msg = "Email already registered."
            if request.is_json:
                return jsonify({"error": msg}), 400
            flash(msg, "error")
            return render_template("register.html")

        try:
            password_hash = generate_password_hash(password)
            user_id = db.create_user(username, email, password_hash)

            db.log_activity(
                action="register",
                user_id=user_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent")
            )

            user = User(user_id, username, email, False, True)
            login_user(user, remember=True)

            if request.is_json:
                return jsonify({"success": True, "redirect": url_for("main.index")})

            flash("Account created successfully!", "success")
            return redirect(url_for("main.index"))

        except Exception as e:
            msg = f"Registration failed: {str(e)}"
            if request.is_json:
                return jsonify({"error": msg}), 500
            flash(msg, "error")
            return render_template("register.html")

    return render_template("register.html")


@main.route("/logout")
@login_required
def logout():
    db.log_activity(
        action="logout",
        user_id=current_user.id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent")
    )
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("main.login"))
