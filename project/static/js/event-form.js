// event-form.js - Handle event creation and editing with validation
const API_BASE = window.API_BASE || '/api';

// Determine if we're creating or editing based on URL
const isEditMode = window.location.pathname.includes('/event-edit');
let eventId = null;
let selectedImageFile = null;

// Load event data for editing
async function loadEventData() {
  // Get event ID from URL query parameter
  const urlParams = new URLSearchParams(window.location.search);
  eventId = urlParams.get('id');
  
  if (!eventId) {
    showFeedback('No event ID provided', 'error');
    return;
  }
  
  try {
    const res = await fetch(`${API_BASE}/events/${eventId}`, {
      credentials: 'include'
    });
    
    if (!res.ok) {
      if (res.status === 404) {
        throw new Error('Event not found');
      }
      throw new Error('Failed to load event');
    }
    
    const event = await res.json();
    populateForm(event);
    
  } catch (error) {
    console.error('Error loading event:', error);
    showFeedback(error.message || 'Failed to load event data', 'error');
  }
}

// Populate form with event data
function populateForm(event) {
  document.getElementById('event-id').value = event.id;
  document.getElementById('title').value = event.title || '';
  document.getElementById('description').value = event.description || '';
  document.getElementById('location').value = event.location || '';
  
  // Populate venue fields if venue data is available
  if (event.venue) {
    document.getElementById('venue-name').value = event.venue.name || '';
    document.getElementById('venue-address').value = event.venue.address || '';
    document.getElementById('venue-postal').value = event.venue.postal_code || '';
  }
  
  // Display current image if available
  if (event.image_url) {
    const preview = document.getElementById('image-preview-img');
    if (preview) {
      preview.src = event.image_url;
    }
  }
  
  // Parse datetime fields
  if (event.start_datetime) {
    const startDate = new Date(event.start_datetime);
    document.getElementById('start-date').value = formatDate(startDate);
    document.getElementById('start-time').value = formatTime(startDate);
  }
  
  if (event.end_datetime) {
    const endDate = new Date(event.end_datetime);
    document.getElementById('end-date').value = formatDate(endDate);
    document.getElementById('end-time').value = formatTime(endDate);
  }
  
  // Update character count
  updateCharCount();
}

// Format date as YYYY-MM-DD
function formatDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// Format time as HH:MM
function formatTime(date) {
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${hours}:${minutes}`;
}

// Validation functions
function validateTitle(title) {
  if (!title || title.trim() === '') {
    return 'Event title is required';
  }
  if (title.length > 255) {
    return 'Event title must be less than 255 characters';
  }
  return null;
}

function validateDescription(description) {
  if (description && description.length > 2000) {
    return 'Description must be less than 2000 characters';
  }
  return null;
}

function validateDateTime(startDate, startTime, endDate, endTime) {
  if (!startDate) {
    return { field: 'start-date', error: 'Start date is required' };
  }
  if (!startTime) {
    return { field: 'start-time', error: 'Start time is required' };
  }
  if (!endDate) {
    return { field: 'end-date', error: 'End date is required' };
  }
  if (!endTime) {
    return { field: 'end-time', error: 'End time is required' };
  }
  
  // Combine date and time
  const start = new Date(`${startDate}T${startTime}`);
  const end = new Date(`${endDate}T${endTime}`);
  const now = new Date();
  
  // Check if dates are valid
  if (isNaN(start.getTime())) {
    return { field: 'start-date', error: 'Invalid start date/time' };
  }
  if (isNaN(end.getTime())) {
    return { field: 'end-date', error: 'Invalid end date/time' };
  }
  
  // Check if start is in the past (only for new events)
  if (!isEditMode && start < now) {
    return { field: 'start-date', error: 'Start date/time must be in the future' };
  }
  
  // Check if end is after start
  if (end <= start) {
    return { field: 'end-date', error: 'End date/time must be after start date/time' };
  }
  
  return null;
}

function validateVenueName(name) {
  if (!name || name.trim() === '') {
    return 'Venue name is required';
  }
  if (name.length > 255) {
    return 'Venue name must be less than 255 characters';
  }
  return null;
}

function validateVenueAddress(address) {
  if (!address || address.trim() === '') {
    return 'Venue address is required';
  }
  if (address.length > 255) {
    return 'Venue address must be less than 255 characters';
  }
  return null;
}

function validateVenuePostal(postal) {
  if (!postal || postal.trim() === '') {
    return 'Venue postal code is required';
  }
  const postalRegex = /^\d{6}$/;
  if (!postalRegex.test(postal.trim())) {
    return 'Postal code must be exactly 6 digits';
  }
  return null;
}

function validateImageFile(file) {
  if (!file) return null; // Optional field
  
  // Check file type
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
  if (!allowedTypes.includes(file.type)) {
    return 'Image must be JPEG, PNG, or WebP format';
  }
  
  // Check file size (5MB = 5 * 1024 * 1024 bytes)
  const maxSize = 5 * 1024 * 1024;
  if (file.size > maxSize) {
    return 'Image must be less than 5MB';
  }
  
  return null;
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
  
  const inputs = document.querySelectorAll('.event-form input, .event-form textarea, .event-form select');
  inputs.forEach(input => {
    input.classList.remove('error');
  });
  
  const feedback = document.getElementById('form-feedback');
  if (feedback) {
    feedback.textContent = '';
  }
}

// Show feedback message
function showFeedback(message, type = 'success') {
  const feedback = document.getElementById('form-feedback');
  if (feedback) {
    feedback.textContent = message;
    feedback.style.color = type === 'error' ? '#ff5454' : '#4caf50';
    feedback.style.display = 'block';
  }
}

// Update character count
function updateCharCount() {
  const description = document.getElementById('description');
  const countSpan = document.getElementById('desc-count');
  if (description && countSpan) {
    countSpan.textContent = description.value.length;
  }
}

// Handle image file selection
function handleImageSelect(event) {
  const file = event.target.files[0];
  if (!file) return;
  
  const error = validateImageFile(file);
  if (error) {
    showError('image', error);
    selectedImageFile = null;
    return;
  }
  
  selectedImageFile = file;
  showError('image', null);
  
  // Show preview
  const reader = new FileReader();
  reader.onload = function(e) {
    const preview = document.getElementById('image-preview-img');
    if (preview) {
      preview.src = e.target.result;
    }
  };
  reader.readAsDataURL(file);
}

// Handle image removal
function handleImageRemove() {
  selectedImageFile = null;
  const fileInput = document.getElementById('image-upload');
  const preview = document.getElementById('image-preview-img');
  
  if (fileInput) {
    fileInput.value = '';
  }
  
  if (preview) {
    preview.src = '/static/assets/images/default-event.svg';
  }
  
  showError('image', null);
}

// Trigger file input click
function triggerImageUpload() {
  const fileInput = document.getElementById('image-upload');
  if (fileInput) {
    fileInput.click();
  }
}

// Create event
async function createEvent(formData) {
  try {
    console.log('Creating event with FormData...');
    const res = await fetch(`${API_BASE}/events`, {
      method: 'POST',
      credentials: 'include',
      body: formData // Send FormData directly, browser sets correct Content-Type
    });
    
    const data = await res.json();
    console.log('Server response:', data);
    
    if (res.ok) {
      return { success: true, event: data };
    } else {
      return { success: false, error: data.error || 'Failed to create event' };
    }
  } catch (error) {
    console.error('Error creating event:', error);
    return { success: false, error: 'Network error' };
  }
}

// Update event
async function updateEvent(eventId, formData) {
  try {
    const res = await fetch(`${API_BASE}/events/${eventId}`, {
      method: 'PUT',
      credentials: 'include',
      body: formData // Send FormData directly
    });
    
    const data = await res.json();
    
    if (res.ok) {
      return { success: true, event: data };
    } else {
      return { success: false, error: data.error || 'Failed to update event' };
    }
  } catch (error) {
    console.error('Error updating event:', error);
    return { success: false, error: 'Network error' };
  }
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
      showFeedback('Event deleted successfully!', 'success');
      setTimeout(() => {
        window.location.href = '/';
      }, 1500);
    } else {
      const data = await res.json();
      showFeedback(data.error || 'Failed to delete event', 'error');
    }
  } catch (error) {
    console.error('Error deleting event:', error);
    showFeedback('Network error', 'error');
  }
}

// Initialize page
document.addEventListener('DOMContentLoaded', async () => {
  // If edit mode, load event data
  if (isEditMode) {
    await loadEventData();
  }
  
  // Character count update
  const description = document.getElementById('description');
  if (description) {
    description.addEventListener('input', updateCharCount);
  }
  
  // Image upload handlers
  const imageUpload = document.getElementById('image-upload');
  const chooseImageBtn = document.getElementById('choose-image-btn');
  const removeImageBtn = document.getElementById('remove-image-btn');
  
  if (imageUpload) {
    imageUpload.addEventListener('change', handleImageSelect);
  }
  
  if (chooseImageBtn) {
    chooseImageBtn.addEventListener('click', triggerImageUpload);
  }
  
  if (removeImageBtn) {
    removeImageBtn.addEventListener('click', handleImageRemove);
  }
  
  // Real-time validation
  const titleInput = document.getElementById('title');
  const startDateInput = document.getElementById('start-date');
  const startTimeInput = document.getElementById('start-time');
  const endDateInput = document.getElementById('end-date');
  const endTimeInput = document.getElementById('end-time');
  const venueNameInput = document.getElementById('venue-name');
  const venueAddressInput = document.getElementById('venue-address');
  const venuePostalInput = document.getElementById('venue-postal');
  
  if (titleInput) {
    titleInput.addEventListener('blur', () => {
      const error = validateTitle(titleInput.value.trim());
      showError('title', error);
    });
  }
  
  if (description) {
    description.addEventListener('blur', () => {
      const error = validateDescription(description.value);
      showError('description', error);
    });
  }
  
  if (venueNameInput) {
    venueNameInput.addEventListener('blur', () => {
      const error = validateVenueName(venueNameInput.value.trim());
      showError('venue-name', error);
    });
  }
  
  if (venueAddressInput) {
    venueAddressInput.addEventListener('blur', () => {
      const error = validateVenueAddress(venueAddressInput.value.trim());
      showError('venue-address', error);
    });
  }
  
  if (venuePostalInput) {
    venuePostalInput.addEventListener('blur', () => {
      const error = validateVenuePostal(venuePostalInput.value.trim());
      showError('venue-postal', error);
    });
  }
  
  // Validate datetime on change
  const validateDateTimes = () => {
    if (startDateInput && startTimeInput && endDateInput && endTimeInput) {
      const error = validateDateTime(
        startDateInput.value,
        startTimeInput.value,
        endDateInput.value,
        endTimeInput.value
      );
      
      if (error) {
        showError(error.field, error.error);
      } else {
        showError('start-date', null);
        showError('start-time', null);
        showError('end-date', null);
        showError('end-time', null);
      }
    }
  };
  
  [startDateInput, startTimeInput, endDateInput, endTimeInput].forEach(input => {
    if (input) {
      input.addEventListener('change', validateDateTimes);
    }
  });
  
  // Delete button handler (edit mode only)
  const deleteBtn = document.getElementById('delete-btn');
  if (deleteBtn && isEditMode) {
    deleteBtn.addEventListener('click', () => {
      if (eventId) {
        deleteEvent(eventId);
      }
    });
  }
  
  // Form submission handler
  const eventForm = document.getElementById('event-form');
  if (eventForm) {
    eventForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      clearErrors();
      
      // Get form values
      const title = titleInput.value.trim();
      const descriptionVal = description.value.trim();
      const startDate = startDateInput.value;
      const startTime = startTimeInput.value;
      const endDate = endDateInput.value;
      const endTime = endTimeInput.value;
      const location = document.getElementById('location').value.trim();
      const venueName = venueNameInput.value.trim();
      const venueAddress = venueAddressInput.value.trim();
      const venuePostal = venuePostalInput.value.trim();
      
      // Validate all fields
      let hasErrors = false;
      
      const titleError = validateTitle(title);
      if (titleError) {
        showError('title', titleError);
        hasErrors = true;
      }
      
      const descError = validateDescription(descriptionVal);
      if (descError) {
        showError('description', descError);
        hasErrors = true;
      }
      
      const dateTimeError = validateDateTime(startDate, startTime, endDate, endTime);
      if (dateTimeError) {
        showError(dateTimeError.field, dateTimeError.error);
        hasErrors = true;
      }
      
      const venueNameError = validateVenueName(venueName);
      if (venueNameError) {
        showError('venue-name', venueNameError);
        hasErrors = true;
      }
      
      const venueAddressError = validateVenueAddress(venueAddress);
      if (venueAddressError) {
        showError('venue-address', venueAddressError);
        hasErrors = true;
      }
      
      const venuePostalError = validateVenuePostal(venuePostal);
      if (venuePostalError) {
        showError('venue-postal', venuePostalError);
        hasErrors = true;
      }
      
      const imageError = validateImageFile(selectedImageFile);
      if (imageError) {
        showError('image', imageError);
        hasErrors = true;
      }
      
      if (hasErrors) {
        showFeedback('Please fix the errors above', 'error');
        return;
      }
      
      // Combine date and time into ISO format
      const startDatetime = new Date(`${startDate}T${startTime}`).toISOString();
      const endDatetime = new Date(`${endDate}T${endTime}`).toISOString();
      
      // Build FormData
      const formData = new FormData();
      formData.append('title', title);
      formData.append('description', descriptionVal || '');
      formData.append('start_datetime', startDatetime);
      formData.append('end_datetime', endDatetime);
      formData.append('location', location || '');
      formData.append('venue_name', venueName);
      formData.append('venue_address', venueAddress);
      formData.append('venue_postal', venuePostal);
      
      // Add image file if selected
      if (selectedImageFile) {
        formData.append('image', selectedImageFile);
      }
      
      // Create or update
      let result;
      if (isEditMode && eventId) {
        result = await updateEvent(eventId, formData);
      } else {
        result = await createEvent(formData);
      }
      
      if (result.success) {
        const action = isEditMode ? 'updated' : 'created';
        showFeedback(`Event ${action} successfully!`, 'success');
        
        // Redirect to home after delay
        setTimeout(() => {
          window.location.href = '/';
        }, 1500);
      } else {
        showFeedback(result.error || `Failed to ${isEditMode ? 'update' : 'create'} event`, 'error');
      }
    });
  }
});
