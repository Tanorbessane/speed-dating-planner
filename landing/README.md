# 🚀 Landing Page - Speed Dating Planner

Landing page professionnelle pour présenter et vendre Speed Dating Planner.

## ✨ Fonctionnalités

- ✅ Design moderne et responsive
- ✅ Hero section avec gradient
- ✅ Section features avec 6 fonctionnalités
- ✅ Pricing cards (Free, Pro, Business)
- ✅ Formulaire capture d'emails
- ✅ Animations fluides
- ✅ Mobile-first

## 🎯 Déploiement sur Netlify (GRATUIT - 5 minutes)

### Option 1 : Via Interface Web (Le Plus Simple)

1. **Aller sur Netlify** : https://www.netlify.com
2. **Sign up** avec GitHub (gratuit)
3. **New site from Git** → Choisir votre repo
4. **Build settings** :
   - Base directory: `landing`
   - Build command: (laisser vide)
   - Publish directory: `.` (ou laisser vide)
5. **Deploy !**

✅ Votre site sera live en 30 secondes : `https://RANDOM-NAME.netlify.app`

### Option 2 : Via Netlify CLI

```bash
# Installer Netlify CLI
npm install -g netlify-cli

# Se connecter
netlify login

# Déployer depuis le dossier landing/
cd landing
netlify deploy --prod

# Suivre les instructions
```

## 🎨 Déploiement sur Vercel (Alternative)

```bash
# Installer Vercel CLI
npm install -g vercel

# Se connecter
vercel login

# Déployer
cd landing
vercel --prod
```

## 📧 Configuration du Formulaire Email

Le formulaire utilise **Formspree** (gratuit jusqu'à 50 emails/mois).

### Étapes :

1. **Aller sur** : https://formspree.io
2. **Sign up** (gratuit)
3. **Create form** → Copier le Form ID
4. **Éditer `index.html`** :

```html
<!-- Ligne 403 : Remplacer YOUR_FORM_ID -->
<form class="email-form" action="https://formspree.io/f/YOUR_FORM_ID" method="POST">
```

**Alternative** : Mailchimp, ConvertKit, ou votre propre backend.

## 🔧 Personnalisation

### Modifier l'URL de l'App Streamlit

Éditer `index.html` et remplacer partout :

```html
https://tanorbessane-speed-dating-planner.streamlit.app
```

Par votre URL réelle.

### Modifier les Prix

Éditer la section `<!-- Pricing Section -->` (lignes 550+).

### Ajouter Google Analytics

Ajouter avant `</head>` :

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

## 🌐 Domaine Custom (Optionnel)

### Sur Netlify :

1. **Domain settings** → Add custom domain
2. Acheter domaine (Namecheap ~10€/an) ou utiliser existant
3. Configurer DNS :

```
Type: CNAME
Name: www
Value: YOUR-SITE.netlify.app
```

4. Attendre propagation DNS (5-30 min)

✅ Netlify génère automatiquement le certificat SSL (HTTPS).

## 📊 Prochaines Étapes

Après déploiement :

1. ✅ Tester sur mobile et desktop
2. ✅ Vérifier tous les liens
3. ✅ Configurer Formspree
4. ✅ Ajouter Google Analytics
5. ✅ Partager sur réseaux sociaux
6. ✅ Lancer campagne Google Ads

## 💡 Améliorations Futures

- [ ] Chat support (Intercom, Crisp)
- [ ] Témoignages clients
- [ ] Vidéo démo
- [ ] Blog/Articles
- [ ] Page FAQ
- [ ] Multilingue (EN/FR)

## 📞 Support

Questions ? support@speeddating-planner.com

---

**Fait avec ❤️ | © 2026**
