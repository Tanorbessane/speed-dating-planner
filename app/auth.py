"""Système d'authentification pour Speed Dating Planner.

Gestion des utilisateurs, login, signup, et tiers (Free, Pro, Business).
"""

import sqlite3
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Tuple
import streamlit as st


class AuthManager:
    """Gestionnaire d'authentification et d'utilisateurs."""

    def __init__(self, db_path: str = "users.db"):
        """Initialiser le gestionnaire d'authentification.

        Args:
            db_path: Chemin vers la base de données SQLite
        """
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Créer les tables si elles n'existent pas."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                company TEXT,
                tier TEXT DEFAULT 'free',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                stripe_customer_id TEXT,
                subscription_status TEXT DEFAULT 'inactive'
            )
        """)

        # Table usage_stats (pour tracker utilisation)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                participants_count INTEGER,
                sessions_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        conn.commit()
        conn.close()

    @staticmethod
    def _hash_password(password: str) -> str:
        """Hasher un mot de passe avec SHA-256.

        Args:
            password: Mot de passe en clair

        Returns:
            Hash du mot de passe
        """
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(
        self,
        email: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
        company: str = "",
        tier: str = "free"
    ) -> Tuple[bool, str]:
        """Créer un nouveau compte utilisateur.

        Args:
            email: Email de l'utilisateur (unique)
            password: Mot de passe en clair
            first_name: Prénom (optionnel)
            last_name: Nom (optionnel)
            company: Entreprise (optionnel)
            tier: Niveau (free, pro, business)

        Returns:
            (success, message)
        """
        # Validation
        if not email or "@" not in email:
            return False, "Email invalide"

        if len(password) < 6:
            return False, "Le mot de passe doit contenir au moins 6 caractères"

        # Hash password
        password_hash = self._hash_password(password)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO users (email, password_hash, first_name, last_name, company, tier)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (email, password_hash, first_name, last_name, company, tier))

            conn.commit()
            conn.close()

            return True, "Compte créé avec succès !"

        except sqlite3.IntegrityError:
            return False, "Cet email est déjà utilisé"
        except Exception as e:
            return False, f"Erreur lors de la création du compte : {str(e)}"

    def authenticate(self, email: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """Authentifier un utilisateur.

        Args:
            email: Email de l'utilisateur
            password: Mot de passe en clair

        Returns:
            (success, user_data)
        """
        password_hash = self._hash_password(password)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, email, first_name, last_name, company, tier, created_at, is_active
            FROM users
            WHERE email = ? AND password_hash = ? AND is_active = 1
        """, (email, password_hash))

        result = cursor.fetchone()

        if result:
            # Update last login
            cursor.execute("""
                UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            """, (result[0],))
            conn.commit()

            user_data = {
                "id": result[0],
                "email": result[1],
                "first_name": result[2],
                "last_name": result[3],
                "company": result[4],
                "tier": result[5],
                "created_at": result[6],
                "is_active": bool(result[7])
            }

            conn.close()
            return True, user_data
        else:
            conn.close()
            return False, None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Récupérer un utilisateur par ID.

        Args:
            user_id: ID de l'utilisateur

        Returns:
            user_data ou None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, email, first_name, last_name, company, tier, created_at, is_active
            FROM users
            WHERE id = ?
        """, (user_id,))

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                "id": result[0],
                "email": result[1],
                "first_name": result[2],
                "last_name": result[3],
                "company": result[4],
                "tier": result[5],
                "created_at": result[6],
                "is_active": bool(result[7])
            }
        return None

    def update_tier(self, user_id: int, new_tier: str) -> bool:
        """Mettre à jour le tier d'un utilisateur.

        Args:
            user_id: ID de l'utilisateur
            new_tier: Nouveau tier (free, pro, business)

        Returns:
            success
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE users SET tier = ? WHERE id = ?
            """, (new_tier, user_id))

            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def log_usage(
        self,
        user_id: int,
        action: str,
        participants_count: int = 0,
        sessions_count: int = 0
    ):
        """Logger l'utilisation d'un utilisateur.

        Args:
            user_id: ID de l'utilisateur
            action: Action effectuée (generate_planning, export_pdf, etc.)
            participants_count: Nombre de participants
            sessions_count: Nombre de sessions
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO usage_stats (user_id, action, participants_count, sessions_count)
                VALUES (?, ?, ?, ?)
            """, (user_id, action, participants_count, sessions_count))

            conn.commit()
            conn.close()
        except Exception:
            pass  # Silent fail pour ne pas bloquer l'app

    def get_tier_limits(self, tier: str) -> Dict:
        """Récupérer les limites selon le tier.

        Args:
            tier: free, pro, ou business

        Returns:
            dict avec limites
        """
        limits = {
            "free": {
                "max_participants": 30,
                "max_sessions": 3,
                "pdf_export": False,
                "vip_management": False,
                "advanced_analytics": False,
                "constraints": False,
                "name": "Free"
            },
            "pro": {
                "max_participants": 150,
                "max_sessions": 999,
                "pdf_export": True,
                "vip_management": True,
                "advanced_analytics": True,
                "constraints": True,
                "name": "Pro"
            },
            "business": {
                "max_participants": 99999,
                "max_sessions": 99999,
                "pdf_export": True,
                "vip_management": True,
                "advanced_analytics": True,
                "constraints": True,
                "name": "Business"
            }
        }

        return limits.get(tier, limits["free"])

    def check_limit(self, tier: str, limit_key: str, value: int = 0) -> Tuple[bool, str]:
        """Vérifier si une limite est respectée.

        Args:
            tier: Tier de l'utilisateur
            limit_key: Clé de la limite (max_participants, max_sessions)
            value: Valeur à vérifier

        Returns:
            (ok, message)
        """
        limits = self.get_tier_limits(tier)

        if limit_key in ["max_participants", "max_sessions"]:
            max_value = limits.get(limit_key, 0)
            if value > max_value:
                return False, f"Limite {limits['name']} dépassée : maximum {max_value}"
            return True, ""

        # Pour les features booléennes
        if limit_key in limits:
            if not limits[limit_key]:
                return False, f"Fonctionnalité disponible uniquement en Pro/Business"
            return True, ""

        return True, ""


def init_session_state():
    """Initialiser l'état de session pour l'authentification."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "auth_manager" not in st.session_state:
        st.session_state.auth_manager = AuthManager()


def login_page():
    """Page de login/signup."""
    st.title("🔐 Connexion - Speed Dating Planner")

    tab1, tab2 = st.tabs(["Se Connecter", "Créer un Compte"])

    auth_manager = st.session_state.auth_manager

    # Tab 1 : Login
    with tab1:
        st.subheader("Connexion")

        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Mot de passe", type="password", key="login_password")
            submit = st.form_submit_button("Se Connecter", use_container_width=True, type="primary")

            if submit:
                if not email or not password:
                    st.error("Veuillez remplir tous les champs")
                else:
                    success, user_data = auth_manager.authenticate(email, password)

                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user = user_data
                        st.success(f"Bienvenue {user_data['first_name'] or user_data['email']} !")
                        st.rerun()
                    else:
                        st.error("Email ou mot de passe incorrect")

    # Tab 2 : Signup
    with tab2:
        st.subheader("Créer un Compte Gratuit")

        with st.form("signup_form"):
            email = st.text_input("Email *", key="signup_email")
            password = st.text_input("Mot de passe * (min. 6 caractères)", type="password", key="signup_password")
            password_confirm = st.text_input("Confirmer mot de passe *", type="password", key="signup_password_confirm")

            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("Prénom", key="signup_first_name")
            with col2:
                last_name = st.text_input("Nom", key="signup_last_name")

            company = st.text_input("Entreprise (optionnel)", key="signup_company")

            st.info("Plan Free : 30 participants max, 3 sessions, export CSV/JSON")

            submit = st.form_submit_button("Créer mon Compte Gratuit", use_container_width=True, type="primary")

            if submit:
                if not email or not password:
                    st.error("Email et mot de passe obligatoires")
                elif password != password_confirm:
                    st.error("Les mots de passe ne correspondent pas")
                else:
                    success, message = auth_manager.create_user(
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        company=company,
                        tier="free"
                    )

                    if success:
                        st.success(message)
                        st.info("Vous pouvez maintenant vous connecter avec vos identifiants")
                    else:
                        st.error(message)


def logout():
    """Déconnecter l'utilisateur."""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()


def require_auth():
    """Middleware pour protéger les pages.

    Utiliser en début de page :
        if not require_auth():
            return
    """
    init_session_state()

    if not st.session_state.authenticated:
        login_page()
        st.stop()
        return False

    return True


def show_user_info():
    """Afficher les infos utilisateur dans la sidebar."""
    if st.session_state.authenticated and st.session_state.user:
        user = st.session_state.user

        with st.sidebar:
            st.divider()
            st.write(f"**👤 {user['first_name'] or user['email']}**")

            # Badge tier
            tier_colors = {
                "free": "🆓",
                "pro": "⭐",
                "business": "💎"
            }
            st.write(f"{tier_colors.get(user['tier'], '🆓')} **{user['tier'].upper()}**")

            # Limites
            auth_manager = st.session_state.auth_manager
            limits = auth_manager.get_tier_limits(user['tier'])

            st.caption(f"Max participants: {limits['max_participants']}")
            st.caption(f"Max sessions: {limits['max_sessions']}")

            # Bouton upgrade (si pas business)
            if user['tier'] != 'business':
                if st.button("⬆️ Upgrade", use_container_width=True):
                    st.switch_page("pages/7_💳_Pricing.py")

            # Logout
            if st.button("🚪 Déconnexion", use_container_width=True):
                logout()
