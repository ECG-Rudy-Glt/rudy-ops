import type { ReactNode } from "react";

export default function GlassPanel({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={`relative rounded-[28px] p-px ${className}`}
      style={{ background: "var(--card-border)" }}
    >
      <div
        className="rounded-[26px] p-6 sm:p-10"
        style={{
          background: "var(--card)",
          boxShadow: "0 20px 46px rgba(var(--shadow-rgb), .06)",
        }}
      >
        {children}
      </div>
    </div>
  );
}
