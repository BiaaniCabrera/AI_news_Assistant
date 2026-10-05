/**
 * HIPPO AI NEWS TRACKER - CLIENT CONTROLLER
 * Reactive state management, persistent bookmarking, and live pipeline sync.
 */

// Application State
const state = {
  articles: [],
  filteredArticles: [],
  selectedArticle: null,
  activeFilter: 'all', // 'all' | '24h' | 'saved' | 'Agents' | 'LLMs' | 'Robotics'
  selectedSource: null, // null | "Ben's Bites" | "The AI Rundown"
  searchQuery: '',
  isSyncing: false,
  lastSync: null
};

// DOM References
const elements = {
  articlesGrid: document.getElementById('articlesGrid'),
  emptyState: document.getElementById('emptyState'),
  btnResetFilters: document.getElementById('btnResetFilters'),
  streamCounter: document.getElementById('streamCounter'),
  hero24hCount: document.getElementById('hero24hCount'),
  savedCountBadge: document.getElementById('savedCountBadge'),
  badgeDot24h: document.getElementById('badgeDot24h'),
  searchInput: document.getElementById('searchInput'),
  searchClearBtn: document.getElementById('searchClearBtn'),
  searchFeedbackBadge: document.getElementById('searchFeedbackBadge'),
  sourcesAvatarRow: document.getElementById('sourcesAvatarRow'),
  categoryTabs: document.getElementById('categoryTabs'),
  syncStatusText: document.getElementById('syncStatusText'),
  btnSyncHeader: document.getElementById('btnSyncHeader'),
  heroTagBtn: document.getElementById('heroTagBtn'),
  heroExploreBtn: document.getElementById('heroExploreBtn'),
  heroFilter24hBtn: document.getElementById('heroFilter24hBtn'),
  tabNavAll: document.getElementById('tabNavAll'),
  tabNav24h: document.getElementById('tabNav24h'),
  tabNavSaved: document.getElementById('tabNavSaved'),
  toastContainer: document.getElementById('toastContainer')
};

// ==========================================================================
// Initialization & Data Loading
// ==========================================================================
async function init() {
  setupEventListeners();
  await loadArticles();
}

async function loadArticles() {
  try {
    const res = await fetch('/api/articles');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    state.articles = data.articles || [];
    state.lastSync = data.last_sync;

    // Synchronize localStorage backup for offline/speed
    syncLocalBookmarks();

    updateMetrics();
    renderSourcesRow();
    applyFilters();
  } catch (err) {
    console.error('Failed loading articles:', err);
    showToast('⚠️ Could not connect to API server.');
  }
}

// ==========================================================================
// Bookmarks Sync (Dual Persistence: Backend + LocalStorage Mirror)
// ==========================================================================
function syncLocalBookmarks() {
  const localSaved = JSON.parse(localStorage.getItem('hippo_saved_ids') || '[]');
  const localSet = new Set(localSaved);

  state.articles.forEach(art => {
    if (art.is_saved) {
      localSet.add(art.id);
    } else if (localSet.has(art.id)) {
      // Restore from local storage if saved on client
      art.is_saved = true;
    }
  });

  localStorage.setItem('hippo_saved_ids', JSON.stringify(Array.from(localSet)));
}

async function toggleBookmark(articleId, event) {
  if (event) event.stopPropagation();

  const article = state.articles.find(a => a.id === articleId);
  if (!article) return;

  const newState = !article.is_saved;
  article.is_saved = newState;
  article.saved_at = newState ? new Date().toISOString() : null;

  // Update localStorage mirror immediately
  const localSaved = new Set(JSON.parse(localStorage.getItem('hippo_saved_ids') || '[]'));
  if (newState) {
    localSaved.add(articleId);
  } else {
    localSaved.delete(articleId);
  }
  localStorage.setItem('hippo_saved_ids', JSON.stringify(Array.from(localSaved)));

  // Update UI optimistically
  updateMetrics();
  applyFilters();
  if (state.selectedArticle && state.selectedArticle.id === articleId) {
    renderInspector(article);
  }

  showToast(newState ? '♥ Saved to Bookmarks' : 'Removed from Bookmarks');

  // Backend Sync
  try {
    await fetch('/api/bookmark', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: articleId, is_saved: newState })
    });
  } catch (e) {
    console.warn('Backend bookmark sync warning:', e);
  }
}

// ==========================================================================
// Filtering & Search
// ==========================================================================
function applyFilters() {
  let list = [...state.articles];

  // Source Filter
  if (state.selectedSource) {
    list = list.filter(a => a.source.name === state.selectedSource);
  }

  // Tab Filter
  if (state.activeFilter === '24h') {
    list = list.filter(a => a.is_last_24h);
  } else if (state.activeFilter === 'saved') {
    list = list.filter(a => a.is_saved);
  } else if (['Agents', 'LLMs', 'Robotics'].includes(state.activeFilter)) {
    list = list.filter(a => a.tags && a.tags.includes(state.activeFilter));
  }

  // Search Query (Multi-term matching with relevance scoring)
  const qRaw = (state.searchQuery || '').trim();
  if (qRaw) {
    const terms = qRaw.toLowerCase().split(/\s+/).filter(Boolean);
    const scoredList = [];

    list.forEach(a => {
      const titleLower = (a.title || '').toLowerCase();
      const tagsLower = (a.tags || []).map(t => t.toLowerCase()).join(' ');
      const summaryLower = (a.summary || '').toLowerCase();
      const authorLower = (a.author || '').toLowerCase();
      const sourceLower = (a.source && a.source.name || '').toLowerCase();

      // Verify that every term matches at least one field
      const matchesAll = terms.every(t => 
        titleLower.includes(t) || tagsLower.includes(t) || summaryLower.includes(t) || authorLower.includes(t) || sourceLower.includes(t)
      );

      if (matchesAll) {
        let score = 0;
        terms.forEach(t => {
          if (titleLower.includes(t)) score += 10;
          if (tagsLower.includes(t)) score += 5;
          if (authorLower.includes(t) || sourceLower.includes(t)) score += 3;
          if (summaryLower.includes(t)) score += 1;
        });
        scoredList.push({ article: a, score });
      }
    });

    scoredList.sort((a, b) => b.score - a.score);
    list = scoredList.map(item => item.article);
  }

  state.filteredArticles = list;

  // Search feedback badge in dispatches header
  if (elements.searchFeedbackBadge) {
    if (qRaw) {
      elements.searchFeedbackBadge.style.display = 'inline-flex';
      elements.searchFeedbackBadge.innerHTML = `
        <span>Search: "<strong>${escapeHtml(qRaw)}</strong>" (${list.length} results)</span>
        <button class="search-clear-tag" id="clearSearchTag" title="Clear search">Clear</button>
      `;
      const clearTag = document.getElementById('clearSearchTag');
      if (clearTag) {
        clearTag.addEventListener('click', () => {
          elements.searchInput.value = '';
          state.searchQuery = '';
          if (elements.searchClearBtn) elements.searchClearBtn.style.display = 'none';
          applyFilters();
        });
      }
    } else {
      elements.searchFeedbackBadge.style.display = 'none';
    }
  }

  renderArticlesGrid();
}

function updateMetrics() {
  const total = state.articles.length;
  const fresh24h = state.articles.filter(a => a.is_last_24h).length;
  const saved = state.articles.filter(a => a.is_saved).length;

  elements.hero24hCount.textContent = fresh24h;
  elements.savedCountBadge.textContent = saved;
  elements.streamCounter.textContent = `${state.filteredArticles.length || total} articles`;

  // Status text
  if (state.lastSync) {
    const syncDate = new Date(state.lastSync);
    const timeStr = syncDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    elements.syncStatusText.textContent = `Synced at ${timeStr}`;
  }
}

// ==========================================================================
// Rendering Functions
// ==========================================================================
function renderSourcesRow() {
  const counts = {};
  state.articles.forEach(a => {
    const s = a.source.name;
    counts[s] = (counts[s] || 0) + 1;
  });

  const sources = [
    { name: 'All Sources', id: null, icon: '✨', count: state.articles.length },
    { name: "Ben's Bites", id: "Ben's Bites", icon: '⚡', count: counts["Ben's Bites"] || 0 },
    { name: 'The AI Rundown', id: 'The AI Rundown', icon: '📰', count: counts['The AI Rundown'] || 0 },
    { name: 'Reddit AI', id: 'Reddit AI', icon: '🤖', count: 0, tag: 'Coming Soon' }
  ];

  elements.sourcesAvatarRow.innerHTML = sources.map(s => `
    <div class="source-avatar-pill ${state.selectedSource === s.id ? 'active' : ''}" data-source="${s.id || ''}">
      <div class="source-avatar-circle">${s.icon}</div>
      <div class="source-pill-info">
        <span class="source-pill-name">${s.name}</span>
        <span class="source-pill-count">${s.tag ? s.tag : `${s.count} posts`}</span>
      </div>
    </div>
  `).join('');

  // Add click handlers
  elements.sourcesAvatarRow.querySelectorAll('.source-avatar-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      const src = pill.getAttribute('data-source') || null;
      state.selectedSource = src;
      renderSourcesRow();
      applyFilters();
    });
  });
}

function renderArticlesGrid() {
  const list = state.filteredArticles;

  if (list.length === 0) {
    elements.articlesGrid.innerHTML = '';
    elements.emptyState.style.display = 'block';
    elements.streamCounter.textContent = '0 articles';
    return;
  }

  elements.emptyState.style.display = 'none';
  elements.streamCounter.textContent = `${list.length} articles`;

  elements.articlesGrid.innerHTML = list.map(art => {
    const timeAgo = formatTimeAgo(art.published_at);
    const releaseDateStr = art.released_date || formatReleaseDate(art.published_at);
    const releaseFullStr = art.released_full || formatReleaseFull(art.published_at);
    const thumb = art.thumbnail_url || '/DesignGuidelines/glitter_logo.png';
    const tagHtml = (art.tags || []).slice(0, 2).map(t => `<span class="tag-pill">${escapeHtml(t)}</span>`).join('');

    const timePillText = art.is_last_24h 
      ? `🔥 NEW • ${releaseDateStr} (${timeAgo})` 
      : `📅 ${releaseDateStr} • ${timeAgo}`;

    let titleHtml = escapeHtml(art.title);
    let excerptHtml = escapeHtml(art.summary);

    // Highlight search keywords if searching
    const qRaw = (state.searchQuery || '').trim();
    if (qRaw) {
      const terms = qRaw.split(/\s+/).filter(Boolean);
      terms.forEach(term => {
        const regex = new RegExp(`(${term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        titleHtml = titleHtml.replace(regex, '<mark class="search-highlight">$1</mark>');
        excerptHtml = excerptHtml.replace(regex, '<mark class="search-highlight">$1</mark>');
      });
    }

    return `
      <article class="article-card" data-id="${art.id}" data-url="${escapeHtml(art.url)}">
        <div class="card-media-wrapper">
          <img src="${thumb}" alt="${escapeHtml(art.title)}" class="card-img" loading="lazy" onerror="this.src='/DesignGuidelines/glitter_logo.png'">
          
          <div class="card-time-pill ${art.is_last_24h ? 'fresh' : ''}">
            ${timePillText}
          </div>

          <button class="card-bookmark-btn ${art.is_saved ? 'saved' : ''}" title="${art.is_saved ? 'Remove bookmark' : 'Save article'}" data-bookmark-id="${art.id}">
            ♥
          </button>
        </div>

        <div class="card-content">
          <div class="card-source-author-row">
            <span class="source-badge" style="background: ${art.source.badge_color}22; color: ${art.source.badge_color}; border: 1px solid ${art.source.badge_color}44;">
              ${escapeHtml(art.source.name)}
            </span>
            <span class="author-text">${escapeHtml(art.author || '')}</span>
          </div>

          <div class="card-released-row" title="Exact release timestamp">
            <span class="card-released-icon">🗓</span>
            <span>Released: ${escapeHtml(releaseFullStr)}</span>
          </div>

          <h3 class="card-title">${titleHtml}</h3>
          <p class="card-excerpt">${excerptHtml}</p>

          <div class="card-footer">
            <div class="tags-row">${tagHtml}</div>
            <div class="card-footer-actions">
              <span class="reading-pill">${art.reading_time_mins || 3}m read</span>
              <a href="${escapeHtml(art.url)}" target="_blank" rel="noopener noreferrer" class="card-read-btn" title="Open original article">
                Read ↗
              </a>
            </div>
          </div>
        </div>
      </article>
    `;
  }).join('');

  // Clicking anywhere on card (except bookmark or direct link) opens article
  elements.articlesGrid.querySelectorAll('.article-card').forEach(card => {
    card.addEventListener('click', (e) => {
      if (e.target.closest('.card-bookmark-btn') || e.target.closest('.card-read-btn')) return;
      const url = card.getAttribute('data-url');
      if (url) {
        window.open(url, '_blank', 'noopener,noreferrer');
      }
    });
  });

  elements.articlesGrid.querySelectorAll('.card-bookmark-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const artId = btn.getAttribute('data-bookmark-id');
      toggleBookmark(artId, e);
    });
  });
}

// ==========================================================================
// Pipeline Sync Action
// ==========================================================================
async function triggerSync() {
  if (state.isSyncing) return;
  state.isSyncing = true;

  elements.btnSyncHeader.classList.add('spinning');
  elements.syncStatusText.textContent = 'Syncing feeds...';
  showToast('🔄 Running ingestion pipeline...');

  try {
    const res = await fetch('/api/sync', { method: 'POST' });
    const data = await res.json();
    if (data.success && data.data) {
      state.articles = data.data.articles || [];
      state.lastSync = data.data.last_sync;
      syncLocalBookmarks();
      updateMetrics();
      renderSourcesRow();
      applyFilters();
      showToast('✨ Feed updated with latest dispatches!');
    } else {
      showToast('⚠️ Sync completed with non-zero exit code.');
    }
  } catch (err) {
    console.error('Sync failed:', err);
    showToast('[-] Error triggering pipeline sync.');
  } finally {
    state.isSyncing = false;
    elements.btnSyncHeader.classList.remove('spinning');
    updateMetrics();
  }
}

// ==========================================================================
// Utilities & Event Listeners
// ==========================================================================
function setupEventListeners() {
  // Search input with live reactivity and clear button toggle
  elements.searchInput.addEventListener('input', (e) => {
    state.searchQuery = e.target.value;
    if (elements.searchClearBtn) {
      elements.searchClearBtn.style.display = state.searchQuery.trim().length > 0 ? 'flex' : 'none';
    }
    applyFilters();
  });

  if (elements.searchClearBtn) {
    elements.searchClearBtn.addEventListener('click', () => {
      elements.searchInput.value = '';
      state.searchQuery = '';
      elements.searchClearBtn.style.display = 'none';
      elements.searchInput.focus();
      applyFilters();
    });
  }

  // Pressing Enter in search field scrolls to dispatches
  elements.searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const dispatches = document.querySelector('.dispatches-section');
      if (dispatches) {
        dispatches.scrollIntoView({ behavior: 'smooth' });
      }
    }
  });

  // Global search shortcut ⌘K or /
  window.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      elements.searchInput.focus();
    } else if (e.key === '/' && document.activeElement !== elements.searchInput) {
      e.preventDefault();
      elements.searchInput.focus();
    }
  });

  // Category filter tabs
  elements.categoryTabs.querySelectorAll('.cat-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      elements.categoryTabs.querySelectorAll('.cat-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      state.activeFilter = tab.getAttribute('data-filter');
      updateNavRailActive(state.activeFilter);
      applyFilters();
    });
  });

  // Nav rail buttons
  elements.tabNavAll.addEventListener('click', () => setTab('all'));
  elements.tabNav24h.addEventListener('click', () => setTab('24h'));
  elements.tabNavSaved.addEventListener('click', () => setTab('saved'));

  // Hero buttons
  if (elements.heroTagBtn) {
    elements.heroTagBtn.addEventListener('click', () => {
      setTab('24h');
      const dispatches = document.querySelector('.dispatches-section');
      if (dispatches) {
        dispatches.scrollIntoView({ behavior: 'smooth' });
      }
    });
  }

  elements.heroExploreBtn.addEventListener('click', () => {
    const topStory = (state.articles && state.articles.length > 0) ? state.articles[0] : null;
    if (topStory && topStory.url) {
      window.open(topStory.url, '_blank', 'noopener,noreferrer');
    }
  });
  elements.heroFilter24hBtn.addEventListener('click', () => setTab('24h'));

  // Reset filters
  elements.btnResetFilters.addEventListener('click', () => {
    state.searchQuery = '';
    state.activeFilter = 'all';
    state.selectedSource = null;
    elements.searchInput.value = '';
    if (elements.searchClearBtn) elements.searchClearBtn.style.display = 'none';
    renderSourcesRow();
    setTab('all');
  });

  // Header sync trigger
  elements.btnSyncHeader.addEventListener('click', triggerSync);
}

function setTab(filterKey) {
  state.activeFilter = filterKey;
  updateNavRailActive(filterKey);

  elements.categoryTabs.querySelectorAll('.cat-tab').forEach(t => {
    if (t.getAttribute('data-filter') === filterKey) {
      t.classList.add('active');
    } else {
      t.classList.remove('active');
    }
  });

  applyFilters();
}

function updateNavRailActive(filterKey) {
  [elements.tabNavAll, elements.tabNav24h, elements.tabNavSaved].forEach(b => b && b.classList.remove('active'));
  if (filterKey === 'all') elements.tabNavAll.classList.add('active');
  if (filterKey === '24h') elements.tabNav24h.classList.add('active');
  if (filterKey === 'saved') elements.tabNavSaved.classList.add('active');
}

function formatReleaseDate(isoString) {
  if (!isoString) return 'Recent';
  try {
    const pub = new Date(isoString);
    return pub.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch (e) {
    return 'Recent';
  }
}

function formatReleaseFull(isoString) {
  if (!isoString) return 'Recent';
  try {
    const pub = new Date(isoString);
    const d = pub.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    const t = pub.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', timeZone: 'UTC' }) + ' UTC';
    return `${d} • ${t}`;
  } catch (e) {
    return 'Recent';
  }
}

function formatTimeAgo(isoString) {
  if (!isoString) return 'Recent';
  try {
    const pub = new Date(isoString);
    const diffSec = Math.floor((Date.now() - pub.getTime()) / 1000);
    if (diffSec < 3600) return `${Math.max(1, Math.floor(diffSec / 60))}m ago`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
    return `${Math.floor(diffSec / 86400)}d ago`;
  } catch (e) {
    return 'Recent';
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function showToast(message) {
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = message;
  elements.toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}

// Start application
document.addEventListener('DOMContentLoaded', init);
