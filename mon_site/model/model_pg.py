# Auteurs : GERGES Robin, RAONIMANANA Aaron

import random
import json
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from logzero import logger

class Grille:
    def __init__(self, largeur, hauteur):
        """
        Initialise une grille avec des cellules non explorées.
        """
        self.largeur = largeur
        self.hauteur = hauteur
        self.matrice = [[0 for _ in range(largeur)] for _ in range(hauteur)]

    def initialiser_grille(self):
        """
        Remplit la grille avec des cellules non explorées (code 0).
        """
        self.matrice = [[0 for _ in range(self.largeur)] for _ in range(self.hauteur)]

    def appliquer_tir(self, tirs):
        """
        Applique une liste de tirs sur la grille.
        """
        for x, y in tirs:
            if 0 <= x < self.largeur and 0 <= y < self.hauteur:
                self.matrice[y][x] = 1  # Exemple : 1 pour exploré

    def afficher(self):
        """
        Affiche la grille pour le débogage.
        """
        for ligne in self.matrice:
            print(" ".join(map(str, ligne)))

# Exemple de primitive pour transformer un tir en plusieurs tirs selon une carte
def transformer_tir(grille, x, y, code_carte):
    """
    Transforme un tir en une liste de tirs selon le code de carte.
    """
    tirs = []
    if code_carte == "C_MISSILE":
        tirs.append((x, y))
    elif code_carte == "C_MEGA":
        tirs.extend([
            (x, y), (x - 1, y - 1), (x, y - 1), (x + 1, y - 1),
            (x - 1, y), (x + 1, y), (x - 1, y + 1), (x, y + 1), (x + 1, y + 1)
        ])
    # Filtrage des tirs hors de la grille
    tirs = [(tx, ty) for tx, ty in tirs if 0 <= tx < grille.largeur and 0 <= ty < grille.hauteur]
    return tirs

# Exemple de primitive pour exécuter un tir
def executer_tir(grille, tirs):
    """
    Exécute un tir sur la grille et met à jour les cellules.
    """
    grille.appliquer_tir(tirs)

def execute_select_query(connexion, query, params=[]):
    """
    Méthode générique pour exécuter une requête SELECT (qui peut retourner plusieurs instances).
    Utilisée par des fonctions plus spécifiques.
    """
    with connexion.cursor(row_factory=dict_row) as cursor:
        try:
            cursor.execute(query, params)
            result = cursor.fetchall()
            return result 
        except psycopg.Error as e:
            logger.error(e)
    return None

def execute_other_query(connexion, query, params=[]):
    """
    Méthode générique pour exécuter une requête INSERT, UPDATE, DELETE.
    Utilisée par des fonctions plus spécifiques.
    """
    with connexion.cursor() as cursor:
        try:
            cursor.execute(query, params)
            result = cursor.rowcount
            return result 
        except psycopg.Error as e:
            logger.error(e)
    return None

def get_instances(connexion, nom_table):
    """
    Retourne les instances de la table nom_table
    String nom_table : nom de la table
    """
    query = sql.SQL('SELECT * FROM {table}').format(table=sql.Identifier(nom_table), )
    return execute_select_query(connexion, query)

def count_instances(connexion, nom_table):
    """
    Retourne le nombre d'instances de la table nom_table
    String nom_table : nom de la table
    """
    query = sql.SQL('SELECT COUNT(*) AS nb FROM {table}').format(table=sql.Identifier(nom_table))
    return execute_select_query(connexion, query)

def get_table_like(connexion, nom_table, like_pattern):
    """
    Retourne les instances de la table nom_table dont le nom correspond au motif like_pattern
    String nom_table : nom de la table
    String like_pattern : motif pour une requête LIKE
    """
    motif = '%' + like_pattern + '%'
    nom_att = 'nom'
    if nom_table == 'recette':
        nom_att += '_recette'
    query = sql.SQL("SELECT * FROM {} WHERE {} ILIKE {}").format(
        sql.Identifier(nom_table),
        sql.Identifier(nom_att),
        sql.Placeholder())
    return execute_select_query(connexion, query, [motif])


def get_cartes(connexion):
    """
    Retourne la liste des cartes de jeu (code, nom, description, image).
    """
    query = "SELECT code_tc, nom, description, image FROM typecarte ORDER BY code_tc"
    return execute_select_query(connexion, query)


def get_joueur_par_pseudo(connexion, pseudo):
    """
    Retourne le pseudo de l'utilisateur
    String pseudo : pseudo de l'utilisateur
    """
    query = 'SELECT * FROM joueur WHERE pseudo=%s'
    return execute_select_query(connexion, query, [pseudo])


def ajouter_un_joueur(connexion, pseudo, nom, prenom, date_naissance):
    """
    Ajoute un joueur humain en base : d'abord dans la table joueur, puis dans humain.
    Retourne l'identifiant du nouveau joueur, ou None si le pseudo est déjà pris.
    """
    # Vérification si le pseudo existe déjà
    joueur = get_joueur_par_pseudo(connexion, pseudo)
    if joueur:
        return None

    # Insertion dans joueur et récupération de l'identifiant généré
    query_joueur = "INSERT INTO joueur (pseudo) VALUES (%s) RETURNING id_j"
    with connexion.cursor() as cursor:
        cursor.execute(query_joueur, [pseudo])
        row = cursor.fetchone()
        if not row:
            return None
        id_j = row[0]

    # Insertion des informations personnelles dans humain
    query_humain = "INSERT INTO humain (id_j, nom, prenom, date_naissance) VALUES (%s, %s, %s, %s)"
    execute_other_query(connexion, query_humain, [id_j, nom, prenom, date_naissance])
    connexion.commit()

    return id_j


def get_liste_joueurs(connexion):
    """
    1) Afficher la liste des joueurs
    Retourne l'identifiant et le pseudo de tous les joueurs.
    """
    query = "SELECT id_j, pseudo FROM joueur ORDER BY id_j"
    return execute_select_query(connexion, query)




def get_scores_finaux_humains(connexion):
    """
    3) Afficher les scores finaux des joueurs humains.
    Affiche nom, prénom (table HUMAIN) et score_final (association JOUE_REEL).
    """
    query = """
        SELECT h.nom, h.prenom, jr.score_final
        FROM humain h
        JOIN joue_reel jr ON jr.id_humain = h.id_j
        ORDER BY jr.score_final DESC, h.nom, h.prenom
    """
    return execute_select_query(connexion, query)


def get_tirs_joueur_dans_partie(connexion, id_joueur, code_partie):
    """
    4) Afficher les tirs effectués par un joueur dans une partie.

    Hypothèse de schéma (cohérente avec le MCD) :
    - table EST_EFFECTUE_PAR relie (id_j) -> (num_ti)
    - table TIR contient (num_ti, coord_x, coord_y, etat, num_t)
    - table TOUR contient (num_t, code_partie) pour rattacher un tir à une partie

    Si tes clés/colonnes diffèrent, adapte les noms dans la requête.
    """
    query = """
        SELECT t.num_ti, t.coord_x, t.coord_y, t.etat
        FROM tir t
        JOIN est_effectue_par e ON e.num_ti = t.num_ti
        JOIN tour tr ON tr.num_t = t.num_t AND tr.code_partie = %s
        WHERE e.id_j = %s
        ORDER BY t.num_ti
    """
    return execute_select_query(connexion, query, [code_partie, id_joueur])


def get_joueurs_virtuels_par_niveau(connexion, niveau):
    """
    6) Afficher les joueurs virtuels en fonction du niveau souhaité.
    """
    query = "SELECT * FROM joueur j JOIN virtuel v ON j.id_j = v.id_j WHERE v.niveau_expertise = %s;"
    return execute_select_query(connexion, query, [niveau])


def ajouter_un_joueur_virtuel(connexion, pseudo, niveau):
    """
    Ajoute un joueur virtuel.
    """
    query = "INSERT INTO joueur (pseudo) VALUES (%s) RETURNING id_j"
    with connexion.cursor() as cursor:
        cursor.execute(query, [pseudo])
        row = cursor.fetchone()
        if not row:
            return None
        id_j = row[0]

    query_virtuel = "INSERT INTO virtuel (id_j, niveau_expertise) VALUES (%s, %s)"
    execute_other_query(connexion, query_virtuel, [id_j, niveau])
    connexion.commit()

    return id_j


def creer_partie(connexion, pseudo):
    """
    Crée une nouvelle partie en cours pour un joueur donné.
    Retourne le code de la partie créée.
    """
    with connexion.cursor() as cursor:
        # Récupérer l'identifiant du joueur à partir du pseudo
        cursor.execute("SELECT id_j FROM joueur WHERE pseudo = %s", [pseudo])
        row = cursor.fetchone()
        if not row:
            return None
        id_j = row[0]

        # Générer le prochain code de partie
        cursor.execute("SELECT COALESCE(MAX(code_partie), 0) + 1 FROM partie")
        code_partie = cursor.fetchone()[0]
        cursor.execute(
            "INSERT INTO partie (code_partie, date_creation, heure_creation, etat) VALUES (%s, CURRENT_DATE, CURRENT_TIME, %s)",
            (code_partie, 'En cours'),
        )

        # Associer le joueur à la partie via joue_reel
        cursor.execute(
            "INSERT INTO joue_reel (code_partie, id_humain, score_final) VALUES (%s, %s, %s)",
            (code_partie, id_j, 0),
        )

    connexion.commit()
    return code_partie

def creer_pioche(connexion, code_partie):
    """
    Crée une pioche pour une partie donnée.
    Retourne la liste des cartes de la pioche créée.
    """
    with connexion.cursor() as cursor:
        cursor.execute(
            "INSERT INTO pioche (nom_distrib, code_partie) VALUES (%s, %s) RETURNING id_pi",
            ('Distribution initiale', code_partie),
        )
        row = cursor.fetchone()
        if not row:
            return None
        id_pi = row[0]

        # Distribution des cartes sur 100 tirages, selon les proportions du sujet
        distribution = {
            "C_MISSILE": 50,
            "C_REJOUE": 10,
            "C_VIDE": 10,
            "C_MPM": 5,
            "C_LEURRE": 3,
            "C_WILLY": 3,
            "C_MEGA": 3,
            "C_ETOILE": 1,
            "C_PASSE": 10,
            "C_OUPS": 5,
        }

        cursor.execute("SELECT code_tc, nom FROM typecarte")
        rows_tc = cursor.fetchall()
        ids_par_nom = {r[1]: r[0] for r in rows_tc}
        sequence = []
        for nom_code, nb in distribution.items():
            code_tc = ids_par_nom.get(nom_code)
            if code_tc is not None:
                sequence.extend([code_tc] * nb)

        # Complétion avec C_MISSILE si certaines cartes sont absentes en base
        code_missile = ids_par_nom.get("C_MISSILE")
        if len(sequence) < 100 and code_missile is not None:
            sequence.extend([code_missile] * (100 - len(sequence)))
        # Sécurité minimale si C_MISSILE absent
        if not sequence:
            fallback = [r[0] for r in rows_tc]
            if not fallback:
                connexion.commit()
                return []
            while len(sequence) < 100:
                sequence.append(fallback[len(sequence) % len(fallback)])

        random.shuffle(sequence)
        for rang, code_tc in enumerate(sequence, start=1):
            cursor.execute(
                "INSERT INTO carte (id_pi, code_tc, etat, rang) VALUES (%s, %s, %s, %s)",
                (id_pi, code_tc, 'dans_pioche', rang),
            )

    connexion.commit()

    # Retourner les cartes de la pioche créée
    query = """
        SELECT tc.code_tc, tc.nom, tc.description, tc.image
        FROM carte c
        JOIN pioche p ON p.id_pi = c.id_pi
        JOIN typecarte tc ON tc.code_tc = c.code_tc
        WHERE p.code_partie = %s
        ORDER BY c.rang
    """
    return execute_select_query(connexion, query, [code_partie])


def set_partie_etat(connexion, code_partie, etat):
    query = "UPDATE partie SET etat = %s WHERE code_partie = %s"
    execute_other_query(connexion, query, [etat, code_partie])
    connexion.commit()


def _ensure_snapshot_table(connexion):
    query = """
        CREATE TABLE IF NOT EXISTS partie_snapshot (
            code_partie INTEGER PRIMARY KEY,
            state_json TEXT NOT NULL,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """
    execute_other_query(connexion, query, [])
    connexion.commit()


def save_partie_snapshot(connexion, code_partie, state):
    if code_partie is None or state is None:
        return
    _ensure_snapshot_table(connexion)
    payload = json.dumps(state, ensure_ascii=True)
    query = """
        INSERT INTO partie_snapshot (code_partie, state_json, updated_at)
        VALUES (%s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (code_partie)
        DO UPDATE SET
            state_json = EXCLUDED.state_json,
            updated_at = CURRENT_TIMESTAMP
    """
    execute_other_query(connexion, query, [int(code_partie), payload])
    connexion.commit()


def load_partie_snapshot(connexion, code_partie):
    if code_partie is None:
        return None
    _ensure_snapshot_table(connexion)
    query = "SELECT state_json FROM partie_snapshot WHERE code_partie = %s"
    rows = execute_select_query(connexion, query, [int(code_partie)])
    if not rows:
        return None
    raw = rows[0].get('state_json')
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def _get_pioche_id(connexion, code_partie):
    query = "SELECT id_pi FROM pioche WHERE code_partie = %s ORDER BY id_pi DESC LIMIT 1"
    rows = execute_select_query(connexion, query, [code_partie])
    return rows[0]["id_pi"] if rows else None


def _reset_pioche(connexion, id_pi):
    with connexion.cursor() as cursor:
        cursor.execute("SELECT ctid FROM carte WHERE id_pi = %s", [id_pi])
        rows = cursor.fetchall()
        if not rows:
            return
        ctids = [r[0] for r in rows]
        random.shuffle(ctids)
        for rang, ctid in enumerate(ctids, start=1):
            cursor.execute(
                "UPDATE carte SET etat = %s, rang = %s WHERE ctid = %s",
                ('dans_pioche', rang, ctid),
            )
    connexion.commit()


def piocher_carte(connexion, code_partie):
    id_pi = _get_pioche_id(connexion, code_partie)
    if id_pi is None:
        creer_pioche(connexion, code_partie)
        id_pi = _get_pioche_id(connexion, code_partie)
        if id_pi is None:
            return None

    with connexion.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            """
            SELECT c.ctid AS _ctid, c.id_c, tc.code_tc, tc.nom, tc.description, tc.image
            FROM carte c
            JOIN typecarte tc ON tc.code_tc = c.code_tc
            WHERE c.id_pi = %s AND c.etat = 'dans_pioche'
            ORDER BY c.rang ASC
            LIMIT 1
            """,
            [id_pi],
        )
        row = cursor.fetchone()

        if row is None:
            _reset_pioche(connexion, id_pi)
            cursor.execute(
                """
                SELECT c.ctid AS _ctid, c.id_c, tc.code_tc, tc.nom, tc.description, tc.image
                FROM carte c
                JOIN typecarte tc ON tc.code_tc = c.code_tc
                WHERE c.id_pi = %s AND c.etat = 'dans_pioche'
                ORDER BY c.rang ASC
                LIMIT 1
                """,
                [id_pi],
            )
            row = cursor.fetchone()
            if row is None:
                return None

        cursor.execute("UPDATE carte SET etat = 'utilisee' WHERE ctid = %s", [row["_ctid"]])
    connexion.commit()
    return {
        "id_c": row["id_c"],
        "code_tc": row["code_tc"],
        "code_nom": row["nom"],
        "nom": row["nom"],
        "description": row["description"],
        "image": row["image"],
    }


def get_ids_joueurs_partie(connexion, code_partie):
    query = """
        SELECT jr.id_humain AS id_humain, jv.id_virtuel AS id_virtuel
        FROM partie p
        LEFT JOIN joue_reel jr ON jr.code_partie = p.code_partie
        LEFT JOIN joue_virt jv ON jv.code_partie = p.code_partie
        WHERE p.code_partie = %s
        LIMIT 1
    """
    rows = execute_select_query(connexion, query, [code_partie])
    if not rows:
        return None, None
    return rows[0].get("id_humain"), rows[0].get("id_virtuel")


def inserer_tir(connexion, code_partie, num_t, id_j, id_c, coord_x, coord_y):
    query = """
        INSERT INTO tir (coord_x, coord_y, id_j, id_c, code_partie, num_t)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    execute_other_query(connexion, query, [coord_x, coord_y, id_j, id_c, code_partie, num_t])
    connexion.commit()


def upsert_tour(connexion, code_partie, num_t, nb_coules_j1, nb_touches_j1, nb_coules_j2, nb_touches_j2):
    query_update = """
        UPDATE tour
        SET nb_coules_j1 = %s, nb_touches_j1 = %s, nb_coules_j2 = %s, nb_touches_j2 = %s
        WHERE code_partie = %s AND num_t = %s
    """
    rc = execute_other_query(
        connexion,
        query_update,
        [nb_coules_j1, nb_touches_j1, nb_coules_j2, nb_touches_j2, code_partie, num_t],
    )
    if not rc:
        query_insert = """
            INSERT INTO tour (code_partie, num_t, nb_coules_j1, nb_touches_j1, nb_coules_j2, nb_touches_j2)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        execute_other_query(
            connexion,
            query_insert,
            [code_partie, num_t, nb_coules_j1, nb_touches_j1, nb_coules_j2, nb_touches_j2],
        )
    connexion.commit()




def get_parties_par_joueur(connexion, id_joueur):
    """
    2) Afficher les parties jouées par un joueur spécifique.

    D'après le MCD, une partie peut être jouée via JOUE_REEL (humain)
    ou JOUE_VIRT (virtuel) -> on fait un UNION des deux.
    """
    query = """
        SELECT p.code_partie, p.date_creation, p.heure_creation, p.etat
        FROM partie p
        JOIN joue_reel jr ON jr.code_partie = p.code_partie
        WHERE jr.id_humain = %s
        UNION
        SELECT p.code_partie, p.date_creation, p.heure_creation, p.etat
        FROM partie p
        JOIN joue_virt jv ON jv.code_partie = p.code_partie
        WHERE jv.id_virtuel = %s
        ORDER BY code_partie
    """
    return execute_select_query(connexion, query, [id_joueur, id_joueur])


def get_partie_base(connexion, code_partie):
    """
    Récupère les informations de base d'une partie.
    nb_tours : dernier numéro de tour enregistré (table tour), 0 si aucun tour.
    """
    query = """
        SELECT p.code_partie, p.date_creation, p.heure_creation, p.etat,
               COALESCE(
                   (SELECT MAX(t.num_t) FROM tour t WHERE t.code_partie = p.code_partie),
                   0
               ) AS nb_tours
        FROM partie p
        WHERE p.code_partie = %s
    """
    return execute_select_query(connexion, query, [code_partie])


def get_parties_en_cours(connexion, pseudo):
    """
    Parties « en cours » pour un joueur humain connecté (via joue_reel).

    Les compteurs nb_navires_* proviennent du dernier enregistrement tour pour la partie.
    Convention BatNav : joueur 1 = humain (joue_reel), joueur 2 = adversaire (joue_virt).
    """
    query = """
        SELECT
            p.code_partie,
            p.date_creation,
            p.heure_creation,
            COALESCE(
                (SELECT MAX(t2.num_t) FROM tour t2 WHERE t2.code_partie = p.code_partie),
                0
            ) AS nb_tours,
            j_adv.pseudo AS pseudo_adversaire,
            CASE v.niveau_expertise
                WHEN 1 THEN 'Faible'
                WHEN 2 THEN 'Moyen'
                WHEN 3 THEN 'Expert'
                ELSE NULL
            END AS niveau_adversaire,
            jv.id_virtuel AS id_adversaire,
            COALESCE(lt.nb_coules_j1, 0) AS nb_navires_coules_joueur,
            COALESCE(lt.nb_touches_j1, 0) AS nb_navires_touches_joueur,
            COALESCE(lt.nb_coules_j2, 0) AS nb_navires_coules_adversaire,
            COALESCE(lt.nb_touches_j2, 0) AS nb_navires_touches_adversaire
        FROM partie p
        JOIN joue_reel jr ON jr.code_partie = p.code_partie
        JOIN humain h ON h.id_j = jr.id_humain
        JOIN joueur j ON j.id_j = h.id_j
        LEFT JOIN joue_virt jv ON jv.code_partie = p.code_partie
        LEFT JOIN virtuel v ON v.id_j = jv.id_virtuel
        LEFT JOIN joueur j_adv ON j_adv.id_j = jv.id_virtuel
        LEFT JOIN LATERAL (
            SELECT t.nb_coules_j1, t.nb_touches_j1, t.nb_coules_j2, t.nb_touches_j2
            FROM tour t
            WHERE t.code_partie = p.code_partie
            ORDER BY t.num_t DESC
            LIMIT 1
        ) lt ON TRUE
        WHERE LOWER(TRIM(p.etat)) IN ('en cours', 'suspendue') AND j.pseudo = %s
        ORDER BY p.date_creation DESC, p.heure_creation DESC
    """
    rows = execute_select_query(connexion, query, [pseudo])
    return rows if rows is not None else []

def get_joueur_humain(connexion, pseudo):
    """
    Récupère les informations des joueurs humains associés à un pseudo.
    """
    query = """
        SELECT h.id_j, h.nom, h.prenom
        FROM humain h
        JOIN joueur j ON h.id_j = j.id_j
        WHERE j.pseudo = %s
    """
    return execute_select_query(connexion, query, [pseudo])

def get_joueur_virtuel(connexion, pseudo):
    """
    Récupère les informations des joueurs virtuels associés à un pseudo.
    """
    query = """
        SELECT v.id_j, v.niveau_expertise
        FROM virtuel v
        JOIN joueur j ON v.id_j = j.id_j
        WHERE j.pseudo = %s
    """
    return execute_select_query(connexion, query, [pseudo])

def get_parties_en_cours_simplifie(connexion, pseudo):
    """
    Récupère les parties en cours pour un joueur donné en utilisant des primitives simples.
    """
    parties = []

    # Récupérer les joueurs humains et leurs parties
    joueurs_humains = get_joueur_humain(connexion, pseudo)
    for joueur in joueurs_humains:
        query = """
            SELECT p.code_partie
            FROM partie p
            JOIN joue_reel jr ON jr.code_partie = p.code_partie
            WHERE jr.id_humain = %s AND lower(p.etat) IN ('en cours', 'suspendue')
        """
        result = execute_select_query(connexion, query, [joueur['id_j']])
        for partie in result:
            partie_base = get_partie_base(connexion, partie['code_partie'])
            partie_base[0]['joueur'] = joueur
            parties.append(partie_base[0])

    # Récupérer les joueurs virtuels et leurs parties
    joueurs_virtuels = get_joueur_virtuel(connexion, pseudo)
    for joueur in joueurs_virtuels:
        query = """
            SELECT p.code_partie
            FROM partie p
            JOIN joue_virt jv ON jv.code_partie = p.code_partie
            WHERE jv.id_virtuel = %s AND lower(p.etat) IN ('en cours', 'suspendue')
        """
        result = execute_select_query(connexion, query, [joueur['id_j']])
        for partie in result:
            partie_base = get_partie_base(connexion, partie['code_partie'])
            partie_base[0]['joueur'] = joueur
            parties.append(partie_base[0])

    return parties


def get_classement_ijh(connexion, delta_mois=0):
    """
    Classement Individuel des Joueurs Humains (IJH):
    cumul des scores finaux par joueur humain.
    Si delta_mois > 0, on filtre les parties sur les delta derniers mois.
    """
    if delta_mois and int(delta_mois) > 0:
        query = """
            SELECT
                j.pseudo,
                h.nom,
                h.prenom,
                COALESCE(SUM(jr.score_final), 0) AS score_cumule,
                COUNT(*) AS nb_parties
            FROM joue_reel jr
            JOIN partie p ON p.code_partie = jr.code_partie
            JOIN humain h ON h.id_j = jr.id_humain
            JOIN joueur j ON j.id_j = h.id_j
            WHERE p.date_creation >= (CURRENT_DATE - (%s || ' months')::interval)
            GROUP BY j.pseudo, h.nom, h.prenom
            ORDER BY score_cumule DESC, nb_parties DESC, j.pseudo ASC
        """
        return execute_select_query(connexion, query, [int(delta_mois)])

    query = """
        SELECT
            j.pseudo,
            h.nom,
            h.prenom,
            COALESCE(SUM(jr.score_final), 0) AS score_cumule,
            COUNT(*) AS nb_parties
        FROM joue_reel jr
        JOIN partie p ON p.code_partie = jr.code_partie
        JOIN humain h ON h.id_j = jr.id_humain
        JOIN joueur j ON j.id_j = h.id_j
        GROUP BY j.pseudo, h.nom, h.prenom
        ORDER BY score_cumule DESC, nb_parties DESC, j.pseudo ASC
    """
    return execute_select_query(connexion, query)


def get_classement_cpp(connexion, delta_mois=0):
    """
    Classement Par Pavillon (CPP) :
    agrégation des scores des joueurs humains ayant joué avec une flottille nationale.
    Cette requête suppose les tables pavillon/flottille selon le sujet.
    Retourne [] si le schéma n'est pas encore complet.
    """
    try:
        if delta_mois and int(delta_mois) > 0:
            query = """
                SELECT
                    pv.code_pays,
                    pv.nom_pays,
                    COALESCE(SUM(jr.score_final), 0) AS score_cumule,
                    COUNT(*) AS nb_parties
                FROM joue_reel jr
                JOIN partie p ON p.code_partie = jr.code_partie
                JOIN humain h ON h.id_j = jr.id_humain
                JOIN possede_flottille pf ON pf.id_j = h.id_j
                JOIN flottille f ON f.id_flottille = pf.id_flottille
                JOIN pavillon pv ON pv.code_pays = f.code_pays
                WHERE f.type_flottille = 'nationale'
                  AND p.date_creation >= (CURRENT_DATE - (%s || ' months')::interval)
                GROUP BY pv.code_pays, pv.nom_pays
                ORDER BY score_cumule DESC, nb_parties DESC, pv.code_pays ASC
            """
            rows = execute_select_query(connexion, query, [int(delta_mois)])
        else:
            query = """
                SELECT
                    pv.code_pays,
                    pv.nom_pays,
                    COALESCE(SUM(jr.score_final), 0) AS score_cumule,
                    COUNT(*) AS nb_parties
                FROM joue_reel jr
                JOIN partie p ON p.code_partie = jr.code_partie
                JOIN humain h ON h.id_j = jr.id_humain
                JOIN possede_flottille pf ON pf.id_j = h.id_j
                JOIN flottille f ON f.id_flottille = pf.id_flottille
                JOIN pavillon pv ON pv.code_pays = f.code_pays
                WHERE f.type_flottille = 'nationale'
                GROUP BY pv.code_pays, pv.nom_pays
                ORDER BY score_cumule DESC, nb_parties DESC, pv.code_pays ASC
            """
            rows = execute_select_query(connexion, query)
        return rows or []
    except Exception as e:
        logger.error("get_classement_cpp error: %s", e)
        return []


# ===================================================
# Primitives de jeu (logique métier BatNav)
# ===================================================

import random as _random

COLS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
ROWS = list(range(1, 11))

FLOTTE_MODELE = [
    {"nom": "Le Jean Bart", "type": "Porte-avion", "taille": 5, "pavillon": "FR", "label": "PA"},
    {"nom": "Le Foch", "type": "Croiseur", "taille": 4, "pavillon": "FR", "label": "CR"},
    {"nom": "USS Fletcher", "type": "Contre-torpilleur", "taille": 3, "pavillon": "USA", "label": "CT1"},
    {"nom": "HMS Javelin", "type": "Contre-torpilleur", "taille": 3, "pavillon": "UK", "label": "CT2"},
    {"nom": "Le Cyclone", "type": "Torpilleur", "taille": 2, "pavillon": "FR", "label": "TP"},
]


def build_flottille():
    return [
        {
            "nom": s["nom"],
            "type": s["type"],
            "taille": s["taille"],
            "pavillon": s["pavillon"],
            "label": s["label"],
            "place": False,
        }
        for s in FLOTTE_MODELE
    ]


def init_state():
    return {
        'grille_tirs': [[0] * 10 for _ in range(10)],
        'grille_navires': [[0] * 10 for _ in range(10)],
        'grille_navires_ennemi': [[0] * 10 for _ in range(10)],
        'ships_joueur': [],
        'ships_ennemi': [],
        'flottille': build_flottille(),
        'placement_index': 0,
        'grille_navires_labels': [[''] * 10 for _ in range(10)],
        'tour_number': 1,
        'partie_commencee': False,
        'carte_courante': None,
        'carte_piochee': False,
        'phase': 'PLACE',
        'historique': [],
        'message': '',
        'extra_shot_pending': False,
        'leurre_cells': [],
        'leurre_hits': [],
        'willy_cell': None,
        'c_vide_preview_done': False,
    }


def parse_coord(coord):
    if not coord:
        return None
    c = str(coord).strip().upper()
    if len(c) < 2 or len(c) > 3:
        return None
    col = c[0]
    if col < 'A' or col > 'J':
        return None
    try:
        row = int(c[1:])
    except ValueError:
        return None
    if row < 1 or row > 10:
        return None
    return (ord(col) - ord('A'), row - 1)


def coord_label(x, y):
    return f"{chr(ord('A') + x)}{y + 1}"


def normalize_card_code(carte):
    if not carte:
        return 'C_MISSILE'
    code_nom = carte.get('code_nom')
    if isinstance(code_nom, str) and code_nom.startswith('C_'):
        return code_nom
    code_tc = carte.get('code_tc')
    if isinstance(code_tc, str) and code_tc.startswith('C_'):
        return code_tc
    return 'C_MISSILE'


def impact_cells(x, y, code_carte):
    if code_carte in ('C_PASSE', 'C_OUPS'):
        return []
    if code_carte == 'C_MEGA':
        impacts = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < 10 and 0 <= ny < 10:
                    impacts.append((nx, ny))
        return impacts
    if code_carte == 'C_ETOILE':
        impacts = []
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                nx, ny = x + dx, y + dy
                if 0 <= nx < 10 and 0 <= ny < 10:
                    impacts.append((nx, ny))
        return impacts
    return [(x, y)]


def apply_tir_on_enemy(state, impacts):
    touches = 0
    coules = 0
    for x, y in impacts:
        if state['grille_tirs'][y][x] in (1, 2, 3):
            continue
        if state['grille_navires_ennemi'][y][x] == 4:
            state['grille_tirs'][y][x] = 2
            state['grille_navires_ennemi'][y][x] = 2
            touches += 1
        else:
            state['grille_tirs'][y][x] = 1
    for ship in state['ships_ennemi']:
        if all(state['grille_navires_ennemi'][cy][cx] in (2, 3) for cx, cy in ship['cells']):
            if any(state['grille_tirs'][cy][cx] != 3 for cx, cy in ship['cells']):
                for cx, cy in ship['cells']:
                    state['grille_tirs'][cy][cx] = 3
                    state['grille_navires_ennemi'][cy][cx] = 3
                coules += 1
    return touches, coules


def apply_tir_on_player(state, x, y):
    cell = state['grille_navires'][y][x]
    if cell in (1, 2, 3):
        return False, False
    if cell == 4:
        state['grille_navires'][y][x] = 2
        touche = True
    else:
        state['grille_navires'][y][x] = 1
        touche = False
    coule = False
    for ship in state['ships_joueur']:
        if (x, y) in ship['cells']:
            if all(state['grille_navires'][cy][cx] in (2, 3) for cx, cy in ship['cells']):
                for cx, cy in ship['cells']:
                    state['grille_navires'][cy][cx] = 3
                coule = True
            break
    return touche, coule


def count_flotte(ships, grille):
    nb_coules = 0
    nb_touches = 0
    for ship in ships:
        vals = [grille[cy][cx] for cx, cy in ship['cells']]
        if all(v == 3 for v in vals):
            nb_coules += 1
            nb_touches += 1
        elif any(v in (2, 3) for v in vals):
            nb_touches += 1
    return nb_coules, nb_touches


def place_ships_random(grille):
    def can_place(x, y, taille, horizontal):
        for i in range(taille):
            cx = x + i if horizontal else x
            cy = y if horizontal else y + i
            if not (0 <= cx < 10 and 0 <= cy < 10):
                return False
            if grille[cy][cx] != 0:
                return False
        return True

    ships = []
    for taille in [5, 4, 3, 3, 2]:
        placed = False
        for _ in range(200):
            horizontal = _random.choice([True, False])
            if horizontal:
                x = _random.randint(0, 10 - taille)
                y = _random.randint(0, 9)
            else:
                x = _random.randint(0, 9)
                y = _random.randint(0, 10 - taille)
            if not can_place(x, y, taille, horizontal):
                continue
            cells = []
            for i in range(taille):
                cx = x + i if horizontal else x
                cy = y if horizontal else y + i
                grille[cy][cx] = 4
                cells.append((cx, cy))
            ships.append({'cells': cells})
            placed = True
            break
        if not placed:
            raise RuntimeError("Impossible de placer tous les navires.")
    return ships


def place_player_ship(state, x, y, horizontal, ship_index=None):
    idx = state.get('placement_index', 0) if ship_index is None else int(ship_index)
    flotte = state.get('flottille', [])
    if len([s for s in flotte if s.get("place")]) >= len(flotte):
        return False, "Nombre maximal de navires deja atteint."
    if idx < 0 or idx >= len(flotte):
        return False, "Tous les navires sont deja places."
    ship_def = flotte[idx]
    if ship_def.get("place"):
        return False, "Ce navire est deja place."
    taille = int(ship_def['taille'])
    cells = []
    for i in range(taille):
        nx = x + i if horizontal else x
        ny = y if horizontal else y + i
        if not (0 <= nx < 10 and 0 <= ny < 10):
            return False, "Placement hors grille."
        if state['grille_navires'][ny][nx] != 0:
            return False, "Placement impossible: collision avec un autre element."
        cells.append((nx, ny))
    for nx, ny in cells:
        state['grille_navires'][ny][nx] = 4
        state['grille_navires_labels'][ny][nx] = ''
    if cells:
        ax, ay = cells[0]
        state['grille_navires_labels'][ay][ax] = ship_def.get('label', 'N')
    state['ships_joueur'].append({
        "cells": cells,
        "nom": ship_def["nom"],
        "type": ship_def["type"],
        "taille": ship_def["taille"],
        "pavillon": ship_def["pavillon"],
        "label": ship_def.get("label", "N"),
    })
    ship_def["place"] = True
    unplaced = [i for i, s in enumerate(flotte) if not s.get("place")]
    state['placement_index'] = unplaced[0] if unplaced else len(flotte)
    if all(s.get("place") for s in flotte):
        state['phase'] = 'DRAW'
        state['message'] = "Flottille complete. Piochez une carte pour commencer le tour 1."
    else:
        nxt = flotte[state['placement_index']]
        state['message'] = f"Navire place: {ship_def['nom']}. Placez maintenant {nxt['nom']} ({nxt['taille']} cases)."
    return True, state['message']


def sync_placement_state(state):
    flotte = state.get('flottille') or build_flottille()
    state['flottille'] = flotte
    ships_raw = state.get('ships_joueur') or []
    labels_allowed = {s.get("label") for s in flotte}
    labels_seen = set()
    ships = []
    for ship in ships_raw:
        label = ship.get("label")
        cells = ship.get("cells") or []
        if label not in labels_allowed:
            continue
        if label in labels_seen:
            continue
        if not isinstance(cells, list) or len(cells) == 0:
            continue
        ship_def = next((s for s in flotte if s.get("label") == label), None)
        if ship_def is None:
            continue
        if len(cells) != int(ship_def.get("taille", 0)):
            continue
        ok_cells = True
        for cell in cells:
            if not isinstance(cell, (list, tuple)) or len(cell) != 2:
                ok_cells = False
                break
            cx, cy = cell
            if not (isinstance(cx, int) and isinstance(cy, int) and 0 <= cx < 10 and 0 <= cy < 10):
                ok_cells = False
                break
        if not ok_cells:
            continue
        labels_seen.add(label)
        ships.append({
            "cells": [(int(cx), int(cy)) for cx, cy in cells],
            "nom": ship_def["nom"],
            "type": ship_def["type"],
            "taille": ship_def["taille"],
            "pavillon": ship_def["pavillon"],
            "label": ship_def["label"],
        })
    if len(ships) > len(flotte):
        ships = ships[:len(flotte)]
    state['ships_joueur'] = ships
    state['grille_navires'] = [[0] * 10 for _ in range(10)]
    state['grille_navires_labels'] = [[''] * 10 for _ in range(10)]
    for ship in ships:
        label = ship.get('label', 'N')
        for cx, cy in ship.get('cells', []):
            if 0 <= cx < 10 and 0 <= cy < 10:
                state['grille_navires'][cy][cx] = 4
        if ship.get('cells'):
            ax, ay = ship['cells'][0]
            if 0 <= ax < 10 and 0 <= ay < 10:
                state['grille_navires_labels'][ay][ax] = label
    for s in flotte:
        s['place'] = False
    for ship in ships:
        for s in flotte:
            if s.get('label') == ship.get('label'):
                s['place'] = True
                break
    unplaced = [i for i, s in enumerate(flotte) if not s.get('place')]
    state['placement_index'] = unplaced[0] if unplaced else len(flotte)
    if not unplaced and state.get('phase') == 'PLACE':
        state['phase'] = 'DRAW'
    elif unplaced and state.get('partie_commencee') and state.get('phase') not in ('PLACE', 'FINI'):
        state['phase'] = 'PLACE'


def replace_touched_ship(state):
    for ship in state['ships_joueur']:
        vals = [state['grille_navires'][cy][cx] for cx, cy in ship['cells']]
        if any(v == 2 for v in vals) and not all(v == 3 for v in vals):
            old_cells = list(ship['cells'])
            taille = len(old_cells)
            for cx, cy in old_cells:
                state['grille_navires'][cy][cx] = 0
                if 'grille_navires_labels' in state:
                    state['grille_navires_labels'][cy][cx] = ''
            for _ in range(200):
                horizontal = _random.choice([True, False])
                if horizontal:
                    x = _random.randint(0, 10 - taille)
                    y = _random.randint(0, 9)
                else:
                    x = _random.randint(0, 9)
                    y = _random.randint(0, 10 - taille)
                new_cells = []
                ok = True
                for i in range(taille):
                    nx = x + i if horizontal else x
                    ny = y if horizontal else y + i
                    if state['grille_navires'][ny][nx] != 0:
                        ok = False
                        break
                    new_cells.append((nx, ny))
                if ok:
                    for nx, ny in new_cells:
                        state['grille_navires'][ny][nx] = 4
                        if 'grille_navires_labels' in state:
                            state['grille_navires_labels'][ny][nx] = ship.get('label', 'N')
                    ship['cells'] = new_cells
                    return True
            for cx, cy in old_cells:
                state['grille_navires'][cy][cx] = 4
                if 'grille_navires_labels' in state:
                    state['grille_navires_labels'][cy][cx] = ship.get('label', 'N')
            return False
    return False


def replace_touched_ship_to(state, x, y, horizontal):
    damaged_ship = None
    for ship in state['ships_joueur']:
        vals = [state['grille_navires'][cy][cx] for cx, cy in ship['cells']]
        if any(v == 2 for v in vals) and not all(v == 3 for v in vals):
            damaged_ship = ship
            break
    if damaged_ship is None:
        return False
    taille = len(damaged_ship['cells'])
    new_cells = []
    for i in range(taille):
        nx = x + i if horizontal else x
        ny = y if horizontal else y + i
        if not (0 <= nx < 10 and 0 <= ny < 10):
            return False
        if state['grille_navires'][ny][nx] != 0:
            return False
        new_cells.append((nx, ny))
    for cx, cy in damaged_ship['cells']:
        state['grille_navires'][cy][cx] = 0
        if 'grille_navires_labels' in state:
            state['grille_navires_labels'][cy][cx] = ''
    for nx, ny in new_cells:
        state['grille_navires'][ny][nx] = 4
        if 'grille_navires_labels' in state:
            state['grille_navires_labels'][ny][nx] = damaged_ship.get('label', 'N')
    damaged_ship['cells'] = new_cells
    return True


def place_leurre(state):
    for lx, ly in state.get('leurre_cells', []):
        if state['grille_navires'][ly][lx] == 5:
            state['grille_navires'][ly][lx] = 0
    taille = 3
    for _ in range(200):
        horizontal = _random.choice([True, False])
        if horizontal:
            x = _random.randint(0, 10 - taille)
            y = _random.randint(0, 9)
        else:
            x = _random.randint(0, 9)
            y = _random.randint(0, 10 - taille)
        cells = []
        ok = True
        for i in range(taille):
            nx = x + i if horizontal else x
            ny = y if horizontal else y + i
            if state['grille_navires'][ny][nx] != 0:
                ok = False
                break
            cells.append((nx, ny))
        if ok:
            state['leurre_cells'] = cells
            state['leurre_hits'] = []
            for nx, ny in cells:
                state['grille_navires'][ny][nx] = 5
            return True
    return False


def place_leurre_at(state, x, y, horizontal):
    for lx, ly in state.get('leurre_cells', []):
        if state['grille_navires'][ly][lx] == 5:
            state['grille_navires'][ly][lx] = 0
    cells = []
    for i in range(3):
        nx = x + i if horizontal else x
        ny = y if horizontal else y + i
        if not (0 <= nx < 10 and 0 <= ny < 10):
            return False
        if state['grille_navires'][ny][nx] != 0:
            return False
        cells.append((nx, ny))
    state['leurre_cells'] = cells
    state['leurre_hits'] = []
    for nx, ny in cells:
        state['grille_navires'][ny][nx] = 5
    return True


def place_willy(state):
    old = state.get('willy_cell')
    if old is not None:
        ox, oy = old
        if state['grille_navires'][oy][ox] == 6:
            state['grille_navires'][oy][ox] = 0
    free = [(x, y) for y in range(10) for x in range(10) if state['grille_navires'][y][x] == 0]
    if not free:
        return False
    wx, wy = _random.choice(free)
    state['willy_cell'] = (wx, wy)
    state['grille_navires'][wy][wx] = 6
    return True


def place_willy_at(state, x, y):
    old = state.get('willy_cell')
    if old is not None:
        ox, oy = old
        if state['grille_navires'][oy][ox] == 6:
            state['grille_navires'][oy][ox] = 0
    if not (0 <= x < 10 and 0 <= y < 10):
        return False
    if state['grille_navires'][y][x] != 0:
        return False
    state['willy_cell'] = (x, y)
    state['grille_navires'][y][x] = 6
    return True


def sink_three_smallest_enemy_ships(state):
    alive = []
    for ship in state.get('ships_ennemi', []):
        vals = [state['grille_navires_ennemi'][cy][cx] for cx, cy in ship['cells']]
        if not all(v == 3 for v in vals):
            alive.append(ship)
    alive.sort(key=lambda s: len(s['cells']))
    for ship in alive[:3]:
        for cx, cy in ship['cells']:
            state['grille_navires_ennemi'][cy][cx] = 3
            state['grille_tirs'][cy][cx] = 3
    return min(3, len(alive))


def adversaire_tir(state):
    carte_adv = state.get('carte_adv')
    code = normalize_card_code(carte_adv)

    if code == 'C_PASSE':
        return {'coord': None, 'touche': False, 'coule': False, 'impacts': [], 'msg': "L'adversaire passe son tour."}

    def apply_local(x, y):
        cell = state['grille_navires'][y][x]
        if cell in (1, 2, 3):
            return False, False
        if cell == 4:
            state['grille_navires'][y][x] = 2
            touche = True
        else:
            state['grille_navires'][y][x] = 1
            touche = False
        coule = False
        for ship in state.get('ships_joueur', []):
            if (x, y) in ship['cells']:
                if all(state['grille_navires'][cy][cx] in (2, 3) for cx, cy in ship['cells']):
                    for cx, cy in ship['cells']:
                        state['grille_navires'][cy][cx] = 3
                    coule = True
                break
        return touche, coule

    if code == 'C_OUPS':
        candidates = [(x, y) for y in range(10) for x in range(10) if state['grille_navires'][y][x] == 4]
        if not candidates:
            candidates = [(x, y) for y in range(10) for x in range(10) if state['grille_navires'][y][x] == 0]
        if not candidates:
            return {'coord': None, 'touche': False, 'coule': False, 'impacts': [], 'msg': "L'adversaire n'a aucune cible."}
        x, y = _random.choice(candidates)
        touche, coule = apply_local(x, y)
        return {'coord': coord_label(x, y), 'touche': touche, 'coule': coule, 'impacts': [(x, y)], 'msg': "Mauvaise manip adverse !"}

    candidates = [(x, y) for y in range(10) for x in range(10) if state['grille_navires'][y][x] in (0, 4)]
    if not candidates:
        return {'coord': None, 'touche': False, 'coule': False, 'impacts': [], 'msg': "L'adversaire n'a aucune cible."}
    x, y = _random.choice(candidates)
    impacts = impact_cells(x, y, code)
    touche = False
    coule = False
    for ix, iy in impacts:
        hit, sunk = apply_local(ix, iy)
        touche = touche or hit
        coule = coule or sunk
    return {'coord': coord_label(x, y), 'touche': touche, 'coule': coule, 'impacts': impacts, 'msg': None}


def build_cell_images_map():
    import os
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'images')
    names = []
    try:
        names = os.listdir(base_dir)
    except OSError:
        names = []

    def pick(prefix, default_name):
        for n in names:
            if n.lower().startswith(prefix.lower()):
                return n
        return default_name

    return {
        0: pick("Cellule_nonExplore", "logo-batnav.svg"),
        1: pick("Cellule_a", "logo-batnav.svg"),
        2: pick("Cellule_touche", "logo-batnav.svg"),
        3: pick("Cellule_touche", "logo-batnav.svg"),
        4: pick("Cellule_navire", "logo-batnav.svg"),
    }




