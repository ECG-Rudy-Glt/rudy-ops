import { useState, type FormEvent } from "react";

const FORM_ENDPOINT = "https://formspree.io/f/REPLACE_WITH_YOUR_FORM_ID";

export default function ContactForm() {
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setStatus("sending");
    const form = event.currentTarget;
    try {
      const response = await fetch(FORM_ENDPOINT, {
        method: "POST",
        body: new FormData(form),
        headers: { Accept: "application/json" },
      });
      if (response.ok) {
        setStatus("sent");
        form.reset();
      } else {
        setStatus("error");
      }
    } catch {
      setStatus("error");
    }
  };

  if (status === "sent") {
    return (
      <div className="py-10 text-center">
        <h3 className="mb-2 text-xl">Message envoye</h3>
        <p style={{ color: "var(--ink-muted)" }}>Merci, je reviens vers vous rapidement.</p>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-5">
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        <Field label="Nom" name="name" type="text" required />
        <Field label="Email" name="email" type="email" required />
      </div>
      <Field label="Entreprise (optionnel)" name="company" type="text" />
      <div>
        <label className="mb-2 block text-sm font-semibold">Votre besoin</label>
        <textarea
          name="message"
          required
          rows={6}
          className="w-full resize-none rounded-2xl border px-4 py-3 outline-none"
          style={{ background: "var(--card)", borderColor: "var(--card-border)", color: "var(--ink)" }}
          placeholder="Décrivez votre projet, votre infrastructure actuelle, vos délais..."
        />
      </div>

      {status === "error" && (
        <p className="text-sm" style={{ color: "var(--terracotta)" }}>
          Une erreur est survenue. Vous pouvez aussi m'écrire directement à contact@rudy-ops.fr.
        </p>
      )}

      <button type="submit" disabled={status === "sending"} className="btn-primary self-start">
        {status === "sending" ? "Envoi..." : "Envoyer la demande"}
      </button>
    </form>
  );
}

function Field({ label, name, type, required }: { label: string; name: string; type: string; required?: boolean }) {
  return (
    <div>
      <label className="mb-2 block text-sm font-semibold" htmlFor={name}>{label}</label>
      <input
        id={name}
        name={name}
        type={type}
        required={required}
        className="w-full rounded-full border px-4 py-3 outline-none"
        style={{ background: "var(--card)", borderColor: "var(--card-border)", color: "var(--ink)" }}
      />
    </div>
  );
}
