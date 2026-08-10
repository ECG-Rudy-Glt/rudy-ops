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

- [x] **1. Backend de réception** — `backend/app.py` (Flask), déployé comme troisième conteneur sur
  `lxc-portfolio` (port 8082 côté hôte — 8081 est le frontend), pipeline
  `.forgejo/workflows/deploy-backend.yml` écrit le 10/08 (manquait jusque-là)
- [x] **2. Email de confirmation automatique au client** — SMTP Gmail, pattern Alertmanager (App
  Password dédié, via variables d'environnement, secret destiné à OpenBao)
- [x] **3. Notification à Rudy** — email avec le détail complet de la demande
- [x] **4. Création automatique d'une tâche Vikunja** (projet "Pro", id 3) — token API +
  `VIKUNJA_PROJECT_ID` posés en secrets Forgejo Actions le 10/08
- [x] **5. Anti-spam minimal** — honeypot `website` (caché en CSS, hors tabulation)
- [x] **6. Documenter dans HOMELAB** — `Documentation/DID.md` (entrée 10/08) et `Documentation/TODO.md`
  (item 44) du repo HOMELAB, fait

### Reste à faire pour un déploiement réel (10/08)

- [ ] Ajouter la clé publique `rudy-ops-deploy` dans `/root/.ssh/authorized_keys` sur
  `lxc-portfolio` (bloquant — pas d'accès SSH direct depuis la session qui a préparé ce qui précède)
- [ ] Secrets SMTP (`SMTP_USER`/`SMTP_PASSWORD`/`NOTIFY_EMAIL`) en secrets Forgejo Actions
- [ ] Copie de tous les secrets applicatifs dans OpenBao `secret/homelab/rudy-ops`
- [ ] Ingress Cloudflare Tunnel (`rudy-ops.fr`, `api.rudy-ops.fr`) sur `lxc-portfolio` + routes DNS

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
- [x] **10/08** : `GEMINI_API_KEY` rendue optionnelle dans `backend/app.py` — décision utilisateur
  de garder le chatbot désactivé pour l'instant, le backend (formulaire inclus) ne doit pas en
  dépendre pour démarrer. `/quote-chat` répond `503` proprement tant qu'aucune clé n'est fournie.
- [ ] **Activation différée, quand voulu** :
  - Générer `GEMINI_API_KEY` sur aistudio.google.com (tier gratuit)
  - Poser le secret `GEMINI_API_KEY` en secret Forgejo Actions du repo
  - Redéployer (`git push` suffit, la CI relit les secrets à chaque run) et tester une
    conversation réelle de bout en bout

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
