import { Link, useParams } from "react-router-dom";
import { AgentGraph } from "../components/AgentGraph";
import { ATSSection } from "../components/dashboard/ATSSection";
import { ExperienceSection } from "../components/dashboard/ExperienceSection";
import { InterviewSection } from "../components/dashboard/InterviewSection";
import { MatchSection } from "../components/dashboard/MatchSection";
import { RecommendationSection } from "../components/dashboard/RecommendationSection";
import { SkillGapSection } from "../components/dashboard/SkillGapSection";
import { useAnalysisPolling } from "../hooks/useAnalysisPolling";
import type { AnalysisResponse } from "../types/analysis";

interface DashboardTab {
  id: string;
  label: string;
  available: boolean;
}

function getTabs(analysis: AnalysisResponse): DashboardTab[] {
  return [
    { id: "match", label: "Match score", available: !!analysis.matching_result },
    { id: "skill-gap", label: "Skill gap", available: !!analysis.skill_gap_result },
    { id: "ats", label: "ATS analysis", available: !!analysis.ats_result },
    {
      id: "experience",
      label: "Experience and projects",
      available: !!analysis.experience_result,
    },
    {
      id: "recommendations",
      label: "Recommendations",
      available: !!analysis.recommendation_result,
    },
    {
      id: "interview",
      label: "Interview preparation",
      available: !!analysis.interview_result,
    },
  ].filter((tab) => tab.available);
}

function ProgressView({
  currentStep,
  completedNodeIds,
  activeNodeIds,
}: {
  currentStep: string | null;
  completedNodeIds: Set<string>;
  activeNodeIds: Set<string>;
}) {
  return (
    <div>
      <h1 className="text-3xl font-semibold text-ink">Analysis in progress</h1>
      <p className="mt-2 text-ink-soft" role="status" aria-live="polite">
        {currentStep ?? "Waiting for the analysis to start"}
      </p>

      <div className="mt-10">
        <AgentGraph
          className="w-full max-w-4xl"
          completedNodeIds={completedNodeIds}
          activeNodeIds={activeNodeIds}
        />
      </div>

      <p className="mt-6 max-w-[70ch] text-sm text-ink-soft">
        This takes roughly 30 to 60 seconds. Each box above fills in when
        that agent finishes, based on what the server is actually reporting,
        not a timer.
      </p>
    </div>
  );
}

function Dashboard({ analysis }: { analysis: AnalysisResponse }) {
  const tabs = getTabs(analysis);

  return (
    <div>
      <h1 className="text-3xl font-semibold text-ink">
        {analysis.jd_extraction?.job_title ?? "Analysis results"}
      </h1>
      {analysis.resume_extraction?.name && (
        <p className="mt-1 text-ink-soft">
          Resume analyzed for {analysis.resume_extraction.name}
        </p>
      )}
      <div className="mt-4">
        <Link
          to={`/analysis/${analysis.id}/optimize`}
          className="inline-block rounded-md border border-signal px-4 py-2 text-sm font-medium text-signal hover:bg-signal-soft"
        >
          Optimize my resume for this job
        </Link>
      </div>

      {analysis.status === "failed" && (
        <div
          role="alert"
          className="mt-6 border-l-2 border-gap bg-gap-soft px-4 py-3 text-sm text-ink max-w-[70ch]"
        >
          One or more agents reported a problem during this analysis. The
          sections below are the ones that completed successfully; anything
          missing didn't finish.
        </div>
      )}

      <div className="mt-10 grid gap-10 md:grid-cols-[200px_1fr]">
        <nav aria-label="Analysis sections" className="md:sticky md:top-6 md:self-start">
          <ul className="space-y-2 text-sm">
            {tabs.map((tab) => (
              <li key={tab.id}>
                <a href={`#${tab.id}`} className="text-ink-soft hover:text-signal">
                  {tab.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div>
          {analysis.matching_result && (
            <div id="match">
              <MatchSection result={analysis.matching_result} />
            </div>
          )}
          {analysis.skill_gap_result && (
            <div id="skill-gap">
              <SkillGapSection result={analysis.skill_gap_result} />
            </div>
          )}
          {analysis.ats_result && (
            <div id="ats">
              <ATSSection result={analysis.ats_result} />
            </div>
          )}
          {analysis.experience_result && (
            <div id="experience">
              <ExperienceSection result={analysis.experience_result} />
            </div>
          )}
          {analysis.recommendation_result && (
            <div id="recommendations">
              <RecommendationSection
                result={analysis.recommendation_result}
                sources={analysis.recommendation_sources}
              />
            </div>
          )}
          {analysis.interview_result && (
            <div id="interview">
              <InterviewSection
                result={analysis.interview_result}
                sources={analysis.interview_sources}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function AnalysisPage() {
  const { id } = useParams<{ id: string }>();
  const { analysis, isLoading, error, completedNodeIds, activeNodeIds, isTerminal } =
    useAnalysisPolling(id);

  if (isLoading) {
    return <p className="text-ink-soft">Loading analysis…</p>;
  }

  if (error || !analysis) {
    return (
      <div role="alert" className="max-w-xl">
        <h1 className="text-2xl font-semibold text-ink">
          Couldn't load this analysis
        </h1>
        <p className="mt-2 text-ink-soft">
          {error instanceof Error ? error.message : "Unknown error."}
        </p>
        <Link to="/analyze" className="mt-4 inline-block text-signal hover:underline">
          Start a new analysis
        </Link>
      </div>
    );
  }

  if (!isTerminal) {
    return (
      <ProgressView
        currentStep={analysis.current_step}
        completedNodeIds={completedNodeIds}
        activeNodeIds={activeNodeIds}
      />
    );
  }

  return <Dashboard analysis={analysis} />;
}
