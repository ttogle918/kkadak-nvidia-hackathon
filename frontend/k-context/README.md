# k-context — K-Context 프론트엔드 (1단계: 기반 골격)

`docs/ui-mockup/K-Context.dc.html`(Design Component 목업)을 모듈형으로 옮긴 프론트엔드다.
번들러·프레임워크·npm 의존성이 없다. **네이티브 ES 모듈 + 정적 서버**로 돈다. 외부 CDN·원격 폰트·원격 이미지는 쓰지 않는다
(샌드박스 데모에서 차단된다) — 폰트는 시스템 스택(Noto Sans KR 우선), 아이콘·지도는 인라인 SVG.
화면의 문구·연도·인물은 전부 자리표시(○○, "(예시)")다. 실제 사실처럼 보이는 내용을 새로 지어내지 않는다(AGENT_CONTEXT 11장).

1단계 상태: 골격·store·i18n·api(mock)·샘플 데이터·레이아웃·상단 바까지 동작한다. 6개 모듈(map·cards·chat·securitylog·rationale·timeline)은
**플레이스홀더 스텁**이며 2단계에서 채운다.

## 실행
ES 모듈은 `file://` 로 열면 막힌다.

```bash
cd frontend/k-context && python3 -m http.server 8766     # http://127.0.0.1:8766/
node --test                                               # 순수 로직 테스트(의존성 없음, node 20+)
```

`node --test tests/` 는 node 22 에서 "Cannot find module" 이 난다(디렉터리를 파일로 읽음). `node --test` 또는 `node --test tests/*.test.js` 를 쓴다.

URL 파라미터: `?lang=en` · `?theme=dark|light|auto` · `?mode=old|now|both` · `?day=1..3` · `?api=auto|mock|http|chat&base=/api` (기본 `auto` = 부팅 때 backend `http://localhost:8000/api` 를 한 번 찔러 보고 떠 있으면 `chat`(챗봇만 backend, 나머지 mock), 아니면 `mock`. `mock`·`chat` 은 강제 지정이고 `chat` 은 backend 가 없어도 mock 으로 넘어가지 않는다)

## 지도 렌더러 (SVG 기본 · 카카오맵 선택)
기본은 SVG 지도(외부 요청 없음). 카카오맵은 **키가 있고 SDK 가 로드될 때만** 자동으로 쓰이며, 아니면 SVG 로 폴백하고 콘솔에 사유 한 줄(`[map] 카카오맵 대신 SVG 지도 사용: …`, 키 값은 출력 안 함)을 남긴다.

1. 카카오 개발자 콘솔에서 앱 생성 → 카카오맵 사용 설정 ON → **JavaScript SDK 도메인**에 `http://localhost:8766` 등록(`127.0.0.1` 은 별도 도메인이라 따로 등록).
2. `cp config.local.example.js config.local.js` 후 **JavaScript 키**를 넣는다(`config.local.js` 는 gitignore). URL 파라미터로 키를 받지 않는다.
3. `python3 -m http.server 8766` → `http://localhost:8766/`. 키가 없으면 `config.local.js` 404 가 한 번 보이는데 정상이다(SVG 폴백).

**지도 SDK 에는 REST API 키를 쓰지 않는다**(JavaScript 키만). 외부 스크립트는 `https://dapi.kakao.com/v2/maps/sdk.js` 하나뿐이다. 코드: `src/lib/kakao-sdk.js`(로더·8초 타임아웃) · `src/components/map/renderer.js`(선택) · `kakao-view.js`(마커·폴리라인).
좌표는 `[lat, lng]`; lat/lng 가 null 인 항목은 건너뛴다(현재 mock 은 전부 null → 덕수궁 부근 기본 중심 + "좌표 없음" 표시). 결정 초안: `docs/kakao-map-sdk.decision-draft.md`.

## 구조
```
index.html                 진입점: CSS 1개(src/styles/index.css) + module script 1개(src/main.js)
src/
  main.js                  부트: store → api → actions → 레이아웃 → 모듈 mount → 데이터 로드
  modules.js               슬롯 이름 → 모듈 레지스트리
  lib/                     store · panel-level(하단 패널 단계 계산) · dom(h/on/esc/render) · i18n · format(출처 태그 문구·딱지) · theme · placeholder(스텁용)
  i18n/{ko,en}.js          UI 문구 사전(키는 1:1, 테스트가 검사)
  state/                   initial(상태 키) · actions(상태 전이) · selectors(파생값)
  api/                     index(createApi) · mock · http(스텁) · schema(계약 검증기)
  data/                    sources · cards · routes · itinerary · messages · auditlog · rationale (계약 형식 샘플)
  components/
    layout/                app-shell(슬롯 배치·설정 패널 틀·하단 패널 핸들) · topbar(보기·날짜·설정 기어) · settings(설정 패널 머리말·언어·테마·최소 변경) · seg(공용 세그먼트)
    map/ cards/ chat/ securitylog/ rationale/ timeline/    각 index.js(스텁) + <이름>.css(빈 파일)
  styles/                  tokens(변수·다크) · base(공통 원자) · layout(2열/모바일/설정 패널) · index(@import 목록)
tests/                     node --test
```

## 모듈 계약 (2단계 담당이 지킬 것)
각 `components/<m>/index.js` 는 **이것만** export 한다.

```js
export function mount(root /* HTMLElement */, ctx /* {store, api, t, actions} */) { /* ... */ return { destroy() {} }; }
```

- `root` 는 app-shell 이 만든 슬롯 div(`<section class="slot slot-<m>" data-slot="<m>">`). 그 안만 그린다. `destroy()` 는 구독 해제 + 이벤트 해제 + `root.replaceChildren()`.
- **모듈끼리 import 금지.** 소통은 `ctx.store`(상태)와 `ctx.api`(데이터)로만. 공통 동작은 `ctx.actions`, 공통 순수 함수는 `lib/` · `state/selectors.js` 를 쓴다.
- `ctx.t(키 | {ko,en} | 문자열, params?)` — 현재 언어로 바꾼다(아래 i18n). 언어가 바뀌면 `store` 가 알리므로 다시 그린다.
- 렌더는 `h()`/`render()` 로 노드를 만들고 `textContent`(자식 문자열)로 넣는다. **API·사용자 문자열을 innerHTML 에 넣지 않는다**(업로드 문서·웹 콘텐츠는 신뢰할 수 없는 입력).
- 구독: `store.subscribe(fn)` 또는 `store.select(selector, listener, {equals, fire})`. 해제 함수를 `destroy()` 에서 호출한다.
- 이벤트는 root 에 위임한다: `on(root, 'click', '[data-act]', (e, el) => …)`.
- 한 모듈이 던져도 앱은 뜬다(main.js 가 에러 박스를 그린다).
- 스타일은 `components/<m>/<m>.css` 에만 쓴다(이미 `styles/index.css` 가 import 한다 — `index.html`·`index.css` 를 고칠 필요 없음).
  클래스는 `.<m>-` 접두사, 색·간격은 `tokens.css` 변수만(hex 직접 금지), 다크는 변수가 처리한다. 공통 클래스 `.src-tag[data-grade]` · `.badge[data-badge]` · `.seg` · `.chip-toggle` 는 `base.css` 에 있다.
- 새 UI 문구는 `src/i18n/{ko,en}.js` 에 모듈 접두사 키(`map.*`, `cards.*` …)로 **양쪽 모두** 추가한다. 두 파일은 모듈별로 구역을 나눠 추가하고, 기존 키는 고치지 않는다.
- **쓰기 규칙:** 에이전트·도구가 쓰는 것은 draft 뿐이다. 보안 로그의 승인/거절은 사람이 누른 버튼에서만 `actions.decide()` 로 호출한다. 요청자·승인자 신원은 인자·LLM 출력으로 받지 않는다(서버가 주입).

### 모듈별 책임과 읽고 쓰는 상태
| 슬롯 | 책임(목업 화면) | 주로 읽는 키 | 주로 쓰는 액션 |
|---|---|---|---|
| `map` | 옛날 구간·핀, 지금 핀·구역, 숙소 복귀선, 이름표. 구간 클릭 | `mode` `day` `selectedSeg` `selectedRoute` `data` | `selectSeg` `selectRoute` |
| `cards` | 옛날 카드(사실 층·몰입 층·이설 병기)와 지금 카드(+분·체류·왜 맞나·확인 항목·포스터), 출처 태그와 상세 | `mode` `selectedSeg` `selectedNow` `immersion` `selectedTag` `hoverFact` `expandedTags` `added` `skipped` `lang` | `toggleImmersion` `openTag` `closeTag` `expandTags` `setHoverFact` `addSelected` `skipSelected` `openLocalContext` `openEvidence` |
| `chat` | 대화, 입력, 데모 버튼(공격 프롬프트·첫날 저녁) | `messages` `input` `sending` | `setInput` `send` |
| `timeline` | 날짜별 일정(원래/제안/추가/빈 시간) | `day` `added` `skipped` `selectedNow` `data.itinerary` | (읽기 위주) |
| `rationale` | 카드 위 작은 pill 태그 줄 + 누르면 뜨는 작은 팝오버(채택·탈락·충돌 해결·깔때기엔 걸러낸 것) | `openEvidence` `selectedSeg` `selectedNow` `mode` | `openEvidence` `closeEvidence` |
| `securitylog` | 허용/거부/승인 대기 로그, 사람 승인·거절 버튼 — **설정 패널 안**에 마운트 | `logs` `securityOpen` | `decide` `setSecurityOpen` |

## store 상태 키 (`src/state/initial.js`)
| 키 | 기본값 | 의미 | 목업 state |
|---|---|---|---|
| `lang` | `'ko'` | `'ko'`\|`'en'` | lang |
| `theme` | `'auto'` | `'auto'`\|`'light'`\|`'dark'` (`<html data-theme>`) | — |
| `mode` | `'both'` | `'old'`\|`'now'`\|`'both'` 지도·카드 보기 | mode |
| `day` | `1` | 1\|2\|3 | day |
| `minimizeChanges` | `true` | 일정 최소 변경 토글 | min |
| `immersion` | `true` | 몰입 층 켬/끔 | imm |
| `selectedRoute` | `'A'` | 선택한 경로 id | — |
| `selectedSeg` | `'card_old_4'` | 선택한 **옛날 구간의 card_id** \| null | seg |
| `selectedNow` | `'card_now_1'` | 화면에 올린 지금 카드 id \| null | — |
| `selectedTag` | `null` | 열어 둔 출처 태그의 **source id**(예 `doc_03`) | tag |
| `expandedTags` | `{}` | `{[카드 id]: true}` "+N 출처" 펼침 | exp |
| `openEvidence` | `null` | 판단 근거에서 연 항목 key(`rationale.chips[].key`) | ev |
| `hoverFact` | `null` | 사실 층 문장 하이라이트(출처 번호 1~) | hn |
| `securityOpen` | `true` | 보안 로그 패널 열림 | sec |
| `added` / `skipped` | `false` | `selectedNow` 카드를 일정에 넣음/건너뜀 | added / skipped |
| `input` | `''` | 대화 입력창 | input |
| `messages` | `[]` | 대화(Message[]) — `loadAll` 이 채움 | msgs |
| `logs` | `[]` | 보안 로그(AuditEntry[]) | logs |
| `sending` | `false` | `send` 진행 중 | — |
| `data` | `{itinerary,routes,cards,sources: null}` | api 로 받은 원본 | (SEG/TAGS 상수) |
| `loaded` / `error` | `false` / `null` | 로드 상태 | — |
| `settingsOpen` | `false` | 설정 패널(보안 로그·언어·테마·최소 변경) 열림 | — |
| `panelLevel` | `'default'` | 하단 패널(`.cards-zone`) 높이 단계 `'collapsed'`\|`'default'`\|`'expanded'` — 접힘 48px / 가운데 열의 1/3 / 70% | — |
| `mobileTab` / `sheetOpen` | `'chat'` / `false` | 모바일 시트 탭(`chat`\|`timeline`)과 열림 | — |

규칙: 상태는 불변 갱신(`setState({k: 새 값})` 또는 `setState(s => patch)`). 배열·객체는 새 참조로 넣는다. 같은 값이면 알림이 가지 않는다.
`lib/store.js`: `getState()` · `setState(patch|fn)` · `subscribe(fn(state, prev))` · `select(selector, listener, {equals, fire})`.

### 공유 액션 (`ctx.actions`, `src/state/actions.js`)
`loadAll` · `setLang` · `setTheme` · `setMode` · `setDay` · `toggleMinimize` · `toggleImmersion` · `setSecurityOpen` · `setSettingsOpen` ·
`selectSeg(cardId|null)` · `selectRoute(id)` · `selectNow(cardId)` · `openLocalContext(storyCardId)` · `openTag(sourceId)` · `closeTag` · `expandTags(cardId)` ·
`openEvidence(key)` · `closeEvidence` · `setHoverFact(n|null)` · `addSelected` · `skipSelected` · `setInput` · `send(text?)` · `decide(id,'approve'|'reject')` · `setMobileTab` · `setSheetOpen` · `setPanelLevel(level)` · `stepPanel(±1)`.
필요한 전이가 없으면 `actions.js` 에 한 줄 추가하되, 기존 함수의 동작은 바꾸지 않는다(다른 모듈이 의존한다).

### 파생값 (`src/state/selectors.js`) · 표시 규칙 (`src/lib/format.js`)
`cardById` · `routeById` · `nowCardsForDay` · `timelineFor(itinerary, day, state)` · `showsOld(mode)` · `showsNow(mode)` /
`pendingCount(logs)`(승인 대기 수 — 기어 알림) · `sourceLabel(src)` = `[등급] 이름 · 위치` · `numberedSourceLabel(src, i)` · `circled(n)` · `badgeKind(badge)` · `BADGE_KEY`(딱지 → `data-badge` 값).

## API (`ctx.api`) — mock 과 http 의 이름·시그니처가 같다
모두 Promise. `createApi({mode:'mock'|'http', baseUrl, latencyMs})`.

| 메서드 | 반환 |
|---|---|
| `getItinerary()` | `{trip, anchors[], free_slots[], party, language, interests[], minimize_changes, landmarks[], walk_back, timeline[{day,items[]}]}` |
| `getRoutes()` | `Route[]` — A·B·C (계약 3.3 경로 JSON) |
| `getCards()` | `Card[]` — 옛날 3(`card_old_1/2/4`) + 지금 3(`card_now_1/2/3`) |
| `getCard(id)` | `Card` (없으면 reject) |
| `getSources()` | `Source[]` (`doc_01`…`doc_08`) |
| `getRationale(cardId)` | `{card_id, chips[{key,tone,label}], items{[key]:{title,text,rows[{k,v}]}}}` |
| `getMessages()` | `Message[]` `{id, role:'user'\|'agent', text, assume?, blocked?}` |
| `sendMessage(text)` | `{reply: Message, logs: AuditEntry[]}` — 공격 프롬프트(`/secret|\.txt|key/i`)는 `reply.blocked=true` + `kind:'deny'` 로그 |
| `getAuditLog()` | `AuditEntry[]` `{id, time, kind:'ok'\|'deny'\|'pend'\|'approved'\|'rejected', text, decided_by}` |
| `decideAudit(id, decision)` | `AuditEntry` — `decision` 은 `'approve'\|'reject'`, **대기(pend)만** 가능. 결정자(`decided_by`)는 서버가 채운다 |

`decideAudit` 은 backend 의 사람 전용 승인 API 와 같은 개념이다. 요청에 신원 필드를 넣지 않는다.

### 데이터 형식
`data/*.js` 는 AGENT_CONTEXT 3.3 의 카드·경로 JSON 을 그대로 따른다(`api/schema.js` 의 `validateCard`/`validateRoute` 와 테스트가 검증).
문자열 필드는 `string` 또는 `{ko, en}` 이다 — 반드시 `ctx.t(값)` 으로 꺼낸다. 계약에 없는 **확장 필드**(목업 화면에 필요해 추가, 정식 채택은 3.3 수정 후):

- 카드: `era` · `facts[{text, ref}]`(사실 층 문장과 출처 번호) · `alternatives[{label,text}]`(이설 병기) · `checks[{level:'ok'|'warn'|'bad', text}]` · `poster{read}` · `only` · `warning{title,body}` · `kind_label`
- 카드 `geometry.space:'schematic'` — `coords` 가 목업 지도 좌표계(viewBox `0 0 600 700`)의 `[x,y]`. 실제 API 는 `[lat,lng]` 이고 `place.lat/lng` 는 샘플에서 null. 지도 모듈은 `space` 를 보고 둘 다 처리한다.
- 경로 `segments[].coords`·`label_xy`(카드 없는 연결 구간 `card_id:null` 도 그린다). `selectedSeg` 는 구간의 `card_id` 이므로 null 구간은 선택 불가.
- 일정 `landmarks[]`(지도 고정 지점: `anchor`/`hotel`/`poi`/`dot`/`muted`) · `walk_back`(숙소 복귀선) · `timeline[]` · `free_slots[].assumption`
- 출처 `bib`(URL 이 없는 문헌의 서지 문자열). 출처 태그는 `sourceLabel()` 로 만들고, 누르면 `quote` · `url`/`bib` · `collected_at` 을 보여 준다.

## i18n
`ctx.t(x, params?)` 한 함수로 세 형태를 처리한다: 사전 키(`'topbar.mode.old'`) · `{ko,en}` 객체 · 사전에 없는 문자열(그대로). `{n}` 자리표시는 `params` 로 채운다.
딱지는 `t('badge.' + card.badge)`, 경로 딱지는 `t('route.badge.' + b)`.

## 레이아웃 (app-shell)
슬롯: `topbar` `chat` `timeline` `map` `rationale` `cards` `settings` `securitylog` (`SLOT_NAMES`). 오른쪽 열은 없다.
- **데스크톱(≥900px)** 2열: 왼쪽 `chat`+`timeline` / 가운데 `map` + 카드 영역(`.cards-zone` = `rationale` 태그 줄 위, `cards` 아래).
  `rationale` 슬롯은 overflow 를 자르지 않아 태그 팝오버가 카드 위로 뜬다.
- **모바일(<900px)**: `map` 이 바탕, 카드 영역은 지도 위에 겹침(바닥, 팝오버는 위로 열림), `chat`·`timeline` 은 아래 시트이며 하단 탭(대화·일정)으로 전환한다.
- **설정 패널**: 톱바 기어 버튼 → `settingsOpen`. 데스크톱은 톱바 아래 우측 드로어, 모바일은 바닥 시트. 안에 `settings`(머리말·닫기·최소 변경·테마·언어)와 `securitylog` 슬롯이 있다.
  Esc·바깥(backdrop) 클릭·닫기 버튼으로 닫고 포커스는 기어로 돌아간다. 승인 대기(pend) 로그가 있으면 기어에 점+숫자(aria-label 에도 개수).
- 판단 근거 태그는 pill(높이 22px·글자 11px), 터치 영역은 `::after` 투명 패딩으로 확장. `openEvidence` 로 팝오버가 열린다(같은 태그 재클릭·Esc·바깥 클릭·✕ 로 닫음).
  카드의 "왜 이걸 골랐나요?" 링크도 첫 태그의 팝오버를 연다.
- **하단 패널 핸들**(shell 소유, `.cards-zone` 맨 위): 막대+제목(`role=separator`, `aria-valuenow/min/max`) + ^ / v 버튼. 세 단계 — 접힘(핸들+카드 제목 한 줄, 48px) / 기본(가운데 열의 1/3) / 펼침(70%).
  ^ 는 한 단계 위, v 는 한 단계 아래. 핸들 드래그(pointer events, 터치 포함)는 자유 리사이즈 후 놓으면 가장 가까운 단계로 스냅(임시 높이는 shell 로컬, 놓을 때 `setPanelLevel` 만 store 에).
  키보드: 위/아래 화살표 = 단계 이동, Enter/Space = 접힘↔기본. 선택 카드가 바뀌어도 접어 둔 패널을 자동으로 펼치지 않는다. 계산은 `lib/panel-level.js`(순수 함수). 모듈(cards·rationale)은 높이를 몰라도 되고 스크롤만 된다.
  지도(`map`)가 메인이다: 구간 안내 목록은 접힌 채 시작하고 경로 A·B·C 카드는 낮은 한 줄이다(자세한 이유는 툴팁 `title`).
- 모듈은 화면 크기를 몰라도 된다 — 슬롯 안에서 가로로 유연하게만 그린다. 모바일 터치 크기는 `--tap`(40px) 이상.
- 슬롯 높이 배분은 `styles/layout.css` 에 있다.

## API 연결 방법 (mock → 실제 backend)
1. `src/api/http.js` 의 `ENDPOINTS`(제안 표)를 backend 와 확정한다. 계약이 바뀌면 AGENT_CONTEXT 3.3 을 먼저 고친다.
2. `createHttpApi` 의 메서드를 `fetch(baseUrl + path)` 로 채운다(응답 검증은 `api/schema.js`). 인자 개수는 mock 과 같아야 한다(테스트가 검사).
3. 실행: `?api=http&base=/api`. 프론트는 정적 서버가 `/api` 를 프록시하거나 같은 origin 에서 서빙한다. **키·토큰은 프론트에 두지 않는다**(게이트웨이 provider 에만 있다).
4. `decideAudit` 은 사람 세션에서만 호출되는 사람 전용 API 로 연결한다. 에이전트용 MCP 서버와 프로세스를 분리한다(CLAUDE.md D3).


## 행사 찾기·관리자 화면 (별도 페이지)
기존 앱 골격과 분리된 두 페이지다. 같은 `lib/`(dom·store)와 디자인 토큰을 쓴다.

| 페이지 | 설명 |
|---|---|
| `events.html` | 여행 날짜·숙소·관심사·기존 일정 입력 → 행사 목록·지도·상세(날짜·장소·요금·예약·참여조건·언어·출처·마지막 검증)·일정 추가/취소·저장한 행사의 변경 배지·제보 |
| `admin.html` | 신규·변경, 충돌·누락, 수집 오류, 참여조건 확인 필요, 제보 승인/반려, 수동 확인 링크, 출처 현황·수동 재수집 (토큰 필요) |

- URL 파라미터: `?api=http|mock` (기본 http) · `?base=<backend 주소>` · `?lang=en`
- 정적 서버(8766)에서 열면 backend 기본 주소는 같은 호스트의 `:8000/api` 다. 다르면 `?base=` 를 쓴다.
- `?api=mock` 은 데모 데이터(전부 합성, 배너·"(데모)" 표시)다. 실제 행사처럼 쓰지 않는다.
- 일정·저장한 행사는 이 브라우저(localStorage)에만 저장된다. 관리자 토큰은 이 탭(sessionStorage)에만 둔다.
- 코드: `src/events/{api,logic,controller,view,admin,main,i18n,demo-data}.js`. 테스트: `tests/events.*.test.js`.
