// Mirrors backend/app/schemas/optimization.py exactly.

export interface ResumeSuggestion {
    section: string;
    original_text: string;
    suggested_text: string;
    reason: string;
    supporting_evidence: string;
    keywords: string[];
    priority: string;
}

export interface OptimizationResult {
    summary: string;
    suggestions: ResumeSuggestion[];
    missing_information: string[];
    warnings: string[];
}

export interface OptimizationResponse {
    resume_id: string;
    job_description_id: string;
    result: OptimizationResult;
}

export interface TailoredResumeRequest {
    resume_id: string;
    job_description_id: string;
    selected_suggestion_indices: number[];
    custom_instructions?: string;
}

export interface TailoredResumeResponse {
    resume_id: string;
    job_description_id: string;
    tailored_text: string;
    applied_suggestions_count: number;
}

export interface ResumeVersion {
  id: string;
  resume_id: string;
  job_description_id: string;
  name: string;
  tailored_text: string;
  created_at: string;
  updated_at: string;
}

export interface ResumeVersionListResponse {
  versions: ResumeVersion[];
  total: number;
}
