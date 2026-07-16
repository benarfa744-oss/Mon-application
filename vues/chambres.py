import streamlit as st
import pandas as pd

import database as db
import common

user = common.garantir_authentification()
common.afficher_sidebar(user)
etab_id = user["etablissement_id"]

st.title("🏢 Chambres")
st.markdown("---")

chambres = db.get_toutes_chambres(etab_id)
df = pd.DataFrame(chambres)

onglets = ["🗂️ Vue par Catégorie", "⚡ Check-in / Check-out manuel"]
if user["role"] == "admin":
    onglets.append("🛠️ Gérer les chambres")

tabs = st.tabs(onglets)
tab_categories, tab_gestion = tabs[0], tabs[1]
tab_crud = tabs[2] if user["role"] == "admin" else None

with tab_categories:
    if df.empty:
        st.info("Aucune chambre configurée pour le moment."
                + (" Utilise l'onglet Gérer les chambres pour en ajouter." if user["role"] == "admin" else " Contacte ton administrateur pour en ajouter."))
    else:
        categories = df['type'].unique()
        for cat in categories:
            rooms_cat = df[df['type'] == cat]
            total_cat = len(rooms_cat)
            dispo_cat = len(rooms_cat[rooms_cat['statut'] == "Disponible"])

            with st.expander(f"📂 {cat} ({dispo_cat}/{total_cat} dispos) — "
                              f"Standard : {common.fmt_fcfa(rooms_cat['tarif'].iloc[0])} TTC"):
                for _, room in rooms_cat.iterrows():
                    badge = "🟢" if room['statut'] == "Disponible" else f"🔴 ({room['client']})"
                    st.write(f"{room['nom']} | Étage: {room['etage']} | Statut: {badge}")

with tab_gestion:
    if df.empty:
        st.info("Aucune chambre configurée pour le moment.")
    else:
        st.caption("💡 Pour un séjour déjà planifié dans le module Réservations, utilise plutôt "
                   "les boutons Check-in / Check-out de cette réservation. Cette section sert "
                   "pour les passages client sans réservation préalable.")

        st.markdown("### Modifier le statut d'une chambre")
        selected_room_name = st.selectbox("Choisir la chambre", df['nom'].unique(), key="select_gestion")
        chambre_actuelle = db.get_chambre(etab_id, selected_room_name)

        nouveau_statut = st.radio(
            "Nouveau Statut", ["Disponible", "Occupé"],
            index=0 if chambre_actuelle['statut'] == "Disponible" else 1
        )
        nom_client = st.text_input("Nom du client (si occupée)", value=chambre_actuelle['client'])

        if st.button("Mettre à jour le statut"):
            db.maj_statut_chambre(etab_id, selected_room_name, nouveau_statut, nom_client)
            st.success(f"Statut de {selected_room_name} mis à jour.")
            st.rerun()

if tab_crud is not None:
    with tab_crud:
        st.markdown("### ➕ Ajouter une nouvelle chambre")
        col1, col2 = st.columns(2)
        with col1:
            nouveau_nom = st.text_input("Nom de la chambre", key="crud_nouveau_nom")
            nouveau_type = st.text_input("Type / catégorie", key="crud_nouveau_type",
                                          help="Ex: STD EUROPE, Suite, Chambre Standard...")
        with col2:
            nouveau_tarif = st.number_input("Tarif par nuitée (FCFA, TTC)", min_value=0, step=5000, key="crud_nouveau_tarif")
            nouvel_etage = st.text_input("Étage (optionnel)", key="crud_nouvel_etage")

        if st.button("➕ Ajouter la chambre", type="primary"):
            if not nouveau_nom.strip() or not nouveau_type.strip():
                st.warning("Le nom et le type de la chambre sont requis.")
            elif db.nom_chambre_existe(etab_id, nouveau_nom):
                st.warning(f"Une chambre nommée '{nouveau_nom}' existe déjà.")
            else:
                db.ajouter_chambre(etab_id, nouveau_nom, nouveau_type, nouveau_tarif, nouvel_etage)
                st.success(f"Chambre '{nouveau_nom}' ajoutée avec succès.")
                st.rerun()

        st.markdown("---")
        st.markdown("### ✏️ Modifier ou supprimer une chambre existante")if df.empty:
            st.caption("Aucune chambre à modifier pour le moment.")
        else:
            chambre_a_modifier = st.selectbox("Choisir la chambre à modifier", df['nom'].unique(), key="crud_select_modif")
            c = db.get_chambre(etab_id, chambre_a_modifier)
            chambre_id = c["id"]

            col1, col2 = st.columns(2)
            with col1:
                modif_nom = st.text_input("Nom", value=c["nom"], key="crud_modif_nom")
                modif_type = st.text_input("Type / catégorie", value=c["type"], key="crud_modif_type")
            with col2:
                modif_tarif = st.number_input("Tarif par nuitée (FCFA, TTC)", value=int(c["tarif"]),
                                               step=5000, key="crud_modif_tarif")
                modif_etage = st.text_input("Étage", value=c["etage"] or "", key="crud_modif_etage")

            colb1, colb2 = st.columns(2)
            if colb1.button("💾 Enregistrer les modifications"):
                if not modif_nom.strip() or not modif_type.strip():
                    st.warning("Le nom et le type sont requis.")
                elif db.nom_chambre_existe(etab_id, modif_nom, exclure_id=chambre_id):
                    st.warning(f"Une autre chambre nommée '{modif_nom}' existe déjà.")
                else:
                    db.modifier_chambre(chambre_id, modif_nom, modif_type, modif_tarif, modif_etage)
                    st.success("Chambre modifiée avec succès.")
                    st.rerun()

            if colb2.button("🗑️ Supprimer cette chambre"):
                if c["statut"] == "Occupé":
                    st.error("Impossible de supprimer une chambre actuellement occupée. "
                             "Libère-la d'abord (check-out).")
                else:
                    db.supprimer_chambre(chambre_id)
                    st.success(f"Chambre '{modif_nom}' supprimée.")
                    st.rerun()
