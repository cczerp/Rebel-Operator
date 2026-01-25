"""
eBay Search Module
==================
Provides eBay item search functionality using the Buy API.

Includes result normalization, pagination, and filtering.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, List, Optional, Any
from .ebay_auth import get_ebay_token


# eBay condition ID mappings
EBAY_CONDITION_IDS = {
    "new": "1000",
    "used": "3000",
    "new_other": "1500",
    "new_with_defects": "1750",
    "manufacturer_refurbished": "2000",
    "seller_refurbished": "2500",
    "for_parts_or_not_working": "7000",
    "new_with_tags": "1000",  # Alias
    "pre_owned": "3000"  # Alias
}

# Create session with retry strategy for search requests
_ebay_search_session = None

def _get_ebay_search_session():
    """Get or create eBay search session with retry configuration."""
    global _ebay_search_session
    if _ebay_search_session is None:
        _ebay_search_session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]  # Only retry GET for search requests
        )
        adapter = HTTPAdapter(max_retries=retry)
        _ebay_search_session.mount("https://", adapter)
    return _ebay_search_session


def search_ebay(
    query: str,
    limit: int = 10,
    offset: int = 0,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    condition: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search eBay for items using the Buy Browse API with pagination and filters.

    Args:
        query: Search query string
        limit: Maximum number of results (1-200, default 10)
        offset: Number of results to skip (default 0)
        min_price: Minimum price filter
        max_price: Maximum price filter
        condition: Condition filter ("new", "used", etc.)

    Returns:
        Dict containing search results with normalized items

    Raises:
        requests.RequestException: If API request fails
        ValueError: If query is empty or parameters invalid
    """
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty")

    token = get_ebay_token()

    params = {
        "q": query.strip(),
        "limit": min(max(limit, 1), 200),  # Clamp between 1-200
        "offset": max(offset, 0)
    }

    # Add price filter
    if min_price is not None or max_price is not None:
        price_filter = ""
        if min_price is not None:
            price_filter += f"{min_price}"
        price_filter += ".."
        if max_price is not None:
            price_filter += f"{max_price}"
        params["price"] = price_filter

    # Add condition filter
    if condition:
        condition_id = EBAY_CONDITION_IDS.get(condition.lower())
        if condition_id:
            params["filter"] = f"conditionIds:{{{condition_id}}}"
        else:
            # If condition not recognized, try to use it directly as ID
            try:
                int(condition)  # Validate it's numeric
                params["filter"] = f"conditionIds:{{{condition}}}"
            except ValueError:
                raise ValueError(f"Invalid condition: {condition}. Use 'new', 'used', or condition ID.")

    response = _get_ebay_search_session().get(
        "https://api.ebay.com/buy/browse/v1/item_summary/search",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=10
    )

    response.raise_for_status()
    data = response.json()

    # Normalize results
    normalized_items = []
    if "itemSummaries" in data:
        for item in data["itemSummaries"]:
            normalized_items.append(normalize_ebay_item(item))

    # Add pagination info
    result = {
        "query": query,
        "total": data.get("total", 0),
        "limit": limit,
        "offset": offset,
        "items": normalized_items,
        "raw_response": data  # Keep raw data for debugging
    }

    # Add next page URL if more results available
    if data.get("total", 0) > offset + limit:
        result["next_offset"] = offset + limit

    return result


def normalize_ebay_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize eBay item data to canonical format.

    Args:
        item: Raw eBay item data from API

    Returns:
        Dict with standardized item structure
    """
    # Extract price information
    price_info = item.get("price", {})
    price = float(price_info.get("value", 0)) if price_info.get("value") else None
    currency = price_info.get("currency", "USD")

    # Extract shipping cost
    shipping_cost = None
    shipping_options = item.get("shippingOptions", [])
    if shipping_options and len(shipping_options) > 0:
        shipping_cost_info = shipping_options[0].get("shippingCost", {})
        if shipping_cost_info.get("value"):
            shipping_cost = float(shipping_cost_info["value"])

    # Extract image URL
    image_url = None
    image_info = item.get("image")
    if image_info and isinstance(image_info, dict):
        image_url = image_info.get("imageUrl")
    elif image_info and isinstance(image_info, str):
        image_url = image_info

    # Extract location
    location = None
    item_location = item.get("itemLocation", {})
    if isinstance(item_location, dict):
        # Try different location fields
        location = (
            item_location.get("country") or
            item_location.get("city") or
            item_location.get("postalCode") or
            str(item_location)
        )

    return {
        "platform": "ebay",
        "platform_item_id": item.get("itemId"),
        "title": item.get("title", ""),
        "price": price,
        "currency": currency,
        "condition": item.get("condition"),
        "image": image_url,
        "url": item.get("itemWebUrl"),
        "seller": item.get("seller", {}).get("username") if item.get("seller") else None,
        "location": location,
        "shipping_cost": shipping_cost,
        # Additional eBay-specific fields
        "item_id": item.get("itemId"),
        "category_id": item.get("categoryId"),
        "buying_options": item.get("buyingOptions", []),
        "item_group_type": item.get("itemGroupType"),
        "adult_only": item.get("adultOnly", False)
    }