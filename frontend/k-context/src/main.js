// 부트: store 생성 → 레이아웃 마운트 → 모듈 마운트 → 데이터 로드.
// URL 파라미터: ?lang=en · ?theme=dark · ?api=mock|http|chat(&base=/api) · ?mode=old|now|both · ?day=1..3
import { createStore } from './lib/store.js';
import { createT, bindDocumentLang, normalizeLang } from './lib/i18n.js';
import { bindDocumentTheme } from './lib/theme.js';
import { h } from './lib/dom.js';
import { createApi } from './api/index.js';
import { safeBase } from './events/api.js';
import { createInitialState } from './state/initial.js';
import { createActions } from './state/actions.js';
import { mountAppShell } from './components/layout/app-shell.js';
import * as topbar from './components/layout/topbar.js';
import * as settings from './components/layout/settings.js';
import { MODULES } from './modules.js';

function initialFromUrl(search) {
  const q = new URLSearchParams(search);
  const o = {};
  if (q.has('lang')) o.lang = normalizeLang(q.get('lang'));
  if (['light', 'dark', 'auto'].includes(q.get('theme'))) o.theme = q.get('theme');
  if (['old', 'now', 'both'].includes(q.get('mode'))) o.mode = q.get('mode');
  if (['1', '2', '3'].includes(q.get('day'))) o.day = Number(q.get('day'));
  return o;
}

export function mountSafely(name, mod, slotEl, ctx) {
  try {
    return mod.mount(slotEl, ctx);
  } catch (e) {
    console.error(`[${name}] mount 실패`, e);
    slotEl.replaceChildren(h('div', { class: 'module-error', role: 'alert' }, ctx.t('module.error', { name }), ' — ', String(e?.message ?? e)));
    return { destroy() {} };
  }
}

export async function boot(rootEl = document.getElementById('app'), search = location.search) {
  const q = new URLSearchParams(search);
  const store = createStore(createInitialState(initialFromUrl(search)));
  const apiMode = ['http', 'chat'].includes(q.get('api')) ? q.get('api') : 'mock';
  // chat(챗봇만 backend)의 기본 주소: uvicorn 기본 포트. backend CORS 기본 허용 origin 은 http://localhost:8766.
  const baseUrl = safeBase(q.get('base')) || (apiMode === 'chat' ? 'http://localhost:8000/api' : undefined);
  const api = createApi({ mode: apiMode, baseUrl });
  const t = createT(() => store.getState().lang);
  const actions = createActions({ store, api });
  const ctx = { store, api, t, actions };

  bindDocumentLang(store);
  bindDocumentTheme(store);

  const shell = mountAppShell(rootEl, ctx);
  const mounted = [{ destroy: shell.destroy }, mountSafely('topbar', topbar, shell.slots.topbar, ctx), mountSafely('settings', settings, shell.slots.settings, ctx)];
  for (const [name, mod] of Object.entries(MODULES)) mounted.push(mountSafely(name, mod, shell.slots[name], ctx));

  await actions.loadAll();
  return { ctx, destroy: () => mounted.reverse().forEach((m) => m.destroy()) };
}

// 브라우저에서만 자동 부팅(node 에서 import 해 문법을 검사할 수 있게)
if (typeof document !== 'undefined') boot();
