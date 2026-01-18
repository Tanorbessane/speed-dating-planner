"""Page Configuration - Paramètres événement."""

import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH pour permettre les imports depuis src/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from src.models import PlanningConfig
from src.validation import validate_config, InvalidConfigurationError

st.set_page_config(page_title="Configuration", page_icon="⚙️")

st.title("⚙️ Configuration de l'Événement")

st.markdown("""
Définissez les paramètres de votre événement. Le système validera automatiquement
que votre configuration est réalisable.
""")

st.divider()

# Vérifier si participants importés
participants_imported = (
    "participants" in st.session_state and st.session_state.participants is not None
)

if participants_imported:
    n_participants = len(st.session_state.participants)
    st.info(
        f"🔒 **{n_participants} participant(s) importé(s)** : "
        f"le paramètre N est automatiquement défini. "
        f"Pour modifier N, supprimez d'abord la liste de participants (page 👥 Participants)."
    )

# Formulaire de configuration
with st.form("config_form"):
    st.markdown("### 🎯 Paramètres")

    col1, col2 = st.columns(2)

    with col1:
        # Verrouiller N si participants importés
        if participants_imported:
            N = n_participants
            st.number_input(
                "👥 Nombre de participants (N)",
                min_value=2,
                max_value=1000,
                value=N,
                step=1,
                help="Défini automatiquement par l'import de participants (verrouillé)",
                disabled=True,
            )
        else:
            N = st.number_input(
                "👥 Nombre de participants (N)",
                min_value=2,
                max_value=1000,
                value=st.session_state.get("N", 30),
                step=1,
                help="Nombre total de personnes participant à l'événement",
            )

        X = st.number_input(
            "🎲 Nombre de tables (X)",
            min_value=1,
            max_value=200,
            value=st.session_state.get("X", 5),
            step=1,
            help="Nombre de tables disponibles par session",
        )

    with col2:
        x = st.number_input(
            "🪑 Capacité par table (x)",
            min_value=2,
            max_value=20,
            value=st.session_state.get("x", 6),
            step=1,
            help="Nombre maximum de personnes par table",
        )

        S = st.number_input(
            "🔄 Nombre de sessions (S)",
            min_value=1,
            max_value=50,
            value=st.session_state.get("S", 6),
            step=1,
            help="Nombre de rotations/rounds de l'événement",
        )

    st.divider()

    # Presets (désactivés si participants importés)
    if not participants_imported:
        st.markdown("### 📋 Configurations Pré-définies")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.form_submit_button("Petit (N=30)", use_container_width=True):
                N, X, x, S = 30, 5, 6, 6

        with col2:
            if st.form_submit_button("Moyen (N=100)", use_container_width=True):
                N, X, x, S = 100, 20, 5, 10

        with col3:
            if st.form_submit_button("Grand (N=300)", use_container_width=True):
                N, X, x, S = 300, 60, 5, 15
    else:
        st.markdown("### 📋 Configurations Pré-définies")
        st.info("ℹ️ Presets désactivés : N est défini par l'import de participants")

    submitted = st.form_submit_button("✅ Valider Configuration", type="primary")

# Traitement formulaire
if submitted:
    try:
        # Créer et valider config
        config = PlanningConfig(N=N, X=X, x=x, S=S)
        validate_config(config)

        # Sauvegarder dans session state
        st.session_state.N = N
        st.session_state.X = X
        st.session_state.x = x
        st.session_state.S = S
        st.session_state.config = config

        st.success("✅ Configuration validée avec succès !")
        st.info("👉 Allez dans **🎯 Génération** pour créer votre planning.")

        # Afficher résumé
        st.markdown("### 📊 Résumé")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Participants", N)
            st.metric("Tables", X)

        with col2:
            st.metric("Capacité/table", x)
            st.metric("Sessions", S)

        # Calculs théoriques
        capacity_total = X * x
        paires_max_theoriques = N * (N - 1) // 2
        paires_par_session = (N * (x - 1)) // 2
        paires_totales_sessions = paires_par_session * S

        st.markdown("### 🔢 Estimations")
        st.metric("Capacité totale", f"{capacity_total} places")
        st.metric("Places libres", f"{capacity_total - N} places")
        st.metric("Paires max possibles", f"{paires_max_theoriques}")
        st.metric("Paires créées (estimation)", f"~{min(paires_totales_sessions, paires_max_theoriques)}")

    except InvalidConfigurationError as e:
        st.error(f"❌ Configuration invalide : {e}")
    except Exception as e:
        st.error(f"❌ Erreur inattendue : {e}")

# Afficher config actuelle si existe
st.divider()
st.markdown("### 🔍 Configuration Actuelle")

if "config" in st.session_state and st.session_state.config is not None:
    config = st.session_state.config
    st.success(f"""
    ✅ Configuration active :
    - **{config.N}** participants
    - **{config.X}** tables de **{config.x}** places
    - **{config.S}** sessions
    """)
else:
    st.warning("⚠️ Aucune configuration définie. Remplissez le formulaire ci-dessus.")
