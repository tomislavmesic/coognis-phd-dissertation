<template>
  <section class="chat-workspace">
    <div class="row g-4">
      <div class="col-sm-8">
        <header class="base-page-header">
          <div>
            <p class="placeholder-eyebrow mb-2">Conversation</p>
            <h1 class="base-page-header__title mb-2">Main system chat</h1>
            <p class="base-page-header__description mb-0">
              A shared conversation channel for system mode and expert mode, connected to the live MIND backend session.
            </p>
          </div>
        </header>

      </div>
      <div class="col-sm-4">
        <BaseCard 
          class="base-card base-stat-card"
          card-body-class="p-0"
        >
          <ul class="list-unstyled mb-0 d-flex flex-column gap-3">
            <li>
              <strong>Current mode</strong>
              <p class="base-stat-note mb-0">
                <span class="badge text-bg-warning">
                  {{ currentMode }}
                </span>
              </p>
            </li>
            <li>
              <strong>State</strong>
              <p class="base-stat-note mb-0">
                <span class="badge" :class="sessionStateClass">
                  {{ sessionStateLabel }}
                </span>
              </p>
            </li>

          </ul>
        </BaseCard>
      </div>
    </div>
    
    <div class="row g-4 align-items-stretch">
      <div class="col-xl-8">
        <div class="chat-workspace__panel d-flex flex-column">
          <div class="chat-toolbar d-flex flex-wrap justify-content-between align-items-center gap-3">
            <div class="d-flex flex-wrap gap-2">
              <span class="text-body-secondary">
                <span v-if="sessionId">Session #{{ sessionId }}</span>
                <span v-else>New conversation</span>
              </span>
            </div>

            <div class="d-flex flex-wrap gap-2">
              <button
                v-if="!isExpertFacingRoute"
                class="btn btn-sm btn-outline-secondary"
                type="button"
                :disabled="isBusy || !sessionId || currentMode === 'expert' || !recommendedExpert || recommendedExpert.isContactable === false"
                @click="handleHandoff"
              >
                Handoff to expert
              </button>
              <button
                class="btn btn-sm btn-outline-danger"
                type="button"
                :disabled="isBusy || !sessionId || sessionStatus === 'closed'"
                @click="handleCloseConversation"
              >
                Close conversation
              </button>
            </div>
          </div>

          <div ref="historyPanel" class="chat-workspace__history flex-grow-1">
            <div
              v-for="message in messages"
              :key="message.id"
              class="chat-workspace__bubble"
              :class="messageBubbleClass(message)"
            >
              <div
                v-if="message.debugInfo && canSeeDebugPanel"
                class="chat-workspace__debug-panel"
              >
                <div class="chat-workspace__debug-header">
                  <strong>Debug</strong>
                  <span v-if="message.debugInfo.page?.intentLabel || message.debugInfo.page?.styleLabel">
                    {{ [
                      message.debugInfo.page?.intentLabel ? `Intent: ${message.debugInfo.page.intentLabel}` : null,
                      message.debugInfo.page?.styleLabel ? `Style: ${message.debugInfo.page.styleLabel}` : null,
                    ].filter(Boolean).join(' · ') }}
                  </span>
                </div>

                <div class="chat-workspace__debug-grid">
                  <div v-if="message.debugInfo.synapse">
                    <span class="text-body-secondary">SYNAPSE</span>
                    <strong>
                      {{ [
                        message.debugInfo.synapse.effectiveMbti ? `effective ${message.debugInfo.synapse.effectiveMbti}` : null,
                        message.debugInfo.synapse.storedMbti ? `stored ${message.debugInfo.synapse.storedMbti}` : null,
                        message.debugInfo.synapse.inferredMbti ? `live ${message.debugInfo.synapse.inferredMbti}` : null,
                      ].filter(Boolean).join(' · ') }}
                    </strong>
                    <small
                      v-if="typeof message.debugInfo.synapse.confidence === 'number'"
                      class="text-body-secondary"
                    >
                      confidence {{ message.debugInfo.synapse.confidence.toFixed(2) }}
                    </small>
                  </div>
                  <div v-if="message.debugInfo.modulesUsed?.length">
                    <span class="text-body-secondary">Modules</span>
                    <strong>{{ message.debugInfo.modulesUsed.join(', ') }}</strong>
                  </div>
                  <div v-if="message.debugInfo.inferredDomainCodes?.length">
                    <span class="text-body-secondary">Domains</span>
                    <strong>{{ message.debugInfo.inferredDomainCodes.join(', ') }}</strong>
                  </div>
                  <div v-if="message.debugInfo.page?.sections?.length">
                    <span class="text-body-secondary">Sections</span>
                    <strong>{{ message.debugInfo.page.sections.join(', ') }}</strong>
                  </div>
                  <div v-if="message.debugInfo.expertSuggestionReason">
                    <span class="text-body-secondary">Expert match</span>
                    <strong>{{ message.debugInfo.expertSuggestionReason }}</strong>
                  </div>
                </div>

                <div
                  v-if="message.debugInfo.pageInput"
                  class="chat-workspace__debug-page-override"
                >
                  <div class="chat-workspace__debug-page-override-copy">
                    <span class="text-body-secondary">PAGE response MBTI</span>
                    <small class="text-body-secondary">
                      Original {{ message.debugInfo.pageInput.userMbti || 'DEFAULT' }}
                    </small>
                  </div>
                  <div class="chat-workspace__debug-page-override-controls">
                    <select
                      v-model="pageMbtiOverrideByMessageId[message.id]"
                      class="form-select form-select-sm"
                    >
                      <option value="">DEFAULT</option>
                      <option v-for="mbti in MBTI_OPTIONS" :key="`${message.id}-${mbti}`" :value="mbti">
                        {{ mbti }}
                      </option>
                    </select>
                    <button
                      class="btn btn-sm btn-outline-primary"
                      type="button"
                      :disabled="isBusy || regeneratingPageMessageId === message.id"
                      @click="regeneratePageMessage(message)"
                    >
                      {{ regeneratingPageMessageId === message.id ? 'Regenerating...' : 'Regenerate PAGE' }}
                    </button>
                  </div>
                </div>

                <div v-if="message.debugInfo.uexKnowledgeItems?.length" class="chat-workspace__debug-block">
                  <span class="text-body-secondary">UEX knowledge items</span>
                  <ul class="chat-workspace__debug-list">
                    <li v-for="item in message.debugInfo.uexKnowledgeItems" :key="`${message.id}-uex-${item.id}`">
                      {{ item.title }}<span v-if="item.domainCode"> · {{ item.domainCode }}</span>
                    </li>
                  </ul>
                </div>

                <div v-if="message.debugInfo.uexKnowledgePreview" class="chat-workspace__debug-block">
                  <span class="text-body-secondary">UEX preview</span>
                  <p class="mb-0">{{ message.debugInfo.uexKnowledgePreview }}</p>
                </div>

                <div v-if="message.debugInfo.ulmChunks?.length" class="chat-workspace__debug-block">
                  <span class="text-body-secondary">ULM chunks</span>
                  <ul class="chat-workspace__debug-list">
                    <li v-for="(chunk, index) in message.debugInfo.ulmChunks" :key="`${message.id}-ulm-${chunk.documentId || index}`">
                      {{ chunk.title || `Chunk ${index + 1}` }}
                      <span v-if="chunk.sourceType"> · {{ chunk.sourceType }}</span>
                      <span v-if="typeof chunk.score === 'number'"> · score {{ chunk.score.toFixed(2) }}</span>
                    </li>
                  </ul>
                </div>
              </div>
              <div class="chat-workspace__bubble-meta">
                {{ messageMetaLabel(message) }}
              </div>
              <div
                class="chat-workspace__bubble-content"
                v-html="formatMessageContent(messageDisplayText(message))"
              ></div>
              <div
                v-if="messageSources(message).length"
                class="chat-workspace__sources"
              >
                <div class="chat-workspace__sources-label">Sources</div>
                <ul class="chat-workspace__sources-list">
                  <li
                    v-for="(source, index) in messageSources(message)"
                    :key="`${message.id}-source-${source.url || source.title || index}`"
                  >
                    <a
                      v-if="source.url"
                      :href="source.url"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {{ source.title }}
                    </a>
                    <span v-else>{{ source.title }}</span>
                  </li>
                </ul>
              </div>
              <div
                v-if="message.expertAction"
                class="chat-workspace__expert-action"
              >
                <div class="chat-workspace__expert-action-copy">
                  <strong>{{ message.expertAction.name }}</strong>
                  <small class="text-body-secondary">
                    {{ message.expertAction.isContactable
                      ? 'You can hand this conversation to the suggested expert directly from here.'
                      : 'Expert match found, but chat handoff is not available until the account is provisioned.' }}
                  </small>
                </div>
                <button
                  v-if="!isExpertFacingRoute"
                  class="btn btn-sm btn-primary"
                  type="button"
                  :disabled="isBusy || currentMode === 'expert' || sessionStatus === 'closed' || message.expertAction.isContactable === false"
                  @click="handleMessageHandoff(message)"
                >
                  {{ message.expertAction.isContactable === false ? 'Contact unavailable' : 'Contact expert' }}
                </button>
              </div>
            </div>

            <div v-if="showTypingIndicator" class="chat-workspace__typing chat-workspace__typing--presence">
              <span class="chat-workspace__typing-label">{{ typingIndicatorLabel }}</span>
              <span class="chat-workspace__typing-dots" aria-hidden="true">
                <span></span>
                <span></span>
                <span></span>
              </span>
            </div>

            <div v-if="isInitializingConversation" class="chat-workspace__typing">
              Loading conversation history...
            </div>
          </div>

          <div v-if="isTyping" class="chat-workspace__typing">
            {{ currentMode === 'expert' ? 'Expert mode is preparing a response...' : 'System is preparing a response...' }}
          </div>

          <div class="chat-composer">
            <form class="row g-3 align-items-end" @submit.prevent="handleSendMessage">
              <div class="col-12">
                <label class="form-label" for="chat-message">Message</label>
                <textarea
                  id="chat-message"
                  v-model.trim="draftMessage"
                  class="form-control"
                  :disabled="isBusy || sendDisabled"
                  rows="3"
                  placeholder="Type your message here"
                  @keydown="handleComposerKeydown"
                  @focus="handleComposerFocus"
                  @blur="handleComposerBlur"
                  @input="handleComposerInput"
                ></textarea>
              </div>
              <div class="col-12 d-flex justify-content-between align-items-center">
                <small class="text-body-secondary">
                  <span v-if="sessionId">Session #{{ sessionId }} · {{ sessionStateLabel }}</span>
                  <span v-else>{{ composerDisabledReason }}</span>
                </small>
                <button class="btn btn-primary" type="submit" :disabled="isBusy || !draftMessage || sendDisabled">
                  {{ isTyping ? 'Sending...' : 'Send' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      <div class="col-xl-4">
        <div class="chat-workspace__suggestions">
          <BaseCard 
            class="base-card base-stat-card"
            card-body-class="p-0"
          >
            <p class="placeholder-eyebrow mb-3">Response modules</p>
            <h2 class="h5 mb-2">Backend context</h2>
            <p class="text-body-secondary mb-2">
              Modules used for the latest backend response:
            </p>
            <p class="mb-0">{{ modulesUsedLabel }}</p>
          </BaseCard>

          <ExpertHandoffCard
            v-if="recommendedExpert && !isExpertFacingRoute"
            :expert="recommendedExpert"
            :mode="currentMode"
            :disabled="isBusy || currentMode === 'expert'"
            @continue-system="switchMode('system')"
            @contact-expert="handleHandoff"
          />
        </div>
      </div>
    </div>
  </section>

  <FeedbackModal
    :visible="showFeedbackModal"
    :mode="feedbackMode"
    :submitting="isSubmittingFeedback"
    @close="closeFeedbackModal"
    @submit="handleFeedbackSubmit"
  />
</template>

<script>
import BaseCard from '@/components/BaseCard.vue';
import ExpertHandoffCard from '@/components/ExpertHandoffCard.vue';
import FeedbackModal from '@/components/FeedbackModal.vue';
import toastFeedbackMixin from '@/mixins/toastFeedbackMixin';
import chatService from '@/services/chatService';
import authStore from '@/store/authStore';

const DEFAULT_CHAT_POLLING_INTERVAL_MS = 5000;
const CONFIGURED_CHAT_POLLING_INTERVAL_MS = Number(import.meta.env.VITE_CHAT_POLLING_INTERVAL_MS);
const MBTI_OPTIONS = ['INTJ', 'INTP', 'ENTJ', 'ENTP', 'INFJ', 'INFP', 'ENFJ', 'ENFP', 'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ', 'ISTP', 'ISFP', 'ESTP', 'ESFP'];

export default {
  name: 'ChatInterfaceView',
  mixins: [toastFeedbackMixin],
  components: {
    ExpertHandoffCard,
    FeedbackModal,
    BaseCard,
  },
  data() {
    return {
      MBTI_OPTIONS,
      sessionId: null,
      sessionStatus: 'initializing',
      draftMessage: '',
      currentMode: 'system',
      isTyping: false,
      isBusy: false,
      isInitializingConversation: false,
      successMessage: '',
      errorMessage: '',
      showFeedbackModal: false,
      feedbackMode: 'system',
      isSubmittingFeedback: false,
      feedbackContext: null,
      messages: [],
      recommendedExpert: null,
      latestModulesUsed: [],
      pollingTimerId: null,
      pollingIntervalMs: Number.isFinite(CONFIGURED_CHAT_POLLING_INTERVAL_MS) && CONFIGURED_CHAT_POLLING_INTERVAL_MS > 0
        ? CONFIGURED_CHAT_POLLING_INTERVAL_MS
        : DEFAULT_CHAT_POLLING_INTERVAL_MS,
      isComposerFocused: false,
      typingHeartbeatTimerId: null,
      typingHeartbeatIntervalMs: 3000,
      typingActorRole: null,
      stickyTypingActorRole: null,
      typingUpdatedAt: null,
      sessionUserName: '',
      assignedExpertName: '',
      closedByRole: null,
      closedByName: '',
      feedbackModeFromSession: null,
      feedbackPendingForCurrentUser: false,
      feedbackPromptedSessionKey: null,
      debugByMessageId: {},
      expertActionByMessageId: {},
      regeneratedPageResponseByMessageId: {},
      pageMbtiOverrideByMessageId: {},
      regeneratingPageMessageId: null,
    };
  },
  computed: {
    currentActorRole() {
      return authStore.resolveRoleFromPayload(authStore.state.currentUser) || 'user';
    },
    isExpertFacingRoute() {
      return this.$route?.path?.startsWith('/expert') || false;
    },
    currentActorName() {
      const currentUser = authStore.state.currentUser;
      if (!currentUser) {
        return 'You';
      }

      const fullName = [currentUser.first_name, currentUser.last_name].filter(Boolean).join(' ').trim();
      return fullName || currentUser.name || currentUser.email || 'You';
    },
    canSeeDebugPanel() {
      const currentUser = authStore.state.currentUser;
      return Boolean(currentUser?.can_access_chat_debug_panels || this.currentActorRole === 'admin');
    },
    canSwitchToSystem() {
      return this.currentMode === 'system';
    },
    modulesUsedLabel() {
      return this.latestModulesUsed.length ? this.latestModulesUsed.join(', ') : 'No response yet.';
    },
    latestMessage() {
      return this.messages.length ? this.messages[this.messages.length - 1] : null;
    },
    sessionStateLabel() {
      if (this.sessionStatus === 'closed') {
        return 'Closed';
      }

      if (this.sessionStatus === 'awaiting_expert') {
        return this.currentActorRole === 'expert' ? 'Awaiting your reply' : 'Awaiting expert reply';
      }

      if (this.sessionStatus === 'awaiting_user') {
        return this.currentActorRole === 'expert' ? 'Awaiting user reply' : 'Awaiting your reply';
      }

      return this.currentMode === 'system' ? 'System conversation active' : 'Conversation active';
    },
    sessionStateClass() {
      if (this.sessionStatus === 'closed') {
        return 'chat-workspace__session-state--closed';
      }

      if (this.sessionStatus === 'awaiting_expert') {
        return 'chat-workspace__session-state--awaiting-expert';
      }

      if (this.sessionStatus === 'awaiting_user') {
        return 'chat-workspace__session-state--awaiting-user';
      }

      if (this.currentMode === 'expert') {
        return 'chat-workspace__session-state--expert';
      }

      return 'chat-workspace__session-state--system';
    },
    showTypingIndicator() {
      return this.effectiveTypingActorRole && this.effectiveTypingActorRole !== this.currentActorRole && this.sessionStatus !== 'closed' && !this.isTyping;
    },
    effectiveTypingActorRole() {
      if (this.typingActorRole && this.typingActorRole !== this.currentActorRole) {
        return this.typingActorRole;
      }

      if (
        this.currentActorRole === 'expert'
        && this.currentMode === 'expert'
        && this.sessionStatus === 'awaiting_expert'
        && this.stickyTypingActorRole === 'user'
      ) {
        return this.stickyTypingActorRole;
      }

      return null;
    },
    typingIndicatorLabel() {
      if (this.effectiveTypingActorRole === 'expert') {
        return 'Expert is typing';
      }

      if (this.effectiveTypingActorRole === 'user') {
        return 'User is typing';
      }

      return 'Someone is typing';
    },
    currentFeedbackMode() {
      return this.feedbackModeFromSession === 'interaction' ? 'expert' : 'system';
    },
    composerDisabledReason() {
      if (!this.sessionId) {
        return this.currentActorRole === 'expert'
          ? 'Select an assigned conversation to start collaborating.'
          : 'Send your first message to start the conversation.';
      }

      if (this.sessionStatus === 'closed') {
        return 'This conversation is closed. Start a new conversation to continue.';
      }

      if (this.currentActorRole === 'expert' && this.currentMode !== 'expert') {
        return 'Expert replies are available only after a conversation is handed off.';
      }

      return '';
    },
    sendDisabled() {
      if (this.sessionStatus === 'closed') {
        return true;
      }

      if (this.currentActorRole === 'expert' && !this.sessionId) {
        return true;
      }

      return false;
    },
  },
  watch: {
    showTypingIndicator() {
      this.scrollHistoryToBottom();
    },
    typingActorRole: {
      immediate: true,
      handler(newValue) {
        if (
          newValue === 'user'
          && this.currentActorRole === 'expert'
          && this.currentMode === 'expert'
        ) {
          this.stickyTypingActorRole = 'user';
          return;
        }

        if (!newValue && this.currentActorRole !== 'expert') {
          this.stickyTypingActorRole = null;
        }
      },
    },
    isTyping(newValue) {
      if (newValue) {
        this.stickyTypingActorRole = null;
      }
    },
    currentMode(newValue) {
      if (newValue !== 'expert') {
        this.stickyTypingActorRole = null;
      }
    },
    sessionStatus(newValue) {
      if (newValue !== 'awaiting_expert') {
        this.stickyTypingActorRole = null;
      }
    },
  },
  async created() {
    await this.initializeConversation();
  },
  beforeUnmount() {
    this.stopPolling();
    this.stopTypingHeartbeat();
  },
  methods: {
    scrollHistoryToBottom() {
      this.$nextTick(() => {
        const panel = this.$refs.historyPanel;
        if (!panel || typeof panel.scrollTo !== 'function') {
          return;
        }

        panel.scrollTo({
          top: panel.scrollHeight,
          behavior: 'smooth',
        });
      });
    },
    async initializeConversation() {
      this.isInitializingConversation = true;
      this.errorMessage = '';
      this.successMessage = '';

      const requestedSessionId = Number(this.$route.query.session || 0);

      if (requestedSessionId > 0) {
        const sessionResponse = await chatService.fetchConversation(requestedSessionId);

        if (!sessionResponse.success) {
          this.errorMessage = sessionResponse.error?.message || 'Unable to open the requested conversation.';
          this.isInitializingConversation = false;
          return;
        }

        this.sessionId = sessionResponse.data?.id || requestedSessionId;
        this.currentMode = sessionResponse.data?.mode || 'system';
        this.sessionStatus = sessionResponse.data?.status || 'active';
        await this.refreshConversation();
        this.startPolling();
        this.isInitializingConversation = false;
        return;
      }

      if (this.currentActorRole === 'expert') {
        this.errorMessage = 'Open one of your assigned conversations from the expert dashboard or chat list.';
        this.isInitializingConversation = false;
        return;
      }
      this.isInitializingConversation = false;
    },
    async refreshConversation(options = {}) {
      if (!this.sessionId) {
        return;
      }

      const { preserveError = false } = options;
      const previousStatus = this.sessionStatus;
      const previousLastMessageId = this.latestMessage?.id || null;
      const [sessionResponse, historyResponse] = await Promise.all([
        chatService.fetchConversation(this.sessionId),
        chatService.fetchConversationHistory(this.sessionId),
      ]);

      if (sessionResponse.success) {
        this.currentMode = sessionResponse.data?.mode || this.currentMode;
        this.sessionStatus = sessionResponse.data?.status || this.sessionStatus;
        this.typingActorRole = sessionResponse.data?.typing_actor_role || null;
        this.typingUpdatedAt = sessionResponse.data?.typing_updated_at || null;
        this.sessionUserName = sessionResponse.data?.user_name || this.sessionUserName;
        this.assignedExpertName = sessionResponse.data?.assigned_expert_name || this.assignedExpertName;
        this.closedByRole = sessionResponse.data?.closed_by_role || null;
        this.closedByName = sessionResponse.data?.closed_by_name || '';
        this.feedbackModeFromSession = sessionResponse.data?.feedback_mode || null;
        this.feedbackPendingForCurrentUser = Boolean(sessionResponse.data?.feedback_pending_for_current_user);

        if (previousStatus !== 'closed' && this.sessionStatus === 'closed') {
          this.handleClosedConversationEvent();
        } else if (this.sessionStatus === 'closed') {
          this.maybePromptFeedbackForClosedSession();
        }
      } else if (!preserveError) {
        this.errorMessage = sessionResponse.error?.message || 'Unable to refresh the conversation.';
        if ([403, 404].includes(Number(sessionResponse.error?.status || 0))) {
          this.stopPolling();
        }
      }

      if (historyResponse.success) {
        this.messages = chatService.normalizeHistory(historyResponse.data?.items || []);
        this.applyStoredDebugInfo();
        if (this.latestMessage?.id && this.latestMessage.id !== previousLastMessageId) {
          this.scrollHistoryToBottom();
        }
      } else if (!preserveError) {
        this.errorMessage = historyResponse.error?.message || 'Unable to load conversation history.';
        if ([403, 404].includes(Number(historyResponse.error?.status || 0))) {
          this.stopPolling();
        }
      }
    },
    async loadConversationHistory() {
      if (!this.sessionId) {
        return;
      }

      const response = await chatService.fetchConversationHistory(this.sessionId);

      if (response.success) {
        this.messages = chatService.normalizeHistory(response.data?.items || []);
      } else {
        this.errorMessage = response.error?.message || 'Unable to load conversation history.';
      }
    },
    startPolling() {
      this.stopPolling();

      if (!this.sessionId || this.sessionStatus === 'closed') {
        return;
      }

      this.pollingTimerId = window.setInterval(async () => {
        if (this.isBusy || this.isInitializingConversation || !this.sessionId || this.showFeedbackModal) {
          return;
        }

        await this.refreshConversation({ preserveError: true });

        if (this.sessionStatus === 'closed') {
          this.stopPolling();
        }
      }, this.pollingIntervalMs);
    },
    stopPolling() {
      if (!this.pollingTimerId) {
        return;
      }

      window.clearInterval(this.pollingTimerId);
      this.pollingTimerId = null;
    },
    async setTypingState(isTyping) {
      if (!this.sessionId) {
        return;
      }

      const response = await chatService.updateTypingStatus({
        session_id: this.sessionId,
        is_typing: isTyping,
      });

      if (response.success) {
        this.typingActorRole = response.data?.typing_actor_role || null;
        this.typingUpdatedAt = response.data?.typing_updated_at || null;
      }
    },
    startTypingHeartbeat() {
      this.stopTypingHeartbeat();

      if (!this.sessionId || this.sessionStatus === 'closed') {
        return;
      }

      this.typingHeartbeatTimerId = window.setInterval(() => {
        if (!this.isComposerFocused || this.isBusy || !this.sessionId || this.sessionStatus === 'closed') {
          return;
        }

        this.setTypingState(true);
      }, this.typingHeartbeatIntervalMs);
    },
    stopTypingHeartbeat() {
      if (!this.typingHeartbeatTimerId) {
        return;
      }

      window.clearInterval(this.typingHeartbeatTimerId);
      this.typingHeartbeatTimerId = null;
    },
    async loadExpertSuggestion(expertSuggestion) {
      if (!expertSuggestion?.expert_id || expertSuggestion.is_contactable === false) {
        this.recommendedExpert = null;
        return;
      }

      const expertResponse = await chatService.fetchExpert(expertSuggestion.expert_id);
      const expertDetails = expertResponse.success ? expertResponse.data : null;

      this.recommendedExpert = chatService.buildExpertSuggestionCard(expertSuggestion, expertDetails);
    },
    switchMode(mode) {
      if (mode === 'system' && this.currentMode !== 'expert') {
        this.currentMode = 'system';
        this.successMessage = 'System mode is active for this conversation.';
        this.errorMessage = '';
      }
    },
    openFeedbackModal(mode, context) {
      this.feedbackMode = mode;
      this.feedbackContext = context;
      this.showFeedbackModal = true;
    },
    closeFeedbackModal() {
      if (this.isSubmittingFeedback) {
        return;
      }

      this.showFeedbackModal = false;
      this.feedbackContext = null;
    },
    maybePromptFeedbackForClosedSession() {
      if (!this.feedbackPendingForCurrentUser || !this.sessionId) {
        return;
      }

      const promptKey = `${this.sessionId}:${this.closedByRole || 'unknown'}:${this.closedByName || 'unknown'}`;
      if (this.feedbackPromptedSessionKey === promptKey) {
        return;
      }

      this.feedbackPromptedSessionKey = promptKey;
      this.openFeedbackModal(this.currentFeedbackMode, {
        trigger: 'conversation_closed',
        session_id: this.sessionId,
        conversation_mode: this.currentMode,
      });
    },
    handleClosedConversationEvent() {
      const closerMatchesCurrentUser =
        (this.currentActorRole === 'expert' && this.closedByRole === 'expert' && this.closedByName === this.currentActorName) ||
        (this.currentActorRole !== 'expert' && this.closedByRole === 'user' && this.closedByName === this.currentActorName);

      if (closerMatchesCurrentUser) {
        this.successMessage = 'Conversation closed. Please share your feedback now.';
      } else if (this.closedByRole && this.closedByName) {
        this.successMessage = `${this.closedByRole === 'expert' ? 'Expert' : 'User'} ${this.closedByName} closed the conversation.`;
      } else {
        this.successMessage = 'Conversation closed.';
      }

      this.maybePromptFeedbackForClosedSession();
    },
    messageBubbleClass(message) {
      if (message.sender === this.currentActorRole) {
        return 'chat-workspace__bubble--user';
      }

      if (message.sender === 'assistant' && message.mode === 'expert') {
        return 'chat-workspace__bubble--system';
      }

      return 'chat-workspace__bubble--assistant';
    },
    messageMetaLabel(message) {
      if (message.sender === this.currentActorRole) {
        return `${this.currentActorRole === 'expert' ? 'Expert' : 'User'} - ${this.currentActorName}`;
      }

      if (message.sender === 'expert') {
        return `Expert - ${this.assignedExpertName || 'Assigned expert'}`;
      }

      if (message.sender === 'user') {
        return `User - ${this.sessionUserName || 'Conversation user'}`;
      }

      return 'System';
    },
    formatMessageContent(text) {
      const escapedText = this.escapeHtml(text || '');
      const linkifiedText = escapedText.replace(
        /(https?:\/\/[^\s<]+)/gi,
        (url) => `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`,
      );

      return linkifiedText.replace(/\n/g, '<br>');
    },
    messageDisplayText(message) {
      return this.stripInlineSourceNote(message?.text || '');
    },
    messageSources(message) {
      const rawSources = message?.debugInfo?.pageInput?.ulmGrounding?.sources?.length
        ? message.debugInfo.pageInput.ulmGrounding.sources
        : this.extractInlineSources(message?.text || '');
      const uniqueSources = [];
      const seenKeys = new Set();

      rawSources.forEach((source) => {
        const title = this.normalizeSourceTitle(source?.title);
        const url = typeof source?.url === 'string' && source.url.trim() ? source.url.trim() : null;

        if (!title) {
          return;
        }

        const dedupeKey = `${title}::${url || ''}`;
        if (seenKeys.has(dedupeKey)) {
          return;
        }

        seenKeys.add(dedupeKey);
        uniqueSources.push({
          title,
          url,
        });
      });

      return uniqueSources;
    },
    stripInlineSourceNote(text) {
      const normalizedText = String(text || '');
      return normalizedText
        .replace(/\n*\s*External sources used(?: include)?\s*:[\s\S]*$/i, '')
        .replace(/\n*\s*External sources used include[\s\S]*$/i, '')
        .trim();
    },
    extractInlineSources(text) {
      const normalizedText = String(text || '');
      const match = normalizedText.match(/External sources used(?: include)?\s*:?\s*([\s\S]*)$/i);

      if (!match?.[1]) {
        return [];
      }

      const sourceEntries = [];
      const sourcePattern = /([^,(]+?)\s*\((https?:\/\/[^)\s]+)\)/gi;
      let sourceMatch = sourcePattern.exec(match[1]);

      while (sourceMatch) {
        sourceEntries.push({
          title: sourceMatch[1].trim(),
          url: sourceMatch[2].trim(),
        });
        sourceMatch = sourcePattern.exec(match[1]);
      }

      return sourceEntries;
    },
    normalizeSourceTitle(title) {
      return String(title || '')
        .replace(/\s*\(Chunk\s+\d+\s*\/\s*\d+\)\s*$/i, '')
        .trim();
    },
    escapeHtml(value) {
      return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    },
    handleComposerKeydown(event) {
      if (event.key !== 'Enter' || event.shiftKey) {
        return;
      }

      event.preventDefault();

      if (this.isBusy || !this.draftMessage || this.sendDisabled) {
        return;
      }

      this.handleSendMessage();
    },
    async handleComposerFocus() {
      this.isComposerFocused = true;
      await this.setTypingState(true);
      this.startTypingHeartbeat();
    },
    async handleComposerBlur() {
      this.isComposerFocused = false;
      this.stopTypingHeartbeat();
      await this.setTypingState(false);
    },
    async handleComposerInput() {
      if (!this.isComposerFocused || this.isBusy || !this.sessionId || this.sessionStatus === 'closed') {
        return;
      }

      await this.setTypingState(true);
    },
    async ensureConversationSession() {
      if (this.sessionId) {
        return true;
      }

      const response = await chatService.startConversation({
        title: null,
        mode: 'system',
      });

      if (!response.success) {
        this.errorMessage = response.error?.message || 'Unable to start the conversation.';
        return false;
      }

      this.sessionId = response.data?.id || null;
      this.currentMode = response.data?.mode || 'system';
      this.sessionStatus = response.data?.status || 'active';
      this.sessionUserName = response.data?.user_name || this.sessionUserName;
      this.assignedExpertName = response.data?.assigned_expert_name || this.assignedExpertName;
      this.feedbackModeFromSession = response.data?.feedback_mode || this.feedbackModeFromSession;
      this.feedbackPendingForCurrentUser = Boolean(response.data?.feedback_pending_for_current_user);
      this.startPolling();
      return Boolean(this.sessionId);
    },
    async handleSendMessage() {
      if (!this.draftMessage || this.isBusy || this.sendDisabled) {
        return;
      }

      const draft = this.draftMessage;
      const isExpertAuthoring = this.currentActorRole === 'expert' && this.currentMode === 'expert';

      this.successMessage = '';
      this.errorMessage = '';

      if (!isExpertAuthoring) {
        const sessionReady = await this.ensureConversationSession();
        if (!sessionReady) {
          return;
        }
      } else if (!this.sessionId) {
        this.errorMessage = 'Select an assigned conversation to start collaborating.';
        return;
      }

      const localMessageId = `local-user-${Date.now()}`;

      this.messages.push({
        id: localMessageId,
        sender: isExpertAuthoring ? 'expert' : 'user',
        mode: this.currentMode,
        text: draft,
        createdAt: new Date().toISOString(),
      });
      this.scrollHistoryToBottom();
      this.draftMessage = '';
      this.stopTypingHeartbeat();
      await this.setTypingState(false);
      this.isBusy = true;
      this.isTyping = true;

      const response = isExpertAuthoring
        ? await chatService.sendExpertMessage({
            session_id: this.sessionId,
            content: draft,
          })
        : await chatService.sendMessage({
            session_id: this.sessionId,
            query: draft,
            use_synapse: true,
            use_uex: true,
            use_ulm: true,
          });

      if (response.success) {
        if (isExpertAuthoring) {
          this.successMessage = response.data?.expert_profile_updated
            ? 'Expert reply sent. Expert profile refinement state was updated.'
            : 'Expert reply sent.';
          await this.refreshConversation({ preserveError: true });
        } else {
          this.latestModulesUsed = response.data?.modules_used || [];
          await this.refreshConversation({ preserveError: true });
          this.storeResponseExpertAction(response.data);
          this.storeResponseDebugInfo(response.data);
          this.applyStoredDebugInfo();

          if (response.data?.expert_suggestion) {
            await this.loadExpertSuggestion(response.data.expert_suggestion);
            this.storeResponseExpertAction(response.data);
            this.applyStoredDebugInfo();
          } else {
            this.recommendedExpert = null;
          }
        }
      } else {
        this.errorMessage = response.error?.message || 'Unable to send the message.';
        this.messages = this.messages.filter((message) => message.id !== localMessageId);
        this.draftMessage = draft;
      }

      this.isBusy = false;
      this.isTyping = false;

      if (this.isComposerFocused && this.sessionStatus !== 'closed') {
        await this.setTypingState(true);
        this.startTypingHeartbeat();
      }
    },
    storeResponseDebugInfo(payload) {
      const assistantMessageId = Number(payload?.assistant_message_id || 0);
      if (!assistantMessageId || !payload?.debug) {
        return;
      }

      const pageInput = payload.debug.page_input
        ? {
            userMbti: payload.debug.page_input.user_mbti || '',
            query: payload.debug.page_input.query || '',
            uexKnowledge: payload.debug.page_input.uex_knowledge || 'No UEX knowledge available.',
            expertSuggestion: payload.debug.page_input.expert_suggestion
              ? {
                  name: payload.debug.page_input.expert_suggestion.name,
                  domainCodes: payload.debug.page_input.expert_suggestion.domain_codes || [],
                  isContactable: Boolean(payload.debug.page_input.expert_suggestion.is_contactable),
                  reason: payload.debug.page_input.expert_suggestion.reason || null,
                }
              : null,
            ulmGrounding: payload.debug.page_input.ulm_grounding
              ? {
                  summary: payload.debug.page_input.ulm_grounding.summary,
                  sourceCount: payload.debug.page_input.ulm_grounding.source_count || 0,
                  chunkCount: payload.debug.page_input.ulm_grounding.chunk_count || 0,
                  sources: (payload.debug.page_input.ulm_grounding.sources || []).map((source) => ({
                    title: source.title || null,
                    chunkIndex: source.chunk_index ?? null,
                    sourceType: source.source_type || null,
                    url: source.url || null,
                  })),
                }
              : null,
            ulmUsed: Boolean(payload.debug.page_input.ulm_used),
            conversationMode: payload.debug.page_input.conversation_mode || 'system',
          }
        : null;

      this.debugByMessageId = {
        ...this.debugByMessageId,
        [assistantMessageId]: {
          modulesUsed: payload.modules_used || [],
          synapse: payload.debug.synapse
            ? {
                storedMbti: payload.debug.synapse.stored_mbti || '',
                inferredMbti: payload.debug.synapse.inferred_mbti || '',
                effectiveMbti: payload.debug.synapse.effective_mbti || '',
                confidence: typeof payload.debug.synapse.confidence === 'number' ? payload.debug.synapse.confidence : null,
              }
            : null,
          inferredDomainCodes: payload.debug.inferred_domain_codes || [],
          uexKnowledgePreview: payload.debug.uex_knowledge_preview || '',
          uexKnowledgeItems: (payload.debug.uex_knowledge_items || []).map((item) => ({
            id: item.id,
            title: item.title,
            domainCode: item.domain_code,
          })),
          ulmChunks: (payload.debug.ulm_chunks || []).map((chunk) => ({
            sourceId: chunk.source_id,
            documentId: chunk.document_id,
            title: chunk.title,
            chunkIndex: chunk.chunk_index,
            sourceType: chunk.source_type,
            score: typeof chunk.score === 'number' ? chunk.score : null,
          })),
          page: payload.debug.page
            ? {
                styleLabel: payload.debug.page.style_label,
                intentLabel: payload.debug.page.intent_label,
                sections: payload.debug.page.sections || [],
              }
            : null,
          pageInput,
          expertSuggestionReason: payload.debug.expert_suggestion_reason || '',
        },
      };

      if (pageInput && !(assistantMessageId in this.pageMbtiOverrideByMessageId)) {
        this.pageMbtiOverrideByMessageId = {
          ...this.pageMbtiOverrideByMessageId,
          [assistantMessageId]: pageInput.userMbti || '',
        };
      }
    },
    storeResponseExpertAction(payload) {
      const assistantMessageId = Number(payload?.assistant_message_id || 0);
      if (!assistantMessageId) {
        return;
      }

      const suggestion = payload?.expert_suggestion;
      this.expertActionByMessageId = {
        ...this.expertActionByMessageId,
        [assistantMessageId]: suggestion && suggestion.is_contactable !== false
          ? {
              expertId: suggestion.expert_id,
              name: suggestion.name,
              totalScore: suggestion.total_score,
              isContactable: suggestion.is_contactable ?? false,
              reason: `The MIND backend suggested this expert with a match score of ${Number(suggestion.total_score || 0).toFixed(2)}.`,
            }
          : null,
      };
    },
    applyStoredDebugInfo() {
      this.messages = this.messages.map((message) => ({
        ...message,
        text: this.regeneratedPageResponseByMessageId[message.id] || message.text,
        debugInfo: this.debugByMessageId[message.id] || null,
        expertAction: this.expertActionByMessageId[message.id] || null,
      }));
    },
    async regeneratePageMessage(message) {
      const pageInput = message?.debugInfo?.pageInput;
      if (!message?.id || !pageInput || !this.canSeeDebugPanel) {
        return;
      }

      this.regeneratingPageMessageId = message.id;
      this.successMessage = '';
      this.errorMessage = '';

      try {
        const selectedMbti = this.pageMbtiOverrideByMessageId[message.id] || '';
        const response = await chatService.respondWithPage({
          user_profile: {
            mbti: selectedMbti || null,
          },
          query: pageInput.query,
          uex_knowledge: pageInput.uexKnowledge,
          expert_suggestion: pageInput.expertSuggestion
            ? {
                name: pageInput.expertSuggestion.name,
                domain_codes: pageInput.expertSuggestion.domainCodes,
                is_contactable: pageInput.expertSuggestion.isContactable,
                reason: pageInput.expertSuggestion.reason,
              }
            : null,
          ulm_grounding: pageInput.ulmGrounding
            ? {
                summary: pageInput.ulmGrounding.summary,
                source_count: pageInput.ulmGrounding.sourceCount,
                chunk_count: pageInput.ulmGrounding.chunkCount,
                sources: (pageInput.ulmGrounding.sources || []).map((source) => ({
                  title: source.title,
                  chunk_index: source.chunkIndex,
                  source_type: source.sourceType,
                  url: source.url,
                })),
              }
            : null,
          ulm_used: pageInput.ulmUsed,
          conversation_mode: pageInput.conversationMode,
        });

        if (response.success) {
          const regeneratedText = response.data?.response || message.text;
          this.regeneratedPageResponseByMessageId = {
            ...this.regeneratedPageResponseByMessageId,
            [message.id]: regeneratedText,
          };
          this.messages = this.messages.map((entry) => (
            entry.id === message.id
              ? {
                  ...entry,
                  text: regeneratedText,
                }
              : entry
          ));

          if (this.debugByMessageId[message.id]) {
            this.debugByMessageId = {
              ...this.debugByMessageId,
              [message.id]: {
                ...this.debugByMessageId[message.id],
                page: {
                  styleLabel: response.data?.style_label || this.debugByMessageId[message.id].page?.styleLabel || null,
                  intentLabel: response.data?.intent_label || this.debugByMessageId[message.id].page?.intentLabel || null,
                  sections: response.data?.sections || this.debugByMessageId[message.id].page?.sections || [],
                },
                pageInput: {
                  ...this.debugByMessageId[message.id].pageInput,
                  userMbti: selectedMbti || '',
                },
              },
            };
            this.applyStoredDebugInfo();
          }

          this.successMessage = `PAGE response regenerated${selectedMbti ? ` for ${selectedMbti}` : ' with DEFAULT style'}.`;
        } else {
          this.errorMessage = response.error?.message || 'Unable to regenerate the PAGE response.';
        }
      } catch (error) {
        this.errorMessage = error instanceof Error
          ? error.message
          : 'Unable to regenerate the PAGE response.';
      } finally {
        this.regeneratingPageMessageId = null;
      }
    },
    async handleHandoff() {
      if (this.isBusy || !this.sessionId || !this.recommendedExpert?.expertId) {
        return;
      }
      if (this.recommendedExpert.isContactable === false) {
        this.errorMessage = 'This expert is available in UEX, but does not have a provisioned COOGNIS account yet.';
        return;
      }

      this.isBusy = true;
      this.successMessage = '';
      this.errorMessage = '';

      const response = await chatService.handoffToExpert({
        session_id: this.sessionId,
        expert_id: this.recommendedExpert.expertId,
        reason: this.recommendedExpert.reason,
      });

      if (response.success) {
        this.currentMode = response.data?.to_mode || 'expert';
        this.successMessage = 'Conversation handed off to expert mode.';
        await this.refreshConversation({ preserveError: true });
        this.startPolling();
      } else {
        this.errorMessage = response.error?.message || 'Unable to hand off the conversation.';
      }

      this.isBusy = false;
    },
    async handleMessageHandoff(message) {
      if (!message?.expertAction) {
        return;
      }

      this.recommendedExpert = {
        ...(this.recommendedExpert || {}),
        expertId: message.expertAction.expertId,
        name: message.expertAction.name,
        isContactable: message.expertAction.isContactable,
        reason: message.expertAction.reason,
      };

      await this.handleHandoff();
    },
    async handleCloseConversation() {
      if (this.isBusy || !this.sessionId) {
        return;
      }

      this.isBusy = true;
      this.successMessage = '';
      this.errorMessage = '';

      const response = await chatService.closeConversation({
        session_id: this.sessionId,
      });

      if (response.success) {
        this.sessionStatus = response.data?.status || 'closed';
        await this.setTypingState(false);
        this.stopPolling();
        this.stopTypingHeartbeat();
        await this.refreshConversation({ preserveError: true });
      } else {
        this.errorMessage = response.error?.message || 'Unable to close the conversation.';
      }

      this.isBusy = false;
    },
    async handleFeedbackSubmit(payload) {
      this.isSubmittingFeedback = true;
      this.successMessage = '';
      this.errorMessage = '';

      const response = await chatService.submitFeedback({
        ...payload,
        context: this.feedbackContext,
        session_id: this.sessionId,
        conversation_mode: this.currentMode,
      });

      this.isSubmittingFeedback = false;

      if (response.success) {
        this.successMessage = payload.mode === 'expert'
          ? 'Expert interaction feedback recorded.'
          : 'System response feedback recorded.';
        this.feedbackPendingForCurrentUser = false;
        this.closeFeedbackModal();
      } else {
        this.errorMessage = response.error?.message || 'Unable to submit feedback.';
      }
    },
  },
};
</script>
