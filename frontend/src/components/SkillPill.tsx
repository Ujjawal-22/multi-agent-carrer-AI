interface SkillPillProps {
  label: string;
  variant?: "match" | "gap" | "neutral";
}

const VARIANT_CLASSES: Record<NonNullable<SkillPillProps["variant"]>, string> = {
  match: "bg-match-soft text-match",
  gap: "bg-gap-soft text-gap",
  neutral: "bg-chip text-ink-soft",
};

/**
 * Semantic colors (match/gap) are used ONLY here, inside data - never as
 * page chrome or section backgrounds.
 */
export function SkillPill({ label, variant = "neutral" }: SkillPillProps) {
  return (
    <span
      className={`inline-block rounded-sm px-2 py-0.5 text-sm ${VARIANT_CLASSES[variant]}`}
    >
      {label}
    </span>
  );
}
