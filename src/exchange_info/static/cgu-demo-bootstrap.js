/* Loaded before shared scripts: the original platform sees an isolated storage namespace. */
(() => {
  'use strict';
  const prefix = 'uniway-cgu-platform:';
  for (const name of ['localStorage', 'sessionStorage']) {
    let raw;
    const memory = new Map();
    try {
      raw = window[name];
      raw.setItem(prefix + 'probe', '1'); raw.removeItem(prefix + 'probe');
    } catch (_) {
      window.cguDemoStorageLimited = true;
      raw = {getItem: key => memory.get(key) ?? null, setItem: (key, value) => memory.set(key, String(value)),
        removeItem: key => memory.delete(key), key: index => [...memory.keys()][index] ?? null,
        get length() { return memory.size; }};
    }
    const keys = () => Array.from({length: raw.length}, (_, i) => raw.key(i)).filter(key => key?.startsWith(prefix));
    Object.defineProperty(window, name, {value: {
      getItem: key => raw.getItem(prefix + key), setItem: (key, value) => raw.setItem(prefix + key, value),
      removeItem: key => raw.removeItem(prefix + key), clear: () => keys().forEach(key => raw.removeItem(key)),
      key: index => keys()[index]?.slice(prefix.length) ?? null, get length() { return keys().length; },
    }});
  }
  window.localStorage.setItem('exchange-guide-home-school', '長庚大學');
  const url = new URL(location.href);
  url.searchParams.set('home', '長庚大學'); url.searchParams.delete('school');
  history.replaceState(null, '', url);
  window.cguDemoStorageIsolated = true;
})();
