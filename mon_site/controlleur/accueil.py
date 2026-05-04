# Auteurs : GERGES Robin, RAONIMANANA Aaron

from model.model_pg import count_instances, get_parties_par_joueur, get_cartes

# Initialisation du joueur en session s'il est absent
if 'joueur' not in SESSION:
    SESSION['joueur'] = None


# Valeurs par défaut des statistiques affichées sur la page d'accueil
stats = {
    'total_joueurs': 'N/A',
    'total_parties': 'N/A',
    'parties_jouees': 'N/A',
}

conn = SESSION.get('CONNEXION')
if conn is not None:
    # Comptage du nombre total de joueurs et de parties en base
    joueurs = count_instances(conn, 'joueur')
    parties = count_instances(conn, 'partie')
    stats['total_joueurs'] = joueurs[0]['nb'] if joueurs else 0
    stats['total_parties'] = parties[0]['nb'] if parties else 0

    # Comptage des parties jouées par le joueur connecté
    if SESSION.get('joueur') and isinstance(SESSION['joueur'], dict) and 'id_j' in SESSION['joueur']:
        parties_joueur = get_parties_par_joueur(conn, SESSION['joueur']['id_j'])
        stats['parties_jouees'] = len(parties_joueur) if parties_joueur is not None else 0
    else:
        stats['parties_jouees'] = 0

    # Chargement des règles de cartes depuis la base de données
    cartes = get_cartes(conn)
    REQUEST_VARS['cartes'] = cartes if cartes is not None else []

REQUEST_VARS['stats'] = stats
