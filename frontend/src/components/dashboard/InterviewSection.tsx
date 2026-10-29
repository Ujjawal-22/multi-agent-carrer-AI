import type {
  InterviewPrepResult,
  InterviewQuestion,
  QuestionCategory,
} from "../../types/analysis";
import { Section } from "../Section";

const CATEGORY_LABELS: Record<QuestionCategory, string> = {
  technical: "Technical",
  genai: "Generative AI",
  python: "Python",
  ml: "Machine learning",
  rag: "Retrieval-augmented generation",
  agents: "Agents",
  project: "Your projects",
  behavioral: "Behavioral",
};

function groupByCategory(
  questions: InterviewQuestion[],
): [QuestionCategory, InterviewQuestion[]][] {
  const groups = new Map<QuestionCategory, InterviewQuestion[]>();
  for (const q of questions) {
    const existing = groups.get(q.category) ?? [];
    existing.push(q);
    groups.set(q.category, existing);
  }
  return Array.from(groups.entries());
}

export function InterviewSection({
  result,
  sources,
}: {
  result: InterviewPrepResult;
  sources: string[];
}) {
  const grouped = groupByCategory(result.questions);

  return (
    <Section
      title="Interview preparation"
      subtitle="Questions tied to your actual projects and detected gaps. Each includes why it was chosen for you specifically."
    >
      <div className="space-y-8">
        {grouped.map(([category, questions]) => (
          <div key={category}>
            <h3 className="mb-3 text-sm font-medium text-ink-soft">
              {CATEGORY_LABELS[category]}
            </h3>
            <ul className="divide-y divide-line border-y border-line">
              {questions.map((q) => (
                <li key={q.question} className="py-3">
                  <p className="max-w-[70ch] font-medium text-ink">
                    {q.question}
                  </p>
                  <p className="mt-1 max-w-[70ch] text-sm text-ink-soft">
                    Why this question: {q.rationale}
                  </p>
                </li>
              ))}
            </ul>
          </div>
        ))}
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
