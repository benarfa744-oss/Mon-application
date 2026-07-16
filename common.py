"""
Fonctions partagées par toutes les pages de l'application (authentification,
barre latérale, mise en forme). Chaque page appelle garantir_authentification()
en tout premier, avant d'afficher quoi que ce soit d'autre.
"""

import streamlit as st
from datetime import datetime
import database as db

db.init_db()
db.sauvegarder_base_si_necessaire()


def fmt_fcfa(valeur):
    return f"{valeur:,.0f}".replace(",", " ") + " FCFA"


def _afficher_ecran_creation_super_admin():
    st.image("assets/logo.png", width=110)
    st.title("PMS Hôtelier — Multi-établissements")
    st.subheader("🔐 Configuration initiale de la plateforme")
    st.info("Aucun compte super-administrateur n'existe encore. Ce compte est le tien "
             "(l'exploitant de la plateforme) — il te permettra de créer et gérer les "
             "établissements clients (hôtels), pas de gérer un hôtel en particulier.")
    with st.form("form_setup_super_admin"):
        username = st.text_input("Nom d'utilisateur (super-admin)")
        p1 = st.text_input("Mot de passe", type="password")
        p2 = st.text_input("Confirmer le mot de passe", type="password")
        submit = st.form_submit_button("Créer le compte super-administrateur", type="primary")
        if submit:
            if not username.strip() or not p1:
                st.error("Merci de renseigner un nom d'utilisateur et un mot de passe.")
            elif len(p1) < 6:
                st.error("Le mot de passe doit contenir au moins 6 caractères.")
            elif p1 != p2:
                st.error("Les deux mots de passe ne correspondent pas.")
            elif db.username_existe(username):
                st.error("Ce nom d'utilisateur existe déjà.")
            else:
                db.creer_utilisateur(username, p1, role="super_admin", etablissement_id=None)
                st.success("Compte super-administrateur créé avec succès. Connecte-toi ci-dessous.")
                st.rerun()


def _afficher_ecran_connexion():
    st.image("assets/logo.png", width=110)
    st.title("PMS Hôtelier")
    st.subheader("🔐 Connexion")
    with st.form("form_login"):
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submit = st.form_submit_button("Se connecter", type="primary")
        if submit:
            user = db.verifier_identifiants(username, password)
            if user:
                st.session_state.auth_user = user
                st.rerun()
            else:
                st.error("Nom d'utilisateur ou mot de passe incorrect.")


def _afficher_ecran_abonnement_inactif(user, etab):
    st.image("assets/logo.png", width=110)
    st.title(etab["nom"] if etab else "Établissement")
    st.error("⛔ L'abonnement de cet établissement n'est plus actif.")
    if etab and etab["statut_abonnement"] == "Suspendu":
        st.write("Le compte a été suspendu. Contacte l'administrateur de la plateforme pour le réactiver.")
    else:
        st.write(f"La période d'essai ou l'abonnement a expiré "
                 f"(date d'expiration : {etab['date_expiration'] if etab else '—'}). "
                 f"Merci de régulariser le paiement pour continuer à utiliser l'application.")
    if st.button("🚪 Se déconnecter"):
        st.session_state.auth_user = None
        st.rerun()


def garantir_authentification():
    """
    À appeler en tout premier sur chaque page. Gère la création du compte
    super-admin (une seule fois), la connexion, et le blocage si l'abonnement
    de l'établissement n'est plus actif. Retourne le dict de l'utilisateur connecté.
    """
    if "auth_user" not in st.session_state:
        st.session_state.auth_user = None

    if db.compter_super_admins() == 0:
        _afficher_ecran_creation_super_admin()
        st.stop()

    if st.session_state.auth_user is None:
        _afficher_ecran_connexion()
        st.stop()

    user = st.session_state.auth_user

    if user["role"] != "super_admin":
        etab = db.get_etablissement(user["etablissement_id"])
        if not db.etablissement_actif(user["etablissement_id"]):
            _afficher_ecran_abonnement_inactif(user, etab)
            st.stop()

    return user


def afficher_sidebar(user):
    """Affiche le compte connecté, le changement de mot de passe, et (pour les
    admins d'établissement) les paramètres et la gestion des comptes de leur hôtel."""
    with st.sidebar:
        st.image("assets/logo.png", width=70)

        if user["role"] == "super_admin":
            st.markdown(f"👤 Connecté : **{user['username']}** (super-admin plateforme)")
        else:
            etab = db.get_etablissement(user["etablissement_id"])
            nom_etab = etab["nom"] if etab else "—"
            st.markdown(f"🏨 **{nom_etab}**")
            st.markdown(f"👤 Connecté : **{user['username']}** ({user['role']})")

        if st.button("🚪 Se déconnecter"):
            st.session_state.auth_user = None
            st.rerun()

        with st.expander("🔑 Changer mon mot de passe"):
            cur_pwd = st.text_input("Mot de passe actuel", type="password", key="cur_pwd")
            new_pwd1 = st.text_input("Nouveau mot de passe", type="password", key="new_pwd1")
            new_pwd2 = st.text_input("Confirmer le nouveau mot de passe", type="password", key="new_pwd2")
            if st.button("Mettre à jour le mot de passe"):
                verif = db.verifier_identifiants(user["username"], cur_pwd)
                if not verif:
                    st.error("Mot de passe actuel incorrect.")
                elif len(new_pwd1) < 6:
                    st.error("Le nouveau mot de passe doit contenir au moins 6 caractères.")
                elif new_pwd1 != new_pwd2:
                    st.error("Les deux nouveaux mots de passe ne correspondent pas.")
                else:
                    db.changer_mot_de_passe(user["username"], new_pwd1)
                    st.success("Mot de passe mis à jour.")

        if user["role"] == "admin":
            etab_id = user["etablissement_id"]

            with st.expander("⚙️ Paramètres de l'établissement"):
                etab = db.get_etablissement(etab_id)
                nouveau_nom = st.text_input("Nom de l'établissement", value=etab["nom"], key="param_nom")
                nouveau_taux = st.number_input("Taux de TVA (%)", min_value=0.0, max_value=100.0,
                                                value=float(etab["taux_tva"]), step=0.25, key="param_taux")
                if st.button("💾 Enregistrer les paramètres"):
                    db.maj_parametres_etablissement(etab_id, nom=nouveau_nom, taux_tva=nouveau_taux)
                    st.success("Paramètres enregistrés.")
                    st.rerun()

            with st.expander("👥 Gestion des utilisateurs"):
                st.markdown("**Créer un nouveau compte**")
                new_username = st.text_input("Nom d'utilisateur", key="new_user_username")
                new_password = st.text_input("Mot de passe", type="password", key="new_user_password")
                new_role = st.selectbox("Rôle", ["reception", "admin"], key="new_user_role")
                if st.button("➕ Créer le compte"):
                    if not new_username.strip() or not new_password:
                        st.warning("Nom d'utilisateur et mot de passe requis.")
                    elif len(new_password) < 6:
                        st.warning("Le mot de passe doit contenir au moins 6 caractères.")
                    elif db.username_existe(new_username):
                        st.warning("Ce nom d'utilisateur existe déjà.")
                    else:
                        db.creer_utilisateur(new_username, new_password, role=new_role, etablissement_id=etab_id)
                        st.success(f"Compte {new_username} créé.")
                        st.rerun()

                st.markdown("---")
                st.markdown("**Comptes existants**")
                for u in db.lister_utilisateurs(etab_id):
                    colu1, colu2 = st.columns([2, 1])
                    statut = "🟢 Actif" if u["actif"] else "🔴 Désactivé"
                    colu1.write(f"**{u['username']}**  \n{u['role']} — {statut}")
                    if u["username"] != user["username"]:
                        label = "Désactiver" if u["actif"] else "Réactiver"
                        if colu2.button(label, key=f"toggle_{u['username']}"):
                            db.set_actif_utilisateur(u["username"], not u["actif"])
                            st.rerun()

        st.markdown("---")
        st.caption("💡 Toutes les données sont sauvegardées automatiquement "
                   "dans le fichier `swanky_pms.db`.")
        
