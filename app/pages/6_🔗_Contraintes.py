"""Page Contraintes - Groupes cohésifs et exclusifs."""

import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH pour permettre les imports depuis src/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from src.models import (
    GroupConstraint,
    GroupConstraintType,
    PlanningConstraints,
    PlanningConfig,
)

# Import auth
sys.path.append(str(Path(__file__).parent.parent))
from auth import require_auth, init_session_state, show_user_info

st.set_page_config(page_title="Contraintes", page_icon="🔗", layout="wide")

# Auth required
init_session_state()
if not require_auth():
    st.stop()

show_user_info()

st.title("🔗 Contraintes de Groupes")

st.markdown("""
**Définissez des contraintes de groupes** pour contrôler comment certains participants
sont placés aux tables :

- **👥 Groupes Cohésifs** (Must Be Together) : Participants toujours à la même table
- **🚫 Groupes Exclusifs** (Must Be Separate) : Participants jamais à la même table
""")

st.divider()

# Vérifier si participants importés
if "participants" not in st.session_state or st.session_state.participants is None:
    st.warning(
        "⚠️ **Aucun participant importé**. "
        "Rendez-vous sur la page **👥 Participants** pour importer une liste."
    )
    st.stop()

participants_df = st.session_state.participants
participant_ids = participants_df["id"].tolist()
participant_names = [
    f"{row['id']}: {row.get('prenom', '')} {row['nom']}".strip()
    for _, row in participants_df.iterrows()
]

# Initialiser contraintes dans session_state si absent
if "constraints" not in st.session_state:
    st.session_state.constraints = PlanningConstraints(
        cohesive_groups=[], exclusive_groups=[]
    )

constraints = st.session_state.constraints

# ===== SECTION 1: GROUPES COHÉSIFS =====
st.markdown("### 👥 Groupes Cohésifs (Must Be Together)")
st.markdown(
    "Les membres d'un groupe cohésif sont **toujours placés à la même table** dans chaque session."
)

with st.expander("➕ Ajouter Groupe Cohésif", expanded=False):
    with st.form("cohesive_group_form", clear_on_submit=True):
        cohesive_name = st.text_input(
            "Nom du groupe",
            placeholder="ex: Couple 1, Équipe Marketing, Famille Dupont",
            help="Nom descriptif pour identifier ce groupe",
        )

        cohesive_participants = st.multiselect(
            "Sélectionner participants (minimum 2)",
            options=participant_ids,
            format_func=lambda pid: participant_names[participant_ids.index(pid)],
            help="Choisissez au moins 2 participants qui doivent rester ensemble",
        )

        submitted_cohesive = st.form_submit_button(
            "✅ Créer Groupe Cohésif", use_container_width=True, type="primary"
        )

        if submitted_cohesive:
            if not cohesive_name:
                st.error("❌ Le nom du groupe est requis")
            elif len(cohesive_participants) < 2:
                st.error("❌ Un groupe cohésif doit contenir au moins 2 participants")
            else:
                # Créer contrainte
                try:
                    new_group = GroupConstraint(
                        name=cohesive_name,
                        constraint_type=GroupConstraintType.MUST_BE_TOGETHER,
                        participant_ids=set(cohesive_participants),
                    )

                    # Ajouter à contraintes
                    st.session_state.constraints.cohesive_groups.append(new_group)
                    st.success(
                        f"✅ Groupe cohésif **{cohesive_name}** créé avec "
                        f"{len(cohesive_participants)} participant(s)"
                    )
                    st.rerun()

                except ValueError as e:
                    st.error(f"❌ Erreur: {str(e)}")

# Afficher groupes cohésifs actuels
if constraints.cohesive_groups:
    st.markdown(f"**{len(constraints.cohesive_groups)} groupe(s) cohésif(s) défini(s)** :")

    for idx, group in enumerate(constraints.cohesive_groups):
        with st.container():
            col1, col2 = st.columns([4, 1])

            with col1:
                st.markdown(f"**{group.name}** ({len(group.participant_ids)} membres)")
                # Afficher noms des participants
                member_names = [
                    participant_names[participant_ids.index(pid)]
                    for pid in group.participant_ids
                ]
                st.caption(", ".join(member_names))

            with col2:
                if st.button(
                    "🗑️ Supprimer",
                    key=f"delete_cohesive_{idx}",
                    use_container_width=True,
                ):
                    st.session_state.constraints.cohesive_groups.pop(idx)
                    st.rerun()

            st.divider()
else:
    st.info("ℹ️ Aucun groupe cohésif défini")

st.divider()

# ===== SECTION 2: GROUPES EXCLUSIFS =====
st.markdown("### 🚫 Groupes Exclusifs (Must Be Separate)")
st.markdown(
    "Les membres d'un groupe exclusif ne sont **jamais placés à la même table** (séparés dans toutes les sessions)."
)

with st.expander("➕ Ajouter Groupe Exclusif", expanded=False):
    with st.form("exclusive_group_form", clear_on_submit=True):
        exclusive_name = st.text_input(
            "Nom du groupe",
            placeholder="ex: Concurrents A-B, Conflits Équipe X-Y",
            help="Nom descriptif pour identifier ce groupe exclusif",
        )

        exclusive_participants = st.multiselect(
            "Sélectionner participants (minimum 2)",
            options=participant_ids,
            format_func=lambda pid: participant_names[participant_ids.index(pid)],
            help="Choisissez au moins 2 participants qui ne doivent jamais être ensemble",
        )

        submitted_exclusive = st.form_submit_button(
            "✅ Créer Groupe Exclusif", use_container_width=True, type="primary"
        )

        if submitted_exclusive:
            if not exclusive_name:
                st.error("❌ Le nom du groupe est requis")
            elif len(exclusive_participants) < 2:
                st.error("❌ Un groupe exclusif doit contenir au moins 2 participants")
            else:
                # Créer contrainte
                try:
                    new_group = GroupConstraint(
                        name=exclusive_name,
                        constraint_type=GroupConstraintType.MUST_BE_SEPARATE,
                        participant_ids=set(exclusive_participants),
                    )

                    # Ajouter à contraintes
                    st.session_state.constraints.exclusive_groups.append(new_group)
                    st.success(
                        f"✅ Groupe exclusif **{exclusive_name}** créé avec "
                        f"{len(exclusive_participants)} participant(s)"
                    )
                    st.rerun()

                except ValueError as e:
                    st.error(f"❌ Erreur: {str(e)}")

# Afficher groupes exclusifs actuels
if constraints.exclusive_groups:
    st.markdown(f"**{len(constraints.exclusive_groups)} groupe(s) exclusif(s) défini(s)** :")

    for idx, group in enumerate(constraints.exclusive_groups):
        with st.container():
            col1, col2 = st.columns([4, 1])

            with col1:
                st.markdown(f"**{group.name}** ({len(group.participant_ids)} membres)")
                # Afficher noms des participants
                member_names = [
                    participant_names[participant_ids.index(pid)]
                    for pid in group.participant_ids
                ]
                st.caption(", ".join(member_names))

            with col2:
                if st.button(
                    "🗑️ Supprimer",
                    key=f"delete_exclusive_{idx}",
                    use_container_width=True,
                ):
                    st.session_state.constraints.exclusive_groups.pop(idx)
                    st.rerun()

            st.divider()
else:
    st.info("ℹ️ Aucun groupe exclusif défini")

st.divider()

# ===== SECTION 3: VALIDATION =====
st.markdown("### ✅ Validation des Contraintes")

# Vérifier si configuration existe
if "N" not in st.session_state or "X" not in st.session_state or "x" not in st.session_state or "S" not in st.session_state:
    st.warning(
        "⚠️ Configuration incomplète. Rendez-vous sur **⚙️ Configuration** pour définir N, X, x, S."
    )
else:
    # Créer config pour validation
    config = PlanningConfig(
        N=st.session_state.N,
        X=st.session_state.X,
        x=st.session_state.x,
        S=st.session_state.S,
    )

    # Valider contraintes
    validation_errors = constraints.validate(config)

    if validation_errors:
        st.error("❌ **Contraintes invalides détectées** :")
        for error in validation_errors:
            st.warning(error)
    else:
        st.success("✅ **Toutes les contraintes sont valides** et respectent la configuration !")

        # Afficher résumé
        total_constraints = len(constraints.cohesive_groups) + len(
            constraints.exclusive_groups
        )
        if total_constraints > 0:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Groupes Cohésifs", len(constraints.cohesive_groups))
            with col2:
                st.metric("Groupes Exclusifs", len(constraints.exclusive_groups))
            with col3:
                st.metric("Total Contraintes", total_constraints)

st.divider()

# ===== SECTION 4: ACTIONS GLOBALES =====
st.markdown("### 🔧 Actions Globales")

col1, col2 = st.columns(2)

with col1:
    if st.button("🗑️ Supprimer Toutes les Contraintes", use_container_width=True):
        st.session_state.constraints = PlanningConstraints(
            cohesive_groups=[], exclusive_groups=[]
        )
        st.success("✅ Toutes les contraintes ont été supprimées")
        st.rerun()

with col2:
    total_constraints = len(constraints.cohesive_groups) + len(
        constraints.exclusive_groups
    )
    if total_constraints > 0:
        st.info(
            f"ℹ️ **{total_constraints} contrainte(s)** définie(s) et prête(s) "
            f"pour la génération du planning"
        )
    else:
        st.info("ℹ️ Aucune contrainte définie (génération standard)")

st.divider()

# ===== FOOTER: AIDE =====
with st.expander("❓ Aide - Comment utiliser les contraintes", expanded=False):
    st.markdown("""
    ### Groupes Cohésifs (Must Be Together)

    Les participants d'un groupe cohésif sont **toujours placés à la même table** dans toutes les sessions.

    **Cas d'usage** :
    - Couples qui veulent rester ensemble
    - Équipes d'une même entreprise
    - Familles ou groupes d'amis

    **Limitations** :
    - La taille du groupe ne peut pas dépasser la capacité d'une table (x)
    - Un participant ne peut appartenir qu'à un seul groupe cohésif

    ---

    ### Groupes Exclusifs (Must Be Separate)

    Les participants d'un groupe exclusif ne sont **jamais placés à la même table**.

    **Cas d'usage** :
    - Concurrents directs à séparer
    - Personnes en conflit
    - Participants devant éviter certaines interactions

    **Limitations** :
    - Aucune limitation de taille
    - Un participant peut appartenir à plusieurs groupes exclusifs

    ---

    ### Validation

    Les contraintes sont automatiquement validées :
    - ✅ Taille des groupes cohésifs ≤ capacité table
    - ✅ Pas de participant dans plusieurs groupes cohésifs
    - ✅ Pas de conflit entre groupes cohésifs et exclusifs

    Les contraintes **invalides** empêcheront la génération du planning.
    """)
