export default function PageHero({ tag, title, description }: { tag: string; title: string; description: string }) {
  return (
    <section className="pt-[64px] pb-0 text-center">
      <div className="section-tag">{tag}</div>
      <h1 className="mx-auto mt-3.5 max-w-[22ch] text-[clamp(2.1rem,4.6vw,3rem)]">{title}</h1>
      <p className="mx-auto mt-5 max-w-[56ch] text-[1.1rem] leading-relaxed" style={{ color: "var(--ink-muted)" }}>
        {description}
      </p>
    </section>
  );
}

export function BackLink({ href = "/" }: { href?: string }) {
  return (
    <a
      href={href}
      className="mb-6 inline-flex items-center gap-2 text-sm no-underline"
      style={{ color: "var(--ink-muted)" }}
    >
      <svg className="icon h-4 w-4" viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6" /></svg>
      Retour à l'accueil
    </a>
  );
}
