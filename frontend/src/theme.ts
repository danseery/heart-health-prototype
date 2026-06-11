export type ThemeName = "light" | "dark";

const THEME_STORAGE_KEY = "hearty.theme";

export function applyTheme(theme: ThemeName) {
  document.documentElement.setAttribute("data-theme", theme);
}

export function loadSavedTheme(): ThemeName | null {
  if (typeof window === "undefined") return null;

  const savedTheme = window.sessionStorage.getItem(THEME_STORAGE_KEY);
  return savedTheme === "dark" || savedTheme === "light" ? savedTheme : null;
}

export function resolveInitialTheme(): ThemeName {
  if (typeof window === "undefined") return "light";

  const savedTheme = loadSavedTheme();
  if (savedTheme) return savedTheme;

  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function saveTheme(theme: ThemeName) {
  if (typeof window === "undefined") return;

  window.sessionStorage.setItem(THEME_STORAGE_KEY, theme);
}
