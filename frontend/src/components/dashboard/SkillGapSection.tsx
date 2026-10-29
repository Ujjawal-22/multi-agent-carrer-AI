import type { SkillGapResult } from "../../types/analysis";
import { Section } from "../Section";
import { SkillPill } from "../SkillPill";

function PillGroup({
  heading,
  items,
  variant,
}: {
  heading: string;
  items: string[];
  variant: "match" | "gap" | "neutral";
}) {
  if (items.length === 0) return null;
  return (
    <div>
      <h3 className="mb-2 text-sm font-medium text-ink-soft">{heading}</h3>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <SkillPill key={item} label={item} variant={variant} />
        ))}
      </div>
    </div>
  );
}

export function SkillGapSection({ result }: { result: SkillGapResult }) {
  return (
    <Section
      title="Skill gap"
      subtitle="Classified from your resume's actual content against the job's stated requirements. Nothing here is inferred beyond what the two documents contain."
    >
      <div className="space-y-5">
        <PillGroup
          heading="Matching skills"
          items={result.matching_skills}
          variant="match"
        />
        <PillGroup
          heading="Partially matching"
          items={result.partially_matching_skills}
          variant="neutral"
        />
        <PillGroup
          heading="Transferable from your experience"
          items={result.transferable_skills}
          variant="neutral"
        />
      </div>

      {result.missing_skills.length > 0 && (
        <div className="mt-8">
          <h3 className="mb-3 text-sm font-medium text-ink-soft">
            Missing skills
          </h3>
          <ul className="divide-y divide-line border-y border-line">
            {result.missing_skills.map((skill) => (
              <li key={skill.skill_name} className="py-3">
                <div className="flex flex-wrap items-center gap-3">
                  <SkillPill label={skill.skill_name} variant="gap" />
                  <span className="text-sm text-ink-soft">
                    {skill.importance.replace("_", " ")} requirement, with{" "}
                    {skill.suggested_learning_priority} learning priority
                  </span>
                </div>
                <p className="mt-2 max-w-[70ch] text-sm text-ink">
                  {skill.reason}
                </p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </Section>
  );
}
