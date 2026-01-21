# Image Flow & AI Photo Analysis - Current Implementation Snapshot

**Date:** Current (for comparison with ~150 commits earlier)  
**Purpose:** Complete snapshot of image flow and AI photo analysis functionality

---

## Table of Contents

1. [Frontend Image Flow](#frontend-image-flow)
2. [AI Analysis System](#ai-analysis-system)
3. [Backend API Endpoints](#backend-api-endpoints)
4. [CSS Styles](#css-styles)
5. [Key Features](#key-features)

---

## Frontend Image Flow

### Location
`templates/create.html` (lines 16-41, 182-229, 231-291, 295-739)

### Photo Upload Section (HTML)
```html
<!-- Photo Upload -->
<div class="card mb-3">
    <div class="card-header bg-primary text-white">
        <i class="fas fa-camera"></i> Photos
    </div>
    <div class="card-body">
        <div class="row mb-3">
            <div class="col-6">
                <button type="button" class="btn btn-outline-primary w-100" onclick="document.getElementById('cameraInput').click()">
                    <i class="fas fa-camera"></i><br>Take Photo
                </button>
                <input type="file" class="d-none" id="cameraInput" name="photos" accept="image/*" capture="environment" onchange="handlePhotoSelect(event)">
            </div>
            <div class="col-6">
                <button type="button" class="btn btn-outline-secondary w-100" onclick="document.getElementById('photoInput').click()">
                    <i class="fas fa-upload"></i><br>Upload Files
                </button>
                <input type="file" class="d-none" id="photoInput" name="photos" multiple accept="image/*" onchange="handlePhotoSelect(event)">
            </div>
        </div>
        <div id="photoPreview" class="mt-3 d-flex flex-wrap"></div>
        <button type="button" class="btn btn-secondary mt-2" id="analyzeBtn" style="display:none;">
            <i class="fas fa-magic"></i> Analyze with AI
        </button>
    </div>
</div>
```

### Photo Editor Modal (HTML)
```html
<!-- Photo Editor Modal -->
<div id="photoEditorModal" class="photo-editor-modal">
    <div class="photo-editor-container">
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h4><i class="fas fa-magic"></i> Edit Photo (FREE!)</h4>
            <button class="btn btn-outline-danger" onclick="closePhotoEditor()">
                <i class="fas fa-times"></i> Close
            </button>
        </div>

        <div class="text-center mb-3">
            <img id="photoEditorImage" class="photo-editor-image" src="">
        </div>

        <div class="photo-editor-toolbar">
            <button class="btn btn-primary" onclick="enableCrop()">
                <i class="fas fa-crop"></i> Crop
            </button>
            <button class="btn btn-success" id="cropBtn" onclick="applyCrop()" style="display:none;">
                <i class="fas fa-check"></i> Apply Crop
            </button>
            <button class="btn btn-danger" id="cancelCropBtn" onclick="cancelCrop()" style="display:none;">
                <i class="fas fa-times"></i> Cancel Crop
            </button>
            <button class="btn btn-warning" onclick="removeBackground()">
                <i class="fas fa-magic"></i> Remove Background
            </button>
            <button class="btn btn-secondary" onclick="resetPhoto()">
                <i class="fas fa-undo"></i> Reset
            </button>
        </div>

        <div class="alert alert-info mt-3">
            <i class="fas fa-gift"></i> <strong>FREE Feature!</strong> Other apps charge $5-20/month for background removal. We give it to you free!
        </div>
    </div>
</div>
```

### Image Zoom Modal (HTML)
```html
<!-- Image Zoom Modal -->
<div id="imageZoomModal" class="image-zoom-modal" onclick="closeImageZoom()" style="display: none;">
    <div class="image-zoom-container">
        <button class="btn btn-outline-light zoom-close-btn" onclick="closeImageZoom()">
            <i class="fas fa-times"></i>
        </button>
        <img id="zoomImage" src="" alt="Zoomed image">
        <div class="zoom-hint">Click image to zoom | Right-click to see details</div>
    </div>
</div>
```

### JavaScript: Photo Upload Handler
```javascript
// Generic photo handling function for both camera and file upload
async function handlePhotoSelect(e) {
    const files = e.target.files;
    if (files.length === 0) return;

    const formData = new FormData();
    for (let file of files) {
        formData.append('photos', file);
    }

    showLoading();

    try {
        const response = await fetch('/api/upload-photos', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            // Append to existing photos instead of replacing
            uploadedPhotos = uploadedPhotos.concat(data.paths);

            // Show previews (append to existing)
            const previewDiv = document.getElementById('photoPreview');
            for (let i = 0; i < files.length; i++) {
                const photoIndex = uploadedPhotos.length - data.paths.length + i;

                // Create container for photo + delete button
                const container = document.createElement('div');
                container.className = 'photo-preview-container';
                container.style.position = 'relative';
                container.style.display = 'inline-block';
                container.style.margin = '5px';

                // Create image
                const img = document.createElement('img');
                img.src = URL.createObjectURL(files[i]);
                img.className = 'photo-preview';
                img.title = 'Click to edit | Right-click to zoom';

                // Make photo clickable to open editor
                img.onclick = function(e) {
                    e.preventDefault();
                    openPhotoEditor(photoIndex, this.src);
                };

                // Right-click to zoom
                img.oncontextmenu = function(e) {
                    e.preventDefault();
                    openImageZoom(data.paths[i]);
                };

                // Create delete button
                const deleteBtn = document.createElement('button');
                deleteBtn.innerHTML = '<i class="fas fa-times"></i>';
                deleteBtn.className = 'btn btn-danger btn-sm photo-delete-btn';
                deleteBtn.style.position = 'absolute';
                deleteBtn.style.top = '5px';
                deleteBtn.style.right = '5px';
                deleteBtn.style.padding = '2px 6px';
                deleteBtn.style.fontSize = '12px';
                deleteBtn.title = 'Remove photo';
                deleteBtn.onclick = function(e) {
                    e.preventDefault();
                    removePhoto(photoIndex);
                };

                container.appendChild(img);
                container.appendChild(deleteBtn);
                previewDiv.appendChild(container);
            }

            document.getElementById('analyzeBtn').style.display = 'block';
            showAlert(`${data.count} photo(s) added! Total: ${uploadedPhotos.length}`, 'success');
        } else {
            showAlert(data.error, 'danger');
        }
    } catch (error) {
        showAlert('Upload failed: ' + error, 'danger');
    } finally {
        hideLoading();
    }

    // Reset input so same file can be selected again
    e.target.value = '';
}
```

### JavaScript: Photo Editor Functions
```javascript
// Photo Editor Variables
let cropper = null;
let currentEditingPhotoIndex = null;
let currentEditingPhotoSrc = null;
let originalPhotoSrc = null;

// Open Photo Editor
async function openPhotoEditor(photoIndex, photoSrc) {
    currentEditingPhotoIndex = photoIndex;
    originalPhotoSrc = photoSrc;

    const modal = document.getElementById('photoEditorModal');
    const img = document.getElementById('photoEditorImage');

    // Convert blob URL to base64 data URL
    try {
        if (photoSrc.startsWith('blob:')) {
            // Fetch the blob and convert to base64
            const response = await fetch(photoSrc);
            const blob = await response.blob();

            // Convert blob to base64 using FileReader
            const reader = new FileReader();
            reader.onloadend = function() {
                currentEditingPhotoSrc = reader.result; // This is the base64 data URL
                img.src = currentEditingPhotoSrc;
            };
            reader.readAsDataURL(blob);
        } else {
            // Already a data URL or regular URL
            currentEditingPhotoSrc = photoSrc;
            img.src = photoSrc;
        }
    } catch (error) {
        console.error('Error converting image:', error);
        currentEditingPhotoSrc = photoSrc;
        img.src = photoSrc;
    }

    modal.classList.add('show');

    // Destroy existing cropper if any
    if (cropper) {
        cropper.destroy();
        cropper = null;
    }

    // Reset buttons
    document.getElementById('cropBtn').style.display = 'none';
    document.getElementById('cancelCropBtn').style.display = 'none';
}

// Enable Crop
function enableCrop() {
    const img = document.getElementById('photoEditorImage');

    if (cropper) {
        cropper.destroy();
    }

    cropper = new Cropper(img, {
        aspectRatio: NaN, // Free aspect ratio
        viewMode: 1,
        responsive: true,
        autoCropArea: 0.8,
        background: false,
        ready: function() {
            showAlert('Drag to select crop area', 'info');
        }
    });

    // Show crop action buttons
    document.getElementById('cropBtn').style.display = 'inline-block';
    document.getElementById('cancelCropBtn').style.display = 'inline-block';
}

// Apply Crop
async function applyCrop() {
    if (!cropper) return;

    showLoading();

    try {
        const canvas = cropper.getCroppedCanvas();
        const croppedImage = canvas.toDataURL('image/png');

        // Get crop coordinates for API call
        const cropData = cropper.getData();

        // Create abort controller for timeout
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 15000); // 15 second timeout

        const response = await fetch('/api/edit-photo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image: currentEditingPhotoSrc,
                operation: 'crop',
                crop: {
                    x: Math.round(cropData.x),
                    y: Math.round(cropData.y),
                    width: Math.round(cropData.width),
                    height: Math.round(cropData.height)
                }
            }),
            signal: controller.signal
        });

        clearTimeout(timeout);

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            // Update the photo
            updatePhotoAfterEdit(data.image, data.filepath);
            showAlert('Photo cropped successfully!', 'success');

            // Cleanup cropper
            cropper.destroy();
            cropper = null;
            document.getElementById('cropBtn').style.display = 'none';
            document.getElementById('cancelCropBtn').style.display = 'none';
        } else {
            showAlert('Crop failed: ' + (data.error || 'Unknown error'), 'danger');
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            showAlert('Crop timed out. Please try again.', 'warning');
        } else {
            showAlert('Crop failed: ' + error.message, 'danger');
        }
    } finally {
        hideLoading();
    }
}

// Remove Background
async function removeBackground() {
    if (!currentEditingPhotoSrc) return;

    showLoading();
    showAlert('Removing background... This may take 10-15 seconds', 'info');

    try {
        // Create abort controller for timeout
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 30000); // 30 second timeout

        const response = await fetch('/api/edit-photo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image: uploadedPhotos[currentEditingPhotoIndex],
                operation: 'remove-bg'
            }),
            signal: controller.signal
        });

        clearTimeout(timeout);

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            // Update the photo in uploadedPhotos array
            uploadedPhotos[currentEditingPhotoIndex] = data.filepath;
            // Update the editor image
            document.getElementById('photoEditorImage').src = data.filepath;
            currentEditingPhotoSrc = data.filepath;
            showAlert('Background removed! (FREE feature worth $5-20/mo)', 'success');
        } else {
            showAlert('Background removal failed: ' + (data.error || 'Unknown error'), 'danger');
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            showAlert('Background removal timed out. The image may be too large. Try a smaller image or crop it first.', 'warning');
        } else {
            showAlert('Background removal failed: ' + error.message, 'danger');
        }
    } finally {
        hideLoading();
    }
}
```

---

## AI Analysis System

### Two-Tier Architecture

**TIER 1: Quick Analysis (Gemini - Fast & Cheap)**
- Fast initial classification
- Basic item detection
- Form auto-fill
- Market analysis

**TIER 2: Enhanced Scanner (Claude - Deep Dive)**
- Deep collectible analysis
- Card authentication
- Detailed pricing
- Database integration

### JavaScript: Quick Analysis (Tier 1)
```javascript
// AI Analysis Variables
let detectedCardData = null;
let detectedCollectibleData = null;
let enhancedScanData = null;

// TIER 1: Quick Analysis (Gemini - Fast & Cheap)
document.getElementById('analyzeBtn').addEventListener('click', async function() {
    showLoading('Running quick analysis...');

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                photos: uploadedPhotos
            })
        });

        const data = await response.json();

        if (!data.success) {
            showAlert(data.error || 'Analysis failed', 'danger');
            hideLoading();
            return;
        }

        const analysis = data.analysis;

        // Fill form with basic info
        if (analysis.suggested_title) document.getElementById('title').value = analysis.suggested_title;
        if (analysis.description) document.getElementById('description').value = analysis.description;
        if (analysis.brand) document.getElementById('brand').value = analysis.brand;
        if (analysis.size) document.getElementById('size').value = analysis.size;
        if (analysis.color) document.getElementById('color').value = analysis.color;
        if (analysis.suggested_price) document.getElementById('price').value = analysis.suggested_price;
        if (analysis.condition) {
            const condition = analysis.condition.replace(' ', '_').toLowerCase();
            document.getElementById('condition').value = condition;
        }

        // Check if Enhanced Scan would be helpful
        const isCard = analysis.category === 'Trading Cards' || analysis.category === 'Sports Cards';
        const isCollectible = analysis.collectible === true;

        if (isCard || isCollectible) {
            showEnhancedScanOption(isCard, isCollectible, analysis);
        }

        // Show market analysis if available
        if (analysis.market_analysis) {
            showMarketAnalysis(analysis.market_analysis);
        }

        showAlert('Quick analysis complete!', 'success');

    } catch (error) {
        showAlert('Analysis failed: ' + error, 'danger');
    } finally {
        hideLoading();
    }
});
```

### JavaScript: Enhanced Scan (Tier 2)
```javascript
// TIER 2: Enhanced Scanner (Claude - Deep Dive)
async function runEnhancedScan() {
    showLoading('Running enhanced scan... This may take 10-20 seconds');

    try {
        const response = await fetch('/api/enhanced-scan', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                photos: uploadedPhotos
            })
        });

        const data = await response.json();

        if (!data.success) {
            if (data.type === 'standard_item') {
                showAlert('Not a collectible. Quick analysis is sufficient for this item.', 'info');
            } else {
                showAlert(data.error || data.message || 'Enhanced scan failed', 'danger');
            }
            hideLoading();
            return;
        }

        // Store enhanced scan data
        enhancedScanData = data;

        // Remove the "run enhanced scan" card
        document.getElementById('enhancedScanCard')?.remove();

        // Display results based on type
        if (data.type === 'card') {
            detectedCardData = data.data;
            showCardResults(data);
        } else if (data.type === 'collectible') {
            detectedCollectibleData = data.data;
            showCollectibleResults(data);
        }

        showAlert('Enhanced scan complete!', 'success');

    } catch (error) {
        showAlert('Enhanced scan failed: ' + error, 'danger');
    } finally {
        hideLoading();
    }
}
```

### JavaScript: Card Results Display
```javascript
// Display Card Results
function showCardResults(data) {
    const cardData = data.data;
    const prices = data.market_prices || {};

    const statsCard = `
        <div class="card border-success mb-3" id="enhancedResultsCard">
            <div class="card-header bg-success text-white">
                <i class="fas fa-id-card"></i> Card Analysis Complete
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <h5>${cardData.card_name || cardData.player_name || 'Unknown Card'}</h5>
                        ${cardData.set_name ? `<p class="mb-1"><strong>Set:</strong> ${cardData.set_name}</p>` : ''}
                        ${cardData.card_number ? `<p class="mb-1"><strong>Number:</strong> #${cardData.card_number}</p>` : ''}
                        ${cardData.rarity ? `<p class="mb-1"><strong>Rarity:</strong> ${cardData.rarity}</p>` : ''}
                        ${cardData.year ? `<p class="mb-1"><strong>Year:</strong> ${cardData.year}</p>` : ''}
                        ${cardData.brand ? `<p class="mb-1"><strong>Brand:</strong> ${cardData.brand}</p>` : ''}
                        ${cardData.is_rookie_card ? `<p class="mb-1"><span class="badge bg-warning">ROOKIE CARD</span></p>` : ''}
                        ${cardData.is_graded ? `<p class="mb-1"><strong>Graded:</strong> ${cardData.grading_company} ${cardData.grading_score}</p>` : ''}
                    </div>
                    <div class="col-md-6">
                        <h6>Market Prices</h6>
                        ${prices.tcgplayer ? `<p class="mb-1"><strong>TCGPlayer:</strong> $${prices.tcgplayer.market || 'N/A'}</p>` : ''}
                        ${prices.ebay ? `<p class="mb-1"><strong>eBay Sold Avg:</strong> $${prices.ebay.avg || 'N/A'}</p>` : ''}
                        ${prices.actual_selling ? `<p class="mb-1 text-success"><strong>Actual Selling:</strong> $${prices.actual_selling}</p>` : ''}
                        ${prices.quick_sale ? `<p class="mb-1 text-warning"><strong>Quick Sale:</strong> $${prices.quick_sale}</p>` : ''}
                    </div>
                </div>
                
                <hr>
                
                <div class="d-flex gap-2">
                    <button class="btn btn-success" onclick="storeCardOnly()">
                        <i class="fas fa-box"></i> Store in Collection
                    </button>
                    <button class="btn btn-outline-success" onclick="storeAndList()">
                        <i class="fas fa-plus-circle"></i> Store + Create Listing
                    </button>
                </div>
            </div>
        </div>
    `;

    // Remove existing results
    document.getElementById('enhancedResultsCard')?.remove();
    
    // Insert after market analysis or enhanced scan card
    const insertAfter = document.getElementById('marketAnalysisCard') || document.querySelector('.card');
    insertAfter.insertAdjacentHTML('afterend', statsCard);

    // Fill form with detailed card info
    fillFormFromCardData(cardData, prices);
}
```

---

## Backend API Endpoints

### Location
`routes_main.py`

### Photo Upload Endpoint
```python
@main_bp.route("/api/upload-photos", methods=["POST"])
@login_required
def api_upload_photos():
    """Handle photo uploads for listings with compression"""
    try:
        if 'photos' not in request.files:
            return jsonify({"error": "No photos provided"}), 400

        files = request.files.getlist('photos')
        if not files or files[0].filename == '':
            return jsonify({"error": "No files selected"}), 400

        # Create uploads directory if it doesn't exist
        upload_dir = Path('./data/uploads')
        upload_dir.mkdir(parents=True, exist_ok=True)

        uploaded_paths = []
        for file in files:
            if file and allowed_file(file.filename):
                # Compress image before saving
                compressed_file, ext = compress_image(file)

                # Generate unique filename
                filename = f"{uuid.uuid4().hex}.{ext}"
                filepath = upload_dir / filename

                # Save compressed file
                with open(filepath, 'wb') as f:
                    f.write(compressed_file.read())

                # Return web-accessible path
                uploaded_paths.append(f"/uploads/{filename}")

        if not uploaded_paths:
            return jsonify({"error": "No valid images uploaded"}), 400

        return jsonify({
            "success": True,
            "paths": uploaded_paths,
            "count": len(uploaded_paths)
        })

    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({"error": str(e)}), 500
```

### Photo Edit Endpoint
```python
@main_bp.route("/api/edit-photo", methods=["POST"])
@login_required
def api_edit_photo():
    """Edit photos: crop, remove background, etc."""
    try:
        data = request.get_json()
        image_data = data.get('image')
        operation = data.get('operation')
        crop_data = data.get('crop')

        if not image_data or not operation:
            return jsonify({"error": "Image and operation required"}), 400

        # Decode base64 image
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        img_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(img_bytes))

        # Process based on operation
        if operation == 'crop' and crop_data:
            # Crop image
            x = int(crop_data['x'])
            y = int(crop_data['y'])
            width = int(crop_data['width'])
            height = int(crop_data['height'])
            img = img.crop((x, y, x + width, y + height))
        elif operation == 'remove-bg':
            # Remove background using rembg
            from rembg import remove
            img_bytes = remove(img_bytes)
            img = Image.open(io.BytesIO(img_bytes))

        # Save edited image
        upload_dir = Path('./data/uploads')
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        new_filename = f"{uuid.uuid4().hex}.png"
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
```

### Quick Analysis Endpoint (Tier 1)
```python
@main_bp.route("/api/analyze", methods=["POST"])
@login_required
def api_analyze():
    """Analyze general items with Gemini (fast, cheap)"""
    try:
        from src.ai.gemini_classifier import GeminiClassifier
        from src.schema.unified_listing import Photo

        data = request.get_json()
        paths = data.get("photos", [])
        if not paths:
            return jsonify({"error": "No photos provided"}), 400

        photos = [Photo(url=p, local_path=f"./data{p}") for p in paths]
        classifier = GeminiClassifier.from_env()
        result = classifier.analyze_item(photos)

        if result.get("error"):
            return jsonify(result), 500

        return jsonify({"success": True, "analysis": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

### Enhanced Scan Endpoint (Tier 2)
```python
@main_bp.route("/api/enhanced-scan", methods=["POST"])
@login_required
def api_enhanced_scan():
    """
    Enhanced scanner for deep collectible analysis.
    Auto-detects: Card vs Collectible vs Standard Item
    Routes to appropriate analyzer and saves to databases.
    """
    try:
        from src.collectibles.enhanced_scanner import EnhancedScanner
        from src.schema.unified_listing import Photo
        
        data = request.json
        photo_paths = data.get('photos', [])
        
        if not photo_paths:
            return jsonify({'error': 'No photos provided'}), 400

        # Create Photo objects
        photos = [Photo(url=p, local_path=f"./data{p}") for p in photo_paths]

        # Run enhanced scanner
        scanner = EnhancedScanner.from_env()
        result = scanner.scan(photos)
        
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
        
        # Save to public database
        public_db_id = None
        try:
            public_db_id = db.add_to_public_collectibles(
                item_type=result['type'],
                data=result['data'],
                scanned_by=current_user.id
            )
        except Exception as e:
            print(f"Warning: Failed to save to public database: {e}")
        
        # Save to user's personal collection
        user_collection_id = None
        try:
            if result['type'] == 'card':
                # Save to cards collection
                from src.cards import add_card_to_collection
                user_collection_id = add_card_to_collection(
                    result['data'],
                    current_user.id,
                    photos=photo_paths,
                    storage_location=data.get('storage_location')
                )
            else:
                # Save to collectibles collection
                user_collection_id = db.add_to_user_collectibles(
                    current_user.id,
                    result['data'],
                    photos=photo_paths
                )
        except Exception as e:
            print(f"Warning: Failed to save to user collection: {e}")
        
        return jsonify({
            'success': True,
            'type': result['type'],
            'data': result['data'],
            'market_prices': result.get('market_prices'),
            'ai_provider': result.get('ai_provider', 'claude'),
            'public_db_id': public_db_id,
            'user_collection_id': user_collection_id
        })
        
    except Exception as e:
        import traceback
        print(f"Enhanced scan error: {e}")
        print(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
```

---

## CSS Styles

### Image Zoom Modal Styles
```css
.image-zoom-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.95);
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: zoom-out;
}

.image-zoom-container {
    position: relative;
    max-width: 95%;
    max-height: 95%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.zoom-close-btn {
    position: absolute;
    top: 20px;
    right: 20px;
    z-index: 10000;
    border: 2px solid white;
}

#zoomImage {
    max-width: 100%;
    max-height: 90vh;
    object-fit: contain;
    cursor: zoom-in;
}

.zoom-hint {
    position: absolute;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    color: white;
    background: rgba(0, 0, 0, 0.7);
    padding: 10px 20px;
    border-radius: 5px;
    font-size: 14px;
}

.photo-preview {
    cursor: pointer;
    transition: transform 0.2s;
}

.photo-preview:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
}
```

---

## Key Features

### Image Flow Features
1. **Photo Upload**
   - Camera capture (mobile)
   - File upload (multiple files)
   - Image compression (max 2MB, 2048px)
   - Preview thumbnails

2. **Photo Editor**
   - Crop tool (Cropper.js)
   - Background removal (rembg library)
   - Reset to original
   - Click to edit, right-click to zoom

3. **Photo Management**
   - Delete photos
   - Reorder (via array manipulation)
   - Zoom modal
   - Preview thumbnails with hover effects

### AI Analysis Features
1. **Two-Tier System**
   - Tier 1: Gemini (fast, cheap) - Quick classification
   - Tier 2: Claude (deep) - Collectible analysis

2. **Auto-Fill**
   - Title, description, brand, size, color
   - Price suggestions
   - Condition detection
   - Item type classification

3. **Market Analysis**
   - Sell-through rate
   - Demand level
   - Days to sell estimate
   - Average sold price
   - Market insights

4. **Collectible Detection**
   - Card vs Collectible vs Standard Item
   - Enhanced scan option (conditional)
   - Database integration
   - Collection storage

### Backend Features
1. **Image Processing**
   - Compression (PIL/Pillow)
   - Format conversion
   - Size optimization
   - Background removal (rembg)

2. **AI Integration**
   - GeminiClassifier (Tier 1)
   - EnhancedScanner (Tier 2)
   - Photo object handling
   - Error handling

3. **Database Integration**
   - Public collectibles database
   - User collection storage
   - Activity logging
   - Card/collectible routing

---

## Related Files

### Frontend
- `templates/create.html` - Main implementation
- `image-flow-standalone.html` - Standalone version (reference)

### Backend
- `routes_main.py` - API endpoints
- `src/ai/gemini_classifier.py` - Tier 1 AI
- `src/collectibles/enhanced_scanner.py` - Tier 2 AI
- `src/enhancer/ai_enhancer.py` - AI enhancement system

### Dependencies
- Cropper.js (photo cropping)
- rembg (background removal)
- PIL/Pillow (image processing)
- Google Gemini API
- Anthropic Claude API

---

## Notes for Comparison

When comparing with the older version (~150 commits earlier), check for:

1. **Architecture Changes**
   - Two-tier system implementation
   - Enhanced scanner integration
   - Database routing logic

2. **UI/UX Improvements**
   - Photo editor modal design
   - Zoom functionality
   - Loading states
   - Error handling

3. **Performance Optimizations**
   - Image compression
   - Lazy loading
   - Timeout handling
   - Error recovery

4. **Feature Additions**
   - Background removal
   - Market analysis
   - Collection storage
   - Public database integration

5. **Code Quality**
   - Error handling
   - Code organization
   - API consistency
   - User feedback

---

**End of Snapshot**

