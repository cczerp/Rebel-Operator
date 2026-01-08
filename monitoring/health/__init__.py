"""
Health monitoring package
========================
Contains health check endpoints and monitoring utilities.
"""

from .health_checks import health_bp

__all__ = ['health_bp']
