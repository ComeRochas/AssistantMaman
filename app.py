import streamlit as st
import io
import os
from dotenv import load_dotenv
from docxtpl import DocxTemplate
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

# Charger le .env le plus tôt possible (avant que les modules l'utilisent)
load_dotenv()

from architecte import transformer_notes_en_json
from redacteur import orchestrer_redaction
from models import BilanPsychomoteur

# ============================================================
# CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Assistant Bilan Psychomoteur",
    page_icon="🧠",
    layout="wide",
)

# ============================================================
# SIDEBAR — GESTION DE LA CLÉ API
# ============================================================
with st.sidebar:
    st.header("⚙️ Configuration")

    cle_env = os.environ.get("OPENAI_API_KEY", "").strip()

    if cle_env:
        st.success("✅ Clé API configurée")
        # Permet de la remplacer temporairement si besoin
        nouvelle_cle = st.text_input(
            "Remplacer la clé (optionnel)",
            type="password",
            placeholder="Laisser vide pour utiliser la clé du fichier .env",
        )
        if nouvelle_cle.strip():
            os.environ["OPENAI_API_KEY"] = nouvelle_cle.strip()
            st.info("Clé surchargée pour cette session.")
    else:
        st.error("❌ Clé API manquante")
        st.markdown(
            "Ajoutez `OPENAI_API_KEY=sk-...` dans le fichier `.env` "
            "ou saisissez-la ici :"
        )
        cle_manuelle = st.text_input("Clé OpenAI", type="password")
        if cle_manuelle.strip():
            os.environ["OPENAI_API_KEY"] = cle_manuelle.strip()
            st.success("Clé enregistrée pour cette session ✅")
        else:
            st.warning("L'application ne peut pas fonctionner sans clé API.")

    st.divider()
    st.caption(
        "🔒 La clé n'est jamais envoyée ailleurs que vers OpenAI.\n\n"
        "Pour la modifier de façon permanente, éditez le fichier `.env`."
    )

# ============================================================
# INITIALISATION DU SESSION_STATE
# ============================================================
defaults = {
    "etape": 1,
    "bilan_dict": None,
    "notes_brutes": "",
    "identite_form": {},
    "word_bytes": None,
    "nom_fichier": "Bilan_Genere.docx",
}
for cle, valeur in defaults.items():
    if cle not in st.session_state:
        st.session_state[cle] = valeur

# ============================================================
# EN-TÊTE
# ============================================================
st.title("🧠 Assistant Bilan Psychomoteur")
st.caption("Outil d'aide à la rédaction automatique – saisie des notes → bilan Word")

# Barre de progression
labels_etapes = ["1 · Saisie", "2 · Vérification", "3 · Téléchargement"]
cols_prog = st.columns(3)
for i, label in enumerate(labels_etapes):
    with cols_prog[i]:
        if st.session_state.etape == i + 1:
            st.markdown(f"**:blue[{label}]** ◀")
        elif st.session_state.etape > i + 1:
            st.markdown(f"~~{label}~~ ✅")
        else:
            st.markdown(f":gray[{label}]")

st.divider()


# ============================================================
# ÉTAPE 1 — SAISIE
# ============================================================
if st.session_state.etape == 1:

    st.header("Étape 1 — Informations & Notes brutes")

    col_id, col_notes = st.columns([1, 1], gap="large")

    with col_id:
        st.subheader("🪪 Identité du patient")
        prenom = st.text_input(
            "Prénom de l'enfant *",
            value=st.session_state.identite_form.get("prenom", ""),
        )
        date_naissance = st.text_input(
            "Date de naissance (JJ/MM/AAAA) *",
            value=st.session_state.identite_form.get("date_naissance", ""),
            placeholder="Ex : 14/03/2018",
        )
        date_bilan = st.text_input(
            "Date du bilan (Mois AAAA) *",
            value=st.session_state.identite_form.get("date_bilan", ""),
            placeholder="Ex : Février 2026",
        )
        classe_ecole = st.text_input(
            "Niveau scolaire / École *",
            value=st.session_state.identite_form.get("classe_ecole", ""),
            placeholder="Ex : CE2 – école primaire Jules Ferry",
        )
        motif_consultation = st.text_area(
            "Motif de la demande *",
            value=st.session_state.identite_form.get("motif_consultation", ""),
            height=120,
            placeholder="Ex : Adressé par la maîtresse pour difficultés graphiques et agitation...",
        )

    with col_notes:
        st.subheader("📝 Notes brutes d'observation")
        notes_brutes = st.text_area(
            "Collez ou saisissez vos notes de séance *",
            value=st.session_state.notes_brutes,
            height=400,
            placeholder=(
                "Les abréviations sont acceptées.\n\n"
                "Ex :\n"
                "- Mvt global OK, marche pointes pieds++\n"
                "- Moro imm., latéralité D main/pied/oeil\n"
                "- Dessin bonhomme : tête, corps, 4 membres, pas de détails\n"
                "- Sélectivité alimentaire (textures molles refusées)\n"
                "- Envt familial : vit avec père + mère + sœur 5 ans..."
            ),
        )

    st.divider()

    if st.button("🔍 Analyser et Structurer les notes", type="primary", use_container_width=True):
        # --- Validation des champs obligatoires ---
        manquants = []
        if not prenom.strip():             manquants.append("Prénom")
        if not date_naissance.strip():     manquants.append("Date de naissance")
        if not date_bilan.strip():         manquants.append("Date du bilan")
        if not classe_ecole.strip():       manquants.append("Niveau scolaire")
        if not motif_consultation.strip(): manquants.append("Motif de la consultation")
        if not notes_brutes.strip():       manquants.append("Notes brutes")

        if manquants:
            st.error(f"Veuillez renseigner les champs obligatoires : **{', '.join(manquants)}**")
        else:
            # Sauvegarde dans le session_state
            st.session_state.identite_form = {
                "prenom":             prenom.strip(),
                "date_naissance":     date_naissance.strip(),
                "date_bilan":         date_bilan.strip(),
                "classe_ecole":       classe_ecole.strip(),
                "motif_consultation": motif_consultation.strip(),
            }
            st.session_state.notes_brutes = notes_brutes

            with st.spinner("⏳ L'IA analyse et structure vos notes… (20 à 40 secondes)"):
                try:
                    bilan: BilanPsychomoteur = transformer_notes_en_json(notes_brutes)

                    # On injecte l'identité saisie dans le formulaire (ne pas laisser l'IA la deviner)
                    bilan_dict = bilan.model_dump()
                    bilan_dict["identite_patient"] = st.session_state.identite_form

                    st.session_state.bilan_dict = bilan_dict
                    st.session_state.etape = 2
                    st.rerun()

                except Exception as exc:
                    st.error(f"❌ Erreur lors de l'analyse IA : {exc}")


# ============================================================
# ÉTAPE 2 — VÉRIFICATION ET ÉDITION
# ============================================================
elif st.session_state.etape == 2:

    st.header("Étape 2 — Vérification & Édition")
    st.info(
        "💡 L'IA a structuré vos notes ci-dessous. "
        "Relisez et corrigez chaque section si nécessaire, puis validez pour lancer la rédaction."
    )

    bilan_dict: dict = st.session_state.bilan_dict

    # ----------------------------------------------------------
    # Utilitaire : text_area lié au session_state par une clé unique
    # ----------------------------------------------------------
    def champ_texte(section: str, champ: str, label: str,
                    obligatoire: bool = True, height: int = 90):
        """
        Affiche un st.text_area modifiable.
        La valeur initiale est lue depuis bilan_dict (si elle n'a pas déjà été modifiée par l'utilisateur).
        """
        key = f"edit_{section}_{champ}"
        if key not in st.session_state:
            st.session_state[key] = bilan_dict.get(section, {}).get(champ) or ""
        placeholder = "(Non évalué)" if obligatoire else "(Optionnel – laisser vide si non applicable)"
        st.text_area(label, key=key, height=height, placeholder=placeholder)

    # ----------------------------------------------------------
    # Identité (toujours développée — correction facile)
    # ----------------------------------------------------------
    with st.expander("🪪 Identité du patient", expanded=True):
        id_data = bilan_dict.get("identite_patient", {})
        c1, c2 = st.columns(2)
        with c1:
            for cle, label in [
                ("prenom",         "Prénom"),
                ("date_naissance", "Date de naissance"),
                ("date_bilan",     "Date du bilan"),
            ]:
                key = f"edit_identite_{cle}"
                if key not in st.session_state:
                    st.session_state[key] = id_data.get(cle, "")
                st.text_input(label, key=key)
        with c2:
            for cle, label in [
                ("classe_ecole", "Niveau scolaire / École"),
            ]:
                key = f"edit_identite_{cle}"
                if key not in st.session_state:
                    st.session_state[key] = id_data.get(cle, "")
                st.text_input(label, key=key)
            key_motif = "edit_identite_motif_consultation"
            if key_motif not in st.session_state:
                st.session_state[key_motif] = id_data.get("motif_consultation", "")
            st.text_area("Motif de la consultation", key=key_motif, height=100)

    # ----------------------------------------------------------
    # Anamnèse
    # ----------------------------------------------------------
    with st.expander("📋 Anamnèse"):
        champ_texte("anamnese", "environnement_familial",       "Environnement familial")
        champ_texte("anamnese", "grossesse_naissance",          "Grossesse & naissance")
        champ_texte("anamnese", "sante_generale",               "Santé générale")
        champ_texte("anamnese", "alimentation",                 "Alimentation")
        champ_texte("anamnese", "sommeil",                      "Sommeil")
        champ_texte("anamnese", "developpement_psychomoteur",   "Développement psychomoteur")
        champ_texte("anamnese", "proprete",                     "Propreté",                    obligatoire=False)
        champ_texte("anamnese", "language",                     "Langage / Bilinguisme",       obligatoire=False)
        champ_texte("anamnese", "scolarite_vie_sociale",        "Scolarité & vie sociale")
        champ_texte("anamnese", "autonomie_quotidien",          "Autonomie au quotidien")
        champ_texte("anamnese", "activites_extrascolaires",     "Activités extrascolaires",    obligatoire=False)

    # ----------------------------------------------------------
    # Observations transversales
    # ----------------------------------------------------------
    with st.expander("👁️ Observations transversales"):
        champ_texte(
            "observations_transversales",
            "observations_transversales",
            "Comportement, qualité du contact, attention, confiance en soi…",
            height=160,
        )

    # ----------------------------------------------------------
    # Examen clinique
    # ----------------------------------------------------------
    with st.expander("💪 Régulation tonique & posturale"):
        champ_texte("regulation_tonique", "tonus_fond",    "Tonus de fond")
        champ_texte("regulation_tonique", "tonus_soutien", "Tonus de soutien",  obligatoire=False)
        champ_texte("regulation_tonique", "tonus_action",  "Tonus d'action",    obligatoire=False)

    with st.expander("🧍 Schéma corporel"):
        champ_texte("schema_corporel", "connaissance_parties_corps", "Connaissance des parties du corps")
        champ_texte("schema_corporel", "dessin_bonhomme",            "Dessin du bonhomme",                obligatoire=False)
        champ_texte("schema_corporel", "construction_puzzle",        "Construction / Puzzle de Bergès",   obligatoire=False)
        champ_texte("schema_corporel", "imitation_gestes",           "Imitation de gestes")
        champ_texte("schema_corporel", "gnosies_tactiles",           "Gnosies tactiles",                  obligatoire=False)

    with st.expander("🎵 Modulation sensorielle"):
        champ_texte("modulation_sensorielle", "reactivite_sensorielle", "Réactivité sensorielle (visuelle, tactile, auditive)")

    with st.expander("🏃 Motricité globale"):
        champ_texte("motricite_globale", "organisation_posturale",       "Organisation posturale")
        champ_texte("motricite_globale", "coordination_dynamique",       "Coordination dynamique (marche, course, sauts)")
        champ_texte("motricite_globale", "equilibre",                    "Équilibre statique & dynamique")
        champ_texte("motricite_globale", "coordinations_visuo_motrices", "Coordinations visuo-motrices (balle, ballon…)")
        champ_texte("motricite_globale", "dissociations",                "Dissociations & séquences motrices")

    with st.expander("✏️ Motricité fine & oculo-manuelle"):
        champ_texte("motricite_fine", "dexterite_manuelle",           "Dextérité manuelle")
        champ_texte("motricite_fine", "coordinations_oculo_manuelles","Coordinations oculo-manuelles")
        champ_texte("motricite_fine", "graphisme_ecriture",           "Graphisme & écriture")
        champ_texte("motricite_fine", "praxies_habillage",            "Praxies d'habillage",  obligatoire=False)
        champ_texte("motricite_fine", "praxies_faciales",             "Praxies faciales",     obligatoire=False)

    with st.expander("↔️ Latéralité"):
        champ_texte("lateralite", "dominance", "Dominance (main, pied, œil) – homogénéité ou croisement")

    with st.expander("🗺️ Organisation spatiale"):
        champ_texte("organisation_spatiale", "organisation_spatiale", "Organisation spatiale")

    with st.expander("⏱️ Organisation temporelle"):
        champ_texte("organisation_temporelle", "organisation_temporelle", "Organisation temporelle (rythmes, notions temporelles)")

    with st.expander("🎭 Régulation émotionnelle & jeu"):
        champ_texte("emotion_jeu", "regulation_emotionnelle", "Régulation émotionnelle (colère, frustration…)")
        champ_texte("emotion_jeu", "jeu",                     "Jeu (symbolique, créativité, autonomie du jeu)")

    # ----------------------------------------------------------
    # Synthèse & Projet (toujours développée)
    # ----------------------------------------------------------
    with st.expander("📝 Synthèse & Projet de soin", expanded=True):
        champ_texte("conclusion", "synthese_clinique", "Synthèse clinique", height=160)

        # projet_soin est une List[str] → une ligne = un objectif
        key_projet = "edit_conclusion_projet_soin"
        if key_projet not in st.session_state:
            raw = bilan_dict.get("conclusion", {}).get("projet_soin") or []
            st.session_state[key_projet] = "\n".join(raw) if isinstance(raw, list) else str(raw)
        st.text_area(
            "Projet de soin – un objectif par ligne",
            key=key_projet,
            height=120,
            placeholder="Travailler la régulation tonique\nAméliorer la coordination visuo-motrice\n…",
        )

        champ_texte("conclusion", "orientations", "Orientations vers d'autres spécialistes", obligatoire=False)

    # ----------------------------------------------------------
    # Boutons de navigation
    # ----------------------------------------------------------
    st.divider()
    btn_retour, btn_valider = st.columns([1, 3], gap="medium")

    with btn_retour:
        if st.button("◀ Retour", use_container_width=True):
            st.session_state.etape = 1
            st.rerun()

    with btn_valider:
        if st.button("✅ Valider et Rédiger le Bilan", type="primary", use_container_width=True):

            def _lire(key: str, fallback: str = "Non évalué") -> str:
                """Lit une valeur de session_state et renvoie le fallback si vide."""
                v = st.session_state.get(key, "")
                return v.strip() if v and v.strip() else fallback

            def _opt(key: str):
                """Retourne None si la valeur est vide (champ optionnel)."""
                v = st.session_state.get(key, "")
                return v.strip() if v and v.strip() else None

            # Reconstruction du dictionnaire édité
            edited = {
                "identite_patient": {
                    "prenom":             _lire("edit_identite_prenom",             ""),
                    "date_naissance":     _lire("edit_identite_date_naissance",     ""),
                    "date_bilan":         _lire("edit_identite_date_bilan",         ""),
                    "classe_ecole":       _lire("edit_identite_classe_ecole",       ""),
                    "motif_consultation": _lire("edit_identite_motif_consultation", ""),
                },
                "anamnese": {
                    "environnement_familial":     _lire("edit_anamnese_environnement_familial"),
                    "grossesse_naissance":         _lire("edit_anamnese_grossesse_naissance"),
                    "sante_generale":              _lire("edit_anamnese_sante_generale"),
                    "alimentation":                _lire("edit_anamnese_alimentation"),
                    "sommeil":                     _lire("edit_anamnese_sommeil"),
                    "developpement_psychomoteur":  _lire("edit_anamnese_developpement_psychomoteur"),
                    "proprete":                    _opt("edit_anamnese_proprete"),
                    "language":                    _opt("edit_anamnese_language"),
                    "scolarite_vie_sociale":       _lire("edit_anamnese_scolarite_vie_sociale"),
                    "autonomie_quotidien":         _lire("edit_anamnese_autonomie_quotidien"),
                    "activites_extrascolaires":    _opt("edit_anamnese_activites_extrascolaires"),
                },
                "observations_transversales": {
                    "observations_transversales": _lire(
                        "edit_observations_transversales_observations_transversales"
                    ),
                },
                "regulation_tonique": {
                    "tonus_fond":    _lire("edit_regulation_tonique_tonus_fond"),
                    "tonus_soutien": _opt("edit_regulation_tonique_tonus_soutien"),
                    "tonus_action":  _opt("edit_regulation_tonique_tonus_action"),
                },
                "schema_corporel": {
                    "connaissance_parties_corps": _lire("edit_schema_corporel_connaissance_parties_corps"),
                    "dessin_bonhomme":            _opt("edit_schema_corporel_dessin_bonhomme"),
                    "construction_puzzle":        _opt("edit_schema_corporel_construction_puzzle"),
                    "imitation_gestes":           _lire("edit_schema_corporel_imitation_gestes"),
                    "gnosies_tactiles":           _opt("edit_schema_corporel_gnosies_tactiles"),
                },
                "modulation_sensorielle": {
                    "reactivite_sensorielle": _lire("edit_modulation_sensorielle_reactivite_sensorielle"),
                },
                "motricite_globale": {
                    "organisation_posturale":       _lire("edit_motricite_globale_organisation_posturale"),
                    "coordination_dynamique":       _lire("edit_motricite_globale_coordination_dynamique"),
                    "equilibre":                    _lire("edit_motricite_globale_equilibre"),
                    "coordinations_visuo_motrices": _lire("edit_motricite_globale_coordinations_visuo_motrices"),
                    "dissociations":                _lire("edit_motricite_globale_dissociations"),
                },
                "motricite_fine": {
                    "dexterite_manuelle":            _lire("edit_motricite_fine_dexterite_manuelle"),
                    "coordinations_oculo_manuelles": _lire("edit_motricite_fine_coordinations_oculo_manuelles"),
                    "graphisme_ecriture":            _lire("edit_motricite_fine_graphisme_ecriture"),
                    "praxies_habillage":             _opt("edit_motricite_fine_praxies_habillage"),
                    "praxies_faciales":              _opt("edit_motricite_fine_praxies_faciales"),
                },
                "lateralite": {
                    "dominance": _lire("edit_lateralite_dominance"),
                },
                "organisation_spatiale": {
                    "organisation_spatiale": _lire("edit_organisation_spatiale_organisation_spatiale"),
                },
                "organisation_temporelle": {
                    "organisation_temporelle": _lire("edit_organisation_temporelle_organisation_temporelle"),
                },
                "emotion_jeu": {
                    "regulation_emotionnelle": _lire("edit_emotion_jeu_regulation_emotionnelle"),
                    "jeu":                     _lire("edit_emotion_jeu_jeu"),
                },
                "conclusion": {
                    "synthese_clinique": _lire("edit_conclusion_synthese_clinique"),
                    "projet_soin": [
                        line.strip()
                        for line in st.session_state.get("edit_conclusion_projet_soin", "").split("\n")
                        if line.strip()
                    ] or ["À définir"],
                    "orientations": _opt("edit_conclusion_orientations"),
                },
            }

            with st.spinner("✍️ L'IA rédige les paragraphes cliniques… (1 à 2 minutes)"):
                try:
                    bilan_obj = BilanPsychomoteur(**edited)
                    context_redige = orchestrer_redaction(bilan_obj)

                    final_context = {
                        **context_redige,
                        "identite_patient": bilan_obj.identite_patient.model_dump(),
                    }

                    # Génération du document Word en mémoire
                    doc = DocxTemplate("templateWord.docx")
                    doc.render(final_context)

                    # Mise en forme : police Calibri + justification
                    try:
                        normal_style = doc.styles["Normal"]
                        normal_style.font.name = "Calibri"
                        normal_style._element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
                    except Exception:
                        pass  # Mise en forme non critique

                    for paragraph in doc.paragraphs:
                        paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

                    # Écriture dans un buffer mémoire (pas de fichier temporaire)
                    buffer = io.BytesIO()
                    doc.save(buffer)
                    buffer.seek(0)

                    prenom_clean = edited["identite_patient"]["prenom"].replace(" ", "_") or "Patient"
                    st.session_state.word_bytes = buffer.read()
                    st.session_state.nom_fichier = f"Bilan_{prenom_clean}.docx"
                    st.session_state.bilan_dict = edited  # mise à jour avec les données éditées
                    st.session_state.etape = 3
                    st.rerun()

                except Exception as exc:
                    st.error(f"❌ Erreur lors de la rédaction : {exc}")


# ============================================================
# ÉTAPE 3 — TÉLÉCHARGEMENT
# ============================================================
elif st.session_state.etape == 3:

    st.header("Étape 3 — Bilan généré avec succès ✅")
    st.balloons()

    prenom = (
        st.session_state.bilan_dict.get("identite_patient", {}).get("prenom", "")
        if st.session_state.bilan_dict
        else ""
    )
    nom_affiche = prenom if prenom else "le patient"

    st.success(f"Le bilan de **{nom_affiche}** a été rédigé ! Téléchargez le fichier Word ci-dessous.")

    col_dl, col_new = st.columns([3, 1], gap="medium")

    with col_dl:
        st.download_button(
            label="⬇️  Télécharger le bilan Word",
            data=st.session_state.word_bytes,
            file_name=st.session_state.nom_fichier,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True,
        )

    with col_new:
        if st.button("🔄  Nouveau bilan", use_container_width=True):
            # Nettoyage complet du session_state (clés d'édition + données)
            keys_to_delete = [k for k in list(st.session_state.keys()) if k.startswith("edit_")]
            for k in keys_to_delete:
                del st.session_state[k]
            st.session_state.etape = 1
            st.session_state.bilan_dict = None
            st.session_state.notes_brutes = ""
            st.session_state.identite_form = {}
            st.session_state.word_bytes = None
            st.session_state.nom_fichier = "Bilan_Genere.docx"
            st.rerun()

    st.divider()

    with st.expander("🔍 Voir les données structurées du bilan"):
        st.json(st.session_state.bilan_dict)
