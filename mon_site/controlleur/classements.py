# Auteurs : GERGES Robin, RAONIMANANA Aaron

from model.model_pg import get_classement_ijh, get_classement_cpp


# Initialisation du joueur en session s'il est absent
if 'joueur' not in SESSION:
    SESSION['joueur'] = None

# Valeurs par défaut pour les classements
REQUEST_VARS['delta'] = 0
REQUEST_VARS['classement_ijh'] = []
REQUEST_VARS['classement_cpp'] = []

connexion = SESSION.get('CONNEXION')
if connexion is not None:
    donnees_post = POST if 'POST' in globals() else {}
    donnees_get = GET if 'GET' in globals() else {}

    def _first(mapping, key):
        """Retourne la première valeur d'une clé dans un dictionnaire (gère les listes)."""
        if mapping is None or key not in mapping:
            return None
        val = mapping.get(key)
        if isinstance(val, list):
            return val[0] if val else None
        return val

    # Récupération du paramètre delta (nombre de mois pour le filtre de classement)
    raw_delta = _first(donnees_post, 'delta') or _first(donnees_get, 'delta')
    try:
        delta = int(raw_delta) if raw_delta is not None else 0
        if delta < 0:
            delta = 0
    except (TypeError, ValueError):
        delta = 0

    # Chargement des classements filtrés selon le delta
    REQUEST_VARS['delta'] = delta
    REQUEST_VARS['classement_ijh'] = get_classement_ijh(connexion, delta) or []
    REQUEST_VARS['classement_cpp'] = get_classement_cpp(connexion, delta) or []
