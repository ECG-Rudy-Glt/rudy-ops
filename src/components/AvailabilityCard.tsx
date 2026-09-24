export default function AvailabilityCard() {
  return (
    <a
      href="/disponibilites"
      className="group mx-auto mt-16 flex max-w-[720px] flex-col gap-3 rounded-2xl border border-l-4 px-6 py-5 text-left no-underline transition-colors sm:flex-row sm:items-center sm:justify-between"
      style={{ color: "inherit", background: "var(--card)", borderColor: "var(--card-border)", borderLeftColor: "var(--terracotta)" }}
    >
      <div>
        <div className="font-semibold">Disponible en soirée et le week-end</div>
        <div className="mt-1 text-sm" style={{ color: "var(--ink-muted)" }}>
          Lun–ven 18h–23h, sam–dim. Premier appel gratuit.
        </div>
      </div>
      <span className="whitespace-nowrap text-sm font-semibold underline-offset-4 group-hover:underline" style={{ color: "var(--terracotta)" }}>
        Voir les créneaux →
      </span>
    </a>
  );
}
