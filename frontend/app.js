/**
 * Internship Radar - Client Application (v1.3 - Undergraduate Verified)
 * High-performance, reactive developer dashboard for GPU, Deep Learning & Systems Internships.
 * Includes Last 7 Days feed, cross-feed search fallback, dynamic count chips,
 * interactive widgets, and instant pipeline tracking.
 */

const API_BASE = "/api";

// Safe Lucide icon initializer that never throws
function safeCreateIcons() {
  if (window.lucide && typeof window.lucide.createIcons === "function") {
    try {
      window.lucide.createIcons();
    } catch (e) {
      console.warn("Lucide icon creation warning:", e);
    }
  }
}

// Micro Toast System for instant action feedback
function showToast(message, type = "info", undoCallback = null) {
  let container = document.getElementById("radar-toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "radar-toast-container";
    document.body.appendChild(container);
  }
  const toast = document.createElement("div");
  toast.className = `radar-toast toast-${type}`;
  toast.innerHTML = `
    <span class="flex-1">${message}</span>
    ${undoCallback ? `<button class="btn-toast-undo px-1.5 py-0.5 rounded-[1px] bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-[10px] font-bold border border-zinc-700 ml-2 cursor-pointer">Undo</button>` : ''}
  `;
  if (undoCallback) {
    const btnUndo = toast.querySelector(".btn-toast-undo");
    if (btnUndo) {
      btnUndo.addEventListener("click", () => {
        undoCallback();
        toast.remove();
      });
    }
  }
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(8px)";
    toast.style.transition = "all 0.2s ease";
    setTimeout(() => toast.remove(), 250);
  }, 3500);
}

const state = {
  feed: "today", // "today", "last7", "all", "saved", "applied"
  category: "all",
  quick_filter: null, // "triton", "llm", "india", "remote", "summer2027"
  eligibility: "all",
  work_mode: "all",
  search: "",
  sort_by: "match",
  viewMode: localStorage.getItem("radar_view") || "cards",
  page: 0,
  limit: 40,
  totalMatching: 0,
  selectedIndex: 0,
  stats: null,
  listings: [],
  activeListing: null,
  candidateProfile: null
};

// DOM References
const els = {
  todayCount: document.getElementById("stat-today-count"),
  last7Count: document.getElementById("stat-last7-count"),
  priorityCount: document.getElementById("stat-priority-count"),
  savedCount: document.getElementById("stat-saved-count"),
  totalCount: document.getElementById("stat-total-count"),
  appliedSub: document.getElementById("stat-applied-sub"),
  feedResultsSummary: document.getElementById("feed-results-summary"),
  feedDateIndicator: document.getElementById("feed-date-indicator"),
  feedListings: document.getElementById("feed-listings"),
  feedLoading: document.getElementById("feed-loading"),
  feedEmpty: document.getElementById("feed-empty"),
  feedPagination: document.getElementById("feed-pagination"),
  btnPrevPage: document.getElementById("btn-prev-page"),
  btnNextPage: document.getElementById("btn-next-page"),
  paginationInfo: document.getElementById("pagination-info"),
  inputSearch: document.getElementById("input-search"),
  btnClearSearch: document.getElementById("btn-clear-search"),
  selectSort: document.getElementById("select-sort"),
  selectWorkMode: document.getElementById("select-work-mode"),
  btnManualRefresh: document.getElementById("btn-manual-refresh"),
  refreshIcon: document.getElementById("refresh-icon"),
  sourcesSummaryText: document.getElementById("sources-summary-text"),
  sourcesIndicator: document.getElementById("sources-indicator"),
  headerTodayDate: document.getElementById("header-today-date"),
  schedulerStatusText: document.getElementById("scheduler-status-text"),

  // Fallback Banner
  searchFallbackBanner: document.getElementById("search-fallback-banner"),
  searchFallbackText: document.getElementById("search-fallback-text"),
  btnFallbackLast7: document.getElementById("btn-fallback-last7"),
  btnFallbackAll: document.getElementById("btn-fallback-all"),
  fallbackLast7Count: document.getElementById("fallback-last7-count"),
  fallbackAllCount: document.getElementById("fallback-all-count"),

  // Dynamic Count Chips
  ccountAll: document.getElementById("ccount-all"),
  ccountGpu: document.getElementById("ccount-gpu"),
  ccountLlm: document.getElementById("ccount-llm"),
  ccountMlsys: document.getElementById("ccount-mlsys"),
  ccountApplied: document.getElementById("ccount-applied"),
  ccountBackend: document.getElementById("ccount-backend"),
  qcountTriton: document.getElementById("qcount-triton"),
  qcountLlm: document.getElementById("qcount-llm"),
  qcountIndia: document.getElementById("qcount-india"),
  qcountRemote: document.getElementById("qcount-remote"),
  qcountSummer2027: document.getElementById("qcount-summer2027"),

  // Widgets
  widgetToday: document.getElementById("widget-today"),
  widgetLast7: document.getElementById("widget-last7"),
  widgetPriority: document.getElementById("widget-priority"),
  widgetPipeline: document.getElementById("widget-pipeline"),
  chipCountGpu: document.getElementById("chip-count-gpu"),
  chipCountLlm: document.getElementById("chip-count-llm"),
  chipCountApplied: document.getElementById("chip-count-applied"),

  // View Switcher
  btnViewCards: document.getElementById("btn-view-cards"),
  btnViewList: document.getElementById("btn-view-list"),

  // Modals & Drawers
  detailDrawer: document.getElementById("detail-drawer"),
  drawerBackdrop: document.getElementById("drawer-backdrop"),
  btnCloseDrawer: document.getElementById("btn-close-drawer"),
  sourcesModal: document.getElementById("sources-modal"),
  sourcesBackdrop: document.getElementById("sources-backdrop"),
  btnCloseSources: document.getElementById("btn-close-sources"),
  btnOpenSources: document.getElementById("btn-open-sources"),
  sourcesTableBody: document.getElementById("sources-table-body"),
  modalStatHealthy: document.getElementById("modal-stat-healthy"),
  modalStatErrors: document.getElementById("modal-stat-errors"),
  modalStatTotalIndexed: document.getElementById("modal-stat-total-indexed"),
  inputSourcesFilter: document.getElementById("input-sources-filter"),
  modalSourcesBadge: document.getElementById("modal-sources-badge"),
  profileModal: document.getElementById("profile-modal"),
  profileBackdrop: document.getElementById("profile-backdrop"),
  btnCloseProfile: document.getElementById("btn-close-profile"),
  btnOpenProfile: document.getElementById("btn-open-profile"),
  profileModalBody: document.getElementById("profile-modal-body"),

  // Detail Modal Elements
  modalCompany: document.getElementById("modal-company"),
  modalTitle: document.getElementById("modal-title"),
  modalLocationMode: document.getElementById("modal-location-mode"),
  modalMatchBadge: document.getElementById("modal-match-badge"),
  modalEligibilityBadge: document.getElementById("modal-eligibility-badge"),
  modalTodayBadge: document.getElementById("modal-today-badge"),
  modalCategory: document.getElementById("modal-category"),
  modalApplyLink: document.getElementById("modal-apply-link"),
  modalBtnCopyLink: document.getElementById("modal-btn-copy-link"),
  copyLinkText: document.getElementById("copy-link-text"),
  modalBtnSave: document.getElementById("modal-btn-save"),
  modalSaveText: document.getElementById("modal-save-text"),
  modalSaveIcon: document.getElementById("modal-save-icon"),
  modalBtnToggleApplied: document.getElementById("modal-btn-toggle-applied"),
  modalBtnToggleArchive: document.getElementById("modal-btn-toggle-archive"),
  modalArchiveText: document.getElementById("modal-archive-text"),
  modalArchiveIcon: document.getElementById("modal-archive-icon"),
  badgeTabArchived: document.getElementById("badge-tab-archived"),
  modalPitchBox: document.getElementById("modal-pitch-box"),
  btnCopyPitch: document.getElementById("btn-copy-pitch"),
  copyPitchText: document.getElementById("copy-pitch-text"),
  modalMatchReasons: document.getElementById("modal-match-reasons"),
  modalMatchedProjects: document.getElementById("modal-matched-projects"),
  modalMatchedSkills: document.getElementById("modal-matched-skills"),
  modalMissingSkills: document.getElementById("modal-missing-skills"),
  modalMissingContainer: document.getElementById("modal-missing-container"),
  modalEligibilityReasons: document.getElementById("modal-eligibility-reasons"),
  modalDateIst: document.getElementById("modal-date-ist"),
  modalDateUtc: document.getElementById("modal-date-utc"),
  modalDateStatus: document.getElementById("modal-date-status"),
  modalSourceName: document.getElementById("modal-source-name"),
  modalEvidence: document.getElementById("modal-evidence"),
  modalSnippet: document.getElementById("modal-snippet"),

  // Export
  btnExportMenu: document.getElementById("btn-export-menu"),
  exportDropdown: document.getElementById("export-dropdown"),
  btnExportCsv: document.getElementById("btn-export-csv"),
  btnExportJson: document.getElementById("btn-export-json")
};

document.addEventListener("DOMContentLoaded", () => {
  setViewMode(state.viewMode);
  bindEvents();
  fetchCandidateProfile();
  fetchStats();
  fetchListings();

  // Background refresh polling every 60s
  setInterval(() => {
    fetchStats();
  }, 60000);
});

function clearSearchAndQuickFilters() {
  els.inputSearch.value = "";
  state.search = "";
  state.quick_filter = null;
  els.btnClearSearch.classList.add("hidden");
  document.querySelectorAll(".quick-filter-btn").forEach(b => {
    b.classList.remove("active-filter");
  });
}

function bindEvents() {
  // Navigation Tabs (Clears stale search/quick-filter keywords)
  document.querySelectorAll(".feed-tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      clearSearchAndQuickFilters();
      setFeed(btn.getAttribute("data-feed"));
    });
  });

  // Interactive Widgets (Clears stale keywords and switches view)
  els.widgetToday.addEventListener("click", () => {
    clearSearchAndQuickFilters();
    setFeed("today");
  });
  els.widgetLast7.addEventListener("click", () => {
    clearSearchAndQuickFilters();
    setFeed("last7");
  });
  els.widgetPipeline.addEventListener("click", () => {
    clearSearchAndQuickFilters();
    setFeed("applied");
  });
  els.widgetPriority.addEventListener("click", () => {
    clearSearchAndQuickFilters();
    setFeed("last7", false, false);
    setCategory("GPU & Triton Optimization");
  });

  // Domain Category Pills (Clears stale search bar text)
  document.querySelectorAll(".cat-pill").forEach(btn => {
    btn.addEventListener("click", () => {
      clearSearchAndQuickFilters();
      setCategory(btn.getAttribute("data-cat"));
    });
  });

  // Quick Filter Chips (Dedicated filter presets with toggle & cross-feed fallback)
  document.querySelectorAll(".quick-filter-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const qf = btn.getAttribute("data-filter");

      // Toggle functionality: if already active, clicking again turns it off
      if (state.quick_filter === qf) {
        state.quick_filter = null;
        btn.classList.remove("active-filter");
        state.page = 0;
        fetchListings();
        return;
      }

      // Clear search text and conflicting category filters
      els.inputSearch.value = "";
      state.search = "";
      els.btnClearSearch.classList.add("hidden");
      state.category = "all";
      state.work_mode = "all";
      els.selectWorkMode.value = "all";

      document.querySelectorAll(".cat-pill").forEach(p => {
        if (p.getAttribute("data-cat") === "all") {
          p.classList.add("active", "bg-zinc-800", "text-zinc-100", "border-zinc-700");
          p.classList.remove("text-zinc-400", "bg-zinc-900");
        } else {
          p.classList.remove("active", "bg-zinc-800", "text-zinc-100", "border-zinc-700");
          p.classList.add("text-zinc-400", "bg-zinc-900");
        }
      });

      // Set active quick filter
      state.quick_filter = qf;
      document.querySelectorAll(".quick-filter-btn").forEach(b => {
        if (b.getAttribute("data-filter") === qf) {
          b.classList.add("active-filter");
        } else {
          b.classList.remove("active-filter");
        }
      });

      // Smart check: If user is on 'today' feed and today's count for this filter is 0,
      // seamlessly switch to 'last7' so the user immediately gets rich results!
      if (state.feed === "today" && state.stats && state.stats.quick_filter_counts) {
        const todayCount = state.stats.quick_filter_counts.today[qf] || 0;
        if (todayCount === 0) {
          setFeed("last7", false, false); // switch feed to last7 without redundant fetch
        }
      }

      state.page = 0;
      fetchListings();
    });
  });

  // Cross-Feed Fallback Banner Actions
  els.btnFallbackLast7.addEventListener("click", () => {
    setFeed("last7");
  });

  els.btnFallbackAll.addEventListener("click", () => {
    setFeed("all");
  });

  // View Mode Buttons
  els.btnViewCards.addEventListener("click", () => setViewMode("cards"));
  els.btnViewList.addEventListener("click", () => setViewMode("list"));

  // Sort & Work Mode
  els.selectSort.addEventListener("change", (e) => {
    state.sort_by = e.target.value;
    state.page = 0;
    fetchListings();
  });

  els.selectWorkMode.addEventListener("change", (e) => {
    state.work_mode = e.target.value;
    state.page = 0;
    fetchListings();
  });

  // Search input with debounce & auto-deactivation of quick filter chips
  let searchTimeout = null;
  els.inputSearch.addEventListener("input", (e) => {
    clearTimeout(searchTimeout);
    const val = e.target.value.trim();
    if (val) {
      els.btnClearSearch.classList.remove("hidden");
    } else {
      els.btnClearSearch.classList.add("hidden");
    }

    if (state.quick_filter) {
      state.quick_filter = null;
      document.querySelectorAll(".quick-filter-btn").forEach(b => b.classList.remove("active-filter"));
    }

    searchTimeout = setTimeout(() => {
      state.search = val;
      state.page = 0;
      fetchListings();
    }, 200);
  });

  els.btnClearSearch.addEventListener("click", () => {
    clearSearchAndQuickFilters();
    state.page = 0;
    fetchListings();
    els.inputSearch.focus();
  });

  // Manual Refresh
  els.btnManualRefresh.addEventListener("click", triggerManualRefresh);

  // Pagination
  els.btnPrevPage.addEventListener("click", () => {
    if (state.page > 0) {
      state.page--;
      fetchListings();
    }
  });

  els.btnNextPage.addEventListener("click", () => {
    if ((state.page + 1) * state.limit < state.totalMatching) {
      state.page++;
      fetchListings();
    }
  });

  // Modal Closures
  els.btnCloseDrawer.addEventListener("click", closeDetailDrawer);
  els.drawerBackdrop.addEventListener("click", closeDetailDrawer);
  els.btnCloseSources.addEventListener("click", closeSourcesModal);
  els.sourcesBackdrop.addEventListener("click", closeSourcesModal);
  els.btnOpenSources.addEventListener("click", () => openSourcesModal(""));
  els.btnCloseProfile.addEventListener("click", () => els.profileModal.classList.add("hidden"));
  els.profileBackdrop.addEventListener("click", () => els.profileModal.classList.add("hidden"));
  els.btnOpenProfile.addEventListener("click", openProfileModal);

  // Export dropdown
  els.btnExportMenu.addEventListener("click", () => {
    els.exportDropdown.classList.toggle("hidden");
  });
  document.addEventListener("click", (e) => {
    if (!els.btnExportMenu.contains(e.target) && !els.exportDropdown.contains(e.target)) {
      els.exportDropdown.classList.add("hidden");
    }
  });

  els.btnExportCsv.addEventListener("click", () => {
    window.location.href = `${API_BASE}/export?format=csv&feed=${state.feed}`;
    els.exportDropdown.classList.add("hidden");
  });

  els.btnExportJson.addEventListener("click", () => {
    window.location.href = `${API_BASE}/export?format=json&feed=${state.feed}`;
    els.exportDropdown.classList.add("hidden");
  });

  // Detail Modal Actions
  els.modalBtnSave.addEventListener("click", () => {
    if (!state.activeListing) return;
    toggleSaveListing(state.activeListing.id, !state.activeListing.user_saved);
  });

  els.modalBtnToggleApplied.addEventListener("click", () => {
    if (!state.activeListing) return;
    const isCurrentlyApplied = state.activeListing.user_status && state.activeListing.user_status !== "none" && state.activeListing.user_status !== "dismissed";
    if (isCurrentlyApplied) {
      removeListingFromApplied(state.activeListing.id);
    } else {
      markListingAsApplied(state.activeListing.id);
    }
  });

  els.modalBtnToggleArchive.addEventListener("click", () => {
    if (!state.activeListing) return;
    if (state.activeListing.user_status === "dismissed") {
      unarchiveListing(state.activeListing.id);
    } else {
      archiveListing(state.activeListing.id);
    }
  });

  els.modalBtnCopyLink.addEventListener("click", () => {
    if (!state.activeListing) return;
    const url = state.activeListing.original_url || state.activeListing.canonical_url;
    navigator.clipboard.writeText(url).then(() => {
      els.copyLinkText.textContent = "Copied!";
      setTimeout(() => { els.copyLinkText.textContent = "Copy Link"; }, 2000);
    });
  });

  els.btnCopyPitch.addEventListener("click", () => {
    const text = els.modalPitchBox.textContent;
    navigator.clipboard.writeText(text).then(() => {
      els.copyPitchText.textContent = "Copied!";
      setTimeout(() => { els.copyPitchText.textContent = "Copy Pitch"; }, 2000);
    });
  });

  // Keyboard Shortcuts (Linear / Raycast Style)
  document.addEventListener("keydown", (e) => {
    if (e.key === "/" && document.activeElement !== els.inputSearch) {
      e.preventDefault();
      els.inputSearch.focus();
      return;
    }

    if (e.key === "Escape") {
      closeDetailDrawer();
      els.sourcesModal.classList.add("hidden");
      els.profileModal.classList.add("hidden");
      return;
    }

    if (document.activeElement.tagName === "INPUT" || document.activeElement.tagName === "SELECT") {
      return;
    }

    if (e.key === "j" || e.key === "ArrowDown") {
      e.preventDefault();
      navigateCard(1);
    } else if (e.key === "k" || e.key === "ArrowUp") {
      e.preventDefault();
      navigateCard(-1);
    } else if (e.key === "Enter" || e.key === " ") {
      if (state.listings[state.selectedIndex]) {
        e.preventDefault();
        openDetailDrawer(state.listings[state.selectedIndex]);
      }
    } else if (e.key === "s") {
      if (state.listings[state.selectedIndex]) {
        e.preventDefault();
        const it = state.listings[state.selectedIndex];
        toggleSaveListing(it.id, !it.user_saved);
      }
    } else if (e.key === "a") {
      if (state.listings[state.selectedIndex]) {
        e.preventDefault();
        const it = state.listings[state.selectedIndex];
        if (it.user_status && it.user_status !== "none") {
          removeListingFromApplied(it.id);
        } else {
          markListingAsApplied(it.id);
        }
      }
    } else if (e.key === "o") {
      if (state.listings[state.selectedIndex]) {
        e.preventDefault();
        const it = state.listings[state.selectedIndex];
        window.open(it.original_url || it.canonical_url, "_blank");
      }
    }
  });
}

function setViewMode(mode) {
  state.viewMode = mode;
  localStorage.setItem("radar_view", mode);
  if (mode === "cards") {
    els.btnViewCards.classList.add("bg-zinc-800", "text-white");
    els.btnViewCards.classList.remove("text-zinc-400");
    els.btnViewList.classList.remove("bg-zinc-800", "text-white");
    els.btnViewList.classList.add("text-zinc-400");
  } else {
    els.btnViewList.classList.add("bg-zinc-800", "text-white");
    els.btnViewList.classList.remove("text-zinc-400");
    els.btnViewCards.classList.remove("bg-zinc-800", "text-white");
    els.btnViewCards.classList.add("text-zinc-400");
  }
  if (state.listings && state.listings.length > 0) {
    renderListings({
      listings: state.listings,
      total: state.totalMatching,
      feed: state.feed,
      today_ist: state.stats ? state.stats.current_date_ist : ""
    });
  }
}

function navigateCard(delta) {
  if (!state.listings.length) return;
  state.selectedIndex = Math.max(0, Math.min(state.listings.length - 1, state.selectedIndex + delta));
  
  const cards = els.feedListings.querySelectorAll(".radar-card, .list-row");
  cards.forEach((c, idx) => {
    if (idx === state.selectedIndex) {
      c.classList.add("active-selected");
      c.scrollIntoView({ block: "nearest", behavior: "smooth" });
    } else {
      c.classList.remove("active-selected");
    }
  });
}

function setFeed(feedName, triggerFetch = true, clearFilters = true) {
  state.feed = feedName;
  state.page = 0;
  state.selectedIndex = 0;
  
  if (clearFilters) {
    clearSearchAndQuickFilters();
    state.category = "all";
    document.querySelectorAll(".cat-pill").forEach(p => {
      if (p.getAttribute("data-cat") === "all") {
        p.classList.add("active", "bg-zinc-800", "text-zinc-100", "border-zinc-700");
        p.classList.remove("text-zinc-400", "bg-zinc-900");
      } else {
        p.classList.remove("active", "bg-zinc-800", "text-zinc-100", "border-zinc-700");
        p.classList.add("text-zinc-400", "bg-zinc-900");
      }
    });
  }

  document.querySelectorAll(".feed-tab-btn").forEach(b => {
    if (b.getAttribute("data-feed") === feedName) {
      b.classList.add("active", "bg-zinc-800", "text-white", "border-zinc-700");
      b.classList.remove("text-zinc-400", "border-transparent");
    } else {
      b.classList.remove("active", "bg-zinc-800", "text-white", "border-zinc-700");
      b.classList.add("text-zinc-400", "border-transparent");
    }
  });

  updateDynamicBadges();
  if (triggerFetch) {
    fetchListings();
  }
}

function setCategory(catName) {
  state.category = catName;
  state.page = 0;
  state.selectedIndex = 0;
  clearSearchAndQuickFilters();

  // Smart check: If on 'today' feed and today's count for this category is 0,
  // switch to 'last7' so the user sees real postings
  if (state.feed === "today" && catName !== "all" && state.stats && state.stats.category_counts) {
    const todayCount = state.stats.category_counts.today[catName] || 0;
    if (todayCount === 0) {
      setFeed("last7", false, false);
    }
  }

  document.querySelectorAll(".cat-pill").forEach(p => {
    if (p.getAttribute("data-cat") === catName) {
      p.classList.add("active", "bg-zinc-800", "text-zinc-100", "border-zinc-700");
      p.classList.remove("text-zinc-400", "bg-zinc-900");
    } else {
      p.classList.remove("active", "bg-zinc-800", "text-zinc-100", "border-zinc-700");
      p.classList.add("text-zinc-400", "bg-zinc-900");
    }
  });

  fetchListings();
}

// Fetch Candidate Profile
async function fetchCandidateProfile() {
  try {
    const res = await fetch(`${API_BASE}/profile`);
    if (res.ok) {
      state.candidateProfile = await res.json();
    }
  } catch (err) {
    console.error("Failed to load candidate profile:", err);
  }
}

// Fetch Dashboard Stats & Update Live Counter Chips
async function fetchStats() {
  try {
    const res = await fetch(`${API_BASE}/stats`);
    if (!res.ok) return;
    const stats = await res.json();
    state.stats = stats;

    els.todayCount.textContent = stats.today_new_count.toLocaleString();
    els.last7Count.textContent = (stats.last7_days_count || 0).toLocaleString();
    els.priorityCount.textContent = `${stats.high_priority_count} priority`;
    els.savedCount.textContent = stats.applied_count.toLocaleString();
    els.totalCount.textContent = stats.total_open_count.toLocaleString();
    els.appliedSub.textContent = `${stats.saved_count} saved`;

    // Tab badges
    document.getElementById("badge-tab-today").textContent = stats.today_new_count;
    document.getElementById("badge-tab-last7").textContent = stats.last7_days_count || 0;
    document.getElementById("badge-tab-all").textContent = stats.total_open_count;
    document.getElementById("badge-tab-saved").textContent = stats.saved_count;
    document.getElementById("badge-tab-applied").textContent = stats.applied_count;
    if (els.badgeTabArchived) els.badgeTabArchived.textContent = stats.archived_count || 0;

    if (stats.current_date_ist) {
      els.headerTodayDate.textContent = `${stats.current_date_ist} IST`;
    }

    if (stats.sources_error > 0) {
      els.sourcesIndicator.className = "w-1.5 h-1.5 rounded-none bg-amber-400";
      els.sourcesSummaryText.textContent = `${stats.sources_healthy}/${stats.sources_configured} Healthy`;
    } else {
      els.sourcesIndicator.className = "w-1.5 h-1.5 rounded-none bg-emerald-400";
      els.sourcesSummaryText.textContent = `${stats.sources_healthy} Sources Active`;
    }

    if (stats.scheduler && stats.scheduler.next_run) {
      els.schedulerStatusText.textContent = `Next scan: ${stats.scheduler.next_run.slice(11, 19)}`;
    }

    // Update Domain Widget Counts
    if (stats.category_counts && stats.category_counts.all) {
      const allC = stats.category_counts.all;
      els.chipCountGpu.textContent = `GPU: ${allC["GPU & Triton Optimization"] || 0}`;
      els.chipCountLlm.textContent = `LLM: ${allC["LLM Research & Modeling"] || 0}`;
      els.chipCountApplied.textContent = `Applied: ${allC["Applied AI / ML"] || 0}`;
    }

    updateDynamicBadges();
  } catch (err) {
    console.error("Error fetching stats:", err);
  }
}

// Update dynamic counts on Category and Quick Filter Chips
function updateDynamicBadges() {
  if (!state.stats) return;
  const feedKey = (state.feed === "today" || state.feed === "last7") ? state.feed : "all";

  // Category counts
  if (state.stats.category_counts && state.stats.category_counts[feedKey]) {
    const cMap = state.stats.category_counts[feedKey];
    let totalCat = 0;
    Object.values(cMap).forEach(v => totalCat += v);

    els.ccountAll.textContent = `(${totalCat})`;
    els.ccountGpu.textContent = `(${cMap["GPU & Triton Optimization"] || 0})`;
    els.ccountLlm.textContent = `(${cMap["LLM Research & Modeling"] || 0})`;
    els.ccountMlsys.textContent = `(${cMap["ML Systems & Training Infra"] || 0})`;
    els.ccountApplied.textContent = `(${cMap["Applied AI / ML"] || 0})`;
    els.ccountBackend.textContent = `(${cMap["Backend & Systems"] || 0})`;
  }

  // Quick filter counts
  if (state.stats.quick_filter_counts && state.stats.quick_filter_counts[feedKey]) {
    const qMap = state.stats.quick_filter_counts[feedKey];
    els.qcountTriton.textContent = qMap.triton || 0;
    els.qcountLlm.textContent = qMap.llm || 0;
    els.qcountIndia.textContent = qMap.india || 0;
    els.qcountRemote.textContent = qMap.remote || 0;
    els.qcountSummer2027.textContent = qMap.summer2027 || 0;
  }
}

// Fetch Listings with Filter Query
async function fetchListings() {
  els.feedLoading.classList.remove("hidden");
  els.feedEmpty.classList.add("hidden");
  els.searchFallbackBanner.classList.add("hidden");
  els.feedListings.innerHTML = "";

  const params = new URLSearchParams({
    feed: state.feed,
    category: state.category,
    eligibility: state.eligibility,
    work_mode: state.work_mode,
    sort_by: state.sort_by,
    limit: state.limit,
    offset: state.page * state.limit
  });

  if (state.search) {
    params.append("search", state.search);
  }
  if (state.quick_filter) {
    params.append("quick_filter", state.quick_filter);
  }

  try {
    const res = await fetch(`${API_BASE}/listings?${params.toString()}`);
    if (!res.ok) throw new Error("Failed to load listings");
    const data = await res.json();

    state.listings = data.listings;
    state.totalMatching = data.total;
    state.selectedIndex = 0;

    // Check Cross-Feed Fallback (Solves "Filter returns 0 results" problem)
    if (data.total === 0 && data.fallback) {
      const fb = data.fallback;
      if (fb.last7 > 0 || fb.all > 0) {
        els.searchFallbackBanner.classList.remove("hidden");
        const filterLabel = state.quick_filter ? state.quick_filter.toUpperCase() : (state.search || state.category);
        els.searchFallbackText.textContent = `0 results found in Today's Feed for '${filterLabel}'.`;
        els.fallbackLast7Count.textContent = fb.last7;
        els.fallbackAllCount.textContent = fb.all;
      }
    }

    renderListings(data);
  } catch (err) {
    console.error("Failed to load listings:", err);
    els.feedListings.innerHTML = `<div class="p-6 text-center text-rose-400 font-mono text-xs">Error connecting to local server. Check if port 8000 is open.</div>`;
  } finally {
    els.feedLoading.classList.add("hidden");
  }
}

function renderListings(data) {
  const { listings, total, feed, today_ist } = data;

  if (feed === "today") {
    els.feedResultsSummary.innerHTML = `Displaying <strong class="text-white">${total}</strong> confirmed same-day undergraduate postings (<span class="text-blue-400 font-mono">${today_ist} IST</span>)`;
    els.feedDateIndicator.textContent = "Strict Verified Feed";
  } else if (feed === "last7") {
    els.feedResultsSummary.innerHTML = `Displaying <strong class="text-emerald-400 font-bold">${total}</strong> undergraduate postings verified in the <span class="text-emerald-300 font-mono">Last 7 Calendar Days</span>`;
    els.feedDateIndicator.textContent = "7-Day Freshness Window";
  } else if (feed === "saved") {
    els.feedResultsSummary.innerHTML = `Displaying <strong class="text-white">${total}</strong> bookmarked listings`;
    els.feedDateIndicator.textContent = "Saved Bookmarks";
  } else if (feed === "applied") {
    els.feedResultsSummary.innerHTML = `Displaying <strong class="text-white">${total}</strong> tracked applications`;
    els.feedDateIndicator.textContent = "Application Pipeline";
  } else if (feed === "archived") {
    els.feedResultsSummary.innerHTML = `Displaying <strong class="text-zinc-300 font-bold">${total}</strong> archived / dismissed opportunities`;
    els.feedDateIndicator.textContent = "Archived Vault";
  } else {
    els.feedResultsSummary.innerHTML = `Displaying <strong class="text-white">${total}</strong> active undergraduate listings across all sources`;
    els.feedDateIndicator.textContent = "Complete Open Catalog";
  }

  if (listings.length === 0) {
    els.feedEmpty.classList.remove("hidden");
    if (feed === "today") {
      document.getElementById("empty-state-desc").textContent =
        "No new postings have been verified yet today for this specific filter. Switch to 'LAST 7 DAYS' or 'ALL OPEN CATALOG' to view active opportunities.";
    } else if (feed === "applied") {
      document.getElementById("empty-state-desc").textContent =
        "No applications currently in your pipeline. Click 'Track' on any position to track it.";
    } else if (feed === "archived") {
      document.getElementById("empty-state-desc").textContent =
        "Your archive is currently empty. You can archive any opportunity to hide it from your active feeds.";
    } else {
      document.getElementById("empty-state-desc").textContent =
        "No matching positions found. Try relaxing the search or category filters.";
    }
    els.feedPagination.classList.add("hidden");
    return;
  }

  els.feedEmpty.classList.add("hidden");
  const container = els.feedListings;
  container.innerHTML = "";

  if (state.viewMode === "list") {
    renderCompactListView(container, listings, feed);
  } else {
    renderCardsView(container, listings, feed);
  }

  // Update pagination
  if (total > state.limit) {
    els.feedPagination.classList.remove("hidden");
    const totalPages = Math.ceil(total / state.limit);
    els.paginationInfo.textContent = `PAGE ${state.page + 1} OF ${totalPages} (${total} TOTAL)`;
    els.btnPrevPage.disabled = state.page === 0;
    els.btnNextPage.disabled = (state.page + 1) >= totalPages;
  } else {
    els.feedPagination.classList.add("hidden");
  }

  safeCreateIcons();
}

// Render High-Density Cards View
function renderCardsView(container, listings, feed) {
  listings.forEach((item, index) => {
    const card = document.createElement("div");
    card.className = `radar-card card-enter p-3 cursor-pointer flex flex-col gap-2.5 ${index === state.selectedIndex ? 'active-selected' : ''}`;

    let scoreTag = `<span class="tag-amber px-1.5 py-0.2 font-mono text-[10px] font-bold">[${item.match_score}%]</span>`;
    if (item.match_score >= 85) {
      scoreTag = `<span class="tag-emerald px-1.5 py-0.2 font-mono text-[10px] font-bold">[${item.match_score}%]</span>`;
    } else if (item.match_score >= 70) {
      scoreTag = `<span class="tag-blue px-1.5 py-0.2 font-mono text-[10px] font-bold">[${item.match_score}%]</span>`;
    }

    const todayBadge = item.is_today_ist 
      ? `<span class="px-1 py-0.2 rounded-[1px] bg-blue-950 text-blue-300 border border-blue-700 font-mono text-[9px] font-bold">TODAY</span>` 
      : "";

    const indiaBadge = item.is_india 
      ? `<span class="px-1.5 py-0.2 rounded-[1px] bg-emerald-950 text-emerald-300 border border-emerald-700 font-mono text-[9px] font-bold flex items-center gap-1"><span>🇮🇳</span><span>INDIA DOMESTIC</span></span>` 
      : "";

    const undergradBadge = `<span class="px-1.5 py-0.2 rounded-[1px] bg-zinc-900 text-zinc-300 border border-zinc-700 font-mono text-[9px]">B.Tech / Undergrad Verified</span>`;

    const locStr = item.locations && item.locations.length > 0 ? item.locations.join(", ") : "Location Unspecified";
    const applyUrl = item.original_url || item.canonical_url;

    const skillPills = (item.matched_skills || []).slice(0, 4).map(s => 
      `<span class="tag-zinc px-1 py-0.2 font-mono text-[10px]">${s}</span>`
    ).join("");

    let appliedControl = "";
    if (item.user_status && item.user_status !== "none" && item.user_status !== "dismissed") {
      appliedControl = `
        <button class="btn-remove-applied px-2 py-0.5 rounded-[2px] border border-rose-800 bg-rose-950/60 text-rose-300 hover:bg-rose-900 font-mono text-[10px] flex items-center gap-1 transition" title="Manually remove from Applied pipeline">
          <i data-lucide="x" class="w-2.5 h-2.5"></i>
          <span>Remove</span>
        </button>
      `;
    } else if (state.feed !== "archived" && item.user_status !== "dismissed") {
      appliedControl = `
        <button class="btn-mark-applied px-2 py-0.5 rounded-[2px] border border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-zinc-200 hover:border-zinc-700 font-mono text-[10px] flex items-center gap-1 transition" title="Mark as applied">
          <span>Track</span>
        </button>
      `;
    }

    let archiveControl = "";
    if (item.user_status === "dismissed" || state.feed === "archived") {
      archiveControl = `
        <button onclick="event.stopPropagation(); window.unarchiveListing('${escapeHtml(item.id)}')" class="btn-card-restore px-2 py-0.5 rounded-[2px] border border-blue-800 bg-blue-950/60 hover:bg-blue-900 text-blue-300 font-mono text-[10px] flex items-center gap-1 transition cursor-pointer" title="Restore opportunity to active feeds">
          <i data-lucide="rotate-ccw" class="w-2.5 h-2.5"></i>
          <span>Restore</span>
        </button>
      `;
    } else {
      archiveControl = `
        <button onclick="event.stopPropagation(); window.archiveListing('${escapeHtml(item.id)}')" class="btn-card-archive px-2 py-0.5 rounded-[2px] border border-zinc-800 bg-zinc-900/80 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 font-mono text-[10px] flex items-center gap-1 transition cursor-pointer" title="Archive / hide listing from active feeds">
          <i data-lucide="archive" class="w-2.5 h-2.5"></i>
          <span>Archive</span>
        </button>
      `;
    }

    const saveIconColor = item.user_saved ? "text-amber-400 fill-amber-400" : "text-zinc-500 hover:text-zinc-300";

    card.innerHTML = `
      <div class="flex items-start justify-between gap-2">
        <div class="flex-1">
          <div class="flex items-center gap-1.5 flex-wrap text-[11px] font-mono mb-0.5">
            <span class="font-bold text-white">${escapeHtml(item.company)}</span>
            <span class="text-zinc-600">•</span>
            <span class="text-zinc-400">${escapeHtml(locStr)}</span>
            <span class="text-zinc-500">[${escapeHtml(item.work_mode)}]</span>
            ${todayBadge}
            ${indiaBadge}
            ${undergradBadge}
          </div>
          <h3 class="text-xs font-semibold text-zinc-100 group-hover:text-blue-400 transition leading-snug">
            ${escapeHtml(item.title)}
          </h3>
        </div>

        <div class="flex items-center gap-1.5 shrink-0">
          ${scoreTag}
          <button class="btn-card-save p-1 rounded hover:bg-zinc-800 transition cursor-pointer" title="Save / Bookmark">
            <i data-lucide="bookmark" class="w-3.5 h-3.5 ${saveIconColor}"></i>
          </button>
        </div>
      </div>

      <div class="text-[11px] font-mono text-zinc-300 bg-zinc-950/60 p-2 rounded-[2px] border border-zinc-800/80 leading-relaxed">
        ${escapeHtml(item.match_reasons && item.match_reasons[0] ? item.match_reasons[0] : "Direct alignment with technical profile background.")}
      </div>

      <div class="flex items-center justify-between flex-wrap gap-2 pt-1 border-t border-zinc-800/60 text-xs">
        <div class="flex items-center gap-1.5 flex-wrap">
          <button onclick="event.stopPropagation(); window.openSourcesModal('${escapeHtml(item.source_name)}')" class="btn-open-source-tag px-1.5 py-0.2 rounded-[1px] tag-zinc font-mono text-[9px] text-zinc-400 hover:text-white transition flex items-center gap-1 cursor-pointer" title="View source health details">
            <span class="healthy-dot w-1.5 h-1.5"></span>
            <span>${escapeHtml(item.source_name)}</span>
          </button>
          <span class="text-[10px] font-mono text-zinc-500">•</span>
          <span class="text-[10px] font-mono text-zinc-400">${escapeHtml(item.match_category)}</span>
          ${skillPills}
        </div>

        <div class="flex items-center gap-1.5">
          ${archiveControl}
          ${appliedControl}
          <span class="text-[10px] font-mono text-zinc-400">${escapeHtml(item.date_posted_ist || "Recent")}</span>
          <a href="${escapeHtml(applyUrl)}" target="_blank" rel="noopener noreferrer" class="btn-card-apply px-2.5 py-0.5 rounded-[2px] bg-zinc-100 hover:bg-white text-zinc-950 font-mono text-[10px] font-bold flex items-center gap-1 transition shadow-sm">
            <span>Apply</span>
            <i data-lucide="external-link" class="w-2.5 h-2.5"></i>
          </a>
        </div>
      </div>
    `;

    card.addEventListener("click", () => {
      state.selectedIndex = index;
      openDetailDrawer(item);
    });

    const btnSource = card.querySelector(".btn-open-source-tag");
    if (btnSource) {
      btnSource.addEventListener("click", (e) => {
        e.stopPropagation();
        openSourcesModal(item.source_name);
      });
    }

    const btnSave = card.querySelector(".btn-card-save");
    btnSave.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleSaveListing(item.id, !item.user_saved);
    });

    const btnApply = card.querySelector(".btn-card-apply");
    btnApply.addEventListener("click", (e) => {
      e.stopPropagation();
    });

    const btnArchive = card.querySelector(".btn-card-archive");
    if (btnArchive) {
      btnArchive.addEventListener("click", (e) => {
        e.stopPropagation();
        archiveListing(item.id);
      });
    }

    const btnRestore = card.querySelector(".btn-card-restore");
    if (btnRestore) {
      btnRestore.addEventListener("click", (e) => {
        e.stopPropagation();
        unarchiveListing(item.id);
      });
    }

    const btnRemove = card.querySelector(".btn-remove-applied");
    if (btnRemove) {
      btnRemove.addEventListener("click", (e) => {
        e.stopPropagation();
        removeListingFromApplied(item.id);
      });
    }

    const btnMark = card.querySelector(".btn-mark-applied");
    if (btnMark) {
      btnMark.addEventListener("click", (e) => {
        e.stopPropagation();
        markListingAsApplied(item.id);
      });
    }

    container.appendChild(card);
  });
}

// Render Compact List View
function renderCompactListView(container, listings, feed) {
  const table = document.createElement("table");
  table.className = "w-full text-left font-mono text-xs border-collapse";
  table.innerHTML = `
    <thead>
      <tr class="border-b border-zinc-800 text-zinc-400 text-[10px] uppercase">
        <th class="py-1.5 px-2">Match</th>
        <th class="py-1.5 px-2">Company</th>
        <th class="py-1.5 px-2">Title</th>
        <th class="py-1.5 px-2">Location</th>
        <th class="py-1.5 px-2">Posted</th>
        <th class="py-1.5 px-2 text-right">Actions</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-zinc-800/60"></tbody>
  `;

  const tbody = table.querySelector("tbody");

  listings.forEach((item, index) => {
    const tr = document.createElement("tr");
    tr.className = `list-row hover:bg-zinc-900/60 cursor-pointer ${index === state.selectedIndex ? 'bg-zinc-900/80' : ''}`;
    
    const applyUrl = item.original_url || item.canonical_url;
    const saveIconColor = item.user_saved ? "text-amber-400 fill-amber-400" : "text-zinc-600 hover:text-zinc-300";

    let appliedBtn = "";
    if (item.user_status && item.user_status !== "none" && item.user_status !== "dismissed") {
      appliedBtn = `<button class="btn-remove-applied text-[10px] text-rose-400 hover:text-rose-300 mr-2">[Remove]</button>`;
    } else if (state.feed !== "archived" && item.user_status !== "dismissed") {
      appliedBtn = `<button class="btn-mark-applied text-[10px] text-zinc-500 hover:text-zinc-300 mr-2">[Track]</button>`;
    }

    let archiveBtn = "";
    if (item.user_status === "dismissed" || state.feed === "archived") {
      archiveBtn = `<button onclick="event.stopPropagation(); window.unarchiveListing('${escapeHtml(item.id)}')" class="btn-list-restore text-[10px] text-blue-400 hover:text-blue-300 mr-2 cursor-pointer font-mono font-bold">[Restore]</button>`;
    } else {
      archiveBtn = `<button onclick="event.stopPropagation(); window.archiveListing('${escapeHtml(item.id)}')" class="btn-list-archive text-[10px] text-zinc-500 hover:text-zinc-200 mr-2 cursor-pointer font-mono">[Archive]</button>`;
    }

    tr.innerHTML = `
      <td class="py-1.5 px-2 font-bold ${item.match_score >= 85 ? 'text-emerald-400' : 'text-zinc-300'}">${item.match_score}%</td>
      <td class="py-1.5 px-2 font-bold text-white">${escapeHtml(item.company)}</td>
      <td class="py-1.5 px-2 text-zinc-200 truncate max-w-xs">${escapeHtml(item.title)}</td>
      <td class="py-1.5 px-2 text-zinc-400 text-[11px] truncate max-w-[140px]">${item.is_india ? '<span class="text-emerald-400 font-bold mr-1">🇮🇳</span>' : ''}${escapeHtml((item.locations || []).join(", ") || item.work_mode)}</td>
      <td class="py-1.5 px-2 text-zinc-400 text-[11px]">${escapeHtml(item.date_posted_ist || "Recent")}</td>
      <td class="py-1.5 px-2 text-right whitespace-nowrap">
        ${archiveBtn}
        ${appliedBtn}
        <button class="btn-list-save text-[11px] mr-2" title="Save"><i data-lucide="bookmark" class="w-3 h-3 inline ${saveIconColor}"></i></button>
        <a href="${escapeHtml(applyUrl)}" target="_blank" rel="noopener noreferrer" class="px-2 py-0.5 rounded-[1px] bg-zinc-200 hover:bg-white text-zinc-950 text-[10px] font-bold inline-block">Apply</a>
      </td>
    `;

    tr.addEventListener("click", () => {
      state.selectedIndex = index;
      openDetailDrawer(item);
    });

    const btnListArchive = tr.querySelector(".btn-list-archive");
    if (btnListArchive) {
      btnListArchive.addEventListener("click", (e) => {
        e.stopPropagation();
        archiveListing(item.id);
      });
    }

    const btnListRestore = tr.querySelector(".btn-list-restore");
    if (btnListRestore) {
      btnListRestore.addEventListener("click", (e) => {
        e.stopPropagation();
        unarchiveListing(item.id);
      });
    }

    const btnSave = tr.querySelector(".btn-list-save");
    btnSave.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleSaveListing(item.id, !item.user_saved);
    });

    const btnRemove = tr.querySelector(".btn-remove-applied");
    if (btnRemove) {
      btnRemove.addEventListener("click", (e) => {
        e.stopPropagation();
        removeListingFromApplied(item.id);
      });
    }

    const btnMark = tr.querySelector(".btn-mark-applied");
    if (btnMark) {
      btnMark.addEventListener("click", (e) => {
        e.stopPropagation();
        markListingAsApplied(item.id);
      });
    }

    const aTag = tr.querySelector("a");
    aTag.addEventListener("click", (e) => e.stopPropagation());

    tbody.appendChild(tr);
  });

  container.appendChild(table);
}

// Open Detail Drawer
function openDetailDrawer(item) {
  state.activeListing = item;

  els.modalCompany.textContent = item.company;
  els.modalTitle.textContent = item.title;
  els.modalLocationMode.textContent = `${(item.locations || []).join(", ") || "Global"} • ${item.work_mode}`;

  els.modalMatchBadge.className = `px-1.5 py-0.2 rounded-[1px] font-mono font-bold ${item.match_score >= 85 ? 'tag-emerald' : 'tag-amber'}`;
  els.modalMatchBadge.textContent = `${item.match_score}% MATCH`;

  if (item.is_india) {
    els.modalEligibilityBadge.className = "px-1.5 py-0.2 rounded-[1px] bg-emerald-950 text-emerald-300 border border-emerald-700 font-mono font-bold";
    els.modalEligibilityBadge.textContent = "🇮🇳 INDIA DOMESTIC (B.Tech Undergrad)";
  } else if (item.eligibility_status === "eligible") {
    els.modalEligibilityBadge.className = "px-1.5 py-0.2 rounded-[1px] tag-emerald font-mono";
    els.modalEligibilityBadge.textContent = "ELIGIBLE UNDERGRAD";
  } else {
    els.modalEligibilityBadge.className = "px-1.5 py-0.2 rounded-[1px] tag-amber font-mono";
    els.modalEligibilityBadge.textContent = "VERIFY VISA / SPONSORSHIP";
  }

  if (item.is_today_ist) {
    els.modalTodayBadge.classList.remove("hidden");
  } else {
    els.modalTodayBadge.classList.add("hidden");
  }

  els.modalCategory.textContent = item.match_category;
  
  const directUrl = item.original_url || item.canonical_url;
  els.modalApplyLink.href = directUrl;

  updateModalSaveButton(item.user_saved);
  updateModalAppliedButton(item.user_status);
  updateModalArchiveButton(item.user_status);

  els.modalMatchReasons.textContent = (item.match_reasons || []).join(" ");

  els.modalMatchedProjects.innerHTML = "";
  if (item.matched_projects && item.matched_projects.length > 0) {
    item.matched_projects.forEach(p => {
      const div = document.createElement("div");
      div.className = "p-2 rounded-[2px] bg-zinc-900 border border-zinc-800 text-zinc-200 font-mono text-[11px]";
      div.textContent = p;
      els.modalMatchedProjects.appendChild(div);
    });
  } else {
    els.modalMatchedProjects.innerHTML = `<span class="text-zinc-500 font-mono text-[11px]">Core CS & Algorithms fundamentals</span>`;
  }

  els.modalMatchedSkills.innerHTML = "";
  (item.matched_skills || []).forEach(s => {
    const span = document.createElement("span");
    span.className = "px-1.5 py-0.5 rounded-[1px] tag-zinc";
    span.textContent = s;
    els.modalMatchedSkills.appendChild(span);
  });

  els.modalMissingSkills.innerHTML = "";
  if (item.missing_skills && item.missing_skills.length > 0) {
    els.modalMissingContainer.classList.remove("hidden");
    item.missing_skills.forEach(s => {
      const span = document.createElement("span");
      span.className = "px-1.5 py-0.5 rounded-[1px] tag-amber";
      span.textContent = s;
      els.modalMissingSkills.appendChild(span);
    });
  } else {
    els.modalMissingContainer.classList.add("hidden");
  }

  els.modalEligibilityReasons.innerHTML = "";
  (item.eligibility_reasons || []).forEach(r => {
    const div = document.createElement("div");
    div.className = "text-zinc-300 flex items-start gap-1.5";
    div.innerHTML = `<span class="text-blue-400 shrink-0">•</span> <span>${escapeHtml(r)}</span>`;
    els.modalEligibilityReasons.appendChild(div);
  });

  els.modalDateIst.textContent = item.date_posted_ist || "Unknown";
  els.modalDateUtc.textContent = item.date_posted_utc || "Unknown";
  els.modalDateStatus.textContent = item.date_verification_status || "unverified";
  els.modalSourceName.innerHTML = `<span class="cursor-pointer underline decoration-dotted text-blue-400 hover:text-blue-300" title="Click to inspect source health">${escapeHtml(item.source_name)}</span>`;
  els.modalSourceName.onclick = () => openSourcesModal(item.source_name);
  els.modalEvidence.textContent = item.date_source_evidence || "Direct provider listing record";
  els.modalSnippet.textContent = item.description_snippet || "No description text provided.";

  fetchPitchForListing(item.id);

  els.detailDrawer.classList.remove("hidden");
  safeCreateIcons();
}

function closeDetailDrawer() {
  els.detailDrawer.classList.add("hidden");
  state.activeListing = null;
}

function updateModalSaveButton(isSaved) {
  if (isSaved) {
    els.modalSaveText.textContent = "Saved";
    els.modalSaveIcon.classList.add("text-amber-400", "fill-amber-400");
  } else {
    els.modalSaveText.textContent = "Save";
    els.modalSaveIcon.classList.remove("text-amber-400", "fill-amber-400");
  }
}

function updateModalAppliedButton(status) {
  if (status && status !== "none" && status !== "dismissed") {
    els.modalBtnToggleApplied.textContent = "✕ Remove from Applied";
    els.modalBtnToggleApplied.className = "px-2.5 py-1.5 rounded-[2px] border border-rose-800 bg-rose-950/70 hover:bg-rose-900 text-xs font-mono text-rose-300 transition";
  } else {
    els.modalBtnToggleApplied.textContent = "✓ Mark as Applied";
    els.modalBtnToggleApplied.className = "px-2.5 py-1.5 rounded-[2px] border border-zinc-700 bg-zinc-800 hover:bg-zinc-700 text-xs font-mono text-zinc-200 transition";
  }
}

function updateModalArchiveButton(status) {
  if (!els.modalBtnToggleArchive) return;
  if (status === "dismissed") {
    els.modalBtnToggleArchive.innerHTML = `<i data-lucide="rotate-ccw" class="w-3 h-3 text-blue-400"></i><span id="modal-archive-text">Restore</span>`;
    els.modalBtnToggleArchive.className = "px-2.5 py-1.5 rounded-[2px] border border-blue-800 bg-blue-950/70 hover:bg-blue-900 text-xs font-mono text-blue-300 transition flex items-center gap-1.5 cursor-pointer";
    els.modalBtnToggleArchive.title = "Restore this opportunity to active discovery feeds";
  } else {
    els.modalBtnToggleArchive.innerHTML = `<i data-lucide="archive" class="w-3 h-3 text-zinc-400"></i><span id="modal-archive-text">Archive</span>`;
    els.modalBtnToggleArchive.className = "px-2.5 py-1.5 rounded-[2px] border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-xs font-mono text-zinc-400 hover:text-zinc-200 transition flex items-center gap-1.5 cursor-pointer";
    els.modalBtnToggleArchive.title = "Archive / hide this opportunity from active discovery feeds";
  }
  safeCreateIcons();
}

// Fetch Outreach Pitch
async function fetchPitchForListing(id) {
  els.modalPitchBox.textContent = "Generating high-signal recruiter pitch from technical candidate profile...";
  try {
    const res = await fetch(`${API_BASE}/listings/${id}/pitch`, { method: "POST" });
    if (res.ok) {
      const data = await res.json();
      els.modalPitchBox.textContent = data.pitch;
    }
  } catch (e) {
    els.modalPitchBox.textContent = "Unable to generate pitch. Review candidate profile for outreach angles.";
  }
}

// Mark as Applied API
async function markListingAsApplied(id) {
  try {
    const res = await fetch(`${API_BASE}/listings/${id}/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "applied", notes: "" })
    });
    if (res.ok) {
      const it = state.listings.find(x => x.id === id);
      if (it) it.user_status = "applied";
      if (state.activeListing && state.activeListing.id === id) {
        state.activeListing.user_status = "applied";
        updateModalAppliedButton("applied");
      }
      fetchStats();
      renderListings({
        listings: state.listings,
        total: state.totalMatching,
        feed: state.feed,
        today_ist: state.stats ? state.stats.current_date_ist : ""
      });
    }
  } catch (err) {
    console.error("Failed to mark applied:", err);
  }
}

// Manually Remove from Applied API
async function removeListingFromApplied(id) {
  try {
    const res = await fetch(`${API_BASE}/listings/${id}/status`, {
      method: "DELETE"
    });
    if (res.ok) {
      const it = state.listings.find(x => x.id === id);
      if (it) it.user_status = "none";
      if (state.activeListing && state.activeListing.id === id) {
        state.activeListing.user_status = "none";
        updateModalAppliedButton("none");
      }
      fetchStats();

      if (state.feed === "applied") {
        state.listings = state.listings.filter(x => x.id !== id);
        state.totalMatching = Math.max(0, state.totalMatching - 1);
      }

      renderListings({
        listings: state.listings,
        total: state.totalMatching,
        feed: state.feed,
        today_ist: state.stats ? state.stats.current_date_ist : ""
      });
    }
  } catch (err) {
    console.error("Failed to remove from applied:", err);
  }
}

// Manually Archive Listing API with Optimistic UI & Toast Feedback
async function archiveListing(id) {
  const listingItem = state.listings.find(x => x.id === id) || (state.activeListing && state.activeListing.id === id ? state.activeListing : null);
  const companyName = listingItem ? listingItem.company : "Opportunity";
  const titleName = listingItem ? listingItem.title : "";

  // 1. Optimistic UI update
  if (listingItem) listingItem.user_status = "dismissed";
  if (state.activeListing && state.activeListing.id === id) {
    state.activeListing.user_status = "dismissed";
    updateModalArchiveButton("dismissed");
  }

  // Optimistically update archive badge count
  if (els.badgeTabArchived) {
    const currentArchived = parseInt(els.badgeTabArchived.textContent || "0", 10);
    els.badgeTabArchived.textContent = currentArchived + 1;
  }

  // Remove from non-archived feeds
  if (state.feed !== "archived") {
    state.listings = state.listings.filter(x => x.id !== id);
    state.totalMatching = Math.max(0, state.totalMatching - 1);
  }

  renderListings({
    listings: state.listings,
    total: state.totalMatching,
    feed: state.feed,
    today_ist: state.stats ? state.stats.current_date_ist : ""
  });

  // Sleek Obsidian toast with instant Undo action
  showToast(`Archived: <strong>${escapeHtml(companyName)}</strong> moved to Archive tab.`, "archive", () => {
    unarchiveListing(id);
  });

  // 2. Dispatch background API call
  try {
    const res = await fetch(`${API_BASE}/listings/${id}/archive`, { method: "POST" });
    if (!res.ok) throw new Error("Server rejected archive");
    fetchStats();
  } catch (err) {
    console.error("Failed to archive listing:", err);
    showToast("Failed to archive opportunity. Please check local server connection.", "archive");
    if (listingItem) listingItem.user_status = "none";
    fetchStats();
    fetchListings();
  }
}

// Restore / Unarchive Listing API with Optimistic UI & Toast Feedback
async function unarchiveListing(id) {
  const listingItem = state.listings.find(x => x.id === id) || (state.activeListing && state.activeListing.id === id ? state.activeListing : null);
  const companyName = listingItem ? listingItem.company : "Opportunity";

  // 1. Optimistic UI update
  if (listingItem) listingItem.user_status = "none";
  if (state.activeListing && state.activeListing.id === id) {
    state.activeListing.user_status = "none";
    updateModalArchiveButton("none");
  }

  // Optimistically decrement archive badge count
  if (els.badgeTabArchived) {
    const currentArchived = parseInt(els.badgeTabArchived.textContent || "0", 10);
    els.badgeTabArchived.textContent = Math.max(0, currentArchived - 1);
  }

  // Remove from archived feed
  if (state.feed === "archived") {
    state.listings = state.listings.filter(x => x.id !== id);
    state.totalMatching = Math.max(0, state.totalMatching - 1);
  }

  renderListings({
    listings: state.listings,
    total: state.totalMatching,
    feed: state.feed,
    today_ist: state.stats ? state.stats.current_date_ist : ""
  });

  // Toast feedback
  showToast(`Restored: <strong>${escapeHtml(companyName)}</strong> returned to active feeds.`, "restore");

  // 2. Dispatch background API call
  try {
    const res = await fetch(`${API_BASE}/listings/${id}/unarchive`, { method: "POST" });
    if (!res.ok) throw new Error("Server rejected unarchive");
    fetchStats();
  } catch (err) {
    console.error("Failed to unarchive listing:", err);
    showToast("Failed to restore opportunity. Please check local server connection.", "restore");
    if (listingItem) listingItem.user_status = "dismissed";
    fetchStats();
    fetchListings();
  }
}

// Toggle Save API
async function toggleSaveListing(id, saved) {
  try {
    const res = await fetch(`${API_BASE}/listings/${id}/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ saved })
    });
    if (res.ok) {
      const it = state.listings.find(x => x.id === id);
      if (it) it.user_saved = saved ? 1 : 0;
      if (state.activeListing && state.activeListing.id === id) {
        state.activeListing.user_saved = saved ? 1 : 0;
        updateModalSaveButton(saved);
      }
      fetchStats();
      if (state.feed === "saved" && !saved) {
        state.listings = state.listings.filter(x => x.id !== id);
        state.totalMatching = Math.max(0, state.totalMatching - 1);
      }
      renderListings({
        listings: state.listings,
        total: state.totalMatching,
        feed: state.feed,
        today_ist: state.stats ? state.stats.current_date_ist : ""
      });
    }
  } catch (err) {
    console.error("Failed to toggle save:", err);
  }
}

// Manual Refresh API
async function triggerManualRefresh() {
  els.refreshIcon.classList.add("animate-spin");
  els.btnManualRefresh.disabled = true;

  try {
    await fetch(`${API_BASE}/refresh`, { method: "POST" });
    setTimeout(async () => {
      await fetchStats();
      await fetchListings();
      els.refreshIcon.classList.remove("animate-spin");
      els.btnManualRefresh.disabled = false;
    }, 2500);
  } catch (err) {
    console.error("Refresh failed:", err);
    els.refreshIcon.classList.remove("animate-spin");
    els.btnManualRefresh.disabled = false;
  }
}

// Open Sources Registry Modal with Health Checks & Real-time Filter
let cachedSourcesList = [];

function closeSourcesModal() {
  if (els.sourcesModal) {
    els.sourcesModal.classList.add("hidden");
    els.sourcesModal.classList.remove("modal-open");
    els.sourcesModal.style.display = "none";
  }
}

async function openSourcesModal(filterText = "") {
  if (typeof filterText !== "string") filterText = "";

  // 1. OPEN IMMEDIATELY (0ms latency visual feedback)
  if (els.sourcesModal) {
    els.sourcesModal.classList.remove("hidden");
    els.sourcesModal.classList.add("modal-open");
    els.sourcesModal.style.display = "flex";
  }

  if (els.inputSourcesFilter) {
    els.inputSourcesFilter.value = filterText;
    els.inputSourcesFilter.oninput = (e) => renderSourcesTable(e.target.value);
  }

  // 2. Render cached data immediately if available, or clean skeleton
  if (cachedSourcesList && cachedSourcesList.length > 0) {
    renderSourcesTable(filterText);
  } else if (els.sourcesTableBody) {
    els.sourcesTableBody.innerHTML = `
      <tr>
        <td colspan="6" class="text-center py-10 text-zinc-400 font-mono text-xs">
          <div class="inline-flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
            <span>Connecting to 26 undergraduate career APIs & ATS connectors...</span>
          </div>
        </td>
      </tr>
    `;
  }

  // 3. Background fetch for latest health checks and counts
  try {
    const res = await fetch(`${API_BASE}/sources`);
    if (res.ok) {
      cachedSourcesList = await res.json();

      const totalCount = cachedSourcesList.length;
      const healthyCount = cachedSourcesList.filter(s => s.status === "healthy").length;
      const errorCount = cachedSourcesList.filter(s => s.status === "error").length;
      const totalIndexed = cachedSourcesList.reduce((acc, s) => acc + (s.items_indexed_count || 0), 0);

      if (els.modalStatHealthy) els.modalStatHealthy.textContent = healthyCount;
      if (els.modalStatErrors) els.modalStatErrors.textContent = errorCount;
      if (els.modalStatTotalIndexed) els.modalStatTotalIndexed.textContent = totalIndexed.toLocaleString();
      if (els.modalSourcesBadge) els.modalSourcesBadge.textContent = `${healthyCount}/${totalCount} ACTIVE`;

      const currentFilter = els.inputSourcesFilter ? els.inputSourcesFilter.value : filterText;
      renderSourcesTable(currentFilter);
    }
  } catch (err) {
    console.error("Failed to load sources:", err);
  }
}

function renderSourcesTable(filterText = "") {
  if (typeof filterText !== "string") filterText = "";
  const tbody = els.sourcesTableBody;
  if (!tbody) return;
  tbody.innerHTML = "";

  const query = (filterText || "").toLowerCase().trim();
  const filtered = cachedSourcesList.filter(s => 
    !query || 
    s.name.toLowerCase().includes(query) || 
    s.type.toLowerCase().includes(query) || 
    (s.company && s.company.toLowerCase().includes(query))
  );

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-zinc-500 font-mono text-xs">No source connectors match '${escapeHtml(filterText)}'</td></tr>`;
    return;
  }

  filtered.forEach(s => {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-zinc-900/60 transition";

    let statusBadge = `
      <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-[1px] tag-emerald text-[10px] font-bold">
        <span class="healthy-dot"></span>
        <span>HEALTHY</span>
      </span>
    `;
    if (s.status === "error") {
      statusBadge = `
        <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-[1px] tag-rose text-[10px] font-bold" title="${escapeHtml(s.error_message)}">
          <span class="error-dot"></span>
          <span>ERROR</span>
        </span>
      `;
    } else if (s.status === "pending") {
      statusBadge = `
        <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-[1px] tag-amber text-[10px] font-bold">
          <span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
          <span>PENDING</span>
        </span>
      `;
    }

    // Format IST date
    let lastCheckedFormatted = "Never";
    if (s.last_checked_at) {
      try {
        const d = new Date(s.last_checked_at);
        lastCheckedFormatted = d.toLocaleTimeString('en-US', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', second: '2-digit' }) + " IST";
      } catch (e) {
        lastCheckedFormatted = s.last_checked_at.slice(0, 19).replace('T', ' ');
      }
    }

    tr.innerHTML = `
      <td class="py-2.5 px-3">
        <div class="font-bold text-white text-xs">${escapeHtml(s.name)}</div>
        <div class="text-[10px] text-zinc-400 truncate max-w-sm mt-0.5 font-mono">${escapeHtml(s.url || "Native ATS API Connector")}</div>
      </td>
      <td class="py-2.5 px-3">
        <span class="tag-zinc px-1.5 py-0.2 rounded-[1px] text-[10px] uppercase font-mono">${escapeHtml(s.type)}</span>
      </td>
      <td class="py-2.5 px-3">${statusBadge}</td>
      <td class="py-2.5 px-3 font-mono font-bold text-zinc-200">${(s.items_indexed_count || 0).toLocaleString()}</td>
      <td class="py-2.5 px-3 text-zinc-400 text-[11px] font-mono">${lastCheckedFormatted}</td>
      <td class="py-2.5 px-3 text-right">
        <div class="flex items-center justify-end gap-1.5">
          <button class="btn-check-source text-[10px] px-2 py-0.5 rounded-[1px] border border-blue-800 bg-blue-950/60 hover:bg-blue-900 text-blue-300 font-mono flex items-center gap-1 transition" data-id="${s.id}" title="Run immediate health scan">
            <i data-lucide="refresh-cw" class="w-2.5 h-2.5"></i>
            <span>Check</span>
          </button>
          <button class="btn-toggle-source text-[10px] px-2 py-0.5 rounded-[1px] border border-zinc-700 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 font-mono transition" data-id="${s.id}">
            ${s.enabled ? 'DISABLE' : 'ENABLE'}
          </button>
        </div>
      </td>
    `;

    // Check Source Button
    const btnCheck = tr.querySelector(".btn-check-source");
    btnCheck.addEventListener("click", async () => {
      btnCheck.disabled = true;
      btnCheck.innerHTML = `<i data-lucide="loader" class="w-2.5 h-2.5 animate-spin"></i><span>Checking...</span>`;
      safeCreateIcons();
      try {
        const checkRes = await fetch(`${API_BASE}/sources/${s.id}/check`, { method: "POST" });
        if (checkRes.ok) {
          await openSourcesModal(els.inputSourcesFilter ? els.inputSourcesFilter.value : "");
          fetchStats();
        }
      } catch (e) {
        console.error("Source check failed:", e);
      }
    });

    // Toggle Source Button
    const btnToggle = tr.querySelector(".btn-toggle-source");
    btnToggle.addEventListener("click", async () => {
      await fetch(`${API_BASE}/sources/${s.id}/toggle`, { method: "POST" });
      openSourcesModal(els.inputSourcesFilter ? els.inputSourcesFilter.value : "");
      fetchStats();
    });

    tbody.appendChild(tr);
  });
  safeCreateIcons();
}

// Open Candidate Profile Modal
function openProfileModal() {
  const p = state.candidateProfile;
  if (!p) return;

  els.profileModalBody.innerHTML = `
    <div class="radar-card p-3 border-zinc-800">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-sm font-bold text-white">${escapeHtml(p.name)}</h3>
          <p class="text-zinc-400 font-mono text-[11px]">${escapeHtml(p.university)}</p>
        </div>
        <div class="text-right">
          <span class="px-1.5 py-0.5 rounded-[1px] tag-blue font-bold">CLASS OF ${p.graduation_year}</span>
          <p class="text-[10px] text-zinc-400 mt-0.5">CGPA: ${p.cgpa} / 10</p>
        </div>
      </div>
      <div class="mt-2 text-zinc-300 flex items-center gap-3 flex-wrap text-[11px]">
        <span>Degree: <strong>${escapeHtml(p.degree)} ${escapeHtml(p.major)} (Undergraduate)</strong></span>
        <span>Target: <strong>Summer 2027</strong></span>
      </div>
    </div>

    <div>
      <h4 class="font-bold text-zinc-200 mb-1 text-[11px]">PRIMARY SPECIALIZATION:</h4>
      <div class="flex flex-wrap gap-1">
        ${p.primary_skills.map(s => `<span class="px-1.5 py-0.5 rounded-[1px] tag-emerald text-[10px]">${s}</span>`).join('')}
      </div>
    </div>

    <div>
      <h4 class="font-bold text-zinc-200 mb-1 text-[11px]">KEY RESUME PROJECTS:</h4>
      <div class="flex flex-col gap-1.5">
        ${p.projects.map(proj => `
          <div class="p-2 rounded-[2px] bg-zinc-900 border border-zinc-800">
            <div class="font-bold text-blue-300 text-[11px]">${escapeHtml(proj.name)}</div>
            <div class="text-zinc-400 mt-0.5 text-[10px] leading-relaxed">${escapeHtml(proj.description)}</div>
          </div>
        `).join('')}
      </div>
    </div>

    <div>
      <h4 class="font-bold text-zinc-200 mb-1 text-[11px]">PRIORITY ORDER:</h4>
      <ol class="list-decimal list-inside space-y-0.5 text-zinc-400 text-[11px]">
        ${p.priority_domains.map(dom => `<li>${dom}</li>`).join('')}
      </ol>
    </div>
  `;

  els.profileModal.classList.remove("hidden");
  safeCreateIcons();
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Expose critical UI handlers globally on window for inline and dynamic events
window.openSourcesModal = openSourcesModal;
window.closeSourcesModal = closeSourcesModal;
window.archiveListing = archiveListing;
window.unarchiveListing = unarchiveListing;
window.showToast = showToast;
window.openProfileModal = openProfileModal;
window.safeCreateIcons = safeCreateIcons;
