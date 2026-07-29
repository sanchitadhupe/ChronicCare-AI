/* ============================================================
   HealthGuard AI — Main JavaScript
   ============================================================ */

// ── Theme Management ─────────────────────────────────────────
const ThemeManager = {
  KEY: 'healthguard_theme',

  init() {
    const saved = localStorage.getItem(this.KEY) || 'light';
    this.apply(saved);
    const btn = document.getElementById('themeToggle');
    if (btn) btn.addEventListener('click', () => this.toggle());
  },

  apply(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(this.KEY, theme);
    const icon = document.getElementById('themeIcon');
    if (icon) {
      icon.className = theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon-stars';
    }
  },

  toggle() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    this.apply(current === 'dark' ? 'light' : 'dark');
  }
};

// ── Sidebar Management ────────────────────────────────────────
const SidebarManager = {
  sidebar: null,
  backdrop: null,

  init() {
    this.sidebar = document.getElementById('sidebar');
    if (!this.sidebar) return;

    // Create backdrop for mobile
    this.backdrop = document.createElement('div');
    this.backdrop.className = 'sidebar-backdrop';
    document.body.appendChild(this.backdrop);
    this.backdrop.addEventListener('click', () => this.closeMobile());

    // Desktop toggle (collapse/expand)
    const toggleBtn = document.getElementById('sidebarToggle');
    if (toggleBtn) toggleBtn.addEventListener('click', () => this.toggleDesktop());

    // Mobile toggle
    const mobileBtn = document.getElementById('mobileSidebarToggle');
    if (mobileBtn) mobileBtn.addEventListener('click', () => this.toggleMobile());

    // Restore state
    const collapsed = localStorage.getItem('sidebar_collapsed') === 'true';
    if (collapsed && window.innerWidth > 992) {
      this.sidebar.classList.add('collapsed');
    }
  },

  toggleDesktop() {
    this.sidebar.classList.toggle('collapsed');
    localStorage.setItem('sidebar_collapsed', this.sidebar.classList.contains('collapsed'));
  },

  toggleMobile() {
    this.sidebar.classList.toggle('mobile-open');
    this.backdrop.classList.toggle('active');
  },

  closeMobile() {
    this.sidebar.classList.remove('mobile-open');
    this.backdrop.classList.remove('active');
  }
};

// ── Flash Message Auto-dismiss ────────────────────────────────
const FlashManager = {
  init() {
    const alerts = document.querySelectorAll('.alert.alert-dismissible');
    alerts.forEach(alert => {
      setTimeout(() => {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
        if (bsAlert) bsAlert.close();
      }, 5000);
    });
  }
};

// ── Vital Sign Real-time Validation ──────────────────────────
const VitalValidator = {
  ranges: {
    blood_pressure_systolic: { min: 60, max: 300, normal: [90, 130], label: 'Systolic BP' },
    blood_pressure_diastolic: { min: 40, max: 200, normal: [60, 85], label: 'Diastolic BP' },
    heart_rate: { min: 30, max: 300, normal: [60, 100], label: 'Heart Rate' },
    blood_sugar: { min: 20, max: 800, normal: [70, 140], label: 'Blood Sugar' },
    oxygen_saturation: { min: 50, max: 100, normal: [95, 100], label: 'SpO2' },
    temperature: { min: 34, max: 45, normal: [36.1, 37.5], label: 'Temperature' },
  },

  init() {
    Object.keys(this.ranges).forEach(fieldName => {
      const input = document.querySelector(`[name="${fieldName}"]`);
      if (input) input.addEventListener('input', () => this.validate(input, fieldName));
    });
  },

  validate(input, fieldName) {
    const range = this.ranges[fieldName];
    const val = parseFloat(input.value);
    if (isNaN(val)) { this.clearFeedback(input); return; }

    let cls = 'is-valid';
    let msg = `${range.label}: ${val} — Normal range: ${range.normal[0]}–${range.normal[1]}`;

    if (val < range.min || val > range.max) {
      cls = 'is-invalid';
      msg = `${range.label}: Value out of expected range (${range.min}–${range.max})`;
    } else if (val < range.normal[0] || val > range.normal[1]) {
      cls = 'is-warning';
      msg = `${range.label}: ${val} — Outside normal range (${range.normal[0]}–${range.normal[1]})`;
    }

    input.className = input.className.replace(/is-(valid|invalid|warning)/g, '').trim();
    input.classList.add(cls);

    let feedback = input.parentElement.querySelector('.field-feedback');
    if (!feedback) {
      feedback = document.createElement('div');
      feedback.className = 'field-feedback';
      input.parentElement.appendChild(feedback);
    }
    feedback.textContent = msg;
    feedback.style.fontSize = '11px';
    feedback.style.marginTop = '3px';
    feedback.style.color = cls === 'is-valid' ? '#059669' : cls === 'is-invalid' ? '#dc2626' : '#d97706';
  },

  clearFeedback(input) {
    const fb = input.parentElement.querySelector('.field-feedback');
    if (fb) fb.remove();
    input.className = input.className.replace(/is-(valid|invalid|warning)/g, '').trim();
  }
};

// ── Jinja filter polyfill for JS template use ────────────────
// from_json filter is added to Jinja via app context
// JS equivalent:
function safeJsonParse(str, fallback = []) {
  try { return JSON.parse(str); } catch { return fallback; }
}

// ── Number formatting ─────────────────────────────────────────
function formatNumber(n) {
  if (n === null || n === undefined) return '—';
  return Number(n).toLocaleString('en-IN');
}

// ── Chart color helper ────────────────────────────────────────
function chartColor(color, alpha = 1) {
  const colors = {
    red: `rgba(239,68,68,${alpha})`,
    blue: `rgba(59,130,246,${alpha})`,
    green: `rgba(16,185,129,${alpha})`,
    purple: `rgba(139,92,246,${alpha})`,
    orange: `rgba(249,115,22,${alpha})`,
  };
  return colors[color] || color;
}

// ── Emergency check on vital input ────────────────────────────
const EmergencyChecker = {
  timeout: null,

  init() {
    const vitals = ['blood_pressure_systolic', 'blood_pressure_diastolic', 'blood_sugar', 'heart_rate', 'oxygen_saturation'];
    vitals.forEach(name => {
      const el = document.querySelector(`[name="${name}"]`);
      if (el) el.addEventListener('input', () => this.scheduleCheck());
    });
  },

  scheduleCheck() {
    clearTimeout(this.timeout);
    this.timeout = setTimeout(() => this.check(), 1500);
  },

  async check() {
    const getValue = name => parseFloat(document.querySelector(`[name="${name}"]`)?.value) || 0;
    const vitals = {
      systolic: getValue('blood_pressure_systolic'),
      diastolic: getValue('blood_pressure_diastolic'),
      blood_sugar: getValue('blood_sugar'),
      heart_rate: getValue('heart_rate'),
      oxygen_saturation: getValue('oxygen_saturation') || 100,
    };

    if (!vitals.systolic && !vitals.blood_sugar && !vitals.heart_rate) return;

    try {
      const res = await fetch('/api/emergency-check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
        body: JSON.stringify(vitals)
      });
      const data = await res.json();
      this.showAlerts(data);
    } catch (e) { /* Silent fail */ }
  },

  showAlerts(data) {
    const existing = document.getElementById('liveEmergencyAlert');
    if (existing) existing.remove();
    if (!data.alerts || !data.alerts.length) return;

    const div = document.createElement('div');
    div.id = 'liveEmergencyAlert';
    div.className = `alert alert-${data.risk_level === 'critical' ? 'danger' : 'warning'} mt-3 animated-alert`;
    div.innerHTML = `<strong>⚠️ Health Alert:</strong><ul class="mb-0 mt-1">${data.alerts.map(a => `<li>${a}</li>`).join('')}</ul>`;

    const form = document.querySelector('form');
    if (form) form.insertAdjacentElement('beforebegin', div);
    if (data.risk_level === 'critical') {
      div.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }
};

// ── CSRF Token Helper ─────────────────────────────────────────
function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  if (meta) return meta.content;
  const input = document.querySelector('input[name="csrf_token"]');
  return input ? input.value : '';
}

// ── Active nav link ───────────────────────────────────────────
function setActiveNav() {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(link => {
    link.classList.remove('active');
    const href = link.getAttribute('href');
    if (href && path === href) link.classList.add('active');
  });
}

// ── Page load progress bar ────────────────────────────────────
function showLoader() {
  const bar = document.createElement('div');
  bar.id = 'pageLoader';
  bar.style.cssText = 'position:fixed;top:0;left:0;height:3px;width:0;background:var(--accent);z-index:9999;transition:width 0.3s ease';
  document.body.appendChild(bar);
  setTimeout(() => bar.style.width = '70%', 50);
  setTimeout(() => { bar.style.width = '100%'; setTimeout(() => bar.remove(), 300); }, 400);
}

// Attach to nav clicks
document.addEventListener('click', e => {
  const link = e.target.closest('a[href]');
  if (link && !link.getAttribute('href').startsWith('#') && link.hostname === window.location.hostname) {
    showLoader();
  }
});

// ── Initialize Everything ─────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  ThemeManager.init();
  SidebarManager.init();
  FlashManager.init();
  VitalValidator.init();
  EmergencyChecker.init();
  setActiveNav();

  // Tooltip init
  document.querySelectorAll('[title]').forEach(el => {
    new bootstrap.Tooltip(el, { trigger: 'hover', placement: 'top' });
  });

  // Add Jinja from_json filter equivalent to template rendering
  // (handled server-side, this is just for reference)

  console.log('%cHealthGuard AI%c — IBM Granite Powered', 'color:#2563eb;font-weight:bold;font-size:14px', 'color:#6b7280');
});
