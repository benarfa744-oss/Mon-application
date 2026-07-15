import streamlit.web.cli as stcli
import os, sys

def resolve_path(path):
    if getattr(sys, "frozen", False):
        # Si c'est un exécutable, le chemin est temporaire
        basedir = sys._MEIPASS
    else:
        # Sinon, c'est le chemin normal
        basedir = os.path.dirname(__file__)
    return os.path.join(basedir, path)

if __name__ == "__main__":
    # Résout le chemin de votre fichier principal app.py
    app_path = resolve_path("app.py")
    
    # Configure Streamlit pour s'ouvrir dans une fenêtre d'application (Webview)
    # sans barre d'adresse et sans menus inutiles
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        "--server.headless=true",  # Ne pas ouvrir le navigateur par défaut
    ]
    sys.exit(stcli.main())
