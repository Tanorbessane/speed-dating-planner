# 🚀 Déploiement Immédiat - Guide Rapide

**Temps estimé** : 15 minutes
**Coût** : 0€ (tier gratuit)

---

## Option 1 : Streamlit Cloud (RECOMMANDÉ - Gratuit) ⚡

### Étape 1 : Préparer le Code (2 min)

```bash
# Vérifier que requirements.txt existe
cat requirements.txt

# Si manquant, créer :
cat > requirements.txt << 'EOF'
streamlit==1.31.0
pandas==2.2.0
plotly==5.18.0
reportlab==4.4.9
kaleido==1.2.0
Pillow==10.2.0
scipy==1.12.0
EOF
```

### Étape 2 : Push sur GitHub (3 min)

```bash
# Initialiser git si pas déjà fait
git init
git add .
git commit -m "Production ready v2.0 - Speed Dating Planner"

# Créer repo GitHub (via interface web github.com/new)
# Puis :
git remote add origin https://github.com/VOTRE_USERNAME/speed-dating-planner.git
git branch -M main
git push -u origin main
```

### Étape 3 : Déployer sur Streamlit Cloud (5 min)

1. **Aller sur** : https://share.streamlit.io
2. **Sign in** avec GitHub
3. **New app** → Sélectionner votre repository
4. **Configurer** :
   - Main file path : `app/main.py`
   - Python version : 3.10
5. **Deploy !**

✅ **URL générée** : `https://VOTRE_USERNAME-speed-dating-planner.streamlit.app`

### Étape 4 : Configurer Domaine Custom (Optionnel) (5 min)

1. **Acheter domaine** : Namecheap, Gandi (~10€/an)
2. **DNS Settings** :
   ```
   Type: CNAME
   Name: www
   Value: VOTRE_USERNAME-speed-dating-planner.streamlit.app
   ```
3. **Attendre** : Propagation DNS (5-30 min)

✅ **Votre app** : `https://www.speeddating-planner.com`

---

## Option 2 : Railway (Professionnel - 5€/mois) 🚂

### Setup Complet en 10 minutes

```bash
# 1. Créer fichier railway.toml
cat > railway.toml << 'EOF'
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0"
healthcheckPath = "/"
restartPolicyType = "ON_FAILURE"
EOF

# 2. Créer .env.example
cat > .env.example << 'EOF'
# Configuration Production
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@host:5432/dbname
STRIPE_PUBLIC_KEY=pk_live_xxx
STRIPE_SECRET_KEY=sk_live_xxx
EOF

# 3. Push sur GitHub
git add railway.toml .env.example
git commit -m "Add Railway config"
git push
```

**Puis** :
1. Aller sur https://railway.app
2. **New Project** → Deploy from GitHub
3. Sélectionner repo
4. Ajouter **PostgreSQL** (Database addon)
5. Configurer variables :
   ```
   SECRET_KEY=généré-automatiquement
   DATABASE_URL=auto-fournie-par-railway
   ```
6. **Deploy** → URL live en 2 min !

✅ **URL** : `https://speed-dating-planner.up.railway.app`

---

## Option 3 : Docker + VPS (Contrôle Total) 🐳

### Fichier Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Copier requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier code
COPY . .

# Port
EXPOSE 8501

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Commande
CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - app
    restart: unless-stopped
```

### Déploiement sur VPS

```bash
# SSH vers serveur
ssh root@VOTRE_IP

# Installer Docker
curl -fsSL https://get.docker.com | sh

# Cloner repo
git clone https://github.com/VOTRE_USERNAME/speed-dating-planner.git
cd speed-dating-planner

# Créer .env
cp .env.example .env
nano .env  # Éditer

# Lancer
docker-compose up -d

# Logs
docker-compose logs -f
```

✅ **Accès** : `http://VOTRE_IP:8501`

### SSL avec Let's Encrypt

```bash
# Installer Certbot
sudo apt install certbot python3-certbot-nginx

# Obtenir certificat
sudo certbot --nginx -d speeddating-planner.com -d www.speeddating-planner.com

# Auto-renouvellement
sudo certbot renew --dry-run
```

✅ **HTTPS** : `https://speeddating-planner.com`

---

## 📊 Comparatif Options

| Critère | Streamlit Cloud | Railway | VPS Docker |
|---------|----------------|---------|------------|
| **Coût** | 0€ (Free tier) | 5€/mois | 12€/mois |
| **Setup** | 15 min | 20 min | 60 min |
| **Scalabilité** | ⭐⭐ (limité) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Maintenance** | 0 (géré) | Faible | Moyenne |
| **Custom Domain** | ✅ Gratuit | ✅ Gratuit | ✅ (~10€/an) |
| **SSL** | ✅ Auto | ✅ Auto | Manuel |
| **Database** | ❌ | ✅ Incluse | ✅ DIY |
| **Auth** | DIY | DIY | DIY |
| **Idéal pour** | MVP/Test | Production | Enterprise |

---

## 🔐 Ajouter Authentification Simple

### Fichier : `app/auth_simple.py`

```python
import streamlit as st
import hashlib

# Users hardcodés (remplacer par DB en production)
USERS = {
    "demo@example.com": {
        "password_hash": hashlib.sha256("demo123".encode()).hexdigest(),
        "tier": "pro"
    }
}

def check_login():
    """Vérifier authentification."""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("🔐 Connexion")

        with st.form("login"):
            email = st.text_input("Email")
            password = st.text_input("Mot de passe", type="password")
            submit = st.form_submit_button("Se connecter")

            if submit:
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                user = USERS.get(email)

                if user and user['password_hash'] == password_hash:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.session_state.user_tier = user['tier']
                    st.success("✅ Connecté !")
                    st.rerun()
                else:
                    st.error("❌ Email ou mot de passe incorrect")

        st.stop()
```

### Modifier `app/main.py`

```python
# AJOUTER EN HAUT du fichier (après imports)
from auth_simple import check_login

# AVANT st.set_page_config
check_login()

# Le reste du code continue normalement...
```

✅ **Login requis** avant d'accéder à l'app !

---

## 💳 Intégration Stripe (Paiements)

### 1. Créer compte Stripe

- https://stripe.com → Sign up
- Activer compte (vérification)
- Récupérer clés : Dashboard → Developers → API Keys

### 2. Créer produits Stripe

```python
# Script à exécuter une fois
import stripe

stripe.api_key = "sk_test_..."

# Plan Pro
product_pro = stripe.Product.create(name="Plan Pro")
price_pro = stripe.Price.create(
    product=product_pro.id,
    unit_amount=2900,  # 29€
    currency="eur",
    recurring={"interval": "month"}
)

print(f"Pro Price ID: {price_pro.id}")
# Sauvegarder cet ID !
```

### 3. Ajouter checkout

```python
# app/stripe_checkout.py
import streamlit as st
import stripe

stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

def create_checkout_session(tier: str):
    """Créer session paiement."""
    prices = {
        'pro': 'price_1234_pro',  # Remplacer par vos IDs
        'business': 'price_1234_business'
    }

    session = stripe.checkout.Session.create(
        customer_email=st.session_state.user_email,
        payment_method_types=['card'],
        line_items=[{'price': prices[tier], 'quantity': 1}],
        mode='subscription',
        success_url='https://your-app.com/success',
        cancel_url='https://your-app.com/cancel',
    )

    return session.url

# Dans votre page pricing
if st.button("Upgrade vers Pro"):
    checkout_url = create_checkout_session('pro')
    st.markdown(f'<meta http-equiv="refresh" content="0;url={checkout_url}">', unsafe_allow_html=True)
```

---

## 📱 Landing Page Express

### Template HTML Simple

```html
<!DOCTYPE html>
<html>
<head>
    <title>Speed Dating Planner - Créez plannings parfaits en 1 clic</title>
    <meta charset="utf-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }

        .hero {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 100px 20px;
            text-align: center;
        }

        .hero h1 { font-size: 48px; margin-bottom: 20px; }
        .hero p { font-size: 24px; margin-bottom: 40px; }

        .cta {
            background: white;
            color: #667eea;
            padding: 15px 40px;
            font-size: 18px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }

        .features {
            max-width: 1200px;
            margin: 80px auto;
            padding: 0 20px;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 40px;
        }

        .feature {
            text-align: center;
            padding: 30px;
        }

        .feature h3 { font-size: 24px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="hero">
        <h1>🎯 Créez des plannings Speed Dating parfaits en 1 clic</h1>
        <p>0 erreur garantie. 100% équité. Export PDF professionnel.</p>
        <a href="https://your-app.streamlit.app" class="cta">Essayer Gratuitement</a>
    </div>

    <div class="features">
        <div class="feature">
            <div style="font-size: 60px;">⚡</div>
            <h3>Ultra Rapide</h3>
            <p>Génération en < 1 seconde pour 100 participants</p>
        </div>

        <div class="feature">
            <div style="font-size: 60px;">⚖️</div>
            <h3>Équité Garantie</h3>
            <p>Écart max = 1 rencontre entre tous les participants</p>
        </div>

        <div class="feature">
            <div style="font-size: 60px;">📊</div>
            <h3>Export Pro</h3>
            <p>PDF haute résolution avec graphiques et analyses</p>
        </div>
    </div>
</body>
</html>
```

**Hébergement gratuit** :
- GitHub Pages (gratuit)
- Netlify (gratuit)
- Vercel (gratuit)

---

## ✅ Checklist Pré-Déploiement

### Code
- [ ] Tests passent (309/315 ✅)
- [ ] requirements.txt à jour
- [ ] .env.example créé
- [ ] .gitignore inclut .env, __pycache__, *.pyc
- [ ] README.md complet

### Sécurité
- [ ] Secrets pas committés (check git log)
- [ ] Variables environnement utilisées
- [ ] Input validation (injections SQL/XSS)
- [ ] HTTPS activé

### UX
- [ ] Page d'accueil moderne ✅
- [ ] Toutes les pages accessibles
- [ ] Pas d'erreurs 404
- [ ] Mobile responsive

### Business
- [ ] Landing page prête
- [ ] Email support@ configuré
- [ ] CGU/CGV rédigées (template: termsfeed.com)
- [ ] Google Analytics ajouté

---

## 🚀 DÉPLOYEZ MAINTENANT !

**Choix recommandé pour MVP** :

✅ **Streamlit Cloud Free** (0€)
- Parfait pour tester le marché
- URL publique immédiate
- Upgrade facile vers paid si succès

**Commandes rapides** :

```bash
# 1. Commit final
git add .
git commit -m "🚀 Production ready v2.0"
git push

# 2. Déployer (via https://share.streamlit.io)
# 3. Partager URL
# 4. Collecter feedback
# 5. Itérer !
```

---

## 📞 Support Déploiement

**Problèmes ?**

- **Streamlit Cloud** : https://docs.streamlit.io/streamlit-community-cloud
- **Railway** : https://docs.railway.app
- **Discord** : Streamlit Community

**Besoin d'aide ?**

Ouvrez une issue GitHub : https://github.com/VOTRE_USERNAME/speed-dating-planner/issues

---

**Bon déploiement ! 🎉**
