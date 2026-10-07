// 계약 형식 검증기(AGENT_CONTEXT 3.3). 테스트와 개발 중 점검용 — 문제 목록(string[])을 돌려주고, 던지지 않는다.
// 문자열 필드는 string 또는 {ko,en} 을 모두 허용한다(i18n.js 참고).
import { badgeKind } from '../lib/format.js';

const KINDS = ['story', 'now'];
const GEOMETRY_TYPES = ['point', 'segment', 'area', 'approx'];
const USER_STATES = ['proposed', 'added', 'visited', 'skipped'];
const TIERS = ['S', 'A', 'B', 'C', 'D'];

const isText = (v) => typeof v === 'string' || (v && typeof v === 'object' && typeof v.ko === 'string' && typeof v.en === 'string');
const isCoord = (c) => Array.isArray(c) && c.length === 2 && c.every((n) => typeof n === 'number');

export function validateSource(s, at = 'source') {
  const p = [];
  if (!s || typeof s !== 'object') return [`${at}: 객체가 아님`];
  for (const k of ['id', 'name', 'locator', 'collected_at', 'quote']) if (typeof s[k] !== 'string' || !s[k]) p.push(`${at}.${k}: 문자열 필요`);
  if (!TIERS.includes(s.tier)) p.push(`${at}.tier: ${TIERS.join('/')} 중 하나`);
  // 태그를 만들려면 위치(쪽수·게시일)와 수집일이 반드시 있어야 한다(AGENT_CONTEXT 3.3)
  return p;
}

export function validateCard(c) {
  const at = `card[${c?.id}]`;
  const p = [];
  if (!c || typeof c !== 'object') return [`${at}: 객체가 아님`];
  if (typeof c.id !== 'string' || !c.id) p.push(`${at}.id`);
  if (!KINDS.includes(c.kind)) p.push(`${at}.kind: story|now`);
  if (!isText(c.title)) p.push(`${at}.title`);
  if (!isText(c.body)) p.push(`${at}.body`);
  const g = c.geometry;
  if (!g || !GEOMETRY_TYPES.includes(g.type)) p.push(`${at}.geometry.type: ${GEOMETRY_TYPES.join('|')}`);
  else {
    if (!Array.isArray(g.coords) || g.coords.length === 0 || !g.coords.every(isCoord)) p.push(`${at}.geometry.coords: [[a,b],…]`);
    if (g.type === 'segment' && g.coords?.length < 2) p.push(`${at}.geometry: segment 는 좌표 2개 이상`);
    if (!isText(g.basis)) p.push(`${at}.geometry.basis`);
  }
  const bk = badgeKind(c.badge);
  if (!bk) p.push(`${at}.badge: 알 수 없는 딱지 "${c.badge}"`);
  else if (bk !== c.kind) p.push(`${at}.badge: ${c.kind} 카드에 ${bk} 딱지`);
  if (!Array.isArray(c.sources) || c.sources.length === 0) p.push(`${at}.sources: 비어 있음(출처 없는 카드는 없다)`);
  else c.sources.forEach((s, i) => p.push(...validateSource(s, `${at}.sources[${i}]`)));
  if (!USER_STATES.includes(c.user_state)) p.push(`${at}.user_state`);
  for (const k of ['why_fits', 'caveats', 'rejected']) if (!Array.isArray(c[k])) p.push(`${at}.${k}: 배열`);
  if (c.kind === 'now') {
    if (!c.slot || typeof c.slot.day !== 'number') p.push(`${at}.slot.day: now 카드는 slot 필요`);
    if (typeof c.time_cost_min !== 'number') p.push(`${at}.time_cost_min`);
    if (!c.valid || !c.valid.as_of) p.push(`${at}.valid.as_of`);
  }
  if (c.kind === 'story' && !isText(c.narration)) p.push(`${at}.narration: story 카드는 몰입 층 필요`);
  return p;
}

export function validateRoute(r, cardIds = null) {
  const at = `route[${r?.id}]`;
  const p = [];
  if (!r || typeof r !== 'object') return [`${at}: 객체가 아님`];
  if (typeof r.id !== 'string' || !r.id) p.push(`${at}.id`);
  if (!isText(r.theme)) p.push(`${at}.theme`);
  for (const k of ['walk_min', 'delta_min', 'story_count']) if (typeof r[k] !== 'number') p.push(`${at}.${k}: 숫자`);
  if (!Array.isArray(r.badges)) p.push(`${at}.badges: 배열`);
  if (!Array.isArray(r.segments) || r.segments.length === 0) p.push(`${at}.segments: 비어 있음`);
  else {
    r.segments.forEach((s, i) => {
      const sa = `${at}.segments[${i}]`;
      if (!isText(s.name)) p.push(`${sa}.name`);
      if (s.card_id !== null && typeof s.card_id !== 'string') p.push(`${sa}.card_id: string|null`);
      if (cardIds && s.card_id && !cardIds.includes(s.card_id)) p.push(`${sa}.card_id: 없는 카드 ${s.card_id}`);
      if (typeof s.weak !== 'boolean') p.push(`${sa}.weak: boolean`);
    });
    const withCard = r.segments.filter((s) => s.card_id).length;
    if (typeof r.story_count === 'number' && withCard !== r.story_count) p.push(`${at}.story_count(${r.story_count}) != 카드 있는 구간 수(${withCard})`);
  }
  return p;
}
