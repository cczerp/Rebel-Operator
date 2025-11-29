"""
Platform Tracker
===============
Tracks per-platform status and errors
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from ..database import get_db


class PlatformTracker:
    """Tracks listing status across platforms"""
    
    def __init__(self):
        self.db = get_db()
    
    def get_platform_status(self, listing_id: int) -> Dict[str, Any]:
        """Get status for all platforms for a listing"""
        platform_listings = self.db.get_platform_listings(listing_id)
        
        return {
            pl['platform']: {
                'status': pl['status'],
                'platform_listing_id': pl['platform_listing_id'],
                'platform_url': pl['platform_url'],
                'error_message': pl.get('error_message'),
                'retry_count': pl.get('retry_count', 0),
                'last_synced': pl.get('last_synced'),
                'posted_at': pl.get('posted_at')
            }
            for pl in platform_listings
        }
    
    def get_active_platforms(self, listing_id: int) -> List[str]:
        """Get list of platforms where listing is active"""
        platform_listings = self.db.get_platform_listings(listing_id)
        return [
            pl['platform']
            for pl in platform_listings
            if pl['status'] == 'active'
        ]
    
    def get_failed_platforms(self, listing_id: int) -> List[Dict[str, Any]]:
        """Get list of platforms where listing failed"""
        platform_listings = self.db.get_platform_listings(listing_id)
        return [
            {
                'platform': pl['platform'],
                'error_message': pl.get('error_message'),
                'retry_count': pl.get('retry_count', 0)
            }
            for pl in platform_listings
            if pl['status'] == 'failed'
        ]
    
    def track_error(
        self,
        listing_id: int,
        platform: str,
        error_message: str
    ):
        """Track an error for a platform listing"""
        self.db.update_platform_listing_status(
            listing_id=listing_id,
            platform=platform,
            status='failed',
            error_message=error_message
        )
    
    def get_listings_by_platform(
        self,
        platform: str,
        status: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all listings for a platform"""
        cursor = self.db._get_cursor()
        
        query = """
            SELECT l.*, pl.platform_listing_id, pl.platform_url, pl.status as platform_status
            FROM listings l
            JOIN platform_listings pl ON l.id = pl.listing_id
            WHERE pl.platform = %s
        """
        params = [platform]
        
        if status:
            query += " AND pl.status = %s"
            params.append(status)
        
        if user_id:
            query += " AND l.user_id = %s"
            params.append(user_id)
        
        query += " ORDER BY l.created_at DESC"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

