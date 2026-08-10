import { useState, useRef, useEffect, type FormEvent } from "react";
import { services } from "../data/services";

const CHAT_ENDPOINT = "https://api.rudy-ops.fr/quote-chat";
// Repère côté client uniquement, pour couper la conversation après un certain
// nombre d'échanges : le backend est sans état (l'historique vit côté Google
// via previous_interaction_id), donc c'est ici que la limite de bon sens vit.
const MAX_TURNS = 12;

// Suggestions de premier message par service, pour éviter d'avoir à taper une
// phrase complète pour démarrer : cliquer une bulle envoie directement le texte.
const STARTER_PROMPTS: Record<string, string[]> = {
  "devops-iac": [
    "Je veux mettre en place un pipeline CI/CD",
    "Je veux automatiser mon infrastructure avec Terraform/Ansible",
    "Je veux ajouter de la supervision et des alertes",
  ],
  "infra-on-premise": [
    "Je veux héberger mon infra moi-même plutôt que sur le cloud",
    "Je veux segmenter et sécuriser mon réseau",
    "Je veux une stratégie de sauvegarde fiable",
  ],
  "site-statique": [
    "Je veux un site vitrine simple et rapide",
    "Je veux migrer mon site vers de l'hébergement on-premise",
  ],
  "site-dynamique": [
    "Je veux un back-office avec authentification",
    "Je veux intégrer un outil tiers (paiement, CRM...)",
  ],
  "open-source": [
    "Je veux remplacer un outil propriétaire par de l'open source",
    "Je veux éviter le vendor lock-in sur mon infra",
  ],
  "ia-llm": [
    "Je veux intégrer l'IA dans mes workflows (support, doc, code)",
    "Je veux un système RAG sur ma documentation interne",
  ],
  securite: [
    "Je veux un audit de sécurité de mon infrastructure",
    "Je veux durcir la sécurité de mes systèmes",
  ],
};

type ChatMessage = { role: "user" | "assistant"; content: string };

export default function QuoteChat() {
  const [service, setService] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "done" | "error" | "maxed">("idle");
  // Identifiant opaque renvoyé par le backend (previous_interaction_id côté Gemini) :
  // on ne renvoie que ça + le dernier message, jamais tout l'historique.
  const interactionIdRef = useRef<string | null>(null);
  const turnCountRef = useRef(0);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const startChat = (slug: string) => {
    const chosen = services.find((s) => s.slug === slug);
    setService(slug);
    interactionIdRef.current = null;
    turnCountRef.current = 0;
    setMessages([
      {
        role: "assistant",
        content: `Bonjour ! Vous vous intéressez à "${chosen?.title}". Pour préparer votre devis, quel est votre nom et votre email ?`,
      },
    ]);
  };

  const submitMessage = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || status === "sending" || status === "done") return;

    if (turnCountRef.current >= MAX_TURNS) {
      setStatus("maxed");
      return;
    }
    turnCountRef.current += 1;

    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setInput("");
    setStatus("sending");

    try {
      const response = await fetch(CHAT_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          service,
          message: trimmed,
          previous_interaction_id: interactionIdRef.current,
        }),
      });
      if (!response.ok) throw new Error("request failed");
      const data = await response.json();
      interactionIdRef.current = data.interaction_id ?? null;
      setMessages((prev) => [...prev, { role: "assistant", content: data.reply }]);
      setStatus(data.done ? "done" : "idle");
    } catch {
      setStatus("error");
    }
  };

  const send = (event: FormEvent) => {
    event.preventDefault();
    submitMessage(input);
  };

  if (!service) {
    return (
      <div>
        <p className="mb-4 text-sm" style={{ color: "var(--ink-muted)" }}>
          Choisissez le service qui vous intéresse, l'assistant vous posera quelques
          questions pour préparer votre devis.
        </p>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {services.map((s) => (
            <button
              key={s.slug}
              type="button"
              onClick={() => startChat(s.slug)}
              className="rounded-2xl border px-4 py-3 text-left text-sm transition hover:opacity-80"
              style={{ background: "var(--card)", borderColor: "var(--card-border)", color: "var(--ink)" }}
            >
              {s.title}
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div
        ref={scrollRef}
        className="flex max-h-[420px] flex-col gap-3 overflow-y-auto rounded-2xl border p-4"
        style={{ background: "var(--card)", borderColor: "var(--card-border)" }}
      >
        {messages.map((m, i) => (
          <div
            key={i}
            className="max-w-[85%] rounded-2xl px-4 py-2 text-sm"
            style={
              m.role === "user"
                ? { alignSelf: "flex-end", background: "var(--terracotta)", color: "var(--bg)" }
                : { alignSelf: "flex-start", background: "var(--bg-elevated, transparent)", color: "var(--ink)" }
            }
          >
            {m.content}
          </div>
        ))}
        {status === "sending" && (
          <div className="text-sm" style={{ color: "var(--ink-muted)" }}>
            ...
          </div>
        )}
      </div>

      {messages.length === 1 && status === "idle" && (STARTER_PROMPTS[service]?.length ?? 0) > 0 && (
        <div className="flex flex-wrap gap-2">
          {STARTER_PROMPTS[service].map((prompt) => (
            <button
              key={prompt}
              type="button"
              onClick={() => submitMessage(prompt)}
              className="rounded-full border px-3.5 py-2 text-xs transition hover:opacity-80"
              style={{ background: "var(--card)", borderColor: "var(--card-border)", color: "var(--ink-muted)" }}
            >
              {prompt}
            </button>
          ))}
        </div>
      )}

      {status === "error" && (
        <p className="text-sm" style={{ color: "var(--terracotta)" }}>
          Une erreur est survenue. Vous pouvez aussi m'écrire directement à contact@rudy-ops.fr.
        </p>
      )}

      {status === "done" ? (
        <p className="text-sm font-semibold" style={{ color: "var(--ink)" }}>
          Demande envoyée, à bientôt !
        </p>
      ) : status === "maxed" ? (
        <p className="text-sm" style={{ color: "var(--ink-muted)" }}>
          La conversation devient longue : pour aller plus vite, écrivez-moi directement à{" "}
          <a href="mailto:contact@rudy-ops.fr" className="underline">contact@rudy-ops.fr</a> ou utilisez le
          formulaire ci-dessus.
        </p>
      ) : (
        <form onSubmit={send} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Votre réponse..."
            disabled={status === "sending"}
            className="w-full rounded-full border px-4 py-3 outline-none"
            style={{ background: "var(--card)", borderColor: "var(--card-border)", color: "var(--ink)" }}
          />
          <button type="submit" disabled={status === "sending"} className="btn-primary shrink-0">
            Envoyer
          </button>
        </form>
      )}
    </div>
  );
}
