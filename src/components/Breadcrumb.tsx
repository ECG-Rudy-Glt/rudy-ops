interface Crumb {
  label: string;
  href?: string;
}

export default function Breadcrumb({ items }: { items: Crumb[] }) {
  const all: Crumb[] = [{ label: "Accueil", href: "/" }, ...items];

  return (
    <nav aria-label="Fil d'Ariane" className="mx-auto mb-6 flex max-w-[1120px] flex-wrap items-center gap-2 pt-6 text-sm">
      {all.map((item, i) => {
        const isLast = i === all.length - 1;
        return (
          <span key={item.label} className="flex items-center gap-2">
            {i > 0 && (
              <svg className="icon h-3.5 w-3.5" viewBox="0 0 24 24" style={{ color: "var(--ink-muted)" }}>
                <path d="M9 18l6-6-6-6" />
              </svg>
            )}
            {isLast || !item.href ? (
              <span style={{ color: isLast ? "var(--ink)" : "var(--ink-muted)" }}>{item.label}</span>
            ) : (
              <a href={item.href} className="no-underline hover:opacity-80" style={{ color: "var(--ink-muted)" }}>
                {item.label}
              </a>
            )}
          </span>
        );
      })}
    </nav>
  );
}
