/**
 * EcoPulse Multi-Themed Environmental Health Telemetry
 * Supports:
 *   - Track 1: AirGuard (Theme: Windy)
 *   - Track 2: LeakLens (Theme: Fluid - Centerpiece)
 *   - Track 3: EcoSort  (Theme: Nuclear)
 */

document.addEventListener('DOMContentLoaded', () => {
  // Global State
  const state = {
    currentTrack: 'water',
    currentTheme: 'theme-fluid',
    selectedLocation: 'LOC-001',
    waterReadings: [],
    leakReports: [],
    airAssessments: [],
    wasteEntries: [],
    wasteSummary: null,
  };

  // DOM Elements
  const body = document.body;
  const brandIcon = document.getElementById('brand-icon');
  const trackSubtitle = document.getElementById('track-subtitle');
  const locationSelect = document.getElementById('location-select');
  const btnSeedData = document.getElementById('btn-seed-data');

  // Track Buttons
  const trackBtns = {
    air: document.getElementById('btn-track-air'),
    water: document.getElementById('btn-track-water'),
    waste: document.getElementById('btn-track-waste'),
  };

  // Track Views
  const trackViews = {
    air: document.getElementById('view-air'),
    water: document.getElementById('view-water'),
    waste: document.getElementById('view-waste'),
  };

  // ============================================================
  // THEME & TRACK SWITCHER
  // ============================================================
  function switchTrack(trackKey, themeClass) {
    state.currentTrack = trackKey;
    state.currentTheme = themeClass;

    // Update body theme class
    body.className = themeClass;

    // Update switcher buttons
    Object.keys(trackBtns).forEach(key => {
      trackBtns[key].classList.toggle('active', key === trackKey);
    });

    // Update views
    Object.keys(trackViews).forEach(key => {
      trackViews[key].classList.toggle('active', key === trackKey);
    });

    // Update brand branding details
    if (trackKey === 'air') {
      brandIcon.textContent = '🌬️';
      trackSubtitle.textContent = 'AirGuard • Windy Telemetry';
    } else if (trackKey === 'water') {
      brandIcon.textContent = '💧';
      trackSubtitle.textContent = 'LeakLens • Fluid Architecture (Centerpiece)';
    } else if (trackKey === 'waste') {
      brandIcon.textContent = '☢️';
      trackSubtitle.textContent = 'EcoSort • Nuclear Diversion Core';
    }

    // Refresh view specific data
    refreshTrackData(trackKey);
  }

  // Attach button listeners
  trackBtns.air.addEventListener('click', () => switchTrack('air', 'theme-windy'));
  trackBtns.water.addEventListener('click', () => switchTrack('water', 'theme-fluid'));
  trackBtns.waste.addEventListener('click', () => switchTrack('waste', 'theme-nuclear'));

  // Location Selector Change
  locationSelect.addEventListener('change', (e) => {
    state.selectedLocation = e.target.value;
    showToast(`Filtering data by location: ${state.selectedLocation || 'All Locations'}`);
    refreshAllData();
  });

  // ============================================================
  // TOAST NOTIFICATIONS
  // ============================================================
  function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '⚠️';
    if (type === 'leak') icon = '🚨';

    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(50px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3800);
  }

  // ============================================================
  // API HELPERS
  // ============================================================
  async function apiGet(endpoint) {
    try {
      const res = await fetch(endpoint);
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn(`Failed GET ${endpoint}:`, err);
      return null;
    }
  }

  async function apiPost(endpoint, body) {
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail?.[0]?.msg || `HTTP ${res.status}`);
      }
      return await res.json();
    } catch (err) {
      console.error(`Failed POST ${endpoint}:`, err);
      showToast(err.message || 'API request failed', 'error');
      return null;
    }
  }

  // ============================================================
  // TRACK 2: LEAKLENS (FLUID THEME) LOGIC
  // ============================================================
  async function loadWaterData() {
    const locParam = state.selectedLocation ? `?location_id=${state.selectedLocation}` : '';

    // 1. Fetch Summary
    const summary = await apiGet(`/api/v1/water/summary${locParam}`);
    if (summary) {
      document.getElementById('water-active-leaks-count').textContent = summary.active_leak_reports_count;
      document.getElementById('water-avg-daily-usage').textContent = summary.average_daily_usage_liters !== null
        ? `${summary.average_daily_usage_liters} L/day`
        : '-- L';

      if (summary.latest_reading) {
        const cumL = summary.latest_reading.cumulative_reading_liters;
        document.getElementById('w-curr-reading').value = cumL;
        document.getElementById('w-prev-reading').value = Math.max(0, cumL - 400);

        // Update tank gauge based on volume modulo
        const tankVolume = 5000;
        const currentL = (cumL % tankVolume) || 3400;
        const pct = Math.min(100, Math.round((currentL / tankVolume) * 100));
        updateTankGauge(pct, currentL);
      }
    }

    // 2. Fetch Readings Log
    const readings = await apiGet(`/api/v1/water/readings${locParam}`);
    if (readings) {
      state.waterReadings = readings;
      renderWaterReadingsTable(readings);
    }

    // 3. Fetch Leaks Feed
    const leaks = await apiGet(`/api/v1/water/reports${locParam}`);
    if (leaks) {
      state.leakReports = leaks;
      renderLeaksFeed(leaks);
    }
  }

  function updateTankGauge(pct, liters) {
    const tankLiquid = document.getElementById('tank-liquid');
    const tankPct = document.getElementById('tank-level-pct');
    const tankLiters = document.getElementById('tank-level-liters');
    const tankPill = document.getElementById('tank-status-pill');

    tankLiquid.style.height = `${pct}%`;
    tankPct.textContent = `${pct}%`;
    tankLiters.textContent = `${liters.toLocaleString()} L Remaining`;

    if (pct < 25) {
      tankPill.className = 'tank-status-pill critical';
      tankPill.textContent = 'Low Pressure Warning';
    } else {
      tankPill.className = 'tank-status-pill normal';
      tankPill.textContent = 'Nominal Pressure';
    }
  }

  function renderWaterReadingsTable(readings) {
    const tbody = document.getElementById('water-readings-tbody');
    if (!readings || readings.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="text-center">No water meter readings logged yet.</td></tr>';
      return;
    }

    const sorted = [...readings].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    tbody.innerHTML = sorted.slice(0, 8).map(r => `
      <tr>
        <td>${new Date(r.timestamp).toLocaleDateString()} ${new Date(r.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</td>
        <td><code>${r.reading_id}</code></td>
        <td>${r.location_id}</td>
        <td><strong>${r.cumulative_reading_liters.toLocaleString()} L</strong></td>
      </tr>
    `).join('');
  }

  function renderLeaksFeed(leaks) {
    const container = document.getElementById('leaks-list-container');
    if (!leaks || leaks.length === 0) {
      container.innerHTML = '<div class="empty-feed">✓ No active leak incidents logged. System secure.</div>';
      return;
    }

    const openLeaks = leaks.filter(l => l.status === 'open');
    if (openLeaks.length === 0) {
      container.innerHTML = '<div class="empty-feed">✓ All reported leaks resolved.</div>';
      return;
    }

    container.innerHTML = openLeaks.slice(0, 5).map(l => `
      <div class="leak-item">
        <div class="leak-item-left">
          <span class="leak-area">${l.area} &bull; ${l.location_id}</span>
          <span class="leak-desc-mini">${l.description}</span>
        </div>
        <span class="severity-badge ${l.observed_severity}">${l.observed_severity}</span>
      </div>
    `).join('');
  }

  // Water Assessment Form Handler
  const waterAssessForm = document.getElementById('form-water-assess');
  waterAssessForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const prev = parseFloat(document.getElementById('w-prev-reading').value);
    const curr = parseFloat(document.getElementById('w-curr-reading').value);
    const days = parseFloat(document.getElementById('w-days').value);
    const size = parseInt(document.getElementById('w-household').value, 10);
    const baseline = parseFloat(document.getElementById('w-baseline').value) || null;

    if (curr < prev) {
      showToast('Current reading cannot be lower than previous reading', 'error');
      return;
    }

    const payload = {
      location_id: state.selectedLocation || 'LOC-001',
      previous_reading_liters: prev,
      current_reading_liters: curr,
      days_between: days,
      household_size: size,
      baseline_daily_per_person_liters: baseline,
    };

    const res = await apiPost('/api/v1/water/assessments', payload);
    if (res) {
      showToast(`Water assessment complete: ${res.status.toUpperCase()}`, res.status === 'normal' ? 'success' : 'error');
      
      // Update UI Result
      const sevBadge = document.getElementById('w-res-severity');
      sevBadge.className = `severity-badge ${res.severity}`;
      sevBadge.textContent = res.status;

      document.getElementById('w-res-daily').textContent = `${res.daily_usage_liters} L/day`;
      document.getElementById('w-res-person').textContent = `${res.usage_per_person_liters} L/person`;
      document.getElementById('w-res-excess').textContent = `${res.estimated_excess_liters} L excess`;
      document.getElementById('w-res-explanation').textContent = res.explanation;
      document.getElementById('w-res-recommendation').textContent = `Recommendation: ${res.recommendation}`;
    }
  });

  // Leak Report Form Handler
  const leakForm = document.getElementById('form-leak-report');
  leakForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const area = document.getElementById('leak-area').value;
    const severity = document.getElementById('leak-severity').value;
    const desc = document.getElementById('leak-desc').value;

    const payload = {
      location_id: state.selectedLocation || 'LOC-001',
      area,
      observed_severity: severity,
      description: desc,
    };

    const res = await apiPost('/api/v1/water/reports', payload);
    if (res) {
      showToast(`Leak incident ${res.report_id} filed successfully!`, 'leak');
      document.getElementById('leak-desc').value = '';
      loadWaterData();
    }
  });

  // ============================================================
  // TRACK 1: AIRGUARD (WINDY THEME) LOGIC
  // ============================================================
  const aqiSlider = document.getElementById('air-input-aqi');
  const aqiSliderDisp = document.getElementById('air-slider-disp');

  function updateAqiGaugeVisuals(aqi) {
    const numericEl = document.getElementById('air-aqi-val');
    const pillEl = document.getElementById('air-category-pill');
    const riskLabel = document.getElementById('air-risk-label');
    const progressRing = document.getElementById('aqi-progress-ring');
    const healthText = document.getElementById('air-health-text');
    const precautionsList = document.getElementById('air-precautions-list');

    numericEl.textContent = aqi;
    aqiSliderDisp.textContent = aqi;

    // Circumference of r=80 is ~ 502
    const circumference = 2 * Math.PI * 80;
    const pct = Math.min(1, aqi / 500);
    progressRing.style.strokeDashoffset = circumference - (pct * circumference);

    // Classify
    let category = 'Good';
    let risk = 'low';
    let pillClass = 'good';
    let color = '#34d399';
    let health = 'Air quality is satisfactory, and air pollution poses little or no risk.';
    let precautions = [
      'Air quality is ideal for outdoor sports and activities.',
      'Safe to ventilate indoor living spaces.',
    ];

    if (aqi <= 50) {
      // default
    } else if (aqi <= 100) {
      category = 'Moderate';
      risk = 'moderate';
      pillClass = 'moderate';
      color = '#fbbf24';
      health = 'Air quality is acceptable; however, some pollutants may affect unusually sensitive individuals.';
      precautions = [
        'Unusually sensitive individuals should consider reducing prolonged outdoor exertion.',
        'General public can continue normal outdoor activities.',
      ];
    } else if (aqi <= 150) {
      category = 'Unhealthy for Sensitive Groups';
      risk = 'elevated';
      pillClass = 'sensitive';
      color = '#fb923c';
      health = 'Members of sensitive groups may experience adverse health effects.';
      precautions = [
        'Sensitive groups should limit strenuous outdoor activities.',
        'Wear protective particulate masks (N95) near high-traffic corridors.',
      ];
    } else if (aqi <= 200) {
      category = 'Unhealthy';
      risk = 'high';
      pillClass = 'unhealthy';
      color = '#f87171';
      health = 'Everyone may begin to experience health effects; sensitive groups experience more serious effects.';
      precautions = [
        'Active children and adults should avoid prolonged outdoor exertion.',
        'Wear N95/FFP2 masks outdoors.',
        'Operate indoor HEPA air purifiers where available.',
      ];
    } else if (aqi <= 300) {
      category = 'Very Unhealthy';
      risk = 'very_high';
      pillClass = 'very_unhealthy';
      color = '#c084fc';
      health = 'Health alert: risk of health effects is increased for everyone in the area.';
      precautions = [
        'Avoid all outdoor physical and recreational activities.',
        'Wear certified high-filtration respirators when outside.',
      ];
    } else {
      category = 'Hazardous';
      risk = 'severe';
      pillClass = 'hazardous';
      color = '#fda4af';
      health = 'Health warning of emergency conditions: everyone is more likely to be seriously affected.';
      precautions = [
        'Remain strictly indoors and seal windows against particulate infiltration.',
        'Consult healthcare providers if shortness of breath occurs.',
      ];
    }

    pillEl.className = `aqi-category-pill ${pillClass}`;
    pillEl.textContent = category;
    riskLabel.textContent = `${risk.toUpperCase()} RISK`;
    progressRing.style.stroke = color;
    healthText.textContent = health;

    precautionsList.innerHTML = precautions.map(p => `
      <div class="precaution-item">
        <span class="check-icon">✓</span>
        <span>${p}</span>
      </div>
    `).join('');
  }

  aqiSlider.addEventListener('input', (e) => {
    updateAqiGaugeVisuals(parseInt(e.target.value, 10));
  });

  async function loadAirData() {
    const locParam = state.selectedLocation ? `?location_id=${state.selectedLocation}` : '';
    const assessments = await apiGet(`/api/v1/air/assessments${locParam}`);
    if (assessments && assessments.length > 0) {
      state.airAssessments = assessments;
      const latest = assessments[assessments.length - 1];
      aqiSlider.value = latest.aqi;
      updateAqiGaugeVisuals(latest.aqi);
      renderAirTable(assessments);
    } else {
      updateAqiGaugeVisuals(parseInt(aqiSlider.value, 10));
    }
  }

  function renderAirTable(assessments) {
    const tbody = document.getElementById('air-tbody');
    if (!assessments || assessments.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center">No atmospheric observations logged yet.</td></tr>';
      return;
    }

    const sorted = [...assessments].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    tbody.innerHTML = sorted.slice(0, 8).map(a => `
      <tr>
        <td>${new Date(a.timestamp).toLocaleDateString()} ${new Date(a.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</td>
        <td>${a.location_id}</td>
        <td><strong>${a.aqi}</strong></td>
        <td><span class="badge-sub">${a.category}</span></td>
        <td>${a.risk_level}</td>
        <td>${a.dominant_pollutant || '--'}</td>
        <td>${a.source}</td>
      </tr>
    `).join('');
  }

  // Air Observation Form Handler
  const airForm = document.getElementById('form-air-assess');
  airForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const aqi = parseInt(aqiSlider.value, 10);
    const source = document.getElementById('air-source').value;
    const dominant = document.getElementById('air-dominant').value;

    const payload = {
      location_id: state.selectedLocation || 'LOC-001',
      aqi,
      source,
      dominant_pollutant: dominant,
    };

    const res = await apiPost('/api/v1/air/assessments', payload);
    if (res) {
      showToast(`AQI observation recorded: ${res.category}`, 'success');
      loadAirData();
    }
  });

  // ============================================================
  // TRACK 3: ECOSORT (NUCLEAR THEME) LOGIC
  // ============================================================
  async function loadWasteData() {
    const locParam = state.selectedLocation ? `?location_id=${state.selectedLocation}` : '';

    // Fetch Summary
    const summary = await apiGet(`/api/v1/waste/summary${locParam}`);
    if (summary) {
      state.wasteSummary = summary;
      renderWasteSummary(summary);
    }

    // Fetch Entries Feed
    const entries = await apiGet(`/api/v1/waste/entries${locParam}`);
    if (entries) {
      state.wasteEntries = entries;
      renderWasteTable(entries);
    }
  }

  function renderWasteSummary(summary) {
    document.getElementById('waste-diversion-rate').textContent = `${summary.recycling_rate_percentage}%`;
    document.getElementById('waste-total-kg').textContent = `${summary.total_quantity_kg.toFixed(1)} kg`;

    // Estimate recovered kWh (approx 1.8 kWh per kg diverted) and carbon avoided (~ 2.2 kg CO2 per kg diverted)
    const divertedKg = (summary.total_quantity_kg * (summary.recycling_rate_percentage / 100.0));
    const kwhEst = Math.round(divertedKg * 1.8);
    const co2Est = Math.round(divertedKg * 2.2);

    document.getElementById('waste-energy-kwh').textContent = `${kwhEst.toLocaleString()} kWh`;
    document.getElementById('waste-co2-tons').textContent = `${co2Est.toLocaleString()} kg CO2`;

    // Directives
    const listEl = document.getElementById('waste-recommendations-list');
    if (summary.top_recommendations && summary.top_recommendations.length > 0) {
      listEl.innerHTML = summary.top_recommendations.map(r => `<li>${r}</li>`).join('');
    }

    // Render Material Category Cards
    const cardsContainer = document.getElementById('material-cards-grid');
    const categories = summary.categories || {};
    const catKeys = Object.keys(categories);

    if (catKeys.length === 0) {
      cardsContainer.innerHTML = '<div class="empty-feed">No material feedstock logged yet.</div>';
    } else {
      cardsContainer.innerHTML = catKeys.map(k => `
        <div class="material-card">
          <span class="mat-cat-title">${k}</span>
          <span class="mat-cat-mass">${categories[k].total_quantity_kg.toFixed(1)} kg</span>
          <span class="badge-sub">${categories[k].entries_count} logs</span>
        </div>
      `).join('');
    }
  }

  function renderWasteTable(entries) {
    const tbody = document.getElementById('waste-tbody');
    if (!entries || entries.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center">No waste items logged yet.</td></tr>';
      return;
    }

    const sorted = [...entries].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    tbody.innerHTML = sorted.slice(0, 8).map(e => `
      <tr>
        <td>${new Date(e.timestamp).toLocaleDateString()} ${new Date(e.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</td>
        <td><code>${e.entry_id}</code></td>
        <td>${e.location_id}</td>
        <td><strong class="neon-green">${e.category}</strong></td>
        <td>${e.quantity} ${e.unit}</td>
        <td><span class="badge-sub">${e.disposal_method}</span></td>
        <td style="max-width: 220px; font-size: 0.75rem; color: #94a3b8;">${e.suggestion}</td>
      </tr>
    `).join('');
  }

  // Waste Entry Form Handler
  const wasteForm = document.getElementById('form-waste-entry');
  wasteForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const category = document.getElementById('waste-category').value;
    const method = document.getElementById('waste-disposal').value;
    const qty = parseFloat(document.getElementById('waste-quantity').value);
    const unit = document.getElementById('waste-unit').value;
    const notes = document.getElementById('waste-notes').value || null;

    const payload = {
      location_id: state.selectedLocation || 'LOC-001',
      category,
      quantity: qty,
      unit,
      disposal_method: method,
      notes,
    };

    const res = await apiPost('/api/v1/waste/entries', payload);
    if (res) {
      showToast(`Material feedstock ${res.category} recorded!`, 'success');
      loadWasteData();
    }
  });

  // ============================================================
  // SEED DEMO DATA ACTION
  // ============================================================
  btnSeedData.addEventListener('click', async () => {
    btnSeedData.disabled = true;
    btnSeedData.innerHTML = '<span class="btn-icon">⏳</span> Seeding...';

    // Call seed endpoint or trigger seeding via health/seed
    const res = await apiPost('/seed?reset=true', {});
    if (res) {
      showToast('Demo datasets seeded successfully across all tracks!', 'success');
    } else {
      showToast('Seeding completed.', 'info');
    }

    await refreshAllData();
    btnSeedData.disabled = false;
    btnSeedData.innerHTML = '<span class="btn-icon">⚡</span> Seed Demo';
  });

  // ============================================================
  // GLOBAL DATA REFRESH
  // ============================================================
  function refreshTrackData(trackKey) {
    if (trackKey === 'water') loadWaterData();
    if (trackKey === 'air') loadAirData();
    if (trackKey === 'waste') loadWasteData();
  }

  async function refreshAllData() {
    await Promise.all([
      loadWaterData(),
      loadAirData(),
      loadWasteData(),
    ]);
  }

  // Initialize
  refreshAllData();
});
