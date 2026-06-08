import {
  MOCK_2FA_CODE,
  MOCK_AUTH_ENABLED,
  clearMockAuth,
  clearMockPendingTwoFactor,
  createMockUser,
  delay,
  getMockCurrentUser,
  getMockPendingTwoFactor,
  resolveMockDashboardPath,
  resolveMockRole,
  setMockCurrentUser,
  setMockPendingTwoFactor,
  shouldRequireTwoFactor,
} from '@/utils/mockAuth';
import { APP_PUBLIC_NAME } from '@/config/branding';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/+$/, '');

function buildUrl(path) {
  if (!path.startsWith('/')) {
    return `${API_BASE_URL}/${path}`;
  }

  return `${API_BASE_URL}${path}`;
}

function createErrorObject({
  status = 0,
  code = 'REQUEST_FAILED',
  message = 'Request failed.',
  details = null,
}) {
  return {
    status,
    code,
    message,
    details,
  };
}

function createSuccessResponse(data) {
  return {
    success: true,
    data,
    error: null,
  };
}

function createMockRecoveryCodes() {
  return Array.from({ length: 8 }, (_, index) => `MOCK-${String(index + 1).padStart(4, '0')}`);
}

async function parseResponse(response) {
  const contentType = response.headers.get('content-type') || '';

  if (contentType.includes('application/json')) {
    return response.json();
  }

  const text = await response.text();

  return text ? { message: text } : null;
}

function extractErrorMessage(payload, status) {
  if (typeof payload?.message === 'string' && payload.message) {
    return payload.message;
  }

  if (typeof payload?.detail === 'string' && payload.detail) {
    return payload.detail;
  }

  if (typeof payload?.detail?.message === 'string' && payload.detail.message) {
    return payload.detail.message;
  }

  if (Array.isArray(payload?.detail) && payload.detail.length > 0) {
    return payload.detail
      .map((item) => item?.msg || item?.message)
      .filter(Boolean)
      .join(' ');
  }

  return status ? 'The request could not be completed.' : 'Unable to reach the API service.';
}

async function request(path, options = {}) {
  try {
    const response = await fetch(buildUrl(path), {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...(options.headers || {}),
      },
      ...options,
    });

    const payload = await parseResponse(response);

    if (!response.ok) {
      return {
        success: false,
        error: createErrorObject({
          status: response.status,
          code: payload?.code || `HTTP_${response.status}`,
          message: extractErrorMessage(payload, response.status),
          details: payload?.details || payload,
        }),
      };
    }

    return {
      success: true,
      data: payload,
      error: null,
    };
  } catch (error) {
    return {
      success: false,
      error: createErrorObject({
        status: 0,
        code: 'NETWORK_ERROR',
        message: 'Unable to reach the API service.',
        details: {
          reason: error instanceof Error ? error.message : 'Unknown network error',
        },
      }),
    };
  }
}

async function registerUser(payload) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    if (!payload?.ai_profiling_consent || !payload?.gdpr_consent) {
      return {
        success: false,
        error: createErrorObject({
          status: 422,
          code: 'CONSENT_REQUIRED',
          message: 'Both required consent checkboxes must be accepted.',
        }),
      };
    }

    return createSuccessResponse({
      registration_status: 'pending_approval',
      message: 'Mock registration submitted successfully.',
    });
  }

  return request('/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

async function login(payload) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    if (!payload?.email || !payload?.password) {
      return {
        success: false,
        error: createErrorObject({
          status: 422,
          code: 'INVALID_CREDENTIALS',
          message: 'Email and password are required.',
        }),
      };
    }

    const role = resolveMockRole(payload.email);
    const user = createMockUser({
      email: payload.email,
      role,
    });

    if (shouldRequireTwoFactor(payload.email)) {
      const challenge = {
        challenge_id: `mock-2fa-${role}`,
        email: payload.email,
        role,
        user,
        redirect_to: resolveMockDashboardPath(role),
        remember_device_days: 14,
      };

      setMockPendingTwoFactor(challenge);

      return createSuccessResponse({
        requires_2fa: true,
        ...challenge,
        message: `Mock 2FA required. Use code ${MOCK_2FA_CODE}.`,
      });
    }

    setMockCurrentUser(user);
    clearMockPendingTwoFactor();

    return createSuccessResponse({
      user,
      message: 'Mock login successful.',
    });
  }

  return request('/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

async function logout() {
  if (MOCK_AUTH_ENABLED) {
    await delay(100);
    clearMockAuth();

    return createSuccessResponse({
      message: 'Mock logout successful.',
    });
  }

  return request('/auth/logout', {
    method: 'POST',
  });
}

async function verifyTwoFactor(payload) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    const pendingChallenge = getMockPendingTwoFactor();

    if (!pendingChallenge) {
      return {
        success: false,
        error: createErrorObject({
          status: 400,
          code: 'TWO_FACTOR_NOT_STARTED',
          message: 'No pending two-factor challenge was found.',
        }),
      };
    }

    if (payload?.verification_code !== MOCK_2FA_CODE) {
      return {
        success: false,
        error: createErrorObject({
          status: 422,
          code: 'INVALID_VERIFICATION_CODE',
          message: `Invalid verification code. Use ${MOCK_2FA_CODE}.`,
        }),
      };
    }

    setMockCurrentUser(pendingChallenge.user);
    clearMockPendingTwoFactor();

    return createSuccessResponse({
      user: pendingChallenge.user,
      message: 'Mock two-factor verification successful.',
    });
  }

  return request('/auth/2fa/verify', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

async function setupTwoFactor(challengeId) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    const pendingChallenge = getMockPendingTwoFactor();
    if (!pendingChallenge || pendingChallenge.challengeId !== challengeId) {
      return {
        success: false,
        error: createErrorObject({
          status: 400,
          code: 'TWO_FACTOR_CHALLENGE_EXPIRED',
          message: 'Two-factor challenge is invalid or has expired.',
        }),
      };
    }

    const secret = 'MOCKAUTHCODE12345';
    return createSuccessResponse({
      challenge_id: challengeId,
      secret,
      provisioning_uri: `otpauth://totp/${APP_PUBLIC_NAME}:${encodeURIComponent(pendingChallenge.email || 'mock@example.com')}?secret=${secret}&issuer=${encodeURIComponent(APP_PUBLIC_NAME)}`,
      account_name: pendingChallenge.email || 'mock@example.com',
      issuer: APP_PUBLIC_NAME,
      method: 'totp',
      message: 'Mock authenticator setup details generated.',
    });
  }

  const encodedChallenge = encodeURIComponent(challengeId || '');
  return request(`/auth/2fa/setup?challenge_id=${encodedChallenge}`, {
    method: 'POST',
  });
}

async function confirmTwoFactor(payload) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    const pendingChallenge = getMockPendingTwoFactor();
    if (!pendingChallenge || pendingChallenge.challengeId !== payload?.challenge_id) {
      return {
        success: false,
        error: createErrorObject({
          status: 400,
          code: 'TWO_FACTOR_CHALLENGE_EXPIRED',
          message: 'Two-factor challenge is invalid or has expired.',
        }),
      };
    }

    if (payload?.verification_code !== MOCK_2FA_CODE) {
      return {
        success: false,
        error: createErrorObject({
          status: 422,
          code: 'INVALID_VERIFICATION_CODE',
          message: `Invalid verification code. Use ${MOCK_2FA_CODE}.`,
        }),
      };
    }

    return createSuccessResponse({
      user: {
        ...pendingChallenge.user,
        two_factor_enabled: true,
        two_factor_method: 'totp',
        recovery_codes_remaining: 8,
      },
      redirect_to: pendingChallenge.redirectTo,
      recovery_codes: createMockRecoveryCodes(),
      message: 'Mock two-factor authentication enabled.',
    });
  }

  return request('/auth/2fa/confirm', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

async function regenerateRecoveryCodes() {
  if (MOCK_AUTH_ENABLED) {
    await delay();
    const recoveryCodes = createMockRecoveryCodes();
    return createSuccessResponse({
      recovery_codes: recoveryCodes,
      recovery_codes_remaining: recoveryCodes.length,
      message: 'Mock recovery codes regenerated successfully.',
    });
  }

  return request('/auth/2fa/recovery-codes/regenerate', {
    method: 'POST',
  });
}

async function requestPasswordReset(payload) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    if (!payload?.email) {
      return {
        success: false,
        error: createErrorObject({
          status: 422,
          code: 'EMAIL_REQUIRED',
          message: 'Email is required to request a password reset.',
        }),
      };
    }

    return createSuccessResponse({
      message: 'Mock password reset request submitted.',
    });
  }

  return request('/auth/password-reset/request', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

async function confirmPasswordReset(payload) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    if (!payload?.token) {
      return {
        success: false,
        error: createErrorObject({
          status: 422,
          code: 'TOKEN_REQUIRED',
          message: 'Password reset token is required.',
        }),
      };
    }

    if (payload?.password !== payload?.password_confirmation) {
      return {
        success: false,
        error: createErrorObject({
          status: 422,
          code: 'VALIDATION_ERROR',
          message: 'Password confirmation must match the password.',
        }),
      };
    }

    return createSuccessResponse({
      message: 'Mock password reset completed successfully.',
    });
  }

  return request('/auth/password-reset/confirm', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

async function fetchCurrentUser() {
  if (MOCK_AUTH_ENABLED) {
    await delay(100);

    const currentUser = getMockCurrentUser();

    if (!currentUser) {
      return {
        success: false,
        error: createErrorObject({
          status: 401,
          code: 'NOT_AUTHENTICATED',
          message: 'No mock user session is active.',
        }),
      };
    }

    return createSuccessResponse({
      user: currentUser,
    });
  }

  return request('/auth/me', {
    method: 'GET',
  });
}

async function updateCurrentUserSettings(payload) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    const currentUser = getMockCurrentUser();
    if (!currentUser) {
      return {
        success: false,
        error: createErrorObject({
          status: 401,
          code: 'NOT_AUTHENTICATED',
          message: 'No mock user session is active.',
        }),
      };
    }

    const updatedUser = {
      ...currentUser,
      ...payload,
    };
    setMockCurrentUser(updatedUser);

    return createSuccessResponse({
      user: updatedUser,
      message: 'Mock user settings updated successfully.',
    });
  }

  return request('/auth/me', {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

async function changePassword(payload) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    const currentUser = getMockCurrentUser();
    if (!currentUser) {
      return {
        success: false,
        error: createErrorObject({
          status: 401,
          code: 'NOT_AUTHENTICATED',
          message: 'No mock user session is active.',
        }),
      };
    }

    if (!payload?.current_password) {
      return {
        success: false,
        error: createErrorObject({
          status: 401,
          code: 'INVALID_CURRENT_PASSWORD',
          message: 'Current password is incorrect.',
        }),
      };
    }

    if (payload?.new_password !== payload?.new_password_confirmation) {
      return {
        success: false,
        error: createErrorObject({
          status: 422,
          code: 'VALIDATION_ERROR',
          message: 'Password confirmation must match the new password.',
        }),
      };
    }

    return createSuccessResponse({
      message: 'Mock password changed successfully.',
    });
  }

  return request('/auth/password/change', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export default {
  registerUser,
  login,
  logout,
  setupTwoFactor,
  confirmTwoFactor,
  verifyTwoFactor,
  regenerateRecoveryCodes,
  requestPasswordReset,
  confirmPasswordReset,
  fetchCurrentUser,
  updateCurrentUserSettings,
  changePassword,
};
