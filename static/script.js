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
    weeklyStats: document.getElementById('weeklyStats')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    // Wait a bit for all DOM to be ready
    setTimeout(() => {
        checkUserName(); // Check if user has set their name first
        initializeApp();
        setupEventListeners();
        
        // Check if this is a psychologist session
        const psychSessionId = localStorage.getItem('psychologist_session_id');
        if (psychSessionId && state.isPsychologistSession) {
            state.currentSessionId = psychSessionId;
            loadPsychologistSession(psychSessionId);
            // Clear the flags after loading
            localStorage.removeItem('psychologist_session_id');
        } else {
            loadChatSessions();
        }
        
        loadMoodStats();
    }, 100);
});

// Check if user has set their name
async function checkUserName() {
    // TEMPORARILY DISABLED - Database migration needed
    // The full_name column needs to be added to users table first
    // Run database/add_user_profiles.sql in Supabase SQL Editor
    console.log('Name check disabled - database migration needed');
    return;
    
    const userId = localStorage.getItem('user_id');
    const token = localStorage.getItem('access_token');
    
    if (!userId || !token) return;
    
    try {
        const response = await fetch(`/api/user/profile`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'X-User-ID': userId
            }
        });
        
        const data = await response.json();
        
        if (!data.full_name || data.full_name === 'User') {
            // Show name setup modal
            document.getElementById('nameSetupModal').style.display = 'flex';
        } else {
            // Store name in localStorage for display
            localStorage.setItem('user_name', data.full_name);
            // Update display
            const userEmailEl = document.getElementById('userEmail');
            if (userEmailEl) {
                userEmailEl.textContent = data.full_name;
            }
        }
    } catch (error) {
        console.error('Error checking user name:', error);
    }
}

// Save user name
async function saveUserName(event) {
    event.preventDefault();
    
    const fullName = document.getElementById('fullNameInput').value.trim();
    const userId = localStorage.getItem('user_id');
    const token = localStorage.getItem('access_token');
    
    if (!fullName || fullName.length < 2) {
        alert('Please enter a valid name (at least 2 characters)');
        return;
    }
    
    try {
        const response = await fetch(`/api/user/profile`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'X-User-ID': userId,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ full_name: fullName })
        });
        
        if (!response.ok) {
            throw new Error('Failed to save name');
        }
        
        const data = await response.json();
        
        // Store name in localStorage
        localStorage.setItem('user_name', fullName);
        
        // Update display
        const userEmailEl = document.getElementById('userEmail');
        if (userEmailEl) {
            userEmailEl.textContent = fullName;
        }
        
        // Hide modal
        document.getElementById('nameSetupModal').style.display = 'none';
        
        console.log('✅ Name saved successfully');
    } catch (error) {
        console.error('Error saving name:', error);
        alert('Failed to save name. Please try again.');
    }
}


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
    const role = localStorage.getItem('role');
    const userEmailEl = document.getElementById('userEmail');
    if (userEmailEl && email) {
        userEmailEl.textContent = email;
    }

    // Add back to dashboard button for psychologists in psychologist sessions
    if (state.isPsychologistSession && role === 'psychologist') {
        const navbarRight = document.querySelector('.navbar-right');
        if (navbarRight && !document.getElementById('backToDashboard')) {
            const backBtn = document.createElement('button');
            backBtn.id = 'backToDashboard';
            backBtn.className = 'logout-btn';
            backBtn.textContent = '← Back to Dashboard';
            backBtn.onclick = () => {
                localStorage.removeItem('is_psychologist_chat');
                window.location.href = '/psychologist/dashboard.html';
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

        // Only add AI response if no psychologist present
        if (data.response && !data.has_psychologist) {
            addMessageToUI('assistant', data.response);
        } else if (data.has_psychologist) {
            console.log('👥 Psychologist is in this chat - waiting for human response');
        }

        // Log mood if detected
        if (data.mood_detected && data.mood_detected !== 'neutral') {
            logMoodSilent(data.mood_detected);
        }

        // Check for high-urgency emotions and show psychologist recommendations
        checkEmotionAndShowRecommendations(content);

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

function loadChatSessions(skipAutoSelect = false) {
    const userId = localStorage.getItem('user_id');
    const accessToken = localStorage.getItem('access_token');
    if (!userId) return;

    // Load both regular chat sessions and psychologist sessions
    Promise.all([
        fetch(`${CONFIG.API_BASE}/chat-sessions?userId=${userId}`).then(r => r.json())
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
            const label = session.has_psychologist ? ' (with Psychologist)' : '';
            
            html += `
                <div class="chat-session-item ${session.has_psychologist ? 'psychologist-session' : ''}">
                    <div onclick="loadSession('${session.id}')" style="flex: 1; cursor: pointer;">
                        <p class="session-title">${session.title}${label}</p>
                        <p class="session-date">${date}</p>
                    </div>
                    <button class="btn-delete-chat" onclick="deleteSession('${session.id}')" title="Delete chat">Delete</button>
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
            // Save to localStorage
            localStorage.setItem('current_session_id', data.session.id);
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
                // Clear any existing message refresh interval
                if (state.messageRefreshInterval) {
                    clearInterval(state.messageRefreshInterval);
                }
                
                state.currentSessionId = data.session.id;
                // Save to localStorage
                localStorage.setItem('current_session_id', data.session.id);
                
                // Clear messages and show welcome message
                elements.messagesContainer.innerHTML = `
                    <div class="message assistant">
                        <p>New chat created! How can I help you today?</p>
                    </div>
                `;
                
                // Load sessions but don't auto-select (skip redirect to first chat)
                loadChatSessions(true);
                
                // Start the message refresh for the new session
                state.messageRefreshInterval = setInterval(() => {
                    loadSessionMessages(data.session.id, true);
                }, 3000);
                
                // Focus on input
                elements.messageInput?.focus();
            }
        })
        .catch(error => console.error('Error creating chat:', error));
}

// Helper function to load messages for a specific session
function loadSessionMessages(sessionId, silent = false) {
    fetch(`${CONFIG.API_BASE}/chat-sessions/${sessionId}/messages?limit=50`)
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
                        
                        if (role === 'psychologist') {
                            role = 'assistant';
                            content = `${psychologistName}: ${content}`;
                        }
                        
                        newHTML += `<div class="message ${role}"><p>${content}</p></div>`;
                    });
                } else {
                    newHTML = '<div class="message assistant"><p>No messages in this chat yet. Start a conversation!</p></div>';
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
        fetch(`${CONFIG.API_BASE}/chat-sessions?userId=${userId}`)
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

    // Set up auto-refresh every 3 seconds for live updates
    state.messageRefreshInterval = setInterval(() => {
        loadSessionMessages(sessionId, true);
        checkPsychologistStatus(); // Also check for psychologist status updates
    }, 3000);
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

/**
 * Check user message for emotions and show psychologist recommendations if needed
 */
async function checkEmotionAndShowRecommendations(userMessage) {
    try {
        console.log('🔍 Analyzing emotion for message:', userMessage.substring(0, 100));
        
        const response = await fetch('/api/psychologist/analyze-emotion', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: userMessage
            })
        });

        if (!response.ok) {
            console.warn('Emotion analysis failed:', response.status);
            return;
        }

        const result = await response.json();
        const { emotion, urgency_level } = result;
        
        console.log(`📊 Analysis result - Emotion: ${emotion}, Urgency: ${urgency_level}`);

        // Show psychologist recommendations for high-urgency emotions
        if (window.psychologistRecommendations) {
            if (urgency_level === 'high') {
                console.log('🎯 High urgency detected - showing psychologist recommendations');
                window.psychologistRecommendations.showRecommendations(emotion, urgency_level);
            } else {
                console.log(`⚠️ Urgency level is ${urgency_level}, not showing recommendations`);
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

function showEndSessionModal() {
    // Reset rating
    selectedRating = 0;
    const stars = document.querySelectorAll('.rating-star');
    stars.forEach(star => {
        star.classList.remove('selected');
        star.textContent = '☆';
    });
    document.getElementById('sessionFeedback').value = '';
    
    // Show modal
    document.getElementById('endSessionModal').style.display = 'flex';
}

function closeEndSessionModal() {
    document.getElementById('endSessionModal').style.display = 'none';
}

async function submitEndSession() {
    const feedback = document.getElementById('sessionFeedback').value.trim();
    const userId = localStorage.getItem('user_id');
    const token = localStorage.getItem('access_token');
    
    console.log('🔚 Attempting to end session:', {
        sessionId: state.currentSessionId,
        userId: userId,
        hasToken: !!token,
        rating: selectedRating,
        feedback: feedback
    });
    
    if (!state.currentSessionId) {
        alert('No active session');
        return;
    }
    
    if (!userId || !token) {
        alert('Authentication error. Please log in again.');
        return;
    }
    
    // Rating is optional, but show warning if not provided
    if (selectedRating === 0) {
        if (!confirm('Are you sure you want to end the session without rating?')) {
            return;
        }
    }
    
    try {
        console.log('📤 Sending end session request...');
        const response = await fetch(`/api/chat-sessions/${state.currentSessionId}/end-psychologist-session`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
                'X-User-ID': userId
            },
            body: JSON.stringify({
                rating: selectedRating > 0 ? selectedRating : null,
                feedback: feedback
            })
        });
        
        console.log('📥 Response status:', response.status);
        const data = await response.json();
        console.log('📥 Response data:', data);
        
        if (response.ok && data.success) {
            closeEndSessionModal();
            alert('Session ended successfully. Thank you for your feedback!');
            
            // Reset state
            state.lastPsychologistStatus = null;
            
            // Refresh the chat sessions list
            loadChatSessions(true);
            
            // Reload current session to update UI
            if (state.currentSessionId) {
                loadSession(state.currentSessionId);
            }
        } else {
            console.error('❌ End session failed:', data);
            alert(data.error || 'Failed to end session. Please try again.');
        }
    } catch (error) {
        console.error('❌ Error ending session:', error);
        alert('Failed to end session: ' + error.message);
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
