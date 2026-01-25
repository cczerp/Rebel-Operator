"""
Etsy Integration Module
=======================
Handles Etsy API integrations.
"""

from .etsy_auth import get_etsy_token
from .etsy_search import search_etsy, normalize_etsy_item

__all__ = [
    'get_etsy_token',
    'search_etsy',
    'normalize_etsy_item',
]