"""Backend du formulaire de contact rudy-ops.fr.

Reçoit la demande du formulaire (ContactForm.tsx), puis :
  1. envoie un accusé de réception au client
  2. envoie une notification complète à Rudy
  3. crée une tâche Vikunja dans le projet "Pro" pour ne rien perdre

Anti-spam minimal : champ honeypot ("website") - un humain ne le voit ni ne le
remplit (caché en CSS côté frontend), un bot générique le remplit presque
toujours. Rempli => on répond succès sans rien envoyer, pour ne pas indiquer
au bot qu'il a été détecté.

Expose aussi /quote-chat : un assistant IA (QuoteChat.tsx) optionnel en plus
du formulaire statique, qui pose des questions de qualification adaptées au
service choisi puis crée la même tâche Vikunja / les mêmes emails une fois
assez d'informations réunies. Les données extraites par Claude repassent par
la même validation que le formulaire (validate_contact_fields) avant tout
envoi — le contenu généré par la conversation n'est jamais utilisé tel quel.

Variables d'environnement requises en plus de celles du formulaire :
  ANTHROPIC_API_KEY (secret OpenBao, comme les autres — passé via -e dans le
  playbook Ansible, cf. pattern documenté dans deploy-vikunja.yml).
"""
import logging
import os
import re
import smtplib
from email.message import EmailMessage

import anthropic
import requests
from flask import Flask, jsonify, request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024  # 64 Ko — couvre l'historique du chat, coupe l'abus de payload

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]
NOTIFY_EMAIL = os.environ["NOTIFY_EMAIL"]

VIKUNJA_API_URL = os.environ["VIKUNJA_API_URL"]  # ex: http://10.0.20.52:3456/api/v1
VIKUNJA_API_TOKEN = os.environ["VIKUNJA_API_TOKEN"]
VIKUNJA_PROJECT_ID = os.environ["VIKUNJA_PROJECT_ID"]

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

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
    "summary": 4000,
}

SINGLE_LINE_FIELDS = ("name", "email", "company", "subject")


def validate_fields(data: dict, required: tuple[str, ...]) -> str | None:
    """Retourne un message d'erreur si les données sont invalides, sinon None.

    Utilisée à la fois pour le formulaire statique et pour les données que
    Claude extrait dans /quote-chat — même filtre, quelle que soit l'origine.
    """
    missing = [f for f in required if not data.get(f)]
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

    if "email" in data and not EMAIL_RE.match(data["email"]):
        return "Adresse email invalide"

    return None


def validate(data: dict) -> str | None:
    return validate_fields(data, REQUIRED_FIELDS)


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


# --- Assistant IA de devis (/quote-chat) ------------------------------------
#
# Additif : le formulaire statique (ContactForm.tsx / /contact) reste en place
# comme option par défaut. QuoteChat.tsx propose en plus une conversation qui
# pose 2-3 questions de qualification selon le service choisi, puis appelle le
# même create_vikunja_task()/send_email() une fois assez d'informations
# réunies — via l'outil submit_quote_request, jamais en texte libre.

QUOTE_MODEL = "claude-sonnet-5"

# Doit rester synchronisé avec src/data/services.tsx (slug -> titre affiché).
SERVICE_LABELS = {
    "devops-iac": "DevOps & Infrastructure as Code",
    "infra-on-premise": "Infrastructure on-premise",
    "site-statique": "Sites statiques",
    "site-dynamique": "Sites dynamiques",
    "open-source": "Open source friendly",
    "ia-llm": "IA et LLM dans vos workflows",
    "securite": "Sécurité",
}

# Questions de qualification par service — orientent Claude sans l'y forcer
# mot pour mot ; il adapte selon les réponses déjà données.
SERVICE_QUESTIONS = {
    "devops-iac": (
        "- Quel est l'outillage CI/CD actuel (s'il y en a un) ?\n"
        "- Les déploiements sont-ils aujourd'hui manuels, scriptés, ou déjà automatisés partiellement ?\n"
        "- Quelle est la taille approximative de l'infrastructure concernée (nombre de services/serveurs) ?"
    ),
    "infra-on-premise": (
        "- Où est hébergée l'infrastructure actuellement (cloud, on-premise, mixte) ?\n"
        "- L'objectif principal est-il la maîtrise des données, la réduction des coûts récurrents, ou autre ?\n"
        "- Y a-t-il déjà du matériel sur site, ou faut-il partir de zéro ?"
    ),
    "site-statique": (
        "- Combien de pages environ, et quel type de contenu (vitrine, documentation, blog) ?\n"
        "- Le site doit-il être multilingue ?\n"
        "- Préférence d'hébergement : cloud classique ou directement chez le client (on-premise) ?"
    ),
    "site-dynamique": (
        "- Quelles fonctionnalités dynamiques sont nécessaires (authentification, back-office, paiement, autre) ?\n"
        "- Y a-t-il des outils existants à intégrer (CRM, ERP, API tierces) ?\n"
        "- Quel est l'ordre de grandeur du volume d'utilisateurs attendu ?"
    ),
    "open-source": (
        "- Quel est le stack actuel, et quels outils propriétaires souhaite-t-on remplacer ?\n"
        "- La priorité est-elle d'éviter le vendor lock-in, de réduire les coûts de licence, ou de pouvoir auditer le code ?"
    ),
    "ia-llm": (
        "- Quels workflows concrets souhaite-t-on automatiser ou assister avec de l'IA (revue de code, support, documentation, autre) ?\n"
        "- Y a-t-il des données sensibles à ne jamais exposer à un service tiers ?\n"
        "- Volume attendu (usage ponctuel, quotidien, à grande échelle) ?"
    ),
    "securite": (
        "- Le besoin est-il un audit ponctuel, du durcissement, ou de la supervision continue ?\n"
        "- Y a-t-il déjà eu un incident ou une contrainte de conformité particulière ?\n"
        "- Qu'est-ce qui est déjà en place aujourd'hui en matière de sécurité ?"
    ),
}

DEFAULT_QUESTIONS = (
    "- Quel est le contexte du besoin (existant, contraintes techniques) ?\n"
    "- Y a-t-il un délai ou un budget déjà en tête ?"
)

QUOTE_TOOL = {
    "name": "submit_quote_request",
    "description": (
        "Soumets la demande de devis une fois que tu as le nom, l'email, et un "
        "résumé structuré du besoin incluant les réponses aux questions de "
        "qualification pertinentes. N'appelle cet outil qu'après avoir posé au "
        "moins une question de qualification adaptée au service choisi — pas "
        "immédiatement après le premier message."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Nom de la personne"},
            "email": {"type": "string", "description": "Adresse email"},
            "company": {"type": "string", "description": "Entreprise mentionnée, sinon omettre"},
            "summary": {
                "type": "string",
                "description": (
                    "Résumé structuré et concis du besoin en français : contexte, "
                    "réponses aux questions de qualification, budget/délai si mentionnés."
                ),
            },
        },
        "required": ["name", "email", "summary"],
    },
}

MAX_CHAT_MESSAGES = 24  # ~12 échanges — au-delà, on invite à passer par le formulaire/email
MAX_MESSAGE_LEN = 2000


def build_quote_system_prompt(service_label: str, questions: str) -> str:
    return (
        "Tu es l'assistant de qualification de devis pour rudy-ops.fr, le site "
        "vitrine freelance de Rudy (DevOps, infrastructure, développement web). "
        f"Le visiteur s'intéresse au service : {service_label}.\n\n"
        "Ton rôle : avoir une conversation brève et naturelle en français pour "
        "récolter le nom, l'email, et 2-3 informations de qualification utiles "
        "pour préparer un devis. Questions à explorer selon les réponses déjà "
        f"données (n'en pose pas plus de 2-3 au total, pas toutes d'un coup) :\n{questions}\n\n"
        "Règles :\n"
        "- Une ou deux questions par message maximum, ton direct et professionnel, pas de blabla.\n"
        "- Demande le nom et l'email si le visiteur ne les a pas encore donnés.\n"
        "- N'invente jamais d'information non fournie par le visiteur.\n"
        "- Une fois nom, email et assez de contexte réunis, appelle l'outil "
        "submit_quote_request — n'annonce pas la soumission en texte, l'outil s'en charge.\n"
        "- Si le visiteur ne veut pas continuer ou n'a pas d'email, invite-le à écrire "
        "directement à contact@rudy-ops.fr."
    )


def sanitize_chat_messages(raw: list) -> list[dict] | None:
    """Valide et normalise l'historique envoyé par le frontend.

    Ne fait confiance à rien côté client : rôles limités à user/assistant,
    contenu texte seul, longueur bornée. Retourne None si invalide.
    """
    if not isinstance(raw, list) or not raw or len(raw) > MAX_CHAT_MESSAGES:
        return None
    messages = []
    for entry in raw:
        if not isinstance(entry, dict):
            return None
        role = entry.get("role")
        content = entry.get("content")
        if role not in ("user", "assistant") or not isinstance(content, str):
            return None
        content = content.strip()
        if not content or len(content) > MAX_MESSAGE_LEN:
            return None
        messages.append({"role": role, "content": content})
    if messages[-1]["role"] != "user":
        return None
    return messages


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


@app.route("/quote-chat", methods=["OPTIONS"])
def quote_chat_preflight():
    return "", 204


@app.route("/quote-chat", methods=["POST"])
def quote_chat():
    body = request.get_json(silent=True) or {}

    service_slug = body.get("service")
    if service_slug not in SERVICE_LABELS:
        return jsonify({"ok": False, "error": "Service inconnu"}), 400

    messages = sanitize_chat_messages(body.get("messages"))
    if messages is None:
        if isinstance(body.get("messages"), list) and len(body["messages"]) >= MAX_CHAT_MESSAGES:
            return jsonify({
                "ok": True,
                "done": False,
                "reply": (
                    "La conversation devient longue — pour aller plus vite, "
                    "écrivez-moi directement à contact@rudy-ops.fr ou utilisez le formulaire ci-dessus."
                ),
            })
        return jsonify({"ok": False, "error": "Historique de conversation invalide"}), 400

    system_prompt = build_quote_system_prompt(
        SERVICE_LABELS[service_slug],
        SERVICE_QUESTIONS.get(service_slug, DEFAULT_QUESTIONS),
    )

    try:
        response = anthropic_client.messages.create(
            model=QUOTE_MODEL,
            max_tokens=1024,
            output_config={"effort": "low"},
            system=system_prompt,
            tools=[QUOTE_TOOL],
            messages=messages,
        )
    except anthropic.APIError:
        logger.exception("Échec de l'appel à l'API Claude pour /quote-chat")
        return jsonify({"ok": False, "error": "Assistant indisponible, réessayez plus tard."}), 502

    if response.stop_reason == "refusal":
        return jsonify({
            "ok": True,
            "done": False,
            "reply": "Je ne peux pas répondre à ce message. Pouvez-vous reformuler votre besoin ?",
        })

    tool_use = next((b for b in response.content if b.type == "tool_use"), None)

    if tool_use is None:
        reply = next((b.text for b in response.content if b.type == "text"), "").strip()
        if not reply:
            reply = "Pouvez-vous préciser votre besoin ?"
        return jsonify({"ok": True, "done": False, "reply": reply})

    quote_data = {
        "name": tool_use.input.get("name", ""),
        "email": tool_use.input.get("email", ""),
        "company": tool_use.input.get("company", ""),
        "subject": SERVICE_LABELS[service_slug],
        "summary": tool_use.input.get("summary", ""),
    }
    # Réutilise la même validation (longueurs, caractères de contrôle, format
    # email) que le formulaire statique — le contenu vient de Claude, pas d'un
    # champ de formulaire, mais il n'est pas plus digne de confiance pour autant.
    error = validate_fields(quote_data, required=("name", "email", "summary"))
    if error:
        logger.warning("Données de devis invalides depuis /quote-chat : %s", error)
        return jsonify({
            "ok": True,
            "done": False,
            "reply": (
                "Il me manque une information valide (nom ou email) pour finaliser "
                "la demande — pouvez-vous la repréciser ?"
            ),
        })

    try:
        client_body = (
            f"Bonjour {quote_data['name']},\n\n"
            "Merci pour votre message, je reviens vers vous rapidement "
            "(généralement sous 48h en semaine, un peu plus le week-end).\n\n"
            f"Récapitulatif de votre demande ({quote_data['subject']}) :\n"
            f"{quote_data['summary']}\n\n"
            "À bientôt,\nRudy"
        )
        send_email(quote_data["email"], "Votre demande — rudy-ops.fr", client_body)

        notify_body = (
            f"Nouvelle demande depuis l'assistant IA de rudy-ops.fr\n\n"
            f"Nom : {quote_data['name']}\n"
            f"Email : {quote_data['email']}\n"
            f"Entreprise : {quote_data.get('company') or '-'}\n"
            f"Service : {quote_data['subject']}\n\n"
            f"Résumé :\n{quote_data['summary']}"
        )
        send_email(NOTIFY_EMAIL, f"[rudy-ops.fr] Nouvelle demande (chat) — {quote_data['subject']}", notify_body)

        create_vikunja_task({**quote_data, "message": quote_data["summary"]})
    except Exception:
        logger.exception("Échec du traitement de la demande de devis (chat)")
        return jsonify({"ok": False, "error": "Erreur serveur, réessayez plus tard."}), 500

    return jsonify({
        "ok": True,
        "done": True,
        "reply": (
            f"Merci {quote_data['name']}, votre demande est enregistrée ! "
            "Je reviens vers vous rapidement par email."
        ),
    })


@app.route("/health")
def health():
    return jsonify({"ok": True})


@app.errorhandler(Exception)
def handle_unexpected_error(err):
    logger.exception("Erreur inattendue")
    return jsonify({"ok": False, "error": "Erreur serveur"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8082)
