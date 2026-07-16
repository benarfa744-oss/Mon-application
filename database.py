"""
Couche d'accès aux données (SQLite) pour le PMS multi-établissements.
Chaque hôtel client (établissement) a ses propres chambres, réservations,
factures et utilisateurs, cloisonnés par etablissement_id. Un rôle spécial
'super_admin' (toi, l'exploitant du SaaS) gère la liste des établissements
et leur statut d'abonnement.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from contextlib import contextmanager

DB_PATH = "swanky_pms.db"

CHAMBRES_DEMO = [
    ("MIAMI", "STD VIP USA", 85000, "Disponible", "", "Etage 1"),
    ("LAS-VEGAS", "STD VIP USA", 85000, "Disponible", "", "Etage 2"),
    ("PARIS", "STD EUROPE", 65000, "Disponible", "", "Etage 1"),
    ("LONDRES", "STD EUROPE", 65000, "Disponible", "", "Etage 1"),
    ("BERLIN", "CH EUROPE", 45000, "Disponible", "", "Etage 2"),
    ("DAKAR", "STD AFRIQ", 55000, "Disponible", "", "Etage 2"),
]

TAUX_TVA_DEFAUT = 19.25
JOURS_ESSAI_DEFAUT = 30


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _colonne_existe(conn, table, colonne):
    cols = [r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    return colonne in cols


def _table_existe(conn, table):
    r = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return r is not None


def init_db():
    with get_connection() as conn:
        migration_necessaire = _table_existe(conn, "chambres") and not _colonne_existe(conn, "chambres", "etablissement_id")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS etablissements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                telephone_contact TEXT DEFAULT '',
                taux_tva REAL NOT NULL DEFAULT 19.25,
                statut_abonnement TEXT NOT NULL DEFAULT 'Essai',
                date_expiration TEXT,
                date_creation TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS chambres (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                etablissement_id INTEGER,
                nom TEXT NOT NULL,
                type TEXT NOT NULL,
                tarif INTEGER NOT NULL,
                statut TEXT NOT NULL DEFAULT 'Disponible',
                client TEXT DEFAULT '',
                etage TEXT,
                UNIQUE(etablissement_id, nom)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS factures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                etablissement_id INTEGER,
                numero_facture TEXT NOT NULL,
                date_creation TEXT NOT NULL,
                chambre_nom TEXT NOT NULL,
                chambre_type TEXT,
                client TEXT NOT NULL,
                nuitees INTEGER NOT NULL,
                tarif_unitaire INTEGER NOT NULL,
                montant_ht INTEGER NOT NULL,
                taux_tva REAL NOT NULL,
                montant_tva INTEGER NOT NULL,
                montant_ttc INTEGER NOT NULL,
                statut_paiement TEXT DEFAULT 'Payé',
                mode_paiement TEXT DEFAULT 'Espèces',
                notes TEXT DEFAULT '',
                UNIQUE(etablissement_id, numero_facture)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS utilisateurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                etablissement_id INTEGER,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'reception',
                actif INTEGER NOT NULL DEFAULT 1,
                date_creation TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                etablissement_id INTEGER,
                numero_reservation TEXT NOT NULL,
                chambre_nom TEXT NOT NULL,
                chambre_type TEXT,
                client TEXT NOT NULL,
                telephone TEXT DEFAULT '',
                societe TEXT DEFAULT '',
                code_client TEXT DEFAULT '',
                date_arrivee TEXT NOT NULL,
                date_depart TEXT NOT NULL,
                nb_personnes INTEGER NOT NULL DEFAULT 1,
                tarif_nuit INTEGER NOT NULL,
                statut TEXT NOT NULL DEFAULT 'Confirmée',
                notes TEXT DEFAULT '',
                date_creation TEXT NOT NULL,
                UNIQUE(etablissement_id, numero_reservation)
            )
        """)

        if migration_necessaire:
            _migrer_vers_multi_etablissements(conn)


def _migrer_vers_multi_etablissements(conn):
    nom_existant = "Mon Établissement"
    taux_existant = TAUX_TVA_DEFAUT
    if _table_existe(conn, "parametres"):
        r = conn.execute("SELECT valeur FROM parametres WHERE cle='nom_etablissement'").fetchone()
        if r:
            nom_existant = r["valeur"]
        r2 = conn.execute("SELECT valeur FROM parametres WHERE cle='taux_tva'").fetchone()
        if r2:
            taux_existant = float(r2["valeur"])

    date_creation = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute(
        "INSERT INTO etablissements (nom, telephone_contact, taux_tva, statut_abonnement, date_expiration, date_creation) "
        "VALUES (?, '', ?, 'Actif', NULL, ?)",
        (nom_existant, taux_existant, date_creation)
    )
    etab_id = cur.lastrowid

    for table in ("chambres", "factures", "utilisateurs", "reservations"):
        if not _colonne_existe(conn, table, "etablissement_id"):
            conn.execute(f"ALTER TABLE {table} ADD COLUMN etablissement_id INTEGER")
        conn.execute(f"UPDATE {table} SET etablissement_id = ? WHERE etablissement_id IS NULL", (etab_id,))


# ---------- ÉTABLISSEMENTS ----------

def creer_etablissement(nom, telephone_contact="", taux_tva=None, jours_essai=JOURS_ESSAI_DEFAUT, avec_chambres_demo=True):
    if taux_tva is None:
        taux_tva = TAUX_TVA_DEFAUT
    date_creation = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_expiration = (datetime.now() + timedelta(days=jours_essai)).strftime("%Y-%m-%d")

    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO etablissements (nom, telephone_contact, taux_tva, statut_abonnement, date_expiration, date_creation) "
            "VALUES (?, ?, ?, 'Essai', ?, ?)",
            (nom.strip(), telephone_contact.strip(), taux_tva, date_expiration, date_creation)
        )
        etab_id = cur.lastrowid

        if avec_chambres_demo:
            conn.executemany(
                "INSERT INTO chambres (etablissement_id, nom, type, tarif, statut, client, etage) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                [(etab_id,) + chambre for chambre in CHAMBRES_DEMO]
            )
    return etab_id


def lister_etablissements():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM etablissements ORDER BY nom").fetchall()
        return [dict(r) for r in rows]


def get_etablissement(etablissement_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM etablissements WHERE id = ?", (etablissement_id,)).fetchone()
        return dict(row) if row else None


def maj_abonnement(etablissement_id, statut, jours_supplementaires=None):
    with get_connection() as conn:
        if jours_supplementaires is not None:
            nouvelle_date = (datetime.now() + timedelta(days=jours_supplementaires)).strftime("%Y-%m-%d")
            conn.execute(
                "UPDATE etablissements SET statut_abonnement = ?, date_expiration = ? WHERE id = ?",
                (statut, nouvelle_date, etablissement_id)
            )
        else:
            conn.execute(
                "UPDATE etablissements SET statut_abonnement = ? WHERE id = ?",
                (statut, etablissement_id)
            )


def maj_parametres_etablissement(etablissement_id, nom=None, taux_tva=None, telephone_contact=None):
    with get_connection() as conn:
        if nom is not None:
            conn.execute("UPDATE etablissements SET nom = ? WHERE id = ?", (nom, etablissement_id))
        if taux_tva is not None:
            conn.execute("UPDATE etablissements SET taux_tva = ? WHERE id = ?", (taux_tva, etablissement_id))
        if telephone_contact is not None:
            conn.execute("UPDATE etablissements SET telephone_contact = ? WHERE id = ?", (telephone_contact, etablissement_id))


def etablissement_actif(etablissement_id):
    etab = get_etablissement(etablissement_id)
    if etab is None:
        return False
    if etab["statut_abonnement"] not in ("Actif", "Essai"):
        return False
    if etab["date_expiration"]:
        aujourdhui = datetime.now().strftime("%Y-%m-%d")
        if etab["date_expiration"] < aujourdhui:
            return False
    return True


def supprimer_etablissement(etablissement_id):
    with get_connection() as conn:
        for table in ("chambres", "factures", "reservations", "utilisateurs"):
            conn.execute(f"DELETE FROM {table} WHERE etablissement_id = ?", (etablissement_id,))
        conn.execute("DELETE FROM etablissements WHERE id = ?", (etablissement_id,))


# ---------- CHAMBRES ----------

def get_toutes_chambres(etablissement_id):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM chambres WHERE etablissement_id = ? ORDER BY etage, type, nom",
            (etablissement_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def maj_statut_chambre(etablissement_id, nom, statut, client=""):
    with get_connection() as conn:
        conn.execute(
            "UPDATE chambres SET statut = ?, client = ? WHERE etablissement_id = ? AND nom = ?",
            (statut, client if statut == "Occupé" else "", etablissement_id, nom)
        )


def get_chambre(etablissement_id, nom):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM chambres WHERE etablissement_id = ? AND nom = ?", (etablissement_id, nom)
        ).fetchone()
        return dict(row) if row else None


def ajouter_chambre(etablissement_id, nom, type_chambre, tarif, etage=""):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO chambres (etablissement_id, nom, type, tarif, statut, client, etage) "
            "VALUES (?, ?, ?, ?, 'Disponible', '', ?)",
            (etablissement_id, nom.strip(), type_chambre.strip(), tarif, etage.strip())
        )


def modifier_chambre(chambre_id, nom, type_chambre, tarif, etage):
    with get_connection() as conn:
        conn.execute(
            "UPDATE chambres SET nom = ?, type = ?, tarif = ?, etage = ? WHERE id = ?",
            (nom.strip(), type_chambre.strip(), tarif, etage.strip(), chambre_id)
        )


def supprimer_chambre(chambre_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM chambres WHERE id = ?", (chambre_id,))


def nom_chambre_existe(etablissement_id, nom, exclure_id=None):
    query = "SELECT 1 FROM chambres WHERE etablissement_id = ? AND nom = ?"
    params = [etablissement_id, nom.strip()]
    if exclure_id is not None:
        query += " AND id != ?"
        params.append(exclure_id)
    with get_connection() as conn:
        return conn.execute(query, params).fetchone() is not None


# ---------- FACTURES ----------

def generer_numero_facture(etablissement_id):
    annee = datetime.now().strftime("%Y")
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT COUNT(*) AS n FROM factures WHERE etablissement_id = ? AND numero_facture LIKE ?",
            (etablissement_id, f"FACT-{annee}-%")
        )
        n = cur.fetchone()["n"] + 1
        return f"FACT-{annee}-{n:04d}"


def creer_facture(etablissement_id, chambre_nom, chambre_type, client, nuitees, tarif_unitaire,
                   taux_tva, statut_paiement="Payé", mode_paiement="Espèces", notes=""):
    montant_ttc = int(round(tarif_unitaire * nuitees))
    montant_ht = int(round(montant_ttc / (1 + taux_tva / 100)))
    montant_tva = montant_ttc - montant_ht
    numero = generer_numero_facture(etablissement_id)
    date_creation = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO factures (
                etablissement_id, numero_facture, date_creation, chambre_nom, chambre_type, client,
                nuitees, tarif_unitaire, montant_ht, taux_tva, montant_tva, montant_ttc,
                statut_paiement, mode_paiement, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (etablissement_id, numero, date_creation, chambre_nom, chambre_type, client, nuitees,
              tarif_unitaire, montant_ht, taux_tva, montant_tva, montant_ttc,
              statut_paiement, mode_paiement, notes))

    return {
        "numero_facture": numero,
        "date_creation": date_creation,
        "chambre_nom": chambre_nom,
        "chambre_type": chambre_type,
        "client": client,
        "nuitees": nuitees,
        "tarif_unitaire": tarif_unitaire,
        "montant_ht": montant_ht,
        "taux_tva": taux_tva,
        "montant_tva": montant_tva,
        "montant_ttc": montant_ttc,
        "statut_paiement": statut_paiement,
        "mode_paiement": mode_paiement,
        "notes": notes,
    }


def get_toutes_factures(etablissement_id):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM factures WHERE etablissement_id = ? ORDER BY id DESC", (etablissement_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_facture_par_numero(etablissement_id, numero):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM factures WHERE etablissement_id = ? AND numero_facture = ?",
            (etablissement_id, numero)
        ).fetchone()
        return dict(row) if row else None


def maj_statut_paiement(etablissement_id, numero, statut):
    with get_connection() as conn:
        conn.execute(
            "UPDATE factures SET statut_paiement = ? WHERE etablissement_id = ? AND numero_facture = ?",
            (statut, etablissement_id, numero)
        )


# ---------- UTILISATEURS ----------

def compter_utilisateurs():
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) AS n FROM utilisateurs").fetchone()["n"]


def compter_super_admins():
    with get_connection() as conn:
        return conn.execute(
            "SELECT COUNT(*) AS n FROM utilisateurs WHERE role = 'super_admin'"
        ).fetchone()["n"]


def username_existe(username):
    with get_connection() as conn:
        row = conn.execute("SELECT 1 FROM utilisateurs WHERE username = ?", (username.strip(),)).fetchone()
        return row is not None


def creer_utilisateur(username, password, role="reception", etablissement_id=None):
    from auth import hash_password
    pwd_hash, salt = hash_password(password)
    date_creation = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO utilisateurs (etablissement_id, username, password_hash, salt, role, actif, date_creation) "
            "VALUES (?, ?, ?, ?, ?, 1, ?)",
            (etablissement_id, username.strip(), pwd_hash, salt, role, date_creation)
        )


def verifier_identifiants(username, password):
    from auth import verify_password
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM utilisateurs WHERE username = ? AND actif = 1",
            (username.strip(),)
        ).fetchone()
    if row is None:
        return None
    if verify_password(password, row["salt"], row["password_hash"]):
        return dict(row)
    return None


def lister_utilisateurs(etablissement_id):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, username, role, actif, date_creation FROM utilisateurs "
            "WHERE etablissement_id = ? ORDER BY username",
            (etablissement_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def set_actif_utilisateur(username, actif):
    with get_connection() as conn:
        conn.execute("UPDATE utilisateurs SET actif = ? WHERE username = ?", (1 if actif else 0, username))


def changer_mot_de_passe(username, nouveau_password):
    from auth import hash_password
    pwd_hash, salt = hash_password(nouveau_password)
    with get_connection() as conn:
        conn.execute(
            "UPDATE utilisateurs SET password_hash = ?, salt = ? WHERE username = ?",
            (pwd_hash, salt, username)
        )


# ---------- RÉSERVATIONS ----------

def generer_numero_reservation(etablissement_id):
    annee = datetime.now().strftime("%Y")
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT COUNT(*) AS n FROM reservations WHERE etablissement_id = ? AND numero_reservation LIKE ?",
            (etablissement_id, f"RES-{annee}-%")
        )
        n = cur.fetchone()["n"] + 1
        return f"RES-{annee}-{n:04d}"


def chambre_disponible_periode(etablissement_id, chambre_nom, date_arrivee, date_depart, exclure_reservation_id=None):
    query = """
        SELECT COUNT(*) AS n FROM reservations
        WHERE etablissement_id = ? AND chambre_nom = ?
          AND statut IN ('Confirmée', 'En cours')
          AND date_arrivee < ?
          AND date_depart > ?
    """
    params = [etablissement_id, chambre_nom, date_depart, date_arrivee]
    if exclure_reservation_id is not None:
        query += " AND id != ?"
        params.append(exclure_reservation_id)
    with get_connection() as conn:
        n = conn.execute(query, params).fetchone()["n"]
        return n == 0


def creer_reservation(etablissement_id, chambre_nom, chambre_type, client, date_arrivee, date_depart,
                       tarif_nuit, telephone="", societe="", code_client="",
                       nb_personnes=1, notes=""):
    numero = generer_numero_reservation(etablissement_id)
    date_creation = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO reservations (
                etablissement_id, numero_reservation, chambre_nom, chambre_type, client, telephone,
                societe, code_client, date_arrivee, date_depart, nb_personnes,
                tarif_nuit, statut, notes, date_creation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Confirmée', ?, ?)
        """, (etablissement_id, numero, chambre_nom, chambre_type, client, telephone, societe, code_client,
              date_arrivee, date_depart, nb_personnes, tarif_nuit, notes, date_creation))
    return numero


def get_toutes_reservations(etablissement_id):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM reservations WHERE etablissement_id = ? ORDER BY date_arrivee",
            (etablissement_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_reservation(reservation_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM reservations WHERE id = ?", (reservation_id,)).fetchone()
        return dict(row) if row else None


def maj_statut_reservation(reservation_id, statut):
    with get_connection() as conn:
        conn.execute("UPDATE reservations SET statut = ? WHERE id = ?", (statut, reservation_id))


def effectuer_checkin(reservation_id):
    resa = get_reservation(reservation_id)
    if resa is None:
        return False
    maj_statut
