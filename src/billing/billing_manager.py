"""
Billing Manager
===============
Manages subscriptions, tiers, and feature gates
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..database import get_db


class SubscriptionTier(Enum):
    """Subscription tiers"""
    FREE = "FREE"
    PRO = "PRO"
    BUSINESS = "BUSINESS"
    ADMIN = "ADMIN"


class FeatureGate:
    """Feature gate configuration"""
    
    TIER_FEATURES = {
        SubscriptionTier.FREE: {
            'listings_per_month': 10,
            'platforms': ['poshmark', 'facebook'],  # CSV-only platforms
            'api_platforms': 0,
            'bulk_operations': False,
            'auto_sync': False,
            'advanced_seo': False,
            'storage_management': False,
            'analytics': False,
        },
        SubscriptionTier.PRO: {
            'listings_per_month': -1,  # Unlimited
            'platforms': ['poshmark', 'facebook', 'etsy', 'shopify'],
            'api_platforms': 3,
            'bulk_operations': True,
            'auto_sync': True,
            'advanced_seo': True,
            'storage_management': True,
            'analytics': False,
        },
        SubscriptionTier.BUSINESS: {
            'listings_per_month': -1,  # Unlimited
            'platforms': ['all'],  # All platforms
            'api_platforms': -1,  # Unlimited
            'bulk_operations': True,
            'auto_sync': True,
            'advanced_seo': True,
            'storage_management': True,
            'analytics': True,
        },
        SubscriptionTier.ADMIN: {
            'listings_per_month': -1,
            'platforms': ['all'],
            'api_platforms': -1,
            'bulk_operations': True,
            'auto_sync': True,
            'advanced_seo': True,
            'storage_management': True,
            'analytics': True,
        }
    }
    
    @classmethod
    def can_access_feature(cls, tier: SubscriptionTier, feature: str) -> bool:
        """Check if tier has access to a feature"""
        tier_config = cls.TIER_FEATURES.get(tier, cls.TIER_FEATURES[SubscriptionTier.FREE])
        return tier_config.get(feature, False)
    
    @classmethod
    def get_tier_limits(cls, tier: SubscriptionTier) -> Dict[str, Any]:
        """Get limits for a tier"""
        return cls.TIER_FEATURES.get(tier, cls.TIER_FEATURES[SubscriptionTier.FREE])


class BillingManager:
    """Manages billing and subscriptions"""
    
    def __init__(self):
        self.db = get_db()
        self._ensure_billing_tables()
    
    def _ensure_billing_tables(self):
        """Ensure billing tables exist"""
        cursor = self.db._get_cursor()
        
        # Subscriptions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                tier TEXT NOT NULL DEFAULT 'FREE',
                stripe_subscription_id TEXT,
                stripe_customer_id TEXT,
                status TEXT DEFAULT 'active',
                current_period_start TIMESTAMP,
                current_period_end TIMESTAMP,
                cancel_at_period_end BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Usage tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_tracking (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value INTEGER DEFAULT 0,
                period_start TIMESTAMP,
                period_end TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        self.db.conn.commit()
    
    def get_user_tier(self, user_id: int) -> SubscriptionTier:
        """Get user's subscription tier"""
        user = self.db.get_user_by_id(user_id)
        if not user:
            return SubscriptionTier.FREE
        
        tier_str = user.get('tier', 'FREE')
        try:
            return SubscriptionTier(tier_str)
        except ValueError:
            return SubscriptionTier.FREE
    
    def can_access_feature(self, user_id: int, feature: str) -> bool:
        """Check if user can access a feature"""
        tier = self.get_user_tier(user_id)
        return FeatureGate.can_access_feature(tier, feature)
    
    def check_listing_limit(self, user_id: int) -> tuple:
        """Check if user can create more listings this month"""
        tier = self.get_user_tier(user_id)
        limits = FeatureGate.get_tier_limits(tier)
        
        monthly_limit = limits.get('listings_per_month', 10)
        
        if monthly_limit == -1:
            return True, None  # Unlimited
        
        # Count listings created this month
        cursor = self.db._get_cursor()
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM listings
            WHERE user_id = %s
            AND created_at >= DATE_TRUNC('month', CURRENT_DATE)
        """, (user_id,))
        
        count = cursor.fetchone()['count']
        
        if count >= monthly_limit:
            return False, f"Monthly limit of {monthly_limit} listings reached"
        
        return True, None
    
    def track_usage(
        self,
        user_id: int,
        metric_name: str,
        value: int = 1
    ):
        """Track usage of a metric"""
        cursor = self.db._get_cursor()
        
        # Get current period
        period_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = (period_start.replace(month=period_start.month + 1) if period_start.month < 12 
                     else period_start.replace(year=period_start.year + 1, month=1))
        
        # Check if record exists
        cursor.execute("""
            SELECT id, metric_value
            FROM usage_tracking
            WHERE user_id = %s
            AND metric_name = %s
            AND period_start = %s
        """, (user_id, metric_name, period_start))
        
        row = cursor.fetchone()
        
        if row:
            # Update existing
            cursor.execute("""
                UPDATE usage_tracking
                SET metric_value = metric_value + %s
                WHERE id = %s
            """, (value, row['id']))
        else:
            # Create new
            cursor.execute("""
                INSERT INTO usage_tracking (
                    user_id, metric_name, metric_value,
                    period_start, period_end
                ) VALUES (%s, %s, %s, %s, %s)
            """, (user_id, metric_name, value, period_start, period_end))
        
        self.db.conn.commit()
    
    def update_subscription(
        self,
        user_id: int,
        tier: SubscriptionTier,
        stripe_subscription_id: Optional[str] = None,
        stripe_customer_id: Optional[str] = None
    ):
        """Update user subscription"""
        cursor = self.db._get_cursor()
        
        # Update user tier
        cursor.execute("""
            UPDATE users
            SET tier = %s
            WHERE id = %s
        """, (tier.value, user_id))
        
        # Update or create subscription record
        cursor.execute("""
            SELECT id FROM subscriptions
            WHERE user_id = %s
        """, (user_id,))
        
        row = cursor.fetchone()
        
        if row:
            # Update existing
            cursor.execute("""
                UPDATE subscriptions
                SET tier = %s,
                    stripe_subscription_id = COALESCE(%s, stripe_subscription_id),
                    stripe_customer_id = COALESCE(%s, stripe_customer_id),
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """, (tier.value, stripe_subscription_id, stripe_customer_id, user_id))
        else:
            # Create new
            cursor.execute("""
                INSERT INTO subscriptions (
                    user_id, tier, stripe_subscription_id, stripe_customer_id
                ) VALUES (%s, %s, %s, %s)
            """, (user_id, tier.value, stripe_subscription_id, stripe_customer_id))
        
        self.db.conn.commit()

