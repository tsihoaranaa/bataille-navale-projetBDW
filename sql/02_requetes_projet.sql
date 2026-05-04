-- ============================================================
-- Auteurs : GERGES Robin, RAONIMANANA Aaron
-- Ensemble des requêtes SQL du projet
-- Ce fichier sert de référence pour les requêtes demandées et utilisées.
-- Paramètres : :pseudo, :id_joueur, :code_partie, :niveau, :delta_mois
-- ============================================================

-- ===========================================================
-- A) Requetes de consultation (demandes du projet)
-- ===========================================================

-- 1) Liste des joueurs
SELECT id_j, pseudo
FROM joueur
ORDER BY id_j;

-- 2) Parties jouees par un joueur (humain ou virtuel)
SELECT p.code_partie, p.date_creation, p.heure_creation, p.etat
FROM partie p
JOIN joue_reel jr ON jr.code_partie = p.code_partie
WHERE jr.id_humain = :id_joueur
UNION
SELECT p.code_partie, p.date_creation, p.heure_creation, p.etat
FROM partie p
JOIN joue_virt jv ON jv.code_partie = p.code_partie
WHERE jv.id_virtuel = :id_joueur
ORDER BY code_partie;

-- 3) Scores finaux des joueurs humains
SELECT h.nom, h.prenom, jr.score_final
FROM humain h
JOIN joue_reel jr ON jr.id_humain = h.id_j
ORDER BY jr.score_final DESC, h.nom, h.prenom;

-- 4) Tirs d un joueur dans une partie
SELECT t.num_ti, t.coord_x, t.coord_y, t.etat
FROM tir t
WHERE t.id_j = :id_joueur
  AND t.code_partie = :code_partie
ORDER BY t.num_ti;

-- 5) Joueurs virtuels par niveau
SELECT j.id_j, j.pseudo, v.niveau_expertise
FROM joueur j
JOIN virtuel v ON v.id_j = j.id_j
WHERE v.niveau_expertise = :niveau
ORDER BY j.pseudo;

-- 6) Cartes disponibles
SELECT code_tc, nom, description, image
FROM typecarte
ORDER BY code_tc;

-- 7) Parties en cours/suspendues d un joueur connecte
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
WHERE LOWER(TRIM(p.etat)) IN ('en cours', 'suspendue')
  AND j.pseudo = :pseudo
ORDER BY p.date_creation DESC, p.heure_creation DESC;

-- 8) Informations de base d une partie
SELECT p.code_partie, p.date_creation, p.heure_creation, p.etat,
     COALESCE(
       (SELECT MAX(t.num_t) FROM tour t WHERE t.code_partie = p.code_partie),
       0
     ) AS nb_tours
FROM partie p
WHERE p.code_partie = :code_partie;

-- ===========================================================
-- B) Requetes operationnelles (utilisees par l application)
-- ===========================================================

-- Authentification / profil
SELECT *
FROM joueur
WHERE pseudo = :pseudo;

-- Primitives generiques utilitaires
-- Note: nom de table/colonne dynamiques a proteger via psycopg.sql.Identifier en Python.
SELECT *
FROM :table_name;

SELECT COUNT(*) AS nb
FROM :table_name;

SELECT *
FROM :table_name
WHERE :column_name ILIKE :motif;

-- Creation joueur humain
INSERT INTO joueur (pseudo)
VALUES (:pseudo)
RETURNING id_j;

INSERT INTO humain (id_j, nom, prenom, date_naissance)
VALUES (:id_joueur, :nom, :prenom, :date_naissance);

-- Creation joueur virtuel
INSERT INTO joueur (pseudo)
VALUES (:pseudo_virtuel)
RETURNING id_j;

INSERT INTO virtuel (id_j, niveau_expertise)
VALUES (:id_joueur, :niveau);

-- Creation partie
SELECT COALESCE(MAX(code_partie), 0) + 1 AS next_code_partie
FROM partie;

INSERT INTO partie (code_partie, date_creation, heure_creation, etat)
VALUES (:code_partie, CURRENT_DATE, CURRENT_TIME, 'En cours');

INSERT INTO joue_reel (code_partie, id_humain, score_final)
VALUES (:code_partie, :id_humain, 0);

INSERT INTO joue_virt (code_partie, id_virtuel)
VALUES (:code_partie, :id_virtuel);

-- Gestion etat partie
UPDATE partie
SET etat = :etat
WHERE code_partie = :code_partie;

-- Gestion pioche
INSERT INTO pioche (nom_distrib, code_partie)
VALUES ('Distribution initiale', :code_partie)
RETURNING id_pi;

SELECT id_pi
FROM pioche
WHERE code_partie = :code_partie
ORDER BY id_pi DESC
LIMIT 1;

INSERT INTO carte (id_pi, code_tc, etat, rang)
VALUES (:id_pi, :code_tc, 'dans_pioche', :rang);

SELECT c.id_c, tc.code_tc, tc.nom, tc.description, tc.image
FROM carte c
JOIN typecarte tc ON tc.code_tc = c.code_tc
WHERE c.id_pi = :id_pi
  AND c.etat = 'dans_pioche'
ORDER BY c.rang ASC
LIMIT 1;

-- Version exacte utilisee dans l application (avec ctid)
SELECT c.ctid AS _ctid, c.id_c, tc.code_tc, tc.nom, tc.description, tc.image
FROM carte c
JOIN typecarte tc ON tc.code_tc = c.code_tc
WHERE c.id_pi = :id_pi
  AND c.etat = 'dans_pioche'
ORDER BY c.rang ASC
LIMIT 1;

SELECT ctid
FROM carte
WHERE id_pi = :id_pi;

UPDATE carte
SET etat = 'dans_pioche',
    rang = :rang
WHERE ctid = :ctid;

UPDATE carte
SET etat = 'utilisee'
WHERE id_c = :id_c;

UPDATE carte
SET etat = 'utilisee'
WHERE ctid = :ctid;

-- Tour / tirs
INSERT INTO tir (coord_x, coord_y, id_j, id_c, code_partie, num_t)
VALUES (:coord_x, :coord_y, :id_joueur, :id_c, :code_partie, :num_t);

UPDATE tour
SET nb_coules_j1 = :nb_coules_j1,
    nb_touches_j1 = :nb_touches_j1,
    nb_coules_j2 = :nb_coules_j2,
    nb_touches_j2 = :nb_touches_j2
WHERE code_partie = :code_partie
  AND num_t = :num_t;

INSERT INTO tour (code_partie, num_t, nb_coules_j1, nb_touches_j1, nb_coules_j2, nb_touches_j2)
VALUES (:code_partie, :num_t, :nb_coules_j1, :nb_touches_j1, :nb_coules_j2, :nb_touches_j2);

-- Sauvegarde/restauration snapshot
INSERT INTO partie_snapshot (code_partie, state_json, updated_at)
VALUES (:code_partie, :state_json, CURRENT_TIMESTAMP)
ON CONFLICT (code_partie)
DO UPDATE SET
    state_json = EXCLUDED.state_json,
    updated_at = CURRENT_TIMESTAMP;

SELECT state_json
FROM partie_snapshot
WHERE code_partie = :code_partie;

-- Recuperation ids joueurs pour une partie
SELECT jr.id_humain AS id_humain, jv.id_virtuel AS id_virtuel
FROM partie p
LEFT JOIN joue_reel jr ON jr.code_partie = p.code_partie
LEFT JOIN joue_virt jv ON jv.code_partie = p.code_partie
WHERE p.code_partie = :code_partie
LIMIT 1;

-- Recuperation adversaire pour affichage dans le jeu
SELECT j.pseudo, v.niveau_expertise
FROM joue_virt jv
JOIN virtuel v ON v.id_j = jv.id_virtuel
JOIN joueur j ON j.id_j = jv.id_virtuel
WHERE jv.code_partie = :code_partie;

-- Mise a jour score final en fin de partie
UPDATE joue_reel
SET score_final = :score_final
WHERE code_partie = :code_partie
  AND id_humain = :id_humain;

-- ===========================================================
-- C) Classements
-- ===========================================================

-- IJH: Classement individuel joueurs humains (sans filtre periode)
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
ORDER BY score_cumule DESC, nb_parties DESC, j.pseudo ASC;

-- IJH: avec filtre sur les :delta_mois derniers mois
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
WHERE p.date_creation >= (CURRENT_DATE - (:delta_mois || ' months')::interval)
GROUP BY j.pseudo, h.nom, h.prenom
ORDER BY score_cumule DESC, nb_parties DESC, j.pseudo ASC;

-- CPP: Classement par pavillon (si tables pavillon/flottille alimentees)
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
ORDER BY score_cumule DESC, nb_parties DESC, pv.code_pays ASC;

-- CPP: avec filtre sur les :delta_mois derniers mois
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
  AND p.date_creation >= (CURRENT_DATE - (:delta_mois || ' months')::interval)
GROUP BY pv.code_pays, pv.nom_pays
ORDER BY score_cumule DESC, nb_parties DESC, pv.code_pays ASC;
