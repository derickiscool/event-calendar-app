// events.js — Fetch and display both official and community events
const API_BASE = window.API_BASE || '/api';

/**
 * Fetch all events (official from MongoDB + community from MariaDB)
 * @param {string} category - Category filter ('all', 'music', 'theatre', etc.)
 * @param {string} searchQuery - Search query string
 * @returns {Promise<Object>} - Response with events array and metadata
 */
export async function fetchAllEvents(category = 'all', searchQuery = '') {
    try {
        const params = new URLSearchParams();
        if (category && category !== 'all') {
            params.append('category', category);
        }
        if (searchQuery) {
            params.append('q', searchQuery);
        }

        const url = `${API_BASE}/all-events${params.toString() ? '?' + params.toString() : ''}`;
        const response = await fetch(url, {
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching events:', error);
        throw error;
    }
}

/**
 * Fetch only official events from MongoDB
 * @returns {Promise<Array>} - Array of official events
 */
export async function fetchOfficialEvents() {
    try {
        const response = await fetch(`${API_BASE}/official-events`, {
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching official events:', error);
        throw error;
    }
}

/**
 * Fetch only community events from MariaDB
 * @returns {Promise<Array>} - Array of community events
 */
export async function fetchCommunityEvents() {
    try {
        const response = await fetch(`${API_BASE}/events`, {
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching community events:', error);
        throw error;
    }
}

/**
 * Render events to the DOM
 * @param {Array} events - Array of event objects
 * @param {HTMLElement} container - Container element to render into
 */
export function renderEvents(events, container) {
    if (!container) {
        console.error('Container element not found');
        return;
    }

    if (!events || events.length === 0) {
        container.innerHTML = '<div class="empty-state">No events found matching your criteria.</div>';
        return;
    }

    container.innerHTML = events.map(event => createEventCard(event)).join('');
}

/**
 * Create HTML for a single event card
 * @param {Object} event - Event object
 * @returns {string} - HTML string for event card
 */
function createEventCard(event) {
    const defaultImage = '/static/assets/images/default-event.svg';
    const imageUrl = event.image || event.image_url || defaultImage;
    const title = escapeHtml(event.title || 'Untitled Event');
    const venue = escapeHtml(event.venue || 'Venue TBA');
    const date = event.date || 'Date TBA';
    const category = event.category || 'other';
    const source = event.source || 'unknown';
    const sourceLabel = event.source_label || 'Event';

    // Create badge HTML for source
    const sourceBadge = `<span class="badge badge-${source}">${source === 'official' ? '🏛️ Official' : '👥 Community'}</span>`;

    // Create tags HTML (show actual tags if available, fallback to category)
    let tagBadges = '';
    if (event.tags && event.tags.length > 0) {
        tagBadges = event.tags.map(tag => 
            `<span class="badge badge-tag">${escapeHtml(tag)}</span>`
        ).join('');
    } else if (category !== 'other') {
        tagBadges = `<span class="badge badge-${category}">${formatCategory(category)}</span>`;
    }

    return `
    <div class="card event-card" data-event-id="${event.id}" data-category="${category}" data-source="${source}">
      <img 
        src="${imageUrl}" 
        alt="${title}"
        onerror="this.onerror=null; this.src='${defaultImage}'"
        class="card-img"
      >
      <div class="card-body">
        <div class="card-badges">
          ${tagBadges}
          ${sourceBadge}
        </div>
        <h3 class="card-title">${title}</h3>
        <p class="card-meta">
          <span class="meta-icon">📅</span> ${escapeHtml(date)}
        </p>
        <p class="card-meta">
          <span class="meta-icon">📍</span> ${venue}
        </p>
        ${event.description ? `<p class="card-description">${truncateText(escapeHtml(event.description), 120)}</p>` : ''}
        <div class="card-actions">
          <button class="btn btn-sm btn-primary" onclick="viewEventDetails('${event.id}')">
            View Details
          </button>
        </div>
      </div>
    </div>
  `;
}

/**
 * Format category slug to display name
 * @param {string} category - Category slug
 * @returns {string} - Formatted category name
 */
function formatCategory(category) {
    const categories = {
        'music': 'Music',
        'theatre': 'Theatre',
        'comedy': 'Comedy',
        'film': 'Film',
        'visual-arts': 'Visual Arts',
        'workshops': 'Workshops',
        'other': 'Other'
    };
    return categories[category] || category;
}

/**
 * Truncate text to specified length
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} - Truncated text
 */
function truncateText(text, maxLength) {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + '...';
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} - Escaped text
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Filter events by category and search query (client-side)
 * @param {Array} events - Array of events
 * @param {string} category - Category filter
 * @param {string} searchQuery - Search query
 * @returns {Array} - Filtered events
 */
export function filterEvents(events, category = 'all', searchQuery = '') {
    let filtered = [...events];

    // Filter by category
    if (category && category !== 'all') {
        filtered = filtered.filter(event => event.category === category);
    }

    // Filter by search query
    if (searchQuery) {
        const query = searchQuery.toLowerCase();
        filtered = filtered.filter(event => {
            const searchText = [
                event.title || '',
                event.description || '',
                event.venue || '',
                event.location || ''
            ].join(' ').toLowerCase();
            return searchText.includes(query);
        });
    }

    return filtered;
}

/**
 * Get event statistics
 * @param {Array} events - Array of events
 * @returns {Object} - Statistics object
 */
export function getEventStats(events) {
    const stats = {
        total: events.length,
        official: events.filter(e => e.source === 'official').length,
        community: events.filter(e => e.source === 'community').length,
        byCategory: {}
    };

    // Count by category
    events.forEach(event => {
        const cat = event.category || 'other';
        stats.byCategory[cat] = (stats.byCategory[cat] || 0) + 1;
    });

    return stats;
}

/**
 * View event details (placeholder - to be implemented)
 * @param {string} eventId - Event ID
 */
window.viewEventDetails = function (eventId) {
    // Navigate to event detail page
    window.location.href = `/event-detail?id=${encodeURIComponent(eventId)}`;
};

// Export for use in other modules
export default {
    fetchAllEvents,
    fetchOfficialEvents,
    fetchCommunityEvents,
    renderEvents,
    filterEvents,
    getEventStats
};
