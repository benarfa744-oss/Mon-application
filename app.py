import streamlit as st
import pandas as pd
from datetime import datetime, date

import database as db
import common

st.set_page_config(page_title="Swanky Apartments - PMS", layout="wide", page_icon="🏨")

user = common.garantir_authentification()

NOM_ETABLISSEMENT = db.get_parametre("nom_etablissement", "Swanky Apartments")

common.afficher_sidebar(user)

# --- EN-TÊTE ---
st.title(f"🏨 {NOM_ETABLISSEMENT} — PMS")
st.caption(f"Système de Gestion Hôtelière | Connecté en tant que **{user['username']}** "
           f"({user['role']}) | Date système : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
st.markdown("---")

st.info("👈 Utilise le menu à gauche pour naviguer : **Réservations** (planning et création "
        "de réservations), **Chambres** (statuts et check-in/out), **Facturation** (nouvelle "
        "facture et historique).")

# --- CHARGEMENT DES DONNÉES ---
chambres = db.get_toutes_chambres()
df = pd.DataFrame(chambres)
reservations = db.get_toutes_reservations()
factures = db.get_toutes_factures()

today = date.today().isoformat()

# --- INDICATEURS CLÉS ---
col1, col2, col3, col4 = st.columns(4)

dispos = df[df['statut'] == "Disponible"]
occupes = df[df['statut'] == "Occupé"]
taux_occupation = (len(occupes) / len(df) * 100) if len(df) > 0 else 0

col1.metric("Chambres disponibles", len(dispos))
col2.metric("Chambres occupées", len(occupes))
col3.metric("Taux d'occupation", f"{taux_occupation:.0f} %")

arrivees_jour = [r for r in reservations if r['date_arrivee'] == today and r['statut'] == 'Confirmée']
col4.metric("Arrivées prévues aujourd'hui", len(arrivees_jour))

st.markdown("---")

col_gauche, col_droite = st.columns([1.3, 1.7])

# ==========================================
# COLONNE GAUCHE : ÉTAT DES CHAMBRES
# ==========================================
with col_gauche:
    st.subheader("📋 État des Chambres")

    st.success(f"🟢 Disponibles ({len(dispos)})")
    for _, r in dispos.iterrows():
        st.text(f"  • {r['nom']} ({r['type']})")

    st.error(f"🔴 Occupées ({len(occupes)})")
    for _, r in occupes.iterrows():
        st.text(f"  • {r['nom']} → {r['client']}")

# ==========================================
# COLONNE DROITE : ARRIVÉES / DÉPARTS DU JOUR
# ==========================================
with col_droite:
    st.subheader("📅 Mouvements du jour")

    depart_jour = [r for r in reservations if r['date_depart'] == today and r['statut'] == 'En cours']

    st.markdown("**Arrivées prévues aujourd'hui**")
    if not arrivees_jour:
        st.caption("Aucune arrivée prévue aujourd'hui.")
    for r in arrivees_jour:
        st.write(f"🛬 **{r['client']}** — {r['chambre_nom']} ({r['numero_reservation']})")

    st.markdown("**Départs prévus aujourd'hui**")
    if not depart_jour:
        st.caption("Aucun départ prévu aujourd'hui.")
    for r in depart_jour:
        st.write(f"🛫 **{r['client']}** — {r['chambre_nom']} ({r['numero_reservation']})")

    st.markdown("---")
    st.markdown("**Dernières factures**")
    if not factures:
        st.caption("Aucune facture enregistrée pour le moment.")
    for f in factures[:3]:
        icone = "✅" if f['statut_paiement'] == "Payé" else "⏳"
        st.write(f"{icone} {f['numero_facture']} — {f['client']} — {common.fmt_fcfa(f['montant_ttc'])}")
        
