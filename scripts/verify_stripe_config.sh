#!/bin/bash
# Script de vérification de la configuration Stripe
# Usage: ./scripts/verify_stripe_config.sh

set -e

echo "========================================="
echo "🔍 Vérification Configuration Stripe"
echo "========================================="
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Vérifier si le fichier secrets.toml existe
if [ -f ".streamlit/secrets.toml" ]; then
    echo -e "${GREEN}✅ Fichier .streamlit/secrets.toml trouvé${NC}"

    # Vérifier que les clés ne sont pas les placeholders
    if grep -q "YOUR_SECRET_KEY_HERE" .streamlit/secrets.toml; then
        echo -e "${RED}❌ ERREUR: secret_key contient encore 'YOUR_SECRET_KEY_HERE'${NC}"
        echo -e "${YELLOW}→ Remplacez par votre vraie clé TEST Stripe (sk_test_...)${NC}"
        exit 1
    fi

    if grep -q "YOUR_PUBLISHABLE_KEY_HERE" .streamlit/secrets.toml; then
        echo -e "${RED}❌ ERREUR: publishable_key contient encore 'YOUR_PUBLISHABLE_KEY_HERE'${NC}"
        echo -e "${YELLOW}→ Remplacez par votre vraie clé TEST Stripe (pk_test_...)${NC}"
        exit 1
    fi

    # Vérifier format des clés (sk_test_ ou sk_live_)
    SECRET_KEY=$(grep 'secret_key' .streamlit/secrets.toml | cut -d'"' -f2)
    PUB_KEY=$(grep 'publishable_key' .streamlit/secrets.toml | cut -d'"' -f2)

    if [[ $SECRET_KEY == sk_test_* ]]; then
        echo -e "${GREEN}✅ secret_key est en mode TEST (sk_test_...)${NC}"
    elif [[ $SECRET_KEY == sk_live_* ]]; then
        echo -e "${RED}⚠️  WARNING: secret_key est en mode LIVE (sk_live_...)${NC}"
        echo -e "${YELLOW}→ Pour les tests, utilisez les clés TEST (sk_test_...)${NC}"
    else
        echo -e "${RED}❌ ERREUR: secret_key a un format invalide${NC}"
        echo -e "${YELLOW}→ Doit commencer par 'sk_test_' ou 'sk_live_'${NC}"
        exit 1
    fi

    if [[ $PUB_KEY == pk_test_* ]]; then
        echo -e "${GREEN}✅ publishable_key est en mode TEST (pk_test_...)${NC}"
    elif [[ $PUB_KEY == pk_live_* ]]; then
        echo -e "${RED}⚠️  WARNING: publishable_key est en mode LIVE (pk_live_...)${NC}"
        echo -e "${YELLOW}→ Pour les tests, utilisez les clés TEST (pk_test_...)${NC}"
    else
        echo -e "${RED}❌ ERREUR: publishable_key a un format invalide${NC}"
        echo -e "${YELLOW}→ Doit commencer par 'pk_test_' ou 'pk_live_'${NC}"
        exit 1
    fi

    echo ""
    echo -e "${GREEN}✅ Configuration Stripe valide !${NC}"
    echo ""
    echo "Mode détecté: $([ $SECRET_KEY == sk_test_* ] && echo 'TEST ✅' || echo 'LIVE ⚠️ ')"
    echo ""
    echo "Prochaines étapes:"
    echo "1. Lancer l'application: ./venv/bin/streamlit run app/main.py"
    echo "2. Aller sur http://localhost:8501"
    echo "3. Tester un paiement avec: 4242 4242 4242 4242"
    echo ""

else
    echo -e "${RED}❌ ERREUR: Fichier .streamlit/secrets.toml introuvable${NC}"
    echo ""
    echo "Solution:"
    echo "1. Copier le template: cp .streamlit/secrets.toml.example .streamlit/secrets.toml"
    echo "2. Éditer .streamlit/secrets.toml"
    echo "3. Ajouter vos clés Stripe TEST"
    echo ""
    echo "Pour obtenir vos clés:"
    echo "→ https://dashboard.stripe.com/test/apikeys"
    echo ""
    exit 1
fi

echo "========================================="
