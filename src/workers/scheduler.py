"""
Scheduler
========
Schedules recurring and one-time jobs
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import threading
import time

from .job_queue import JobQueue, JobPriority


class Scheduler:
    """Schedules recurring and one-time jobs"""
    
    def __init__(self):
        self.job_queue = JobQueue()
        self.scheduled_jobs: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self.thread: Optional[threading.Thread] = None
    
    def schedule_job(
        self,
        job_id: str,
        job_type: str,
        payload: Dict[str, Any],
        schedule_time: datetime,
        priority: JobPriority = JobPriority.NORMAL
    ):
        """Schedule a one-time job"""
        self.job_queue.enqueue(
            job_type=job_type,
            payload=payload,
            priority=priority,
            scheduled_for=schedule_time
        )
        
        self.scheduled_jobs[job_id] = {
            'job_id': job_id,
            'job_type': job_type,
            'schedule_time': schedule_time,
            'recurring': False
        }
    
    def schedule_recurring(
        self,
        job_id: str,
        job_type: str,
        payload: Dict[str, Any],
        interval_seconds: int,
        priority: JobPriority = JobPriority.NORMAL
    ):
        """Schedule a recurring job"""
        next_run = datetime.now() + timedelta(seconds=interval_seconds)
        
        self.scheduled_jobs[job_id] = {
            'job_id': job_id,
            'job_type': job_type,
            'payload': payload,
            'interval_seconds': interval_seconds,
            'next_run': next_run,
            'recurring': True,
            'priority': priority
        }
    
    def start(self):
        """Start scheduler"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop scheduler"""
        self.running = False
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                now = datetime.now()
                
                # Check recurring jobs
                for job_id, job_info in list(self.scheduled_jobs.items()):
                    if job_info['recurring']:
                        if now >= job_info['next_run']:
                            # Enqueue job
                            self.job_queue.enqueue(
                                job_type=job_info['job_type'],
                                payload=job_info['payload'],
                                priority=job_info['priority'],
                                scheduled_for=now
                            )
                            
                            # Schedule next run
                            job_info['next_run'] = now + timedelta(
                                seconds=job_info['interval_seconds']
                            )
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"Error in scheduler loop: {e}")
                time.sleep(30)
    
    def cancel_job(self, job_id: str):
        """Cancel a scheduled job"""
        if job_id in self.scheduled_jobs:
            del self.scheduled_jobs[job_id]
    
    def schedule_nightly_sync(self, hour: int = 2, minute: int = 0):
        """Schedule nightly sync at specific time"""
        now = datetime.now()
        scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If time has passed today, schedule for tomorrow
        if scheduled_time < now:
            scheduled_time += timedelta(days=1)
        
        self.schedule_job(
            job_id='nightly_sync',
            job_type='nightly_sync',
            payload={},
            schedule_time=scheduled_time,
            priority=JobPriority.NORMAL
        )
        
        # Make it recurring
        self.schedule_recurring(
            job_id='nightly_sync_recurring',
            job_type='nightly_sync',
            payload={},
            interval_seconds=24 * 60 * 60  # 24 hours
        )
    
    def schedule_feed_sync(
        self,
        user_id: int,
        platforms: list = None,
        interval_hours: int = 6  # Sync every 6 hours
    ):
        """Schedule recurring feed sync for catalog platforms"""
        if platforms is None:
            platforms = ['facebook', 'google', 'pinterest']
        
        job_id = f'feed_sync_user_{user_id}'
        
        self.schedule_recurring(
            job_id=job_id,
            job_type='feed_sync',
            payload={
                'user_id': user_id,
                'platforms': platforms
            },
            interval_seconds=interval_hours * 60 * 60,
            priority=JobPriority.NORMAL
        )
        
        return job_id

