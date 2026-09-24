export default function PortraitCard() {
  return (
    <div
      className="flex aspect-[4/5] w-full flex-col overflow-hidden rounded-[28px] border"
      style={{
        borderColor: "var(--card-border)",
        background:
          "color-mix(in srgb, var(--terracotta) 8%, var(--bg))",
        boxShadow: "0 24px 54px rgba(var(--shadow-rgb), .1)",
      }}
    >
      <img
        src="/images/avatar.png"
        alt="Rudy Gault"
        className="min-h-0 w-full flex-1 object-contain p-8 pb-4"
      />
      <div className="border-t px-6 py-4" style={{ borderColor: "var(--card-border)", background: "var(--card)" }}>
        <div
          className="text-[1.15rem] font-semibold"
          style={{ color: "var(--ink)" }}
        >
          Rudy Gault
        </div>
        <p className="mt-1 text-sm" style={{ color: "var(--ink-muted)" }}>
          Freelance DevOps - Tours
        </p>
      </div>
    </div>
  );
}
