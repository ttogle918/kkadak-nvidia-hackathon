확인 날짜: 2026-10-10 (T403, Sprint 4 Stage 1a). 실호출 없음 — 문서 읽기만 했다. 계정·사이트·토큰은 쓰지 않았다.

# T403 — Netlify 정적 배포·API 연결

방법: `curl -sL https://docs.netlify.com/<경로>.md`(문서 페이지의 Markdown 판)를 받아 읽었다. 아래 "원문" 은 문서 문장을 옮긴 것이고, 문서에 없는 것은 `[확인 필요]` 로 둔다. 출처는 모두 docs.netlify.com 이고 확인 날짜는 2026-10-10 이다.

## 요약 (결론은 §9)
- 프록시 리라이트 요청 시간 한도는 **26초**다. 일정 흐름은 최대 100초이므로 프록시로는 끊긴다.
- 프록시가 방문자 IP 를 어떤 헤더로 넘기는지는 문서에 없다 `[확인 필요]`.
- **결론: 직접 CORS** (프록시 쓰지 않음).

## 1. 출처
| 주제 | URL |
|---|---|
| 리라이트·프록시 | https://docs.netlify.com/manage/routing/redirects/rewrites-proxies/ |
| 리다이렉트 규칙 순서 | https://docs.netlify.com/manage/routing/redirects/redirect-options/ |
| 사용자 지정 헤더 | https://docs.netlify.com/manage/routing/headers/ |
| CSP | https://docs.netlify.com/manage/security/content-security-policy/ |
| 파일 기반 설정 `netlify.toml` | https://docs.netlify.com/build/configure-builds/file-based-configuration/ |
| 빌드 설정 정의(publish·command) | https://docs.netlify.com/build/configure-builds/overview/ |
| 빌드 환경변수 | https://docs.netlify.com/build/configure-builds/environment-variables/ |
| 비밀 환경변수 | https://docs.netlify.com/build/environment-variables/secrets-controller/ |
| 배포 방법 | https://docs.netlify.com/deploy/create-deploys/ |
| CLI | https://docs.netlify.com/api-and-cli-guides/cli-guides/get-started-with-cli/ |
| Deploy Preview | https://docs.netlify.com/deploy/deploy-types/deploy-previews/ |
| 요금제(크레딧) | https://docs.netlify.com/manage/accounts-and-billing/billing/billing-for-credit-based-plans/credit-based-pricing-plans/ |
| 크레딧 소진 시 | https://docs.netlify.com/manage/accounts-and-billing/billing/billing-for-credit-based-plans/how-credits-work/ |
| 함수 API(`ip`) | https://docs.netlify.com/build/functions/api/ |
| Edge Functions API | https://docs.netlify.com/build/edge-functions/api/ |

## 2. 정적 배포 (CLI · Git 연동, publish · build command)
- `netlify.toml` 의 `[build]` 에 `publish`(publish directory)와 `command`(build command)를 쓴다. `command` 는 Bash 에서 돈다. `environment` 로 빌드 환경변수도 선언할 수 있다. (출처: file-based-configuration, "Build settings", 2026-10-10)
- 파일 위치·컨텍스트: `[context.production]`·`[context.deploy-preview]` 등으로 배포 컨텍스트별 `publish`·`command` 를 바꿀 수 있다. 단 `[[redirects]]`·`[[headers]]` 는 컨텍스트별로 못 나눈다(같은 문서 "Deploy contexts").
- 배포 방법: Git 연동(push 마다 빌드), **Netlify CLI**, 드래그 앤 드롭, API 등. (출처: deploy/create-deploys, 2026-10-10)
- **수동 배포는 빌드 명령을 실행하지 않는다**: 원문 "When you create a deploy manually without continuous deployment, Netlify does not run a build command." 즉 `netlify deploy` 는 로컬에서 만든 디렉터리를 올린다. 로컬에서 먼저 `dist/` 를 만들어야 한다. (출처: deploy/create-deploys)
- `netlify deploy` 요약 (출처: CLI get-started, "Manual deploys", 2026-10-10)
  - `netlify deploy` — 기본은 **draft(미리보기) URL** 로 올린다. `--alias=이름` 으로 draft 주소의 하위 도메인을 정한다(브랜치 이름과 겹치면 안 됨).
  - `netlify deploy --prod` (`-p`) — 운영 주소에 배포.
  - `netlify deploy --dir=<폴더>` — 올릴 폴더. 플래그 → `netlify.toml` → UI 설정 순으로 찾는다.
  - 인증: `netlify login`(토큰을 로컬 `config.json` 에 저장) 또는 환경변수 `NETLIFY_AUTH_TOKEN`(CI). 사이트 지정은 `--site` 또는 `NETLIFY_SITE_ID`.
  - `--allow-anonymous` — 계정 없이 임시 프로젝트를 만들고 1시간 안에 소유권을 가져가야 한다(우리 운영 배포에는 쓰지 않는다).
- 이 프로젝트 적용안(T424 입력): 빌드 스크립트가 `dist/` 를 만든 뒤 `netlify deploy --dir=dist --prod` 로 올린다. `netlify.toml` 에는 `[build] publish = "dist"` 를 둔다. `[확인 필요]`: `--prod` 에서 draft 를 먼저 보고 올리는 권장 순서는 T427 에서 실측.
- 가격: **운영(Production) 배포 1회 = 15 크레딧.** 미리보기·브랜치 배포·실패한 배포는 크레딧을 쓰지 않는다. (출처: credit-based-pricing-plans, "Platform Features"·"Non-metered functionality", 2026-10-10)

## 3. 빌드 때 환경변수로 파일 생성, 값이 로그에 찍히는가
- 환경변수는 UI·CLI·API·`netlify.toml` 로 선언한다. 스코프에 **Builds** 가 포함돼야 빌드에서 보인다. (출처: build/configure-builds/environment-variables, 2026-10-10)
- 원문: 변수를 배포 로그에 찍으려면 빌드 명령에 `echo $GREETING` 같은 것을 **직접 넣어야** 한다("**not-sensitive** variable"). 즉 **자동으로 찍히지 않는다. 우리 빌드 스크립트가 값을 echo 하지 않으면 로그에 안 나온다.** `NETLIFY_BUILD_DEBUG=true` 는 디버그 출력을 늘리지만 "민감 정보는 없다"고 문서가 적었다.
- `netlify.toml` 안에 `$VAR` 를 쓰면 값이 치환되지 **않는다**. 치환은 빌드 명령(`sed` 등)으로만 되고, 그것도 `[[headers]]`·`[[redirects]]` 에만 해당한다. (출처: file-based-configuration, "Inject environment variable values")
- 비밀 표시(`netlify env:set --secret`): 값은 쓰기 전용이 된다. 빌드·함수 등 Netlify 시스템 안의 코드만 원문을 받는다. (출처: secrets-controller) → 카카오 JS 키는 설계상 공개값이므로(T404) 비밀 표시는 필수가 아니다. 그래도 빌드 스크립트가 `config.local.js` 를 만들 때 값을 echo·set -x 로 출력하지 않는다(T424 규칙).
- 비밀 스캔: secrets-controller 문서에 "Secret scanning" 절이 있다(내용은 이번에 끝까지 읽지 않았다). 브라우저에 들어가는 공개 키가 걸리는지는 `[확인 필요]` (T427 첫 배포에서 확인. 걸리면 해당 변수를 비밀로 표시하지 않거나 스캔 제외 설정을 쓴다).
- 로컬 빌드에서 원문 값은 없다: 비밀로 표시한 변수는 `netlify build`(로컬)에서도 마스킹 값이 된다. 비밀로 표시하지 않으면 로컬 빌드는 `.env` 나 셸 env 로 한다.

## 4. 프록시 리라이트의 요청 시간 한도 (핵심)
- 문서 문장 그대로: **"Proxy rewrite requests will time out after 26 seconds. If you are proxying to a longer-running process, we recommend making an asynchronous request rather than waiting for a response."**
- 출처: https://docs.netlify.com/manage/routing/redirects/rewrites-proxies/ ("Limitations" 절), 확인 날짜 2026-10-10.
- 문법(참고): `/api/*  https://api.example.com/:splat  200` 상태 코드 200 이 리라이트다. 같은 문서에 "CORS 를 지원하지 않는 API 를 위해"라는 용도로 소개돼 있다.
- 일정 흐름 최대 100초 > 26초 → **프록시 부적합**.
- 같은 문서의 다른 제약(참고): 내부 리라이트는 1 hop 만, 프록시 응답에는 `_headers`/`[[headers]]` 의 사용자 지정 헤더가 붙지 않는다(§6), HTTPS→HTTP 리다이렉트가 기대대로 안 될 수 있다, 요청 헤더는 `[[redirects]]` 의 `headers = {X-From = "Netlify"}` 로 추가할 수 있다(응답이 아니라 요청).
- `[확인 필요]`: 유료 플랜·Enterprise 에서 이 한도가 달라지는지는 문서에 적혀 있지 않다. 무료 플랜 기준은 위 문서 하나뿐이다.

## 5. 프록시가 방문자 IP 를 넘기는 헤더
- rewrites-proxies, redirect-options, headers 문서에는 **프록시 요청에 방문자 IP 를 어떤 헤더로 붙이는지 적혀 있지 않다.** → `[확인 필요]` (`X-Forwarded-For`·`X-Nf-Client-Connection-Ip` 같은 이름은 기억에서 나온 것이라 쓰지 않는다. 받은 문서 페이지들을 `x-forwarded-for`·`client-ip`·`x-nf-client-connection-ip` 로 검색했지만 프록시 관련 기재는 없었다.)
- 문서에 있는 IP 관련 항목은 함수·엣지 함수의 값뿐이다: 함수 API 의 `context.ip` ("A string containing the client IP address."), Edge Functions 의 `context` 객체. 원문(edge-functions/api): "Netlify doesn't add specific headers to edge function requests. To find information about the client request, use the `context` object instead." 이는 프록시가 아니라 Netlify 함수를 쓸 때의 이야기이고, 우리는 함수를 쓰지 않는다(D27 대안 (a)).
- 영향: 프록시를 쓰면 Cloud Run 이 보는 연결 주소는 Netlify 이므로 IP 기반 제한(D24)이 무력해질 수 있다. 헤더가 문서에 없으므로 프록시 선택은 이 점으로도 불리하다.
- 직접 CORS 에서는 브라우저가 Cloud Run 에 직접 연결하므로 IP 는 Cloud Run 이 `X-Forwarded-For` 로 본다(`KC_TRUSTED_PROXY_HOPS` 값은 T402 근거).

## 6. 응답 헤더(CSP) 설정과 HTML meta 의 관계, Report-Only
- 설정 방법 두 가지 (출처: manage/routing/headers, 2026-10-10)
  - publish 디렉터리에 `_headers` 파일. 경로 줄 아래에 들여쓰기로 `이름: 값`.
  - `netlify.toml` 의 `[[headers]]` (`for = "/*"`, `[headers.values]`).
  - 예: `/events.html` 줄 아래 `  Content-Security-Policy: ...`. 와일드카드 `*`·플레이스홀더 `:name` 사용 가능.
- 제약 (같은 문서 "Limitations"): 헤더는 **Netlify 가 자기 저장소에서 서빙하는 파일에만** 붙는다. 프록시·함수·엣지 함수 응답에는 안 붙는다. 헤더는 모든 빌드에 전역이며 브랜치·컨텍스트별로 나눌 수 없다(우회: 빌드 명령에서 파일 복사). `Content-Encoding`·`Set-Cookie` 등 일부 헤더는 무시된다.
- `_headers` 파일은 빌드 결과(publish 디렉터리)에 들어 있어야 한다. 빌드 스크립트가 `dist/_headers` 를 만들 수 있다.
- CSP 문서(manage/security/content-security-policy): 두 헤더 이름이 문서에 있다.
  - `Content-Security-Policy` — 강제.
  - **`Content-Security-Policy-Report-Only`** — 차단 없이 위반만 수집하는 시험용. 예시 줄이 문서에 있고 `_headers` 에 넣으라고 한다. → **Report-Only 지원: 예 (문서에 있음).**
  - nonce 는 확장(Content Security Policy extension)이나 엣지 함수로 만든다. 우리는 쓰지 않는다(정적 + 카카오 SDK 때문에 강제하지 않음, D27 ②).
- **HTML `<meta http-equiv="Content-Security-Policy">` 와 `_headers` 의 관계: 문서에 없다. `[확인 필요]`.** (헤더 문서·CSP 문서 모두 meta 언급 없음.) 일반적인 브라우저 동작(헤더와 meta 가 둘 다 있으면 각각의 정책이 모두 적용되어 더 엄격한 쪽이 이김)은 Netlify 문서가 아니라 브라우저 표준의 이야기이므로 여기서 확정하지 않고 T427 의 화면 확인에서 실측한다.
- 직접 CORS 일 때 `events.html` 의 `connect-src` 에 Cloud Run 원점을 넣는 것(D27 ②)은 `_headers` 든 meta 든 가능하다. 어느 쪽이든 카카오 SDK 가 쓰는 출처 목록은 T404 가 정하므로 지금은 **강제 CSP 를 넣지 않고, 넣는다면 Report-Only** 로 제안한다.

## 7. 무료 플랜 한도
출처: credit-based-pricing-plans (2026-10-10). **2025-09-04 이후 신규 계정은 모두 크레딧제**이고 그 전 계정은 Legacy 플랜이다. 우리 계정이 어느 쪽인지는 H5 때 확인 `[확인 필요]`.
| 항목 | 무료(Free) 값 |
|---|---|
| 월 크레딧 | **300 크레딧/월, 하드 리밋**(자동 충전 없음) |
| 월 구독료 | $0 |
| 웹 요청 | 10,000 요청 = 2 크레딧 |
| 웹 대역폭 | 1 GB = 20 크레딧 |
| 운영 배포 | 1회 = 15 크레딧 |
| 미리보기·브랜치 배포·실패한 배포 | 크레딧 소모 없음 |
| 동시 빌드 | 1 |
| 폼 제출 | 무제한 무료 |
| Functions compute | 1 GB-hour = 10 크레딧 (우리는 안 씀) |
- 크레딧을 다 쓰면 **모든 웹 프로젝트가 정지되고 방문자는 `Site not available` 페이지를 본다.** (출처: how-credits-work, 2026-10-10) → 공개 배포가 공격·과다 트래픽으로 크레딧을 소진하면 화면이 멈춘다. 다만 요금이 청구되지는 않는다(하드 리밋).
- 간단 계산(참고, 계산식은 위 표 값만 사용): 300 크레딧 = 운영 배포 20회 분 또는 대역폭 15 GB 분 또는 웹 요청 1,500만 건 분. 정적 화면이라 배포 횟수를 아끼면 충분하다(이 값은 계산이며 Netlify 문서에는 이 문장이 없다).
- 프록시 요청도 웹 요청으로 세어질 가능성이 있으나 문서에 명시가 없다 `[확인 필요]` — 어차피 프록시를 쓰지 않는다.
- 규칙 수·`netlify.toml` 크기 제한 등 리다이렉트 개수 한도: 문서에서 찾지 못했다 `[확인 필요]` (우리는 규칙이 거의 없다).

## 8. 미리보기 도메인 형식
출처: deploy/deploy-types/deploy-previews, create-deploys (2026-10-10).
- 운영: `https://<프로젝트이름>.netlify.app`.
- Deploy Preview(PR): `deploy-preview-<PR번호>--<프로젝트이름>.netlify.app`.
- 배포 영구 링크: `<배포ID>--<프로젝트이름>.netlify.app` (내용이 바뀌지 않는다).
- Agent Runner 미리보기: `agent-<실행ID>--<프로젝트이름>.netlify.app`.
- CLI draft 배포: 임의 문자 하위 도메인. `--alias=<이름>` 이면 `<이름>--<프로젝트이름>.netlify.app` 형태일 것으로 보이나 문서 예시 텍스트는 이미지라서 형태는 `[확인 필요]`.
- 영향: 이 미리보기 출처들은 운영 출처와 **다르다.** 직접 CORS 에서는 `KC_CORS_ORIGINS` 에 운영 도메인 1개만 두므로 미리보기에서 API 호출은 거부된다(안전한 쪽). 미리보기를 화면 확인용으로만 쓰고 API 는 운영 도메인에서만 확인한다. 카카오 도메인 등록 필요 여부는 T404. `netlify.app` 은 Public Suffix List 에 올라 있어 하위 도메인 간 쿠키 공유가 안 된다(출처: manage/routing/headers). 우리는 쿠키를 쓰지 않는다(D24 (a) 기각).

## 9. 결론: 직접 CORS

**결론: 직접 CORS. 프록시를 쓰지 않는다.**

근거 (절 번호):
1. **§4** — 프록시 리라이트 요청 시간 한도는 26초(문서 명시). 일정 요청 최대 100초 > 26초. 명세 "프록시 한도가 100초 미만이면 직접 CORS" 에 해당한다.
2. **§5** — 프록시가 방문자 IP 를 넘기는 헤더가 문서에 없다. IP 기반 제한(D24)을 프록시 뒤에서 보증할 수 없다 `[확인 필요]`. (이것만으로도 기각 사유가 된다.)
3. **§6** — 프록시 응답에는 `_headers` 가 붙지 않으므로, 프록시를 쓴다면 CSP 등을 Cloud Run 이 직접 내려야 한다. 직접 CORS 에서는 정적 파일(`events.html`)에만 `_headers`/meta 로 `connect-src` 를 넣으면 된다.
4. **§7** — 프록시를 쓰든 안 쓰든 무료 크레딧(300)은 정적 요청에도 소모된다. 직접 CORS 는 API 트래픽이 Netlify 를 거치지 않아 Netlify 쪽 크레딧을 아낀다. (요청 수 환산은 §7 표 기준, 프록시 요청의 과금 방식은 `[확인 필요]`.)

CSP 조건별 정리 (명세 ⑨ "CSP 조건별"):
| 조건 | 선택 |
|---|---|
| CSP 강제 안 함(기본) | `_headers` 없이 시작. 카카오 SDK 를 깨뜨리지 않는다. |
| 시험(권장) | `_headers` 에 `Content-Security-Policy-Report-Only`(문서에 예시 있음)로 시작 → 위반 목록은 T404 의 출처 목록과 대조. |
| 강제 | T404 가 확정한 카카오 출처 + Cloud Run 원점을 `connect-src` 에 넣은 뒤. meta 와 헤더 동시 적용 규칙은 `[확인 필요]` 이므로 **둘 중 하나만** 쓴다. |

### D27 ② 문장 제안 (사람이 승인한 뒤 DECISIONS 에 반영 — dev 는 DECISIONS 를 고치지 않는다)
> ② API 연결은 **직접 CORS** 다. Netlify 프록시 리라이트의 요청 시간 한도가 26초(docs.netlify.com, 2026-10-10)로 일정 흐름 최대 100초보다 짧고, 프록시가 방문자 IP 를 넘기는 헤더가 문서에 없어 IP 기반 제한(D24)을 보증할 수 없다. 브라우저가 Cloud Run 을 직접 호출하며 `KC_CORS_ORIGINS`=Netlify 운영 도메인 1개, 빌드가 `dist/events.html` 의 `connect-src` 에 Cloud Run 원점을 넣는다. 미리보기 도메인은 CORS 허용 대상이 아니다. `index.html` 의 CSP 는 이번에 강제하지 않는다(카카오 SDK 를 깨뜨릴 위험 — 넣는다면 `Content-Security-Policy-Report-Only`). [확인 필요: meta CSP 와 `_headers` CSP 의 동시 적용 규칙(T427 실측), T402 의 `KC_TRUSTED_PROXY_HOPS` 근거]

## 10. `[확인 필요]` 목록
1. 프록시가 방문자 IP 를 붙이는 헤더 이름 (§5) — 문서에 없음. 프록시를 쓰지 않으므로 결론에 영향 없음.
2. `<meta>` CSP 와 `_headers` CSP 의 동시 적용 (§6) — Netlify 문서에 없음. T427 에서 실측.
3. 비밀 스캔이 공개 JS 키(카카오)를 막는지 (§3) — T427 첫 배포에서 확인.
4. 계정이 크레딧제인지 Legacy 인지 (§7) — H5 때 확인.
5. 프록시 요청의 과금 방식·유료 플랜에서 26초 한도 변경 여부 (§4·§7) — 쓰지 않으므로 보류.
6. CLI `--alias` draft 주소의 정확한 형태 (§8).
7. `netlify deploy --prod` 전에 draft 를 보는 권장 순서와 `NETLIFY_AUTH_TOKEN`·`NETLIFY_SITE_ID` 사용법 실측 (§2) — T427.
