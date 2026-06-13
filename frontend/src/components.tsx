import { useEffect, useState } from "react";
import { Apple, ArrowRight, Dumbbell, Moon } from "lucide-react";

import { normalizeNumberInput } from "./riskDisplay";
import type {
  ClinicalSignal,
  HeartPlanCard,
  HeartPlanCitation,
  HeartPlanResponse,
  HeartPlanSection,
  LearningResource,
} from "./types";

export function ThemeToggle(props: { checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <label className="theme-toggle" htmlFor="theme-toggle">
      <input
        id="theme-toggle"
        type="checkbox"
        checked={props.checked}
        onChange={(event) => props.onChange(event.target.checked)}
      />
      <span className="theme-toggle-track" aria-hidden="true">
        <span className="theme-toggle-thumb" />
      </span>
      <span className="theme-toggle-label">Dark Mode</span>
    </label>
  );
}

export function NumberField(props: {
  label: string;
  value: number | null;
  unit?: string;
  error?: string;
  onChange: (value: number | null) => void;
}) {
  const [draftValue, setDraftValue] = useState(props.value?.toString() ?? "");

  useEffect(() => {
    setDraftValue(props.value?.toString() ?? "");
  }, [props.value]);

  return (
    <label className="field">
      <span>{props.label}</span>
      <div className="input-with-unit">
        <input
          type="text"
          inputMode="decimal"
          value={draftValue}
          onChange={(event) => {
            const nextValue = event.target.value;
            const normalized = normalizeNumberInput(nextValue);
            setDraftValue(nextValue);
            props.onChange(nextValue === "" ? null : normalized);
          }}
          onBlur={(event) => {
            const normalized = normalizeNumberInput(event.target.value);
            props.onChange(normalized);
            setDraftValue(normalized === null ? "" : String(normalized));
          }}
          aria-invalid={props.error ? "true" : "false"}
        />
        {props.unit ? <small>{props.unit}</small> : null}
      </div>
      {props.error ? <small className="field-error">{props.error}</small> : null}
    </label>
  );
}

export function OptionalNumberField(props: {
  label: string;
  value: number | null;
  unit?: string;
  error?: string;
  onChange: (value: number | null) => void;
}) {
  const [draftValue, setDraftValue] = useState(props.value?.toString() ?? "");

  useEffect(() => {
    setDraftValue(props.value?.toString() ?? "");
  }, [props.value]);

  return (
    <label className="field">
      <span>{props.label}</span>
      <div className="input-with-unit">
        <input
          type="text"
          inputMode="decimal"
          value={draftValue}
          onChange={(event) => {
            const nextValue = event.target.value;
            const normalized = normalizeNumberInput(nextValue);
            setDraftValue(nextValue);
            props.onChange(nextValue === "" ? null : normalized);
          }}
          onBlur={(event) => {
            const normalized = normalizeNumberInput(event.target.value);
            props.onChange(normalized);
            setDraftValue(normalized?.toString() ?? "");
          }}
          aria-invalid={props.error ? "true" : "false"}
        />
        {props.unit ? <small>{props.unit}</small> : null}
      </div>
      {props.error ? <small className="field-error">{props.error}</small> : null}
    </label>
  );
}

export function OptionalCheckbox(props: {
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

export function SelectField(props: {
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

export function SubmitButton(props: { isSubmitting: boolean }) {
  return (
    <button className="primary-button" type="submit" disabled={props.isSubmitting}>
      {props.isSubmitting ? "Calculating..." : "Calculate Results"}
      <ArrowRight size={18} aria-hidden="true" />
    </button>
  );
}

export function ScoreCard(props: {
  label: string;
  value: string;
  helper?: string;
  tone: string;
  onClick?: () => void;
}) {
  return (
    <button
      className={`score-card tone-${props.tone}`}
      type="button"
      onClick={props.onClick}
      aria-label={`Learn about ${props.label}`}
    >
      <span>{props.label}</span>
      <strong>{props.value}</strong>
      {props.helper ? <small>{props.helper}</small> : null}
    </button>
  );
}

export function SignalSection(props: {
  title: string;
  items: ClinicalSignal[];
  variant: "protective" | "risk";
}) {
  if (!props.items.length) return null;

  return (
    <section className={`signal-section signal-section--${props.variant}`}>
      <h3>{props.title}</h3>
      {props.items.map((item) => (
        <article className="signal-item" key={`${props.variant}-${item.label}`}>
          <div className="signal-header">
            <strong>{item.label}</strong>
            <span
              className={
                props.variant === "protective"
                  ? "signal-value signal-value--positive"
                  : `signal-value severity-${item.severity}`
              }
            >
              {item.value}
            </span>
          </div>
          <p>{item.explanation}</p>
        </article>
      ))}
    </section>
  );
}

export function HeartPlan(props: {
  plan: HeartPlanResponse | null;
  isLoading: boolean;
  error: string | null;
  loadingContentId: string | null;
  onOpenCitation: (citation: HeartPlanCitation) => void;
  onOpenLearningResource: (resource: LearningResource) => void;
}) {
  const [activeSection, setActiveSection] = useState("all");
  const [activePriority, setActivePriority] = useState("all");
  const sections = props.plan?.sections ?? [];
  const sourceList = uniqueLearningResources(sections);
  const streamItems = sections.flatMap((section) =>
    section.cards.map((card) => ({ section, card })),
  );
  const visibleItems = streamItems.filter((item) => {
    const sectionMatches = activeSection === "all" || item.section.section === activeSection;
    const priorityMatches = activePriority === "all" || item.card.priority === activePriority;
    return sectionMatches && priorityMatches;
  });
  const highPriorityCount = streamItems.filter((item) => item.card.priority === "high").length;
  const sectionItems =
    activeSection === "all"
      ? streamItems
      : streamItems.filter((item) => item.section.section === activeSection);
  const availablePriorities = new Set(sectionItems.map((item) => item.card.priority));
  const priorities = [
    ["all", "Any priority"],
    ["high", "High"],
    ["medium", "Medium"],
    ["low", "Low"],
  ];

  useEffect(() => {
    if (activePriority !== "all" && !availablePriorities.has(activePriority)) {
      setActivePriority("all");
    }
  }, [activePriority, availablePriorities]);

  if (props.isLoading) {
    return (
      <section className="heart-plan" aria-label="Personalized Heart Plan">
        <div className="heart-plan-heading">
          <div>
            <span>Personalized Heart Plan</span>
            <h3>Preparing nutrition, fitness, and lifestyle guidance...</h3>
          </div>
        </div>
      </section>
    );
  }

  if (props.error) {
    return (
      <section className="heart-plan" aria-label="Personalized Heart Plan">
        <div className="heart-plan-heading">
          <div>
            <span>Personalized Heart Plan</span>
            <h3>Recommendations are temporarily unavailable.</h3>
            <p>{props.error}</p>
          </div>
        </div>
      </section>
    );
  }

  if (!props.plan) return null;

  return (
    <section className="heart-plan" aria-label="Personalized Heart Plan">
      <div className="heart-plan-heading">
        <div>
          <span>Heart Plan</span>
          <h3>Your next cardiology learning path</h3>
          <p>
            Start with the highest-signal items, then dip into nutrition, fitness, or
            lifestyle when you want specifics.
          </p>
        </div>
      </div>

      <div className="plan-briefing-strip" aria-label="Heart Plan summary">
        <div>
          <strong>{streamItems.length}</strong>
          <span>learning items</span>
        </div>
        <div>
          <strong>{highPriorityCount}</strong>
          <span>high priority</span>
        </div>
        <div>
          <strong>{sourceList.length}</strong>
          <span>Sources</span>
        </div>
      </div>

      <div className="filter-bar filter-bar--compact" aria-label="Heart Plan filters">
        <label className="compact-filter" aria-label="Heart Plan focus filter">
          <span>Focus</span>
          <select
            value={activeSection}
            onChange={(event) => setActiveSection(event.target.value)}
          >
            <option value="all">All</option>
            {sections.map((section) => (
              <option key={section.section} value={section.section}>
                {section.title}
              </option>
            ))}
          </select>
        </label>

        <label className="compact-filter" aria-label="Heart Plan priority filter">
          <span>Priority</span>
          <select
            value={activePriority}
            onChange={(event) => setActivePriority(event.target.value)}
          >
            {priorities.map(([value, label]) => (
              <option
                key={value}
                value={value}
                disabled={value !== "all" && !availablePriorities.has(value)}
              >
                {label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {visibleItems.length === 0 ? (
        <p className="empty-filter-state">No items match these filters.</p>
      ) : null}

      <div className="plan-stream">
        {visibleItems.map(({ section, card }, index) => (
          <article
            className={`plan-stream-item priority-${card.priority}`}
            key={`${section.section}-${card.title}`}
          >
            <div className="stream-index">{String(index + 1).padStart(2, "0")}</div>
            <div className="stream-body">
              <div className="stream-meta">
                <span className={`section-pill section-${section.section}`}>
                  <SectionIcon section={section.section} />
                  {section.title}
                </span>
                <span className={`priority-label priority-${card.priority}`}>
                  {card.priority}
                </span>
              </div>
              <h4>{card.title}</h4>
              <p>{card.why_it_matters}</p>
              <LearningFocus
                card={card}
                onOpenLearningResource={props.onOpenLearningResource}
              />
              <div className="stream-footer">
                <span>{card.clinician_question}</span>
                <InlineSourceButton
                  card={card}
                  loadingContentId={props.loadingContentId}
                  onOpenCitation={props.onOpenCitation}
                />
              </div>
            </div>
          </article>
        ))}
      </div>

      <div className="source-shelf source-shelf--footer" aria-label="Sources used">
        <div>
          <span>Sources used</span>
          <small>Curated cardiology resources</small>
        </div>
        <div>
          {sourceList.map((citation) => (
            <button
              key={citation.resource_id}
              type="button"
              onClick={() => props.onOpenLearningResource(citation)}
            >
              {citation.title}
            </button>
          ))}
        </div>
      </div>

      <div className="disclaimer" aria-label="Disclaimer">
        <span>Disclaimer</span>
        <p>{props.plan.disclaimer}</p>
      </div>
    </section>
  );
}

function SectionIcon(props: { section: HeartPlanSection["section"] }) {
  if (props.section === "fitness") return <Dumbbell size={16} aria-hidden="true" />;
  if (props.section === "lifestyle") return <Moon size={16} aria-hidden="true" />;
  return <Apple size={16} aria-hidden="true" />;
}

function InlineSourceButton(props: {
  card: HeartPlanCard;
  loadingContentId: string | null;
  onOpenCitation: (citation: HeartPlanCitation) => void;
}) {
  const primarySource = props.card.citations[0];
  if (!primarySource) return null;

  return (
    <button type="button" onClick={() => props.onOpenCitation(primarySource)}>
      {props.loadingContentId === primarySource.source_id ? "Loading..." : "Source"}
    </button>
  );
}

function LearningFocus(props: {
  card: HeartPlanCard;
  onOpenLearningResource: (resource: LearningResource) => void;
}) {
  const resource = props.card.learning_resource;
  if (!resource) {
    return (
      <div className="next-step">
        <span>Learning focus</span>
        <p>{props.card.educational_next_step}</p>
      </div>
    );
  }

  return (
    <button
      className="next-step next-step--link"
      type="button"
      onClick={() => props.onOpenLearningResource(resource)}
    >
      <span>Learning focus</span>
      <p>{props.card.educational_next_step}</p>
      <small>{resource.title}</small>
    </button>
  );
}

function uniqueLearningResources(sections: HeartPlanSection[]) {
  const resources = new Map<string, LearningResource>();
  for (const section of sections) {
    for (const card of section.cards) {
      if (card.learning_resource) {
        resources.set(card.learning_resource.resource_id, card.learning_resource);
      }
    }
  }
  return [...resources.values()];
}
