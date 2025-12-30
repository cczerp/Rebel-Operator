"""
Inventory Manager
================
Manages inventory items with unified state transitions: draft → active → sold → archived
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from ..database import get_db


class InventoryState(Enum):
    """Inventory item states"""
    DRAFT = "draft"
    ACTIVE = "active"
    SOLD = "sold"
    SHIPPED = "shipped"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted"""
    pass


class InventoryManager:
    """
    Unified inventory management system with state transitions.
    
    State flow:
    - draft → active (when published)
    - active → sold (when item sells)
    - sold → shipped (when marked as shipped)
    - sold/shipped → archived (when archived)
    - active → cancelled (when cancelled)
    - cancelled → draft (when reactivated)
    """
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        InventoryState.DRAFT: [InventoryState.ACTIVE, InventoryState.ARCHIVED],
        InventoryState.ACTIVE: [InventoryState.SOLD, InventoryState.CANCELLED, InventoryState.ARCHIVED],
        InventoryState.SOLD: [InventoryState.SHIPPED, InventoryState.ARCHIVED],
        InventoryState.SHIPPED: [InventoryState.ARCHIVED],
        InventoryState.CANCELLED: [InventoryState.DRAFT, InventoryState.ARCHIVED],
        InventoryState.ARCHIVED: [InventoryState.DRAFT],  # Can reactivate from archive
    }
    
    def __init__(self):
        self.db = get_db()
    
    def get_listing_state(self, listing_id: int) -> Optional[InventoryState]:
        """Get current state of a listing"""
        listing = self.db.get_listing(listing_id)
        if not listing:
            return None
        
        status = listing.get('status', 'draft')
        try:
            return InventoryState(status)
        except ValueError:
            return InventoryState.DRAFT
    
    def can_transition(self, from_state: InventoryState, to_state: InventoryState) -> bool:
        """Check if a state transition is valid"""
        valid_targets = self.VALID_TRANSITIONS.get(from_state, [])
        return to_state in valid_targets
    
    def transition_state(
        self,
        listing_id: int,
        new_state: InventoryState,
        user_id: Optional[int] = None,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Transition a listing to a new state.
        
        Args:
            listing_id: The listing ID
            new_state: Target state
            user_id: User performing the transition
            notes: Optional notes about the transition
            metadata: Optional metadata (e.g., sold_price, platform, etc.)
        
        Returns:
            True if transition succeeded, False otherwise
        
        Raises:
            StateTransitionError: If transition is invalid
        """
        listing = self.db.get_listing(listing_id)
        if not listing:
            raise ValueError(f"Listing {listing_id} not found")
        
        current_status = listing.get('status', 'draft')
        try:
            current_state = InventoryState(current_status)
        except ValueError:
            current_state = InventoryState.DRAFT
        
        # Check if transition is valid
        if not self.can_transition(current_state, new_state):
            raise StateTransitionError(
                f"Cannot transition from {current_state.value} to {new_state.value}"
            )
        
        # Prepare update data
        update_data = {
            'status': new_state.value,
        }
        
        # Handle state-specific updates
        if new_state == InventoryState.SOLD and metadata:
            if 'sold_price' in metadata:
                update_data['sold_price'] = metadata['sold_price']
            if 'sold_platform' in metadata:
                update_data['sold_platform'] = metadata['sold_platform']
            if 'sold_date' in metadata:
                update_data['sold_date'] = metadata['sold_date']
            else:
                update_data['sold_date'] = datetime.now()
        
        # Update listing
        self.db.update_listing(listing_id, **update_data)
        
        # Log state transition
        self._log_transition(
            listing_id=listing_id,
            from_state=current_state,
            to_state=new_state,
            user_id=user_id,
            notes=notes,
            metadata=metadata
        )
        
        return True
    
    def _log_transition(
        self,
        listing_id: int,
        from_state: InventoryState,
        to_state: InventoryState,
        user_id: Optional[int] = None,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log state transition to activity logs"""
        self.db.log_activity(
            action=f"state_transition_{to_state.value}",
            user_id=user_id,
            resource_type="listing",
            resource_id=listing_id,
            details={
                'from_state': from_state.value,
                'to_state': to_state.value,
                'notes': notes,
                'metadata': metadata or {}
            }
        )
    
    def get_listings_by_state(
        self,
        state: InventoryState,
        user_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all listings in a specific state"""
        cursor = self.db._get_cursor()
        
        if user_id:
            cursor.execute("""
                SELECT * FROM listings
                WHERE status = %s AND user_id = %s
                ORDER BY updated_at DESC
                LIMIT %s OFFSET %s
            """, (state.value, user_id, limit, offset))
        else:
            cursor.execute("""
                SELECT * FROM listings
                WHERE status = %s
                ORDER BY updated_at DESC
                LIMIT %s OFFSET %s
            """, (state.value, limit, offset))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def bulk_transition(
        self,
        listing_ids: List[int],
        new_state: InventoryState,
        user_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Bulk transition multiple listings to a new state.
        
        Returns:
            Dict with 'succeeded', 'failed', and 'errors' keys
        """
        results = {
            'succeeded': [],
            'failed': [],
            'errors': []
        }
        
        for listing_id in listing_ids:
            try:
                self.transition_state(
                    listing_id=listing_id,
                    new_state=new_state,
                    user_id=user_id,
                    notes=notes
                )
                results['succeeded'].append(listing_id)
            except (StateTransitionError, ValueError) as e:
                results['failed'].append(listing_id)
                results['errors'].append({
                    'listing_id': listing_id,
                    'error': str(e)
                })
        
        return results
    
    def archive_old_sold_items(
        self,
        days_old: int = 90,
        user_id: Optional[int] = None
    ) -> int:
        """
        Automatically archive sold items older than specified days.
        
        Returns:
            Number of items archived
        """
        cursor = self.db._get_cursor()
        
        query = """
            SELECT id FROM listings
            WHERE status IN ('sold', 'shipped')
            AND sold_date < NOW() - INTERVAL '%s days'
        """
        params = [days_old]
        
        if user_id:
            query += " AND user_id = %s"
            params.append(user_id)
        
        cursor.execute(query, params)
        listings_to_archive = [row['id'] for row in cursor.fetchall()]
        
        archived_count = 0
        for listing_id in listings_to_archive:
            try:
                self.transition_state(
                    listing_id=listing_id,
                    new_state=InventoryState.ARCHIVED,
                    user_id=user_id,
                    notes=f"Auto-archived after {days_old} days"
                )
                archived_count += 1
            except StateTransitionError:
                pass  # Skip if transition invalid
        
        return archived_count
    
    def get_inventory_summary(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get inventory summary by state"""
        cursor = self.db._get_cursor()
        
        if user_id:
            cursor.execute("""
                SELECT 
                    status,
                    COUNT(*) as count,
                    SUM(price) as total_value,
                    SUM(CASE WHEN cost IS NOT NULL THEN cost ELSE 0 END) as total_cost
                FROM listings
                WHERE user_id = %s
                GROUP BY status
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT 
                    status,
                    COUNT(*) as count,
                    SUM(price) as total_value,
                    SUM(CASE WHEN cost IS NOT NULL THEN cost ELSE 0 END) as total_cost
                FROM listings
                GROUP BY status
            """)
        
        summary = {}
        for row in cursor.fetchall():
            state = row['status']
            summary[state] = {
                'count': row['count'],
                'total_value': float(row['total_value'] or 0),
                'total_cost': float(row['total_cost'] or 0),
                'estimated_profit': float(row['total_value'] or 0) - float(row['total_cost'] or 0)
            }
        
        return summary

