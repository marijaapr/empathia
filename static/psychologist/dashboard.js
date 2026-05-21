/**
 * Psychologist Dashboard JavaScript
 * Handles all dashboard functionality including status toggling, notifications, and session management
 */

// ============================================================================
// INITIALIZATION & SETUP
// ============================================================================

let currentUserId = localStorage.getItem('user_id');
let currentUserEmail = localStorage.getItem('email');
let currentRole = localStorage.getItem('role');
let currentAccessToken = localStorage.getItem('access_token');

// Check authentication on page load
document.addEventListener('DOMContentLoaded', function() {
    if (!currentUserId || currentRole !== 'psychologist') {
        window.location.href = '/login';
        return;
    }

    // Initialize dashboard
    initializeDashboard();
});

function setPsychologistDisplayName(name) {
    const el = document.getElementById('psychologistDisplayName');
    const trimmed = (name || '').trim();
    if (!el || !trimmed) return;
    el.textContent = trimmed;
    localStorage.setItem('user_name', trimmed);
}

function initPsychologistDisplayName() {
    const cached = localStorage.getItem('user_name');
    if (cached) {
        setPsychologistDisplayName(cached);
    }
}

function initializeDashboard() {
    console.log('Initializing dashboard for psychologist:', currentUserEmail);

    initPsychologistDisplayName();
    
    // Load psychologist profile
    loadPsychologistProfile();
    
    // Load dashboard data
    loadDashboardData();
    
    // Setup online toggle listener
    setupOnlineToggle();
    
    // Setup chat input Enter key handler
    setupChatInputHandler();
    
    // Start SSE stream for new requests (replaces polling)
    startRequestStream();
}

function setupChatInputHandler() {
    // Add event listener for Enter key on chat input
    document.addEventListener('keydown', function(e) {
        const chatInput = document.getElementById('chatInputInDashboard');
        if (chatInput && document.activeElement === chatInput) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const form = chatInput.closest('form');
                if (form) {
                    const event = new Event('submit', { bubbles: true, cancelable: true });
                    form.dispatchEvent(event);
                }
            }
        }
    });
}

// ============================================================================
// ONLINE STATUS TOGGLE
// ============================================================================

function setupOnlineToggle() {
    const onlineToggle = document.getElementById('onlineToggle');
    
    if (onlineToggle) {
        onlineToggle.addEventListener('change', function() {
            toggleOnlineStatus(this.checked);
        });
        
        // Load current online status
        loadOnlineStatus();
    }
}

function toggleOnlineStatus(isOnline) {
    const btn = document.getElementById('onlineToggle');
    btn.disabled = true;
    
    apiFetch('/api/psychologist/online-status', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${currentAccessToken}`,
            'X-User-ID': currentUserId
        },
        body: JSON.stringify({
            is_online: isOnline
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.id || data.success) {
            updateStatusIndicator(isOnline);
            showNotification(`Status changed to ${isOnline ? 'Online' : 'Offline'}`);
        } else {
            throw new Error(data.error || 'Failed to update status');
        }
    })
    .catch(error => {
        console.error('Error updating status:', error);
        showNotification('Failed to update status', 'error');
        btn.checked = !isOnline;
    })
    .finally(() => {
        btn.disabled = false;
    });
}

function loadOnlineStatus() {
    apiFetch('/api/psychologist/profile', {
        headers: {
            'Authorization': `Bearer ${currentAccessToken}`,
            'X-User-ID': currentUserId
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('📡 Loaded profile data:', data);
        // Backend returns profile directly, not wrapped in {profile: ...}
        if (data && data.is_online !== undefined) {
            console.log('✅ Setting online status:', data.is_online);
            document.getElementById('onlineToggle').checked = data.is_online;
            updateStatusIndicator(data.is_online);
        } else {
            console.warn('⚠️ No is_online field in profile data');
        }
    })
    .catch(error => console.error('Error loading online status:', error));
}

function updateStatusIndicator(isOnline) {
    const indicator = document.querySelector('.status-indicator');
    const text = document.getElementById('statusText');
    
    if (indicator) {
        if (isOnline) {
            indicator.classList.add('online');
            indicator.classList.remove('offline');
        } else {
            indicator.classList.add('offline');
            indicator.classList.remove('online');
        }
    }
    
    if (text) {
        text.textContent = isOnline ? 'Online' : 'Offline';
    }
    
    // Also update profile section indicator if visible
    updateProfileStatusIndicator(isOnline);
}

function updateProfileStatusIndicator(isOnline) {
    const profileIndicator = document.getElementById('statusIndicatorProfile');
    const profileText = document.getElementById('statusTextProfile');
    
    if (profileIndicator) {
        if (isOnline) {
            profileIndicator.classList.add('online');
            profileIndicator.classList.remove('offline');
        } else {
            profileIndicator.classList.add('offline');
            profileIndicator.classList.remove('online');
        }
    }
    
    if (profileText) {
        profileText.textContent = isOnline ? 'Online' : 'Offline';
    }
}

// ============================================================================
// PROFILE LOADING
// ============================================================================

function loadPsychologistProfile() {
    apiFetch('/api/psychologist/profile', {
        headers: {
            'Authorization': `Bearer ${currentAccessToken}`,
            'X-User-ID': currentUserId
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('📥 Profile data received:', data);
        // Handle both data.profile and direct profile response
        const profile = data.profile || data;
        if (profile && profile.id) {
            updateProfileDisplay(profile);
        } else {
            console.log('⚠️ No profile found or profile missing id');
        }
    })
    .catch(error => console.error('Error loading profile:', error));
}

function updateProfileDisplay(profile) {
    console.log('📋 Updating profile display with:', profile);

    const displayName = (profile.full_name || '').trim();
    if (displayName) {
        setPsychologistDisplayName(displayName);
    }
    
    // Update profile form if visible
    if (document.getElementById('profileFullName')) {
        document.getElementById('profileFullName').value = profile.full_name || '';
        console.log('✓ Full Name:', profile.full_name);
    }
    if (document.getElementById('profileBio')) {
        document.getElementById('profileBio').value = profile.bio || '';
    }
    if (document.getElementById('profileSessionRate')) {
        document.getElementById('profileSessionRate').value = profile.session_rate_usd || '';
    }
    if (document.getElementById('profileResponseTime')) {
        document.getElementById('profileResponseTime').value = profile.average_response_time_minutes || '';
    }
    if (document.getElementById('profileSpecializations')) {
        const specs = Array.isArray(profile.specializations) 
            ? profile.specializations.join(', ') 
            : profile.specializations || '';
        document.getElementById('profileSpecializations').value = specs;
    }
    if (document.getElementById('profileLanguages')) {
        const langs = Array.isArray(profile.languages_spoken) 
            ? profile.languages_spoken.join(', ') 
            : profile.languages_spoken || '';
        document.getElementById('profileLanguages').value = langs;
    }
    
    // Update profile picture
    const profilePictureEl = document.getElementById('profilePicture');
    if (profilePictureEl) {
        if (profile.profile_image_url) {
            profilePictureEl.src = profile.profile_image_url;
            console.log('✓ Profile Picture loaded from database');
        } else {
            // Use default placeholder
            profilePictureEl.src = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22200%22%3E%3Crect fill=%22%23ddd%22 width=%22200%22 height=%22200%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-family=%22Arial%22 font-size=%2216%22 fill=%22%23666%22%3ENo Profile Picture%3C/text%3E%3C/svg%3E';
            console.log('⚠️ No profile picture URL in database');
        }
    }
    
    // Update status indicator in profile
    if (profile.is_online !== undefined) {
        updateProfileStatusIndicator(profile.is_online);
    }
}

// ============================================================================
// DASHBOARD DATA LOADING
// ============================================================================

function loadDashboardData() {
    return Promise.all([
        loadPendingRequests(),
        loadActiveSessions(),
        loadRatings(),
        loadCompletedSessions()
    ]).catch(error => console.error('Error loading dashboard data:', error));
}

function loadPendingRequests() {
    // Add cache-busting timestamp to force fresh data
    const timestamp = new Date().getTime();
    return apiFetch(`/api/psychologist/requests/pending?_t=${timestamp}`, {
        headers: {
            'Authorization': `Bearer ${currentAccessToken}`,
            'X-User-ID': currentUserId,
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache'
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('📨 Loaded pending requests:', data.requests?.length || 0);
        
        const count = data.requests ? data.requests.length : 0;
        document.getElementById('pendingRequestsCount').textContent = count;
        
        const badge = document.getElementById('requestsBadge');
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
        
        displayRequests(data.requests || []);
    })
    .catch(error => console.error('Error loading pending requests:', error));
}

function displayRequests(requests) {
    const requestsList = document.getElementById('requestsList');
    
    if (!requestsList) return;
    
    let html = '';
    
    if (requests.length === 0) {
        html = '<div class="empty-state">No pending requests</div>';
    } else {
        html = requests.map(req => `
            <div class="request-card" data-request-id="${req.id}">
                <div class="request-header">
                    <h3>${req.user_name || 'Anonymous User'}</h3>
                    <span class="urgency urgency-${req.urgency_level || 'medium'}">${req.urgency_level || 'Medium'}</span>
                </div>
                <p class="request-message">${req.message || 'Client wants to chat with you'}</p>
                <div class="request-time">${formatDate(req.created_at)}</div>
                <div class="request-actions">
                    <button class="btn-action btn-accept" onclick="openRequestDetail('${req.id}')">View & Respond</button>
                </div>
            </div>
        `).join('');
    }
    
    // Only update DOM if content has changed (prevents blinking)
    if (requestsList.innerHTML !== html) {
        requestsList.innerHTML = html;
    }
}

// ============================================================================
// SSE STREAMING FOR NEW REQUESTS
// ============================================================================

let requestStream = null;

function startRequestStream() {
    // Don't create duplicate streams
    if (requestStream) {
        console.log('ℹ️ Request stream already active');
        return;
    }
    
    if (!currentAccessToken) {
        console.warn('⚠️ No access token for streaming');
        return;
    }
    
    console.log('🔌 Starting SSE stream for new requests');
    
    // Note: EventSource doesn't support custom headers, so we pass token as query param
    const streamUrl = `/api/psychologist/requests/stream?access_token=${currentAccessToken}`;
    requestStream = new EventSource(streamUrl);
    
    requestStream.onmessage = function(event) {
        try {
            const request = JSON.parse(event.data);
            if (request.error) {
                console.error('❌ Stream error:', request.error);
                return;
            }
            console.log('📨 New request via SSE:', request);
            prependRequestCard(request);
        } catch (e) {
            console.error('❌ Error parsing SSE request:', e);
        }
    };
    
    requestStream.onerror = function(error) {
        console.error('❌ SSE connection error:', error);
        // Auto-reconnect is handled by browser
        if (requestStream.readyState === EventSource.CLOSED) {
            console.log('🔌 SSE request stream closed');
            requestStream = null;
        }
    };
    
    requestStream.onopen = function() {
        console.log('✅ SSE request stream connected');
    };
}

function prependRequestCard(request) {
    const requestsList = document.getElementById('requestsList');
    if (!requestsList) return;
    
    // Remove empty state if present
    const emptyState = requestsList.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }
    
    // Create new request card
    const cardHtml = `
        <div class="request-card new-request" data-request-id="${request.id}">
            <div class="request-header">
                <h3>${request.user_name || 'Anonymous User'}</h3>
                <span class="urgency urgency-${request.urgency_level || 'medium'}">${request.urgency_level || 'Medium'}</span>
            </div>
            <p class="request-message">${request.message || 'Client wants to chat with you'}</p>
            <div class="request-time">${formatDate(request.created_at)}</div>
            <div class="request-actions">
                <button class="btn-action btn-accept" onclick="openRequestDetail('${request.id}')">View & Respond</button>
            </div>
        </div>
    `;
    
    // Insert at the beginning
    requestsList.insertAdjacentHTML('afterbegin', cardHtml);
    
    // Update count
    const badge = document.getElementById('requestsBadge');
    const countEl = document.getElementById('pendingRequestsCount');
    const currentCount = parseInt(countEl.textContent) || 0;
    const newCount = currentCount + 1;
    
    countEl.textContent = newCount;
    if (badge) {
        badge.textContent = newCount;
        badge.style.display = 'inline-block';
    }
    
    // Add animation effect (optional)
    const newCard = requestsList.querySelector('.new-request');
    if (newCard) {
        setTimeout(() => {
            newCard.classList.remove('new-request');
        }, 2000);
    }
    
    // Show notification
    showNotification(`New request from ${request.user_name || 'a user'}`, 'info');
}

// Remove a request card from the list (when accepted or declined)
function removeRequestCard(requestId) {
    console.log('🗑️ Attempting to remove request card:', requestId);
    const requestsList = document.getElementById('requestsList');
    if (!requestsList) {
        console.error('❌ requestsList element not found');
        return;
    }
    
    // Find the request card by data-request-id attribute
    const card = requestsList.querySelector(`.request-card[data-request-id="${requestId}"]`);
    if (card) {
        console.log('✅ Found request card, removing...');
        card.remove();
        
        // Update count
        const badge = document.getElementById('requestsBadge');
        const countEl = document.getElementById('pendingRequestsCount');
        const currentCount = parseInt(countEl.textContent) || 0;
        const newCount = Math.max(0, currentCount - 1);
        
        console.log(`📊 Updating count: ${currentCount} → ${newCount}`);
        countEl.textContent = newCount;
        if (badge) {
            badge.textContent = newCount;
            if (newCount === 0) {
                badge.style.display = 'none';
            }
        }
        
        // If no more requests, show empty state
        if (requestsList.children.length === 0) {
            console.log('📝 No more requests, showing empty state');
            requestsList.innerHTML = '<div class="empty-state">No pending requests</div>';
        }
    } else {
        console.warn('⚠️ Request card not found with ID:', requestId);
        // Fallback: try to find by onclick attribute
        const requestCards = requestsList.querySelectorAll('.request-card');
        console.log(`🔍 Trying fallback search through ${requestCards.length} cards`);
        for (const card of requestCards) {
            const button = card.querySelector('.btn-action[onclick*="' + requestId + '"]');
            if (button) {
                console.log('✅ Found via fallback, removing...');
                card.remove();
                
                // Update count
                const badge = document.getElementById('requestsBadge');
                const countEl = document.getElementById('pendingRequestsCount');
                const currentCount = parseInt(countEl.textContent) || 0;
                const newCount = Math.max(0, currentCount - 1);
                
                countEl.textContent = newCount;
                if (badge) {
                    badge.textContent = newCount;
                    if (newCount === 0) {
                        badge.style.display = 'none';
                    }
                }
                
                if (requestsList.children.length === 0) {
                    requestsList.innerHTML = '<div class="empty-state">No pending requests</div>';
                }
                break;
            }
        }
    }
}

function stopRequestStream() {
    if (requestStream) {
        console.log('🔌 Closing request stream');
        requestStream.close();
        requestStream = null;
    }
}

function loadActiveSessions() {
    // Add cache-busting timestamp
    const timestamp = new Date().getTime();
    return apiFetch(`/api/psychologist/sessions/psychologist/active?_=${timestamp}`, {
        headers: {
            'Authorization': `Bearer ${currentAccessToken}`,
            'X-User-ID': currentUserId,
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache'
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('📊 Active sessions data:', data);
        const sessions = data.sessions || [];
        console.log(`✅ Found ${sessions.length} active sessions (ended_at=null)`);
        const count = sessions.length;
        document.getElementById('activeSessionsCount').textContent = count;
        
        displayActiveSessions(sessions);
    })
    .catch(error => console.error('Error loading active sessions:', error));
}

function refreshActiveSessions() {
    console.log('🔄 Manual refresh of active sessions...');
    const chatsList = document.getElementById('activeChatsList');
    if (chatsList) {
        chatsList.innerHTML = '<div class="loading">Refreshing...</div>';
    }
    loadActiveSessions();
}

function displayActiveSessions(sessions) {
    const chatsList = document.getElementById('activeChatsList');
    
    if (!chatsList) return;
    
    console.log(`📋 Displaying ${sessions.length} active sessions`);
    
    // Filter out sessions without a chat_session_id (old architecture data)
    const validSessions = sessions.filter(session => {
        const hasValidChatId = session.chat_session_id && session.chat_session_id !== null;
        if (!hasValidChatId) {
            console.warn(`⚠️ Skipping session ${session.id} - no chat_session_id`);
        }
        return hasValidChatId;
    });
    
    console.log(`✅ ${validSessions.length} sessions have valid chat_session_id`);
    
    let html = '';
    
    if (validSessions.length === 0) {
        html = '<div class="empty-state">No active sessions</div>';
    } else {
        html = validSessions.map(session => {
            console.log('🔨 Building card for session:', session);
            // Use chat_session_id for opening the actual chat
            const chatId = session.chat_session_id;
            const psychSessionId = session.id;
            
            console.log(`  → chat_session_id: ${chatId} (will be used for Continue Chat button)`);
            console.log(`  → psychologist_session_id: ${psychSessionId} (will be used for End button)`);
            console.log(`  → Button will call: openChat('${chatId}')`);
            console.log(`  → ended_at: ${session.ended_at} (should be null for active)`);
            
            return `
            <div class="chat-card">
                <div class="chat-header">
                    <h3>${session.title || session.user_name || 'Chat Session'}</h3>
                    <span class="status-badge online">Active</span>
                </div>
                <p class="chat-preview">${session.last_message || 'No messages yet'}</p>
                <div class="chat-time">${formatDate(session.started_at || session.created_at)}</div>
                <div style="display: flex; gap: 8px; margin-top: 12px;">
                    <button class="btn-action btn-primary" onclick="openChat('${chatId}')" style="flex: 1;">Continue Chat</button>
                    <button class="btn-action btn-danger" onclick="event.stopPropagation(); endPsychologistSession('${psychSessionId}')" title="End Session">End</button>
                </div>
            </div>
            `;
        }).join('');
    }
    
    // Only update DOM if content has changed (prevents blinking)
    if (chatsList.innerHTML !== html) {
        chatsList.innerHTML = html;
    }
}

function loadCompletedSessions() {
    return apiFetch('/api/psychologist/sessions/completed', {
        headers: {
            'Authorization': `Bearer ${currentAccessToken}`,
            'X-User-ID': currentUserId
        }
    })
    .then(response => response.json())
    .then(data => {
        const count = data.sessions ? data.sessions.length : 0;
        document.getElementById('totalSessions').textContent = count;
        
        displayCompletedSessions(data.sessions || []);
    })
    .catch(error => console.error('Error loading completed sessions:', error));
}

function displayCompletedSessions(sessions) {
    const sessionsList = document.getElementById('sessionsList');
    
    if (!sessionsList) return;
    
    console.log(`📋 Displaying ${sessions.length} completed sessions`);
    
    if (sessions.length === 0) {
        sessionsList.innerHTML = '<div class="empty-state">No completed sessions</div>';
        return;
    }
    
    sessionsList.innerHTML = sessions.map(session => {
        const endedDate = session.ended_at || session.completed_at || session.created_at;
        const startedDate = session.started_at || session.created_at;
        
        // Calculate duration if both dates exist
        let durationText = 'N/A';
        if (endedDate && startedDate) {
            const duration = Math.floor((new Date(endedDate) - new Date(startedDate)) / 60000); // minutes
            durationText = formatDuration(duration);
        }
        
        return `
        <div class="session-card">
            <div class="session-header">
                <h3>${session.user_name || session.title || 'Anonymous Session'}</h3>
                <span class="session-date">${formatDate(endedDate)}</span>
            </div>
            <p class="session-duration">Duration: ${durationText}</p>
            <div class="session-notes">${session.notes || 'Session completed'}</div>
        </div>
    `;
    }).join('');
}

function loadRatings() {
    return apiFetch('/api/psychologist/ratings', {
        headers: {
            'Authorization': `Bearer ${currentAccessToken}`,
            'X-User-ID': currentUserId
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.stats) {
            const avgRating = (data.stats.average_rating || 0).toFixed(1);
            document.getElementById('averageRating').textContent = avgRating;
            
            // Also update the big rating display in Reviews & Ratings section
            const bigRatingEl = document.getElementById('bigRating');
            if (bigRatingEl) {
                bigRatingEl.textContent = avgRating;
            }
            
            displayRatings(data.ratings || []);
            displayRatingStars(data.stats.average_rating || 0);
            document.getElementById('ratingCount').textContent = `${data.stats.total_ratings || 0} reviews`;
        }
    })
    .catch(error => console.error('Error loading ratings:', error));
}

function displayRatings(ratings) {
    const reviewsList = document.getElementById('reviewsList');
    
    if (!reviewsList) return;
    
    if (ratings.length === 0) {
        reviewsList.innerHTML = '<div class="empty-state">No ratings yet</div>';
        return;
    }
    
    reviewsList.innerHTML = ratings.map(rating => `
        <div class="review-card">
            <div class="review-header">
                <div class="stars">${'★'.repeat(Math.round(rating.rating))}${'☆'.repeat(5 - Math.round(rating.rating))}</div>
                <span class="review-date">${formatDate(rating.created_at)}</span>
            </div>
            <p class="review-text">${rating.review_text || 'No review text'}</p>
        </div>
    `).join('');
}

function displayRatingStars(rating) {
    const starsEl = document.getElementById('ratingStars');
    if (starsEl) {
        const fullStars = Math.round(rating);
        const emptyStars = 5 - fullStars;
        starsEl.innerHTML = '★'.repeat(fullStars) + '☆'.repeat(emptyStars);
    }
}

// ============================================================================
// SECTION NAVIGATION
// ============================================================================

function showSection(sectionId) {
    console.log('🔀 Switching to section:', sectionId);
    
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.style.display = 'none';
    });
    
    // Remove active class from all menu items
    document.querySelectorAll('.sidebar-menu .menu-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Show selected section
    const section = document.getElementById(sectionId);
    if (section) {
        section.style.display = 'block';
        console.log('✅ Section displayed:', sectionId);
        return true;
    } else {
        console.error('❌ Section not found:', sectionId);
        return false;
    }
    
    // Add active class to corresponding menu item
    document.querySelector(`[onclick="showSection('${sectionId}')"]`)?.classList.add('active');
}

// ============================================================================
// MODAL MANAGEMENT
// ============================================================================

function openRequestDetail(requestId) {
    // Fetch request details
    apiFetch(`/api/psychologist/requests/${requestId}`, {
        headers: {
            'Authorization': `Bearer ${currentAccessToken}`,
            'X-User-ID': currentUserId
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.request) {
            const detail = document.getElementById('requestDetail');
            const req = data.request;
            
            detail.innerHTML = `
                <div class="request-detail-content">
                    <div class="detail-section">
                        <label>Client Name</label>
                        <div class="detail-value client-name">${req.user_name || 'Anonymous User'}</div>
                    </div>
                    
                    <div class="detail-section">
                        <label>Urgency Level</label>
                        <div class="detail-value urgency urgency-${req.urgency_level || 'medium'}">
                            ${(req.urgency_level || 'medium').toUpperCase()}
                        </div>
                    </div>
                    
                    <div class="detail-section">
                        <label>Client Message</label>
                        <div class="detail-value message-box">${req.message || 'Client wants to chat with you'}</div>
                    </div>
                    
                    <div class="detail-section">
                        <label>Submitted At</label>
                        <div class="detail-value timestamp">${formatDate(req.created_at)}</div>
                    </div>
                </div>
            `;
            
            // Store request ID for later
            document.getElementById('requestModal').dataset.requestId = requestId;
            
            openModal('requestModal');
        } else {
            throw new Error(data.error || 'Failed to load request');
        }
    })
    .catch(error => {
        console.error('Error loading request:', error);
        showNotification('Failed to load request details', 'error');
    });
}

function acceptRequest() {
    const requestId = document.getElementById('requestModal').dataset.requestId;
    const acceptBtn = document.querySelector('.btn-accept');
    
    if (!requestId) {
        showNotification('Error: Request ID not found', 'error');
        return;
    }
    
    // Disable button and show loading state
    acceptBtn.disabled = true;
    const originalText = acceptBtn.textContent;
    acceptBtn.textContent = '⏳ Accepting...';
    
    apiFetch(`/api/psychologist/request/${requestId}/accept`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${currentAccessToken}`,
            'X-User-ID': currentUserId,
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => {
                console.error('Accept request failed, raw response:', text);
                let parsed = {};
                try { parsed = JSON.parse(text); } catch(e) { parsed = { raw: text }; }
                throw new Error(parsed.error || `HTTP ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('✅ Accept response:', data);
        if (data.success && data.chat_session_id) {
            showNotification('✅ Request accepted! Opening chat...', 'success');
            closeModal('requestModal');
            
            // Remove the request card from the list
            removeRequestCard(requestId);
            
            const chatSessionId = data.chat_session_id;
            console.log('📂 Chat session ID:', chatSessionId);
            
            // Open the chat immediately - SSE will handle any updates
            setTimeout(() => {
                console.log('🔄 Opening chat view...');
                openChatInDashboard(chatSessionId, 'Psychologist Session');
                
                // Don't reload dashboard - SSE request stream will handle updates
                // loadDashboardData().catch(err => {
                //     console.warn('⚠️ Dashboard reload failed (non-critical):', err);
                // });
            }, 300);
        } else {
            console.error('❌ Unexpected response format:', data);
            throw new Error(data.error || 'Failed to accept request');
        }
    })
    .catch(error => {
        console.error('Error accepting request:', error);
        showNotification('❌ Failed to accept request: ' + error.message, 'error');
        
        // Restore button
        acceptBtn.disabled = false;
        acceptBtn.textContent = originalText;
    });
}

function closeRequestModal() {
    closeModal('requestModal');
}

// Open chat in dashboard instead of redirecting
function openChat(sessionId) {
    console.log('📱 openChat() called with sessionId:', sessionId);
    console.log('📱 Type of sessionId:', typeof sessionId);
    openChatInDashboard(sessionId, 'Chat Session');
}

let currentChatRefreshInterval = null;
let currentChatStream = null;

function openChatInDashboard(sessionId, title) {
    console.log('💬 openChatInDashboard() called');
    console.log('💬 sessionId:', sessionId, '(type:', typeof sessionId + ')');
    console.log('📋 title:', title);
    
    // Switch to chat view
    console.log('🔀 Attempting to switch to chat-view section...');
    const switched = showSection('chat-view');
    console.log('🔀 Section switched:', switched);
    
    // Verify the section is actually visible
    const chatViewSection = document.getElementById('chat-view');
    if (chatViewSection) {
        console.log('✅ chat-view section exists, display:', chatViewSection.style.display);
    } else {
        console.error('❌ chat-view section NOT FOUND in DOM!');
        return;
    }
    
    // Set chat title
    const titleElement = document.getElementById('chatTitle');
    const chatViewElement = document.getElementById('chatView');
    
    console.log('🎯 Elements found:', {
        titleElement: !!titleElement,
        chatViewElement: !!chatViewElement
    });
    
    if (titleElement) {
        titleElement.textContent = title || 'Chat Session';
        console.log('📝 Title set to:', titleElement.textContent);
    }
    if (chatViewElement) {
        chatViewElement.dataset.sessionId = sessionId;
        console.log('💾 Session ID stored in dataset:', chatViewElement.dataset.sessionId);
    }
    
    console.log('📨 Loading messages for session:', sessionId);
    
    // Load messages
    loadChatMessagesInDashboard(sessionId);
    
    // Clear any existing interval
    if (currentChatRefreshInterval) {
        console.log('🔄 Clearing existing refresh interval');
        clearInterval(currentChatRefreshInterval);
        currentChatRefreshInterval = null;
    }
    
    // Close any existing stream
    if (currentChatStream) {
        console.log('🔌 Closing existing chat stream');
        currentChatStream.close();
        currentChatStream = null;
    }
    
    // Start SSE stream for real-time messages
    startChatStream(sessionId);
    
    // Add a backup session status check every 2 seconds (critical for when SSE fails due to expired tokens)
    if (currentChatRefreshInterval) {
        clearInterval(currentChatRefreshInterval);
    }
    console.log('⏰ Starting backup session status check every 2 seconds');
    currentChatRefreshInterval = setInterval(() => {
        checkSessionStatus(sessionId);
    }, 2000); // Check every 2 seconds
    
    console.log('✅ Chat view setup complete');
    
    // Focus on input
    setTimeout(() => {
        const input = document.getElementById('chatInputInDashboard');
        if (input) {
            input.focus();
            console.log('⌨️ Input focused');
        } else {
            console.warn('⚠️ Input not found');
        }
    }, 100);
}

function startChatStream(sessionId) {
    // Don't create duplicate streams
    if (currentChatStream) {
        console.log('ℹ️ Chat stream already active');
        return;
    }
    
    if (!currentAccessToken) {
        console.warn('⚠️ No access token for streaming');
        return;
    }
    
    console.log('🔌 Starting SSE stream for chat session:', sessionId);
    
    // Use the same endpoint as user chat (streams from session_messages table)
    // The sessionId here is the chat_session_id, not psychologist_session_id
    const streamUrl = `/api/chat-sessions/${sessionId}/stream?access_token=${currentAccessToken}`;
    currentChatStream = new EventSource(streamUrl);
    
    currentChatStream.onmessage = function(event) {
        console.log('📬 SSE onmessage fired, raw event data:', event.data);
        try {
            const message = JSON.parse(event.data);
            console.log('📨 Parsed SSE message:', message);
            
            if (message.error) {
                console.error('❌ Stream error:', message.error);
                return;
            }
            
            appendMessageToDashboard(message);
        } catch (e) {
            console.error('❌ Error parsing SSE message:', e, 'Raw data:', event.data);
        }
    };
    
    currentChatStream.onerror = function(error) {
        console.error('❌ SSE chat connection error:', error);
        console.error('🔍 SSE readyState:', currentChatStream?.readyState);
        console.error('🔍 EventSource states:', {
            CONNECTING: EventSource.CONNECTING,
            OPEN: EventSource.OPEN,
            CLOSED: EventSource.CLOSED,
            current: currentChatStream?.readyState
        });
        
        // If connection failed (possibly due to expired token), rely on backup polling
        console.warn('⚠️ SSE connection failed - backup polling will handle session updates');
        
        // Close stream to prevent auto-reconnect to invalid sessions
        if (currentChatStream) {
            console.log('🔌 Closing chat stream due to error');
            currentChatStream.close();
            currentChatStream = null;
        }
    };
    
    currentChatStream.onopen = function() {
        console.log('✅ SSE chat stream connected');
    };
}

// Backup check to verify session is still active (in case SSE fails)
function checkSessionStatus(sessionId) {
    console.log('🔍 Checking session status for:', sessionId);
    
    // Use plain fetch without auth headers to avoid 401 errors when token expires
    fetch(`/api/chat-sessions/${sessionId}/messages?limit=1`, {
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        console.log('📡 Session status check response:', response.status);
        if (!response.ok) {
            console.warn('⚠️ Session status check failed:', response.status);
            // Don't throw - just log and continue
            return null;
        }
        return response.json();
    })
    .then(data => {
        if (!data) {
            console.log('⚠️ No data from session status check');
            return;
        }
        
        console.log('📊 Session status:', {
            has_psychologist: data.has_psychologist,
            session_id: sessionId
        });
        
        // If has_psychologist is false, session was ended by user
        if (data.has_psychologist === false) {
            console.log('� BACKUP CHECK TRIGGERED: User has ended the session!');
            showNotification('⚠️ User ended the session - closing chat', 'info');
            
            // Clear the interval
            if (currentChatRefreshInterval) {
                clearInterval(currentChatRefreshInterval);
                currentChatRefreshInterval = null;
            }
            
            // Close chat immediately
            stopChatStream();
            closeChatInDashboard();
            
            // Refresh lists
            setTimeout(() => {
                loadActiveSessions();
                loadCompletedSessions();
            }, 500);
        }
    })
    .catch(error => {
        console.error('❌ Error checking session status:', error);
        // Don't close chat on error - might just be network issue
    });
}

function appendMessageToDashboard(message) {
    console.log('🎯 appendMessageToDashboard CALLED with message:', {
        id: message.id,
        role: message.role,
        message_type: message.message_type,
        content: message.content?.substring(0, 50),
        session_id: message.session_id
    });
    
    const messagesContainer = document.getElementById('chatMessagesInDashboard');
    if (!messagesContainer) {
        console.warn('⚠️ messagesContainer not found!');
        return;
    }
    
    const chatViewElement = document.getElementById('chatView');
    const currentSessionId = chatViewElement?.dataset?.sessionId;
    
    console.log('🔍 Session check:', {
        messageSessionId: message.session_id,
        currentSessionId: currentSessionId,
        matches: message.session_id === currentSessionId
    });
    
    // Only append if message is for current session
    if (message.session_id !== currentSessionId) {
        console.warn('⚠️ Message session mismatch, skipping');
        return;
    }
    
    // Check if message already exists (prevent duplicates)
    const messageId = message.id;
    if (messageId) {
        const existingMessage = messagesContainer.querySelector(`[data-message-id="${messageId}"]`);
        if (existingMessage) {
            console.log('ℹ️ Message already in DOM, skipping:', messageId);
            return;
        }
    }
    
    // Check if this is a session end notification
    const isSystem = message.message_type === 'system' || message.role === 'system';
    console.log('🔍 Message check:', {
        isSystem,
        message_type: message.message_type,
        role: message.role,
        content: message.content,
        includesEndedSession: message.content?.includes('ended the session')
    });
    
    if (isSystem && message.content && message.content.includes('ended the session')) {
        console.log('🚨 USER ENDED SESSION - CLOSING CHAT NOW!');
        showNotification('⚠️ User ended the session - closing chat', 'info');
        
        // Close chat immediately - no delay
        stopChatStream(); // Stop SSE stream first
        closeChatInDashboard();
        
        // Refresh lists after a short delay
        setTimeout(() => {
            loadActiveSessions();
            loadCompletedSessions();
        }, 500);
        
        // Don't show the message in chat since we're closing
        return;
    }
    
    const wasAtBottom = messagesContainer.scrollHeight - messagesContainer.scrollTop <= messagesContainer.clientHeight + 50;
    
    // Get psychologist's user_id from auth.users (not psychologist profile id)
    const psychologistUserId = currentUserId;
    
    const isOwnMessage = message.sender_id === psychologistUserId || message.user_id === psychologistUserId;
    const isPsychologist = message.role === 'psychologist' || isOwnMessage;
    
    let messageClass;
    if (isSystem) {
        messageClass = 'message-system';
    } else if (isOwnMessage) {
        messageClass = 'message-sent';
    } else {
        messageClass = 'message-received';
    }
    
    const messageIdAttr = messageId ? `data-message-id="${messageId}"` : '';
    const messageHtml = `
        <div class="chat-message ${messageClass}" ${messageIdAttr}>
            <div class="message-content">${escapeHtml(message.content)}</div>
            <div class="message-time">${formatDate(message.created_at)}</div>
        </div>
    `;
    
    messagesContainer.insertAdjacentHTML('beforeend', messageHtml);
    
    // Auto-scroll to bottom if was near bottom
    if (wasAtBottom) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

function stopChatStream() {
    if (currentChatStream) {
        console.log('🔌 Closing chat stream');
        currentChatStream.close();
        currentChatStream = null;
    }
}

function loadChatMessagesInDashboard(sessionId, silent = false) {
    console.log('📬 loadChatMessagesInDashboard called with sessionId:', sessionId, '(type:', typeof sessionId + ')');
    
    // Load from regular chat API since psychologist joined the user's chat
    apiFetch(`/api/chat-sessions/${sessionId}/messages`, {
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        console.log('📥 Message fetch response:', response.status, 'for session:', sessionId);
        return response.json();
    })
    .then(data => {
        console.log('📨 Loaded', data.messages?.length || 0, 'messages for session:', sessionId);
        
        // Check if user ended the session
        if (data.has_psychologist === false) {
            console.log('⚠️ User has ended the session');
            showNotification('User ended the session', 'info');
            
            // Close the chat view
            setTimeout(() => {
                closeChatInDashboard();
                // Refresh sessions to update the lists
                loadActiveSessions();
                loadCompletedSessions();
            }, 2000); // Give time to see the notification
            
            return; // Don't update messages if session ended
        }
        
        const messagesContainer = document.getElementById('chatMessagesInDashboard');
        if (!messagesContainer) return;
        
        const wasAtBottom = messagesContainer.scrollHeight - messagesContainer.scrollTop <= messagesContainer.clientHeight + 50;
        
        // Get psychologist's user_id from auth.users (not psychologist profile id)
        const psychologistUserId = currentUserId;
        
        // Build new HTML
        const newHTML = (data.messages || []).map(msg => {
            const isOwnMessage = msg.user_id === psychologistUserId;
            const isPsychologist = msg.role === 'psychologist' || isOwnMessage;
            const isSystem = msg.role === 'system';
            
            let messageClass;
            if (isSystem) {
                messageClass = 'message-system';
            } else if (isOwnMessage) {
                messageClass = 'message-sent';
            } else {
                messageClass = 'message-received';
            }
            
            const messageIdAttr = msg.id ? `data-message-id="${msg.id}"` : '';
            return `
                <div class="chat-message ${messageClass}" ${messageIdAttr}>
                    <div class="message-content">${escapeHtml(msg.content)}</div>
                    <div class="message-time">${formatDate(msg.created_at)}</div>
                </div>
            `;
        }).join('');
        
        // Only update if content has changed (prevents blinking)
        if (messagesContainer.innerHTML !== newHTML) {
            messagesContainer.innerHTML = newHTML;
            
            // Auto-scroll to bottom if was near bottom
            if (wasAtBottom) {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        }
    })
    .catch(error => {
        if (!silent) {
            console.error('Error loading messages:', error);
        }
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function sendMessageInDashboard(event) {
    event.preventDefault();
    
    const chatViewElement = document.getElementById('chatView');
    const input = document.getElementById('chatInputInDashboard');
    
    if (!chatViewElement || !input) {
        console.error('❌ Chat elements not found');
        return;
    }
    
    const sessionId = chatViewElement.dataset.sessionId;
    const message = input.value.trim();
    
    console.log('📤 Attempting to send message:', {
        sessionId: sessionId,
        messageLength: message.length,
        hasAuth: !!currentAccessToken,
        userId: currentUserId
    });
    
    if (!message) {
        console.log('⚠️ Empty message, aborting');
        return;
    }
    
    if (!sessionId) {
        console.error('❌ No session ID');
        showNotification('Error: No active session', 'error');
        return;
    }
    
    const originalValue = message;
    input.value = '';
    input.disabled = true;
    
    // Send to regular chat API with psychologist role
    apiFetch(`/api/chat-sessions/${sessionId}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message: message,
            userId: currentUserId,
            role: 'psychologist'  // Mark as psychologist message
        })
    })
    .then(response => {
        console.log('📡 Response status:', response.status);
        if (!response.ok) {
            return response.text().then(text => {
                console.error('❌ Server error response:', text);
                
                // Check if session has ended (403 error)
                if (response.status === 403) {
                    let errorData;
                    try {
                        errorData = JSON.parse(text);
                    } catch (e) {
                        errorData = { error: text };
                    }
                    
                    // If session ended, close chat
                    if (errorData.error && errorData.error.includes('ended')) {
                        console.log('🚨 Session ended detected via 403 error - closing chat');
                        showNotification('⚠️ User ended the session - closing chat', 'info');
                        stopChatStream();
                        closeChatInDashboard();
                        setTimeout(() => {
                            loadActiveSessions();
                            loadCompletedSessions();
                        }, 500);
                        throw new Error('Session ended');
                    }
                }
                
                throw new Error(`HTTP ${response.status}: ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('✅ Message sent successfully:', data);
        // Don't reload - message will arrive via SSE stream automatically
        // This prevents blinking
    })
    .catch(error => {
        console.error('❌ Error sending message:', error);
        showNotification('Failed to send: ' + error.message, 'error');
        // Restore message on error
        input.value = originalValue;
    })
    .finally(() => {
        input.disabled = false;
        input.focus();
    });
}

function closeChatInDashboard() {
    console.log('🔙 Closing chat view');
    
    // Stop auto-refresh
    if (currentChatRefreshInterval) {
        clearInterval(currentChatRefreshInterval);
        currentChatRefreshInterval = null;
    }
    
    // Stop SSE stream
    stopChatStream();
    
    // Reload active sessions to show updated list
    loadActiveSessions().then(() => {
        // Switch back to active chats view
        showSection('active-chats');
    });
}

function endPsychologistSession(psychSessionId) {
    if (!confirm('Are you sure you want to end this session? This will close the chat.')) {
        return;
    }
    
    console.log('🔚 Ending psychologist session:', psychSessionId);
    
    apiFetch(`/api/psychologist/sessions/${psychSessionId}/end`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${currentAccessToken}`,
            'X-User-ID': currentUserId,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            session_notes: 'Session ended by psychologist'
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('✅ Session ended:', data);
        showNotification('✅ Session ended successfully', 'success');
        
        // Close chat if currently open
        if (currentChatRefreshInterval) {
            closeChatInDashboard();
        } else {
            // Just reload active sessions
            loadActiveSessions();
        }
    })
    .catch(error => {
        console.error('❌ Error ending session:', error);
        showNotification('Failed to end session: ' + error.message, 'error');
    });
}

function openNotifications() {
    openModal('notificationModal');
    loadNotifications();
}

function closeNotifications() {
    closeModal('notificationModal');
}

function loadNotifications() {
    apiFetch('/api/psychologist/notifications', {
        headers: {
            'Authorization': `Bearer ${currentAccessToken}`,
            'X-User-ID': currentUserId
        }
    })
    .then(response => response.json())
    .then(data => {
        const list = document.getElementById('notificationsList');
        const count = document.getElementById('notificationCount');
        
        if (data.notifications && data.notifications.length > 0) {
            count.textContent = data.notifications.length;
            count.style.display = 'inline-block';
            
            list.innerHTML = data.notifications.map(notif => `
                <div class="notification-item">
                    <h4>${notif.title}</h4>
                    <p>${notif.message}</p>
                    <span class="notif-time">${formatDate(notif.created_at)}</span>
                </div>
            `).join('');
        } else {
            count.style.display = 'none';
            list.innerHTML = '<div class="empty-state">No notifications</div>';
        }
    })
    .catch(error => console.error('Error loading notifications:', error));
}

// ============================================================================
// PROFILE FORM SUBMISSION
// ============================================================================

let profileImageFile = null;

function handleProfileImageChange(event) {
    const file = event.target.files[0];
    if (file) {
        profileImageFile = file;
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('profilePicture').src = e.target.result;
        };
        reader.readAsDataURL(file);
        showNotification('Profile picture selected. Click "Save Changes" to upload.');
    }
}

function resetProfileForm() {
    const form = document.getElementById('profileForm');
    if (form) {
        form.reset();
        loadPsychologistProfile();
    }
}

const profileForm = document.getElementById('profileForm');
if (profileForm) {
    profileForm.addEventListener('submit', function(event) {
        event.preventDefault();
        
        const btn = this.querySelector('button[type="submit"]');
        btn.disabled = true;
        btn.textContent = 'Saving...';
        
        const formData = new FormData();
        
        // Add text fields directly to FormData
        formData.append('full_name', document.getElementById('profileFullName').value);
        formData.append('bio', document.getElementById('profileBio').value);
        formData.append('session_rate_usd', parseFloat(document.getElementById('profileSessionRate').value) || 0);
        formData.append('average_response_time_minutes', parseInt(document.getElementById('profileResponseTime').value) || 30);
        
        const specializations = document.getElementById('profileSpecializations').value
            .split(',')
            .map(s => s.trim().toLowerCase())
            .filter(s => s);
        formData.append('specializations', JSON.stringify(specializations));
        
        const languages = document.getElementById('profileLanguages').value
            .split(',')
            .map(s => s.trim())
            .filter(s => s) || ['English'];
        formData.append('languages_spoken', JSON.stringify(languages));
        
        // Add image if selected
        if (profileImageFile) {
            formData.append('profile_image', profileImageFile);
        }
        
        console.log('📤 Sending profile update...');
        
        apiFetch('/api/psychologist/profile', {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${currentAccessToken}`,
                'X-User-ID': currentUserId
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log('📥 Response:', data);
            if (data.id || data.success || data.user_id) {
                showNotification('Profile updated successfully!');
                profileImageFile = null;
                loadPsychologistProfile();
            } else {
                throw new Error(data.error || 'Failed to update profile');
            }
        })
        .catch(error => {
            console.error('❌ Error updating profile:', error);
            showNotification('Failed to update profile: ' + error.message, 'error');
        })
        .finally(() => {
            btn.disabled = false;
            btn.textContent = 'Save Changes';
        });
    });
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

function showNotification(message, type = 'success') {
    if (typeof showToast === 'function') {
        showToast(message, type);
        return;
    }
    console.log(`[${type}] ${message}`);
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString();
}

function formatDuration(minutes) {
    if (minutes < 60) return `${minutes} minutes`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
}

function setRejectFormError(message) {
    const el = document.getElementById('rejectRequestFormError');
    if (!el) return;
    if (message) {
        el.textContent = message;
        el.hidden = false;
    } else {
        el.textContent = '';
        el.hidden = true;
    }
}

function openRejectRequestModal() {
    const requestModal = document.getElementById('requestModal');
    const rejectModal = document.getElementById('rejectRequestModal');
    const input = document.getElementById('rejectReasonInput');
    if (!rejectModal || !requestModal?.dataset?.requestId) return;

    setRejectFormError('');
    if (input) input.value = '';
    rejectModal.style.display = 'flex';
    setTimeout(() => input?.focus(), 50);
}

function closeRejectRequestModal() {
    const rejectModal = document.getElementById('rejectRequestModal');
    if (rejectModal) rejectModal.style.display = 'none';
    setRejectFormError('');
}

function showRejectReason() {
    openRejectRequestModal();
}

function submitRejectRequest() {
    const requestId = document.getElementById('requestModal')?.dataset?.requestId;
    const reason = (document.getElementById('rejectReasonInput')?.value || '').trim();

    if (!requestId) {
        showNotification('Error: Request ID not found', 'error');
        return;
    }

    setRejectFormError('');
    const declineBtn = document.querySelector('#rejectRequestModal .btn-reject:last-child');
    if (declineBtn) declineBtn.disabled = true;

    apiFetch(`/api/psychologist/request/${requestId}/reject`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${currentAccessToken}`,
            'X-User-ID': currentUserId,
        },
        body: JSON.stringify({ reason: reason || 'No reason provided' }),
    })
        .then(async (response) => {
            const data = await response.json();
            if (!response.ok || !(data.success || data.request)) {
                throw new Error(data.error || 'Failed to reject request');
            }
            return data;
        })
        .then(() => {
            showNotification('Request declined', 'success');
            closeRejectRequestModal();
            closeModal('requestModal');
            loadDashboardData();
        })
        .catch((error) => {
            console.error('Error rejecting request:', error);
            setRejectFormError(error.message || 'Failed to decline request');
        })
        .finally(() => {
            if (declineBtn) declineBtn.disabled = false;
        });
}

document.addEventListener('click', (e) => {
    if (e.target.id === 'rejectRequestModal') {
        closeRejectRequestModal();
    }
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && document.getElementById('rejectRequestModal')?.style.display === 'flex') {
        closeRejectRequestModal();
    }
});
