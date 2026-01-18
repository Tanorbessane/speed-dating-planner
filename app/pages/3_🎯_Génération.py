"""Page Génération - Créer planning optimisé."""

import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH pour permettre les imports depuis src/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import time
from src.planner import generate_optimized_planning
from src.display_utils import format_table_participants

st.set_page_config(page_title="Génération", page_icon="🎯")

st.title("🎯 Génération de Planning")

# Vérifier config existe
if "config" not in st.session_state or st.session_state.config is None:
    st.error("❌ Aucune configuration définie. Allez dans **⚙️ Configuration** d'abord.")
    st.stop()

config = st.session_state.config

# Récupérer contraintes si définies
constraints = st.session_state.get("constraints", None)
has_constraints = (
    constraints is not None
    and (len(constraints.cohesive_groups) > 0 or len(constraints.exclusive_groups) > 0)
)

st.markdown(f"""
### 📋 Configuration actuelle

- **👥 Participants** : {config.N}
- **🎲 Tables** : {config.X} tables de {config.x} places
- **🔄 Sessions** : {config.S}
""")

# Afficher contraintes actives
if has_constraints:
    st.success(f"""
    ✅ **Contraintes actives** :
    - {len(constraints.cohesive_groups)} groupe(s) cohésif(s) (must be together)
    - {len(constraints.exclusive_groups)} groupe(s) exclusif(s) (must be separate)
    """)

    # Validation contraintes
    validation_errors = constraints.validate(config)
    if validation_errors:
        st.error("❌ **Contraintes invalides détectées** :")
        for error in validation_errors:
            st.warning(error)
        st.error("⚠️ **Génération bloquée** : corrigez les contraintes dans **🔗 Contraintes**")
        st.stop()
else:
    st.info("ℹ️ Aucune contrainte définie (génération standard)")

st.divider()

# Paramètres génération
st.markdown("### ⚙️ Paramètres de génération")

col1, col2 = st.columns(2)

with col1:
    seed = st.number_input(
        "🎲 Seed aléatoire",
        min_value=0,
        max_value=9999,
        value=42,
        step=1,
        help="Pour reproductibilité : même seed = même planning",
    )

with col2:
    st.info("""
    **💡 Astuce**

    Changez le seed pour générer
    différentes variantes du planning
    et choisir la meilleure.
    """)

st.divider()

# Bouton génération
if st.button("🚀 Générer Planning Optimisé", type="primary", use_container_width=True):
    with st.spinner("Génération en cours..."):
        # Barre de progression
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Phase 1: Baseline
        status_text.text("Phase 1/3 : Génération baseline (round-robin)...")
        progress_bar.progress(10)
        time.sleep(0.1)

        # Phase 2: Amélioration
        status_text.text("Phase 2/3 : Amélioration locale (optimisation)...")
        progress_bar.progress(40)

        # Préparer participants si chargés (Story 4.4)
        participants = None
        if "participants" in st.session_state and st.session_state.participants is not None:
            from src.models import Participant
            import pandas as pd

            participants_df = st.session_state.participants
            # Convertir DataFrame → List[Participant]
            participants = [
                Participant(
                    id=row["id"],
                    nom=row["nom"],
                    prenom=row["prenom"] if pd.notna(row.get("prenom")) else None,
                    email=row["email"] if pd.notna(row.get("email")) else None,
                    groupe=row["groupe"] if pd.notna(row.get("groupe")) else None,
                    tags=row["tags"] if row.get("tags") else [],
                    is_vip=row.get("is_vip", False),
                )
                for _, row in participants_df.iterrows()
            ]

        # Génération réelle (avec contraintes et participants si définis)
        start_time = time.time()
        planning, metrics = generate_optimized_planning(
            config,
            seed=seed,
            constraints=constraints if has_constraints else None,
            participants=participants,
        )
        duration = time.time() - start_time

        # Phase 3: Équité
        status_text.text("Phase 3/3 : Enforcement équité (FR6)...")
        progress_bar.progress(80)
        time.sleep(0.1)

        # Terminé
        progress_bar.progress(100)
        status_text.text("✅ Génération terminée !")
        time.sleep(0.3)

    # Sauvegarder dans session state
    st.session_state.planning = planning
    st.session_state.metrics = metrics
    st.session_state.generation_time = duration
    st.session_state.seed_used = seed

    # Afficher résultats
    st.success(f"🎉 Planning généré avec succès en {duration:.3f}s !")

    st.divider()

    # Métriques rapides
    st.markdown("### 📊 Résultats Rapides")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🤝 Paires Uniques", metrics.total_unique_pairs)

    with col2:
        st.metric("🔄 Répétitions", metrics.total_repeat_pairs)

    with col3:
        if metrics.equity_gap <= 1:
            st.metric("⚖️ Equity Gap", metrics.equity_gap, delta="✅")
        else:
            st.metric("⚖️ Equity Gap", metrics.equity_gap, delta="⚠️")

    with col4:
        # Performance check
        target_time = 2.0 if config.N <= 100 else (5.0 if config.N <= 300 else 30.0)
        if duration < target_time:
            st.metric("⚡ Performance", "✅ OK", delta=f"{duration:.2f}s")
        else:
            st.metric("⚡ Performance", "⚠️ Lent", delta=f"{duration:.2f}s")

    st.divider()

    # ===== MÉTRIQUES VIP RAPIDES (Story 4.4) =====
    if metrics.vip_metrics:
        st.markdown("### ⭐ Aperçu VIP")

        vip = metrics.vip_metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("VIP", vip.vip_count)

        with col2:
            st.metric("Réguliers", vip.non_vip_count)

        with col3:
            if vip.vip_count > 0 and vip.non_vip_count > 0:
                vip_advantage = vip.vip_min_unique - vip.non_vip_min_unique
                st.metric("Avantage VIP", f"+{vip_advantage}", delta="⭐" if vip_advantage > 0 else "")

        st.info(
            f"VIP: min={vip.vip_min_unique}, max={vip.vip_max_unique}, gap={vip.vip_equity_gap} | "
            f"Réguliers: min={vip.non_vip_min_unique}, max={vip.non_vip_max_unique}, gap={vip.non_vip_equity_gap}"
        )

        st.divider()

    # Distribution rencontres
    st.markdown("### 📈 Distribution Rencontres Uniques")
    import pandas as pd

    data = pd.DataFrame(
        {
            "Participant": range(config.N),
            "Rencontres Uniques": metrics.unique_meetings_per_person,
        }
    )

    st.bar_chart(data.set_index("Participant"))

    st.info(f"""
    **Statistiques** :
    - Min : {metrics.min_unique} rencontres
    - Max : {metrics.max_unique} rencontres
    - Moyenne : {metrics.mean_unique:.1f} rencontres
    - Écart (equity_gap) : {metrics.equity_gap}
    """)

    st.divider()

    # Actions suivantes
    st.markdown("### 🎯 Prochaines étapes")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📊 Voir Dashboard", use_container_width=True):
            st.info("Allez dans **📊 Dashboard** via menu latéral")

    with col2:
        if st.button("💾 Exporter Résultats", use_container_width=True):
            st.info("Allez dans **📈 Résultats** via menu latéral")

# Si planning déjà généré, afficher infos
elif "planning" in st.session_state and st.session_state.planning is not None:
    st.info(f"""
    ℹ️ Un planning existe déjà (seed={st.session_state.seed_used}).

    Cliquez sur **Générer** pour en créer un nouveau (écrasera l'ancien).
    """)

    metrics = st.session_state.metrics
    st.metric("Equity Gap actuel", metrics.equity_gap)
    st.metric("Répétitions actuelles", metrics.total_repeat_pairs)
