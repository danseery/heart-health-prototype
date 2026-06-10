import React, { FormEvent, useMemo, useState } from "react";
import ReactDOM from "react-dom/client";
import { Activity, HeartPulse, ShieldCheck } from "lucide-react";

import {
  NumberField,
  OptionalCheckbox,
  OptionalNumberField,
  ScoreCard,
  SelectField,
  SignalSection,
  SubmitButton,
  ThemeToggle,
} from "./components";
import {
  ascvdTone,
  framinghamTone,
  heartAgeHelper,
  heartAgeTone,
} from "./riskDisplay";
import "./styles.css";
import { applyTheme, type ThemeName } from "./theme";
import type { AssessmentAnswers, ContentSummary, ResultResponse } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api";

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
  established_ascvd: null,
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
  const [theme, setTheme] = useState<ThemeName>("light");

  React.useEffect(() => {
    applyTheme(theme);
  }, [theme]);

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
      <div className="theme-switch">
        <ThemeToggle
          checked={theme === "dark"}
          onChange={(checked) => setTheme(checked ? "dark" : "light")}
        />
      </div>

      <section className="hero">
        <div className="brand-mark" aria-hidden="true">
          <HeartPulse size={30} strokeWidth={2.2} />
        </div>
        <div>
          <p className="eyebrow">HeartHealth AI</p>
          <h1>Your heart health, translated.</h1>
          <p className="lede">
            Review key cardiovascular inputs, spot meaningful signals, and prepare
            clearer questions for your next healthcare conversation.
          </p>
        </div>
      </section>

      <section className="workspace" aria-label="Heart health assessment">
        <form className="assessment-panel" onSubmit={submitAssessment}>
          <div className="panel-heading">
            <Activity size={22} aria-hidden="true" />
            <div>
              <h2>Risk Assessment</h2>
              <p>Enter values you want to review and interpret.</p>
            </div>
          </div>

          <div className="field-grid">
            <NumberField
              label="Age"
              value={answers.age}
              min={18}
              max={100}
              onChange={(value) => updateAnswer("age", value)}
            />
            <SelectField
              label="Sex"
              value={answers.sex}
              options={[
                ["female", "Female"],
                ["male", "Male"],
              ]}
              onChange={(value) => updateAnswer("sex", value as AssessmentAnswers["sex"])}
            />
            <NumberField
              label="Systolic BP"
              value={answers.systolic_bp}
              min={70}
              max={260}
              unit="mmHg"
              onChange={(value) => updateAnswer("systolic_bp", value)}
            />
            <NumberField
              label="Diastolic BP"
              value={answers.diastolic_bp}
              min={30}
              max={160}
              unit="mmHg"
              onChange={(value) => updateAnswer("diastolic_bp", value)}
            />
            <NumberField
              label="Total cholesterol"
              value={answers.total_cholesterol}
              min={50}
              max={500}
              unit="mg/dL"
              onChange={(value) => updateAnswer("total_cholesterol", value)}
            />
            <NumberField
              label="HDL cholesterol"
              value={answers.hdl_cholesterol}
              min={10}
              max={150}
              unit="mg/dL"
              onChange={(value) => updateAnswer("hdl_cholesterol", value)}
            />
            <NumberField
              label="LDL cholesterol"
              value={answers.ldl_cholesterol}
              min={0}
              max={400}
              unit="mg/dL"
              onChange={(value) => updateAnswer("ldl_cholesterol", value)}
            />
            <SelectField
              label="Smoking status"
              value={answers.smoking_status}
              options={[
                ["never", "Never"],
                ["former", "Former"],
                ["current", "Current"],
              ]}
              onChange={(value) =>
                updateAnswer("smoking_status", value as AssessmentAnswers["smoking_status"])
              }
            />
            <SelectField
              label="Diabetes"
              value={answers.diabetes}
              options={[
                ["no", "No"],
                ["yes", "Yes"],
                ["not_sure", "Not sure"],
              ]}
              onChange={(value) =>
                updateAnswer("diabetes", value as AssessmentAnswers["diabetes"])
              }
            />
          </div>

          <label className="checkbox-field">
            <input
              type="checkbox"
              checked={answers.on_bp_medication}
              onChange={(event) => updateAnswer("on_bp_medication", event.target.checked)}
            />
            Currently taking blood pressure medication
          </label>

          <details className="advanced-section">
            <summary className="advanced-summary">
              <span>Advanced Risk Factors</span>
              <small>Optional labs, history, and cardiac tests</small>
            </summary>
            <div className="advanced-content">
              <p>
                Add these only if you already have them. The basic assessment works without
                any advanced values.
              </p>
              <details className="advanced-group">
                <summary>Clinical history</summary>
                <div className="checkbox-grid">
                  <OptionalCheckbox
                    label="Established ASCVD or prior cardiovascular event"
                    checked={answers.established_ascvd}
                    onChange={(value) => updateAnswer("established_ascvd", value)}
                  />
                  <OptionalCheckbox
                    label="Family history of premature ASCVD"
                    checked={answers.family_history_premature_ascvd}
                    onChange={(value) => updateAnswer("family_history_premature_ascvd", value)}
                  />
                  <OptionalCheckbox
                    label="Chronic kidney disease"
                    checked={answers.chronic_kidney_disease}
                    onChange={(value) => updateAnswer("chronic_kidney_disease", value)}
                  />
                  <OptionalCheckbox
                    label="Metabolic syndrome"
                    checked={answers.metabolic_syndrome}
                    onChange={(value) => updateAnswer("metabolic_syndrome", value)}
                  />
                  <OptionalCheckbox
                    label="Chronic inflammatory condition"
                    checked={answers.inflammatory_condition}
                    onChange={(value) => updateAnswer("inflammatory_condition", value)}
                  />
                  <OptionalCheckbox
                    label="Premature menopause"
                    checked={answers.premature_menopause}
                    onChange={(value) => updateAnswer("premature_menopause", value)}
                  />
                  <OptionalCheckbox
                    label="History of preeclampsia"
                    checked={answers.preeclampsia_history}
                    onChange={(value) => updateAnswer("preeclampsia_history", value)}
                  />
                  <OptionalCheckbox
                    label="South Asian ancestry"
                    checked={answers.south_asian_ancestry}
                    onChange={(value) => updateAnswer("south_asian_ancestry", value)}
                  />
                </div>
              </details>

              <details className="advanced-group">
                <summary>Advanced labs</summary>
                <div className="field-grid">
                  <OptionalNumberField
                    label="Lp(a)"
                    value={answers.lpa_mg_dl}
                    min={0}
                    max={500}
                    step="0.1"
                    unit="mg/dL"
                    onChange={(value) => updateAnswer("lpa_mg_dl", value)}
                  />
                  <OptionalNumberField
                    label="ApoB"
                    value={answers.apob_mg_dl}
                    min={20}
                    max={300}
                    unit="mg/dL"
                    onChange={(value) => updateAnswer("apob_mg_dl", value)}
                  />
                  <OptionalNumberField
                    label="hs-CRP"
                    value={answers.hs_crp_mg_l}
                    min={0}
                    max={100}
                    step="0.1"
                    unit="mg/L"
                    onChange={(value) => updateAnswer("hs_crp_mg_l", value)}
                  />
                  <OptionalNumberField
                    label="A1c"
                    value={answers.a1c_percent}
                    min={3}
                    max={18}
                    step="0.1"
                    unit="%"
                    onChange={(value) => updateAnswer("a1c_percent", value)}
                  />
                  <OptionalNumberField
                    label="eGFR (mL/min/1.73 m2)"
                    value={answers.egfr}
                    min={0}
                    max={150}
                    onChange={(value) => updateAnswer("egfr", value)}
                  />
                  <OptionalNumberField
                    label="Triglycerides"
                    value={answers.triglycerides}
                    min={20}
                    max={3000}
                    unit="mg/dL"
                    onChange={(value) => updateAnswer("triglycerides", value)}
                  />
                </div>
              </details>

              <details className="advanced-group">
                <summary>Cardiac tests</summary>
                <div className="field-grid">
                  <OptionalNumberField
                    label="CAC score"
                    value={answers.cac_score}
                    min={0}
                    max={5000}
                    unit="Agatston"
                    onChange={(value) => updateAnswer("cac_score", value)}
                  />
                  <OptionalNumberField
                    label="Ankle-brachial index"
                    value={answers.ankle_brachial_index}
                    min={0}
                    max={2.5}
                    step="0.01"
                    onChange={(value) => updateAnswer("ankle_brachial_index", value)}
                  />
                </div>
                <div className="checkbox-grid compact">
                  <OptionalCheckbox
                    label="Carotid plaque documented"
                    checked={answers.carotid_plaque}
                    onChange={(value) => updateAnswer("carotid_plaque", value)}
                  />
                  <OptionalCheckbox
                    label="LVH on ECG/echo"
                    checked={answers.left_ventricular_hypertrophy}
                    onChange={(value) => updateAnswer("left_ventricular_hypertrophy", value)}
                  />
                  <OptionalCheckbox
                    label="History of atrial fibrillation"
                    checked={answers.atrial_fibrillation_history}
                    onChange={(value) => updateAnswer("atrial_fibrillation_history", value)}
                  />
                </div>
              </details>
            </div>
          </details>

          {error ? <p className="error">{error}</p> : null}
          <SubmitButton isSubmitting={isSubmitting} />
        </form>

        <section className="results-panel" aria-live="polite">
          {result ? (
            <>
              <div className="panel-heading results-heading">
                <ShieldCheck size={22} aria-hidden="true" />
                <div>
                  <h2>Risk Snapshot</h2>
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

              <div className="ai-summary ai-summary--featured">
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

              <div className="signal-grid">
                <SignalSection
                  title="Protective Signals"
                  items={result.protective_signals ?? []}
                  variant="protective"
                />

                <SignalSection
                  title="Your Risk Factors"
                  items={result.risk_factors ?? []}
                  variant="risk"
                />
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
                  <small>{contentSummary.author}</small>
                </aside>
              ) : null}
            </>
          ) : (
            <div className="empty-state">
              <ShieldCheck size={34} aria-hidden="true" />
              <h2>Your results will appear here</h2>
              <p>
                Complete the assessment to see your score cards, key signals, and an
                educational summary in one focused view.
              </p>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
