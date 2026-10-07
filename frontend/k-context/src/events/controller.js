// 행사 찾기 화면의 동작(상태 전이). DOM 을 만지지 않는다 — api 와 store, 저장소만 쓴다.
// 서버 계산 결과를 그대로 보여 주고, 이동시간·운영일을 여기서 다시 계산하지 않는다.
import { EventsApiError } from './api.js';
import {
  ackChanges, applyChanges, loadJson, newPlan, nowSeoulIso, oldestSeen, planPayload, saveEvent,
  saveJson, seoulToday, addDays, sortPlans, unsaveEvent, validateForm, validatePlan,
} from './logic.js';
import { DEMO_PLANS } from './demo-data.js';

const KEY = 'kc.events.v1';
// 데모(mock)와 실제(http)의 일정·저장 목록은 섞이지 않게 키를 나눈다.
export const storageKey = (demo) => (demo ? `${KEY}.demo` : KEY);


export function initialState(storage, { today = seoulToday(), demo = false } = {}) {
  const saved = loadJson(storage, storageKey(demo), {});
  return {
    lang: saved.lang === 'en' ? 'en' : 'ko',
    form: { from: today, to: addDays(today, 3), originName: '', lat: '', lng: '', interests: '', maxExtra: '30', duration: '', requireInterest: false, ...(saved.form ?? {}) },
    itinerary: cleanPlans(saved.itinerary),
    saved: cleanSaved(saved.saved),
    result: null, loading: false, error: null, formErrors: {},
    selectedId: null, detail: null, detailLoading: false,
    planError: null, planFormError: false, reportStatus: null, reportError: null, checking: false, coverage: null,
  };
}

/** localStorage 에서 읽은 일정은 믿지 않는다 — 형식이 틀린 항목은 버린다(하나 때문에 검색이 막히지 않게). */
function cleanPlans(v) {
  if (!Array.isArray(v)) return [];
  const ok = v.filter((p) => p && typeof p === 'object' && typeof p.id === 'string' && p.id && p.id.length <= 80
    && validatePlan(p) && (p.lat == null || typeof p.lat === 'number') && (p.lng == null || typeof p.lng === 'number'));
  return sortPlans(ok.slice(0, 60).map((p) => {
    const o = { ...p, title: String(p.title ?? '').slice(0, 120) };
    // 서버가 받는 표시용 키는 허용 값만 남긴다(틀린 값 하나가 모든 검색을 422 로 막지 않게)
    if (!['user', 'catalog', 'demo'].includes(o.source)) delete o.source;
    if (typeof o.entry_id !== 'string' || o.entry_id.length > 40) delete o.entry_id;
    if (typeof o.end_assumed !== 'boolean') delete o.end_assumed;
    return o;
  }));
}
function cleanSaved(v) {
  if (!v || typeof v !== 'object' || Array.isArray(v)) return {};
  return Object.fromEntries(Object.entries(v).filter(([id, it]) => id.length <= 40 && it && typeof it === 'object'
    && typeof it.title === 'string' && typeof it.seenAt === 'string').slice(0, 100));
}

const errKey = (e) => (e instanceof EventsApiError && e.code === 'network' ? 'error.network' : 'error.server');

export function createController({ store, api, storage = null, now = () => new Date() }) {
  const get = store.getState;
  const set = store.setState;
  let searchSeq = 0;
  const persist = () => {
    const s = get();
    saveJson(storage, storageKey(!!api.demo), { lang: s.lang, form: s.form, itinerary: s.itinerary, saved: s.saved });
  };

  const c = {
    setLang(lang) { set({ lang: lang === 'en' ? 'en' : 'ko' }); persist(); },
    setForm(patch) { set((s) => ({ form: { ...s.form, ...patch } })); persist(); },

    async search() {
      const s0 = get();
      const v = validateForm(s0.form, s0.itinerary);
      if (!v.ok) { set({ formErrors: v.errors, error: null }); return null; }
      set({ loading: true, formErrors: {}, error: null });
      const mine = ++searchSeq;
      try {
        const result = await api.search(v.request);
        if (mine !== searchSeq) return null; // 더 나중에 시작한 검색이 있으면 이 응답은 버린다
        set({ result, loading: false, coverage: result.coverage ?? get().coverage });
        const sel = get().selectedId;
        if (sel && !result.events.some((e) => e.id === sel)) set({ selectedId: null, detail: null });
        c.checkSaved();
        return result;
      } catch (e) {
        if (mine === searchSeq) set({ loading: false, error: errKey(e) });
        return null;
      }
    },

    async loadCoverage() {
      try {
        const r = await api.coverage();
        set({ coverage: r.coverage });
      } catch { /* 범위 표시는 없어도 화면이 동작한다 */ }
    },

    async openDetail(id) {
      set({ selectedId: id, detailLoading: true, planError: null });
      try {
        const detail = await api.detail(id, { lang: get().lang, demo: api.demo });
        if (get().selectedId === id) set({ detail, detailLoading: false });
      } catch (e) {
        if (get().selectedId === id) set({ detail: null, detailLoading: false, error: errKey(e) });
      }
    },
    closeDetail() { set({ selectedId: null, detail: null, planError: null }); },

    // ---- 일정 ----
    addUserPlan(p) {
      if (!validatePlan(p)) { set({ planFormError: true }); return false; }
      set((s) => ({ itinerary: sortPlans([...s.itinerary, newPlan(p)]), planFormError: false }));
      persist();
      return true;
    },
    deleteUserPlan(id) {
      set((s) => ({ itinerary: s.itinerary.filter((p) => !(p.id === id && p.source !== 'catalog')) }));
      persist();
    },
    loadSamplePlans() {
      if (!api.demo) return;
      set((s) => ({ itinerary: sortPlans([...s.itinerary.filter((p) => p.source !== 'demo'), ...DEMO_PLANS]) }));
      persist();
    },
    /** 제안 한 건을 일정에 넣는다. 맞지 않는 제안은 서버가 409 로 막고, force 로 다시 보내면 넣는다. */
    async addSession(sug, { force = false } = {}) {
      const s = get();
      const v = validateForm(s.form, s.itinerary);
      const req = v.request ?? {};
      set({ planError: null });
      try {
        const out = await api.addToPlan({
          entry_id: sug.entry_id, date: sug.date, start_time: sug.session.start_time,
          itinerary: planPayload(s.itinerary), max_extra_minutes: req.max_extra_minutes ?? 30,
          ...(req.origin ? { origin: req.origin } : {}), ...(req.assumed_duration_min ? { assumed_duration_min: req.assumed_duration_min } : {}),
          force, demo: !!api.demo,
        });
        set({ itinerary: out.itinerary });
        persist();
        c.search();
        return true;
      } catch (e) {
        set({ planError: { code: e.code ?? 'error', message: e.message ?? '', sug, key: errKey(e) } });
        return false;
      }
    },
    async removeCatalogItem(id) {
      const s = get();
      const item = s.itinerary.find((p) => p.id === id);
      if (!item || item.source !== 'catalog') return false;
      try {
        const out = await api.removeFromPlan({ item_id: id, itinerary: planPayload(s.itinerary) });
        set({ itinerary: out.itinerary });
        persist();
        c.search();
        return true;
      } catch (e) {
        set({ error: errKey(e) });
        return false;
      }
    },

    // ---- 저장한 행사·변경 배지 ----
    toggleSave(ev) {
      const s = get();
      set({ saved: s.saved[ev.id] ? unsaveEvent(s.saved, ev.id) : saveEvent(s.saved, ev, nowSeoulIso(now())) });
      persist();
    },
    async checkSaved() {
      const ids = Object.keys(get().saved);
      if (!ids.length || get().checking) return;
      set({ checking: true });
      try {
        const out = await api.savedChanges(ids, oldestSeen(get().saved));
        set((s) => ({ saved: applyChanges(s.saved, out.saved), checking: false }));
      } catch {
        set({ checking: false }); // 변경 확인 실패는 저장 목록을 지우지 않는다
      }
    },
    ackSaved(id) { set((s) => ({ saved: ackChanges(s.saved, id, nowSeoulIso(now())) })); persist(); },

    // ---- 제보 ----
    async submitReport(f) {
      set({ reportStatus: null, reportError: null });
      const link = String(f.official_link ?? '').trim();
      const reason = String(f.reason ?? '').trim();
      if (!/^https?:\/\/\S+\.\S+/.test(link) || reason.length < 5) { set({ reportError: 'client' }); return false; }
      const fields = {};
      for (const [k, v] of Object.entries(f.fields ?? {})) if (String(v ?? '').trim()) fields[k] = String(v).trim();
      const body = { kind: f.kind || 'other', official_link: link, reason, fields };
      if (f.entry_id) body.entry_id = String(f.entry_id).trim();
      try {
        await api.submitReport(body);
        set({ reportStatus: 'sent' });
        return true;
      } catch (e) {
        set({ reportError: e instanceof EventsApiError && e.code === 'bad_request' ? e.message : errKey(e) });
        return false;
      }
    },
  };
  return c;
}
