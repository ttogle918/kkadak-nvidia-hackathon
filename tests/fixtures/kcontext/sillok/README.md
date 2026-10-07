# 실록 발췌 fixture (T204)
`docs/spikes/sillok.md` 참고. 세 파일 모두 국사편찬위원회 조선왕조실록 정보_실록원문(공공누리 1유형, 출처표시) 원본에서 기사 1건씩을 기사 요소는 **무수정**으로, 상위 level(`level2`~`level4`)은 그 기사에 이르는 가지만 남기고 뽑았다. 첫 줄 주석에 출처·내려받은 날짜·이용허락이 있다. 합성 XML 은 없다.

| 파일 | 원본 | 기사 ID | 용도 |
|---|---|---|---|
| `sample.xml` | `2nd_waa_101.xml` | `waa_10107017_001` | 태조 즉위(壽昌宮). 긴 본문·색인 다수 |
| `sample_jongno.xml` | `2nd_wca_111.xml` | `wca_11112017_001` | 종로 지역 키워드 `鍾樓` |
| `sample_euljiro.xml` | `2nd_wca_107.xml` | `wca_10705009_002` | 중구 지역 키워드 `崇禮門` |

- 파일마다 `<!DOCTYPE level2 SYSTEM "history.dtd">` 가 그대로 있다. `history.dtd` 는 포함하지 않는다(원본은 gitignore). 파서는 DTD 를 가져오지 않아야 한다.
- 원본 전체는 `domains/kcontext/data/raw/sillok/` 에 두며 git 에 올리지 않는다.
- 명세(T204)는 `sample.xml` 하나였으나 원본이 파일마다 루트 하나라 기사 3건을 파일 3개로 나눴다. T209 의 fixture 경로(`sample.xml` 만 지정)는 디렉터리 전체(`--src tests/fixtures/kcontext/sillok`)로 읽으면 맞는다.
