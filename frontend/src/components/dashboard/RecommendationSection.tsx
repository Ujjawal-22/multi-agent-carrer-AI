import type { RecommendationResult } from "../../types/analysis";
import { Section } from "../Section";

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

export function RecommendationSection({
  result,
  sources,
}: {
  result: RecommendationResult;
  sources: string[];
}) {
  return (
    <Section
      title="Recommendations"
      subtitle="Based on the gaps detected above, and grounded in retrieved reference material rather than the model's memory alone."
    >
      <div className="space-y-6">
        <BulletList heading="Skills to learn first" items={result.skills_to_learn} />
        <BulletList
          heading="Technologies to practice"
          items={result.technologies_to_practice}
        />
        <BulletList heading="Project ideas" items={result.project_ideas} />
        <BulletList
          heading="Resume improvements"
          items={result.resume_improvements}
        />
        <BulletList
          heading="Relevant certifications"
          items={result.relevant_certifications}
        />
        <BulletList
          heading="Interview topics to prepare"
          items={result.interview_prep_focus_areas}
        />

        {result.short_term_roadmap.length > 0 && (
          <div>
            <h3 className="mb-2 text-sm font-medium text-ink-soft">
              Short-term roadmap
            </h3>
            <ol className="list-decimal space-y-1 pl-5 text-ink max-w-[70ch]">
              {result.short_term_roadmap.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </div>
        )}
      </div>

      {sources.length > 0 && (
        <p className="mt-6 text-sm text-ink-soft">
          Reference documents consulted:{" "}
          <span className="font-mono">{sources.join(", ")}</span>
        </p>
      )}
    </Section>
  );
}
