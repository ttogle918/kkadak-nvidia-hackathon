"""K-Context 평가 패키지. 입구는 ``uv run python eval/kc.py <하위 명령>`` 하나다.

모듈은 ``from kc_eval import match`` 처럼 가져온다(``eval/`` 이 sys.path 에 있어야 한다 — kc.py·tests/eval/conftest.py).
이 파일은 모듈을 미리 가져오지 않는다(모듈마다 무거운 의존성이 달라 지연 import).
"""

__all__: list[str] = []
