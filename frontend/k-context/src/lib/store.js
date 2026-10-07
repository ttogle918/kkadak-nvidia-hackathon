// 최소 상태 저장소. 상태는 불변으로 갱신한다(새 객체를 만들고 최상위는 freeze).
// 모듈끼리는 서로 import 하지 않고 이 store 와 api 로만 소통한다.

/**
 * @template S
 * @param {S} initial 초기 상태(평범한 객체)
 */
export function createStore(initial) {
  let state = Object.freeze({ ...initial });
  const listeners = new Set();

  /** 현재 상태(읽기 전용 스냅샷). 직접 수정하지 말고 setState 를 쓴다. */
  function getState() {
    return state;
  }

  /**
   * 상태 갱신. patch 는 객체(얕은 병합) 또는 (state)=>patch 함수.
   * 바뀐 키가 하나도 없으면(Object.is 기준) 알리지 않는다.
   * 중첩 객체/배열은 호출자가 새 참조로 만들어 넣는다(예: messages: [...s.messages, m]).
   */
  function setState(patch) {
    const part = typeof patch === 'function' ? patch(state) : patch;
    if (!part || typeof part !== 'object') return state;
    let changed = false;
    for (const k of Object.keys(part)) {
      if (!Object.is(state[k], part[k])) {
        changed = true;
        break;
      }
    }
    if (!changed) return state;
    const prev = state;
    state = Object.freeze({ ...state, ...part });
    for (const fn of [...listeners]) fn(state, prev);
    return state;
  }

  /** 변경 구독. fn(state, prev). 반환값은 구독 해제 함수. */
  function subscribe(fn) {
    listeners.add(fn);
    return () => listeners.delete(fn);
  }

  /**
   * 파생값 구독. selector(state) 결과가 바뀔 때만 listener(value, prevValue) 호출.
   * fire=true 면 등록 즉시 한 번 호출한다. 반환값은 구독 해제 함수.
   */
  function select(selector, listener, { equals = Object.is, fire = false } = {}) {
    let cur = selector(state);
    if (fire) listener(cur, undefined);
    return subscribe((s) => {
      const next = selector(s);
      if (!equals(cur, next)) {
        const prev = cur;
        cur = next;
        listener(next, prev);
      }
    });
  }

  return { getState, setState, subscribe, select };
}
