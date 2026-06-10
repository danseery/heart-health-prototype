export type ThemeName = "light" | "dark";

export function applyTheme(theme: ThemeName) {
  document.documentElement.setAttribute("data-theme", theme);
}
