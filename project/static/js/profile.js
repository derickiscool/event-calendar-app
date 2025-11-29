// profile.js - Handle profile viewing, editing, reviews, and preferences
const API_BASE = window.API_BASE || '/api';

let currentProfile = null;
let selectedAvatarFile = null;
let allTags = [];
let userPreferences = [];

// --- INITIALIZATION ---
document.addEventListener('DOMContentLoaded', async () => {
    await loadProfile();
    await loadTags(); // Load tags for preferences

    // --- EVENT LISTENERS ---

    // 1. Edit/Cancel Mode Toggles
    const editBtn = document.getElementById('edit-profile-btn'); // Add this ID to your "Edit Profile" button if you have one
    if (editBtn) editBtn.addEventListener('click', enterEditMode);

    // If you have a cancel button in the form
    const cancelBtn = document.querySelector('button[onclick="window.location.href=\'/\'"]');
    if (cancelBtn) {
        cancelBtn.removeAttribute('onclick'); // Remove inline handler
        cancelBtn.addEventListener('click', (e) => {
            e.preventDefault();
            // Since you don't have a "View Mode" div yet, we just redirect or reload
            window.location.href = '/'; 
        });
    }

    // 2. Avatar Upload
    const avatarInput = document.getElementById('avatar-input');
    if (avatarInput) {
        avatarInput.addEventListener('change', handleAvatarSelect);
    }

    // 3. Form Submission
    const profileForm = document.getElementById('profile-form');
    if (profileForm) {
        profileForm.addEventListener('submit', handleProfileUpdate);
    }

    // 4. Input Validation Listeners
    setupValidationListeners();
});


// --- PROFILE LOADING & DISPLAY ---

async function loadProfile() {
    try {
        const res = await fetch(`${API_BASE}/profile/me`, { credentials: 'include' });

        if (res.status === 401) {
            window.location.href = '/login';
            return;
        }
        if (!res.ok) throw new Error('Failed to load profile');

        const data = await res.json();
        currentProfile = data;
        displayProfile(data);

    } catch (e) {
        console.error("Profile load error:", e);
        showToast('Failed to load profile', 'text-bg-danger');
    }
}

function displayProfile(data) {
    const { user, profile, reviews } = data;

    // Sidebar Info
    setText('display-username', user.username || 'User');
    setText('display-email', user.email || '');

    // Avatar
    const avatarImg = document.getElementById('display-avatar');
    if (avatarImg) {
        if (profile.avatar_url) {
            avatarImg.src = profile.avatar_url;
        } else {
            const initial = (user.username || 'U').charAt(0).toUpperCase();
            avatarImg.src = `https://ui-avatars.com/api/?name=${initial}&background=3b82f6&color=fff&size=128`;
        }
    }

    // Form Fields
    setValue('fname', profile.fname);
    setValue('lname', profile.lname);
    setValue('phone', profile.phone);
    setValue('postal', profile.postal_code);

    // Render Reviews
    renderMyReviews(reviews);
}

function renderMyReviews(reviews) {
    const container = document.getElementById('my-reviews-list');
    if (!container) return;

    if (!reviews || reviews.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5 border border-dashed border-secondary border-opacity-25 rounded-3">
                <i class="bi bi-chat-square-text text-secondary display-6 mb-3 d-block opacity-50"></i>
                <p class="text-gray-400 mb-0">You haven't written any reviews yet.</p>
            </div>`;
        return;
    }

    container.innerHTML = reviews.map(r => {
        const stars = '<i class="bi bi-star-fill"></i>'.repeat(r.score) + '<i class="bi bi-star"></i>'.repeat(5 - r.score);
        const dateStr = new Date(r.created_at).toLocaleDateString('en-SG', { day: 'numeric', month: 'short', year: 'numeric' });
        
        return `
            <div class="review-item" style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem;">
                <div class="review-header" style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255, 255, 255, 0.05); padding-bottom: 0.75rem; margin-bottom: 0.75rem;">
                    <a href="/event-detail?id=${r.event_identifier}" class="review-event-title" style="color: #60a5fa; text-decoration: none; font-weight: 700;">
                        <i class="bi bi-calendar-event me-2"></i> ${escapeHtml(r.event_title)}
                    </a>
                    <div class="text-end">
                        <div class="review-stars mb-1" style="color: #fbbf24;">${stars}</div>
                        <div class="review-date" style="font-size: 0.75rem; color: #64748b;">${dateStr}</div>
                    </div>
                </div>
                
                <div class="review-content">
                    <h6 style="color: #e2e8f0; font-weight: 600;">${escapeHtml(r.title || 'No Title')}</h6>
                    <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 0;">${escapeHtml(r.body || '')}</p>
                </div>
            </div>
        `;
    }).join('');
}


// --- PREFERENCES / TAGS ---

async function loadTags() {
    try {
        const res = await fetch(`${API_BASE}/tags`, { credentials: 'include' });
        if (res.ok) {
            allTags = await res.json();
            await loadUserPreferences();
        }
    } catch (e) { console.error("Tags error:", e); }
}

async function loadUserPreferences() {
    try {
        const res = await fetch(`${API_BASE}/preferences/me`, { credentials: 'include' });
        if (res.ok) {
            const data = await res.json();
            userPreferences = data.preferences.map(p => p.tag_id);
            renderTags();
        }
    } catch (e) { console.error("Prefs error:", e); }
}

function renderTags() {
    const container = document.getElementById('tags-container');
    if (!container) return;
    container.innerHTML = '';

    allTags.forEach(tag => {
        const isActive = userPreferences.includes(tag.id);
        const tagName = tag.tag_name || tag.name || 'Tag';

        const pill = document.createElement('div');
        pill.className = `tag-pill ${isActive ? 'active' : ''}`;
        pill.innerHTML = `<span>${escapeHtml(tagName)}</span>`;
        if (isActive) pill.innerHTML += '<i class="bi bi-check-circle-fill small"></i>';

        pill.onclick = () => toggleTag(tag.id, pill);
        container.appendChild(pill);
    });
}

async function toggleTag(tagId, element) {
    const isAdding = !element.classList.contains('active');
    const method = isAdding ? 'POST' : 'DELETE';
    const url = isAdding ? `${API_BASE}/preferences/me` : `${API_BASE}/preferences/me/${tagId}`;
    const options = { method: method };

    if (isAdding) {
        options.headers = { 'Content-Type': 'application/json' };
        options.body = JSON.stringify({ tag_id: tagId });
    }

    try {
        // Optimistic UI update
        element.classList.toggle('active');
        const spanText = element.querySelector('span').innerText;
        if (isAdding) element.innerHTML = `<span>${spanText}</span><i class="bi bi-check-circle-fill small"></i>`;
        else element.innerHTML = `<span>${spanText}</span>`;

        const res = await fetch(url, options);
        if (!res.ok) throw new Error();
    } catch (e) {
        element.classList.toggle('active'); // Revert
        showToast('Failed to update preference', 'text-bg-danger');
    }
}


// --- FORM HANDLING ---

function handleAvatarSelect(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
            document.getElementById('display-avatar').src = e.target.result;
            showToast('Image selected. Click "Save Changes" to apply.', 'text-bg-info');
        };
        reader.readAsDataURL(file);
    }
}

async function handleProfileUpdate(e) {
    e.preventDefault();
    const btn = document.getElementById('save-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving...';

    const formData = new FormData(e.target);

    try {
        const res = await fetch(`${API_BASE}/profile/me`, {
            method: 'PUT',
            body: formData
        });

        const data = await res.json();

        if (res.ok) {
            showToast('Profile updated successfully!', 'text-bg-success');
            // Update Navbar Avatar if it exists
            const navImg = document.getElementById('nav-user-img');
            const navInitial = document.getElementById('nav-user-initial');
            if (data.profile.avatar_url && navImg) {
                navImg.src = data.profile.avatar_url + '?t=' + new Date().getTime();
            } else if (data.profile.avatar_url && navInitial) {
                window.location.reload(); // Refresh to switch from letter to image
            }
            await loadProfile();
        } else {
            showToast(data.error || 'Update failed', 'text-bg-danger');
        }
    } catch (e) {
        console.error(e);
        showToast('Server error', 'text-bg-danger');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Save Changes';
    }
}

// --- ACCOUNT DELETION ---

window.handleDeleteAccount = async function () {
    const confirmMsg = "WARNING: This cannot be undone!\n\nDeleting your account will remove:\n• Your profile\n• All events you created\n• All reviews and bookmarks\n\nAre you absolutely sure?";
    if (!confirm(confirmMsg)) return;

    const doubleCheck = confirm("Final Confirmation: Delete account permanently?");
    if (!doubleCheck) return;

    try {
        const res = await fetch(`${API_BASE}/delete-account`, {
            method: 'DELETE',
            credentials: 'include'
        });

        const data = await res.json();

        if (res.ok) {
            alert('Account deleted. Redirecting to home...');
            window.location.href = '/';
        } else {
            alert(data.message || 'Failed to delete account');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Network error occurred.');
    }
};


// --- UTILITIES ---

function setupValidationListeners() {
    // Basic real-time validation visual cues could go here
    // Currently handled by server response feedback
}

function showToast(msg, bgClass) {
    const el = document.getElementById('liveToast');
    if (!el) return;
    document.getElementById('toast-message').textContent = msg;
    el.className = `toast align-items-center border-0 ${bgClass}`;
    new bootstrap.Toast(el).show();
}

function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function setValue(id, val) {
    const el = document.getElementById(id);
    if (el) el.value = val || '';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}