// Configuration
const CONFIG = {
    API_BASE: '/api',
    REFRESH_INTERVAL: 30000 // 30 seconds
};

// State Management
let state = {
    userId: null,
    language: localStorage.getItem('language') || 'en',
    persona: localStorage.getItem('persona') || 'supportive_friend',
    messages: [],
    isLoading: false
};

// DOM Elements
const elements = {
    messagesContainer: document.getElementById('messages'),
    messageInput: document.getElementById('message-input'),
    sendButton: document.getElementById('send-button'),
    languageSelect: document.getElementById('language-select'),
    personaSelect: document.getElementById('persona-select'),
    loadingSpinner: document.getElementById('loading'),
    moodHistory: document.getElementById('mood-history'),
    weeklySummary: document.getElementById('weekly-summary'),
    refreshStats: document.getElementById('refresh-stats'),
    quickActionButtons: document.querySelectorAll('.quick-action-btn')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
    loadMoodStats();
});

function initializeApp() {
    // Set initial language and persona
    elements.languageSelect.value = state.language;
    elements.personaSelect.value = state.persona;

    // Generate or retrieve user ID
    state.userId = getOrCreateUserId();

    // Focus on input
    elements.messageInput.focus();
}

function setupEventListeners() {
    // Send message
    elements.sendButton.addEventListener('click', sendMessage);
    elements.messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Settings
    elements.languageSelect.addEventListener('change', (e) => {
        state.language = e.target.value;
        localStorage.setItem('language', state.language);
    });

    elements.personaSelect.addEventListener('change', (e) => {
        state.persona = e.target.value;
        localStorage.setItem('persona', state.persona);
    });

    // Quick actions
    elements.quickActionButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const mood = btn.dataset.mood;
            logMood(mood);
        });
    });

    // Refresh stats
    elements.refreshStats.addEventListener('click', loadMoodStats);
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
async function sendMessage() {
    const content = elements.messageInput.value.trim();

    if (!content) return;
    if (state.isLoading) return;

    // Disable input
    setLoading(true);
    elements.messageInput.value = '';

    // Add user message to UI
    addMessageToUI('user', content);

    try {
        // Send to API
        const response = await fetch(`${CONFIG.API_BASE}/chat`, {
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
    elements.loadingSpinner.classList.toggle('hidden', !loading);
    elements.sendButton.disabled = loading;
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

// Auto-refresh stats periodically
setInterval(loadMoodStats, CONFIG.REFRESH_INTERVAL);
