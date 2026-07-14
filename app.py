import streamlit as st
import pandas as pd
from datetime import datetime

import database as db
from pdf_generator import generer_pdf_facture

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Swanky Apartments - PMS", layout="wide", page_icon="🏨")

# --- INITIALISATION DE LA BASE DE DONNÉES (persistante entre les sessions) ---
db.init_db()

NOM_ETABLISSEMENT = db.get_parametre("nom_etablissement", "Swanky Apartments")
TAUX_TVA = float(db.get_parametre("taux_tva", db.TAUX_TVA_DEFAUT))


def fmt_fcfa(valeur):
    return f"{valeur:,.0f}".replace(",", " ") + " FCFA"


# --- EN-TÊTE ---
st.title(f"🏨 {NOM_ETABLISSEMENT} — PMS")
st.caption(f"Système de Gestion Hôtelière | Connecté en tant que Réceptionniste | "
           f"Date système : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
st.markdown("---")

# --- BARRE LATÉRALE : PARAMÈTRES ---
with st.sidebar:
    st.header("⚙️ Paramètres")
    nouveau_nom = st.text_input("Nom de l'établissement", value=NOM_ETABLISSEMENT)
    nouveau_taux = st.number_input("Taux de TVA (%)", min_value=0.0, max_value=100.0,
                                    value=TAUX_TVA, step=0.25)
    if st.button("💾 Enregistrer les paramètres"):
        db.set_parametre("nom_etablissement", nouveau_nom)
        db.set_parametre("taux_tva", nouveau_taux)
        st.success("Paramètres enregistrés.")
        st.rerun()

    st.markdown("---")
    st.caption("💡 Toutes les données (chambres, factures) sont sauvegardées "
               "automatiquement dans le fichier `swanky_pms.db`.")

# --- CHARGEMENT DES DONNÉES ---
chambres = db.get_toutes_chambres()
df = pd.DataFrame(chambres)

# --- ARCHITECTURE EN 3 COLONNES ---
col_gauche, col_centre, col_droite = st.columns([1.2, 2.5, 1.5])

# ==========================================
# COLONNE GAUCHE : STATUTS EN TEMPS RÉEL
# ==========================================
with col_gauche:
    st.subheader("📋 État des Chambres")

    dispos = df[df['statut'] == "Disponible"]
    occupes = df[df['statut'] == "Occupé"]

    st.success(f"🟢 Disponibles ({len(dispos)})")
    for _, r in dispos.iterrows():
        st.text(f"  • {r['nom']} ({r['type']})")

    st.error(f"🔴 Occupées ({len(occupes)})")
    for _, r in occupes.iterrows():
        st.text(f"  • {r['nom']} → {r['client']}")

    st.markdown("---")
    taux_occupation = (len(occupes) / len(df) * 100) if len(df) > 0 else 0
    st.metric("Taux d'occupation", f"{taux_occupation:.0f} %")

# ==========================================
# COLONNE CENTRALE : VUE PAR TYPE & FILTRES
# ==========================================
with col_centre:
    st.subheader("🗂️ Répartition et Affectations")

    tab_types, tab_gestion = st.tabs(["Vue par Catégorie", "⚡ Check-in / Check-out"])

    with tab_types:
        categories = df['type'].unique()
        for cat in categories:
            rooms_cat = df[df['type'] == cat]
            total_cat = len(rooms_cat)
            dispo_cat = len(rooms_cat[rooms_cat['statut'] == "Disponible"])

            with st.expander(f"📂 {cat} ({dispo_cat}/{total_cat} dispos) — "
                              f"Standard : {fmt_fcfa(rooms_cat['tarif'].iloc[0])}"):
                for _, room in rooms_cat.iterrows():
                    badge = "🟢" if room['statut'] == "Disponible" else f"🔴 ({room['client']})"
                    st.write(f"**{room['nom']}** | Étage: {room['etage']} | Statut: {badge}")

    with tab_gestion:
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

# ==========================================
# COLONNE DROITE : MODULE FACTURATION COMPLET
# ==========================================
with col_droite:
    st.subheader("💰 Module Facturation")

    tab_nouvelle, tab_historique = st.tabs(["🧾 Nouvelle facture", "📜 Historique"])

    # ---------- NOUVELLE FACTURE ----------
    with tab_nouvelle:
        room_facture = st.selectbox("Chambre à facturer", df['nom'].unique(), key="facture_room")
        room_data = db.get_chambre(room_facture)
        tarif_de_base = room_data['tarif']

        client_facture = st.text_input(
            "Nom du client",
            value=room_data['client'] if room_data['statut'] == "Occupé" else "",
            key="client_facture"
        )

        nuitees = st.number_input("Nombre de nuitées", min_value=1, value=1, step=1, key="nuitees_facture")

        tarif_applique = st.number_input(
            "Tarif par nuitée appliqué (FCFA)",
            value=int(tarif_de_base),
            step=5000,
            help=f"Tarif standard : {fmt_fcfa(tarif_de_base)}. Modifiez ce montant si un prix "
                 f"dégressif a été accordé."
        )

        mode_paiement = st.selectbox("Mode de paiement", ["Espèces", "Mobile Money", "Carte bancaire", "Virement"])
        statut_paiement = st.radio("Statut du paiement", ["Payé", "En attente"], horizontal=True)
        notes_facture = st.text_area("Notes (optionnel)", height=68)

        # Calcul en direct
        montant_ht = tarif_applique * nuitees
        montant_tva = round(montant_ht * TAUX_TVA / 100)
        montant_ttc = montant_ht + montant_tva

        st.markdown("---")
        c1, c2 = st.columns(2)
        c1.metric("Total HT", fmt_fcfa(montant_ht))
        c2.metric(f"TVA ({TAUX_TVA:g}%)", fmt_fcfa(montant_tva))
        st.markdown(f"### **Total TTC : {fmt_fcfa(montant_ttc)}**")
        st.caption(f"Calculé sur la base de {nuitees} nuit(s) à {fmt_fcfa(tarif_applique)}/nuit.")

        if st.button("🖨️ Générer la facture", type="primary"):
            if not client_facture.strip():
                st.warning("Merci d'indiquer le nom du client avant de générer la facture.")
            else:
                facture = db.creer_facture(
                    chambre_nom=room_facture,
                    chambre_type=room_data['type'],
                    client=client_facture.strip(),
                    nuitees=nuitees,
                    tarif_unitaire=tarif_applique,
                    taux_tva=TAUX_TVA,
                    statut_paiement=statut_paiement,
                    mode_paiement=mode_paiement,
                    notes=notes_facture.strip(),
                )
                st.session_state["derniere_facture"] = facture
                st.success(f"Facture {facture['numero_facture']} enregistrée avec succès !")

        # Bouton de téléchargement pour la dernière facture générée dans cette session
        if "derniere_facture" in st.session_state:
            f = st.session_state["derniere_facture"]
            pdf_bytes = generer_pdf_facture(f, NOM_ETABLISSEMENT)
            st.download_button(
                "⬇️ Télécharger le reçu PDF",
                data=pdf_bytes,
                file_name=f"{f['numero_facture']}.pdf",
                mime="application/pdf",
                key="download_derniere"
            )

    # ---------- HISTORIQUE ----------
    with tab_historique:
        factures = db.get_toutes_factures()

        if not factures:
            st.info("Aucune facture enregistrée pour le moment.")
        else:
            df_factures = pd.DataFrame(factures)

            recherche = st.text_input("🔎 Rechercher (client, chambre, n° facture)", key="recherche_hist")
            if recherche:
                masque = (
                    df_factures['client'].str.contains(recherche, case=False, na=False) |
                    df_factures['chambre_nom'].str.contains(recherche, case=False, na=False) |
                    df_factures['numero_facture'].str.contains(recherche, case=False, na=False)
                )
                df_factures = df_factures[masque]

            total_ttc_periode = int(df_factures['montant_ttc'].sum()) if not df_factures.empty else 0
            st.metric("Chiffre d'affaires (TTC) — sélection affichée", fmt_fcfa(total_ttc_periode))

            for _, f in df_factures.iterrows():
                statut_icone = "✅" if f['statut_paiement'] == "Payé" else "⏳"
                with st.expander(
                    f"{statut_icone} {f['numero_facture']} — {f['client']} — {fmt_fcfa(f['montant_ttc'])}"
                ):
                    st.write(f"**Chambre :** {f['chambre_nom']} ({f['chambre_type']})")
                    st.write(f"**Date :** {f['date_creation'][:16]}")
                    st.write(f"**Nuitées :** {f['nuitees']} à {fmt_fcfa(f['tarif_unitaire'])}")
                    st.write(f"**Total HT :** {fmt_fcfa(f['montant_ht'])}")
                    st.write(f"**TVA ({f['taux_tva']:g}%) :** {fmt_fcfa(f['montant_tva'])}")
                    st.write(f"**Total TTC :** {fmt_fcfa(f['montant_ttc'])}")
                    st.write(f"**Mode de paiement :** {f['mode_paiement']}")
                    st.write(f"**Statut :** {f['statut_paiement']}")
                    if f['notes']:
                        st.write(f"**Notes :** {f['notes']}")

                    colb1, colb2 = st.columns(2)
                    pdf_bytes = generer_pdf_facture(dict(f), NOM_ETABLISSEMENT)
                    colb1.download_button(
                        "⬇️ PDF",
                        data=pdf_bytes,
                        file_name=f"{f['numero_facture']}.pdf",
                        mime="application/pdf",
                        key=f"pdf_{f['numero_facture']}"
                    )
                    if f['statut_paiement'] == "En attente":
                        if colb2.button("Marquer comme payé", key=f"payer_{f['numero_facture']}"):
                            db.maj_statut_paiement(f['numero_facture'], "Payé")
                            st.rerun()
