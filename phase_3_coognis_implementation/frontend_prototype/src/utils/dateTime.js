const dateFormatter = new Intl.DateTimeFormat(undefined, {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
});

const timeFormatter = new Intl.DateTimeFormat(undefined, {
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
});

export function asDate(value) {
  if (!value) {
    return null;
  }

  const parsed = value instanceof Date ? value : new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

export function formatDate(value) {
  const parsed = asDate(value);
  return parsed ? dateFormatter.format(parsed) : '—';
}

export function formatTime(value) {
  const parsed = asDate(value);
  return parsed ? timeFormatter.format(parsed) : '—';
}

export function formatDateTime(value) {
  const parsed = asDate(value);
  return parsed ? `${formatDate(parsed)} ${formatTime(parsed)}` : '—';
}
