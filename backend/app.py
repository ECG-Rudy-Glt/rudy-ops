"""Backend du formulaire de contact rudy-ops.fr.

Reçoit la demande du formulaire (ContactForm.tsx), puis :
  1. envoie un accusé de réception au client
  2. envoie une notification complète à Rudy
  3. crée une tâche Vikunja dans le projet "Pro" pour ne rien perdre

Anti-spam minimal : champ honeypot ("website") - un humain ne le voit ni ne le
remplit (caché en CSS côté frontend), un bot générique le remplit presque
toujours. Rempli => on répond succès sans rien envoyer, pour ne pas indiquer
au bot qu'il a été détecté.
"""
import logging
import os
import re
import smtplib
from email.message import EmailMessage

import requests
from flask import Flask, jsonify, request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024  # 32 Ko — largement suffisant, coupe l'abus de payload

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]
NOTIFY_EMAIL = os.environ["NOTIFY_EMAIL"]

VIKUNJA_API_URL = os.environ["VIKUNJA_API_URL"]  # ex: http://10.0.20.52:3456/api/v1
VIKUNJA_API_TOKEN = os.environ["VIKUNJA_API_TOKEN"]
VIKUNJA_PROJECT_ID = os.environ["VIKUNJA_PROJECT_ID"]

ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "https://rudy-ops.fr")

REQUIRED_FIELDS = ("name", "email", "subject", "message")

# Validation stricte — défense en profondeur même si EmailMessage()/requests
# encodent déjà proprement leurs valeurs :
#   - EMAIL_RE : format d'adresse raisonnable, refuse d'utiliser ce endpoint comme
#     relais pour spammer une adresse arbitraire avec un contenu à moitié contrôlé
#   - CONTROL_CHARS_RE : \r/\n/\0 interdits sur les champs mono-ligne — bloque une
#     tentative d'injection d'en-tête SMTP (ex: "email" contenant "\r\nBcc: ...")
#     avant même que le champ n'atteigne EmailMessage
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
CONTROL_CHARS_RE = re.compile(r"[\r\n\0]")

FIELD_MAX_LENGTHS = {
    "name": 100,
    "email": 200,
    "company": 200,
    "subject": 200,
    "message": 5000,
}

SINGLE_LINE_FIELDS = ("name", "email", "company", "subject")


def validate(data: dict) -> str | None:
    """Retourne un message d'erreur si les données sont invalides, sinon None."""
    missing = [f for f in REQUIRED_FIELDS if not data.get(f)]
    if missing:
        return f"Champs manquants : {', '.join(missing)}"

    for field, max_len in FIELD_MAX_LENGTHS.items():
        value = data.get(field)
        if value and len(value) > max_len:
            return f"Champ trop long : {field} (max {max_len} caractères)"

    for field in SINGLE_LINE_FIELDS:
        value = data.get(field)
        if value and CONTROL_CHARS_RE.search(value):
            return f"Caractère invalide dans le champ : {field}"

    if not EMAIL_RE.match(data["email"]):
        return "Adresse email invalide"

    return None


def send_email(to: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(msg)


def create_vikunja_task(data: dict) -> None:
    title = f"{data['name']} — {data['subject']}"
    company = f" ({data['company']})" if data.get("company") else ""
    description = (
        f"**Email** : {data['email']}\n"
        f"**Entreprise** : {data.get('company') or '-'}\n"
        f"**Sujet** : {data['subject']}\n\n"
        f"{data['message']}"
    )
    resp = requests.put(
        f"{VIKUNJA_API_URL}/projects/{VIKUNJA_PROJECT_ID}/tasks",
        headers={"Authorization": f"Bearer {VIKUNJA_API_TOKEN}"},
        json={"title": title + company, "description": description},
        timeout=10,
    )
    resp.raise_for_status()


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/contact", methods=["OPTIONS"])
def contact_preflight():
    return "", 204


@app.route("/contact", methods=["POST"])
def contact():
    data = request.get_json(silent=True) or {}

    # Honeypot rempli => bot très probable, on répond succès sans rien faire.
    if data.get("website"):
        return jsonify({"ok": True}), 200

    error = validate(data)
    if error:
        return jsonify({"ok": False, "error": error}), 400

    try:
        client_body = (
            f"Bonjour {data['name']},\n\n"
            "Merci pour votre message, je reviens vers vous rapidement "
            "(généralement sous 48h en semaine, un peu plus le week-end).\n\n"
            f"Récapitulatif de votre demande :\n"
            f"- Sujet : {data['subject']}\n"
            f"- Message : {data['message']}\n\n"
            "À bientôt,\nRudy"
        )
        send_email(data["email"], "Votre demande — rudy-ops.fr", client_body)

        notify_body = (
            f"Nouvelle demande depuis rudy-ops.fr\n\n"
            f"Nom : {data['name']}\n"
            f"Email : {data['email']}\n"
            f"Entreprise : {data.get('company') or '-'}\n"
            f"Sujet : {data['subject']}\n\n"
            f"Message :\n{data['message']}"
        )
        send_email(NOTIFY_EMAIL, f"[rudy-ops.fr] Nouvelle demande — {data['subject']}", notify_body)

        create_vikunja_task(data)
    except Exception:
        logger.exception("Échec du traitement de la demande de contact")
        return jsonify({"ok": False, "error": "Erreur serveur, réessayez plus tard."}), 500

    return jsonify({"ok": True}), 200


@app.route("/health")
def health():
    return jsonify({"ok": True})


@app.errorhandler(Exception)
def handle_unexpected_error(err):
    logger.exception("Erreur inattendue")
    return jsonify({"ok": False, "error": "Erreur serveur"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8082)
