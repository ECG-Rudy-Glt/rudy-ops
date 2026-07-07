export default function AvailabilityCard() {
  return (
    <a
      href="/disponibilités"
      className="mx-auto mt-16 block max-w-[720px] cursor-pointer rounded-[26px] p-0.5 text-left no-underline transition-transform duration-300 ease-out hover:-translate-y-1"
      style={{
        color: "inherit",
        background: "linear-gradient(150deg, var(--rim), transparent 40%, transparent 60%, var(--rim))",
      }}
    >
      <div
        className="grid grid-cols-1 items-center gap-6 rounded-[24px] p-7 sm:grid-cols-[1fr_auto] sm:text-left text-center"
        style={{
          background: "var(--card)",
          backdropFilter: "blur(30px) saturate(170%)",
          WebkitBackdropFilter: "blur(30px) saturate(170%)",
          boxShadow: "0 20px 46px rgba(var(--shadow-rgb), .07)",
        }}
      >
        <div>
          <div className="text-[1.04rem] font-semibold">Creneaux ouverts en soirée et le week-end</div>
          <div className="mt-1 text-sm" style={{ color: "var(--ink-muted)" }}>
            Pourquoi ces horaires, et comment réserver un appel gratuit
          </div>
        </div>
        <div className="flex items-center justify-center gap-2.5 sm:justify-start">
          <span
            className="whitespace-nowrap rounded-full border px-4 py-2 text-sm font-semibold"
            style={{
              color: "var(--blue-deep)",
              background: "color-mix(in srgb, var(--blue) 20%, transparent)",
              borderColor: "color-mix(in srgb, var(--blue) 42%, transparent)",
            }}
          >
            lun-ven 18h-23h - sam-dim
          </span>
          <svg className="icon h-4 w-4" viewBox="0 0 24 24" style={{ color: "var(--ink-muted)" }}>
            <path d="M9 18l6-6-6-6" />
          </svg>
        </div>
      </div>
    </a>
  );
}
