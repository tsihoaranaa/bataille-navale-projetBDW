-- ============================================================
-- Auteurs : GERGES Robin, RAONIMANANA Aaron
-- Script de création de la base ProjetBDW2026
-- Usage (psql) :
--   psql -h <host> -U <user> -d <database> -f sql/01_creation_base.sql
-- ============================================================

BEGIN;

-- =========================
-- Tables de reference
-- =========================

CREATE TABLE IF NOT EXISTS joueur (
    id_j INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pseudo VARCHAR(64) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS humain (
    id_j INTEGER PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    date_naissance DATE,
    CONSTRAINT fk_humain_joueur
        FOREIGN KEY (id_j) REFERENCES joueur(id_j)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS virtuel (
    id_j INTEGER PRIMARY KEY,
    niveau_expertise INTEGER NOT NULL CHECK (niveau_expertise BETWEEN 1 AND 3),
    CONSTRAINT fk_virtuel_joueur
        FOREIGN KEY (id_j) REFERENCES joueur(id_j)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS partie (
    code_partie INTEGER PRIMARY KEY,
    date_creation DATE NOT NULL DEFAULT CURRENT_DATE,
    heure_creation TIME NOT NULL DEFAULT CURRENT_TIME,
    etat VARCHAR(32) NOT NULL
);

CREATE TABLE IF NOT EXISTS typecarte (
    code_tc VARCHAR(32) PRIMARY KEY,
    nom VARCHAR(64) NOT NULL,
    description TEXT,
    image VARCHAR(255)
);

-- =========================
-- Tables de jeu
-- =========================

CREATE TABLE IF NOT EXISTS joue_reel (
    code_partie INTEGER NOT NULL,
    id_humain INTEGER NOT NULL,
    score_final INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (code_partie, id_humain),
    CONSTRAINT fk_joue_reel_partie
        FOREIGN KEY (code_partie) REFERENCES partie(code_partie)
        ON DELETE CASCADE,
    CONSTRAINT fk_joue_reel_humain
        FOREIGN KEY (id_humain) REFERENCES humain(id_j)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS joue_virt (
    code_partie INTEGER NOT NULL,
    id_virtuel INTEGER NOT NULL,
    PRIMARY KEY (code_partie, id_virtuel),
    CONSTRAINT fk_joue_virt_partie
        FOREIGN KEY (code_partie) REFERENCES partie(code_partie)
        ON DELETE CASCADE,
    CONSTRAINT fk_joue_virt_virtuel
        FOREIGN KEY (id_virtuel) REFERENCES virtuel(id_j)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tour (
    code_partie INTEGER NOT NULL,
    num_t INTEGER NOT NULL,
    nb_coules_j1 INTEGER NOT NULL DEFAULT 0,
    nb_touches_j1 INTEGER NOT NULL DEFAULT 0,
    nb_coules_j2 INTEGER NOT NULL DEFAULT 0,
    nb_touches_j2 INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (code_partie, num_t),
    CONSTRAINT fk_tour_partie
        FOREIGN KEY (code_partie) REFERENCES partie(code_partie)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pioche (
    id_pi INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom_distrib VARCHAR(128) NOT NULL,
    code_partie INTEGER NOT NULL,
    CONSTRAINT fk_pioche_partie
        FOREIGN KEY (code_partie) REFERENCES partie(code_partie)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS carte (
    id_c INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_pi INTEGER NOT NULL,
    code_tc VARCHAR(32) NOT NULL,
    etat VARCHAR(32) NOT NULL,
    rang INTEGER NOT NULL,
    CONSTRAINT fk_carte_pioche
        FOREIGN KEY (id_pi) REFERENCES pioche(id_pi)
        ON DELETE CASCADE,
    CONSTRAINT fk_carte_type
        FOREIGN KEY (code_tc) REFERENCES typecarte(code_tc)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS tir (
    num_ti INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    coord_x INTEGER NOT NULL CHECK (coord_x BETWEEN 0 AND 9),
    coord_y INTEGER NOT NULL CHECK (coord_y BETWEEN 0 AND 9),
    id_j INTEGER NOT NULL,
    id_c INTEGER,
    code_partie INTEGER NOT NULL,
    num_t INTEGER NOT NULL,
    etat VARCHAR(32) NOT NULL DEFAULT 'utilisee',
    CONSTRAINT fk_tir_joueur
        FOREIGN KEY (id_j) REFERENCES joueur(id_j)
        ON DELETE CASCADE,
    CONSTRAINT fk_tir_carte
        FOREIGN KEY (id_c) REFERENCES carte(id_c)
        ON DELETE SET NULL,
    CONSTRAINT fk_tir_partie
        FOREIGN KEY (code_partie) REFERENCES partie(code_partie)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS partie_snapshot (
    code_partie INTEGER PRIMARY KEY,
    state_json TEXT NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_snapshot_partie
        FOREIGN KEY (code_partie) REFERENCES partie(code_partie)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS a_gagne (
    code_partie INTEGER PRIMARY KEY,
    id_j INTEGER NOT NULL,
    CONSTRAINT fk_a_gagne_partie
        FOREIGN KEY (code_partie) REFERENCES partie(code_partie)
        ON DELETE CASCADE,
    CONSTRAINT fk_a_gagne_joueur
        FOREIGN KEY (id_j) REFERENCES joueur(id_j)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS sequence_temporelle (
    code_partie INTEGER PRIMARY KEY,
    date_debut DATE,
    heure_debut TIME,
    date_fin DATE,
    heure_fin TIME,
    CONSTRAINT fk_sequence_partie
        FOREIGN KEY (code_partie) REFERENCES partie(code_partie)
        ON DELETE CASCADE,
    CONSTRAINT chk_sequence_fin
        CHECK (
            date_fin IS NULL
            OR date_fin > date_debut
            OR (date_fin = date_debut AND heure_fin IS NOT NULL AND heure_debut IS NOT NULL AND heure_fin >= heure_debut)
        )
);

CREATE TABLE IF NOT EXISTS grille (
    id_grille INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    largeur INTEGER NOT NULL CHECK (largeur BETWEEN 1 AND 20),
    hauteur INTEGER NOT NULL CHECK (hauteur BETWEEN 1 AND 20),
    img_non_exp VARCHAR(255),
    img_eau VARCHAR(255),
    img_navire VARCHAR(255),
    nom_orque VARCHAR(128),
    img_orque VARCHAR(255),
    taille_leurre INTEGER CHECK (taille_leurre IS NULL OR taille_leurre BETWEEN 1 AND 10),
    x_leurre INTEGER,
    y_leurre INTEGER,
    id_j INTEGER NOT NULL,
    type_grille VARCHAR(32),
    code_partie INTEGER,
    CONSTRAINT fk_grille_joueur
        FOREIGN KEY (id_j) REFERENCES joueur(id_j)
        ON DELETE CASCADE,
    CONSTRAINT fk_grille_partie
        FOREIGN KEY (code_partie) REFERENCES partie(code_partie)
        ON DELETE SET NULL
);

-- Tables de classement par pavillon (utilisees par get_classement_cpp)
CREATE TABLE IF NOT EXISTS pavillon (
    code_pays VARCHAR(8) PRIMARY KEY,
    nom_pays VARCHAR(128) NOT NULL
);

CREATE TABLE IF NOT EXISTS flottille (
    id_flottille INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code_pays VARCHAR(8) NOT NULL,
    id_grille INTEGER,
    type_flottille VARCHAR(32) NOT NULL,
    CONSTRAINT fk_flottille_pavillon
        FOREIGN KEY (code_pays) REFERENCES pavillon(code_pays)
        ON DELETE RESTRICT,
    CONSTRAINT fk_flottille_grille
        FOREIGN KEY (id_grille) REFERENCES grille(id_grille)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS navire (
    id_navire INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom_bat VARCHAR(128) NOT NULL,
    type_bat VARCHAR(64),
    taille INTEGER NOT NULL CHECK (taille BETWEEN 1 AND 10),
    code_pays VARCHAR(8) NOT NULL,
    CONSTRAINT fk_navire_pavillon
        FOREIGN KEY (code_pays) REFERENCES pavillon(code_pays)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS compose_de (
    id_flottille INTEGER NOT NULL,
    id_navire INTEGER NOT NULL,
    coord_x INTEGER NOT NULL,
    coord_y INTEGER NOT NULL,
    sens VARCHAR(1) NOT NULL,
    etat_navire VARCHAR(32),
    PRIMARY KEY (id_flottille, id_navire),
    CONSTRAINT fk_compose_flottille
        FOREIGN KEY (id_flottille) REFERENCES flottille(id_flottille)
        ON DELETE CASCADE,
    CONSTRAINT fk_compose_navire
        FOREIGN KEY (id_navire) REFERENCES navire(id_navire)
        ON DELETE RESTRICT,
    CONSTRAINT chk_sens
        CHECK (sens IN ('H', 'V'))
);

CREATE TABLE IF NOT EXISTS possede_flottille (
    id_j INTEGER NOT NULL,
    id_flottille INTEGER NOT NULL,
    PRIMARY KEY (id_j, id_flottille),
    CONSTRAINT fk_possede_joueur
        FOREIGN KEY (id_j) REFERENCES humain(id_j)
        ON DELETE CASCADE,
    CONSTRAINT fk_possede_flottille
        FOREIGN KEY (id_flottille) REFERENCES flottille(id_flottille)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cree_par (
    id_virtuel INTEGER PRIMARY KEY,
    id_humain INTEGER NOT NULL,
    date_creation DATE NOT NULL,
    CONSTRAINT fk_cree_par_virtuel
        FOREIGN KEY (id_virtuel) REFERENCES virtuel(id_j)
        ON DELETE CASCADE,
    CONSTRAINT fk_cree_par_humain
        FOREIGN KEY (id_humain) REFERENCES humain(id_j)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS a_pour_distribution (
    id_pi INTEGER NOT NULL,
    code_tc INTEGER NOT NULL,
    pourcentage NUMERIC(5,2) NOT NULL CHECK (pourcentage >= 0 AND pourcentage <= 100),
    PRIMARY KEY (id_pi, code_tc),
    CONSTRAINT fk_distribution_pioche
        FOREIGN KEY (id_pi) REFERENCES pioche(id_pi)
        ON DELETE CASCADE,
    CONSTRAINT fk_distribution_typecarte
        FOREIGN KEY (code_tc) REFERENCES typecarte(code_tc)
        ON DELETE CASCADE
);

-- =========================
-- Index utiles
-- =========================

CREATE INDEX IF NOT EXISTS idx_joueur_pseudo ON joueur(pseudo);
CREATE INDEX IF NOT EXISTS idx_partie_etat ON partie(etat);
CREATE INDEX IF NOT EXISTS idx_pioche_code_partie ON pioche(code_partie);
CREATE INDEX IF NOT EXISTS idx_carte_id_pi_etat_rang ON carte(id_pi, etat, rang);
CREATE INDEX IF NOT EXISTS idx_tir_partie_tour ON tir(code_partie, num_t);

-- =========================
-- Donnees minimales typecarte
-- Compatible avec 2 variantes de schema:
-- 1) code_tc texte (ex: C_MISSILE)
-- 2) code_tc entier auto-genere + nom = code logique
-- =========================

DO $$
DECLARE
    v_type_code_tc TEXT;
BEGIN
    SELECT data_type
    INTO v_type_code_tc
    FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND table_name = 'typecarte'
      AND column_name = 'code_tc';

    IF v_type_code_tc IN ('integer', 'bigint', 'smallint') THEN
        INSERT INTO typecarte (nom, description, image)
        SELECT v.nom, v.description, v.image
        FROM (
            VALUES
                ('C_MISSILE', 'Tir simple sur une case', 'images/c_missile.png'),
                ('C_REJOUE', 'Permet un second tir', 'images/c_rejoue.png'),
                ('C_VIDE', 'Sonde une case sans tir destructif', 'images/c_vide.png'),
                ('C_MPM', 'Deplacement d un navire touche', 'images/c_mpm.png'),
                ('C_LEURRE', 'Place un bateau leurre', 'images/c_leurre.png'),
                ('C_WILLY', 'Effet special Sauvez Willy', 'images/c_willy.png'),
                ('C_MEGA', 'Impact 3x3', 'images/c_mega.png'),
                ('C_ETOILE', 'Impact 5x5', 'images/c_etoile.png'),
                ('C_PASSE', 'Passe le tour', 'images/c_passe.png'),
                ('C_OUPS', 'Impact sur sa propre grille', 'images/c_oups.png')
        ) AS v(nom, description, image)
        WHERE NOT EXISTS (
            SELECT 1
            FROM typecarte t
            WHERE t.nom = v.nom
        );
    ELSE
        INSERT INTO typecarte (code_tc, nom, description, image)
        VALUES
            ('C_MISSILE', 'C_MISSILE', 'Tir simple sur une case', 'images/c_missile.png'),
            ('C_REJOUE', 'C_REJOUE', 'Permet un second tir', 'images/c_rejoue.png'),
            ('C_VIDE', 'C_VIDE', 'Sonde une case sans tir destructif', 'images/c_vide.png'),
            ('C_MPM', 'C_MPM', 'Deplacement d un navire touche', 'images/c_mpm.png'),
            ('C_LEURRE', 'C_LEURRE', 'Place un bateau leurre', 'images/c_leurre.png'),
            ('C_WILLY', 'C_WILLY', 'Effet special Sauvez Willy', 'images/c_willy.png'),
            ('C_MEGA', 'C_MEGA', 'Impact 3x3', 'images/c_mega.png'),
            ('C_ETOILE', 'C_ETOILE', 'Impact 5x5', 'images/c_etoile.png'),
            ('C_PASSE', 'C_PASSE', 'Passe le tour', 'images/c_passe.png'),
            ('C_OUPS', 'C_OUPS', 'Impact sur sa propre grille', 'images/c_oups.png')
        ON CONFLICT (code_tc) DO NOTHING;
    END IF;
END
$$;

COMMIT;
