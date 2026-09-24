export default function PortraitCard() {
  return (
    <div
      className="relative aspect-[4/5] w-full overflow-hidden rounded-[28px] border"
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
        className="absolute inset-0 h-full w-full object-contain p-8"
      />
      <div className="absolute inset-x-0 bottom-0 p-6">
        <div
          className="text-[1.15rem] font-semibold"
          style={{ fontFamily: "Fraunces, Georgia, serif", color: "var(--ink)" }}
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
