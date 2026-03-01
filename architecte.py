import os
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Optional, List
import json
from dotenv import load_dotenv

from models import BilanPsychomoteur

load_dotenv()  # Charge les variables depuis .env

def _get_client() -> OpenAI:
    """Crée le client OpenAI en lisant OPENAI_API_KEY au moment de l'appel."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError(
            "Clé API OpenAI introuvable. "
            "Ajoutez OPENAI_API_KEY dans le fichier .env ou saisissez-la dans l'application."
        )
    return OpenAI(api_key=key)


def transformer_notes_en_json(texte_notes: str) -> BilanPsychomoteur:
    """
    Prend le texte brut des notes et retourne un objet validé BilanPsychomoteur.
    Utilise le mode 'Structured Outputs' de GPT-4o.
    """
    print("⏳ Analyse des notes et structuration des données en cours...")
    
    completion = _get_client().beta.chat.completions.parse(
        model="gpt-4o-2024-08-06", # Ce modèle est CRITIQUE pour le respect du JSON
        messages=[
            {
                "role": "system",
                "content": (
                    "Tu es un assistant expert en psychomotricité. "
                    "Ta tâche est d'extraire des informations de notes cliniques brutes (souvent télégraphiques, "
                    "avec abréviations médicales) pour remplir une structure de bilan formelle. "
                    "Instructions :"
                    "1. Interprète les abréviations (ex: 'Mvt' -> Mouvement, 'Moro imm.' -> Réflexe de Moro immature)."
                    "2. Si une information est absente, sois factuel (indique 'Non mentionné' ou 'RAS' selon le contexte), "
                    "ne jamais inventer."
                    "3. Range chaque information dans la bonne case du JSON, même si elle est notée ailleurs dans le brouillon."
                    "4. Pour les champs 'Obligatoires' (str), si l'info manque totalement, mets 'Non évalué'."
                )
            },
            {
                "role": "user", 
                "content": f"Voici les notes brutes de la séance :\n\n{texte_notes}"
            },
        ],
        response_format=BilanPsychomoteur,
    )

    event_object = completion.choices[0].message.parsed
    
    return event_object


if __name__ == "__main__":
    # 1. Lire le fichier de notes
    fichier_entree = "notes.txt"
    
    try:
        with open(fichier_entree, "r", encoding="utf-8") as f:
            notes_brutes = f.read()
            
        # 2. Lancer l'IA
        if not notes_brutes.strip():
            print("❌ Le fichier notes.txt est vide.")
        else:
            bilan_structure = transformer_notes_en_json(notes_brutes)
            
            # 3. Sauvegarder le résultat en JSON pour vérification ou étape suivante
            output_filename = "bilan_structure.json"
            
            # On convertit l'objet Pydantic en dict, puis en JSON string
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(bilan_structure.model_dump_json(indent=4))
                
            print(f"✅ Succès ! Les données structurées sont dans '{output_filename}'")

    except FileNotFoundError:
        print(f"❌ Erreur : Le fichier '{fichier_entree}' est introuvable.")
    except Exception as e:
        print(f"❌ Une erreur est survenue : {e}")