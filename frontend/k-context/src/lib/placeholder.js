// 2단계 전 스텁이 쓰는 플레이스홀더. 모듈 이름과 관련 store 값을 실시간으로 보여 준다(배선 확인용).
// 모듈을 채울 때 이 호출은 지우고 실제 렌더로 바꾼다.
import { h, render } from './dom.js';

/**
 * @param {HTMLElement} root
 * @param {{store, t}} ctx
 * @param {string} name 모듈 이름(module.<name> 사전 키가 있어야 한다)
 * @param {string[]} watchKeys 화면에 echo 할 store 키
 * @returns {{destroy(): void}}
 */
export function mountPlaceholder(root, ctx, name, watchKeys = []) {
  const { store, t } = ctx;
  const draw = () => {
    const s = store.getState();
    const echo = watchKeys.map((k) => `${k}=${JSON.stringify(s[k])}`).join('  ');
    render(
      root,
      h('div', { class: 'placeholder', dataset: { module: name } },
        h('strong', { class: 'placeholder__name' }, t(`module.${name}`)),
        h('span', { class: 'placeholder__note' }, t('module.placeholder', { name })),
        echo ? h('code', { class: 'placeholder__echo' }, echo) : null),
    );
  };
  draw();
  const off = store.subscribe(draw);
  return {
    destroy() {
      off();
      root.replaceChildren();
    },
  };
}
