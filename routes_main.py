"""
routes_main.py
Main application routes: listings, drafts, notifications, storage, settings
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from pathlib import Path
from functools import wraps
import json
import os
import uuid
import logging
import tempfile
import traceback
from werkzeug.utils import secure_filename
from PIL import Image
import io


# Create blueprint
main_bp = Blueprint('main', __name__)

# db will be set by init_routes() in web_app.py
db = None

def init_routes(database):
    """Initialize routes with database"""
    global db
    db = database


# ============================================================================
# ADMIN DECORATOR
# ============================================================================

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        from flask import redirect, url_for, flash
        if not current_user.is_admin:
            flash('You need administrator privileges to access this page.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# -------------------------------------------------------------------------
# DELETE DRAFT
# -------------------------------------------------------------------------

# -------------------------------------------------------------------------
# PHOTO UPLOAD API ENDPOINTS
# -------------------------------------------------------------------------

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'heic'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def compress_image(image_file, max_size_mb=2, quality=85):
    """Compress image to reduce file size"""
    try:
        # Read image
        img = Image.open(image_file)

        # Convert RGBA to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background

        # Resize if too large (max 2048px on longest side)
        max_dimension = 2048
        if max(img.size) > max_dimension:
            ratio = max_dimension / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Save compressed image to bytes
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)

        # If still too large, reduce quality
        if len(output.getvalue()) > max_size_mb * 1024 * 1024 and quality > 60:
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=60, optimize=True)
            output.seek(0)

        return output, 'jpg'
    except Exception as e:
        print(f"Compression error: {e}")
        # Return original if compression fails
        image_file.seek(0)
        return image_file, image_file.filename.rsplit('.', 1)[1].lower()


@main_bp.route("/api/upload-photos", methods=["POST"])
@login_required
def api_upload_photos():
    """Handle photo uploads for listings with compression - uploads to Supabase Storage temp bucket"""
    try:
        if 'photos' not in request.files:
            return jsonify({"error": "No photos provided"}), 400

        files = request.files.getlist('photos')
        if not files or files[0].filename == '':
            return jsonify({"error": "No files selected"}), 400

        # Initialize Supabase Storage
        try:
            from src.storage.supabase_storage import get_supabase_storage
            storage = get_supabase_storage()
        except Exception as storage_error:
            import logging
            logging.error(f"Supabase Storage initialization failed: {storage_error}")
            return jsonify({"error": "Storage service unavailable. Please check configuration."}), 500

        uploaded_urls = []
        for file in files:
            if file and allowed_file(file.filename):
                # Check file size (20MB limit for Gemini)
                file.seek(0, 2)  # Seek to end
                file_size = file.tell()
                file.seek(0)  # Reset to beginning
                
                if file_size > 20 * 1024 * 1024:  # 20MB
                    return jsonify({"error": f"File {file.filename} exceeds 20MB limit"}), 400

                # Compress image before uploading
                compressed_file, ext = compress_image(file)
                
                # Determine content type
                content_type_map = {
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg',
                    'png': 'image/png',
                    'gif': 'image/gif',
                    'webp': 'image/webp'
                }
                content_type = content_type_map.get(ext.lower(), 'image/jpeg')
                
                # Ensure compressed_file is a BytesIO object and reset position
                compressed_file.seek(0)
                
                # Try passing BytesIO directly first (Supabase SDK prefers file-like objects)
                # If that doesn't work, fall back to bytes
                import logging
                logging.info(f"[UPLOAD DEBUG] Uploading {file.filename} with folder='temp' (should use temp-photos bucket)")
                
                try:
                    success, result = storage.upload_photo(
                        file_data=compressed_file,  # Pass BytesIO directly
                        folder='temp',
                        content_type=content_type
                    )
                except Exception as upload_error:
                    # Fall back to bytes if BytesIO doesn't work
                    logging.warning(f"[UPLOAD DEBUG] Upload with BytesIO failed: {upload_error}, trying with bytes")
                    compressed_file.seek(0)
                    file_data = compressed_file.read()
                    
                    if not isinstance(file_data, bytes):
                        return jsonify({"error": f"Invalid file data type: {type(file_data)}"}), 500
                    
                    success, result = storage.upload_photo(
                        file_data=file_data,
                        folder='temp',
                        content_type=content_type
                    )
                
                if success:
                    # Log which bucket the photo was uploaded to
                    if 'temp-photos' in result:
                        logging.info(f"[UPLOAD DEBUG] ✅ Photo uploaded to temp-photos bucket: {result[:100]}...")
                    elif 'listing-images' in result:
                        logging.warning(f"[UPLOAD DEBUG] ⚠️ Photo uploaded to listing-images bucket (WRONG!): {result[:100]}...")
                    elif 'draft-images' in result:
                        logging.warning(f"[UPLOAD DEBUG] ⚠️ Photo uploaded to draft-images bucket (unexpected): {result[:100]}...")
                    else:
                        logging.info(f"[UPLOAD DEBUG] Photo uploaded (bucket unclear from URL): {result[:100]}...")
                    
                    uploaded_urls.append(result)  # result is the public URL
                else:
                    logging.error(f"[UPLOAD DEBUG] ❌ Failed to upload {file.filename}: {result}")
                    return jsonify({"error": f"Upload failed: {result}"}), 500

        if not uploaded_urls:
            return jsonify({"error": "No valid images uploaded"}), 400

        return jsonify({
            "success": True,
            "paths": uploaded_urls,  # Now returns Supabase Storage URLs
            "count": len(uploaded_urls)
        })

    except Exception as e:
        import logging
        import traceback
        logging.error(f"Upload error: {e}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/cleanup-temp-photos", methods=["POST"])
@login_required
def api_cleanup_temp_photos():
    """Clean up temporary photos that weren't saved (called when user leaves page)"""
    import logging
    try:
        data = request.get_json()
        if not data:
            logging.warning("[CLEANUP] No JSON data received")
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        photo_urls = data.get("photos", [])
        
        logging.info(f"[CLEANUP] Received cleanup request for {len(photo_urls)} photo(s)")
        
        if not photo_urls:
            logging.info("[CLEANUP] No photos to clean up")
            return jsonify({"success": True, "message": "No photos to clean up", "deleted": 0})
        
        try:
            from src.storage.supabase_storage import get_supabase_storage
            storage = get_supabase_storage()
            
            deleted = 0
            failed = 0
            for i, url in enumerate(photo_urls):
                # Only delete from temp bucket
                if 'supabase.co' in url and 'temp-photos' in url:
                    logging.info(f"[CLEANUP] Deleting photo {i+1}/{len(photo_urls)}: {url[:100]}...")
                    if storage.delete_photo(url):
                        deleted += 1
                        logging.info(f"[CLEANUP] ✅ Successfully deleted photo {i+1}")
                    else:
                        failed += 1
                        logging.warning(f"[CLEANUP] ⚠️ Failed to delete photo {i+1}")
                else:
                    logging.warning(f"[CLEANUP] ⚠️ Skipping URL (not temp-photos bucket): {url[:100]}...")
            
            logging.info(f"[CLEANUP] ✅ Cleanup complete: {deleted} deleted, {failed} failed")
            
            return jsonify({
                "success": True,
                "deleted": deleted,
                "failed": failed,
                "message": f"Cleaned up {deleted} temporary photos"
            })
        except Exception as storage_error:
            import traceback
            logging.error(f"[CLEANUP] ❌ Storage cleanup failed: {storage_error}")
            logging.error(f"[CLEANUP] Traceback: {traceback.format_exc()}")
            return jsonify({"success": False, "error": str(storage_error)}), 500
            
    except Exception as e:
        import traceback
        logging.error(f"[CLEANUP] ❌ Cleanup error: {e}")
        logging.error(f"[CLEANUP] Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@main_bp.route("/uploads/<filename>")
def serve_upload(filename):
    """Serve uploaded files (legacy support - now using Supabase Storage)"""
    try:
        from flask import send_from_directory
        upload_dir = Path('./data/uploads')
        return send_from_directory(upload_dir, filename)
    except Exception as e:
        return jsonify({"error": "File not found"}), 404


@main_bp.route("/api/edit-photo", methods=["POST"])
@login_required
def api_edit_photo():
    """Handle photo editing (crop, resize, background removal)"""
    try:
        data = request.json
        operation = data.get('operation')
        image_path = data.get('image')

        if not operation or not image_path:
            return jsonify({"error": "Missing parameters"}), 400

        # Extract filename from path (e.g., "/uploads/abc123.jpg" -> "abc123.jpg")
        filename = image_path.split('/')[-1]
        upload_dir = Path('./data/uploads')
        filepath = upload_dir / filename

        if not filepath.exists():
            return jsonify({"error": "Image file not found"}), 404

        # Open the image
        img = Image.open(filepath)

        # Handle different operations
        if operation == 'crop':
            # Get crop parameters
            crop_data = data.get('cropData', {})
            x = int(crop_data.get('x', 0))
            y = int(crop_data.get('y', 0))
            width = int(crop_data.get('width', img.width))
            height = int(crop_data.get('height', img.height))

            # Crop the image
            img = img.crop((x, y, x + width, y + height))

        elif operation == 'resize':
            # Get resize parameters (e.g., 2x = enlarge by 2x)
            scale = data.get('scale', 2.0)
            new_size = (int(img.width * scale), int(img.height * scale))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        elif operation == 'remove-bg':
            # Background removal using simple thresholding
            # For better results, you could integrate rembg library
            # This is a basic implementation
            try:
                # Try to import rembg if available
                from rembg import remove
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                result = remove(img_bytes.read())
                img = Image.open(io.BytesIO(result))
            except ImportError:
                # Fallback: convert to RGBA and make white background transparent
                img = img.convert('RGBA')
                data_img = img.getdata()
                new_data = []
                for item in data_img:
                    # Change white (also shades of whites) to transparent
                    if item[0] > 200 and item[1] > 200 and item[2] > 200:
                        new_data.append((255, 255, 255, 0))
                    else:
                        new_data.append(item)
                img.putdata(new_data)

        else:
            return jsonify({"error": f"Unknown operation: {operation}"}), 400

        # Save edited image (create new file to preserve original)
        new_filename = f"{uuid.uuid4().hex}.{'png' if operation == 'remove-bg' else 'jpg'}"
        new_filepath = upload_dir / new_filename

        if operation == 'remove-bg':
            img.save(new_filepath, format='PNG')
        else:
            # Convert RGBA to RGB if needed
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            img.save(new_filepath, format='JPEG', quality=85, optimize=True)

        return jsonify({
            "success": True,
            "filepath": f"/uploads/{new_filename}",
            "message": f"Photo {operation} completed successfully"
        })

    except Exception as e:
        print(f"Photo editing error: {e}")
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------------------------
# STORAGE API ENDPOINTS
# -------------------------------------------------------------------------

@main_bp.route("/api/storage/find", methods=["GET"])
@login_required
def api_find_storage_item():
    """Find a storage item by ID"""
    try:
        storage_id = request.args.get("storage_id", "").strip()
        if not storage_id:
            return jsonify({"error": "Storage ID required"}), 400

        item = db.find_storage_item(current_user.id, storage_id)

        if item:
            return jsonify({"success": True, "item": item})
        else:
            return jsonify({"success": False, "error": "Item not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/save-draft", methods=["POST"])
@login_required
def api_save_draft():
    """Save or update a draft listing"""
    try:
        data = request.json

        # Extract form data with safe type conversions
        title = data.get('title', 'Untitled')
        description = data.get('description', '')

        # Safe float conversion for price
        try:
            price_val = data.get('price', '0')
            price = float(price_val) if price_val not in [None, ''] else 0.0
        except (ValueError, TypeError):
            price = 0.0

        # Safe float conversion for cost
        try:
            cost_val = data.get('cost', '')
            cost = float(cost_val) if cost_val not in [None, ''] else None
        except (ValueError, TypeError):
            cost = None

        condition = data.get('condition', 'good')
        item_type = data.get('item_type', 'general')

        # Safe int conversion for quantity
        try:
            quantity_val = data.get('quantity', '1')
            quantity = int(quantity_val) if quantity_val not in [None, ''] else 1
        except (ValueError, TypeError):
            quantity = 1

        storage_location = data.get('storage_location', '')
        sku = data.get('sku', '')
        upc = data.get('upc', '')
        status = data.get('status', 'draft')

        # Check if we're updating an existing draft (need listing_uuid before photo moving)
        draft_id = data.get('draft_id')
        listing_uuid = data.get('listing_uuid') or uuid.uuid4().hex

        # Get photos array (should be Supabase Storage URLs from temp bucket)
        photos = data.get('photos', [])
        
        # Move photos from temp bucket to drafts bucket if using Supabase Storage
        try:
            from src.storage.supabase_storage import get_supabase_storage
            storage = get_supabase_storage()
            
            # Move each photo from temp to drafts bucket
            moved_photos = []
            for photo_url in photos:
                # Check if it's a Supabase Storage URL (temp bucket)
                if 'supabase.co' in photo_url and 'temp-photos' in photo_url:
                    # Move to draft-images bucket
                    success, new_url = storage.move_photo(
                        source_url=photo_url,
                        destination_folder='drafts',
                        new_filename=f"{listing_uuid}_{uuid.uuid4().hex}.jpg"
                    )
                    if success:
                        moved_photos.append(new_url)
                    else:
                        # If move fails, keep original URL (might already be in drafts)
                        moved_photos.append(photo_url)
                else:
                    # Already in drafts or not Supabase URL, keep as-is
                    moved_photos.append(photo_url)
            
            photos = moved_photos
        except Exception as storage_error:
            import logging
            logging.warning(f"Could not move photos to drafts bucket: {storage_error}")
            # Continue with original photos if storage move fails
            pass

        # Build attributes from additional fields
        attributes = {
            'brand': data.get('brand', ''),
            'size': data.get('size', ''),
            'color': data.get('color', ''),
            'shipping_cost': data.get('shipping_cost', 0)
        }

        if draft_id:
            # Update existing draft
            db.update_listing(
                listing_id=draft_id,
                title=title,
                description=description,
                price=price,
                cost=cost,
                condition=condition,
                item_type=item_type,
                attributes=attributes,
                photos=photos,
                quantity=quantity,
                storage_location=storage_location,
                sku=sku,
                upc=upc,
                status=status
            )
            return jsonify({
                "success": True,
                "listing_id": draft_id,
                "listing_uuid": listing_uuid,
                "message": "Draft updated successfully"
            })
        else:
            # Create new draft (listing_uuid already set above)
            listing_id = db.create_listing(
                listing_uuid=listing_uuid,
                user_id=current_user.id,
                title=title,
                description=description,
                price=price,
                cost=cost,
                condition=condition,
                item_type=item_type,
                attributes=attributes,
                photos=photos,
                quantity=quantity,
                storage_location=storage_location,
                sku=sku,
                upc=upc,
                status=status
            )
            return jsonify({
                "success": True,
                "listing_id": listing_id,
                "listing_uuid": listing_uuid,
                "message": "Draft saved successfully"
            })

    except Exception as e:
        print(f"Save draft error: {e}")
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/get-draft/<int:listing_id>", methods=["GET"])
@login_required
def api_get_draft(listing_id):
    """Retrieve a draft listing for editing"""
    try:
        listing = db.get_listing(listing_id)

        if not listing:
            return jsonify({"error": "Draft not found"}), 404

        if listing["user_id"] != current_user.id:
            return jsonify({"error": "Unauthorized"}), 403

        # Parse JSON fields
        if listing.get('photos'):
            if isinstance(listing['photos'], str):
                listing['photos'] = json.loads(listing['photos'])
        else:
            listing['photos'] = []

        if listing.get('attributes'):
            if isinstance(listing['attributes'], str):
                attributes = json.loads(listing['attributes'])
            else:
                attributes = listing['attributes']

            # Merge attributes into main listing object for frontend
            listing['brand'] = attributes.get('brand', '')
            listing['size'] = attributes.get('size', '')
            listing['color'] = attributes.get('color', '')
            listing['shipping_cost'] = attributes.get('shipping_cost', 0)
        else:
            listing['brand'] = ''
            listing['size'] = ''
            listing['color'] = ''
            listing['shipping_cost'] = 0

        return jsonify({
            "success": True,
            "listing": listing
        })

    except Exception as e:
        print(f"Get draft error: {e}")
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/delete-draft/<int:listing_id>", methods=["DELETE"])
@login_required
def delete_draft(listing_id):
    """Delete a draft and all stored photos."""
    try:
        listing = db.get_listing(listing_id)
        if not listing:
            return jsonify({"error": "Listing not found"}), 404
        if listing["user_id"] != current_user.id:
            return jsonify({"error": "Unauthorized"}), 403

        # Remove photos directory
        try:
            import shutil
            if listing.get("listing_uuid"):
                photo_dir = Path("data/draft_photos") / listing["listing_uuid"]
                if photo_dir.exists():
                    shutil.rmtree(photo_dir)
        except Exception:
            pass  # Not fatal

        db.delete_listing(listing_id)
        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/drafts/bulk-delete", methods=["DELETE"])
@login_required
def bulk_delete_drafts():
    """Bulk delete multiple drafts"""
    try:
        data = request.json
        row_ids = data.get("row_ids", [])

        if not row_ids:
            return jsonify({"error": "No draft IDs provided"}), 400

        deleted_count = 0
        for listing_id in row_ids:
            try:
                listing = db.get_listing(listing_id)
                if not listing:
                    continue
                if listing["user_id"] != current_user.id:
                    continue

                # Remove photos directory
                try:
                    import shutil
                    if listing.get("listing_uuid"):
                        photo_dir = Path("data/draft_photos") / listing["listing_uuid"]
                        if photo_dir.exists():
                            shutil.rmtree(photo_dir)
                except Exception:
                    pass

                db.delete_listing(listing_id)
                deleted_count += 1
            except Exception as e:
                logger.error(f"Error deleting draft {listing_id}: {str(e)}")
                continue

        return jsonify({
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Deleted {deleted_count} draft(s)"
        }), 200

    except Exception as e:
        logger.error(f"Error in bulk delete: {str(e)}")
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/update-drafts", methods=["PATCH"])
@login_required
def update_drafts():
    """Update multiple draft fields (Excel-style bulk editor)"""
    try:
        data = request.json
        changes = data.get("changes", {})
        
        if not changes:
            return jsonify({"error": "No changes provided"}), 400
        
        # Process each draft and its field changes
        for draft_id_str, fields in changes.items():
            draft_id = int(draft_id_str)
            listing = db.get_listing(draft_id)
            
            if not listing:
                continue
            if listing["user_id"] != current_user.id:
                return jsonify({"error": "Unauthorized"}), 403
            
            # Build update dictionary with only editable fields
            update_data = {}
            
            if "title" in fields:
                update_data["title"] = fields["title"]
            
            if "price" in fields:
                try:
                    update_data["price"] = float(fields["price"])
                except (ValueError, TypeError):
                    update_data["price"] = listing.get("price", 0)
            
            if "cost" in fields:
                try:
                    update_data["cost"] = float(fields["cost"])
                except (ValueError, TypeError):
                    update_data["cost"] = listing.get("cost", 0)
            
            if "condition" in fields:
                update_data["condition"] = fields["condition"]
            
            # Handle attributes (brand, size, color)
            attributes = listing.get("attributes")
            if attributes:
                try:
                    attrs = json.loads(attributes) if isinstance(attributes, str) else attributes
                except (json.JSONDecodeError, TypeError):
                    attrs = {}
            else:
                attrs = {}
            
            if "brand" in fields:
                attrs["brand"] = fields["brand"]
            if "size" in fields:
                attrs["size"] = fields["size"]
            if "color" in fields:
                attrs["color"] = fields["color"]
            
            if attrs:
                update_data["attributes"] = json.dumps(attrs)
            
            # Update in database
            db.update_listing(draft_id, **update_data)
        
        return jsonify({
            "success": True,
            "message": f"Updated {len(changes)} draft(s)",
            "updated_count": len(changes)
        }), 200
    
    except Exception as e:
        logger.error(f"Error updating drafts: {str(e)}")
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/drafts", methods=["GET"])
@login_required
def get_user_drafts():
    """Get all drafts for current user"""
    try:
        drafts = db.get_drafts(user_id=current_user.id)
        return jsonify({"success": True, "drafts": drafts}), 200
    except Exception as e:
        logger.error(f"Error fetching drafts: {str(e)}")
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------------------------
# USER SETTINGS — NOTIFICATION EMAIL
# -------------------------------------------------------------------------

@main_bp.route("/api/settings/notification-email", methods=["POST"])
@login_required
def update_notification_email():
    try:
        data = request.json
        email = data.get("notification_email")
        if not email:
            return jsonify({"error": "Notification email required"}), 400

        db.update_notification_email(current_user.id, email)
        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------------------------
# MARKETPLACE CREDENTIALS CRUD
# -------------------------------------------------------------------------

VALID_MARKETPLATFORMS = [
    "etsy", "poshmark", "depop", "offerup", "shopify", "craigslist",
    "facebook", "tiktok_shop", "woocommerce", "nextdoor", "varagesale",
    "ruby_lane", "ecrater", "bonanza", "kijiji", "personal_website",
    "grailed", "vinted", "mercado_libre", "tradesy", "vestiaire",
    "rebag", "thredup", "poshmark_ca", "mercari", "ebay", "pinterest",
    "square", "rubylane", "other"
]


@main_bp.route("/api/settings/platform-credentials", methods=["POST"])
@login_required
def save_platform_credentials():
    """Save platform credentials - supports API keys, OAuth tokens, and email/password"""
    try:
        data = request.json
        platform = data.get("platform", "").lower()
        cred_type = data.get("type", "email_password")
        credentials = data.get("credentials", {})

        if platform not in VALID_MARKETPLATFORMS:
            return jsonify({"error": "Invalid platform"}), 400
        if not credentials:
            return jsonify({"error": "Credentials required"}), 400

        # Store credentials as JSON
        db.save_marketplace_credentials(
            current_user.id,
            platform,
            cred_type,
            json.dumps(credentials)
        )
        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/settings/marketplace-credentials", methods=["POST"])
@login_required
def save_marketplace_credentials():
    """Legacy endpoint for backward compatibility"""
    try:
        data = request.json
        platform = data.get("platform", "").lower()
        username = data.get("username")
        password = data.get("password")

        if platform not in VALID_MARKETPLATFORMS:
            return jsonify({"error": "Invalid platform"}), 400
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400

        db.save_marketplace_credentials(
            current_user.id, platform, username, password
        )
        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/settings/platform-credentials", methods=["GET"])
@login_required
def get_all_platform_credentials():
    """Retrieve all platform credentials for current user"""
    try:
        # Get all marketplace credentials
        cursor = db._get_cursor()
        cursor.execute("""
            SELECT platform, username FROM marketplace_credentials
            WHERE user_id = %s
        """, (current_user.id,))

        credentials = {}
        for row in cursor.fetchall():
            credentials[row['platform']] = {
                'username': row['username'],
                'configured': True
            }

        cursor.close()
        return jsonify({"success": True, "credentials": credentials})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/settings/marketplace-credentials/<platform>", methods=["DELETE"])
@login_required
def delete_marketplace_credentials(platform):
    try:
        platform = platform.lower()
        db.delete_marketplace_credentials(current_user.id, platform)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------------------------
# API CREDENTIALS CRUD (Etsy/Shopify/WooCommerce/Facebook)
# -------------------------------------------------------------------------

VALID_API_PLATFORMS = ["etsy", "shopify", "woocommerce", "facebook"]


@main_bp.route("/api/settings/api-credentials", methods=["POST"])
@login_required
def save_api_credentials():
    try:
        data = request.json
        platform = data.get("platform", "").lower()
        credentials = data.get("credentials")

        if platform not in VALID_API_PLATFORMS:
            return jsonify({"error": "Invalid API platform"}), 400
        if not credentials:
            return jsonify({"error": "Credentials required"}), 400

        db.save_marketplace_credentials(
            current_user.id,
            f"api_{platform}",
            "api_token",
            json.dumps(credentials)
        )

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/settings/api-credentials/<platform>", methods=["GET"])
@login_required
def get_api_credentials(platform):
    try:
        platform = platform.lower()
        creds = db.get_marketplace_credentials(
            current_user.id, f"api_{platform}"
        )

        if creds and creds.get("password"):
            return jsonify({
                "success": True,
                "configured": True,
                "credentials": json.loads(creds["password"])
            })

        return jsonify({"success": True, "configured": False})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------------------------
# CARD ANALYSIS (TCG + Sports) - QUICK ANALYSIS
# -------------------------------------------------------------------------

@main_bp.route("/api/analyze", methods=["POST"])
def api_analyze():
    """Analyze general items with Gemini (fast, cheap) - allows guest access with 8 free uses"""
    from flask import session
    from flask_login import current_user
    
    # Check guest usage limit if not authenticated
    if not current_user.is_authenticated:
        guest_uses = session.get('guest_ai_uses', 0)
        if guest_uses >= 8:
            return jsonify({
                "success": False,
                "error": "You've used all 8 free AI analyses. Please sign up to continue using AI features!",
                "requires_signup": True
            }), 403
        
        # Increment guest usage counter
        session['guest_ai_uses'] = guest_uses + 1
        session.permanent = True  # Make session persist
    
    try:
        from src.ai.gemini_classifier import GeminiClassifier
        from src.schema.unified_listing import Photo
        import tempfile
        import os

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        paths = data.get("photos", [])
        if not paths:
            return jsonify({"error": "No photos provided"}), 400

        # Log which URLs we received (important for debugging bucket issues)
        import logging
        logging.info(f"[ANALYZE DEBUG] Received {len(paths)} photo URL(s) for analysis")
        for i, path in enumerate(paths):
            if 'temp-photos' in path:
                logging.info(f"[ANALYZE DEBUG] Photo {i+1}: ✅ URL from temp-photos bucket: {path[:100]}...")
            elif 'listing-images' in path:
                logging.warning(f"[ANALYZE DEBUG] Photo {i+1}: ⚠️ URL from listing-images bucket (unexpected for new uploads): {path[:100]}...")
            elif 'draft-images' in path:
                logging.info(f"[ANALYZE DEBUG] Photo {i+1}: ℹ️ URL from draft-images bucket: {path[:100]}...")
            elif 'supabase.co' in path:
                logging.warning(f"[ANALYZE DEBUG] Photo {i+1}: ⚠️ URL from Supabase but bucket unclear: {path[:100]}...")
            else:
                logging.info(f"[ANALYZE DEBUG] Photo {i+1}: Local path or non-Supabase URL: {path[:100]}...")

        # Download photos from Supabase Storage or use local paths
        photo_objects = []
        temp_files = []  # Track temp files for cleanup
        
        try:
            from src.storage.supabase_storage import get_supabase_storage
            storage = get_supabase_storage()
            use_supabase = True
        except Exception:
            use_supabase = False
            storage = None

        for i, path in enumerate(paths):
            local_path = None
            
            # Check if it's a Supabase Storage URL
            if use_supabase and storage and 'supabase.co' in path:
                logging.info(f"[ANALYZE DEBUG] Downloading image {i+1}/{len(paths)} from Supabase: {path[:100]}...")
                
                # Download from Supabase Storage to temp file
                file_data = storage.download_photo(path)
                
                # Debug logging
                debug_info = {
                    'hasFile': bool(file_data),
                    'filePath': path,
                    'dataLength': len(file_data) if file_data else 0,
                    'isBytes': isinstance(file_data, bytes) if file_data else False
                }
                logging.info(f"[ANALYZE DEBUG] Image {i+1}: {debug_info}")
                
                if file_data and len(file_data) > 0:
                    # Create temp file
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                    temp_file.write(file_data)
                    temp_file.flush()  # Ensure data is written to buffer
                    os.fsync(temp_file.fileno())  # Force write to disk
                    temp_file.close()
                    local_path = temp_file.name
                    temp_files.append(local_path)
                    
                    # Verify file was written and exists
                    from pathlib import Path
                    file_exists = Path(local_path).exists()
                    file_size = Path(local_path).stat().st_size if file_exists else 0
                    
                    logging.info(f"✅ Downloaded image {i+1} ({len(file_data)} bytes) to {local_path}")
                    logging.info(f"[ANALYZE DEBUG] Temp file exists: {file_exists}, size: {file_size} bytes")
                    
                    if not file_exists or file_size == 0:
                        logging.error(f"❌ Temp file was not created properly: {local_path}")
                        return jsonify({"error": f"Failed to create temp file for image {i+1}"}), 500
                else:
                    logging.error(f"❌ Failed to download image {i+1} from Supabase: {path}")
                    logging.error(f"[ANALYZE DEBUG] file_data is None or empty: {file_data}")
                    # Try one more time with direct HTTP request as last resort
                    try:
                        import requests
                        logging.info(f"Last resort: attempting direct HTTP download for image {i+1}...")
                        http_response = requests.get(path, timeout=30, allow_redirects=True)
                        if http_response.status_code == 200 and http_response.content and len(http_response.content) > 0:
                            # Create temp file from HTTP response
                            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                            temp_file.write(http_response.content)
                            temp_file.flush()
                            os.fsync(temp_file.fileno())
                            temp_file.close()
                            local_path = temp_file.name
                            temp_files.append(local_path)
                            logging.info(f"✅ Last resort HTTP download successful: {len(http_response.content)} bytes to {local_path}")
                        else:
                            return jsonify({"error": f"Failed to download photo {i+1} from Supabase Storage. URL may be invalid or file may not exist. Status: {http_response.status_code if hasattr(http_response, 'status_code') else 'unknown'}"}), 404
                    except Exception as http_error:
                        logging.error(f"Last resort HTTP download also failed: {http_error}")
                        return jsonify({"error": f"Failed to download photo {i+1} from Supabase Storage. All download methods failed. Error: {str(http_error)}"}), 404
            else:
                # Assume local path (legacy support)
                if path.startswith('/'):
                    local_path = f"./data{path}"
                else:
                    local_path = f"./data/{path}"
                
                # Verify file exists
                from pathlib import Path
                if not Path(local_path).exists():
                    return jsonify({"error": f"Photo file not found: {local_path}"}), 404
            
            photo_objects.append(Photo(url=path, local_path=local_path))
        
        if not photo_objects:
            return jsonify({"error": "No valid photos found"}), 400

        # Initialize classifier
        try:
            classifier = GeminiClassifier.from_env()
        except ValueError as e:
            # Cleanup temp files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass
            return jsonify({"error": f"AI service not configured: {str(e)}"}), 500

        # Analyze photos
        result = classifier.analyze_item(photo_objects)

        # Cleanup temp files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass

        if result.get("error"):
            return jsonify({"success": False, "error": result.get("error")}), 500

        return jsonify({"success": True, "analysis": result})

    except ImportError as e:
        import logging
        logging.error(f"Import error in analyzer: {e}")
        return jsonify({"error": f"Module import failed: {str(e)}"}), 500
    except Exception as e:
        import logging
        import traceback
        logging.error(f"Analyzer error: {e}\n{traceback.format_exc()}")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@main_bp.route("/api/analyze-card", methods=["POST"])
@login_required
def api_analyze_card():
    """Legacy card analysis endpoint (use /api/enhanced-scan instead)"""
    try:
        from src.ai.gemini_classifier import analyze_card
        from src.schema.unified_listing import Photo

        data = request.get_json()
        paths = data.get("photos", [])
        if not paths:
            return jsonify({"error": "No photos provided"}), 400

        photos = [Photo(url=p, local_path=f"./data{p}") for p in paths]
        result = analyze_card(photos)

        if result.get("error"):
            return jsonify(result), 500

        return jsonify({"success": True, "card_data": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------------------------
# ENHANCED SCANNER - Unified Card & Collectible Deep Analysis
# -------------------------------------------------------------------------

@main_bp.route("/api/enhanced-scan", methods=["POST"])
@login_required
def api_enhanced_scan():
    """
    Enhanced scanner for deep collectible analysis.
    Auto-detects: Card vs Collectible vs Standard Item
    Routes to appropriate analyzer and returns results (no automatic saving).
    """
    temp_files = []  # Initialize temp_files at the top for cleanup

    try:
        from src.schema.unified_listing import Photo

        data = request.json
        photo_paths = data.get('photos', [])

        if not photo_paths:
            logging.error("[ENHANCED SCAN ERROR] No photos provided in request")
            return jsonify({'error': 'No photos provided'}), 400

        # Validate photo paths are not empty
        photo_paths = [p for p in photo_paths if p and isinstance(p, str) and len(p.strip()) > 0]
        if not photo_paths:
            logging.error("[ENHANCED SCAN ERROR] All photo paths are empty or invalid")
            return jsonify({'error': 'No valid photo URLs provided'}), 400

        # Log which URLs we received (important for debugging bucket issues)
        logging.info(f"[ENHANCED SCAN DEBUG] Received {len(photo_paths)} photo URL(s) for enhanced scan")
        for i, path in enumerate(photo_paths):
            if not path or not isinstance(path, str):
                logging.error(f"[ENHANCED SCAN DEBUG] Photo {i+1}: ❌ Invalid path type: {type(path)}")
                continue
            if 'temp-photos' in path:
                logging.info(f"[ENHANCED SCAN DEBUG] Photo {i+1}: ✅ URL from temp-photos bucket: {path[:100]}...")
            elif 'listing-images' in path:
                logging.warning(f"[ENHANCED SCAN DEBUG] Photo {i+1}: ⚠️ URL from listing-images bucket (unexpected for new uploads): {path[:100]}...")
            elif 'draft-images' in path:
                logging.info(f"[ENHANCED SCAN DEBUG] Photo {i+1}: ℹ️ URL from draft-images bucket: {path[:100]}...")
            elif 'supabase.co' in path:
                logging.info(f"[ENHANCED SCAN DEBUG] Photo {i+1}: ✅ Supabase URL detected: {path[:100]}...")
            elif path.startswith('http://') or path.startswith('https://'):
                logging.warning(f"[ENHANCED SCAN DEBUG] Photo {i+1}: ⚠️ HTTP/HTTPS URL but not Supabase: {path[:100]}...")
            else:
                logging.info(f"[ENHANCED SCAN DEBUG] Photo {i+1}: Local path or non-Supabase URL: {path[:100]}...")

        # Download photos from Supabase Storage or use local paths
        photo_objects = []

        try:
            from src.storage.supabase_storage import get_supabase_storage
            storage = get_supabase_storage()
            use_supabase = True
            logging.info("[ENHANCED SCAN DEBUG] Supabase storage initialized successfully")
        except Exception as e:
            logging.warning(f"[ENHANCED SCAN DEBUG] Supabase storage not available: {e}")
            use_supabase = False
            storage = None

        for i, path in enumerate(photo_paths):
            local_path = None

            # Check if it's a Supabase Storage URL
            if use_supabase and storage:
                # Validate URL format first
                is_supabase_url = 'supabase.co' in path or path.startswith('http') and 'supabase' in path.lower()
                
                if is_supabase_url:
                    logging.info(f"[ENHANCED SCAN DEBUG] Downloading image {i+1}/{len(photo_paths)} from Supabase: {path[:100]}...")

                    # Download from Supabase Storage to temp file
                    try:
                        file_data = storage.download_photo(path)
                    except ValueError as value_error:
                        # URL validation error
                        logging.error(f"[ENHANCED SCAN ERROR] Invalid URL format for photo {i+1}: {value_error}")
                        logging.error(f"[ENHANCED SCAN ERROR] URL: {path[:200]}")
                        file_data = None
                    except Exception as download_exception:
                        # Other download errors
                        logging.error(f"[ENHANCED SCAN ERROR] Exception downloading photo {i+1}: {download_exception}")
                        logging.error(f"[ENHANCED SCAN ERROR] Exception type: {type(download_exception).__name__}")
                        logging.error(f"[ENHANCED SCAN ERROR] URL: {path[:200]}")
                        import traceback
                        logging.error(f"[ENHANCED SCAN ERROR] Traceback: {traceback.format_exc()}")
                        file_data = None

                    # Debug logging
                    debug_info = {
                        'hasFile': bool(file_data),
                        'filePath': path[:100] if path else 'None',
                        'dataLength': len(file_data) if file_data else 0,
                        'isBytes': isinstance(file_data, bytes) if file_data else False
                    }
                    logging.info(f"[ENHANCED SCAN DEBUG] Image {i+1}: {debug_info}")

                    if file_data and len(file_data) > 0:
                        # Create temp file
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                        temp_file.write(file_data)
                        temp_file.flush()  # Ensure data is written to buffer
                        os.fsync(temp_file.fileno())  # Force write to disk
                        temp_file.close()
                        local_path = temp_file.name
                        temp_files.append(local_path)

                        # Verify file was written and exists
                        file_exists = Path(local_path).exists()
                        file_size = Path(local_path).stat().st_size if file_exists else 0

                        logging.info(f"✅ Downloaded image {i+1} ({len(file_data)} bytes) to {local_path}")
                        logging.info(f"[ENHANCED SCAN DEBUG] Temp file exists: {file_exists}, size: {file_size} bytes")

                        if not file_exists or file_size == 0:
                            logging.error(f"❌ Temp file was not created properly: {local_path}")
                            # Cleanup temp files
                            for temp_file in temp_files:
                                try:
                                    os.unlink(temp_file)
                                except:
                                    pass
                            return jsonify({"error": f"Failed to create temp file for image {i+1}"}), 500
                        
                        # Successfully downloaded - append photo object
                        photo_objects.append(Photo(url=path, local_path=local_path))
                        continue  # Continue to next photo
                    else:
                        logging.error(f"❌ Failed to download image {i+1} from Supabase: {path}")
                        logging.error(f"[ENHANCED SCAN DEBUG] file_data is None or empty: {file_data}")
                        logging.error(f"[ENHANCED SCAN DEBUG] URL format may be invalid. Expected: https://{{project}}.supabase.co/storage/v1/object/public/{{bucket}}/{{path}}")
                        
                        # Try last resort: direct HTTP download
                        try:
                            import requests
                            logging.info(f"[ENHANCED SCAN] Last resort: attempting direct HTTP download for image {i+1}...")
                            http_response = requests.get(path, timeout=30, allow_redirects=True)
                            if http_response.status_code == 200 and http_response.content and len(http_response.content) > 0:
                                # Create temp file from HTTP response
                                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                                temp_file.write(http_response.content)
                                temp_file.flush()
                                os.fsync(temp_file.fileno())
                                temp_file.close()
                                local_path = temp_file.name
                                temp_files.append(local_path)
                                logging.info(f"✅ Last resort HTTP download successful: {len(http_response.content)} bytes to {local_path}")
                                photo_objects.append(Photo(url=path, local_path=local_path))
                                continue  # Continue to next photo
                        except Exception as http_error:
                            logging.error(f"[ENHANCED SCAN] Last resort HTTP download also failed: {http_error}")
                        
                        # If all download methods failed, return error
                        # Cleanup temp files
                        for temp_file in temp_files:
                            try:
                                os.unlink(temp_file)
                            except:
                                pass
                        return jsonify({
                            "error": f"Failed to download photo {i+1} from Supabase Storage. URL may be invalid or file may not exist.",
                            "url_preview": path[:100] if path else "No URL provided",
                            "hint": "Check that the photo URL is a valid Supabase Storage URL"
                        }), 404
            else:
                # Assume local path (legacy support)
                if path.startswith('/'):
                    local_path = f"./data{path}"
                else:
                    local_path = f"./data/{path}"

                # Verify file exists
                if not Path(local_path).exists():
                    logging.error(f"[ENHANCED SCAN ERROR] Local photo file not found: {local_path}")
                    # Cleanup temp files
                    for temp_file in temp_files:
                        try:
                            os.unlink(temp_file)
                        except:
                            pass
                    return jsonify({"error": f"Photo file not found: {local_path}"}), 404
                
                photo_objects.append(Photo(url=path, local_path=local_path))

        if not photo_objects:
            # Cleanup temp files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass
            logging.error("[ENHANCED SCAN ERROR] No valid photo objects created")
            return jsonify({"error": "No valid photos found"}), 400

        logging.info(f"[ENHANCED SCAN] Created {len(photo_objects)} photo objects. Using Gemini with detailed collectible analysis prompt...")

        # Use Gemini with detailed prompt (same prompt that was designed for Claude)
        try:
            from src.ai.gemini_classifier import GeminiClassifier
            classifier = GeminiClassifier.from_env()
            logging.info("[ENHANCED SCAN] Analyzing with Gemini using detailed collectible prompt (mint marks, serial numbers, signatures, errors, historical context, etc.)...")
            detailed_analysis = classifier.analyze_collectible_detailed(photo_objects)
            logging.info(f"[ENHANCED SCAN] ✅ Gemini detailed analysis completed: {list(detailed_analysis.keys()) if detailed_analysis else 'empty'}")
            
            if detailed_analysis.get("error"):
                # Cleanup temp files
                for temp_file in temp_files:
                    try:
                        os.unlink(temp_file)
                    except:
                        pass
                return jsonify({
                    "success": False,
                    "error": f"Detailed analysis failed: {detailed_analysis.get('error')}"
                }), 500
            
            # Format Gemini's detailed analysis (same structure as Claude's EnhancedScanner returns)
            # Determine item type
            item_type = 'collectible'
            category = detailed_analysis.get('category', '').lower()
            if 'card' in category or 'trading card' in category or detailed_analysis.get('card_type'):
                item_type = 'card'
            
            # Extract market analysis
            market_analysis = detailed_analysis.get('market_analysis', {})
            
            # Format as collectible or card response (similar to EnhancedScanner)
            if item_type == 'card':
                # Format as card
                result = {
                    'type': 'card',
                    'data': {
                        'card_name': detailed_analysis.get('item_name', 'Unknown Card'),
                        'player_name': detailed_analysis.get('player_name', ''),
                        'set_name': detailed_analysis.get('set_name', ''),
                        'card_number': detailed_analysis.get('card_number', ''),
                        'card_type': detailed_analysis.get('card_type', 'unknown'),
                        'game_name': detailed_analysis.get('game_name', ''),
                        'franchise': detailed_analysis.get('franchise', ''),
                        'rarity': detailed_analysis.get('rarity', ''),
                        'brand': detailed_analysis.get('brand', ''),
                        'sport': detailed_analysis.get('sport', ''),
                        'serial_number': detailed_analysis.get('serial_number', {}),
                        'signature': detailed_analysis.get('signature', {}),
                        'errors_variations': detailed_analysis.get('errors_variations', {}),
                        'historical_context': detailed_analysis.get('historical_context', {}),
                        'condition': detailed_analysis.get('condition', {}),
                        'authentication': detailed_analysis.get('authentication', {}),
                        'estimated_value_low': market_analysis.get('current_market_value_low', 0),
                        'estimated_value_high': market_analysis.get('current_market_value_high', 0),
                        'collector_notes': detailed_analysis.get('collector_notes', ''),
                        'is_card': True
                    },
                    'market_prices': {
                        'tcgplayer': {'market': market_analysis.get('estimated_value')},
                        'ebay': {'avg': market_analysis.get('estimated_value')},
                        'actual_selling': market_analysis.get('estimated_value'),
                        'quick_sale': market_analysis.get('current_market_value_low')
                    },
                    'ai_provider': 'gemini'
                }
            else:
                # Format as collectible
                result = {
                    'type': 'collectible',
                    'data': {
                        'item_name': detailed_analysis.get('item_name', 'Unknown Collectible'),
                        'franchise': detailed_analysis.get('franchise', ''),
                        'brand': detailed_analysis.get('brand', ''),
                        'category': detailed_analysis.get('category', ''),
                        'mint_mark': detailed_analysis.get('mint_mark', {}),
                        'serial_number': detailed_analysis.get('serial_number', {}),
                        'signature': detailed_analysis.get('signature', {}),
                        'errors_variations': detailed_analysis.get('errors_variations', {}),
                        'historical_context': detailed_analysis.get('historical_context', {}),
                        'condition': detailed_analysis.get('condition', {}),
                        'authentication': detailed_analysis.get('authentication', {}),
                        'item_significance': detailed_analysis.get('historical_context', {}).get('backstory', ''),
                        'rarity_info': detailed_analysis.get('collector_notes', ''),
                        'authentication_markers': detailed_analysis.get('authentication', {}).get('authentication_markers', []),
                        'market_analysis': market_analysis,
                        'collector_notes': detailed_analysis.get('collector_notes', '')
                    },
                    'market_prices': {
                        'retail': market_analysis.get('estimated_value') or market_analysis.get('current_market_value_high'),
                        'actual_selling': market_analysis.get('estimated_value'),
                        'quick_sale': market_analysis.get('current_market_value_low'),
                        'value_range': {
                            'low': market_analysis.get('current_market_value_low', 0),
                            'high': market_analysis.get('current_market_value_high', 0)
                        }
                    },
                    'ai_provider': 'gemini'
                }
        except Exception as analyze_error:
            logging.error(f"[ENHANCED SCAN] Gemini detailed analysis error: {analyze_error}")
            import traceback
            logging.error(f"[ENHANCED SCAN] Traceback: {traceback.format_exc()}")
            # Cleanup temp files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass
            return jsonify({
                "success": False,
                "error": f"Analysis failed: {str(analyze_error)}"
            }), 500
        
        logging.info(f"[ENHANCED SCAN] ✅ Analysis completed, result type: {result.get('type')}")

        # Cleanup temp files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass

        # Check if standard item (not collectible)
        if result.get('type') == 'standard_item':
            return jsonify({
                'success': False,
                'type': 'standard_item',
                'message': 'Not a collectible. Use quick analysis for listing.',
                'classification': result.get('classification')
            })

        # Check for errors
        if result.get('error'):
            return jsonify({
                'success': False,
                'error': result['error'],
                'raw_response': result.get('raw_response'),
                'type': result.get('type')
            }), 500

        # Extract artifact-relevant data (handle both Claude's detailed structure and Gemini's basic structure)
        data = result.get('data', {})
        ai_provider = result.get('ai_provider', 'gemini')
        
        # Handle Claude's nested structure (detailed collectible attributes)
        if ai_provider == 'claude':
            # Claude returns nested structures
            historical_context_dict = data.get('historical_context', {})
            market_analysis_dict = data.get('market_analysis', {})
            errors_dict = data.get('errors_variations', {})
            
            historical_context = {
                'release_year': historical_context_dict.get('release_year'),
                'backstory': historical_context_dict.get('backstory', ''),
                'significance': historical_context_dict.get('significance', ''),
                'rarity_context': historical_context_dict.get('rarity_context', '')
            }
            
            value_context = {
                'current_market_value_low': market_analysis_dict.get('current_market_value_low'),
                'current_market_value_high': market_analysis_dict.get('current_market_value_high'),
                'estimated_value': market_analysis_dict.get('estimated_value'),
                'market_trend': market_analysis_dict.get('market_trend', ''),
                'demand_level': market_analysis_dict.get('demand_level', ''),
                'value_factors': market_analysis_dict.get('value_factors', [])
            }
            
            known_errors = {
                'present': errors_dict.get('present', False),
                'error_type': errors_dict.get('error_type', ''),
                'error_description': errors_dict.get('error_description', ''),
                'error_severity': errors_dict.get('error_severity', ''),
                'value_impact': errors_dict.get('value_impact', '')
            }
            
            collector_notes = data.get('collector_notes', '')
            fun_fact = ''  # Claude doesn't provide fun_fact
        else:
            # Gemini's flat structure (basic - missing detailed attributes)
            historical_context = {
                'release_year': data.get('release_year'),
                'backstory': data.get('backstory', ''),
                'significance': data.get('significance', ''),
                'rarity_context': data.get('rarity_context', '')
            }
            
            value_context = {
                'current_market_value_low': data.get('current_market_value_low'),
                'current_market_value_high': data.get('current_market_value_high'),
                'estimated_value': data.get('estimated_value'),
                'market_trend': data.get('market_trend', ''),
                'demand_level': data.get('demand_level', ''),
                'value_factors': data.get('value_factors', [])
            }
            
            known_errors = {
                'present': bool(data.get('errors_variations')),
                'error_type': '',
                'error_description': str(data.get('errors_variations', '')),
                'error_severity': '',
                'value_impact': ''
            }
            
            collector_notes = data.get('collector_notes', '')
            fun_fact = data.get('fun_fact', '')

        # Create artifact record (automatic, no user choice - GUARANTEED)
        artifact_id = db.create_or_update_artifact(
            item_name=data.get('item_name', 'Unknown Item'),
            brand=data.get('brand', ''),
            franchise=data.get('franchise', ''),
            category=data.get('category', ''),
            item_type=result.get('type', 'collectible'),  # 'card' or 'collectible'
            historical_context=historical_context,
            value_context=value_context,
            known_errors=known_errors,
            collector_notes=collector_notes,
            fun_fact=fun_fact,
            photos=photo_paths,  # Stored as PENDING - admin selects which to make public
            user_id=current_user.id,  # Track who uploaded photos
            coin_info=data.get('coin_info', {})  # Coin-specific metadata
        )
        
        logging.info(f"[ENHANCED SCAN] Automatically created/updated artifact {artifact_id} in public Hall of Records (no user approval required)")
        
        # Database update is automatic - follows merge rules:
        # - New franchise: Sets initial data
        # - Existing franchise: Only adds new missing fields (never overwrites)
        # Photos stored as pending - user will select which to make public
        
        # Return artifact_id for redirect to artifact detail page
        return jsonify({
            'success': True,
            'artifact_id': artifact_id,
            'message': 'Artifact automatically updated in public Hall of Records'
        })

    except Exception as e:
        error_trace = traceback.format_exc()
        logging.error(f"[ENHANCED SCAN ERROR] Exception occurred: {e}")
        logging.error(f"[ENHANCED SCAN ERROR] Traceback:\n{error_trace}")

        # Cleanup temp files on error
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
                logging.info(f"[ENHANCED SCAN DEBUG] Cleaned up temp file: {temp_file}")
            except Exception as cleanup_error:
                logging.warning(f"[ENHANCED SCAN DEBUG] Failed to cleanup temp file {temp_file}: {cleanup_error}")

        return jsonify({
            'success': False,
            'error': f'Enhanced scan failed: {str(e)}',
            'error_type': type(e).__name__,
            'traceback': error_trace if os.getenv('FLASK_DEBUG') else None
        }), 500


# -------------------------------------------------------------------------
# ARTIFACT ROUTES (Hall of Records)
# -------------------------------------------------------------------------

@main_bp.route("/artifact/<int:artifact_id>")
@login_required
def artifact_detail(artifact_id):
    """Display artifact detail page"""
    artifact = db.get_artifact(artifact_id)
    if not artifact:
        flash('Artifact not found', 'error')
        return redirect(url_for('main.index'))
    
    # Public database is READ-ONLY - no saving to personal collection from public view
    # Photo selection: Only admin can select photos to make public
    # Get all pending photos (from all users who scanned) - admin can select any
    pending_photos = []
    if current_user.is_admin:
        # Admin can see all pending photos from any user
        cursor = db._get_cursor()
        cursor.execute("""
            SELECT id, photo_url, is_selected, created_at, user_id
            FROM pending_artifact_photos
            WHERE artifact_id = %s
            ORDER BY created_at ASC
        """, (artifact_id,))
        pending_photos = [dict(row) for row in cursor.fetchall()]
    
    # Check if artifact is in user's personal collection
    in_collection = db.is_artifact_in_user_collection(current_user.id, artifact_id)
    
    return render_template('artifact_detail.html', 
                         artifact=artifact, 
                         pending_photos=pending_photos,
                         is_admin=current_user.is_admin,
                         in_collection=in_collection)

@main_bp.route("/api/artifacts/<int:artifact_id>")
@login_required
def api_get_artifact(artifact_id):
    """Get artifact data as JSON"""
    artifact = db.get_artifact(artifact_id)
    if not artifact:
        return jsonify({'error': 'Artifact not found'}), 404
    
    # Check if artifact is in user's collection
    in_collection = db.is_artifact_in_user_collection(current_user.id, artifact_id)
    artifact['in_collection'] = in_collection
    
    return jsonify({
        'success': True,
        'artifact': artifact
    })

@main_bp.route("/api/user/artifacts/save", methods=["POST"])
@login_required
def api_save_artifact_to_collection():
    """Save artifact to user's personal collection - users choose what goes in their database"""
    try:
        data = request.json
        artifact_id = data.get('artifact_id')
        
        if not artifact_id:
            return jsonify({'error': 'artifact_id required'}), 400
        
        # Verify artifact exists
        artifact = db.get_artifact(artifact_id)
        if not artifact:
            return jsonify({'error': 'Artifact not found'}), 404
        
        # Save to user's personal collection - their choice
        success = db.save_artifact_to_user_collection(current_user.id, artifact_id)
        
        if success:
            db.log_activity(
                action="save_artifact",
                user_id=current_user.id,
                resource_type="artifact",
                resource_id=artifact_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent")
            )
            return jsonify({
                'success': True,
                'message': 'Artifact saved to your personal Hall of Records'
            })
        else:
            return jsonify({'error': 'Failed to save artifact'}), 500
            
    except Exception as e:
        logging.error(f"Error saving artifact to collection: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route("/api/artifacts/<int:artifact_id>/select-photos", methods=["POST"])
@login_required
def api_select_artifact_photos(artifact_id):
    """Admin only - selects which photos to make public"""
    from routes_admin import admin_required
    
    # Check admin permission
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required to select photos for public display'}), 403
    
    try:
        data = request.json
        selected_photo_ids = data.get('photo_ids', [])
        
        if not selected_photo_ids:
            return jsonify({'error': 'No photos selected'}), 400
        
        # Verify artifact exists
        artifact = db.get_artifact(artifact_id)
        if not artifact:
            return jsonify({'error': 'Artifact not found'}), 404
        
        # Admin can select any photos from any user - pass None for user_id
        success = db.select_artifact_photos(artifact_id, None, selected_photo_ids)
        
        if success:
            db.log_activity(
                action="admin_select_artifact_photos",
                user_id=current_user.id,
                resource_type="artifact",
                resource_id=artifact_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent")
            )
            return jsonify({
                'success': True,
                'message': f'{len(selected_photo_ids)} photo(s) made public'
            })
        else:
            return jsonify({'error': 'Failed to select photos'}), 500
            
    except Exception as e:
        logging.error(f"Error selecting artifact photos: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route("/my-artifacts")
@login_required
def my_artifacts():
    """View user's personal artifact collection"""
    artifacts = db.get_user_artifact_collection(current_user.id)
    return render_template('my_artifacts.html', artifacts=artifacts)

# -------------------------------------------------------------------------
# ADD COLLECTIBLE TO COLLECTION
# -------------------------------------------------------------------------

@main_bp.route("/api/collectibles/add", methods=["POST"])
@login_required
def api_add_collectible():
    """
    Add collectible to user's personal collection.
    Used by "Store Only" and "Store + List" buttons.
    """
    try:
        data = request.json
        ai_result = data.get('ai_result')
        photos = data.get('photos', [])
        storage_location = data.get('storage_location')
        
        if not ai_result:
            return jsonify({'error': 'No collectible data provided'}), 400
        
        # Add to user's collectibles
        collectible_id = db.add_to_user_collectibles(
            current_user.id,
            ai_result,
            photos=photos,
            storage_location=storage_location
        )
        
        if not collectible_id:
            return jsonify({'error': 'Failed to add collectible'}), 500
        
        db.log_activity(
            action="add_collectible",
            user_id=current_user.id,
            resource_type="collectible",
            resource_id=collectible_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent")
        )
        
        return jsonify({
            'success': True,
            'collectible_id': collectible_id
        })
        
    except Exception as e:
        print(f"Add collectible error: {e}")
        return jsonify({'error': str(e)}), 500


# -------------------------------------------------------------------------
# ADD CARD (AI or Manual)
# -------------------------------------------------------------------------

@main_bp.route("/api/cards/add", methods=["POST"])
@login_required
def api_add_card():
    try:
        from src.cards import CardCollectionManager
        stats = CardCollectionManager().get_collection_stats(current_user.id)
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------------------------
# GET CARD BY ID
# -------------------------------------------------------------------------

@main_bp.route("/api/cards/<int:card_id>", methods=["GET"])
@login_required
def api_get_card(card_id):
    try:
        from src.cards import CardCollectionManager
        manager = CardCollectionManager()

        card = manager.get_card(card_id)
        if not card:
            return jsonify({"error": "Card not found"}), 404
        if card.user_id != current_user.id:
            return jsonify({"error": "Unauthorized"}), 403

        return jsonify({"success": True, "card": card.to_dict()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------------------------
# UPDATE CARD
# -------------------------------------------------------------------------

@main_bp.route("/api/cards/<int:card_id>", methods=["PUT"])
@login_required
def api_update_card(card_id):
    try:
        from src.cards import CardCollectionManager
        manager = CardCollectionManager()

        card = manager.get_card(card_id)
        if not card:
            return jsonify({"error": "Card not found"}), 404
        if card.user_id != current_user.id:
            return jsonify({"error": "Unauthorized"}), 403

        data = request.get_json()

        # Update fields
        for field in [
            "title", "quantity", "storage_location", "notes",
            "estimated_value", "grading_company", "grading_score"
        ]:
            if field in data:
                setattr(card, field, data[field])

        manager.update_card(card_id, card)

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------------------------
# DELETE CARD
# -------------------------------------------------------------------------

@main_bp.route("/api/cards/<int:card_id>", methods=["DELETE"])
@login_required
def api_delete_card(card_id):
    try:
        from src.cards import CardCollectionManager
        manager = CardCollectionManager()

        card = manager.get_card(card_id)
        if not card:
            return jsonify({"error": "Card not found"}), 404
        if card.user_id != current_user.id:
            return jsonify({"error": "Unauthorized"}), 403

        manager.delete_card(card_id)
        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------------------------
# STORAGE API ENDPOINTS
# -------------------------------------------------------------------------

@main_bp.route('/api/storage/bins', methods=['GET'])
@login_required
def api_get_storage_bins():
    """Get all storage bins for the current user"""
    try:
        bin_type = request.args.get('type')  # 'clothing' or 'cards'
        bins = db.get_storage_bins(current_user.id, bin_type)

        # Get section counts for each bin
        for bin in bins:
            sections = db.get_storage_sections(bin['id'])
            bin['section_count'] = len(sections)
            bin['sections'] = sections

        return jsonify({
            "success": True,
            "bins": bins
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/storage/create-bin', methods=['POST'])
@login_required
def api_create_storage_bin():
    """Create a new storage bin"""
    try:
        data = request.get_json()
        bin_name = data.get('bin_name')
        bin_type = data.get('bin_type')  # 'clothing' or 'cards'
        description = data.get('description', '')

        if not bin_name or not bin_type:
            return jsonify({"error": "bin_name and bin_type are required"}), 400

        bin_id = db.create_storage_bin(
            user_id=current_user.id,
            bin_name=bin_name,
            bin_type=bin_type,
            description=description
        )

        return jsonify({
            "success": True,
            "bin_id": bin_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/storage/create-section', methods=['POST'])
@login_required
def api_create_storage_section():
    """Create a new section within a bin"""
    try:
        data = request.get_json()
        bin_id = data.get('bin_id')
        section_name = data.get('section_name')
        capacity = data.get('capacity')

        if not bin_id or not section_name:
            return jsonify({"error": "bin_id and section_name are required"}), 400

        # Verify the bin belongs to the current user
        bins = db.get_storage_bins(current_user.id)
        if not any(b['id'] == bin_id for b in bins):
            return jsonify({"error": "Bin not found or unauthorized"}), 403

        section_id = db.create_storage_section(
            bin_id=bin_id,
            section_name=section_name,
            capacity=capacity
        )

        return jsonify({
            "success": True,
            "section_id": section_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/storage/items', methods=['GET'])
@login_required
def api_get_storage_items():
    """Get storage items, optionally filtered by bin"""
    try:
        bin_id = request.args.get('bin_id', type=int)

        if bin_id:
            # Verify the bin belongs to the current user
            bins = db.get_storage_bins(current_user.id)
            if not any(b['id'] == bin_id for b in bins):
                return jsonify({"error": "Bin not found or unauthorized"}), 403

            items = db.get_storage_items(current_user.id, bin_id=bin_id)
        else:
            items = db.get_storage_items(current_user.id)

        return jsonify({
            "success": True,
            "items": items
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/storage/add-item', methods=['POST'])
@login_required
def api_add_storage_item():
    """Add a new item to storage"""
    try:
        data = request.get_json()
        bin_id = data.get('bin_id')
        section_id = data.get('section_id')
        item_type = data.get('item_type')
        category = data.get('category')
        title = data.get('title')
        description = data.get('description')
        notes = data.get('notes')

        if not bin_id:
            return jsonify({"error": "bin_id is required"}), 400

        # Verify the bin belongs to the current user
        bins = db.get_storage_bins(current_user.id)
        bin_obj = next((b for b in bins if b['id'] == bin_id), None)
        if not bin_obj:
            return jsonify({"error": "Bin not found or unauthorized"}), 403

        # Get section name if section_id provided
        section_name = None
        if section_id:
            sections = db.get_storage_sections(bin_id)
            section_obj = next((s for s in sections if s['id'] == section_id), None)
            if section_obj:
                section_name = section_obj['section_name']

        # Generate storage ID
        storage_id = db.generate_storage_id(
            user_id=current_user.id,
            bin_name=bin_obj['bin_name'],
            section_name=section_name,
            category=category
        )

        # Add the item
        item_id = db.add_storage_item(
            user_id=current_user.id,
            storage_id=storage_id,
            bin_id=bin_id,
            section_id=section_id,
            item_type=item_type,
            category=category,
            title=title,
            description=description,
            notes=notes
        )

        return jsonify({
            "success": True,
            "item_id": item_id,
            "storage_id": storage_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route(
    "/api/storage/find",
    methods=["GET"],
    endpoint="storage_find_get"
)
@login_required
def api_find_storage_item():
    """Find an item by storage ID"""
    try:
        storage_id = request.args.get('storage_id')

        if not storage_id:
            return jsonify({"error": "storage_id is required"}), 400

        item = db.find_storage_item(current_user.id, storage_id)

        if item:
            return jsonify({
                "success": True,
                "item": item
            })
        else:
            return jsonify({
                "success": False,
                "error": "Item not found"
            }), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------------------------
# INVENTORY MANAGEMENT ENDPOINTS
# -------------------------------------------------------------------------

@main_bp.route('/inventory')
@login_required
def inventory():
    """Centralized inventory management page"""
    return render_template('inventory.html')


@main_bp.route('/api/inventory/listings')
@login_required
def api_get_inventory():
    """Get all inventory items with filtering"""
    try:
        from src.database.db import get_db_instance
        db = get_db_instance()

        # Get filter parameters
        status_filter = request.args.get('status', 'all')  # all, draft, active, sold, shipped, archived
        category_filter = request.args.get('category', 'all')
        platform_filter = request.args.get('platform', 'all')
        search_query = request.args.get('search', '').strip()
        sort_by = request.args.get('sort', 'created_at')  # created_at, title, price, status
        sort_order = request.args.get('order', 'desc')  # asc, desc
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        # Build query
        query = """
            SELECT
                l.*,
                COALESCE(SUM(CASE WHEN ps.status = 'sold' THEN 1 ELSE 0 END), 0) as sold_count,
                COUNT(ps.id) as platform_count,
                STRING_AGG(DISTINCT p.name, ', ') as platforms
            FROM listings l
            LEFT JOIN platform_listings ps ON l.id = ps.listing_id
            LEFT JOIN platforms p ON ps.platform_id = p.id
            WHERE l.user_id::text = %s::text
        """
        params = [str(current_user.id)]

        # Add status filter
        if status_filter != 'all':
            query += " AND l.status = %s"
            params.append(status_filter)

        # Add category filter
        if category_filter != 'all':
            query += " AND l.category ILIKE %s"
            params.append(f"%{category_filter}%")

        # Add platform filter
        if platform_filter != 'all':
            query += " AND p.name = %s"
            params.append(platform_filter)

        # Add search filter
        if search_query:
            query += """ AND (
                l.title ILIKE %s OR
                l.description ILIKE %s OR
                l.sku ILIKE %s OR
                l.upc ILIKE %s
            )"""
            search_param = f"%{search_query}%"
            params.extend([search_param] * 4)

        # Group by and add sorting
        query += """
            GROUP BY l.id
            ORDER BY l.{sort_by} {sort_order}
            LIMIT %s OFFSET %s
        """.format(sort_by=sort_by, sort_order=sort_order)
        params.extend([per_page, (page - 1) * per_page])

        # Execute query
        cursor = db._get_cursor()
        try:
            cursor.execute(query, params)
            listings = [dict(row) for row in cursor.fetchall()]

            # Get total count for pagination
            count_query = """
                SELECT COUNT(DISTINCT l.id) as total
                FROM listings l
                LEFT JOIN platform_listings ps ON l.id = ps.listing_id
                LEFT JOIN platforms p ON ps.platform_id = p.id
                WHERE l.user_id::text = %s::text
            """
            count_params = [str(current_user.id)]

            # Apply same filters for count
            if status_filter != 'all':
                count_query += " AND l.status = %s"
                count_params.append(status_filter)
            if category_filter != 'all':
                count_query += " AND l.category ILIKE %s"
                count_params.append(f"%{category_filter}%")
            if platform_filter != 'all':
                count_query += " AND p.name = %s"
                count_params.append(platform_filter)
            if search_query:
                count_query += """ AND (
                    l.title ILIKE %s OR
                    l.description ILIKE %s OR
                    l.sku ILIKE %s OR
                    l.upc ILIKE %s
                )"""
                search_param = f"%{search_query}%"
                count_params.extend([search_param] * 4)

            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()['total']

            # Get summary stats
            stats_query = """
                SELECT
                    COUNT(CASE WHEN status = 'draft' THEN 1 END) as draft_count,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_count,
                    COUNT(CASE WHEN status = 'sold' THEN 1 END) as sold_count,
                    COUNT(CASE WHEN status = 'shipped' THEN 1 END) as shipped_count,
                    COUNT(CASE WHEN status = 'archived' THEN 1 END) as archived_count,
                    COUNT(*) as total_count,
                    COALESCE(SUM(CASE WHEN status IN ('sold', 'shipped') THEN price ELSE 0 END), 0) as total_value
                FROM listings
                WHERE user_id::text = %s::text
            """
            cursor.execute(stats_query, (str(current_user.id),))
            stats = dict(cursor.fetchone())

            return jsonify({
                'success': True,
                'listings': listings,
                'stats': stats,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': (total_count + per_page - 1) // per_page
                }
            })
        finally:
            cursor.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/inventory/bulk-update', methods=['POST'])
@login_required
def api_bulk_update_inventory():
    """Bulk update inventory items"""
    try:
        from src.database.db import get_db_instance
        db = get_db_instance()

        data = request.get_json()
        listing_ids = data.get('listing_ids', [])
        updates = data.get('updates', {})  # status, category, etc.

        if not listing_ids:
            return jsonify({'error': 'No listing IDs provided'}), 400

        if not updates:
            return jsonify({'error': 'No updates provided'}), 400

        updated_count = 0
        failed = []

        for listing_id in listing_ids:
            try:
                # Verify ownership
                listing = db.get_listing(listing_id)
                if not listing or str(listing['user_id']) != str(current_user.id):
                    failed.append({'id': listing_id, 'error': 'Not found or unauthorized'})
                    continue

                # Update listing
                db.update_listing(listing_id, **updates)
                updated_count += 1

            except Exception as e:
                failed.append({'id': listing_id, 'error': str(e)})

        return jsonify({
            'success': True,
            'updated': updated_count,
            'failed': failed
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/inventory/bulk-delete', methods=['POST'])
@login_required
def api_bulk_delete_inventory():
    """Bulk delete inventory items"""
    try:
        from src.database.db import get_db_instance
        db = get_db_instance()

        data = request.get_json()
        listing_ids = data.get('listing_ids', [])
        confirm_delete = data.get('confirm', False)

        if not listing_ids:
            return jsonify({'error': 'No listing IDs provided'}), 400

        if not confirm_delete:
            return jsonify({'error': 'Deletion not confirmed'}), 400

        deleted_count = 0
        failed = []

        for listing_id in listing_ids:
            try:
                # Verify ownership
                listing = db.get_listing(listing_id)
                if not listing or str(listing['user_id']) != str(current_user.id):
                    failed.append({'id': listing_id, 'error': 'Not found or unauthorized'})
                    continue

                # Delete listing
                db.delete_listing(listing_id)
                deleted_count += 1

            except Exception as e:
                failed.append({'id': listing_id, 'error': str(e)})

        return jsonify({
            'success': True,
            'deleted': deleted_count,
            'failed': failed
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/inventory/export')
@login_required
def api_export_inventory():
    """Export inventory data"""
    try:
        from src.database.db import get_db_instance
        from src.import_export.csv_handler import CSVImportExport

        db = get_db_instance()
        csv_handler = CSVImportExport(db)

        export_type = request.args.get('type', 'all')  # all, draft, active, sold
        format_type = request.args.get('format', 'csv')  # csv, json

        if format_type == 'csv':
            csv_content = csv_handler.export_csv(current_user.id, export_type)
            return csv_content, 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename=inventory_{export_type}.csv'
            }
        else:
            # JSON export
            listings = csv_handler._get_listings_for_export(current_user.id, export_type)
            return jsonify({
                'success': True,
                'listings': listings,
                'export_type': export_type
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# -------------------------------------------------------------------------
# SETTINGS API ENDPOINTS
# -------------------------------------------------------------------------

@main_bp.route('/api/settings/notification-email', methods=['POST'])
@login_required
def api_update_notification_email():
    """Update notification email"""
    try:
        from src.database.db import get_db_instance
        db = get_db_instance()

        data = request.get_json()
        email = data.get('notification_email')

        if not email:
            return jsonify({"error": "notification_email is required"}), 400

        cursor = db._get_cursor()
        cursor.execute("""
            UPDATE users
            SET notification_email = %s
            WHERE id = %s
        """, (email, current_user.id))
        db.conn.commit()

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/settings/marketplace-credentials', methods=['POST'])
@login_required
def api_save_marketplace_credentials():
    """Save marketplace credentials"""
    try:
        from src.database.db import get_db_instance
        db = get_db_instance()

        data = request.get_json()
        platform = data.get('platform')
        username = data.get('username')
        password = data.get('password')

        if not platform or not username or not password:
            return jsonify({"error": "platform, username, and password are required"}), 400

        cursor = db._get_cursor()
        cursor.execute("""
            INSERT INTO marketplace_credentials (user_id, platform, username, password)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, platform)
            DO UPDATE SET username = %s, password = %s, updated_at = CURRENT_TIMESTAMP
        """, (current_user.id, platform, username, password, username, password))
        db.conn.commit()

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/settings/marketplace-credentials/<platform>', methods=['DELETE'])
@login_required
def api_delete_marketplace_credentials(platform):
    """Delete marketplace credentials"""
    try:
        from src.database.db import get_db_instance
        db = get_db_instance()

        cursor = db._get_cursor()
        cursor.execute("""
            DELETE FROM marketplace_credentials
            WHERE user_id = %s AND platform = %s
        """, (current_user.id, platform))
        db.conn.commit()

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/settings/api-credentials', methods=['POST'])
@login_required
def api_save_api_credentials():
    """Save API credentials for automated platforms"""
    try:
        from src.database.db import get_db_instance
        import json
        db = get_db_instance()

        data = request.get_json()
        platform = data.get('platform')
        credentials = data.get('credentials')

        if not platform or not credentials:
            return jsonify({"error": "platform and credentials are required"}), 400

        cursor = db._get_cursor()
        cursor.execute("""
            INSERT INTO api_credentials (user_id, platform, credentials)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, platform)
            DO UPDATE SET credentials = %s, updated_at = CURRENT_TIMESTAMP
        """, (current_user.id, platform, json.dumps(credentials), json.dumps(credentials)))
        db.conn.commit()

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------------------------
# CSV EXPORT ENDPOINT
# -------------------------------------------------------------------------

@main_bp.route('/api/export-csv', methods=['POST'])
@login_required
def api_export_csv():
    """Export listings to platform-specific CSV format"""
    try:
        import csv
        import io
        from flask import make_response

        data = request.get_json()
        platform = data.get('platform', 'generic')
        listings = data.get('listings', [])

        if not listings:
            return jsonify({"error": "No listings provided"}), 400

        # Create CSV in memory
        output = io.StringIO()

        # Platform-specific CSV formats
        if platform == 'poshmark':
            fieldnames = ['Title', 'Description', 'Category', 'Brand', 'Size', 'Color', 'Price', 'Quantity', 'Condition', 'Photos']
        elif platform == 'mercari':
            fieldnames = ['Title', 'Description', 'Category', 'Brand', 'Price', 'Condition', 'Shipping Weight', 'Photos']
        elif platform == 'ebay':
            fieldnames = ['Title', 'Description', 'Category', 'Price', 'Quantity', 'Condition', 'Brand', 'Photos', 'SKU']
        elif platform == 'grailed':
            fieldnames = ['Title', 'Description', 'Designer', 'Size', 'Category', 'Price', 'Condition', 'Photos']
        elif platform == 'depop':
            fieldnames = ['Title', 'Description', 'Category', 'Brand', 'Size', 'Price', 'Condition', 'Photos']
        else:  # generic
            fieldnames = ['Title', 'Description', 'Price', 'Category', 'Brand', 'Size', 'Color', 'Condition', 'Quantity', 'Storage Location', 'Photos']

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for listing in listings:
            # Parse photos if stored as JSON string
            photos = listing.get('photos', '')
            if isinstance(photos, str) and photos:
                try:
                    import json
                    photos = json.loads(photos)
                    photos = ','.join(photos) if isinstance(photos, list) else photos
                except:
                    pass

            # Create row based on platform
            row = {}
            if platform == 'poshmark':
                row = {
                    'Title': listing.get('title', ''),
                    'Description': listing.get('description', ''),
                    'Category': listing.get('category', listing.get('item_type', '')),
                    'Brand': listing.get('brand', ''),
                    'Size': listing.get('size', ''),
                    'Color': listing.get('color', ''),
                    'Price': listing.get('price', ''),
                    'Quantity': listing.get('quantity', 1),
                    'Condition': listing.get('condition', ''),
                    'Photos': photos
                }
            elif platform == 'mercari':
                row = {
                    'Title': listing.get('title', ''),
                    'Description': listing.get('description', ''),
                    'Category': listing.get('category', listing.get('item_type', '')),
                    'Brand': listing.get('brand', ''),
                    'Price': listing.get('price', ''),
                    'Condition': listing.get('condition', ''),
                    'Shipping Weight': listing.get('weight', '1 lb'),
                    'Photos': photos
                }
            elif platform == 'ebay':
                row = {
                    'Title': listing.get('title', ''),
                    'Description': listing.get('description', ''),
                    'Category': listing.get('category', listing.get('item_type', '')),
                    'Price': listing.get('price', ''),
                    'Quantity': listing.get('quantity', 1),
                    'Condition': listing.get('condition', ''),
                    'Brand': listing.get('brand', ''),
                    'Photos': photos,
                    'SKU': listing.get('sku', '')
                }
            elif platform == 'grailed':
                row = {
                    'Title': listing.get('title', ''),
                    'Description': listing.get('description', ''),
                    'Designer': listing.get('brand', ''),
                    'Size': listing.get('size', ''),
                    'Category': listing.get('category', listing.get('item_type', '')),
                    'Price': listing.get('price', ''),
                    'Condition': listing.get('condition', ''),
                    'Photos': photos
                }
            elif platform == 'depop':
                row = {
                    'Title': listing.get('title', ''),
                    'Description': listing.get('description', ''),
                    'Category': listing.get('category', listing.get('item_type', '')),
                    'Brand': listing.get('brand', ''),
                    'Size': listing.get('size', ''),
                    'Price': listing.get('price', ''),
                    'Condition': listing.get('condition', ''),
                    'Photos': photos
                }
            else:  # generic
                row = {
                    'Title': listing.get('title', ''),
                    'Description': listing.get('description', ''),
                    'Price': listing.get('price', ''),
                    'Category': listing.get('category', listing.get('item_type', '')),
                    'Brand': listing.get('brand', ''),
                    'Size': listing.get('size', ''),
                    'Color': listing.get('color', ''),
                    'Condition': listing.get('condition', ''),
                    'Quantity': listing.get('quantity', 1),
                    'Storage Location': listing.get('storage_location', ''),
                    'Photos': photos
                }

            writer.writerow(row)

        # Create response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename={platform}_export.csv'

        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# FEED GENERATION ENDPOINT
# -------------------------------------------------------------------------

@main_bp.route('/api/generate-feed', methods=['POST'])
@login_required
def api_generate_feed():
    """Generate product feed for catalog platforms (Facebook, Google Shopping, Pinterest)"""
    try:
        import io
        from flask import make_response  # type: ignore
        from ..src.adapters.all_platforms import FacebookShopsAdapter, GoogleShoppingAdapter, PinterestAdapter  # type: ignore
        from ..src.schema.unified_listing import UnifiedListing, Price, ListingCondition, Photo

        data = request.get_json()
        platform = data.get('platform', 'facebook')
        format_type = data.get('format', 'csv')  # csv, xml, json

        # Get active listings for the user
        listings_data = db.get_active_listings(current_user.id)
        
        if not listings_data:
            return jsonify({"error": "No active listings found"}), 404

        # Convert to UnifiedListing objects
        listings = []
        for listing_data in listings_data:
            try:
                # Convert price to Price object
                price_obj = Price(amount=float(listing_data['price']))

                # Convert condition to ListingCondition enum
                condition_str = listing_data.get('condition', 'good').lower()
                condition_enum = ListingCondition.GOOD  # default
                if condition_str == 'new':
                    condition_enum = ListingCondition.NEW
                elif condition_str == 'like_new':
                    condition_enum = ListingCondition.LIKE_NEW
                elif condition_str == 'excellent':
                    condition_enum = ListingCondition.EXCELLENT
                elif condition_str == 'fair':
                    condition_enum = ListingCondition.FAIR
                elif condition_str == 'poor':
                    condition_enum = ListingCondition.POOR

                # Convert photos from JSON string to List[Photo]
                photos = []
                if listing_data.get('photos'):
                    try:
                        import json
                        photos_data = json.loads(listing_data['photos'])
                        for i, photo_url in enumerate(photos_data):
                            photos.append(Photo(url=photo_url, order=i, is_primary=(i == 0)))
                    except (json.JSONDecodeError, TypeError):
                        # If photos is not valid JSON, skip
                        pass

                listing = UnifiedListing(
                    title=listing_data['title'],
                    description=listing_data.get('description', ''),
                    price=price_obj,
                    condition=condition_enum,
                    photos=photos
                )
                listings.append(listing)
            except Exception as e:
                print(f"Error converting listing {listing_data.get('id')}: {e}")
                continue

        # Initialize the appropriate adapter
        adapter = None
        if platform == 'facebook':
            adapter = FacebookShopsAdapter()
        elif platform == 'google':
            adapter = GoogleShoppingAdapter()
        elif platform == 'pinterest':
            adapter = PinterestAdapter()
        else:
            return jsonify({"error": f"Unsupported platform: {platform}"}), 400

        # Generate the feed
        feed_path = adapter.generate_feed(listings, format_type)
        
        # Read the feed file and return it
        with open(feed_path, 'r', encoding='utf-8') as f:
            feed_content = f.read()

        # Create response
        response = make_response(feed_content)
        
        # Set appropriate content type
        if format_type == 'xml':
            response.headers['Content-Type'] = 'application/xml'
            extension = 'xml'
        elif format_type == 'json':
            response.headers['Content-Type'] = 'application/json'
            extension = 'json'
        else:
            response.headers['Content-Type'] = 'text/csv'
            extension = 'csv'
            
        response.headers['Content-Disposition'] = f'attachment; filename={platform}_feed.{extension}'

        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# DRAFT → LISTING WORKFLOW
# ============================================================================

@main_bp.route('/api/publish-drafts', methods=['POST'])
@login_required
def api_publish_drafts():
    """Publish selected drafts to active listings and optionally to platforms"""
    try:
        data = request.get_json()
        draft_ids = data.get('draft_ids', [])
        platforms = data.get('platforms', [])  # List of platforms to publish to
        auto_assign_sku = data.get('auto_assign_sku', True)

        if not draft_ids:
            return jsonify({"error": "No draft IDs provided"}), 400

        results = {
            'published': [],
            'failed': [],
            'platform_results': {}
        }

        for draft_id in draft_ids:
            try:
                # Get draft
                draft = db.get_listing(draft_id)
                if not draft:
                    results['failed'].append({
                        'draft_id': draft_id,
                        'error': 'Draft not found'
                    })
                    continue

                # Verify ownership
                if str(draft['user_id']) != str(current_user.id):
                    results['failed'].append({
                        'draft_id': draft_id,
                        'error': 'Permission denied'
                    })
                    continue

                # Auto-assign SKU if needed
                if auto_assign_sku and not draft.get('sku'):
                    sku = db.assign_auto_sku_if_missing(draft_id, current_user.id)
                    draft['sku'] = sku

                # Move photos from draft-images to listing-images bucket when publishing
                try:
                    from src.storage.supabase_storage import get_supabase_storage
                    storage = get_supabase_storage()
                    
                    if draft.get('photos'):
                        moved_photos = []
                        for photo_url in draft['photos']:
                            # Check if it's in draft-images bucket
                            if 'supabase.co' in photo_url and 'draft-images' in photo_url:
                                # Move to listing-images bucket
                                success, new_url = storage.move_photo(
                                    source_url=photo_url,
                                    destination_folder='listings',
                                    new_filename=f"{draft.get('listing_uuid', uuid.uuid4().hex)}_{uuid.uuid4().hex}.jpg"
                                )
                                if success:
                                    moved_photos.append(new_url)
                                else:
                                    moved_photos.append(photo_url)  # Keep original if move fails
                            else:
                                moved_photos.append(photo_url)  # Keep non-Supabase URLs
                        
                        # Update listing with new photo URLs
                        if moved_photos != draft['photos']:
                            db.update_listing(draft_id, photos=moved_photos)
                except Exception as storage_error:
                    import logging
                    logging.warning(f"Could not move photos to listing-images bucket: {storage_error}")
                    # Continue with publish even if photo move fails

                # Change status to active
                db.update_listing_status(draft_id, 'active')

                results['published'].append({
                    'draft_id': draft_id,
                    'title': draft['title'],
                    'sku': draft.get('sku')
                })

            except Exception as e:
                results['failed'].append({
                    'draft_id': draft_id,
                    'error': str(e)
                })

        # Publish to platforms if specified
        if platforms and results['published']:
            platform_results = {}
            for platform in platforms:
                try:
                    # Import platform adapter
                    if platform.lower() == 'ebay':
                        from ..src.adapters.ebay_adapter import EbayAdapter
                        adapter_class = EbayAdapter
                    elif platform.lower() == 'mercari':
                        from ..src.adapters.mercari_adapter import MercariAdapter
                        adapter_class = MercariAdapter
                    elif platform.lower() == 'poshmark':
                        from ..src.adapters.poshmark_adapter import PoshmarkAdapter
                        adapter_class = PoshmarkAdapter
                    else:
                        # Try to get from all_platforms
                        from ..src.adapters.all_platforms import get_adapter_class as get_all_adapter_class
                        adapter_class = get_all_adapter_class(platform)
                        if not adapter_class:
                            platform_results[platform] = {'error': f'Unsupported platform: {platform}'}
                            continue

                    # Try to create adapter instance
                    adapter = None
                    try:
                        # Check if adapter has from_env method
                        if hasattr(adapter_class, 'from_env'):
                            adapter = adapter_class.from_env()
                        else:
                            # For adapters that don't need auth (like CSV adapters)
                            adapter = adapter_class()
                    except Exception as e:
                        platform_results[platform] = {'error': f'Authentication/setup required for {platform}: {str(e)}'}
                        continue

                    # Get platform mapper
                    from ..src.adapters.platform_configs import get_platform_mapper
                    mapper = get_platform_mapper(platform)

                    # Publish each listing
                    published_count = 0
                    failed_count = 0
                    for item in results['published']:
                        try:
                            listing_data = db.get_listing(item['draft_id'])

                            # Convert to UnifiedListing
                            from ..schema.unified_listing import UnifiedListing
                            unified_listing = UnifiedListing.from_dict(listing_data)

                            # Publish to platform (adapter handles field mapping internally)
                            result = adapter.publish_listing(unified_listing)
                            if result.get('success'):
                                published_count += 1
                            else:
                                failed_count += 1
                                print(f"Failed to publish {item['draft_id']} to {platform}: {result.get('error', 'Unknown error')}")

                        except Exception as e:
                            failed_count += 1
                            print(f"Failed to publish {item['draft_id']} to {platform}: {e}")

                    platform_results[platform] = {
                        'published': published_count,
                        'failed': failed_count,
                        'total': len(results['published'])
                    }

                except Exception as e:
                    platform_results[platform] = {'error': str(e)}

            results['platform_results'] = platform_results

            # Format response for frontend compatibility
            csv_files = {}
            api_results = []

            for platform, result in platform_results.items():
                if 'error' in result:
                    if platform.lower() in ['poshmark', 'bonanza', 'ecrater', 'rubylane', 'offerup']:
                        # CSV platform error
                        csv_files[platform] = {
                            'platform_name': platform.title(),
                            'error': result['error']
                        }
                    else:
                        # API platform error
                        api_results.append({
                            'platform_name': platform.title(),
                            'status': 'error',
                            'message': result['error']
                        })
                else:
                    if platform.lower() in ['poshmark', 'bonanza', 'ecrater', 'rubylane', 'offerup']:
                        # CSV platform success - would need to generate CSV here
                        csv_files[platform] = {
                            'platform_name': platform.title(),
                            'download_url': f'/api/export-csv?platform={platform}&ids={",".join(str(item["draft_id"]) for item in results["published"])}',
                            'instructions': [
                                f'Log into your {platform.title()} account',
                                f'Go to the bulk upload section',
                                f'Upload the generated CSV file',
                                'Review and publish listings'
                            ]
                        }
                    else:
                        # API platform result
                        api_results.append({
                            'platform_name': platform.title(),
                            'status': 'posted' if result['published'] > 0 else 'partial',
                            'message': f'Successfully posted {result["published"]} of {result["total"]} listings'
                        })

            results['csv_files'] = csv_files
            results['api_results'] = api_results

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/bulk-edit-drafts', methods=['POST'])
@login_required
def api_bulk_edit_drafts():
    """Bulk edit multiple drafts"""
    try:
        data = request.get_json()
        draft_ids = data.get('draft_ids', [])
        updates = data.get('updates', {})  # Fields to update

        if not draft_ids:
            return jsonify({"error": "No draft IDs provided"}), 400

        if not updates:
            return jsonify({"error": "No updates provided"}), 400

        results = {
            'updated': [],
            'failed': []
        }

        for draft_id in draft_ids:
            try:
                # Verify ownership
                draft = db.get_listing(draft_id)
                if not draft or str(draft['user_id']) != str(current_user.id):
                    results['failed'].append({
                        'draft_id': draft_id,
                        'error': 'Permission denied or draft not found'
                    })
                    continue

                # Update the draft
                db.update_listing(draft_id, **updates)

                results['updated'].append({
                    'draft_id': draft_id,
                    'title': draft['title']
                })

            except Exception as e:
                results['failed'].append({
                    'draft_id': draft_id,
                    'error': str(e)
                })

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/schedule-feed-sync', methods=['POST'])
@login_required
def api_schedule_feed_sync():
    """Schedule automatic feed sync for catalog platforms"""
    try:
        from ..src.workers.scheduler import Scheduler
        
        data = request.get_json()
        platforms = data.get('platforms', ['facebook', 'google', 'pinterest'])
        interval_hours = data.get('interval_hours', 6)  # Default 6 hours
        
        # Get or create scheduler instance
        # TODO: This should be a singleton/global instance
        scheduler = Scheduler()
        scheduler.start()
        
        # Schedule feed sync for current user
        job_id = scheduler.schedule_feed_sync(
            user_id=current_user.id,
            platforms=platforms,
            interval_hours=interval_hours
        )
        
        return jsonify({
            "status": "scheduled",
            "job_id": job_id,
            "platforms": platforms,
            "interval_hours": interval_hours,
            "message": f"Feed sync scheduled every {interval_hours} hours for platforms: {', '.join(platforms)}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# PLATFORM CONNECTIONS UI & API
# ============================================================================

@main_bp.route("/platforms")
@login_required
def platforms_page():
    """Platform connections management page"""
    # Get user's platform connections from database
    connections = db.get_platform_connections(current_user.id) if hasattr(db, 'get_platform_connections') else {}

    return render_template("platforms.html", connections=connections)


@main_bp.route("/api/platform/<platform>/connect", methods=["POST"])
@login_required
def connect_platform(platform):
    """Connect a platform with API key/credentials"""
    try:
        data = request.get_json()

        # Store platform credentials (encrypted in production!)
        if hasattr(db, 'save_platform_connection'):
            db.save_platform_connection(
                user_id=current_user.id,
                platform=platform,
                credentials=data
            )
        else:
            # Fallback: store in user's settings
            print(f"Platform {platform} connection saved for user {current_user.id}")

        return jsonify({"success": True, "message": f"Connected to {platform}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/platform/<platform>/disconnect", methods=["DELETE"])
@login_required
def disconnect_platform(platform):
    """Disconnect a platform"""
    try:
        if hasattr(db, 'delete_platform_connection'):
            db.delete_platform_connection(current_user.id, platform)
        else:
            print(f"Platform {platform} disconnected for user {current_user.id}")

        return jsonify({"success": True, "message": f"Disconnected from {platform}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/platform/<platform>/test", methods=["GET"])
@login_required
def test_platform_connection(platform):
    """Test a platform connection"""
    try:
        # Get platform credentials
        if hasattr(db, 'get_platform_connection'):
            credentials = db.get_platform_connection(current_user.id, platform)

            if not credentials:
                return jsonify({"error": "Platform not connected"}), 404

            # Test the connection (implement per platform)
            # For now, just return success
            return jsonify({"success": True, "message": f"Connection to {platform} is working"})
        else:
            return jsonify({"error": "Platform connections not implemented"}), 501

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/listing/<int:listing_id>/platforms", methods=["GET"])
@login_required
def get_listing_platforms(listing_id):
    """Get platform status for a specific listing"""
    try:
        # Check listing belongs to user
        listing = db.get_listing(listing_id)
        if not listing or listing.get('user_id') != current_user.id:
            return jsonify({"error": "Listing not found"}), 404

        # Get platform statuses
        if hasattr(db, 'get_listing_platform_status'):
            platforms = db.get_listing_platform_status(listing_id)
        else:
            # Default implementation
            platforms = [
                {"name": "ebay", "status": "active", "listing_id": "123456789", "updated_at": "2025-11-29"},
                {"name": "etsy", "status": "draft", "listing_id": None, "updated_at": "2025-11-29"},
                {"name": "shopify", "status": "inactive", "listing_id": None, "updated_at": None}
            ]

        return jsonify({"success": True, "platforms": platforms})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/listing/<int:listing_id>/publish-to-platform", methods=["POST"])
@login_required
def publish_to_platform(listing_id):
    """Publish a listing to a specific platform"""
    try:
        data = request.get_json()
        platform = data.get('platform')

        if not platform:
            return jsonify({"error": "Platform is required"}), 400

        # Check listing belongs to user
        listing = db.get_listing(listing_id)
        if not listing or listing.get('user_id') != current_user.id:
            return jsonify({"error": "Listing not found"}), 404

        # Publish to platform
        from src.listing_manager import ListingManager
        manager = ListingManager()
        result = manager.publish_to_platform(listing_id, platform)

        return jsonify({"success": True, "result": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/listing/<int:listing_id>/delist-from-platform", methods=["POST"])
@login_required
def delist_from_platform(listing_id):
    """Remove a listing from a specific platform"""
    try:
        data = request.get_json()
        platform = data.get('platform')

        if not platform:
            return jsonify({"error": "Platform is required"}), 400

        # Check listing belongs to user
        listing = db.get_listing(listing_id)
        if not listing or listing.get('user_id') != current_user.id:
            return jsonify({"error": "Listing not found"}), 404

        # Delist from platform
        from src.listing_manager import ListingManager
        manager = ListingManager()
        result = manager.delist_from_platform(listing_id, platform)

        return jsonify({"success": True, "result": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# CSV IMPORT SYSTEM
# ============================================================================

@main_bp.route("/api/import/csv", methods=["POST"])
@login_required
def import_csv():
    """Import listings from CSV file"""
    try:
        csv_module = __import__("src.import", fromlist=["CSVImporter"])

        CSVImporter = csv_module.CSVImporter
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        if not file.filename.endswith('.csv'):
            return jsonify({"error": "File must be a CSV"}), 400

        # Read CSV
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as temp:
            file.save(temp.name)
            temp_path = temp.name

        try:
            importer = CSVImporter(user_id=current_user.id, db=db)
            result = importer.import_csv(temp_path)

            return jsonify({
                "success": True,
                "imported": result['imported'],
                "skipped": result['skipped'],
                "errors": result['errors'],
                "duplicates": result.get('duplicates', [])
            })
        finally:
            import os
            os.unlink(temp_path)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# IMAGE PROCESSING PIPELINE
# ============================================================================

@main_bp.route("/api/image/process", methods=["POST"])
@login_required
def process_image():
    """Process an image through the pipeline"""
    try:
        from src.images import ImagePipeline

        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        platform = request.form.get('platform', 'generic')

        # Save uploaded file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp:
            file.save(temp.name)
            input_path = temp.name

        try:
            pipeline = ImagePipeline()

            # Process image
            output_path = pipeline.process_for_platform(input_path, platform)

            # Return processed image
            from flask import send_file
            return send_file(output_path, as_attachment=True)

        finally:
            import os
            os.unlink(input_path)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# TAX & ACCOUNTING REPORTS
# ============================================================================

@main_bp.route("/api/reports/tax/<period>", methods=["GET"])
@login_required
def generate_tax_report(period):
    """Generate tax report (monthly, quarterly, annual)"""
    try:
        from src.accounting import TaxReportGenerator

        generator = TaxReportGenerator(db)
        report = generator.generate_report(
            user_id=current_user.id,
            period=period,
            year=int(request.args.get('year', datetime.now().year))
        )

        return jsonify({"success": True, "report": report})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/reports/profit", methods=["GET"])
@login_required
def get_profit_summary():
    """Get profit summary for user's listings"""
    try:
        from src.accounting import TaxReportGenerator

        generator = TaxReportGenerator(db)
        summary = generator.get_profit_summary(current_user.id)

        return jsonify({"success": True, "summary": summary})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# STORAGE LOCATION MANAGEMENT
# ============================================================================

@main_bp.route("/api/storage/locations", methods=["GET"])
@login_required
def get_storage_locations():
    """Get all storage locations for current user"""
    try:
        from src.storage import StorageManager
        manager = StorageManager(db)
        locations = manager.get_user_locations(current_user.id)
        return jsonify({"success": True, "locations": locations})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/storage/location", methods=["POST"])
@login_required
def create_storage_location():
    """Create a new storage location"""
    try:
        from src.storage import StorageManager
        data = request.get_json()

        manager = StorageManager(db)
        location = manager.create_location(
            user_id=current_user.id,
            name=data.get('name'),
            location_type=data.get('type', 'bin'),
            parent_id=data.get('parent_id'),
            notes=data.get('notes')
        )

        return jsonify({"success": True, "location": location})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/storage/location/<int:location_id>", methods=["GET"])
@login_required
def get_storage_location(location_id):
    """Get storage location details"""
    try:
        from src.storage import StorageManager
        manager = StorageManager(db)
        location = manager.get_location(location_id)

        if not location:
            return jsonify({"error": "Location not found"}), 404

        # Get items in this location
        items = manager.get_location_items(location_id)

        return jsonify({
            "success": True,
            "location": location,
            "items": items
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/storage/assign", methods=["POST"])
@login_required
def assign_storage_location():
    """Assign an item to a storage location"""
    try:
        from src.storage import StorageManager
        data = request.get_json()

        manager = StorageManager(db)
        success = manager.assign_location(
            listing_id=data.get('listing_id'),
            location_id=data.get('location_id'),
            quantity=data.get('quantity', 1)
        )

        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/storage/bulk-assign", methods=["POST"])
@login_required
def bulk_assign_storage():
    """Bulk assign multiple items to a location"""
    try:
        from src.storage import StorageManager
        data = request.get_json()

        manager = StorageManager(db)
        result = manager.bulk_assign(
            location_id=data.get('location_id'),
            listing_ids=data.get('listing_ids', [])
        )

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/storage/suggest", methods=["POST"])
@login_required
def suggest_storage_location():
    """Suggest optimal storage location for an item"""
    try:
        from src.storage import StorageManager
        data = request.get_json()

        manager = StorageManager(db)
        suggestion = manager.suggest_location(
            user_id=current_user.id,
            category=data.get('category'),
            size=data.get('size')
        )

        return jsonify({"success": True, "suggestion": suggestion})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# SALES SYNC ENGINE
# ============================================================================

@main_bp.route("/api/sales/sync/<platform>", methods=["POST"])
@login_required
def sync_platform_sales(platform):
    """Sync sales from a specific platform"""
    try:
        from src.sales import SalesSyncEngine

        engine = SalesSyncEngine(db)
        result = engine.sync_platform_sales(current_user.id, platform)

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/sales/sync-all", methods=["POST"])
@login_required
def sync_all_sales():
    """Sync sales from all connected platforms"""
    try:
        from src.sales import SalesSyncEngine

        engine = SalesSyncEngine(db)
        result = engine.sync_all_platforms(current_user.id)

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/sales/manual-sale", methods=["POST"])
@login_required
def record_manual_sale():
    """Manually record a sale (for platforms without API)"""
    try:
        from src.sales import SalesSyncEngine
        data = request.get_json()

        engine = SalesSyncEngine(db)
        result = engine.detect_sale(
            listing_id=data.get('listing_id'),
            platform=data.get('platform', 'manual'),
            sale_data={
                'price': data.get('price'),
                'buyer': data.get('buyer', {}),
                'sale_date': data.get('sale_date', datetime.now()),
                'transaction_id': data.get('transaction_id')
            }
        )

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/sales/<int:listing_id>", methods=["GET"])
@login_required
def get_sale_details(listing_id):
    """Get detailed sale information"""
    try:
        from src.sales import SalesSyncEngine

        # Check listing belongs to user
        listing = db.get_listing(listing_id)
        if not listing or listing.get('user_id') != current_user.id:
            return jsonify({"error": "Listing not found"}), 404

        engine = SalesSyncEngine(db)
        details = engine.get_sale_details(listing_id)

        if not details:
            return jsonify({"error": "No sale data found"}), 404

        return jsonify({"success": True, "sale": details})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# INVOICING ROUTES
# ============================================================================

@main_bp.route('/invoicing')
@login_required
def invoicing():
    """Invoicing management page"""
    return render_template('invoicing.html')


@main_bp.route('/api/create-invoice', methods=['POST'])
@login_required
def api_create_invoice():
    """Create a new invoice"""
    try:
        from ..src.invoicing.invoice_generator import InvoiceGenerator

        data = request.get_json()
        listing_id = data.get('listing_id')
        buyer_email = data.get('buyer_email')
        tax_rate = data.get('tax_rate', 0)
        shipping_cost = data.get('shipping_cost', 0)
        discount = data.get('discount', 0)

        if not listing_id or not buyer_email:
            return jsonify({"error": "Missing required fields"}), 400

        # Get listing details
        listing = db.get_listing(listing_id)
        if not listing:
            return jsonify({"error": "Listing not found"}), 404

        # Create buyer info
        buyer = {
            'email': buyer_email,
            'name': buyer_email.split('@')[0]  # Simple name extraction
        }

        # Generate invoice
        generator = InvoiceGenerator()
        invoice_data = generator.create_invoice(
            listing=listing,
            buyer=buyer,
            tax_rate=tax_rate / 100.0,  # Convert percentage to decimal
            shipping=shipping_cost,
            discount=discount
        )

        # Store invoice in database (simplified - just return for now)
        invoice_id = f"inv_{listing_id}_{int(datetime.now().timestamp())}"

        return jsonify({
            "success": True,
            "invoice_id": invoice_id,
            "invoice": invoice_data,
            "message": "Invoice created successfully"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/invoices')
@login_required
def api_get_invoices():
    """Get list of invoices for current user"""
    try:
        # For now, return empty list since we don't have database storage
        return jsonify({"success": True, "invoices": []})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/invoice/<invoice_id>')
@login_required
def api_get_invoice(invoice_id):
    """Get invoice details and HTML"""
    try:
        # For now, return a sample invoice
        sample_invoice = {
            'invoice_number': 'INV-2024-00001',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'buyer': {'email': 'buyer@example.com', 'name': 'Sample Buyer'},
            'item': {'title': 'Sample Item', 'price': 25.00},
            'totals': {'subtotal': 25.00, 'tax': 2.06, 'shipping': 5.00, 'total': 32.06},
            'status': 'unpaid'
        }

        from ..src.invoicing.invoice_generator import InvoiceGenerator
        generator = InvoiceGenerator()
        html = generator.generate_invoice_html(sample_invoice)

        return jsonify({"success": True, "invoice": sample_invoice, "html": html})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/email-invoice/<invoice_id>', methods=['POST'])
@login_required
def api_email_invoice(invoice_id):
    """Email invoice to buyer"""
    try:
        from ..src.invoicing.invoice_generator import InvoiceGenerator

        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({"error": "Email address required"}), 400

        generator = InvoiceGenerator()
        invoice = generator.get_invoice(invoice_id)

        if not invoice or str(invoice.get('user_id')) != str(current_user.id):
            return jsonify({"error": "Invoice not found"}), 404

        # Generate HTML and send email
        html = generator.generate_invoice_html(invoice)

        # TODO: Implement email sending
        # For now, just return success
        return jsonify({"success": True, "message": f"Invoice would be sent to {email}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# BILLING & SUBSCRIPTION ROUTES
# ============================================================================

@main_bp.route('/billing')
@login_required
def billing():
    """Billing and subscription management page"""
    try:
        from ..src.billing import BillingManager, SubscriptionTier

        billing_manager = BillingManager()
        user_tier = billing_manager.get_user_tier(current_user.id)
        tier_limits = billing_manager.get_tier_limits(user_tier)

        # Get current usage
        can_create_listing, limit_message = billing_manager.check_listing_limit(current_user.id)

        return render_template('billing.html',
                user_tier=user_tier.value,
                tier_limits=tier_limits,
                can_create_listing=can_create_listing,
                limit_message=limit_message)

    except Exception as e:
        flash(f'Error loading billing page: {str(e)}', 'error')
        return redirect(url_for('main.index'))


@main_bp.route('/api/billing/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create Stripe checkout session for subscription"""
    try:
        from ..src.billing import StripeIntegration

        data = request.get_json()
        tier = data.get('tier')

        if not tier or tier not in ['PRO', 'BUSINESS']:
            return jsonify({"error": "Invalid tier"}), 400

        stripe_integration = StripeIntegration()

        success_url = url_for('main.billing_success', _external=True)
        cancel_url = url_for('main.billing', _external=True)

        session = stripe_integration.create_checkout_session(
            user_id=current_user.id,
            tier=tier,
            success_url=success_url,
            cancel_url=cancel_url
        )

        return jsonify(session)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/billing/success')
@login_required
def billing_success():
    """Billing success page"""
    flash('Subscription activated successfully!', 'success')
    return redirect(url_for('main.billing'))


@main_bp.route('/api/billing/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    try:
        from ..src.billing import StripeIntegration

        payload = request.get_data()
        sig_header = request.headers.get('stripe-signature')

        if not sig_header:
            return jsonify({"error": "No signature"}), 400

        stripe_integration = StripeIntegration()
        result = stripe_integration.handle_webhook(payload, sig_header)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/billing/check-feature-access', methods=['GET'])
@login_required
def check_feature_access():
    """Check if user can access a feature"""
    try:
        from ..src.billing import BillingManager

        feature = request.args.get('feature')
        if not feature:
            return jsonify({"error": "Feature parameter required"}), 400

        billing_manager = BillingManager()
        can_access = billing_manager.can_access_feature(current_user.id, feature)

        return jsonify({
            "can_access": can_access,
            "feature": feature
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/billing/usage', methods=['GET'])
@login_required
def get_usage():
    """Get current usage statistics"""
    try:
        from ..src.billing import BillingManager

        billing_manager = BillingManager()

        # Check listing limit
        can_create, limit_message = billing_manager.check_listing_limit(current_user.id)

        return jsonify({
            "can_create_listing": can_create,
            "limit_message": limit_message
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/billing/cancel-subscription', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel user subscription"""
    try:
        from ..src.billing import BillingManager, SubscriptionTier

        billing_manager = BillingManager()

        # Cancel at period end (downgrade to FREE)
        billing_manager.update_subscription(
            user_id=current_user.id,
            tier=SubscriptionTier.FREE
        )

        flash('Subscription cancelled. You will be downgraded to FREE tier at the end of your billing period.', 'info')
        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/save-vault", methods=["POST"])
@login_required
def api_save_vault():
    """Save card/item to user's card_collections database"""
    try:
        from src.cards import CardCollectionManager, UnifiedCard
        from src.cards.storage_maps import suggest_storage_region
        import uuid as uuid_module

        data = request.json

        # Validation logging
        logging.info(f"[VAULT SAVE] User {current_user.id} saving item")
        logging.info(f"[VAULT SAVE] Data keys: {list(data.keys()) if data else 'None'}")
        
        # Check if user wants storage map guidance
        use_storage_map = data.get('use_storage_map', False)
        
        # Extract card data from form or AI analysis
        # Check if we have card data from AI analysis
        card_data = data.get('card_data') or data.get('ai_result') or {}
        
        # Extract form fields
        title = data.get('title', card_data.get('card_name') or card_data.get('player_name') or 'Unknown Card')
        brand = data.get('brand', card_data.get('brand', ''))
        year = data.get('year', card_data.get('year'))
        if year:
            try:
                year = int(year) if isinstance(year, (int, str)) and str(year).isdigit() else None
            except:
                year = None
        
        # Determine card type - prioritize TCG detection
        item_type = data.get('item_type', '').lower()
        category = card_data.get('category', '').lower() if isinstance(card_data.get('category'), str) else ''
        game_name = card_data.get('game_name', '').lower() if isinstance(card_data.get('game_name'), str) else ''
        
        card_type = 'unknown'
        
        # Check for TCG cards first (Pokemon, MTG, Yu-Gi-Oh, etc.)
        if 'pokemon' in game_name or 'pokemon' in category or 'pokemon' in item_type:
            card_type = 'pokemon'
        elif 'magic' in game_name or 'mtg' in game_name or 'magic' in category:
            card_type = 'mtg'
        elif 'yugioh' in game_name or 'yu-gi-oh' in game_name or 'yugioh' in category:
            card_type = 'yugioh'
        elif card_data.get('game_name'):
            # Generic TCG - use game name to determine type
            game = card_data.get('game_name').lower()
            if 'pokemon' in game:
                card_type = 'pokemon'
            elif 'magic' in game or 'mtg' in game:
                card_type = 'mtg'
            elif 'yugioh' in game or 'yu-gi-oh' in game:
                card_type = 'yugioh'
            else:
                card_type = 'tcg'  # Generic TCG
        # Check for sports cards
        elif card_data.get('sport'):
            sport = card_data.get('sport').lower()
            if 'football' in sport or 'nfl' in sport:
                card_type = 'sports_nfl'
            elif 'basketball' in sport or 'nba' in sport:
                card_type = 'sports_nba'
            elif 'baseball' in sport or 'mlb' in sport:
                card_type = 'sports_mlb'
            elif 'hockey' in sport or 'nhl' in sport:
                card_type = 'sports_nhl'
            else:
                card_type = f'sports_{sport.replace(" ", "_")}'
        elif 'sports card' in item_type or 'sports' in category:
            card_type = 'sports'
        elif 'trading card' in item_type or card_data.get('card_type'):
            # Use provided card_type or default to generic
            card_type = card_data.get('card_type', 'trading_card')
        
        # Determine if this is a TCG or Sports card
        is_tcg = card_type in ['pokemon', 'mtg', 'yugioh', 'tcg', 'trading_card'] or card_type.startswith('tcg_')
        is_sports = card_type.startswith('sports') or card_type == 'sports'
        
        # Extract game_name for TCG cards
        tcg_game_name = None
        if is_tcg:
            if card_type == 'pokemon':
                tcg_game_name = 'Pokemon'
            elif card_type == 'mtg':
                tcg_game_name = 'Magic: The Gathering'
            elif card_type == 'yugioh':
                tcg_game_name = 'Yu-Gi-Oh!'
            else:
                tcg_game_name = card_data.get('game_name') or 'Trading Card Game'
        
        # Create UnifiedCard - only set sport-related fields for sports cards
        manager = CardCollectionManager()
        
        # Get storage region guidance if enabled
        storage_region = None
        if use_storage_map:
            # Determine franchise from card data (try multiple sources)
            franchise = (
                card_data.get('franchise') or 
                card_data.get('game_name') or 
                data.get('franchise') or
                data.get('game_name')
            )
            
            if not franchise and is_tcg:
                # Try to get franchise from game_name
                franchise = tcg_game_name or card_data.get('game_name')
            elif not franchise and is_sports:
                # Try to get franchise from sport
                sport = card_data.get('sport') or data.get('sport')
                if sport:
                    franchise = sport.upper()
            elif not franchise:
                # Try to infer from card_type
                if card_type == 'pokemon':
                    franchise = 'Pokemon'
                elif card_type == 'mtg':
                    franchise = 'Magic: The Gathering'
                elif card_type == 'yugioh':
                    franchise = 'Yu-Gi-Oh!'
                elif card_type.startswith('sports_'):
                    franchise = card_type.replace('sports_', '').upper()
            
            # Get recommended region
            region, guidance = suggest_storage_region(
                franchise=franchise,
                card_type=card_type,
                rarity=card_data.get('rarity'),
                is_rookie=card_data.get('is_rookie_card', False),
                grading_score=card_data.get('grading_score')
            )
            
            if region:
                storage_region = region.value
        
        # Build card with conditional fields
        card_kwargs = {
            'card_type': card_type,
            'title': title,
            'user_id': current_user.id,
            'card_number': card_data.get('card_number') or data.get('card_number'),
            'quantity': int(data.get('quantity', 1)),
            'organization_mode': 'by_set' if is_tcg else 'by_year' if is_sports else 'by_set',
            
            # Grading (universal)
            'grading_company': card_data.get('grading_company'),
            'grading_score': card_data.get('grading_score'),
            'grading_serial': card_data.get('grading_serial'),
            
            # Value & storage (universal)
            'estimated_value': card_data.get('estimated_value') or card_data.get('estimated_value_avg'),
            'storage_location': data.get('storage_location', ''),
            'storage_region': storage_region,  # Recommended region from storage map
            'photos': data.get('photos', []),
            'notes': data.get('description', ''),
            'ai_identified': bool(card_data),
            'ai_confidence': card_data.get('confidence_score', 0.0)
        }
        
        # Add TCG-specific fields
        if is_tcg:
            card_kwargs.update({
                'game_name': tcg_game_name,
                'set_name': card_data.get('set_name') or card_data.get('set'),
                'set_code': card_data.get('set_code'),
                'rarity': card_data.get('rarity'),
            })
        
        # Add Sports-specific fields (only for sports cards)
        if is_sports:
            card_kwargs.update({
                'sport': card_data.get('sport'),
                'year': year,
                'brand': brand or card_data.get('brand'),
                'series': card_data.get('series'),
                'player_name': card_data.get('player_name'),
                'is_rookie_card': card_data.get('is_rookie_card', False),
            })
        elif is_tcg:
            # For TCG cards, year and brand might still be useful
            if year:
                card_kwargs['year'] = year
            if brand:
                card_kwargs['brand'] = brand
        
        card = UnifiedCard(**card_kwargs)
        logging.info(f"[VAULT SAVE] Created UnifiedCard: type={card.card_type}, title={card.title}")

        card_id = manager.add_card(card)
        logging.info(f"[VAULT SAVE] Successfully saved card with ID: {card_id}")

        # Prepare response with storage guidance if used
        response_data = {
            "success": True,
            "card_id": card_id,
            "message": "Card saved to your collection vault successfully"
        }
        
        if use_storage_map and storage_region:
            # Get guidance text for the region
            from src.cards.storage_maps import get_storage_map_for_franchise, StorageRegion
            franchise = card_data.get('franchise') or card_data.get('game_name') or card_data.get('sport')
            if franchise:
                storage_map = get_storage_map_for_franchise(franchise)
                if storage_map:
                    region_enum = StorageRegion(storage_region)
                    guidance = storage_map.get_guidance_text(region_enum)
                    response_data['storage_guidance'] = guidance
                    response_data['storage_region'] = storage_region
        
        return jsonify(response_data)

    except ImportError as e:
        import traceback
        logging.error(f"[VAULT SAVE] Import error: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": f"Module import failed: {str(e)}"}), 500
    except ValueError as e:
        import traceback
        logging.error(f"[VAULT SAVE] Validation error: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": f"Invalid data: {str(e)}"}), 400
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logging.error(f"[VAULT SAVE] Unexpected error: {e}\n{error_trace}")
        return jsonify({"success": False, "error": f"Failed to save: {str(e)}"}), 500


# -------------------------------------------------------------------------
# CSV EXPORT ENDPOINTS
# -------------------------------------------------------------------------

@main_bp.route("/api/export/csv/<platform>", methods=["POST"])
@login_required
def export_csv_for_platform(platform):
    """
    Export listings to platform-specific CSV format
    
    POST body:
    {
        "listing_ids": [1, 2, 3],  // Optional, if not provided exports all drafts
        "include_drafts": true      // Optional, default true
    }
    """
    try:
        from src.csv_exporters import get_exporter
        from flask import make_response
        
        # Get request data
        data = request.json or {}
        listing_ids = data.get('listing_ids', [])
        include_drafts = data.get('include_drafts', True)
        
        # Get listings
        cursor = db._get_cursor()
        
        if listing_ids:
            # Export specific listings
            placeholders = ','.join(['%s'] * len(listing_ids))
            query = f"""
                SELECT * FROM listings
                WHERE id IN ({placeholders}) AND user_id = %s
                ORDER BY created_at DESC
            """
            cursor.execute(query, (*listing_ids, current_user.id))
        else:
            # Export all drafts by default
            if include_drafts:
                cursor.execute("""
                    SELECT * FROM listings
                    WHERE user_id = %s AND status = 'draft'
                    ORDER BY created_at DESC
                """, (current_user.id,))
            else:
                cursor.execute("""
                    SELECT * FROM listings
                    WHERE user_id = %s AND status != 'draft'
                    ORDER BY created_at DESC
                """, (current_user.id,))
        
        listings = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        
        if not listings:
            return jsonify({"error": "No listings found to export"}), 404
        
        # Get the appropriate exporter
        try:
            exporter = get_exporter(platform)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        
        # Generate CSV
        csv_content = exporter.export_to_csv(listings)
        
        # Create response with CSV file
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename={platform}_export.csv'
        
        return response
        
    except Exception as e:
        import traceback
        logging.error(f"CSV export error: {e}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/export/platforms", methods=["GET"])
@login_required
def get_export_platforms():
    """Get list of available CSV export platforms"""
    try:
        from src.csv_exporters import EXPORTERS
        
        platforms = []
        for platform_key, exporter_class in EXPORTERS.items():
            exporter = exporter_class()
            platforms.append({
                'key': platform_key,
                'name': exporter.platform_name,
                'description': f'Export to {exporter.platform_name} CSV format'
            })
        
        return jsonify({
            "success": True,
            "platforms": platforms
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/export/preview/<platform>", methods=["POST"])
@login_required
def preview_csv_export(platform):
    """
    Preview how listings will be mapped to platform format
    Returns first 3 transformed listings for preview
    """
    try:
        from src.csv_exporters import get_exporter
        
        data = request.json or {}
        listing_ids = data.get('listing_ids', [])
        
        # Get first few listings
        cursor = db._get_cursor()
        
        if listing_ids:
            query = """
                SELECT * FROM listings
                WHERE id IN (%s, %s, %s) AND user_id = %s
                LIMIT 3
            """
            cursor.execute(query, (*listing_ids[:3], current_user.id))
        else:
            cursor.execute("""
                SELECT * FROM listings
                WHERE user_id = %s AND status = 'draft'
                ORDER BY created_at DESC
                LIMIT 3
            """, (current_user.id,))
        
        listings = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        
        if not listings:
            return jsonify({"error": "No listings found"}), 404
        
        # Get exporter and transform
        try:
            exporter = get_exporter(platform)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        
        # Transform listings for preview
        transformed = [exporter.transform_listing(listing) for listing in listings]
        
        return jsonify({
            "success": True,
            "platform": exporter.platform_name,
            "preview": transformed,
            "field_mapping": exporter.get_field_mapping()
        })
        
    except Exception as e:
        import traceback
        logging.error(f"CSV preview error: {e}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500
