"""
Job Queue System
===============
Background job queue with retry logic and priority support
"""

from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
import json
import uuid
import time

from ..database import get_db


class JobStatus(Enum):
    """Job status states"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class JobPriority(Enum):
    """Job priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class Job:
    """Represents a background job"""
    
    def __init__(
        self,
        job_type: str,
        payload: Dict[str, Any],
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 3,
        retry_delay: int = 60,
        job_id: Optional[str] = None
    ):
        self.job_id = job_id or str(uuid.uuid4())
        self.job_type = job_type
        self.payload = payload
        self.priority = priority
        self.status = JobStatus.PENDING
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_count = 0
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for storage"""
        return {
            'job_id': self.job_id,
            'job_type': self.job_type,
            'payload': json.dumps(self.payload),
            'priority': self.priority.value,
            'status': self.status.value,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'retry_count': self.retry_count,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'result': json.dumps(self.result) if self.result else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create job from dictionary"""
        job = cls(
            job_type=data['job_type'],
            payload=json.loads(data['payload']),
            priority=JobPriority(data['priority']),
            max_retries=data['max_retries'],
            retry_delay=data['retry_delay'],
            job_id=data['job_id']
        )
        job.status = JobStatus(data['status'])
        job.retry_count = data['retry_count']
        if data['started_at']:
            job.started_at = datetime.fromisoformat(data['started_at'])
        if data['completed_at']:
            job.completed_at = datetime.fromisoformat(data['completed_at'])
        job.error_message = data.get('error_message')
        if data.get('result'):
            job.result = json.loads(data['result'])
        return job


class JobQueue:
    """Manages background job queue"""
    
    def __init__(self):
        self.db = get_db()
        self._ensure_job_table()
    
    def _ensure_job_table(self):
        """Ensure job queue table exists"""
        cursor = self.db._get_cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_queue (
                id SERIAL PRIMARY KEY,
                job_id TEXT UNIQUE NOT NULL,
                job_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                priority INTEGER DEFAULT 2,
                status TEXT DEFAULT 'pending',
                max_retries INTEGER DEFAULT 3,
                retry_delay INTEGER DEFAULT 60,
                retry_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                result TEXT,
                scheduled_for TIMESTAMP,
            )
        """)
        
        # Create indexes (PostgreSQL syntax)
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_job_queue_status
                ON job_queue(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_job_queue_priority
                ON job_queue(priority DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_job_queue_scheduled
                ON job_queue(scheduled_for)
            """)
        except Exception:
            pass  # Indexes may already exist
        
        self.db.conn.commit()
    
    def enqueue(
        self,
        job_type: str,
        payload: Dict[str, Any],
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 3,
        retry_delay: int = 60,
        scheduled_for: Optional[datetime] = None
    ) -> str:
        """Add job to queue"""
        job = Job(
            job_type=job_type,
            payload=payload,
            priority=priority,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        
        cursor = self.db._get_cursor()
        cursor.execute("""
            INSERT INTO job_queue (
                job_id, job_type, payload, priority, status,
                max_retries, retry_delay, scheduled_for
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            job.job_id,
            job.job_type,
            json.dumps(job.payload),
            job.priority.value,
            job.status.value,
            job.max_retries,
            job.retry_delay,
            scheduled_for
        ))
        
        self.db.conn.commit()
        return job.job_id
    
    def dequeue(self, limit: int = 1) -> List[Job]:
        """Get next jobs from queue (highest priority first)"""
        cursor = self.db._get_cursor()
        
        cursor.execute("""
            SELECT * FROM job_queue
            WHERE status IN ('pending', 'queued', 'retrying')
            AND (scheduled_for IS NULL OR scheduled_for <= NOW())
            ORDER BY priority DESC, created_at ASC
            LIMIT %s
            FOR UPDATE SKIP LOCKED
        """, (limit,))
        
        jobs = []
        for row in cursor.fetchall():
            # Mark as running
            cursor.execute("""
                UPDATE job_queue
                SET status = 'running', started_at = NOW()
                WHERE job_id = %s
            """, (row['job_id'],))
            
            job = Job.from_dict(dict(row))
            job.status = JobStatus.RUNNING
            jobs.append(job)
        
        self.db.conn.commit()
        return jobs
    
    def complete_job(self, job_id: str, result: Optional[Dict[str, Any]] = None):
        """Mark job as completed"""
        cursor = self.db._get_cursor()
        cursor.execute("""
            UPDATE job_queue
            SET status = 'completed',
                completed_at = NOW(),
                result = %s
            WHERE job_id = %s
        """, (json.dumps(result) if result else None, job_id))
        self.db.conn.commit()
    
    def fail_job(self, job_id: str, error_message: str, retry: bool = True):
        """Mark job as failed, optionally retry"""
        cursor = self.db._get_cursor()
        
        # Get job details
        cursor.execute("SELECT * FROM job_queue WHERE job_id = %s", (job_id,))
        job_data = cursor.fetchone()
        
        if not job_data:
            return
        
        retry_count = job_data['retry_count'] + 1
        
        if retry and retry_count < job_data['max_retries']:
            # Schedule retry
            retry_delay = job_data['retry_delay'] * (2 ** (retry_count - 1))  # Exponential backoff
            scheduled_for = datetime.now() + timedelta(seconds=retry_delay)
            
            cursor.execute("""
                UPDATE job_queue
                SET status = 'retrying',
                    retry_count = %s,
                    error_message = %s,
                    scheduled_for = %s
                WHERE job_id = %s
            """, (retry_count, error_message, scheduled_for, job_id))
        else:
            # Mark as permanently failed
            cursor.execute("""
                UPDATE job_queue
                SET status = 'failed',
                    error_message = %s,
                    retry_count = %s
                WHERE job_id = %s
            """, (error_message, retry_count, job_id))
        
        self.db.conn.commit()
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        cursor = self.db._get_cursor()
        cursor.execute("SELECT * FROM job_queue WHERE job_id = %s", (job_id,))
        row = cursor.fetchone()
        return Job.from_dict(dict(row)) if row else None
    
    def get_pending_jobs(self, job_type: Optional[str] = None) -> List[Job]:
        """Get all pending jobs"""
        cursor = self.db._get_cursor()
        
        if job_type:
            cursor.execute("""
                SELECT * FROM job_queue
                WHERE status IN ('pending', 'queued', 'retrying')
                AND job_type = %s
                ORDER BY priority DESC, created_at ASC
            """, (job_type,))
        else:
            cursor.execute("""
                SELECT * FROM job_queue
                WHERE status IN ('pending', 'queued', 'retrying')
                ORDER BY priority DESC, created_at ASC
            """)
        
        return [Job.from_dict(dict(row)) for row in cursor.fetchall()]
    
    def cancel_job(self, job_id: str):
        """Cancel a pending job"""
        cursor = self.db._get_cursor()
        cursor.execute("""
            UPDATE job_queue
            SET status = 'cancelled'
            WHERE job_id = %s
            AND status IN ('pending', 'queued', 'retrying')
        """, (job_id,))
        self.db.conn.commit()

