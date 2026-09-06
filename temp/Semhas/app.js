/**
 * Mudlogging Pro — Main Interactive Application Controller
 * Author: UGM Skripsi (SDLC 5-Phase Architecture)
 */

// Default 21-Track Petrophysical Indicator Schema
const DEFAULT_SCHEMA = [
  // 1-8: Raw Chromatographic Gases & Total Gas
  { id: 'C1', key: 'C1', name: 'C1 (Methane)', unit: 'ppm', scale: '0 - 60k', scaleType: 'log', visible: true, isCustom: false, color: '#38bdf8' },
  { id: 'C2', key: 'C2', name: 'C2 (Ethane)', unit: 'ppm', scale: '0 - 4k', scaleType: 'log', visible: true, isCustom: false, color: '#818cf8' },
  { id: 'C3', key: 'C3', name: 'C3 (Propane)', unit: 'ppm', scale: '0 - 2k', scaleType: 'log', visible: true, isCustom: false, color: '#f472b6' },
  { id: 'iC4', key: 'IC4', name: 'iC4 (Iso-Butane)', unit: 'ppm', scale: '0 - 800', scaleType: 'log', visible: true, isCustom: false, color: '#fb923c' },
  { id: 'nC4', key: 'NC4', name: 'nC4 (Nor-Butane)', unit: 'ppm', scale: '0 - 1k', scaleType: 'log', visible: true, isCustom: false, color: '#facc15' },
  { id: 'iC5', key: 'IC5', name: 'iC5 (Iso-Pentane)', unit: 'ppm', scale: '0 - 500', scaleType: 'log', visible: true, isCustom: false, color: '#34d399' },
  { id: 'nC5', key: 'NC5', name: 'nC5 (Nor-Pentane)', unit: 'ppm', scale: '0 - 500', scaleType: 'log', visible: true, isCustom: false, color: '#a78bfa' },
  { id: 'TG', key: 'TG_USED', name: 'Total Gas (TG)', unit: 'ppm', scale: '0 - 70k', scaleType: 'log', visible: true, isCustom: false, color: '#ffffff' },

  // 9-13: Pixler Ratios & Normalized Hydrocarbon Multipliers
  { id: 'Pixler1', key: 'R1_C1_C2', name: 'Pixler R1 (C1/C2)', unit: 'ratio', scale: '0 - 100', scaleType: 'log', visible: true, isCustom: false, color: '#38bdf8' },
  { id: 'Pixler2', key: 'R2_C1_C3', name: 'Pixler R2 (C1/C3)', unit: 'ratio', scale: '0 - 80', scaleType: 'log', visible: true, isCustom: false, color: '#818cf8' },
  { id: 'Pixler3', key: 'R3_C2_C3', name: 'Pixler R3 (C2/C3)', unit: 'ratio', scale: '0 - 10', scaleType: 'log', visible: true, isCustom: false, color: '#f472b6' },
  { id: 'Ratio4', key: 'R4_C1_IC4', name: 'Ratio 4 (C1/iC4)', unit: 'ratio', scale: '0 - 300', scaleType: 'log', visible: true, isCustom: false, color: '#fb923c' },
  { id: 'Ratio5', key: 'R5_C1_NC4', name: 'Ratio 5 (C1/nC4)', unit: 'ratio', scale: '0 - 250', scaleType: 'log', visible: true, isCustom: false, color: '#facc15' },

  // 14-15: Gas Dryness & Carbon Density Index
  { id: 'Dryness', key: 'DRYNESS', name: 'Dryness (C1/TG)', unit: '%', scale: '50 - 100', scaleType: 'linear', visible: true, isCustom: false, color: '#eab308' },
  { id: 'Icarbon', key: 'CARBON_INDEX', name: 'Carbon Index (Ci)', unit: 'index', scale: '0 - 1.0', scaleType: 'linear', visible: true, isCustom: false, color: '#818cf8' },

  // 16-18: Haworth Show Indicators
  { id: 'Wh', key: 'WH', name: 'Haworth Wetness (Wh)', unit: '%', scale: '0 - 40', scaleType: 'linear', visible: true, isCustom: false, color: '#22c55e' },
  { id: 'Bh', key: 'BH', name: 'Haworth Balance (Bh)', unit: 'index', scale: '0 - 200', scaleType: 'linear', visible: true, isCustom: false, color: '#f59e0b' },
  { id: 'Ch', key: 'CH', name: 'Haworth Character (Ch)', unit: 'index', scale: '0 - 5', scaleType: 'linear', visible: true, isCustom: false, color: '#ef4444' },

  // 19-21: Composite Indicators & Fluid Classification
  { id: 'GOW', key: 'GOW', name: 'Composite GOW', unit: 'index', scale: '0 - 50k', scaleType: 'log', visible: true, isCustom: false, color: '#10b981' },
  { id: 'WBS', key: 'WBS', name: 'Wetness-Balance (WBS)', unit: 'score', scale: '-2 to +2', scaleType: 'linear', visible: true, isCustom: false, color: '#f97316' },
  { id: 'FluidZone', key: 'ZONE', name: 'Fluid Zone Class', unit: 'facies', scale: 'Gas/Oil/Wat', scaleType: 'discrete', visible: true, isCustom: false, color: '#6366f1', isZone: true }
];

// Formula Definitions with defaults
const DEFAULT_FORMULAS = {
  pixler1: { name: "Pixler Ratio 1 (C1 / C2)", expr: "C1 / C2", gas: "R1 > 15", oil: "2 <= R1 < 15", water: "R1 < 2" },
  pixler2: { name: "Pixler Ratio 2 (C1 / C3)", expr: "C1 / C3", gas: "R2 > 30", oil: "4 <= R2 <= 30", water: "R2 < 4" },
  pixler3: { name: "Pixler Ratio 3 (C2 / C3)", expr: "C2 / C3", gas: "R3 < 0.5", oil: "0.5 <= R3 <= 5.0", water: "R3 > 5.0" },
  r4: { name: "Ratio 4 (C1 / iC4)", expr: "C1 / iC4", gas: "R4 > 150", oil: "15 <= R4 <= 150", water: "R4 < 15" },
  r5: { name: "Ratio 5 (C1 / nC4)", expr: "C1 / nC4", gas: "R5 > 100", oil: "10 <= R5 <= 100", water: "R5 < 10" },
  dryness: { name: "Dryness Ratio", expr: "(C1 / TG) * 100", gas: "Dry >= 85%", oil: "50 <= Dry < 85%", water: "Dry < 50%" },
  carbon_density: { name: "Carbon Density Index (I_carbon)", expr: "TG / (C1 + 2*C2 + 3*C3 + 4*iC4 + 4*nC4 + 5*iC5 + 5*nC5)", gas: "> 0.85", oil: "0.40 - 0.85", water: "< 0.40" },
  wh: { name: "Haworth Wetness Ratio (Wh)", expr: "((C2 + C3 + iC4 + nC4 + iC5 + nC5) / TG) * 100", gas: "Wh < 17.5", oil: "17.5 <= Wh <= 40.0", water: "Wh > 40.0" },
  bh: { name: "Haworth Balance Ratio (Bh)", expr: "(C1 + C2) / (C3 + iC4 + nC4 + iC5 + nC5)", gas: "Bh >= 15.0", oil: "0.5 <= Bh < 15.0", water: "Bh < 0.5" },
  ch: { name: "Haworth Character Ratio (Ch)", expr: "(iC4 + nC4 + iC5 + nC5) / C3", gas: "Ch < 0.5", oil: "Ch >= 0.5", water: "Ch undefined" },
  gow: { name: "Composite GOW", expr: "(C3 + iC4 + nC4 + iC5 + nC5) * TG", gas: "GOW < 500", oil: "500 <= GOW <= 15000", water: "GOW > 15000" },
  gow_notg: { name: "GOW No-TG", expr: "(C3 + iC4 + nC4 + iC5 + nC5) / TG", gas: "< 0.015", oil: "0.015 - 0.08", water: "> 0.08" },
  wbs: { name: "Wetness-Balance Score (WBS)", expr: "((log10(Bh) - 0.903) / 2.097) - (log10(Wh) / 2)", gas: "WBS > 0", oil: "-0.5 <= WBS <= 0", water: "WBS < -0.5" },
  gor: { name: "Gas-Oil Ratio (GOR)", expr: "TG / (C2 + C3 + iC4 + nC4)", gas: "> 5000", oil: "500 - 5000", water: "< 500" }
};

// Application State
let currentSchema = JSON.parse(JSON.stringify(DEFAULT_SCHEMA));
let formulaDefinitions = JSON.parse(JSON.stringify(DEFAULT_FORMULAS));
let customFormulaOverrides = {};
let wellData = [];
let chartObjects = {};

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
  // Load synthetic benchmark dataset
  wellData = PetrophysicalEngine.generateBenchmarkDataset('synthetic');
  
  // Render views
  renderKPIBar();
  build21UniqueTracks();
  renderColumnChecklist();
  renderRemoveColumnsList();
  setupSynchronizedCrosshair();
  setupWindowClickListeners();
  loadFormulaDefinition('wh');
});

/**
 * Render KPI Summary Top Bar
 */
function renderKPIBar() {
  if (!wellData || wellData.length === 0) return;

  const depths = wellData.map(d => d.DEPTH);
  const minDepth = Math.min(...depths);
  const maxDepth = Math.max(...depths);
  const depthSpan = (maxDepth - minDepth).toFixed(0);

  const c1Values = wellData.map(d => d.C1);
  const maxC1 = Math.max(...c1Values);

  const drynessValues = wellData.map(d => d.DRYNESS).filter(v => !isNaN(v) && v > 0);
  const meanDryness = drynessValues.length ? (drynessValues.reduce((a, b) => a + b, 0) / drynessValues.length).toFixed(1) : '0.0';

  const whValues = wellData.map(d => d.WH).filter(v => !isNaN(v) && v > 0);
  const meanWh = whValues.length ? (whValues.reduce((a, b) => a + b, 0) / whValues.length).toFixed(2) : '0.00';

  // Count zones
  const zoneCounts = { Gas: 0, Oil: 0, Water: 0, 'No Show': 0 };
  wellData.forEach(d => {
    const z = d.ZONE || 'No Show';
    zoneCounts[z] = (zoneCounts[z] || 0) + 1;
  });

  const payIntervalRows = (zoneCounts.Gas || 0) + (zoneCounts.Oil || 0);
  const avgStep = depths.length > 1 ? (maxDepth - minDepth) / (depths.length - 1) : 10;
  const payThickness = (payIntervalRows * avgStep).toFixed(0);

  let dominantFacies = 'Gas Pay';
  if (zoneCounts.Oil > zoneCounts.Gas) dominantFacies = 'Oil Pay';
  else if (zoneCounts.Water > zoneCounts.Gas && zoneCounts.Water > zoneCounts.Oil) dominantFacies = 'Water / Non-Prod';

  document.getElementById('kpiDepthSpan').innerText = `${minDepth.toLocaleString()} - ${maxDepth.toLocaleString()} m (${depthSpan}m)`;
  document.getElementById('kpiDominantZone').innerText = dominantFacies;
  document.getElementById('kpiPeakC1').innerText = `${Math.round(maxC1).toLocaleString()} ppm`;
  document.getElementById('kpiMeanDryness').innerText = `${meanDryness} %`;
  document.getElementById('kpiPayThickness').innerText = `${payThickness} m`;
  document.getElementById('kpiMeanWh').innerText = `${meanWh} %`;

  // Depth range subtitle in header strip
  const depthBadge = document.getElementById('depthRangeIndicator');
  if (depthBadge) depthBadge.innerText = `MD: ${minDepth.toFixed(0)}m – ${maxDepth.toFixed(0)}m (${wellData.length} pts)`;
}

/**
 * Build All Unique Multi-Tracks and Attach Dedicated Chart.js Instances
 */
function build21UniqueTracks() {
  const mount = document.getElementById('dynamicTracksMount');
  if (!mount) return;
  mount.innerHTML = '';

  // Destroy previous charts to avoid memory leak
  Object.keys(chartObjects).forEach(k => {
    if (chartObjects[k]) chartObjects[k].destroy();
  });
  chartObjects = {};

  // Build Sticky Depth Column Marks
  buildStickyDepthScale();

  const depths = wellData.map(d => d.DEPTH);

  currentSchema.forEach((col, index) => {
    if (!col.visible) return;

    const trackDiv = document.createElement('div');
    trackDiv.className = `unique-track ${col.isZone ? 'zone-track-width' : ''}`;
    trackDiv.id = `track_${col.id}`;
    trackDiv.setAttribute('data-col-id', col.id);

    // Track Header
    trackDiv.innerHTML = `
      <div class="unique-track-header">
        <div class="track-name-title" style="color: ${col.color || '#38bdf8'};" title="${col.name}">
          ${index + 1}. ${col.name}
        </div>
        <div class="track-scale-range">
          <span>[${col.unit}]</span>
          <span>${col.scale || ''}</span>
        </div>
      </div>
      <div class="unique-track-body" id="body_${col.id}">
        ${col.isZone ? buildFluidZoneFaciesHTML() : `<canvas id="canvas_${col.id}" class="unique-track-canvas"></canvas>`}
      </div>
    `;

    mount.appendChild(trackDiv);

    // If numeric continuous track, instantiate high-performance Chart.js
    if (!col.isZone) {
      const canvasEl = document.getElementById(`canvas_${col.id}`);
      if (canvasEl) {
        const ctx = canvasEl.getContext('2d');
        const dataKey = col.key || col.id;
        const dataValues = wellData.map(d => {
          const val = d[dataKey] !== undefined ? d[dataKey] : (d[col.id] !== undefined ? d[col.id] : 0);
          return parseFloat(val);
        });

        // Compute color gradient fill
        const gradient = ctx.createLinearGradient(0, 0, 120, 0);
        gradient.addColorStop(0, `${col.color || '#38bdf8'}08`);
        gradient.addColorStop(1, `${col.color || '#38bdf8'}35`);

        chartObjects[col.id] = new Chart(ctx, {
          type: 'line',
          data: {
            labels: depths,
            datasets: [
              {
                label: col.name,
                data: dataValues,
                borderColor: col.color || '#38bdf8',
                backgroundColor: gradient,
                fill: true,
                borderWidth: 1.6,
                pointRadius: 0,
                pointHoverRadius: 4,
                pointHoverBackgroundColor: col.color || '#38bdf8',
                pointHoverBorderColor: '#ffffff',
                pointHoverBorderWidth: 1.5,
                tension: 0.12
              }
            ]
          },
          options: getSingleTrackChartOptions(col, depths)
        });
      }
    }
  });

  // Update active track count badges
  const activeCount = currentSchema.filter(c => c.visible).length;
  const trackBadge = document.getElementById('activeTrackBadge');
  if (trackBadge) trackBadge.innerText = `${activeCount} Unique Tracks Active`;
  const dropdownPill = document.getElementById('dropdownColCount');
  if (dropdownPill) dropdownPill.innerText = `${activeCount} active`;
}

/**
 * Builds Sticky Depth Scale Numbers on Left Column
 */
function buildStickyDepthScale() {
  const depthBody = document.querySelector('.depth-scale-body');
  if (!depthBody || !wellData.length) return;

  depthBody.innerHTML = '';
  const depths = wellData.map(d => d.DEPTH);
  const minDepth = Math.min(...depths);
  const maxDepth = Math.max(...depths);
  const step = (maxDepth - minDepth) / 7;

  for (let i = 0; i <= 7; i++) {
    const dVal = Math.round(minDepth + (step * i));
    const mark = document.createElement('div');
    mark.className = 'depth-mark';
    mark.innerText = dVal.toLocaleString();
    depthBody.appendChild(mark);
  }
}

/**
 * Builds Fluid Zone Facies HTML Blocks
 */
function buildFluidZoneFaciesHTML() {
  if (!wellData.length) return '';

  // Aggregate contiguous zone intervals
  const intervals = [];
  let currentZone = wellData[0].ZONE || 'No Show';
  let startMD = wellData[0].DEPTH;
  let count = 1;

  for (let i = 1; i < wellData.length; i++) {
    const z = wellData[i].ZONE || 'No Show';
    if (z === currentZone) {
      count++;
    } else {
      intervals.push({
        zone: currentZone,
        startMD: startMD,
        endMD: wellData[i - 1].DEPTH,
        count: count
      });
      currentZone = z;
      startMD = wellData[i].DEPTH;
      count = 1;
    }
  }
  intervals.push({
    zone: currentZone,
    startMD: startMD,
    endMD: wellData[wellData.length - 1].DEPTH,
    count: count
  });

  let html = `<div class="zone-column" id="zoneVisualColumn">`;
  intervals.forEach(inv => {
    let cssClass = 'zone-noshow';
    let label = 'No Show / Noise';
    if (inv.zone === 'Gas') {
      cssClass = 'zone-gas';
      label = `Gas Pay (${Math.round(inv.startMD)}-${Math.round(inv.endMD)}m)`;
    } else if (inv.zone === 'Oil') {
      cssClass = 'zone-oil';
      label = `Oil Pay (${Math.round(inv.startMD)}-${Math.round(inv.endMD)}m)`;
    } else if (inv.zone === 'Water') {
      cssClass = 'zone-water';
      label = `Water Sand (${Math.round(inv.startMD)}-${Math.round(inv.endMD)}m)`;
    }

    html += `
      <div class="zone-block ${cssClass}" style="flex: ${inv.count};" title="${inv.zone} (${inv.startMD.toFixed(1)}m – ${inv.endMD.toFixed(1)}m)" onclick="showToast('Selected Facies: ${inv.zone} interval [${inv.startMD.toFixed(0)}m - ${inv.endMD.toFixed(0)}m]')">
        <span>${label}</span>
      </div>
    `;
  });
  html += `</div>`;
  return html;
}

/**
 * Single Track Chart.js Configuration
 */
function getSingleTrackChartOptions(col, depths) {
  const isLog = col.scaleType === 'log';

  return {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y', // Vertical depth log orientation
    animation: false,
    scales: {
      x: {
        type: isLog ? 'logarithmic' : 'linear',
        grid: { color: 'rgba(255,255,255,0.04)' },
        ticks: {
          color: '#64748b',
          font: { size: 8, family: 'JetBrains Mono' },
          maxTicksLimit: 3,
          callback: function(val) {
            if (val >= 1000) return (val / 1000) + 'k';
            return val;
          }
        }
      },
      y: {
        reverse: false, // Depth goes downward
        grid: { color: 'rgba(255,255,255,0.04)' },
        ticks: { display: false }
      }
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: '#0f192f',
        borderColor: '#2d4575',
        borderWidth: 1,
        titleColor: col.color || '#38bdf8',
        bodyFont: { family: 'JetBrains Mono', size: 10 },
        callbacks: {
          title: function(items) {
            if (!items.length) return '';
            const depthVal = depths[items[0].dataIndex];
            return `MD: ${depthVal.toFixed(1)} m`;
          },
          label: function(item) {
            const rawVal = item.raw;
            return `${col.name}: ${typeof rawVal === 'number' ? rawVal.toFixed(2) : rawVal} ${col.unit}`;
          }
        }
      }
    },
    onHover: (e, activeEls, chart) => {
      if (activeEls && activeEls.length > 0) {
        const index = activeEls[0].index;
        syncDepthCrosshairByIndex(index);
      }
    }
  };
}

/**
 * Synchronized Depth Crosshair Cursor across all 21 tracks
 */
function setupSynchronizedCrosshair() {
  const wrapper = document.getElementById('tracksScrollWrapper');
  const inner = document.getElementById('tracksContainer');
  if (!wrapper || !inner) return;

  let crossLine = document.getElementById('syncCrosshairLine');
  if (!crossLine) {
    crossLine = document.createElement('div');
    crossLine.id = 'syncCrosshairLine';
    crossLine.className = 'sync-crosshair-line';
    inner.appendChild(crossLine);
  }

  let crossBadge = document.getElementById('syncCrosshairBadge');
  if (!crossBadge) {
    crossBadge = document.createElement('div');
    crossBadge.id = 'syncCrosshairBadge';
    crossBadge.className = 'sync-crosshair-badge';
    inner.appendChild(crossBadge);
  }

  wrapper.addEventListener('mousemove', (e) => {
    const rect = inner.getBoundingClientRect();
    const relY = e.clientY - rect.top;
    if (relY >= 52 && relY <= rect.height) {
      crossLine.style.top = `${relY}px`;
      crossLine.style.display = 'block';

      // Find nearest depth point
      const fraction = (relY - 52) / (rect.height - 52);
      if (wellData.length > 0) {
        const idx = Math.min(wellData.length - 1, Math.max(0, Math.round(fraction * (wellData.length - 1))));
        const currentMD = wellData[idx].DEPTH;
        crossBadge.style.top = `${relY}px`;
        crossBadge.innerText = `${currentMD.toFixed(0)}m`;
        crossBadge.style.display = 'block';
      }
    }
  });

  wrapper.addEventListener('mouseleave', () => {
    crossLine.style.display = 'none';
    crossBadge.style.display = 'none';
  });
}

function syncDepthCrosshairByIndex(dataIndex) {
  if (dataIndex < 0 || dataIndex >= wellData.length) return;
  const inner = document.getElementById('tracksContainer');
  const crossLine = document.getElementById('syncCrosshairLine');
  const crossBadge = document.getElementById('syncCrosshairBadge');
  if (!inner || !crossLine || !crossBadge) return;

  const rect = inner.getBoundingClientRect();
  const stepHeight = (rect.height - 52) / (wellData.length - 1);
  const posY = 52 + (dataIndex * stepHeight);

  crossLine.style.top = `${posY}px`;
  crossLine.style.display = 'block';

  crossBadge.style.top = `${posY}px`;
  crossBadge.innerText = `${wellData[dataIndex].DEPTH.toFixed(0)}m`;
  crossBadge.style.display = 'block';
}

/**
 * Dropdown Controls
 */
function toggleDropdown(id) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle('active');
}

function closeDropdown(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('active');
}

function setupWindowClickListeners() {
  window.addEventListener('click', (e) => {
    if (!e.target.closest('.dropdown')) {
      document.querySelectorAll('.dropdown').forEach(d => d.classList.remove('active'));
    }
  });
}

/**
 * Modal Dialog Controller
 */
function openModal(id) {
  const m = document.getElementById(id);
  if (m) {
    m.classList.add('active');
    if (id === 'columnsModal') renderColumnChecklist();
    if (id === 'formulasModal') updateFormulaLivePreview();
  }
}

function closeModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.remove('active');
}

/**
 * Column Sub-Tab Switching
 */
function switchColumnSubTab(subTab) {
  ['visibility', 'add', 'manage'].forEach(t => {
    const el = document.getElementById(`colSubTab${capitalize(t)}`);
    const btn = document.getElementById(`btnColTab${capitalize(t)}`);
    if (el) el.style.display = 'none';
    if (btn) btn.classList.remove('active');
  });

  const activeEl = document.getElementById(`colSubTab${capitalize(subTab)}`);
  const activeBtn = document.getElementById(`btnColTab${capitalize(subTab)}`);
  if (activeEl) activeEl.style.display = 'block';
  if (activeBtn) activeBtn.classList.add('active');
}

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/**
 * Render Checklist for Show/Hide Columns
 */
function renderColumnChecklist() {
  const container = document.getElementById('columnsChecklist');
  if (!container) return;
  container.innerHTML = '';

  currentSchema.forEach((col, idx) => {
    const card = document.createElement('div');
    card.className = 'column-check-card';
    card.innerHTML = `
      <label>
        <input type="checkbox" id="chk_col_${col.id}" ${col.visible ? 'checked' : ''} onchange="toggleColumnVisibilityState('${col.id}', this.checked)" />
        <span style="color: ${col.color || '#fff'}">${idx + 1}. ${col.name}</span>
      </label>
      <span class="col-badge">[${col.unit}]</span>
    `;
    container.appendChild(card);
  });
}

function toggleColumnVisibilityState(colId, isVisible) {
  const target = currentSchema.find(c => c.id === colId);
  if (target) target.visible = isVisible;
}

function toggleAllColumns(state) {
  currentSchema.forEach(c => c.visible = state);
  renderColumnChecklist();
}

function applyColumnChanges() {
  closeModal('columnsModal');
  build21UniqueTracks();
  showToast(`Column configuration applied: ${currentSchema.filter(c => c.visible).length} active tracks`);
}

/**
 * Add Custom Computed Column
 */
function insertNewColVar(v) {
  const input = document.getElementById('newColFormula');
  if (input) {
    input.value += (input.value.length > 0 ? ' ' : '') + v;
    input.focus();
  }
}

function addNewColumnFromModal() {
  const nameInput = document.getElementById('newColName');
  const unitInput = document.getElementById('newColUnit');
  const colorInput = document.getElementById('newColColor');
  const formulaInput = document.getElementById('newColFormula');

  const name = nameInput.value.trim();
  const unit = unitInput.value.trim() || 'ratio';
  const color = colorInput.value || '#38bdf8';
  const formula = formulaInput.value.trim();

  if (!name) {
    alert('Please enter a column identifier name');
    return;
  }
  if (!formula) {
    alert('Please enter a mathematical computation formula');
    return;
  }

  const colId = 'custom_' + name.replace(/[^a-zA-Z0-9]/g, '_');
  customFormulaOverrides[colId] = formula;

  currentSchema.push({
    id: colId,
    key: colId,
    name: name,
    unit: unit,
    scale: 'auto',
    scaleType: 'linear',
    visible: true,
    isCustom: true,
    formula: formula,
    color: color
  });

  // Recompute well data with new formula
  wellData = PetrophysicalEngine.computeAll(wellData, customFormulaOverrides);

  nameInput.value = '';
  formulaInput.value = '';

  renderColumnChecklist();
  renderRemoveColumnsList();
  build21UniqueTracks();
  switchColumnSubTab('visibility');
  showToast(`Added new graph column: ${name}`);
}

/**
 * Remove Custom Columns
 */
function renderRemoveColumnsList() {
  const container = document.getElementById('removeColumnsList');
  if (!container) return;
  container.innerHTML = '';

  const customOrRemovable = currentSchema.filter(c => c.id !== 'C1');
  if (customOrRemovable.length === 0) {
    container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.8rem;">No removable columns available.</div>';
    return;
  }

  customOrRemovable.forEach(col => {
    const row = document.createElement('div');
    row.style.cssText = 'display: flex; justify-content: space-between; align-items: center; background: rgba(16, 26, 46, 0.5); padding: 0.5rem 0.8rem; border-radius: 6px; border: 1px solid var(--border-color);';
    row.innerHTML = `
      <div>
        <strong style="font-size: 0.82rem; color: ${col.color || '#fff'}">${col.name}</strong>
        <span style="font-size: 0.7rem; color: var(--text-muted); margin-left: 0.4rem;">(${col.unit}) ${col.isCustom ? '• Custom' : ''}</span>
      </div>
      <button class="btn btn-outline" style="padding: 0.25rem 0.55rem; font-size: 0.72rem; color: var(--accent-rose); border-color: rgba(244, 63, 94, 0.3);" onclick="removeColumnById('${col.id}')">
        <i class="fa-solid fa-trash"></i> Remove
      </button>
    `;
    container.appendChild(row);
  });
}

function removeColumnById(colId) {
  currentSchema = currentSchema.filter(c => c.id !== colId);
  delete customFormulaOverrides[colId];
  renderColumnChecklist();
  renderRemoveColumnsList();
  build21UniqueTracks();
  showToast('Column removed from active schema');
}

/**
 * Formula Manager Controller
 */
function loadFormulaDefinition(key) {
  const f = formulaDefinitions[key];
  if (f) {
    document.getElementById('formulaExprInput').value = f.expr;
    document.getElementById('threshGas').value = f.gas;
    document.getElementById('threshOil').value = f.oil;
    document.getElementById('threshWater').value = f.water;
    updateFormulaLivePreview();
  }
}

function insertFormulaToken(token) {
  const input = document.getElementById('formulaExprInput');
  if (input) {
    input.value += token;
    input.focus();
    updateFormulaLivePreview();
  }
}

function updateFormulaLivePreview() {
  const previewEl = document.getElementById('formulaLivePreview');
  const exprInput = document.getElementById('formulaExprInput');
  if (!previewEl || !exprInput || !wellData.length) return;

  const sampleRow = wellData[Math.floor(wellData.length / 2)] || wellData[0];
  const expr = exprInput.value;

  try {
    const val = PetrophysicalEngine.evaluateExpression(expr, sampleRow);
    previewEl.innerHTML = `
      <span>Calculated at MD = ${sampleRow.DEPTH}m: <strong style="color: #38bdf8;">${val.toFixed(3)}</strong></span>
      <span class="badge-pill" style="background: rgba(16, 185, 129, 0.2); color: #34d399;">Auditable & Valid</span>
    `;
  } catch (err) {
    previewEl.innerHTML = `
      <span style="color: var(--accent-rose);">Syntax error in expression</span>
      <span class="badge-pill" style="background: rgba(244, 63, 94, 0.2); color: #fb7185;">Invalid</span>
    `;
  }
}

function saveFormulaChanges() {
  const key = document.getElementById('formulaSelect').value;
  const newExpr = document.getElementById('formulaExprInput').value;

  if (formulaDefinitions[key]) {
    formulaDefinitions[key].expr = newExpr;
    customFormulaOverrides[key] = newExpr;
  }

  closeModal('formulasModal');
  wellData = PetrophysicalEngine.computeAll(wellData, customFormulaOverrides);
  renderKPIBar();
  build21UniqueTracks();
  showToast(`Formula for ${key.toUpperCase()} updated & all 21 log curves recomputed`);
}

function restoreCurrentFormulaDefault() {
  const key = document.getElementById('formulaSelect').value;
  if (DEFAULT_FORMULAS[key]) {
    formulaDefinitions[key] = JSON.parse(JSON.stringify(DEFAULT_FORMULAS[key]));
    delete customFormulaOverrides[key];
    loadFormulaDefinition(key);
    showToast('Restored skripsi default formula baseline');
  }
}

function resetToDefaults() {
  currentSchema = JSON.parse(JSON.stringify(DEFAULT_SCHEMA));
  formulaDefinitions = JSON.parse(JSON.stringify(DEFAULT_FORMULAS));
  customFormulaOverrides = {};
  wellData = PetrophysicalEngine.generateBenchmarkDataset('synthetic');
  renderKPIBar();
  build21UniqueTracks();
  renderColumnChecklist();
  renderRemoveColumnsList();
  showToast('Reset to original 21-parameter Skripsi baseline');
}

/**
 * File Ingestion (CSV, LAS, XLSX, TXT)
 */
function handleFileUpload(files) {
  if (!files || files.length === 0) return;
  const file = files[0];
  const filename = file.name.toLowerCase();
  const startTime = performance.now();

  const reader = new FileReader();

  if (filename.endsWith('.xlsx') || filename.endsWith('.xls')) {
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target.result);
        const workbook = XLSX.read(data, { type: 'array' });
        const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
        const jsonRows = XLSX.utils.sheet_to_json(firstSheet);
        processParsedData(jsonRows, file.name, startTime);
      } catch (err) {
        alert('Failed to parse Excel file. Please verify format.');
      }
    };
    reader.readAsArrayBuffer(file);
  } else {
    reader.onload = (e) => {
      try {
        const text = e.target.result;
        let parsedRows = [];

        if (filename.endsWith('.las')) {
          parsedRows = parseLASFormat(text);
        } else {
          // Standard CSV / TXT / TSV
          const result = Papa.parse(text, { header: true, dynamicTyping: true, skipEmptyLines: true });
          parsedRows = result.data;
        }

        processParsedData(parsedRows, file.name, startTime);
      } catch (err) {
        alert('Failed to parse mud log text file.');
      }
    };
    reader.readAsText(file);
  }
}

function processParsedData(rawRows, filename, startTime) {
  if (!rawRows || rawRows.length === 0) {
    alert('Uploaded file contains no valid data rows.');
    return;
  }

  // Normalize column headers to standard uppercase
  const normalized = rawRows.map(row => {
    const cleanRow = {};
    Object.keys(row).forEach(k => {
      const uKey = k.trim().toUpperCase();
      cleanRow[uKey] = row[k];
    });

    // Map common aliases
    return {
      DEPTH: cleanRow.DEPTH || cleanRow.MD || cleanRow.DEPTH_M || cleanRow.DEP || 0,
      C1: cleanRow.C1 || cleanRow.CH4 || cleanRow.METHANE || 0,
      C2: cleanRow.C2 || cleanRow.C2H6 || cleanRow.ETHANE || 0,
      C3: cleanRow.C3 || cleanRow.C3H8 || cleanRow.PROPANE || 0,
      IC4: cleanRow.IC4 || cleanRow['I-C4'] || cleanRow.ISOBUTANE || cleanRow.I_C4 || 0,
      NC4: cleanRow.NC4 || cleanRow['N-C4'] || cleanRow.NORMALBUTANE || cleanRow.N_C4 || 0,
      IC5: cleanRow.IC5 || cleanRow['I-C5'] || cleanRow.ISOPENTANE || cleanRow.I_C5 || 0,
      NC5: cleanRow.NC5 || cleanRow['N-C5'] || cleanRow.NORMALPENTANE || cleanRow.N_C5 || 0,
      TG: cleanRow.TG || cleanRow.TOTAL_GAS || cleanRow.TOT_GAS || cleanRow.GAS || 0
    };
  }).filter(r => r.DEPTH > 0);

  if (normalized.length === 0) {
    alert('No valid rows with DEPTH/MD values could be extracted.');
    return;
  }

  wellData = PetrophysicalEngine.computeAll(normalized, customFormulaOverrides);
  const elapsed = ((performance.now() - startTime) / 1000).toFixed(3);

  closeModal('uploadModal');
  renderKPIBar();
  build21UniqueTracks();
  showToast(`Ingested ${filename} (${normalized.length} rows, ${elapsed}s latency)`);
}

function parseLASFormat(text) {
  const lines = text.split(/\r?\n/);
  let inDataSection = false;
  let curveHeaders = [];
  const rows = [];

  for (let line of lines) {
    line = line.trim();
    if (line.startsWith('#') || !line) continue;

    if (line.startsWith('~A') || line.startsWith('~ASCII')) {
      inDataSection = true;
      continue;
    }

    if (!inDataSection) {
      if (line.startsWith('~C') || line.startsWith('~CURVE')) {
        // Curve section
        continue;
      }
      if (line.includes('.')) {
        const parts = line.split(/[.:\s]+/);
        if (parts.length > 0 && parts[0].length > 0) {
          curveHeaders.push(parts[0].toUpperCase());
        }
      }
    } else {
      const tokens = line.split(/\s+/).map(Number);
      if (tokens.length >= 2) {
        const rowObj = {};
        tokens.forEach((val, i) => {
          const colName = curveHeaders[i] || `COL_${i}`;
          rowObj[colName] = val;
        });
        rows.push(rowObj);
      }
    }
  }
  return rows;
}

/**
 * Load Preset Benchmark Datasets
 */
function loadPresetDataset(preset) {
  wellData = PetrophysicalEngine.generateBenchmarkDataset(preset);
  closeModal('uploadModal');
  renderKPIBar();
  build21UniqueTracks();
  showToast(`Loaded ${preset.toUpperCase()} benchmark mud log (${wellData.length} records)`);
}

/**
 * Export Utilities (CSV, PNG, Schema, Report)
 */
function exportAnalysisReport() {
  openModal('exportModal');
}

function downloadComputedCSV() {
  if (!wellData.length) return;
  const csv = Papa.unparse(wellData);
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `mudlog_petrophysical_results_${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  closeModal('exportModal');
  showToast('Exported complete 21-parameter computed CSV dataset');
}

function exportLogImagePNG() {
  const target = document.getElementById('tracksScrollWrapper');
  if (!target) return;

  showToast('Generating high-resolution well log snapshot...');
  html2canvas(target, { backgroundColor: '#070c17', scale: 2 }).then(canvas => {
    const link = document.createElement('a');
    link.download = `mudlog_21track_visualization_${Date.now()}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
    closeModal('exportModal');
    showToast('Saved high-resolution well log PNG');
  });
}

function exportSchemaJSON() {
  const schemaExport = {
    appName: 'Mudlogging Pro',
    schemaVersion: '2.0-SDLC',
    timestamp: new Date().toISOString(),
    columns: currentSchema,
    formulas: formulaDefinitions,
    overrides: customFormulaOverrides
  };

  const blob = new Blob([JSON.stringify(schemaExport, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `mudlog_schema_config_${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
  closeModal('exportModal');
  showToast('Exported custom schema configuration JSON');
}

function triggerPresentationPrint() {
  closeModal('exportModal');
  window.print();
}

/**
 * Toast Helper
 */
function showToast(msg) {
  const toast = document.getElementById('appToast');
  const msgEl = document.getElementById('toastMsg');
  if (!toast || !msgEl) return;

  msgEl.innerText = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3200);
}
