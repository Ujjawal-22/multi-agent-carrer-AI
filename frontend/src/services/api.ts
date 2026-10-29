import type { AnalysisResponse } from "../types/analysis";

import type {
  ResumeVersion,
  ResumeVersionListResponse,
} from "../types/optimization";

import type { OptimizationResponse } from "../types/optimization";
import type {
  JobDescriptionResponse,
  ResumeUploadResponse,
} from "../types/documents";
import type { TailoredResumeRequest, TailoredResumeResponse } from "../types/optimization";

export async function generateTailoredResume(
  payload: TailoredResumeRequest,
): Promise<TailoredResumeResponse> {
  const response = await fetch(`${API_BASE_URL}/api/optimization/tailor`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<TailoredResumeResponse>(response);
}


export async function getSavedResumeVersions(
  resumeId: string,
  jobDescriptionId: string,
): Promise<ResumeVersionListResponse> {
  const params = new URLSearchParams({
    resume_id: resumeId,
    job_description_id: jobDescriptionId,
  });

  const response = await fetch(
    `${API_BASE_URL}/api/resume-versions?${params.toString()}`,
  );

  return handleResponse<ResumeVersionListResponse>(response);
}

export async function saveResumeVersion(
  resumeId: string,
  jobDescriptionId: string,
  name: string,
  tailoredText: string,
): Promise<ResumeVersion> {
  const response = await fetch(`${API_BASE_URL}/api/resume-versions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      resume_id: resumeId,
      job_description_id: jobDescriptionId,
      name,
      tailored_text: tailoredText,
    }),
  });

  return handleResponse<ResumeVersion>(response);
}


export async function deleteSavedResumeVersion(
  versionId: string,
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/resume-versions/${encodeURIComponent(versionId)}`,
    {
      method: "DELETE",
    },
  );

  if (!response.ok) {
    throw new Error(
      `Failed to delete saved resume version (${response.status}).`,
    );
  }
}

export async function downloadResumePdf(
  tailoredText: string,
): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/optimization/pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tailored_text: tailoredText }),
  });

  if (!response.ok) {
    throw new Error(`PDF generation failed (${response.status}).`);
  }

  return response.blob();
}

const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
  "http://localhost:8000";

export async function downloadSavedResumeVersionPdf(
  versionId: string,
): Promise<Blob> {
  const response = await fetch(
    `${API_BASE_URL}/api/resume-versions/${encodeURIComponent(versionId)}/pdf`,
  );

  if (!response.ok) {
    throw new Error(
      `Saved resume PDF download failed (${response.status}).`,
    );
  }

  return response.blob();
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // Response body wasn't JSON - fall back to statusText, nothing to
      // parse further.
    }
    throw new ApiError(response.status, detail);
  }
  return response.json() as Promise<T>;
}

export async function uploadResume(
  file: File,
): Promise<ResumeUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/resumes/upload`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<ResumeUploadResponse>(response);
}

export async function createJobFromText(
  text: string,
  title?: string,
): Promise<JobDescriptionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, title: title ?? null }),
  });
  return handleResponse<JobDescriptionResponse>(response);
}

export async function uploadJobFile(
  file: File,
): Promise<JobDescriptionResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/jobs/upload`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<JobDescriptionResponse>(response);
}

export async function createAnalysis(
  resumeId: string,
  jobDescriptionId: string,
): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/api/analysis`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      resume_id: resumeId,
      job_description_id: jobDescriptionId,
    }),
  });
  return handleResponse<AnalysisResponse>(response);
}

export async function getAnalysis(
  analysisId: string,
): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/api/analysis/${analysisId}`);
  return handleResponse<AnalysisResponse>(response);
}
export async function createOptimization(
  resumeId: string,
  jobDescriptionId: string,
): Promise<OptimizationResponse> {
  const response = await fetch(`${API_BASE_URL}/api/optimization`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      resume_id: resumeId,
      job_description_id: jobDescriptionId,
    }),
  });
  return handleResponse<OptimizationResponse>(response);
}

// Returns null on 404 (not generated yet) rather than throwing - this is
// an expected, normal state for a resume/job pair that hasn't been
// optimized, not an error condition.
export async function getOptimization(
  resumeId: string,
  jobDescriptionId: string,
): Promise<OptimizationResponse | null> {
  const response = await fetch(
    `${API_BASE_URL}/api/optimization/${resumeId}/${jobDescriptionId}`,
  );
  if (response.status === 404) {
    return null;
  }
  return handleResponse<OptimizationResponse>(response);
}