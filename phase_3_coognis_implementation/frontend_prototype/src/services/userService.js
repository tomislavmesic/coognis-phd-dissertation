import { MOCK_AUTH_ENABLED, delay } from '@/utils/mockAuth';

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

async function fetchRecommendedExpert() {
  if (MOCK_AUTH_ENABLED) {
    await delay(150);

    return {
      success: true,
      data: {
        item: {
          expert_id: 1,
          name: 'Dr. Petra Novak',
          email: 'petra@example.com',
          is_active: true,
          is_contactable: true,
          domain_codes: ['adaptive-systems', 'expert-guidance'],
          total_score: 0.92,
          reason: 'Recommended using current mock compatibility and expert availability.',
          compatibility_note: 'Mock matching uses a fixed expert recommendation for local demos.',
        },
        profiling_used: true,
        target_mbti: 'INTJ',
        profile_source: 'synapse_inferred',
        message: 'Mock recommended expert loaded successfully.',
      },
      error: null,
    };
  }

  return request('/user/dashboard/recommended-expert', {
    method: 'GET',
  });
}

export default {
  fetchRecommendedExpert,
};
