const links = [
  { href: "/#services", label: "Services" },
  { href: "/disponibilites", label: "Disponibilités" },
  { href: "https://portfolio.gault-rudy.com", label: "Portfolio" },
  { href: "/contact", label: "Contact" },
];

export default function Footer() {
  return (
    <footer className="mt-5 pb-12">
      <div className="wrap">
        <div
          className="relative rounded-[30px] p-0.5"
          style={{ background: "linear-gradient(150deg, var(--rim), transparent 40%, transparent 60%, var(--rim))" }}
        >
          <div
            className="rounded-[28px] px-8 py-10 sm:px-11"
            style={{
              background: "var(--card)",
              backdropFilter: "blur(30px) saturate(170%)",
              WebkitBackdropFilter: "blur(30px) saturate(170%)",
              boxShadow: "0 24px 54px rgba(var(--shadow-rgb), .07)",
            }}
          >
            <div className="flex flex-wrap items-start justify-between gap-6">
              <div>
                <div className="text-lg font-semibold">rudy-ops.fr</div>
                <div className="mt-2 text-sm" style={{ color: "var(--ink-muted)" }}>
                  Freelance DevOps et Platform Engineer - Tours, France
                </div>
              </div>
              <div className="flex flex-wrap gap-6 text-sm" style={{ color: "var(--ink-muted)" }}>
                {links.map((l) => (
                  <a key={l.href} href={l.href} className="no-underline hover:opacity-80" style={{ color: "inherit" }}>
                    {l.label}
                  </a>
                ))}
              </div>
            </div>
          </div>
        </div>
        <div
          className="mt-5 flex flex-wrap justify-between gap-2.5 px-2 text-[0.8rem]"
          style={{ color: "var(--ink-muted)" }}
        >
          <span>© 2026 Rudy Gault</span>
          <span>SIRET à venir - mentions légales</span>
        </div>
      </div>
    </footer>
  );
}
