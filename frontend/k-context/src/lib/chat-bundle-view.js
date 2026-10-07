// 챗봇 묶음의 공용 DOM 조각. 외부 문자열은 전부 h() 의 자식(텍스트 노드)·속성으로만 들어간다 — innerHTML 금지.
// 링크는 http/https 만(safeUrl), 새 탭 + rel=noopener noreferrer.
import { h } from './dom.js';
import { safeUrl } from '../api/bundle.js';

/** 외부 링크. url 이 http/https 가 아니면 링크 없이 null. */
export function externalLink(url, text, cls = 'cb-link') {
  const href = safeUrl(url);
  return href ? h('a', { class: cls, href, target: '_blank', rel: 'noopener noreferrer' }, text) : null;
}

/** 아주 작은 출처 태그 한 줄: [등급] 이름. 등급을 모르면 '?'. */
export function sourceTagNode(tier, name, extraClass) {
  return h('span', { class: ['src-tag', 'cb-srctag', extraClass], 'data-grade': tier ?? 'unknown' }, `[${tier ?? '?'}] ${name ?? ''}`.trim());
}

/** 실록 언급 1건(간이 카드 본문). 한글 요약(원문 아님)과 한문 원문(국역 없음)을 구분해 보인다. */
export function mentionNode(m, t) {
  return h('li', { class: 'cb-mention', dataset: { article: m.article_id ?? '' } },
    h('div', { class: 'cb-mention__when' }, [m.king, m.date_label].filter(Boolean).join(' · ') || t('bundle.unknown_date')),
    m.title_summary ? h('p', { class: 'cb-mention__summary' }, h('span', { class: 'cb-note' }, t('bundle.summary_label')), ' ', m.title_summary) : null,
    m.quote ? h('p', { class: 'cb-mention__quote', lang: 'lzh' }, h('span', { class: 'cb-note' }, t('bundle.quote_label')), ' ', m.quote) : null,
    h('div', { class: 'cb-mention__foot' },
      sourceTagNode(m.tier, m.source_name),
      externalLink(m.url, t('bundle.open_sillok'))));
}

/** 앵커별 "실록에 이런 기록이 있어요" 간이 카드. */
export function mentionGroupNode(g, t) {
  return h('article', { class: 'cb-card', dataset: { kind: 'mention', anchor: g.name } },
    h('h3', { class: 'cb-card__title' }, g.name),
    h('div', { class: 'cb-card__sub' }, t('bundle.cards.record_count', { n: g.count }), g.atLeast ? ` ${t('bundle.at_least')}` : ''),
    h('ul', { class: 'cb-list' }, g.mentions.map((m) => mentionNode(m, t))));
}

/** 행사 간이 카드: 제목·기간·장소·공식 링크·출처 태그, tier C/미확인이면 "검색 수집 · 미확인" 딱지. */
export function eventNode(ev, t) {
  const link = ev.links.find((l) => l.url) ?? null;
  const src = ev.links.find((l) => l.source_name) ?? null;
  const period = ev.start_date && ev.end_date && ev.start_date !== ev.end_date ? `${ev.start_date} ~ ${ev.end_date}` : (ev.start_date ?? ev.end_date ?? t('bundle.unknown_date'));
  return h('li', { class: 'cb-event', dataset: { kind: 'event', id: ev.id ?? '' } },
    h('div', { class: 'cb-event__title' }, ev.title, ev.unverified ? h('span', { class: 'cb-flag', dataset: { flag: 'unverified' } }, t('bundle.events.unverified')) : null),
    h('div', { class: 'cb-event__meta' }, period, ev.venue_name ? ` · ${ev.venue_name}` : ''),
    h('div', { class: 'cb-event__foot' },
      sourceTagNode(ev.tier, src?.source_name ?? null),
      link ? externalLink(link.url, t('bundle.events.official')) : null));
}

/** 지도 정보창 내용. 앵커 이름·언급 건수·상위 1건(왕·날짜·한글 요약·한문 원문·출처 태그·링크). */
export function pinInfoNode(info, t) {
  const top = info.top;
  return h('div', { class: 'cb-info', dataset: { module: 'pin-info' } },
    h('strong', { class: 'cb-info__name' }, info.name),
    h('div', { class: 'cb-info__count' }, info.count > 0 ? [t('bundle.pin.count', { n: info.count }), info.atLeast ? ` ${t('bundle.at_least')}` : ''] : t('bundle.pin.none')),
    top ? [
      h('div', { class: 'cb-mention__when' }, [top.king, top.dateLabel].filter(Boolean).join(' · ') || t('bundle.unknown_date')),
      top.summary ? h('p', { class: 'cb-mention__summary' }, h('span', { class: 'cb-note' }, t('bundle.summary_label')), ' ', top.summary) : null,
      top.quote ? h('p', { class: 'cb-mention__quote', lang: 'lzh' }, h('span', { class: 'cb-note' }, t('bundle.quote_label')), ' ', top.quote) : null,
      h('div', { class: 'cb-mention__foot' }, sourceTagNode(top.tier, top.sourceName), externalLink(top.url, t('bundle.open_sillok'))),
    ] : null);
}
