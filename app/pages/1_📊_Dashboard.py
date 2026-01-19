"""Page Dashboard - Home Page Produit (Story 5.5).

Dashboard principal affichant :
- Score qualité global (0-100) avec badge visuel
- KPIs principaux (6 métriques clés)
- Interprétations automatiques
- Actions recommandées
- Navigation rapide vers autres pages
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH pour permettre les imports depuis src/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from src.analysis import compute_meetings_matrix, compute_matrix_statistics, compute_quality_score

# Import auth et stripe
sys.path.append(str(Path(__file__).parent.parent))
from auth import require_auth, init_session_state, show_user_info
from stripe_integration import retrieve_checkout_session

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

# Auth required
init_session_state()
if not require_auth():
    st.stop()

show_user_info()

# ===== VÉRIFIER SI PAIEMENT RÉUSSI =====
query_params = st.query_params
session_id = query_params.get("session_id", None)

if session_id:
    # Afficher confirmation de paiement
    st.balloons()

    st.markdown("""
    <div style='background: linear-gradient(135deg, #48bb78 0%, #38a169 100%); padding: 30px; border-radius: 15px; color: white; text-align: center; margin-bottom: 30px;'>
        <h1 style='font-size: 3rem; margin: 0;'>🎉</h1>
        <h2 style='margin: 20px 0 10px 0;'>Paiement Réussi !</h2>
        <p style='font-size: 1.2rem; margin: 0;'>Votre abonnement a été activé</p>
    </div>
    """, unsafe_allow_html=True)

    # Récupérer les détails
    session_details = retrieve_checkout_session(session_id)

    if session_details:
        col1, col2 = st.columns(2)

        with col1:
            st.success(f"""
            **📧 Email de confirmation**

            {session_details.get('customer_email', 'N/A')}
            """)

        with col2:
            tier = session_details.get('metadata', {}).get('tier', 'N/A').upper()
            st.success(f"""
            **📦 Plan activé**

            {tier}
            """)

    st.warning("""
    ⏳ **Activation de votre compte**

    Votre plan sera activé automatiquement dans les prochaines minutes.
    Vous pouvez déjà commencer à créer des plannings !
    """)

    st.divider()

    # Nettoyer l'URL (enlever session_id)
    if st.button("✅ Compris, aller au Dashboard", type="primary", use_container_width=True):
        st.query_params.clear()
        st.rerun()

# ===== VÉRIFIER PLANNING EXISTE =====
if "planning" not in st.session_state or st.session_state.planning is None:
    st.title("📊 Dashboard - Speed Dating Planner")

    st.info("""
    👋 **Bienvenue dans Speed Dating Planner !**

    Pour commencer, vous devez générer un planning :
    1. Configurez les paramètres dans **⚙️ Configuration**
    2. (Optionnel) Importez vos participants dans **👥 Participants**
    3. Générez votre planning dans **🎯 Génération**
    4. Revenez ici pour voir la qualité !
    """)

    if st.button("🚀 Aller à Configuration", type="primary", use_container_width=True):
        st.switch_page("pages/2_⚙️_Configuration.py")

    st.stop()

# ===== RÉCUPÉRER DONNÉES =====
planning = st.session_state.planning
metrics = st.session_state.metrics
config = st.session_state.config
participants_df = st.session_state.get("participants", None)

# Calculer matrice et stats
with st.spinner("Calcul métriques qualité..."):
    matrix = compute_meetings_matrix(planning, config.N)
    stats = compute_matrix_statistics(matrix)

    # Calculer score qualité
    quality = compute_quality_score(metrics, stats)

# ===== HERO SECTION =====
st.title("📊 Dashboard - Planning Optimisé")

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.markdown(f"""
    ### {quality['emoji']} Qualité : **{quality['grade']}** ({quality['score']}/100)

    {config.N} participants • {config.S} sessions • {stats['coverage_rate']:.1f}% couverture
    """)

with col2:
    st.metric(
        "Score Qualité",
        f"{quality['score']}/100",
        delta=f"{quality['grade']}",
        delta_color="off"
    )

with col3:
    if st.button("🗺️ Voir Heatmap", use_container_width=True):
        st.switch_page("pages/4_📈_Résultats.py")

st.divider()

# ===== KPIS PRINCIPAUX =====
st.markdown("### 📊 KPIs Principaux")

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("👥 Participants", config.N)

with col2:
    coverage_delta = f"+{stats['coverage_rate']:.0f}%" if stats['coverage_rate'] > 0 else "0%"
    st.metric("📈 Couverture", f"{stats['coverage_rate']:.1f}%", delta=coverage_delta, delta_color="off")

with col3:
    equity_emoji = "✅" if metrics.equity_gap <= 1 else "⚠️"
    st.metric(f"{equity_emoji} Équité", f"Gap: {metrics.equity_gap}")

with col4:
    repeat_pct = 100 * stats['repeat_pairs'] / stats['total_possible_pairs'] if stats['total_possible_pairs'] > 0 else 0
    st.metric("🔄 Répétitions", f"{stats['repeat_pairs']}", delta=f"{repeat_pct:.1f}%", delta_color="inverse")

with col5:
    st.metric("🎯 Max Rencontres", stats['max_meetings'])

with col6:
    st.metric("📅 Sessions", config.S)

st.divider()

# ===== INTERPRÉTATIONS =====
st.markdown("### 💡 Analyse Qualité")

# Équité
if metrics.equity_gap <= 1:
    st.success("✅ **Équité parfaite** : Tous les participants ont un nombre de rencontres équilibré (FR6 respecté)")
else:
    st.warning(f"⚠️ **Équité à améliorer** : Écart de {metrics.equity_gap} rencontres entre participants. Objectif : ≤ 1")

# Couverture
if stats['coverage_rate'] >= 90:
    st.success(f"✅ **Excellente couverture** : {stats['coverage_rate']:.1f}% des paires se sont rencontrées")
elif stats['coverage_rate'] >= 70:
    st.info(f"ℹ️ **Bonne couverture** : {stats['coverage_rate']:.1f}% des paires se sont rencontrées")
else:
    st.warning(f"⚠️ **Couverture à améliorer** : Seulement {stats['coverage_rate']:.1f}% des paires rencontrées. Augmentez le nombre de sessions.")

# Répétitions
if stats['repeat_pairs'] == 0:
    st.success("✅ **Planning optimal** : Aucune répétition ! Chaque paire ne se rencontre qu'une fois (FR5)")
elif repeat_pct < 10:
    st.info(f"ℹ️ **Répétitions acceptables** : {stats['repeat_pairs']} paires ({repeat_pct:.1f}%)")
else:
    st.warning(f"⚠️ **Nombreuses répétitions** : {stats['repeat_pairs']} paires ({repeat_pct:.1f}%). Ajustez la configuration.")

st.divider()

# ===== MÉTRIQUES DÉTAILLÉES =====
with st.expander("📊 Métriques Détaillées"):
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Distribution Rencontres**")
        st.write(f"- Min : {metrics.min_unique} rencontres")
        st.write(f"- Max : {metrics.max_unique} rencontres")
        st.write(f"- Moyenne : {metrics.mean_unique:.1f} rencontres")
        st.write(f"- Equity Gap : {metrics.equity_gap}")

    with col2:
        st.markdown("**Statistiques Paires**")
        st.write(f"- Paires uniques : {metrics.total_unique_pairs}")
        st.write(f"- Répétitions : {metrics.total_repeat_pairs}")
        st.write(f"- Paires possibles : {stats['total_possible_pairs']}")
        st.write(f"- Taux unicité : {100 - repeat_pct:.1f}%")

    # VIP metrics si disponibles
    if metrics.vip_metrics:
        st.divider()
        st.markdown("**⭐ Métriques VIP**")
        vip = metrics.vip_metrics

        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**VIP ({vip.vip_count})** : {vip.vip_min_unique}-{vip.vip_max_unique} rencontres (gap: {vip.vip_equity_gap})")
        with col2:
            st.write(f"**Réguliers ({vip.non_vip_count})** : {vip.non_vip_min_unique}-{vip.non_vip_max_unique} rencontres (gap: {vip.non_vip_equity_gap})")

st.divider()

# ===== GRAPHIQUES VISUALISATION (Story 5.3) =====
with st.expander("📊 Graphiques Visualisation", expanded=False):
    st.markdown("### Distribution Rencontres")

    from src.visualizations import create_distribution_chart, create_pairs_pie_chart

    fig_dist = create_distribution_chart(
        metrics.unique_meetings_per_person,
        participants_df
    )
    st.plotly_chart(fig_dist, use_container_width=True)

    st.divider()

    st.markdown("### Répartition Paires")
    fig_pie = create_pairs_pie_chart(stats)
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# ===== ACTIONS RECOMMANDÉES =====
st.markdown("### 🎯 Prochaines Étapes")

if quality['score'] >= 90:
    st.success("🎉 Votre planning est excellent ! Vous pouvez :")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💾 Exporter CSV/JSON", use_container_width=True):
            st.switch_page("pages/4_📈_Résultats.py")
    with col2:
        if st.button("🗺️ Analyser Heatmap", use_container_width=True):
            st.switch_page("pages/4_📈_Résultats.py")
    with col3:
        if st.button("🔄 Générer Variante", use_container_width=True):
            st.switch_page("pages/3_🎯_Génération.py")
else:
    st.info("💡 Recommandations pour améliorer votre planning :")

    recommendations = []

    if metrics.equity_gap > 1:
        recommendations.append("- ⚖️ **Améliorer équité** : L'algorithme devrait avoir atteint gap ≤ 1. Vérifiez les contraintes.")

    if stats['coverage_rate'] < 70:
        recommendations.append(f"- 📈 **Augmenter couverture** : Ajoutez des sessions (actuellement {config.S})")

    if repeat_pct >= 10:
        recommendations.append("- 🔄 **Réduire répétitions** : Augmentez le nombre de participants par table ou réduisez les sessions")

    for rec in recommendations:
        st.markdown(rec)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⚙️ Modifier Configuration", use_container_width=True):
            st.switch_page("pages/2_⚙️_Configuration.py")
    with col2:
        if st.button("🔄 Régénérer Planning", use_container_width=True):
            st.switch_page("pages/3_🎯_Génération.py")
