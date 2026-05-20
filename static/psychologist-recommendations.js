/**
 * Psychologist Recommendations Module
 * Displays recommended psychologists when high-urgency emotions are detected
 */

class PsychologistRecommendations {
    constructor() {
        this.container = null;
        this.isOpen = false;
        this.selectedPsychologist = null;
        this.init();
    }

    init() {
        // Create container for recommendations modal
        this.container = document.createElement('div');
        this.container.id = 'psychologist-recommendations-modal';
        this.container.className = 'psychologist-modal hidden';
        document.body.appendChild(this.container);
    }

    /**
     * Show recommendations when high-urgency emotion is detected
     */
    async showRecommendations(emotion, urgency) {
        if (urgency !== 'high') return;

        try {
            const response = await apiFetch('/api/psychologist/recommended');
            const psychologists = await response.json();

            if (!psychologists || psychologists.length === 0) {
                this.showNoAvailable();
                return;
            }

            this.renderRecommendations(psychologists, emotion);
            this.open();
        } catch (error) {
            console.error('Error fetching psychologists:', error);
            this.showError();
        }
    }

    /**
     * Render psychologist recommendation cards
     */
    renderRecommendations(psychologists, emotion) {
        const title = this.getEmotionTitle(emotion);
        
        const html = `
            <div class="psychologist-modal-content">
                <div class="psychologist-modal-header">
                    <h2>Professional Support Available</h2>
                    <p>We detected signs of ${title.toLowerCase()}. Connect with a verified psychologist.</p>
                    <button class="modal-close-btn" onclick="psychologistRecommendations.close()">×</button>
                </div>

                <div class="psychologist-cards-container">
                    ${psychologists.slice(0, 3).map(psy => this.renderCard(psy)).join('')}
                </div>

                <div class="psychologist-modal-footer">
                    <p>All psychologists are verified professionals</p>
                </div>
            </div>
        `;

        this.container.innerHTML = html;
    }

    /**
     * Render individual psychologist card
     */
    renderCard(psychologist) {
        const specializations = Array.isArray(psychologist.specializations)
            ? psychologist.specializations.join(', ')
            : psychologist.specializations || 'General';

        const languages = Array.isArray(psychologist.languages_spoken)
            ? psychologist.languages_spoken.join(', ')
            : psychologist.languages_spoken || 'English';

        return `
            <div class="psychologist-card">
                <div class="psychologist-avatar">
                    ${psychologist.profile_image_url
                        ? `<img src="${psychologist.profile_image_url}" alt="${psychologist.full_name}">`
                        : `<div class="avatar-placeholder">${psychologist.full_name.charAt(0)}</div>`
                    }
                </div>

                <div class="psychologist-info">
                    <h3>${psychologist.full_name}</h3>
                    <div class="rating">
                        ${this.renderStars(psychologist.average_rating)}
                        <span class="rating-number">${psychologist.average_rating.toFixed(1)}</span>
                        <span class="review-count">(${psychologist.review_count} reviews)</span>
                    </div>
                    <p class="bio">${psychologist.bio || 'Experienced professional'}</p>
                    <p class="specializations"><strong>Specializations:</strong> ${specializations}</p>
                    <p class="languages"><strong>Languages:</strong> ${languages}</p>
                    <div class="psychologist-meta">
                        <span class="response-time">
                            Response: ${psychologist.average_response_time_minutes}min
                        </span>
                        <span class="status ${psychologist.is_online ? 'online' : 'offline'}">
                            ${psychologist.is_online ? 'Online' : 'Offline'}
                        </span>
                    </div>
                </div>

                <div class="psychologist-action">
                    <button class="btn-connect" 
                            onclick="psychologistRecommendations.sendRequest('${psychologist.id}', '${psychologist.full_name}', 'high')">
                        Send Request
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Render star rating
     */
    renderStars(rating) {
        let stars = '';
        for (let i = 1; i <= 5; i++) {
            if (i <= Math.round(rating)) {
                stars += '<span class="star filled">★</span>';
            } else {
                stars += '<span class="star empty">☆</span>';
            }
        }
        return stars;
    }

    /**
     * Get emotion title for display
     */
    getEmotionTitle(emotion) {
        const emotionMap = {
            'depression': 'Depression',
            'anxiety': 'Anxiety',
            'panic': 'Panic',
            'loneliness': 'Loneliness',
            'burnout': 'Burnout',
            'overwhelm': 'Overwhelm',
            'grief': 'Grief',
            'trauma': 'Trauma',
            'substance_abuse': 'Substance Abuse',
            'suicidal_ideation': 'Suicidal Thoughts'
        };
        return emotionMap[emotion] || 'Emotional Distress';
    }

    /**
     * Send chat request to psychologist
     */
    async sendRequest(psychologistId, psychologistName, urgencyLevel) {
        try {
            const messageInput = document.querySelector('#message-input');
            const userMessage = messageInput?.value || 'I need support';

            // Get access token from localStorage (set during login)
            const accessToken = localStorage.getItem('access_token');
            const userId = localStorage.getItem('user_id');
            
            // CRITICAL: Get the current chat session ID from localStorage or global
            let currentChatSessionId = localStorage.getItem('current_session_id');
            
            // Fallback: try to get from state if exposed globally
            if (!currentChatSessionId && typeof state !== 'undefined') {
                currentChatSessionId = state.currentSessionId;
            }
            
            console.log('📨 Sending request with:');
            console.log('  - access_token:', accessToken ? `${accessToken.substring(0, 20)}...` : 'NO TOKEN');
            console.log('  - user_id:', userId || 'NO USER_ID');
            console.log('  - chat_session_id:', currentChatSessionId || 'NO CHAT SESSION');
            
            if (!currentChatSessionId) {
                console.error('❌ No chat session ID found!');
                this.showError('Please start a chat session first before requesting a psychologist.');
                return;
            }
            
            // Prepare request body
            const requestBody = {
                psychologist_id: psychologistId,
                message: userMessage,
                urgency_level: urgencyLevel,
                chat_session_id: currentChatSessionId  // Link to the original chat session
            };
            
            // Include user_id for development/fallback
            if (userId) {
                requestBody.user_id = userId;
            }

            console.log('📤 POST /api/psychologist/request', requestBody);

            const response = await apiFetch('/api/psychologist/request', {
                method: 'POST',
                body: JSON.stringify(requestBody)
            });

            console.log('📥 Response status:', response.status);

            if (response.ok) {
                const result = await response.json();
                this.showSuccessMessage(`Request sent to ${psychologistName}!`);
                this.close();
                
                // Clear input
                if (messageInput) messageInput.value = '';
            } else if (response.status === 401) {
                console.error('❌ 401 Unauthorized - access token may be expired or missing');
                const errorData = await response.json().catch(() => ({}));
                console.error('Error response:', errorData);
                this.showError('Please log in again to send a request');
            } else {
                console.error('❌ Request failed with status:', response.status);
                const errorData = await response.json().catch(() => ({}));
                console.error('Error response:', errorData);
                this.showError('Failed to send request');
            }
        } catch (error) {
            console.error('Error sending request:', error);
            this.showError('Error sending request');
        }
    }

    /**
     * Show success message
     */
    showSuccessMessage(message) {
        const notification = document.createElement('div');
        notification.className = 'psychologist-notification success';
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    /**
     * Show error message
     */
    showError(message = 'Failed to load psychologists') {
        const html = `
            <div class="psychologist-modal-content">
                <div class="psychologist-modal-header">
                    <h2>Oops!</h2>
                    <p>${message}</p>
                    <button class="modal-close-btn" onclick="psychologistRecommendations.close()">×</button>
                </div>
            </div>
        `;
        this.container.innerHTML = html;
        this.open();
    }

    /**
     * Show no available psychologists
     */
    showNoAvailable() {
        const html = `
            <div class="psychologist-modal-content">
                <div class="psychologist-modal-header">
                    <h2>No Psychologists Available</h2>
                    <p>No verified psychologists are currently available. Please try again later.</p>
                    <button class="modal-close-btn" onclick="psychologistRecommendations.close()">×</button>
                </div>
            </div>
        `;
        this.container.innerHTML = html;
        this.open();
    }

    /**
     * Get JWT token from localStorage
     */
    getToken() {
        return localStorage.getItem('access_token') || '';
    }

    /**
     * Open modal
     */
    open() {
        this.container.classList.remove('hidden');
        this.isOpen = true;
    }

    /**
     * Close modal
     */
    close() {
        this.container.classList.add('hidden');
        this.isOpen = false;
    }
}

// Initialize on document ready
document.addEventListener('DOMContentLoaded', () => {
    window.psychologistRecommendations = new PsychologistRecommendations();
});

/**
 * Export for use in other scripts
 */
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PsychologistRecommendations;
}
