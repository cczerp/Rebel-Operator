"""
Platform Configuration for Rebel Operator
Defines all supported platforms with their credential requirements and CSV mappings
"""

PLATFORM_CREDENTIALS_CONFIG = {
    # Marketplace Platforms
    "ebay": {
        "name": "eBay",
        "icon": "fas fa-gavel",
        "color": "primary",
        "category": "marketplace",
        "supports_api": True,
        "supports_csv": True,
        "credentials": {
            "api_key": {"required": True, "label": "API Key"},
            "username": {"required": False, "label": "Username"},
            "password": {"required": False, "label": "Password"}
        }
    },
    "mercari": {
        "name": "Mercari",
        "icon": "fas fa-store",
        "color": "info",
        "category": "marketplace",
        "supports_api": True,
        "supports_csv": True,
        "credentials": {
            "api_key": {"required": False, "label": "API Key"},
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "poshmark": {
        "name": "Poshmark",
        "icon": "fas fa-shopping-bag",
        "color": "danger",
        "category": "fashion",
        "supports_api": False,
        "supports_csv": True,
        "credentials": {
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "discogs": {
        "name": "Discogs",
        "icon": "fas fa-compact-disc",
        "color": "dark",
        "category": "collectibles",
        "supports_api": True,
        "supports_csv": True,
        "credentials": {
            "api_key": {"required": True, "label": "Personal Access Token"},
            "username": {"required": True, "label": "Username"}
        }
    },
    "etsy": {
        "name": "Etsy",
        "icon": "fas fa-shopping-bag",
        "color": "warning",
        "category": "marketplace",
        "supports_api": True,
        "supports_csv": True,
        "credentials": {
            "api_key": {"required": True, "label": "API Key"},
            "shop_id": {"required": True, "label": "Shop ID"},
            "username": {"required": False, "label": "Username"},
            "password": {"required": False, "label": "Password"}
        }
    },
    "offerup": {
        "name": "OfferUp",
        "icon": "fas fa-tags",
        "color": "success",
        "category": "marketplace",
        "supports_api": False,
        "supports_csv": True,
        "credentials": {
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "depop": {
        "name": "Depop",
        "icon": "fas fa-tshirt",
        "color": "danger",
        "category": "fashion",
        "supports_api": True,
        "supports_csv": True,
        "credentials": {
            "api_key": {"required": False, "label": "API Key"},
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "grailed": {
        "name": "Grailed",
        "icon": "fas fa-user-tie",
        "color": "dark",
        "category": "fashion",
        "supports_api": False,
        "supports_csv": True,
        "credentials": {
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "vinted": {
        "name": "Vinted",
        "icon": "fas fa-recycle",
        "color": "info",
        "category": "fashion",
        "supports_api": False,
        "supports_csv": True,
        "credentials": {
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "bonanza": {
        "name": "Bonanza",
        "icon": "fas fa-gem",
        "color": "warning",
        "category": "marketplace",
        "supports_api": True,
        "supports_csv": True,
        "credentials": {
            "api_key": {"required": True, "label": "API Key"},
            "api_secret": {"required": True, "label": "API Secret"},
            "username": {"required": False, "label": "Username"},
            "password": {"required": False, "label": "Password"}
        }
    },
    "5miles": {
        "name": "5miles",
        "icon": "fas fa-map-marker-alt",
        "color": "success",
        "category": "local",
        "supports_api": False,
        "supports_csv": False,
        "credentials": {
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "varagesale": {
        "name": "VarageSale",
        "icon": "fas fa-handshake",
        "color": "info",
        "category": "local",
        "supports_api": False,
        "supports_csv": False,
        "credentials": {
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "tcgplayer": {
        "name": "TCGplayer",
        "icon": "fas fa-dice-d20",
        "color": "primary",
        "category": "cards",
        "supports_api": True,
        "supports_csv": True,
        "credentials": {
            "api_key": {"required": True, "label": "API Key"},
            "username": {"required": False, "label": "Username"},
            "password": {"required": False, "label": "Password"}
        }
    },
    "cardmarket": {
        "name": "Cardmarket (EU)",
        "icon": "fas fa-globe-europe",
        "color": "primary",
        "category": "cards",
        "supports_api": True,
        "supports_csv": True,
        "credentials": {
            "api_key": {"required": True, "label": "API Key"},
            "username": {"required": False, "label": "Username"},
            "password": {"required": False, "label": "Password"}
        }
    },
    "whatnot": {
        "name": "Whatnot",
        "icon": "fas fa-video",
        "color": "danger",
        "category": "cards",
        "supports_api": False,
        "supports_csv": False,
        "credentials": {
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "comc": {
        "name": "COMC",
        "icon": "fas fa-baseball-ball",
        "color": "info",
        "category": "cards",
        "supports_api": True,
        "supports_csv": True,
        "credentials": {
            "api_key": {"required": False, "label": "API Key"},
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "pwcc": {
        "name": "PWCC",
        "icon": "fas fa-trophy",
        "color": "warning",
        "category": "cards",
        "supports_api": False,
        "supports_csv": True,
        "credentials": {
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "ebid": {
        "name": "eBid",
        "icon": "fas fa-gavel",
        "color": "primary",
        "category": "marketplace",
        "supports_api": False,
        "supports_csv": True,
        "credentials": {
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "myslabs": {
        "name": "MySlabs",
        "icon": "fas fa-certificate",
        "color": "info",
        "category": "cards",
        "supports_api": True,
        "supports_csv": True,
        "credentials": {
            "api_key": {"required": False, "label": "API Key"},
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "alt": {
        "name": "Alt",
        "icon": "fas fa-exchange-alt",
        "color": "primary",
        "category": "cards",
        "supports_api": True,
        "supports_csv": False,
        "credentials": {
            "api_key": {"required": False, "label": "API Key"},
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "stockx": {
        "name": "StockX (cards + sealed)",
        "icon": "fas fa-chart-line",
        "color": "success",
        "category": "cards",
        "supports_api": True,
        "supports_csv": False,
        "credentials": {
            "api_key": {"required": False, "label": "API Key"},
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "goldin": {
        "name": "Goldin (auction sync)",
        "icon": "fas fa-hammer",
        "color": "warning",
        "category": "cards",
        "supports_api": False,
        "supports_csv": True,
        "credentials": {
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "therealreal": {
        "name": "The RealReal",
        "icon": "fas fa-gem",
        "color": "dark",
        "category": "luxury",
        "supports_api": False,
        "supports_csv": True,
        "credentials": {
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "vestiaire": {
        "name": "Vestiaire Collective",
        "icon": "fas fa-crown",
        "color": "warning",
        "category": "luxury",
        "supports_api": False,
        "supports_csv": True,
        "credentials": {
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "tradesy": {
        "name": "Tradesy",
        "icon": "fas fa-shopping-bag",
        "color": "info",
        "category": "luxury",
        "supports_api": False,
        "supports_csv": True,
        "credentials": {
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "rebag": {
        "name": "Rebag",
        "icon": "fas fa-handbag",
        "color": "danger",
        "category": "luxury",
        "supports_api": False,
        "supports_csv": True,
        "credentials": {
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "thredup": {
        "name": "ThredUp",
        "icon": "fas fa-recycle",
        "color": "success",
        "category": "fashion",
        "supports_api": True,
        "supports_csv": True,
        "credentials": {
            "api_key": {"required": False, "label": "API Key (limited)"},
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "chairish": {
        "name": "Chairish (home + vintage)",
        "icon": "fas fa-couch",
        "color": "warning",
        "category": "home",
        "supports_api": False,
        "supports_csv": True,
        "credentials": {
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "craigslist": {
        "name": "Craigslist",
        "icon": "fas fa-list",
        "color": "info",
        "category": "local",
        "supports_api": False,
        "supports_csv": False,
        "credentials": {
            "username": {"required": True, "label": "Username/Email"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "nextdoor": {
        "name": "Nextdoor",
        "icon": "fas fa-home",
        "color": "success",
        "category": "local",
        "supports_api": False,
        "supports_csv": False,
        "credentials": {
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "facebook": {
        "name": "Facebook Marketplace",
        "icon": "fab fa-facebook",
        "color": "primary",
        "category": "local",
        "supports_api": True,
        "supports_csv": False,
        "credentials": {
            "api_key": {"required": False, "label": "Access Token"},
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "shopify": {
        "name": "Shopify",
        "icon": "fas fa-shopping-cart",
        "color": "success",
        "category": "ecommerce",
        "supports_api": True,
        "supports_csv": True,
        "credentials": {
            "api_key": {"required": True, "label": "Access Token"},
            "store_url": {"required": True, "label": "Store URL"},
            "username": {"required": False, "label": "Username"},
            "password": {"required": False, "label": "Password"}
        }
    },
    "woocommerce": {
        "name": "WooCommerce",
        "icon": "fab fa-wordpress",
        "color": "primary",
        "category": "ecommerce",
        "supports_api": True,
        "supports_csv": True,
        "credentials": {
            "api_key": {"required": True, "label": "Consumer Key"},
            "api_secret": {"required": True, "label": "Consumer Secret"},
            "store_url": {"required": True, "label": "Store URL"},
            "username": {"required": False, "label": "Username"},
            "password": {"required": False, "label": "Password"}
        }
    },
    "squarespace": {
        "name": "Squarespace Commerce",
        "icon": "fas fa-square",
        "color": "dark",
        "category": "ecommerce",
        "supports_api": True,
        "supports_csv": True,
        "credentials": {
            "api_key": {"required": True, "label": "API Key"},
            "username": {"required": False, "label": "Username"},
            "password": {"required": False, "label": "Password"}
        }
    },
    "bigcommerce": {
        "name": "BigCommerce",
        "icon": "fas fa-store",
        "color": "info",
        "category": "ecommerce",
        "supports_api": True,
        "supports_csv": True,
        "credentials": {
            "api_key": {"required": True, "label": "Access Token"},
            "store_hash": {"required": True, "label": "Store Hash"},
            "username": {"required": False, "label": "Username"},
            "password": {"required": False, "label": "Password"}
        }
    },
    "ecwid": {
        "name": "Ecwid",
        "icon": "fas fa-shopping-basket",
        "color": "success",
        "category": "ecommerce",
        "supports_api": True,
        "supports_csv": True,
        "credentials": {
            "api_key": {"required": True, "label": "API Token"},
            "store_id": {"required": True, "label": "Store ID"},
            "username": {"required": False, "label": "Username"},
            "password": {"required": False, "label": "Password"}
        }
    },
    "rakuten": {
        "name": "Rakuten",
        "icon": "fas fa-yen-sign",
        "color": "danger",
        "category": "international",
        "supports_api": True,
        "supports_csv": True,
        "credentials": {
            "api_key": {"required": False, "label": "API Key"},
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "buyee": {
        "name": "Buyee",
        "icon": "fas fa-shopping-cart",
        "color": "warning",
        "category": "international",
        "supports_api": False,
        "supports_csv": False,
        "credentials": {
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "allegro": {
        "name": "Allegro",
        "icon": "fas fa-tags",
        "color": "danger",
        "category": "international",
        "supports_api": True,
        "supports_csv": True,
        "credentials": {
            "api_key": {"required": False, "label": "API Key"},
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "leboncoin": {
        "name": "Leboncoin",
        "icon": "fas fa-euro-sign",
        "color": "warning",
        "category": "international",
        "supports_api": False,
        "supports_csv": False,
        "credentials": {
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "carousell": {
        "name": "Carousell",
        "icon": "fas fa-circle",
        "color": "danger",
        "category": "international",
        "supports_api": False,
        "supports_csv": True,
        "credentials": {
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    },
    "shopee": {
        "name": "Shopee",
        "icon": "fas fa-shopping-bag",
        "color": "warning",
        "category": "international",
        "supports_api": True,
        "supports_csv": True,
        "credentials": {
            "api_key": {"required": False, "label": "API Key"},
            "username": {"required": True, "label": "Username"},
            "password": {"required": True, "label": "Password"}
        }
    }
}

# Platform capabilities registry
PLATFORM_CAPABILITIES = {
    "ebay": {
        "search": "platform_api",
        "auth": "app_only"
    },
    "etsy": {
        "search": "platform_api",
        "auth": "app_only"
    },
    "mercari": {
        "search": "blocked",
        "reason": "no_public_api"
    },
    "poshmark": {
        "search": "web_scraping",
        "auth": "user_credentials"
    },
    "facebook_marketplace": {
        "search": "web_scraping",
        "auth": "user_credentials"
    },
    "offerup": {
        "search": "web_scraping",
        "auth": "user_credentials"
    },
    "depop": {
        "search": "web_scraping",
        "auth": "user_credentials"
    }
}

# Platform categories for organization
PLATFORM_CATEGORIES = {
    "marketplace": "General Marketplaces",
    "fashion": "Fashion & Apparel",
    "luxury": "Luxury & Designer",
    "cards": "Trading Cards & Collectibles",
    "ecommerce": "E-Commerce Platforms",
    "local": "Local & Community",
    "home": "Home & Furniture",
    "international": "International Platforms"
}

# Get all valid platform keys
VALID_PLATFORMS = list(PLATFORM_CREDENTIALS_CONFIG.keys())
