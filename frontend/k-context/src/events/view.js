// 행사 찾기 화면 그리기. 사용자·API 문자열은 모두 h() 의 텍스트 노드로만 넣는다(innerHTML 금지).
// 폼은 한 번만 만들고(입력 포커스 유지), 나머지 영역은 상태가 바뀔 때 다시 그린다.
import { h, on, render } from '../lib/dom.js';
import { makeT } from './i18n.js';
import {
  closuresText, describeChange, eventWhen, languageInfo, mapPoints, needsCheckLabels, participationBadges,
  priceLabel, projectPoints, reservationInfo, safeHref, sortPlans, suggestionLabels, verificationBadge,
} from './logic.js';

const badge = (text, tone = 'warn', extra = '') => h('span', { class: ['ev-badge', `is-${tone}`, extra] }, text);
const row = (label, ...children) => h('div', { class: 'ev-row' }, h('dt', null, label), h('dd', null, ...children));
const link = (url, text) => {
  const href = safeHref(url);
  return href ? h('a', { href, target: '_blank', rel: 'noopener noreferrer' }, text || href) : h('span', null, text || '');
};

export function mountEvents(root, ctx) {
  const { store, api, controller: c } = ctx;
  const T = () => makeT(store.getState().lang);
  const form = {};

  // ---- 폼(한 번만 만든다) ----
  const field = (name, labelKey, attrs = {}) => {
    const input = h('input', { id: `f-${name}`, name, ...attrs });
    form[name] = input;
    return h('label', { class: 'ev-field', for: `f-${name}` }, h('span', { dataset: { i18n: labelKey } }), input);
  };
  const errBox = h('p', { class: 'ev-error', role: 'alert' });
  const submit = h('button', { type: 'submit', class: 'ev-btn is-primary' });
  form.requireInterest = h('input', { id: 'f-require', type: 'checkbox', name: 'requireInterest' });
  const formEl = h('form', { class: 'ev-form', novalidate: true },
    h('h2', { dataset: { i18n: 'form.title' } }),
    h('div', { class: 'ev-grid2' },
      field('from', 'form.from', { type: 'date', required: true }), field('to', 'form.to', { type: 'date', required: true })),
    field('originName', 'form.origin', { type: 'text', maxlength: '80' }),
    h('div', { class: 'ev-grid2' }, field('lat', 'form.lat', { type: 'text', inputmode: 'decimal' }), field('lng', 'form.lng', { type: 'text', inputmode: 'decimal' })),
    field('interests', 'form.interests', { type: 'text' }),
    h('div', { class: 'ev-grid2' },
      field('maxExtra', 'form.max_extra', { type: 'number', min: '0', max: '240', step: '1' }),
      field('duration', 'form.duration', { type: 'number', min: '1', max: '720', step: '1' })),
    h('label', { class: 'ev-check', for: 'f-require' }, form.requireInterest, h('span', { dataset: { i18n: 'form.require_interest' } })),
    errBox, submit);

  const head = h('header', { class: 'ev-head' });
  const banner = h('div', { class: 'ev-demo', role: 'status' });
  const resultsEl = h('section', { class: 'ev-results', 'aria-labelledby': 'ev-results-title' });
  const detailEl = h('section', { class: 'ev-detail', 'aria-labelledby': 'ev-detail-title' });
  const mapEl = h('section', { class: 'ev-map' });
  const planEl = h('section', { class: 'ev-plan' });
  const savedEl = h('section', { class: 'ev-saved' });
  const reportEl = h('section', { class: 'ev-report' });
  const coverageEl = h('footer', { class: 'ev-coverage' });

  // 일정 입력 폼과 제보 폼도 한 번만 만든다.
  const planForm = {};
  const planErr = h('p', { class: 'ev-error', role: 'alert' });
  const planFormEl = h('form', { class: 'ev-planform', novalidate: true },
    ...[['title', 'plan.add.title', 'text'], ['date', 'plan.add.date', 'date'], ['start', 'plan.add.start', 'time'], ['end', 'plan.add.end', 'time']]
      .map(([n, k, type]) => h('label', { class: 'ev-field', for: `p-${n}` }, h('span', { dataset: { i18n: k } }), (planForm[n] = h('input', { id: `p-${n}`, name: n, type })))),
    h('div', { class: 'ev-grid2' }, ...[['lat', 'form.lat'], ['lng', 'form.lng']].map(([n, k]) => h('label', { class: 'ev-field', for: `p-${n}` }, h('span', { dataset: { i18n: k } }), (planForm[n] = h('input', { id: `p-${n}`, name: n, type: 'text', inputmode: 'decimal' }))))),
    planErr, h('button', { type: 'submit', class: 'ev-btn', dataset: { i18n: 'plan.add.submit' } }));

  const rep = {};
  const repMsg = h('p', { class: 'ev-status', role: 'status' });
  const repKind = h('select', { id: 'r-kind', name: 'kind' }, ...['new_event', 'correction', 'cancel_notice', 'other'].map((k) => h('option', { value: k, dataset: { i18n: `report.kind.${k}` } })));
  rep.kind = repKind;
  const repField = (n, k, attrs = {}) => h('label', { class: 'ev-field', for: `r-${n}` }, h('span', { dataset: { i18n: k } }), (rep[n] = h(attrs.tag || 'input', { id: `r-${n}`, name: n, ...attrs.a })));
  const reportForm = h('form', { class: 'ev-reportform', novalidate: true },
    h('label', { class: 'ev-field', for: 'r-kind' }, h('span', { dataset: { i18n: 'report.kind' } }), repKind),
    repField('official_link', 'report.link', { a: { type: 'url', maxlength: '500' } }),
    repField('reason', 'report.reason', { tag: 'textarea', a: { rows: '3', maxlength: '1000' } }),
    repField('title', 'report.event_title', { a: { type: 'text', maxlength: '200' } }),
    repField('start_date', 'report.date', { a: { type: 'text', maxlength: '10' } }),
    repField('venue_address', 'report.venue', { a: { type: 'text', maxlength: '200' } }),
    repField('entry_id', 'report.entry', { a: { type: 'text', maxlength: '40' } }),
    h('button', { type: 'submit', class: 'ev-btn', dataset: { i18n: 'report.submit' } }), repMsg);

  render(root,
    head, banner,
    h('div', { class: 'ev-layout' },
      h('div', { class: 'ev-col' }, formEl, resultsEl),
      h('div', { class: 'ev-col' }, detailEl, mapEl),
      h('div', { class: 'ev-col' }, planEl, savedEl, reportEl)),
    coverageEl);

  // 정적 문구(data-i18n)를 현재 언어로 채운다. 입력 값은 건드리지 않는다.
  function drawStatic() {
    const t = T();
    for (const el of root.querySelectorAll?.('[data-i18n]') ?? []) render(el, t(el.dataset.i18n));
    render(submit, store.getState().loading ? t('form.loading') : t('form.submit'));
    submit.disabled = store.getState().loading;
    for (const [n, k] of [['originName', 'form.origin.hint'], ['interests', 'form.interests.hint']]) form[n].setAttribute('placeholder', t(k));
  }

  function drawHead() {
    const s = store.getState();
    const t = T();
    render(head, h('div', null, h('h1', null, t('app.title')), h('p', { class: 'ev-sub' }, t('app.subtitle'))),
      h('div', { class: 'seg', role: 'group', 'aria-label': 'language' }, ...['ko', 'en'].map((l) => h('button', { type: 'button', class: ['seg__btn', s.lang === l && 'is-on'], dataset: { act: 'lang', value: l }, 'aria-pressed': String(s.lang === l) }, t(`lang.${l}`)))));
    render(banner, api.demo ? t('demo.banner') : null);
    banner.hidden = !api.demo;
  }

  function eventCard(ev, s, t) {
    const sel = s.selectedId === ev.id;
    const w = eventWhen(ev, t);
    const pb = participationBadges(ev, t);
    const vb = verificationBadge(ev, t);
    const checks = needsCheckLabels(ev, t);
    const pr = priceLabel(ev, t);
    return h('li', { class: ['ev-card', sel && 'is-selected'], dataset: { id: ev.id } },
      h('h3', null, ev.demo ? badge(t('common.demo'), 'warn') : null, ' ', ev.title),
      h('div', { class: 'ev-badges' },
        badge(t(`avail.${ev.availability}`), ev.availability === 'session_match' ? 'ok' : 'warn'), badge(vb.text, vb.tone), ...pb.map((b) => badge(b.text, b.tone))),
      h('p', { class: 'ev-meta' }, `${w.range}${w.sessions ? ` · ${w.sessions}` : ''}`),
      h('p', { class: 'ev-meta' }, ev.venue.name || t('common.unknown'), ' · ', pr.kind),
      ev.participation.status === 'restricted' ? h('p', { class: 'ev-restrict' }, ev.participation.reasons.join(' · ')) : null,
      checks.length ? h('p', { class: 'ev-check-list' }, `${t('detail.needs_check')}: ${checks.join(', ')}`) : null,
      h('p', { class: 'ev-verified' }, `${t('detail.verified')}: ${ev.last_verified_at ?? t('common.unknown')}`),
      h('div', { class: 'ev-actions' },
        h('button', { type: 'button', class: 'ev-btn', dataset: { act: 'detail', id: ev.id } }, t('actions.details')),
        h('button', { type: 'button', class: ['ev-btn', s.saved[ev.id] && 'is-on'], dataset: { act: 'save', id: ev.id }, 'aria-pressed': String(!!s.saved[ev.id]) }, s.saved[ev.id] ? t('actions.saved') : t('actions.save'))));
  }

  function drawResults() {
    const s = store.getState();
    const t = T();
    const r = s.result;
    const nodes = [h('h2', { id: 'ev-results-title' }, t('results.title'), r ? ` ${t('results.count', { n: r.events.length })}` : '')];
    if (s.error) nodes.push(h('p', { class: 'ev-error', role: 'alert' }, t(s.error)));
    if (r) {
      if (r.problems?.length) nodes.push(h('p', { class: 'ev-error' }, r.problems.join(' · ')));
      if (r.events.length) nodes.push(h('ul', { class: 'ev-list' }, ...r.events.map((ev) => eventCard(ev, s, t))));
      else nodes.push(h('p', { class: 'ev-empty' }, r.catalog_empty ? t('results.catalog_empty') : t('results.empty')));
      if (r.excluded?.length) {
        nodes.push(h('details', { class: 'ev-excluded' }, h('summary', null, t('results.excluded', { n: r.excluded.length })),
          h('ul', null, ...r.excluded.map((x) => h('li', null, `${x.title} — ${x.reason}`)))));
      }
    }
    render(resultsEl, ...nodes);
  }

  function suggestionBlock(s, t) {
    const sugs = (s.result?.suggestions ?? []).filter((x) => x.entry_id === s.selectedId);
    if (!Array.isArray(s.result?.suggestions)) return null;
    if (!sugs.length) return h('p', { class: 'ev-empty' }, t('sug.empty'));
    return h('div', { class: 'ev-sugs' }, h('h3', null, t('sug.title')), h('ul', null, ...sugs.map((x) => {
      const L = suggestionLabels(x, t);
      const key = `${x.date}|${x.session.start_time}`;
      const pe = s.planError && s.planError.sug.date === x.date && s.planError.sug.session.start_time === x.session.start_time ? s.planError : null;
      const done = s.itinerary.some((p) => p.source === 'catalog' && p.entry_id === x.entry_id && p.date === x.date && p.start === x.session.start_time);
      return h('li', { class: 'ev-sug', dataset: { key } },
        h('p', null, h('strong', null, `${x.date} ${x.session.start_time}${x.session.end_time ? `–${x.session.end_time}` : ''}`), ' ', badge(L.status, L.tone)),
        h('p', { class: 'ev-meta' }, x.after_item_id ? t('sug.after', { title: s.itinerary.find((p) => p.id === x.after_item_id)?.title ?? x.after_item_id }) : L.after),
        h('p', { class: 'ev-meta' }, `${L.extra}${L.estimated} · ${L.basis}`),
        h('p', { class: 'ev-meta' }, L.provider),
        x.reasons.length ? h('ul', { class: 'ev-reasons', 'aria-label': t('sug.reasons') }, ...x.reasons.map((r) => h('li', null, s.lang === 'en' ? r.en : r.ko))) : null,
        pe ? h('p', { class: 'ev-error', role: 'alert' }, pe.code === 'conflict' ? pe.message : t(pe.key)) : null,
        h('div', { class: 'ev-actions' },
          done ? h('button', { type: 'button', class: 'ev-btn', dataset: { act: 'plan-rm-sug', date: x.date, start: x.session.start_time, id: x.entry_id } }, t('actions.cancel'))
            : h('button', { type: 'button', class: 'ev-btn is-primary', dataset: { act: 'add-session', key } }, t('actions.add')),
          pe?.code === 'conflict' ? h('button', { type: 'button', class: 'ev-btn', dataset: { act: 'add-session-force', key } }, t('actions.add_anyway')) : null));
    })));
  }

  function drawDetail() {
    const s = store.getState();
    const t = T();
    const d = s.detail;
    if (!s.selectedId) { render(detailEl, h('h2', { id: 'ev-detail-title' }, t('detail.title')), h('p', { class: 'ev-empty' }, '—')); return; }
    if (!d) { render(detailEl, h('h2', { id: 'ev-detail-title' }, t('detail.title')), h('p', null, s.detailLoading ? '…' : t('error.server'))); return; }
    const w = eventWhen(d, t);
    const res = reservationInfo(d, t);
    const pr = priceLabel(d, t);
    const li = languageInfo(d, t);
    const clos = closuresText(d, t);
    const vb = verificationBadge(d, t);
    const checks = needsCheckLabels(d, t);
    const nodes = [
      h('div', { class: 'ev-detail-head' }, h('h2', { id: 'ev-detail-title' }, d.title), h('button', { type: 'button', class: 'ev-btn', dataset: { act: 'close' } }, t('detail.close'))),
      d.demo ? badge(t('common.demo'), 'warn') : null,
      h('div', { class: 'ev-badges' }, badge(vb.text, vb.tone), badge(t(`life.${d.lifecycle}`), d.lifecycle === 'cancelled' ? 'bad' : 'warn')),
      h('dl', { class: 'ev-dl' },
        row(t('detail.when'), w.range, w.sessions ? h('div', null, w.sessions) : null, d.schedule.hours_text ? h('div', null, `${t('detail.hours')}: ${d.schedule.hours_text}`) : null,
          clos ? h('div', null, `${t('detail.closures')}: ${clos}`) : null, d.schedule.entry_cutoff ? h('div', null, `${t('detail.cutoff')}: ${d.schedule.entry_cutoff}`) : null,
          !d.schedule.sessions.length ? h('div', { class: 'ev-unknown' }, t('avail.date_range_unconfirmed')) : null),
        row(t('detail.where'), d.venue.name || t('common.unknown'), d.venue.address ? h('div', null, d.venue.address) : null),
        row(t('detail.price'), pr.kind, pr.text ? h('div', null, pr.text) : null),
        row(t('detail.reservation'), badge(res.required, res.tone), ' ', res.status, res.deadline ? h('div', null, `${t('detail.deadline')}: ${res.deadline}`) : null,
          res.link ? h('div', null, link(res.link, t('detail.link'))) : null, res.note ? h('div', { class: 'ev-meta' }, res.note) : null),
        row(t('detail.eligibility'), ...participationBadges(d, t).map((b) => badge(b.text, b.tone)), d.eligibility.audience ? h('div', null, d.eligibility.audience) : null,
          ...d.participation.reasons.map((r) => h('div', { class: 'ev-meta' }, r))),
        row(t('detail.language'), li.event, h('div', null, li.guidance), h('div', null, li.subtitles), li.site ? h('div', { class: 'ev-meta' }, li.site) : null),
        row(t('detail.verified'), d.last_verified_at ?? t('common.unknown'), d.independent_sources ? ` · ${d.independent_sources}` : '')),
      checks.length ? h('p', { class: 'ev-check-list' }, `${t('detail.needs_check')}: ${checks.join(', ')}`) : null,
      d.conflicts?.length ? h('div', { class: 'ev-conflicts' }, h('h3', null, t('detail.conflicts')), h('ul', null, ...d.conflicts.map((cf) => h('li', null, `${t(`field.${cf.field}`).startsWith('field.') ? cf.field : t(`field.${cf.field}`)}: ${cf.values.map((v) => v.value).join(' / ')}${cf.resolved ? '' : ` — ${t('common.unknown')}`}`)))) : null,
      h('div', { class: 'ev-sources' }, h('h3', null, t('detail.sources')), h('ul', null, ...d.links.map((l) => h('li', null,
        h('span', { class: 'ev-src-kind' }, `[${l.kind}] ${l.source_name}`), ' ', link(l.url, t('detail.original')), l.ai_extracted ? ` (${t('detail.ai')})` : '',
        l.quote ? h('blockquote', null, l.quote) : null, l.location ? h('div', { class: 'ev-meta' }, l.location) : null)))),
      suggestionBlock(s, t),
      d.stories?.length ? h('div', { class: 'ev-stories' }, h('h3', null, t('detail.stories')), ...d.stories.map((st) => h('article', null, h('h4', null, st.title),
        ...['facts', 'lore', 'inference'].flatMap((k) => st[k].map((cl) => h('p', null, badge(t(`story.${k === 'facts' ? 'fact' : k}`), k === 'facts' ? 'ok' : 'warn'), ' ', cl.text, ' ', ...cl.sources.map((sr) => h('span', { class: 'ev-meta' }, `[${sr.tier}] ${sr.name} · ${sr.locator} `))))),
        h('p', { class: 'ev-suggest' }, badge(t('story.suggestion'), 'warn'), ' ', st.experience.text, ' ', st.record_prompt.text)))) : null,
      h('div', { class: 'ev-history' }, h('h3', null, t('detail.history')),
        d.history?.filter((x) => x.field !== '__new__').length ? h('ul', null, ...d.history.filter((x) => x.field !== '__new__').map((x) => h('li', null, `${x.detected_at} · ${describeChange(x, t)}`))) : h('p', { class: 'ev-empty' }, t('detail.none'))),
    ];
    render(detailEl, ...nodes);
  }

  function drawMap() {
    const s = store.getState();
    const t = T();
    const pts = projectPoints(mapPoints(s.result, s.itinerary, s.form));
    const un = s.result?.map?.unlocated?.length ?? 0;
    const shape = (p) => {
      const sel = s.selectedId === p.id;
      if (p.kind === 'origin') return h('g', { class: 'ev-pt is-origin' }, h('rect', { x: p.x - 7, y: p.y - 7, width: 14, height: 14 }), h('title', null, `${t('map.origin')} ${p.title}`));
      if (p.kind === 'plan') return h('g', { class: 'ev-pt is-plan' }, h('path', { d: `M${p.x} ${p.y - 8} L${p.x + 8} ${p.y} L${p.x} ${p.y + 8} L${p.x - 8} ${p.y} Z` }), h('title', null, `${t('map.plan')}: ${p.title}`));
      return h('g', { class: ['ev-pt', 'is-event', sel && 'is-selected'], dataset: { act: 'detail', id: p.id }, tabindex: '0', role: 'button', 'aria-label': p.title },
        h('circle', { cx: p.x, cy: p.y, r: 9 }), h('text', { x: p.x, y: p.y + 4, 'text-anchor': 'middle' }, String(p.n)), h('title', null, p.title));
    };
    render(mapEl, h('h2', null, t('map.title')),
      pts.length ? h('svg', { viewBox: '0 0 360 240', class: 'ev-svg', role: 'img', 'aria-label': t('map.title') }, h('rect', { x: 0, y: 0, width: 360, height: 240, class: 'ev-svg-bg' }), ...pts.map(shape)) : h('p', { class: 'ev-empty' }, '—'),
      h('ul', { class: 'ev-legend' }, h('li', null, `● ${t('map.event')}`), h('li', null, `◆ ${t('map.plan')}`), h('li', null, `■ ${t('map.origin')}`)),
      un ? h('p', { class: 'ev-meta' }, t('map.unlocated', { n: un })) : null,
      h('p', { class: 'ev-meta' }, t('map.note')));
  }

  function drawPlan() {
    const s = store.getState();
    const t = T();
    const items = sortPlans(s.itinerary);
    render(planEl, h('h2', null, t('plan.title')),
      items.length ? h('ul', { class: 'ev-plans' }, ...items.map((p) => h('li', { class: ['ev-plan-item', p.source === 'catalog' && 'is-event'], dataset: { id: p.id } },
        h('span', null, `${p.date} ${p.start}–${p.end}${p.end_assumed ? ` (${t('plan.end_assumed')})` : ''} · ${p.title}`, p.source === 'catalog' ? ` [${t('plan.added_event')}]` : ''),
        p.source === 'catalog' ? h('button', { type: 'button', class: 'ev-btn', dataset: { act: 'plan-rm', id: p.id } }, t('actions.cancel'))
          : h('button', { type: 'button', class: 'ev-btn', dataset: { act: 'plan-del', id: p.id } }, t('plan.remove')))))
        : h('p', { class: 'ev-empty' }, t('plan.empty')),
      api.demo ? h('button', { type: 'button', class: 'ev-btn', dataset: { act: 'sample' } }, t('plan.sample')) : null,
      planFormEl);
    render(planErr, s.planFormError ? t('plan.add.error') : '');
  }

  function drawSaved() {
    const s = store.getState();
    const t = T();
    const items = Object.values(s.saved);
    render(savedEl, h('h2', null, t('saved.title')),
      items.length ? h('ul', { class: 'ev-savedlist' }, ...items.map((it) => h('li', { class: 'ev-saved-item', dataset: { id: it.id } },
        h('p', null, h('button', { type: 'button', class: 'ev-link', dataset: { act: 'detail', id: it.id } }, it.title), ' ', it.changes?.length ? badge(t('saved.changed'), it.hasMajor ? 'bad' : 'warn', 'is-changed') : null),
        it.changes?.length ? h('ul', { class: 'ev-changes' }, ...it.changes.map((x) => h('li', null, describeChange(x, t)))) : null,
        it.changes?.length ? h('button', { type: 'button', class: 'ev-btn', dataset: { act: 'ack', id: it.id } }, t('saved.ack')) : null)))
        : h('p', { class: 'ev-empty' }, t('saved.empty')),
      items.length ? h('button', { type: 'button', class: 'ev-btn', dataset: { act: 'check-saved' } }, t('saved.check')) : null);
  }

  function drawReport() {
    const s = store.getState();
    const t = T();
    reportEl.replaceChildren(h('h2', null, t('report.title')), h('p', { class: 'ev-meta' }, t('report.note')), reportForm);
    render(repMsg, s.reportStatus === 'sent' ? t('report.sent') : s.reportError ? (s.reportError === 'client' ? `${t('report.link')} / ${t('report.reason')}` : String(s.reportError).startsWith('error.') ? t(s.reportError) : s.reportError) : '');
  }

  function drawCoverage() {
    const s = store.getState();
    const t = T();
    const cov = s.result?.coverage ?? s.coverage;
    render(coverageEl, h('h2', null, t('coverage.title')), h('p', null, t('coverage.note')),
      cov ? h('ul', { class: 'ev-sources-list' }, ...(cov.sources ?? []).map((x) => h('li', null,
        x.url ? link(x.url, x.name) : x.name, ` — ${t('coverage.last')}: ${x.last_success_at ?? t('coverage.never')}`, x.last_error ? ` · ${t('coverage.error')}: ${x.last_error}` : ''))) : null,
      cov?.entries_built_at ? h('p', { class: 'ev-meta' }, `${t('coverage.built')}: ${cov.entries_built_at}`) : null);
  }

  const drawAll = () => { drawHead(); drawStatic(); drawResults(); drawDetail(); drawMap(); drawPlan(); drawSaved(); drawReport(); drawCoverage(); drawFormErrors(); };
  function drawFormErrors() {
    const s = store.getState();
    const t = T();
    render(errBox, Object.values(s.formErrors).map((k) => t(k)).join(' '));
  }
  const syncForm = () => {
    const f = store.getState().form;
    for (const k of ['from', 'to', 'originName', 'lat', 'lng', 'interests', 'maxExtra', 'duration']) if (form[k].value !== String(f[k] ?? '')) form[k].value = String(f[k] ?? '');
    form.requireInterest.checked = !!f.requireInterest;
  };

  // ---- 이벤트 ----
  const offs = [];
  const sugFor = (key) => (store.getState().result?.suggestions ?? []).find((x) => x.entry_id === store.getState().selectedId && `${x.date}|${x.session.start_time}` === key);
  offs.push(on(root, 'click', '[data-act]', (_e, el) => {
    const { act, id, value, key } = el.dataset;
    const s = store.getState();
    if (act === 'lang') c.setLang(value);
    else if (act === 'detail') c.openDetail(id);
    else if (act === 'close') c.closeDetail();
    else if (act === 'save') { const ev = s.result?.events.find((e) => e.id === id) ?? (s.detail?.id === id ? s.detail : null); if (ev) c.toggleSave(ev); }
    else if (act === 'add-session' || act === 'add-session-force') { const sg = sugFor(key); if (sg) c.addSession(sg, { force: act === 'add-session-force' }); }
    else if (act === 'plan-rm' || act === 'plan-rm-sug') {
      const item = act === 'plan-rm' ? s.itinerary.find((p) => p.id === id) : s.itinerary.find((p) => p.source === 'catalog' && p.entry_id === id && p.date === el.dataset.date && p.start === el.dataset.start);
      if (item) c.removeCatalogItem(item.id);
    } else if (act === 'plan-del') c.deleteUserPlan(id);
    else if (act === 'sample') c.loadSamplePlans();
    else if (act === 'ack') c.ackSaved(id);
    else if (act === 'check-saved') c.checkSaved();
  }));
  const bindInput = (name) => {
    const el = form[name];
    const fn = () => c.setForm({ [name]: el.type === 'checkbox' ? !!el.checked : el.value });
    el.addEventListener('input', fn);
    el.addEventListener('change', fn);
    offs.push(() => { el.removeEventListener('input', fn); el.removeEventListener('change', fn); });
  };
  ['from', 'to', 'originName', 'lat', 'lng', 'interests', 'maxExtra', 'duration', 'requireInterest'].forEach(bindInput);
  const onSubmit = (e) => { e.preventDefault?.(); c.search(); };
  formEl.addEventListener('submit', onSubmit);
  const onPlan = (e) => {
    e.preventDefault?.();
    const p = Object.fromEntries(Object.entries(planForm).map(([k, el]) => [k, el.value]));
    if (c.addUserPlan(p)) for (const el of Object.values(planForm)) el.value = '';
  };
  planFormEl.addEventListener('submit', onPlan);
  const onReport = (e) => {
    e.preventDefault?.();
    c.submitReport({ kind: rep.kind.value, official_link: rep.official_link.value, reason: rep.reason.value, entry_id: rep.entry_id.value,
      fields: { title: rep.title.value, start_date: rep.start_date.value, venue_address: rep.venue_address.value } });
  };
  reportForm.addEventListener('submit', onReport);

  syncForm();
  drawAll();
  const keys = ['lang', 'result', 'loading', 'error', 'formErrors', 'selectedId', 'detail', 'detailLoading', 'itinerary', 'saved', 'planError', 'planFormError', 'reportStatus', 'reportError', 'coverage'];
  const off = store.select((s) => keys.map((k) => s[k]), () => drawAll(), { equals: (a, b) => a.every((v, i) => v === b[i]) });
  return {
    destroy() {
      off();
      offs.forEach((f) => f());
      formEl.removeEventListener('submit', onSubmit);
      planFormEl.removeEventListener('submit', onPlan);
      reportForm.removeEventListener('submit', onReport);
      root.replaceChildren();
    },
  };
}
