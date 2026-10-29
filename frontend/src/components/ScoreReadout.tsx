interface ScoreReadoutProps {
  label: string;
  value: number;
  /** Optional context shown beneath the number, e.g. "weight 35%". */
  detail?: string;
  size?: "large" | "small";
}

/**
 * Numbers are instruments: every score renders in the mono face, which is
 * reserved for real numeric readouts across this app - never decorative
 * labels.
 */
export function ScoreReadout({
  label,
  value,
  detail,
  size = "small",
}: ScoreReadoutProps) {
  const numberClasses =
    size === "large"
      ? "text-6xl font-semibold"
      : "text-2xl font-medium";

  return (
    <div>
      <div className={`font-mono tabular-nums text-ink ${numberClasses}`}>
        {value.toFixed(1)}
      </div>
      <div className="mt-1 text-sm text-ink-soft">{label}</div>
      {detail && <div className="text-xs text-ink-soft">{detail}</div>}
    </div>
  );
}
