"""
Stripe Integration
=================
Stripe payment processing and webhook handling
"""

from typing import Dict, Any, Optional
import os

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False


class StripeIntegration:
    """Stripe payment integration"""
    
    def __init__(self):
        if not STRIPE_AVAILABLE:
            raise ImportError(
                "stripe is required. Install with: pip install stripe"
            )
        
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        if not stripe.api_key:
            raise ValueError("STRIPE_SECRET_KEY environment variable required")
        
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    def create_checkout_session(
        self,
        user_id: int,
        tier: str,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """Create Stripe checkout session"""
        price_map = {
            'PRO': os.getenv('STRIPE_PRICE_ID_PRO'),
            'BUSINESS': os.getenv('STRIPE_PRICE_ID_BUSINESS'),
        }
        
        price_id = price_map.get(tier)
        if not price_id:
            raise ValueError(f"Invalid tier: {tier}")
        
        session = stripe.checkout.Session.create(
            customer_email=None,  # Will be collected during checkout
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'user_id': str(user_id),
                'tier': tier
            }
        )
        
        return {
            'session_id': session.id,
            'url': session.url
        }
    
    def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Handle Stripe webhook"""
        if not self.webhook_secret:
            raise ValueError("STRIPE_WEBHOOK_SECRET required for webhooks")
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
        except ValueError:
            raise ValueError("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid signature")
        
        event_type = event['type']
        data = event['data']['object']
        
        if event_type == 'checkout.session.completed':
            # Subscription created
            return self._handle_subscription_created(data)
        elif event_type == 'customer.subscription.updated':
            # Subscription updated
            return self._handle_subscription_updated(data)
        elif event_type == 'customer.subscription.deleted':
            # Subscription cancelled
            return self._handle_subscription_deleted(data)
        
        return {'status': 'ignored', 'event_type': event_type}
    
    def _handle_subscription_created(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription creation"""
        from .billing_manager import BillingManager, SubscriptionTier
        
        billing = BillingManager()
        user_id = int(session['metadata']['user_id'])
        tier = SubscriptionTier(session['metadata']['tier'])
        
        subscription_id = session.get('subscription')
        customer_id = session.get('customer')
        
        billing.update_subscription(
            user_id=user_id,
            tier=tier,
            stripe_subscription_id=subscription_id,
            stripe_customer_id=customer_id
        )
        
        return {'status': 'success', 'user_id': user_id, 'tier': tier.value}
    
    def _handle_subscription_updated(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription update"""
        # TODO: Implement subscription update logic
        return {'status': 'updated'}
    
    def _handle_subscription_deleted(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription cancellation"""
        from .billing_manager import BillingManager, SubscriptionTier
        
        billing = BillingManager()
        customer_id = subscription.get('customer')
        
        # Find user by customer ID
        # TODO: Implement user lookup by customer_id
        
        # Downgrade to FREE
        # billing.update_subscription(user_id, SubscriptionTier.FREE)
        
        return {'status': 'cancelled'}

