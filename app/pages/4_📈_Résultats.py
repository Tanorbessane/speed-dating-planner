"""Page Résultats - Analyses et exports."""

import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH pour permettre les imports depuis src/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import tempfile
from src.exporters import export_to_csv, export_to_json
from src.display_utils import format_table_participants

st.set_page_config(page_title="Résultats", page_icon="📈", layout="wide")

st.title("📈 Résultats et Exports")

# Vérifier planning existe
if "planning" not in st.session_state or st.session_state.planning is None:
    st.error("❌ Aucun planning généré. Allez dans **🎯 Génération** d'abord.")
    st.stop()

planning = st.session_state.planning
metrics = st.session_state.metrics
config = st.session_state.config

# Récupérer participants si disponibles (Story 5.1)
participants_df = st.session_state.get("participants", None)

# Onglets
tab1, tab2, tab3, tab4 = st.tabs(["📊 Métriques", "🗺️ Heatmap", "💾 Exports", "🔍 Analyses Avancées"])

# ===== TAB 1: MÉTRIQUES =====
with tab1:
    st.markdown("### 📊 Métriques Complètes")

    # Grille métriques
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 👥 Participants")
        st.metric("Total", config.N)
        st.metric("Tables", config.X)
        st.metric("Capacité/table", config.x)
        st.metric("Sessions", config.S)

    with col2:
        st.markdown("#### 🤝 Rencontres")
        st.metric("Paires uniques", metrics.total_unique_pairs)
        st.metric("Répétitions", metrics.total_repeat_pairs)

        total_paires = metrics.total_unique_pairs + metrics.total_repeat_pairs
        taux_unique = (
            100 * metrics.total_unique_pairs / total_paires if total_paires > 0 else 0
        )
        st.metric("Taux unicité", f"{taux_unique:.1f}%")

    with col3:
        st.markdown("#### ⚖️ Équité")
        if metrics.equity_gap <= 1:
            st.success(f"**Equity Gap: {metrics.equity_gap}** ✅")
        else:
            st.warning(f"**Equity Gap: {metrics.equity_gap}** ⚠️")

        st.metric("Min rencontres", metrics.min_unique)
        st.metric("Max rencontres", metrics.max_unique)
        st.metric("Moyenne", f"{metrics.mean_unique:.1f}")

    st.divider()

    # ===== MÉTRIQUES VIP (Story 4.4) =====
    if metrics.vip_metrics:
        st.markdown("### ⭐ Métriques VIP (Story 4.4)")
        st.info(
            "Les participants VIP bénéficient d'une priorité lors de l'optimisation "
            "pour maximiser leurs rencontres uniques."
        )

        vip = metrics.vip_metrics

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### ⭐ VIP")
            st.metric("Nombre VIP", vip.vip_count)
            st.metric("Min rencontres", vip.vip_min_unique)
            st.metric("Max rencontres", vip.vip_max_unique)
            st.metric("Moyenne", f"{vip.vip_mean_unique:.1f}")

            if vip.vip_equity_gap <= 1:
                st.success(f"**Equity Gap VIP: {vip.vip_equity_gap}** ✅")
            else:
                st.warning(f"**Equity Gap VIP: {vip.vip_equity_gap}** ⚠️")

        with col2:
            st.markdown("#### 👤 Réguliers")
            st.metric("Nombre réguliers", vip.non_vip_count)
            st.metric("Min rencontres", vip.non_vip_min_unique)
            st.metric("Max rencontres", vip.non_vip_max_unique)
            st.metric("Moyenne", f"{vip.non_vip_mean_unique:.1f}")

            if vip.non_vip_equity_gap <= 1:
                st.success(f"**Equity Gap Réguliers: {vip.non_vip_equity_gap}** ✅")
            else:
                st.warning(f"**Equity Gap Réguliers: {vip.non_vip_equity_gap}** ⚠️")

        # Avantage VIP
        if vip.vip_count > 0 and vip.non_vip_count > 0:
            vip_advantage = vip.vip_min_unique - vip.non_vip_min_unique
            st.divider()
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if vip_advantage > 0:
                    st.success(
                        f"🎯 **Avantage VIP**: +{vip_advantage} rencontre(s) minimum vs réguliers"
                    )
                elif vip_advantage == 0:
                    st.info("ℹ️ VIP et réguliers ont le même minimum de rencontres")
                else:
                    st.warning(
                        f"⚠️ VIP ont {abs(vip_advantage)} rencontre(s) de moins que réguliers"
                    )

        st.divider()

    # Distribution rencontres avec noms participants (Story 5.3)
    st.markdown("### 📊 Distribution Rencontres par Participant")

    from src.visualizations import create_distribution_chart

    fig = create_distribution_chart(
        metrics.unique_meetings_per_person,
        participants_df,
        title="Nombre de rencontres uniques par participant"
    )

    st.plotly_chart(fig, use_container_width=True)

# ===== TAB 2: HEATMAP (Story 5.2) =====
with tab2:
    st.markdown("### 🗺️ Matrice des Rencontres")

    st.info("""
    **Comment lire cette heatmap** :
    - Chaque cellule (i, j) indique combien de fois le participant i a rencontré le participant j
    - **Blanc** : 0 rencontre (ne se sont jamais rencontrés)
    - **Jaune** : 1 rencontre (optimal !)
    - **Orange** : 2 rencontres (répétition)
    - **Rouge foncé** : 3+ rencontres (répétitions multiples)

    Survolez les cellules pour voir les détails !
    """)

    # Warning si N > 100
    if config.N > 100:
        st.warning("⚠️ Heatmap peut être lente pour grands plannings (N > 100)")

    # Bouton afficher si N > 50
    show_heatmap = True
    if config.N > 50:
        show_heatmap = st.button("🗺️ Afficher Heatmap", type="primary", use_container_width=True)

    if show_heatmap:
        from src.analysis import compute_meetings_matrix, compute_matrix_statistics
        from src.visualizations import create_meetings_heatmap

        # Calculer matrice
        with st.spinner("Calcul matrice rencontres..."):
            matrix = compute_meetings_matrix(planning, config.N)

        # Afficher heatmap
        fig_heatmap = create_meetings_heatmap(matrix, participants_df)
        st.plotly_chart(fig_heatmap, use_container_width=True)

        # Statistiques
        st.divider()
        st.markdown("### 📊 Statistiques Matrice")

        stats = compute_matrix_statistics(matrix)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Paires rencontrées",
                f"{stats['total_pairs_met']}/{stats['total_possible_pairs']}"
            )

        with col2:
            st.metric("Taux couverture", f"{stats['coverage_rate']:.1f}%")

        with col3:
            st.metric("Répétitions (≥2)", stats['repeat_pairs'])

        with col4:
            st.metric("Max rencontres paire", stats['max_meetings'])

        # Interprétation
        st.divider()
        st.markdown("### 💡 Interprétation")

        if stats['coverage_rate'] >= 90:
            st.success(f"✅ Excellent ! {stats['coverage_rate']:.1f}% des paires se sont rencontrées.")
        elif stats['coverage_rate'] >= 70:
            st.info(f"ℹ️ Bon : {stats['coverage_rate']:.1f}% des paires se sont rencontrées.")
        else:
            st.warning(f"⚠️ {stats['coverage_rate']:.1f}% des paires se sont rencontrées. Augmenter le nombre de sessions pourrait améliorer la couverture.")

        if stats['repeat_pairs'] == 0:
            st.success("✅ Aucune répétition ! Planning optimal (FR5).")
        else:
            repeat_pct = 100 * stats['repeat_pairs'] / stats['total_possible_pairs']
            st.info(f"ℹ️ {stats['repeat_pairs']} répétitions ({repeat_pct:.1f}% des paires possibles)")

# ===== TAB 3: EXPORTS =====
with tab3:
    st.markdown("### 💾 Télécharger Planning")

    col1, col2 = st.columns(2)

    # Export CSV
    with col1:
        st.markdown("#### 📄 Format CSV")
        st.info("""
        **Colonnes** :
        - `session_id` : ID de session (0-indexed)
        - `table_id` : ID de table (0-indexed)
        - `participant_id` : ID participant (0-indexed)

        Compatible Excel, Google Sheets, etc.
        """)

        if st.button("💾 Générer CSV", use_container_width=True):
            # Export temporaire
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".csv"
            ) as tmp:
                tmp_path = tmp.name

            export_to_csv(planning, config, tmp_path, participants_df)

            # Lire contenu
            with open(tmp_path, "rb") as f:
                csv_data = f.read()

            # Bouton download
            st.download_button(
                label="⬇️ Télécharger planning.csv",
                data=csv_data,
                file_name="planning.csv",
                mime="text/csv",
                use_container_width=True,
            )

            # Cleanup
            Path(tmp_path).unlink()

            st.success("✅ CSV généré avec succès !")

    # Export JSON
    with col2:
        st.markdown("#### 📋 Format JSON")
        st.info("""
        **Structure** :
        ```json
        {
          "sessions": [...],
          "metadata": {
            "config": {...},
            "total_participants": N
          }
        }
        ```

        Inclut métadonnées pour intégrations.
        """)

        if st.button("💾 Générer JSON", use_container_width=True):
            # Export temporaire
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".json"
            ) as tmp:
                tmp_path = tmp.name

            export_to_json(planning, config, tmp_path, include_metadata=True, participants_df=participants_df)

            # Lire contenu
            with open(tmp_path, "rb") as f:
                json_data = f.read()

            # Bouton download
            st.download_button(
                label="⬇️ Télécharger planning.json",
                data=json_data,
                file_name="planning.json",
                mime="application/json",
                use_container_width=True,
            )

            # Cleanup
            Path(tmp_path).unlink()

            st.success("✅ JSON généré avec succès !")

    st.divider()

    # ===== EXPORT PDF (Story 5.4) =====
    st.markdown("### 📄 Rapport PDF Complet")

    st.info("""
    **Contenu du rapport PDF** :
    - 📋 Page de garde avec configuration et score qualité
    - 📊 KPIs principaux (Participants, Couverture, Équité, Répétitions, etc.)
    - 📈 Graphiques visuels (heatmap, distribution, répartition paires)
    - 📝 Planning détaillé (toutes sessions/tables avec noms)

    **Format** : A4, haute résolution, prêt à imprimer
    """)

    if config.N > 100:
        st.warning("⚠️ Génération PDF peut prendre 10-15s pour N > 100")

    if st.button("📄 Générer Rapport PDF", type="primary", use_container_width=True):
        with st.spinner("Génération PDF en cours..."):
            try:
                from src.pdf_exporter import export_to_pdf

                # Générer PDF en mémoire
                pdf_bytes = export_to_pdf(planning, config, metrics, participants_df)

                # Nom fichier avec timestamp
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"planning_report_{timestamp}.pdf"

                # Bouton download
                st.download_button(
                    label="⬇️ Télécharger Rapport PDF",
                    data=pdf_bytes.getvalue(),
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True,
                )

                st.success("✅ PDF généré avec succès !")

            except ImportError as e:
                st.error("❌ Erreur : Dépendances PDF manquantes")
                st.info("💡 Installez avec : `pip install reportlab kaleido`")
            except Exception as e:
                st.error(f"❌ Erreur génération PDF : {e}")
                st.info("💡 Vérifiez que toutes les dépendances sont installées")

    st.divider()

    # Preview planning
    st.markdown("### 👀 Aperçu Planning")

    # Afficher quelques sessions
    st.markdown("**Sessions (aperçu)**")

    for session_idx, session in enumerate(planning.sessions[:3]):  # 3 premières sessions
        with st.expander(f"Session {session_idx + 1}/{config.S}"):
            for table_idx, table in enumerate(session.tables):
                # Story 5.1: Afficher noms si disponibles
                participants_str = format_table_participants(
                    table, participants_df, include_vip_badge=True
                )
                st.write(f"**Table {table_idx + 1}** : {participants_str}")

    if len(planning.sessions) > 3:
        st.info(f"... et {len(planning.sessions) - 3} autres sessions (voir export complet)")

# ===== TAB 4: ANALYSES AVANCÉES =====
with tab4:
    st.markdown("### 🔍 Analyses Avancées")

    st.info("🚧 Fonctionnalité en développement (V2.1)")

    st.markdown("""
    **Prochainement** :
    - 🗺️ Heatmap matrice rencontres N×N
    - 🕸️ Graphe social (NetworkX)
    - 📊 Statistiques avancées (écart-type, Gini)
    - 📈 Comparaison multi-seeds
    - 🎨 Export PDF avec logos
    """)

    # Placeholder : statistiques basiques
    st.markdown("#### 📊 Statistiques Distribution")

    import numpy as np

    data_array = np.array(metrics.unique_meetings_per_person)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Médiane", f"{np.median(data_array):.1f}")

    with col2:
        st.metric("Écart-type", f"{np.std(data_array):.2f}")

    with col3:
        cv = np.std(data_array) / np.mean(data_array) if np.mean(data_array) > 0 else 0
        st.metric("Coeff. Variation", f"{cv:.2%}")
