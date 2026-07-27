import { useState } from "react";
import ContactForm from "./ContactForm";
import QuoteChat from "./QuoteChat";

export default function ContactPanel() {
  const [mode, setMode] = useState<"form" | "chat">("form");

  return (
    <div>
      <div className="mb-6 flex gap-2 text-sm">
        <TabButton active={mode === "form"} onClick={() => setMode("form")}>
          Formulaire
        </TabButton>
        <TabButton active={mode === "chat"} onClick={() => setMode("chat")}>
          Assistant IA
        </TabButton>
      </div>
      {mode === "form" ? <ContactForm /> : <QuoteChat />}
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded-full border px-4 py-2 font-semibold transition"
      style={
        active
          ? { background: "var(--accent)", borderColor: "var(--accent)", color: "var(--bg)" }
          : { background: "transparent", borderColor: "var(--card-border)", color: "var(--ink-muted)" }
      }
    >
      {children}
    </button>
  );
}
