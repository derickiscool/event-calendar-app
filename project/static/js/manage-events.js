// manage-events.js - Display and manage user's own events
const API_BASE = window.API_BASE || '/api';

// Fetch user's events
async function fetchUserEvents() {
  try {
    const res = await fetch(`${API_BASE}/events/my-events`, {
      credentials: 'include'
    });

    if (!res.ok) {
      throw new Error('Failed to fetch events');
    }

    const events = await res.json();
    return events;
  } catch (error) {
    console.error('Error fetching user events:', error);
    throw error;
  }
}

// Format date for display
function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-SG', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// Create event card HTML
function createEventCard(event) {
  const imageUrl = event.image_url || '/static/assets/images/default-event.svg';
  const venueName = event.venue ? event.venue.name : 'Unknown Venue';
  const description = event.description || 'No description provided';
  const truncatedDesc = description.length > 150 
    ? description.substring(0, 150) + '...' 
    : description;

  return `
    <div class="event-card" data-event-id="${event.id}">
      <div class="event-card-image">
        <img src="${imageUrl}" alt="${event.title}">
      </div>
      <div class="event-card-content">
        <h3>${event.title}</h3>
        <div class="event-meta">
          <div class="event-date">
            <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="10" height="10" rx="1"/>
              <line x1="3" y1="7" x2="13" y2="7"/>
            </svg>
            <span>${formatDate(event.start_datetime)}</span>
          </div>
          <div class="event-venue">
            <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M8 2 L8 8 M8 8 L3 10 M8 8 L13 10"/>
              <circle cx="8" cy="8" r="6"/>
            </svg>
            <span>${venueName}</span>
          </div>
        </div>
        <p class="event-description">${truncatedDesc}</p>
        <div class="event-actions">
          <a href="/event-edit?id=${event.id}" class="btn btn-secondary btn-sm">Edit</a>
          <button class="btn btn-danger btn-sm delete-event-btn" data-event-id="${event.id}">Delete</button>
        </div>
      </div>
    </div>
  `;
}

// Display events
function displayEvents(events) {
  const loading = document.getElementById('loading');
  const emptyState = document.getElementById('empty-state');
  const eventsList = document.getElementById('events-list');
  const errorState = document.getElementById('error-state');

  loading.classList.add('hidden');
  errorState.classList.add('hidden');

  if (events.length === 0) {
    emptyState.classList.remove('hidden');
    eventsList.classList.add('hidden');
  } else {
    emptyState.classList.add('hidden');
    eventsList.classList.remove('hidden');
    eventsList.innerHTML = events.map(event => createEventCard(event)).join('');

    // Attach delete handlers
    attachDeleteHandlers();
  }
}

// Show error
function showError(message) {
  const loading = document.getElementById('loading');
  const errorState = document.getElementById('error-state');
  const errorMessage = document.getElementById('error-message');

  loading.classList.add('hidden');
  errorState.classList.remove('hidden');
  errorMessage.textContent = message;
}

// Delete event
async function deleteEvent(eventId) {
  if (!confirm('Are you sure you want to delete this event? This action cannot be undone.')) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/events/${eventId}`, {
      method: 'DELETE',
      credentials: 'include'
    });

    if (res.ok) {
      // Reload events
      loadEvents();
    } else {
      const data = await res.json();
      alert(data.error || 'Failed to delete event');
    }
  } catch (error) {
    console.error('Error deleting event:', error);
    alert('Network error. Please try again.');
  }
}

// Attach delete button handlers
function attachDeleteHandlers() {
  const deleteButtons = document.querySelectorAll('.delete-event-btn');
  deleteButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const eventId = btn.getAttribute('data-event-id');
      deleteEvent(eventId);
    });
  });
}

// Load and display events
async function loadEvents() {
  try {
    const events = await fetchUserEvents();
    displayEvents(events);
  } catch (error) {
    showError('Failed to load your events. Please try again.');
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  loadEvents();
});
