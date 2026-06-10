export type AssessmentAnswers = {
  age: number;
  sex: "female" | "male";
  systolic_bp: number;
  diastolic_bp: number;
  total_cholesterol: number;
  hdl_cholesterol: number;
  ldl_cholesterol: number;
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
