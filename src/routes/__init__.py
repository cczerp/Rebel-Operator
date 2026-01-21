"""
Routes module for Rebel Operator web application.

This module contains all Flask route blueprints organized by functionality:
- admin: Admin dashboard and management routes
- auth: Authentication and user management routes
- cards: Card-specific routes and functionality
- csv: CSV export routes for various platforms
- main: Main application routes (listings, drafts, vault, etc.)
"""

from .admin import admin_bp
from .auth import auth_bp
from .cards import cards_bp
from .csv import csv_bp
from .main import main_bp

__all__ = ['admin_bp', 'auth_bp', 'cards_bp', 'csv_bp', 'main_bp']
