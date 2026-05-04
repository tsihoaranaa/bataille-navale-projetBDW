# Auteurs : GERGES Robin, RAONIMANANA Aaron

# Contrôleur pour la page de connexion/création de compte.
# Le serveur exécute ce fichier avec exec() et fournit les variables
# globales : SESSION, GET, POST, REQUEST_VARS.

from model.model_pg import ajouter_un_joueur, get_joueur_par_pseudo


# Initialisation du joueur en session s'il est absent
if "joueur" not in SESSION:
    SESSION["joueur"] = None


conn = SESSION.get("CONNEXION")


def _get_first_value(mapping, key):
    """Retourne la première valeur d'une clé dans un dictionnaire (gère les listes)."""
    if mapping is None or key not in mapping:
        return None
    value = mapping[key]
    if isinstance(value, list):
        return value[0] if value else None
    return value



# Recherche d'un joueur par son pseudo (connexion)
if "pseudo_search" in GET:
    pseudo = _get_first_value(GET, "pseudo_search")
    if conn is not None and pseudo:
        joueurs = get_joueur_par_pseudo(conn, pseudo)
        REQUEST_VARS["resultat"] = joueurs[0] if joueurs else None
        if joueurs:
            SESSION["joueur"] = joueurs[0]
            REQUEST_VARS["redirect"] = "/accueil"
    else:
        REQUEST_VARS["resultat"] = None


# Création d'un nouveau compte joueur
if "pseudo_create" in POST:
    pseudo = _get_first_value(POST, "pseudo_create")
    nom = _get_first_value(POST, "nom_create")
    prenom = _get_first_value(POST, "prenom_create")
    date_naissance = _get_first_value(POST, "date_naissance_create")

    if conn is None:
        REQUEST_VARS["error"] = "Connexion à la BD indisponible."
    elif not (pseudo and nom and prenom and date_naissance):
        REQUEST_VARS["error"] = "Tous les champs sont requis."
    else:
        id_j = ajouter_un_joueur(conn, pseudo, nom, prenom, date_naissance)
        if id_j is None:
            REQUEST_VARS["error"] = "Pseudo déjà utilisé."
            REQUEST_VARS["resultat"] = get_joueur_par_pseudo(conn, pseudo)[0]
        else:
            joueurs = get_joueur_par_pseudo(conn, pseudo)
            SESSION["joueur"] = joueurs[0] if joueurs else {"pseudo": pseudo}
            REQUEST_VARS["redirect"] = "/accueil"
            REQUEST_VARS["created"] = True
            REQUEST_VARS["resultat"] = SESSION["joueur"]