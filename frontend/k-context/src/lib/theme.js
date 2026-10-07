// store.theme 를 <html data-theme> 에 반영한다. 'auto' 는 속성을 빼서 prefers-color-scheme 이 정하게 한다.
export function bindDocumentTheme(store, doc = globalThis.document) {
  return store.select(
    (s) => s.theme,
    (theme) => {
      const el = doc?.documentElement;
      if (!el) return;
      if (theme === 'light' || theme === 'dark') el.setAttribute('data-theme', theme);
      else el.removeAttribute('data-theme');
    },
    { fire: true },
  );
}
