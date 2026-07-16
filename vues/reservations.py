import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

import database as db
import common

user = common.garantir_authentification()
common.afficher_sidebar(user)
etab_id = user["etablissement_id"]

st.title("📅 Réservations & Planning")
st.markdown("---")

chambres = db.get_toutes_chambres(etab_id)
df_chambres = pd.DataFrame(chambres)
reservations = db.get_toutes_reservations(etab_id)

if df_chambres.empty:
    st.warning("Aucune chambre configurée pour le moment. Rends-toi sur la page Chambres "
               "pour ajouter tes premières chambres avant de créer des réservations.")
    st.stop()

tab_planning, tab_nouvelle, tab_liste = st.tabs(
    ["🗓️ Planning", "➕ Nouvelle réservation", "📋 Liste & gestion"]
)

with tab_planning:
    reservations_actives = [r for r in reservations if r['statut'] in ('Confirmée', 'En cours')]

    if not reservations_actives:
        st.info("Aucune réservation active à afficher sur le planning pour le moment. "
                "Crée une réservation dans l'onglet ci-contre.")
    else:
        couleurs = {"Confirmée": "#3B82F6", "En cours": "#16A34A"}
        df_planning = pd.DataFrame([
            {
                "Chambre": r["chambre_nom"],
                "Début": r["date_arrivee"],
                "Fin": r["date_depart"],
                "Client": r["client"],
                "Statut": r["statut"],
                "Réservation": r["numero_reservation"],
            }
            for r in reservations_actives
        ])

        fig = px.timeline(
            df_planning, x_start="Début", x_end="Fin", y="Chambre", color="Statut",
            color_discrete_map=couleurs, hover_data=["Client", "Réservation"],
            title="Planning des réservations en cours et à venir"
        )
        fig.update_yaxes(categoryorder="category ascending", autorange="reversed")
        fig.update_layout(height=max(350, 40 * df_chambres['nom'].nunique()), xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    st.caption("🔵 Confirmée — en attente d'arrivée   |   🟢 En cours — client déjà installé")

with tab_nouvelle:
    st.markdown("### Créer une nouvelle réservation")

    col1, col2 = st.columns(2)
    with col1:
        chambre_choisie = st.selectbox("Chambre", df_chambres['nom'].unique(), key="resa_chambre")
        chambre_data = db.get_chambre(etab_id, chambre_choisie)
        client = st.text_input("Nom du client", key="resa_client")
        telephone = st.text_input("Téléphone", key="resa_tel")
        nb_personnes = st.number_input("Nombre de personnes", min_value=1, value=1, key="resa_pers")

    with col2:
        aujourdhui = date.today()
        date_arrivee = st.date_input("Date d'arrivée", value=aujourdhui, key="resa_arrivee")
        date_depart = st.date_input("Date de départ", value=aujourdhui + timedelta(days=1), key="resa_depart")
        societe = st.text_input("Société (optionnel)", key="resa_societe")
        code_client = st.text_input("Code client (optionnel)", key="resa_code")

    tarif_nuit = st.number_input(
        "Tarif par nuitée (FCFA, TTC)", value=int(chambre_data['tarif']), step=5000, key="resa_tarif"
    )
    notes = st.text_area("Notes (optionnel)", height=68, key="resa_notes")

    nb_nuits = (date_depart - date_arrivee).days
    if nb_nuits > 0:
        st.caption(f"Séjour de {nb_nuits} nuit(s) — total estimé : "
                   f"{common.fmt_fcfa(tarif_nuit * nb_nuits)} TTC")

    if st.button("📌 Créer la réservation", type="primary"):
        if date_depart <= date_arrivee:
            st.error("La date de départ doit être postérieure à la date d'arrivée.")
        elif not client.strip():
            st.warning("Merci d'indiquer le nom du client.")
        elif not db.chambre_disponible_periode(etab_id, chambre_choisie, date_arrivee.isoformat(), date_depart.isoformat()):st.error(f"⚠️ {chambre_choisie} est déjà réservée sur une partie de cette période. "
                      "Choisis d'autres dates ou une autre chambre.")
        else:
            numero = db.creer_reservation(
                etablissement_id=etab_id,
                chambre_nom=chambre_choisie,
                chambre_type=chambre_data['type'],
                client=client.strip(),
                date_arrivee=date_arrivee.isoformat(),
                date_depart=date_depart.isoformat(),
                tarif_nuit=tarif_nuit,
                telephone=telephone.strip(),
                societe=societe.strip(),
                code_client=code_client.strip(),
                nb_personnes=nb_personnes,
                notes=notes.strip(),
            )
            st.success(f"Réservation {numero} créée avec succès pour {client} — "
                       f"{chambre_choisie} du {date_arrivee.strftime('%d/%m/%Y')} "
                       f"au {date_depart.strftime('%d/%m/%Y')}.")
            st.rerun()

with tab_liste:
    if not reservations:
        st.info("Aucune réservation enregistrée pour le moment.")
    else:
        filtre_statut = st.multiselect(
            "Filtrer par statut", ["Confirmée", "En cours", "Terminée", "Annulée"],
            default=["Confirmée", "En cours"], key="filtre_statut_resa"
        )
        reservations_filtrees = [r for r in reservations if r['statut'] in filtre_statut] if filtre_statut else reservations

        for r in reservations_filtrees:
            icones = {"Confirmée": "🔵", "En cours": "🟢", "Terminée": "⚪", "Annulée": "🔴"}
            icone = icones.get(r['statut'], "⚪")
            with st.expander(
                f"{icone} {r['numero_reservation']} — {r['client']} — {r['chambre_nom']} "
                f"({r['date_arrivee']} → {r['date_depart']}) — {r['statut']}"
            ):
                c1, c2 = st.columns(2)
                c1.write(f"Chambre : {r['chambre_nom']} ({r['chambre_type']})")
                c1.write(f"Client : {r['client']}")
                c1.write(f"Téléphone : {r['telephone'] or '—'}")
                c1.write(f"Personnes : {r['nb_personnes']}")
                c2.write(f"Arrivée : {r['date_arrivee']}")
                c2.write(f"Départ : {r['date_depart']}")
                c2.write(f"Société : {r['societe'] or '—'}")
                c2.write(f"Code client : {r['code_client'] or '—'}")
                if r['notes']:
                    st.write(f"Notes : {r['notes']}")

                colb1, colb2, colb3 = st.columns(3)
                if r['statut'] == 'Confirmée':
                    if colb1.button("🛬 Check-in", key=f"checkin_{r['id']}"):
                        db.effectuer_checkin(r['id'])
                        st.success(f"Check-in effectué pour {r['client']}.")
                        st.rerun()
                    if colb2.button("❌ Annuler", key=f"annuler_{r['id']}"):
                        db.annuler_reservation(r['id'])
                        st.rerun()
                elif r['statut'] == 'En cours':
                    if colb1.button("🛫 Check-out", key=f"checkout_{r['id']}"):
                        db.effectuer_checkout(r['id'])
                        st.success(f"Check-out effectué pour {r['client']}.")
                        st.rerun()
