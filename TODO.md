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
  créée dans le projet "Pro"

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

- [x] **1. Backend de réception** — `backend/app.py` (Flask), déployé comme second conteneur sur
  `lxc-portfolio` (port 8081 côté hôte), déployé via `.forgejo/workflows/deploy.yml`
- [x] **2. Email de confirmation automatique au client** — SMTP Gmail, pattern Alertmanager (App
  Password dédié, via variables d'environnement, secret destiné à OpenBao)
- [x] **3. Notification à Rudy** — email avec le détail complet de la demande
- [x] **4. Création automatique d'une tâche Vikunja** (projet "Pro")
- [x] **5. Anti-spam minimal** — honeypot `website` (caché en CSS, hors tabulation)
- [ ] **6. Documenter dans HOMELAB** — ajouter une entrée dans `Documentation/DID.md`/`TODO.md` du
  repo HOMELAB (nouveau service = nouvelle ligne dans l'inventaire) — pas encore fait, à ne pas oublier

## Assistant IA de devis (chatbot) — additif au formulaire, formulaire gardé en secours

Décidé : le chatbot vient **en plus** du formulaire statique (onglet "Assistant IA" à côté de
"Formulaire" sur `/contact`, cf. `ContactPanel.tsx`) — le formulaire reste l'option par défaut et ne
disparaît pas si le chat a un souci.

- [x] Endpoint `/quote-chat` (`backend/app.py`) — API Claude (**Sonnet 5**, `claude-sonnet-5` —
  suffisant pour ce cas d'usage simple, pas besoin d'Opus), avec un outil `submit_quote_request` que
  Claude appelle une fois nom/email/résumé réunis (jamais de texte libre parsé)
- [x] Questions de qualification adaptées par service (`SERVICE_QUESTIONS`, à garder synchronisé avec
  `src/data/services.tsx` si un service est ajouté/renommé)
- [x] Sécurité : les données extraites par Claude repassent par la **même validation** que le
  formulaire statique (longueur, format email, caractères de contrôle anti-injection SMTP) avant tout
  envoi d'email ou création de tâche Vikunja — testé (tentative d'injection d'en-tête via le nom,
  email invalide, historique de conversation trop long)
- [x] Composant `QuoteChat.tsx` (choix du service puis conversation), testé en local (build Astro +
  tests backend avec l'appel Claude mocké)
- [ ] **Reste à faire côté déploiement** (à faire par Rudy, pas depuis cet environnement) :
  - Ajouter le secret `ANTHROPIC_API_KEY` (OpenBao, comme les autres secrets du backend)
  - Passer la variable d'environnement au conteneur backend (même pattern que
    `SMTP_USER`/`VIKUNJA_API_TOKEN`)
  - Redéployer et tester une conversation réelle de bout en bout

## Calendrier — prise de rendez-vous (Cal.com auto-hébergé)

- Décidé le 07/07 : **Cal.com auto-hébergé**, pas de service tiers (Calendly/Cal.com cloud)
- La page `/disponibilites` a déjà l'emplacement prévu (placeholder "Emplacement du widget de prise
  de rendez-vous (Cal.com auto-hébergé)") — reste à déployer le service et brancher le vrai widget
- **Déploiement infra tracké dans HOMELAB**, pas ici : voir `Documentation/TODO.md` étape 31 du repo
  HOMELAB (LXC 111, 10.0.20.56, exposition publique sans Cloudflare Access — la réservation doit être
  possible sans compte)
- [ ] Une fois le service Cal.com en ligne : remplacer le placeholder dans
  `src/pages/disponibilites.astro` (la div avec la bordure en pointillés) par le vrai embed/lien
  Cal.com
- [ ] Décider du mode d'intégration : iframe embed officiel Cal.com vs simple lien vers
  `cal.rudy-ops.fr/<slug>` qui ouvre dans un nouvel onglet — l'embed donne une meilleure UX (reste
  sur le site) mais demande le script `embed.js` de Cal.com
- [ ] Vérifier la sync calendrier réel (Google Calendar ou CalDAV, à trancher côté HOMELAB étape 31)
  avant de considérer la fonctionnalité complète

## Non-objectifs (pour l'instant)

- Pas de CRM complet — Vikunja suffit pour tracer les demandes à ce stade
- Pas de réponse générée par IA dans l'email de confirmation — accusé de réception simple d'abord,
  personnalisation IA éventuelle plus tard si le volume de demandes le justifie
