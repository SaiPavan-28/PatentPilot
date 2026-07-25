/**
 * PatentPilot API Service Layer
 * Typed client for all backend endpoints.
 */

const BASE_URL = "http://localhost:8000/api/v1";

export interface MoleculeValidateResponse {
  valid: boolean;
  smiles: string;
  canonical_smiles?: string;
  molecular_formula?: string;
  molecular_weight?: number;
  num_atoms?: number;
  structure_svg?: string;
  error?: string;
}

export interface MoleculeSubmitRequest {
  smiles: string;
  molecule_name?: string;
  target?: string;
  indication?: string;
}

export interface AnalysisCreateResponse {
  id: string;
  status: string;
  smiles: string;
  molecule_name?: string;
  target?: string;
  indication?: string;
  structure_svg?: string;
  created_at?: string;
}

export interface ScoreBreakdown {
  chemical_similarity: number;
  target_match: number;
  disease_match: number;
  semantic_relevance: number;
  overall_score: number;
  confidence_score: number;
  evidence_flags: string[];
}

export interface PatentExplanation {
  why_retrieved: string;
  similar_aspects: string;
  possible_overlap: string;
  confidence_assessment: string;
  key_concerns?: string[];
}

export interface Patent {
  id: string;
  analysis_id: string;
  patent_number: string;
  title?: string;
  abstract?: string;
  claims?: string;
  assignee?: string;
  publication_date?: string;
  source?: string;
  patent_url?: string;
  pdf_url?: string;
  uspto_url?: string;
  epo_url?: string;
  google_patents_url?: string;
  verification_status?: {
    surechembl: boolean;
    patentsview: boolean;
    google_patents: boolean;
  };
  scores: ScoreBreakdown;
  explanation?: PatentExplanation;
  explanation_generated: boolean;
  rank: number;
  review_status?: string;
  created_at?: string;
}

export interface PatentsListResponse {
  analysis_id: string;
  analysis_status: string;
  patent_count: number;
  patents: Patent[];
}

export interface ReportResponse {
  id: string;
  analysis_id: string;
  executive_summary?: string;
  key_similar_patents: any[];
  novelty_concerns: string[];
  patents_requiring_review: any[];
  potential_novel_regions?: string;
  recommended_next_actions: string[];
  manual_review_checklist: string[];
  key_evidence: string[];
  recommendation?: string;
  risk_score?: number;
  confidence_score?: number;
  recommendation_rationale?: string;
  scoring_methodology_explanation?: string;
  generated_at?: string;
}

export interface AnalysisSummary {
  id: string;
  smiles: string;
  molecule_name?: string;
  target?: string;
  indication?: string;
  status: string;
  patent_count: number;
  risk_level?: string;
  risk_score?: number;
  created_at?: string;
}

export interface HistoryListResponse {
  items: AnalysisSummary[];
  total: number;
  page: number;
  per_page: number;
}

export interface AnalysisDetail {
  id: string;
  smiles: string;
  molecule_name?: string;
  target?: string;
  indication?: string;
  status: string;
  structure_svg?: string;
  patents: Patent[];
  report?: ReportResponse;
  created_at?: string;
}

export interface DashboardStats {
  total_analyses: number;
  risk_distribution: Record<string, number>;
  top_indications: { indication: string; count: number }[];
  top_targets: { target: string; count: number }[];
  source_distribution: Record<string, number>;
  recent_analyses: AnalysisSummary[];
}

// ── API Functions ──────────────────────────────────────────────────────────────

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Molecule
  validateSmiles: (smiles: string) =>
    request<MoleculeValidateResponse>("/molecule/validate", {
      method: "POST",
      body: JSON.stringify({ smiles }),
    }),

  submitMolecule: (data: MoleculeSubmitRequest) =>
    request<AnalysisCreateResponse>("/molecule/submit", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Patents
  getPatents: (analysisId: string, params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<PatentsListResponse>(`/patents/${analysisId}${qs}`);
  },

  updateReviewStatus: (patentId: string, status: string, notes?: string) =>
    request<any>(`/patents/${patentId}/review`, {
      method: "PUT",
      body: JSON.stringify({ status, notes }),
    }),

  // Report
  generateReport: (analysisId: string) =>
    request<ReportResponse>("/report/generate", {
      method: "POST",
      body: JSON.stringify({ analysis_id: analysisId }),
    }),

  getReport: (analysisId: string) =>
    request<ReportResponse>(`/report/${analysisId}`),

  // History
  getHistory: (page = 1, perPage = 10, search?: string) => {
    const params = new URLSearchParams({
      page: String(page),
      per_page: String(perPage),
      ...(search ? { search } : {}),
    });
    return request<HistoryListResponse>(`/history?${params}`);
  },

  getAnalysis: (id: string) =>
    request<AnalysisDetail>(`/history/${id}`),

  // Dashboard
  getDashboard: () => request<DashboardStats>("/dashboard"),

  // Health
  health: () => request<any>("/health"),
};
