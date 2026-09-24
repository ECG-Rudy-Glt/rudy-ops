export default function ProofSection() {
  return (
    <section className="section text-center" id="propos">
      <div className="section-tag">Preuves</div>
      <a
        href="https://portfolio.gault-rudy.com"
        className="group mx-auto mt-5 block max-w-[720px] text-center no-underline"
      >
        <h2 className="inline text-[clamp(1.9rem,6vw,3.4rem)] leading-tight transition-opacity group-hover:opacity-75">
          Trois ans de terrain, avant le freelance
          <svg
            className="icon ml-3 inline-block h-[0.75em] w-[0.75em] flex-none align-middle transition-transform group-hover:translate-x-1"
            viewBox="0 0 24 24"
            style={{ color: "var(--terracotta)" }}
          >
            <path d="M7 17 17 7M8 7h9v9" />
          </svg>
        </h2>
      </a>
      <p className="mx-auto mt-3.5 max-w-[640px] text-[1.05rem] leading-relaxed" style={{ color: "var(--ink-muted)" }}>
        L'essentiel de mes réalisations détaillées vit sur mon portfolio - projets école, personnels et en entreprise.
      </p>
      <p className="mx-auto mt-2 max-w-[640px] text-[0.95rem] leading-relaxed" style={{ color: "var(--ink-muted)" }}>
        Du code Terraform/Ansible réel à consulter directement, pas juste des captures d'écran :{" "}
        <a href="https://github.com/ECG-Rudy-Glt/HOMELAB" target="_blank" rel="noreferrer" className="underline">
          infrastructure complète open source
        </a>
        , {" "}
        <a href="https://github.com/ECG-Rudy-Glt/shelfmark_ready_to_deploy" target="_blank" rel="noreferrer" className="underline">
          déploiement applicatif
        </a>{" "}
        et{" "}
        <a href="https://github.com/ECG-Rudy-Glt/jellyfin_local_ready_to_deploy" target="_blank" rel="noreferrer" className="underline">
          stack media conteneurisée
        </a>
        .
      </p>
    </section>
  );
}
