"""Intégration Stripe pour les paiements et abonnements.

Gestion des checkout sessions, webhooks et mise à jour des tiers utilisateurs.
"""

import logging
import os
import stripe
import streamlit as st
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def init_stripe() -> bool:
    """Initialiser Stripe avec les clés API depuis secrets ou environment variables.

    Ordre de priorité:
    1. Streamlit secrets (.streamlit/secrets.toml) - RECOMMANDÉ pour Streamlit
    2. Variables d'environnement (.env) - Fallback pour déploiements non-Streamlit

    Returns:
        True si initialisation réussie, False sinon

    Note:
        Voir .streamlit/secrets.toml.example pour la configuration des secrets.
    """
    try:
        # Essayer d'abord Streamlit secrets (préféré)
        secret_key = st.secrets["stripe"]["secret_key"]

        # Validation format clé secrète
        if not secret_key or not secret_key.startswith(("sk_test_", "sk_live_")):
            logger.error(
                "Clé Stripe invalide : doit commencer par 'sk_test_' (test) "
                "ou 'sk_live_' (production)"
            )
            st.error("""
            ❌ **Configuration Stripe invalide**

            La clé secrète doit commencer par `sk_test_` (mode test) ou `sk_live_` (production).

            Voir `.streamlit/secrets.toml.example` pour la configuration.
            """)
            return False

        stripe.api_key = secret_key

        # Log du mode (test ou live) sans exposer la clé
        mode = "TEST" if secret_key.startswith("sk_test_") else "LIVE"
        logger.info(f"Stripe initialisé en mode {mode}")

        return True

    except KeyError:
        # Fallback sur variables d'environnement
        secret_key = os.getenv("STRIPE_SECRET_KEY")

        if not secret_key:
            logger.error(
                "Configuration Stripe manquante : aucune clé trouvée dans "
                "st.secrets['stripe']['secret_key'] ni STRIPE_SECRET_KEY"
            )
            st.error("""
            ❌ **Configuration Stripe manquante**

            Veuillez configurer vos clés API Stripe :

            **Option 1 (Recommandé pour Streamlit):**
            - Créer `.streamlit/secrets.toml` à partir de `.streamlit/secrets.toml.example`
            - Ajouter vos clés Stripe dans la section `[stripe]`

            **Option 2 (Déploiement non-Streamlit):**
            - Définir la variable d'environnement `STRIPE_SECRET_KEY`

            **Pour obtenir vos clés:**
            - Aller sur https://dashboard.stripe.com/apikeys
            - Utiliser les clés TEST pour développement (sk_test_...)
            """)
            return False

        stripe.api_key = secret_key
        mode = "TEST" if secret_key.startswith("sk_test_") else "LIVE"
        logger.info(f"Stripe initialisé depuis env vars en mode {mode}")
        return True

    except Exception as e:
        logger.exception("Erreur inattendue lors de l'initialisation Stripe")
        st.error(f"""
        ❌ **Erreur inattendue lors de la configuration Stripe**

        {str(e)}

        Veuillez vérifier votre configuration dans `.streamlit/secrets.toml`.
        """)
        return False


def get_publishable_key() -> Optional[str]:
    """Récupérer la clé publique Stripe.

    Returns:
        Clé publique (pk_test_... ou pk_live_...) ou None si non trouvée
    """
    try:
        key = st.secrets["stripe"]["publishable_key"]

        # Validation format
        if key and not key.startswith(("pk_test_", "pk_live_")):
            logger.warning(
                "Clé publique Stripe invalide : doit commencer par 'pk_test_' ou 'pk_live_'"
            )
            return None

        return key

    except KeyError:
        # Fallback environment variable
        key = os.getenv("STRIPE_PUBLISHABLE_KEY")
        if not key:
            logger.warning("Clé publique Stripe non trouvée")
        return key

    except Exception as e:
        logger.error(f"Erreur récupération clé publique : {e}")
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
