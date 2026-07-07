import {
  IconAutomation,
  IconServer,
  IconGlobe,
  IconLayers,
  IconNetwork,
  IconBot,
  IconShield,
} from "../components/icons";

export const services = [
  {
    slug: "devops-iac",
    Icon: IconAutomation,
    title: "DevOps & Infrastructure as Code",
    description:
      "Automatisation de bout en bout : provisioning, CI/CD, supervision. Vos infrastructures deviennent versionnées, testables et reproductibles.",
    tags: ["Terraform", "Ansible", "CI/CD"],
    href: "/services/devops-iac",
    longDescription:
      "Toute infrastructure devrait pouvoir être détruite et recréée à l'identique en quelques minutes. Je mets en place des pipelines CI/CD et des configurations Terraform/Ansible versionnées, testées et documentées, pour que votre infrastructure devienne un actif fiable plutôt qu'une boîte noire fragile.",
    bullets: [
      "Ecriture et audit de modules Terraform réutilisables",
      "Playbooks Ansible idempotents et documentés",
      "Pipelines CI/CD (tests, build, déploiement automatise)",
      "Supervision et alerting sur l'ensemble de la chaine",
    ],
  },
  {
    slug: "infra-on-premise",
    Icon: IconServer,
    title: "Infrastructure on-premise",
    description:
      "Conception et durcissement d'infrastructures self-hosted : virtualisation, réseau segmenté, sauvegarde et supervision maison.",
    tags: ["Proxmox", "Reseau", "Sécurité"],
    href: "/services/infra-on-premise",
    longDescription:
      "Garder la maîtrise totale de vos données et de vos couts recurrents en hebergeant chez vous. Je conçois des infrastructures on-premise robustes : virtualisation, segmentation réseau, sauvegardes chiffrees et supervision, avec la même rigueur qu'une infrastructure cloud.",
    bullets: [
      "Virtualisation Proxmox et plans de reprise d'activité",
      "Segmentation réseau (VLAN, firewall, PKI interne)",
      "Strategie de sauvegarde chiffrée et testee",
      "Supervision et alerting sur site",
    ],
  },
  {
    slug: "site-statique",
    Icon: IconGlobe,
    title: "Sites statiques",
    description:
      "Sites rapides et sobres, heberges en ligne ou directement chez vous, en on-premise, sans compromis sur la performance.",
    tags: ["Astro", "Self-hosted", "SEO"],
    href: "/services/site-statique",
    longDescription:
      "Un site vitrine ou une documentation n'a pas besoin d'un serveur applicatif complexe. Je construis des sites statiques légers et rapides (Astro), optimisés pour le référencement, déployables sur un hébergeur classique ou directement sur votre propre infrastructure.",
    bullets: [
      "Sites Astro rapides, accessibles et optimisés SEO",
      "Hebergement au choix : cloud ou on-premise chez vous",
      "Performance et sobriete numerique par defaut",
      "Multilingue et structure de contenu évolutive",
    ],
  },
  {
    slug: "site-dynamique",
    Icon: IconLayers,
    title: "Sites dynamiques",
    description:
      "Applications web sur mesure quand un site statique ne suffit plus : back-office, authentification, intégrations tierces.",
    tags: ["API", "Auth", "Base de données"],
    href: "/services/site-dynamique",
    longDescription:
      "Quand votre besoin dépasse la simple vitrine, je développe des applications web sur mesure : back-office d'administration, authentification, intégrations avec vos outils existants, base de données adaptée à vos volumes.",
    bullets: [
      "APIs et back-office sur mesure",
      "Authentification et gestion des roles",
      "Integrations tierces (paiement, CRM, outils internes)",
      "Choix de base de données adapté à l'usage",
    ],
  },
  {
    slug: "open-source",
    Icon: IconNetwork,
    title: "Open source friendly",
    description:
      "Priorite aux briques open source et auditables : pas de vendor lock-in, un stack que vous maîtrisez et pouvez reprendre.",
    tags: ["Self-hosted", "Sans lock-in", "Auditable"],
    href: "/services/open-source",
    longDescription:
      "Je privilégie systématiquement les solutions open source auditables plutôt que les services propriétaires fermées. Vous gardez la possibilité de reprendre la main sur votre stack, sans dépendre indéfiniment d'un prestataire ou d'un éditeur.",
    bullets: [
      "Choix d'outils open source matures et maintenus",
      "Documentation permettant une reprise en interne",
      "Auto-hebergement des briques critiques quand pertinent",
      "Aucune dépendance à une licence propriétaire non nécessaire",
    ],
  },
  {
    slug: "ia-llm",
    Icon: IconBot,
    title: "IA et LLM dans vos workflows",
    description:
      "Integration raisonnee de l'IA générative dans vos pipelines : revue de code, documentation, support, automatisations, sans exposer vos données.",
    tags: ["LLM", "Agents", "RAG"],
    href: "/services/ia-llm",
    longDescription:
      "L'IA générative devient un outil de productivité concret quand elle est intégrée avec méthode : agents pour automatiser des tâches répétitives, RAG pour interroger votre documentation interne, revue de code assistée. Je veille à ce que vos données sensibles ne soient jamais exposées à des services tiers sans contrôle.",
    bullets: [
      "Integration de LLM dans vos pipelines CI/CD",
      "Systemes RAG sur votre documentation interne",
      "Agents d'automatisation sur mesure",
      "Attention particulière à la confidentialité des données",
    ],
  },
  {
    slug: "securite",
    Icon: IconShield,
    title: "Sécurité",
    description:
      "Durcissement, gestion des secrets, audits réguliers et supervision : la sécurité intégrée des la conception, pas ajoutee apres coup.",
    tags: ["Hardening", "Audit", "Secrets"],
    href: "/services/securite",
    longDescription:
      "La sécurité se pense des la conception, pas en dernier recours. Je durcis vos systemes, mets en place une gestion rigoureuse des secrets et réalise des audits réguliers pour identifier les points faibles avant qu'ils ne deviennent des incidents.",
    bullets: [
      "Hardening système et réseau",
      "Gestion centralisee des secrets (vault, rotation)",
      "Audits de sécurité réguliers",
      "Supervision et détection d'anomalies",
    ],
  },
];

export const transformationServices = [
  {
    iconKey: "audit" as const,
    title: "Audit et cadrage",
    description:
      "Diagnostic de l'existant, identification des risques et des priorites, feuille de route réaliste et chiffrée.",
    tags: ["Etat des lieux", "Roadmap"],
    href: "/transformation-digitale#audit",
  },
  {
    iconKey: "migration" as const,
    title: "Migration progressive",
    description:
      "Passage vers le cloud, l'on-premise ou un modèle hybride sans interruption de service, par étapes maîtrisées.",
    tags: ["Cloud", "Hybride"],
    href: "/transformation-digitale#migration",
  },
  {
    iconKey: "training" as const,
    title: "Montee en autonomie",
    description:
      "Documentation, transfert de compétences et bonnes pratiques pour que vos équipes reprennent la main sereinement.",
    tags: ["Documentation", "Formation"],
    href: "/transformation-digitale#formation",
  },
];
