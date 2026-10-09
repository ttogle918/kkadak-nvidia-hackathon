// 카카오 렌더러. 입력은 map 모듈의 state(itinerary·routes·cards). 좌표는 계약 3.3 의 [lat, lng].
// 텍스트는 textContent(h() 의 문자열 자식)와 Marker.title(속성) 로만 넣는다 — innerHTML 금지.
// 일정 앵커(itinerary.anchors)의 유효 좌표도 마커가 된다. lat/lng 가 null·비수치·범위 밖인 항목은 건너뛴다. 하나도 없으면 기본 중심만 보이고 '좌표 없음'을 표시한다.
import { h } from '../../lib/dom.js';
import { mockBadge } from '../../lib/mock-badge.js';
import { bundlePins, pinInfo, pinLinks } from '../../lib/chat-bundle.js';
import { pinInfoNode } from '../../lib/chat-bundle-view.js';

// 기본 중심: 덕수궁 37.56556, 126.97489 (인접: 정동제일교회 37.56541, 126.97273).
// 근거: 카카오맵 MCP 응답의 길찾기 링크 안 좌표, 2026-10-07 확인. level 은 카카오맵의 확대 단계(작을수록 확대).
export const DEFAULT_CENTER = { lat: 37.56556, lng: 126.97489 };
export const DEFAULT_LEVEL = 4;

// mock '내 위치': 실제 위치가 아니라 샘플이다(navigator.geolocation 미사용). 기본 중심과 같은 덕수궁 부근 좌표
// (카카오맵 MCP 길찾기 링크 안 좌표, 2026-10-07). 실제 위치로 바꿀 때는 getMyLocation() 만 고친다.
export const MOCK_MY_LOCATION = { lat: 37.56556, lng: 126.97489 };
export const MY_LOCATION_LABEL = { ko: '내 위치 (예시)', en: 'My location (sample)' };
/** 현재는 상수를 반환한다. 반환: {lat,lng}. 좌표가 유효하지 않으면 호출부가 건너뛴다. */
export function getMyLocation() {
  return MOCK_MY_LOCATION;
}

const isNum = (v) => typeof v === 'number' && Number.isFinite(v);
export function validLatLng(p) {
  return Array.isArray(p) && isNum(p[0]) && isNum(p[1]) && Math.abs(p[0]) <= 90 && Math.abs(p[1]) <= 180;
}

const NEAR = 1e-5; // 약 1m. 카드 마커와 앵커 마커가 같은 자리면 하나만 둔다.

/** 순수: 점들 [[lat,lng]] 의 경계 {sw:[lat,lng], ne:[lat,lng]}. 유효한 점이 없으면 null. */
export function computeBounds(points) {
  const pts = (points ?? []).filter(validLatLng);
  if (!pts.length) return null;
  const lats = pts.map((p) => p[0]);
  const lngs = pts.map((p) => p[1]);
  return { sw: [Math.min(...lats), Math.min(...lngs)], ne: [Math.max(...lats), Math.max(...lngs)] };
}

/** state -> {markers:[{lat,lng,title,kind}], lines:[{path:[[lat,lng]], active}]}. 순수 함수. */
export function collectGeo(state, t) {
  const cards = state.data?.cards ?? [];
  const routes = state.data?.routes ?? [];
  const cardOf = (id) => cards.find((c) => c.id === id);
  const markers = [];
  for (const c of cards) {
    const geo = c.geometry?.space !== 'schematic'; // 계약: space 기본은 geo
    const pt = c.place && validLatLng([c.place.lat, c.place.lng]) ? [c.place.lat, c.place.lng]
      : (geo && c.geometry?.coords?.length ? c.geometry.coords.find(validLatLng) : null);
    if (!pt) continue;
    markers.push({ lat: pt[0], lng: pt[1], title: t(c.place?.name ?? c.title ?? ''), kind: c.kind ?? 'poi' });
  }
  // 일정 앵커(실제 장소): 유효 lat/lng 만. hotel 은 항상, visit 은 day 가 있고 선택한 날(state.day)과 다르면 제외.
  for (const a of state.data?.itinerary?.anchors ?? []) {
    if (!validLatLng([a.lat, a.lng])) continue;
    if (a.type !== 'hotel' && a.day != null && state.day != null && a.day !== state.day) continue;
    if (markers.some((m) => Math.abs(m.lat - a.lat) < NEAR && Math.abs(m.lng - a.lng) < NEAR)) continue;
    markers.push({ lat: a.lat, lng: a.lng, title: t(a.name ?? ''), kind: a.type === 'hotel' ? 'hotel' : 'visit' });
  }
  const lines = [];
  const sel = routes.find((r) => r.id === state.selectedRoute) ?? routes[0];
  for (const r of routes) {
    const anyGeo = r.segments.some((s) => cardOf(s.card_id)?.geometry?.space === 'geo');
    for (const s of r.segments) {
      const card = cardOf(s.card_id);
      const isGeo = card ? card.geometry?.space !== 'schematic' : anyGeo;
      if (!isGeo) continue;
      const path = (s.coords ?? []).filter(validLatLng);
      if (path.length >= 2) lines.push({ path, active: r === sel });
    }
  }
  return { markers, lines };
}

/** 카카오 지도 뷰. host 는 영속 컨테이너(재렌더 때 같은 노드를 다시 붙인다). */
export function createKakaoView(kakao, host, t, { myLocation = true } = {}) {
  const maps = kakao.maps;
  const center = () => new maps.LatLng(DEFAULT_CENTER.lat, DEFAULT_CENTER.lng);
  let map = null;
  let overlays = [];
  let info = null;
  const myLabel = () => t(MY_LOCATION_LABEL);
  // 내 위치 레이어: 파란 점 + 반투명 원. CustomOverlay 가 있으면 DOM 노드(텍스트는 textContent), 없으면 title 만 있는 Marker.
  function addMyLocation(pos) {
    const label = myLabel();
    let o;
    if (maps.CustomOverlay) {
      const node = h('div', { class: 'map-kakao__me', title: label }, [
        h('span', { class: 'map-kakao__me-halo' }),
        h('span', { class: 'map-kakao__me-dot' }),
        h('span', { class: 'map-kakao__me-label' }, label),
        mockBadge(t),
      ]);
      o = new maps.CustomOverlay({ position: pos, content: node, xAnchor: 0.5, yAnchor: 0.5, zIndex: 10 });
    } else {
      o = new maps.Marker({ position: pos, title: `${label} · MOCK` });
    }
    o.setMap(map);
    overlays.push(o);
  }
  const status = h('div', { class: 'map-kakao__status', role: 'status' });

  function clear() {
    info?.close?.();
    info = null;
    overlays.forEach((o) => o.setMap(null));
    overlays = [];
  }

  /** 챗봇이 정리한 일정: 좌표가 있는 앵커에만 핀(옛길 선·내 위치 없음). 누르면 정보창(DOM 노드 + textContent). */
  function updateBundle(bundle) {
    const pins = bundlePins(bundle);
    const at = new Map(pins.map((p) => [p.key, p]));
    // 같은 날 이웃 핀의 점선(D16: 직선 연결일 뿐 실제 길이 아니다) — SVG 지도와 같은 pinLinks() 데이터. 모양(점선)과 글자 라벨을 함께 둔다.
    const links = pinLinks(bundle).filter((l) => at.has(l.from) && at.has(l.to));
    for (const l of links) {
      const a = at.get(l.from);
      const b = at.get(l.to);
      const pl = new maps.Polyline({
        path: [new maps.LatLng(a.lat, a.lng), new maps.LatLng(b.lat, b.lng)],
        strokeWeight: 3, strokeColor: '#555555', strokeOpacity: 0.7, strokeStyle: 'shortdot',
      });
      pl.setMap(map);
      overlays.push(pl);
    }
    if (links.length && maps.CustomOverlay) {
      const a = at.get(links[0].from);
      const b = at.get(links[0].to);
      const label = h('div', { class: 'map-kakao__straight', dataset: { straight: 'label' } }, `┈ ${t('map.bundle.straight_note')}`);
      const o = new maps.CustomOverlay({ position: new maps.LatLng((a.lat + b.lat) / 2, (a.lng + b.lng) / 2), content: label, xAnchor: 0.5, yAnchor: 0, zIndex: 5 });
      o.setMap(map);
      overlays.push(o);
    }
    for (const p of pins) {
      const pos = new maps.LatLng(p.lat, p.lng);
      const mk = new maps.Marker({ position: pos, title: p.name });
      mk.setMap(map);
      overlays.push(mk);
      if (maps.event?.addListener && maps.InfoWindow) {
        maps.event.addListener(mk, 'click', () => {
          info?.close?.();
          info = new maps.InfoWindow({ position: pos, content: pinInfoNode(pinInfo(p), t), removable: true });
          info.open(map, mk);
        });
      }
    }
    const bb = computeBounds(pins.map((p) => [p.lat, p.lng]));
    if (!bb) {
      map.setCenter?.(center());
      map.setLevel?.(DEFAULT_LEVEL);
      status.replaceChildren(t('map.bundle.no_pins'));
    } else if (pins.length === 1) {
      map.setCenter?.(new maps.LatLng(pins[0].lat, pins[0].lng));
      map.setLevel?.(DEFAULT_LEVEL);
      status.replaceChildren();
    } else {
      const bounds = new maps.LatLngBounds();
      bounds.extend(new maps.LatLng(bb.sw[0], bb.sw[1]));
      bounds.extend(new maps.LatLng(bb.ne[0], bb.ne[1]));
      map.setBounds?.(bounds);
      status.replaceChildren();
    }
    if (links.length) status.replaceChildren(`┈ ${t('map.bundle.straight_note')}`); // 오버레이를 못 쓰는 환경에서도 글자 라벨이 남는다
  }

  return {
    status,
    update(state) {
      map ??= new maps.Map(host, { center: center(), level: DEFAULT_LEVEL });
      map.relayout?.();
      clear();
      if (state.chatBundle) { updateBundle(state.chatBundle); return; }
      const { markers, lines } = collectGeo(state, t);
      for (const l of lines) {
        const pl = new maps.Polyline({
          path: l.path.map(([la, ln]) => new maps.LatLng(la, ln)),
          strokeWeight: l.active ? 6 : 3, strokeColor: '#3a6ea5', strokeOpacity: l.active ? 0.85 : 0.35,
        });
        pl.setMap(map);
        overlays.push(pl);
      }
      for (const m of markers) {
        const pos = new maps.LatLng(m.lat, m.lng);
        const mk = new maps.Marker({ position: pos, title: m.title }); // title 은 속성(텍스트)
        mk.setMap(map);
        overlays.push(mk);
        if (maps.event?.addListener && maps.InfoWindow) {
          maps.event.addListener(mk, 'click', () => {
            info?.close?.();
            info = new maps.InfoWindow({ position: pos, content: h('div', { class: 'map-kakao__info' }, m.title) }); // DOM 노드 + textContent
            info.open(map, mk);
          });
        }
      }
      const me = myLocation ? getMyLocation() : null; // 실제 모드(myLocation=false)에는 예시 좌표를 그리지 않는다
      const myPt = validLatLng([me?.lat, me?.lng]) ? [me.lat, me.lng] : null;
      if (myPt) addMyLocation(new maps.LatLng(myPt[0], myPt[1]));
      const sched = [...markers.map((m) => [m.lat, m.lng]), ...lines.flatMap((l) => l.path)];
      const all = myPt ? [...sched, myPt] : sched;
      const bb = computeBounds(all);
      if (bb) {
        if (all.length === 1) { // 점 하나면 setBounds 가 과확대되므로 중심만
          map.setCenter?.(new maps.LatLng(all[0][0], all[0][1]));
          map.setLevel?.(DEFAULT_LEVEL);
        } else {
          const bounds = new maps.LatLngBounds();
          bounds.extend(new maps.LatLng(bb.sw[0], bb.sw[1]));
          bounds.extend(new maps.LatLng(bb.ne[0], bb.ne[1]));
          map.setBounds?.(bounds);
        }
        if (sched.length) status.replaceChildren();
        else status.replaceChildren(t({ ko: '일정 좌표 없음 — 내 위치(예시)만 표시합니다', en: 'No itinerary coordinates — showing only the sample location' }));
      } else {
        map.setCenter?.(center());
        map.setLevel?.(DEFAULT_LEVEL);
        status.replaceChildren(t({ ko: '좌표 없음 — 기본 위치(덕수궁 부근)만 표시합니다', en: 'No coordinates — showing the default area (near Deoksugung)' }));
      }
    },
    destroy() { clear(); status.replaceChildren(); },
  };
}
