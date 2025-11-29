"""
Worker Manager
=============
Manages background workers that process jobs
"""

import time
import threading
from typing import Dict, Callable, Optional
from concurrent.futures import ThreadPoolExecutor

from .job_queue import JobQueue, Job, JobStatus
from ..database import get_db


class WorkerManager:
    """Manages background workers for processing jobs"""
    
    def __init__(self, num_workers: int = 4):
        self.job_queue = JobQueue()
        self.num_workers = num_workers
        self.workers: Dict[str, Callable] = {}
        self.executor: Optional[ThreadPoolExecutor] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
    
    def register_worker(self, job_type: str, handler: Callable[[Job], Dict]):
        """Register a worker handler for a job type"""
        self.workers[job_type] = handler
    
    def start(self):
        """Start worker threads"""
        if self.running:
            return
        
        self.running = True
        self.executor = ThreadPoolExecutor(max_workers=self.num_workers)
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop worker threads"""
        self.running = False
        if self.executor:
            self.executor.shutdown(wait=True)
    
    def _worker_loop(self):
        """Main worker loop"""
        while self.running:
            try:
                # Get jobs from queue
                jobs = self.job_queue.dequeue(limit=self.num_workers)
                
                if not jobs:
                    time.sleep(1)  # No jobs, wait a bit
                    continue
                
                # Process jobs in parallel
                for job in jobs:
                    self.executor.submit(self._process_job, job)
                
            except Exception as e:
                print(f"Error in worker loop: {e}")
                time.sleep(5)
    
    def _process_job(self, job: Job):
        """Process a single job"""
        handler = self.workers.get(job.job_type)
        
        if not handler:
            self.job_queue.fail_job(
                job.job_id,
                f"No handler registered for job type: {job.job_type}",
                retry=False
            )
            return
        
        try:
            result = handler(job)
            self.job_queue.complete_job(job.job_id, result)
        except Exception as e:
            error_msg = str(e)
            print(f"Job {job.job_id} failed: {error_msg}")
            self.job_queue.fail_job(job.job_id, error_msg, retry=True)
    
    def process_job_sync(self, job: Job) -> Dict:
        """Process a job synchronously (for testing or immediate execution)"""
        handler = self.workers.get(job.job_type)
        
        if not handler:
            raise ValueError(f"No handler registered for job type: {job.job_type}")
        
        return handler(job)


# Built-in job handlers
def sync_listing_handler(job: Job) -> Dict:
    """Handler for syncing listings across platforms"""
    from ..sync.multi_platform_sync import MultiPlatformSyncManager
    
    payload = job.payload
    listing_id = payload.get('listing_id')
    platforms = payload.get('platforms', [])
    
    if not listing_id:
        raise ValueError("listing_id required")
    
    db = get_db()
    listing = db.get_listing(listing_id)
    
    if not listing:
        raise ValueError(f"Listing {listing_id} not found")
    
    # Use sync manager to sync
    sync_manager = MultiPlatformSyncManager()
    # TODO: Implement actual sync logic
    
    return {'status': 'synced', 'listing_id': listing_id}


def update_seo_handler(job: Job) -> Dict:
    """Handler for updating SEO across platforms"""
    payload = job.payload
    listing_id = payload.get('listing_id')
    
    if not listing_id:
        raise ValueError("listing_id required")
    
    # TODO: Implement SEO sync logic
    
    return {'status': 'updated', 'listing_id': listing_id}


def archive_old_items_handler(job: Job) -> Dict:
    """Handler for archiving old sold items"""
    from ..inventory import InventoryManager
    
    payload = job.payload
    days_old = payload.get('days_old', 90)
    user_id = payload.get('user_id')
    
    inventory = InventoryManager()
    archived_count = inventory.archive_old_sold_items(days_old=days_old, user_id=user_id)
    
    return {'archived_count': archived_count}


def image_optimization_handler(job: Job) -> Dict:
    """Handler for image optimization"""
    payload = job.payload
    listing_id = payload.get('listing_id')
    image_paths = payload.get('image_paths', [])
    
    # TODO: Implement image optimization
    
    return {'status': 'optimized', 'listing_id': listing_id}


def feed_sync_handler(job: Job) -> Dict:
    """Handler for syncing product feeds to catalog platforms"""
    from ..adapters.all_platforms import FacebookShopsAdapter, GoogleShoppingAdapter, PinterestAdapter
    
    payload = job.payload
    user_id = payload.get('user_id')
    platforms = payload.get('platforms', ['facebook', 'google', 'pinterest'])
    
    if not user_id:
        raise ValueError("user_id required")
    
    results = {}
    
    # Get active listings for the user
    db = get_db()
    listings_data = db.get_active_listings(user_id)
    
    if not listings_data:
        return {'status': 'no_listings', 'message': 'No active listings found for user'}
    
    # Convert to UnifiedListing objects
    from ..schema.unified_listing import UnifiedListing, Price, ListingCondition, Photo
    listings = []
    
    for listing_data in listings_data:
        try:
            # Convert price to Price object
            price_obj = Price(amount=float(listing_data['price']))

            # Convert condition to ListingCondition enum
            condition_str = listing_data.get('condition', 'good').lower()
            condition_enum = ListingCondition.GOOD  # default
            if condition_str == 'new':
                condition_enum = ListingCondition.NEW
            elif condition_str == 'like_new':
                condition_enum = ListingCondition.LIKE_NEW
            elif condition_str == 'excellent':
                condition_enum = ListingCondition.EXCELLENT
            elif condition_str == 'fair':
                condition_enum = ListingCondition.FAIR
            elif condition_str == 'poor':
                condition_enum = ListingCondition.POOR

            # Convert photos from JSON string to List[Photo]
            photos = []
            if listing_data.get('photos'):
                try:
                    import json
                    photos_data = json.loads(listing_data['photos'])
                    for i, photo_url in enumerate(photos_data):
                        photos.append(Photo(url=photo_url, order=i, is_primary=(i == 0)))
                except (json.JSONDecodeError, TypeError):
                    pass

            listing = UnifiedListing(
                title=listing_data['title'],
                description=listing_data.get('description', ''),
                price=price_obj,
                condition=condition_enum,
                photos=photos
            )
            listings.append(listing)
        except Exception as e:
            print(f"Error converting listing {listing_data.get('id')}: {e}")
            continue
    
    # Sync to each platform
    for platform in platforms:
        try:
            if platform == 'facebook':
                adapter = FacebookShopsAdapter()
            elif platform == 'google':
                adapter = GoogleShoppingAdapter()
            elif platform == 'pinterest':
                adapter = PinterestAdapter()
            else:
                continue
            
            # Generate feed and sync
            feed_data = adapter.generate_csv(listings)
            # TODO: Actually upload/sync the feed to the platform
            results[platform] = {'status': 'success', 'items_count': len(listings)}
            
        except Exception as e:
            print(f"Error syncing {platform} feed: {e}")
            results[platform] = {'status': 'error', 'error': str(e)}
    
    return {
        'status': 'completed',
        'platforms_synced': results,
        'total_listings': len(listings)
    }

