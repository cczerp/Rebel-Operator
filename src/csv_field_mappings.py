"""
CSV Field Mappings for Platform-Specific Uploads
Maps Rebel Operator fields to platform-specific CSV column names
"""

# Standard Rebel Operator fields
REBEL_OPERATOR_FIELDS = [
    'title', 'description', 'price', 'cost', 'condition', 'item_type',
    'brand', 'size', 'color', 'shipping_cost', 'quantity', 'sku',
    'weight', 'category', 'photos', 'created_at', 'updated_at'
]

# Platform-specific CSV field mappings
CSV_FIELD_MAPPINGS = {
    "ebay": {
        "title": "Title",
        "description": "Description",
        "price": "StartPrice",
        "condition": "ConditionID",
        "brand": "Brand",
        "category": "Category",
        "photos": "PicURL",
        "quantity": "Quantity",
        "sku": "CustomLabel",
        "shipping_cost": "ShippingCost",
        "weight": "WeightMajor"
    },
    "mercari": {
        "title": "Title",
        "description": "Description",
        "price": "Price",
        "condition": "Condition",
        "brand": "Brand",
        "category": "Category",
        "photos": "Photo",
        "shipping_cost": "ShippingCost",
        "color": "Color",
        "size": "Size"
    },
    "poshmark": {
        "title": "Title",
        "description": "Description",
        "price": "Price",
        "condition": "Condition",
        "brand": "Brand",
        "category": "Category",
        "size": "Size",
        "color": "Color",
        "photos": "Image",
        "image1": "Image1",
        "image2": "Image2",
        "image3": "Image3",
        "image4": "Image4",
        "image5": "Image5",
        "image6": "Image6",
        "image7": "Image7",
        "image8": "Image8"
    },
    "etsy": {
        "title": "Title",
        "description": "Description",
        "price": "Price",
        "quantity": "Quantity",
        "sku": "SKU",
        "category": "Category",
        "photos": "Image1",
        "tags": "Tags",
        "materials": "Materials",
        "shipping_cost": "ShippingCost"
    },
    "offerup": {
        "title": "Title",
        "description": "Description",
        "price": "Price",
        "condition": "Condition",
        "category": "Category",
        "photos": "Photo",
        "location": "Location"
    },
    "depop": {
        "title": "Title",
        "description": "Description",
        "price": "Price",
        "brand": "Brand",
        "category": "Category",
        "size": "Size",
        "color": "Color",
        "condition": "Condition",
        "photos": "Image"
    },
    "grailed": {
        "title": "Title",
        "description": "Description",
        "price": "Price",
        "brand": "Brand",
        "category": "Category",
        "size": "Size",
        "condition": "Condition",
        "photos": "Photos",
        "designer": "Designer"
    },
    "vinted": {
        "title": "Title",
        "description": "Description",
        "price": "Price",
        "brand": "Brand",
        "size": "Size",
        "condition": "Condition",
        "category": "Category",
        "color": "Color",
        "photos": "Photo"
    },
    "bonanza": {
        "title": "Title",
        "description": "Description",
        "price": "Price",
        "quantity": "Quantity",
        "condition": "Condition",
        "sku": "SKU",
        "upc": "UPC",
        "category": "Category",
        "image_url_1": "Image1",
        "image_url_2": "Image2",
        "image_url_3": "Image3",
        "image_url_4": "Image4",
        "image_url_5": "Image5",
        "image_url_6": "Image6",
        "image_url_7": "Image7",
        "image_url_8": "Image8"
    },
    "tcgplayer": {
        "title": "Product Name",
        "quantity": "Quantity",
        "price": "Price",
        "condition": "Condition",
        "language": "Language",
        "sku": "SKU",
        "card_number": "Card Number",
        "set_name": "Set Name",
        "rarity": "Rarity",
        "photos": "Image"
    },
    "cardmarket": {
        "title": "Name",
        "quantity": "Amount",
        "price": "Price",
        "condition": "Condition",
        "language": "Language",
        "foil": "Foil",
        "signed": "Signed",
        "altered": "Altered",
        "comments": "Comments"
    },
    "comc": {
        "title": "Title",
        "description": "Description",
        "price": "Price",
        "quantity": "Quantity",
        "condition": "Condition",
        "year": "Year",
        "sport": "Sport",
        "player": "Player",
        "team": "Team",
        "card_number": "CardNumber",
        "photos": "Image"
    },
    "pwcc": {
        "title": "Title",
        "description": "Description",
        "price": "Reserve Price",
        "condition": "Condition",
        "year": "Year",
        "sport": "Sport",
        "photos": "Image",
        "certification": "Certification"
    },
    "ebid": {
        "title": "Title",
        "description": "Description",
        "price": "StartPrice",
        "quantity": "Quantity",
        "category": "Category",
        "photos": "Image",
        "shipping_cost": "ShippingCost"
    },
    "myslabs": {
        "title": "Card Name",
        "description": "Description",
        "price": "Price",
        "condition": "Grade",
        "year": "Year",
        "sport": "Sport",
        "cert_number": "Cert Number",
        "photos": "Image"
    },
    "goldin": {
        "title": "Title",
        "description": "Description",
        "price": "Reserve Price",
        "condition": "Condition",
        "category": "Category",
        "photos": "Image"
    },
    "therealreal": {
        "title": "Title",
        "description": "Description",
        "price": "Price",
        "brand": "Brand",
        "category": "Category",
        "size": "Size",
        "condition": "Condition",
        "material": "Material",
        "color": "Color",
        "photos": "Image"
    },
    "vestiaire": {
        "title": "Title",
        "description": "Description",
        "price": "Price",
        "brand": "Brand",
        "category": "Category",
        "size": "Size",
        "condition": "Condition",
        "color": "Color",
        "material": "Material",
        "photos": "Photos"
    },
    "tradesy": {
        "title": "Title",
        "description": "Description",
        "price": "Price",
        "brand": "Brand",
        "category": "Category",
        "size": "Size",
        "condition": "Condition",
        "color": "Color",
        "photos": "Image"
    },
    "rebag": {
        "title": "Title",
        "description": "Description",
        "price": "Price",
        "brand": "Brand",
        "category": "Category",
        "condition": "Condition",
        "color": "Color",
        "material": "Material",
        "photos": "Image"
    },
    "thredup": {
        "title": "Title",
        "description": "Description",
        "price": "Price",
        "brand": "Brand",
        "category": "Category",
        "size": "Size",
        "condition": "Condition",
        "color": "Color",
        "photos": "Image"
    },
    "chairish": {
        "title": "Title",
        "description": "Description",
        "price": "Price",
        "condition": "Condition",
        "category": "Category",
        "style": "Style",
        "period": "Period",
        "materials": "Materials",
        "dimensions": "Dimensions",
        "photos": "Image"
    },
    "shopify": {
        "title": "Title",
        "description": "Body (HTML)",
        "price": "Variant Price",
        "quantity": "Variant Inventory Qty",
        "sku": "Variant SKU",
        "weight": "Variant Grams",
        "brand": "Vendor",
        "category": "Type",
        "photos": "Image Src",
        "tags": "Tags",
        "published": "Published"
    },
    "woocommerce": {
        "title": "Name",
        "description": "Description",
        "price": "Regular price",
        "quantity": "Stock",
        "sku": "SKU",
        "weight": "Weight (kg)",
        "category": "Categories",
        "photos": "Images",
        "tags": "Tags",
        "published": "Published"
    },
    "squarespace": {
        "title": "Product Name",
        "description": "Description",
        "price": "Price",
        "quantity": "Quantity",
        "sku": "SKU",
        "weight": "Weight",
        "category": "Category",
        "photos": "Image URL",
        "published": "Status"
    },
    "bigcommerce": {
        "title": "Product Name",
        "description": "Product Description",
        "price": "Price",
        "quantity": "Current Stock Level",
        "sku": "Product Code/SKU",
        "weight": "Product Weight",
        "brand": "Brand Name",
        "category": "Category",
        "photos": "Product Image File"
    },
    "ecwid": {
        "title": "Name",
        "description": "Description",
        "price": "Price",
        "quantity": "Quantity in stock",
        "sku": "SKU",
        "weight": "Weight",
        "brand": "Brand",
        "category": "Category",
        "photos": "Image URL"
    },
    "rakuten": {
        "title": "Item Name",
        "description": "Item Description",
        "price": "Item Price",
        "quantity": "Inventory Quantity",
        "sku": "Item Number",
        "category": "Category",
        "photos": "Item Image"
    },
    "allegro": {
        "title": "Name",
        "description": "Description",
        "price": "Price",
        "quantity": "Stock",
        "condition": "Condition",
        "category": "Category",
        "photos": "Images",
        "ean": "EAN"
    },
    "carousell": {
        "title": "Title",
        "description": "Description",
        "price": "Price",
        "condition": "Condition",
        "category": "Category",
        "photos": "Photos",
        "location": "Location"
    },
    "shopee": {
        "title": "Product Name",
        "description": "Description",
        "price": "Price",
        "quantity": "Stock",
        "sku": "SKU",
        "weight": "Weight",
        "category": "Category",
        "brand": "Brand",
        "photos": "Image"
    }
}

# Condition mappings per platform
CONDITION_MAPPINGS = {
    "poshmark": {
        "new": "New with tags",
        "like_new": "Like new",
        "excellent": "Good",
        "good": "Fair",
        "fair": "Poor"
    },
    "ebay": {
        "new": "1000",  # New
        "like_new": "1500",  # New other
        "excellent": "3000",  # Used
        "good": "4000",  # Very Good
        "fair": "5000"  # Good
    },
    "mercari": {
        "new": "New",
        "like_new": "Like New",
        "excellent": "Good",
        "good": "Fair",
        "fair": "Poor"
    },
    "depop": {
        "new": "Brand new",
        "like_new": "Like new",
        "excellent": "Excellent",
        "good": "Good",
        "fair": "Fair"
    },
    "grailed": {
        "new": "New/Never Worn",
        "like_new": "Gently Used",
        "excellent": "Used",
        "good": "Well Worn",
        "fair": "Heavily Used"
    },
    "tcgplayer": {
        "new": "Near Mint",
        "like_new": "Lightly Played",
        "excellent": "Moderately Played",
        "good": "Heavily Played",
        "fair": "Damaged"
    },
    "cardmarket": {
        "new": "Mint",
        "like_new": "Near Mint",
        "excellent": "Excellent",
        "good": "Good",
        "fair": "Light Played"
    }
}

# Category mappings for specific platforms (examples)
CATEGORY_MAPPINGS = {
    "poshmark": {
        "clothing": "Women > Tops",
        "shoes": "Women > Shoes",
        "accessories": "Women > Accessories",
        "home": "Home"
    },
    "etsy": {
        "jewelry": "Jewelry",
        "clothing": "Clothing",
        "home_decor": "Home & Living",
        "art": "Art & Collectibles"
    },
    "ebay": {
        "electronics": "Consumer Electronics",
        "clothing": "Clothing, Shoes & Accessories",
        "collectibles": "Collectibles",
        "sports_cards": "Sports Mem, Cards & Fan Shop"
    }
}

def get_platform_headers(platform: str) -> list:
    """Get CSV headers for a specific platform"""
    if platform not in CSV_FIELD_MAPPINGS:
        return REBEL_OPERATOR_FIELDS

    mapping = CSV_FIELD_MAPPINGS[platform]
    return list(mapping.values())

def map_field_value(platform: str, field: str, value: any) -> any:
    """Map a field value to platform-specific format"""
    # Handle condition mappings
    if field == "condition" and platform in CONDITION_MAPPINGS:
        condition_map = CONDITION_MAPPINGS[platform]
        return condition_map.get(str(value).lower(), value)

    # Handle category mappings
    if field == "category" and platform in CATEGORY_MAPPINGS:
        category_map = CATEGORY_MAPPINGS[platform]
        return category_map.get(str(value).lower(), value)

    return value

def transform_listing_to_platform_csv(listing: dict, platform: str) -> dict:
    """Transform a Rebel Operator listing to platform-specific CSV format"""
    if platform not in CSV_FIELD_MAPPINGS:
        return listing

    mapping = CSV_FIELD_MAPPINGS[platform]
    transformed = {}

    for rebel_field, platform_field in mapping.items():
        if rebel_field in listing:
            value = listing[rebel_field]
            transformed[platform_field] = map_field_value(platform, rebel_field, value)

    return transformed
