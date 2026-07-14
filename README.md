# Swanky Apartments — PMS

## Installation

```bash
pip install -r requirements.txt
```

## Lancement

```bash
streamlit run app.py
```

L'application s'ouvre dans ton navigateur (en général sur http://localhost:8501).

## Ce qui a changé par rapport à la version précédente

- **Sécurité par comptes utilisateurs** :
  - Au tout premier lancement, l'application demande de créer un compte **administrateur**
    (nom d'utilisateur + mot de passe). Personne ne peut utiliser l'application sans compte.
  - Chaque utilisateur suivant se connecte avec son propre nom d'utilisateur et mot de passe.
  - Deux rôles : `admin` (peut créer/désactiver des comptes) et `reception` (utilise l'application au quotidien).
  - Les mots de passe ne sont **jamais stockés en clair** : ils sont hachés avec PBKDF2-SHA256
    (200 000 itérations) et un sel unique par compte, dans `auth.py`.
  - Chaque utilisateur peut changer son propre mot de passe depuis la barre latérale.
  - L'administrateur peut créer de nouveaux comptes et désactiver/réactiver des comptes
    existants depuis la barre latérale ("👥 Gestion des utilisateurs").
- **Persistance réelle** : toutes les données (chambres, factures, paramètres) sont
  stockées dans un fichier `swanky_pms.db` (SQLite) créé automatiquement au premier
  lancement, dans le même dossier que `app.py`. Fermer l'application ou redémarrer
  l'ordinateur ne fait rien perdre.
- **Facturation complète** :
  - Calcul automatique de la TVA (taux modifiable dans la barre latérale, 19,25 % par défaut).
  - Numérotation automatique des factures (`FACT-2026-0001`, etc.).
  - Génération d'un **reçu PDF** téléchargeable pour chaque facture.
  - **Historique des factures** avec recherche (client, chambre, numéro), chiffre
    d'affaires cumulé, statut de paiement (Payé / En attente) et export PDF a posteriori.
- **Paramètres** : nom de l'établissement et taux de TVA modifiables sans toucher au code.

## Structure du projet

```
swanky_pms/
├── app.py              → Interface Streamlit (connexion + 3 colonnes + onglets)
├── database.py         → Couche SQLite (chambres, factures, paramètres, utilisateurs)
├── auth.py             → Hachage sécurisé des mots de passe (PBKDF2)
├── pdf_generator.py     → Génération des reçus PDF (fpdf2)
├── requirements.txt
└── swanky_pms.db        → créé automatiquement au premier lancement
```

## Important à savoir sur la connexion

- Si tu perds/oublies le mot de passe admin et qu'il n'y a plus personne pour le
  réinitialiser, il faudra supprimer manuellement la ligne correspondante dans le
  fichier `swanky_pms.db` (table `utilisateurs`) — pense à toujours créer au moins
  deux comptes admin par sécurité.
- La connexion est valable pour la session de navigateur en cours. Si l'onglet est
  fermé ou l'application redémarrée, il faut se reconnecter — c'est volontaire pour
  la sécurité.

## Remarque sur les tests

`database.py` a été testé unitairement (création, statuts, calcul TVA, numérotation,
persistance). `streamlit` et `fpdf2` n'ont pas pu être installés dans l'environnement
de génération (pas d'accès réseau), donc pense à lancer `streamlit run app.py` de ton
côté pour valider l'affichage et la génération des PDF avant mise en production.
