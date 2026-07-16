import streamlit as st
import common

st.set_page_config(page_title="PMS Hôtelier", layout="wide", page_icon="assets/logo_64.png")

user = common.garantir_authentification()
common.afficher_sidebar(user)

if user["role"] == "super_admin":
    pg = st.navigation([
        st.Page("vues/superadmin.py", title="Gestion des établissements", icon="🏢", default=True),
    ])
else:
    pg = st.navigation([
        st.Page("vues/accueil.py", title="Accueil", icon="🏨", default=True),
        st.Page("vues/reservations.py", title="Réservations", icon="📅"),
        st.Page("vues/chambres.py", title="Chambres", icon="🏢"),
        st.Page("vues/facturation.py", title="Facturation", icon="💰"),
    ])

pg.run()
