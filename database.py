"""
Couche d'accès aux données (SQLite) pour Swanky Apartments PMS.
Toutes les données (chambres, factures) sont persistées dans un fichier
swanky_pms.db qui reste sur le disque entre deux lancements de l'application.
"""

import sqlite3
from datetime import datetime
from contextlib import contextmanager

DB_PATH = "swanky_pms.db"

# Données initiales des chambres (utilisées uniquement au tout premier lancement)
CHAMBRES_INITIALES = [
    ("MIAMI", "STD VIP USA", 85000, "Disponible", "", "Etage 1"),
    ("LAS-VEGAS", "STD VIP USA", 85000, "Disponible", "", "Etage 2"),
    ("NEW YORK", "STD VIP USA", 85000, "Disponible", "", "Etage 2"),
    ("ACCRA", "APPT AFRIQ", 120000, "Disponible", "", "Etage 1"),
    ("DOUALA", "APPT AFRIQ", 120000, "Occupé", "RAMANAN DILAI", "Etage 1"),
    ("ISTANBUL", "STD EUROPE", 65000, "Disponible", "", "Etage 0"),
    ("MADRID", "STD EUROPE", 65000, "Disponible", "", "Etage 0"),
    ("PARIS", "STD EUROPE", 65000, "Disponible", "", "Etage 1"),
    ("LONDRES", "STD EUROPE", 65000, "Occupé", "BEIDI WAFFA", "Etage 1"),
    ("BERLIN", "CH EUROPE", 45000, "Disponible", "", "Etage 2"),
    ("BRUXELLES", "CH EUROPE", 45000, "Disponible", "", "Etage 2"),
    ("ROME", "CH EUROPE", 45000, "Occupé", "SILA HERVE", "Etage 2"),
    ("VENISE", "CH EUROPE", 45000, "Occupé", "DJABIR OUBIR", "Etage 2"),
    ("DAKAR", "STD AFRIQ", 55000, "Disponible", "", "Etage 2"),
    ("LAGOS", "STD AFRIQ", 55000, "Disponible", "", "Etage 2"),
    ("BANGKOK", "STD ASIE", 55000, "Disponible", "", "Etage 2"),
    ("JAKARTA", "STD ASIE", 55000, "Disponible", "", "Etage 2"),
    ("PEKIN", "APPT ASIE", 120000, "Disponible", "", "Etage 1"),
    ("SEOUL", "APPT ASIE", 120000, "Occupé", "KAMGUE TAKOUGAN", "Etage 1"),
]

TAUX_TVA_DEFAUT = 19.25  # % — modifiable dans les paramètres de l'application


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Crée les tables si elles n'existent pas et alimente les chambres de base."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chambres (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                tarif INTEGER NOT NULL,
                statut TEXT NOT NULL DEFAULT 'Disponible',
                client TEXT DEFAULT '',
                etage TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS factures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_facture TEXT UNIQUE NOT NULL,
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
                notes TEXT DEFAULT ''
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS parametres (
                cle TEXT PRIMARY KEY,
                valeur TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS utilisateurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'reception',
                actif INTEGER NOT NULL DEFAULT 1,
                date_creation TEXT NOT NULL
            )
        """)

        # Seed des chambres uniquement si la table est vide
        cur = conn.execute("SELECT COUNT(*) AS n FROM chambres")
        if cur.fetchone()["n"] == 0:
            conn.executemany(
                "INSERT INTO chambres (nom, type, tarif, statut, client, etage) VALUES (?, ?, ?, ?, ?, ?)",
                CHAMBRES_INITIALES
            )

        # Seed du taux de TVA par défaut
        cur = conn.execute("SELECT valeur FROM parametres WHERE cle = 'taux_tva'")
        if cur.fetchone() is None:
            conn.execute("INSERT INTO parametres (cle, valeur) VALUES ('taux_tva', ?)", (str(TAUX_TVA_DEFAUT),))

        cur = conn.execute("SELECT valeur FROM parametres WHERE cle = 'nom_etablissement'")
        if cur.fetchone() is None:
            conn.execute("INSERT INTO parametres (cle, valeur) VALUES ('nom_etablissement', ?)", ("Swanky Apartments",))


# ---------- CHAMBRES ----------

def get_toutes_chambres():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM chambres ORDER BY etage, type, nom").fetchall()
        return [dict(r) for r in rows]


def maj_statut_chambre(nom, statut, client=""):
    with get_connection() as conn:
        conn.execute(
            "UPDATE chambres SET statut = ?, client = ? WHERE nom = ?",
            (statut, client if statut == "Occupé" else "", nom)
        )


def get_chambre(nom):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM chambres WHERE nom = ?", (nom,)).fetchone()
        return dict(row) if row else None


# ---------- FACTURES ----------

def generer_numero_facture():
    """Génère un numéro de facture séquentiel du type FACT-2026-0001."""
    annee = datetime.now().strftime("%Y")
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT COUNT(*) AS n FROM factures WHERE numero_facture LIKE ?",
            (f"FACT-{annee}-%",)
        )
        n = cur.fetchone()["n"] + 1
        return f"FACT-{annee}-{n:04d}"


def creer_facture(chambre_nom, chambre_type, client, nuitees, tarif_unitaire,
                   taux_tva, statut_paiement="Payé", mode_paiement="Espèces", notes=""):
    # Le tarif appliqué est le prix TTC affiché/payé par nuitée (pratique hôtelière
    # standard : le client voit et paie ce montant, la TVA en est extraite ensuite).
    montant_ttc = int(round(tarif_unitaire * nuitees))
    montant_ht = int(round(montant_ttc / (1 + taux_tva / 100)))
    montant_tva = montant_ttc - montant_ht
    numero = generer_numero_facture()
    date_creation = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO factures (
                numero_facture, date_creation, chambre_nom, chambre_type, client,
                nuitees, tarif_unitaire, montant_ht, taux_tva, montant_tva, montant_ttc,
                statut_paiement, mode_paiement, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (numero, date_creation, chambre_nom, chambre_type, client, nuitees,
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


def get_toutes_factures():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM factures ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


def get_facture_par_numero(numero):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM factures WHERE numero_facture = ?", (numero,)).fetchone()
        return dict(row) if row else None


def maj_statut_paiement(numero, statut):
    with get_connection() as conn:
        conn.execute("UPDATE factures SET statut_paiement = ? WHERE numero_facture = ?", (statut, numero))


# ---------- PARAMÈTRES ----------

def get_parametre(cle, defaut=None):
    with get_connection() as conn:
        row = conn.execute("SELECT valeur FROM parametres WHERE cle = ?", (cle,)).fetchone()
        return row["valeur"] if row else defaut


def set_parametre(cle, valeur):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO parametres (cle, valeur) VALUES (?, ?) "
            "ON CONFLICT(cle) DO UPDATE SET valeur = excluded.valeur",
            (cle, str(valeur))
        )


# ---------- UTILISATEURS (authentification) ----------

def compter_utilisateurs():
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) AS n FROM utilisateurs").fetchone()["n"]


def username_existe(username):
    with get_connection() as conn:
        row = conn.execute("SELECT 1 FROM utilisateurs WHERE username = ?", (username.strip(),)).fetchone()
        return row is not None


def creer_utilisateur(username, password, role="reception"):
    """Crée un compte utilisateur. Le mot de passe est haché avant stockage."""
    from auth import hash_password
    pwd_hash, salt = hash_password(password)
    date_creation = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO utilisateurs (username, password_hash, salt, role, actif, date_creation) "
            "VALUES (?, ?, ?, ?, 1, ?)",
            (username.strip(), pwd_hash, salt, role, date_creation)
        )


def verifier_identifiants(username, password):
    """Retourne le dict utilisateur si les identifiants sont valides et le compte actif, sinon None."""
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


def lister_utilisateurs():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, username, role, actif, date_creation FROM utilisateurs ORDER BY username"
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
        
