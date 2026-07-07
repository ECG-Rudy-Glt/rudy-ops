import ServiceCard from "./ServiceCard";
import { IconAudit, IconMigration, IconTraining } from "./icons";
import { transformationServices } from "../data/services";

const iconMap = {
  audit: IconAudit,
  migration: IconMigration,
  training: IconTraining,
};

export default function TransformationSection() {
  return (
    <section className="section" id="transformation">
      <div className="section-head">
        <div className="section-tag">Accompagnement</div>
        <h2>Transformation digitale</h2>
        <p>
          Au-delà de l'exécution technique, un accompagnement pour structurer votre transition : audit de l'existant,
          feuille de route, montée en autonomie de vos équipes.
        </p>
      </div>
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {transformationServices.map((s) => (
          <ServiceCard
            key={s.title}
            Icon={iconMap[s.iconKey]}
            title={s.title}
            description={s.description}
            tags={s.tags}
            href={s.href}
          />
        ))}
      </div>
    </section>
  );
}
