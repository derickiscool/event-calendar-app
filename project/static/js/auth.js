// auth.js — login/register/logout handlers with session management
const API_BASE = window.API_BASE || '/api';

// Check authentication status on page load
export async function checkAuthStatus() {
  try {
    const res = await fetch(`${API_BASE}/auth/status`, {
      credentials: 'include' // Include session cookie
    });
    const data = await res.json();
    return data;
  } catch (error) {
    console.error('Auth status check failed:', error);
    return { authenticated: false };
  }
}

// Login handler
export async function login(email, password) {
  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, password })
    });
    
    const data = await res.json();
    
    if (res.ok) {
      return { success: true, user: data.user };
    } else {
      return { success: false, error: data.error || 'Login failed' };
    }
  } catch (error) {
    console.error('Login error:', error);
    return { success: false, error: 'Network error' };
  }
}

// Register handler
export async function register(userData) {
  try {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(userData)
    });
    
    const data = await res.json();
    
    if (res.ok) {
      return { success: true, user: data.user };
    } else {
      return { success: false, error: data.error || 'Registration failed' };
    }
  } catch (error) {
    console.error('Registration error:', error);
    return { success: false, error: 'Network error' };
  }
}

// Logout handler
export async function logout() {
  try {
    const res = await fetch(`${API_BASE}/auth/logout`, {
      method: 'POST',
      credentials: 'include'
    });
    
    if (res.ok) {
      return { success: true };
    } else {
      return { success: false, error: 'Logout failed' };
    }
  } catch (error) {
    console.error('Logout error:', error);
    return { success: false, error: 'Network error' };
  }
}

// --- Validation Helpers ---

// Sanitize input (trim whitespace, remove dangerous characters)
function sanitizeInput(input, allowSpaces = false) {
  if (!input) return '';
  let sanitized = input.trim();
  // Remove null bytes and control characters
  sanitized = sanitized.replace(/[\0\x08\x09\x1a\n\r"'\\\%]/g, '');
  if (!allowSpaces) {
    sanitized = sanitized.replace(/\s/g, '');
  }
  return sanitized;
}

// Email validation
function validateEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!email) return 'Email is required';
  if (!emailRegex.test(email)) return 'Please enter a valid email address';
  if (email.length > 255) return 'Email must be less than 255 characters';
  return null;
}

// Username validation
function validateUsername(username) {
  if (!username) return 'Username is required';
  if (username.length < 3) return 'Username must be at least 3 characters';
  if (username.length > 50) return 'Username must be less than 50 characters';
  if (!/^[a-zA-Z0-9_]+$/.test(username)) return 'Username can only contain letters, numbers, and underscores';
  return null;
}

// Password validation
function validatePassword(password) {
  if (!password) return 'Password is required';
  if (password.length < 8) return 'Password must be at least 8 characters';
  if (password.length > 128) return 'Password must be less than 128 characters';
  if (!/[a-zA-Z]/.test(password)) return 'Password must contain at least one letter';
  if (!/[0-9]/.test(password)) return 'Password must contain at least one number';
  return null;
}

// Name validation (optional field)
function validateName(name, fieldName) {
  if (!name) return null; // Optional field
  if (name.length > 100) return `${fieldName} must be less than 100 characters`;
  if (!/^[a-zA-Z\s'-]+$/.test(name)) return `${fieldName} can only contain letters, spaces, hyphens, and apostrophes`;
  return null;
}

// Display error message
function showError(fieldId, message) {
  const errorElement = document.getElementById(`${fieldId}-error`);
  const inputElement = document.getElementById(`register-${fieldId}`);
  
  if (errorElement) {
    errorElement.textContent = message || '';
    errorElement.style.display = message ? 'block' : 'none';
  }
  
  if (inputElement) {
    if (message) {
      inputElement.classList.add('error');
      inputElement.setAttribute('aria-invalid', 'true');
    } else {
      inputElement.classList.remove('error');
      inputElement.removeAttribute('aria-invalid');
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
  
  const inputs = document.querySelectorAll('.auth-form input');
  inputs.forEach(input => {
    input.classList.remove('error');
    input.removeAttribute('aria-invalid');
  });
}

// --- Form handlers for login/register pages ---

// Handle login form submission
document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const email = loginForm.querySelector('[name="email"]').value;
      const password = loginForm.querySelector('[name="password"]').value;
      
      const result = await login(email, password);
      
      if (result.success) {
        // Redirect to home page on success
        window.location.href = '/';
      } else {
        // Show error message
        alert(result.error || 'Login failed');
      }
    });
  }
  
  const registerForm = document.getElementById('register-form');
  if (registerForm) {
    // Real-time validation on blur
    const usernameInput = document.getElementById('register-username');
    const emailInput = document.getElementById('register-email');
    const passwordInput = document.getElementById('register-password');
    const fnameInput = document.getElementById('register-fname');
    const lnameInput = document.getElementById('register-lname');
    
    if (usernameInput) {
      usernameInput.addEventListener('blur', () => {
        const sanitized = sanitizeInput(usernameInput.value);
        usernameInput.value = sanitized;
        const error = validateUsername(sanitized);
        showError('username', error);
      });
    }
    
    if (emailInput) {
      emailInput.addEventListener('blur', () => {
        const sanitized = sanitizeInput(emailInput.value);
        emailInput.value = sanitized;
        const error = validateEmail(sanitized);
        showError('email', error);
      });
    }
    
    if (passwordInput) {
      passwordInput.addEventListener('blur', () => {
        const error = validatePassword(passwordInput.value);
        showError('password', error);
      });
      
      // Real-time password strength indicator
      passwordInput.addEventListener('input', () => {
        const password = passwordInput.value;
        if (password.length > 0 && password.length < 8) {
          showError('password', `${password.length}/8 characters`);
        } else {
          showError('password', null);
        }
      });
    }
    
    if (fnameInput) {
      fnameInput.addEventListener('blur', () => {
        const sanitized = sanitizeInput(fnameInput.value, true);
        fnameInput.value = sanitized;
        const error = validateName(sanitized, 'First name');
        showError('fname', error);
      });
    }
    
    if (lnameInput) {
      lnameInput.addEventListener('blur', () => {
        const sanitized = sanitizeInput(lnameInput.value, true);
        lnameInput.value = sanitized;
        const error = validateName(sanitized, 'Last name');
        showError('lname', error);
      });
    }
    
    // Form submission with validation
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      clearErrors();
      
      // Get and sanitize form values
      const username = sanitizeInput(registerForm.querySelector('[name="username"]').value);
      const email = sanitizeInput(registerForm.querySelector('[name="email"]').value);
      const fname = sanitizeInput(registerForm.querySelector('[name="fname"]')?.value || '', true);
      const lname = sanitizeInput(registerForm.querySelector('[name="lname"]')?.value || '', true);
      const password = registerForm.querySelector('[name="password_hash"]').value; // Don't sanitize password
      
      // Validate all fields
      let hasErrors = false;
      
      const usernameError = validateUsername(username);
      if (usernameError) {
        showError('username', usernameError);
        hasErrors = true;
      }
      
      const emailError = validateEmail(email);
      if (emailError) {
        showError('email', emailError);
        hasErrors = true;
      }
      
      const passwordError = validatePassword(password);
      if (passwordError) {
        showError('password', passwordError);
        hasErrors = true;
      }
      
      const fnameError = validateName(fname, 'First name');
      if (fnameError) {
        showError('fname', fnameError);
        hasErrors = true;
      }
      
      const lnameError = validateName(lname, 'Last name');
      if (lnameError) {
        showError('lname', lnameError);
        hasErrors = true;
      }
      
      // Stop if validation failed
      if (hasErrors) {
        const feedback = document.getElementById('register-feedback');
        if (feedback) {
          feedback.textContent = 'Please fix the errors above';
          feedback.style.color = '#ff5454';
        }
        return;
      }
      
      // Submit to backend
      const formData = {
        username,
        email,
        fname,
        lname,
        password_hash: password
      };
      
      const result = await register(formData);
      
      if (result.success) {
        // Redirect to home page on success
        window.location.href = '/';
      } else {
        // Show error message
        const feedback = document.getElementById('register-feedback');
        if (feedback) {
          feedback.textContent = result.error || 'Registration failed';
          feedback.style.color = '#ff5454';
        } else {
          alert(result.error || 'Registration failed');
        }
      }
    });
  }
});
