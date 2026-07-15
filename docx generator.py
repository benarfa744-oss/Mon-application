"""
Génération de factures au format Word (.docx) pour Swanky Apartments PMS.
Utilise python-docx.
"""

import io
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT


def _fmt(v):
    return f"{v:,.0f}".replace(",", " ") + " FCFA"


def _cellule(cell, texte, gras=False, taille=10, couleur=None, align=None):
    cell.text = ""
    p = cell.paragraphs[0]
    if align:
        p.alignment = align
    run = p.add_run(str(texte))
    run.bold = gras
    run.font.size = Pt(taille)
    if couleur:
        run.font.color.rgb = RGBColor(*couleur)


def generer_docx_facture(facture: dict, nom_etablissement="Swanky Apartments") -> bytes:
    doc = Document()

    # --- En-tête ---
    titre = doc.add_paragraph()
    titre_run = titre.add_run(nom_etablissement)
    titre_run.bold = True
    titre_run.font.size = Pt(22)
    titre_run.font.color.rgb = RGBColor(24, 34, 54)

    sous_titre = doc.add_paragraph()
    sous_titre_run = sous_titre.add_run("Reçu de facturation")
    sous_titre_run.font.size = Pt(12)
    sous_titre_run.font.color.rgb = RGBColor(90, 90, 90)

    doc.add_paragraph()

    # --- Bloc infos ---
    infos = doc.add_table(rows=4, cols=2)
    infos.alignment = WD_TABLE_ALIGNMENT.LEFT
    lignes_infos = [
        ("Facture N°", facture["numero_facture"]),
        ("Date", facture["date_creation"][:16]),
        ("Client", facture["client"]),
        ("Statut", f"{facture.get('statut_paiement', 'Payé')} — {facture.get('mode_paiement', 'Espèces')}"),
    ]
    for i, (label, valeur) in enumerate(lignes_infos):
        _cellule(infos.cell(i, 0), label, gras=True, taille=11)
        _cellule(infos.cell(i, 1), valeur, taille=11)

    doc.add_paragraph()

    # --- Tableau de détail ---
    table = doc.add_table(rows=2, cols=4)
    table.style = "Light Grid Accent 1"
    entetes = ["Chambre", "Nuitée(s)", "Tarif unitaire (TTC)", "Sous-total (TTC)"]
    for i, texte in enumerate(entetes):
        _cellule(table.cell(0, i), texte, gras=True, taille=10)

    designation = f"{facture['chambre_nom']} ({facture.get('chambre_type', '')})"
    valeurs = [
        designation,
        str(facture["nuitees"]),
        _fmt(facture["tarif_unitaire"]),
        _fmt(facture["montant_ttc"]),
    ]
    for i, texte in enumerate(valeurs):
        _cellule(table.cell(1, i), texte, taille=10)

    doc.add_paragraph()

    # --- Totaux ---
    totaux = doc.add_table(rows=3, cols=2)
    lignes_totaux = [
        ("Total HT", _fmt(facture["montant_ht"]), False),
        (f"TVA ({facture['taux_tva']:g}%)", _fmt(facture["montant_tva"]), False),
        ("TOTAL TTC", _fmt(facture["montant_ttc"]), True),
    ]
    for i, (label, valeur, accent) in enumerate(lignes_totaux):
        couleur = (255, 255, 255) if accent else None
        _cellule(totaux.cell(i, 0), label, gras=True, taille=13 if accent else 11, couleur=couleur,
                  align=WD_ALIGN_PARAGRAPH.RIGHT)
        _cellule(totaux.cell(i, 1), valeur, gras=True, taille=13 if accent else 11, couleur=couleur,
                  align=WD_ALIGN_PARAGRAPH.RIGHT)
        if accent:
            for c in (totaux.cell(i, 0), totaux.cell(i, 1)):
                shading = c._tc.get_or_add_tcPr()
                from docx.oxml.ns import qn
                from docx.oxml import OxmlElement
                shd = OxmlElement("w:shd")
                shd.set(qn("w:fill"), "182236")
                shading.append(shd)

    if facture.get("notes"):
        doc.add_paragraph()
        note_p = doc.add_paragraph()
        note_run = note_p.add_run(f"Notes : {facture['notes']}")
        note_run.italic = True
        note_run.font.size = Pt(9)

    doc.add_paragraph()
    pied = doc.add_paragraph()
    pied_run = pied.add_run("Document généré automatiquement — Swanky Apartments PMS")
    pied_run.font.size = Pt(8)
    pied_run.font.color.rgb = RGBColor(140, 140, 140)
    pied.alignment = WD_ALIGN_PARAGRAPH.CENTER

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
