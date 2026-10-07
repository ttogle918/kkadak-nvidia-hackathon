// 카카오 렌더러. 입력은 map 모듈의 state(itinerary·routes·cards). 좌표는 계약 3.3 의 [lat, lng].
// 텍스트는 textContent(h() 의 문자열 자식)와 Marker.title(속성) 로만 넣는다 — innerHTML 금지.
// lat/lng 가 null·비수치·범위 밖인 항목은 건너뛴다. 하나도 없으면 기본 중심만 보이고 '좌표 없음'을 표시한다.
import { h } from '../../lib/dom.js';

// 기본 중심: 덕수궁 37.56556, 126.97489 (인접: 정동제일교회 37.56541, 126.97273).
// 근거: 카카오맵 MCP 응답의 길찾기 링크 안 좌표, 2026-10-07 확인. level 은 카카오맵의 확대 단계(작을수록 확대).
export const DEFAULT_CENTER = { lat: 37.56556, lng: 126.97489 };
export const DEFAULT_LEVEL = 4;

const isNum = (v) => typeof v === 'number' && Number.isFinite(v);
export function validLatLng(p) {
  return Array.isArray(p) && isNum(p[0]) && isNum(p[1]) && Math.abs(p[0]) <= 90 && Math.abs(p[1]) <= 180;
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
export function createKakaoView(kakao, host, t) {
  const maps = kakao.maps;
  const center = () => new maps.LatLng(DEFAULT_CENTER.lat, DEFAULT_CENTER.lng);
  let map = null;
  let overlays = [];
  let info = null;
  const status = h('div', { class: 'map-kakao__status', role: 'status' });

  function clear() {
    info?.close?.();
    info = null;
    overlays.forEach((o) => o.setMap(null));
    overlays = [];
  }

  return {
    status,
    update(state) {
      map ??= new maps.Map(host, { center: center(), level: DEFAULT_LEVEL });
      map.relayout?.();
      clear();
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
      if (markers.length || lines.length) {
        const bounds = new maps.LatLngBounds();
        markers.forEach((m) => bounds.extend(new maps.LatLng(m.lat, m.lng)));
        lines.forEach((l) => l.path.forEach(([la, ln]) => bounds.extend(new maps.LatLng(la, ln))));
        map.setBounds?.(bounds);
        status.replaceChildren();
      } else {
        map.setCenter?.(center());
        map.setLevel?.(DEFAULT_LEVEL);
        status.replaceChildren(t({ ko: '좌표 없음 — 기본 위치(덕수궁 부근)만 표시합니다', en: 'No coordinates — showing the default area (near Deoksugung)' }));
      }
    },
    destroy() { clear(); status.replaceChildren(); },
  };
}
