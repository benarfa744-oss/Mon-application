import streamlit as st
import pandas as pd

import database as db
import common

st.set_page_config(page_title="Chambres - Swanky Apartments", layout="wide", page_icon="🏢")

user = common.garantir_authentification()
common.afficher_sidebar(user)

st.title("🏢 Chambres")
st.markdown("---")

chambres = db.get_toutes_chambres()
df = pd.DataFrame(chambres)

tab_categories, tab_gestion = st.tabs(["🗂️ Vue par Catégorie", "⚡ Check-in / Check-out manuel"])

# ==========================================
# VUE PAR CATÉGORIE
# ==========================================
with tab_categories:
    categories = df['type'].unique()
    for cat in categories:
        rooms_cat = df[df['type'] == cat]
        total_cat = len(rooms_cat)
        dispo_cat = len(rooms_cat[rooms_cat['statut'] == "Disponible"])

        with st.expander(f"📂 {cat} ({dispo_cat}/{total_cat} dispos) — "
                          f"Standard : {common.fmt_fcfa(rooms_cat['tarif'].iloc[0])} TTC"):
            for _, room in rooms_cat.iterrows():
                badge = "🟢" if room['statut'] == "Disponible" else f"🔴 ({room['client']})"
                st.write(f"**{room['nom']}** | Étage: {room['etage']} | Statut: {badge}")

# ==========================================
# CHECK-IN / CHECK-OUT MANUEL (sans passer par une réservation planifiée)
# ==========================================
with tab_gestion:
    st.caption("💡 Pour un séjour déjà planifié dans le module Réservations, utilise plutôt "
               "les boutons Check-in / Check-out de cette réservation. Cette section sert "
               "pour les passages client sans réservation préalable.")

    st.markdown("### Modifier le statut d'une chambre")
    selected_room_name = st.selectbox("Choisir la chambre", df['nom'].unique(), key="select_gestion")
    chambre_actuelle = db.get_chambre(selected_room_name)

    nouveau_statut = st.radio(
        "Nouveau Statut", ["Disponible", "Occupé"],
        index=0 if chambre_actuelle['statut'] == "Disponible" else 1
    )
    nom_client = st.text_input("Nom du client (si occupée)", value=chambre_actuelle['client'])

    if st.button("Mettre à jour le statut"):
        db.maj_statut_chambre(selected_room_name, nouveau_statut, nom_client)
        st.success(f"Statut de {selected_room_name} mis à jour.")
        st.rerun()
