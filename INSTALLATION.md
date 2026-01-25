# 📦 Guide d'Installation - Speed Dating Planner

Ce document explique les différents modes d'installation selon vos besoins.

---

## 🎯 Modes d'Installation

### Mode 1️⃣ : Core Only (Algorithme Pur)

**Pour qui ?** Développeurs qui veulent uniquement l'algorithme d'optimisation sans interface.

**Dépendances:** Python 3.10+ uniquement (stdlib)

```bash
# Installation minimale
pip install -e .

# OU avec Poetry
poetry install
```

**Fonctionnalités disponibles:**
- ✅ Core algorithm (baseline, improvement, equity)
- ✅ Models & validation
- ✅ Metrics computation
- ❌ CLI
- ❌ Interface Streamlit
- ❌ Exports PDF
- ❌ Paiements Stripe

**Usage:**
```python
from src.models import PlanningConfig
from src.planner import generate_optimized_planning

config = PlanningConfig(N=30, X=5, x=6, S=6)
planning, metrics = generate_optimized_planning(config, seed=42)
print(f"Equity gap: {metrics.equity_gap}")
```

---

### Mode 2️⃣ : CLI (Interface Ligne de Commande)

**Pour qui ?** Utilisateurs qui veulent une interface ligne de commande lightweight.

**Dépendances:** `python-dateutil`

```bash
pip install -e ".[cli]"
```

**Fonctionnalités disponibles:**
- ✅ Core algorithm
- ✅ CLI interface (`speed-dating-planner`)
- ✅ Export CSV/JSON basique
- ❌ Interface Streamlit
- ❌ Exports PDF
- ❌ Paiements Stripe

**Usage:**
```bash
speed-dating-planner generate --N 30 --X 5 --x 6 --S 6 --output planning.json
```

---

### Mode 3️⃣ : Streamlit (Interface Web)

**Pour qui ?** Utilisateurs finaux qui veulent l'interface web complète.

**Dépendances:** `streamlit`, `pandas`, `numpy`, `plotly`, `python-dateutil`

```bash
pip install -e ".[streamlit]"
```

**Fonctionnalités disponibles:**
- ✅ Core algorithm
- ✅ Interface web Streamlit
- ✅ Visualizations (heatmap, graphiques)
- ✅ Gestion participants (CSV/Excel basique)
- ✅ Export CSV/JSON
- ⚠️ Export PDF (nécessite extra `pdf`)
- ⚠️ Paiements Stripe (nécessite extra `payments`)

**Usage:**
```bash
streamlit run app/main.py
```

---

### Mode 4️⃣ : Full (Production Complète)

**Pour qui ?** Déploiement production avec toutes les fonctionnalités.

**Dépendances:** Toutes (streamlit, pandas, plotly, reportlab, kaleido, stripe, etc.)

```bash
pip install -e ".[all]"
```

**Fonctionnalités disponibles:**
- ✅ Core algorithm
- ✅ Interface web Streamlit
- ✅ Visualizations complètes
- ✅ Gestion participants (CSV/Excel)
- ✅ Export PDF professionnel haute résolution
- ✅ Paiements Stripe (Pro/Business)
- ✅ Toutes les features

**Usage:**
```bash
streamlit run app/main.py
# Accès: http://localhost:8501
```

---

## 🔧 Installation À la Carte

Vous pouvez combiner plusieurs extras selon vos besoins :

### Streamlit + PDF (sans Stripe)
```bash
pip install -e ".[streamlit,pdf]"
```

### Streamlit + Payments (sans PDF)
```bash
pip install -e ".[streamlit,payments]"
```

### CLI + Excel
```bash
pip install -e ".[cli,excel]"
```

---

## 📋 Liste Complète des Extras

| Extra | Dépendances | Usage |
|-------|-------------|-------|
| `cli` | `python-dateutil` | Interface ligne de commande |
| `streamlit` | `streamlit`, `pandas`, `numpy`, `plotly`, `python-dateutil` | Interface web complète |
| `pdf` | `reportlab`, `kaleido`, `pillow` | Export PDF professionnel |
| `excel` | `openpyxl` | Import/export Excel |
| `payments` | `stripe` | Paiements Pro/Business |
| `viz` | `plotly`, `pandas`, `numpy` | Visualizations uniquement |
| `all` | Toutes les dépendances | Production complète |

---

## 🐍 Environnement Virtuel (Recommandé)

### Avec venv (Python standard)

```bash
# Créer environnement virtuel
python3 -m venv venv

# Activer (Linux/Mac)
source venv/bin/activate

# Activer (Windows)
venv\Scripts\activate

# Installer mode souhaité
pip install -e ".[all]"
```

### Avec Poetry

```bash
# Installer Poetry
curl -sSL https://install.python-poetry.sh | python3 -

# Installer dépendances dev
poetry install

# Installer avec extras
poetry install -E all

# OU installer uniquement certains extras
poetry install -E streamlit -E pdf
```

---

## 🔄 Migration depuis requirements.txt

Si vous utilisiez `requirements.txt` auparavant :

### Option 1 : Continuer avec requirements.txt
```bash
pip install -r requirements.txt
```
*(Toutes les dépendances, comme avant)*

### Option 2 : Migrer vers Poetry extras
```bash
# Désinstaller anciennes dépendances
pip freeze | xargs pip uninstall -y

# Installer mode souhaité
pip install -e ".[all]"  # Équivalent à requirements.txt
```

---

## 🧪 Tester l'Installation

### Core Only
```python
python -c "from src.planner import generate_optimized_planning; print('Core OK')"
```

### CLI
```bash
speed-dating-planner --help
```

### Streamlit
```bash
streamlit run app/main.py
```

### PDF Export
```python
python -c "from src.pdf_exporter import create_pdf_report; print('PDF OK')"
```

### Stripe
```python
python -c "import stripe; print('Stripe OK')"
```

---

## ⚠️ Dépendances Système (PDF Export)

Pour l'export PDF, certaines dépendances système peuvent être requises :

### Linux (Ubuntu/Debian)
```bash
sudo apt-get install libcairo2-dev pkg-config python3-dev
```

### macOS
```bash
brew install cairo pkg-config
```

### Windows
Kaleido fournit des binaires pré-compilés, aucune dépendance supplémentaire requise.

---

## 🐛 Troubleshooting

### Erreur "No module named 'streamlit'"
```bash
# Installer extra streamlit
pip install -e ".[streamlit]"
```

### Erreur "No module named 'reportlab'"
```bash
# Installer extra pdf
pip install -e ".[pdf]"
```

### Erreur "No module named 'stripe'"
```bash
# Installer extra payments
pip install -e ".[payments]"
```

### Erreur Kaleido (PDF)
```bash
# Réinstaller kaleido
pip uninstall kaleido
pip install kaleido==1.2.0 --force-reinstall
```

---

## 📚 Ressources

- [README.md](README.md) - Vue d'ensemble du projet
- [pyproject.toml](pyproject.toml) - Configuration Poetry
- [requirements.txt](requirements.txt) - Dépendances complètes (legacy)
- [docs/architecture.md](docs/architecture.md) - Architecture technique

---

## 💡 Recommandations

| Cas d'Usage | Mode Recommandé | Commande |
|-------------|-----------------|----------|
| **Développement algorithm** | Core | `pip install -e .` |
| **Scripts automation** | CLI | `pip install -e ".[cli]"` |
| **Démonstration locale** | Streamlit | `pip install -e ".[streamlit]"` |
| **Production complète** | All | `pip install -e ".[all]"` |
| **CI/CD (tests)** | Dev | `pip install -e ".[dev]"` |

---

**Bonne installation ! 🚀**
