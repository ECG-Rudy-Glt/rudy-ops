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
      <p className="mt-6 text-xs leading-relaxed" style={{ color: "var(--ink-muted)" }}>
        Vos informations servent uniquement à répondre à votre demande et ne sont ni revendues ni utilisées pour de
        la prospection. L'assistant IA transmet vos messages à Google (Gemini) pour générer ses réponses.{" "}
        <a href="/confidentialite" className="underline">En savoir plus et exercer vos droits</a>.
      </p>
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
          ? { background: "var(--terracotta)", borderColor: "var(--terracotta)", color: "var(--bg)" }
          : { background: "transparent", borderColor: "var(--card-border)", color: "var(--ink-muted)" }
      }
    >
      {children}
    </button>
  );
}
