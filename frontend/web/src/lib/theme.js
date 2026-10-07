// 라이트/다크 테마
import { $, ic } from "./dom.js";

export function applyTheme(t) { document.documentElement.dataset.theme = t; try { localStorage.setItem("kit-theme", t); } catch (e) {} renderThemeBtn(); }
export function renderThemeBtn() { const b = $("#theme-btn"); if (b) b.innerHTML = ic(document.documentElement.dataset.theme === "dark" ? "sun" : "moon"); }
export function initTheme() {
  let t = null; try { t = localStorage.getItem("kit-theme"); } catch (e) {}
  if (!t) t = matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
  document.documentElement.dataset.theme = t;
}
