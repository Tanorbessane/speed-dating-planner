"""Page Participants - Import et gestion CSV/Excel."""

import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH pour permettre les imports depuis src/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import io
from typing import Dict, Optional
from src.participants import (
    parse_csv,
    parse_excel,
    validate_participants,
    normalize_dataframe,
)

# Import auth
sys.path.append(str(Path(__file__).parent.parent))
from auth import require_auth, init_session_state, show_user_info

st.set_page_config(page_title="Participants", page_icon="👥", layout="wide")

# Auth required
init_session_state()
if not require_auth():
    st.stop()

show_user_info()

st.title("👥 Gestion des Participants")

# ===== SECTION 1: TEMPLATE TÉLÉCHARGEABLE =====
with st.expander("📄 Télécharger Template CSV", expanded=False):
    st.markdown("""
    **Colonnes disponibles** :
    - `participant_id` : ID unique (optionnel, auto-généré si absent)
    - `nom` : Nom de famille (REQUIS)
    - `prenom` : Prénom (optionnel)
    - `email` : Adresse email (optionnel, validé si présent)
    - `groupe` : Groupe d'appartenance (optionnel, pour contraintes)
    - `tags` : Tags séparés par virgule (ex: "VIP,Speaker")
    - `vip` : Statut VIP (optionnel, Story 4.4, valeurs: 1/0, yes/no, true/false, vip/non)
    """)

    # Générer template exemple
    template_data = pd.DataFrame(
        {
            "participant_id": [0, 1, 2, 3, 4],
            "nom": ["Dupont", "Martin", "Bernard", "Durand", "Petit"],
            "prenom": ["Jean", "Marie", "Luc", "Sophie", "Paul"],
            "email": [
                "jean.dupont@example.com",
                "marie.martin@example.com",
                "luc.bernard@example.com",
                "sophie.durand@example.com",
                "paul.petit@example.com",
            ],
            "groupe": ["Groupe A", "Groupe A", "Groupe B", "", "Groupe B"],
            "tags": ["VIP", "", "Speaker", "VIP", ""],
            "vip": ["yes", "no", "no", "yes", "no"],
        }
    )

    csv_buffer = io.StringIO()
    template_data.to_csv(csv_buffer, index=False)
    csv_string = csv_buffer.getvalue()

    st.download_button(
        label="⬇️ Télécharger participants_template.csv",
        data=csv_string,
        file_name="participants_template.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.divider()

# ===== SECTION 2: UPLOAD FICHIER =====
st.markdown("### 📥 Importer Participants")

uploaded_file = st.file_uploader(
    "Choisir fichier CSV ou Excel",
    type=["csv", "xlsx"],
    help="Formats supportés: .csv (UTF-8) et .xlsx (Excel)",
)

if uploaded_file is not None:
    file_extension = uploaded_file.name.split(".")[-1].lower()

    # ===== PARSING FICHIER =====
    try:
        if file_extension == "csv":
            # CSV : détection auto délimiteur
            df_raw = pd.read_csv(uploaded_file, encoding="utf-8")
            st.success(f"✅ Fichier CSV chargé : {len(df_raw)} ligne(s)")

        elif file_extension == "xlsx":
            # Excel : sélection sheet
            excel_file = pd.ExcelFile(uploaded_file)
            sheet_names = excel_file.sheet_names

            if len(sheet_names) > 1:
                selected_sheet = st.selectbox(
                    "Sélectionner feuille Excel",
                    options=sheet_names,
                    help=f"{len(sheet_names)} feuilles détectées",
                )
            else:
                selected_sheet = sheet_names[0]
                st.info(f"📄 Feuille unique détectée : **{selected_sheet}**")

            df_raw = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
            st.success(f"✅ Fichier Excel chargé : {len(df_raw)} ligne(s)")

        else:
            st.error(f"❌ Format non supporté : .{file_extension}")
            st.stop()

    except Exception as e:
        st.error(f"❌ Erreur lecture fichier : {str(e)}")
        st.stop()

    st.divider()

    # ===== SECTION 3: MAPPING COLONNES =====
    st.markdown("### 🔗 Mapper les Colonnes")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        **Instructions** : Associez les colonnes de votre fichier aux champs système.
        Seul le champ **nom** est requis.
        """)

    with col2:
        ignore_first_row = st.checkbox(
            "Ignorer ligne 1 (si déjà header)",
            value=False,
            help="Cochez si votre fichier a déjà une ligne d'en-tête",
        )

    # Options pour sélecteurs
    file_columns = ["(Ne pas importer)"] + list(df_raw.columns)

    # Mapping interactif
    col1, col2, col3 = st.columns(3)

    with col1:
        nom_col = st.selectbox(
            "🔴 Nom (REQUIS)",
            options=file_columns,
            index=file_columns.index("nom") if "nom" in df_raw.columns else 0,
        )
        prenom_col = st.selectbox(
            "Prénom",
            options=file_columns,
            index=file_columns.index("prenom") if "prenom" in df_raw.columns else 0,
        )

    with col2:
        email_col = st.selectbox(
            "Email",
            options=file_columns,
            index=file_columns.index("email") if "email" in df_raw.columns else 0,
        )
        groupe_col = st.selectbox(
            "Groupe",
            options=file_columns,
            index=file_columns.index("groupe") if "groupe" in df_raw.columns else 0,
        )

    with col3:
        tags_col = st.selectbox(
            "Tags",
            options=file_columns,
            index=file_columns.index("tags") if "tags" in df_raw.columns else 0,
        )
        vip_col = st.selectbox(
            "VIP (Story 4.4)",
            options=file_columns,
            index=file_columns.index("vip") if "vip" in df_raw.columns else 0,
            help="Colonne VIP (1/0, yes/no, true/false, vip/non)",
        )
        id_col = st.selectbox(
            "ID Participant",
            options=file_columns,
            index=(
                file_columns.index("participant_id")
                if "participant_id" in df_raw.columns
                else 0
            ),
        )

    # Appliquer mapping
    df_mapped = pd.DataFrame()

    if nom_col != "(Ne pas importer)":
        df_mapped["nom"] = df_raw[nom_col]
    if prenom_col != "(Ne pas importer)":
        df_mapped["prenom"] = df_raw[prenom_col]
    if email_col != "(Ne pas importer)":
        df_mapped["email"] = df_raw[email_col]
    if groupe_col != "(Ne pas importer)":
        df_mapped["groupe"] = df_raw[groupe_col]
    if tags_col != "(Ne pas importer)":
        df_mapped["tags"] = df_raw[tags_col]
    if vip_col != "(Ne pas importer)":
        df_mapped["vip"] = df_raw[vip_col]
    if id_col != "(Ne pas importer)":
        df_mapped["participant_id"] = df_raw[id_col]

    # Ignorer première ligne si demandé
    if ignore_first_row and len(df_mapped) > 0:
        df_mapped = df_mapped.iloc[1:]
        st.info("ℹ️ Première ligne ignorée (header)")

    st.divider()

    # ===== SECTION 4: PREVIEW DONNÉES =====
    st.markdown("### 👀 Preview (10 premières lignes)")

    if df_mapped.empty:
        st.warning("⚠️ Aucune colonne mappée. Sélectionnez au moins 'nom'.")
    else:
        st.dataframe(df_mapped.head(10), use_container_width=True)

        st.info(
            f"**Total** : {len(df_mapped)} ligne(s) | "
            f"**Colonnes** : {', '.join(df_mapped.columns)}"
        )

    st.divider()

    # ===== SECTION 5: VALIDATION ET IMPORT =====
    st.markdown("### ✅ Validation et Import")

    if st.button("🚀 Valider et Importer", type="primary", use_container_width=True):
        if df_mapped.empty:
            st.error("❌ Impossible d'importer : aucune colonne mappée")
            st.stop()

        if "nom" not in df_mapped.columns:
            st.error("❌ Impossible d'importer : colonne 'nom' requise")
            st.stop()

        # Validation complète
        with st.spinner("Validation en cours..."):
            participants, errors = validate_participants(df_mapped, auto_ids=True)

        # Afficher rapport
        st.markdown("#### 📊 Rapport de Validation")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Lignes traitées", len(df_mapped))
        with col2:
            st.metric("Participants valides", len(participants), delta="✅")
        with col3:
            st.metric("Erreurs détectées", len(errors), delta="⚠️" if errors else "✅")
        with col4:
            taux_validite = (
                100 * len(participants) / len(df_mapped) if len(df_mapped) > 0 else 0
            )
            st.metric("Taux validité", f"{taux_validite:.1f}%")

        # Afficher erreurs si présentes
        if errors:
            with st.expander("⚠️ Détails des Erreurs", expanded=True):
                for error in errors:
                    st.warning(error)

        # Import réussi
        if participants:
            # Stocker dans session_state
            participants_df = pd.DataFrame([p.__dict__ for p in participants])
            st.session_state.participants = participants_df

            # Mettre à jour N automatiquement
            st.session_state.N = len(participants)

            st.success(
                f"🎉 **{len(participants)} participant(s) importé(s) avec succès !**"
            )
            st.info(
                f"ℹ️ Configuration mise à jour : **N = {len(participants)}** "
                f"(verrouillé tant que la liste est présente)"
            )

            # Preview tableau final
            with st.expander("👀 Preview Participants Importés", expanded=False):
                st.dataframe(participants_df, use_container_width=True)

            # Bouton reset
            if st.button("🔄 Réinitialiser Import", use_container_width=True):
                if "participants" in st.session_state:
                    del st.session_state.participants
                # Supprimer aussi N pour déverrouiller la configuration
                if "N" in st.session_state:
                    del st.session_state.N
                st.rerun()

        else:
            st.error("❌ Aucun participant valide après validation")

else:
    # Aucun fichier uploadé
    st.info("👆 Uploadez un fichier CSV ou Excel pour commencer l'import")

st.divider()

# ===== SECTION 6: PARTICIPANTS ACTUELS =====
st.markdown("### 📋 Participants Actuels")

if "participants" in st.session_state and st.session_state.participants is not None:
    participants_df = st.session_state.participants

    st.success(f"✅ {len(participants_df)} participant(s) chargé(s)")

    # Statistiques
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        emails_valides = participants_df["email"].notna().sum()
        st.metric("Avec email", emails_valides)

    with col2:
        avec_groupe = participants_df["groupe"].notna().sum()
        st.metric("Avec groupe", avec_groupe)

    with col3:
        # Compter participants avec tags
        avec_tags = sum(
            1 for tags in participants_df["tags"] if tags and len(tags) > 0
        )
        st.metric("Avec tags", avec_tags)

    with col4:
        # Compter VIP (Story 4.4)
        vip_count = participants_df["is_vip"].sum() if "is_vip" in participants_df.columns else 0
        st.metric("VIP ⭐", vip_count)

    st.divider()

    # ===== SECTION VIP MANAGEMENT (Story 4.4) =====
    with st.expander("⭐ Gestion Statut VIP", expanded=False):
        st.markdown("""
        **Gérer le statut VIP des participants** (Story 4.4)

        Les participants VIP bénéficient d'une priorité lors de l'optimisation du planning
        pour maximiser leurs rencontres uniques.
        """)

        # Filtres
        col1, col2 = st.columns([1, 1])
        with col1:
            filter_option = st.radio(
                "Afficher",
                options=["Tous", "VIP uniquement", "Non-VIP uniquement"],
                horizontal=True,
            )

        with col2:
            search_term = st.text_input(
                "🔍 Rechercher participant",
                placeholder="Nom, prénom ou email...",
                help="Filtrer par nom, prénom ou email",
            )

        # Filtrer DataFrame selon options
        display_df = participants_df.copy()

        if filter_option == "VIP uniquement":
            display_df = display_df[display_df["is_vip"] == True]
        elif filter_option == "Non-VIP uniquement":
            display_df = display_df[display_df["is_vip"] == False]

        if search_term:
            # Recherche case-insensitive dans nom, prenom, email
            mask = (
                display_df["nom"].str.contains(search_term, case=False, na=False)
                | display_df["prenom"].astype(str).str.contains(search_term, case=False, na=False)
                | display_df["email"].astype(str).str.contains(search_term, case=False, na=False)
            )
            display_df = display_df[mask]

        if display_df.empty:
            st.info("Aucun participant ne correspond aux critères de filtrage.")
        else:
            st.markdown(f"**{len(display_df)} participant(s) affiché(s)**")

            # Afficher chaque participant avec toggle VIP
            for idx, row in display_df.iterrows():
                col1, col2, col3 = st.columns([3, 2, 1])

                with col1:
                    name_display = f"{row['prenom'] or ''} {row['nom']}".strip()
                    email_display = f"({row['email']})" if pd.notna(row['email']) else ""
                    st.text(f"{name_display} {email_display}")

                with col2:
                    # Badge VIP actuel
                    if row["is_vip"]:
                        st.markdown("⭐ **VIP**")
                    else:
                        st.markdown("👤 Régulier")

                with col3:
                    # Toggle VIP
                    toggle_key = f"vip_toggle_{row['id']}"
                    if st.button(
                        "↔️",
                        key=toggle_key,
                        help=f"Basculer statut VIP pour {name_display}",
                        use_container_width=True,
                    ):
                        # Toggle VIP status
                        st.session_state.participants.loc[
                            st.session_state.participants["id"] == row["id"], "is_vip"
                        ] = not row["is_vip"]
                        st.rerun()

            st.divider()

            # Actions groupées
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⭐ Marquer tous comme VIP", use_container_width=True):
                    st.session_state.participants["is_vip"] = True
                    st.rerun()

            with col2:
                if st.button("👤 Marquer tous comme Réguliers", use_container_width=True):
                    st.session_state.participants["is_vip"] = False
                    st.rerun()

    st.divider()

    # Tableau complet
    st.dataframe(participants_df, use_container_width=True)

    # Export JSON local
    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Sauvegarder en JSON local", use_container_width=True):
            participants_df.to_json(
                "data/participants.json", orient="records", indent=2
            )
            st.success("✅ Sauvegardé dans `data/participants.json`")

    with col2:
        if st.button("🗑️ Supprimer Liste", use_container_width=True):
            del st.session_state.participants
            # Supprimer aussi N pour déverrouiller la configuration
            if "N" in st.session_state:
                del st.session_state.N
            st.rerun()

else:
    st.info("ℹ️ Aucun participant chargé. Importez un fichier ci-dessus.")
