"""
Health check endpoints for monitoring and deployment readiness
==============================================================
Provides readiness endpoint with state-change logging.
Only logs when status changes or on exceptions.
"""

import logging
from flask import Blueprint, jsonify
from datetime import datetime
from src.database import get_db

# Configure logger
logger = logging.getLogger(__name__)

# Global state tracking for readiness status
_readiness_state = {
    'last_status': None,
    'last_check_time': None,
    'consecutive_failures': 0
}

health_bp = Blueprint('health', __name__, url_prefix='/health')

def check_database_connection():
    """Check if database connection is working"""
    try:
        db = get_db()
        cursor = db._get_cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        return result is not None
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False

def check_essential_services():
    """Check if essential services are available"""
    checks = {
        'database': check_database_connection(),
        # Add more service checks here if needed
        # 'redis': check_redis_connection(),
        # 'external_api': check_external_api(),
    }
    
    all_healthy = all(checks.values())
    return all_healthy, checks

@health_bp.route('/ready')
def readiness_check():
    """
    Readiness endpoint that logs only on state changes or exceptions.
    Returns 200 OK if ready, 503 Service Unavailable if not ready.
    """
    global _readiness_state
    
    try:
        # Perform readiness checks
        is_ready, service_checks = check_essential_services()
        current_time = datetime.utcnow()
        
        # Determine if we should log (state changed or first check)
        should_log = (
            _readiness_state['last_status'] is None or  # First check
            _readiness_state['last_status'] != is_ready  # Status changed
        )
        
        # Log state changes
        if should_log:
            if is_ready:
                if _readiness_state['last_status'] is False:
                    logger.info(f"Service ready: Status changed from NOT READY → READY. Services: {service_checks}")
                elif _readiness_state['last_status'] is None:
                    logger.info(f"Service ready: Initial readiness check passed. Services: {service_checks}")
                _readiness_state['consecutive_failures'] = 0
            else:
                if _readiness_state['last_status'] is True:
                    logger.warning(f"Service not ready: Status changed from READY → NOT READY. Services: {service_checks}")
                elif _readiness_state['last_status'] is None:
                    logger.warning(f"Service not ready: Initial readiness check failed. Services: {service_checks}")
                _readiness_state['consecutive_failures'] += 1
        
        # Update state
        _readiness_state['last_status'] = is_ready
        _readiness_state['last_check_time'] = current_time
        
        # Return appropriate response
        if is_ready:
            return jsonify({
                'status': 'ready',
                'timestamp': current_time.isoformat(),
                'services': service_checks
            }), 200
        else:
            return jsonify({
                'status': 'not_ready',
                'timestamp': current_time.isoformat(),
                'services': service_checks,
                'consecutive_failures': _readiness_state['consecutive_failures']
            }), 503
            
    except Exception as e:
        # Always log exceptions
        logger.error(f"Readiness check exception: {str(e)}", exc_info=True)
        _readiness_state['last_status'] = False
        _readiness_state['last_check_time'] = datetime.utcnow()
        _readiness_state['consecutive_failures'] += 1
        
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

@health_bp.route('/live')
def liveness_check():
    """
    Liveness endpoint - simple check that the application is running.
    Always returns 200 OK if the application can respond.
    """
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@health_bp.route('/status')
def health_status():
    """
    Detailed health status endpoint with service breakdown.
    """
    try:
        is_ready, service_checks = check_essential_services()
        
        return jsonify({
            'status': 'ready' if is_ready else 'degraded',
            'timestamp': datetime.utcnow().isoformat(),
            'services': service_checks,
            'last_readiness_check': _readiness_state['last_check_time'].isoformat() if _readiness_state['last_check_time'] else None,
            'consecutive_failures': _readiness_state['consecutive_failures']
        }), 200 if is_ready else 503
        
    except Exception as e:
        logger.error(f"Health status check exception: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500
