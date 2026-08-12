# TODO — rudy-ops.fr

## Corrections déjà faites (07/07)

- [x] Lien cassé "Créneaux ouverts en soirée et week-end" (`/disponibilités` avec accent → `/disponibilites`)
- [x] Contours de champs/tags invisibles en mode clair (`--card-border` corrigée dans `global.css`)
- [x] Surlignage de sélection de texte harmonisé au bleu du thème (`::selection`)
- [x] Sujet de la demande : liste déroulante (services + "Autre") au lieu de cases à cocher
- [x] Retrait de la pastille "Disponible en soirée et week-end" du Hero (redondante avec l'AvailabilityCard)
- [x] Liens vers l'ancien domaine portfolio (`portfolio.rudy-ops.fr`) corrigés vers `portfolio.gault-rudy.com`

## État actuel du formulaire de contact — FAIT (voir plan d'implémentation ci-dessous)

- `ContactForm.tsx` poste en JSON vers le backend self-hosted (`backend/app.py`, `/contact`), plus de
  Formspree
- Champs actuels : Nom, Email, Entreprise (optionnel), Sujet de la demande (liste déroulante, un
  sujet parmi les services + "Autre"), Message, + honeypot caché anti-spam
- Envoi automatique : accusé de réception au client, notification complète à Rudy, tâche Vikunja
  créée dans le projet **"Freelance"** (id 6, basculé depuis "Pro" le 10/08 — projet dédié aux
  demandes rudy-ops.fr), + notification Telegram (bot `Rudy_freelance_bot`)

## Objectif — système de réponse automatique

Quand quelqu'un envoie une demande de devis, deux choses doivent se produire automatiquement :
1. **Le client reçoit un accusé de réception immédiat** (email), avec un délai de réponse indicatif
   cohérent avec la dispo affichée sur le site ("soirée et week-end")
2. **La demande arrive quelque part d'exploitable** pour Rudy — pas juste un email perdu dans la boîte

## Options envisagées

| Option | Effort | Avantage | Inconvénient |
|---|---|---|---|
| **Formspree — plugin autoresponse** | Très faible (config UI) | Zéro code | Payant au-delà du plan gratuit, personnalisation limitée, dépendance à un tiers |
| **Backend self-hosted maison** | Moyen | Contrôle total, s'intègre au reste du homelab (SMTP déjà en place pour Alertmanager/Vaultwarden), gratuit | Il faut l'écrire et l'exposer |
| **Backend self-hosted + création auto d'une tâche Vikunja** | Moyen-élevé | Idem + chaque demande devient une tâche traçable dans Vikunja (projet "Pro"), rien ne se perd | Un peu plus de code, dépendance à l'API Vikunja |

## Décision (à valider avec Rudy avant implémentation)

Piste retenue à date : **backend self-hosted + Vikunja**, cohérent avec l'infra déjà en place
(OpenBao pour les secrets, pattern SMTP Gmail déjà utilisé pour Alertmanager/Vaultwarden, API Vikunja
déjà utilisée pour gérer des tâches). Dogfooding pertinent vu que le site vend justement de
l'intégration IA/automatisation dans les workflows.

## Plan d'implémentation — FAIT

- [x] **1. Backend de réception** — `backend/app.py` (Flask), déployé comme troisième conteneur sur
  `lxc-portfolio` (port 8082 côté hôte — 8081 est le frontend), pipeline
  `.forgejo/workflows/deploy-backend.yml` écrit le 10/08 (manquait jusque-là)
- [x] **2. Email de confirmation automatique au client** — SMTP Gmail, pattern Alertmanager (App
  Password dédié, via variables d'environnement, secret destiné à OpenBao)
- [x] **3. Notification à Rudy** — email avec le détail complet de la demande
- [x] **4. Création automatique d'une tâche Vikunja** (projet **"Freelance"**, id 6 — bascule
  depuis "Pro" le 10/08) — token API + `VIKUNJA_PROJECT_ID` posés en secrets Forgejo Actions
- [x] **5. Anti-spam minimal** — honeypot `website` (caché en CSS, hors tabulation)
- [x] **6. Documenter dans HOMELAB** — `Documentation/DID.md` (entrées 10/08) et
  `Documentation/TODO.md` (items 31/44) du repo HOMELAB, fait

### Déploiement réel — FAIT le 10/08

- [x] Clé publique `rudy-ops-deploy` déjà en place, backend accessible en SSH
- [x] Secrets SMTP OVH (`contact@rudy-ops.fr`, `SMTP_HOST=ssl0.ovh.net:587`), Vikunja, Gemini,
  Telegram — tous stockés dans OpenBao `secret/homelab/rudy-ops` (source de vérité) et copiés en
  secrets Forgejo Actions
- [x] Ingress Cloudflare Tunnel (`rudy-ops.fr`, `api.rudy-ops.fr`) — déjà en place avant cette
  session
- [x] **Test réel de bout en bout** : `/contact` → email client + notification + tâche Vikunja +
  Telegram, tous confirmés reçus
- [x] **Bugs trouvés et corrigés en testant** : `SMTP_HOST`/`SMTP_PORT` et
  `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` manquaient dans le `docker run` de
  `deploy-backend.yml` malgré leur présence dans le bloc `env:` du step CI (deux oublis
  distincts, voir `Documentation/DID.md` 10/08 du repo HOMELAB pour le détail)

## Assistant IA de devis (chatbot) — additif au formulaire, formulaire gardé en secours

Décidé : le chatbot vient **en plus** du formulaire statique (onglet "Assistant IA" à côté de
"Formulaire" sur `/contact`, cf. `ContactPanel.tsx`) — le formulaire reste l'option par défaut et ne
disparaît pas si le chat a un souci.

- [x] Endpoint `/quote-chat` (`backend/app.py`) — **API Gemini (Google), tier gratuit** (changé depuis
  Claude le 27/07 : pas de nouvelle facturation à ouvrir pour ce volume). Utilise l'API Interactions
  (`client.interactions.create`, modèle `gemini-3.6-flash`), avec un outil `submit_quote_request` que
  le modèle appelle une fois nom/email/résumé réunis (jamais de texte libre parsé). L'historique de
  conversation vit côté Google (`previous_interaction_id`) — le backend Flask reste sans état, le
  frontend ne renvoie que le dernier message + cet identifiant.
- [x] Le prompt système laisse le modèle poser **autant de questions que nécessaire** pour bien
  cadrer le projet (pas limité à 2-3) — l'objectif est un résumé exploitable pour un devis, pas une
  conversation minimale. Mais adaptatif dans les deux sens : si le message initial est déjà bien
  détaillé, pas de questions superflues (juste une confirmation) ; et si le visiteur ne veut pas
  répondre à plus de questions ou veut envoyer tel quel, le modèle n'insiste pas et soumet avec ce
  qu'il a (nom/email restent nécessaires, rien d'autre)
- [x] Questions de qualification adaptées par service (`SERVICE_QUESTIONS`, à garder synchronisé avec
  `src/data/services.tsx` si un service est ajouté/renommé)
- [x] Bulles de suggestion de premier message par service (`STARTER_PROMPTS` dans `QuoteChat.tsx`) —
  réduit la friction pour démarrer, un clic envoie le texte
- [x] Sécurité : les données extraites par le modèle repassent par la **même validation** que le
  formulaire statique (longueur, format email, caractères de contrôle anti-injection SMTP) avant tout
  envoi d'email ou création de tâche Vikunja — testé (tentative d'injection d'en-tête via le nom,
  email invalide, message trop long, identifiant de conversation malformé)
- [x] Composant `QuoteChat.tsx` (choix du service puis conversation), testé en local (build Astro +
  tests backend avec l'appel Claude mocké)
- [x] **10/08** : `GEMINI_API_KEY` rendue optionnelle dans `backend/app.py` — le backend
  (formulaire inclus) ne dépend pas d'elle pour démarrer, `/quote-chat` répondrait `503`
  proprement si elle manquait.
- [x] **Activée le 10/08** : clé Gemini générée et posée (OpenBao + secrets Forgejo Actions) —
  chatbot en ligne. Pas encore testé avec une vraie conversation multi-tours de bout en bout
  (juste `/contact` classique testé pour l'instant).

## Calendrier — prise de rendez-vous (Cal.com auto-hébergé) — déployé le 10/08

- Décidé le 07/07 : **Cal.com auto-hébergé**, pas de service tiers (Calendly/Cal.com cloud)
- **Déploiement infra tracké dans HOMELAB** : voir `Documentation/TODO.md` étape 31 + `DID.md`
  10/08 du repo HOMELAB (LXC 111, `10.0.20.56`, public sur `https://cal.rudy-ops.fr` sans
  Cloudflare Access — réservation possible sans compte, confirmé HTTP 200)
- [x] Widget branché dans `src/pages/disponibilites.astro` — embed inline officiel Cal.com
  (`embed.js`), pas un simple iframe/lien (meilleure UX, reste sur le site). `calLink` = username
  `rudy`, **confirmé** (`https://cal.rudy-ops.fr/rudy` répond 200, compte créé)
- [x] **Webhook Cal.com → tâche Vikunja avec la date du RDV** (demandé 10/08, fait le 11/08) —
  route `/calcom-webhook` : vérifie la signature `X-Cal-Signature-256` (HMAC-SHA256), traite
  `BOOKING_CREATED`, crée la tâche dans le projet "Freelance" avec `due_date` = `startTime`.
  Secret `CALCOM_WEBHOOK_SECRET` dans OpenBao + Forgejo Actions. **Testé réel** (signature valide
  simulée, tâche créée avec la bonne date en fuseau local). **Reste à faire côté Cal.com** :
  configurer le webhook dans Settings → Developer → Webhooks avec l'URL
  `https://api.rudy-ops.fr/calcom-webhook` et le secret ci-dessus (pas fait — nécessite l'accès
  admin Cal.com)
- [ ] **Disponibilités Cal.com à restreindre à 18h-22h** (signalé 11/08) — actuellement configuré
  avec les horaires par défaut de Cal.com, à ajuster dans Settings → Availability (fait par
  l'utilisateur, pas depuis cet environnement)
- [ ] **Sync calendrier Outlook — bloqué** : CalDAV générique incompatible avec Outlook.com/
  Microsoft 365 (abandonné par Microsoft), connecteur "Microsoft Exchange" (EWS) tenté ensuite →
  `401 Unauthorized` (authentification basique désactivée côté Microsoft). Pas bloquant pour les
  réservations clients (Cal.com gère ses dispos tout seul), mais pas de garde-fou contre un
  double-booking avec d'autres rendez-vous hors Cal.com pour l'instant. Reprendre avec soit une
  app OAuth "Office 365 Calendar" (enregistrement Azure AD requis), soit Google Calendar en repli

## Reste ouvert

- [x] **Email de confirmation stylisé** (fait le 11/08) — `send_email()` accepte un `html_body`
  optionnel (`multipart/alternative`, repli texte brut conservé), template inline-styled cohérent
  avec la charte (`client_confirmation_html()`), branché sur `/contact` et `/quote-chat`. Champs
  utilisateur échappés (`html.escape`) avant injection. Testé (email réel envoyé) — **à confirmer
  visuellement** par Rudy dans sa boîte mail, pas vérifiable depuis cet environnement
- [x] **Bug corrigé** : `--accent` (utilisée dans `ContactPanel.tsx` et `QuoteChat.tsx`) n'était
  définie nulle part dans `global.css` → bouton "Assistant IA" actif blanc sur fond clair,
  illisible. Remplacée par `--terracotta`, seule couleur d'accent réelle de la palette

## Page tarifs (`/tarifs`) — FAIT

- [x] TJM unique 400€/j, aligné sur les tarifs freelance junior marché français 2026 (recherche par
  spécialité faite le 27/07 : DevOps/Sécu/IA ~400-550€/j, dev web/infra ~300-400€/j)
- [x] Fourchettes indicatives par prestation (TJM × durée), avec mention explicite "devis final établi
  selon le projet" — pas des prix figés
- [x] Section "Périmètre par prestation" (inclus/hors périmètre par service, `<details>` par service) +
  limites générales transverses (pas de langages compilés, pas d'intervention physique, pas d'astreinte
  24/7, pas de certification engageante type ISO 27001/PASSI)
- [x] Mention transparente de l'usage de Claude dans le processus de travail de Rudy (pas caché)
- [x] Lien "Tarifs" ajouté dans `Nav.tsx`
- Si les services évoluent (nouveau service, nouvelle limite découverte en mission), penser à
  synchroniser `src/pages/tarifs.astro` en plus de `src/data/services.tsx`

## Non-objectifs (pour l'instant)

- Pas de CRM complet — Vikunja suffit pour tracer les demandes à ce stade
- Pas de réponse générée par IA dans l'email de confirmation — accusé de réception simple d'abord,
  personnalisation IA éventuelle plus tard si le volume de demandes le justifie
