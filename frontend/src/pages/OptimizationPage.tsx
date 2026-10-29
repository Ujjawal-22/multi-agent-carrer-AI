
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { Section } from "../components/Section";
import { SkillPill } from "../components/SkillPill";

import {
    createOptimization,
    deleteSavedResumeVersion,
    downloadResumePdf,
    downloadSavedResumeVersionPdf,
    generateTailoredResume,
    getAnalysis,
    getOptimization,
    getSavedResumeVersions,
} from "../services/api";

import type { ResumeSuggestion } from "../types/optimization";

const PRIORITY_VARIANT: Record<string, "match" | "gap" | "neutral"> = {
    high: "gap",
    medium: "neutral",
    low: "match",
};

function SuggestionCard({
    suggestion,
    index,
    isSelected,
    onToggle,
}: {
    suggestion: ResumeSuggestion;
    index: number;
    isSelected: boolean;
    onToggle: (index: number) => void;
}) {
    return (
        <li className="py-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                    <input
                        type="checkbox"
                        id={`suggestion-${index}`}
                        checked={isSelected}
                        onChange={() => onToggle(index)}
                        className="h-4 w-4 rounded border-line text-signal focus:ring-signal"
                    />
                    <label
                        htmlFor={`suggestion-${index}`}
                        className="font-medium text-ink cursor-pointer"
                    >
                        {suggestion.section}
                    </label>
                </div>

                <SkillPill
                    label={`${suggestion.priority} priority`}
                    variant={PRIORITY_VARIANT[suggestion.priority] ?? "neutral"}
                />
            </div>

            <div className="mt-3 grid gap-3 md:grid-cols-2">
                <div>
                    <h4 className="text-xs font-medium uppercase text-ink-soft">
                        Original
                    </h4>
                    <p className="mt-1 text-sm text-ink">
                        {suggestion.original_text}
                    </p>
                </div>

                <div>
                    <h4 className="text-xs font-medium uppercase text-ink-soft">
                        Suggested
                    </h4>
                    <p className="mt-1 text-sm text-ink">
                        {suggestion.suggested_text}
                    </p>
                </div>
            </div>

            <p className="mt-3 text-sm text-ink-soft">
                {suggestion.reason}
            </p>

            <p className="mt-1 text-sm text-ink-soft">
                Job requirement addressed: {suggestion.supporting_evidence}
            </p>

            {suggestion.keywords.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                    {suggestion.keywords.map((kw) => (
                        <SkillPill key={kw} label={kw} />
                    ))}
                </div>
            )}
        </li>
    );
}

export function OptimizationPage() {
    const { id } = useParams<{ id: string }>();
    const queryClient = useQueryClient();

    const [selectedIndices, setSelectedIndices] = useState<number[]>([]);
    const [copied, setCopied] = useState(false);
    const [pdfError, setPdfError] = useState<string | null>(null);

    // Load the analysis associated with this page.
    const analysisQuery = useQuery({
        queryKey: ["analysis", id],
        queryFn: () => getAnalysis(id as string),
        enabled: Boolean(id),
    });

    const resumeId = analysisQuery.data?.resume_id;
    const jobDescriptionId = analysisQuery.data?.job_description_id;

    // Load optimization suggestions for this resume and job description.
    const existingQuery = useQuery({
        queryKey: ["optimization", resumeId, jobDescriptionId],
        queryFn: () =>
            getOptimization(resumeId as string, jobDescriptionId as string),
        enabled: Boolean(resumeId && jobDescriptionId),
    });

    // Load previously saved tailored resume versions.
    const savedVersionsQuery = useQuery({
        queryKey: ["resume-versions", resumeId, jobDescriptionId],
        queryFn: () =>
            getSavedResumeVersions(
                resumeId as string,
                jobDescriptionId as string,
            ),
        enabled: Boolean(resumeId && jobDescriptionId),
    });

    const generateMutation = useMutation({
        mutationFn: () =>
            createOptimization(
                resumeId as string,
                jobDescriptionId as string,
            ),
        onSuccess: (data) => {
            queryClient.setQueryData(
                ["optimization", resumeId, jobDescriptionId],
                data,
            );
        },
    });

    // The backend automatically saves a ResumeVersion when tailoring succeeds.
    const tailorMutation = useMutation({
        mutationFn: () =>
            generateTailoredResume({
                resume_id: resumeId as string,
                job_description_id: jobDescriptionId as string,
                selected_suggestion_indices: selectedIndices,
            }),
        onSuccess: async () => {
            await queryClient.invalidateQueries({
                queryKey: ["resume-versions", resumeId, jobDescriptionId],
            });
        },
    });


    const deleteVersionMutation = useMutation({
        mutationFn: (versionId: string) =>
            deleteSavedResumeVersion(versionId),
        onSuccess: async () => {
            await queryClient.invalidateQueries({
                queryKey: ["resume-versions", resumeId, jobDescriptionId],
            });
        },
    });


    const toggleSuggestion = (index: number) => {
        setSelectedIndices((prev) =>
            prev.includes(index)
                ? prev.filter((i) => i !== index)
                : [...prev, index],
        );
    };

    const handleCopy = async (text: string) => {
        try {
            await navigator.clipboard.writeText(text);
            setCopied(true);
            window.setTimeout(() => setCopied(false), 2000);
        } catch (error) {
            console.error("Copy failed:", error);
            setPdfError("Unable to copy the resume. Please try again.");
        }
    };

    const handleDownload = (text: string) => {
        const blob = new Blob([text], {
            type: "text/markdown;charset=utf-8",
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");

        a.href = url;
        a.download = "tailored_resume.md";
        document.body.appendChild(a);
        a.click();
        a.remove();

        window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    };

    const handleDownloadPdf = async (text: string) => {
        setPdfError(null);

        try {
            const blob = await downloadResumePdf(text);
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");

            a.href = url;
            a.download = "tailored_resume.pdf";
            document.body.appendChild(a);
            a.click();
            a.remove();

            window.setTimeout(() => URL.revokeObjectURL(url), 1000);
        } catch (error) {
            console.error("PDF download failed:", error);
            setPdfError(
                error instanceof Error
                    ? error.message
                    : "Unable to download the PDF. Please try again.",
            );
        }
    };

    // Download a PDF generated from a previously saved database version.
    const handleDownloadSavedVersionPdf = async (
        versionId: string,
        versionName: string,
    ) => {
        setPdfError(null);

        try {
            const blob = await downloadSavedResumeVersionPdf(versionId);
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");

            const safeName = versionName
                .replace(/[<>:"/\\|?*]/g, "_")
                .trim();

            a.href = url;
            a.download = `${safeName || "saved_resume"}.pdf`;
            document.body.appendChild(a);
            a.click();
            a.remove();

            window.setTimeout(() => URL.revokeObjectURL(url), 1000);
        } catch (error) {
            console.error("Saved resume PDF download failed:", error);
            setPdfError(
                error instanceof Error
                    ? error.message
                    : "Unable to download the saved resume PDF.",
            );
        }
    };

    if (analysisQuery.isLoading || existingQuery.isLoading) {
        return <p className="text-ink-soft">Loading...</p>;
    }

    if (analysisQuery.error || !analysisQuery.data) {
        return (
            <div role="alert">
                <p className="text-ink-soft">
                    Couldn't load the original analysis.
                </p>
                <Link to="/analyze" className="text-signal hover:underline">
                    Start a new analysis
                </Link>
            </div>
        );
    }

    const optimization = generateMutation.data ?? existingQuery.data;

    return (
        <div>
            <Link
                to={`/analysis/${id}`}
                className="text-sm text-signal hover:underline"
            >
                &larr; Back to analysis
            </Link>

            <h1 className="mt-4 text-3xl font-semibold text-ink">
                Resume optimization
            </h1>

            <p className="mt-2 max-w-[70ch] text-ink-soft">
                Suggestions grounded in your actual resume text and this
                job's requirements. Select the suggestions you want to
                accept to assemble a tailored resume draft.
            </p>

            {!optimization && (
                <div className="mt-8">
                    <button
                        type="button"
                        onClick={() => generateMutation.mutate()}
                        disabled={generateMutation.isPending}
                        className="rounded-md bg-signal px-5 py-2.5 font-medium text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
                    >
                        {generateMutation.isPending
                            ? "Generating..."
                            : "Generate optimization suggestions"}
                    </button>

                    {generateMutation.isError && (
                        <p role="alert" className="mt-3 text-sm text-gap">
                            {generateMutation.error instanceof Error
                                ? generateMutation.error.message
                                : "Something went wrong."}
                        </p>
                    )}
                </div>
            )}

            {optimization && (
                <div className="mt-8 space-y-8">
                    <Section title="Summary">
                        <p className="max-w-[70ch] text-ink">
                            {optimization.result.summary}
                        </p>
                    </Section>

                    <Section
                        title="Suggestions"
                        subtitle="Check the suggestions you want to incorporate into your tailored draft."
                    >
                        <ul className="divide-y divide-line border-y border-line">
                            {optimization.result.suggestions.map((s, i) => (
                                <SuggestionCard
                                    key={`${s.section}-${i}`}
                                    suggestion={s}
                                    index={i}
                                    isSelected={selectedIndices.includes(i)}
                                    onToggle={toggleSuggestion}
                                />
                            ))}
                        </ul>

                        <div className="mt-4 flex items-center gap-4">
                            <button
                                type="button"
                                onClick={() => tailorMutation.mutate()}
                                disabled={tailorMutation.isPending}
                                className="rounded-md bg-signal px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-40"
                            >
                                {tailorMutation.isPending
                                    ? "Building draft..."
                                    : `Compile Tailored Draft (${selectedIndices.length} selected)`}
                            </button>
                        </div>

                        {tailorMutation.isError && (
                            <p role="alert" className="mt-3 text-sm text-gap">
                                {tailorMutation.error instanceof Error
                                    ? tailorMutation.error.message
                                    : "Failed to compile the tailored resume."}
                            </p>
                        )}
                    </Section>


                    {/* Saved versions and their individual PDF downloads. */}
                    <Section
                        title="Saved Resume Versions"
                        subtitle="Previously generated tailored resumes for this job description."
                    >
                        <div className="space-y-4">
                            {savedVersionsQuery.isLoading && (
                                <p className="text-sm text-ink-soft">
                                    Loading saved resume versions...
                                </p>
                            )}

                            {savedVersionsQuery.isError && (
                                <p className="text-sm text-red-600">
                                    Failed to load saved resume versions. Please refresh and try again.
                                </p>
                            )}

                            {savedVersionsQuery.data &&
                                savedVersionsQuery.data.versions.length === 0 && (
                                    <p className="text-sm text-ink-soft">
                                        No saved resume versions yet. Generate and save a
                                        tailored resume to see it here.
                                    </p>
                                )}

                            {savedVersionsQuery.data?.versions.map((version) => (
                                <div
                                    key={version.id}
                                    className="flex flex-wrap items-center justify-between gap-4 rounded-md border border-line p-4"
                                >
                                    <div>
                                        <h3 className="font-medium text-ink">
                                            {version.name}
                                        </h3>

                                        <p className="mt-1 text-sm text-ink-soft">
                                            Created:{" "}
                                            {new Date(version.created_at).toLocaleString()}
                                        </p>
                                    </div>

                                    <div className="flex flex-wrap items-center gap-2">
                                        <button
                                            type="button"
                                            onClick={() =>
                                                handleDownloadSavedVersionPdf(
                                                    version.id,
                                                    version.name,
                                                )
                                            }
                                            className="rounded-md bg-signal px-3 py-2 text-sm font-medium text-white hover:opacity-90"
                                        >
                                            Download PDF
                                        </button>

                                        <button
                                            type="button"
                                            onClick={() => {
                                                const confirmed = window.confirm(
                                                    `Are you sure you want to delete "${version.name}"? This action cannot be undone.`,
                                                );

                                                if (confirmed) {
                                                    deleteVersionMutation.mutate(version.id);
                                                }
                                            }}
                                            disabled={deleteVersionMutation.isPending}
                                            className="rounded-md border border-gap px-3 py-2 text-sm font-medium text-gap hover:bg-gap/10 disabled:cursor-not-allowed disabled:opacity-50"
                                        >
                                            {deleteVersionMutation.isPending
                                                ? "Deleting..."
                                                : "Delete"}
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>

                        {deleteVersionMutation.isError && (
                            <p className="mt-3 text-sm text-red-600">
                                Failed to delete the saved resume version. Please try again.
                            </p>
                        )}

                        {pdfError && (
                            <p className="mt-3 text-sm text-red-600">
                                {pdfError}
                            </p>
                        )}
                    </Section>

                    {tailorMutation.data && (
                        <Section
                            title="Tailored Resume Draft"
                            subtitle={`Draft generated with ${tailorMutation.data.applied_suggestions_count} applied changes.`}
                        >
                            <div className="space-y-4">
                                <div className="flex flex-wrap gap-2">
                                    <button
                                        type="button"
                                        onClick={() =>
                                            handleCopy(
                                                tailorMutation.data.tailored_text,
                                            )
                                        }
                                        className="rounded-md border border-line px-3 py-1.5 text-xs font-medium text-ink hover:bg-line/20"
                                    >
                                        {copied
                                            ? "Copied!"
                                            : "Copy to Clipboard"}
                                    </button>

                                    <button
                                        type="button"
                                        onClick={() =>
                                            handleDownload(
                                                tailorMutation.data.tailored_text,
                                            )
                                        }
                                        className="rounded-md border border-line px-3 py-1.5 text-xs font-medium text-ink hover:bg-line/20"
                                    >
                                        Download Markdown (.md)
                                    </button>

                                    <button
                                        type="button"
                                        onClick={() =>
                                            handleDownloadPdf(
                                                tailorMutation.data.tailored_text,
                                            )
                                        }
                                        className="rounded-md bg-signal px-3 py-1.5 text-xs font-medium text-white hover:opacity-90"
                                    >
                                        Download PDF
                                    </button>
                                </div>

                                {pdfError && (
                                    <p role="alert" className="text-sm text-gap">
                                        {pdfError}
                                    </p>
                                )}

                                <pre className="max-h-96 overflow-y-auto whitespace-pre-wrap rounded-md bg-line/10 p-4 text-sm font-mono text-ink">
                                    {tailorMutation.data.tailored_text}
                                </pre>
                            </div>
                        </Section>
                    )}

                    {optimization.result.missing_information.length > 0 && (
                        <Section
                            title="Information that could strengthen your resume"
                            subtitle="Facts or metrics you could add yourself — nothing here was invented on your behalf."
                        >
                            <ul className="list-disc space-y-1 pl-5 text-ink max-w-[70ch]">
                                {optimization.result.missing_information.map(
                                    (item) => (
                                        <li key={item}>{item}</li>
                                    ),
                                )}
                            </ul>
                        </Section>
                    )}

                    {optimization.result.warnings.length > 0 && (
                        <Section title="Warnings">
                            <ul className="list-disc space-y-1 pl-5 text-ink max-w-[70ch]">
                                {optimization.result.warnings.map((item) => (
                                    <li key={item}>{item}</li>
                                ))}
                            </ul>
                        </Section>
                    )}

                    <div className="mt-8">
                        <button
                            type="button"
                            onClick={() => generateMutation.mutate()}
                            disabled={generateMutation.isPending}
                            className="text-sm text-signal hover:underline disabled:opacity-40"
                        >
                            {generateMutation.isPending
                                ? "Regenerating..."
                                : "Regenerate suggestions"}
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}