"""
Lance Swanky Apartments PMS dans sa propre fenÃªtre (comme un vrai logiciel),
sans ouvrir Chrome/Firefox/Edge. Fonctionne en dÃ©marrant Streamlit en arriÃ¨re-plan
(invisible) puis en l'affichant dans une fenÃªtre native via pywebview.

Double-clique sur ce fichier (extension .pyw) pour le lancer sans fenÃªtre noire
de terminal qui reste ouverte.
"""

import os
import sys
import time
import socket
import subprocess
import threading

import webview

DOSSIER = os.path.dirname(os.path.abspath(__file__))
PORT = 8501


def port_est_pris(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def lancer_serveur_streamlit():
    """DÃ©marre Streamlit en arriÃ¨re-plan, sans fenÃªtre de console visible."""
    kwargs = {}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", os.path.join(DOSSIER, "app.py"),
            "--server.headless", "true",
            "--server.port", str(PORT),
            "--browser.gatherUsageStats", "false",
            "--server.address", "127.0.0.1",
        ],
        cwd=DOSSIER,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **kwargs,
    )


def attendre_serveur_pret(timeout=25):
    depart = time.time()
    while time.time() - depart < timeout:
        if port_est_pris(PORT):
            return True
        time.sleep(0.5)
    return False


def main():
    if not port_est_pris(PORT):
        threading.Thread(target=lancer_serveur_streamlit, daemon=True).start()
        attendre_serveur_pret()
    else:
        # Le serveur tourne dÃ©jÃ  (ex: lancÃ© manuellement) â€” on ouvre juste la fenÃªtre
        pass

    # Petite marge supplÃ©mentaire pour laisser Streamlit finir son initialisation
    time.sleep(1.5)

    webview.create_window(
        "Swanky Apartments â€” PMS",
        f"http://127.0.0.1:{PORT}",
        width=1440,
        height=900,
        min_size=(1000, 700),
    )
    webview.start()


if __name__ == "__main__":
    main()
