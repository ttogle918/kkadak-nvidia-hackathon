// 관리자 검토 화면: 신규·변경 행사, 정보 충돌·누락, 수집 오류, 참여조건 확인 필요, 제보, 수동 확인 링크, 출처 현황.
// 토큰은 이 탭(sessionStorage)에만 둔다. 승인·반려의 신원은 서버가 정하고 요청에 싣지 않는다.
import { createStore } from '../lib/store.js';
import { h, on, render } from '../lib/dom.js';
import { createEventsApi, EventsApiError, safeBase } from './api.js';
import { makeT } from './i18n.js';
import { describeChange, loadJson, safeHref, safeStorage, saveJson } from './logic.js';

const TOKEN_KEY = 'kc.admin.token';

export function createAdmin({ api, session = null }) {
  const store = createStore({
    lang: 'ko', token: loadJson(session, TOKEN_KEY, ''), loading: false, error: null,
    review: null, sources: null, reports: [], busy: null, message: null,
  });
  const get = store.getState;
  const set = store.setState;
  const fail = (e) => set({ loading: false, busy: null, error: e instanceof EventsApiError && e.code === 'forbidden' ? 'admin.forbidden' : e instanceof EventsApiError && e.code === 'network' ? 'error.network' : 'error.server' });
  const a = {
    store,
    setLang: (lang) => set({ lang: lang === 'en' ? 'en' : 'ko' }),
    setToken(token) { set({ token }); saveJson(session, TOKEN_KEY, token); },
    async load() {
      const { token } = get();
      if (!token) { set({ error: 'admin.forbidden' }); return false; }
      set({ loading: true, error: null, message: null });
      try {
        const [review, sources, reports] = await Promise.all([api.admin.review(token), api.admin.sources(token), api.admin.reports(token)]);
        set({ review, sources, reports: reports.reports, loading: false });
        return true;
      } catch (e) { fail(e); return false; }
    },
    async decide(id, decision, note) {
      set({ busy: id, error: null });
      try {
        await api.admin.decide(get().token, id, decision, note);
        await a.load();
        set({ busy: null });
        return true;
      } catch (e) { fail(e); return false; }
    },
    async refresh(sourceId) {
      set({ busy: sourceId, error: null });
      try {
        const out = await api.admin.refresh(get().token, sourceId);
        await a.load();
        set({ busy: null, message: { source: sourceId, run: out.run } });
        return out.run;
      } catch (e) { fail(e); return null; }
    },
    async linkCheck(sourceId, note) {
      set({ busy: sourceId, error: null });
      try {
        await api.admin.linkCheck(get().token, sourceId, note);
        await a.load();
        set({ busy: null });
        return true;
      } catch (e) { fail(e); return false; }
    },
  };
  return a;
}

const empty = (t) => h('p', { class: 'ev-empty' }, t('admin.empty'));
const link = (url, text) => {
  const href = safeHref(url);
  return href ? h('a', { href, target: '_blank', rel: 'noopener noreferrer' }, text || href) : h('span', null, text || '');
};
const section = (title, count, ...children) => h('section', { class: 'ad-section' }, h('h2', null, title, ' ', h('span', { class: 'ad-count' }, `(${count})`)), ...children);

export function mountAdmin(root, { admin, api }) {
  const { store } = admin;
  const T = () => makeT(store.getState().lang);
  const tokenInput = h('input', { id: 'ad-token', type: 'password', autocomplete: 'off', value: store.getState().token });
  const loadBtn = h('button', { type: 'button', class: 'ev-btn is-primary', dataset: { act: 'load' } });
  const langBox = h('div', { class: 'seg' });
  const head = h('header', { class: 'ev-head' });
  const msg = h('p', { class: 'ev-error', role: 'alert' });
  const body = h('div', { class: 'ad-body' });
  const tokenRow = h('div', { class: 'ad-tokenrow' }, h('label', { class: 'ev-field', for: 'ad-token' }, h('span', { dataset: { i18n: 'admin.token' } }), tokenInput), loadBtn);
  const hint = h('p', { class: 'ev-meta' });
  render(root, head, tokenRow, hint, msg, body);

  const item = (e, ...extra) => h('div', { class: 'ad-item', dataset: { id: e.id } },
    h('p', null, h('strong', null, e.title), ` · ${e.verification} · ${e.last_verified_at ?? ''}`),
    e.links?.length ? h('p', { class: 'ev-meta' }, ...e.links.map((u) => [link(u, u), ' '])) : null, ...extra);

  function draw() {
    const s = store.getState();
    const t = T();
    render(head, h('h1', null, t('admin.title')), h('div', { class: 'seg' }, ...['ko', 'en'].map((l) => h('button', { type: 'button', class: ['seg__btn', s.lang === l && 'is-on'], dataset: { act: 'lang', value: l } }, t(`lang.${l}`)))));
    render(loadBtn, s.loading ? t('form.loading') : t('admin.load'));
    loadBtn.disabled = s.loading;
    render(tokenRow.children[0].children[0], t('admin.token'));
    render(hint, t('admin.token.hint'));
    render(msg, s.error ? t(s.error) : '');
    const r = s.review;
    if (!r) { render(body); return; }
    const nodes = [];
    nodes.push(section(t('admin.section.new'), r.new_or_changed.length, ...(r.new_or_changed.length ? r.new_or_changed.map((e) => item(e, h('ul', null, ...e.changes.map((c) => h('li', null, c.field === '__new__' ? `${c.importance}` : `${c.detected_at} · ${describeChange(c, t)} (${c.importance})`))))) : [empty(t)])));
    nodes.push(section(t('admin.section.conflicts'), r.conflicts.length, ...(r.conflicts.length ? r.conflicts.map((e) => item(e, h('ul', null, ...e.conflicts.map((c) => h('li', null, `${c.field}: ${c.values.map((v) => `${v.value} (${v.kind})`).join(' / ')}`))))) : [empty(t)])));
    nodes.push(section(t('admin.section.missing'), r.missing_info.length, ...(r.missing_info.length ? r.missing_info.map((e) => item(e, h('p', null, e.missing.map((k) => t(`check.${k}`)).join(', ')))) : [empty(t)])));
    nodes.push(section(t('admin.section.eligibility'), r.eligibility_check.length, ...(r.eligibility_check.length ? r.eligibility_check.map((e) => item(e, h('p', null, e.reasons.join(' · ')))) : [empty(t)])));
    nodes.push(section(t('admin.section.errors'), r.collection_errors.length, ...(r.collection_errors.length ? r.collection_errors.map((x) => h('div', { class: 'ad-item', dataset: { id: x.source_id } },
      h('p', null, h('strong', null, x.name), ` · ${t('admin.errors.failures')}: ${x.consecutive_failures}`), h('p', { class: 'ev-error' }, x.error ?? ''),
      h('p', { class: 'ev-meta' }, `${t('admin.last_success')}: ${x.last_success_at ?? t('coverage.never')} · ${t('admin.errors.retry')}: ${x.next_retry_at ?? '-'}`))) : [empty(t)])));
    nodes.push(section(t('admin.section.stale'), r.stale_sources.length, ...(r.stale_sources.length ? r.stale_sources.map((x) => h('p', null, `${x.source_id} · ${x.last_success_at}`)) : [empty(t)])));
    nodes.push(section(t('admin.section.reports'), s.reports.length, ...(s.reports.length ? s.reports.map((x) => h('div', { class: 'ad-item', dataset: { id: x.id } },
      h('p', null, h('strong', null, `${t(`report.kind.${x.kind}`)}`), ` · ${x.status} · ${x.submitted_at}`), h('p', null, x.reason),
      h('p', { class: 'ev-meta' }, link(x.official_link), x.entry_id ? ` · ${x.entry_id}` : ''),
      Object.keys(x.fields ?? {}).length ? h('p', { class: 'ev-meta' }, Object.entries(x.fields).map(([k, v]) => `${k}: ${v}`).join(' · ')) : null,
      x.status === 'pending' ? h('div', { class: 'ev-actions' },
        h('input', { type: 'text', class: 'ad-note', placeholder: t('admin.note'), dataset: { note: x.id }, maxlength: '300' }),
        h('button', { type: 'button', class: 'ev-btn is-primary', dataset: { act: 'approve', id: x.id } }, t('admin.approve')),
        h('button', { type: 'button', class: 'ev-btn', dataset: { act: 'reject', id: x.id } }, t('admin.reject'))) : h('p', { class: 'ev-meta' }, `${x.decided_by ?? ''} · ${x.decided_at ?? ''}`))) : [empty(t)])));
    nodes.push(section(t('admin.section.manual'), r.manual_links.length, ...(r.manual_links.length ? r.manual_links.map((m) => h('div', { class: 'ad-item', dataset: { id: m.source_id } },
      h('p', null, h('strong', null, m.name), m.due ? ` · ${t('admin.due')}` : ''), h('ul', null, ...m.links.map((l) => h('li', null, link(l.url, l.name || l.url)))),
      h('p', { class: 'ev-meta' }, m.notes), m.last_check ? h('p', { class: 'ev-meta' }, `${m.last_check.checked_at} · ${m.last_check.checked_by} · ${m.last_check.note}`) : null,
      h('div', { class: 'ev-actions' }, h('input', { type: 'text', class: 'ad-note', placeholder: t('admin.check.note'), dataset: { note: m.source_id }, maxlength: '300' }),
        h('button', { type: 'button', class: 'ev-btn', dataset: { act: 'check', id: m.source_id } }, t('admin.checked'))))) : [empty(t)])));
    const runs = s.sources?.runs ?? {};
    nodes.push(section(t('admin.section.sources'), (s.sources?.sources ?? []).length, ...(s.sources?.sources ?? []).map((x) => h('div', { class: 'ad-item', dataset: { id: x.id } },
      h('p', null, h('strong', null, x.name), ' ', link(x.url, '↗')), h('p', { class: 'ev-meta' }, `${t('admin.method')}: ${x.method} · ${t('admin.status')}: ${t(`admin.src.${x.status}`)} · ${t('admin.last_success')}: ${runs[x.id]?.last_success_at ?? t('coverage.never')}`),
      h('p', { class: 'ev-meta' }, `${t('admin.notes')}: ${x.notes}`),
      x.status === 'implemented' ? h('button', { type: 'button', class: 'ev-btn', disabled: s.busy === x.id, dataset: { act: 'refresh', id: x.id } }, t('admin.refresh')) : null))));
    if (s.message) nodes.push(h('p', { class: 'ev-status' }, `${t('admin.refreshed')}: ${s.message.source} — ${s.message.run.ok ? `ok (${s.message.run.fetched})` : s.message.run.error}`));
    render(body, ...nodes);
  }

  const offs = [];
  const input = () => admin.setToken(tokenInput.value.trim());
  tokenInput.addEventListener('input', input);
  offs.push(() => tokenInput.removeEventListener('input', input));
  const noteOf = (id) => [...(root.querySelectorAll?.('[data-note]') ?? [])].find((e) => e.dataset?.note === id)?.value ?? '';
  offs.push(on(root, 'click', '[data-act]', (_e, el) => {
    const { act, id, value } = el.dataset;
    if (act === 'load') admin.load();
    else if (act === 'lang') admin.setLang(value);
    else if (act === 'approve' || act === 'reject') admin.decide(id, act === 'approve' ? 'approve' : 'reject', noteOf(id));
    else if (act === 'refresh') admin.refresh(id);
    else if (act === 'check') admin.linkCheck(id, noteOf(id));
  }));
  draw();
  const off = store.select((s) => [s.lang, s.loading, s.error, s.review, s.sources, s.reports, s.busy, s.message], draw, { equals: (a, b) => a.every((v, i) => v === b[i]) });
  return { destroy() { off(); offs.forEach((f) => f()); root.replaceChildren(); } };
}

export async function boot(root = document.getElementById('app'), search = location.search) {
  const q = new URLSearchParams(search);
  const api = createEventsApi({ mode: 'http', baseUrl: safeBase(q.get('base')) });
  const admin = createAdmin({ api, session: safeStorage('session') });
  if (q.get('lang') === 'en') admin.setLang('en');
  const view = mountAdmin(root, { admin, api });
  // ?base= 로 주소를 바꿨으면 저장된 토큰을 자동으로 보내지 않는다(관리자가 직접 "불러오기"를 누른다)
  if (admin.store.getState().token && !q.get('base')) admin.load();
  return { admin, view, api };
}

if (typeof document !== 'undefined' && document.body?.dataset?.page === 'admin') boot();
