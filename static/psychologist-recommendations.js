/**
 * Psychology student recommendations — browse anytime + crisis trigger
 */

class PsychologistRecommendations {
    constructor() {
        this.container = null;
        this.isOpen = false;
        this.selectedPsychologist = null;
        this.init();
    }

    init() {
        this.container = document.createElement('div');
        this.container.id = 'psychologist-recommendations-modal';
        this.container.className = 'psychologist-modal hidden';
        document.body.appendChild(this.container);
    }

    /**
     * Fetch students and open modal (no urgency check)
     */
    async showBrowseStudents() {
        await this._fetchAndShow(null, {
            title: 'Psychology students available',
            subtitle: 'Connect with a psychology student for supervised practice support—not licensed clinical care.',
            footer: 'Students are trainees under supervision.',
        });
    }

    /**
     * Show recommendations when high-urgency emotion is detected
     */
    async showRecommendations(emotion, urgency) {
        if (urgency !== 'high') return;

        const title = this.getEmotionTitle(emotion);
        await this._fetchAndShow(emotion, {
            title: 'Support from a psychology student',
            subtitle: `We noticed signs of ${title.toLowerCase()}. You can talk with a psychology student in training.`,
            footer: 'Supervised trainees—not licensed clinicians. Not for emergencies.',
        });
    }

    async _fetchAndShow(emotion, headerCopy) {
        try {
            const response = await apiFetch('/api/psychologist/recommended');
            const psychologists = await response.json();

            if (!psychologists || psychologists.length === 0) {
                this.showNoAvailable();
                return;
            }

            this.renderRecommendations(psychologists, emotion, headerCopy);
            this.open();
        } catch (error) {
            console.error('Error fetching psychology students:', error);
            this.showError();
        }
    }

    renderRecommendations(psychologists, emotion, headerCopy) {
        const html = `
            <div class="psychologist-modal-content">
                <div class="psychologist-modal-header">
                    <h2>${headerCopy.title}</h2>
                    <p>${headerCopy.subtitle}</p>
                    <button class="modal-close-btn" onclick="psychologistRecommendations.close()">×</button>
                </div>

                <div class="psychologist-cards-container">
                    ${psychologists.slice(0, 3).map(psy => this.renderCard(psy)).join('')}
                </div>

                <div class="psychologist-modal-footer">
                    <p>${headerCopy.footer}</p>
                </div>
            </div>
        `;

        this.container.innerHTML = html;
    }

    renderCard(psychologist) {
        const specializations = Array.isArray(psychologist.specializations)
            ? psychologist.specializations.join(', ')
            : psychologist.specializations || 'General';

        const languages = Array.isArray(psychologist.languages_spoken)
            ? psychologist.languages_spoken.join(', ')
            : psychologist.languages_spoken || 'English';

        const safeName = (psychologist.full_name || 'Student').replace(/'/g, "\\'");

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
                    <p class="bio">${psychologist.bio || 'Psychology student in training'}</p>
                    <p class="specializations"><strong>Areas of interest:</strong> ${specializations}</p>
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
                            onclick="psychologistRecommendations.sendRequest('${psychologist.id}', '${safeName}', 'high')">
                        Send Request
                    </button>
                </div>
            </div>
        `;
    }

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

    async sendRequest(psychologistId, psychologistName, urgencyLevel) {
        try {
            const messageInput = document.querySelector('#messageInput');
            const userMessage = messageInput?.value || 'I need support';

            const accessToken = localStorage.getItem('access_token');
            const userId = localStorage.getItem('user_id');

            let currentChatSessionId = localStorage.getItem('current_session_id');

            if (!currentChatSessionId && typeof state !== 'undefined') {
                currentChatSessionId = state.currentSessionId;
            }

            if (!currentChatSessionId) {
                console.error('❌ No chat session ID found!');
                this.showError('Please start a chat session first before requesting a student.');
                return;
            }

            const requestBody = {
                psychologist_id: psychologistId,
                message: userMessage,
                urgency_level: urgencyLevel,
                chat_session_id: currentChatSessionId
            };

            if (userId) {
                requestBody.user_id = userId;
            }

            const response = await apiFetch('/api/psychologist/request', {
                method: 'POST',
                body: JSON.stringify(requestBody)
            });

            if (response.ok) {
                this.showSuccessMessage(`Request sent to ${psychologistName}!`);
                this.close();
                if (messageInput) messageInput.value = '';
                
                // Trigger immediate message refresh to catch psychologist responses faster
                if (typeof loadSessionMessages === 'function' && currentChatSessionId) {
                    console.log('🔄 Triggering immediate message refresh after request...');
                    setTimeout(() => loadSessionMessages(currentChatSessionId, true), 500);
                    setTimeout(() => loadSessionMessages(currentChatSessionId, true), 1500);
                }
            } else if (response.status === 401) {
                this.showError('Please log in again to send a request');
            } else {
                this.showError('Failed to send request');
            }
        } catch (error) {
            console.error('Error sending request:', error);
            this.showError('Error sending request');
        }
    }

    showSuccessMessage(message) {
        const notification = document.createElement('div');
        notification.className = 'psychologist-notification success';
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    showError(message = 'Failed to load students') {
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

    showNoAvailable() {
        const html = `
            <div class="psychologist-modal-content">
                <div class="psychologist-modal-header">
                    <h2>No students available right now</h2>
                    <p>No psychology students are online at the moment. Please try again later or continue chatting with AI.</p>
                    <button class="modal-close-btn" onclick="psychologistRecommendations.close()">×</button>
                </div>
            </div>
        `;
        this.container.innerHTML = html;
        this.open();
    }

    getToken() {
        return localStorage.getItem('access_token') || '';
    }

    open() {
        this.container.classList.remove('hidden');
        this.isOpen = true;
    }

    close() {
        this.container.classList.add('hidden');
        this.isOpen = false;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.psychologistRecommendations = new PsychologistRecommendations();
});

if (typeof module !== 'undefined' && module.exports) {
    module.exports = PsychologistRecommendations;
}
