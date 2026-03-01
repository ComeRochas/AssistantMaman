#!/bin/bash
# -------------------------------------------------------
# Script de lancement – Assistant Bilan Psychomoteur
# Double-cliquez sur ce fichier pour ouvrir l'application.
# -------------------------------------------------------

# Se placer dans le dossier du script (peu importe depuis où on le lance)
cd "$(dirname "$0")"

# Vérifier que streamlit est installé, sinon l'installer
if ! python3 -m streamlit --version &>/dev/null; then
    echo "Installation des dépendances (première fois seulement)…"
    pip3 install streamlit python-dotenv docxtpl openai pydantic
fi

# Vérifier que python-dotenv est disponible
python3 -c "import dotenv" 2>/dev/null || pip3 install python-dotenv

echo ""
echo "=============================================="
echo "  🧠  Assistant Bilan Psychomoteur"
echo "=============================================="
echo "  L'application va s'ouvrir dans votre"
echo "  navigateur dans quelques secondes..."
echo ""
echo "  Pour fermer l'application :"
echo "  → fermez cette fenêtre noire"
echo "=============================================="
echo ""

# Lancer l'application Streamlit
python3 -m streamlit run app.py --server.headless false --browser.gatherUsageStats false
