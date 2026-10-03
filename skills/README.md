# skills/

이 프로젝트가 직접 만드는 에이전트 스킬(SKILL.md 표준). 스킬 하나당 디렉터리 하나.

```
skills/<name>/
  SKILL.md        # frontmatter(name, description) + 지침
  evals/evals.json
  skill-card.md   # /skill-card-generator 로 생성
```

NVIDIA 카탈로그 스킬은 `.claude/skills/` 에 있다.
NVIDIA 공식 카탈로그 전체(398종)가 `.claude/skills/` 에 설치되어 있다(`skills-lock.json`). 비공식 출처 스킬만 SkillSpector 로 먼저 스캔한다(MaintQ `docs/hackathon/day2.md` §8).
