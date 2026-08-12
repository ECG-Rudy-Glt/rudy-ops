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
assez d'informations réunies. Les données extraites par le modèle repassent
par la même validation que le formulaire (validate_fields) avant tout envoi —
le contenu généré par la conversation n'est jamais utilisé tel quel.

Utilise l'API Gemini (Google), tier gratuit — pas de coût pour ce volume, pas
de nouvelle facturation à ouvrir. L'API Interactions de Gemini est gérée côté
serveur Google (previous_interaction_id), donc /quote-chat est sans état côté
Flask : le frontend renvoie juste le dernier interaction_id, pas tout
l'historique.

Variables d'environnement requises en plus de celles du formulaire :
  GEMINI_API_KEY (clé générée sur aistudio.google.com, tier gratuit — secret
  destiné à OpenBao comme les autres, passé via -e dans le playbook Ansible,
  cf. pattern documenté dans deploy-vikunja.yml).
"""
import hashlib
import hmac
import html
import logging
import os
import re
import smtplib
from email.message import EmailMessage

import requests
from flask import Flask, jsonify, request
from google import genai
from google.genai import errors as genai_errors

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024  # 64 Ko — couvre l'historique du chat, coupe l'abus de payload

# Configurable, pas figé sur un fournisseur (passé de Gmail à l'email OVH du domaine le 10/08).
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]
NOTIFY_EMAIL = os.environ["NOTIFY_EMAIL"]

VIKUNJA_API_URL = os.environ["VIKUNJA_API_URL"]  # ex: http://10.0.20.52:3456/api/v1
VIKUNJA_API_TOKEN = os.environ["VIKUNJA_API_TOKEN"]
VIKUNJA_PROJECT_ID = os.environ["VIKUNJA_PROJECT_ID"]

# Optionnel : le chatbot de devis (/quote-chat) est un additif au formulaire
# statique (toujours fonctionnel sans elle), pas un prérequis au démarrage —
# désactivé tant qu'aucune clé n'est fournie plutôt que de faire planter tout
# le backend (y compris /contact) pour une fonctionnalité annexe.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# Optionnel également : notification Telegram en plus de l'email, pour être
# prévenu plus vite qu'une demande arrive. Silencieux si non configuré (pas de
# raison de bloquer /contact pour un canal de notif secondaire).
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Optionnel également : webhook Cal.com (BOOKING_CREATED -> tâche Vikunja avec la date du
# rendez-vous). /calcom-webhook répond 503 tant qu'aucun secret n'est configuré, plutôt que de
# bloquer le démarrage du backend pour une intégration annexe.
CALCOM_WEBHOOK_SECRET = os.environ.get("CALCOM_WEBHOOK_SECRET")

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


def send_email(to: str, subject: str, body: str, html_body: str | None = None) -> None:
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(msg)


def client_confirmation_html(name: str, subject: str, message: str) -> str:
    """Email HTML pour la confirmation client — styles inline (compatibilité clients mail),
    repli texte brut toujours envoyé en parallèle (multipart/alternative, cf. send_email).
    Champs échappés (html.escape) : injectés dans du HTML, contrairement au texte brut."""
    name, subject, message = html.escape(name), html.escape(subject), html.escape(message)
    return f"""\
<div style="background:#fbfaf7;padding:32px 16px;font-family:Georgia,'Times New Roman',serif;">
  <table role="presentation" width="100%" style="max-width:520px;margin:0 auto;background:#ffffff;
      border-radius:16px;overflow:hidden;border:1px solid rgba(28,26,23,0.12);">
    <tr><td style="background:#a2532c;padding:20px 28px;">
      <span style="color:#fbfaf7;font-size:20px;font-weight:bold;">rudy-ops.fr</span>
    </td></tr>
    <tr><td style="padding:28px;">
      <p style="color:#1c1a17;font-size:16px;margin:0 0 16px;">Bonjour {name},</p>
      <p style="color:#1c1a17;font-size:15px;line-height:1.6;margin:0 0 20px;">
        Merci pour votre message, je reviens vers vous rapidement
        (généralement sous 48h en semaine, un peu plus le week-end).
      </p>
      <table role="presentation" width="100%" style="background:#fbfaf7;border-radius:12px;
          border:1px solid rgba(28,26,23,0.1);margin:0 0 20px;">
        <tr><td style="padding:16px 20px;">
          <p style="color:#8a8478;font-size:12px;text-transform:uppercase;letter-spacing:0.05em;
              margin:0 0 4px;">Sujet</p>
          <p style="color:#1c1a17;font-size:15px;margin:0 0 14px;">{subject}</p>
          <p style="color:#8a8478;font-size:12px;text-transform:uppercase;letter-spacing:0.05em;
              margin:0 0 4px;">Message</p>
          <p style="color:#1c1a17;font-size:15px;line-height:1.5;margin:0;white-space:pre-wrap;">{message}</p>
        </td></tr>
      </table>
      <p style="color:#1c1a17;font-size:15px;margin:0;">À bientôt,<br><strong>Rudy</strong></p>
    </td></tr>
    <tr><td style="padding:16px 28px;border-top:1px solid rgba(28,26,23,0.1);">
      <p style="color:#8a8478;font-size:12px;margin:0;">rudy-ops.fr — DevOps &amp; Infrastructure as Code</p>
    </td></tr>
  </table>
</div>"""


def notify_telegram(text: str) -> None:
    """Notif best-effort — n'échoue jamais bruyamment, un canal secondaire ne doit pas
    faire échouer /contact si Telegram est down ou mal configuré."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=10,
        )
    except Exception:
        logger.exception("Échec de la notification Telegram (non bloquant)")


def create_vikunja_task(data: dict, due_date: str | None = None) -> None:
    title = f"{data['name']} : {data['subject']}"
    company = f" ({data['company']})" if data.get("company") else ""
    description = (
        f"**Email** : {data['email']}\n"
        f"**Entreprise** : {data.get('company') or '-'}\n"
        f"**Sujet** : {data['subject']}\n\n"
        f"{data['message']}"
    )
    task = {"title": title + company, "description": description}
    if due_date:
        task["due_date"] = due_date
    resp = requests.put(
        f"{VIKUNJA_API_URL}/projects/{VIKUNJA_PROJECT_ID}/tasks",
        headers={"Authorization": f"Bearer {VIKUNJA_API_TOKEN}"},
        json=task,
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
#
# Gemini (tier gratuit) plutôt que Claude ici : ce chatbot ne justifie pas
# d'ouvrir une facturation API séparée pour ce volume. L'API Interactions
# gère l'historique de conversation côté Google (previous_interaction_id) —
# le frontend ne renvoie que le dernier message + cet identifiant, pas tout
# l'historique.

QUOTE_MODEL = "gemini-3.6-flash"  # tier gratuit — largement suffisant pour ce volume

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

# Forme attendue par l'API Interactions de Gemini pour un tool de type
# "function" : {"type": "function", "name", "description", "parameters"}
# (vérifié empiriquement contre google-genai 2.14 — pas de "input_schema"
# imbriqué comme chez Claude, "parameters" est directement au même niveau).
QUOTE_TOOL = {
    "type": "function",
    "name": "submit_quote_request",
    "description": (
        "Soumets la demande de devis une fois que tu as le nom, l'email, et un "
        "résumé structuré du besoin incluant les réponses aux questions de "
        "qualification pertinentes. N'appelle cet outil qu'après au moins un échange "
        "avec le visiteur (une question de qualification, ou une confirmation si son "
        "message initial était déjà bien détaillé) — jamais dès le tout premier message "
        "sans aucune interaction, sauf si le visiteur demande explicitement d'envoyer "
        "tel quel."
    ),
    "parameters": {
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

MAX_MESSAGE_LEN = 2000
# previous_interaction_id est un identifiant opaque généré par Google, jamais
# construit par le client — on ne fait que le relayer. Bornage défensif du
# format malgré tout, plutôt que de faire confiance à un champ non typé venu
# du frontend.
INTERACTION_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,200}$")


def build_quote_system_prompt(service_label: str, questions: str) -> str:
    return (
        "Tu es l'assistant de qualification de devis pour rudy-ops.fr, le site "
        "vitrine freelance de Rudy (DevOps, infrastructure, développement web). "
        f"Le visiteur s'intéresse au service : {service_label}.\n\n"
        "Ton rôle : avoir une conversation naturelle en français pour récolter le nom, "
        "l'email, et un cadrage du projet suffisamment détaillé pour que Rudy puisse "
        "préparer un devis précis sans avoir à recontacter le visiteur pour des infos "
        "manquantes. Explore ces pistes selon les réponses déjà données, et n'hésite pas "
        f"à creuser au-delà si une réponse appelle une précision utile :\n{questions}\n\n"
        "Règles :\n"
        "- Une ou deux questions par message maximum (jamais toutes d'un coup), ton direct "
        "et professionnel, pas de blabla.\n"
        "- Adapte-toi à ce que le visiteur a déjà donné : si son message initial est déjà "
        "détaillé et bien cadré, ne pose pas de questions superflues juste pour la forme — "
        "propose de confirmer et de soumettre directement (demande juste nom/email si "
        "manquants). Si le cadrage est encore flou, pose les questions utiles une à une.\n"
        "- Si le visiteur dit explicitement qu'il ne veut pas répondre à plus de questions, "
        "qu'il est pressé, ou qu'il veut envoyer sa demande telle quelle : n'insiste jamais. "
        "Soumets l'outil avec les informations déjà réunies (nom et email restent "
        "nécessaires, redemande-les si vraiment manquants, mais rien d'autre).\n"
        "- Demande le nom et l'email si le visiteur ne les a pas encore donnés.\n"
        "- N'invente jamais d'information non fournie par le visiteur.\n"
        "- Une fois nom, email et un cadrage suffisant réunis (ou dès que le visiteur signale "
        "vouloir s'arrêter là), appelle l'outil submit_quote_request — n'annonce pas la "
        "soumission en texte, l'outil s'en charge.\n"
        "- Si le visiteur ne veut pas continuer ou n'a pas d'email, invite-le à écrire "
        "directement à contact@rudy-ops.fr."
    )


def sanitize_chat_input(body: dict) -> tuple[str, str | None] | None:
    """Valide le message entrant et l'identifiant de conversation.

    Ne fait confiance à rien côté client. Retourne (message, previous_interaction_id)
    ou None si invalide. L'historique de conversation n'est pas géré ici — il vit
    côté Google (previous_interaction_id), le backend Flask reste sans état.
    """
    message = body.get("message")
    if not isinstance(message, str):
        return None
    message = message.strip()
    if not message or len(message) > MAX_MESSAGE_LEN:
        return None

    previous_interaction_id = body.get("previous_interaction_id")
    if previous_interaction_id is not None:
        if not isinstance(previous_interaction_id, str) or not INTERACTION_ID_RE.match(previous_interaction_id):
            return None

    return message, previous_interaction_id


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
        send_email(
            data["email"],
            "Votre demande, rudy-ops.fr",
            client_body,
            html_body=client_confirmation_html(data["name"], data["subject"], data["message"]),
        )

        notify_body = (
            f"Nouvelle demande depuis rudy-ops.fr\n\n"
            f"Nom : {data['name']}\n"
            f"Email : {data['email']}\n"
            f"Entreprise : {data.get('company') or '-'}\n"
            f"Sujet : {data['subject']}\n\n"
            f"Message :\n{data['message']}"
        )
        send_email(NOTIFY_EMAIL, f"[rudy-ops.fr] Nouvelle demande : {data['subject']}", notify_body)

        create_vikunja_task(data)
        notify_telegram(f"Nouvelle demande (formulaire) : {data['name']} — {data['subject']}")
    except Exception:
        logger.exception("Échec du traitement de la demande de contact")
        return jsonify({"ok": False, "error": "Erreur serveur, réessayez plus tard."}), 500

    return jsonify({"ok": True}), 200


@app.route("/quote-chat", methods=["OPTIONS"])
def quote_chat_preflight():
    return "", 204


@app.route("/quote-chat", methods=["POST"])
def quote_chat():
    if genai_client is None:
        return jsonify({
            "ok": False,
            "error": "Assistant IA temporairement désactivé, utilisez le formulaire ci-contre.",
        }), 503

    body = request.get_json(silent=True) or {}

    service_slug = body.get("service")
    if service_slug not in SERVICE_LABELS:
        return jsonify({"ok": False, "error": "Service inconnu"}), 400

    sanitized = sanitize_chat_input(body)
    if sanitized is None:
        return jsonify({"ok": False, "error": "Message invalide"}), 400
    message, previous_interaction_id = sanitized

    system_prompt = build_quote_system_prompt(
        SERVICE_LABELS[service_slug],
        SERVICE_QUESTIONS.get(service_slug, DEFAULT_QUESTIONS),
    )

    try:
        interaction = genai_client.interactions.create(
            model=QUOTE_MODEL,
            input=message,
            system_instruction=system_prompt,
            tools=[QUOTE_TOOL],
            previous_interaction_id=previous_interaction_id,
        )
    except genai_errors.APIError:
        logger.exception("Échec de l'appel à l'API Gemini pour /quote-chat")
        return jsonify({"ok": False, "error": "Assistant indisponible, réessayez plus tard."}), 502

    fc_step = next((s for s in (interaction.steps or []) if s.type == "function_call"), None)

    if fc_step is None:
        reply = (interaction.output_text or "").strip() or "Pouvez-vous préciser votre besoin ?"
        return jsonify({
            "ok": True,
            "done": False,
            "reply": reply,
            "interaction_id": interaction.id,
        })

    quote_data = {
        "name": fc_step.arguments.get("name", ""),
        "email": fc_step.arguments.get("email", ""),
        "company": fc_step.arguments.get("company", ""),
        "subject": SERVICE_LABELS[service_slug],
        "summary": fc_step.arguments.get("summary", ""),
    }
    # Réutilise la même validation (longueurs, caractères de contrôle, format
    # email) que le formulaire statique — le contenu vient du modèle, pas d'un
    # champ de formulaire, mais il n'est pas plus digne de confiance pour autant.
    error = validate_fields(quote_data, required=("name", "email", "summary"))
    if error:
        logger.warning("Données de devis invalides depuis /quote-chat : %s", error)
        return jsonify({
            "ok": True,
            "done": False,
            "reply": (
                "Il me manque une information valide (nom ou email) pour finaliser "
                "la demande, pouvez-vous la repréciser ?"
            ),
            "interaction_id": interaction.id,
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
        send_email(
            quote_data["email"],
            "Votre demande, rudy-ops.fr",
            client_body,
            html_body=client_confirmation_html(
                quote_data["name"], quote_data["subject"], quote_data["summary"]
            ),
        )

        notify_body = (
            f"Nouvelle demande depuis l'assistant IA de rudy-ops.fr\n\n"
            f"Nom : {quote_data['name']}\n"
            f"Email : {quote_data['email']}\n"
            f"Entreprise : {quote_data.get('company') or '-'}\n"
            f"Service : {quote_data['subject']}\n\n"
            f"Résumé :\n{quote_data['summary']}"
        )
        send_email(NOTIFY_EMAIL, f"[rudy-ops.fr] Nouvelle demande (chat) : {quote_data['subject']}", notify_body)

        create_vikunja_task({**quote_data, "message": quote_data["summary"]})
        notify_telegram(f"Nouvelle demande (chat) : {quote_data['name']} — {quote_data['subject']}")
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


@app.route("/calcom-webhook", methods=["POST"])
def calcom_webhook():
    """Reçoit les événements Cal.com (Settings -> Developer -> Webhooks côté Cal.com).

    Ne traite que BOOKING_CREATED : crée une tâche Vikunja avec la date du rendez-vous
    (due_date = startTime), même projet "Freelance" que le formulaire/chatbot. Les autres
    triggers (CANCELLED, RESCHEDULED, ...) sont accusés 200 sans action pour l'instant.
    """
    if not CALCOM_WEBHOOK_SECRET:
        logger.error("CALCOM_WEBHOOK_SECRET non configuré — webhook refusé")
        return jsonify({"ok": False, "error": "webhook non configuré"}), 503

    raw_body = request.get_data()
    signature = request.headers.get("X-Cal-Signature-256", "")
    expected = hmac.new(CALCOM_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        logger.warning("Signature webhook Cal.com invalide")
        return jsonify({"ok": False, "error": "signature invalide"}), 401

    body = request.get_json(silent=True) or {}
    if body.get("triggerEvent") != "BOOKING_CREATED":
        return jsonify({"ok": True}), 200

    payload = body.get("payload", {})
    attendees = payload.get("attendees") or [{}]
    attendee = attendees[0]

    data = {
        "name": attendee.get("name") or "Inconnu",
        "email": attendee.get("email") or "-",
        "company": "",
        "subject": payload.get("title") or "Rendez-vous Cal.com",
        "message": payload.get("description") or "(pas de description fournie)",
    }

    try:
        create_vikunja_task(data, due_date=payload.get("startTime"))
        notify_telegram(f"Nouveau RDV Cal.com : {data['name']} — {payload.get('startTime', '?')}")
    except Exception:
        logger.exception("Échec du traitement du webhook Cal.com")
        return jsonify({"ok": False, "error": "erreur serveur"}), 500

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
