"""
Unified Cross-Platform Listing Manager
======================================
Single source of truth for managing listings across all platforms
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from ..database import get_db
from ..schema.unified_listing import UnifiedListing
from .platform_tracker import PlatformTracker


class ListingManager:
    """
    Unified listing manager - single source of truth for all listings.
    
    Features:
    - Track listings across all platforms
    - List everywhere / Delist everywhere / Relist everywhere
    - Per-platform status tracking
    - Error tracking and retry logic
    - Bulk operations
    """
    
    def __init__(self):
        self.db = get_db()
        self.platform_tracker = PlatformTracker()
    
    def create_listing(
        self,
        listing: UnifiedListing,
        user_id: int,
        target_platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new listing and optionally publish to platforms.
        
        Args:
            listing: UnifiedListing object
            user_id: User ID
            target_platforms: List of platforms to publish to (None = all)
        
        Returns:
            Dict with listing_id and platform results
        """
        import uuid
        listing_uuid = str(uuid.uuid4())
        
        # Create listing in database
        listing_id = self.db.create_listing(
            listing_uuid=listing_uuid,
            title=listing.title,
            description=listing.description,
            price=listing.price.amount,
            condition=listing.condition.value,
            photos=[p.url or p.local_path for p in listing.photos],
            user_id=user_id,
            cost=listing.price.cost if hasattr(listing.price, 'cost') else None,
            category=listing.category.name if listing.category else None,
            item_type=listing.item_specifics.item_type if listing.item_specifics else None,
            attributes={
                'brand': listing.item_specifics.brand,
                'size': listing.item_specifics.size,
                'color': listing.item_specifics.color,
            } if listing.item_specifics else None,
            quantity=listing.quantity,
            storage_location=listing.storage_location,
            sku=listing.sku,
            status='draft'
        )
        
        results = {
            'listing_id': listing_id,
            'listing_uuid': listing_uuid,
            'platforms': {}
        }
        
        # If platforms specified, publish immediately
        if target_platforms:
            publish_results = self.publish_to_platforms(
                listing_id=listing_id,
                platforms=target_platforms
            )
            results['platforms'] = publish_results
        
        return results
    
    def publish_to_platforms(
        self,
        listing_id: int,
        platforms: List[str],
        force_update: bool = False
    ) -> Dict[str, Any]:
        """
        Publish listing to specified platforms.
        
        Args:
            listing_id: Listing ID
            platforms: List of platform names
            force_update: If True, update even if already published
        
        Returns:
            Dict with results per platform
        """
        listing = self.db.get_listing(listing_id)
        if not listing:
            raise ValueError(f"Listing {listing_id} not found")
        
        results = {}
        
        for platform in platforms:
            try:
                # Check if already published
                platform_listings = self.db.get_platform_listings(listing_id)
                existing = next(
                    (pl for pl in platform_listings if pl['platform'] == platform),
                    None
                )
                
                if existing and not force_update:
                    results[platform] = {
                        'status': 'already_published',
                        'platform_listing_id': existing['platform_listing_id'],
                        'platform_url': existing['platform_url']
                    }
                    continue
                
                # Publish to platform
                # TODO: Integrate with actual platform adapters
                platform_listing_id = self._publish_to_platform(listing, platform)
                
                # Track platform listing
                self.db.add_platform_listing(
                    listing_id=listing_id,
                    platform=platform,
                    platform_listing_id=platform_listing_id,
                    status='active'
                )
                
                results[platform] = {
                    'status': 'published',
                    'platform_listing_id': platform_listing_id
                }
                
            except Exception as e:
                # Track error
                self.db.add_platform_listing(
                    listing_id=listing_id,
                    platform=platform,
                    status='failed',
                    error_message=str(e)
                )
                
                results[platform] = {
                    'status': 'failed',
                    'error': str(e)
                }
        
        # Update listing status to active if at least one platform succeeded
        if any(r.get('status') == 'published' for r in results.values()):
            self.db.update_listing_status(listing_id, 'active')
        
        return results
    
    def _publish_to_platform(self, listing: Dict, platform: str) -> str:
        """Publish listing to a specific platform (placeholder)"""
        # TODO: Integrate with platform adapters
        # For now, return a mock ID
        import uuid
        return str(uuid.uuid4())
    
    def list_everywhere(
        self,
        listing_id: int,
        platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        List item on all available platforms.
        
        Args:
            listing_id: Listing ID
            platforms: Optional list of platforms (None = all available)
        
        Returns:
            Results for each platform
        """
        if platforms is None:
            # Get all available platforms
            from ..adapters.all_platforms import PLATFORM_ADAPTERS
            platforms = list(PLATFORM_ADAPTERS.keys())
        
        return self.publish_to_platforms(listing_id, platforms)
    
    def delist_everywhere(
        self,
        listing_id: int,
        platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Delist item from all platforms.
        
        Args:
            listing_id: Listing ID
            platforms: Optional list of platforms (None = all)
        
        Returns:
            Results for each platform
        """
        listing = self.db.get_listing(listing_id)
        if not listing:
            raise ValueError(f"Listing {listing_id} not found")
        
        platform_listings = self.db.get_platform_listings(listing_id)
        
        if platforms:
            platform_listings = [
                pl for pl in platform_listings if pl['platform'] in platforms
            ]
        
        results = {}
        
        for platform_listing in platform_listings:
            platform = platform_listing['platform']
            
            try:
                # Cancel on platform
                # TODO: Integrate with platform adapters
                self._cancel_on_platform(
                    platform_listing['platform_listing_id'],
                    platform
                )
                
                # Update status
                self.db.update_platform_listing_status(
                    listing_id=listing_id,
                    platform=platform,
                    status='cancelled'
                )
                
                results[platform] = {'status': 'cancelled'}
                
            except Exception as e:
                results[platform] = {
                    'status': 'failed',
                    'error': str(e)
                }
        
        return results
    
    def _cancel_on_platform(self, platform_listing_id: str, platform: str):
        """Cancel listing on a platform (placeholder)"""
        # TODO: Integrate with platform adapters
        pass
    
    def relist_everywhere(
        self,
        listing_id: int,
        platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Relist item on all platforms (delist then list).
        
        Args:
            listing_id: Listing ID
            platforms: Optional list of platforms
        
        Returns:
            Results for each platform
        """
        # First delist
        delist_results = self.delist_everywhere(listing_id, platforms)
        
        # Then list again
        if platforms is None:
            from ..adapters.all_platforms import PLATFORM_ADAPTERS
            platforms = list(PLATFORM_ADAPTERS.keys())
        
        list_results = self.publish_to_platforms(listing_id, platforms, force_update=True)
        
        return {
            'delist': delist_results,
            'relist': list_results
        }
    
    def get_listing_status(self, listing_id: int) -> Dict[str, Any]:
        """Get comprehensive listing status across all platforms"""
        listing = self.db.get_listing(listing_id)
        if not listing:
            raise ValueError(f"Listing {listing_id} not found")
        
        platform_listings = self.db.get_platform_listings(listing_id)
        
        return {
            'listing_id': listing_id,
            'title': listing['title'],
            'status': listing['status'],
            'platforms': {
                pl['platform']: {
                    'status': pl['status'],
                    'platform_listing_id': pl['platform_listing_id'],
                    'platform_url': pl['platform_url'],
                    'error_message': pl.get('error_message'),
                    'last_synced': pl.get('last_synced')
                }
                for pl in platform_listings
            }
        }
    
    def bulk_list_everywhere(
        self,
        listing_ids: List[int],
        platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Bulk list multiple items everywhere"""
        results = {
            'succeeded': [],
            'failed': [],
            'errors': []
        }
        
        for listing_id in listing_ids:
            try:
                result = self.list_everywhere(listing_id, platforms)
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
    
    def sync_listing_updates(
        self,
        listing_id: int,
        updates: Dict[str, Any],
        platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Update listing and sync changes to all platforms.
        
        Args:
            listing_id: Listing ID
            updates: Dict of fields to update
            platforms: Optional list of platforms (None = all active)
        
        Returns:
            Results for each platform
        """
        # Update listing in database
        self.db.update_listing(listing_id, **updates)
        
        # Get active platform listings
        platform_listings = self.db.get_platform_listings(listing_id)
        
        if platforms:
            platform_listings = [
                pl for pl in platform_listings if pl['platform'] in platforms
            ]
        
        # Filter to only active listings
        platform_listings = [
            pl for pl in platform_listings if pl['status'] == 'active'
        ]
        
        results = {}
        
        for platform_listing in platform_listings:
            platform = platform_listing['platform']
            
            try:
                # Update on platform
                # TODO: Integrate with platform adapters
                self._update_on_platform(
                    platform_listing['platform_listing_id'],
                    platform,
                    updates
                )
                
                # Update last_synced
                self.db.update_platform_listing_status(
                    listing_id=listing_id,
                    platform=platform,
                    status='active'
                )
                
                results[platform] = {'status': 'updated'}
                
            except Exception as e:
                results[platform] = {
                    'status': 'failed',
                    'error': str(e)
                }
        
        return results
    
    def _update_on_platform(
        self,
        platform_listing_id: str,
        platform: str,
        updates: Dict[str, Any]
    ):
        """Update listing on a platform (placeholder)"""
        # TODO: Integrate with platform adapters
        pass

