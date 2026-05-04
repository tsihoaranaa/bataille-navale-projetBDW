# Auteurs : GERGES Robin, RAONIMANANA Aaron

from model.model_pg import (
    get_parties_en_cours,
    creer_partie,
    creer_pioche,
    execute_other_query,
    ajouter_un_joueur_virtuel,
    get_joueurs_virtuels_par_niveau,
    set_partie_etat,
)

# Initialisation du joueur en session s'il est absent
if 'joueur' not in SESSION:
    SESSION['joueur'] = None

# Valeurs par défaut
REQUEST_VARS['parties'] = []
REQUEST_VARS['joueurs_virtuels'] = []

if SESSION.get('joueur'):
    connexion = SESSION.get('CONNEXION')
    pseudo = SESSION['joueur'].get('pseudo')

    if connexion and pseudo:
        try:
            donnees_post = POST if 'POST' in globals() else {}
            donnees_get = GET if 'GET' in globals() else {}

            def _get_first_value(mapping, key):
                """Retourne la première valeur d'une clé dans un dictionnaire (gère les listes)."""
                if mapping is None or key not in mapping:
                    return None
                val = mapping.get(key)
                if isinstance(val, list):
                    return val[0] if val else None
                return val

            # Récupération de l'action demandée par le formulaire
            action = _get_first_value(donnees_post, 'action') or _get_first_value(donnees_get, 'action')

            if action == 'rejoindre':
                # Rejoint une partie existante et redirige vers l'interface de jeu
                id_partie = _get_first_value(donnees_get, 'id') or _get_first_value(donnees_post, 'id')
                if id_partie:
                    try:
                        set_partie_etat(connexion, int(id_partie), 'En cours')
                    except Exception:
                        pass
                    try:
                        SESSION['partie_en_cours'] = int(id_partie)
                    except (TypeError, ValueError):
                        SESSION['partie_en_cours'] = id_partie
                    REQUEST_VARS['redirect'] = '/jeu'

            elif action == 'suspendre':
                # Suspend une partie en cours
                id_partie = _get_first_value(donnees_get, 'id') or _get_first_value(donnees_post, 'id')
                if id_partie:
                    set_partie_etat(connexion, int(id_partie), 'Suspendue')
                REQUEST_VARS['redirect'] = '/parties'

            elif action == 'creer_partie':
                # Création d'une nouvelle partie et association à un adversaire virtuel
                code_partie = creer_partie(connexion, pseudo)
                if code_partie:
                    creer_pioche(connexion, code_partie)
                    id_adversaire = _get_first_value(donnees_post, 'adversaire')
                    if id_adversaire and str(id_adversaire).strip() != "":
                        requete_virt = "INSERT INTO joue_virt (code_partie, id_virtuel) VALUES (%s, %s)"
                        execute_other_query(connexion, requete_virt, [code_partie, int(id_adversaire)])
                    SESSION['partie_en_cours'] = code_partie
                    SESSION['grille_tirs'] = [[0] * 10 for _ in range(10)]
                    SESSION['grille_navires'] = [[0] * 10 for _ in range(10)]
                    SESSION['tour_number'] = 1
                    SESSION['partie_commencee'] = False
                    SESSION['carte_courante'] = None
                    REQUEST_VARS['redirect'] = f'/jeu?code_partie={code_partie}'
                else:
                    REQUEST_VARS['redirect'] = '/parties'

            elif action == 'creer_virtuel':
                # Création d'un nouveau joueur virtuel avec le niveau choisi
                pseudo_virtuel = _get_first_value(donnees_post, 'pseudo_virtuel')
                niveau = _get_first_value(donnees_post, 'niveau')
                if pseudo_virtuel and niveau:
                    ajouter_un_joueur_virtuel(connexion, pseudo_virtuel, int(niveau))
                REQUEST_VARS['redirect'] = '/parties'

            # Chargement des parties en cours pour le joueur connecté
            REQUEST_VARS['parties'] = get_parties_en_cours(connexion, pseudo)

            # Chargement de tous les joueurs virtuels (niveaux 1, 2, 3)
            tous_virtuels = []
            for n in [1, 2, 3]:
                resultats = get_joueurs_virtuels_par_niveau(connexion, n)
                if resultats:
                    tous_virtuels.extend(resultats)

            REQUEST_VARS['joueurs_virtuels'] = tous_virtuels

        except Exception as e:
            import traceback
            REQUEST_VARS['error_msg'] = f"Crash Python intercepté : {e} \n {traceback.format_exc()}"
