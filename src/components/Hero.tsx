import AvailabilityCard from "./AvailabilityCard";
import PortraitCard from "./PortraitCard";

export default function Hero() {
  return (
    <section className="pt-[110px] pb-0 sm:pt-[90px]">
      <div className="grid grid-cols-1 items-start gap-10 lg:grid-cols-[1fr_auto] lg:gap-12">
        <div>
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
