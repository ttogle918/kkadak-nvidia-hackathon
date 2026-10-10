확인 날짜: 2026-10-10 (T401, Sprint 4 Stage 1a). 공식 페이지는 `curl` 로 받아 읽었고, 서비스키(H2)가 `.env` 에 있어 실호출 8회(유효 키)를 했다. 키 값·요청 URL 은 어디에도 남기지 않았다. 실호출 원문은 저장하지 않고 필드 이름·형태·건수만 적는다.

표기: **확정** = 출처 URL 로 읽었거나 실호출로 본 것. `[확인 필요]` = 받지 못했거나 판단 근거가 없는 것. 실호출로만 본 값은 "실측" 이라고 쓴다.

# T401 — TourAPI KorService2 + 이용 조건

## ① 출처 목록
| # | 출처 | 확인 | 비고 |
|---|---|---|---|
| S1 | https://www.data.go.kr/data/15101578/openapi.do (한국관광공사_국문 관광정보 서비스_GW) | 2026-10-10, HTTP 200 | 페이지에 OpenAPI 명세(Swagger JSON)가 내장되어 있어 오퍼레이션·응답 필드를 읽었다. 페이지 표기 수정일 2026-02-26 |
| S2 | https://www.kogl.or.kr/info/licenseType1.do (공공누리 제1유형) | 2026-10-10, HTTP 200 | |
| S3 | https://www.kogl.or.kr/info/licenseType3.do (공공누리 제3유형) | 2026-10-10, HTTP 200 | |
| S4 | https://api.visitkorea.or.kr (한국관광콘텐츠랩 TourAPI 안내) | 2026-10-10, HTTP 200 | JavaScript 앱 껍데기만 받아짐 — 안내 문서 본문 읽지 못함 `[확인 필요]` |
| S5 | https://api.visitkorea.or.kr/guide/tourapi.do | 2026-10-10, HTTP 404 | 없는 주소 |
| S6 | 실호출 (`https://apis.data.go.kr/B551011/KorService2/...`) | 2026-10-10, 유효 키 8회 + 무효/무키 2회 | 필드 이름·형태·건수만 기록 |
| S7 | 첨부 `개방데이터_활용매뉴얼(국문).zip` (S1 의 참고문서) | **받지 못함** | 로그인 뒤에만 받을 수 있는 것으로 보인다(내려받기 링크가 페이지 HTML 에 없음). → `[확인 필요]` (사람이 받아 올 것) |
| S8 | `https://api.visitkorea.or.kr/#/cmsNoticeDetail?no=207` (법정동코드·신분류코드 안내) | 접근 시도 안 함 | SPA(자바스크립트 렌더링)라 curl 로 본문을 받을 수 없다 `[확인 필요]` |

KorService1 문서는 이번에 읽지 않았다. 아래는 모두 **KorService2** 기준이다. S1 은 `areaCode2`·`categoryCode2` 를 "미사용 기능(삭제예정)" 으로 표시한다.

## ② 엔드포인트
- `https://apis.data.go.kr/B551011/KorService2` — **확정**. S1 내장 명세 `host` 가 `apis.data.go.kr/B551011/KorService2`, `schemes` 는 https·http. 실호출(S6)도 이 주소로 HTTP 200.
- 오퍼레이션 주소 = 엔드포인트 + `/오퍼레이션이름` (예 `/searchFestival2`). S1 명세 `paths` 와 실호출로 확인.
- 참고: S1 의 `oprtinUrl` 은 내부 게이트웨이 주소(`gwapi.visitkorea.or.kr/...`) 로 적혀 있으나 호출은 `apis.data.go.kr` 로 한다(우리는 이 주소만 쓴다).
- 데이터 포맷: JSON+XML (S1 "데이터 포맷"). 한국관광공사 제공, REST.

## ③ 오퍼레이션 표 (S1 명세 `paths` 에서)
15개 오퍼레이션이 있다. 파라미터 표는 S1 에서 **searchFestival2 만** 상세히 읽혔다(`swaggerOprtinVOs`). 나머지는 응답 필드(S1)와 실호출에서 본 파라미터만 적고 그 외는 `[확인 필요]`(활용매뉴얼 S7 필요).

공통 필수: `serviceKey` · `MobileOS`(IOS/AND/WEB/ETC) · `MobileApp`(서비스명). 공통 선택: `numOfRows`(기본 10) · `pageNo`(기본 1) · `_type`(`json` 지정 시 JSON, 기본 XML). (S1, searchFestival2 명세)

| 오퍼레이션 | 용도 | 필수/선택 파라미터 | 응답 `item` 필드 (S1 명세) | 출처 |
|---|---|---|---|---|
| `ldongCode2` | 법정동 코드 조회(시도/시군구) | 실측: `lDongRegnCd`(시도 코드, 시군구 조회 시), `lDongListYn`(N=code/name 형태, Y=lDongRegnCd·lDongRegnNm·lDongSignguCd·lDongSignguNm 형태) | `code` `name` `rnum` (N) / `lDongRegnCd` `lDongRegnNm` `lDongSignguCd` `lDongSignguNm` (Y) | S1, S6 |
| `searchFestival2` | 행사 목록 | 필수 `eventStartDate`(YYYYMMDD) · 선택 `eventEndDate` · `arrange`(A 제목순, C 수정일순, D 생성일순, 이미지 있는 것 우선 O·Q·R) · `lDongRegnCd` · `lDongSignguCd`(시도 필수) · `lclsSystm1~3` · `modifiedtime`. `areaCode`·`sigunguCode`·`cat1~3` 는 "미사용(삭제예정)" | `title` `addr1` `addr2` `zipcode` `contentid` `contenttypeid` `createdtime` `modifiedtime` `eventstartdate` `eventenddate` `progresstype` `festivaltype` `firstimage` `firstimage2` `cpyrhtDivCd` `mapx` `mapy` `mlevel` `tel` `lDongRegnCd` `lDongSignguCd` `lclsSystm1~3` (+ 삭제예정 `areacode` `sigungucode` `cat1~3`) | S1, S6 |
| `areaBasedList2` | 지역 기반 관광정보(관광지 등) | 실측: `contentTypeId`(12=관광지), `lDongRegnCd`, `lDongSignguCd`, `arrange` 로 정상 응답. 그 외 `[확인 필요]` | `title` `addr1` `addr2` `zipcode` `contentid` `contenttypeid` `createdtime` `modifiedtime` `firstimage` `firstimage2` `cpyrhtDivCd` `mapx` `mapy` `mlevel` `tel` `lDongRegnCd` `lDongSignguCd` `lclsSystm1~3` (+ 삭제예정 필드) | S1, S6 |
| `locationBasedList2` | 위치 기반(거리순) | `[확인 필요]` | 위와 같고 `dist` 추가 | S1 |
| `searchKeyword2` | 키워드 검색 | `[확인 필요]` | areaBasedList2 와 같은 필드 | S1 |
| `searchStay2` | 숙박 목록 | `[확인 필요]` (우리는 쓰지 않음) | 같은 계열 | S1 |
| `detailCommon2` | 공통정보(개요·홈페이지 등) | 실측: `contentId` | `contentid` `contenttypeid` `title` `createdtime` `modifiedtime` `tel` `telname` `homepage` `firstimage` `firstimage2` `cpyrhtDivCd` `lDongRegnCd` `lDongSignguCd` `lclsSystm1~3` `addr1` `addr2` `zipcode` `mapx` `mapy` `mlevel` `overview` (+ 삭제예정 `areacode` `sigungucode` `cat1~3`) | S1, S6 |
| `detailIntro2` | 소개정보(행사 장소·기간·주최 등, 타입별 필드) | `[확인 필요]` (contentId·contentTypeId 로 추정, 미실측) | 행사형: `eventstartdate` `eventenddate` `eventplace` `eventhomepage` `playtime` `program` `sponsor1` `sponsor1tel` `usetimefestival` 등 (S1 명세에 타입 혼합 목록) | S1 |
| `detailInfo2` | 반복정보 | `[확인 필요]` (쓰지 않음) | `infoname` `infotext` `serialnum` `fldgubun` 등 | S1 |
| `detailImage2` | 서브 이미지 목록과 **이미지별 공공누리 유형** | 실측: `contentId`, `imageYN=Y`, `numOfRows` | `contentid` `originimgurl` `smallimageurl` `imgname` `serialnum` `cpyrhtDivCd` | S1, S6 |
| `detailPetTour2` | 반려동물 동반 정보 | 쓰지 않음 | — | S1 |
| `lclsSystmCode2` | 분류체계 코드 | `[확인 필요]` | `code` `name` `lclsSystm1~3Cd/Nm` | S1 |
| `areaBasedSyncList2` | 동기화 목록(삭제·변경 반영) | `[확인 필요]` | 위 목록 필드 + `showflag` `oldContentid` | S1 |
| `areaCode2` | 지역코드(**미사용, 삭제 예정**) | — | `code` `name` `rnum` | S1 |
| `categoryCode2` | 서비스 분류(**미사용, 삭제 예정**) | — | `code` `name` `rnum` | S1 |

**페이지 방식**: `numOfRows` + `pageNo`. 응답 `body` 에 `numOfRows` · `pageNo` · `totalCount`(S1, S6 실측). 마지막 페이지 이후·결과 0건일 때의 `items` 형태: 0건 시 `totalCount: 0` 이고 `items` 가 비어 있다(detailImage2 실측, 형태는 빈 값 — 파서는 `item` 키 없음을 처리해야 한다). 결과 1건일 때 `item` 이 객체인지 리스트인지는 detailCommon2 실측 1건에서 `body.items.item` 이 단일 객체/리스트 어느 쪽이든 오는 것으로 가정하고 **둘 다 처리**하는 파서를 쓴다(공공데이터포털 XML→JSON 변환의 일반 관행이지만 이 API 의 보장은 `[확인 필요]`).

## ④ 인증
- 서비스키 파라미터 이름: **`serviceKey`** (S1 명세: `serviceKey` · 필수 · 설명 "인증키(URL-Encode)").
- 인코딩/디코딩 키: 공공데이터포털은 Encoding·Decoding 두 형태의 키를 준다. S1 명세는 쿼리에 **URL 인코딩된 값**을 넣으라고 쓴다. 실측: `.env` 의 키가 이미 `%` 가 든 인코딩 형태이고, 그대로(재인코딩 없이) 쿼리에 넣어 HTTP 200 / `resultCode 0000` 이 나왔다. **이중 인코딩하면 안 된다** — 코드는 `%` 가 있으면 그대로, 없으면 `urllib.parse.quote(safe="")` 로 한 번만 인코딩하는 방식이 안전하다.
- env 변수 이름: `DATA_GO_KR_SERVICE_KEY` (값은 문서·로그·오류 메시지에 남기지 않는다. 키가 쿼리 문자열에 들어가므로 **오류 메시지에 요청 URL 을 싣지 않는다**).
- 활용신청: 개발계정은 "자동승인", 운영계정은 "심의승인" (S1).

## ⑤ 호출 한도
- S1: 비용 무료, 업데이트 주기 실시간. 트래픽 **개발계정 1,000건 / 운영계정은 활용사례 등록 시 신청하면 증가 가능** (단위는 일일로 추정 — 에러코드 22 가 "일일 호출 허용량 초과" 이므로. 단위 명시는 페이지에 없음 `[확인 필요]`).
- 초당 한도: 에러코드 23 `LIMITED_NUMBER_OF_SERVICE_REQUESTS_PER_SECOND_EXCEEDS_ERROR` 가 있으나 **초당 수치는 적혀 있지 않다** `[확인 필요]`. → 수집기는 호출 사이에 지연을 둔다.
- 이번 실호출 사용량: 유효 키 8회(운영/개발 계정 구분 `[확인 필요]`).
- 이용허락범위: S1 "이용허락범위 제한 없음". 단 이것은 **포털 데이터셋 수준 표기**이고 항목별 공공누리 유형(⑨)과는 별개다.

## ⑥ 응답 형식 · 오류
- JSON: `_type=json` 을 쿼리에 넣는다(기본은 XML). 실측 `content-type: application/json`.
- 성공 형태(실측): `{"response": {"header": {"resultCode": "0000", "resultMsg": "OK"}, "body": {"items": {"item": [...]}, "numOfRows", "pageNo", "totalCount"}}}`.
- 게이트웨이 오류 형태(실측, 키 없음/무효 시 HTTP 200 으로 옴): `{"OpenAPI_ServiceResponse": {"cmmMsgHeader": {"errMsg": "<이름>", "returnAuthMsg": "<한글 설명>", "returnReasonCode": "<코드>"}}}`. 즉 **HTTP 상태가 200 이어도 최상위 키가 `response` 가 아니면 오류**다.
  - 실측: 키 없음 → `SERVICE_KEY_IS_NULL` / 코드 `20`. 등록되지 않은 키 → `SERVICE_KEY_IS_NOT_REGISTERED_ERROR` / 코드 `30`.
- S1 오픈API 에러코드 표(이름 / 코드): `APPLICATION_ERROR` 01 · `HTTP_ERROR` 04 · `SERVICETIMEOUT_ERROR` 05 · `INVALID_REQUEST_PARAMETER_ERROR` 10 · `NO_OPENAPI_SERVICE_ERROR` 12 · `SERVICE_KEY_IS_NULL` 20 · `PERMISSION_DENIED` 20 · `LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR` 22 (일일 초과) · `LIMITED_NUMBER_OF_SERVICE_REQUESTS_PER_SECOND_EXCEEDS_ERROR` 23 (초당 초과) · `BLACKLIST_IP_ACCESS_ERROR` 29 · 인증: `SERVICE_ACCESS_DENIED_ERROR` 20 · `SERVICE_KEY_IS_NOT_REGISTERED_ERROR` 30 · `DEADLINE_HAS_EXPIRED_ERROR` 31. (코드 20 은 여러 이름이 공유 — 이름으로 구분.)
- 관광공사 본체 오류(`response.header.resultCode` 가 `0000` 이 아닌 경우)의 코드표: `[확인 필요]` (S7 필요). 명세에 `NO_MANDATORY_REQUEST_PARAMETERS_ERROR` 문구가 보이나 코드는 불명.

## ⑦ 서울 지역 코드·시군구 코드
조회 방법(실측, 확정): `ldongCode2` 법정동 코드 조회.
1. 시도 목록: `ldongCode2?lDongListYn=N&numOfRows=30` → 16건. 서울특별시 = `lDongRegnCd` **`11`**. (참고 실측: 전남광주통합특별시 12, 부산 26, 대구 27, 인천 28, 대전 30, 울산 31, 경기 41, 충북 43, 충남 44, 경북 47, 경남 48, 제주 50, 강원 51, 전북 52, 세종 36110 — 시도 코드가 2자리가 아닌 항목이 있다.)
2. 서울 시군구: `ldongCode2?lDongRegnCd=11&lDongListYn=N&numOfRows=50` → 25건.

**서울 25개 구 `lDongSignguCd` 표 (S6 실측, 2026-10-10).** 서울 열린데이터광장의 `GUNAME`(구 이름)과 이름으로 맞춘다. 행사·관광지 응답의 `lDongSignguCd` 도 같은 코드(실측으로 확인 — 예 `110`, `200`, `140`).

| 코드 | 구 | 코드 | 구 | 코드 | 구 |
|---|---|---|---|---|---|
| 110 | 종로구 | 305 | 강북구 | 560 | 영등포구 |
| 140 | 중구 | 320 | 도봉구 | 590 | 동작구 |
| 170 | 용산구 | 350 | 노원구 | 620 | 관악구 |
| 200 | 성동구 | 380 | 은평구 | 650 | 서초구 |
| 215 | 광진구 | 410 | 서대문구 | 680 | 강남구 |
| 230 | 동대문구 | 440 | 마포구 | 710 | 송파구 |
| 260 | 중랑구 | 470 | 양천구 | 740 | 강동구 |
| 290 | 성북구 | 500 | 강서구 | | |
| | | 530 | 구로구 | | |
| | | 545 | 금천구 | | |

(25개: 110 140 170 200 215 230 260 290 305 320 350 380 410 440 470 500 530 545 560 590 620 650 680 710 740. 코드는 3자리 문자열이며 일부가 10단위가 아닌 215·305·545 이므로 **자릿수·간격을 가정하지 말고 이 표(또는 런타임 조회)를 쓴다**. 코드는 `data/regions/*.json` 에 두는 것이 규칙(지역은 코드에 박지 않음) — 이 표는 T419 가 `data/tourapi_codes.json` 으로 옮긴다.)

삭제 예정인 `areaCode`·`sigunguCode`(구 코드 체계)는 응답에서 빈 값이다(실측) → **쓰지 않는다**.

## ⑧ 행사 기간 · 좌표 · 수정일 · 콘텐츠 id 필드 (searchFestival2 실측 + S1 명세)
| 의미 | 필드 | 형태(실측) | 출처 |
|---|---|---|---|
| 콘텐츠 id | `contentid` | 문자열 숫자(7자리 예) | S1, S6 |
| 콘텐츠 타입 | `contenttypeid` | `15`=행사/공연/축제, `12`=관광지 (실측: 행사 목록 58건 모두 15, 관광지 목록 12) | S6 |
| 행사 시작일 | `eventstartdate` | `YYYYMMDD` 8자리 | S1, S6 |
| 행사 종료일 | `eventenddate` | `YYYYMMDD` 8자리 | S1, S6 |
| 수정일 | `modifiedtime` | `YYYYMMDDHHMMSS` 14자리 (예: 2026-10-07 수정분이 목록에 있음) | S6 |
| 생성일 | `createdtime` | 14자리 | S6 |
| 경도 | `mapx` | 문자열, 소수 10자리 안팎 (예: `127.04…`) — **x=경도(WGS84)** | S1(명세 "WGS84 경도"), S6 |
| 위도 | `mapy` | 문자열 (예: `37.54…`) — **y=위도(WGS84)** | S1, S6 |
| 지도 레벨 | `mlevel` | 문자열 1자리 | S6 |
| 구 코드 | `lDongSignguCd` | 3자리 | S6 |
| 시도 코드 | `lDongRegnCd` | `11` | S6 |
| 행사 진행 구분 | `progresstype`("축제형태": 취소·행사연기 등) · `festivaltype`("진행형태": 상시·온라인·격년제) | 실측: `progresstype` 은 `선택안함` 53건 / 빈 값 5건, `festivaltype` 은 58건 모두 빈 값 | S1, S6 |
| 대표 이미지 | `firstimage`(원본, 약 500x333) · `firstimage2`(썸네일) | URL 문자열 | S1, S6 |
| 공공누리 유형 | `cpyrhtDivCd` | `Type1` / `Type3` (⑨) | S1, S6 |

- 좌표 축 순서: **mapx=경도, mapy=위도** (서울 열린데이터광장의 LAT·LOT 와 이름이 반대로 보이기 쉽다). 실측값이 서울 범위(경도 126~127, 위도 37.5)에 들어와 일치한다. 좌표가 빈 문자열인 행: 실측 58건 중 0건이나, 일반적으로 빈 값 가능성은 `[확인 필요]` → 코드는 빈 값을 건너뛴다.
- 행사 목록 응답은 `overview`(개요)·`homepage`·행사 장소(`eventplace`) 를 **포함하지 않는다**. 장소명은 `addr1`(주소) 이거나 `detailIntro2` 의 `eventplace` 인데 후자는 미실측 `[확인 필요]`.
- 서울 행사 실측 규모(서울 `lDongRegnCd=11`, 2026-10-01~12-31 기간 질의): `totalCount` 58건 — 구별 분포는 종로 15 · 중 11 · 강남 5 · 마포 4 등으로 18개 구에 걸치고 7개 구는 0건. (관광지 종로구 contentTypeId=12: 149건.)

## ⑨ 이용 조건 (공공누리 1·3유형)

### 공식 설명 (S2·S3, 확정)
| | 제1유형 (출처표시) | 제3유형 (출처표시 + 변경금지) |
|---|---|---|
| 공유·이용 | 가능 | 가능 |
| 영리 목적 | 가능 | 가능 |
| 2차적 저작물 작성 · 변경 | **가능** ("2차적 저작물 작성 등 변형하여 이용할 수 있습니다") | **불가** ("공공저작물의 내용을 변형 또는 변경하지 않는 한 … 자유롭게 이용" · "변경금지: 저작물을 변경하거나 2차적 저작물 등으로 작성할 수 없습니다") |
| 의무 | 출처 표시(기관명·작성연도·공공누리 유형·저작물명, 가능하면 하이퍼링크). 공공기관이 후원·특수관계인 것처럼 오인시키는 표시 금지 | 같음 |
| 변경 시 | 저작인격권 존중 (예: 사진 일부를 잘라 의미가 현저히 달라지는 경우, 통계 수치 수정으로 오인 유발하는 경우는 침해 예시) | — |
| 위반 | 이용허락 즉시 종료, 이후 이용은 저작권 침해 | 같음 |
| 면책 | 공공기관은 정확성·지속 제공을 보장하지 않음 | 같음 |
| 별도 허락 | 저작물 보유 기관의 별도 이용허락을 받았다면 공공누리 조건 불필요 | 같음 |

공식 페이지에는 "저장", "재배포", "컨테이너 이미지", "병합", "요약", "정규화" 에 대한 **별도 문구가 없다.** 아래 허용/불허는 위 문구에서 우리가 해석한 것이며 법률 판단이 아니다.

### TourAPI 데이터에서 유형이 어디에 붙는가 (S1 + S6)
- S1 설명: "사진 자료의 경우 … (공공누리 1유형, 3유형 이미지 제공됨)" 이라는 문장이 있어, 공공누리 유형 표기가 **이미지에 대해** 설명되어 있다. 같은 설명이 "저작권 등에 구애 없이 자유롭게 활용 가능한 정보만을 선별하여 제공" 이라고도 한다.
- 항목별 유형 표시 필드: **있다 — `cpyrhtDivCd`.** 설명(S1): "저작권 유형 (Type1:제1유형(출처표시-권장), Type3:제3유형(제1유형+변경금지))". 위치: 목록 `searchFestival2`·`areaBasedList2`·`locationBasedList2`·`searchKeyword2`·`searchStay2`·`areaBasedSyncList2` 의 item, `detailCommon2` 의 item, `detailImage2` 의 이미지별 item (+ `detailInfo2` 는 객실 이미지별 `cpyrhtDivCd1~5`).
- **하지만 필드가 텍스트·좌표·사진 중 무엇에 적용되는지 문서가 명시하지 않는다** `[확인 필요]`. 목록 item 에 하나의 `cpyrhtDivCd` 가 있고 같은 item 에 `firstimage`(대표 이미지)가 있어 대표 이미지에 대한 값일 가능성이 높으나, 텍스트·좌표에 대한 값인지는 문서에 없다. 이는 활용매뉴얼(S7)에서 확인해야 한다.
- 실측 분포: 서울 행사 58건 **58건 모두 `Type3`**. 관광지(종로구) 표본 3건 모두 `Type3`. 한 관광지의 `detailImage2` 5건(전체 7건 중) 표본 모두 `Type3`. `detailCommon2` 표본 1건 `Type3`. 즉 **지금 본 표본에는 `Type1` 이 한 건도 없다.** (표본이 작다: Type1 이 전혀 없는지 여부는 `[확인 필요]`.)

### 허용/불허/미확인 표 (3유형 = `Type3`, 1유형 = `Type1`)
판정 기준: 3유형 = "내용을 변형·변경하지 않는 한 이용" (S3). 1유형 = 변형 가능, 출처 표시 (S2).

| 행위 | 대상 | `Type1` | `Type3` | 근거 |
|---|---|---|---|---|
| 실시간 호출해서 화면에 **원문 그대로** 표시 (출처 표시 포함) | 텍스트(제목·주소·기간) | 허용 | **허용(원문 그대로일 때)** | S2·S3 "공유 및 이용 가능". 단 필드가 텍스트에 적용되는지 `[확인 필요]` |
| 원문 그대로 **저장**(캐시·로컬 파일, 커밋 안 함) | 텍스트·좌표 | 허용 | **미확인** — 저장 자체를 막는 문구는 없으나, "공유 및 이용" 범위에 저장이 포함되는지 문서에 없음 | S3, 문구 없음 |
| **정규화**(필드 이름 바꾸기·형식 변환·날짜 포맷 통일·공백 정리) | 텍스트 | 허용 | **미확인 → 불허로 취급** (내용 변경인지 형식 변환인지 경계가 문서에 없음) | S3 "변형 또는 변경" |
| **병합**(서울 열린데이터광장 행사와 합쳐 한 레코드 만들기, 값 선택) | 텍스트·좌표 | 허용 | **불허로 취급**(원문 대신 섞은 값을 내면 변경) | S3 |
| **요약·번역·재서술**(LLM 등) | 텍스트 | 허용 | **불허** | S3 "2차적 저작물로 작성할 수 없음" |
| **저장소·컨테이너 이미지에 포함해 재배포** | 텍스트·좌표 | 허용(출처 표시) | **미확인 → 불허로 취급** | D26 ⑦ "이용 조건 미확인이면 재배포하지 않는다" |
| **사진 재배포·이미지에 포함** | 이미지 | 허용(출처 표시, 인격권 존중) | **불허로 취급**(자르기·리사이즈도 변경에 해당할 수 있음) | S2·S3의 인격권 예시, S1 사진 사용 제한 |
| 사진을 **원본 URL 그대로 hotlink** 로 표시 | 이미지 | 허용 | **미확인** (재배포인지 단순 링크인지 문서에 없음) | `[확인 필요]` |
| 좌표(`mapx`·`mapy`)를 **지도 핀 위치**로만 사용 | 좌표 | 허용 | **미확인**. 사실 정보(위치)는 저작물 해당성이 낮다는 일반론은 있으나 이 데이터셋에 대한 명시 근거는 없다 | `[확인 필요]` — 사람 판단 필요 |
| 관광공사 사진을 **기업 CI/BI·명예훼손 용도**로 사용 | 이미지 | 금지 | 금지 | S1 |

해석: 공식 문구로 확정된 것은 "1유형 = 변형 가능 + 출처 표시, 3유형 = 변형 금지 + 출처 표시" 뿐이다. **저장·병합·재배포·이미지 포함은 문서에 직접적인 언급이 없고**, 이 데이터는 `cpyrhtDivCd` 가 실측 표본에서 전부 `Type3` 이므로 **이용 조건은 "미확인(안전한 쪽으로 불허)"** 로 둔다. (명세 엣지 케이스: 이용 조건이 판단되지 않으면 ⑨ 표는 "미확인", D26 ⑦ 에 따라 재배포하지 않는다.)

## ⑩ T419 용 필드 목록

### 확정 필드 목록 (T419 가 코드에 써도 되는 이름 — S1 명세와 실호출 모두에서 확인)
- 엔드포인트 요청: `serviceKey` · `MobileOS` · `MobileApp` · `_type` · `numOfRows` · `pageNo`
- 행사 질의 파라미터: `eventStartDate`(필수) · `eventEndDate` · `lDongRegnCd` · `lDongSignguCd` · `arrange` (실호출 정상 응답)
- 코드 조회 오퍼레이션: `ldongCode2` + `lDongRegnCd` + `lDongListYn` (실호출 정상)
- 관광지 오퍼레이션: `areaBasedList2` + `contentTypeId` + `lDongRegnCd` + `lDongSignguCd` (실호출 정상)
- 응답 헤더: `response.header.resultCode`(`0000`=성공) · `resultMsg` · `response.body.items.item` · `totalCount` · `numOfRows` · `pageNo`
- 게이트웨이 오류: `OpenAPI_ServiceResponse.cmmMsgHeader.{errMsg, returnAuthMsg, returnReasonCode}`
- 행사 item: `contentid` · `contenttypeid` · `title` · `addr1` · `addr2` · `eventstartdate` · `eventenddate` · `mapx`(경도) · `mapy`(위도) · `modifiedtime` · `createdtime` · `lDongRegnCd` · `lDongSignguCd` · `progresstype` · `festivaltype` · `cpyrhtDivCd` · `tel` · `firstimage` · `firstimage2`
- 관광지 item: 위에서 `eventstartdate`·`eventenddate`·`progresstype`·`festivaltype` 제외
- 코드 조회 item: `code` · `name` · `rnum`

### 쓰지 말 것 목록
- `areaCode` · `sigunguCode` · `cat1` · `cat2` · `cat3` 요청 파라미터와 응답의 `areacode` · `sigungucode` · `cat1~3` — S1 이 "미사용(삭제예정)" 이고 응답은 실측으로 빈 값.
- `areaCode2` · `categoryCode2` 오퍼레이션 — 삭제 예정.
- 확인 못한 것 전부: `locationBasedList2` · `searchKeyword2` · `lclsSystmCode2` · `areaBasedSyncList2` · `detailIntro2` · `detailInfo2` 의 요청 파라미터(S7 필요), `detailIntro2` 의 `eventplace` 등 타입별 필드.
- `firstimage` · `firstimage2` · `detailImage2` 이미지 URL — 이미지 재배포/표시는 ⑨ 에서 미확인 → 이미지는 수집·저장하지 않는다.
- `overview`(`detailCommon2`) 원문 장문 — 요약·재서술 불가(3유형), 저장도 미확인.
- 값 자체: `.env` 키, 요청 URL, 응답 원문 전체(로그·결과 파일·커밋).
- 파서 가정: HTTP 200 이면 성공이라고 가정하지 않는다(⑥ 오류가 200 으로 온다).

## ⑪ D26 ⑦ 결론 문장 제안
> **TourAPI(한국관광공사 KorService2) 데이터는 공공누리 `cpyrhtDivCd` 가 실측 표본에서 전부 `Type3`(출처표시+변경금지)이고, 그 값이 텍스트·좌표·사진 중 무엇에 적용되는지 공식 문서에 명시가 없으므로 이용 조건을 "미확인(3유형으로 취급)"으로 둔다. 따라서 TourAPI 유래 데이터는 저장소·컨테이너 이미지·공개 응답의 정적 데이터에 넣지 않고, 정규화·병합·요약·재서술도 하지 않는다. 허용하는 것은 (a) 사용자 요청 시점에 실시간으로 호출해 받은 값을 변경 없이 출처(한국관광공사, 공공누리 유형 표기, 원문 링크)와 함께 보여주는 것, (b) 이용 조건을 확인하지 않은 채 공유하지 않는 로컬 `var/` 측정 용도뿐이다. 사진은 수집·저장·재배포하지 않는다. `cpyrhtDivCd` 가 `Type1` 이고 활용매뉴얼 또는 한국관광공사 회신으로 적용 대상이 확인된 항목만, 출처 표시를 붙여 병합·재배포 대상에 올릴 수 있다.**

이 결론이 D25(자동 좌표)에 주는 영향: TourAPI 좌표를 `var/places/auto_places.json` 에 병합하는 것(정규화·병합)은 이 결론에 따라 **지금은 할 수 없다.** 풀려면 사람이 아래 `[확인 필요]` 의 1·2번을 해결해야 한다. T422 는 서울 API 좌표만 만든다(스프린트 §의 "TourAPI 키가 늦어져도" 경로와 동일).

## [확인 필요] 모음
1. **`cpyrhtDivCd` 가 적용되는 대상**(텍스트·좌표·사진 중 무엇) — 활용매뉴얼(S7) 또는 한국관광공사 TourAPI 문의(문의처 [확인 필요 — 출처 URL 미확보], 관광공사 문의는 https://api.visitkorea.or.kr 안내 참조).
2. **3유형 데이터의 저장·정규화·재배포(컨테이너 이미지)·hotlink 허용 여부**와 좌표를 지도 핀으로 쓰는 것의 허용 여부 — 문서에 직접 문구 없음. 사람 판단 또는 기관 회신 필요.
3. 활용매뉴얼 `개방데이터_활용매뉴얼(국문).zip` — 로그인 뒤 내려받기로 추정, 받지 못함.
4. 호출 한도의 단위(일/월)와 초당 한도 수치, 운영계정 전환 절차의 세부.
5. 나머지 오퍼레이션(`locationBasedList2`·`searchKeyword2`·`detailIntro2` 등)의 요청 파라미터와 `detailIntro2` 의 행사 장소 필드 실측.
6. `Type1` 항목이 실제로 존재하는지(표본 외 전체 분포) — 서울 전체 행사·관광지를 페이지 끝까지 보면 알 수 있으나 호출 상한(10회) 때문에 하지 않았다. T408/T419 가 건수만 세는 것을 제안.
7. 목록 응답에서 `item` 이 1건일 때의 형태(객체/리스트)와 빈 결과의 `items` 형태(실측: 0건 시 빈 값).
8. 관광공사 본체 오류(`resultCode` ≠ `0000`)의 코드표.
9. S4 안내 사이트(SPA)의 이용 약관/출처 표시 문구 — curl 로 본문을 받지 못함. 브라우저로 확인 필요.
