import type { ReactNode } from "react";

interface SectionProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
}

/**
 * A plain hairline-bordered content block - deliberately NOT a rounded
 * card with a drop shadow. No radius, no shadow: content sections are
 * distinguished by a single top divider and typographic hierarchy, not
 * by looking like a stack of identical cards.
 */
export function Section({ title, subtitle, children }: SectionProps) {
  return (
    <section className="border-t border-line py-8 first:border-t-0 first:pt-0">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-ink">{title}</h2>
        {subtitle && (
          <p className="mt-1 text-sm text-ink-soft max-w-[70ch]">{subtitle}</p>
        )}
      </div>
      {children}
    </section>
  );
}
