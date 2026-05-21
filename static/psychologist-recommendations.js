/**
 * Psychology student recommendations — browse anytime + crisis trigger (EN / MK)
 */

const RECOMMENDATIONS_I18N = {
    en: {
        browseTitle: 'Psychology students available',
        browseSubtitle: 'Connect with a psychology student for supervised practice support—not licensed clinical care.',
        browseFooter: 'Students are trainees under supervision.',
        crisisTitle: 'Support from a psychology student',
        crisisSubtitle: (label) =>
            `We noticed signs of ${label}. You can talk with a psychology student in training.`,
        crisisFooter: 'Supervised trainees—not licensed clinicians. Not for emergencies.',
        noStudentsTitle: 'No students available right now',
        noStudentsBody:
            'No psychology students are online at the moment. Please try again later or continue chatting with AI.',
        errorDefault: 'Failed to load students',
        errorLogin: 'Please log in again to send a request',
        errorRequest: 'Failed to send request',
        errorNoSession: 'Please start a chat session first before requesting a student.',
        oops: 'Oops!',
        areas: 'Areas of interest:',
        languages: 'Languages:',
        response: 'Response:',
        min: 'min',
        online: 'Online',
        offline: 'Offline',
        reviews: 'reviews',
        sendRequest: 'Send Request',
        defaultBio: 'Psychology student in training',
        requestSent: (name) => `Request sent to ${name}!`,
        emotions: {
            depression: 'depression',
            anxiety: 'anxiety',
            panic: 'panic',
            loneliness: 'loneliness',
            burnout: 'burnout',
            overwhelm: 'overwhelm',
            grief: 'grief',
            trauma: 'trauma',
            substance_abuse: 'substance use',
            suicidal_ideation: 'suicidal thoughts',
            default: 'emotional distress',
        },
    },
    mk: {
        browseTitle: 'Достапни студенти по психологија',
        browseSubtitle:
            'Поврзи се со студент по психологија за поддршка под супервизија—не лиценцирана клиничка нега.',
        browseFooter: 'Студентите се во обука под супервизија.',
        crisisTitle: 'Поддршка од студент по психологија',
        crisisSubtitle: (label) =>
            `Забележавме знаци на ${label}. Можеш да разговараш со студент по психологија во обука.`,
        crisisFooter:
            'Студенти под супервизија—не лиценцирани клиничари. Не за итни случаи.',
        noStudentsTitle: 'Моментално нема достапни студенти',
        noStudentsBody:
            'Нема онлајн студенти по психологија во моментов. Обиди се повторно подоцна или продолжи со разговор со AI.',
        errorDefault: 'Неуспешно вчитување на студенти',
        errorLogin: 'Најави се повторно за да испратиш барање',
        errorRequest: 'Неуспешно испраќање на барање',
        errorNoSession: 'Прво започни разговор пред да испратиш барање до студент.',
        oops: 'Упс!',
        areas: 'Области на интерес:',
        languages: 'Јазици:',
        response: 'Одговор:',
        min: 'мин',
        online: 'Онлајн',
        offline: 'Офлајн',
        reviews: 'рецензии',
        sendRequest: 'Испрати барање',
        defaultBio: 'Студент по психологија во обука',
        requestSent: (name) => `Барањето е испратено до ${name}!`,
        emotions: {
            depression: 'депресија',
            anxiety: 'анксиозност',
            panic: 'паника',
            loneliness: 'осаменост',
            burnout: 'исцрпеност',
            overwhelm: 'преоптоварување',
            grief: 'тага',
            trauma: 'траума',
            substance_abuse: 'злоупотреба на супстанции',
            suicidal_ideation: 'суицидални мисли',
            default: 'емоционална дистрес',
        },
    },
};

class PsychologistRecommendations {
    constructor() {
        this.container = null;
        this.isOpen = false;
        this.selectedPsychologist = null;
        this.init();
    }

    getLang() {
        if (typeof state !== 'undefined' && state.language) {
            return state.language;
        }
        return localStorage.getItem('language') || 'en';
    }

    t(key, ...args) {
        const lang = this.getLang() === 'mk' ? 'mk' : 'en';
        const bundle = RECOMMENDATIONS_I18N[lang];
        const value = bundle[key];
        if (typeof value === 'function') {
            return value(...args);
        }
        return value ?? RECOMMENDATIONS_I18N.en[key];
    }

    init() {
        this.container = document.createElement('div');
        this.container.id = 'psychologist-recommendations-modal';
        this.container.className = 'psychologist-modal hidden';
        document.body.appendChild(this.container);
    }

    async showBrowseStudents() {
        await this._fetchAndShow(null, {
            title: this.t('browseTitle'),
            subtitle: this.t('browseSubtitle'),
            footer: this.t('browseFooter'),
        });
    }

    async showRecommendations(emotion, urgency, force = false) {
        if (!force && urgency !== 'high') return;

        const label = this.getEmotionTitle(emotion);
        await this._fetchAndShow(emotion, {
            title: this.t('crisisTitle'),
            subtitle: this.t('crisisSubtitle', label),
            footer: this.t('crisisFooter'),
        });
    }

    async _fetchAndShow(emotion, headerCopy) {
        try {
            const response = await apiFetch('/api/psychologist/recommended');
            const psychologists = await response.json();

            if (!Array.isArray(psychologists) || psychologists.length === 0) {
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
                    ${psychologists.slice(0, 3).map((psy) => this.renderCard(psy)).join('')}
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
                        <span class="review-count">(${psychologist.review_count} ${this.t('reviews')})</span>
                    </div>
                    <p class="bio">${psychologist.bio || this.t('defaultBio')}</p>
                    <p class="specializations"><strong>${this.t('areas')}</strong> ${specializations}</p>
                    <p class="languages"><strong>${this.t('languages')}</strong> ${languages}</p>
                    <div class="psychologist-meta">
                        <span class="response-time">
                            ${this.t('response')} ${psychologist.average_response_time_minutes}${this.t('min')}
                        </span>
                        <span class="status ${psychologist.is_online ? 'online' : 'offline'}">
                            ${psychologist.is_online ? this.t('online') : this.t('offline')}
                        </span>
                    </div>
                </div>

                <div class="psychologist-action">
                    <button class="btn-connect" 
                            onclick="psychologistRecommendations.sendRequest('${psychologist.id}', '${safeName}', 'high')">
                        ${this.t('sendRequest')}
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
        const lang = this.getLang() === 'mk' ? 'mk' : 'en';
        const emotions = RECOMMENDATIONS_I18N[lang].emotions;
        return emotions[emotion] || emotions.default;
    }

    async sendRequest(psychologistId, psychologistName, urgencyLevel) {
        try {
            const messageInput = document.querySelector('#messageInput');
            const userMessage = messageInput?.value || (this.getLang() === 'mk' ? 'ми треба поддршка' : 'I need support');

            const userId = localStorage.getItem('user_id');

            let currentChatSessionId = localStorage.getItem('current_session_id');

            if (!currentChatSessionId && typeof state !== 'undefined') {
                currentChatSessionId = state.currentSessionId;
            }

            if (!currentChatSessionId) {
                console.error('❌ No chat session ID found!');
                this.showError(this.t('errorNoSession'));
                return;
            }

            const requestBody = {
                psychologist_id: psychologistId,
                message: userMessage,
                urgency_level: urgencyLevel,
                chat_session_id: currentChatSessionId,
            };

            if (userId) {
                requestBody.user_id = userId;
            }

            const response = await apiFetch('/api/psychologist/request', {
                method: 'POST',
                body: JSON.stringify(requestBody),
            });

            if (response.ok) {
                this.showSuccessMessage(this.t('requestSent', psychologistName));
                this.close();
                if (messageInput) messageInput.value = '';

                // Don't reload messages - SSE stream will handle updates
                // if (typeof loadSessionMessages === 'function' && currentChatSessionId) {
                //     setTimeout(() => loadSessionMessages(currentChatSessionId, true), 500);
                //     setTimeout(() => loadSessionMessages(currentChatSessionId, true), 1500);
                // }
            } else if (response.status === 401) {
                this.showError(this.t('errorLogin'));
            } else {
                this.showError(this.t('errorRequest'));
            }
        } catch (error) {
            console.error('Error sending request:', error);
            this.showError(this.t('errorRequest'));
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

    showError(message) {
        const text = message || this.t('errorDefault');
        const html = `
            <div class="psychologist-modal-content">
                <div class="psychologist-modal-header">
                    <h2>${this.t('oops')}</h2>
                    <p>${text}</p>
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
                    <h2>${this.t('noStudentsTitle')}</h2>
                    <p>${this.t('noStudentsBody')}</p>
                    <button class="modal-close-btn" onclick="psychologistRecommendations.close()">×</button>
                </div>
            </div>
        `;
        this.container.innerHTML = html;
        this.open();
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
