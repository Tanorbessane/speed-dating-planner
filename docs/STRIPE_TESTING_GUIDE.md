# 🧪 Guide de Test Stripe - Speed Dating Planner

**Date:** 2026-01-24
**Version:** 1.0
**Objectif:** Tester l'intégration Stripe en mode TEST sans vrais paiements

---

## 🎯 Vue d'Ensemble

Ce guide explique comment tester les paiements Stripe dans l'application **sans utiliser de vraies cartes bancaires** et **sans frais réels**.

---

## ⚙️ Étape 1 : Configuration des Clés TEST Stripe

### 1.1 Créer un compte Stripe (si pas encore fait)

1. Aller sur https://dashboard.stripe.com/register
2. Créer un compte **gratuit** (aucune carte requise)
3. Activer le **mode TEST** (toggle en haut à gauche du dashboard)

### 1.2 Récupérer les Clés TEST

1. Dans le dashboard Stripe, aller dans **Developers > API keys**
2. **S'assurer que le mode TEST est activé** (indicateur "Viewing test data" visible)
3. Copier les deux clés :
   - **Publishable key** : commence par `pk_test_...`
   - **Secret key** : commence par `sk_test_...` (cliquer "Reveal test key")

### 1.3 Configurer l'Application

**Option A : Streamlit Secrets (Recommandé)**

Créer le fichier `.streamlit/secrets.toml` :

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Éditer `.streamlit/secrets.toml` :

```toml
[stripe]
# ⚠️ IMPORTANT: Utiliser les clés TEST (pk_test_ et sk_test_)
secret_key = "sk_test_VOTRE_CLE_SECRETE_TEST_ICI"
publishable_key = "pk_test_VOTRE_CLE_PUBLIQUE_TEST_ICI"
```

**Option B : Variables d'Environnement**

Créer le fichier `.env` :

```bash
cp .env.example .env
```

Éditer `.env` :

```bash
STRIPE_SECRET_KEY=sk_test_VOTRE_CLE_SECRETE_TEST_ICI
STRIPE_PUBLISHABLE_KEY=pk_test_VOTRE_CLE_PUBLIQUE_TEST_ICI
```

### 1.4 Vérifier la Configuration

Lancer l'application :

```bash
streamlit run app/main.py
```

Dans les logs, vérifier :
```
INFO: Stripe initialisé en mode TEST
```

✅ Si vous voyez "mode TEST" → Configuration correcte !
❌ Si vous voyez "mode LIVE" → STOP ! Vous utilisez les clés de production !

---

## 💳 Étape 2 : Cartes de Test Stripe

Stripe fournit des **cartes de test gratuites** qui simulent différents scénarios.

### 2.1 Cartes de Test Standards

#### ✅ **Paiement Réussi (Recommandé)**

```
Numéro de carte:  4242 4242 4242 4242
MM/YY:           12/34 (ou n'importe quelle date future)
CVC:             123 (ou n'importe quel 3 chiffres)
Code postal:     12345 (ou n'importe quel code)
```

**Résultat :** Paiement accepté ✅

---

#### ✅ **Paiement avec 3D Secure (Authentication forte)**

```
Numéro de carte:  4000 0025 0000 3155
MM/YY:           12/34
CVC:             123
```

**Résultat :** Popup d'authentification 3D Secure → Cliquer "Complete" → Paiement accepté ✅

---

#### ❌ **Paiement Refusé (Carte Déclinée)**

```
Numéro de carte:  4000 0000 0000 0002
MM/YY:           12/34
CVC:             123
```

**Résultat :** Paiement refusé ❌
**Message :** "Your card was declined"

---

#### ❌ **Fonds Insuffisants**

```
Numéro de carte:  4000 0000 0000 9995
MM/YY:           12/34
CVC:             123
```

**Résultat :** Paiement refusé ❌
**Message :** "Your card has insufficient funds"

---

#### ❌ **Carte Expirée**

```
Numéro de carte:  4000 0000 0000 0069
MM/YY:           12/34
CVC:             123
```

**Résultat :** Paiement refusé ❌
**Message :** "Your card has expired"

---

### 2.2 Cartes Internationales (Test Pays Spécifiques)

#### 🇫🇷 France (EUR)
```
4000 0025 0000 1001
```

#### 🇬🇧 UK (GBP)
```
4000 0082 6000 0000
```

#### 🇺🇸 USA (USD)
```
4242 4242 4242 4242
```

---

## 🧪 Étape 3 : Scénarios de Test

### Test 1 : Paiement Pro Réussi ✅

**Objectif :** Tester le flow complet d'upgrade vers Pro

**Steps :**
1. Lancer l'application : `streamlit run app/main.py`
2. Aller sur la page **💳 Pricing**
3. Cliquer sur **"⬆️ Upgrade vers Pro - 29€/mois"**
4. Remplir le formulaire Stripe avec la carte test :
   ```
   4242 4242 4242 4242
   12/34
   123
   12345
   ```
5. Cliquer **"Subscribe"**

**Résultat attendu :**
- ✅ Redirection vers `http://localhost:8501/?session_id=cs_test_...`
- ✅ Page de confirmation avec 🎉 balloons
- ✅ Message "Paiement Réussi !"
- ✅ Email de confirmation affiché
- ✅ Plan activé : **PRO**

**Vérification dans Stripe Dashboard :**
- Aller dans **Payments** → Voir le paiement de 29€
- Aller dans **Customers** → Voir le client créé
- Aller dans **Subscriptions** → Voir l'abonnement actif

---

### Test 2 : Paiement Business Réussi ✅

**Steps :**
1. Page **💳 Pricing**
2. Cliquer **"💎 Upgrade vers Business - 99€/mois"**
3. Utiliser la carte test `4242 4242 4242 4242`
4. Subscribe

**Résultat attendu :**
- ✅ Confirmation paiement 99€
- ✅ Plan : **BUSINESS**

---

### Test 3 : Paiement Refusé (Carte Déclinée) ❌

**Objectif :** Vérifier que l'error handling fonctionne

**Steps :**
1. Page **💳 Pricing**
2. Cliquer **"⬆️ Upgrade vers Pro"**
3. Utiliser la carte qui échoue :
   ```
   4000 0000 0000 0002
   12/34
   123
   ```
4. Cliquer Subscribe

**Résultat attendu :**
- ❌ Message d'erreur Stripe : "Your card was declined"
- ✅ Utilisateur reste sur page pricing
- ✅ Aucun paiement créé dans Stripe Dashboard

---

### Test 4 : Annulation Paiement ❌

**Objectif :** Tester le flow d'annulation

**Steps :**
1. Page **💳 Pricing**
2. Cliquer **"⬆️ Upgrade vers Pro"**
3. Sur la page Stripe, cliquer **← Back** (ou fermer l'onglet)

**Résultat attendu :**
- ✅ Redirection vers `http://localhost:8501/Pricing` (cancel_url)
- ✅ Utilisateur revient sur page Pricing
- ✅ Aucun paiement créé

---

### Test 5 : 3D Secure Authentication 🔒

**Objectif :** Tester l'authentification forte

**Steps :**
1. Page **💳 Pricing**
2. Cliquer **"⬆️ Upgrade vers Pro"**
3. Utiliser la carte 3D Secure :
   ```
   4000 0025 0000 3155
   12/34
   123
   ```
4. Cliquer Subscribe

**Résultat attendu :**
- ✅ Popup 3D Secure apparaît
- ✅ Cliquer **"Complete"** dans la popup
- ✅ Paiement accepté
- ✅ Redirection vers page confirmation

---

## 📊 Étape 4 : Vérifier les Paiements dans Stripe Dashboard

### 4.1 Voir les Paiements

1. Aller sur https://dashboard.stripe.com/test/payments
2. **S'assurer d'être en mode TEST** ("Viewing test data" visible)
3. Voir la liste des paiements test

**Colonnes importantes :**
- **Amount** : Montant (29€ ou 99€)
- **Customer** : Email du client
- **Status** : `Succeeded` (réussi) ou `Failed` (échoué)
- **Created** : Date/heure du paiement

### 4.2 Voir les Clients

1. Aller sur https://dashboard.stripe.com/test/customers
2. Voir les clients créés avec leurs emails

### 4.3 Voir les Abonnements

1. Aller sur https://dashboard.stripe.com/test/subscriptions
2. Voir les abonnements actifs (Pro ou Business)

**Colonnes importantes :**
- **Customer** : Email du client
- **Plan** : Plan Pro (29€/mois) ou Business (99€/mois)
- **Status** : `Active`, `Canceled`, etc.

---

## 🔍 Étape 5 : Tester le Logging

### 5.1 Vérifier les Logs Application

Dans le terminal où Streamlit tourne, vérifier les logs :

**Paiement réussi :**
```
INFO: Stripe initialisé en mode TEST
INFO: Création checkout session Pro pour user@example.com
INFO: Checkout session Pro créée: https://checkout.stripe.com/...
```

**Paiement échoué :**
```
ERROR: Échec création checkout Pro: Configuration Stripe manquante
```

### 5.2 Activer Mode Debug (Optionnel)

Dans `app/pages/7_💳_Pricing.py`, activer le mode debug :

```python
# Dans session_state
st.session_state.debug_mode = True
```

En cas d'erreur, un expander "🐛 Debug Info" s'affichera avec le stack trace complet.

---

## 🛡️ Sécurité : Mode TEST vs LIVE

### ⚠️ IMPORTANT - Différences TEST vs LIVE

| Aspect | Mode TEST | Mode LIVE |
|--------|-----------|-----------|
| **Clés** | `pk_test_...`, `sk_test_...` | `pk_live_...`, `sk_live_...` |
| **Paiements** | ✅ Simulés (gratuit) | ❌ RÉELS (argent débité) |
| **Cartes** | Cartes test Stripe | Vraies cartes bancaires |
| **Dashboard** | "Viewing test data" | "Viewing live data" |
| **Risque** | ✅ Aucun | ❌ TRÈS ÉLEVÉ |

### ✅ Checklist Sécurité

Avant de passer en PRODUCTION (mode LIVE) :

- [ ] ✅ **Tous les tests passent** en mode TEST
- [ ] ✅ **Error handling vérifié** (cartes refusées, annulations)
- [ ] ✅ **Logs vérifiés** (pas d'erreurs inattendues)
- [ ] ✅ **Webhooks configurés** (si nécessaire)
- [ ] ✅ **Conditions générales** (CGV) et politique de remboursement en place
- [ ] ⚠️ **Remplacer clés TEST par clés LIVE** dans `.streamlit/secrets.toml`
- [ ] ⚠️ **Vérifier mode LIVE** dans logs au démarrage
- [ ] ⚠️ **Activer monitoring** (Sentry, alertes)

---

## 🐛 Troubleshooting

### Problème 1 : "Configuration Stripe manquante"

**Cause :** Clés Stripe non configurées

**Solution :**
1. Vérifier que `.streamlit/secrets.toml` existe
2. Vérifier que les clés sont bien renseignées (pas de "YOUR_...HERE")
3. Relancer Streamlit

---

### Problème 2 : "Invalid API Key"

**Cause :** Clé Stripe invalide ou mode TEST/LIVE mismatch

**Solution :**
1. Vérifier que la clé commence par `sk_test_` (pas `sk_live_`)
2. Re-copier la clé depuis Stripe Dashboard (sans espaces)
3. S'assurer d'être en mode TEST dans Stripe Dashboard

---

### Problème 3 : Redirect après paiement ne fonctionne pas

**Cause :** URLs de redirect incorrectes

**Solution :**

Dans `app/pages/7_💳_Pricing.py`, vérifier les URLs :

```python
# LOCAL (développement)
success_url = "http://localhost:8501/"
cancel_url = "http://localhost:8501/Pricing"

# PRODUCTION (Streamlit Cloud)
success_url = "https://VOTRE-APP.streamlit.app/"
cancel_url = "https://VOTRE-APP.streamlit.app/Pricing"
```

**Adapter selon votre environnement !**

---

### Problème 4 : "Your card was declined" même avec carte test

**Cause :** Possible problème Stripe ou mauvaise carte

**Solution :**
1. Vérifier que vous utilisez `4242 4242 4242 4242` (carte de base)
2. Vérifier mode TEST actif dans Stripe Dashboard
3. Essayer avec une autre carte test
4. Vérifier les logs Stripe Dashboard > Logs

---

## 📚 Ressources Officielles Stripe

- **Documentation cartes test :** https://stripe.com/docs/testing
- **Dashboard test :** https://dashboard.stripe.com/test
- **Guide Checkout :** https://stripe.com/docs/payments/checkout
- **Webhooks :** https://stripe.com/docs/webhooks
- **Support Stripe :** https://support.stripe.com

---

## ✅ Checklist de Test Complète

### Tests Fonctionnels
- [ ] ✅ Paiement Pro réussi (4242 4242 4242 4242)
- [ ] ✅ Paiement Business réussi (4242 4242 4242 4242)
- [ ] ✅ Paiement avec 3D Secure (4000 0025 0000 3155)
- [ ] ❌ Paiement refusé - carte déclinée (4000 0000 0000 0002)
- [ ] ❌ Paiement refusé - fonds insuffisants (4000 0000 0000 9995)
- [ ] ❌ Annulation paiement (bouton Back)

### Tests Techniques
- [ ] ✅ Logs "mode TEST" au démarrage
- [ ] ✅ Création checkout session (logs)
- [ ] ✅ Redirection success_url avec session_id
- [ ] ✅ Page confirmation affichée
- [ ] ✅ Paiement visible dans Stripe Dashboard
- [ ] ✅ Client créé dans Stripe Dashboard
- [ ] ✅ Abonnement actif dans Stripe Dashboard

### Tests Error Handling
- [ ] ✅ Message d'erreur user-friendly si Stripe down
- [ ] ✅ Mode debug affiche stack trace
- [ ] ✅ Logs structurés (INFO/ERROR)
- [ ] ✅ Aucun crash application

---

## 🎉 Conclusion

Vous êtes maintenant prêt à tester Stripe en toute sécurité ! 🚀

**Carte recommandée pour débuter :**
```
4242 4242 4242 4242
12/34
123
12345
```

**Prochaine étape :** Une fois tous les tests passés en mode TEST, vous pourrez passer en mode LIVE pour accepter de vrais paiements.

---

**📘 Guide créé par Winston (Architect Agent)**
**Date :** 2026-01-24
**Version :** 1.0
