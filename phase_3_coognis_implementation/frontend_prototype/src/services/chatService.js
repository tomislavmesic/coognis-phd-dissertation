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

async function startConversation(payload) {
  if (MOCK_AUTH_ENABLED) {
    await delay(250);

    return createSuccessResponse({
      id: Date.now(),
      user_id: payload.user_id || null,
      title: payload.title || 'Mock conversation',
      mode: payload.mode || 'system',
      status: 'active',
      assigned_expert_id: null,
      created_at: new Date().toISOString(),
      closed_at: null,
    });
  }

  return request('/mind/chat/start', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

async function fetchConversationHistory(sessionId) {
  if (MOCK_AUTH_ENABLED) {
    await delay(200);

    return createSuccessResponse({
      items: [
        {
          id: 1,
          session_id: sessionId,
          role: 'assistant',
          mode: 'system',
          content: 'Welcome to the shared conversation channel.',
          created_at: new Date().toISOString(),
        },
      ],
      total: 1,
    });
  }

  return request(`/mind/chat/${sessionId}/history`, {
    method: 'GET',
  });
}

async function fetchConversation(sessionId) {
  if (MOCK_AUTH_ENABLED) {
    await delay(150);

    return createSuccessResponse({
      id: sessionId,
      user_id: null,
      title: 'Mock conversation',
      mode: 'system',
      status: 'active',
      assigned_expert_id: null,
      created_at: new Date().toISOString(),
      closed_at: null,
    });
  }

  return request(`/mind/chat/${sessionId}`, {
    method: 'GET',
  });
}

async function fetchConversations(userId) {
  if (MOCK_AUTH_ENABLED) {
    await delay(200);

    return createSuccessResponse({
      items: [
        {
          id: 101,
          user_id: userId || 1,
          title: 'Conversation 101',
          mode: 'system',
          status: 'active',
          assigned_expert_id: null,
          created_at: new Date().toISOString(),
          closed_at: null,
          last_message_at: new Date().toISOString(),
          last_activity_at: new Date().toISOString(),
          last_message_role: 'assistant',
          last_message_preview: 'Here is the latest grounded answer about your study options and next steps.',
        },
        {
          id: 100,
          user_id: userId || 1,
          title: 'Conversation 100',
          mode: 'expert',
          status: 'closed',
          assigned_expert_id: 2,
          created_at: new Date(Date.now() - 86400000).toISOString(),
          closed_at: new Date(Date.now() - 86000000).toISOString(),
          last_message_at: new Date(Date.now() - 86000000).toISOString(),
          last_activity_at: new Date(Date.now() - 86000000).toISOString(),
          last_message_role: 'user',
          last_message_preview: 'I still need help understanding the tuition breakdown for EU students.',
        },
      ],
      total: 2,
    });
  }

  return request('/mind/chat', {
    method: 'GET',
  });
}

async function fetchExpert(expertId) {
  if (MOCK_AUTH_ENABLED) {
    await delay(150);

    return createSuccessResponse({
      id: expertId,
      name: 'Dr. Petra Novak',
      email: 'petra@example.com',
      is_active: true,
      domain_codes: ['adaptive-systems', 'expert-guidance'],
      platform_user_id: 1,
      is_contactable: true,
      created_at: new Date().toISOString(),
    });
  }

  return request(`/uex/experts/${expertId}`, {
    method: 'GET',
  });
}

async function sendMessage(payload) {
  if (MOCK_AUTH_ENABLED) {
    await delay(450);

    const modulesUsed = ['MIND'];
    if (payload?.use_synapse !== false) {
      modulesUsed.push('SYNAPSE');
    }
    if (payload?.use_uex !== false) {
      modulesUsed.push('UEX');
    }
    modulesUsed.push('PAGE');
    if (payload?.use_ulm) {
      modulesUsed.splice(modulesUsed.length - 1, 0, 'ULM');
    }

    return createSuccessResponse({
      final_response: 'System mode placeholder response. Adaptive system messaging will be connected later.',
      modules_used: modulesUsed,
      assistant_message_id: Date.now() + 1,
      expert_suggestion: payload?.use_uex === false
        ? null
        : {
            expert_id: 1,
            name: 'Dr. Petra Novak',
            total_score: 0.92,
            is_contactable: true,
            domain_codes: ['adaptive-systems', 'expert-guidance'],
          },
      debug: {
        synapse: payload?.use_synapse === false
          ? null
          : {
              stored_mbti: 'ESFJ',
              inferred_mbti: 'ESFJ',
              effective_mbti: 'ESFJ',
              confidence: 0.81,
            },
        inferred_domain_codes: ['adaptive-systems'],
        uex_knowledge_preview: 'Adaptive guidance baseline: Students may request certificates through the administrative portal.',
        uex_knowledge_items: [
          { id: 1, title: 'Certificate requests', domain_code: 'administrative-services' },
        ],
        ulm_chunks: payload?.use_ulm
          ? [
              {
                source_id: 1,
                document_id: 2,
                title: 'Administrative portal guide (Chunk 1/2)',
                chunk_index: 0,
                source_type: 'document',
                score: 0.42,
              },
            ]
          : [],
        page: {
          style_label: 'balanced-clear',
          intent_label: 'general_guidance',
          sections: ['answer', 'next_steps'],
        },
        page_input: {
          user_mbti: payload?.use_synapse === false ? null : 'ESFJ',
          query: payload?.query || '',
          uex_knowledge: 'Adaptive guidance baseline: Students may request certificates through the administrative portal.',
          expert_suggestion: payload?.use_uex === false
            ? null
            : {
                name: 'Dr. Petra Novak',
                domain_codes: ['adaptive-systems', 'expert-guidance'],
                is_contactable: true,
                reason: 'Match score 0.92 based on current query routing.',
              },
          ulm_grounding: payload?.use_ulm
            ? {
                summary: 'Retrieved external guidance from one indexed source.',
                source_count: 1,
                chunk_count: 1,
                sources: [
                  {
                    title: 'Administrative portal guide (Chunk 1/2)',
                    chunk_index: 0,
                    source_type: 'document',
                  },
                ],
              }
            : null,
          ulm_used: Boolean(payload?.use_ulm),
          conversation_mode: 'system',
        },
        expert_suggestion_reason: 'Match score 0.92',
      },
    });
  }

  return request('/mind/chat/message', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

async function respondWithPage(payload) {
  if (MOCK_AUTH_ENABLED) {
    await delay(250);
    const mbti = payload?.user_profile?.mbti || 'DEFAULT';
    return createSuccessResponse({
      response: `Mock PAGE response for ${mbti}.`,
      style_label: 'balanced-clear',
      intent_label: 'general_guidance',
      sections: ['answer', 'next_steps'],
    });
  }

  return request('/page/respond', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

async function sendExpertMessage(payload) {
  if (MOCK_AUTH_ENABLED) {
    await delay(250);

    return createSuccessResponse({
      message: {
        id: Date.now(),
        session_id: payload.session_id,
        role: 'expert',
        mode: 'expert',
        content: payload.content,
        created_at: new Date().toISOString(),
      },
      expert_profile_updated: true,
    });
  }

  return request('/mind/chat/expert-message', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

async function handoffToExpert(payload) {
  if (MOCK_AUTH_ENABLED) {
    await delay(250);

    return createSuccessResponse({
      id: Date.now(),
      session_id: payload.session_id,
      expert_id: payload.expert_id,
      reason: payload.reason || null,
      from_mode: 'system',
      to_mode: 'expert',
      created_at: new Date().toISOString(),
    });
  }

  return request('/mind/chat/handoff', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

async function closeConversation(payload) {
  if (MOCK_AUTH_ENABLED) {
    await delay(250);

    return createSuccessResponse({
      id: payload.session_id,
      user_id: null,
      title: 'Mock conversation',
      mode: payload.mode || 'system',
      status: 'closed',
      assigned_expert_id: null,
      created_at: new Date().toISOString(),
      closed_at: new Date().toISOString(),
    });
  }

  return request('/mind/chat/close', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

async function updateTypingStatus(payload) {
  if (MOCK_AUTH_ENABLED) {
    await delay(100);

    return createSuccessResponse({
      id: payload.session_id,
      typing_actor_role: payload.is_typing ? (payload.actor_role || 'user') : null,
      typing_updated_at: payload.is_typing ? new Date().toISOString() : null,
    });
  }

  return request('/mind/chat/typing', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

async function fetchUnreadSummary() {
  if (MOCK_AUTH_ENABLED) {
    await delay(100);

    return createSuccessResponse({
      attention_count: 2,
    });
  }

  return request('/mind/chat/unread-summary', {
    method: 'GET',
  });
}

async function submitFeedback(payload) {
  if (MOCK_AUTH_ENABLED) {
    await delay(250);

    return createSuccessResponse({
      status: 'recorded',
      ...payload,
    });
  }

  const feedbackPath = payload.mode === 'expert' ? '/feedback/interaction' : '/feedback/system';
  const normalizedPayload = {
    session_id: payload.session_id,
    clarity: payload.clarity,
    usefulness: payload.usefulness,
    personalization_fit: payload.personalization_fit ?? payload.satisfaction,
    communication_quality: payload.communication_quality ?? payload.satisfaction,
    satisfaction: payload.satisfaction,
    comment: payload.comment ?? null,
  };

  return request(feedbackPath, {
    method: 'POST',
    body: JSON.stringify(normalizedPayload),
  });
}

function normalizeHistory(items = []) {
  return items.map((item) => ({
    id: item.id,
    sender: item.role === 'user' ? 'user' : item.role === 'expert' ? 'expert' : 'assistant',
    mode: item.mode || 'system',
    text: item.content || '',
    createdAt: item.created_at || null,
    debugInfo: null,
  }));
}

function buildExpertSuggestionCard(suggestion, expertDetails = null) {
  if (!suggestion) {
    return null;
  }

  const domainCodes = expertDetails?.domain_codes || [];

  return {
    expertId: suggestion.expert_id,
    name: expertDetails?.name || suggestion.name,
    domain: domainCodes.length ? domainCodes.join(', ') : 'Expert guidance',
    reason: `The MIND backend suggested this expert with a match score of ${Number(suggestion.total_score || 0).toFixed(2)}.`,
    isContactable: expertDetails?.is_contactable ?? suggestion.is_contactable ?? false,
    compatibility: domainCodes.length
      ? `Relevant domains: ${domainCodes.join(', ')}.`
      : 'Suitable for deeper follow-up beyond the system response.',
  };
}

export default {
  startConversation,
  fetchConversations,
  fetchConversation,
  fetchConversationHistory,
  fetchExpert,
  sendMessage,
  respondWithPage,
  sendExpertMessage,
  handoffToExpert,
  closeConversation,
  updateTypingStatus,
  fetchUnreadSummary,
  submitFeedback,
  normalizeHistory,
  buildExpertSuggestionCard,
};
