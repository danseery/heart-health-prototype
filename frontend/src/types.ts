export type AssessmentAnswers = {
  age: number | null;
  sex: "female" | "male";
  systolic_bp: number | null;
  diastolic_bp: number | null;
  total_cholesterol: number | null;
  hdl_cholesterol: number | null;
  ldl_cholesterol: number | null;
  on_bp_medication: boolean;
  smoking_status: "never" | "former" | "current";
  diabetes: "no" | "yes" | "not_sure";
  established_ascvd: boolean | null;
  family_history_premature_ascvd: boolean | null;
  chronic_kidney_disease: boolean | null;
  metabolic_syndrome: boolean | null;
  inflammatory_condition: boolean | null;
  premature_menopause: boolean | null;
  preeclampsia_history: boolean | null;
  south_asian_ancestry: boolean | null;
  cac_score: number | null;
  lpa_mg_dl: number | null;
  apob_mg_dl: number | null;
  hs_crp_mg_l: number | null;
  a1c_percent: number | null;
  egfr: number | null;
  triglycerides: number | null;
  ankle_brachial_index: number | null;
  carotid_plaque: boolean | null;
  left_ventricular_hypertrophy: boolean | null;
  atrial_fibrillation_history: boolean | null;
};

export type ClinicalSignal = {
  label: string;
  value: string;
  severity: string;
  explanation: string;
};

export type ResultResponse = {
  session_id: string;
  status: string;
  scores: {
    ascvd_risk: number;
    framingham_risk: number;
    heart_age: number;
    category: string;
  };
  risk_factors: ClinicalSignal[];
  protective_signals: ClinicalSignal[];
  ai_report: {
    summary: string;
    disclaimer: string;
    citations: Array<{
      title: string;
      source_id: string;
      author: string;
    }>;
  };
};

export type ContentSummary = {
  content_id: string;
  title: string;
  topic: string;
  author: string;
  summary: string;
  cached: boolean;
};

export type HeartPlanCitation = {
  title: string;
  source_id: string;
  author: string;
  source_url?: string | null;
};

export type LearningResource = {
  resource_id: string;
  title: string;
  source: string;
  url: string;
  topic: string;
  applies_to: string[];
  priority: number;
};

export type HeartPlanCard = {
  title: string;
  priority: "high" | "medium" | "low" | string;
  trigger_signals: string[];
  why_it_matters: string;
  educational_next_step: string;
  learning_resource: LearningResource;
  clinician_question: string;
  citations: HeartPlanCitation[];
  disclaimer: string;
};

export type HeartPlanSection = {
  section: "nutrition" | "fitness" | "lifestyle" | string;
  title: string;
  cards: HeartPlanCard[];
};

export type HeartPlanResponse = {
  session_id: string;
  sections: HeartPlanSection[];
  generated_by: string;
  cached: boolean;
  disclaimer: string;
};
