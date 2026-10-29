// Mirrors backend/app/schemas/resume.py and job_description.py exactly.

export interface ResumeUploadResponse {
  id: string;
  original_filename: string;
  extraction_method: string;
  char_count: number;
  uploaded_at: string;
}

export interface JobDescriptionResponse {
  id: string;
  title: string | null;
  source: string;
  char_count: number;
  created_at: string;
}
