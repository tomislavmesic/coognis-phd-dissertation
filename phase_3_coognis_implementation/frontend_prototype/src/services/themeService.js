const STORAGE_KEY = 'theme';

export function getStoredTheme() {
  return window.localStorage.getItem(STORAGE_KEY);
}

export function setStoredTheme(theme) {
  window.localStorage.setItem(STORAGE_KEY, theme);
}

export function getPreferredTheme() {
  const storedTheme = getStoredTheme();
  if (storedTheme) {
    return storedTheme;
  }

  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function resolveTheme(theme) {
  if (theme === 'auto') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  return theme;
}

export function applyTheme(theme) {
  document.documentElement.setAttribute('data-bs-theme', resolveTheme(theme));
}

export function setTheme(theme) {
  setStoredTheme(theme);
  applyTheme(theme);
}

export function initTheme() {
  applyTheme(getPreferredTheme());

  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    const storedTheme = getStoredTheme();
    if (storedTheme !== 'light' && storedTheme !== 'dark') {
      applyTheme('auto');
    }
  });
}
