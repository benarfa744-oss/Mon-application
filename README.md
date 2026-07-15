# Swanky Apartments — PMS

## Installation

```bash
pip install -r requirements.txt
```

## Lancement

```bash
streamlit run app.py
```

L'application s'ouvre dans ton navigateur. Un **menu de navigation** apparaît automatiquement
dans la barre latérale (Accueil, Réservations, Chambres, Facturation) — c'est le fonctionnement
standard d'une application Streamlit multi-pages.

## Structure du projet

```
swanky_pms/
├── app.py                        → Page d'accueil / tableau de bord
├── pages/
│   ├── 1_📅_Reservations.py      → Planning (calendrier), création et gestion des réservations
│   ├── 2_🏢_Chambres.py          → Vue par catégorie, check-in/out manuel
│   └── 3_💰_Facturation.py       → Nouvelle facture, historique, exports PDF/Word/Excel
├── common.py                     → Authentification + barre latérale partagées entre les pages
├── database.py                   → Couche SQLite (chambres, réservations, factures, utilisateurs)
├── auth.py                       → Hachage sécurisé des mots de passe (PBKDF2)
├── pdf_generator.py              → Génération des reçus PDF (fpdf2)
├── docx_generator.py             → Génération des reçus Word (python-docx)
├── xlsx_generator.py             → Génération des reçus + historique Excel (openpyxl)
├── requirements.txt
└── swanky_pms.db                 → créé automatiquement au premier lancement
```

## Ce qui a été ajouté dans cette version

- **Module Réservations complet** : calendrier visuel (planning façon Gantt), création de
  réservations avec dates d'arrivée/départ, détection automatique des chevauchements de
  dates (impossible de réserver une chambre déjà prise sur la période), champs société /
  téléphone / code client, check-in et check-out directement liés à la réservation.
- **Exports Word et Excel** des factures, en plus du PDF déjà existant. Un bouton d'export
  Excel de l'historique complet est aussi disponible dans l'onglet Historique.
- **Authentification par comptes** (admin / réception), mots de passe hachés (PBKDF2-SHA256).
- **Calcul TVA aligné sur la pratique du secteur** : le tarif saisi est le prix TTC (celui
  payé par le client), le HT et la TVA sont calculés par extraction, comme sur un reçu
  hôtelier classique.
- **Persistance complète** dans `swanky_pms.db` (chambres, réservations, factures, comptes,
  paramètres).

## Utilisation 100% hors-ligne, gratuite, à vie

L'application est déjà conçue pour ça — rien n'appelle internet une fois installée
(base de données locale, calculs, génération PDF/Word/Excel). Il n'y a **aucun abonnement,
aucune licence, aucun service payant** : Streamlit et toutes les bibliothèques utilisées sont
gratuites et open source.

⚠️ Attention à une confusion possible : si l'application est accédée via un lien
**Streamlit Community Cloud** (`....streamlit.app`), *ça* nécessite internet, car c'est hébergé
en ligne. Pour un fonctionnement garanti sans connexion, il faut lancer l'application
**directement sur l'ordinateur de la réception**, en local.

### Installation en une fois (avec internet, chez toi ou n'importe où)

```bash
pip install -r requirements.txt
```

### Utilisation quotidienne (sans internet, sur l'ordinateur de la réception)

**Windows** : double-clique simplement sur `lancer_app.bat` — l'application démarre et
s'ouvre automatiquement dans le navigateur, sans avoir besoin d'ouvrir un terminal.

**Mac / Linux** :
```bash
streamlit run app.py
```

### Si l'ordinateur de la réception n'a jamais accès à internet (même pas pour l'installation)

1. Sur un autre ordinateur qui a internet, dans le dossier du projet, lance :
   ```bash
   pip download -r requirements.txt -d offline_packages
   ```
   Cela télécharge tous les fichiers d'installation dans un dossier `offline_packages/`.
2. Copie tout le dossier du projet (y compris `offline_packages/`) sur une clé USB.
3. Sur l'ordinateur de la réception (sans internet), lance :
   ```bash
   pip install --no-index --find-links=offline_packages -r requirements.txt
   ```
4. Ensuite, lance l'application normalement (`lancer_app.bat` ou `streamlit run app.py`) —
   elle n'aura plus jamais besoin d'internet.

## Important à savoir

- Au tout premier lancement (ou si la base ne contient encore aucun compte), l'application
  demande de créer un compte administrateur avant de laisser accéder à quoi que ce soit.
- Crée au moins deux comptes admin par sécurité (voir "Gestion des utilisateurs" dans la
  barre latérale, réservé aux admins).
- Le module Réservations et le statut "Occupé/Disponible" des chambres sont maintenant liés :
  le check-in d'une réservation occupe la chambre, le check-out la libère. Pour un client de
  passage sans réservation préalable, utilise l'onglet "Check-in / Check-out manuel" de la
  page Chambres.
- Les extras (petit-déjeuner, bar, restaurant, etc.) vus sur ton reçu de référence ne sont
  pas encore implémentés (sur ta demande) — dis-moi si tu veux les ajouter plus tard.

## Remarque sur les tests

Tout a été testé unitairement et en scénario complet dans mon environnement : création de
comptes, réservations (y compris détection de chevauchement de dates), check-in/check-out,
calcul TVA, génération Word et Excel (contenu vérifié). `streamlit`, `fpdf2` et `plotly`
n'ont pas pu être installés dans mon environnement de génération (pas d'accès réseau) — pense
à lancer `streamlit run app.py` de ton côté pour valider l'affichage (notamment le graphique
de planning) avant mise en production.
