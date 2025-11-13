// profile.js - Handle profile viewing and editing
const API_BASE = window.API_BASE || '/api';

let currentProfile = null;
let selectedAvatarFile = null;
let allTags = [];
let userPreferences = [];

// Fetch user profile data
async function loadProfile() {
  try {
    const res = await fetch(`${API_BASE}/profile/me`, {
      credentials: 'include'
    });

    if (!res.ok) {
      if (res.status === 401) {
        // Not logged in, redirect to login
        window.location.href = '/login';
        return;
      }
      throw new Error('Failed to load profile');
    }

    const data = await res.json();
    currentProfile = data;
    displayProfile(data);
  } catch (error) {
    console.error('Error loading profile:', error);
    showFeedback('Failed to load profile', 'error');
  }
}

// Display profile data in view mode
function displayProfile(data) {
  const { user, profile } = data;

  // Display user info
  document.getElementById('username-display').textContent = user.username || '—';
  document.getElementById('email-display').textContent = user.email || '—';

  // Display profile info
  document.getElementById('fname-display').textContent = profile.fname || '—';
  document.getElementById('lname-display').textContent = profile.lname || '—';
  document.getElementById('phone-display').textContent = profile.phone ? `+65 ${profile.phone}` : '—';
  document.getElementById('postal-display').textContent = profile.postal_code || '—';

  // Display avatar
  const avatarImg = document.getElementById('avatar-display');
  if (profile.avatar_url) {
    avatarImg.src = profile.avatar_url;
    avatarImg.onerror = function () {
      this.src = '/static/assets/images/default-avatar.svg';
    };
  } else {
    avatarImg.src = '/static/assets/images/default-avatar.svg';
  }
}

// Populate edit form with current data
function populateEditForm() {
  if (!currentProfile) return;

  const { profile } = currentProfile;

  // Set avatar preview
  const avatarPreview = document.getElementById('avatar-preview-img');
  if (profile.avatar_url) {
    avatarPreview.src = profile.avatar_url;
  } else {
    avatarPreview.src = '/static/assets/images/default-avatar.svg';
  }

  // Reset file input
  selectedAvatarFile = null;
  const fileInput = document.getElementById('avatar-upload');
  if (fileInput) fileInput.value = '';

  // Show/hide remove button
  const removeBtn = document.getElementById('remove-avatar-btn');
  if (removeBtn) {
    removeBtn.style.display = profile.avatar_url ? 'inline-block' : 'none';
  }

  // Populate other fields
  document.getElementById('fname').value = profile.fname || '';
  document.getElementById('lname').value = profile.lname || '';
  document.getElementById('phone').value = profile.phone || '';
  document.getElementById('postal-code').value = profile.postal_code || '';
}

// Switch to edit mode
function enterEditMode() {
  document.getElementById('profile-view').classList.add('hidden');
  document.getElementById('profile-edit').classList.remove('hidden');
  populateEditForm();
  clearErrors();
}

// Switch to view mode
function exitEditMode() {
  document.getElementById('profile-edit').classList.add('hidden');
  document.getElementById('profile-view').classList.remove('hidden');
  clearErrors();
}

// Validation functions
function validateName(name, fieldName, required = false) {
  if (!name && !required) return null; // Optional field
  if (!name && required) return `${fieldName} is required`;
  if (name.length > 45) return `${fieldName} must be less than 45 characters`;
  if (!/^[a-zA-Z\s'-]+$/.test(name)) {
    return `${fieldName} can only contain letters, spaces, hyphens, and apostrophes`;
  }
  return null;
}

function validatePhone(phone) {
  if (!phone) return null; // Optional
  if (phone.length !== 8) return 'Phone number must be exactly 8 digits';
  if (!/^\d{8}$/.test(phone)) {
    return 'Phone number must be 8 digits only (no spaces or symbols)';
  }
  return null;
}

function validatePostalCode(postal) {
  if (!postal) return null; // Optional
  if (postal.length !== 6) return 'Postal code must be exactly 6 digits';
  if (!/^\d{6}$/.test(postal)) return 'Postal code must be 6 digits';
  return null;
}

function validateAvatarFile(file) {
  if (!file) return null; // Optional

  // Check file type
  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
  if (!allowedTypes.includes(file.type)) {
    return 'Only JPEG, PNG, and WebP images are allowed';
  }

  // Check file size (3MB max)
  const maxSize = 3 * 1024 * 1024; // 3MB in bytes
  if (file.size > maxSize) {
    return `File size must be less than 3MB (current: ${(file.size / 1024 / 1024).toFixed(2)}MB)`;
  }

  return null;
}

async function validateAvatarDimensions(file) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = function (e) {
      const img = new Image();
      img.onload = function () {
        const minSize = 268;
        if (img.width < minSize || img.height < minSize) {
          resolve(`Image dimensions must be at least ${minSize}×${minSize}px (current: ${img.width}×${img.height}px)`);
        } else {
          resolve(null);
        }
      };
      img.onerror = function () {
        resolve('Failed to load image');
      };
      img.src = e.target.result;
    };
    reader.onerror = function () {
      resolve('Failed to read file');
    };
    reader.readAsDataURL(file);
  });
}

// Show error message
function showError(fieldId, message) {
  const errorElement = document.getElementById(`${fieldId}-error`);
  const inputElement = document.getElementById(fieldId);

  if (errorElement) {
    errorElement.textContent = message || '';
    errorElement.style.display = message ? 'block' : 'none';
  }

  if (inputElement) {
    if (message) {
      inputElement.classList.add('error');
    } else {
      inputElement.classList.remove('error');
    }
  }
}

// Clear all errors
function clearErrors() {
  const errorElements = document.querySelectorAll('.error-message');
  errorElements.forEach(el => {
    el.textContent = '';
    el.style.display = 'none';
  });

  const inputs = document.querySelectorAll('.profile-form input');
  inputs.forEach(input => {
    input.classList.remove('error');
  });

  const feedback = document.getElementById('profile-feedback');
  if (feedback) {
    feedback.textContent = '';
  }
}

// Show feedback message
function showFeedback(message, type = 'success') {
  const feedback = document.getElementById('profile-feedback');
  if (feedback) {
    feedback.textContent = message;
    feedback.style.color = type === 'error' ? '#ff5454' : '#4caf50';
    feedback.style.display = 'block';

    // Auto-hide after 3 seconds
    setTimeout(() => {
      feedback.style.display = 'none';
    }, 3000);
  }
}

// Update profile
async function updateProfile(formData) {
  try {
    const res = await fetch(`${API_BASE}/profile/me`, {
      method: 'PUT',
      credentials: 'include',
      body: formData // FormData will set Content-Type automatically
    });

    const data = await res.json();

    if (res.ok) {
      return { success: true, profile: data.profile };
    } else {
      return { success: false, error: data.error || 'Update failed' };
    }
  } catch (error) {
    console.error('Error updating profile:', error);
    return { success: false, error: 'Network error' };
  }
}

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
  // Load profile data
  loadProfile();

  // Load tags and preferences
  loadTags();

  // Edit button handler
  const editBtn = document.getElementById('edit-profile-btn');
  if (editBtn) {
    editBtn.addEventListener('click', enterEditMode);
  }

  // Cancel button handler
  const cancelBtn = document.getElementById('cancel-edit-btn');
  if (cancelBtn) {
    cancelBtn.addEventListener('click', exitEditMode);
  }

  // Avatar upload handlers
  const chooseAvatarBtn = document.getElementById('choose-avatar-btn');
  const avatarFileInput = document.getElementById('avatar-upload');
  const removeAvatarBtn = document.getElementById('remove-avatar-btn');
  const avatarPreview = document.getElementById('avatar-preview-img');

  if (chooseAvatarBtn && avatarFileInput) {
    chooseAvatarBtn.addEventListener('click', () => {
      avatarFileInput.click();
    });

    avatarFileInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      clearErrors();

      // Validate file type and size
      const fileError = validateAvatarFile(file);
      if (fileError) {
        showError('avatar', fileError);
        avatarFileInput.value = '';
        return;
      }

      // Validate dimensions
      const dimensionError = await validateAvatarDimensions(file);
      if (dimensionError) {
        showError('avatar', dimensionError);
        avatarFileInput.value = '';
        return;
      }

      // File is valid, set preview and store file
      selectedAvatarFile = file;
      const reader = new FileReader();
      reader.onload = function (e) {
        avatarPreview.src = e.target.result;
        if (removeAvatarBtn) {
          removeAvatarBtn.style.display = 'inline-block';
        }
      };
      reader.readAsDataURL(file);
    });
  }

  if (removeAvatarBtn) {
    removeAvatarBtn.addEventListener('click', () => {
      selectedAvatarFile = 'remove'; // Special marker to remove avatar
      avatarPreview.src = '/static/assets/images/default-avatar.svg';
      if (avatarFileInput) avatarFileInput.value = '';
      removeAvatarBtn.style.display = 'none';
    });
  }

  // Form validation on blur
  const fnameInput = document.getElementById('fname');
  const lnameInput = document.getElementById('lname');
  const phoneInput = document.getElementById('phone');
  const postalInput = document.getElementById('postal-code');

  if (fnameInput) {
    fnameInput.addEventListener('blur', () => {
      const error = validateName(fnameInput.value.trim(), 'First name', false);
      showError('fname-edit', error);
    });
  }

  if (lnameInput) {
    lnameInput.addEventListener('blur', () => {
      const error = validateName(lnameInput.value.trim(), 'Last name', false);
      showError('lname-edit', error);
    });
  }

  if (phoneInput) {
    phoneInput.addEventListener('blur', () => {
      const error = validatePhone(phoneInput.value.trim());
      showError('phone', error);
    });
  }

  if (postalInput) {
    postalInput.addEventListener('blur', () => {
      const error = validatePostalCode(postalInput.value.trim());
      showError('postal', error);
    });
  }

  // Form submission handler
  const profileForm = document.getElementById('profile-form');
  if (profileForm) {
    profileForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      clearErrors();

      // Get form values
      const fname = fnameInput.value.trim();
      const lname = lnameInput.value.trim();
      const phone = phoneInput.value.trim();
      const postal = postalInput.value.trim();

      // Validate all fields
      let hasErrors = false;

      const fnameError = validateName(fname, 'First name', false);
      if (fnameError) {
        showError('fname-edit', fnameError);
        hasErrors = true;
      }

      const lnameError = validateName(lname, 'Last name', false);
      if (lnameError) {
        showError('lname-edit', lnameError);
        hasErrors = true;
      }

      const phoneError = validatePhone(phone);
      if (phoneError) {
        showError('phone', phoneError);
        hasErrors = true;
      }

      const postalError = validatePostalCode(postal);
      if (postalError) {
        showError('postal', postalError);
        hasErrors = true;
      }

      if (hasErrors) {
        showFeedback('Please fix the errors above', 'error');
        return;
      }

      // Build FormData for file upload
      const formData = new FormData();
      formData.append('fname', fname);
      formData.append('lname', lname);
      formData.append('phone', phone);
      formData.append('postal_code', postal);

      // Handle avatar
      if (selectedAvatarFile === 'remove') {
        formData.append('remove_avatar', 'true');
      } else if (selectedAvatarFile) {
        formData.append('avatar', selectedAvatarFile);
      }

      const result = await updateProfile(formData);

      if (result.success) {
        showFeedback('Profile updated successfully!', 'success');
        selectedAvatarFile = null; // Reset
        // Reload profile data and exit edit mode
        await loadProfile();
        setTimeout(() => {
          exitEditMode();
        }, 1000);
      } else {
        showFeedback(result.error || 'Failed to update profile', 'error');
      }
    });
  }

  // Delete account button handler
  const deleteAccountBtn = document.getElementById('delete-account-btn');
  if (deleteAccountBtn) {
    deleteAccountBtn.addEventListener('click', async () => {
      await handleDeleteAccount();
    });
  }
});

// Handle delete account with confirmation
async function handleDeleteAccount() {
  // Show confirmation dialog
  const confirmMessage = `WARNING: This action cannot be undone!\n\nDeleting your account will permanently remove:\n• Your profile and personal information\n• All events you created\n• All your reviews and Bookmarks\n• All uploaded images\n\nAre you absolutely sure you want to delete your account?`;

  if (!confirm(confirmMessage)) {
    return;
  }

  // Second confirmation
  const finalConfirm = confirm('This is your final warning. Delete account permanently?');
  if (!finalConfirm) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/delete-account`, {
      method: 'DELETE',
      credentials: 'include'
    });

    const data = await res.json();

    if (res.ok && data.status === 'success') {
      alert('Your account has been successfully deleted. You will now be redirected to the home page.');
      window.location.href = '/';
    } else {
      alert(`Failed to delete account: ${data.message || 'Unknown error'}`);
    }
  } catch (error) {
    console.error('Error deleting account:', error);
    alert('Failed to delete account. Please try again or contact support.');
  }
}

// ===== USER PREFERENCES / TAGS =====

// Load all available tags
async function loadTags() {
  try {
    const res = await fetch(`${API_BASE}/tags`, {
      credentials: 'include'
    });

    if (!res.ok) throw new Error('Failed to load tags');

    allTags = await res.json();
    await loadUserPreferences();
  } catch (error) {
    console.error('Error loading tags:', error);
    showPreferencesFeedback('Failed to load tags', 'error');
  }
}

// Load user's current preferences
async function loadUserPreferences() {
  try {
    const res = await fetch(`${API_BASE}/preferences/me`, {
      credentials: 'include'
    });

    if (!res.ok) throw new Error('Failed to load preferences');

    const data = await res.json();
    userPreferences = data.preferences.map(p => p.tag_id);

    renderTags();
  } catch (error) {
    console.error('Error loading preferences:', error);
    showPreferencesFeedback('Failed to load preferences', 'error');
  }
}

// Render tags as selectable chips
function renderTags() {
  const container = document.getElementById('tags-container');
  if (!container) return;

  if (allTags.length === 0) {
    container.innerHTML = '<p class="empty-state">No tags available yet</p>';
    return;
  }

  container.innerHTML = allTags.map(tag => {
    const isSelected = userPreferences.includes(tag.id);
    const icon = getTagIcon(tag.tag_name);

    return `
      <div class="tag-chip ${isSelected ? 'selected' : ''}" 
           data-tag-id="${tag.id}" 
           onclick="togglePreference(${tag.id}, '${escapeHtml(tag.tag_name)}')">
        <span class="tag-icon">${icon}</span>
        <span>${escapeHtml(tag.tag_name)}</span>
      </div>
    `;
  }).join('');
}

// Toggle tag preference
async function togglePreference(tagId, tagName) {
  const isCurrentlySelected = userPreferences.includes(tagId);

  try {
    if (isCurrentlySelected) {
      // Remove preference
      const res = await fetch(`${API_BASE}/preferences/me/${tagId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (!res.ok) throw new Error('Failed to remove preference');

      userPreferences = userPreferences.filter(id => id !== tagId);
      showPreferencesFeedback(`Removed "${tagName}" from your interests`, 'success');
    } else {
      // Add preference
      const res = await fetch(`${API_BASE}/preferences/me`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ tag_id: tagId })
      });

      if (!res.ok) throw new Error('Failed to add preference');

      userPreferences.push(tagId);
      showPreferencesFeedback(`Added "${tagName}" to your interests`, 'success');
    }

    renderTags();
  } catch (error) {
    console.error('Error toggling preference:', error);
    showPreferencesFeedback('Failed to update preference', 'error');
  }
}

// Get icon for tag
function getTagIcon(tagName) {
  const icons = {
    'music': '🎵',
    'theatre': '🎭',
    'comedy': '😂',
    'film': '🎬',
    'visual arts': '🎨',
    'visual-arts': '🎨',
    'workshops': '🛠️',
    'food': '🍽️',
    'sports': '⚽',
    'technology': '💻',
    'dance': '💃',
    'literature': '📚',
    'festival': '🎪',
    'exhibition': '🖼️',
    'concert': '🎤',
    'performance': '🎪'
  };

  const normalized = tagName.toLowerCase().replace(/\s+/g, '-');
  return icons[normalized] || icons[tagName.toLowerCase()] || '🏷️';
}

// Show feedback for preferences
function showPreferencesFeedback(message, type = 'success') {
  const feedback = document.getElementById('preferences-feedback');
  if (!feedback) return;

  feedback.textContent = message;
  feedback.className = `preferences-feedback ${type}`;

  setTimeout(() => {
    feedback.textContent = '';
    feedback.className = 'preferences-feedback';
  }, 3000);
}

// Utility function to escape HTML
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Make togglePreference available globally
window.togglePreference = togglePreference;
