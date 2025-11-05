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
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const formData = {
        username: registerForm.querySelector('[name="username"]').value,
        email: registerForm.querySelector('[name="email"]').value,
        fname: registerForm.querySelector('[name="fname"]')?.value || '',
        lname: registerForm.querySelector('[name="lname"]')?.value || '',
        password_hash: registerForm.querySelector('[name="password_hash"]').value
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
          feedback.style.color = 'red';
        } else {
          alert(result.error || 'Registration failed');
        }
      }
    });
  }
});
