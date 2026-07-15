import streamlit as st
import pandas as pd

import database as db
import common
from pdf_generator import generer_pdf_facture
from docx_generator import generer_docx_facture
from xlsx_generator import generer_xlsx_facture, generer_xlsx_historique

st.set_page_config(page_title="Facturation - Swanky Apartments", layout="wide", page_icon="💰")

user = common.garantir_authentification()
common.afficher_sidebar(user)

NOM_ETABLISSEMENT = db.get_parametre("nom_etablissement", "Swanky Apartments")
TAUX_TVA = float(db.get_parametre("taux_tva", db.TAUX_TVA_DEFAUT))

st.title("💰 Facturation")
st.markdown("---")

chambres = db.get_toutes_chambres()
df_chambres = pd.DataFrame(chambres)

tab_nouvelle, tab_historique = st.tabs(["🧾 Nouvelle facture", "📜 Historique"])

# ==========================================
# NOUVELLE FACTURE
# ==========================================
with tab_nouvelle:
    col_form, col_recap = st.columns([1.3, 1])

    with col_form:
        room_facture = st.selectbox("Chambre à facturer", df_chambres['nom'].unique(), key="facture_room")
        room_data = db.get_chambre(room_facture)
        tarif_de_base = room_data['tarif']

        client_facture = st.text_input(
            "Nom du client",
            value=room_data['client'] if room_data['statut'] == "Occupé" else "",
            key="client_facture"
        )

        nuitees = st.number_input("Nombre de nuitées", min_value=1, value=1, step=1, key="nuitees_facture")

        tarif_applique = st.number_input(
            "Tarif par nuitée appliqué (FCFA, TTC)",
            value=int(tarif_de_base),
            step=5000,
            help=f"Tarif standard : {common.fmt_fcfa(tarif_de_base)} TTC (taxes comprises). "
                 f"Modifiez ce montant si un prix dégressif a été accordé."
        )

        mode_paiement = st.selectbox("Mode de paiement", ["Espèces", "Mobile Money", "Carte bancaire", "Virement"])
        statut_paiement = st.radio("Statut du paiement", ["Payé", "En attente"], horizontal=True)
        notes_facture = st.text_area("Notes (optionnel)", height=68)

    with col_recap:
        montant_ttc = tarif_applique * nuitees
        montant_ht = round(montant_ttc / (1 + TAUX_TVA / 100))
        montant_tva = montant_ttc - montant_ht

        st.markdown("#### Récapitulatif")
        st.metric("Total HT", common.fmt_fcfa(montant_ht))
        st.metric(f"TVA ({TAUX_TVA:g}%)", common.fmt_fcfa(montant_tva))
        st.markdown(f"### **Total TTC : {common.fmt_fcfa(montant_ttc)}**")
        st.caption(f"{nuitees} nuit(s) à {common.fmt_fcfa(tarif_applique)}/nuit (TTC).")

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

        if "derniere_facture" in st.session_state:
            f = st.session_state["derniere_facture"]
            st.markdown("**Télécharger le reçu :**")
            colp, colw, colx = st.columns(3)
            colp.download_button(
                "⬇️ PDF", data=generer_pdf_facture(f, NOM_ETABLISSEMENT),
                file_name=f"{f['numero_facture']}.pdf", mime="application/pdf", key="dl_pdf_derniere"
            )
            colw.download_button(
                "⬇️ Word", data=generer_docx_facture(f, NOM_ETABLISSEMENT),
                file_name=f"{f['numero_facture']}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="dl_docx_derniere"
            )
            colx.download_button(
                "⬇️ Excel", data=generer_xlsx_facture(f, NOM_ETABLISSEMENT),
                file_name=f"{f['numero_facture']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_xlsx_derniere"
            )

# ==========================================
# HISTORIQUE
# ==========================================
with tab_historique:
    factures = db.get_toutes_factures()

    if not factures:
        st.info("Aucune facture enregistrée pour le moment.")
    else:
        df_factures = pd.DataFrame(factures)

        col_recherche, col_export_all = st.columns([3, 1])
        with col_recherche:
            recherche = st.text_input("🔎 Rechercher (client, chambre, n° facture)", key="recherche_hist")
        with col_export_all:
            st.write("")
            st.write("")
            st.download_button(
                "📊 Exporter tout (Excel)",
                data=generer_xlsx_historique(factures, NOM_ETABLISSEMENT),
                file_name="historique_factures.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_xlsx_historique"
            )

        if recherche:
            masque = (
                df_factures['client'].str.contains(recherche, case=False, na=False) |
                df_factures['chambre_nom'].str.contains(recherche, case=False, na=False) |
                df_factures['numero_facture'].str.contains(recherche, case=False, na=False)
            )
            df_factures = df_factures[masque]

        total_ttc_periode = int(df_factures['montant_ttc'].sum()) if not df_factures.empty else 0
        st.metric("Chiffre d'affaires (TTC) — sélection affichée", common.fmt_fcfa(total_ttc_periode))

        for _, f in df_factures.iterrows():
            f_dict = dict(f)
            statut_icone = "✅" if f['statut_paiement'] == "Payé" else "⏳"
            with st.expander(
                f"{statut_icone} {f['numero_facture']} — {f['client']} — {common.fmt_fcfa(f['montant_ttc'])}"
            ):
                st.write(f"**Chambre :** {f['chambre_nom']} ({f['chambre_type']})")
                st.write(f"**Date :** {f['date_creation'][:16]}")
                st.write(f"**Nuitées :** {f['nuitees']} à {common.fmt_fcfa(f['tarif_unitaire'])}")
                st.write(f"**Total HT :** {common.fmt_fcfa(f['montant_ht'])}")
                st.write(f"**TVA ({f['taux_tva']:g}%) :** {common.fmt_fcfa(f['montant_tva'])}")
                st.write(f"**Total TTC :** {common.fmt_fcfa(f['montant_ttc'])}")
                st.write(f"**Mode de paiement :** {f['mode_paiement']}")
                st.write(f"**Statut :** {f['statut_paiement']}")
                if f['notes']:
                    st.write(f"**Notes :** {f['notes']}")

                colb1, colb2, colb3, colb4 = st.columns(4)
                colb1.download_button(
                    "⬇️ PDF", data=generer_pdf_facture(f_dict, NOM_ETABLISSEMENT),
                    file_name=f"{f['numero_facture']}.pdf", mime="application/pdf",
                    key=f"pdf_{f['numero_facture']}"
                )
                colb2.download_button(
                    "⬇️ Word", data=generer_docx_facture(f_dict, NOM_ETABLISSEMENT),
                    file_name=f"{f['numero_facture']}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=f"docx_{f['numero_facture']}"
                )
                colb3.download_button(
                    "⬇️ Excel", data=generer_xlsx_facture(f_dict, NOM_ETABLISSEMENT),
                    file_name=f"{f['numero_facture']}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"xlsx_{f['numero_facture']}"
                )
                if f['statut_paiement'] == "En attente":
                    if colb4.button("Marquer payé", key=f"payer_{f['numero_facture']}"):
                        db.maj_statut_paiement(f['numero_facture'], "Payé")
                        st.rerun()
