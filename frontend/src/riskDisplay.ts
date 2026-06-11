export function ascvdTone(risk: number) {
  if (risk < 5) return "green";
  if (risk < 7.5) return "yellow";
  if (risk < 20) return "orange";
  return "red";
}

export function framinghamTone(risk: number) {
  if (risk < 5) return "green";
  if (risk < 10) return "yellow";
  if (risk < 20) return "orange";
  return "red";
}

export function heartAgeTone(heartAge: number, actualAge: number) {
  const delta = heartAge - actualAge;
  if (delta <= 0) return "green";
  if (delta <= 5) return "yellow";
  if (delta <= 10) return "orange";
  return "red";
}

export function heartAgeHelper(heartAge: number, actualAge: number) {
  const delta = heartAge - actualAge;
  if (delta <= 0) return "at or below age";
  return `+${delta} years`;
}

export function normalizeNumberInput(value: string) {
  const trimmed = value.trim();
  if (trimmed === "") return null;
  const normalized = Number(trimmed);
  return Number.isFinite(normalized) ? normalized : null;
}
