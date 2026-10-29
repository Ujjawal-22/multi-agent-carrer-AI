import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ApiError,
  createAnalysis,
  createJobFromText,
  uploadJobFile,
  uploadResume,
} from "../services/api";

type JobInputMode = "paste" | "upload";

const ACCEPTED_FILES = ".pdf,.docx";

export function UploadPage() {
  const navigate = useNavigate();

  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jobMode, setJobMode] = useState<JobInputMode>("paste");
  const [jobTitle, setJobTitle] = useState("");
  const [jobText, setJobText] = useState("");
  const [jobFile, setJobFile] = useState<File | null>(null);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStage, setSubmitStage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const jobInputReady =
    jobMode === "paste" ? jobText.trim().length > 0 : jobFile !== null;
  const canSubmit = resumeFile !== null && jobInputReady && !isSubmitting;

  async function handleSubmit() {
    if (!resumeFile) return;

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      setSubmitStage("Uploading your resume");
      const resume = await uploadResume(resumeFile);

      setSubmitStage("Saving the job description");
      const job =
        jobMode === "paste"
          ? await createJobFromText(jobText, jobTitle || undefined)
          : await uploadJobFile(jobFile as File);

      setSubmitStage("Starting the analysis");
      const analysis = await createAnalysis(resume.id, job.id);

      navigate(`/analysis/${analysis.id}`);
    } catch (err) {
      setErrorMessage(
        err instanceof ApiError
          ? err.message
          : "Something went wrong reaching the server. Is the backend running?",
      );
      setIsSubmitting(false);
      setSubmitStage(null);
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-3xl font-semibold text-ink">New analysis</h1>
      <p className="mt-2 text-ink-soft">
        Upload your resume and provide the job you're targeting.
      </p>

      <div className="mt-10 space-y-10">
        <div>
          <label
            htmlFor="resume-file"
            className="block text-sm font-medium text-ink"
          >
            Your resume
          </label>
          <p className="mt-1 text-sm text-ink-soft">PDF or DOCX, up to 5 MB.</p>
          <input
            id="resume-file"
            type="file"
            accept={ACCEPTED_FILES}
            onChange={(e) => setResumeFile(e.target.files?.[0] ?? null)}
            disabled={isSubmitting}
            className="mt-3 block w-full text-sm text-ink file:mr-4 file:rounded-md file:border file:border-line file:bg-paper-raised file:px-4 file:py-2 file:text-sm file:text-ink hover:file:bg-chip"
          />
        </div>

        <div>
          <span className="block text-sm font-medium text-ink">
            Job description
          </span>

          <div
            role="tablist"
            aria-label="Job description input method"
            className="mt-3 inline-flex border border-line"
          >
            {(["paste", "upload"] as const).map((mode) => (
              <button
                key={mode}
                role="tab"
                type="button"
                aria-selected={jobMode === mode}
                onClick={() => setJobMode(mode)}
                disabled={isSubmitting}
                className={`px-4 py-2 text-sm ${
                  jobMode === mode
                    ? "bg-signal text-white"
                    : "bg-paper-raised text-ink hover:bg-chip"
                }`}
              >
                {mode === "paste" ? "Paste text" : "Upload file"}
              </button>
            ))}
          </div>

          {jobMode === "paste" ? (
            <div className="mt-4 space-y-3">
              <input
                type="text"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                placeholder="Job title (optional)"
                disabled={isSubmitting}
                className="block w-full rounded-md border border-line bg-paper-raised px-3 py-2 text-sm text-ink"
              />
              <textarea
                value={jobText}
                onChange={(e) => setJobText(e.target.value)}
                placeholder="Paste the full job description here"
                rows={10}
                disabled={isSubmitting}
                className="block w-full rounded-md border border-line bg-paper-raised px-3 py-2 text-sm text-ink"
              />
            </div>
          ) : (
            <input
              type="file"
              accept={ACCEPTED_FILES}
              onChange={(e) => setJobFile(e.target.files?.[0] ?? null)}
              disabled={isSubmitting}
              aria-label="Job description file"
              className="mt-4 block w-full text-sm text-ink file:mr-4 file:rounded-md file:border file:border-line file:bg-paper-raised file:px-4 file:py-2 file:text-sm file:text-ink hover:file:bg-chip"
            />
          )}
        </div>

        {errorMessage && (
          <div
            role="alert"
            className="border-l-2 border-gap bg-gap-soft px-4 py-3 text-sm text-ink"
          >
            {errorMessage}
          </div>
        )}

        <div>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!canSubmit}
            className="rounded-md bg-signal px-5 py-2.5 font-medium text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {isSubmitting ? (submitStage ?? "Working") : "Analyze application"}
          </button>
        </div>
      </div>
    </div>
  );
}
