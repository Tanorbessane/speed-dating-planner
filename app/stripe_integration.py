"""Intégration Stripe pour les paiements et abonnements.

Gestion des checkout sessions, webhooks et mise à jour des tiers utilisateurs.
"""

import stripe
import streamlit as st
from typing import Optional, Tuple


def init_stripe():
    """Initialiser Stripe avec les clés API depuis secrets."""
    try:
        stripe.api_key = st.secrets["stripe"]["secret_key"]
        return True
    except Exception as e:
        st.error(f"❌ Erreur configuration Stripe : {str(e)}")
        return False


def get_publishable_key() -> Optional[str]:
    """Récupérer la clé publique Stripe."""
    try:
        return st.secrets["stripe"]["publishable_key"]
    except Exception:
        return None


def create_checkout_session(
    user_email: str,
    tier: str,
    success_url: str,
    cancel_url: str
) -> Tuple[bool, Optional[str], str]:
    """Créer une session de paiement Stripe Checkout.

    Args:
        user_email: Email de l'utilisateur
        tier: Tier à acheter (pro ou business)
        success_url: URL de redirection après succès
        cancel_url: URL de redirection après annulation

    Returns:
        (success, checkout_url, error_message)
    """
    if not init_stripe():
        return False, None, "Configuration Stripe manquante"

    # Prix selon le tier
    prices = {
        "pro": {
            "name": "Plan Pro",
            "amount": 2900,  # 29€ en centimes
            "description": "150 participants, sessions illimitées, PDF, VIP, Analytics"
        },
        "business": {
            "name": "Plan Business",
            "amount": 9900,  # 99€ en centimes
            "description": "Illimité, Multi-users, API, White-label, Support 24/7"
        }
    }

    if tier not in prices:
        return False, None, "Tier invalide"

    price_info = prices[tier]

    try:
        # Créer la session de paiement
        session = stripe.checkout.Session.create(
            customer_email=user_email,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': price_info['name'],
                        'description': price_info['description'],
                    },
                    'unit_amount': price_info['amount'],
                    'recurring': {
                        'interval': 'month',
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=cancel_url,
            metadata={
                'tier': tier,
                'user_email': user_email,
            },
        )

        return True, session.url, ""

    except stripe.error.StripeError as e:
        return False, None, f"Erreur Stripe : {str(e)}"
    except Exception as e:
        return False, None, f"Erreur : {str(e)}"


def create_one_time_payment_session(
    user_email: str,
    tier: str,
    success_url: str,
    cancel_url: str
) -> Tuple[bool, Optional[str], str]:
    """Créer une session de paiement unique (pas abonnement).

    Args:
        user_email: Email de l'utilisateur
        tier: Tier à acheter
        success_url: URL de redirection après succès
        cancel_url: URL de redirection après annulation

    Returns:
        (success, checkout_url, error_message)
    """
    if not init_stripe():
        return False, None, "Configuration Stripe manquante"

    # Prix uniques (exemple : accès à vie)
    prices = {
        "pro_lifetime": {
            "name": "Plan Pro - Accès à Vie",
            "amount": 29900,  # 299€
            "description": "Accès illimité à vie au plan Pro"
        },
        "business_lifetime": {
            "name": "Plan Business - Accès à Vie",
            "amount": 99900,  # 999€
            "description": "Accès illimité à vie au plan Business"
        }
    }

    if tier not in prices:
        return False, None, "Tier invalide"

    price_info = prices[tier]

    try:
        session = stripe.checkout.Session.create(
            customer_email=user_email,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': price_info['name'],
                        'description': price_info['description'],
                    },
                    'unit_amount': price_info['amount'],
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=cancel_url,
            metadata={
                'tier': tier.replace('_lifetime', ''),
                'user_email': user_email,
                'payment_type': 'lifetime',
            },
        )

        return True, session.url, ""

    except stripe.error.StripeError as e:
        return False, None, f"Erreur Stripe : {str(e)}"
    except Exception as e:
        return False, None, f"Erreur : {str(e)}"


def retrieve_checkout_session(session_id: str) -> Optional[dict]:
    """Récupérer les détails d'une session de paiement.

    Args:
        session_id: ID de la session Stripe

    Returns:
        dict avec les détails ou None si erreur
    """
    if not init_stripe():
        return None

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return {
            'id': session.id,
            'customer_email': session.customer_email,
            'payment_status': session.payment_status,
            'metadata': session.metadata,
        }
    except Exception:
        return None


def create_customer_portal_session(
    customer_id: str,
    return_url: str
) -> Tuple[bool, Optional[str], str]:
    """Créer une session du portail client Stripe.

    Permet au client de gérer son abonnement, paiements, factures.

    Args:
        customer_id: ID client Stripe
        return_url: URL de retour après gestion

    Returns:
        (success, portal_url, error_message)
    """
    if not init_stripe():
        return False, None, "Configuration Stripe manquante"

    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return True, session.url, ""
    except stripe.error.StripeError as e:
        return False, None, f"Erreur Stripe : {str(e)}"
    except Exception as e:
        return False, None, f"Erreur : {str(e)}"


def handle_webhook_event(payload: str, signature: str, webhook_secret: str) -> dict:
    """Traiter un événement webhook Stripe.

    Args:
        payload: Corps de la requête webhook
        signature: Signature Stripe
        webhook_secret: Secret du webhook

    Returns:
        dict avec type d'événement et données
    """
    try:
        event = stripe.Webhook.construct_event(
            payload, signature, webhook_secret
        )

        event_type = event['type']
        data = event['data']['object']

        return {
            'success': True,
            'type': event_type,
            'data': data,
        }

    except ValueError:
        return {'success': False, 'error': 'Invalid payload'}
    except stripe.error.SignatureVerificationError:
        return {'success': False, 'error': 'Invalid signature'}


def get_subscription_status(subscription_id: str) -> Optional[str]:
    """Récupérer le statut d'un abonnement.

    Args:
        subscription_id: ID de l'abonnement Stripe

    Returns:
        Statut (active, canceled, etc.) ou None
    """
    if not init_stripe():
        return None

    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        return subscription.status
    except Exception:
        return None


def cancel_subscription(subscription_id: str) -> Tuple[bool, str]:
    """Annuler un abonnement.

    Args:
        subscription_id: ID de l'abonnement

    Returns:
        (success, message)
    """
    if not init_stripe():
        return False, "Configuration Stripe manquante"

    try:
        subscription = stripe.Subscription.delete(subscription_id)
        return True, "Abonnement annulé avec succès"
    except stripe.error.StripeError as e:
        return False, f"Erreur : {str(e)}"
    except Exception as e:
        return False, f"Erreur : {str(e)}"
