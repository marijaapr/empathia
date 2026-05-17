// Configuration
const CONFIG = {
    API_BASE: '/api',
    REFRESH_INTERVAL: 30000 // 30 seconds
};

// State Management
let state = {
    userId: null,
    currentSessionId: null,
    language: localStorage.getItem('language') || 'en',
    persona: localStorage.getItem('persona') || 'supportive_friend',
    messages: [],
    isLoading: false
};

// DOM Elements
const elements = {
    messagesContainer: document.getElementById('chatMessages'),
    messageInput: document.getElementById('messageInput'),
    sendButton: document.querySelector('.btn-send'),
    languageSelect: document.getElementById('language-select'),
    personaSelect: document.getElementById('persona-select'),
    weeklyStats: document.getElementById('weeklyStats')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    // Wait a bit for all DOM to be ready
    setTimeout(() => {
        initializeApp();
        setupEventListeners();
        loadChatSessions();
        loadMoodStats();
    }, 100);
});

function initializeApp() {
    // Check if user is authenticated
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login';
        return;
    }

    // Set initial language and persona
    elements.languageSelect.value = state.language;
    elements.personaSelect.value = state.persona;

    // Use authenticated user ID from localStorage
    state.userId = localStorage.getItem('user_id') || getOrCreateUserId();

    // Display user email
    const email = localStorage.getItem('email');
    const userEmailEl = document.getElementById('userEmail');
    if (userEmailEl && email) {
        userEmailEl.textContent = email;
    }

    // Focus on input
    elements.messageInput?.focus();
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
        });
    }

    if (elements.personaSelect) {
        elements.personaSelect.addEventListener('change', (e) => {
            state.persona = e.target.value;
            localStorage.setItem('persona', state.persona);
        });
    }
}

// User Management
function getOrCreateUserId() {
    let userId = sessionStorage.getItem('userId');
    if (!userId) {
        userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        sessionStorage.setItem('userId', userId);
    }
    return userId;
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
    }

    // Disable input
    setLoading(true);
    elements.messageInput.value = '';

    // Add user message to UI
    addMessageToUI('user', content);

    try {
        // Send to session API
        const endpoint = `${CONFIG.API_BASE}/chat-sessions/${state.currentSessionId}/chat`;
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: content,
                language: state.language,
                persona: state.persona,
                userId: state.userId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        // Add assistant message to UI
        addMessageToUI('assistant', data.response);

        // Log mood if detected
        if (data.mood_detected && data.mood_detected !== 'neutral') {
            logMoodSilent(data.mood_detected);
        }

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

function addMessageToUI(role, content) {
    const messageEl = document.createElement('div');
    messageEl.className = `message ${role}`;

    const contentEl = document.createElement('div');
    contentEl.className = 'message-content';
    contentEl.textContent = content;

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
}

// Mood Functions
async function logMood(mood) {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/mood`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                mood: mood,
                userId: state.userId,
                language: state.language
            })
        });

        if (response.ok) {
            const data = await response.json();
            // Show system message
            const messages = {
                'en': `Great! I've logged your mood as "${mood}". ${data.message || ''}`,
                'mk': `Одлично! Го забележав твоето расположение како "${mood}". ${data.message || ''}`
            };
            addMessageToUI('system', messages[state.language] || messages['en']);

            // Refresh stats
            setTimeout(loadMoodStats, 500);
        }
    } catch (error) {
        console.error('Error logging mood:', error);
    }
}

async function logMoodSilent(mood) {
    try {
        await fetch(`${CONFIG.API_BASE}/mood`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                mood: mood,
                userId: state.userId,
                language: state.language
            })
        });

        // Refresh stats silently
        loadMoodStats();
    } catch (error) {
        console.error('Error logging mood:', error);
    }
}

// Stats Functions
async function loadMoodStats() {
    try {
        // Get mood history
        const historyResponse = await fetch(`${CONFIG.API_BASE}/mood-history?userId=${state.userId}`);
        if (historyResponse.ok) {
            const historyData = await historyResponse.json();
            displayMoodHistory(historyData.entries);
        }

        // Get weekly summary
        const summaryResponse = await fetch(`${CONFIG.API_BASE}/weekly-summary?userId=${state.userId}`);
        if (summaryResponse.ok) {
            const summaryData = await summaryResponse.json();
            displayWeeklySummary(summaryData.summary);
        }
    } catch (error) {
        console.error('Error loading mood stats:', error);
    }
}

function displayMoodHistory(entries) {
    if (!entries || entries.length === 0) {
        elements.moodHistory.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #999;">No mood history yet</p>';
        return;
    }

    elements.moodHistory.innerHTML = entries.slice(0, 7).map(entry => `
        <div class="mood-item">
            <div class="mood-item-label">${formatDate(entry.date)}</div>
            <div class="mood-item-value">${entry.mood}</div>
            <div class="mood-item-label">${entry.count} ${entry.count === 1 ? 'entry' : 'entries'}</div>
        </div>
    `).join('');
}

function displayWeeklySummary(summary) {
    if (!summary || summary.length === 0) {
        elements.weeklySummary.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #999;">No weekly data</p>';
        return;
    }

    const moodEmojis = {
        'happy': '😊',
        'sad': '😢',
        'anxious': '😰',
        'angry': '😠',
        'calm': '😌',
        'positive': '😊',
        'negative': '😢',
        'neutral': '😐'
    };

    elements.weeklySummary.innerHTML = summary.map(item => `
        <div class="summary-item">
            <div class="summary-item-label">${moodEmojis[item.mood] || '💭'} ${item.mood}</div>
            <div class="summary-item-value">${item.count}</div>
            <div class="summary-item-label">avg: ${item.avg_intensity.toFixed(1)}</div>
        </div>
    `).join('');
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (dateString === today.toISOString().split('T')[0]) {
        return 'Today';
    } else if (dateString === yesterday.toISOString().split('T')[0]) {
        return 'Yesterday';
    }

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// Logout function
function logout() {
    const token = localStorage.getItem('access_token');
    
    fetch('/api/auth/logout', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    }).then(() => {
        localStorage.clear();
        window.location.href = '/login';
    }).catch(error => {
        console.error('Logout error:', error);
        // Clear storage and redirect anyway
        localStorage.clear();
        window.location.href = '/login';
    });
}

// Chat History Functions
function loadChatHistory() {
    const userId = localStorage.getItem('user_id');
    if (!userId) {
        console.error('User ID not found');
        return;
    }

    fetch(`${CONFIG.API_BASE}/chat-history?userId=${userId}&limit=50`)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        })
        .then(data => {
            if (data.messages && elements.messagesContainer) {
                // Clear existing messages
                elements.messagesContainer.innerHTML = '';
                
                // Add all historical messages
                data.messages.forEach(msg => {
                    addMessageToUI(msg.role, msg.content);
                });
                
                console.log(`Loaded ${data.count} messages from history`);
            }
        })
        .catch(error => console.error('Error loading chat history:', error));
}

function loadMoodHistory() {
    alert('Mood history feature coming soon!');
}

function loadMoodStats() {
    // Load mood stats from API
    const userId = localStorage.getItem('user_id');
    if (!userId) return;
    
    fetch(`/api/weekly-summary?userId=${userId}`)
        .then(response => response.json())
        .then(data => {
            if (elements.weeklyStats && data.summary) {
                let statsHtml = '<h3>Weekly Summary</h3>';
                data.summary.forEach(item => {
                    statsHtml += `<p>${item.mood}: ${item.count} times</p>`;
                });
                if (data.insight) {
                    statsHtml += `<p><i>${data.insight}</i></p>`;
                }
                elements.weeklyStats.innerHTML = statsHtml;
            }
        })
        .catch(error => console.error('Error loading stats:', error));
}

function loadChatSessions() {
    const userId = localStorage.getItem('user_id');
    if (!userId) return;

    fetch(`${CONFIG.API_BASE}/chat-sessions?userId=${userId}`)
        .then(response => response.json())
        .then(data => {
            const sessionsList = document.getElementById('chatSessionsList');
            if (data.sessions && data.sessions.length > 0) {
                let html = '';
                data.sessions.forEach(session => {
                    const date = new Date(session.created_at).toLocaleDateString();
                    html += `
                        <div class="chat-session-item">
                            <div onclick="loadSession('${session.id}')" style="flex: 1; cursor: pointer;">
                                <p class="session-title">${session.title}</p>
                                <p class="session-date">${date}</p>
                            </div>
                            <button class="btn-delete-chat" onclick="deleteSession('${session.id}')" title="Delete chat">🗑️</button>
                        </div>
                    `;
                });
                sessionsList.innerHTML = html;
                
                // Load the first (most recent) session if no session is currently selected
                if (!state.currentSessionId && data.sessions.length > 0) {
                    loadSession(data.sessions[0].id);
                }
            } else {
                sessionsList.innerHTML = '<p>No chats yet</p>';
            }
        })
        .catch(error => console.error('Error loading chat sessions:', error));
}

async function createDefaultSession() {
    const userId = localStorage.getItem('user_id');
    if (!userId) return;

    try {
        const response = await fetch(`${CONFIG.API_BASE}/chat-sessions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                userId, 
                title: `Chat on ${new Date().toLocaleDateString()}`
            })
        });
        const data = await response.json();
        if (data.session) {
            state.currentSessionId = data.session.id;
            loadChatSessions();
        }
    } catch (error) {
        console.error('Error creating default session:', error);
    }
}

function createNewChat() {
    const userId = localStorage.getItem('user_id');
    if (!userId) return;

    const title = prompt('Enter chat name (optional):', `Chat on ${new Date().toLocaleDateString()}`);
    if (title === null) return;

    fetch(`${CONFIG.API_BASE}/chat-sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId, title })
    })
        .then(response => response.json())
        .then(data => {
            if (data.session) {
                state.currentSessionId = data.session.id;
                elements.messagesContainer.innerHTML = `
                    <div class="message assistant">
                        <p>New chat created! How can I help you today?</p>
                    </div>
                `;
                loadChatSessions();
            }
        })
        .catch(error => console.error('Error creating chat:', error));
}

function loadSession(sessionId) {
    state.currentSessionId = sessionId;
    const userId = localStorage.getItem('user_id');

    fetch(`${CONFIG.API_BASE}/chat-sessions/${sessionId}/messages?limit=50`)
        .then(response => response.json())
        .then(data => {
            if (elements.messagesContainer) {
                elements.messagesContainer.innerHTML = '';
                if (data.messages && data.messages.length > 0) {
                    data.messages.forEach(msg => {
                        addMessageToUI(msg.role, msg.content);
                    });
                } else {
                    addMessageToUI('assistant', 'No messages in this chat yet. Start a conversation!');
                }
            }
        })
        .catch(error => console.error('Error loading session:', error));
}

function deleteSession(sessionId) {
    if (!confirm('Are you sure you want to delete this chat? This action cannot be undone.')) {
        return;
    }

    fetch(`${CONFIG.API_BASE}/chat-sessions/${sessionId}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // If deleted session was the current one, clear messages
                if (state.currentSessionId === sessionId) {
                    state.currentSessionId = null;
                    elements.messagesContainer.innerHTML = '';
                }
                // Reload chat sessions
                loadChatSessions();
            } else {
                alert('Failed to delete chat');
            }
        })
        .catch(error => {
            console.error('Error deleting session:', error);
            alert('Error deleting chat');
        });
}

// Auto-refresh stats periodically
setInterval(loadMoodStats, CONFIG.REFRESH_INTERVAL);
