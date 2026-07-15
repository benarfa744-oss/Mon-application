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


def _afficher_ecran_premiere_configuration():
    st.title("🏨 Swanky Apartments — PMS")
    st.subheader("🔐 Configuration initiale")
    st.info("Aucun compte n'existe encore sur cette installation. Crée le premier "
             "compte — il sera administrateur et pourra ensuite créer les comptes "
             "des autres membres de l'équipe.")
    with st.form("form_setup_admin"):
        username = st.text_input("Nom d'utilisateur")
        p1 = st.text_input("Mot de passe", type="password")
        p2 = st.text_input("Confirmer le mot de passe", type="password")
        submit = st.form_submit_button("Créer le compte administrateur", type="primary")
        if submit:
            if not username.strip() or not p1:
                st.error("Merci de renseigner un nom d'utilisateur et un mot de passe.")
            elif len(p1) < 6:
                st.error("Le mot de passe doit contenir au moins 6 caractères.")
            elif p1 != p2:
                st.error("Les deux mots de passe ne correspondent pas.")
            else:
                db.creer_utilisateur(username, p1, role="admin")
                st.success("Compte administrateur créé avec succès. Connecte-toi ci-dessous.")
                st.rerun()


def _afficher_ecran_connexion():
    st.title("🏨 Swanky Apartments — PMS")
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


def garantir_authentification():
    """
    À appeler en tout premier sur chaque page. Affiche l'écran de configuration
    initiale ou de connexion si nécessaire (et arrête l'exécution de la page avec
    st.stop()), sinon retourne le dict de l'utilisateur connecté.
    """
    if "auth_user" not in st.session_state:
        st.session_state.auth_user = None

    if db.compter_utilisateurs() == 0:
        _afficher_ecran_premiere_configuration()
        st.stop()

    if st.session_state.auth_user is None:
        _afficher_ecran_connexion()
        st.stop()

    return st.session_state.auth_user


def afficher_sidebar(user):
    """Affiche le compte connecté, le changement de mot de passe, les paramètres
    et (pour les admins) la gestion des comptes utilisateurs. À appeler sur
    chaque page, après garantir_authentification()."""
    with st.sidebar:
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
            with st.expander("⚙️ Paramètres de l'établissement"):
                nom_actuel = db.get_parametre("nom_etablissement", "Swanky Apartments")
                taux_actuel = float(db.get_parametre("taux_tva", db.TAUX_TVA_DEFAUT))
                nouveau_nom = st.text_input("Nom de l'établissement", value=nom_actuel, key="param_nom")
                nouveau_taux = st.number_input("Taux de TVA (%)", min_value=0.0, max_value=100.0,
                                                value=taux_actuel, step=0.25, key="param_taux")
                if st.button("💾 Enregistrer les paramètres"):
                    db.set_parametre("nom_etablissement", nouveau_nom)
                    db.set_parametre("taux_tva", nouveau_taux)
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
                        db.creer_utilisateur(new_username, new_password, role=new_role)
                        st.success(f"Compte {new_username} créé.")
                        st.rerun()

                st.markdown("---")
                st.markdown("**Comptes existants**")
                for u in db.lister_utilisateurs():
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
        
