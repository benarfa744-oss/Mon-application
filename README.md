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
├── app.py              → Interface Streamlit (3 colonnes + onglets)
├── database.py         → Couche SQLite (chambres, factures, paramètres)
├── pdf_generator.py     → Génération des reçus PDF (fpdf2)
├── requirements.txt
└── swanky_pms.db        → créé automatiquement au premier lancement
```

## Remarque sur les tests

`database.py` a été testé unitairement (création, statuts, calcul TVA, numérotation,
persistance). `streamlit` et `fpdf2` n'ont pas pu être installés dans l'environnement
de génération (pas d'accès réseau), donc pense à lancer `streamlit run app.py` de ton
côté pour valider l'affichage et la génération des PDF avant mise en production.
