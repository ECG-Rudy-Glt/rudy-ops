import type { ComponentType } from "react";

interface ServiceCardProps {
  Icon: ComponentType;
  title: string;
  description: string;
  tags: string[];
  href: string;
}

export default function ServiceCard({ Icon, title, description, tags, href }: ServiceCardProps) {
  return (
    <a
      href={href}
      className="group relative block cursor-pointer rounded-[26px] p-0.5 no-underline transition-transform duration-300 ease-out hover:-translate-y-1"
      style={{
        background: "linear-gradient(155deg, var(--rim), transparent 38%, transparent 62%, var(--rim))",
        boxShadow: "0 18px 40px rgba(var(--shadow-rgb), .06)",
      }}
    >
      <div
        className="h-full rounded-[24px] p-6 transition-colors duration-300 sm:p-8"
        style={{ background: "var(--card)", backdropFilter: "blur(30px) saturate(170%)", WebkitBackdropFilter: "blur(30px) saturate(170%)" }}
      >
        <div className="flex items-start justify-between">
          <div
            className="mb-5 flex h-11 w-11 items-center justify-center rounded-[13px] border"
            style={{
              background: "color-mix(in srgb, var(--blue) 18%, transparent)",
              borderColor: "color-mix(in srgb, var(--blue) 38%, transparent)",
              color: "var(--blue-deep)",
            }}
          >
            <Icon />
          </div>
          <div
            className="flex h-[30px] w-[30px] items-center justify-center rounded-full border transition-transform duration-300 group-hover:translate-x-[3px] group-hover:-translate-y-[3px]"
            style={{ borderColor: "var(--card-border)", color: "var(--ink-muted)" }}
          >
            <svg className="icon h-3.5 w-3.5" viewBox="0 0 24 24"><path d="M7 17 17 7M8 7h9v9" /></svg>
          </div>
        </div>
        <h3 className="mb-2.5 text-xl" style={{ color: "var(--ink)" }}>{title}</h3>
        <p className="mb-4 text-[0.97rem] leading-relaxed" style={{ color: "var(--ink-muted)" }}>{description}</p>
        <div className="flex flex-wrap gap-2">
          {tags.map((tag) => (
            <span
              key={tag}
              className="rounded-full border px-3 py-1 text-xs"
              style={{ borderColor: "var(--card-border)", color: "var(--ink-muted)" }}
            >
              {tag}
            </span>
          ))}
        </div>
      </div>
    </a>
  );
}
