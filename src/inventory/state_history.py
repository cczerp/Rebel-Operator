"""
State History Tracker
=====================
Tracks state transition history for inventory items
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from ..database import get_db


class StateHistory:
    """Tracks state transition history for listings"""
    
    def __init__(self):
        self.db = get_db()
    
    def get_listing_history(self, listing_id: int) -> List[Dict[str, Any]]:
        """Get state transition history for a listing"""
        cursor = self.db._get_cursor()
        
        cursor.execute("""
            SELECT 
                action,
                resource_type,
                resource_id,
                details,
                created_at,
                user_id
            FROM activity_logs
            WHERE resource_type = 'listing'
            AND resource_id = %s
            AND action LIKE 'state_transition_%'
            ORDER BY created_at ASC
        """, (listing_id,))
        
        history = []
        for row in cursor.fetchall():
            details = row['details']
            if isinstance(details, str):
                import json
                details = json.loads(details)
            
            history.append({
                'action': row['action'],
                'from_state': details.get('from_state'),
                'to_state': details.get('to_state'),
                'notes': details.get('notes'),
                'metadata': details.get('metadata', {}),
                'timestamp': row['created_at'],
                'user_id': row['user_id']
            })
        
        return history
    
    def get_current_state_info(self, listing_id: int) -> Optional[Dict[str, Any]]:
        """Get current state and when it was set"""
        history = self.get_listing_history(listing_id)
        if not history:
            return None
        
        latest = history[-1]
        return {
            'current_state': latest['to_state'],
            'transitioned_at': latest['timestamp'],
            'transitioned_by': latest['user_id'],
            'notes': latest['notes']
        }

