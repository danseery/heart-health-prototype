import React, { FormEvent, useMemo, useState } from "react";
import ReactDOM from "react-dom/client";
import { Activity, ArrowRight, HeartPulse, ShieldCheck } from "lucide-react";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api";

type AssessmentAnswers = {
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

type ResultResponse = {
  session_id: string;
  status: string;
  scores: {
    ascvd_risk: number;
    framingham_risk: number;
    heart_age: number;
    category: string;
  };
  risk_factors: Array<{
    label: string;
    value: string;
    severity: string;
    explanation: string;
  }>;
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

type ContentSummary = {
  content_id: string;
  title: string;
  topic: string;
  author: string;
  summary: string;
  cached: boolean;
};

const initialAnswers: AssessmentAnswers = {
  age: 52,
  sex: "female",
  systolic_bp: 138,
  diastolic_bp: 88,
  total_cholesterol: 214,
  hdl_cholesterol: 44,
  ldl_cholesterol: 148,
  on_bp_medication: false,
  smoking_status: "never",
  diabetes: "no",
  family_history_premature_ascvd: null,
  chronic_kidney_disease: null,
  metabolic_syndrome: null,
  inflammatory_condition: null,
  premature_menopause: null,
  preeclampsia_history: null,
  south_asian_ancestry: null,
  cac_score: null,
  lpa_mg_dl: null,
  apob_mg_dl: null,
  hs_crp_mg_l: null,
  a1c_percent: null,
  egfr: null,
  triglycerides: null,
  ankle_brachial_index: null,
  carotid_plaque: null,
  left_ventricular_hypertrophy: null,
  atrial_fibrillation_history: null,
};

function App() {
  const [answers, setAnswers] = useState<AssessmentAnswers>(initialAnswers);
  const [result, setResult] = useState<ResultResponse | null>(null);
  const [contentSummary, setContentSummary] = useState<ContentSummary | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loadingContentId, setLoadingContentId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const categoryLabel = useMemo(() => {
    if (!result) return null;
    return result.scores.category.replace(/^\w/, (char) => char.toUpperCase());
  }, [result]);

  async function submitAssessment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      const sessionResponse = await fetch(`${API_BASE}/assessment/sessions`, {
        method: "POST",
      });
      if (!sessionResponse.ok) throw new Error("Could not start assessment.");
      const session = (await sessionResponse.json()) as { session_id: string };

      const answersResponse = await fetch(
        `${API_BASE}/assessment/sessions/${session.session_id}/answers`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(answers),
        },
      );
      if (!answersResponse.ok) throw new Error("Could not save assessment answers.");

      const resultResponse = await fetch(
        `${API_BASE}/assessment/sessions/${session.session_id}/complete`,
        { method: "POST" },
      );
      if (!resultResponse.ok) throw new Error("Could not calculate results.");
      setResult((await resultResponse.json()) as ResultResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function updateAnswer<Key extends keyof AssessmentAnswers>(
    key: Key,
    value: AssessmentAnswers[Key],
  ) {
    setAnswers((current) => ({ ...current, [key]: value }));
  }

  async function openContentSummary(contentId: string) {
    setLoadingContentId(contentId);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/content/${contentId}/summary`);
      if (!response.ok) throw new Error("Could not load content summary.");
      setContentSummary((await response.json()) as ContentSummary);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoadingContentId(null);
    }
  }

  return (
    <main className="app-shell">
      <section className="hero">
        <div className="brand-mark" aria-hidden="true">
          <HeartPulse size={30} strokeWidth={2.2} />
        </div>
        <div>
          <p className="eyebrow">HeartHealth AI</p>
          <h1>Understand your heart health numbers in plain English.</h1>
          <p className="lede">
            Complete a quick demo assessment and see how clinical-style inputs can become
            clear risk signals, education, and doctor-ready talking points.
          </p>
        </div>
      </section>

      <section className="workspace" aria-label="Heart health assessment">
        <form className="assessment-panel" onSubmit={submitAssessment}>
          <div className="panel-heading">
            <Activity size={22} aria-hidden="true" />
            <div>
              <h2>Risk Assessment</h2>
              <p>Use synthetic demo values only.</p>
            </div>
          </div>

          <div className="field-grid">
            <NumberField label="Age" value={answers.age} min={18} max={100} onChange={(value) => updateAnswer("age", value)} />
            <SelectField label="Sex" value={answers.sex} options={[["female", "Female"], ["male", "Male"]]} onChange={(value) => updateAnswer("sex", value as AssessmentAnswers["sex"])} />
            <NumberField label="Systolic BP" value={answers.systolic_bp} min={70} max={260} unit="mmHg" onChange={(value) => updateAnswer("systolic_bp", value)} />
            <NumberField label="Diastolic BP" value={answers.diastolic_bp} min={30} max={160} unit="mmHg" onChange={(value) => updateAnswer("diastolic_bp", value)} />
            <NumberField label="Total cholesterol" value={answers.total_cholesterol} min={50} max={500} unit="mg/dL" onChange={(value) => updateAnswer("total_cholesterol", value)} />
            <NumberField label="HDL cholesterol" value={answers.hdl_cholesterol} min={10} max={150} unit="mg/dL" onChange={(value) => updateAnswer("hdl_cholesterol", value)} />
            <NumberField label="LDL cholesterol" value={answers.ldl_cholesterol} min={0} max={400} unit="mg/dL" onChange={(value) => updateAnswer("ldl_cholesterol", value)} />
            <SelectField label="Smoking status" value={answers.smoking_status} options={[["never", "Never"], ["former", "Former"], ["current", "Current"]]} onChange={(value) => updateAnswer("smoking_status", value as AssessmentAnswers["smoking_status"])} />
            <SelectField label="Diabetes" value={answers.diabetes} options={[["no", "No"], ["yes", "Yes"], ["not_sure", "Not sure"]]} onChange={(value) => updateAnswer("diabetes", value as AssessmentAnswers["diabetes"])} />
          </div>

          <label className="checkbox-field">
            <input
              type="checkbox"
              checked={answers.on_bp_medication}
              onChange={(event) => updateAnswer("on_bp_medication", event.target.checked)}
            />
            Currently taking blood pressure medication
          </label>

          <section className="advanced-section">
            <div className="advanced-heading">
              <h3>Advanced Risk Factors</h3>
              <p>Optional. Leave these collapsed if you only want the basic assessment.</p>
            </div>
            <details>
              <summary>Clinical history</summary>
              <div className="checkbox-grid">
                <OptionalCheckbox label="Family history of premature ASCVD" checked={answers.family_history_premature_ascvd} onChange={(value) => updateAnswer("family_history_premature_ascvd", value)} />
                <OptionalCheckbox label="Chronic kidney disease" checked={answers.chronic_kidney_disease} onChange={(value) => updateAnswer("chronic_kidney_disease", value)} />
                <OptionalCheckbox label="Metabolic syndrome" checked={answers.metabolic_syndrome} onChange={(value) => updateAnswer("metabolic_syndrome", value)} />
                <OptionalCheckbox label="Chronic inflammatory condition" checked={answers.inflammatory_condition} onChange={(value) => updateAnswer("inflammatory_condition", value)} />
                <OptionalCheckbox label="Premature menopause" checked={answers.premature_menopause} onChange={(value) => updateAnswer("premature_menopause", value)} />
                <OptionalCheckbox label="History of preeclampsia" checked={answers.preeclampsia_history} onChange={(value) => updateAnswer("preeclampsia_history", value)} />
                <OptionalCheckbox label="South Asian ancestry" checked={answers.south_asian_ancestry} onChange={(value) => updateAnswer("south_asian_ancestry", value)} />
              </div>
            </details>
            <details>
              <summary>Advanced labs</summary>
              <div className="field-grid">
                <OptionalNumberField label="Lp(a)" value={answers.lpa_mg_dl} min={0} max={500} step="0.1" unit="mg/dL" onChange={(value) => updateAnswer("lpa_mg_dl", value)} />
                <OptionalNumberField label="ApoB" value={answers.apob_mg_dl} min={20} max={300} unit="mg/dL" onChange={(value) => updateAnswer("apob_mg_dl", value)} />
                <OptionalNumberField label="hs-CRP" value={answers.hs_crp_mg_l} min={0} max={100} step="0.1" unit="mg/L" onChange={(value) => updateAnswer("hs_crp_mg_l", value)} />
                <OptionalNumberField label="A1c" value={answers.a1c_percent} min={3} max={18} step="0.1" unit="%" onChange={(value) => updateAnswer("a1c_percent", value)} />
                <OptionalNumberField label="eGFR (mL/min/1.73 m2)" value={answers.egfr} min={0} max={150} onChange={(value) => updateAnswer("egfr", value)} />
                <OptionalNumberField label="Triglycerides" value={answers.triglycerides} min={20} max={3000} unit="mg/dL" onChange={(value) => updateAnswer("triglycerides", value)} />
              </div>
            </details>
            <details>
              <summary>Cardiac tests</summary>
              <div className="field-grid">
                <OptionalNumberField label="CAC score" value={answers.cac_score} min={0} max={5000} unit="Agatston" onChange={(value) => updateAnswer("cac_score", value)} />
                <OptionalNumberField label="Ankle-brachial index" value={answers.ankle_brachial_index} min={0} max={2.5} step="0.01" onChange={(value) => updateAnswer("ankle_brachial_index", value)} />
              </div>
              <div className="checkbox-grid compact">
                <OptionalCheckbox label="Carotid plaque documented" checked={answers.carotid_plaque} onChange={(value) => updateAnswer("carotid_plaque", value)} />
                <OptionalCheckbox label="LVH on ECG/echo" checked={answers.left_ventricular_hypertrophy} onChange={(value) => updateAnswer("left_ventricular_hypertrophy", value)} />
                <OptionalCheckbox label="History of atrial fibrillation" checked={answers.atrial_fibrillation_history} onChange={(value) => updateAnswer("atrial_fibrillation_history", value)} />
              </div>
            </details>
          </section>

          {error ? <p className="error">{error}</p> : null}

          <button className="primary-button" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Calculating..." : "Calculate Demo Results"}
            <ArrowRight size={18} aria-hidden="true" />
          </button>
        </form>

        <section className="results-panel" aria-live="polite">
          {result ? (
            <>
              <div className="panel-heading">
                <ShieldCheck size={22} aria-hidden="true" />
                <div>
                  <h2>Results Dashboard</h2>
                  <p>{categoryLabel} risk category</p>
                </div>
              </div>
              <div className="score-grid">
                <ScoreCard
                  label="10-year ASCVD risk"
                  value={`${result.scores.ascvd_risk}%`}
                  tone={ascvdTone(result.scores.ascvd_risk)}
                />
                <ScoreCard
                  label="Framingham-style risk"
                  value={`${result.scores.framingham_risk}%`}
                  tone={framinghamTone(result.scores.framingham_risk)}
                />
                <ScoreCard
                  label="Heart age"
                  value={`${result.scores.heart_age}`}
                  helper={heartAgeHelper(result.scores.heart_age, answers.age)}
                  tone={heartAgeTone(result.scores.heart_age, answers.age)}
                />
              </div>
              <div className="risk-list">
                <h3>Your Risk Factors</h3>
                {result.risk_factors.map((factor) => (
                  <article key={factor.label}>
                    <div>
                      <strong>{factor.label}</strong>
                      <span>{factor.value}</span>
                    </div>
                    <p>{factor.explanation}</p>
                  </article>
                ))}
              </div>
              <div className="ai-summary">
                <h3>AI Summary</h3>
                <p>{result.ai_report.summary}</p>
                <div className="citations">
                  {result.ai_report.citations.map((citation) => (
                    <button
                      key={citation.source_id}
                      type="button"
                      onClick={() => openContentSummary(citation.source_id)}
                    >
                      {loadingContentId === citation.source_id ? "Loading..." : citation.title}
                    </button>
                  ))}
                </div>
                <p className="disclaimer">{result.ai_report.disclaimer}</p>
              </div>
              {contentSummary ? (
                <aside className="content-summary">
                  <div>
                    <span>{contentSummary.topic}</span>
                    <button type="button" onClick={() => setContentSummary(null)}>
                      Close
                    </button>
                  </div>
                  <h3>{contentSummary.title}</h3>
                  <p>{contentSummary.summary}</p>
                  <small>
                    {contentSummary.author} - {contentSummary.cached ? "Cached summary" : "Summary cached"}
                  </small>
                </aside>
              ) : null}
            </>
          ) : (
            <div className="empty-state">
              <ShieldCheck size={34} aria-hidden="true" />
              <h2>Your results will appear here</h2>
              <p>
                The backend will calculate risk signals, save a synthetic assessment,
                and return a grounded educational summary.
              </p>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}

function NumberField(props: {
  label: string;
  value: number;
  min: number;
  max: number;
  unit?: string;
  onChange: (value: number) => void;
}) {
  return (
    <label className="field">
      <span>{props.label}</span>
      <div className="input-with-unit">
        <input
          type="number"
          min={props.min}
          max={props.max}
          value={props.value}
          onChange={(event) => props.onChange(Number(event.target.value))}
        />
        {props.unit ? <small>{props.unit}</small> : null}
      </div>
    </label>
  );
}

function OptionalNumberField(props: {
  label: string;
  value: number | null;
  min: number;
  max: number;
  step?: string;
  unit?: string;
  onChange: (value: number | null) => void;
}) {
  return (
    <label className="field">
      <span>{props.label}</span>
      <div className="input-with-unit">
        <input
          type="number"
          min={props.min}
          max={props.max}
          step={props.step}
          value={props.value ?? ""}
          placeholder="Optional"
          onChange={(event) => {
            const value = event.target.value;
            props.onChange(value === "" ? null : Number(value));
          }}
        />
        {props.unit ? <small>{props.unit}</small> : null}
      </div>
    </label>
  );
}

function OptionalCheckbox(props: {
  label: string;
  checked: boolean | null;
  onChange: (value: boolean | null) => void;
}) {
  return (
    <label className="mini-checkbox">
      <input
        type="checkbox"
        checked={props.checked === true}
        onChange={(event) => props.onChange(event.target.checked ? true : null)}
      />
      {props.label}
    </label>
  );
}

function SelectField(props: {
  label: string;
  value: string;
  options: Array<[string, string]>;
  onChange: (value: string) => void;
}) {
  return (
    <label className="field">
      <span>{props.label}</span>
      <select value={props.value} onChange={(event) => props.onChange(event.target.value)}>
        {props.options.map(([value, label]) => (
          <option value={value} key={value}>
            {label}
          </option>
        ))}
      </select>
    </label>
  );
}

function ScoreCard(props: { label: string; value: string; helper?: string; tone: string }) {
  return (
    <article className={`score-card tone-${props.tone}`}>
      <span>{props.label}</span>
      <strong>{props.value}</strong>
      {props.helper ? <small>{props.helper}</small> : null}
    </article>
  );
}

function ascvdTone(risk: number) {
  if (risk < 5) return "green";
  if (risk < 7.5) return "yellow";
  if (risk < 20) return "orange";
  return "red";
}

function framinghamTone(risk: number) {
  if (risk < 5) return "green";
  if (risk < 10) return "yellow";
  if (risk < 20) return "orange";
  return "red";
}

function heartAgeTone(heartAge: number, actualAge: number) {
  const delta = heartAge - actualAge;
  if (delta <= 0) return "green";
  if (delta <= 5) return "yellow";
  if (delta <= 10) return "orange";
  return "red";
}

function heartAgeHelper(heartAge: number, actualAge: number) {
  const delta = heartAge - actualAge;
  if (delta <= 0) return "at or below age";
  return `+${delta} years`;
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
