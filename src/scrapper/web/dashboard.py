"""Inline HTML dashboard for the scrapper web UI."""

DASHBOARD_HTML = """\
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Scrapper — Lead Dashboard</title>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
       background: #f5f7fa; color: #1a1a2e; line-height: 1.5; }
.container { max-width: 1400px; margin: 0 auto; padding: 16px; }
header { background: #2f5496; color: #fff; padding: 16px 0; margin-bottom: 20px; }
header .container { display: flex; justify-content: space-between; align-items: center; }
header h1 { font-size: 1.4rem; font-weight: 600; }
.header-actions { display: flex; gap: 8px; }
.btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer;
       font-size: 0.85rem; font-weight: 500; transition: opacity 0.2s; }
.btn:hover { opacity: 0.85; }
.btn-primary { background: #fff; color: #2f5496; }
.btn-success { background: #27ae60; color: #fff; }
.btn-outline { background: transparent; color: #fff; border: 1px solid rgba(255,255,255,0.4); }

/* Stats cards */
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
              gap: 12px; margin-bottom: 20px; }
.stat-card { background: #fff; border-radius: 8px; padding: 16px;
             box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.stat-card .label { font-size: 0.75rem; text-transform: uppercase; color: #666;
                    letter-spacing: 0.5px; margin-bottom: 4px; }
.stat-card .value { font-size: 1.6rem; font-weight: 700; color: #2f5496; }
.stat-card .sub { font-size: 0.75rem; color: #888; margin-top: 2px; }

/* Controls */
.controls { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; align-items: center; }
.search-input { padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px;
                font-size: 0.9rem; width: 280px; }
.search-input:focus { outline: none; border-color: #2f5496; }
select { padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px;
         font-size: 0.9rem; background: #fff; }
.controls .right { margin-left: auto; display: flex; gap: 8px; }

/* Table */
.table-wrap { background: #fff; border-radius: 8px; overflow: hidden;
              box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
thead th { background: #f8f9fa; padding: 10px 12px; text-align: left;
           font-weight: 600; color: #555; border-bottom: 2px solid #e9ecef;
           white-space: nowrap; position: sticky; top: 0; }
tbody td { padding: 8px 12px; border-bottom: 1px solid #f0f0f0;
           max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
tbody tr:hover { background: #f8f9fb; }
.td-phone, .td-email { font-family: monospace; font-size: 0.8rem; }
.has-data { color: #27ae60; }
.no-data { color: #ccc; }

/* Status bar */
.status-bar { display: flex; justify-content: space-between; align-items: center;
              padding: 8px 0; font-size: 0.8rem; color: #888; }
.refresh-indicator { display: inline-block; width: 8px; height: 8px; border-radius: 50%;
                     background: #27ae60; margin-right: 6px; }
.refresh-indicator.stale { background: #e74c3c; }

/* Responsive */
@media (max-width: 768px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .controls { flex-direction: column; }
  .search-input { width: 100%; }
  .controls .right { margin-left: 0; }
  .table-wrap { overflow-x: auto; }
}
</style>
</head>
<body>
<header>
  <div class="container">
    <h1>Scrapper Dashboard</h1>
    <div class="header-actions">
      <button class="btn btn-success" onclick="triggerDiscover()">Discover</button>
      <button class="btn btn-outline" onclick="refreshAll()">Refresh</button>
    </div>
  </div>
</header>

<div class="container">
  <!-- Stats -->
  <div class="stats-grid" id="stats-grid">
    <div class="stat-card"><div class="label">Total Leads</div><div class="value" id="s-leads">-</div></div>
    <div class="stat-card"><div class="label">Candidates</div><div class="value" id="s-candidates">-</div></div>
    <div class="stat-card"><div class="label">With Phone</div><div class="value" id="s-phone">-</div><div class="sub" id="s-phone-pct"></div></div>
    <div class="stat-card"><div class="label">With Email</div><div class="value" id="s-email">-</div><div class="sub" id="s-email-pct"></div></div>
    <div class="stat-card"><div class="label">With INN</div><div class="value" id="s-inn">-</div><div class="sub" id="s-inn-pct"></div></div>
    <div class="stat-card"><div class="label">Queue (NEW)</div><div class="value" id="s-queue-new">0</div></div>
  </div>

  <!-- Controls -->
  <div class="controls">
    <input class="search-input" id="search" type="text" placeholder="Search by name, INN, or address...">
    <select id="source-filter">
      <option value="">All sources</option>
      <option value="yandex_maps">Yandex Maps</option>
      <option value="twogis">2GIS</option>
      <option value="zakupki">Zakupki</option>
      <option value="fake">Fake</option>
    </select>
    <div class="right">
      <button class="btn btn-primary" onclick="exportLeads('xlsx')">Export XLSX</button>
      <button class="btn btn-outline" style="color:#333;border-color:#ccc" onclick="exportLeads('csv')">CSV</button>
      <button class="btn btn-outline" style="color:#333;border-color:#ccc" onclick="exportLeads('json')">JSON</button>
    </div>
  </div>

  <!-- Table -->
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Company</th><th>INN</th><th>Phone</th><th>Email</th>
          <th>Address</th><th>CEO</th><th>Website</th><th>Revenue</th><th>Source</th>
        </tr>
      </thead>
      <tbody id="leads-body">
        <tr><td colspan="9" style="text-align:center;padding:40px;color:#999">Loading...</td></tr>
      </tbody>
    </table>
  </div>

  <!-- Status -->
  <div class="status-bar">
    <span><span class="refresh-indicator" id="refresh-dot"></span>
      <span id="status-text">Loading...</span></span>
    <span id="last-refresh"></span>
  </div>
</div>

<script>
let autoRefreshId = null;
const API_BASE = '';

async function apiFetch(url) {
  const resp = await fetch(API_BASE + url);
  if (resp.status === 401) { location.reload(); return null; }
  if (!resp.ok) { console.error('API error', resp.status); return null; }
  return resp.json();
}

async function loadStats() {
  const data = await apiFetch('/stats');
  if (!data) return;
  const el = (id) => document.getElementById(id);
  el('s-leads').textContent = data.leads || 0;
  el('s-candidates').textContent = data.candidates || 0;
  const fr = data.fill_rates || {};
  const total = fr.total || 0;
  el('s-phone').textContent = fr.has_phone || 0;
  el('s-email').textContent = fr.has_email || 0;
  el('s-inn').textContent = fr.has_inn || 0;
  if (total > 0) {
    el('s-phone-pct').textContent = Math.round((fr.has_phone||0)/total*100) + '%';
    el('s-email-pct').textContent = Math.round((fr.has_email||0)/total*100) + '%';
    el('s-inn-pct').textContent = Math.round((fr.has_inn||0)/total*100) + '%';
  }
  el('s-queue-new').textContent = (data.queue || {})['NEW'] || 0;
}

async function loadLeads() {
  const search = document.getElementById('search').value;
  const source = document.getElementById('source-filter').value;
  let url = '/api/leads?limit=500';
  if (search) url += '&search=' + encodeURIComponent(search);
  if (source) url += '&source=' + encodeURIComponent(source);
  const data = await apiFetch(url);
  if (!data) return;
  renderTable(data);
  document.getElementById('status-text').textContent = data.length + ' leads loaded';
  document.getElementById('last-refresh').textContent = 'Updated: ' + new Date().toLocaleTimeString();
  document.getElementById('refresh-dot').className = 'refresh-indicator';
}

function renderTable(leads) {
  const tbody = document.getElementById('leads-body');
  if (!leads.length) {
    tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:40px;color:#999">No leads found</td></tr>';
    return;
  }
  tbody.innerHTML = leads.map(l => `<tr>
    <td title="${esc(l.company_name)}">${esc(l.company_name)}</td>
    <td>${cell(l.inn)}</td>
    <td class="td-phone">${cell(l.phone)}</td>
    <td class="td-email">${cell(l.email)}</td>
    <td title="${esc(l.address)}">${cell(l.address)}</td>
    <td>${cell(l.ceo)}</td>
    <td>${l.website ? '<a href="'+esc(l.website)+'" target="_blank">'+shortUrl(l.website)+'</a>' : span('-','no-data')}</td>
    <td>${cell(l.revenue)}</td>
    <td>${cell(l.discovery_source)}</td>
  </tr>`).join('');
}

function esc(s) { if (!s) return ''; const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
function cell(v) { return v ? span(esc(v), 'has-data') : span('-', 'no-data'); }
function span(t, cls) { return '<span class="'+cls+'">'+t+'</span>'; }
function shortUrl(u) { try { return new URL(u).hostname; } catch(e) { return u; } }

function exportLeads(fmt) {
  window.open('/export?format=' + fmt, '_blank');
}

async function triggerDiscover() {
  const source = prompt('Source (yandex_maps, twogis, zakupki):', 'yandex_maps');
  if (!source) return;
  const region = prompt('Region (e.g. moscow,spb):', 'moscow');
  if (region === null) return;
  const resp = await fetch('/runs/discover?source='+encodeURIComponent(source)+'&region='+encodeURIComponent(region), {method:'POST'});
  if (!resp.ok) { const e = await resp.json(); alert('Error: ' + (e.detail || resp.status)); return; }
  const data = await resp.json();
  alert('Discovered ' + data.new_candidates + ' new candidates, ' + data.tasks_created + ' tasks created');
  refreshAll();
}

async function refreshAll() {
  await Promise.all([loadStats(), loadLeads()]);
}

// Debounced search
let searchTimer;
document.getElementById('search').addEventListener('input', () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadLeads, 400);
});
document.getElementById('source-filter').addEventListener('change', loadLeads);

// Initial load + auto-refresh
refreshAll();
autoRefreshId = setInterval(refreshAll, 60000);
</script>
</body>
</html>
"""
