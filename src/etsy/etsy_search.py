"""
Etsy Search Module
==================
Provides Etsy item search functionality using the Etsy API.

Includes result normalization, pagination, and filtering.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, List, Optional, Any
from .etsy_auth import get_etsy_token


# Create session with retry strategy for search requests
_etsy_search_session = None

def _get_etsy_search_session():
    """Get or create Etsy search session with retry configuration."""
    global _etsy_search_session
    if _etsy_search_session is None:
        _etsy_search_session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]  # Only retry GET for search requests
        )
        adapter = HTTPAdapter(max_retries=retry)
        _etsy_search_session.mount("https://", adapter)
    return _etsy_search_session


def search_etsy(
    query: str,
    limit: int = 10,
    offset: int = 0,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
) -> Dict[str, Any]:
    """
    Search Etsy for items using the Etsy API.

    Args:
        query: Search query string
        limit: Maximum number of results (1-100, default 10)
        offset: Number of results to skip (default 0)
        min_price: Minimum price filter
        max_price: Maximum price filter

    Returns:
        Dict containing search results with normalized items

    Raises:
        requests.RequestException: If API request fails
        ValueError: If query is empty or parameters invalid
    """
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty")

    api_key = get_etsy_token()

    params = {
        "keywords": query.strip(),
        "limit": min(max(limit, 1), 100),  # Clamp between 1-100
        "offset": max(offset, 0)
    }

    # Add price filters if provided
    if min_price is not None:
        params["min_price"] = max(min_price, 0)
    if max_price is not None:
        params["max_price"] = max(max_price, 0)

    response = _get_etsy_search_session().get(
        "https://openapi.etsy.com/v3/application/listings/active",
        headers={"x-api-key": api_key},
        params=params,
        timeout=10
    )

    response.raise_for_status()
    data = response.json()

    # Normalize results
    normalized_items = []
    if "results" in data:
        for item in data["results"]:
            normalized_items.append(normalize_etsy_item(item))

    # Add pagination info
    result = {
        "query": query,
        "total": data.get("count", 0),
        "limit": limit,
        "offset": offset,
        "items": normalized_items,
        "raw_response": data  # Keep raw data for debugging
    }

    # Add next page URL if more results available
    if data.get("count", 0) > offset + limit:
        result["next_offset"] = offset + limit

    return result


def normalize_etsy_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize Etsy item data to canonical format.

    Args:
        item: Raw Etsy item data from API

    Returns:
        Dict with standardized item structure
    """
    # Extract price information (Etsy uses cents)
    price = None
    currency = "USD"  # Etsy primarily uses USD

    if "price" in item and item["price"] is not None:
        # Etsy price is in cents, convert to dollars
        price = float(item["price"]["amount"]) / 100

    # Extract image URL
    image_url = None
    if "images" in item and item["images"] and len(item["images"]) > 0:
        image_url = item["images"][0].get("url_570xN") or item["images"][0].get("url_fullxfull")

    return {
        "platform": "etsy",
        "platform_item_id": str(item.get("listing_id")),
        "title": item.get("title", ""),
        "price": price,
        "currency": currency,
        "condition": None,  # Etsy doesn't have condition like eBay
        "image": image_url,
        "url": item.get("url"),
        "seller": item.get("shop_name") or item.get("user_id"),
        "location": None,  # Etsy doesn't expose seller location in basic API
        "shipping_cost": None,  # Would need additional API calls
        # Additional Etsy-specific fields
        "listing_id": item.get("listing_id"),
        "shop_id": item.get("shop_id"),
        "user_id": item.get("user_id"),
        "shop_name": item.get("shop_name"),
        "is_digital": item.get("is_digital", False),
        "state": item.get("state"),
        "category_id": item.get("category_id")
    }