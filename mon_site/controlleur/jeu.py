# Auteurs : GERGES Robin, RAONIMANANA Aaron

from model import model_pg
import random

# Raccourcis vers les fonctions utilitaires du modèle
execute_select_query = model_pg.execute_select_query
piocher_carte = model_pg.piocher_carte
set_partie_etat = model_pg.set_partie_etat

# Importation des primitives métier depuis le modèle
build_flottille = model_pg.build_flottille
init_state = model_pg.init_state
parse_coord = model_pg.parse_coord
coord_label = model_pg.coord_label
normalize_card_code = model_pg.normalize_card_code
impact_cells = model_pg.impact_cells
apply_tir_on_enemy = model_pg.apply_tir_on_enemy
apply_tir_on_player = model_pg.apply_tir_on_player
count_flotte = model_pg.count_flotte
place_ships_random = model_pg.place_ships_random
place_player_ship = model_pg.place_player_ship
sync_placement_state = model_pg.sync_placement_state
replace_touched_ship = model_pg.replace_touched_ship
replace_touched_ship_to = model_pg.replace_touched_ship_to
place_leurre = model_pg.place_leurre
place_leurre_at = model_pg.place_leurre_at
place_willy = model_pg.place_willy
place_willy_at = model_pg.place_willy_at
sink_three_smallest_enemy_ships = model_pg.sink_three_smallest_enemy_ships
adversaire_tir = model_pg.adversaire_tir
build_cell_images_map = model_pg.build_cell_images_map
COLS = model_pg.COLS
ROWS = model_pg.ROWS


# Fonctions de repli utilisées si les primitives correspondantes sont absentes du modèle
def _fallback_get_ids_joueurs_partie(_connexion, _code_partie):
    return None, None


def _fallback_inserer_tir(_connexion, _code_partie, _num_t, _id_j, _id_c, _coord_x, _coord_y):
    return None


def _fallback_upsert_tour(_connexion, _code_partie, _num_t, _nb_coules_j1, _nb_touches_j1, _nb_coules_j2, _nb_touches_j2):
    return None


def _fallback_save_partie_snapshot(_connexion, _code_partie, _state):
    return None


def _fallback_load_partie_snapshot(_connexion, _code_partie):
    return None


# Utilisation des vraies primitives si disponibles, sinon repli sur les fonctions ci-dessus
get_ids_joueurs_partie = getattr(model_pg, 'get_ids_joueurs_partie', _fallback_get_ids_joueurs_partie)
inserer_tir = getattr(model_pg, 'inserer_tir', _fallback_inserer_tir)
upsert_tour = getattr(model_pg, 'upsert_tour', _fallback_upsert_tour)
save_partie_snapshot = getattr(model_pg, 'save_partie_snapshot', _fallback_save_partie_snapshot)
load_partie_snapshot = getattr(model_pg, 'load_partie_snapshot', _fallback_load_partie_snapshot)


def _first(mapping, key):
    """Retourne la première valeur d'une clé dans un dictionnaire (gère les listes)."""
    if not mapping or key not in mapping:
        return None
    val = mapping.get(key)
    if isinstance(val, list):
        return val[0] if val else None
    return val




# Le contrôleur est exécuté via exec() dans server.py.
# On publie les symboles locaux dans globals() pour fiabiliser
# la résolution des noms dans les fonctions auxiliaires.
globals().update(locals())


# Initialisation du joueur en session s'il est absent
if 'joueur' not in SESSION:
    SESSION['joueur'] = None

# Récupération de la connexion et des données GET/POST
conn = SESSION.get('CONNEXION')
get_data = GET if 'GET' in globals() else {}
post_data = POST if 'POST' in globals() else {}

# Récupération du code de partie depuis les paramètres d'URL
raw_code = _first(get_data, 'code_partie') or _first(get_data, 'id')
if raw_code:
    try:
        SESSION['partie_en_cours'] = int(raw_code)
    except (TypeError, ValueError):
        SESSION['partie_en_cours'] = raw_code

# Chargement de l'état de jeu en mémoire pour la partie en cours
code_partie_actuel = SESSION.get('partie_en_cours')
game_states = SESSION.setdefault('game_states', {})
state_key = str(code_partie_actuel) if code_partie_actuel is not None else None
state = game_states.get(state_key) if state_key else None

# Accès interdit sans partie sélectionnée
if not SESSION.get('joueur'):
    REQUEST_VARS['redirect'] = '/connexion'
elif not code_partie_actuel:
    REQUEST_VARS['redirect'] = '/parties'

pseudo_adversaire_db = None
niveau_adversaire_db = None

if SESSION.get('joueur') and conn and code_partie_actuel:
    # Chargement du snapshot ou initialisation d'un nouvel état
    if state is None:
        loaded_state = load_partie_snapshot(conn, code_partie_actuel)
        state = loaded_state if loaded_state else init_state()
        game_states[state_key] = state
    # Correction automatique d'un état incomplet (partie commencée sans navires)
    if state.get('partie_commencee'):
        if not state.get('ships_joueur'):
            state['grille_navires'] = [[0] * 10 for _ in range(10)]
            state['ships_joueur'] = place_ships_random(state['grille_navires'])
        if not state.get('ships_ennemi'):
            state['grille_navires_ennemi'] = [[0] * 10 for _ in range(10)]
            state['ships_ennemi'] = place_ships_random(state['grille_navires_ennemi'])
    # Initialisation des champs manquants pour la compatibilité avec d'anciens états
    if 'phase' not in state:
        state['phase'] = 'DRAW'
    if 'historique' not in state:
        state['historique'] = []
    if 'message' not in state:
        state['message'] = ''
    if 'tour_number' not in state:
        state['tour_number'] = 1
    if 'partie_commencee' not in state:
        state['partie_commencee'] = False
    if 'flottille' not in state:
        state['flottille'] = build_flottille()
    if 'placement_index' not in state:
        state['placement_index'] = 0
    if 'grille_navires_labels' not in state:
        state['grille_navires_labels'] = [[''] * 10 for _ in range(10)]
    if 'extra_shot_pending' not in state:
        state['extra_shot_pending'] = False
    if 'leurre_cells' not in state:
        state['leurre_cells'] = []
    if 'leurre_hits' not in state:
        state['leurre_hits'] = []
    if 'willy_cell' not in state:
        state['willy_cell'] = None
    if 'c_vide_preview_done' not in state:
        state['c_vide_preview_done'] = False

    # Synchronisation de l'état de placement uniquement en phase PLACE
    # pour éviter les navires fantômes issus d'anciens snapshots
    if state.get('phase') == 'PLACE':
        sync_placement_state(state)

    # Récupération du pseudo adversaire (nécessaire aussi pour la détection de fin de partie)
    pseudo_adversaire_db = None
    niveau_adversaire_db = None
    try:
        q_adv = """
            SELECT j.pseudo, v.niveau_expertise
            FROM joue_virt jv
            JOIN virtuel v ON v.id_j = jv.id_virtuel
            JOIN joueur j ON j.id_j = jv.id_virtuel
            WHERE jv.code_partie = %s
        """
        adv_rows = execute_select_query(conn, q_adv, [code_partie_actuel])
        if adv_rows:
            pseudo_adversaire_db = adv_rows[0]['pseudo']
            niv = adv_rows[0]['niveau_expertise']
            niveau_adversaire_db = {1: 'Faible', 2: 'Moyen', 3: 'Expert'}.get(niv, str(niv))
    except Exception:
        pass

    action = _first(post_data, 'action')
    if action in ('commencer', 'placer_navire', 'piocher', 'tirer', 'suivant', 'suspendre'):
        id_humain, id_virtuel = get_ids_joueurs_partie(conn, code_partie_actuel)
        if action == 'suspendre':
            # Sauvegarde des stats du tour courant avant suspension
            if state.get('ships_joueur') and state.get('ships_ennemi'):
                nb_coules_j1, nb_touches_j1 = count_flotte(state['ships_joueur'], state['grille_navires'])
                nb_coules_j2, nb_touches_j2 = count_flotte(state['ships_ennemi'], state['grille_navires_ennemi'])
                upsert_tour(conn, code_partie_actuel, state['tour_number'], nb_coules_j1, nb_touches_j1, nb_coules_j2, nb_touches_j2)
            set_partie_etat(conn, code_partie_actuel, 'Suspendue')
            state['message'] = 'Partie suspendue.'
            REQUEST_VARS['redirect'] = '/parties'
        elif action == 'commencer':
            state['partie_commencee'] = True
            set_partie_etat(conn, code_partie_actuel, 'En cours')
            state['grille_tirs'] = [[0] * 10 for _ in range(10)]
            state['grille_navires'] = [[0] * 10 for _ in range(10)]
            state['grille_navires_labels'] = [[''] * 10 for _ in range(10)]
            state['grille_navires_ennemi'] = [[0] * 10 for _ in range(10)]
            state['ships_joueur'] = []
            state['ships_ennemi'] = place_ships_random(state['grille_navires_ennemi'])
            state['flottille'] = build_flottille()
            state['placement_index'] = 0
            state['carte_courante'] = None
            state['carte_piochee'] = False
            state['phase'] = 'PLACE'
            state['extra_shot_pending'] = False
            state['leurre_cells'] = []
            state['leurre_hits'] = []
            state['willy_cell'] = None
            state['c_vide_preview_done'] = False
            premier = state['flottille'][0]
            state['message'] = f"La partie commence ! Placez {premier['nom']} ({premier['taille']} cases)."
        elif action == 'placer_navire':
            placement_coord = _first(post_data, 'start_coordinates') or _first(post_data, 'placement_coordinates')
            placement_dir = _first(post_data, 'placement_direction') or 'H'
            ship_index_raw = _first(post_data, 'ship_index')
            if not state.get('partie_commencee'):
                state['message'] = "Commencez d'abord la partie."
            elif state.get('phase') != 'PLACE':
                state['message'] = "Le placement des navires est deja termine."
            else:
                parsed = parse_coord(placement_coord)
                if parsed is None:
                    state['message'] = "Coordonnee invalide pour placer le navire."
                else:
                    sx, sy = parsed
                    horizontal = str(placement_dir).upper() != 'V'
                    ship_index = None
                    try:
                        ship_index = int(ship_index_raw) if ship_index_raw is not None else None
                    except (TypeError, ValueError):
                        ship_index = None
                    ok, msg = place_player_ship(state, sx, sy, horizontal, ship_index=ship_index)
                    if not ok:
                        state['message'] = msg
        elif action == 'piocher':
            if not state.get('partie_commencee'):
                state['message'] = "Commencez d'abord la partie."
            elif state.get('phase') == 'PLACE':
                state['message'] = "Placez d'abord tous vos navires."
            elif state.get('phase') != 'DRAW':
                state['message'] = "Vous avez deja pioche une carte ce tour. Effectuez votre tir."
            else:
                carte = piocher_carte(conn, code_partie_actuel)
                state['carte_courante'] = carte
                state['carte_piochee'] = True
                state['phase'] = 'FIRE'
                state['c_vide_preview_done'] = False
                if carte:
                    state['message'] = f"Tour {state['tour_number']} — Carte piochee : {carte['nom']}. Choisissez une coordonnee et tirez !"
                else:
                    state['message'] = "Aucune carte disponible dans la pioche."
        elif action == 'tirer':
            coord = _first(post_data, 'coordinates')
            placement_coord = _first(post_data, 'placement_coordinates')
            placement_dir = _first(post_data, 'placement_direction') or 'H'
            tir_effectue = False
            if not state.get('partie_commencee'):
                state['message'] = "Commencez d'abord la partie."
            elif not state.get('ships_joueur'):
                state['message'] = "Erreur d'etat: relancez la partie avec Commencer."
            elif state.get('phase') != 'FIRE':
                state['message'] = "Piochez d'abord une carte avant de tirer."
            elif not state.get('carte_piochee'):
                state['message'] = "Pioche d'abord une carte avant de tirer."
            else:
                carte = state.get('carte_courante')
                code_carte = normalize_card_code(carte)
                if code_carte in ('C_PASSE', 'C_OUPS'):
                    if code_carte == 'C_PASSE':
                        state['message'] = f"Tour {state['tour_number']} — Carte Passe ton tour : vous perdez ce tour."
                    else:
                        candidates = [(cx, cy) for cy in range(10) for cx in range(10) if state['grille_navires'][cy][cx] == 4]
                        if not candidates:
                            candidates = [(cx, cy) for cy in range(10) for cx in range(10) if state['grille_navires'][cy][cx] == 0]
                        if candidates:
                            ox, oy = random.choice(candidates)
                            touche_oups, coule_oups = apply_tir_on_player(state, ox, oy)
                            state['message'] = f"Tour {state['tour_number']} — Mauvaise manip ! Impact sur {coord_label(ox, oy)}."
                        else:
                            touche_oups, coule_oups = False, False
                            state['message'] = f"Tour {state['tour_number']} — Mauvaise manip sans impact."
                    state['historique'].append({
                        'tour': state['tour_number'],
                        'joueur': 'humain',
                        'carte': carte['nom'] if carte else code_carte,
                        'coord': '-',
                        'impacts': [],
                    })
                    state['phase'] = 'ENEMY'
                    tir_effectue = True
                else:
                    parsed = parse_coord(coord)
                    if parsed is None:
                        state['message'] = "Coordonnées invalides (exemples: A1, J10)."
                    else:
                        x, y = parsed
                        effet_msg = None
                        if code_carte == 'C_VIDE':
                            if not state.get('c_vide_preview_done'):
                                preview = "occupee" if state['grille_navires_ennemi'][y][x] == 4 else "vide"
                                state['c_vide_preview_done'] = True
                                state['message'] = f"Sonde C_VIDE: {coord_label(x, y)} est {preview}. Vous pouvez changer la cible puis cliquer Tirer."
                                tir_effectue = False
                            else:
                                effet_msg = "C_VIDE active: tir confirme apres sonde"
                                state['c_vide_preview_done'] = False
                        elif code_carte == 'C_MPM':
                            parsed_place = parse_coord(placement_coord)
                            if parsed_place is None:
                                state['message'] = "C_MPM: choisissez la position de replacement sur votre grille."
                                tir_effectue = False
                            else:
                                px, py = parsed_place
                                horizontal = str(placement_dir).upper() != 'V'
                                moved = replace_touched_ship_to(state, px, py, horizontal)
                                effet_msg = "Même pas mal active: navire touche deplace et degat annule" if moved else "Même pas mal: placement invalide ou aucun navire touche"
                        elif code_carte == 'C_LEURRE':
                            parsed_place = parse_coord(placement_coord)
                            if parsed_place is None:
                                state['message'] = "C_LEURRE: choisissez une case de depart sur votre grille."
                                tir_effectue = False
                            else:
                                px, py = parsed_place
                                horizontal = str(placement_dir).upper() != 'V'
                                placed = place_leurre_at(state, px, py, horizontal)
                                effet_msg = "Bateau leurre place sur votre grille" if placed else "Bateau leurre: placement impossible"
                        elif code_carte == 'C_WILLY':
                            parsed_place = parse_coord(placement_coord)
                            if parsed_place is None:
                                state['message'] = "C_WILLY: choisissez une case libre sur votre grille."
                                tir_effectue = False
                            else:
                                px, py = parsed_place
                                placed = place_willy_at(state, px, py)
                                effet_msg = "Sauvez Willy: orque placee sur votre grille" if placed else "Sauvez Willy: placement impossible"

                        if code_carte != 'C_VIDE' or state.get('c_vide_preview_done') is False:
                            impacts = impact_cells(x, y, code_carte if code_carte in ('C_MEGA', 'C_ETOILE') else 'C_MISSILE')
                            touches, coules = apply_tir_on_enemy(state, impacts)
                            if id_humain and carte and carte.get('id_c') is not None:
                                inserer_tir(conn, code_partie_actuel, state['tour_number'], id_humain, carte['id_c'], x, y)
                            state['historique'].append({
                                'tour': state['tour_number'],
                                'joueur': 'humain',
                                'carte': carte['nom'] if carte else code_carte,
                                'coord': coord_label(x, y),
                                'impacts': [coord_label(ix, iy) for ix, iy in impacts],
                            })
                            tir_effectue = True
                            if code_carte == 'C_REJOUE' and not state.get('extra_shot_pending'):
                                state['extra_shot_pending'] = True
                                state['message'] = f"Tour {state['tour_number']} — Carte Rejoue: tirez une 2e fois avec missile simple."
                            elif state.get('extra_shot_pending'):
                                state['extra_shot_pending'] = False
                                state['phase'] = 'ENEMY'
                                if coules:
                                    state['message'] = f"Tour {state['tour_number']} — 2e tir en {coord_label(x, y)} : {touches} touche(s), {coules} coule(s)."
                                elif touches:
                                    state['message'] = f"Tour {state['tour_number']} — 2e tir touche en {coord_label(x, y)}."
                                else:
                                    state['message'] = f"Tour {state['tour_number']} — 2e tir a l'eau en {coord_label(x, y)}."
                            else:
                                if coules:
                                    state['message'] = f"Tour {state['tour_number']} — Tir en {coord_label(x, y)} : {touches} touche(s), {coules} navire(s) coule(s)."
                                elif touches:
                                    state['message'] = f"Tour {state['tour_number']} — Touche en {coord_label(x, y)} !"
                                else:
                                    state['message'] = f"Tour {state['tour_number']} — A l'eau en {coord_label(x, y)}."
                                if effet_msg:
                                    state['message'] = f"{state['message']} ({effet_msg})"
                                state['phase'] = 'ENEMY'

                if tir_effectue:
                    # Mise à jour des statistiques du tour courant
                    nb_coules_j1, nb_touches_j1 = count_flotte(state['ships_joueur'], state['grille_navires'])
                    nb_coules_j2, nb_touches_j2 = count_flotte(state['ships_ennemi'], state['grille_navires_ennemi'])
                    upsert_tour(conn, code_partie_actuel, state['tour_number'], nb_coules_j1, nb_touches_j1, nb_coules_j2, nb_touches_j2)
                    # Vérification fin de partie : le joueur a coulé tous les navires ennemis
                    if nb_coules_j2 >= len(state['ships_ennemi']):
                        set_partie_etat(conn, code_partie_actuel, 'Terminée')
                        pseudo_joueur = SESSION.get('joueur', {}).get('pseudo', 'Joueur')
                        state['gagnant'] = pseudo_joueur
                        state['phase'] = 'FINI'
                        state['message'] = f"Victoire ! Vous avez coulé tous les navires ennemis."
                        model_pg.execute_other_query(conn,
                            "UPDATE joue_reel SET score_final = %s WHERE code_partie = %s AND id_humain = %s",
                            [nb_coules_j2, code_partie_actuel, id_humain])
                        conn.commit()
        elif action == 'suivant':
            if not state.get('partie_commencee'):
                state['message'] = "Commencez d'abord la partie."
            elif not state.get('ships_joueur'):
                state['message'] = "Erreur d'etat: relancez la partie avec Commencer."
            elif state.get('phase') != 'ENEMY':
                state['message'] = "Vous devez d'abord jouer votre tir avant le tour adverse."
            else:
                carte_adv = piocher_carte(conn, code_partie_actuel)
                state['carte_adv'] = carte_adv
                tir_adv = adversaire_tir(state)
                coord_adv = tir_adv['coord'] if tir_adv else None
                touche_adv = tir_adv['touche'] if tir_adv else False
                coule_adv = tir_adv['coule'] if tir_adv else False
                impacts_adv = tir_adv['impacts'] if tir_adv else []

                for ix, iy in impacts_adv:
                    if state.get('leurre_cells') and (ix, iy) in state['leurre_cells']:
                        state['leurre_hits'].append((ix, iy))
                        for lx, ly in state['leurre_cells']:
                            if state['grille_navires'][ly][lx] == 5:
                                state['grille_navires'][ly][lx] = 0
                        state['leurre_cells'] = []
                        state['message'] = "Leurre touche par l'adversaire: faux impact declenche."
                    if state.get('willy_cell') == (ix, iy):
                        sunk = sink_three_smallest_enemy_ships(state)
                        if state['grille_navires'][iy][ix] == 6:
                            state['grille_navires'][iy][ix] = 0
                        state['willy_cell'] = None
                        state['message'] = f"Sauvez Willy active: {sunk} navire(s) ennemi(s) coules."

                if id_virtuel and carte_adv and carte_adv.get('id_c') is not None and coord_adv:
                    xy = parse_coord(coord_adv)
                    if xy:
                        inserer_tir(conn, code_partie_actuel, state['tour_number'], id_virtuel, carte_adv['id_c'], xy[0], xy[1])
                state['historique'].append({
                    'tour': state['tour_number'],
                    'joueur': 'virtuel',
                    'carte': carte_adv['nom'] if carte_adv else '-',
                    'coord': coord_adv or '-',
                    'impacts': [coord_label(ix, iy) for ix, iy in impacts_adv] if impacts_adv else [],
                })
                nb_coules_j1, nb_touches_j1 = count_flotte(state['ships_joueur'], state['grille_navires'])
                nb_coules_j2, nb_touches_j2 = count_flotte(state['ships_ennemi'], state['grille_navires_ennemi'])
                upsert_tour(conn, code_partie_actuel, state['tour_number'], nb_coules_j1, nb_touches_j1, nb_coules_j2, nb_touches_j2)
                if coule_adv:
                    resultat_tir = "coule un de vos navires"
                elif touche_adv:
                    resultat_tir = "touche un de vos navires"
                else:
                    resultat_tir = "rate son tir"
                # Vérification fin de partie : l'adversaire a coulé tous les navires du joueur
                if nb_coules_j1 >= len(state['ships_joueur']):
                    set_partie_etat(conn, code_partie_actuel, 'Terminée')
                    pseudo_adv = pseudo_adversaire_db or 'Adversaire'
                    state['gagnant'] = pseudo_adv
                    state['phase'] = 'FINI'
                    state['message'] = f"Défaite ! Tous vos navires ont été coulés. Gagnant : {pseudo_adv}."
                    model_pg.execute_other_query(conn,
                        "UPDATE joue_reel SET score_final = %s WHERE code_partie = %s AND id_humain = %s",
                        [0, code_partie_actuel, id_humain])
                    conn.commit()
                else:
                    if not state.get('message'):
                        state['message'] = f"Adversaire: {carte_adv['nom'] if carte_adv else '-'} en {coord_adv or '-'} ({resultat_tir}). A vous de piocher pour le tour suivant."
                    state['tour_number'] += 1
                    state['carte_courante'] = None
                    state['carte_piochee'] = False
                    state['extra_shot_pending'] = False
                    state['phase'] = 'DRAW'
                state.pop('carte_adv', None)

        game_states[state_key] = state
        SESSION['game_states'] = game_states
        save_partie_snapshot(conn, code_partie_actuel, state)

REQUEST_VARS['pseudo_adversaire'] = pseudo_adversaire_db
REQUEST_VARS['niveau_adversaire'] = niveau_adversaire_db

if not state:
    state = init_state()

carte_courante = state.get('carte_courante')
if carte_courante and carte_courante.get('image'):
    img = str(carte_courante['image']).strip()
    if img.startswith('images/'):
        carte_courante['image_path'] = img
    elif img.startswith('/'):
        carte_courante['image_path'] = img.lstrip('/')
    else:
        carte_courante['image_path'] = f"images/{img}"

REQUEST_VARS['grille_tirs'] = state['grille_tirs']
REQUEST_VARS['grille_navires'] = state['grille_navires']
REQUEST_VARS['grille_navires_labels'] = state.get('grille_navires_labels', [[''] * 10 for _ in range(10)])
REQUEST_VARS['tour_number'] = state['tour_number']
REQUEST_VARS['partie_commencee'] = state['partie_commencee']
REQUEST_VARS['carte_courante'] = carte_courante
REQUEST_VARS['carte_piochee'] = state.get('carte_piochee', False)
REQUEST_VARS['phase'] = state.get('phase', 'DRAW')
REQUEST_VARS['historique'] = state.get('historique', [])
REQUEST_VARS['message'] = state.get('message', '')
REQUEST_VARS['gagnant'] = state.get('gagnant', None)
REQUEST_VARS['cols'] = COLS
REQUEST_VARS['rows'] = ROWS
REQUEST_VARS['code_partie'] = code_partie_actuel
REQUEST_VARS['cell_images'] = build_cell_images_map()
REQUEST_VARS['flottille'] = state.get('flottille', [])
idx = state.get('placement_index', 0)
REQUEST_VARS['navire_a_placer'] = state['flottille'][idx] if idx < len(state.get('flottille', [])) else None
REQUEST_VARS['navires_non_places'] = [
    {"index": i, "nom": s["nom"], "taille": s["taille"], "pavillon": s["pavillon"], "label": s.get("label", "")}
    for i, s in enumerate(state.get('flottille', []))
    if not s.get("place")
]