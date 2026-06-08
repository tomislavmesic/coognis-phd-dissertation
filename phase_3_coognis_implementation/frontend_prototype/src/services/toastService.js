import { reactive } from 'vue';

const state = reactive({
  items: [],
});

let nextToastId = 1;

function normalizeVariant(variant) {
  const value = String(variant || 'info').toLowerCase();
  if (value === 'alert') {
    return 'danger';
  }
  if (['success', 'info', 'warning', 'danger'].includes(value)) {
    return value;
  }
  return 'info';
}

function defaultDelay(variant) {
  if (variant === 'danger') {
    return 8000;
  }
  return 4000;
}

function defaultTitle(variant) {
  if (variant === 'success') return 'Success';
  if (variant === 'warning') return 'Warning';
  if (variant === 'danger') return 'Alert';
  return 'Info';
}

function show(options = {}) {
  const variant = normalizeVariant(options.variant);
  const message = String(options.message || '').trim();
  if (!message) {
    return null;
  }

  const toast = {
    id: nextToastId++,
    title: String(options.title || defaultTitle(variant)),
    message,
    variant,
    autohide: typeof options.autohide === 'boolean' ? options.autohide : variant !== 'danger',
    delay: Number.isFinite(Number(options.delay)) ? Number(options.delay) : defaultDelay(variant),
  };

  state.items.push(toast);
  return toast.id;
}

function remove(id) {
  const index = state.items.findIndex((item) => item.id === id);
  if (index !== -1) {
    state.items.splice(index, 1);
  }
}

function clear() {
  state.items.splice(0, state.items.length);
}

function success(message, options = {}) {
  return show({ ...options, variant: 'success', message });
}

function info(message, options = {}) {
  return show({ ...options, variant: 'info', message });
}

function warning(message, options = {}) {
  return show({ ...options, variant: 'warning', message });
}

function error(message, options = {}) {
  return show({ ...options, variant: 'danger', message });
}

export default {
  state,
  show,
  remove,
  clear,
  success,
  info,
  warning,
  error,
};
