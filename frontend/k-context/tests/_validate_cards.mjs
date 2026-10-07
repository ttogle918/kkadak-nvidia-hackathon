// stdin 의 JSON({cards, rationale}) 을 schema.js 의 validateCard 와 판단 근거 모양 검사로 확인한다.
// Python 테스트(tests/domains/kcontext/catalog/test_kc_catalog_cards.py)가 부른다. 파일명 앞 _ 는 node --test 가 실행하지 않게 한다.
import { validateCard } from '../src/api/schema.js';

let raw = '';
for await (const chunk of process.stdin) raw += chunk;
const { cards, rationale } = JSON.parse(raw);
const isText = (v) => typeof v === 'string' || (v && typeof v.ko === 'string' && typeof v.en === 'string');
const problems = [];
for (const c of cards) {
  problems.push(...validateCard(c));
  const r = rationale?.[c.id];
  if (!r) { problems.push(`rationale[${c.id}]: 없음`); continue; }
  if (r.card_id !== c.id) problems.push(`rationale[${c.id}].card_id`);
  if (!Array.isArray(r.chips) || !r.chips.length) problems.push(`rationale[${c.id}].chips`);
  for (const ch of r.chips ?? []) {
    if (typeof ch.key !== 'string' || ch.tone !== 'now' || !isText(ch.label)) problems.push(`rationale[${c.id}].chip ${ch.key}`);
    const it = r.items?.[ch.key];
    if (!it || !isText(it.title) || !isText(it.text) || !Array.isArray(it.rows)) problems.push(`rationale[${c.id}].items.${ch.key}`);
    for (const row of it?.rows ?? []) if (!isText(row.k) || !(typeof row.v === 'string' || isText(row.v))) problems.push(`rationale[${c.id}].items.${ch.key}.row`);
  }
}
console.log(JSON.stringify({ count: cards.length, problems }));
