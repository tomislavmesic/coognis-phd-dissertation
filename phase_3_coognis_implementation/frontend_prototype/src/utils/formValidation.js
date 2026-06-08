function isBlank(value) {
  return value === null || value === undefined || String(value).trim() === '';
}

function required(message) {
  return (value) => {
    if (typeof value === 'boolean') {
      return value ? '' : message;
    }

    return isBlank(value) ? message : '';
  };
}

function email(message) {
  return (value) => {
    if (isBlank(value)) {
      return '';
    }

    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value).trim()) ? '' : message;
  };
}

function minLength(length, message) {
  return (value) => {
    if (isBlank(value)) {
      return '';
    }

    return String(value).length >= length ? '' : message;
  };
}

function oneOf(options, message) {
  return (value) => (options.includes(value) ? '' : message);
}

function matchesField(otherField, message) {
  return (value, form) => {
    if (isBlank(value)) {
      return '';
    }

    return value === form[otherField] ? '' : message;
  };
}

function requiredWhen(predicate, message) {
  return (value, form) => {
    if (!predicate(form)) {
      return '';
    }

    return isBlank(value) ? message : '';
  };
}

function validateFieldValue(fieldName, form, rules) {
  const validators = rules[fieldName] || [];

  for (const validator of validators) {
    const error = validator(form[fieldName], form);

    if (error) {
      return error;
    }
  }

  return '';
}

function validateField(fieldName, form, errors, rules) {
  return {
    ...errors,
    [fieldName]: validateFieldValue(fieldName, form, rules),
  };
}

function validateFields(fieldNames, form, rules) {
  return fieldNames.reduce((nextErrors, fieldName) => {
    return {
      ...nextErrors,
      [fieldName]: validateFieldValue(fieldName, form, rules),
    };
  }, {});
}

function hasFieldError(errors, fieldName) {
  return Boolean(errors[fieldName]);
}

function getServerErrorMessage(error, fallbackMessage) {
  return error?.message || fallbackMessage;
}

export {
  email,
  getServerErrorMessage,
  hasFieldError,
  matchesField,
  minLength,
  oneOf,
  required,
  requiredWhen,
  validateField,
  validateFields,
};
