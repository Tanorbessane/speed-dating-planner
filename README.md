# 🎯 Speed Dating Planner v2.0

**Générateur intelligent de plannings optimisés pour événements de networking**

[![Tests](https://img.shields.io/badge/tests-309%2F315%20passing-brightgreen)](https://github.com/yourusername/speed-dating-planner)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.52-red)](https://streamlit.io/)

---

## ✨ Fonctionnalités

- ⚡ **Ultra Rapide** : Génération en < 1 seconde pour 100 participants
- ⚖️ **Équité Garantie** : Écart maximum de 1 rencontre entre tous les participants
- 📊 **Analyses Avancées** : Heatmap, graphiques, métriques détaillées
- 👥 **Gestion VIP** : Priorité automatique pour participants VIP
- 💾 **Multi-Export** : CSV, JSON, PDF professionnel haute résolution
- 🎨 **Interface Moderne** : Design ergonomique et intuitif
- 🔒 **0 Répétition** : Algorithme optimisé pour maximiser rencontres uniques

---

## 🚀 Installation Rapide

```bash
# Cloner le repository
git clone https://github.com/yourusername/speed-dating-planner.git
cd speed-dating-planner

# Installer dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run app/main.py
```

**Accès** : http://localhost:8501

---

## ⚙️ Configuration

### Configuration Stripe (Paiements)

Pour activer les fonctionnalités de paiement (plans Pro et Business), configurez vos clés API Stripe :

#### Option 1 : Streamlit Secrets (Recommandé)

1. **Créer le fichier de configuration** :
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

2. **Obtenir vos clés Stripe** :
   - Créer un compte sur [stripe.com](https://stripe.com)
   - Aller dans **Developers > API keys**
   - Copier votre **Secret key** (sk_test_...) et **Publishable key** (pk_test_...)

3. **Éditer `.streamlit/secrets.toml`** :
   ```toml
   [stripe]
   secret_key = "sk_test_YOUR_SECRET_KEY_HERE"
   publishable_key = "pk_test_YOUR_PUBLISHABLE_KEY_HERE"
   ```

4. **Important** : Ne **jamais** committer `secrets.toml` dans Git (déjà dans `.gitignore`)

#### Option 2 : Variables d'Environnement (Déploiement non-Streamlit)

```bash
# Créer fichier .env
cp .env.example .env

# Éditer .env
STRIPE_SECRET_KEY=sk_test_YOUR_SECRET_KEY_HERE
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_PUBLISHABLE_KEY_HERE
```

#### Mode Test vs Production

- **Développement** : Utiliser clés **TEST** (`sk_test_`, `pk_test_`)
- **Production** : Utiliser clés **LIVE** (`sk_live_`, `pk_live_`) ⚠️ Paiements réels !

Pour plus de détails, voir [.streamlit/secrets.toml.example](.streamlit/secrets.toml.example)

---

## 📖 Guide d'Utilisation

### Workflow Simple

1. **Configuration** : Définir participants (N), tables (X), capacité (x), sessions (S)
2. **Génération** : Cliquer "Générer Planning Optimisé"
3. **Export** : Télécharger CSV, JSON ou PDF professionnel

### Format CSV Import

```csv
nom,prenom,email,vip
Dupont,Jean,jean@example.com,yes
Martin,Marie,marie@example.com,no
```

---

## 🧪 Tests

```bash
# Tous les tests
pytest tests/ -v

# Résultats : 309/315 passing (98.1%)
```

---

## 📊 Performance

- **N=100** : < 1 seconde
- **N=300** : < 2 secondes
- **N=1000** : < 30 secondes

---

## 🚀 Déploiement

### Streamlit Cloud (Gratuit)

1. Push sur GitHub
2. Aller sur [share.streamlit.io](https://share.streamlit.io)
3. Sélectionner repository
4. Deploy avec `app/main.py`

---

## 📚 Documentation Complète

### Architecture & Développement
- [Architecture Review (2026-01)](docs/ARCHITECTURE_REVIEW_2026-01.md) - Revue architecturale complète
- [Architecture Streamlit](docs/architecture-streamlit.md) - Architecture application web
- [Architecture Technique](docs/architecture.md) - Architecture core algorithm

### Déploiement & Production
- [Production Deployment Guide](docs/PRODUCTION_DEPLOYMENT_GUIDE.md)
- [Deploy Now](DEPLOY_NOW.md)

### Business & Validation
- [Marketing & Sales Strategy](docs/MARKETING_SALES_STRATEGY.md)
- [Validation Report Epic 5](docs/VALIDATION_REPORT_EPIC5.md)

---

## 📄 License

MIT License - voir [LICENSE](LICENSE)

---

## 📞 Support

- Email : support@speeddating-planner.com
- Issues : [GitHub Issues](https://github.com/yourusername/speed-dating-planner/issues)

---

<p align="center">
  Développé avec ❤️ en Python | © 2026
</p>
