import { useEffect, useState } from "react";
import ThemeToggle from "./ThemeToggle";

const links = [
  { href: "/", label: "Accueil" },
  { href: "/#services", label: "Services" },
  { href: "/disponibilites", label: "Disponibilités" },
  { href: "/a-propos", label: "À propos" },
  { href: "https://portfolio.gault-rudy.com", label: "Portfolio" },
];

export default function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => {
      setScrolled(window.scrollY > 24);
      setMenuOpen(false);
    };
    onScroll();
    document.addEventListener("scroll", onScroll, { passive: true });
    return () => document.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className="sticky top-0 z-20 transition-[padding] duration-300 ease-out"
      style={{ padding: scrolled ? "8px 0" : "12px 0" }}
    >
      <div className="relative mx-auto max-w-[1080px] px-4">
        <nav
          className="relative flex items-center justify-center rounded-full border transition-all duration-300"
          style={{
            background: "var(--nav-bg)",
            borderColor: "var(--card-border)",
            backdropFilter: "blur(26px) saturate(180%)",
            WebkitBackdropFilter: "blur(26px) saturate(180%)",
            padding: scrolled ? "7px 6px" : "9px 8px",
            boxShadow: scrolled
              ? "0 14px 32px rgba(var(--shadow-rgb), .16), inset 0 1.5px 0 var(--rim)"
              : "0 8px 24px rgba(var(--shadow-rgb), .08), inset 0 1.5px 0 var(--rim)",
            transform: scrolled ? "scale(0.99)" : "scale(1)",
          }}
        >
          <button
            aria-label="Ouvrir le menu"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((v) => !v)}
            className="ml-2 flex h-8 w-8 flex-none items-center justify-center rounded-full sm:hidden"
            style={{ color: "var(--ink-muted)" }}
          >
            <svg className="icon h-5 w-5" viewBox="0 0 24 24">
              {menuOpen ? <path d="M6 6l12 12M18 6L6 18" /> : <path d="M4 7h16M4 12h16M4 17h16" />}
            </svg>
          </button>

          <div className="hidden flex-1 items-center justify-center gap-8 px-4 text-sm sm:flex" style={{ color: "var(--ink-muted)" }}>
            {links.map((l) => (
              <a key={l.href} href={l.href} className="whitespace-nowrap transition-colors hover:opacity-100" style={{ color: "inherit" }}>
                {l.label}
              </a>
            ))}
          </div>

          <div className="flex flex-1 items-center justify-end gap-2.5 sm:flex-none sm:gap-3.5">
            <ThemeToggle />
            <a
              href="/contact"
              className="rounded-full px-4 py-2.5 text-sm font-semibold no-underline transition-opacity hover:opacity-85 sm:px-5"
              style={{ background: "var(--ink)", color: "var(--bg)" }}
            >
              Demander un devis
            </a>
          </div>
        </nav>

        {menuOpen && (
          <div
            className="absolute left-0 right-0 top-[calc(100%+10px)] rounded-3xl border p-2 sm:hidden"
            style={{
              background: "var(--nav-bg)",
              borderColor: "var(--card-border)",
              backdropFilter: "blur(26px) saturate(180%)",
              WebkitBackdropFilter: "blur(26px) saturate(180%)",
              boxShadow: "0 14px 32px rgba(var(--shadow-rgb), .16)",
            }}
          >
            {links.map((l) => (
              <a
                key={l.href}
                href={l.href}
                onClick={() => setMenuOpen(false)}
                className="block rounded-2xl px-4 py-3 text-[0.95rem] no-underline"
                style={{ color: "var(--ink)" }}
              >
                {l.label}
              </a>
            ))}
          </div>
        )}
      </div>
    </header>
  );
}
