from pydantic import BaseModel, Field
from typing import Optional, List

# --- 1. IDENTITÉ (pour le contexte, pour l'IA rédactionnelle) ---
class Identite(BaseModel):
    prenom: str = Field(..., description="Prénom de l'enfant")
    date_naissance: str = Field(..., description="Format JJ/MM/AAAA")
    date_bilan: str = Field(..., description="Mois et Année du bilan")
    classe_ecole: str = Field(..., description="Niveau scolaire et nom de l'école")
    motif_consultation: str = Field(..., description="Raison de la consultation")
    
# --- 2. ANAMNÈSE ---
class Anamnese(BaseModel):
    environnement_familial: str = Field(..., description="Composition, fratrie, climat familial.")
    grossesse_naissance: str = Field(..., description="Déroulement, terme, accouchement, premiers jours.")
    sante_generale: str = Field(..., description="Antécédents médicaux (ORL, digestif, vision), interventions.")
    alimentation: str = Field(..., description="Allaitement, diversification, sélectivité, troubles de l'oralité.")
    sommeil: str = Field(..., description="Endormissement, réveils nocturnes, co-dodo, cauchemars.")
    developpement_psychomoteur: str = Field(..., description="Étapes clés (assis, 4 pattes, marche), qualité du mouvement (prudence/audace).")
    proprete: Optional[str] = Field(None, description="Acquisition de la maîtrise sphinctérienne, énurésie/encoprésie.")
    language: Optional[str] = Field(None, description="Langues parlées, si autre que français.")
    scolarite_vie_sociale: str = Field(..., description="Parcours scolaire, comportement en classe, relations avec les pairs.")
    autonomie_quotidien: str = Field(..., description="Habillage, repas, autonomie dans les tâches quotidiennes.")
    activites_extrascolaires: Optional[str] = Field(None, description="Sports et loisirs pratiqués.")

# --- 3. OBSERVATIONS TRANSVERSALES ---
class ObservationsTransversales(BaseModel):
    observations_transversales: str = Field(..., description="Qualité du contact, regard, entrée en relation. Attention, compréhension des consignes, coopération, fatigue, agitation. Confiance en soi, besoin de réassurance, réaction à la difficulté.")

# --- 4. EXAMEN PSYCHOMOTEUR ---

# 4.A Régulation Tonique et Posturale
class RegulationTonique(BaseModel):
    tonus_fond: str = Field(..., description="État de tension au repos, extensibilité, ballant, passivité.")
    tonus_soutien: Optional[str] = Field(None, description="Maintien de l'axe, résistance aux poussées, qualité de l'assise.")
    tonus_action: Optional[str] = Field(None, description="Parasitage tonique, syncinésies, épreuve des marionnettes (diadococinésies).")

# 4.B Intégration du Schéma Corporel
class SchemaCorporel(BaseModel):
    connaissance_parties_corps: str = Field(..., description="Vocabulaire corporel, désignation.")
    dessin_bonhomme: Optional[str] = Field(None, description="Dessin du bonhomme (si mentionné ici).")
    construction_puzzle: Optional[str] = Field(None, description="Puzzle de Bergès : orientation, placement.")
    imitation_gestes: str = Field(..., description="Imitation de gestes simples (bras) et complexes (mains/doigts), imitation de postures.")
    gnosies_tactiles: Optional[str] = Field(None, description="Localisation tactile, discrimination des doigts (souvent testé ici).")

# 4.C Modulation Sensorielle (Partie extraite comme demandé)
class ModulationSensorielle(BaseModel):
    reactivite_sensorielle: str = Field(..., description="Traitement de l'information (visuelle, tactile, auditive), hypersensibilité ou recherche de sensation.")

# 4.D Compétences Posturo-Motrices - Coordinations Globales
class MotriciteGlobale(BaseModel):
    organisation_posturale: str = Field(..., description="Qualité posturale, réflexes primordiaux (Moro, etc.), schèmes de redressement.")
    coordination_dynamique: str = Field(..., description="Marche (avant/arrière/pointes/talons), course, sauts.")
    equilibre: str = Field(..., description="Équilibre statique (yeux ouverts/fermés), unipodal, sur pointes.")
    coordinations_visuo_motrices: str = Field(..., description="Balle/Ballon/Sac lesté : lancer, rattraper, viser, rebond.")
    dissociations: str = Field(..., description="Indépendance des ceintures, coordination haut/bas, séquences motrices.")

# 4.E Habiletés Oculo-Manuelles - Motricité Fine
class MotriciteFine(BaseModel):
    dexterite_manuelle: str = Field(..., description="Pinces digitales, déliement, fluidité, diadococinésies (si non traité dans tonus).")
    coordinations_oculo_manuelles: str = Field(..., description="Perles, cubes, encastrements, visuo-construction (puzzles).")
    graphisme_ecriture: str = Field(..., description="Tenue du crayon, posture, fluidité, pression, reproduction de formes, découpage.")
    praxies_habillage: Optional[str] = Field(None, description="Boutonnage, fermetures, orientation des vêtements.")
    praxies_faciales: Optional[str] = Field(None, description="Souffler, gonfler les joues, mobilité de la langue.")

# 4.F Latéralité
class Lateralite(BaseModel):
    dominance: str = Field(..., description="Latéralité manuelle, pédestre et oculaire. Homogénéité ou croisement.")

# 4.G Organisation Spatiale (Partie distinguée comme demandé)
class OrganisationSpatiale(BaseModel):
    organisation_spatiale: str = Field(..., description="Connaissance des notions spatiales, vocabulaire. Orientation sur soi, sur autrui, croisement de la ligne médiane. Ajustement aux distances, organisation dans l'espace graphique ou moteur.")

# 4.H Organisation Temporelle (Partie distinguée comme demandé)
class OrganisationTemporelle(BaseModel):
    organisation_temporelle: str = Field(..., description="Reproduction de structures rythmiques (mains/pieds), synchronisation au métronome. Connaissance des jours, mois, notions de durée/vitesse.")

# 4.I Compétences Émotionnelles et Jeu
class EmotionJeu(BaseModel):
    regulation_emotionnelle: str = Field(..., description="Gestion des émotions (colère, peur), tolérance à la frustration.")
    jeu: str = Field(..., description="Capacité à jouer seul, jeu symbolique, imagination, créativité.")

# --- 5. SYNTHÈSE ET PROJET ---
class SyntheseProjet(BaseModel):
    synthese_clinique: str = Field(..., description="Résumé des compétences et difficultés, mise en lien des symptômes (hypothèses de compréhension).")
    projet_soin: List[str] = Field(..., description="Liste des objectifs thérapeutiques prioritaires et axes de travail.")
    orientations: Optional[str] = Field(None, description="Réorientation vers d'autres spécialistes si nécessaire (ostéo, ophtalmo, etc.).")

# --- MODÈLE RACINE ---
class BilanPsychomoteur(BaseModel):
    identite_patient: Identite

    anamnese: Anamnese
    observations_transversales: ObservationsTransversales

    # Examen Clinique Détaillé
    regulation_tonique: RegulationTonique
    schema_corporel: SchemaCorporel
    modulation_sensorielle: ModulationSensorielle
    motricite_globale: MotriciteGlobale
    motricite_fine: MotriciteFine
    lateralite: Lateralite
    organisation_spatiale: OrganisationSpatiale
    organisation_temporelle: OrganisationTemporelle
    emotion_jeu: EmotionJeu

    conclusion: SyntheseProjet

