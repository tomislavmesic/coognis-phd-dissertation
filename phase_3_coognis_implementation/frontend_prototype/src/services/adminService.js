import { MOCK_AUTH_ENABLED, delay } from '@/utils/mockAuth';
import authStore from '@/store/authStore';

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

async function parseResponse(response) {
  const contentType = response.headers.get('content-type') || '';

  if (contentType.includes('application/json')) {
    return response.json();
  }

  const text = await response.text();

  return text ? { message: text } : null;
}

function extractErrorMessage(payload, status) {
  if (Array.isArray(payload?.detail) && payload.detail.length) {
    return payload.detail
      .map((item) => item?.msg || item?.message || 'Validation error')
      .join(' ');
  }

  if (typeof payload?.message === 'string' && payload.message) {
    return payload.message;
  }

  if (typeof payload?.detail === 'string' && payload.detail) {
    return payload.detail;
  }

  if (typeof payload?.detail?.message === 'string' && payload.detail.message) {
    return payload.detail.message;
  }

  return status ? 'The request could not be completed.' : 'Unable to reach the API service.';
}

async function request(path, options = {}) {
  try {
    const adminRole = authStore.state.currentUser?.role;
    const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;
    const response = await fetch(buildUrl(path), {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        ...(adminRole ? { 'X-Admin-Role': adminRole } : {}),
        ...(!isFormData && options.body ? { 'Content-Type': 'application/json' } : {}),
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

async function approveRegistration(registrationId) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      registration_id: registrationId,
      status: 'approved',
      credentials_email_triggered: true,
    });
  }

  return request(`/admin/registrations/${registrationId}/approve`, {
    method: 'POST',
    body: JSON.stringify({
      send_credentials_email: true,
    }),
  });
}

async function fetchDashboardSummary() {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      pending_registrations: [
        {
          id: 1,
          name: 'Marta Kovac',
          role: 'User',
          submitted_at: new Date().toISOString(),
          consents: 'AI + GDPR',
        },
      ],
      system_stats: [
        { label: 'Pending approvals', value: 1 },
        { label: 'Active users', value: 10 },
        { label: 'Active experts', value: 3 },
        { label: 'Open deletion requests', value: 2 },
      ],
      active_users: [
        { id: 1, name: 'Ana Markovic', email: 'ana@example.com', status: 'Active', two_factor: 'Enabled' },
      ],
      active_experts: [
        { id: 1, name: 'Tom Expert', email: 'tom@example.com', availability: 'Available', two_factor: 'Enabled' },
      ],
      consent_requests: [
        { id: 1, type: 'Account Deletion', submitted_by: 'Lana Basic', status: 'Pending' },
      ],
    });
  }

  return request('/admin/dashboard', {
    method: 'GET',
  });
}

async function bulkUpdateTwoFactor(payload) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      role: payload.role,
      enabled: payload.enabled,
      affected_count: payload.role === 'user' ? 10 : 3,
      message: `Two-factor authentication ${payload.enabled ? 'enabled' : 'disabled'} for all ${payload.role} accounts.`,
    });
  }

  return request('/admin/two-factor/bulk', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

async function fetchPendingRegistrations() {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse([
      {
        id: 'reg-001',
        full_name: 'Marta Kovac',
        email: 'marta@example.com',
        requested_role: 'user',
        ai_profiling_consent: true,
        gdpr_consent: true,
        created_at: '2026-03-20T09:12:00Z',
      },
      {
        id: 'reg-002',
        full_name: 'Ivan Expert',
        email: 'ivan.expert@example.com',
        requested_role: 'expert',
        ai_profiling_consent: true,
        gdpr_consent: true,
        created_at: '2026-03-20T08:47:00Z',
      },
    ]);
  }

  return request('/admin/registrations', {
    method: 'GET',
  });
}

async function rejectRegistration(registrationId) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      registration_id: registrationId,
      status: 'rejected',
    });
  }

  return request(`/admin/registrations/${registrationId}/reject`, {
    method: 'POST',
  });
}

async function createUser(payload) {
  const normalizedPayload = {
    ...payload,
    temporary_password: payload.auto_generate_password ? null : payload.temporary_password,
  };

  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      user_id: `created-${normalizedPayload.role}-${Date.now()}`,
      status: 'created',
      credentials_email_triggered: true,
      ...normalizedPayload,
    });
  }

  return request('/admin/users', {
    method: 'POST',
    body: JSON.stringify({
      ...normalizedPayload,
      send_credentials_email: true,
    }),
  });
}

async function fetchUsers() {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse([
      {
        id: 1,
        name: 'Ana Markovic',
        first_name: 'Ana',
        last_name: 'Markovic',
        email: 'ana@example.com',
        role: 'user',
        is_active: true,
        registration_status: 'approved',
        two_factor_enabled: true,
        ai_profiling_consent: true,
        gdpr_consent: true,
        can_access_chat_debug_panels: true,
        profiling_opt_out_requested: false,
        account_deletion_requested: false,
        manual_mbti: null,
        inferred_mbti: 'INFJ',
        effective_mbti: 'INFJ',
        profile_confidence: 0.82,
        profile_interaction_count: 6,
      },
      {
        id: 2,
        name: 'Tom Expert',
        first_name: 'Tom',
        last_name: 'Expert',
        email: 'tom.expert@example.com',
        role: 'expert',
        is_active: true,
        registration_status: 'approved',
        two_factor_enabled: true,
        ai_profiling_consent: true,
        gdpr_consent: true,
        can_access_chat_debug_panels: false,
        profiling_opt_out_requested: false,
        account_deletion_requested: false,
        manual_mbti: 'ENTJ',
        inferred_mbti: 'ENFJ',
        effective_mbti: 'ENTJ',
        profile_confidence: 0.77,
        profile_interaction_count: 12,
      },
      {
        id: 3,
        name: 'Admin Demo',
        first_name: 'Admin',
        last_name: 'Demo',
        email: 'admin@example.com',
        role: 'admin',
        is_active: true,
        registration_status: 'approved',
        two_factor_enabled: true,
        ai_profiling_consent: false,
        gdpr_consent: true,
        can_access_chat_debug_panels: false,
        profiling_opt_out_requested: false,
        account_deletion_requested: false,
        manual_mbti: null,
        inferred_mbti: null,
        effective_mbti: null,
        profile_confidence: null,
        profile_interaction_count: 0,
      },
    ]);
  }

  return request('/admin/users', {
    method: 'GET',
  });
}

async function viewUser(userId) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    const items = (await fetchUsers()).data || [];
    const match = items.find((item) => item.id === userId) || items[0];
    return createSuccessResponse(match);
  }

  return request(`/admin/users/${userId}`, {
    method: 'GET',
  });
}

async function editUser(userId, payload) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      id: userId,
      ...payload,
    });
  }

  return request(`/admin/users/${userId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

async function deactivateUser(userId) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      user_id: userId,
      status: 'deactivated',
    });
  }

  return request(`/admin/users/${userId}`, {
    method: 'PUT',
    body: JSON.stringify({
      is_active: false,
    }),
  });
}

async function resetUserPassword(userId) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      user_id: userId,
      action: 'password_reset',
      credentials_email_triggered: false,
      generated_temporary_password: 'TempReset123',
    });
  }

  return request(`/admin/users/${userId}/reset-password`, {
    method: 'POST',
  });
}

async function resendUserCredentials(userId) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      user_id: userId,
      action: 'credentials_reissued',
      credentials_email_triggered: true,
      generated_temporary_password: null,
    });
  }

  return request(`/admin/users/${userId}/resend-credentials`, {
    method: 'POST',
  });
}

async function resetUserTwoFactor(userId) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      user_id: userId,
      action: 'two_factor_reset',
      credentials_email_triggered: false,
      generated_temporary_password: null,
    });
  }

  return request(`/admin/users/${userId}/reset-two-factor`, {
    method: 'POST',
  });
}

async function fetchUserTrustedDevices(userId) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse([
      {
        id: 101,
        created_at: new Date(Date.now() - 10 * 86400000).toISOString(),
        last_used_at: new Date(Date.now() - 2 * 3600000).toISOString(),
        expires_at: new Date(Date.now() + 4 * 86400000).toISOString(),
      },
      {
        id: 102,
        created_at: new Date(Date.now() - 3 * 86400000).toISOString(),
        last_used_at: null,
        expires_at: new Date(Date.now() + 11 * 86400000).toISOString(),
      },
    ]);
  }

  return request(`/admin/users/${userId}/trusted-devices`, {
    method: 'GET',
  });
}

async function revokeUserTrustedDevice(userId, deviceId) {
  if (MOCK_AUTH_ENABLED) {
    await delay();
    return createSuccessResponse({
      user_id: userId,
      action: 'trusted_device_revoked',
    });
  }

  return request(`/admin/users/${userId}/trusted-devices/${deviceId}/revoke`, {
    method: 'POST',
  });
}

async function revokeAllUserTrustedDevices(userId) {
  if (MOCK_AUTH_ENABLED) {
    await delay();
    return createSuccessResponse({
      user_id: userId,
      action: 'all_trusted_devices_revoked',
    });
  }

  return request(`/admin/users/${userId}/trusted-devices/revoke-all`, {
    method: 'POST',
  });
}

async function deleteChatSession(sessionId) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      session_id: sessionId,
      deleted: true,
      message: 'Chat session deleted successfully.',
    });
  }

  return request(`/admin/chat-sessions/${sessionId}`, {
    method: 'DELETE',
  });
}

async function fetchDeletableChatSessions() {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse([
      {
        id: 101,
        title: 'Initial onboarding question',
        status: 'closed',
        mode: 'system',
        user_id: 1,
        user_name: 'Ana Markovic',
        assigned_expert_id: null,
        assigned_expert_name: null,
        created_at: new Date(Date.now() - 2 * 86400000).toISOString(),
        closed_at: new Date(Date.now() - 2 * 86400000 + 3600000).toISOString(),
        eligible_reason: 'Closed empty chat',
      },
      {
        id: 102,
        title: null,
        status: 'active',
        mode: 'expert',
        user_id: 2,
        user_name: 'Ivan Basic',
        assigned_expert_id: 3,
        assigned_expert_name: 'Tom Expert',
        created_at: new Date(Date.now() - 30 * 3600000).toISOString(),
        closed_at: null,
        eligible_reason: 'Open empty chat older than 24 hours',
      },
    ]);
  }

  return request('/admin/chat-sessions', {
    method: 'GET',
  });
}

async function fetchExperts() {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse([
      {
        id: 1,
        name: 'Dr. Marko Novak',
        email: 'marko.novak@university.example',
        is_active: true,
        domain_codes: ['academic-advising', 'learning-support'],
        platform_user_id: 11,
        has_platform_account: true,
        platform_account_active: true,
        platform_account_registration_status: 'approved',
        created_at: new Date().toISOString(),
      },
      {
        id: 2,
        name: 'Ana Horvat',
        email: 'ana.horvat@university.example',
        is_active: true,
        domain_codes: ['student-support', 'administrative-services'],
        platform_user_id: null,
        has_platform_account: false,
        platform_account_active: false,
        platform_account_registration_status: null,
        created_at: new Date().toISOString(),
      },
    ]);
  }

  return request('/admin/experts', {
    method: 'GET',
  });
}

async function updateExpert(expertId, payload) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      id: expertId,
      ...payload,
      created_at: new Date().toISOString(),
    });
  }

  return request(`/admin/experts/${expertId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

async function provisionExpertAccount(expertId) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      expert_id: expertId,
      platform_user_id: Date.now(),
      action: 'provisioned',
      credentials_email_triggered: false,
      generated_temporary_password: 'ExpertTemp123',
    });
  }

  return request(`/admin/experts/${expertId}/provision-account`, {
    method: 'POST',
  });
}

async function fetchDomains() {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse([
      { code: 'student-support' },
      { code: 'academic-advising' },
      { code: 'finance-services' },
      { code: 'it-helpdesk' },
      { code: 'cybersecurity' },
      { code: 'learning-support' },
      { code: 'administrative-services' },
    ]);
  }

  return request('/admin/domains', {
    method: 'GET',
  });
}

async function fetchModuleSettings() {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      synapse_enabled: true,
      uex_enabled: true,
      ulm_enabled: false,
      page_enabled: true,
      llm_provider: 'mock',
      llm_model: 'mock',
      llm_available_providers: [
        {
          provider: 'openai',
          default_model: 'gpt-5.4-mini',
          model_options: ['gpt-5.4-mini', 'gpt-5.4'],
        },
        {
          provider: 'llama_cpp',
          default_model: 'local-default',
          model_options: ['local-default'],
        },
        {
          provider: 'mock',
          default_model: 'mock',
          model_options: ['mock'],
        },
      ],
    });
  }

  return request('/admin/module-settings', {
    method: 'GET',
  });
}

async function updateModuleSettings(payload) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    const availableProviders = [
      {
        provider: 'openai',
        default_model: 'gpt-5.4-mini',
        model_options: ['gpt-5.4-mini', 'gpt-5.4'],
      },
      {
        provider: 'llama_cpp',
        default_model: 'local-default',
        model_options: ['local-default'],
      },
      {
        provider: 'mock',
        default_model: 'mock',
        model_options: ['mock'],
      },
    ];
    const selectedProvider =
      availableProviders.find((item) => item.provider === payload.llm_provider) || availableProviders[2];
    const selectedModel = selectedProvider.model_options.includes(payload.llm_model)
      ? payload.llm_model
      : selectedProvider.default_model;

    return createSuccessResponse({
      synapse_enabled: payload.synapse_enabled ?? true,
      uex_enabled: payload.uex_enabled ?? true,
      ulm_enabled: payload.ulm_enabled ?? false,
      page_enabled: payload.page_enabled ?? true,
      llm_provider: selectedProvider.provider,
      llm_model: selectedModel,
      llm_available_providers: availableProviders,
    });
  }

  return request('/admin/module-settings', {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

async function fetchGeneralSettings() {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      show_chat_debug_panels: false,
      verbose_routing_logs: true,
      allow_expert_handoff: true,
      allow_ulm_in_chat: true,
    });
  }

  return request('/admin/general-settings', {
    method: 'GET',
  });
}

async function updateGeneralSettings(payload) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      show_chat_debug_panels: payload.show_chat_debug_panels ?? false,
      verbose_routing_logs: payload.verbose_routing_logs ?? true,
      allow_expert_handoff: payload.allow_expert_handoff ?? true,
      allow_ulm_in_chat: payload.allow_ulm_in_chat ?? true,
    });
  }

  return request('/admin/general-settings', {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

async function fetchKnowledgeItems() {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse([
      {
        id: 1,
        title: 'Applying for student exchange programs',
        content: 'Students interested in exchange programs must complete the online application form.',
        domain_code: 'student-support',
        status: 'published',
        source_expert_id: 2,
        source_expert_name: 'Ana Horvat',
        created_at: new Date().toISOString(),
      },
    ]);
  }

  return request('/admin/knowledge', {
    method: 'GET',
  });
}

async function createKnowledgeItem(payload) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      id: Date.now(),
      ...payload,
      source_expert_name: 'Mock expert',
      created_at: new Date().toISOString(),
    });
  }

  return request('/admin/knowledge', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

async function updateKnowledgeItem(itemId, payload) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      id: itemId,
      ...payload,
      source_expert_name: 'Mock expert',
      created_at: new Date().toISOString(),
    });
  }

  return request(`/admin/knowledge/${itemId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

async function deleteKnowledgeItem(itemId) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      deleted: true,
      knowledge_item_id: itemId,
    });
  }

  return request(`/admin/knowledge/${itemId}`, {
    method: 'DELETE',
  });
}

async function fetchUlmSources() {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse([
      {
        id: 1,
        title: 'Campus Wi-Fi Troubleshooting',
        source_type: 'document',
        source_value: 'Campus Wi-Fi can fail for several reasons...',
        indexing_status: 'indexed',
        document_count: 2,
        indexed_chunk_count: 2,
        created_at: new Date().toISOString(),
        last_updated_at: new Date().toISOString(),
      },
      {
        id: 2,
        title: 'Student handbook extract',
        source_type: 'document',
        source_value: 'Handbook policies on enrollment and coursework...',
        indexing_status: 'indexed',
        document_count: 4,
        indexed_chunk_count: 4,
        created_at: new Date(Date.now() - 86400000).toISOString(),
        last_updated_at: new Date(Date.now() - 43200000).toISOString(),
      },
    ]);
  }

  return request('/admin/ulm-sources', {
    method: 'GET',
  });
}

async function createUlmSource(payload) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      id: Date.now(),
      title: payload.title || (payload.url ? 'Imported URL source' : 'Pasted document'),
      source_type: payload.url ? 'url' : 'document',
      source_value: payload.url || payload.document,
      indexing_status: 'indexed',
      document_count: payload.url ? 3 : 2,
      indexed_chunk_count: payload.url ? 3 : 2,
      created_at: new Date().toISOString(),
      last_updated_at: new Date().toISOString(),
    });
  }

  return request('/admin/ulm-sources', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

async function uploadUlmSource({ title, file }) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      id: Date.now(),
      title: title || file?.name || 'Uploaded source',
      source_type: 'document',
      source_value: file?.name || 'Uploaded file',
      indexing_status: 'indexed',
      document_count: 3,
      indexed_chunk_count: 3,
      created_at: new Date().toISOString(),
      last_updated_at: new Date().toISOString(),
    });
  }

  const formData = new FormData();
  formData.append('file', file);

  if (title) {
    formData.append('title', title);
  }

  return request('/admin/ulm-sources/upload', {
    method: 'POST',
    body: formData,
  });
}

async function deleteUlmSource(sourceId) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      deleted: true,
      source_id: sourceId,
    });
  }

  return request(`/admin/ulm-sources/${sourceId}`, {
    method: 'DELETE',
  });
}

async function fetchUlmSourceDetail(sourceId) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      id: sourceId,
      title: 'Campus Wi-Fi Troubleshooting',
      source_type: 'url',
      source_value: 'https://university.example/support/wifi',
      indexing_status: 'indexed',
      document_count: 2,
      indexed_chunk_count: 2,
      created_at: new Date().toISOString(),
      last_updated_at: new Date().toISOString(),
      documents: [
        {
          id: 11,
          title: 'Campus Wi-Fi Troubleshooting (Chunk 1/2)',
          content: 'Campus Wi-Fi can fail for several reasons. First, confirm the student account is active and the device is using the correct SSID.',
          url: 'https://university.example/support/wifi',
          chunk_index: 0,
          chunk_count: 2,
          indexing_status: 'indexed',
          created_at: new Date().toISOString(),
        },
        {
          id: 12,
          title: 'Campus Wi-Fi Troubleshooting (Chunk 2/2)',
          content: 'If multiple devices fail in the same building, report the outage to IT support with the building name and room number.',
          url: 'https://university.example/support/wifi',
          chunk_index: 1,
          chunk_count: 2,
          indexing_status: 'indexed',
          created_at: new Date().toISOString(),
        },
      ],
    });
  }

  return request(`/admin/ulm-sources/${sourceId}`, {
    method: 'GET',
  });
}

async function refreshUlmSource(sourceId) {
  if (MOCK_AUTH_ENABLED) {
    return fetchUlmSourceDetail(sourceId);
  }

  return request(`/admin/ulm-sources/${sourceId}/refresh`, {
    method: 'POST',
  });
}

async function fetchConversationOverview() {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse([
      {
        id: 401,
        title: 'Adaptive learning onboarding',
        status: 'awaiting_expert',
        mode: 'expert',
        user_id: 1,
        user_name: 'Ana Markovic',
        assigned_expert_id: 3,
        assigned_expert_name: 'Tom Expert',
        created_at: new Date(Date.now() - 3 * 3600000).toISOString(),
        closed_at: null,
        last_message_at: new Date(Date.now() - 15 * 60000).toISOString(),
        last_message_role: 'user',
        last_message_preview: 'I need help understanding the recommended path for my profile.',
        message_count: 8,
        unread_message_count: 2,
        needs_attention: true,
        waiting_on: 'Expert',
        typing_actor_role: 'user',
      },
      {
        id: 402,
        title: 'Profile follow-up',
        status: 'awaiting_user',
        mode: 'expert',
        user_id: 2,
        user_name: 'Luka Horvat',
        assigned_expert_id: 3,
        assigned_expert_name: 'Tom Expert',
        created_at: new Date(Date.now() - 7 * 3600000).toISOString(),
        closed_at: null,
        last_message_at: new Date(Date.now() - 45 * 60000).toISOString(),
        last_message_role: 'expert',
        last_message_preview: 'Please confirm which recommendation track you want to continue with.',
        message_count: 14,
        unread_message_count: 1,
        needs_attention: true,
        waiting_on: 'User',
        typing_actor_role: null,
      },
    ]);
  }

  return request('/admin/conversations', {
    method: 'GET',
  });
}

async function fetchConversationDetail(conversationId) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      conversation: {
        id: conversationId,
        title: 'Adaptive learning onboarding',
        status: 'awaiting_expert',
        mode: 'expert',
        user_id: 1,
        user_name: 'Ana Markovic',
        assigned_expert_id: 3,
        assigned_expert_name: 'Tom Expert',
        created_at: new Date(Date.now() - 3 * 3600000).toISOString(),
        closed_at: null,
        last_message_at: new Date(Date.now() - 15 * 60000).toISOString(),
        last_message_role: 'user',
        last_message_preview: 'I need help understanding the recommended path for my profile.',
        message_count: 8,
        unread_message_count: 2,
        needs_attention: true,
        waiting_on: 'Expert',
        typing_actor_role: 'user',
      },
      messages: [
        {
          id: 1,
          role: 'user',
          mode: 'system',
          content: 'Can you suggest the next step for my profile?',
          created_at: new Date(Date.now() - 2 * 3600000).toISOString(),
        },
        {
          id: 2,
          role: 'assistant',
          mode: 'system',
          content: 'An expert handoff may help with this question.',
          created_at: new Date(Date.now() - 110 * 60000).toISOString(),
        },
        {
          id: 3,
          role: 'expert',
          mode: 'expert',
          content: 'Let me review your current profile context.',
          created_at: new Date(Date.now() - 60 * 60000).toISOString(),
        },
      ],
      handoffs: [
        {
          id: 11,
          session_id: conversationId,
          session_title: 'Adaptive learning onboarding',
          expert_id: 3,
          expert_name: 'Tom Expert',
          reason: 'The system suggested expert follow-up based on the current topic.',
          from_mode: 'system',
          to_mode: 'expert',
          created_at: new Date(Date.now() - 75 * 60000).toISOString(),
        },
      ],
    });
  }

  return request(`/admin/conversations/${conversationId}`, {
    method: 'GET',
  });
}

async function fetchHandoffs() {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse([
      {
        id: 11,
        session_id: 401,
        session_title: 'Adaptive learning onboarding',
        expert_id: 3,
        expert_name: 'Tom Expert',
        reason: 'The system suggested expert follow-up based on the current topic.',
        from_mode: 'system',
        to_mode: 'expert',
        created_at: new Date(Date.now() - 75 * 60000).toISOString(),
      },
    ]);
  }

  return request('/admin/handoffs', {
    method: 'GET',
  });
}

async function viewDataRequest(requestId) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      id: requestId,
      request_type: 'account_deletion',
      status: 'pending',
      reason: 'user_requested_deletion',
      user_id: 1,
      full_name: 'Lana Basic',
      email: 'lana@example.com',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
  }

  return request(`/admin/data-requests/${requestId}`, {
    method: 'GET',
  });
}

async function fetchDataRequests() {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse([
      {
        id: 1,
        request_type: 'account_deletion',
        status: 'pending',
        reason: 'user_requested_deletion',
        user_id: 1,
        full_name: 'Lana Basic',
        email: 'lana@example.com',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: 2,
        request_type: 'profiling_opt_out',
        status: 'completed',
        reason: 'user_withdrew_ai_profiling_consent',
        user_id: 2,
        full_name: 'Ivan P.',
        email: 'ivan@example.com',
        created_at: new Date(Date.now() - 86400000).toISOString(),
        updated_at: new Date(Date.now() - 86000000).toISOString(),
      },
    ]);
  }

  return request('/admin/data-requests', {
    method: 'GET',
  });
}

async function markDataRequestCompleted(requestId) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      request_id: requestId,
      status: 'completed',
    });
  }

  return request(`/admin/data-requests/${requestId}/complete`, {
    method: 'POST',
  });
}

async function rejectDataRequest(requestId) {
  if (MOCK_AUTH_ENABLED) {
    await delay();

    return createSuccessResponse({
      request_id: requestId,
      status: 'rejected',
    });
  }

  return request(`/admin/data-requests/${requestId}/reject`, {
    method: 'POST',
  });
}

export default {
  fetchDashboardSummary,
  bulkUpdateTwoFactor,
  fetchPendingRegistrations,
  approveRegistration,
  rejectRegistration,
  createUser,
  fetchUsers,
  viewUser,
  editUser,
  deactivateUser,
  resetUserPassword,
  resendUserCredentials,
  resetUserTwoFactor,
  fetchUserTrustedDevices,
  revokeUserTrustedDevice,
  revokeAllUserTrustedDevices,
  fetchDeletableChatSessions,
  deleteChatSession,
  fetchExperts,
  updateExpert,
  provisionExpertAccount,
  fetchDomains,
  fetchModuleSettings,
  updateModuleSettings,
  fetchGeneralSettings,
  updateGeneralSettings,
  fetchKnowledgeItems,
  createKnowledgeItem,
  updateKnowledgeItem,
  deleteKnowledgeItem,
  fetchUlmSources,
  createUlmSource,
  uploadUlmSource,
  fetchUlmSourceDetail,
  refreshUlmSource,
  deleteUlmSource,
  fetchConversationOverview,
  fetchConversationDetail,
  fetchHandoffs,
  fetchDataRequests,
  viewDataRequest,
  markDataRequestCompleted,
  rejectDataRequest,
};
