import os
import json
from docxtpl import DocxTemplate
from docx.oxml.ns import qn
from architecte import transformer_notes_en_json
from redacteur import orchestrer_redaction
from models import BilanPsychomoteur

def generer_bilan_final(chemin_notes: str, chemin_template: str, chemin_sortie: str):
    print(f"🚀 Démarrage de la génération pour : {chemin_notes}")

    # --- ÉTAPE 1 : L'ARCHITECTE (Notes -> Structure) ---
    print(f"1️⃣  Lecture et structuration des notes...")
    try:
        with open(chemin_notes, "r", encoding="utf-8") as f:
            notes_raw = f.read()
    except FileNotFoundError:
        print(f"❌ Erreur : Le fichier {chemin_notes} est introuvable.")
        return

    # On transforme le texte en objet Pydantic
    bilan_brut: BilanPsychomoteur = transformer_notes_en_json(notes_raw)
    print("   ✅ Données structurées avec succès.")
    
    # Sauvegarde intermédiaire du bilan brut (JSON)
    with open("bilan_brut.json", "w", encoding="utf-8") as f:
        f.write(bilan_brut.model_dump_json(indent=4))

    # --- ÉTAPE 2 : LE RÉDACTEUR (Structure -> Texte Rédigé) ---
    print("2️⃣  Rédaction des paragraphes cliniques par l'IA...")
    # Cette fonction renvoie un dictionnaire de dictionnaires (ex: context_redige['anamnese']['sommeil'])
    context_redige = orchestrer_redaction(bilan_brut)
    print("   ✅ Rédaction terminée.")

    # Sauvegarde intermédiaire du texte rédigé (JSON)
    with open("context_redige.json", "w", encoding="utf-8") as f:
        json.dump(context_redige, f, ensure_ascii=False, indent=4)

    # --- ÉTAPE 3 : ASSEMBLAGE (Fusion dans Word) ---
    print(f"3️⃣  Injection dans le modèle Word...")
    
    # On prépare le contexte final pour Jinja2.
    # On aplatit la structure : context_redige contient déjà les clés 'anamnese', 'regulation_tonique', etc.
    # correspondant exactement aux balises {{ anamnese.sommeil }} du Word.
    # On injecte aussi l'identité pour éviter l'erreur Jinja2 si le template
    # contient des balises {{ identite_patient.* }}.
    final_context = {
        **context_redige,
        "identite_patient": bilan_brut.identite_patient.model_dump(),
    }

    # Chargement du template
    try:
        doc = DocxTemplate(chemin_template)
        doc.render(final_context)

        # Forcer la police par defaut du document a Calibri
        normal_style = doc.styles["Normal"]
        normal_style.font.name = "Calibri"
        normal_style._element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
        
        # Sauvegarde
        doc.save(chemin_sortie)
        print(f"🎉 Bilan généré avec succès ! Disponible ici : {chemin_sortie}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération Word : {e}")

if __name__ == "__main__":
    # Configuration des chemins
    INPUT_FILE = "notes.txt"          # Le fichier où votre mère a collé ses notes
    TEMPLATE_FILE = "templateWord.docx" # Le modèle Word corrigé
    OUTPUT_FILE = "Bilan_Genere.docx"   # Le résultat final

    generer_bilan_final(INPUT_FILE, TEMPLATE_FILE, OUTPUT_FILE)