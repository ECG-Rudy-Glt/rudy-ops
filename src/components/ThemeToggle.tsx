import { useEffect, useState } from "react";

export default function ThemeToggle() {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const root = document.documentElement;
    const current =
      root.getAttribute("data-theme") ??
      (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    setIsDark(current === "dark");
  }, []);

  const toggle = () => {
    const root = document.documentElement;
    const next = isDark ? "light" : "dark";
    root.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
    setIsDark(!isDark);
  };

  return (
    <button
      onClick={toggle}
      aria-label={isDark ? "Passer en mode clair" : "Passer en mode sombre"}
      className="flex h-8 w-8 items-center justify-center rounded-full border transition-transform hover:scale-105"
      style={{ borderColor: "var(--card-border)", background: "var(--card)", color: "var(--ink-muted)" }}
    >
      {isDark ? (
        <svg className="icon h-4 w-4" viewBox="0 0 24 24">
          <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
        </svg>
      ) : (
        <svg className="icon h-4 w-4" viewBox="0 0 24 24">
          <path d="M12 3v1M12 20v1M4.2 4.2l.7.7M19.1 19.1l.7.7M3 12h1M20 12h1M4.2 19.8l.7-.7M19.1 4.9l.7-.7" />
          <circle cx="12" cy="12" r="4.2" />
        </svg>
      )}
    </button>
  );
}
