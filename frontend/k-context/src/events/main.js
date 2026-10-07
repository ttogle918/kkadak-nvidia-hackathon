// 행사 찾기 부트. URL: ?api=http|mock · ?base=<backend 주소> · ?lang=en
import { createStore } from '../lib/store.js';
import { createEventsApi } from './api.js';
import { createController, initialState } from './controller.js';
import { safeStorage } from './logic.js';
import { mountEvents } from './view.js';

export async function boot(root = document.getElementById('app'), search = location.search) {
  const q = new URLSearchParams(search);
  const storage = safeStorage('local');
  const api = createEventsApi({ mode: q.get('api') === 'mock' ? 'mock' : 'http', baseUrl: q.get('base') || undefined });
  const store = createStore(initialState(storage));
  if (q.get('lang') === 'en' || q.get('lang') === 'ko') store.setState({ lang: q.get('lang') });
  const controller = createController({ store, api, storage });
  const view = mountEvents(root, { store, api, controller });
  document.documentElement.lang = store.getState().lang;
  store.select((s) => s.lang, (lang) => { document.documentElement.lang = lang; });
  await controller.loadCoverage();
  controller.checkSaved();
  return { store, controller, view };
}

if (typeof document !== 'undefined') boot();
