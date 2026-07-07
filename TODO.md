# TODO — rudy-ops.fr

## Corrections déjà faites (07/07)

- [x] Lien cassé "Créneaux ouverts en soirée et week-end" (`/disponibilités` avec accent → `/disponibilites`)
- [x] Contours de champs/tags invisibles en mode clair (`--card-border` corrigée dans `global.css`)
- [x] Surlignage de sélection de texte harmonisé au bleu du thème (`::selection`)
- [x] Sujet de la demande : liste déroulante (services + "Autre") au lieu de cases à cocher
- [x] Retrait de la pastille "Disponible en soirée et week-end" du Hero (redondante avec l'AvailabilityCard)
- [x] Liens vers l'ancien domaine portfolio (`portfolio.rudy-ops.fr`) corrigés vers `portfolio.gault-rudy.com`

## État actuel du formulaire de contact

- `ContactForm.tsx` poste vers Formspree (`FORM_ENDPOINT` = placeholder `REPLACE_WITH_YOUR_FORM_ID`,
  **pas encore configuré** — le formulaire ne fonctionne pas tel quel)
- Champs actuels : Nom, Email, Entreprise (optionnel), Sujet de la demande (liste déroulante, un
  sujet parmi les services + "Autre"), Message
- Aucune réponse automatique à l'envoi — le client voit juste "Message envoyé", sans email de
  confirmation

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

## Plan d'implémentation

- [ ] **1. Backend de réception** — petit service (Node/Python) qui reçoit le POST du formulaire
  - À héberger sur le homelab (nouveau LXC léger, ou conteneur sur un hôte Docker existant) et exposer
    publiquement via le même pattern Cloudflare Tunnel que le portfolio/Vikunja
  - Remplacer `FORM_ENDPOINT` dans `ContactForm.tsx` par l'URL de ce backend
- [ ] **2. Email de confirmation automatique au client**
  - SMTP Gmail (réutiliser le pattern Alertmanager : App Password dédié, stocké dans OpenBao
    `secret/homelab/rudy-ops`, jamais dans le code)
  - Contenu : accusé de réception, rappel des sujets sélectionnés, délai de réponse indicatif
- [ ] **3. Notification à Rudy**
  - Email avec le détail complet de la demande (nom, email, entreprise, sujets, message)
- [ ] **4. Création automatique d'une tâche Vikunja** (projet "Pro")
  - Titre = nom + sujets sélectionnés, description = message complet
  - Token API Vikunja dédié (scope limité au projet Pro si possible), stocké dans OpenBao
- [ ] **5. Anti-spam minimal**
  - Honeypot field (champ caché, invisible pour un humain, rempli par les bots) — simple et suffisant
    à ce stade, pas besoin de reCAPTCHA
- [ ] **6. Documenter dans HOMELAB** — si le backend est hébergé sur l'infra existante, ajouter une
  entrée dans `Documentation/DID.md`/`TODO.md` du repo HOMELAB (nouveau service = nouvelle ligne dans
  l'inventaire), pas seulement dans ce TODO.md local

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
