# Speed Dating Planner - Interface Streamlit

Application web locale pour générer des plannings optimisés d'événements.

## 🚀 Lancement

```bash
# Installation dépendances (si pas déjà fait)
pip install streamlit pandas plotly

# Lancer l'application
streamlit run app/main.py
```

L'application s'ouvrira automatiquement dans votre navigateur sur `http://localhost:8501`

## 📁 Structure

```
app/
├── main.py                 # Page d'accueil (point d'entrée)
├── pages/                  # Pages multipage Streamlit
│   ├── 1_📊_Dashboard.py
│   ├── 2_⚙️_Configuration.py
│   ├── 3_🎯_Génération.py
│   ├── 4_📈_Résultats.py
│   └── 5_👥_Participants.py
├── components/             # Composants réutilisables
│   ├── kpi_cards.py
│   ├── charts.py
│   └── forms.py
├── utils/                  # Utilitaires
│   ├── session_state.py
│   └── validators.py
└── .streamlit/
    └── config.toml        # Configuration thème/serveur
```

## 🎨 Pages

### 1. Dashboard (`main.py`)
- Vue d'ensemble
- Introduction et guide rapide
- Statistiques globales

### 2. Configuration
- Formulaire paramètres (N, X, x, S)
- Validation en temps réel
- Presets configurations courantes

### 3. Génération
- Bouton "Générer planning"
- Barre de progression
- Seed customisable

### 4. Résultats
- Métriques détaillées
- Visualisations (charts, heatmap)
- Export CSV/JSON

### 5. Participants (V2.1)
- Import CSV/Excel
- Gestion contraintes
- Tags VIP

## 🔧 Développement

### Hot Reload

Streamlit détecte automatiquement les changements de code et reload l'app.

### Session State

Utiliser `st.session_state` pour persister données entre reruns :

```python
if 'planning' not in st.session_state:
    st.session_state.planning = None

# Modifier
st.session_state.planning = new_planning
```

### Composants

Créer composants réutilisables dans `components/` :

```python
# components/kpi_cards.py
import streamlit as st

def display_kpi(label, value, delta=None):
    st.metric(label=label, value=value, delta=delta)
```

## 📦 Dépendances

**Runtime** :
- `streamlit>=1.30.0` - Framework web
- `pandas>=2.0.0` - Manipulation données
- `plotly>=5.18.0` - Visualisations interactives

**Dev** :
- (mêmes que projet principal)

## 🚀 Build Executable

```bash
# Installer PyInstaller
pip install pyinstaller

# Build standalone
pyinstaller --onefile --windowed app/main.py

# Résultat : dist/main.exe (Windows) ou dist/main (Linux/Mac)
```

## 🐛 Debugging

```bash
# Logs détaillés
streamlit run app/main.py --logger.level=debug

# Désactiver cache
streamlit run app/main.py --server.runOnSave=false
```

## 📝 Notes

- **État session** : Persisté uniquement durant session browser
- **Cache** : Utiliser `@st.cache_data` pour fonctions coûteuses
- **Multipage** : Fichiers `pages/` automatiquement détectés et ajoutés au menu
