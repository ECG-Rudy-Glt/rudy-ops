import AvailabilityCard from "./AvailabilityCard";
import PortraitCard from "./PortraitCard";

export default function Hero() {
  return (
    <section className="pt-[110px] pb-0 sm:pt-[90px]">
      <div className="grid grid-cols-1 items-start gap-10 lg:grid-cols-[1fr_auto] lg:gap-12">
        <div>
          <span
            className="mb-7 inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-[0.82rem]"
            style={{
              background: "color-mix(in srgb, var(--terracotta) 10%, var(--card))",
              borderColor: "color-mix(in srgb, var(--terracotta) 22%, var(--card-border))",
              color: "var(--ink-muted)",
              backdropFilter: "blur(14px)",
              boxShadow: "inset 0 1px 0 var(--rim), inset 0 -6px 10px -6px color-mix(in srgb, var(--terracotta) 18%, transparent)",
            }}
          >
            <span className="h-1.5 w-1.5 rounded-full" style={{ background: "var(--blue-deep)" }} />
            Disponible en soirée et week-end - basé à Tours
          </span>
          <h1 className="max-w-[15ch] text-[clamp(2.5rem,5.4vw,4rem)] leading-[1.08]">
            Infrastructure et DevOps, <em className="not-italic" style={{ color: "var(--blue-deep)" }}>pensés pour durer.</em>
          </h1>
          <p className="mt-6 max-w-[46ch] text-[1.15rem] leading-relaxed" style={{ color: "var(--ink-muted)" }}>
            Freelance DevOps et Platform Engineer à Tours. J'automatise, sécurise et industrialise votre infrastructure, du cloud à l'on-premise.
          </p>
          <div className="mt-9 flex flex-wrap gap-3.5">
            <a href="/contact" className="btn-primary">Demander un devis</a>
            <a href="#services" className="btn-ghost">Voir les services</a>
          </div>
        </div>

        <div className="hidden w-[300px] lg:block">
          <PortraitCard />
        </div>
      </div>

      <AvailabilityCard />
    </section>
  );
}
