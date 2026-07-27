import { useState, useRef, useEffect, type FormEvent } from "react";
import { services } from "../data/services";

const CHAT_ENDPOINT = "https://api.rudy-ops.fr/quote-chat";

type ChatMessage = { role: "user" | "assistant"; content: string };

export default function QuoteChat() {
  const [service, setService] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "done" | "error">("idle");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const startChat = (slug: string) => {
    const chosen = services.find((s) => s.slug === slug);
    setService(slug);
    setMessages([
      {
        role: "assistant",
        content: `Bonjour ! Vous vous intéressez à "${chosen?.title}". Pour préparer votre devis, quel est votre nom et votre email ?`,
      },
    ]);
  };

  const send = async (event: FormEvent) => {
    event.preventDefault();
    const text = input.trim();
    if (!text || status === "sending" || status === "done") return;

    const nextMessages: ChatMessage[] = [...messages, { role: "user", content: text }];
    setMessages(nextMessages);
    setInput("");
    setStatus("sending");

    try {
      const response = await fetch(CHAT_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // On n'envoie que role/content à chaque appel : le backend est sans état,
        // il reconstruit le contexte à partir de l'historique complet renvoyé ici.
        body: JSON.stringify({ service, messages: nextMessages }),
      });
      if (!response.ok) throw new Error("request failed");
      const data = await response.json();
      setMessages((prev) => [...prev, { role: "assistant", content: data.reply }]);
      setStatus(data.done ? "done" : "idle");
    } catch {
      setStatus("error");
    }
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
                ? { alignSelf: "flex-end", background: "var(--accent)", color: "var(--bg)" }
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

      {status === "error" && (
        <p className="text-sm" style={{ color: "var(--terracotta)" }}>
          Une erreur est survenue. Vous pouvez aussi m'écrire directement à contact@rudy-ops.fr.
        </p>
      )}

      {status === "done" ? (
        <p className="text-sm font-semibold" style={{ color: "var(--ink)" }}>
          Demande envoyée — à bientôt !
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
