import json
import os
import re
import smtplib
import ssl
import uuid
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
# Nécessaire pour les sessions (connexion au panneau de contrôle). À changer en prod.
app.secret_key = os.environ.get("SECRET_KEY", "4517c4afd01a48e834924703fc0854a5af4603563e7cd970")

# ---------------------------------------------------------------------------
# Configuration des demandes de démo / contact + panneau de contrôle
# ---------------------------------------------------------------------------
# Option 1 (recommandé) : définir ces valeurs comme variables d'environnement
#   (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, CONTACT_TO, ADMIN_PASSWORD)
# Option 2 (rapide) : remplacer directement les valeurs ci-dessous.
CONFIG = {
    # Serveur SMTP utilisé pour ENVOYER la notification (ex: smtp.gmail.com, smtp.office365.com)
    "SMTP_HOST": os.environ.get("SMTP_HOST", ""),
    "SMTP_PORT": int(os.environ.get("SMTP_PORT", "587")),
    # Compte utilisé pour envoyer l'email (ex: scaleupadministration@gmail.com)
    "SMTP_USER": os.environ.get("SMTP_USER", ""),
    # Mot de passe applicatif (jamais le mot de passe principal du compte)
    "SMTP_PASSWORD": os.environ.get("SMTP_PASSWORD", ""),
    # Adresse qui doit RECEVOIR les demandes de démo / contact
    "CONTACT_TO": os.environ.get("CONTACT_TO", "scaleupadministration@gmail.com"),
    # Mot de passe pour se connecter au panneau de contrôle (/admin) — à changer impérativement
    "ADMIN_PASSWORD": os.environ.get("ADMIN_PASSWORD", "ScaleUp-Fes-2026!"),
}

DATA_DIR = Path(__file__).parent / "data"
DATA_FILE = DATA_DIR / "demandes.json"
PROMOS_FILE = DATA_DIR / "promos.json"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Bannières promotionnelles (slider de la page d'accueil) — image uploadée par l'admin
PROMO_UPLOAD_DIR = Path(__file__).parent / "static" / "img" / "promos"
PROMO_ALLOWED_EXT = {"png", "jpg", "jpeg", "webp"}
# Dimensions recommandées pour les images du slider (affichées dans le panneau admin)
PROMO_RECOMMENDED_SIZE = "1600 × 700 px (ratio ~2.3:1)"
app.config["MAX_CONTENT_LENGTH"] = 6 * 1024 * 1024  # 6 Mo max par requête (upload d'image inclus)

NAV = [
    {"label": "Accueil", "href": "/"},
    {"label": "École privée", "href": "/ecole"},
    {"label": "Médecins", "href": "/medecin"},
]


# ---------------------------------------------------------------------------
# Stockage des demandes (JSON local — aucune base de données nécessaire)
# ---------------------------------------------------------------------------
def load_demandes():
    if not DATA_FILE.exists():
        return []
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def write_demandes(entries):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


def save_demande(entry):
    entries = load_demandes()
    entries.append(entry)
    write_demandes(entries)


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


def require_admin():
    return session.get("is_admin", False)


# ---------------------------------------------------------------------------
# Slider promotionnel de la page d'accueil (bannières gérées depuis /admin/promos)
# ---------------------------------------------------------------------------
def load_promos():
    if not PROMOS_FILE.exists():
        return []
    try:
        return json.loads(PROMOS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def write_promos(entries):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROMOS_FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


def default_promos():
    """Diapositives affichées tant qu'aucune promotion n'a été ajoutée depuis /admin/promos."""
    return [
        {
            "eyebrow": "École privée",
            "title": "Application de gestion scolaire complète",
            "subtitle": "Élèves, paiements, présence, transport : tout piloté depuis une seule plateforme.",
            "link": "/ecole",
            "image": "img/app-screenshot.png",
        },
        {
            "eyebrow": "Marketing Digital",
            "title": "Des campagnes qui font connaître votre activité",
            "subtitle": "Réseaux sociaux, Facebook Ads, Google Ads : une présence qui convertit.",
            "link": "/marketing",
            "image": None,
        },
        {
            "eyebrow": "Digitalisation",
            "title": "Vos process automatisés et connectés",
            "subtitle": "Applications sur mesure, automatisation, CRM, ERP et cloud.",
            "link": "/digitalisation",
            "image": None,
        },
        {
            "eyebrow": "Cabinets médicaux",
            "title": "Développez votre patientèle",
            "subtitle": "Marketing digital et digitalisation pensés pour votre cabinet.",
            "link": "/medecin",
            "image": None,
        },
    ]


def active_promo_slides():
    """Retourne les promotions actives ; si aucune n'a été configurée, retombe sur les 4 services par défaut."""
    saved = [p for p in load_promos() if p.get("active", True)]
    return saved if saved else default_promos()


@app.context_processor
def inject_nav():
    return {"nav_items": NAV}


# ---------------------------------------------------------------------------
# Pages publiques
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    """Page d'accueil courte : slider de promotions + choix du domaine."""
    return render_template("landing.html", active="/", promo_slides=active_promo_slides())


@app.route("/ecole")
def ecole():
    return render_template("ecole.html", active="/ecole")


@app.route("/medecin")
def medecin():
    return render_template("medecin.html", active="/medecin")


@app.route("/application")
def application():
    return render_template("application.html", active="")


@app.route("/marketing")
def marketing():
    return render_template("marketing.html", active="")


@app.route("/digitalisation")
def digitalisation():
    return render_template("digitalisation.html", active="")


@app.route("/contact")
def contact():
    # ?service=ecole ou ?service=medecin permet de pré-remplir le formulaire
    preselect = request.args.get("service", "")
    return render_template("contact.html", active="", preselect=preselect)


# ---------------------------------------------------------------------------
# API — réception des demandes de démo / contact
# ---------------------------------------------------------------------------
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
        "id": uuid.uuid4().hex,
        "name": name,
        "org": org,
        "email": email,
        "service": service,
        "message": message,
        "status": "nouveau",
        "received_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    save_demande(entry)
    email_sent = send_email_notification(entry)

    return jsonify(success=True, email_sent=email_sent)


# ---------------------------------------------------------------------------
# Panneau de contrôle (réception des messages / demandes de démo)
# ---------------------------------------------------------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == CONFIG["ADMIN_PASSWORD"]:
            session["is_admin"] = True
            return redirect(url_for("admin_panel"))
        else:
            error = "Mot de passe incorrect."
    return render_template("admin_login.html", active="", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin_login"))


@app.route("/admin")
def admin_panel():
    if not require_admin():
        return redirect(url_for("admin_login"))
    entries = list(reversed(load_demandes()))
    total = len(entries)
    nouveaux = sum(1 for e in entries if e.get("status", "nouveau") == "nouveau")
    return render_template("admin.html", active="", entries=entries, total=total, nouveaux=nouveaux)


@app.route("/admin/demandes/<entry_id>/status", methods=["POST"])
def toggle_status(entry_id):
    if not require_admin():
        return jsonify(success=False, error="Non autorisé."), 403
    entries = load_demandes()
    updated = False
    for e in entries:
        if e.get("id") == entry_id:
            e["status"] = "traité" if e.get("status", "nouveau") != "traité" else "nouveau"
            updated = True
            break
    if updated:
        write_demandes(entries)
    return jsonify(success=updated)


# ---------------------------------------------------------------------------
# Panneau de contrôle — gestion des promotions du slider d'accueil
# ---------------------------------------------------------------------------
def _allowed_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in PROMO_ALLOWED_EXT


@app.route("/admin/promos")
def admin_promos():
    if not require_admin():
        return redirect(url_for("admin_login"))
    promos = list(reversed(load_promos()))
    return render_template(
        "admin_promos.html",
        active="",
        promos=promos,
        recommended_size=PROMO_RECOMMENDED_SIZE,
        upload_error=request.args.get("error"),
    )


@app.route("/admin/promos", methods=["POST"])
def create_promo():
    if not require_admin():
        return redirect(url_for("admin_login"))

    title = (request.form.get("title") or "").strip()
    subtitle = (request.form.get("subtitle") or "").strip()
    eyebrow = (request.form.get("eyebrow") or "").strip()
    link = (request.form.get("link") or "").strip()
    image_path = None

    file = request.files.get("image")
    if file and file.filename:
        if not _allowed_image(file.filename):
            return redirect(url_for("admin_promos", error="format"))
        PROMO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = secure_filename(f"{uuid.uuid4().hex}.{ext}")
        file.save(PROMO_UPLOAD_DIR / filename)
        image_path = f"img/promos/{filename}"

    if not title:
        return redirect(url_for("admin_promos", error="titre"))

    promo = {
        "id": uuid.uuid4().hex,
        "eyebrow": eyebrow,
        "title": title,
        "subtitle": subtitle,
        "link": link,
        "image": image_path,
        "active": True,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    promos = load_promos()
    promos.append(promo)
    write_promos(promos)
    return redirect(url_for("admin_promos"))


@app.route("/admin/promos/<promo_id>/toggle", methods=["POST"])
def toggle_promo(promo_id):
    if not require_admin():
        return jsonify(success=False, error="Non autorisé."), 403
    promos = load_promos()
    for p in promos:
        if p.get("id") == promo_id:
            p["active"] = not p.get("active", True)
            write_promos(promos)
            return jsonify(success=True, active=p["active"])
    return jsonify(success=False), 404


@app.route("/admin/promos/<promo_id>/delete", methods=["POST"])
def delete_promo(promo_id):
    if not require_admin():
        return redirect(url_for("admin_login"))
    promos = load_promos()
    remaining = []
    for p in promos:
        if p.get("id") == promo_id:
            if p.get("image"):
                img_file = Path(__file__).parent / "static" / p["image"]
                if img_file.exists():
                    img_file.unlink()
            continue
        remaining.append(p)
    write_promos(remaining)
    return redirect(url_for("admin_promos"))


@app.errorhandler(413)
def too_large(_e):
    return redirect(url_for("admin_promos", error="taille"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
