RESTE A FAIRE :






faire en sorte que Maman remplisse ces infos :
class Identite(BaseModel):
    prenom: str = Field(..., description="Prénom de l'enfant")
    date_naissance: str = Field(..., description="Format JJ/MM/AAAA")
    date_bilan: str = Field(..., description="Mois et Année du bilan")
    classe_ecole: str = Field(..., description="Niveau scolaire et nom de l'école")
    motif_consultation: str = Field(..., description="Raison de la consultation")