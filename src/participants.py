"""Module de gestion des participants pour événements de networking.

Ce module fournit les fonctions pour importer, valider et gérer des listes
de participants depuis CSV ou Excel.

Functions:
    parse_csv: Parse fichier CSV avec détection auto délimiteur
    parse_excel: Parse fichier Excel avec support multisheets
    validate_email: Valide format email (regex RFC 5322 basique)
    normalize_dataframe: Normalise données (strips, lowercase email, etc.)
    find_duplicates: Détecte doublons (nom+prénom ou email)
    auto_generate_ids: Auto-génère participant_id si absent
    validate_participants: Validation complète DataFrame → Participants
"""

import csv
import re
from io import StringIO
from typing import List, Tuple, Optional
import pandas as pd
from src.models import Participant


# Regex basique email (RFC 5322 simplifié)
EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"


def validate_email(email: str) -> bool:
    """Valide format email avec regex basique.

    Args:
        email: Adresse email à valider

    Returns:
        True si email valide, False sinon

    Example:
        >>> validate_email("test@example.com")
        True
        >>> validate_email("invalid@com")
        False
        >>> validate_email("no-at-sign")
        False
    """
    if not email or not isinstance(email, str):
        return False
    return bool(re.match(EMAIL_PATTERN, email.strip()))


def detect_delimiter(filepath: str, sample_size: int = 1024) -> str:
    """Détecte délimiteur CSV (, ou ;) automatiquement.

    Args:
        filepath: Chemin vers fichier CSV
        sample_size: Nombre de caractères à analyser

    Returns:
        Délimiteur détecté (',' ou ';')

    Example:
        >>> detect_delimiter("data.csv")
        ','
    """
    with open(filepath, "r", encoding="utf-8") as f:
        sample = f.read(sample_size)
        sniffer = csv.Sniffer()
        delimiter = sniffer.sniff(sample).delimiter
    return delimiter


def parse_csv(
    filepath: str, delimiter: Optional[str] = None, encoding: str = "utf-8"
) -> pd.DataFrame:
    """Parse fichier CSV avec détection auto délimiteur.

    Args:
        filepath: Chemin vers fichier CSV
        delimiter: Délimiteur (None = auto-détection)
        encoding: Encodage fichier

    Returns:
        DataFrame pandas avec données brutes

    Raises:
        FileNotFoundError: Si fichier n'existe pas
        pd.errors.EmptyDataError: Si fichier vide

    Example:
        >>> df = parse_csv("participants.csv")
        >>> df.columns
        Index(['nom', 'prenom', 'email'], dtype='object')
    """
    if delimiter is None:
        delimiter = detect_delimiter(filepath)

    df = pd.read_csv(filepath, delimiter=delimiter, encoding=encoding)
    return df


def parse_excel(filepath: str, sheet_name: str = "0") -> pd.DataFrame:
    """Parse fichier Excel avec support multisheets.

    Args:
        filepath: Chemin vers fichier .xlsx
        sheet_name: Nom ou index de la sheet (défaut: première sheet)

    Returns:
        DataFrame pandas avec données brutes

    Raises:
        FileNotFoundError: Si fichier n'existe pas
        ValueError: Si sheet n'existe pas

    Example:
        >>> df = parse_excel("participants.xlsx", "Sheet1")
        >>> df.shape
        (50, 6)
    """
    # Convertir "0", "1", etc. en int
    if isinstance(sheet_name, str) and sheet_name.isdigit():
        sheet_name = int(sheet_name)

    df = pd.read_excel(filepath, sheet_name=sheet_name)
    return df


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise données DataFrame (strips, casse, vides).

    Opérations :
    - Strip whitespace sur toutes colonnes string
    - Lowercase email
    - Remplacer chaînes vides par None
    - Normaliser casse nom/prénom (capitalize)

    Args:
        df: DataFrame brut à normaliser

    Returns:
        DataFrame normalisé (copie)

    Example:
        >>> df = pd.DataFrame({"nom": ["  DUPONT  "], "email": [" TEST@EXAMPLE.COM "]})
        >>> normalized = normalize_dataframe(df)
        >>> normalized["nom"].iloc[0]
        'Dupont'
        >>> normalized["email"].iloc[0]
        'test@example.com'
    """
    df = df.copy()

    # Strip whitespace sur toutes colonnes object/string
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].str.strip()

    # Remplacer chaînes vides par None
    df = df.replace(r"^\s*$", None, regex=True)

    # Normaliser nom/prénom (capitalize première lettre)
    if "nom" in df.columns:
        df["nom"] = df["nom"].str.capitalize()
    if "prenom" in df.columns:
        df["prenom"] = df["prenom"].str.capitalize()

    # Lowercase email
    if "email" in df.columns:
        df["email"] = df["email"].str.lower()

    return df


def auto_generate_ids(df: pd.DataFrame) -> pd.DataFrame:
    """Auto-génère colonne participant_id si absente.

    Args:
        df: DataFrame (potentiellement sans colonne 'id')

    Returns:
        DataFrame avec colonne 'participant_id' (0, 1, 2, ...)

    Example:
        >>> df = pd.DataFrame({"nom": ["Dupont", "Martin"]})
        >>> df_with_ids = auto_generate_ids(df)
        >>> list(df_with_ids["participant_id"])
        [0, 1]
    """
    df = df.copy()

    if "participant_id" not in df.columns and "id" not in df.columns:
        df.insert(0, "participant_id", range(len(df)))
    elif "id" in df.columns and "participant_id" not in df.columns:
        # Renommer 'id' → 'participant_id'
        df = df.rename(columns={"id": "participant_id"})

    return df


def find_duplicates(df: pd.DataFrame) -> List[str]:
    """Détecte doublons dans DataFrame (nom+prénom ou email).

    Args:
        df: DataFrame avec colonnes 'nom', 'prenom' (opt), 'email' (opt)

    Returns:
        Liste de messages d'erreur pour chaque doublon détecté

    Example:
        >>> df = pd.DataFrame({
        ...     "nom": ["Dupont", "Dupont", "Martin"],
        ...     "prenom": ["Jean", "Jean", "Marie"],
        ...     "email": ["jean@ex.com", "jean2@ex.com", "marie@ex.com"]
        ... })
        >>> errors = find_duplicates(df)
        >>> len(errors)
        1
        >>> "Dupont Jean" in errors[0]
        True
    """
    errors = []

    # Doublons nom+prénom (si prenom existe)
    if "nom" in df.columns:
        if "prenom" in df.columns:
            # Combiner nom+prénom pour détection
            name_cols = ["nom", "prenom"]
            name_dupes = df[df.duplicated(subset=name_cols, keep=False)]

            if not name_dupes.empty:
                # Grouper par (nom, prénom) et compter
                grouped = name_dupes.groupby(name_cols).size()
                for (nom, prenom), count in grouped.items():
                    if pd.notna(nom) and pd.notna(prenom):
                        errors.append(
                            f"Doublon détecté : {prenom} {nom} ({count} occurrences)"
                        )
        else:
            # Doublons nom uniquement
            name_dupes = df[df.duplicated(subset=["nom"], keep=False)]
            if not name_dupes.empty:
                grouped = name_dupes.groupby("nom").size()
                for nom, count in grouped.items():
                    if pd.notna(nom):
                        errors.append(f"Doublon détecté : {nom} ({count} occurrences)")

    # Doublons email (ignorer None/NaN)
    if "email" in df.columns:
        # Filtrer emails non-null
        df_with_email = df[df["email"].notna()]
        email_dupes = df_with_email[df_with_email.duplicated(subset=["email"], keep=False)]

        if not email_dupes.empty:
            grouped = email_dupes.groupby("email").size()
            for email, count in grouped.items():
                if pd.notna(email):
                    errors.append(f"Email doublon : {email} ({count} occurrences)")

    return errors


def validate_participants(
    df: pd.DataFrame, auto_ids: bool = True
) -> Tuple[List[Participant], List[str]]:
    """Valide DataFrame et convertit en liste Participant objects.

    Pipeline de validation :
    1. Auto-génération IDs (si auto_ids=True)
    2. Normalisation données (strips, casse)
    3. Validation colonne 'nom' requise
    4. Validation emails (format regex)
    5. Détection doublons (nom+prénom, email)
    6. Conversion → Participant objects

    Colonnes supportées :
    - participant_id (ou id) : ID unique participant (auto-généré si absent)
    - nom : Nom participant (REQUIS)
    - prenom : Prénom participant (optionnel)
    - email : Email participant (optionnel, validé si présent)
    - groupe : Groupe d'affiliation (optionnel, pour contraintes Story 4.2)
    - tags : Tags séparés par virgule (optionnel, ex: "VIP,Speaker")
    - vip : Statut VIP (optionnel, Story 4.4, formats: 1/0, true/false, yes/no, vip/non)

    Args:
        df: DataFrame brut avec colonnes mappées
        auto_ids: Auto-générer participant_id si absent

    Returns:
        Tuple (participants, errors)
        - participants: Liste Participant objects valides
        - errors: Liste messages erreur (str)

    Example:
        >>> df = pd.DataFrame({
        ...     "nom": ["Dupont", "Martin"],
        ...     "prenom": ["Jean", "Marie"],
        ...     "email": ["jean@ex.com", "invalid"],
        ...     "vip": ["yes", "no"]
        ... })
        >>> participants, errors = validate_participants(df)
        >>> len(participants)
        2
        >>> participants[0].is_vip
        True
        >>> len(errors)
        1
        >>> "invalid" in errors[0]
        True
    """
    errors = []

    # 1. Auto-génération IDs
    if auto_ids:
        df = auto_generate_ids(df)

    # 2. Normalisation
    df = normalize_dataframe(df)

    # 3. Validation colonne 'nom' requise
    if "nom" not in df.columns:
        errors.append("❌ Colonne 'nom' manquante (champ requis)")
        return [], errors

    # Vérifier lignes sans nom
    missing_nom = df["nom"].isna().sum()
    if missing_nom > 0:
        errors.append(f"⚠️ {missing_nom} ligne(s) sans nom (seront ignorées)")
        df = df[df["nom"].notna()]

    if df.empty:
        errors.append("❌ Aucune ligne valide après filtrage")
        return [], errors

    # 4. Validation emails (si colonne existe)
    if "email" in df.columns:
        invalid_emails = []
        for idx, row in df.iterrows():
            email = row.get("email")
            if pd.notna(email) and email and not validate_email(email):
                invalid_emails.append(f"Ligne {idx + 1}: email invalide '{email}'")

        if invalid_emails:
            errors.append(f"⚠️ {len(invalid_emails)} email(s) invalide(s):")
            errors.extend(invalid_emails)

    # 5. Détection doublons
    duplicate_errors = find_duplicates(df)
    if duplicate_errors:
        errors.append(f"⚠️ {len(duplicate_errors)} doublon(s) détecté(s):")
        errors.extend(duplicate_errors)

    # 6. Conversion → Participant objects
    participants = []
    for idx, row in df.iterrows():
        try:
            # Parser tags (string "VIP,Speaker" → list ["VIP", "Speaker"])
            tags_raw = row.get("tags", "")
            if pd.isna(tags_raw) or not tags_raw:
                tags = []
            else:
                tags = [tag.strip() for tag in str(tags_raw).split(",") if tag.strip()]

            # Parser statut VIP (Story 4.4: colonne 'vip' optionnelle)
            # Formats supportés: 1/0, true/false, yes/no, vip/non (case-insensitive)
            is_vip = False
            if "vip" in df.columns:
                vip_raw = row.get("vip")
                if pd.notna(vip_raw):
                    vip_str = str(vip_raw).strip().lower()
                    # Valeurs truthy: 1, true, yes, vip
                    if vip_str in ["1", "true", "yes", "vip"]:
                        is_vip = True
                    # Valeurs falsy: 0, false, no, non (déjà False par défaut)

            participant = Participant(
                id=int(row.get("participant_id", idx)),
                nom=str(row["nom"]),
                prenom=str(row["prenom"]) if pd.notna(row.get("prenom")) else None,
                email=str(row["email"]) if pd.notna(row.get("email")) else None,
                groupe=str(row["groupe"]) if pd.notna(row.get("groupe")) else None,
                tags=tags,
                is_vip=is_vip,
            )
            participants.append(participant)
        except Exception as e:
            errors.append(f"❌ Erreur ligne {idx + 1}: {str(e)}")

    return participants, errors
