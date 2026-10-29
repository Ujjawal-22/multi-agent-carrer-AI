import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { MatchingResult } from "../../types/analysis";
import { ScoreReadout } from "../ScoreReadout";
import { Section } from "../Section";

const SUB_SCORE_LABELS: Record<string, string> = {
  technical_skill_match: "Technical skills",
  ats_keyword_match: "ATS keywords",
  experience_project_match: "Experience & projects",
  education_match: "Education",
  domain_match: "Domain",
};

export function MatchSection({ result }: { result: MatchingResult }) {
  const chartData = Object.entries(result.sub_scores).map(([key, value]) => ({
    name: SUB_SCORE_LABELS[key] ?? key,
    score: value,
    weight: result.weights_used[key as keyof typeof result.weights_used],
  }));

  return (
    <Section
      title="Match score"
      subtitle="Computed by a deterministic weighted formula, not an LLM guess. The written summary below explains the numbers; it does not set them."
    >
      <div className="grid gap-8 md:grid-cols-[auto_1fr] md:items-start">
        <ScoreReadout
          label="Overall match"
          value={result.overall_match_score}
          size="large"
        />

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 4, right: 24, bottom: 4, left: 8 }}
            >
              <CartesianGrid horizontal={false} stroke="var(--color-line)" />
              <XAxis
                type="number"
                domain={[0, 100]}
                tick={{ fontFamily: "var(--font-mono)", fontSize: 11 }}
                stroke="var(--color-ink-soft)"
              />
              <YAxis
                type="category"
                dataKey="name"
                width={140}
                tick={{ fontSize: 12 }}
                stroke="var(--color-ink-soft)"
              />
              <Tooltip
                formatter={(value, _name, item) => [
                  `${Number(value).toFixed(1)} (weight ${(
                    (item.payload as { weight: number }).weight * 100
                  ).toFixed(0)}%)`,
                  "Score",
                ]}
              />
              <Bar dataKey="score" radius={0}>
                {chartData.map((entry) => (
                  <Cell key={entry.name} fill="var(--color-signal)" />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <p className="mt-6 max-w-[70ch] text-ink">{result.narrative_summary}</p>

      <details className="mt-4 max-w-[70ch] text-sm text-ink-soft">
        <summary className="cursor-pointer">How this score is calculated</summary>
        <p className="mt-2">{result.methodology_note}</p>
      </details>
    </Section>
  );
}
