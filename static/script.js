// Configuration
const CONFIG = {
    API_BASE: '/api',
    REFRESH_INTERVAL: 30000 // 30 seconds
};

const MOOD_CHIPS = ['happy', 'sad', 'anxious', 'angry', 'calm', 'neutral'];

const CHAT_UI = {
    en: {
        newChatError: 'Failed to create chat. Please try again.',
        deleteTitle: 'Delete chat?',
        deleteBody: (name) => `Delete "${name}"? This cannot be undone.`,
        deleteError: 'Failed to delete chat. Please try again.',
        deleteSuccess: 'Chat deleted.',
        endNoSession: 'No active session.',
        endAuth: 'Please log in again.',
        endSuccess: 'Session ended. Thank you for your feedback!',
        endError: 'Failed to end session. Please try again.',
        endTitle: 'End Session with Psychology Student',
        endSubtitle: 'How was your experience?',
        endConfirmText: 'You have not selected a star rating. You can still end the session.',
        createChat: 'Create chat',
        creating: 'Creating…',
        goBack: 'Go back',
        endAnyway: 'End anyway',
        cancel: 'Cancel',
        endSession: 'End Session',
    },
    mk: {
        newChatError: 'Неуспешно креирање на разговор. Обиди се повторно.',
        deleteTitle: 'Избриши разговор?',
        deleteBody: (name) => `Да се избрише „${name}"? Ова не може да се врати.`,
        deleteError: 'Неуспешно бришење на разговор. Обиди се повторно.',
        deleteSuccess: 'Разговорот е избришан.',
        endNoSession: 'Нема активна сесија.',
        endAuth: 'Најави се повторно.',
        endSuccess: 'Сесијата заврши. Благодариме за повратните информации!',
        endError: 'Неуспешно завршување на сесијата. Обиди се повторно.',
        endTitle: 'Заврши сесија со студент по психологија',
        endSubtitle: 'Како беше твоето искуство?',
        endConfirmText: 'Не избра оценка. Сепак можеш да ја завршиш сесијата.',
        createChat: 'Креирај разговор',
        creating: 'Се креира…',
        goBack: 'Назад',
        endAnyway: 'Заврши сепак',
        cancel: 'Откажи',
        endSession: 'Заврши сесија',
    },
};

let pendingDeleteSessionId = null;

function chatT(key, ...args) {
    const lang = state.language === 'mk' ? 'mk' : 'en';
    const value = CHAT_UI[lang][key];
    if (typeof value === 'function') {
        return value(...args);
    }
    return value ?? CHAT_UI.en[key];
}

// State Management
let state = {
    userId: null,
    currentSessionId: null,
    language: localStorage.getItem('language') || 'en',
    persona: localStorage.getItem('persona') || 'supportive_friend',
    selectedMood: localStorage.getItem('selected_mood') || null,
    messages: [],
    isLoading: false,
    isPsychologistSession: localStorage.getItem('is_psychologist_chat') === 'true',
    messageRefreshInterval: null,
    lastPsychologistStatus: null  // Track last known psychologist status
};

// DOM Elements
const elements = {
    messagesContainer: document.getElementById('chatMessages'),
    messageInput: document.getElementById('messageInput'),
    sendButton: document.querySelector('.btn-send'),
    languageSelect: document.getElementById('language-select'),
    personaSelect: document.getElementById('persona-select'),
    weeklyStats: document.getElementById('weeklyStats'),
    moodStatus: document.getElementById('moodStatus'),
    typingIndicator: document.getElementById('typingIndicator')
};

function setUserDisplayName(name) {
    const display = (name || '').trim();
    const el = document.getElementById('userDisplayName');
    if (el && display) {
        el.textContent = display;
        localStorage.setItem('user_name', display);
    }
}

async function loadUserDisplayName() {
    const el = document.getElementById('userDisplayName');
    if (!el) return;

    const cached = localStorage.getItem('user_name');
    if (cached) {
        el.textContent = cached;
    }

    try {
        const response = await apiFetch('/api/user/profile');
        if (response.ok) {
            const data = await response.json();
            const name = (data.full_name || data.username || '').trim();
            if (name) {
                setUserDisplayName(name);
            }
        }
    } catch (error) {
        console.warn('Could not load user display name:', error);
    }
}

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(async () => {
        initializeApp();
        setupEventListeners();
        await loadUserDisplayName();

        const psychSessionId = localStorage.getItem('psychologist_session_id');
        if (psychSessionId && state.isPsychologistSession) {
            state.currentSessionId = psychSessionId;
            loadPsychologistSession(psychSessionId);
            localStorage.removeItem('psychologist_session_id');
        } else {
            loadChatSessions();
        }

        loadMoodStats();
        restoreMoodSelection();
    }, 100);
});

// Save user name (name-setup modal; enable when profile migration is ready)
async function saveUserName(event) {
    event.preventDefault();
    
    const fullName = document.getElementById('fullNameInput').value.trim();
    
    if (!fullName || fullName.length < 2) {
        alert('Please enter a valid name (at least 2 characters)');
        return;
    }
    
    try {
        const response = await apiFetch(`/api/user/profile`, {
            method: 'PUT',
            body: JSON.stringify({ full_name: fullName })
        });
        
        if (!response.ok) {
            throw new Error('Failed to save name');
        }
        
        const data = await response.json();
        
        // Store name in localStorage
        localStorage.setItem('user_name', fullName);
        
        // Update display
        setUserDisplayName(fullName);
        
        // Hide modal
        document.getElementById('nameSetupModal').style.display = 'none';
        
        console.log('✅ Name saved successfully');
    } catch (error) {
        console.error('Error saving name:', error);
        alert('Failed to save name. Please try again.');
    }
}


function initializeApp() {
    const token = localStorage.getItem('access_token');
    const userId = localStorage.getItem('user_id');
    if (!token || !userId) {
        window.location.href = '/login';
        return;
    }

    state.userId = userId;

    if (elements.languageSelect) {
        elements.languageSelect.value = state.language;
    }
    if (elements.personaSelect) {
        elements.personaSelect.value = state.persona;
    }

    const cachedName = localStorage.getItem('user_name');
    if (cachedName) {
        const userDisplayEl = document.getElementById('userDisplayName');
        if (userDisplayEl) {
            userDisplayEl.textContent = cachedName;
        }
    }

    CustomSelect.init(elements.languageSelect);
    CustomSelect.init(elements.personaSelect);
    CustomSelect.setValue(elements.languageSelect, state.language);
    CustomSelect.setValue(elements.personaSelect, state.persona);

    const role = localStorage.getItem('role');

    // Add back to dashboard button for psychologists in psychologist sessions
    if (state.isPsychologistSession && role === 'psychologist') {
        const navbarRight = document.querySelector('.navbar-right');
        if (navbarRight && !document.getElementById('backToDashboard')) {
            const backBtn = document.createElement('button');
            backBtn.id = 'backToDashboard';
            backBtn.className = 'btn-primary btn-logout';
            backBtn.textContent = '← Back to Dashboard';
            backBtn.onclick = () => {
                localStorage.removeItem('is_psychologist_chat');
                window.location.href = '/psychologist/dashboard';
            };
            navbarRight.insertBefore(backBtn, navbarRight.firstChild);
        }
    }

    // Focus on input
    elements.messageInput?.focus();
    
    // Auto-refresh chat sessions every 15 seconds to detect psychologist joins
    setInterval(() => {
        console.log('🔄 Auto-refreshing chat sessions...');
        loadChatSessions();
    }, 15000);
}

function setupEventListeners() {
    // Send message
    if (elements.sendButton) {
        elements.sendButton.addEventListener('click', sendMessage);
    }
    
    if (elements.messageInput) {
        elements.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    // Settings
    if (elements.languageSelect) {
        elements.languageSelect.addEventListener('change', (e) => {
            state.language = e.target.value;
            localStorage.setItem('language', state.language);
            applyEndSessionModalCopy();
            const moodLabels = {
                en: (m) => `Selected: ${capitalizeMood(m)}`,
                mk: (m) => `Избрано: ${capitalizeMood(m)}`,
            };
            if (state.selectedMood && elements.moodStatus) {
                const fn = moodLabels[state.language] || moodLabels.en;
                elements.moodStatus.textContent = fn(state.selectedMood);
            }
        });
    }

    if (elements.personaSelect) {
        elements.personaSelect.addEventListener('change', (e) => {
            state.persona = e.target.value;
            localStorage.setItem('persona', state.persona);
        });
    }
}

// Message Functions
async function sendMessage(event) {
    if (event) {
        event.preventDefault();
    }
    
    const content = elements.messageInput.value.trim();

    if (!content) return;
    if (state.isLoading) return;

    // If no session exists, create one first
    if (!state.currentSessionId) {
        await createDefaultSession();
        
        // Check again if session was created
        if (!state.currentSessionId) {
            console.error('Failed to create session');
            alert('Unable to create chat session. Please refresh the page.');
            return;
        }
    }

    // Disable input
    setLoading(true);
    elements.messageInput.value = '';

    // Add user message to UI
    addMessageToUI('user', content);

    try {
        // Send to session API
        const endpoint = `${CONFIG.API_BASE}/chat-sessions/${state.currentSessionId}/chat`;
        const response = await apiFetch(endpoint, {
            method: 'POST',
            body: JSON.stringify({
                message: content,
                language: state.language,
                persona: state.persona,
                userId: state.userId,
                selectedMood: state.selectedMood || undefined
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        // Only add AI response if no psychologist present
        if (data.response && !data.has_psychologist) {
            addMessageToUI('assistant', data.response);
        } else if (data.has_psychologist) {
            console.log('👥 Psychologist is in this chat - waiting for human response');
        }

        // Update mood chip if message implies a mood (no extra chat spam)
        if (data.mood_detected && MOOD_CHIPS.includes(data.mood_detected) && data.mood_detected !== 'neutral') {
            setMoodSelection(data.mood_detected, { persist: true, showStatus: true });
            logMoodSilent(data.mood_detected);
        }

        // Non-blocking crisis / student support check (after reply is visible)
        void checkEmotionAndShowRecommendations(content);

    } catch (error) {
        console.error('Error:', error);
        const errorMessages = {
            'en': 'Sorry, I encountered an error. Please try again.',
            'mk': 'Извините, наидов на грешка. Ве молиме обидитесе повторно.'
        };
        addMessageToUI('system', errorMessages[state.language] || errorMessages['en']);
    } finally {
        setLoading(false);
        elements.messageInput.focus();
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Turn plain text into safe HTML with paragraph blocks and line breaks.
 */
function formatMessageHtml(text) {
    const trimmed = String(text || '').trim();
    if (!trimmed) {
        return '<p class="message-paragraph"></p>';
    }
    const safe = escapeHtml(trimmed);
    const blocks = safe.split(/\n\s*\n+/);
    return blocks
        .map((block) => {
            const inner = block.replace(/\n/g, '<br>');
            return `<p class="message-paragraph">${inner}</p>`;
        })
        .join('');
}

function addMessageToUI(role, content) {
    const messageEl = document.createElement('div');
    messageEl.className = `message ${role}`;

    const contentEl = document.createElement('div');
    contentEl.className = 'message-content message-body';
    contentEl.innerHTML = formatMessageHtml(content);

    messageEl.appendChild(contentEl);
    elements.messagesContainer.appendChild(messageEl);

    // Scroll to bottom
    elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
}

function setLoading(loading) {
    state.isLoading = loading;
    if (elements.sendButton) {
        elements.sendButton.disabled = loading;
    }
    if (elements.messageInput) {
        elements.messageInput.disabled = loading;
    }
    const indicator = elements.typingIndicator;
    if (indicator && elements.messagesContainer) {
        elements.messagesContainer.appendChild(indicator);
        indicator.classList.toggle('hidden', !loading);
        indicator.setAttribute('aria-hidden', loading ? 'false' : 'true');
        if (loading) {
            elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
        }
    }
    const label = indicator?.querySelector('.chat-typing-label');
    if (label) {
        label.textContent = state.language === 'mk'
            ? 'Емпатија размислува…'
            : 'Empathia is thinking…';
    }
}

function capitalizeMood(mood) {
    if (!mood) return '';
    return mood.charAt(0).toUpperCase() + mood.slice(1);
}

function setMoodSelection(mood, options = {}) {
    const { persist = true, showStatus = true } = options;
    if (!mood || !MOOD_CHIPS.includes(mood)) return;

    state.selectedMood = mood;
    if (persist) {
        localStorage.setItem('selected_mood', mood);
    }

    document.querySelectorAll('.mood-btn').forEach((btn) => {
        btn.classList.toggle('active', btn.dataset.mood === mood);
    });

    if (showStatus && elements.moodStatus) {
        const labels = {
            en: `Selected: ${capitalizeMood(mood)}`,
            mk: `Избрано: ${capitalizeMood(mood)}`
        };
        elements.moodStatus.textContent = labels[state.language] || labels.en;
    }
}

function restoreMoodSelection() {
    const saved = state.selectedMood || localStorage.getItem('selected_mood');
    if (saved && MOOD_CHIPS.includes(saved)) {
        setMoodSelection(saved, { persist: false, showStatus: true });
    }
}

// Mood Functions
async function logMood(mood) {
    if (!MOOD_CHIPS.includes(mood)) return;

    setMoodSelection(mood, { persist: true, showStatus: true });

    try {
        const response = await apiFetch(`${CONFIG.API_BASE}/mood`, {
            method: 'POST',
            body: JSON.stringify({
                mood: mood,
                userId: state.userId,
                language: state.language
            })
        });

        if (response.ok) {
            setTimeout(loadMoodStats, 500);
        }
    } catch (error) {
        console.error('Error logging mood:', error);
    }
}

async function logMoodSilent(mood) {
    if (!mood || !MOOD_CHIPS.includes(mood) || mood === 'neutral') return;

    try {
        await apiFetch(`${CONFIG.API_BASE}/mood`, {
            method: 'POST',
            body: JSON.stringify({
                mood: mood,
                userId: state.userId,
                language: state.language
            })
        });

        loadMoodStats();
    } catch (error) {
        console.error('Error logging mood:', error);
    }
}

// Stats Functions
async function loadMoodStats() {
    if (!state.userId || !elements.weeklyStats) return;

    try {
        const summaryResponse = await apiFetch(
            `${CONFIG.API_BASE}/weekly-summary?userId=${state.userId}`
        );
        if (!summaryResponse.ok) return;

        const data = await summaryResponse.json();
        if (!data.summary || data.summary.length === 0) {
            elements.weeklyStats.innerHTML = '<p class="stats-empty">No mood data this week yet</p>';
            return;
        }

        let statsHtml = '<h3>Weekly Summary</h3>';
        data.summary.forEach(item => {
            statsHtml += `<p>${item.mood}: ${item.count} times</p>`;
        });
        if (data.insight) {
            statsHtml += `<p><i>${data.insight}</i></p>`;
        }
        elements.weeklyStats.innerHTML = statsHtml;
    } catch (error) {
        console.error('Error loading mood stats:', error);
    }
}

function loadChatSessions(skipAutoSelect = false) {
    const userId = localStorage.getItem('user_id');
    const accessToken = localStorage.getItem('access_token');
    if (!userId) return;

    // Load both regular chat sessions and psychologist sessions
    Promise.all([
        apiFetch(`${CONFIG.API_BASE}/chat-sessions?userId=${userId}`).then(r => r.json())
    ])
    .then(([chatData]) => {
        console.log('📊 Chat data:', chatData);
        
        const sessionsList = document.getElementById('chatSessionsList');
        const sessions = chatData.sessions || [];
        
        console.log(`✅ Found ${sessions.length} chat sessions`);
        
        if (sessions.length === 0) {
            sessionsList.innerHTML = '<p>No chats yet</p>';
            return;
        }
        
        let html = '';
        
        sessions.forEach(session => {
            console.log('💬 Chat session:', session);
            const date = new Date(session.created_at).toLocaleDateString();
            const label = session.has_psychologist ? ' (with student)' : '';
            
            html += `
                <div class="chat-session-item ${session.has_psychologist ? 'psychologist-session' : ''}">
                    <div onclick="loadSession('${session.id}')" style="flex: 1; cursor: pointer;">
                        <p class="session-title">${session.title}${label}</p>
                        <p class="session-date">${date}</p>
                    </div>
                    <button class="btn-delete-chat" onclick='openDeleteChatModal(${JSON.stringify(session.id)}, ${JSON.stringify(session.title || "Chat")})' title="Delete chat">Delete</button>
                </div>
            `;
        });
        
        // Only update if content has changed (prevents blinking)
        if (sessionsList.innerHTML !== html) {
            sessionsList.innerHTML = html;
        }
        
        // Skip auto-select when creating new chat or when explicitly requested
        if (skipAutoSelect) {
            return;
        }
        
        // Check if there's a specific session to load (from psychologist dashboard)
        const activeSessionId = localStorage.getItem('active_session_id');
        if (activeSessionId) {
            // Load the specified session
            loadSession(activeSessionId);
            // Clear the flag
            localStorage.removeItem('active_session_id');
        } else if (!state.currentSessionId) {
            // Load the first session if no session is currently selected
            if (sessions.length > 0) {
                loadSession(sessions[0].id);
            }
        }
    })
    .catch(error => console.error('Error loading chat sessions:', error));
}

async function createDefaultSession() {
    const userId = localStorage.getItem('user_id');
    if (!userId) return;

    try {
        const response = await apiFetch(`${CONFIG.API_BASE}/chat-sessions`, {
            method: 'POST',
            body: JSON.stringify({ 
                userId, 
                title: `Chat on ${new Date().toLocaleDateString()}`
            })
        });
        const data = await response.json();
        if (data.session) {
            state.currentSessionId = data.session.id;
            // Save to localStorage
            localStorage.setItem('current_session_id', data.session.id);
            loadChatSessions();
        }
    } catch (error) {
        console.error('Error creating default session:', error);
    }
}

function getDefaultChatTitle() {
    return `Chat on ${new Date().toLocaleDateString()}`;
}

function setInlineError(elId, message) {
    const el = document.getElementById(elId);
    if (!el) return;
    if (message) {
        el.textContent = message;
        el.hidden = false;
    } else {
        el.textContent = '';
        el.hidden = true;
    }
}

function openNewChatModal() {
    const modal = document.getElementById('newChatModal');
    const input = document.getElementById('newChatTitleInput');
    if (!modal) return;

    setInlineError('newChatFormError', '');
    if (input) {
        input.value = getDefaultChatTitle();
    }
    modal.style.display = 'flex';
    setTimeout(() => input?.focus(), 50);
    setTimeout(() => input?.select(), 80);
}

function closeNewChatModal() {
    const modal = document.getElementById('newChatModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function createNewChat() {
    const userId = localStorage.getItem('user_id');
    if (!userId) {
        window.location.href = '/login';
        return;
    }
    openNewChatModal();
}

function submitNewChat(event) {
    event.preventDefault();

    const userId = localStorage.getItem('user_id');
    const input = document.getElementById('newChatTitleInput');
    const title = (input?.value || '').trim() || getDefaultChatTitle();

    if (!userId) return;

    setInlineError('newChatFormError', '');

    const submitBtn = document.querySelector('#newChatForm button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = chatT('creating');
    }

    apiFetch(`${CONFIG.API_BASE}/chat-sessions`, {
        method: 'POST',
        body: JSON.stringify({ userId, title })
    })
        .then(async (response) => {
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || chatT('newChatError'));
            }
            return data;
        })
        .then(data => {
            if (data.session) {
                closeNewChatModal();

                if (state.messageRefreshInterval) {
                    clearInterval(state.messageRefreshInterval);
                }

                state.currentSessionId = data.session.id;
                localStorage.setItem('current_session_id', data.session.id);

                elements.messagesContainer.innerHTML = `
                    <div class="message assistant">
                        <div class="message-content message-body">
                            <p class="message-paragraph">New chat created! How can I help you today?</p>
                        </div>
                    </div>
                `;

                loadChatSessions(true);

                state.messageRefreshInterval = setInterval(() => {
                    loadSessionMessages(data.session.id, true);
                }, 2000);

                elements.messageInput?.focus();
            }
        })
        .catch(error => {
            console.error('Error creating chat:', error);
            setInlineError('newChatFormError', error.message || chatT('newChatError'));
        })
        .finally(() => {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = chatT('createChat');
            }
        });
}

function openDeleteChatModal(sessionId, chatTitle) {
    pendingDeleteSessionId = sessionId;
    const modal = document.getElementById('deleteChatModal');
    const titleEl = document.getElementById('deleteChatModalTitle');
    const bodyEl = document.getElementById('deleteChatModalBody');
    if (!modal) return;

    setInlineError('deleteChatFormError', '');

    const chatName = (chatTitle || 'Chat').replace(/\s*\(with student\)\s*$/i, '').trim() || 'Chat';

    if (titleEl) titleEl.textContent = chatT('deleteTitle');
    if (bodyEl) bodyEl.textContent = chatT('deleteBody', chatName);

    modal.style.display = 'flex';
}

function closeDeleteChatModal() {
    pendingDeleteSessionId = null;
    const modal = document.getElementById('deleteChatModal');
    if (modal) modal.style.display = 'none';
    setInlineError('deleteChatFormError', '');
}

function confirmDeleteChat() {
    if (!pendingDeleteSessionId) return;

    setInlineError('deleteChatFormError', '');
    const deleteBtn = document.querySelector('#deleteChatModal .btn-danger');
    if (deleteBtn) {
        deleteBtn.disabled = true;
    }

    apiFetch(`${CONFIG.API_BASE}/chat-sessions/${pendingDeleteSessionId}`, {
        method: 'DELETE'
    })
        .then(async (response) => {
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.error || chatT('deleteError'));
            }
            return data;
        })
        .then(() => {
            const deletedId = pendingDeleteSessionId;
            closeDeleteChatModal();
            showToast(chatT('deleteSuccess'), 'success');

            if (state.currentSessionId === deletedId) {
                state.currentSessionId = null;
                localStorage.removeItem('current_session_id');
                if (elements.messagesContainer) {
                    elements.messagesContainer.innerHTML = '';
                }
            }
            loadChatSessions();
        })
        .catch(error => {
            console.error('Error deleting session:', error);
            setInlineError('deleteChatFormError', error.message || chatT('deleteError'));
        })
        .finally(() => {
            if (deleteBtn) deleteBtn.disabled = false;
        });
}

function deleteSession(sessionId) {
    openDeleteChatModal(sessionId);
}

// Modal backdrop click + Escape
document.addEventListener('click', (e) => {
    if (e.target.id === 'newChatModal') closeNewChatModal();
    if (e.target.id === 'deleteChatModal') closeDeleteChatModal();
    if (e.target.id === 'endSessionModal') closeEndSessionModal();
});

document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (document.getElementById('newChatModal')?.style.display === 'flex') closeNewChatModal();
    if (document.getElementById('deleteChatModal')?.style.display === 'flex') closeDeleteChatModal();
    if (document.getElementById('endSessionModal')?.style.display === 'flex') closeEndSessionModal();
});

// Helper function to load messages for a specific session
function loadSessionMessages(sessionId, silent = false) {
    apiFetch(`${CONFIG.API_BASE}/chat-sessions/${sessionId}/messages?limit=50`)
        .then(response => response.json())
        .then(data => {
            if (elements.messagesContainer && state.currentSessionId === sessionId) {
                const wasAtBottom = elements.messagesContainer.scrollHeight - elements.messagesContainer.scrollTop <= elements.messagesContainer.clientHeight + 50;
                
                // Build HTML string
                let newHTML = '';
                const psychologistName = data.psychologist_name || 'Psychologist';
                
                // Update button based on has_psychologist status from API
                if (data.has_psychologist !== undefined) {
                    console.log('📊 Has psychologist from messages API:', data.has_psychologist);
                    if (state.lastPsychologistStatus !== data.has_psychologist) {
                        console.log('📊 Psychologist status changed via messages:', {
                            was: state.lastPsychologistStatus,
                            now: data.has_psychologist
                        });
                        state.lastPsychologistStatus = data.has_psychologist;
                        updateEndSessionButton(data.has_psychologist);
                    }
                }
                
                if (data.messages && data.messages.length > 0) {
                    data.messages.forEach(msg => {
                        let role = msg.role;
                        let content = msg.content;
                        let formattedContent;
                        
                        // Handle different message roles
                        if (role === 'psychologist') {
                            role = 'assistant';
                            // Format: <strong>Name:</strong> message (with HTML allowed)
                            formattedContent = `<strong>${psychologistName}:</strong> ${formatMessageHtml(content)}`;
                        } else if (role === 'system') {
                            // System messages like "Psychologist joined"
                            role = 'system';
                            formattedContent = formatMessageHtml(content);
                        } else {
                            // Regular messages (user, assistant)
                            formattedContent = formatMessageHtml(content);
                        }
                        
                        newHTML += `<div class="message ${role}"><div class="message-content message-body">${formattedContent}</div></div>`;
                    });
                } else {
                    newHTML = '<div class="message assistant"><div class="message-content message-body"><p class="message-paragraph">No messages in this chat yet. Start a conversation!</p></div></div>';
                }
                
                // Only update if content has changed (prevents blinking)
                if (elements.messagesContainer.innerHTML !== newHTML) {
                    elements.messagesContainer.innerHTML = newHTML;
                    
                    // Auto-scroll to bottom if was near bottom
                    if (wasAtBottom) {
                        elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
                    }
                }
            }
        })
        .catch(error => {
            if (!silent) {
                console.error('Error loading session:', error);
            }
        });
}

function loadSession(sessionId) {
    state.currentSessionId = sessionId;
    state.isPsychologistSession = false;  // Reset flag
    state.lastPsychologistStatus = null;  // Reset status tracking
    
    // Save to localStorage so psychologist-recommendations.js can access it
    localStorage.setItem('current_session_id', sessionId);
    
    const userId = localStorage.getItem('user_id');

    // Clear any existing refresh interval
    if (state.messageRefreshInterval) {
        clearInterval(state.messageRefreshInterval);
    }
    
    // Function to check and update end session button
    const checkPsychologistStatus = () => {
        apiFetch(`${CONFIG.API_BASE}/chat-sessions?userId=${userId}`)
            .then(response => response.json())
            .then(data => {
                console.log('🔍 Full session data:', data);
                const currentSession = data.sessions?.find(s => s.id === sessionId);
                console.log('🔍 Current session found:', currentSession);
                if (currentSession) {
                    const hasPsychologist = currentSession.has_psychologist;
                    console.log('🔍 Has psychologist value:', hasPsychologist, 'Type:', typeof hasPsychologist);
                    
                    // Update if status changed OR if this is the first check (was null)
                    if (state.lastPsychologistStatus !== hasPsychologist) {
                        console.log('📊 Psychologist status changed:', {
                            id: sessionId,
                            was: state.lastPsychologistStatus,
                            now: hasPsychologist
                        });
                        state.lastPsychologistStatus = hasPsychologist;
                        updateEndSessionButton(hasPsychologist);
                    } else {
                        console.log('ℹ️ No status change detected');
                    }
                }
            })
            .catch(error => console.error('Error checking session status:', error));
    };
    
    // Check initially and update button immediately
    checkPsychologistStatus();

    // Load messages initially
    loadSessionMessages(sessionId);

    // Set up auto-refresh every 2 seconds for live updates (faster for real-time feel)
    state.messageRefreshInterval = setInterval(() => {
        loadSessionMessages(sessionId, true);
        checkPsychologistStatus(); // Also check for psychologist status updates
    }, 2000);
}

/**
 * Check user message for emotions and show psychologist recommendations if needed
 */
async function checkEmotionAndShowRecommendations(userMessage) {
    try {
        console.log('🔍 Analyzing emotion for message:', userMessage.substring(0, 100));
        
        const response = await apiFetch('/api/psychologist/analyze-emotion', {
            method: 'POST',
            body: JSON.stringify({
                message: userMessage,
                language: state.language
            })
        });

        if (!response.ok) {
            console.warn('Emotion analysis failed:', response.status);
            return;
        }

        const result = await response.json();
        const { emotion, urgency_level, suggest_student_support } = result;
        
        console.log(`📊 Analysis result - Emotion: ${emotion}, Urgency: ${urgency_level}, Suggest: ${suggest_student_support}`);

        if (window.psychologistRecommendations) {
            if (suggest_student_support) {
                console.log('🎯 Suggesting psychology student support');
                window.psychologistRecommendations.showRecommendations(
                    emotion,
                    urgency_level,
                    true
                );
            } else {
                console.log(`ℹ️ No auto-suggest (urgency=${urgency_level})`);
            }
        } else {
            console.warn('⚠️ psychologistRecommendations not initialized');
        }
    } catch (error) {
        console.error('❌ Emotion analysis error:', error);
    }
}

// Initialize Psychologist Recommendations module when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (typeof PsychologistRecommendations !== 'undefined') {
        window.psychologistRecommendations = new PsychologistRecommendations();
        console.log('✅ Psychologist Recommendations module initialized');
    } else {
        console.warn('⚠️ PsychologistRecommendations class not found');
    }
});

// Auto-refresh stats periodically
setInterval(loadMoodStats, CONFIG.REFRESH_INTERVAL);

// ============================================================================
// USER END SESSION WITH PSYCHOLOGIST - RATING SYSTEM
// ============================================================================

let selectedRating = 0;

function selectRating(rating) {
    selectedRating = rating;
    const stars = document.querySelectorAll('.rating-star');
    stars.forEach((star, index) => {
        if (index < rating) {
            star.classList.add('selected');
            star.textContent = '★';
        } else {
            star.classList.remove('selected');
            star.textContent = '☆';
        }
    });
}

// Add hover effect for stars
document.addEventListener('DOMContentLoaded', function() {
    const stars = document.querySelectorAll('.rating-star');
    stars.forEach((star, index) => {
        star.addEventListener('mouseenter', function() {
            const rating = parseInt(star.dataset.rating);
            stars.forEach((s, i) => {
                if (i < rating) {
                    s.classList.add('hover');
                    s.textContent = '★';
                }
            });
        });
        
        star.addEventListener('mouseleave', function() {
            stars.forEach((s, i) => {
                s.classList.remove('hover');
                if (i < selectedRating) {
                    s.textContent = '★';
                } else {
                    s.textContent = '☆';
                }
            });
        });
    });
});

function applyEndSessionModalCopy() {
    const title = document.getElementById('endSessionTitle');
    const subtitle = document.getElementById('endSessionSubtitle');
    const confirmText = document.getElementById('endSessionConfirmText');
    if (title) title.textContent = chatT('endTitle');
    if (subtitle) subtitle.textContent = chatT('endSubtitle');
    if (confirmText) confirmText.textContent = chatT('endConfirmText');

    const ratingPanel = document.getElementById('endSessionPanelRating');
    if (ratingPanel) {
        const cancelBtn = ratingPanel.querySelector('.btn-modal-secondary');
        const endBtn = ratingPanel.querySelector('.btn-send');
        if (cancelBtn) cancelBtn.textContent = chatT('cancel');
        if (endBtn) endBtn.textContent = chatT('endSession');
    }
    const confirmPanel = document.getElementById('endSessionPanelConfirm');
    if (confirmPanel) {
        const backBtn = confirmPanel.querySelector('.btn-modal-secondary');
        const anywayBtn = confirmPanel.querySelector('.btn-send');
        if (backBtn) backBtn.textContent = chatT('goBack');
        if (anywayBtn) anywayBtn.textContent = chatT('endAnyway');
    }
}

function showEndSessionRatingPanel() {
    document.getElementById('endSessionPanelRating')?.removeAttribute('hidden');
    document.getElementById('endSessionPanelConfirm')?.setAttribute('hidden', '');
    setInlineError('endSessionFormError', '');
}

function showEndSessionConfirmPanel() {
    document.getElementById('endSessionPanelRating')?.setAttribute('hidden', '');
    document.getElementById('endSessionPanelConfirm')?.removeAttribute('hidden');
    setInlineError('endSessionFormError', '');
}

function showEndSessionModal() {
    selectedRating = 0;
    const stars = document.querySelectorAll('.rating-star');
    stars.forEach(star => {
        star.classList.remove('selected');
        star.textContent = '☆';
    });
    const feedbackEl = document.getElementById('sessionFeedback');
    if (feedbackEl) feedbackEl.value = '';

    applyEndSessionModalCopy();
    showEndSessionRatingPanel();
    document.getElementById('endSessionModal').style.display = 'flex';
}

function closeEndSessionModal() {
    document.getElementById('endSessionModal').style.display = 'none';
    showEndSessionRatingPanel();
    setInlineError('endSessionFormError', '');
}

function submitEndSession() {
    setInlineError('endSessionFormError', '');

    if (!state.currentSessionId) {
        showToast(chatT('endNoSession'), 'error');
        return;
    }

    if (!localStorage.getItem('user_id') || !localStorage.getItem('access_token')) {
        showToast(chatT('endAuth'), 'error');
        return;
    }

    if (selectedRating === 0) {
        showEndSessionConfirmPanel();
        return;
    }

    void performEndSession();
}

function confirmEndSessionWithoutRating() {
    void performEndSession();
}

async function performEndSession() {
    const feedback = document.getElementById('sessionFeedback')?.value.trim() || '';
    setInlineError('endSessionFormError', '');

    const endBtn = document.querySelector('#endSessionPanelRating .btn-send');
    const confirmBtn = document.querySelector('#endSessionPanelConfirm .btn-send');
    [endBtn, confirmBtn].forEach((btn) => {
        if (btn) btn.disabled = true;
    });

    try {
        const response = await apiFetch(
            `/api/chat-sessions/${state.currentSessionId}/end-psychologist-session`,
            {
                method: 'POST',
                body: JSON.stringify({
                    rating: selectedRating > 0 ? selectedRating : null,
                    feedback: feedback,
                }),
            }
        );

        const data = await response.json();

        if (response.ok && data.success) {
            closeEndSessionModal();
            showToast(chatT('endSuccess'), 'success');
            state.lastPsychologistStatus = null;
            loadChatSessions(true);
            if (state.currentSessionId) {
                loadSession(state.currentSessionId);
            }
        } else {
            setInlineError('endSessionFormError', data.error || chatT('endError'));
        }
    } catch (error) {
        console.error('Error ending session:', error);
        setInlineError('endSessionFormError', error.message || chatT('endError'));
    } finally {
        [endBtn, confirmBtn].forEach((btn) => {
            if (btn) btn.disabled = false;
        });
    }
}

// Check if current session has psychologist and show end button
function updateEndSessionButton(hasPsychologist) {
    console.log('🔘 updateEndSessionButton called, hasPsychologist:', hasPsychologist);
    
    // Get existing button container
    const existingContainer = document.querySelector('.end-session-container');
    
    if (hasPsychologist) {
        console.log('✅ Psychologist is present, ensuring button exists');
        
        // If button already exists, don't recreate it
        if (existingContainer) {
            console.log('ℹ️ Button already exists, keeping it');
            return;
        }
        
        // Add end session button to chat settings panel
        const settingsPanel = document.querySelector('.chat-settings-panel');
        if (settingsPanel) {
            const endBtnContainer = document.createElement('div');
            endBtnContainer.className = 'settings-card end-session-container';
            endBtnContainer.innerHTML = `
                <button class="end-session-btn" onclick="showEndSessionModal()" style="
                    background: #dc3545;
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 600;
                    width: 100%;
                    transition: background 0.3s;
                " onmouseover="this.style.background='#c82333'" onmouseout="this.style.background='#dc3545'">
                    End Session & Rate
                </button>
            `;
            settingsPanel.appendChild(endBtnContainer);
            console.log('✅ End session button added to settings panel');
        } else {
            console.error('❌ Settings panel not found!');
        }
    } else {
        console.log('⚠️ No psychologist in session, removing button if exists');
        // Remove button if psychologist left
        if (existingContainer) {
            existingContainer.remove();
            console.log('✅ Button removed');
        }
    }
}
