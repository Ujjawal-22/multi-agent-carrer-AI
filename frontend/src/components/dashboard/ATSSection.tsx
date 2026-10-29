import type { ATSAnalysisResult } from "../../types/analysis";
import { ScoreReadout } from "../ScoreReadout";
import { Section } from "../Section";
import { SkillPill } from "../SkillPill";

function BulletList({ heading, items }: { heading: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div>
      <h3 className="mb-2 text-sm font-medium text-ink-soft">{heading}</h3>
      <ul className="list-disc space-y-1 pl-5 text-ink max-w-[70ch]">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

export function ATSSection({ result }: { result: ATSAnalysisResult }) {
  return (
    <Section title="ATS analysis">
      {/*
        The methodology note is set in code by the backend (never trusted
        from the LLM) and is surfaced here up-front, not tucked away in a
        footnote - it's the honest framing for the score right beside it.
      */}
      <div className="mb-6 border-l-2 border-signal bg-signal-soft px-4 py-3 text-sm text-ink max-w-[70ch]">
        {result.methodology_note}
      </div>

      <div className="grid gap-8 md:grid-cols-[auto_1fr]">
        <ScoreReadout label="ATS score (estimate)" value={result.ats_score} size="large" />
        <p className="max-w-[70ch] text-ink">{result.score_explanation}</p>
      </div>

      <div className="mt-8 space-y-5">
        {result.keyword_coverage.matched_keywords.length > 0 && (
          <div>
            <h3 className="mb-2 text-sm font-medium text-ink-soft">
              Keywords found in your resume
            </h3>
            <div className="flex flex-wrap gap-2">
              {result.keyword_coverage.matched_keywords.map((kw) => (
                <SkillPill key={kw} label={kw} variant="match" />
              ))}
            </div>
          </div>
        )}

        {result.keyword_coverage.missing_keywords.length > 0 && (
          <div>
            <h3 className="mb-2 text-sm font-medium text-ink-soft">
              Keywords missing from your resume
            </h3>
            <div className="flex flex-wrap gap-2">
              {result.keyword_coverage.missing_keywords.map((kw) => (
                <SkillPill key={kw} label={kw} variant="gap" />
              ))}
            </div>
          </div>
        )}

        {result.job_title_alignment_note && (
          <div>
            <h3 className="mb-2 text-sm font-medium text-ink-soft">
              Job title alignment
            </h3>
            <p className="max-w-[70ch] text-ink">
              {result.job_title_alignment_note}
            </p>
          </div>
        )}

        <BulletList
          heading="Section structure issues"
          items={result.section_structure_issues}
        />
        <BulletList heading="Formatting issues" items={result.formatting_issues} />
        <BulletList
          heading="Suggested improvements"
          items={result.improvement_suggestions}
        />
      </div>
    </Section>
  );
}
