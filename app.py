import json
import os
import re
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Configuration des demandes de démo / contact
# ---------------------------------------------------------------------------
# Option 1 (recommandé) : définir ces valeurs comme variables d'environnement
#   (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, CONTACT_TO, ADMIN_KEY)
# Option 2 (rapide) : remplacer directement les valeurs ci-dessous.
CONFIG = {
    # Serveur SMTP utilisé pour ENVOYER la notification (ex: smtp.gmail.com, smtp.office365.com)
    "SMTP_HOST": os.environ.get("SMTP_HOST", ""),
    "SMTP_PORT": int(os.environ.get("SMTP_PORT", "587")),
    # Compte utilisé pour envoyer l'email (ex: notifications@scaleup.agency)
    "SMTP_USER": os.environ.get("SMTP_USER", ""),
    # Mot de passe applicatif (jamais le mot de passe principal du compte)
    "SMTP_PASSWORD": os.environ.get("SMTP_PASSWORD", ""),
    # Adresse qui doit RECEVOIR les demandes de démo / contact
    "CONTACT_TO": os.environ.get("CONTACT_TO", "scaleupadministration@gmail.com"),
    # Clé secrète pour consulter /admin/demandes (à changer impérativement)
    "ADMIN_KEY": os.environ.get("ADMIN_KEY", "changeme"),
}

DATA_DIR = Path(__file__).parent / "data"
DATA_FILE = DATA_DIR / "demandes.json"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def load_demandes():
    if not DATA_FILE.exists():
        return []
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def save_demande(entry):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    entries = load_demandes()
    entries.append(entry)
    DATA_FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


def is_smtp_configured():
    return all(CONFIG[k] for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"))


def send_email_notification(entry):
    """Envoie un email à CONTACT_TO. Retourne True si l'email est bien parti."""
    if not is_smtp_configured():
        return False
    try:
        msg = EmailMessage()
        msg["Subject"] = f"Nouvelle demande de démo — {entry['org']}"
        msg["From"] = CONFIG["SMTP_USER"]
        msg["To"] = CONFIG["CONTACT_TO"]
        msg["Reply-To"] = entry["email"]
        msg.set_content(
            "Nouvelle demande reçue depuis le site ScaleUp\n\n"
            f"Nom : {entry['name']}\n"
            f"Établissement / Entreprise : {entry['org']}\n"
            f"Email : {entry['email']}\n"
            f"Service demandé : {entry['service']}\n"
            f"Message : {entry['message'] or '(aucun)'}\n"
            f"Reçu le : {entry['received_at']}\n"
        )
        context = ssl.create_default_context()
        with smtplib.SMTP(CONFIG["SMTP_HOST"], CONFIG["SMTP_PORT"]) as server:
            server.starttls(context=context)
            server.login(CONFIG["SMTP_USER"], CONFIG["SMTP_PASSWORD"])
            server.send_message(msg)
        return True
    except Exception as exc:  # noqa: BLE001 — on ne bloque jamais la sauvegarde pour un souci d'email
        app.logger.warning("Échec de l'envoi de l'email de notification : %s", exc)
        return False

NAV = [
    {"label": "Accueil", "href": "/"},
    {"label": "Application", "href": "/application"},
    {"label": "Marketing", "href": "/marketing"},
    {"label": "Digitalisation", "href": "/digitalisation"},
]


@app.context_processor
def inject_nav():
    return {"nav_items": NAV}


@app.route("/")
def home():
    return render_template("index.html", active="/")


@app.route("/application")
def application():
    return render_template("application.html", active="/application")


@app.route("/marketing")
def marketing():
    return render_template("marketing.html", active="/marketing")


@app.route("/digitalisation")
def digitalisation():
    return render_template("digitalisation.html", active="/digitalisation")


@app.route("/api/demande", methods=["POST"])
def api_demande():
    payload = request.get_json(silent=True) or request.form
    name = (payload.get("name") or "").strip()
    org = (payload.get("org") or "").strip()
    email = (payload.get("email") or "").strip()
    service = (payload.get("service") or "").strip()
    message = (payload.get("message") or "").strip()

    if not name or not org or not email:
        return jsonify(success=False, error="Merci de renseigner nom, établissement et email."), 400
    if not EMAIL_RE.match(email):
        return jsonify(success=False, error="Adresse email invalide."), 400

    entry = {
        "name": name,
        "org": org,
        "email": email,
        "service": service,
        "message": message,
        "received_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    save_demande(entry)
    email_sent = send_email_notification(entry)

    return jsonify(success=True, email_sent=email_sent)


@app.route("/admin/demandes")
def admin_demandes():
    if request.args.get("key") != CONFIG["ADMIN_KEY"] or CONFIG["ADMIN_KEY"] == "changeme":
        return (
            "Accès refusé. Définissez ADMIN_KEY dans app.py ou en variable d'environnement, "
            "puis ouvrez /admin/demandes?key=VOTRE_CLE",
            403,
        )
    entries = list(reversed(load_demandes()))
    return render_template("admin.html", active="", entries=entries)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
