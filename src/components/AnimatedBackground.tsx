export default function AnimatedBackground() {
  return (
    <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
      <div
        className="blob-anim absolute rounded-full"
        style={{
          width: 640,
          height: 640,
          top: -260,
          left: "5%",
          background: "var(--blue)",
          opacity: 0.18,
          filter: "blur(130px)",
          animation: "drift1 36s ease-in-out infinite",
        }}
      />
      <div
        className="blob-anim absolute rounded-full"
        style={{
          width: 520,
          height: 520,
          bottom: -200,
          right: -140,
          background: "var(--terracotta)",
          opacity: 0.09,
          filter: "blur(130px)",
          animation: "drift2 42s ease-in-out infinite",
        }}
      />
    </div>
  );
}
