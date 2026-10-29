import type { ExperienceAnalysisResult } from "../../types/analysis";
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

const RELEVANCE_VARIANT = {
  high: "match",
  medium: "neutral",
  low: "gap",
} as const;

export function ExperienceSection({
  result,
}: {
  result: ExperienceAnalysisResult;
}) {
  return (
    <Section
      title="Experience and projects"
      subtitle="How well your existing work demonstrates what this job requires. Suggestions below are about presenting what you've actually done, never about claiming what you haven't."
    >
      <p className="max-w-[70ch] text-ink">{result.overall_relevance_summary}</p>

      {result.project_relevance.length > 0 && (
        <div className="mt-6">
          <h3 className="mb-3 text-sm font-medium text-ink-soft">
            Relevance of each project
          </h3>
          <ul className="divide-y divide-line border-y border-line">
            {result.project_relevance.map((project) => (
              <li key={project.project_name} className="py-3">
                <div className="flex flex-wrap items-center gap-3">
                  <span className="font-medium text-ink">
                    {project.project_name}
                  </span>
                  <SkillPill
                    label={`${project.relevance_to_role} relevance`}
                    variant={RELEVANCE_VARIANT[project.relevance_to_role]}
                  />
                </div>
                <p className="mt-2 max-w-[70ch] text-sm text-ink">
                  {project.notes}
                </p>
                {project.relevant_technologies.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {project.relevant_technologies.map((tech) => (
                      <SkillPill key={tech} label={tech} />
                    ))}
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-6 space-y-5">
        <div>
          <h3 className="mb-2 text-sm font-medium text-ink-soft">
            Technical depth
          </h3>
          <p className="max-w-[70ch] text-ink">
            {result.technical_depth_assessment}
          </p>
        </div>
        <BulletList
          heading="Quantifiable achievements already in your resume"
          items={result.quantifiable_achievements_found}
        />
        <BulletList
          heading="Evidence the job implies but your resume doesn't show"
          items={result.missing_evidence}
        />
        <BulletList
          heading="Descriptions that read as weak"
          items={result.weak_descriptions}
        />
        <BulletList
          heading="Suggested wording and presentation improvements"
          items={result.improvement_suggestions}
        />
      </div>
    </Section>
  );
}
