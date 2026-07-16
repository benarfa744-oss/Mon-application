import streamlit as st
from datetime import datetime

import database as db
import common

user = common.garantir_authentification()
common.afficher_sidebar(user)

if user["role"] != "super_admin":
    st.error("Accès réservé au super-administrateur de la plateforme.")
    st.stop()

st.title("🏢 Gestion des établissements clients")
st.markdown("---")

tab_liste, tab_nouveau = st.tabs(["📋 Établissements existants", "➕ Nouvel établissement"])

with tab_liste:
    etablissements = db.lister_etablissements()

    if not etablissements:
        st.info("Aucun établissement créé pour le moment. Utilise l'onglet "
                 "'➕ Nouvel établissement' pour ajouter ton premier client.")
    else:
        aujourdhui = datetime.now().strftime("%Y-%m-%d")
        for etab in etablissements:
            actif = db.etablissement_actif(etab["id"])
            if not actif:
                icone = "🔴"
            elif etab["statut_abonnement"] == "Essai":
                icone = "🟡"
            else:
                icone = "🟢"

            expire_bientot = ""
            if etab["date_expiration"]:
                jours_restants = (datetime.strptime(etab["date_expiration"], "%Y-%m-%d") - datetime.now()).days
                if 0 <= jours_restants <= 5:
                    expire_bientot = f" ⚠️ expire dans {jours_restants} jour(s)"

            with st.expander(f"{icone} {etab['nom']} — {etab['statut_abonnement']}{expire_bientot}"):
                utilisateurs = db.lister_utilisateurs(etab["id"])
                chambres = db.get_toutes_chambres(etab["id"])
                factures = db.get_toutes_factures(etab["id"])

                c1, c2 = st.columns(2)
                c1.write(f"Téléphone contact : {etab['telephone_contact'] or '—'}")
                c1.write(f"Taux de TVA : {etab['taux_tva']:g}%")
                c1.write(f"Créé le : {etab['date_creation'][:10]}")
                c2.write(f"Statut abonnement : {etab['statut_abonnement']}")
                c2.write(f"Expire le : {etab['date_expiration'] or '—'}")
                c2.write(f"Comptes utilisateurs : {len(utilisateurs)} | "
                         f"Chambres : {len(chambres)} | Factures : {len(factures)}")

                st.markdown("---")
                st.markdown("Actions sur l'abonnement")
                colb1, colb2, colb3 = st.columns(3)

                if colb1.button("✅ Paiement reçu (+30 jours)", key=f"payer_{etab['id']}"):
                    db.maj_abonnement(etab["id"], "Actif", jours_supplementaires=30)
                    st.success(f"Abonnement de {etab['nom']} prolongé de 30 jours et activé.")
                    st.rerun()

                if colb2.button("⏸️ Suspendre", key=f"suspendre_{etab['id']}"):
                    db.maj_abonnement(etab["id"], "Suspendu")
                    st.warning(f"{etab['nom']} suspendu — leurs comptes ne pourront plus se connecter.")
                    st.rerun()

                with colb3.popover("🗑️ Supprimer"):
                    st.write(f"Supprimer {etab['nom']} et toutes ses données "
                             f"(chambres, réservations, {len(factures)} facture(s), "
                             f"{len(utilisateurs)} compte(s)) ? Cette action est irréversible.")
                    if st.button("Confirmer la suppression définitive", key=f"confirm_del_{etab['id']}"):
                        db.supprimer_etablissement(etab["id"])
                        st.success(f"{etab['nom']} supprimé.")
                        st.rerun()

                st.markdown("---")
                st.markdown("Comptes utilisateurs de cet établissement")
                if not utilisateurs:
                    st.caption("Aucun compte créé pour cet établissement.")
                for u in utilisateurs:
                    statut_u = "🟢 Actif" if u["actif"] else "🔴 Désactivé"
                    st.write(f"• {u['username']} — {u['role']} — {statut_u}")

with tab_nouveau:
    st.markdown("### Créer un nouvel établissement client")col1, col2 = st.columns(2)
    with col1:
        nom_etab = st.text_input("Nom de l'établissement", key="new_etab_nom")
        telephone_contact = st.text_input("Téléphone de contact (Mobile Money)", key="new_etab_tel")
        taux_tva = st.number_input("Taux de TVA (%)", min_value=0.0, max_value=100.0,
                                    value=db.TAUX_TVA_DEFAUT, step=0.25, key="new_etab_tva")
    with col2:
        jours_essai = st.number_input("Durée de l'essai gratuit (jours)", min_value=0, value=30, key="new_etab_essai")
        avec_demo = st.checkbox("Ajouter des chambres d'exemple pour démarrer rapidement", value=True, key="new_etab_demo")

    st.markdown("---")
    st.markdown("Premier compte administrateur de cet établissement")
    col3, col4 = st.columns(2)
    with col3:
        admin_username = st.text_input("Nom d'utilisateur", key="new_etab_admin_user")
    with col4:
        admin_password = st.text_input("Mot de passe", type="password", key="new_etab_admin_pwd")

    if st.button("🏢 Créer l'établissement", type="primary"):
        if not nom_etab.strip():
            st.warning("Le nom de l'établissement est requis.")
        elif not admin_username.strip() or not admin_password:
            st.warning("Le nom d'utilisateur et le mot de passe de l'admin sont requis.")
        elif len(admin_password) < 6:
            st.warning("Le mot de passe doit contenir au moins 6 caractères.")
        elif db.username_existe(admin_username):
            st.warning("Ce nom d'utilisateur existe déjà (les noms d'utilisateur sont uniques sur toute la plateforme).")
        else:
            etab_id = db.creer_etablissement(
                nom_etab.strip(), telephone_contact.strip(), taux_tva, jours_essai, avec_demo
            )
            db.creer_utilisateur(admin_username, admin_password, role="admin", etablissement_id=etab_id)
            st.success(f"Établissement '{nom_etab}' créé avec succès, avec le compte admin '{admin_username}'.")
            st.rerun()
