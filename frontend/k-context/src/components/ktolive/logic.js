// 한국관광공사 관광정보(원문) 절의 뷰 모델. DOM 을 만지지 않는다. 값은 서버 응답 문자열 그대로(가공 없음, D29).
// 계약: docs/sprints/sprint-4.md §5.2 kto_live.
export const KTO_TITLE_KEY = 'ktolive.title';

const present = (v) => typeof v === 'string' && v !== '';

/**
 * @param {object|null} bundle 검증된 챗 묶음(validateChatBundle 의 bundle)
 * @param {(key:string)=>string} t i18n
 * @returns {{state:'none'|'ok'|'unavailable', items:Array<{fields:Array<{label,value}>, attribution:string}>, sourceUrl:string|null}}
 */
export function ktoView(bundle, t) {
  const k = bundle?.kto_live;
  if (!k || typeof k !== 'object') return { state: 'none', items: [], sourceUrl: null };
  if (k.status !== 'ok') return { state: 'unavailable', items: [], sourceUrl: null };
  const att = k.attribution ?? {};
  const items = (k.items ?? []).map((it) => {
    const fields = [];
    if (present(it.title)) fields.push({ key: 'title', label: t('ktolive.f.title'), value: it.title });
    const addr = [it.addr1, it.addr2].filter(present).join(' ');
    if (addr) fields.push({ key: 'addr', label: t('ktolive.f.addr'), value: addr });
    if (present(it.eventstartdate) || present(it.eventenddate)) {
      fields.push({ key: 'period', label: t('ktolive.f.period'), value: `${it.eventstartdate ?? ''}–${it.eventenddate ?? ''}` });
    }
    if (present(it.tel)) fields.push({ key: 'tel', label: t('ktolive.f.tel'), value: it.tel });
    // 유형별 출처 문구. 모르는 값이면 Type3(더 엄격한 쪽).
    const text = (present(it.cpyrhtDivCd) && att[it.cpyrhtDivCd]) || att.Type3 || t('ktolive.attribution.type3');
    return { fields, attribution: text };
  });
  return { state: 'ok', items, sourceUrl: present(k.source_url) ? k.source_url : null };
}
