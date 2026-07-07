import type { ReactNode } from "react";

export default function GlassPanel({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={`relative rounded-[28px] p-0.5 ${className}`}
      style={{ background: "linear-gradient(150deg, var(--rim), transparent 40%, transparent 60%, var(--rim))" }}
    >
      <div
        className="rounded-[26px] p-6 sm:p-10"
        style={{
          background: "var(--card)",
          backdropFilter: "blur(28px) saturate(160%)",
          WebkitBackdropFilter: "blur(28px) saturate(160%)",
          boxShadow: "0 20px 46px rgba(var(--shadow-rgb), .06)",
        }}
      >
        {children}
      </div>
    </div>
  );
}
