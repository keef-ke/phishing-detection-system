// ── Config ──
const API_BASE = 'http://localhost:5000';
let confChart  = null;
let statsChart = null;

// Dynamic telemetry display rules matching your core backend features
const FEAT_META = {
  has_https:              {label:'TLS/HTTPS Connection', good:1},
  is_ip_address:          {label:'Raw IP Point-of-Origin', good:0},
  url_shortener_used:     {label:'Masked Domain Redirection', good:0},
  suspicious_keyword_cnt: {label:'High-Risk Target Lexicon', good:0},
  has_login_form:         {label:'Credential Input Vectors', good:null},
  redirect_count:         {label:'HTTP Forward Hops', good:null},
  has_valid_ssl:          {label:'Cryptographic Integrity', good:1},
  domain_age_days:        {label:'Domain Age Horizon', good:null},
  form_action_external:   {label:'Exfiltration Data Vectors', good:0},
  right_click_disabled:   {label:'Client Context Interception', good:0},
  has_hidden_iframe:      {label:'Invisible Elements Group', good:0},
  meta_refresh_redirect:  {label:'Client Refresh Loops', good:0},
  favicon_external:       {label:'Asset Origin Integrity', good:0},
};

// Defensive Helper: Replaces dangerous characters to prevent DOM-based XSS injection
function escapeHTML(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

// Secure Network Client: Enforces an explicit 30-second processing window timeout
async function fetchWithTimeout(resource, options = {}) {
  const { timeout = 30000 } = options;
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(resource, { ...options, signal: controller.signal });
    clearTimeout(id);
    return response;
  } catch (error) {
    clearTimeout(id);
    throw error;
  }
}

// ── Navigation Core ──
function showPage(name) {
  const sanitizedName = escapeHTML(name);
  const targetPage = document.getElementById('page-' + sanitizedName);
  const targetBtn = document.querySelector(`.nav-btn[data-page="${sanitizedName}"]`);
  
  if (!targetPage) return;

  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  targetPage.classList.add('active');
  
  document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
  if (targetBtn) targetBtn.classList.add('active');
  
  if (sanitizedName === 'history') loadHistory();
  if (sanitizedName === 'stats')   loadStats();
}

// ── Main Scan Execution ──
async function scanUrl() {
  const urlInput = document.getElementById('urlInput').value.trim();
  if (!urlInput) { alert('Validation Failure: Target input register is empty.'); return; }
  if (!urlInput.startsWith('http://') && !urlInput.startsWith('https://')) { 
    alert('Validation Failure: Target layout must begin with http:// or https://'); 
    return; 
  }

  // Trigger Skeleton State Visibility
  document.getElementById('loadingSection').style.display = 'block';
  document.getElementById('resultSection').style.display  = 'none';

  try {
    const resp = await fetchWithTimeout(`${API_BASE}/predict`, {
      method : 'POST',
      headers: {'Content-Type':'application/json'},
      body   : JSON.stringify({ url: urlInput }),
      timeout: 25000 // 25 seconds extraction ceiling
    });

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.error || 'Server processing error.');
    }

    const data = await resp.json();
    displayResult(data);

  } catch (err) {
    if (err.name === 'AbortError') {
      alert('Execution Aborted: Network connection timed out.');
    } else {
      alert(`Execution Aborted: ${escapeHTML(err.message)}`);
    }
  } finally {
    document.getElementById('loadingSection').style.display = 'none';
  }
}

// ── Threat Representation Processing ──
function displayResult(data) {
  const isPhishing = data.prediction === 'PHISHING';
  const card       = document.getElementById('resultCard');
  card.className   = 'result-card mb-4 ' + (isPhishing ? 'phishing' : 'legitimate');

  const badge = document.getElementById('verdictBadge');
  badge.textContent  = isPhishing ? '🚨 SYSTEM THREAT DETECTED' : '✅ DOMAIN VERIFIED SECURE';
  badge.className    = 'verdict-title ' + (isPhishing ? 'text-danger-neon' : 'text-legit-neon');

  const riskBadge = document.getElementById('riskBadge');
  const cleanRisk = escapeHTML(data.risk_level);
  riskBadge.textContent = cleanRisk;
  riskBadge.className   = 'risk-badge risk-' + cleanRisk;

  document.getElementById('confidenceText').textContent = Number(data.confidence) + '%';
  document.getElementById('resultUrl').textContent      = 'SIGNATURE FOOTPRINT // ' + escapeHTML(data.url);

  // ── High Contrast Indicator Chart ──
  if (confChart) confChart.destroy();
  const ctx  = document.getElementById('confidenceChart').getContext('2d');
  const conf = Number(data.confidence);
  
  confChart  = new Chart(ctx, {
    type: 'doughnut',
    data: {
      datasets:[{
        data: [conf, 100 - conf],
        backgroundColor: [isPhishing ? '#ff3333' : '#00ff66', 'rgba(255, 255, 255, 0.04)'],
        borderWidth: 0,
      }]
    },
    options:{
      cutout: '84%',
      responsive: true,
      maintainAspectRatio: false,
      plugins:{
        legend:{display:false},
        tooltip:{enabled: false}
      },
    },
  });

  // ── Telemetry List Population ──
  const tbody = document.getElementById('featureTableBody');
  tbody.innerHTML = '';
  const feats = data.features || {};

  Object.entries(FEAT_META).forEach(([key, meta]) => {
    const val = feats[key];
    if (val === undefined || val === null) return;
    
    let cls = '';
    if (meta.good === 1 && val === 1) cls = 'val-good';
    if (meta.good === 1 && val === 0) cls = 'val-bad';
    if (meta.good === 0 && val === 1) cls = 'val-bad';
    if (meta.good === 0 && val === 0) cls = 'val-good';

    const meaning = getMeaning(key, val);
    tbody.innerHTML += `
      <tr>
        <td class="text-white-50">${escapeHTML(meta.label)}</td>
        <td class="${cls}">${Number(val)}</td>
        <td class="text-muted font-mono small">${escapeHTML(meaning)}</td>
      </tr>`;
  });

  document.getElementById('resultSection').style.display = 'block';
  document.getElementById('resultSection').scrollIntoView({behavior:'smooth'});
}

function getMeaning(key, val) {
  const meanings = {
    has_https:              v => v===1 ? 'Session data is encrypted natively' : '⚠️ Unencrypted context — active cleartext vulnerability',
    is_ip_address:          v => v===1 ? '⚠️ Bypassing standard DNS naming trees' : 'Standard mapped pointer structure',
    url_shortener_used:     v => v===1 ? '⚠️ Obfuscating downstream location registers' : 'Transparent endpoint validation',
    suspicious_keyword_cnt: v => v===0 ? 'Zero targeted vectors located' : `⚠️ Found ${v} keyword targets inside token set`,
    has_login_form:         v => v===1 ? 'Interrogating for identification parameters' : 'Passive layout — zero profile inputs found',
    redirect_count:         v => v===0 ? 'Zero forwarding hops observed' : v===1 ? 'Single forwarding hop' : `⚠️ Transiting ${v} automated sequence jumps`,
    has_valid_ssl:          v => v===1 ? 'Valid cryptographic root verified' : '⚠️ Missing or unverified root certificates',
    domain_age_days:        v => v<0 ? 'Indeterminate timestamp metadata' : v<30 ? `⚠️ High-risk registration timeline: only ${v} days!` : `Active historical footprint verified at ${v} days`,
    form_action_external:   v => v===1 ? '⚠️ Destination routing leads outside host asset tree' : 'Form targets remain inside local infrastructure',
    right_click_disabled:   v => v===1 ? '⚠️ Forcing modification of core browser mechanics' : 'Unmodified user-interface baseline',
    has_hidden_iframe:      v => v===1 ? '⚠️ Background code block loading undetected assets' : 'Isolated standard view model',
    meta_refresh_redirect:  v => v===1 ? '⚠️ Direct refresh hijack detected' : 'Standard static visibility index',
    favicon_external:       v => v===1 ? '⚠️ Asset spoofing indicator located' : 'Cohesive icon origin framework',
  };
  return meanings[key] ? meanings[key](val) : '';
}

// ── Historic Logs Population ──
async function loadHistory() {
  const tbody = document.getElementById('historyTableBody');
  tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted font-mono py-4">Querying system index registers...</td></tr>';
  
  try {
    const r = await fetchWithTimeout(`${API_BASE}/history?limit=50`, { timeout: 15000 });
    const d = await r.json();
    tbody.innerHTML = '';
    
    if (!d.records || !d.records.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted font-mono py-4">Database ledger is currently unpopulated.</td></tr>';
      return;
    }
    
    d.records.forEach((rec, i) => {
      const isPh = rec.prediction === 'PHISHING';
      const ts   = new Date(rec.timestamp).toLocaleString();
      const cleanRisk = escapeHTML(rec.risk_level);
      tbody.innerHTML += `
        <tr>
          <td class="font-mono text-white-50">${i+1}</td>
          <td class="text-truncate font-mono text-muted" style="max-width:240px" title="${escapeHTML(rec.url)}">${escapeHTML(rec.url)}</td>
          <td><span class="${isPh?'badge-ph':'badge-lg'}">${isPh?'PHISHING':'LEGITIMATE'}</span></td>
          <td class="font-mono fw-bold text-white">${Number(rec.confidence)}%</td>
          <td><span class="risk-badge risk-${cleanRisk}">${cleanRisk}</span></td>
          <td class="text-muted font-mono small">${escapeHTML(ts)}</td>
        </tr>`;
    });
  } catch(e) { 
    tbody.innerHTML = `<tr><td colspan="6" class="text-danger font-mono text-center py-4">Ledger Retrieval Failure: ${escapeHTML(e.message)}</td></tr>`; 
  }
}

// ── Analytics Metrics Aggregation ──
async function loadStats() {
  try {
    const r = await fetchWithTimeout(`${API_BASE}/stats`, { timeout: 15000 });
    const d = await r.json();
    
    document.getElementById('statTotal').textContent    = parseInt(d.total) || 0;
    document.getElementById('statPhishing').textContent = parseInt(d.phishing_count) || 0;
    document.getElementById('statLegit').textContent    = parseInt(d.legitimate_count) || 0;

    if (statsChart) statsChart.destroy();
    const ctx = document.getElementById('statsChart').getContext('2d');
    
    statsChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Malicious Threats', 'Verified Legitimate'],
        datasets: [{
          data: [parseInt(d.phishing_count) || 0, parseInt(d.legitimate_count) || 0],
          backgroundColor: ['#ff3333', '#00ff66'],
          borderWidth: 0,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color: '#7a8599',
              font: { family: 'ui-monospace, monospace', size: 11 }
            }
          }
        }
      }
    });
  } catch(e) { 
    console.error('Metrics engine exception observed:', e); 
  }
}

// ── Event Wiring (CSP-safe, no inline handlers) ──
document.addEventListener('DOMContentLoaded', () => {
  // Bind Nav Tabs dynamically using dataset properties
  document.querySelectorAll('.nav-btn[data-page]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      showPage(btn.dataset.page);
    });
  });

  // Matches id="brandLink" from index.html safely
  const brand = document.getElementById('brandLink');
  if (brand) {
    brand.addEventListener('click', (e) => { 
      e.preventDefault(); 
      showPage('home'); 
    });
  }

  // Bind primary scan action button
  const scanBtn = document.getElementById('scanBtn');
  if (scanBtn) {
    scanBtn.addEventListener('click',(e) => {
      e.preventDefault();
      scanUrl(e);
    });
  }

  // Bind keydown events inside the input register
  const urlInput = document.getElementById('urlInput');
  if (urlInput) {
    urlInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        scanUrl();
      }
    });
  }

  // Bind example target footprint links cleanly using dataset properties
  document.querySelectorAll('.badge-link[data-url]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      if (urlInput) {
        urlInput.value = btn.dataset.url;
      }
    });
  });
});