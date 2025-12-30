"""
Cross-Site SEO Synchronization
==============================
Auto-update SEO metadata across all platforms
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from ..database import get_db
from ..listing_manager import ListingManager
from ..workers import JobQueue, JobPriority


class SEOSynchronizer:
    """
    Synchronizes SEO metadata across all platforms.
    
    When SEO is updated on one platform, automatically updates all others.
    """
    
    def __init__(self):
        self.db = get_db()
        self.listing_manager = ListingManager()
        self.job_queue = JobQueue()
    
    def update_seo(
        self,
        listing_id: int,
        seo_data: Dict[str, Any],
        sync_to_all_platforms: bool = True
    ) -> Dict[str, Any]:
        """
        Update SEO data for a listing and sync to all platforms.
        
        Args:
            listing_id: Listing ID
            seo_data: Dict with SEO fields (title, description, keywords, etc.)
            sync_to_all_platforms: If True, sync to all active platforms
        
        Returns:
            Results for each platform
        """
        listing = self.db.get_listing(listing_id)
        if not listing:
            raise ValueError(f"Listing {listing_id} not found")
        
        # Update listing SEO in database
        # TODO: Store SEO data in listings table or separate SEO table
        
        results = {}
        
        if sync_to_all_platforms:
            # Get active platforms
            from ..listing_manager import PlatformTracker
            tracker = PlatformTracker()
            active_platforms = tracker.get_active_platforms(listing_id)
            
            # Sync SEO to all platforms
            for platform in active_platforms:
                try:
                    result = self._sync_seo_to_platform(
                        listing_id=listing_id,
                        platform=platform,
                        seo_data=seo_data
                    )
                    results[platform] = result
                except Exception as e:
                    results[platform] = {
                        'status': 'failed',
                        'error': str(e)
                    }
        else:
            results['database'] = {'status': 'updated'}
        
        return results
    
    def _sync_seo_to_platform(
        self,
        listing_id: int,
        platform: str,
        seo_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sync SEO data to a specific platform"""
        # Get platform listing
        platform_listings = self.db.get_platform_listings(listing_id)
        platform_listing = next(
            (pl for pl in platform_listings if pl['platform'] == platform),
            None
        )
        
        if not platform_listing:
            return {'status': 'not_found'}
        
        # Update SEO on platform
        # TODO: Integrate with platform adapters to update SEO
        # For now, queue a job
        self.job_queue.enqueue(
            job_type='update_seo',
            payload={
                'listing_id': listing_id,
                'platform': platform,
                'seo_data': seo_data
            },
            priority=JobPriority.NORMAL
        )
        
        return {'status': 'queued'}
    
    def auto_sync_seo_on_edit(
        self,
        listing_id: int,
        updated_fields: Dict[str, Any]
    ):
        """
        Automatically sync SEO when listing is edited.
        
        This is called when a listing's title, description, or other SEO-relevant
        fields are updated.
        """
        seo_fields = ['title', 'description', 'category']
        
        if any(field in updated_fields for field in seo_fields):
            # Extract SEO data from updated fields
            seo_data = {
                'title': updated_fields.get('title'),
                'description': updated_fields.get('description'),
                'category': updated_fields.get('category')
            }
            
            # Queue SEO sync job
            self.job_queue.enqueue(
                job_type='sync_seo',
                payload={
                    'listing_id': listing_id,
                    'seo_data': seo_data
                },
                priority=JobPriority.HIGH
            )
    
    def bulk_sync_seo(
        self,
        listing_ids: List[int],
        seo_updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Bulk sync SEO for multiple listings"""
        results = {
            'succeeded': [],
            'failed': [],
            'errors': []
        }
        
        for listing_id in listing_ids:
            try:
                result = self.update_seo(listing_id, seo_updates)
                results['succeeded'].append({
                    'listing_id': listing_id,
                    'platforms': result
                })
            except Exception as e:
                results['failed'].append(listing_id)
                results['errors'].append({
                    'listing_id': listing_id,
                    'error': str(e)
                })
        
        return results

