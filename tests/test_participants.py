"""Tests unitaires pour le module participants."""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
from src.participants import (
    validate_email,
    normalize_dataframe,
    auto_generate_ids,
    find_duplicates,
    validate_participants,
    parse_csv,
    parse_excel,
)
from src.models import Participant


class TestValidateEmail:
    """Tests pour la validation d'email."""

    def test_valid_emails(self) -> None:
        """Test emails valides."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "first+last@test.org",
            "123@numbers.com",
        ]
        for email in valid_emails:
            assert validate_email(email), f"Email devrait être valide: {email}"

    def test_invalid_emails(self) -> None:
        """Test emails invalides."""
        invalid_emails = [
            "invalid@com",  # TLD trop court
            "no-at-sign.com",
            "@domain.com",
            "user@",
            "",
            "spaces @domain.com",
        ]
        for email in invalid_emails:
            assert not validate_email(email), f"Email devrait être invalide: {email}"

    def test_none_and_whitespace(self) -> None:
        """Test valeurs None et whitespace."""
        assert not validate_email(None)
        assert not validate_email("   ")
        assert validate_email("  test@example.com  ")  # Strips whitespace


class TestNormalizeDataFrame:
    """Tests pour la normalisation de DataFrame."""

    def test_strip_whitespace(self) -> None:
        """Test suppression whitespace."""
        df = pd.DataFrame({"nom": ["  Dupont  ", "Martin"], "prenom": ["Jean  ", "  Marie"]})
        normalized = normalize_dataframe(df)

        assert normalized["nom"].iloc[0] == "Dupont"
        assert normalized["prenom"].iloc[0] == "Jean"
        assert normalized["prenom"].iloc[1] == "Marie"

    def test_capitalize_names(self) -> None:
        """Test capitalisation nom/prénom."""
        df = pd.DataFrame({"nom": ["DUPONT", "martin"], "prenom": ["JEAN", "marie"]})
        normalized = normalize_dataframe(df)

        assert normalized["nom"].iloc[0] == "Dupont"
        assert normalized["nom"].iloc[1] == "Martin"
        assert normalized["prenom"].iloc[0] == "Jean"
        assert normalized["prenom"].iloc[1] == "Marie"

    def test_lowercase_email(self) -> None:
        """Test conversion email en minuscules."""
        df = pd.DataFrame({"email": ["TEST@EXAMPLE.COM", "User@Domain.COM"]})
        normalized = normalize_dataframe(df)

        assert normalized["email"].iloc[0] == "test@example.com"
        assert normalized["email"].iloc[1] == "user@domain.com"

    def test_empty_strings_to_none(self) -> None:
        """Test conversion chaînes vides → None."""
        df = pd.DataFrame({"nom": ["Dupont", "  ", "Martin"], "groupe": ["A", "", "B"]})
        normalized = normalize_dataframe(df)

        assert pd.isna(normalized["nom"].iloc[1])
        assert pd.isna(normalized["groupe"].iloc[1])


class TestAutoGenerateIds:
    """Tests pour l'auto-génération d'IDs."""

    def test_generate_ids_when_missing(self) -> None:
        """Test génération IDs quand colonne absente."""
        df = pd.DataFrame({"nom": ["Dupont", "Martin", "Bernard"]})
        df_with_ids = auto_generate_ids(df)

        assert "participant_id" in df_with_ids.columns
        assert list(df_with_ids["participant_id"]) == [0, 1, 2]

    def test_rename_id_to_participant_id(self) -> None:
        """Test renommage colonne 'id' → 'participant_id'."""
        df = pd.DataFrame({"id": [10, 20, 30], "nom": ["Dupont", "Martin", "Bernard"]})
        df_with_ids = auto_generate_ids(df)

        assert "participant_id" in df_with_ids.columns
        assert "id" not in df_with_ids.columns
        assert list(df_with_ids["participant_id"]) == [10, 20, 30]

    def test_preserve_existing_participant_id(self) -> None:
        """Test conservation participant_id existant."""
        df = pd.DataFrame(
            {"participant_id": [100, 200], "nom": ["Dupont", "Martin"]}
        )
        df_with_ids = auto_generate_ids(df)

        assert list(df_with_ids["participant_id"]) == [100, 200]


class TestFindDuplicates:
    """Tests pour la détection de doublons."""

    def test_duplicate_nom_prenom(self) -> None:
        """Test détection doublons nom+prénom."""
        df = pd.DataFrame(
            {
                "nom": ["Dupont", "Dupont", "Martin"],
                "prenom": ["Jean", "Jean", "Marie"],
            }
        )
        errors = find_duplicates(df)

        assert len(errors) == 1
        assert "Dupont" in errors[0] and "Jean" in errors[0]

    def test_duplicate_email(self) -> None:
        """Test détection doublons email."""
        df = pd.DataFrame(
            {
                "nom": ["Dupont", "Martin"],
                "prenom": ["Jean", "Marie"],
                "email": ["test@example.com", "test@example.com"],
            }
        )
        errors = find_duplicates(df)

        assert len(errors) == 1
        assert "test@example.com" in errors[0]

    def test_no_duplicates(self) -> None:
        """Test aucun doublon."""
        df = pd.DataFrame(
            {
                "nom": ["Dupont", "Martin"],
                "prenom": ["Jean", "Marie"],
                "email": ["jean@example.com", "marie@example.com"],
            }
        )
        errors = find_duplicates(df)

        assert len(errors) == 0

    def test_ignore_none_emails(self) -> None:
        """Test ignorer emails None dans détection doublons."""
        df = pd.DataFrame(
            {
                "nom": ["Dupont", "Martin", "Bernard"],
                "email": [None, "test@example.com", None],
            }
        )
        errors = find_duplicates(df)

        # Pas de doublon car None n'est pas compté
        assert len(errors) == 0


class TestValidateParticipants:
    """Tests pour la validation complète de participants."""

    def test_valid_participants(self) -> None:
        """Test participants valides."""
        df = pd.DataFrame(
            {
                "nom": ["Dupont", "Martin"],
                "prenom": ["Jean", "Marie"],
                "email": ["jean@example.com", "marie@example.com"],
            }
        )
        participants, errors = validate_participants(df)

        assert len(participants) == 2
        assert len(errors) == 0
        assert participants[0].nom == "Dupont"
        assert participants[0].prenom == "Jean"
        assert participants[1].nom == "Martin"

    def test_auto_generate_ids(self) -> None:
        """Test auto-génération IDs."""
        df = pd.DataFrame({"nom": ["Dupont", "Martin"]})
        participants, errors = validate_participants(df, auto_ids=True)

        assert participants[0].id == 0
        assert participants[1].id == 1

    def test_missing_nom_column(self) -> None:
        """Test colonne 'nom' manquante."""
        df = pd.DataFrame({"prenom": ["Jean", "Marie"]})
        participants, errors = validate_participants(df)

        assert len(participants) == 0
        assert len(errors) > 0
        assert any("nom" in err.lower() for err in errors)

    def test_invalid_emails(self) -> None:
        """Test emails invalides."""
        df = pd.DataFrame(
            {
                "nom": ["Dupont", "Martin"],
                "email": ["valid@example.com", "invalid@com"],
            }
        )
        participants, errors = validate_participants(df)

        # Les deux participants sont créés
        assert len(participants) == 2
        # Mais erreur pour email invalide
        assert len(errors) > 0
        assert any("invalid@com" in err for err in errors)

    def test_duplicate_detection(self) -> None:
        """Test détection doublons."""
        df = pd.DataFrame(
            {
                "nom": ["Dupont", "Dupont"],
                "prenom": ["Jean", "Jean"],
            }
        )
        participants, errors = validate_participants(df)

        # Les deux participants sont créés (doublons autorisés, juste signalés)
        assert len(participants) == 2
        # Erreur signalée
        assert len(errors) > 0
        assert any("doublon" in err.lower() for err in errors)

    def test_tags_parsing(self) -> None:
        """Test parsing tags."""
        df = pd.DataFrame(
            {
                "nom": ["Dupont", "Martin", "Bernard"],
                "tags": ["VIP,Speaker", "VIP", ""],
            }
        )
        participants, errors = validate_participants(df)

        assert participants[0].tags == ["VIP", "Speaker"]
        assert participants[1].tags == ["VIP"]
        assert participants[2].tags == []

    def test_normalize_data(self) -> None:
        """Test normalisation données."""
        df = pd.DataFrame(
            {
                "nom": ["  DUPONT  "],
                "prenom": ["JEAN"],
                "email": ["  TEST@EXAMPLE.COM  "],
            }
        )
        participants, errors = validate_participants(df)

        assert participants[0].nom == "Dupont"
        assert participants[0].prenom == "Jean"
        assert participants[0].email == "test@example.com"


class TestParseCSV:
    """Tests pour le parsing CSV."""

    def test_parse_csv_with_comma_delimiter(self) -> None:
        """Test parsing CSV avec délimiteur virgule."""
        # Créer fichier temporaire
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv", encoding="utf-8"
        ) as tmp:
            tmp.write("nom,prenom,email\n")
            tmp.write("Dupont,Jean,jean@example.com\n")
            tmp.write("Martin,Marie,marie@example.com\n")
            tmp_path = tmp.name

        try:
            df = parse_csv(tmp_path)
            assert len(df) == 2
            assert list(df.columns) == ["nom", "prenom", "email"]
            assert df["nom"].iloc[0] == "Dupont"
        finally:
            Path(tmp_path).unlink()

    def test_parse_csv_with_semicolon_delimiter(self) -> None:
        """Test parsing CSV avec délimiteur point-virgule."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv", encoding="utf-8"
        ) as tmp:
            tmp.write("nom;prenom;email\n")
            tmp.write("Dupont;Jean;jean@example.com\n")
            tmp_path = tmp.name

        try:
            df = parse_csv(tmp_path, delimiter=";")
            assert len(df) == 1
            assert df["nom"].iloc[0] == "Dupont"
        finally:
            Path(tmp_path).unlink()


class TestParseExcel:
    """Tests pour le parsing Excel."""

    def test_parse_excel_first_sheet(self) -> None:
        """Test parsing Excel (première sheet)."""
        # Créer fichier temporaire Excel
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp_path = tmp.name

        try:
            df_test = pd.DataFrame(
                {
                    "nom": ["Dupont", "Martin"],
                    "prenom": ["Jean", "Marie"],
                    "email": ["jean@example.com", "marie@example.com"],
                }
            )
            df_test.to_excel(tmp_path, index=False, sheet_name="Participants")

            df = parse_excel(tmp_path, "Participants")
            assert len(df) == 2
            assert list(df.columns) == ["nom", "prenom", "email"]
        finally:
            Path(tmp_path).unlink()

    def test_parse_excel_by_index(self) -> None:
        """Test parsing Excel par index sheet."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp_path = tmp.name

        try:
            df_test = pd.DataFrame({"nom": ["Dupont"], "prenom": ["Jean"]})
            df_test.to_excel(tmp_path, index=False)

            # Parse première sheet par index
            df = parse_excel(tmp_path, "0")
            assert len(df) == 1
        finally:
            Path(tmp_path).unlink()


class TestParticipantModel:
    """Tests pour le modèle Participant."""

    def test_participant_creation(self) -> None:
        """Test création participant."""
        p = Participant(
            id=0,
            nom="Dupont",
            prenom="Jean",
            email="jean@example.com",
            groupe="Groupe A",
            tags=["VIP"],
        )

        assert p.id == 0
        assert p.nom == "Dupont"
        assert p.prenom == "Jean"
        assert p.email == "jean@example.com"
        assert p.groupe == "Groupe A"
        assert p.tags == ["VIP"]

    def test_participant_full_name(self) -> None:
        """Test propriété full_name."""
        p1 = Participant(id=0, nom="Dupont", prenom="Jean")
        assert p1.full_name == "Jean Dupont"

        p2 = Participant(id=1, nom="Martin")
        assert p2.full_name == "Martin"

    def test_participant_defaults(self) -> None:
        """Test valeurs par défaut."""
        p = Participant(id=0, nom="Dupont")

        assert p.prenom is None
        assert p.email is None
        assert p.groupe is None
        assert p.tags == []

    def test_participant_validation(self) -> None:
        """Test validation champs."""
        # ID négatif invalide
        with pytest.raises(ValueError):
            Participant(id=-1, nom="Dupont")

        # Nom vide invalide
        with pytest.raises(ValueError):
            Participant(id=0, nom="")
