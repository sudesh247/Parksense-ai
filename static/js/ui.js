/**
 * UI utility helpers: toasts, formatting, clock, and view switching.
 */

const UI = {
  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  },

  formatCurrency(amount) {
    if (amount === null || amount === undefined) return '₹0.00';
    return `₹${Number(amount).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  },

  formatDateTime(isoString) {
    if (!isoString) return '--';
    const dt = new Date(isoString);
    return dt.toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  },

  initClock() {
    const clockEl = document.getElementById('live-clock');
    const update = () => {
      const now = new Date();
      if (clockEl) clockEl.textContent = now.toLocaleTimeString('en-IN');
    };
    update();
    setInterval(update, 1000);
  },

  initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const views = document.querySelectorAll('.view-container');
    const titleEl = document.getElementById('page-title');

    const titles = {
      dashboard: 'Dashboard Overview',
      slots: 'Parking Slots Grid',
      bookings: 'Facility Bookings',
      assistant: 'AI Parking Assistant'
    };

    navItems.forEach(btn => {
      btn.addEventListener('click', () => {
        const viewName = btn.getAttribute('data-view');

        navItems.forEach(i => i.classList.remove('active'));
        btn.classList.add('active');

        views.forEach(v => {
          v.classList.remove('active');
          if (v.id === `view-${viewName}`) v.classList.add('active');
        });

        if (titleEl) titleEl.textContent = titles[viewName] || 'ParkSense AI';

        // Trigger view-specific loads
        if (viewName === 'dashboard') DashboardModule.load();
        if (viewName === 'slots') SlotsModule.load();
        if (viewName === 'bookings') BookingsModule.load();
      });
    });
  },

  async checkSystemHealth() {
    const dot = document.getElementById('system-status-dot');
    const text = document.getElementById('system-status-text');
    try {
      const health = await API.getHealth();
      if (dot && text) {
        dot.classList.add('online');
        text.textContent = health.ollama_ready ? 'System Online (Ollama Active)' : 'System Online (Ollama Offline)';
      }
    } catch {
      if (dot && text) {
        dot.classList.remove('online');
        text.textContent = 'Server Offline';
      }
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  UI.initClock();
  UI.initNavigation();
  UI.checkSystemHealth();

  document.getElementById('btn-refresh-data')?.addEventListener('click', () => {
    DashboardModule.load();
    UI.showToast('Dashboard data refreshed.', 'success');
  });
});
