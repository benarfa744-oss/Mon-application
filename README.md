# PMS Hôtelier — Version SaaS multi-établissements

## ⚠️ CHANGEMENT MAJEUR — À lire avant de mettre à jour

Cette version transforme l'application mono-hôtel en plateforme multi-établissements
(plusieurs hôtels clients sur la même installation, chacun avec ses données cloisonnées).

**Le dossier pages/ n'existe plus — remplacé par vues/.** Si tu mets à jour un dépôt existant :Supprime complètementnt** l'ancien dossier pages/ et les 3 fichiers qu'il contenait
2. Crée un nouveau dossier vues/ avec les 5 fichiers listés ci-dessous
3. Remplace app.py, common.py, database.py
4. Remplace requirements.txt (nouvelle version minimale de Streamlit requise)

## Structure du projet (noms EXACTS à respecter)

swanky_pms/
├── app.py                        → Routeur : menu différent selon le rôle (super-admin vs hôtel)
├── bureau_app.pyw                → Lance l'appli en fenêtre native (sans navigateur)
├── lancer_app.bat                → Lance l'appli dans le navigateur (mode simple/debug)
├── assets/
│   ├── logo.png
│   └── icon.ico
├── vues/
│   ├── accueil.py                → Tableau de bord de l'établissement connecté
│   ├── reservations.py           → Planning, création et gestion des réservations
│   ├── chambres.py               → Catégories, check-in/out, + gestion des chambres (ajout/édition/suppression)
│   ├── facturation.py            → Nouvelle facture, historique, exports PDF/Word/Excel
│   └── superadmin.py             → (rôle super_admin uniquement) Gestion des établissements clients et abonnements
├── common.py                     → Authentification, abonnement, barre latérale
├── database.py                   → Couche SQLite multi-établissements
├── auth.py                       → Hachage sécurisé des mots de passe (PBKDF2)
├── pdf_generator.py / docx_generator.py / xlsx_generator.py
├── requirements.txt
└── swanky_pms.db                 → créé/migré automatiquement au premier lancement
## Comment ça marche maintenant

### Rôlesuper_adminin** : toi, l'exploitant de la plateforme. Ne gère aucun hôtel directement — il/elle
  crée les établissements clients, active leur abonnement après paiement Mobile Money, et peut
  suspendre ou supprimer un clientadminin** : administrateur d'un hôtel client précis (ex: le gérant de "Hôtel Le Palmier"). Gère
  ses propres chambres, réservations, factures, et les comptes de son équipereceptionon** : personnel d'un hôtel client, usage quotidien.

### Premier lancement
L'application demande de crun compte super-adminin** (toi). Ensuite, connecte-toi et va d"Gestion des établissements"s"** pour créer ton premier hôtel client (ex: Swanky Apartments,
ou un ami/connaissance à qui tu fais tester) — ça crée en même temps le compte admin de cet hôtel.
Donne ensuite ce nom d'utilisateur/mot de passe à ton client.

### Cycle d'abonnement (paiement manuel Mobile Money)
- Un nouvel établissement démarre avec un sta"Essai"i"** (30 jours par défaut, modifiable).
- Quand le client te paie par Mobile Money, va dans son établissement (panneau super-admin) et
  cli"✅ Paiement reçu (+30 jours)")"** — ça active/prolonge son accès automatiquement.
- S'il ne paie pas, tu peux cliq"⏸️ Suspendre"e"** — ses comptes ne pourront plus se connecter
  tant que tu ne réactives pas.
- Si la date d'expiration est dépassée sans action de ta part, l'accès se bloque automatiquement
  (écran "abonnement inactif" affiché à l'utilisateur, avec juste un bouton de déconnexion).

### Migration de tes données existantes (Swanky Apartments)
Si tu avais déjà une base swanky_pms.db de la version mono-hôtel, elle est migautomatiquement et sans pertete** au premier lancement de cette version : un établissement est
créé pour toi avec toutes tes chambres, réservations, factures et comptes existants. Tu devras
seulement créer, en plus, un compte super-admin distinct (nouveau nom d'utilisateur) pour piloter
la plateforme — ton compte "admin" existant reste l'admin de ton propre hôtel.

## Installation

pip install -r requirements.txt
## Lancementstreamlit run app.py
ou double-clique sur lancer_app.bat / bureau_app.pyw comme avant.

## Hébergement pour un vrai usage SaaS (plusieurs clients, en ligne)

Le mode 100% local (bureau_app.pyw) reste possible, mais si tu veux que **tes clients hôtels
se connectent chacun depuis chez eux via un lien**, il faut un vrai hébergement payant avec disque
persistant (quelques dollars/mois) — le Streamlit Cloud gratuit ne convient pas pour du SaaS
payant (voir la limitation déjà rencontrée : il efface les données après inactivité). Dis-moi
quand tu es prêt pour cette étape, je te guiderai sur le choix et la configuration d'un
hébergeur adapté (ex: une petite VPS, ou une plateforme avec disque persistant).

## Important à savoir

- Les noms d'utilisateur sont uniques sur toute la plateforme (pas seulement par établissement) —
  deux clients différents ne peuvent pas avoir le même nom d'utilisateur.
- Un nouvel établissement peut démarrer avec des chambres d'exemple (modifiables/supprimables) ou
  vide (l'admin ajoute ses propres chambres via la page Chambres → onglet "Gérer les chambres").
- La sauvegarde automatique quotidienne (backups/) couvre maintenant tous les établissements
  dans un seul fichier — elle continue de fonctionner sans changement.

## Remarque sur les tests

Toute la couche database.py a été testée en profondeur dans mon environnement : migration
automatique depuis l'ancien schéma (aucune perte de données), isolation complète entre plusieurs
établissements (chambres, factures, numérotation, utilisateurs), cycle d'abonnement (essai → actif
→ suspendu → expiré), CRUD complet des chambres, suppression en cascade d'un établissement, et
génération des exports Word/Excel avec les bonnes données par établissement. streamlit, fpdf2
et plotly n'ont pas pu être installés dans mon environnement de génération (pas d'accès réseau) —
teste streamlit run app.py de ton côté pour valider l'affichage (notamment le nouveau menu par
rôle) avant mise en production.
