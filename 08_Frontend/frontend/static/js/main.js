/**
 * GestureConnect - Global Utility, Theme, Sidebar & Accessibility Controller
 */

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const CSRF_TOKEN = getCookie('csrftoken') || '';

function showNotification(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toastEl = document.createElement('div');
  const bgClass = type === 'error' ? 'bg-danger text-white' : (type === 'success' ? 'bg-success text-white' : 'bg-primary text-white');
  
  toastEl.className = `toast align-items-center ${bgClass} border-0 show mb-2 shadow-lg`;
  toastEl.setAttribute('role', 'alert');
  toastEl.setAttribute('aria-live', 'assertive');
  toastEl.setAttribute('aria-atomic', 'true');

  toastEl.innerHTML = `
    <div class="d-flex align-items-center">
      <div class="toast-body fw-medium py-2 px-3">${message}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
  `;

  container.appendChild(toastEl);
  setTimeout(() => {
    toastEl.classList.remove('show');
    setTimeout(() => toastEl.remove(), 400);
  }, 4000);
}

// Initialize Theme, Sidebar & Accessibility on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  // Theme Management (Light / Dark)
  const themeToggleBtn = document.getElementById('gc-theme-toggle');
  const savedTheme = localStorage.getItem('gc-theme') || 'light';
  
  function applyTheme(theme) {
    if (theme === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
      document.body.setAttribute('data-theme', 'dark');
      if (themeToggleBtn) {
        themeToggleBtn.innerHTML = '<i class="bi bi-sun-fill text-warning"></i>';
        themeToggleBtn.setAttribute('title', 'Switch to Light Mode');
      }
    } else {
      document.documentElement.removeAttribute('data-theme');
      document.body.removeAttribute('data-theme');
      if (themeToggleBtn) {
        themeToggleBtn.innerHTML = '<i class="bi bi-moon-stars-fill"></i>';
        themeToggleBtn.setAttribute('title', 'Switch to Dark Mode');
      }
    }
    localStorage.setItem('gc-theme', theme);
  }

  applyTheme(savedTheme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
      applyTheme(currentTheme === 'dark' ? 'light' : 'dark');
    });
  }

  // Sidebar Collapse / Expand Controller (Desktop & Mobile)
  const sidebarToggle = document.getElementById('gc-sidebar-toggle');
  const sidebarCloseBtn = document.getElementById('gc-sidebar-close-btn');
  const sidebar = document.getElementById('gcSidebar');
  const sidebarOverlay = document.getElementById('gcSidebarOverlay');

  // Check saved desktop collapse state
  const isInitiallyCollapsed = localStorage.getItem('gc-sidebar-collapsed') === 'true';
  if (isInitiallyCollapsed && window.innerWidth > 992) {
    document.body.classList.add('sidebar-collapsed');
  }

  function toggleSidebar() {
    if (window.innerWidth > 992) {
      // Desktop: toggle collapsed state
      const isCollapsed = document.body.classList.toggle('sidebar-collapsed');
      localStorage.setItem('gc-sidebar-collapsed', isCollapsed);
      if (sidebarToggle) {
        sidebarToggle.setAttribute('title', isCollapsed ? 'Open Sidebar Menu' : 'Collapse Sidebar Menu');
      }
    } else {
      // Mobile: toggle drawer overlay
      if (sidebar) sidebar.classList.toggle('show');
      if (sidebarOverlay) sidebarOverlay.classList.toggle('show');
    }
  }

  function closeSidebar() {
    if (window.innerWidth > 992) {
      document.body.classList.add('sidebar-collapsed');
      localStorage.setItem('gc-sidebar-collapsed', 'true');
    } else {
      if (sidebar) sidebar.classList.remove('show');
      if (sidebarOverlay) sidebarOverlay.classList.remove('show');
    }
  }

  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', (e) => {
      e.preventDefault();
      toggleSidebar();
    });
  }

  if (sidebarCloseBtn) {
    sidebarCloseBtn.addEventListener('click', (e) => {
      e.preventDefault();
      closeSidebar();
    });
  }

  if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', () => {
      closeSidebar();
    });
  }


  // Accessibility Controls
  const fontSizeSelect = document.getElementById('acc-font-size');
  const contrastToggle = document.getElementById('acc-high-contrast');
  const reducedMotionToggle = document.getElementById('acc-reduced-motion');

  // Load saved accessibility preferences
  const savedFontSize = localStorage.getItem('gc-font-size') || 'normal';
  const savedContrast = localStorage.getItem('gc-contrast') === 'true';
  const savedMotion = localStorage.getItem('gc-motion') === 'true';

  function applyAccessibility() {
    // Font size
    document.body.classList.remove('font-size-large', 'font-size-xl');
    if (savedFontSize === 'large') document.body.classList.add('font-size-large');
    if (savedFontSize === 'xl') document.body.classList.add('font-size-xl');
    if (fontSizeSelect) fontSizeSelect.value = savedFontSize;

    // High Contrast
    if (savedContrast) {
      document.body.classList.add('high-contrast');
      if (contrastToggle) contrastToggle.checked = true;
    }

    // Reduced motion
    if (savedMotion) {
      document.body.classList.add('reduced-motion');
      if (reducedMotionToggle) reducedMotionToggle.checked = true;
    }
  }

  applyAccessibility();

  if (fontSizeSelect) {
    fontSizeSelect.addEventListener('change', (e) => {
      localStorage.setItem('gc-font-size', e.target.value);
      location.reload();
    });
  }

  if (contrastToggle) {
    contrastToggle.addEventListener('change', (e) => {
      localStorage.setItem('gc-contrast', e.target.checked);
      document.body.classList.toggle('high-contrast', e.target.checked);
    });
  }

  if (reducedMotionToggle) {
    reducedMotionToggle.addEventListener('change', (e) => {
      localStorage.setItem('gc-motion', e.target.checked);
      document.body.classList.toggle('reduced-motion', e.target.checked);
    });
  }
});
