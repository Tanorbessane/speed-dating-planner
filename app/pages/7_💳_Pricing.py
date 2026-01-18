"""Page Pricing - Plans et Upgrades."""

import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH pour permettre les imports depuis src/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st

# Importer auth
import sys
sys.path.append(str(Path(__file__).parent.parent))
from auth import require_auth, init_session_state, show_user_info

st.set_page_config(page_title="Pricing", page_icon="💳", layout="wide")

init_session_state()

# Auth optionnelle pour cette page (permettre aux non-connectés de voir les prix)
if not st.session_state.authenticated:
    st.info("👋 Connectez-vous pour gérer votre abonnement")

show_user_info()

st.title("💳 Plans et Tarifs")

st.markdown("""
Choisissez le plan adapté à vos besoins. Upgrade ou downgrade à tout moment.
""")

st.divider()

# Pricing Cards
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style='border: 2px solid #e2e8f0; border-radius: 15px; padding: 30px; text-align: center;'>
        <h2>🆓 Free</h2>
        <h1 style='color: #667eea;'>0€<span style='font-size: 1.2rem; color: #4a5568;'>/mois</span></h1>
        <p style='color: #4a5568; margin: 20px 0;'>Pour tester le produit</p>
        <ul style='text-align: left; list-style: none; padding: 0;'>
            <li>✓ Jusqu'à 30 participants</li>
            <li>✓ 3 sessions maximum</li>
            <li>✓ Export CSV/JSON</li>
            <li>✓ Support communautaire</li>
            <li>✓ Analyses basiques</li>
            <li style='color: #cbd5e0;'>✗ Export PDF</li>
            <li style='color: #cbd5e0;'>✗ Gestion VIP</li>
            <li style='color: #cbd5e0;'>✗ Contraintes</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.authenticated:
        if st.session_state.user['tier'] == 'free':
            st.success("✅ Votre plan actuel")
        elif st.session_state.user['tier'] in ['pro', 'business']:
            if st.button("⬇️ Downgrade vers Free", key="downgrade_free", use_container_width=True):
                st.warning("Contactez le support pour downgrader")
    else:
        st.button("Commencer Gratuit", type="primary", use_container_width=True, disabled=True)
        st.caption("Créez un compte pour commencer")

with col2:
    st.markdown("""
    <div style='border: 3px solid #667eea; border-radius: 15px; padding: 30px; text-align: center; position: relative;'>
        <span style='position: absolute; top: -15px; left: 50%; transform: translateX(-50%); background: #667eea; color: white; padding: 5px 20px; border-radius: 20px; font-weight: 600;'>⭐ POPULAIRE</span>
        <h2>⭐ Pro</h2>
        <h1 style='color: #667eea;'>29€<span style='font-size: 1.2rem; color: #4a5568;'>/mois</span></h1>
        <p style='color: #4a5568; margin: 20px 0;'>Pour les organisateurs réguliers</p>
        <ul style='text-align: left; list-style: none; padding: 0;'>
            <li>✓ Jusqu'à 150 participants</li>
            <li>✓ Sessions illimitées</li>
            <li>✓ <strong>Export PDF professionnel</strong></li>
            <li>✓ <strong>Gestion VIP</strong></li>
            <li>✓ <strong>Analyses avancées</strong></li>
            <li>✓ Support prioritaire</li>
            <li>✓ <strong>Contraintes personnalisées</strong></li>
            <li style='color: #cbd5e0;'>✗ Multi-utilisateurs</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.authenticated:
        if st.session_state.user['tier'] == 'pro':
            st.success("✅ Votre plan actuel")
        elif st.session_state.user['tier'] == 'free':
            if st.button("⬆️ Upgrade vers Pro", key="upgrade_pro", type="primary", use_container_width=True):
                st.info("🔜 Intégration Stripe en cours. Contactez-nous : support@speeddating-planner.com")
        elif st.session_state.user['tier'] == 'business':
            if st.button("⬇️ Downgrade vers Pro", key="downgrade_pro", use_container_width=True):
                st.warning("Contactez le support pour downgrader")
    else:
        st.button("Essai 14 Jours Gratuit", type="primary", use_container_width=True, disabled=True)
        st.caption("Créez un compte pour commencer")

with col3:
    st.markdown("""
    <div style='border: 2px solid #e2e8f0; border-radius: 15px; padding: 30px; text-align: center;'>
        <h2>💎 Business</h2>
        <h1 style='color: #667eea;'>99€<span style='font-size: 1.2rem; color: #4a5568;'>/mois</span></h1>
        <p style='color: #4a5568; margin: 20px 0;'>Pour les professionnels</p>
        <ul style='text-align: left; list-style: none; padding: 0;'>
            <li>✓ <strong>Participants illimités</strong></li>
            <li>✓ <strong>Multi-utilisateurs (5)</strong></li>
            <li>✓ Toutes les features Pro</li>
            <li>✓ API access</li>
            <li>✓ White-label</li>
            <li>✓ Intégration CRM</li>
            <li>✓ Support dédié 24/7</li>
            <li>✓ Formation personnalisée</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.authenticated:
        if st.session_state.user['tier'] == 'business':
            st.success("✅ Votre plan actuel")
        else:
            if st.button("💎 Contacter Sales", key="contact_business", use_container_width=True):
                st.info("📧 Email : sales@speeddating-planner.com")
    else:
        st.button("Contacter Sales", use_container_width=True, disabled=True)
        st.caption("Créez un compte pour commencer")

st.divider()

# FAQ
with st.expander("❓ Questions Fréquentes"):
    st.markdown("""
    **Puis-je changer de plan à tout moment ?**
    Oui, upgrade ou downgrade quand vous voulez. Les changements prennent effet immédiatement.

    **Y a-t-il un engagement ?**
    Non, aucun engagement. Annulez quand vous voulez.

    **Comment se passe la facturation ?**
    Paiement mensuel par carte bancaire via Stripe (sécurisé). Facture envoyée automatiquement.

    **Puis-je essayer Pro gratuitement ?**
    Oui, 14 jours d'essai gratuit sans carte bancaire.

    **Les exports sont-ils inclus ?**
    CSV/JSON inclus dans tous les plans. PDF professionnel uniquement Pro et Business.

    **Puis-je avoir plus de 150 participants en Pro ?**
    Contactez-nous pour un plan Business personnalisé selon vos besoins.
    """)

# Testimonials
st.divider()
st.subheader("💬 Ce qu'en disent nos clients")

col1, col2 = st.columns(2)

with col1:
    st.info("""
    "Speed Dating Planner m'a fait gagner 5 heures par événement. Les plannings sont parfaits et l'export PDF est magnifique !"

    **Marie D.** - Organisatrice événements Paris
    """)

with col2:
    st.info("""
    "J'organise 10 événements par mois. Le plan Pro est rentabilisé dès le premier événement. Indispensable !"

    **Thomas R.** - Agence networking
    """)

st.divider()

# CTA Final
st.markdown("""
<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; border-radius: 15px; text-align: center; color: white;'>
    <h2>🚀 Prêt à Optimiser vos Événements ?</h2>
    <p style='font-size: 1.2rem; margin: 20px 0;'>Rejoignez des centaines d'organisateurs satisfaits</p>
</div>
""", unsafe_allow_html=True)

if not st.session_state.authenticated:
    st.info("👋 Créez un compte gratuit pour commencer")
