"""Page de succès après paiement Stripe."""

import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st

# Import auth et stripe
sys.path.append(str(Path(__file__).parent.parent))
from auth import require_auth, init_session_state, show_user_info
from stripe_integration import retrieve_checkout_session

st.set_page_config(page_title="Paiement Réussi", page_icon="✅", layout="centered")

# Auth required
init_session_state()
if not require_auth():
    st.stop()

show_user_info()

# Récupérer session_id depuis URL
query_params = st.query_params
session_id = query_params.get("session_id", None)

st.markdown("""
<div style='text-align: center; padding: 40px 20px;'>
    <h1 style='color: #48bb78; font-size: 3rem;'>🎉</h1>
    <h1 style='color: #2d3748; margin: 20px 0;'>Paiement Réussi !</h1>
</div>
""", unsafe_allow_html=True)

st.divider()

if session_id:
    # Récupérer les détails de la session
    session_details = retrieve_checkout_session(session_id)

    if session_details:
        st.success("✅ Votre paiement a été traité avec succès !")

        # Afficher les détails
        col1, col2 = st.columns(2)

        with col1:
            st.info(f"""
            **📧 Email**
            {session_details.get('customer_email', 'N/A')}
            """)

        with col2:
            tier = session_details.get('metadata', {}).get('tier', 'N/A').upper()
            st.info(f"""
            **📦 Plan**
            {tier}
            """)

        st.divider()

        # Message de mise à jour du tier
        st.warning("""
        ⏳ **Mise à jour de votre compte en cours...**

        Votre plan sera activé automatiquement dans quelques minutes.
        Si ce n'est pas le cas après 5 minutes, contactez le support : support@speeddating-planner.com
        """)

        # TODO: Mettre à jour le tier automatiquement via webhook
        # Pour l'instant, afficher un message manuel

        st.info("""
        **🔄 Activation manuelle temporaire**

        En attendant l'activation automatique, contactez-nous avec votre email et nous activerons votre plan immédiatement.
        """)

        st.divider()

        # Boutons d'action
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🏠 Retour à l'Accueil", use_container_width=True, type="primary"):
                st.switch_page("main.py")

        with col2:
            if st.button("🎯 Créer un Planning", use_container_width=True):
                st.switch_page("pages/2_⚙️_Configuration.py")

    else:
        st.error("❌ Impossible de récupérer les détails du paiement")
        st.info("Votre paiement a bien été effectué. Contactez le support si besoin.")

else:
    # Pas de session_id dans l'URL
    st.info("""
    Cette page confirme votre paiement après un achat.

    Si vous venez d'effectuer un paiement et ne voyez pas de confirmation,
    contactez le support : support@speeddating-planner.com
    """)

    if st.button("🏠 Retour à l'Accueil", use_container_width=True, type="primary"):
        st.switch_page("main.py")

st.divider()

# FAQ rapide
with st.expander("❓ Questions Fréquentes"):
    st.markdown("""
    **Quand mon plan sera-t-il activé ?**
    Votre plan est généralement activé dans les 2-5 minutes. Vous recevrez un email de confirmation.

    **Comment accéder à mes factures ?**
    Vous recevrez les factures par email. Vous pouvez aussi les consulter dans votre espace client Stripe.

    **Puis-je annuler mon abonnement ?**
    Oui, à tout moment depuis la page Pricing. Aucun remboursement au prorata.

    **Comment contacter le support ?**
    Email : support@speeddating-planner.com (réponse sous 24h)
    """)
