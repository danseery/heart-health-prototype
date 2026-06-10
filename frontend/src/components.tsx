import { useEffect, useState } from "react";
import { ArrowRight } from "lucide-react";

import { normalizeNumberInput } from "./riskDisplay";
import type { ClinicalSignal } from "./types";

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
  value: number;
  min: number;
  max: number;
  unit?: string;
  onChange: (value: number) => void;
}) {
  const [draftValue, setDraftValue] = useState(String(props.value));

  useEffect(() => {
    setDraftValue(String(props.value));
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
            if (normalized !== null) props.onChange(normalized);
          }}
          onBlur={(event) => {
            const normalized = normalizeNumberInput(event.target.value);
            if (normalized === null) {
              setDraftValue(String(props.value));
              return;
            }

            props.onChange(normalized);
            setDraftValue(String(normalized));
          }}
        />
        {props.unit ? <small>{props.unit}</small> : null}
      </div>
    </label>
  );
}

export function OptionalNumberField(props: {
  label: string;
  value: number | null;
  min: number;
  max: number;
  step?: string;
  unit?: string;
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
          placeholder="Optional"
          onChange={(event) => {
            const nextValue = event.target.value;
            const normalized = normalizeNumberInput(nextValue);
            setDraftValue(nextValue);
            if (nextValue === "") props.onChange(null);
            if (normalized !== null) props.onChange(normalized);
          }}
          onBlur={(event) => {
            const normalized = normalizeNumberInput(event.target.value);
            props.onChange(normalized);
            setDraftValue(normalized?.toString() ?? "");
          }}
        />
        {props.unit ? <small>{props.unit}</small> : null}
      </div>
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
