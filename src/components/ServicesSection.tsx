import ServiceCard from "./ServiceCard";
import { services } from "../data/services";

export default function ServicesSection() {
  return (
    <section className="section" id="services">
      <div className="section-head">
        <div className="section-tag">Services</div>
        <h2>De l'infrastructure au site en ligne</h2>
        <p>Sept domaines d'intervention, une même exigence : des systèmes reproductibles, documentés et faciles à maintenir.</p>
      </div>
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        {services.map((s) => (
          <ServiceCard key={s.title} Icon={s.Icon} title={s.title} description={s.description} tags={s.tags} href={s.href} />
        ))}
      </div>
    </section>
  );
}
