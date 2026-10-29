import { Link } from "react-router-dom";
import { AgentGraph } from "../components/AgentGraph";

export function LandingPage() {
  return (
    <div>
      <h1 className="max-w-[22ch] text-4xl font-semibold leading-tight text-ink">
        See how your resume measures up against a specific job.
      </h1>
      <p className="mt-4 max-w-[60ch] text-lg text-ink-soft">
        Eight specialized agents read your resume and a job description,
        compare them, and explain every score they produce. Nothing is
        invented: if your resume doesn't say it, the analysis won't claim it.
      </p>

      <div className="mt-8">
        <Link
          to="/analyze"
          className="inline-block rounded-md bg-signal px-5 py-2.5 font-medium text-white hover:opacity-90"
        >
          Start an analysis
        </Link>
      </div>

      <div className="mt-14 border-t border-line pt-8">
        <h2 className="text-lg font-semibold text-ink">How the analysis runs</h2>
        <p className="mt-1 max-w-[70ch] text-sm text-ink-soft">
          This is the actual pipeline that runs on your documents. Agents that
          don't depend on each other run at the same time.
        </p>
        <AgentGraph className="mt-6 w-full max-w-4xl" />
      </div>
    </div>
  );
}
