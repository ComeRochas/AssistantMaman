from openai import OpenAI
import json
from models import BilanPsychomoteur  # Vos classes Pydantic
import os
from dotenv import load_dotenv

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

# Un dictionnaire de prompts spécifiques pour guider le style de chaque section
# (Basé sur les documents fournis comme Lucas/Victoire)
PROMPTS_STYLE = {
    "environnement_familial": (
        "Rédige au présent pour la situation actuelle. Mentionne les prénoms et les âges précis (années + mois ou 1/2). "
        "Indique la qualité de la relation si elle est mentionnée. "
        "Exemple de style : 'Victoire vit avec ses parents et sa petite sœur Faustine qui a 14 mois.'"
    ),
    
    "grossesse_naissance": (
        "Rédige au passé composé et à l'imparfait. Utilise un ton médical et factuel. Ne rajoute aucun élément qui n'est pas mentionné. "
        "Mentionne le terme (prématurité, à terme, J+5), le mode d'accouchement (voie basse, césarienne, déclenchement) et les éventuelles complications suivant la naissance ou le caractère paisible. "
        "Exemple de style : 'La grossesse s'est bien passée. [...] Le bébé se présentait en siège [...] Une césarienne a été programmée 15 jours avant le terme et la naissance s'est bien passée.'"
    ),
    
    "sante_generale": (
        "Sois concis. Utilise des termes techniques (ORL, végétations, aérateurs tympaniques, RGO). "
        "Fais le lien de cause à effet si une intervention a eu lieu. Sois factuel ici"
        "Exemple de style : 'Victoire a eu de nombreuses affections ORL étant petite, ce qui l'a conduite à être opérée des amygdales et végétations avec pose d'aérateurs tympaniques lorsqu'elle était en GS.'"
    ),
    
    "alimentation": (
        "Mentionne l'allaitement ou le biberon, puis la diversification. "
        "Utilise le terme 'sélectivité' si l'enfant trie les aliments. Décris les textures (morceaux, purées) et le comportement à table. "
        "Exemple de style : 'On note une sélectivité sur le plan des textures et des goûts : Lucas n'aime pas les plats froids [...], il préfère le salé au sucré, les textures craquantes aux consistances molles.'"
    ),
    
    "sommeil": (
        "Distingue le passé (bébé) du présent ('Maintenant', 'Actuellement'). "
        "Mentionne les rituels, la présence des parents (co-dodo), les réveils nocturnes ou cauchemars. "
        "Exemple de style et de longueur de paragraphe : ' il a été allaité jusqu’à ses 3 ans. Il est bon mangeur mais il est difficile de lui faire manger des légumes et des fruits, il est surtout très attiré par les sucreries. Cela commence à se réguler.'"
    ),
    
    "developpement_psychomoteur": (
        "Structure chronologiquement : retournements -> assis -> 4 pattes/ramper -> marche. "
        "Précise les âges en mois. Qualifie le mouvement (prudent, audacieux, mobile, peu mobile). Sois factuel en citant les éléments, mais pas besoin d'intépréter/extrapoler"
        "Exemple : 'Elle a enclenché les retournements tardivement (vers 8 mois), mais ensuite tout s'est enchainé. La marche autonome a été acquise à 15 mois. Victoire est décrite comme étant prudente, peu audacieuse.'"
    ),
    
    "proprete": (
        "Utilise les termes 'acquisition de la maîtrise sphinctérienne', 'continence diurne/nocturne'. "
        "Note les difficultés (rétention, encoprésie). "
        "Exemple de style : 'Cette étape a été difficile. Il y a des épisodes de rétention de selles, Diego a tendance à se retenir [...] Un gastroentérologue a éliminé tout problème fonctionnel.'"
    ),
    
    "language": (
        "Mentionne le bilinguisme ou l'âge d'acquisition des premiers mots si pertinent. "
        "Exemple de style : 'Lucas a d'abord acquis le vietnamien (à 18 mois), la langue française est arrivée plus tard, en cours de MS.'"
    ),
    
    "scolarite_vie_sociale": (
        "Décris l'adaptation à l'école (séparation) et le comportement actuel en classe (autonomie, respect des consignes). "
        "Aborde ensuite les relations avec les pairs (leader, suiveur, isolé, conflits). "
        "Exemple de style : 'Il fait partie d'un groupe de copains... Il est plutôt suiveur dans le groupe [...] il a pour autant la capacité d'être attracteur de l'attention bienveillante de ses camarades.'"
    ),
    
    "autonomie_quotidien": (
        "Liste simple et factuelle"
        "Exemple de style : 'à la maison, Diego joue seul. Il sait faire beaucoup de choses, mais il n’a pas envie de les faire de manière autonome. Il fait des activités en autonomie, comme la peinture. Il aime les livres.'"
        "Autre exemple de style : 'Victoire sait faire beaucoup de choses, mais elle n’a pas envie de les faire de manière autonome. Beaucoup de routines de la vie quotidien sont perçues comme des contraintes ce qui est source de tensions fréquentes.'"
    ),
    
    "activites_extrascolaires": (
        "Liste simple et factuelle. "
        "Exemple de style : 'Foot en club; Il a fait de la boxe il y a 2 ans et va reprendre. Piscine en famille.'"
    ),
    
    # --- Observations transversales
    "observations_transversales": (
        "Distingue le comportement pendant l'entretien (en présence des parents) et pendant les épreuves (relation duelle). Indique si l'enfant est 'investi et coopérant'. Précise si les consignes sont comprises. Analyse la confiance en soi et le besoin de réassurance (regard de l'adulte)."
        "Qualifie la présence (qualité de présence, 'dans sa bulle', intimidé). Note le 'coût' de l'effort (fatigue, agitation, besoin de pauses). Fais le lien entre la pression de réussite et la tension tonique ou émotionnelle."
        "Exemple de style : 'Durant le temps d’entretien, Victoire a été très attentive à tout ce qui a été dit à son sujet, et a participé aux échanges, tout en jouant de manière autonome (Légos et Playmobil). Elle s’est montrée sensible à ce que sa maman regarde régulièrement ses créations, marquant des signes d’impatience lorsque Mme n’était pas disponible de suite ; elle peut alors couper la parole, demander une attention de manière pressante. Elle s’est montrée très respectueuse du cadre et à l’écoute des consignes, elle a rangé d’elle-même les jeux lorsque j’ai annoncé la fin du RV. Elle est sensible aux renforçateurs positifs. Durant les épreuves de bilan, elle s’est montrée investie et coopérante. Sensée et sensible, très ouverte dans la relation à mon égard, elle me parle avec aisance, exprimant des ressentis et remarques très pertinentes. Elle s’est bien prêtée à toutes les épreuves du bilan, avec le souci de faire de son mieux. Les consignes données ont été comprises. Tout au long du bilan, Victoire a laissé filtrer des signes d’un manque de confiance en soi, qui semblent la mettre en tension interne, qu’elle n’exprime pas verbalement.'"
    ),
    
    # --- 4.A Régulation Tonique et Posturale ---
    "tonus_fond": (
        "Décris l'état de tension (élevé, faible, ajusté) et la qualité du muscle (mou, dur). "
        "Mentionne la 'laxité ligamentaire' ou la 'raideur' si pertinent. "
        "Indique la capacité au 'relâchement tonique volontaire' (bras/jambes). "
        "Exemple de style : 'Victoire présente une laxité ligamentaire... Je note un tonus de fond globalement élevé, dont la résistance des muscles augmente à l'étirement. Elle accède avec difficulté au relâchement tonique volontaire...'"
    ),
    
    "tonus_soutien": (
        "Parle de la 'synergie tonique des muscles' pour le maintien de l'axe ou de la station assise. "
        "Mentionne la résistance aux poussées (déséquilibre) ou le besoin d'appui (dos au mur). "
        "Exemple de style : 'Le maintien de la station assise résulte d'une synergie correcte entre les muscles antérieurs, postérieurs et latéraux du tronc, avec cependant une stratégie de compensation...'"
    ),
    
    "tonus_action": (
        "Utilise les termes 'diadococinésies' (marionnettes) et 'syncinésies'. "
        "Précise si les syncinésies sont 'bucco-faciales' ou 'd'imitation', et leur localisation (proximale/distale, controlatérale). "
        "Exemple de style : 'L'épreuve des diadococinésies (marionnettes) ne génère aucune syncinésie bucco-faciale, en revanche des syncinésies d'imitation sont observées... elles sont d'organisation distale.'"
    ),

    # --- 4.B Intégration du Schéma Corporel ---
    "connaissance_parties_corps": (
        "Indique si la connaissance est acquise et précise le niveau de détail (articulations, organes). "
        "Exemple de style : 'Lucas a une bonne connaissance des parties de son corps, dont il désigne en premier lieu les zones d'articulations (chevilles, genoux...), même s'il n'en connaît pas tous les noms.'"
        "Si non testé, indique 'Non évalué' pour ce champ obligatoire."
    ),

    "dessin_bonhomme": (
        "Sois factuel, indique simplement ce qui a été réalisé. "
        "Cite comment l'enfant nomme son dessin si mentionné. "
        "Exemple de style : 'Très sommaire, pas de traits du visage.'"
    ),

    "construction_puzzle": (
        "Phrase type standardisée. Mentionne le 'sens du schéma corporel' et 'l'orientation'. "
        "Exemple de style : 'Lucas est capable de refaire le puzzle du corps humain, avec un bon sens du schéma corporel représenté et de l'orientation du corps.'"
    ),

    "imitation_gestes": (
        "Précise 'imitation en miroir' ou 'directe'. Distingue les gestes simples (bras) et complexes (mains/doigts). "
        "Note la qualité de l'observation (regard). "
        "Exemple de style : 'Victoire est capable de reproduire en miroir les gestes simples des bras et les gestes complexes des mains... Elle mobilise les bons segments corporels.'"
    ),

    "gnosies_tactiles": (
        "Teste la perception tactile et la discrimination des doigts. "
        "Fais le lien avec l'attention et la mémoire à court terme (phrase type importante). "
        "Exemple de style : 'Cette intégration somatognosique donne une indication sur les capacités [...] en termes d'attention, de concentration sur la stimulation, et l'efficacité de sa mémoire à court terme.'"
    ),

    "reactivite_sensorielle": (
        "Analyse le filtrage sensoriel (tactile, auditif, visuel). "
        "Conclus toujours par une phrase indiquant si la piste sensorielle explique ou non les difficultés de l'enfant. "
        "Exemple de style : 'Il est possible que la perception et la modulation de l'information sensorielle soient [...] un paramètre potentiellement perturbateur du fonctionnement...'"
        "Exemple de style : 'La piste sensorielle peut être écartée car elle n'explique pas ses comportements et ses réactions émotionnelles.'"
    ),
    
    "organisation_posturale": (
        "Décris les réflexes primordiaux (Moro intégré ou non) et la qualité des appuis (assis, schèmes de redressement). "
        "Note les tensions spécifiques (tonus pneumatique, raideur, mains dans les poches). "
        "Exemple de style : 'Réflexes primordiaux : l'intégration du réflexe de Moro est immature. [...] Une raideur maintient la cohésion posturale... Les bras ballants sont tenus le long du corps.'"
    ),

    "coordination_dynamique": (
        "Détaille la marche (sur ligne, pointes, talons) et la course (alternance des bras). "
        "Mentionne l'impact sur le tonus (pas d'extension notable, ou raideur). "
        "Exemple de style : 'La marche sur les pointes de pieds est correctement exécutée, les 2 pieds sont bien sur les pointes... La course est réalisée avec alternance des bras, Issa sait accélérer, ralentir.'"
    ),

    "equilibre": (
        "Distingue yeux ouverts/fermés. Mentionne la stabilité de l'axe et les crispations éventuelles (épaules, visage). "
        "Précise le pied de soutien préférentiel. "
        "Exemple de style : 'Pour l'équilibre pieds joints les yeux fermés, les bras restent stables... L'équilibre unipodal est réalisé préférentiellement sur le pied de soutien droit; la posture est tenue avec une grande tension dans les épaules.'"
    ),

    "coordinations_visuo_motrices": (
        "Décris la réception (mains ou buste ?) et le lancer (mouvement pendulaire, adaptation de la force). "
        "Note la qualité du regard (suivi de trajectoire). Reste factuelle. "
        "Exemple de style : 'Sacha attrape le sac dans ses mains; son organisation posturale est favorable... Il lance le sac lesté avec un mouvement pendulaire adapté... L'adaptation de la force se fait progressivement.'"
    ),

    "dissociations": (
        "Analyse la synchronisation haut/bas du corps. "
        "Indique si l'enfant s'appuie sur l'imitation pour réussir et si le mouvement s'automatise. "
        "Exemple de style : 'Les séquences motrices... révèlent des difficultés de dissociation... on observe une rapide désynchronisation des mouvements des jambes par rapport à ceux du haut du corps.'"
    ),

    # --- 4.E Habiletés Oculo-Manuelles - Motricité Fine ---
    "dexterite_manuelle": (
        "Qualifie la pince (supérieure, pouce-index) et le déliement des doigts. "
        "Note la fluidité et les éventuelles diffusions toniques sur l'autre main. "
        "Exemple de style : 'Le positionnement des doigts pour la pince est mature... Le déliement digital permis par l'indépendance des doigts est opérant.'"
    ),

    "coordinations_oculo_manuelles": (
        "Cite les épreuves (perles, cubes, puzzle). "
        "Insiste sur la stratégie (essai/erreur, planification) et le rôle du regard. "
        "Exemple de style : 'La posture est stable... le regard guide efficacement la main... Pour réaliser le puzzle, Issa montre une bonne capacité d'organisation visuo-constructive... Il avance par essai / déduction / ajustements.'"
    ),

    "graphisme_ecriture": (
        "Sois très technique : description de la prise (tridigitale, dynamique/statique), position du poignet (prolongement avant-bras), appuis (pieds, main qui tient la feuille). "
        "Mentionne la fluidité du tracé et la reproduction de formes. "
        "Exemple de style : 'Sa préhension du crayon est statique, il stabilise le crayon avec la base de son pouce... il a recours à une autre stratégie en dégageant son poignet de la table...'"
    ),

    "praxies_habillage": (
        "Phrase courte indiquant si c'est acquis ou non, et les difficultés spécifiques (boutons, sens). "
        "Exemple de style : 'Des difficultés dans les praxies de l'habillage : difficultés à trouver le sens d'un vêtement... Issa peut ne pas oser demander de l'aide.'"
    ),

    "praxies_faciales": (
        "Liste les actions : souffler, gonfler les joues, claquer la langue, mobilité de la langue (4 directions). "
        "Exemple de style : 'Lucas peut mobiliser efficacement la musculature de son visage pour souffler, gonfler les joues, claquer la langue. La langue est mobilisable dans les 4 directions.'"
    ),
    
    # --- 4.F Latéralité ---
    "dominance": (
        "Synthétise les 3 pôles (main, pied, œil). Utilise des formules techniques comme 'profil de latéralité harmonieuse' ou 'concordance avec la latéralité tonique'. "
        "Précise si c'est homogène ou croisé. "
        "Exemple de style : 'Victoire présente un profil de latéralité harmonieuse et homogène. La latéralité manuelle et la latéralité pédestre sont affirmées à droite et concordent avec la latéralité tonique. La latéralité oculaire s’établit à gauche.'"
    ),

    # --- 4.G Organisation Spatiale ---
    "organisation_spatiale": (
        "Indique simplement si la connaissance est 'acquise', 'floue' ou 'en cours d'acquisition'. "
        "Exemple de style : 'La connaissance des repères spatiaux est acquise.'"
    ),

    "orientation": (
        "Analyse l'intégration des axes corporels et le 'croisement de la ligne médiane'. "
        "Distingue le repérage sur soi vs sur autrui. "
        "Exemple de style : 'La capacité de Victoire à se placer corporellement à partir de repères spatiaux est bien construite.'"
    ),

    "adaptation_spatiale": (
        "Décris l'ajustement aux distances (adaptation de la taille des pas) et la prise en compte de l'environnement (obstacles, limites de la pièce). "
        "Exemple de style : 'L'ajustement aux distances est fragile: Lucas ne parvient pas à ajuster la taille de ses pas en fonction du nombre de pas demandés...'"
    ),

    # --- 4.H Organisation Temporelle ---
    "organisation_temporelle": (
        "Utilise un vocabulaire spécifique : 'structures rythmiques simples', 'tempii du métronome', 'périodicité', 'synchronisation'. "
        "Note l'impact de la vitesse et la réussite en double tâche (mains/pieds). "
        "Liste les acquis cognitifs (jours, mois, date)."
        "Exemple de style : 'Il perçoit correctement la périodicité du rythme entendu... La vitesse ne désorganise pas ses mouvements. Il parvient difficilement à reproduire les frappés...'"
        "Indique par une phrase si l'acquisition est cohérente avec l'âge de l'enfant. "
        "Si non évalué, indique 'Les connaissances temporelles et perception sensorielle et d’intégration sensori-motrice au niveau rythmique n’ont pas pu être évaluées' pour ce champ obligatoire."
    ),
    
    "regulation_emotionnelle": (
        "Décris les émotions dominantes (colère, peur, anxiété, frustration). "
        "Analyse les déclencheurs (changement, échec, relation) et les mécanismes de régulation (débordement, recherche de l'adulte, somatisation). "
        "Exemple de style : 'Victoire présente d'importantes difficultés à réguler l'intensité de ses émotions. L'émotion principalement exprimée est la colère... Elle n'a pas encore les outils pour se réguler seule... elle a besoin de l'aide des adultes en tant que co-régulateurs.'"
    ),

    "jeu": (
        "Évalue la capacité à jouer seul ('capacité à jouer seul', 's'ennuie vite') et le type de jeu (symbolique, construction, moteur). "
        "Note le recours à l'imaginaire. "
        "Exemple de style : 'À la maison, il est capable de jouer seul, et faire des activités créatives... Il aime bien faire des spectacles... mais il est intimidé s'il doit se montrer.'"
    ),

    
    "synthese_clinique": (
        "Structure par points forts (ressources) puis fragilités, en liant toujours le symptôme à une cause psychomotrice (tonus, schéma corporel, anxiété). "
        "Exemple de style : 'Les points saillants qui ressortent de ce bilan sont les suivants : - Victoire fait preuve de stabilité... Cependant, elle régule difficilement son tonus musculaire... Cette tonicité peut être une manière de contrecarrer sa laxité, mais également un signe de sa tension interne.'"
    ),

    "projet_soin": (
        "Commence par valider l'indication ('Un soin psychomoteur semble bien indiqué...'). "
        "Liste les axes de travail sous forme de tirets ou titres, avec des objectifs commençant par des verbes à l'infinitif (Soutenir, Renforcer, Favoriser, Accompagner). "
        "Exemple de style : 'Régulation tonico-émotionnelle et sécurité corporelle : Favoriser l'apaisement du système nerveux... Travailler l'intégration des réflexes archaïques...'"
    ),

    "orientations": (
        "Si pertinent, rédige un court paragraphe justifiant une orientation vers un autre spécialiste (ostéopathe, orthoptiste, psychologue) en se basant sur une observation clinique précise. "
        "Exemple de style : 'Au vu des difficultés de mobilité... j'émets une orientation vers un ostéopathe en raison d'éléments évocateurs de difficultés oculomotrices.'"
    )
}

def rediger_section(cle_champ: str, valeur_champ, contexte_patient: str) -> str:
    """
    Rédige un paragraphe pour un champ donné.
    """
    # Si les données sont vides ou "RAS", on retourne une chaine vide ou courte
    if valeur_champ is None or valeur_champ == "" or valeur_champ == "RAS":
        return ""

    prompt_systeme = f"""
    Tu es une psychomotricienne experte, et tu es en train de rédiger un bilan suite à une première consultation. Tu vas rédiger le champ '{cle_champ}' du bilan à partir de tes notes.
    
    CONTEXTE PATIENT : {contexte_patient}
    
    STYLE ATTENDU :
    {PROMPTS_STYLE.get(cle_champ, "Style professionnel, neutre et bienveillant.")}
    
    CONSIGNES :
    - Sois neutre et bienveillante.
    - Ne jamais inventer d'informations. Sois factuelle et précise, sans extrapoler. Si une information n'est pas mentionnée, ne la suppose pas.
    - Transforme les notes en phrases fluides.
    - Utilise des tournures directes ("Diego présente..."), sans faire de phrases impersonnelles ("On note que Diego présente...").
    """
    
    response = _get_client().chat.completions.create(
        model="gpt-5.2", 
        messages=[
            {"role": "system", "content": prompt_systeme},
            {"role": "user", "content": f"Données à rédiger : {json.dumps(valeur_champ, ensure_ascii=False)}"}
        ]
    )
    return response.choices[0].message.content

def orchestrer_redaction(bilan_data: BilanPsychomoteur):
    """
    Parcourt l'objet Bilan et génère le texte pour chaque champ.
    """
    # 1. Créer le contexte global pour l'IA (pour qu'elle sache de qui on parle)
    contexte = f"Enfant : {bilan_data.identite_patient.prenom}, Motif de consultation : {bilan_data.identite_patient.motif_consultation}"
    
    resultats_rediges = {}
    
    # 2. Convertir l'objet Pydantic en dict pour itérer facilement
    data_dict = bilan_data.model_dump()
    
    # 3. Boucle sur toutes les sections et tous les champs (aligné avec models.py)
    sections_a_traiter = {
        "anamnese": [
            "environnement_familial",
            "grossesse_naissance",
            "sante_generale",
            "alimentation",
            "sommeil",
            "developpement_psychomoteur",
            "proprete",
            "language",
            "scolarite_vie_sociale",
            "autonomie_quotidien",
            "activites_extrascolaires",
        ],
        "observations_transversales": [
            "observations_transversales",
        ],
        "regulation_tonique": [
            "tonus_fond",
            "tonus_soutien",
            "tonus_action",
        ],
        "schema_corporel": [
            "connaissance_parties_corps",
            "dessin_bonhomme",
            "construction_puzzle",
            "imitation_gestes",
            "gnosies_tactiles",
        ],
        "modulation_sensorielle": [
            "reactivite_sensorielle",
        ],
        "motricite_globale": [
            "organisation_posturale",
            "coordination_dynamique",
            "equilibre",
            "coordinations_visuo_motrices",
            "dissociations",
        ],
        "motricite_fine": [
            "dexterite_manuelle",
            "coordinations_oculo_manuelles",
            "graphisme_ecriture",
            "praxies_habillage",
            "praxies_faciales",
        ],
        "lateralite": [
            "dominance",
        ],
        "organisation_spatiale": [
            "organisation_spatiale",
        ],
        "organisation_temporelle": [
            "organisation_temporelle",
        ],
        "emotion_jeu": [
            "regulation_emotionnelle",
            "jeu",
        ],
        "conclusion": [
            "synthese_clinique",
            "projet_soin",
            "orientations",
        ],
    }
    
    print("✍️  Début de la rédaction...")
    
    for section, champs in sections_a_traiter.items():
        if section in data_dict:
            print(f"   -> Rédaction de : {section}...")
            resultats_rediges[section] = {}
            for champ in champs:
                valeur = data_dict.get(section, {}).get(champ)
                texte = rediger_section(champ, valeur, contexte)
                resultats_rediges[section][champ] = texte
            
    return resultats_rediges

