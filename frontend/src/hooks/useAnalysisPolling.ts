import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { getAnalysis } from "../services/api";
import type { AnalysisResponse } from "../types/analysis";

// Mirrors backend/app/services/analysis_runner.py's _STEP_LABELS, reversed.
// A joined current_step like "Analyzing resume + Analyzing job description"
// is split on " + " and each part looked up here individually.
const LABEL_TO_NODE_ID: Record<string, string> = {
  "Analyzing resume": "resume_analyzer",
  "Analyzing job description": "jd_analyzer",
  "Computing skill gap": "skill_gap",
  "Running ATS analysis": "ats_analysis",
  "Analyzing experience & projects": "experience_analysis",
  "Calculating match score": "matching",
  "Generating recommendations": "recommendation",
  "Generating interview questions": "interview_prep",
};

const TERMINAL_STATUSES = new Set(["completed", "failed"]);
const POLL_INTERVAL_MS = 2500;

function labelToNodeIds(label: string | null): string[] {
  if (!label) return [];
  return label
    .split(" + ")
    .map((part) => LABEL_TO_NODE_ID[part])
    .filter((id): id is string => Boolean(id));
}

/**
 * Polls GET /api/analysis/{id} until the analysis reaches a terminal
 * status. Tracks which graph nodes have been seen as "active" across
 * polls so the AgentGraph can show genuinely observed completion, not
 * a simulated progress estimate - every node marked "completed" here
 * corresponds to a real current_step value this hook actually received
 * from the backend at some earlier poll.
 */
export function useAnalysisPolling(analysisId: string | undefined) {
  const [completedNodeIds, setCompletedNodeIds] = useState<Set<string>>(
    new Set(),
  );
  const previousActiveRef = useRef<Set<string>>(new Set());

  const query = useQuery<AnalysisResponse>({
    queryKey: ["analysis", analysisId],
    queryFn: () => getAnalysis(analysisId as string),
    enabled: Boolean(analysisId),
    refetchInterval: (q) => {
      const status = q.state.data?.status;
      if (status && TERMINAL_STATUSES.has(status)) return false;
      return POLL_INTERVAL_MS;
    },
  });

  useEffect(() => {
    const currentStep = query.data?.current_step ?? null;
    const activeNow = new Set(labelToNodeIds(currentStep));

    // Anything that was active on the PREVIOUS poll and is no longer the
    // current step has, by definition, completed since we last checked.
    setCompletedNodeIds((prev) => {
      const next = new Set(prev);
      previousActiveRef.current.forEach((id) => next.add(id));
      return next;
    });

    previousActiveRef.current = activeNow;

    // Once the analysis is fully done, every real node is complete.
    if (query.data?.status === "completed") {
      setCompletedNodeIds(new Set(Object.values(LABEL_TO_NODE_ID)));
    }
  }, [query.data?.current_step, query.data?.status]);

  const activeNodeIds = new Set(labelToNodeIds(query.data?.current_step ?? null));

  return {
    analysis: query.data,
    isLoading: query.isLoading,
    error: query.error,
    completedNodeIds,
    activeNodeIds,
    isTerminal: Boolean(
      query.data?.status && TERMINAL_STATUSES.has(query.data.status),
    ),
  };
}
