"""Export de plannings vers fichiers CSV et JSON.

Ce module fournit les fonctions d'export pour sauvegarder les plannings
dans des formats standard utilisables par des systèmes externes.

Functions:
    export_to_csv: Exporte planning au format CSV (FR10)
    export_to_json: Exporte planning au format JSON (FR11)
"""

import csv
import json
import logging
from pathlib import Path
from typing import Optional
import pandas as pd

from src.models import Planning, PlanningConfig
from src.display_utils import get_participant_display_name

logger = logging.getLogger(__name__)


def export_to_csv(
    planning: Planning,
    config: PlanningConfig,
    filepath: str,
    participants_df: Optional[pd.DataFrame] = None,
) -> None:
    """Exporte planning au format CSV (FR10) avec noms participants si disponibles.

    Format CSV conforme FR10:
        - Colonnes: session_id, table_id, participant_id[, participant_name]
        - IDs 0-indexed (sessions, tables, participants)
        - Colonne participant_name ajoutée si participants_df fourni (Story 5.1)
        - Encodage UTF-8 avec BOM (compatibilité Excel)
        - Une ligne par participant par session

    Args:
        planning: Planning à exporter
        config: Configuration associée (pour contexte)
        filepath: Chemin fichier sortie (.csv)
        participants_df: DataFrame participants avec colonnes 'id', 'nom', 'prenom' (optionnel)

    Raises:
        IOError: Si impossible d'écrire le fichier

    Example:
        >>> planning, metrics = generate_optimized_planning(config, seed=42)
        >>> export_to_csv(planning, config, "mon_event.csv")
        # Sans participants: session_id,table_id,participant_id
        >>> export_to_csv(planning, config, "event.csv", participants_df)
        # Avec participants: session_id,table_id,participant_id,participant_name

    Complexity:
        Time: O(N × S) pour parcourir tous participants de toutes sessions
        Space: O(1) (écriture streaming)

    Note:
        - Fichier écrasé si existe (avec warning loggé)
        - Gère chemins avec espaces et caractères accentués
        - BOM UTF-8 pour détection automatique par Excel
        - Backward compatible: sans participants_df, format original
    """
    # Créer Path object (gère chemins avec espaces)
    output_path = Path(filepath)

    # Warning si fichier existe déjà
    if output_path.exists():
        logger.warning(f"Fichier existant écrasé : {filepath}")

    # Ouvrir avec encoding UTF-8-sig (ajoute BOM pour Excel)
    try:
        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)

            # Header FR10 (+ participant_name si disponible)
            header = ["session_id", "table_id", "participant_id"]
            if participants_df is not None and not participants_df.empty:
                header.append("participant_name")
            writer.writerow(header)

            # Données: une ligne par participant
            for session in planning.sessions:
                for table_id, table in enumerate(session.tables):
                    # Trier participants pour déterminisme
                    for participant_id in sorted(table):
                        row = [session.session_id, table_id, participant_id]

                        # Ajouter nom si disponible (Story 5.1)
                        if participants_df is not None and not participants_df.empty:
                            participant_name = get_participant_display_name(
                                participant_id, participants_df
                            )
                            row.append(participant_name)

                        writer.writerow(row)

        # Compter lignes exportées
        total_rows = sum(len(t) for s in planning.sessions for t in s.tables)
        logger.info(f"Export CSV réussi : {filepath} ({total_rows} lignes)")

    except IOError as e:
        logger.error(f"Erreur export CSV : {e}")
        raise


def export_to_json(
    planning: Planning,
    config: PlanningConfig,
    filepath: str,
    include_metadata: bool = True,
    participants_df: Optional[pd.DataFrame] = None,
) -> None:
    """Exporte planning au format JSON (FR11) avec noms participants si disponibles.

    Format JSON conforme FR11:
        {
          "sessions": [
            {
              "session_id": 0,
              "tables": [
                {
                  "table_id": 0,
                  "participants": [
                    {"id": 0, "name": "Jean Dupont"},
                    {"id": 1, "name": "Marie Martin"}
                  ]
                }
              ]
            }
          ],
          "metadata": {  // optionnel
            "config": {"N": 6, "X": 2, "x": 3, "S": 2},
            "total_participants": 6,
            "total_sessions": 2
          }
        }

    Args:
        planning: Planning à exporter
        config: Configuration associée
        filepath: Chemin fichier sortie (.json)
        include_metadata: Inclure metadata optionnelle (défaut: True)
        participants_df: DataFrame participants avec colonnes 'id', 'nom', 'prenom' (optionnel)

    Raises:
        IOError: Si impossible d'écrire le fichier

    Example:
        >>> planning, metrics = generate_optimized_planning(config, seed=42)
        >>> export_to_json(planning, config, "event.json")
        # Sans participants: format original avec IDs uniquement
        >>> export_to_json(planning, config, "event.json", participants_df=df)
        # Avec participants: objets {"id": ..., "name": ...}

    Complexity:
        Time: O(N × S) pour parcourir tous participants
        Space: O(N × S) pour construction dict

    Note:
        - JSON indenté 2 espaces (lisibilité humaine)
        - Encodage UTF-8 (sans BOM, standard JSON)
        - Participants triés pour déterminisme
        - Fichier écrasé si existe (avec warning)
        - Backward compatible: sans participants_df, format original
    """
    # Créer Path object
    output_path = Path(filepath)

    # Warning si fichier existe
    if output_path.exists():
        logger.warning(f"Fichier existant écrasé : {filepath}")

    try:
        # Construire structure FR11
        data: dict = {"sessions": []}

        for session in planning.sessions:
            tables_data = []

            for table_id, table in enumerate(session.tables):
                # Format participants selon disponibilité noms (Story 5.1)
                if participants_df is not None and not participants_df.empty:
                    # Format: [{"id": 0, "name": "Jean Dupont"}, ...]
                    participants_list = [
                        {
                            "id": p_id,
                            "name": get_participant_display_name(p_id, participants_df),
                        }
                        for p_id in sorted(list(table))
                    ]
                else:
                    # Format original: [0, 1, 2, ...]
                    participants_list = sorted(list(table))

                tables_data.append({
                    "table_id": table_id,
                    "participants": participants_list,
                })

            session_data = {
                "session_id": session.session_id,
                "tables": tables_data,
            }
            data["sessions"].append(session_data)

        # Metadata optionnelle
        if include_metadata:
            data["metadata"] = {
                "config": {
                    "N": config.N,
                    "X": config.X,
                    "x": config.x,
                    "S": config.S,
                },
                "total_participants": config.N,
                "total_sessions": config.S,
            }

        # Écrire JSON (indent=2 pour lisibilité, ensure_ascii=False pour UTF-8)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Export JSON réussi : {filepath}")

    except IOError as e:
        logger.error(f"Erreur export JSON : {e}")
        raise
