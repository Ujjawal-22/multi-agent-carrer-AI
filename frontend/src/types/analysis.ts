// Hand-mirrored from backend/app/schemas/*.py - kept field-for-field
// identical to the Pydantic models so API responses deserialize without
// surprises. If a backend schema changes, update the matching type here.

export interface Education {
  degree: string | null;
  field_of_study: string | null;
  university: string | null;
  graduation_year: string | null;
}

export interface Project {
  name: string;
  description: string | null;
  technologies: string[];
}

export interface Experience {
  title: string | null;
  company: string | null;
  duration: string | null;
  description: string | null;
  is_internship: boolean;
}

export interface TechnicalSkills {
  programming_languages: string[];
  frameworks: string[];
  tools: string[];
  databases: string[];
  cloud_technologies: string[];
  ai_ml_skills: string[];
  genai_skills: string[];
}

export interface ResumeExtraction {
  name: string | null;
  email: string | null;
  phone: string | null;
  education: Education[];
  technical_skills: TechnicalSkills;
  projects: Project[];
  experience: Experience[];
  certifications: string[];
  achievements: string[];
  soft_skills: string[];
}

export interface JobExtraction {
  job_title: string | null;
  required_skills: string[];
  preferred_skills: string[];
  programming_languages: string[];
  frameworks: string[];
  tools: string[];
  ai_ml_technologies: string[];
  genai_technologies: string[];
  cloud_requirements: string[];
  database_requirements: string[];
  experience_requirements: string | null;
  education_requirements: string | null;
  responsibilities: string[];
  keywords: string[];
  domain: string | null;
  seniority_level: string | null;
}

export type SkillImportance = "critical" | "important" | "nice_to_have";
export type LearningPriority = "high" | "medium" | "low";

export interface MissingSkill {
  skill_name: string;
  importance: SkillImportance;
  reason: string;
  suggested_learning_priority: LearningPriority;
}

export interface SkillGapResult {
  matching_skills: string[];
  partially_matching_skills: string[];
  transferable_skills: string[];
  missing_skills: MissingSkill[];
}

export interface KeywordCoverage {
  matched_keywords: string[];
  missing_keywords: string[];
}

export interface ATSAnalysisResult {
  ats_score: number;
  score_explanation: string;
  keyword_coverage: KeywordCoverage;
  section_structure_issues: string[];
  formatting_issues: string[];
  job_title_alignment_note: string | null;
  improvement_suggestions: string[];
  methodology_note: string;
}

export type RelevanceLevel = "high" | "medium" | "low";

export interface ProjectRelevance {
  project_name: string;
  relevance_to_role: RelevanceLevel;
  relevant_technologies: string[];
  notes: string;
}

export interface ExperienceAnalysisResult {
  overall_relevance_summary: string;
  project_relevance: ProjectRelevance[];
  technical_depth_assessment: string;
  quantifiable_achievements_found: string[];
  missing_evidence: string[];
  weak_descriptions: string[];
  improvement_suggestions: string[];
}

export interface SubScoreBreakdown {
  technical_skill_match: number;
  ats_keyword_match: number;
  experience_project_match: number;
  education_match: number;
  domain_match: number;
}

export interface MatchingResult {
  overall_match_score: number;
  sub_scores: SubScoreBreakdown;
  weights_used: SubScoreBreakdown;
  methodology_note: string;
  narrative_summary: string;
}

export interface RecommendationResult {
  skills_to_learn: string[];
  technologies_to_practice: string[];
  project_ideas: string[];
  resume_improvements: string[];
  relevant_certifications: string[];
  interview_prep_focus_areas: string[];
  short_term_roadmap: string[];
}

export type QuestionCategory =
  | "technical"
  | "genai"
  | "python"
  | "ml"
  | "rag"
  | "agents"
  | "project"
  | "behavioral";

export interface InterviewQuestion {
  question: string;
  category: QuestionCategory;
  rationale: string;
}

export interface InterviewPrepResult {
  questions: InterviewQuestion[];
}

export interface AnalysisErrorDetail {
  agent: string;
  message: string;
}

export type AnalysisStatus = "pending" | "running" | "completed" | "failed";

export interface AnalysisResponse {
  id: string;
  status: AnalysisStatus;
  current_step: string | null;
  resume_id: string;
  job_description_id: string;
  created_at: string;
  completed_at: string | null;

  resume_extraction: ResumeExtraction | null;
  jd_extraction: JobExtraction | null;
  skill_gap_result: SkillGapResult | null;
  ats_result: ATSAnalysisResult | null;
  experience_result: ExperienceAnalysisResult | null;
  matching_result: MatchingResult | null;
  recommendation_result: RecommendationResult | null;
  interview_result: InterviewPrepResult | null;

  recommendation_sources: string[];
  interview_sources: string[];

  errors: AnalysisErrorDetail[];
}
