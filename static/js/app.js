/* ===========================================
   PREMIUM AI DASHBOARD - Interactive Logic
   =========================================== */

document.addEventListener('DOMContentLoaded', () => {

  // =============================================
  // 1. MOUSE SPOTLIGHT EFFECT
  // =============================================
  const spotlight = document.querySelector('.spotlight');
  if (spotlight) {
    document.addEventListener('mousemove', (e) => {
      spotlight.style.left = e.clientX + 'px';
      spotlight.style.top = e.clientY + 'px';
    });
  }

  // =============================================
  // 2. SPARKLE GENERATOR
  // =============================================
  const sparklesContainer = document.querySelector('.sparkles-container');
  if (sparklesContainer) {
    function createSparkle() {
      const sparkle = document.createElement('div');
      sparkle.classList.add('sparkle');
      const size = Math.random() * 3 + 2;
      sparkle.style.width = size + 'px';
      sparkle.style.height = size + 'px';
      sparkle.style.left = Math.random() * 100 + '%';
      sparkle.style.animationDuration = (Math.random() * 3 + 2) + 's';
      sparkle.style.opacity = Math.random() * 0.6 + 0.2;
      sparklesContainer.appendChild(sparkle);
      setTimeout(() => sparkle.remove(), 5000);
    }
    setInterval(createSparkle, 300);
    for (let i = 0; i < 15; i++) {
      setTimeout(createSparkle, i * 100);
    }
  }

  // =============================================
  // 3. PARTICLE SYSTEM (Canvas)
  // =============================================
  const canvas = document.getElementById('particles-canvas');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    let particles = [];
    let animId;

    function resizeCanvas() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    }
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    class Particle {
      constructor() {
        this.reset();
      }
      reset() {
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.size = Math.random() * 2.5 + 0.5;
        this.speedX = (Math.random() - 0.5) * 0.3;
        this.speedY = (Math.random() - 0.5) * 0.3;
        this.opacity = Math.random() * 0.5 + 0.1;
      }
      update() {
        this.x += this.speedX;
        this.y += this.speedY;
        if (this.x < 0 || this.x > canvas.width || this.y < 0 || this.y > canvas.height) {
          this.reset();
        }
      }
      draw() {
        ctx.fillStyle = `rgba(99, 102, 241, ${this.opacity})`;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    function initParticles(count) {
      particles = [];
      for (let i = 0; i < count; i++) {
        particles.push(new Particle());
      }
    }

    function drawConnections() {
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 120) {
            ctx.strokeStyle = `rgba(99, 102, 241, ${0.06 * (1 - dist / 120)})`;
            ctx.lineWidth = 0.5;
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.stroke();
          }
        }
      }
    }

    function animateParticles() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles.forEach(p => {
        p.update();
        p.draw();
      });
      drawConnections();
      animId = requestAnimationFrame(animateParticles);
    }

    const particleCount = Math.min(Math.floor(window.innerWidth / 8), 80);
    initParticles(particleCount);
    animateParticles();
  }

  // =============================================
  // 4. DARK MODE TOGGLE
  // =============================================
  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    const html = document.documentElement;
    const icon = themeToggle.querySelector('i');

    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      html.setAttribute('data-theme', savedTheme);
      icon.textContent = savedTheme === 'dark' ? '\u2600\uFE0F' : '\uD83C\uDF19';
    }

    themeToggle.addEventListener('click', () => {
      const current = html.getAttribute('data-theme');
      const newTheme = current === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);
      icon.textContent = newTheme === 'dark' ? '\u2600\uFE0F' : '\uD83C\uDF19';
    });
  }

  // =============================================
  // 5. PROFILE DROPDOWN
  // =============================================
  const avatar = document.getElementById('userAvatar');
  const dropdown = document.getElementById('profileDropdown');
  if (avatar && dropdown) {
    avatar.addEventListener('click', (e) => {
      e.stopPropagation();
      dropdown.classList.toggle('active');
    });

    document.addEventListener('click', () => {
      dropdown.classList.remove('active');
    });
  }

  // =============================================
  // 6. MOBILE NAV TOGGLE
  // =============================================
  const navToggle = document.getElementById('navToggle');
  const navLinks = document.getElementById('navLinks');
  if (navToggle && navLinks) {
    navToggle.addEventListener('click', () => {
      navToggle.classList.toggle('active');
      navLinks.classList.toggle('active');
    });

    navLinks.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        navToggle.classList.remove('active');
        navLinks.classList.remove('active');
      });
    });
  }

  // =============================================
  // 7. FEATURE SLIDERS & NUMBER INPUTS
  // =============================================
  const featureSliders = document.querySelectorAll('.feature-slider');
  featureSliders.forEach(slider => {
    const featureItem = slider.closest('.feature-item');
    const input = featureItem ? featureItem.querySelector('.feature-input') : null;
    const min = parseFloat(slider.dataset.min) || 0;
    const max = parseFloat(slider.dataset.max) || 100;
    const step = parseFloat(slider.dataset.step) || 1;

    if (input) {
      slider.addEventListener('input', () => {
        const val = parseFloat(slider.value);
        input.value = step < 1 ? val.toFixed(2) : Math.round(val);
        updateSummaryIfNeeded();
      });

      input.addEventListener('input', () => {
        let val = parseFloat(input.value) || min;
        val = Math.min(max, Math.max(min, val));
        slider.value = val;
        updateSummaryIfNeeded();
      });

      input.addEventListener('blur', () => {
        let val = parseFloat(input.value) || min;
        val = Math.min(max, Math.max(min, val));
        input.value = step < 1 ? val.toFixed(2) : Math.round(val);
        slider.value = val;
      });

      const initial = parseFloat(slider.value) || min;
      input.value = step < 1 ? initial.toFixed(2) : Math.round(initial);
    }
  });

  // =============================================
  // 8. SAMPLE DATA / RESET BUTTONS
  // =============================================
  const sampleValues = {
    key_press_count: 120, key_hold_time: 0.20, typing_speed: 45,
    error_rate: 0.08, backspace_count: 15, idle_time: 8,
    mouse_click_count: 25, left_click: 20, right_click: 3,
    double_click: 1, scroll_count: 50, cursor_speed: 100,
    cursor_distance: 50000, drag_count: 10, movement_speed: 100,
    idle_mouse_time: 500
  };

  const defaultValues = {
    key_press_count: 60, key_hold_time: 0.15, typing_speed: 30,
    error_rate: 0.05, backspace_count: 8, idle_time: 5,
    mouse_click_count: 15, left_click: 12, right_click: 2,
    double_click: 0, scroll_count: 25, cursor_speed: 60,
    cursor_distance: 20000, drag_count: 5, movement_speed: 60,
    idle_mouse_time: 300
  };

  function setFeatureValues(values) {
    for (const [key, val] of Object.entries(values)) {
      const slider = document.querySelector(`.feature-slider[data-feature="${key}"]`);
      const input = document.querySelector(`.feature-input[data-feature="${key}"]`);
      if (slider && input) {
        const step = parseFloat(slider.dataset.step) || 1;
        slider.value = val;
        input.value = step < 1 ? parseFloat(val).toFixed(2) : Math.round(val);
      }
    }
    updateSummaryIfNeeded();
  }

  document.getElementById('fillSampleData').addEventListener('click', () => {
    setFeatureValues(sampleValues);
    hideResult();
  });

  document.getElementById('resetData').addEventListener('click', () => {
    setFeatureValues(defaultValues);
    hideResult();
  });

  function hideResult() {
    const result = document.getElementById('predictionResult');
    if (result) {
      result.classList.remove('visible');
      result.style.display = 'none';
    }
  }

  function showError(msg) {
    const result = document.getElementById('predictionResult');
    if (result) {
      result.innerHTML = `
        <div class="prediction-header">
          <div class="prediction-icon high">\u26A0\uFE0F</div>
          <div>
            <div class="prediction-title">Error</div>
            <div class="prediction-status">${msg}</div>
          </div>
        </div>`;
      result.style.display = 'block';
      result.classList.add('visible');
    }
  }

  // =============================================
  // 9. PREDICT BUTTON + RIPPLE + API CALL
  // =============================================
  const predictBtn = document.getElementById('predictBtn');
  if (predictBtn) {
    predictBtn.addEventListener('click', function(e) {
      const rect = this.getBoundingClientRect();
      const ripple = document.createElement('span');
      ripple.classList.add('ripple');
      const size = Math.max(rect.width, rect.height);
      ripple.style.width = ripple.style.height = size + 'px';
      ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
      ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';
      this.appendChild(ripple);
      setTimeout(() => ripple.remove(), 600);
    });

    predictBtn.addEventListener('click', async function() {
      const btn = this;
      const originalContent = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span> Analyzing...';

      const resultDiv = document.getElementById('predictionResult');
      if (resultDiv) {
        resultDiv.style.display = 'none';
        resultDiv.classList.remove('visible');
      }

      const features = {};
      let allFilled = true;
      document.querySelectorAll('.feature-input').forEach(input => {
        const key = input.dataset.feature;
        if (key) {
          const val = parseFloat(input.value);
          if (isNaN(val)) {
            allFilled = false;
            return;
          }
          features[key] = val;
        }
      });

      if (!allFilled || Object.keys(features).length === 0) {
        btn.innerHTML = originalContent;
        btn.disabled = false;
        showError('Please fill in all feature values.');
        return;
      }

      try {
        const params = new URLSearchParams(features);
        const response = await fetch('/predict?' + params.toString());
        const data = await response.json();

        btn.innerHTML = originalContent;
        btn.disabled = false;

        if (data.error) {
          showError('Error: ' + data.error);
          return;
        }

        displayPrediction(data, resultDiv);

      } catch (error) {
        btn.innerHTML = originalContent;
        btn.disabled = false;
        showError('Network error: ' + error.message);
      }
    });
  }

  // =============================================
  // 10. DISPLAY PREDICTION RESULT
  // =============================================
  function displayPrediction(data, resultDiv) {
    if (!resultDiv) return;

    const prediction = data.prediction || 'Unknown';
    const confidence = data.confidence || 0;
    const probability = (confidence * 100);
    const recommendation = data.recommendation || getDefaultRecommendation(prediction);

    let statusIcon, statusClass, statusText;

    if (prediction.toLowerCase().includes('low') || prediction.toLowerCase().includes('normal')) {
      statusIcon = '\uD83D\uDE0A';
      statusClass = 'low';
      statusText = prediction;
    } else if (prediction.toLowerCase().includes('moderate')) {
      statusIcon = '\u26A0\uFE0F';
      statusClass = 'moderate';
      statusText = prediction;
    } else {
      statusIcon = '\uD83D\uDD34';
      statusClass = 'high';
      statusText = prediction;
    }

    resultDiv.innerHTML = `
      <div class="glass-card">
        <div class="prediction-header">
          <div class="prediction-icon ${statusClass}">${statusIcon}</div>
          <div>
            <div class="prediction-title">${statusText}</div>
            <div class="prediction-status">${recommendation}</div>
          </div>
        </div>
        <div class="prediction-details">
          <div class="confidence-section">
            <div class="confidence-label">
              <span>Confidence Score</span>
              <span><strong>${probability.toFixed(1)}%</strong></span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" style="width: ${probability}%"></div>
            </div>
            <div style="margin-top: 16px;">
              <div class="confidence-label">
                <span>Low Fatigue</span>
                <span>${((1 - confidence) * 70).toFixed(1)}%</span>
              </div>
              <div class="progress-bar">
                <div class="progress-fill" style="width: ${((1 - confidence) * 70).toFixed(1)}%; background: linear-gradient(90deg, #22C55E, #4ADE80);"></div>
              </div>
            </div>
          </div>
          <div class="recommendation-section">
            <h4>\uD83D\uDCA1 Recommendation</h4>
            <p>${recommendation}</p>
          </div>
        </div>
      </div>
    `;

    resultDiv.style.display = 'block';
    // Trigger animation after layout
    requestAnimationFrame(() => {
      resultDiv.classList.add('visible');
    });

    // Update summary cards (use data.features when available)
    updateSummaryCards(data.features || {}, prediction);
  }

  function getDefaultRecommendation(prediction) {
    if (prediction.toLowerCase().includes('low') || prediction.toLowerCase().includes('normal')) {
      return 'Everything looks normal. Keep maintaining healthy work habits.';
    } else if (prediction.toLowerCase().includes('moderate')) {
      return 'Signs of fatigue detected. Consider taking a short break and stretching.';
    }
    return 'High fatigue levels detected. We strongly recommend resting and consulting a healthcare professional.';
  }

  // =============================================
  // 11. UPDATE SUMMARY CARDS
  // =============================================
  function updateSummaryIfNeeded() {
    // This is called when sliders change but doesn't auto-update summary
    // Only updates on prediction
  }

  function updateSummaryCards(features, prediction) {
    const typingSpeed = features.typing_speed || 0;
    const mouseClicks = features.mouse_click_count || 0;

    let activityLevel = 'Normal';
    let fatigueLevel = 'Low';

    if (prediction.toLowerCase().includes('moderate')) {
      fatigueLevel = 'Moderate';
      activityLevel = 'Moderate';
    } else if (prediction.toLowerCase().includes('high')) {
      fatigueLevel = 'High';
      activityLevel = 'High';
    }

    animateValue('summaryTyping', typingSpeed);
    animateValue('summaryClicks', mouseClicks);
    document.getElementById('summaryActivity').textContent = activityLevel;
    document.getElementById('summaryFatigue').textContent = fatigueLevel;
  }

  function animateValue(elementId, target) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const current = parseInt(el.textContent) || 0;
    const startTime = performance.now();
    const duration = 1000;

    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const value = Math.round(current + (target - current) * eased);
      el.textContent = value;
      if (progress < 1) {
        requestAnimationFrame(update);
      }
    }
    requestAnimationFrame(update);
  }

  // =============================================
  // 12. BACK TO TOP
  // =============================================
  const backToTop = document.getElementById('backToTop');
  if (backToTop) {
    backToTop.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    window.addEventListener('scroll', () => {
      if (window.scrollY > 400) {
        backToTop.style.opacity = '1';
        backToTop.style.pointerEvents = 'auto';
      } else {
        backToTop.style.opacity = '0.5';
        backToTop.style.pointerEvents = 'auto';
      }
    });
  }

  // =============================================
  // 13. SCROLL REVEAL ANIMATIONS
  // =============================================
  const revealElements = document.querySelectorAll('.fade-in-up');
  if (revealElements.length > 0) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
        }
      });
    }, { threshold: 0.1 });

    revealElements.forEach(el => observer.observe(el));
  }

  // =============================================
  // 14. INITIAL SUMMARY VALUES
  // =============================================
  document.getElementById('summaryTyping').textContent = '30';
  document.getElementById('summaryClicks').textContent = '15';
  document.getElementById('summaryActivity').textContent = 'Normal';
  document.getElementById('summaryFatigue').textContent = 'Low';

  // =============================================
  // 15. REAL-TIME MONITORING SYSTEM
  // =============================================
  let monitoringPollingId = null;
  let monitoringActive = false;
  let sessionStartTime = null;

  const monitorStartBtn = document.getElementById('monitorStartBtn');
  const monitorStopBtn = document.getElementById('monitorStopBtn');
  const statusDot = document.getElementById('statusDot');
  const statusText = document.getElementById('statusText');
  const sessionTimer = document.getElementById('sessionTimer');
  const keyCount = document.getElementById('keyCount');
  const mouseCount = document.getElementById('mouseCount');
  const kbBadge = document.getElementById('kbBadge');
  const mouseBadge = document.getElementById('mouseBadge');

  // Initialize charts
  let trendChart = null;
  let confidenceGauge = null;
  try {
    if (window.FatigueChart && document.getElementById('trendChart')) {
      trendChart = new window.FatigueChart('trendChart', {
        lineColor: '#6366F1',
        fillColor: 'rgba(99, 102, 241, 0.1)',
        textColor: '#6B7280'
      });
    }
    if (window.GaugeChart && document.getElementById('confidenceGauge')) {
      confidenceGauge = new window.GaugeChart('confidenceGauge', {
        arcColor: '#6366F1',
        trackColor: 'rgba(99, 102, 241, 0.1)',
        textColor: '#111827',
        subTextColor: '#6B7280'
      });
    }
  } catch (e) {
    console.warn('Chart initialization error:', e);
  }

  async function startMonitoring() {
    try {
      const resp = await fetch('/api/monitor/start', { method: 'POST' });
      const data = await resp.json();
      if (data.status === 'started' || data.status === 'already_running') {
        monitoringActive = true;
        sessionStartTime = data.session_start || Date.now() / 1000;
        if (monitorStartBtn) monitorStartBtn.style.display = 'none';
        if (monitorStopBtn) monitorStopBtn.style.display = 'inline-flex';
        if (statusDot) { statusDot.className = 'status-dot active'; }
        if (statusText) statusText.textContent = 'Monitoring Active';
        if (kbBadge) kbBadge.style.display = 'inline';
        if (mouseBadge) mouseBadge.style.display = 'inline';
        // Start polling
        if (monitoringPollingId) clearInterval(monitoringPollingId);
        monitoringPollingId = setInterval(pollStatus, 3000);
        pollStatus(); // immediate first poll
      }
    } catch (e) {
      console.error('Start monitoring failed:', e);
      if (statusText) statusText.textContent = 'Connection Error';
    }
  }

  async function stopMonitoring() {
    try {
      const resp = await fetch('/api/monitor/stop', { method: 'POST' });
      const data = await resp.json();
      monitoringActive = false;
      if (monitoringPollingId) { clearInterval(monitoringPollingId); monitoringPollingId = null; }
      if (monitorStartBtn) monitorStartBtn.style.display = 'inline-flex';
      if (monitorStopBtn) monitorStopBtn.style.display = 'none';
      if (statusDot) statusDot.className = 'status-dot inactive';
      if (statusText) statusText.textContent = 'Ready';
      if (kbBadge) kbBadge.style.display = 'none';
      if (mouseBadge) mouseBadge.style.display = 'none';
      if (sessionTimer) sessionTimer.textContent = '00:00';

      // Update report
      updateReport(data);
    } catch (e) {
      console.error('Stop monitoring failed:', e);
    }
  }

  async function pollStatus() {
    if (!monitoringActive) return;
    try {
      const resp = await fetch('/api/monitor/status');
      const data = await resp.json();
      if (!data.is_monitoring) {
        // Monitoring stopped externally
        monitoringActive = false;
        if (monitoringPollingId) { clearInterval(monitoringPollingId); monitoringPollingId = null; }
        if (monitorStartBtn) monitorStartBtn.style.display = 'inline-flex';
        if (monitorStopBtn) monitorStopBtn.style.display = 'none';
        if (statusDot) statusDot.className = 'status-dot inactive';
        if (statusText) statusText.textContent = 'Stopped';
        if (kbBadge) kbBadge.style.display = 'none';
        if (mouseBadge) mouseBadge.style.display = 'none';
        return;
      }

      // Update timer
      if (sessionTimer && data.session_duration) {
        const mins = Math.floor(data.session_duration / 60);
        const secs = Math.floor(data.session_duration % 60);
        sessionTimer.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
      }
      if (keyCount) keyCount.textContent = data.key_events || 0;
      if (mouseCount) mouseCount.textContent = data.mouse_events || 0;

      // Show "Collecting baseline..." message while insufficient behavioral data
      if (statusText && data.is_baseline && data.is_monitoring) {
        statusText.textContent = 'Collecting behavioral baseline...';
      } else if (statusText && data.is_monitoring && !data.is_baseline) {
        statusText.textContent = 'Monitoring Active';
      }

      // Update prediction display if available
      if (data.current_prediction && data.features && Object.keys(data.features).length > 0) {
        const resultDiv = document.getElementById('predictionResult');
        if (resultDiv) {
          displayPrediction({
            prediction: data.current_prediction,
            confidence: data.current_confidence || 0,
            features: data.features,
            recommendation: getDefaultRecommendation(data.current_prediction)
          }, resultDiv);
        }
        // Update charts
        if (trendChart && data.current_confidence !== undefined) {
          const label = new Date().toLocaleTimeString();
          const levelVal = data.current_prediction.toLowerCase().includes('normal') ? 0 :
                          data.current_prediction.toLowerCase().includes('moderate') ? 1 : 2;
          trendChart.addPoint(levelVal, label);
        }
        if (confidenceGauge && data.current_confidence !== undefined) {
          confidenceGauge.setValue(data.current_confidence * 100, 100, 'Confidence');
        }
      }
    } catch (e) {
      console.error('Status poll error:', e);
    }
  }

  function updateReport(data) {
    if (!data || !data.has_data) {
      const durEl = document.getElementById('reportDuration');
      if (durEl) durEl.textContent = data && data.session_duration ? Math.round(data.session_duration) + 's' : '0s';
      return;
    }
    if (document.getElementById('reportDuration')) document.getElementById('reportDuration').textContent = Math.round(data.session_duration || 0) + 's';
    if (document.getElementById('reportPredictions')) document.getElementById('reportPredictions').textContent = data.total_predictions || 0;
    if (document.getElementById('reportDominant')) document.getElementById('reportDominant').textContent = data.dominant_prediction || '-';
    if (document.getElementById('reportKeys') && data.activity_summary) document.getElementById('reportKeys').textContent = data.activity_summary.total_key_presses || 0;
    if (document.getElementById('reportClicks') && data.activity_summary) document.getElementById('reportClicks').textContent = data.activity_summary.total_mouse_clicks || 0;
    if (document.getElementById('reportTyping') && data.activity_summary) document.getElementById('reportTyping').textContent = (data.activity_summary.typing_speed || 0) + ' WPM';
    if (document.getElementById('reportRecommendation')) document.getElementById('reportRecommendation').textContent = data.recommendation || 'No recommendation available.';
  }

  // Wire up monitoring buttons
  if (monitorStartBtn) monitorStartBtn.addEventListener('click', startMonitoring);
  if (monitorStopBtn) monitorStopBtn.addEventListener('click', stopMonitoring);

  // Export buttons
  document.getElementById('exportJsonBtn')?.addEventListener('click', async () => {
    try {
      const resp = await fetch('/api/monitor/report');
      const data = await resp.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = 'fatigue_report.json'; a.click();
      URL.revokeObjectURL(url);
    } catch (e) { console.error('Export JSON error:', e); }
  });

  document.getElementById('exportCsvBtn')?.addEventListener('click', async () => {
    try {
      const resp = await fetch('/api/monitor/history');
      const data = await resp.json();
      if (!data.history || data.history.length === 0) return;
      const headers = Object.keys(data.history[0]);
      const rows = data.history.map(r => headers.map(h => JSON.stringify(r[h] || '')).join(','));
      const csv = [headers.join(','), ...rows].join('\n');
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = 'fatigue_history.csv'; a.click();
      URL.revokeObjectURL(url);
    } catch (e) { console.error('Export CSV error:', e); }
  });

});

