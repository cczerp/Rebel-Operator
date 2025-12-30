========================================
IMAGE FLOW & AI ANALYZER SNAPSHOT
========================================
Date: Current Branch
Purpose: Complete snapshot for comparison with older version (~150 commits earlier)

FILES IN THIS SNAPSHOT:
========================

01_frontend_image_flow_javascript.txt
- Photo upload handler
- Photo editor functions (crop, background removal)
- Photo management (delete, zoom, preview)
- Photo state management

02_frontend_ai_analysis_javascript.txt
- Two-tier AI analysis system
- Tier 1: Quick Analysis (Gemini)
- Tier 2: Enhanced Scanner (Claude)
- Result display and form auto-fill
- Collection storage functions

03_frontend_html_css.txt
- Photo upload UI HTML
- Photo editor modal HTML
- Image zoom modal HTML
- CSS styles for photo previews and modals

04_backend_photo_upload_api.txt
- Photo upload endpoint
- Image compression logic
- File validation
- Upload directory management

05_backend_photo_edit_api.txt
- Photo editing endpoint
- Crop functionality
- Background removal (rembg)
- Image format conversion

06_backend_ai_analyze_api.txt
- Tier 1 API endpoint (/api/analyze)
- Gemini classifier integration
- Quick analysis response

07_backend_enhanced_scan_api.txt
- Tier 2 API endpoint (/api/enhanced-scan)
- Enhanced scanner integration
- Database storage
- Card vs Collectible routing

08_ai_image_format_conversion.txt
- Claude format conversion logic
- WebP/HEIC to JPEG conversion
- MIME type handling
- Format compatibility

09_ai_gemini_classifier.txt
- Gemini classifier overview
- Return data structure
- Key features

10_ai_claude_analysis.txt
- Claude analysis overview
- Collectible vs Card detection
- Return data structures
- Key features

ARCHITECTURE OVERVIEW:
======================

FRONTEND FLOW:
1. User uploads photos → handlePhotoSelect()
2. Photos displayed with preview thumbnails
3. User clicks "Analyze with AI" → Tier 1 (Gemini)
4. If collectible detected → Enhanced Scan option shown
5. User clicks "Enhanced Scan" → Tier 2 (Claude)
6. Results displayed and form auto-filled

BACKEND FLOW:
1. /api/upload-photos → Compress and save images
2. /api/analyze → Gemini quick classification
3. /api/enhanced-scan → Claude deep analysis
4. Results saved to database
5. Response sent back to frontend

IMAGE PROCESSING:
- Upload: Compress to max 2MB, resize to 2048px
- Edit: Crop, background removal
- AI: Convert to JPEG/PNG/GIF for Claude compatibility

KEY FEATURES:
=============
- Two-tier AI system (fast Gemini + deep Claude)
- Photo editing (crop, background removal)
- Image format conversion for Claude
- Market analysis integration
- Collection storage
- Form auto-fill from AI results

COMPARISON NOTES:
=================
When comparing with older version, check:
- Image format handling (WebP/HEIC support)
- Claude format conversion implementation
- Two-tier system architecture
- API endpoint structure
- Frontend state management
- Error handling improvements

