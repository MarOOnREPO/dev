const API_BASE = window.location.origin;

let player = null;
let hls = null;
let currentTorrentId = null;
let statusInterval = null;
let isOnline = navigator.onLine;

// ── State Management (from frontend-mobile-development skill) ──
const State = {
  torrents: [],
  current: null,
  isPlaying: false,
  isLoading: false,
  error: null,
  set(key, val) {
    this[key] = val;
    render();
  },
};

// ── Offline Detection ──
window.addEventListener('online', () => { isOnline = true; showToast('Back online', 'success'); });
window.addEventListener('offline', () => { isOnline = false; showToast('Offline mode — cached assets available', 'warning'); });

function showToast(msg, type = 'info') {
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

// ── Formatters ──
function formatBytes(b) {
  if (!b) return '—';
  const units = ['B','KB','MB','GB'];
  let i = 0;
  while (b >= 1024 && i < units.length - 1) { b /= 1024; i++; }
  return `${b.toFixed(1)} ${units[i]}/s`;
}

function formatTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleTimeString();
}

// ── DOM refs ──
const magnetInput = document.getElementById('magnetInput');
const addBtn = document.getElementById('addBtn');
const torrentsList = document.getElementById('torrentsList');
const playerSection = document.getElementById('playerSection');
const statusText = document.getElementById('statusText');
const dlProgress = document.getElementById('dlProgress');
const tcProgress = document.getElementById('tcProgress');
const speedText = document.getElementById('speedText');
const audioSelect = document.getElementById('audioSelect');
const subSelect = document.getElementById('subSelect');

// ── Skeleton Loading (from ui-design skill) ──
function renderSkeleton(count = 3) {
  let html = '';
  for (let i = 0; i < count; i++) {
    html += `
      <div class="torrent-card skeleton">
        <div class="skeleton-icon"></div>
        <div class="skeleton-lines">
          <div class="skeleton-line" style="width:60%"></div>
          <div class="skeleton-line" style="width:40%"></div>
        </div>
      </div>`;
  }
  torrentsList.innerHTML = html;
}

// ── API ──
async function fetchTorrents() {
  try {
    const res = await fetch(`${API_BASE}/api/torrents`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('fetchTorrents:', err);
    return [];
  }
}

async function fetchTorrent(id) {
  try {
    const res = await fetch(`${API_BASE}/api/torrents/${id}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('fetchTorrent:', err);
    return null;
  }
}

// ── Render ──
function renderTorrents(torrents) {
  if (torrents.length === 0 && State.isLoading) {
    renderSkeleton();
    return;
  }
  if (torrents.length === 0) {
    torrentsList.innerHTML = '<div class="empty-state">No torrents yet. Paste a magnet link above.</div>';
    return;
  }

  torrentsList.innerHTML = '';
  torrents.forEach(t => {
    const card = document.createElement('div');
    card.className = `torrent-card ${t.id === currentTorrentId ? 'active' : ''}`;

    let statusClass = 'status-pending';
    if (t.status === 'downloading') statusClass = 'status-downloading';
    if (t.status === 'transcoding') statusClass = 'status-transcoding';
    if (t.status === 'ready') statusClass = 'status-ready';
    if (t.status === 'error') statusClass = 'status-error';

    card.innerHTML = `
      <div class="icon">🎬</div>
      <div class="info">
        <div class="name">${escapeHtml(t.name || 'Loading...')}</div>
        <div class="meta ${statusClass}">
          ${t.status} · DL: ${t.progress}% · TC: ${Math.round(t.transcodeProgress || 0)}%
        </div>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" style="width:${t.status === 'ready' ? 100 : t.progress}%"></div>
      </div>
      <div class="actions">
        ${t.status === 'ready'
          ? `<button class="btn-small btn-play" onclick="playTorrent('${t.id}')">▶ Play</button>`
          : `<span class="btn-small btn-wait">⏳ ${t.status}</span>`}
        <button class="btn-small danger" onclick="removeTorrent('${t.id}')">✕</button>
      </div>
    `;
    torrentsList.appendChild(card);
  });
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

async function render() {
  const list = await fetchTorrents();
  State.torrents = list;
  renderTorrents(list);

  if (currentTorrentId) {
    const t = await fetchTorrent(currentTorrentId);
    if (t) updatePlayerInfo(t);
  }
}

function updatePlayerInfo(t) {
  statusText.textContent = t.status;
  statusText.className = '';
  if (t.status === 'ready') statusText.className = 'status-ready';
  if (t.status === 'error') statusText.className = 'status-error';
  if (t.status === 'transcoding') statusText.className = 'status-transcoding';

  dlProgress.textContent = t.progress + '%';
  tcProgress.textContent = Math.round(t.transcodeProgress || 0) + '%';
  speedText.textContent = formatBytes(t.downloadSpeed);

  if (t.probe?.audioTracks && audioSelect.options.length <= 1) {
    audioSelect.innerHTML = '';
    t.probe.audioTracks.forEach((track, i) => {
      const opt = document.createElement('option');
      opt.value = i;
      opt.textContent = `${track.title} (${track.codec}, ${track.channels}ch)`;
      audioSelect.appendChild(opt);
    });
  }

  if (t.extractedSubtitles && subSelect.options.length <= 1) {
    subSelect.innerHTML = '<option value="">Off</option>';
    t.extractedSubtitles.forEach((sub) => {
      const opt = document.createElement('option');
      opt.value = sub.name;
      opt.textContent = sub.name;
      subSelect.appendChild(opt);
    });
    if (t.probe?.subtitleStreams) {
      t.probe.subtitleStreams.forEach((sub, i) => {
        const opt = document.createElement('option');
        opt.value = `embedded:${i}`;
        opt.textContent = `[Embedded] ${sub.title || sub.language}`;
        subSelect.appendChild(opt);
      });
    }
  }
}

// ── Actions ──

addBtn.addEventListener('click', async () => {
  const uri = magnetInput.value.trim();
  if (!uri) return showToast('Paste a magnet link first', 'warning');
  if (!uri.startsWith('magnet:?')) return showToast('Invalid magnet link', 'danger');

  addBtn.disabled = true;
  addBtn.textContent = 'Loading...';
  State.set('isLoading', true);

  try {
    const res = await fetch(`${API_BASE}/api/torrents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ magnetUri: uri }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);

    magnetInput.value = '';
    showToast('Torrent added!', 'success');
    startPolling();
  } catch (err) {
    showToast(err.message, 'danger');
  } finally {
    addBtn.disabled = false;
    addBtn.textContent = '▶ Load Torrent';
    State.set('isLoading', false);
  }
});

async function startPolling() {
  if (statusInterval) clearInterval(statusInterval);
  statusInterval = setInterval(render, 2000);
  await render();
}

window.playTorrent = async function (id) {
  currentTorrentId = id;
  playerSection.style.display = 'block';
  State.set('current', id);

  const t = await fetchTorrent(id);
  if (!t) return showToast('Torrent not found', 'danger');
  updatePlayerInfo(t);

  const streamUrl = `${API_BASE}/api/stream/${id}/playlist.m3u8`;

  if (hls) { hls.destroy(); hls = null; }
  if (player) { player.dispose(); player = null; }

  const videoEl = document.getElementById('videoPlayer');

  if (Hls.isSupported()) {
    hls = new Hls({
      enableWorker: true,
      lowLatencyMode: false,
      backBufferLength: 90,
      maxBufferLength: 30,
      maxMaxBufferLength: 60,
    });
    hls.loadSource(streamUrl);
    hls.attachMedia(videoEl);
    hls.on(Hls.Events.MANIFEST_PARSED, () => {
      videoEl.play().catch(() => {});
      State.set('isPlaying', true);
    });
    hls.on(Hls.Events.ERROR, (event, data) => {
      if (data.fatal) {
        console.error('HLS fatal error:', data.type, data.details);
        showToast('Stream error: ' + data.type, 'danger');
      }
    });
  } else if (videoEl.canPlayType('application/vnd.apple.mpegurl')) {
    videoEl.src = streamUrl;
    videoEl.addEventListener('loadedmetadata', () => {
      videoEl.play().catch(() => {});
      State.set('isPlaying', true);
    });
  } else {
    showToast('HLS not supported in this browser', 'danger');
    return;
  }

  player = videojs(videoEl, {
    html5: {
      vhs: {
        overrideNative: true,
        limitRenditionByPlayerDimensions: true,
      },
    },
  });

  playerSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
};

window.removeTorrent = async function (id) {
  if (!confirm('Remove this torrent?')) return;
  try {
    const res = await fetch(`${API_BASE}/api/torrents/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to remove');
    if (currentTorrentId === id) {
      currentTorrentId = null;
      playerSection.style.display = 'none';
      if (player) { player.dispose(); player = null; }
      if (hls) { hls.destroy(); hls = null; }
    }
    showToast('Torrent removed', 'success');
    render();
  } catch (err) {
    showToast(err.message, 'danger');
  }
};

audioSelect.addEventListener('change', () => {
  if (!hls) return;
  const idx = parseInt(audioSelect.value);
  hls.audioTrack = idx;
});

subSelect.addEventListener('change', () => {
  if (!player) return;
  const val = subSelect.value;
  const tracks = player.textTracks();
  for (let i = tracks.length - 1; i >= 0; i--) {
    player.removeRemoteTextTrack(tracks[i]);
  }
  if (!val) return;
  if (val.startsWith('embedded:')) return;
  const subUrl = `${API_BASE}/api/subs/${currentTorrentId}/${encodeURIComponent(val)}`;
  player.addRemoteTextTrack({
    kind: 'subtitles',
    src: subUrl,
    srclang: 'en',
    label: val,
    default: true,
  }, true);
});

// ── Keyboard shortcut (desktop) ──
magnetInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') addBtn.click();
});

// ── Init ──
renderSkeleton();
startPolling();
