"""
Génération de reçus/factures PDF pour Swanky Apartments PMS.
Utilise fpdf2 (léger, sans dépendances lourdes).
"""

from fpdf import FPDF
from datetime import datetime


def _fmt_montant(valeur):
    return f"{valeur:,.0f}".replace(",", " ") + " FCFA"


class FactureA4(FPDF):
    def __init__(self, nom_etablissement):
        super().__init__(format="A4")
        self.nom_etablissement = nom_etablissement
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_fill_color(24, 34, 54)
        self.rect(0, 0, 210, 32, "F")
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 18)
        self.set_xy(10, 8)
        self.cell(0, 10, self.nom_etablissement, ln=True)
        self.set_font("Helvetica", "", 10)
        self.set_xy(10, 20)
        self.cell(0, 6, "Reçu de facturation", ln=True)
        self.set_text_color(0, 0, 0)
        self.ln(15)

    def footer(self):
        self.set_y(-18)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, "Document généré automatiquement — Swanky Apartments PMS", align="C")


def generer_pdf_facture(facture: dict, nom_etablissement="Swanky Apartments") -> bytes:
    """
    Construit le PDF d'une facture à partir d'un dict produit par
    database.creer_facture / database.get_facture_par_numero.
    Retourne les octets du PDF (utilisables directement dans st.download_button).
    """
    pdf = FactureA4(nom_etablissement)
    pdf.add_page()

    # --- Bloc infos facture / client ---
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_xy(10, 40)
    pdf.cell(95, 7, f"Facture N° : {facture['numero_facture']}", ln=0)
    pdf.set_font("Helvetica", "", 11)
    date_aff = facture['date_creation'][:16]
    pdf.cell(95, 7, f"Date : {date_aff}", ln=1, align="R")

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(95, 7, "Client :", ln=0)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(95, 7, facture['client'], ln=1, align="R")

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(95, 7, "Mode de paiement :", ln=0)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(95, 7, facture.get('mode_paiement', 'Espèces'), ln=1, align="R")

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(95, 7, "Statut :", ln=0)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(95, 7, facture.get('statut_paiement', 'Payé'), ln=1, align="R")

    pdf.ln(6)

    # --- Tableau de détail ---
    pdf.set_fill_color(240, 240, 245)
    pdf.set_font("Helvetica", "B", 10)
    largeurs = [70, 30, 35, 55]
    entetes = ["Chambre", "Nuitée(s)", "Tarif unitaire", "Sous-total"]
    for w, h in zip(largeurs, entetes):
        pdf.cell(w, 9, h, border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 10)
    designation = f"{facture['chambre_nom']} ({facture.get('chambre_type', '')})"
    pdf.cell(largeurs[0], 9, designation, border=1)
    pdf.cell(largeurs[1], 9, str(facture['nuitees']), border=1, align="C")
    pdf.cell(largeurs[2], 9, _fmt_montant(facture['tarif_unitaire']), border=1, align="R")
    pdf.cell(largeurs[3], 9, _fmt_montant(facture['montant_ht']), border=1, align="R")
    pdf.ln(14)

    # --- Totaux ---
    x_totaux = 110
    pdf.set_x(x_totaux)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(50, 8, "Total HT :", border=0)
    pdf.cell(40, 8, _fmt_montant(facture['montant_ht']), align="R", ln=1)

    pdf.set_x(x_totaux)
    pdf.cell(50, 8, f"TVA ({facture['taux_tva']:g}%) :", border=0)
    pdf.cell(40, 8, _fmt_montant(facture['montant_tva']), align="R", ln=1)

    pdf.set_x(x_totaux)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_fill_color(24, 34, 54)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(50, 10, "TOTAL TTC :", border=0, fill=True)
    pdf.cell(40, 10, _fmt_montant(facture['montant_ttc']), align="R", fill=True, ln=1)
    pdf.set_text_color(0, 0, 0)

    if facture.get("notes"):
        pdf.ln(10)
        pdf.set_font("Helvetica", "I", 9)
        pdf.multi_cell(0, 6, f"Notes : {facture['notes']}")

    return bytes(pdf.output())
    
