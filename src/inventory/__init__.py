"""
Inventory Management System
============================
Unified inventory management with state transitions: draft → active → sold → archived
"""

from .inventory_manager import InventoryManager, InventoryState, StateTransitionError
from .state_history import StateHistory

__all__ = [
    'InventoryManager',
    'InventoryState',
    'StateTransitionError',
    'StateHistory',
]

