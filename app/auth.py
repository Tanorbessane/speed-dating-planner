"""Système d'authentification pour Speed Dating Planner.

Gestion des utilisateurs, login, signup, et tiers (Free, Pro, Business).
"""

import sqlite3
import hashlib
import secrets
import os
from datetime import datetime, timedelta
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
                subscription_status TEXT DEFAULT 'inactive',
                reset_token TEXT,
                reset_token_expires TIMESTAMP
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
    ) -> Tuple[bool, str, Optional[Dict]]:
        """Créer un nouveau compte utilisateur.

        Args:
            email: Email de l'utilisateur (unique)
            password: Mot de passe en clair
            first_name: Prénom (optionnel)
            last_name: Nom (optionnel)
            company: Entreprise (optionnel)
            tier: Niveau (free, pro, business)

        Returns:
            (success, message, user_data)
        """
        # Validation
        if not email or "@" not in email:
            return False, "❌ Email invalide", None

        if len(password) < 6:
            return False, "❌ Le mot de passe doit contenir au moins 6 caractères", None

        # Hash password
        password_hash = self._hash_password(password)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO users (email, password_hash, first_name, last_name, company, tier)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (email, password_hash, first_name, last_name, company, tier))

            user_id = cursor.lastrowid
            conn.commit()
            conn.close()

            # Retourner les données utilisateur pour auto-login
            user_data = {
                "id": user_id,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "company": company,
                "tier": tier,
                "created_at": datetime.now().isoformat(),
                "is_active": True
            }

            return True, "✅ Compte créé avec succès !", user_data

        except sqlite3.IntegrityError:
            return False, "❌ Cet email est déjà utilisé", None
        except Exception as e:
            return False, f"❌ Erreur lors de la création du compte : {str(e)}", None

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

    def generate_reset_token(self, email: str) -> Tuple[bool, str]:
        """Générer un token de réinitialisation de mot de passe.

        Args:
            email: Email de l'utilisateur

        Returns:
            (success, message)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Vérifier si l'email existe
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            return False, "❌ Aucun compte associé à cet email"

        # Générer token (6 chiffres)
        token = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        expires = datetime.now() + timedelta(hours=1)

        # Sauvegarder token
        cursor.execute("""
            UPDATE users
            SET reset_token = ?, reset_token_expires = ?
            WHERE email = ?
        """, (token, expires.isoformat(), email))

        conn.commit()
        conn.close()

        return True, f"📧 Code de réinitialisation : **{token}** (valide 1h)\n\n*En production, ce code serait envoyé par email*"

    def reset_password(self, email: str, token: str, new_password: str) -> Tuple[bool, str]:
        """Réinitialiser le mot de passe avec un token.

        Args:
            email: Email de l'utilisateur
            token: Token de réinitialisation
            new_password: Nouveau mot de passe

        Returns:
            (success, message)
        """
        if len(new_password) < 6:
            return False, "❌ Le mot de passe doit contenir au moins 6 caractères"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT reset_token, reset_token_expires
            FROM users
            WHERE email = ?
        """, (email,))

        result = cursor.fetchone()

        if not result or not result[0]:
            conn.close()
            return False, "❌ Aucun code de réinitialisation actif"

        stored_token = result[0]
        expires = datetime.fromisoformat(result[1])

        if datetime.now() > expires:
            conn.close()
            return False, "❌ Le code a expiré. Demandez-en un nouveau"

        if token != stored_token:
            conn.close()
            return False, "❌ Code incorrect"

        # Réinitialiser le mot de passe
        new_hash = self._hash_password(new_password)
        cursor.execute("""
            UPDATE users
            SET password_hash = ?, reset_token = NULL, reset_token_expires = NULL
            WHERE email = ?
        """, (new_hash, email))

        conn.commit()
        conn.close()

        return True, "✅ Mot de passe réinitialisé avec succès !"

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
    """Page de login/signup avec design moderne."""

    # CSS personnalisé pour la page d'auth
    st.markdown("""
    <style>
        /* Centrer le contenu */
        .block-container {
            max-width: 600px;
            padding-top: 3rem;
        }

        /* Style des onglets */
        .stTabs [data-baseweb="tab-list"] {
            gap: 20px;
            background-color: #f7fafc;
            padding: 10px;
            border-radius: 10px;
        }

        .stTabs [data-baseweb="tab"] {
            padding: 12px 30px;
            font-weight: 600;
            border-radius: 8px;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        /* Boutons */
        .stButton > button {
            font-weight: 600;
            border-radius: 8px;
            padding: 12px 24px;
        }

        /* Messages */
        .stAlert {
            border-radius: 8px;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header avec logo/titre
    st.markdown("""
    <div style='text-align: center; padding: 20px 0;'>
        <h1 style='color: #667eea; font-size: 2.5rem; margin-bottom: 10px;'>
            🎯 Speed Dating Planner
        </h1>
        <p style='color: #4a5568; font-size: 1.1rem;'>
            Plannings optimisés en 1 clic
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    tab1, tab2, tab3 = st.tabs(["🔑 Connexion", "✨ Créer un Compte", "🔓 Mot de Passe Oublié"])

    auth_manager = st.session_state.auth_manager

    # ===== TAB 1 : LOGIN =====
    with tab1:
        with st.form("login_form", clear_on_submit=False):
            st.markdown("### Connectez-vous à votre compte")

            email = st.text_input("📧 Email", placeholder="votre@email.com", key="login_email")
            password = st.text_input("🔒 Mot de passe", type="password", placeholder="••••••••", key="login_password")

            col1, col2 = st.columns([3, 1])
            with col1:
                submit = st.form_submit_button("Se Connecter", use_container_width=True, type="primary")
            with col2:
                if st.form_submit_button("Annuler", use_container_width=True):
                    st.rerun()

            if submit:
                if not email or not password:
                    st.error("❌ Veuillez remplir tous les champs")
                else:
                    with st.spinner("Connexion en cours..."):
                        success, user_data = auth_manager.authenticate(email, password)

                        if success:
                            st.session_state.authenticated = True
                            st.session_state.user = user_data
                            st.success(f"✅ Bienvenue **{user_data['first_name'] or user_data['email']}** !")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Email ou mot de passe incorrect")

        st.caption("Pas encore de compte ? Utilisez l'onglet **Créer un Compte**")

    # ===== TAB 2 : SIGNUP =====
    with tab2:
        with st.form("signup_form", clear_on_submit=True):
            st.markdown("### Créez votre compte gratuit")

            st.info("🎉 **Plan Free inclus** : 30 participants, 3 sessions, export CSV/JSON")

            email = st.text_input("📧 Email *", placeholder="votre@email.com", key="signup_email")

            col1, col2 = st.columns(2)
            with col1:
                password = st.text_input("🔒 Mot de passe *", type="password", placeholder="Min. 6 caractères", key="signup_password")
            with col2:
                password_confirm = st.text_input("🔒 Confirmer *", type="password", placeholder="Même mot de passe", key="signup_password_confirm")

            st.markdown("**Informations personnelles** (optionnel)")

            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("Prénom", placeholder="Jean", key="signup_first_name")
            with col2:
                last_name = st.text_input("Nom", placeholder="Dupont", key="signup_last_name")

            company = st.text_input("Entreprise", placeholder="Mon Entreprise (optionnel)", key="signup_company")

            st.divider()

            submit = st.form_submit_button("✨ Créer mon Compte Gratuit", use_container_width=True, type="primary")

            if submit:
                if not email or not password:
                    st.error("❌ Email et mot de passe obligatoires")
                elif password != password_confirm:
                    st.error("❌ Les mots de passe ne correspondent pas")
                else:
                    with st.spinner("Création de votre compte..."):
                        success, message, user_data = auth_manager.create_user(
                            email=email,
                            password=password,
                            first_name=first_name,
                            last_name=last_name,
                            company=company,
                            tier="free"
                        )

                        if success:
                            st.success(message)
                            st.success(f"🎉 Bienvenue **{first_name or email}** !")

                            # AUTO-LOGIN après signup
                            st.session_state.authenticated = True
                            st.session_state.user = user_data

                            st.balloons()
                            st.info("🚀 Redirection vers l'application...")
                            st.rerun()
                        else:
                            st.error(message)

    # ===== TAB 3 : MOT DE PASSE OUBLIÉ =====
    with tab3:
        st.markdown("### Réinitialiser votre mot de passe")

        # Étape 1 : Demander email et générer token
        with st.form("reset_request_form"):
            st.info("Entrez votre email pour recevoir un code de réinitialisation")

            email = st.text_input("📧 Email", placeholder="votre@email.com", key="reset_email")
            submit_request = st.form_submit_button("📧 Envoyer le Code", use_container_width=True, type="primary")

            if submit_request:
                if not email:
                    st.error("❌ Veuillez entrer votre email")
                else:
                    success, message = auth_manager.generate_reset_token(email)
                    if success:
                        st.success(message)
                        st.session_state.reset_email = email
                    else:
                        st.error(message)

        st.divider()

        # Étape 2 : Entrer token et nouveau mot de passe
        if "reset_email" in st.session_state:
            with st.form("reset_password_form"):
                st.markdown("**Réinitialisez votre mot de passe**")

                token = st.text_input("🔢 Code de réinitialisation", placeholder="123456", max_chars=6, key="reset_token")

                col1, col2 = st.columns(2)
                with col1:
                    new_password = st.text_input("🔒 Nouveau mot de passe", type="password", placeholder="Min. 6 caractères", key="reset_new_password")
                with col2:
                    new_password_confirm = st.text_input("🔒 Confirmer", type="password", placeholder="Même mot de passe", key="reset_new_password_confirm")

                submit_reset = st.form_submit_button("✅ Réinitialiser", use_container_width=True, type="primary")

                if submit_reset:
                    if not token or not new_password:
                        st.error("❌ Tous les champs sont obligatoires")
                    elif new_password != new_password_confirm:
                        st.error("❌ Les mots de passe ne correspondent pas")
                    else:
                        success, message = auth_manager.reset_password(
                            st.session_state.reset_email,
                            token,
                            new_password
                        )

                        if success:
                            st.success(message)
                            del st.session_state.reset_email
                            st.info("Vous pouvez maintenant vous connecter avec votre nouveau mot de passe")
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

            # Nom utilisateur
            display_name = user['first_name'] or user['email'].split('@')[0]
            st.markdown(f"### 👤 {display_name}")

            # Badge tier avec couleurs
            tier_colors = {
                "free": ("#718096", "🆓 Free"),
                "pro": ("#667eea", "⭐ Pro"),
                "business": ("#d69e2e", "💎 Business")
            }
            color, label = tier_colors.get(user['tier'], tier_colors['free'])

            st.markdown(f"""
            <div style='background: {color}; color: white; padding: 8px 16px; border-radius: 8px; text-align: center; font-weight: 600; margin-bottom: 10px;'>
                {label}
            </div>
            """, unsafe_allow_html=True)

            # Limites du plan
            auth_manager = st.session_state.auth_manager
            limits = auth_manager.get_tier_limits(user['tier'])

            with st.expander("📊 Limites de votre plan"):
                st.caption(f"👥 Participants : {limits['max_participants']}")
                st.caption(f"🔢 Sessions : {limits['max_sessions']}")
                st.caption(f"📄 PDF : {'✅' if limits['pdf_export'] else '❌'}")
                st.caption(f"⭐ VIP : {'✅' if limits['vip_management'] else '❌'}")

            # Bouton upgrade (si pas business)
            if user['tier'] != 'business':
                if st.button("⬆️ Passer à Pro", use_container_width=True, type="primary"):
                    st.switch_page("pages/7_💳_Pricing.py")

            # Logout
            st.divider()
            if st.button("🚪 Déconnexion", use_container_width=True):
                logout()
