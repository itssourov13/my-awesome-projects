(() => {
  "use strict";

  const root = document.documentElement;
  const $ = (selector, scope = document) => scope.querySelector(selector);
  const $$ = (selector, scope = document) => Array.from(scope.querySelectorAll(selector));
  const els = {
    header: $("#site-header"),
    nav: $("#site-nav"),
    menuToggle: $("#menu-toggle"),
    heroTotal: $("#hero-total"),
    heroCategories: $("#hero-categories"),
    heroLive: $("#hero-live"),
    heroShowcase: $("#hero-showcase"),
    navCount: $("#nav-project-count"),
    featured: $("#featured-grid"),
    grid: $("#project-grid"),
    search: $("#project-search"),
    sort: $("#project-sort"),
    categoryFilters: $("#category-filters"),
    quickFilters: $("#quick-filters"),
    techPanel: $("#tech-panel"),
    techFilters: $("#tech-filters"),
    techActive: $("#tech-active-count"),
    summary: $("#project-summary"),
    resultCount: $("#result-count"),
    clear: $("#clear-filters"),
    activeFilters: $("#active-filters"),
    empty: $("#empty-state"),
    emptyClear: $("#empty-clear"),
    loadError: $("#load-error"),
    retry: $("#retry-load"),
    dialog: $("#project-dialog"),
    dialogContent: $("#dialog-content"),
    imageDialog: $("#image-dialog"),
    lightboxImage: $("#lightbox-image"),
    lightboxCaption: $("#lightbox-caption"),
    themeToggle: $("#theme-toggle"),
    footerCategories: $("#footer-categories"),
    footerStats: $("#footer-stats"),
    footerYear: $("#footer-year")
  };

  // Keep in sync with CATEGORY_ORDER in scripts/generate_readme.py.
  const CATEGORY_ORDER = [
    "Cybersecurity", "AI & Developer Tools", "Web Apps", "Creative & 3D",
    "Mobile Apps", "Utilities", "Writing & Publishing", "Open Source"
  ];
  const SORTS = ["featured", "best", "recent", "live", "az"];
  const FEATURED_LIMIT = 7; // one spotlight + six cards, mirroring the README "Selected work".
  const MIN_TECH_PROJECTS = 2;
  const FLAGS = {
    featured: { label: "Featured", test: (item) => Boolean(item.project.featured) },
    live: { label: "Live preview", test: (item) => Boolean(item.live) },
    public: { label: "Public source", test: (item) => Boolean(item.source) }
  };

  const state = {
    projects: [],
    items: [],
    byId: new Map(),
    cards: new Map(),
    categories: [],
    techLabels: new Map(),
    category: "All",
    query: "",
    terms: [],
    sort: "featured",
    sortTouched: false,
    tech: new Set(),
    flags: new Set(),
    openId: "",
    slides: [],
    slideIndex: 0
  };

  const reducedMotion = () => window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);

  const plural = (count, noun) => count + " " + noun + (count === 1 ? "" : "s");

  const parseUrl = (value) => {
    try { return new URL(String(value || "")); } catch { return null; }
  };

  const isSafeHttps = (value) => {
    const parsed = parseUrl(value);
    return Boolean(parsed && parsed.protocol === "https:" && parsed.hostname);
  };

  const isGithubUrl = (value) => {
    const parsed = parseUrl(value);
    return Boolean(parsed && parsed.protocol === "https:" && ["github.com", "www.github.com"].includes(parsed.hostname.toLowerCase()));
  };

  // Only a public entry with a GitHub HTTPS sourceUrl ever yields a source link.
  const sourceUrlOf = (project) =>
    project.sourceAccess === "public" && isGithubUrl(project.sourceUrl) ? project.sourceUrl : "";
  const liveUrlOf = (project) => (isSafeHttps(project.liveUrl) ? project.liveUrl : "");

  // Local, relative asset paths only.
  const localAsset = (value) => {
    if (typeof value !== "string" || !value || value.startsWith("/") || value.includes("\\")) return "";
    if (/^[a-z][a-z0-9+.-]*:/i.test(value) || value.split("/").includes("..")) return "";
    return value;
  };

  const techKey = (name) => String(name || "").replace(/\s+v?\d+(?:\.\d+)*\+?$/i, "").trim().toLowerCase();
  const techLabel = (name) => String(name || "").replace(/\s+v?\d+(?:\.\d+)*\+?$/i, "").trim();
  const initials = (title) => String(title || "?").split(/\s+/).filter(Boolean).slice(0, 2).map((word) => word[0]).join("").toUpperCase();

  const externalLink = (url, label, className) =>
    '<a class="' + className + '" href="' + esc(url) + '" target="_blank" rel="noopener noreferrer">' +
    esc(label) + ' <span aria-hidden="true">↗</span></a>';

  const statusClass = (project) => {
    const status = (project.status || "").toLowerCase();
    if (status.includes("live preview")) return "status-live";
    if (status.includes("pending") || status.includes("needs verification") || status.includes("needs documentation")) return "status-pending";
    return "";
  };

  /* ---------- Model ---------- */

  function buildModel(projects) {
    state.projects = projects;
    state.byId = new Map();
    state.techLabels = new Map();
    state.items = projects.map((project) => {
      const tech = new Set();
      (project.stack || []).forEach((name) => {
        const key = techKey(name);
        if (!key) return;
        tech.add(key);
        if (!state.techLabels.has(key)) state.techLabels.set(key, techLabel(name));
      });
      const item = {
        id: project.id,
        project,
        category: project.category,
        title: String(project.title).toLowerCase(),
        tech,
        techText: Array.from(tech).join(" "),
        live: liveUrlOf(project),
        source: sourceUrlOf(project),
        updated: String(project.updated || ""),
        search: [
          project.title, project.eyebrow, project.category, project.description, project.story,
          project.status, ...(project.stack || []), ...(project.highlights || [])
        ].join(" ").toLowerCase()
      };
      state.byId.set(item.id, item);
      return item;
    });
    const names = Array.from(new Set(projects.map((project) => project.category)));
    state.categories = [
      ...CATEGORY_ORDER.filter((name) => names.includes(name)),
      ...names.filter((name) => !CATEGORY_ORDER.includes(name)).sort((a, b) => a.localeCompare(b))
    ];
  }

  function queryScore(item) {
    if (!state.terms.length) return 1;
    let score = 0;
    for (const term of state.terms) {
      if (!item.search.includes(term)) return 0;
      if (item.title.includes(term)) score += 10;
      else if (item.category.toLowerCase().includes(term) || item.techText.includes(term)) score += 4;
      else score += 1;
    }
    return score;
  }

  function matches(item, options = {}) {
    const { ignoreCategory = false, ignoreFlag = "", ignoreTech = "" } = options;
    if (!ignoreCategory && state.category !== "All" && item.category !== state.category) return false;
    for (const flag of state.flags) {
      if (flag !== ignoreFlag && !FLAGS[flag].test(item)) return false;
    }
    for (const key of state.tech) {
      if (key !== ignoreTech && !item.tech.has(key)) return false;
    }
    return queryScore(item) > 0;
  }

  const byTitle = (a, b) => a.project.title.localeCompare(b.project.title);
  const byUpdated = (a, b) => b.updated.localeCompare(a.updated);
  const byFeatured = (a, b) => Number(Boolean(b.project.featured)) - Number(Boolean(a.project.featured));
  const byLive = (a, b) => Number(Boolean(b.live)) - Number(Boolean(a.live));

  function effectiveSort() {
    if (!state.sortTouched) return state.terms.length ? "best" : "featured";
    return state.sort;
  }

  function sortItems(items, sort) {
    const list = [...items];
    switch (sort) {
      case "az": return list.sort(byTitle);
      case "recent": return list.sort((a, b) => byUpdated(a, b) || byTitle(a, b));
      case "live": return list.sort((a, b) => byLive(a, b) || byUpdated(a, b) || byTitle(a, b));
      case "best": return list.sort((a, b) => queryScore(b) - queryScore(a) || byFeatured(a, b) || byUpdated(a, b) || byTitle(a, b));
      default: return list.sort((a, b) => byFeatured(a, b) || byUpdated(a, b) || byTitle(a, b));
    }
  }

  /* ---------- Markup ---------- */

  function coverButton(item, label) {
    const project = item.project;
    const cover = localAsset(project.cover);
    return '<button type="button" class="project-cover" data-open-project="' + esc(item.id) + '" data-initial="' + esc(initials(project.title)) +
      '" aria-label="' + esc(label || ("Open details for " + project.title)) + '">' +
      (cover ? '<img src="' + esc(cover) + '" alt="" loading="lazy" decoding="async" width="1200" height="700">' : "") +
      '<span class="cover-overlay"></span><span class="cover-open">Open project ↗</span></button>';
  }

  function pillsMarkup(item) {
    const project = item.project;
    const source = item.source
      ? '<span class="source-pill">Public source</span>'
      : '<span class="source-pill private">Source hidden</span>';
    const status = item.live
      ? '<span class="status-pill status-live">Live preview</span>'
      : '<span class="status-pill ' + statusClass(project) + '">' + esc(project.status || "In index") + '</span>';
    return source + status;
  }

  function actionsMarkup(item) {
    return (item.live ? externalLink(item.live, "Live preview", "card-action live") : "") +
      (item.source ? externalLink(item.source, "Source", "card-action") : "") +
      '<button class="card-action spacer" type="button" data-open-project="' + esc(item.id) + '">Details <span aria-hidden="true">→</span></button>';
  }

  function createCard(item, spotlight = false) {
    const project = item.project;
    const tags = (project.stack || []).slice(0, spotlight ? 6 : 4).map((tag) => '<span class="tech-tag">' + esc(tag) + '</span>').join("");
    const highlights = spotlight
      ? '<ul class="spotlight-highlights">' + (project.highlights || []).slice(0, 3).map((line) => '<li>' + esc(line) + '</li>').join("") + '</ul>'
      : "";
    const html =
      '<article class="project-card' + (spotlight ? " is-spotlight" : "") + '" data-project-card="' + esc(item.id) + '">' +
      coverButton(item) +
      '<div class="card-body">' +
      (spotlight ? '<p class="spotlight-eyebrow">' + esc(project.eyebrow || project.category) + '</p>' : "") +
      '<div class="card-meta">' + pillsMarkup(item) + '</div>' +
      '<div class="card-title-row"><h3 class="card-title">' + esc(project.title) + '</h3>' +
      (spotlight ? "" : '<span class="card-category">' + esc(project.category) + '</span>') + '</div>' +
      '<p class="card-description">' + esc(project.description || "A project entry in the work index.") + '</p>' +
      highlights +
      '<div class="tag-row">' + tags + '</div>' +
      '<div class="card-footer">' + actionsMarkup(item) + '</div></div></article>';
    const template = document.createElement("template");
    template.innerHTML = html.trim();
    return template.content.firstElementChild;
  }

  function staggerIn(container) {
    if (reducedMotion()) return;
    $$(".project-card", container).slice(0, 12).forEach((card, index) => card.style.setProperty("--i", String(index)));
    container.classList.add("is-entering");
    window.setTimeout(() => container.classList.remove("is-entering"), 1100);
  }

  /* ---------- Rendering ---------- */

  function renderFeatured() {
    const featured = sortItems(state.items.filter(FLAGS.featured.test), "featured").slice(0, FEATURED_LIMIT);
    els.featured.replaceChildren(...featured.map((item, index) => createCard(item, index === 0)));
    els.featured.classList.toggle("has-spotlight", featured.length > 0);
    $$(".project-cover img", els.featured).forEach((img) => { img.loading = "eager"; });
    staggerIn(els.featured);
  }

  function renderShowcase() {
    const pool = sortItems(state.items.filter((item) => item.project.featured && localAsset(item.project.cover)), "featured");
    const picks = [];
    const seen = new Set();
    pool.forEach((item) => {
      if (picks.length < 3 && !seen.has(item.category)) { seen.add(item.category); picks.push(item); }
    });
    pool.forEach((item) => { if (picks.length < 3 && !picks.includes(item)) picks.push(item); });
    if (!picks.length) { els.heroShowcase.hidden = true; return; }
    els.heroShowcase.hidden = false;
    els.heroShowcase.innerHTML = picks.map((item, index) =>
      '<button type="button" class="showcase-card showcase-' + index + '" data-open-project="' + esc(item.id) +
      '" data-initial="' + esc(initials(item.project.title)) + '">' +
      '<img src="' + esc(localAsset(item.project.cover)) + '" alt="" decoding="async" width="1200" height="700"' +
      (index === 0 ? ' fetchpriority="high"' : ' loading="lazy"') + '>' +
      '<span class="showcase-caption"><strong>' + esc(item.project.title) + '</strong><small>' + esc(item.category) + '</small></span></button>'
    ).join("");
  }

  function renderStats() {
    const total = state.items.length;
    const live = state.items.filter((item) => item.live).length;
    const publicSources = state.items.filter((item) => item.source).length;
    const latest = state.items.reduce((max, item) => (item.updated > max ? item.updated : max), "");
    els.heroTotal.textContent = String(total).padStart(2, "0");
    els.heroCategories.textContent = String(state.categories.length).padStart(2, "0");
    els.heroLive.textContent = String(live).padStart(2, "0");
    els.navCount.textContent = String(total).padStart(2, "0");
    els.summary.textContent = plural(total, "project") + " · " + plural(state.categories.length, "discipline") + " · " + plural(live, "live preview");
    els.footerStats.textContent = plural(total, "project") + " · " + plural(live, "live preview") + " · " +
      plural(publicSources, "public source") + (latest ? " · Catalog updated " + latest : "");
  }

  function buildChips() {
    els.categoryFilters.innerHTML = ["All", ...state.categories].map((name) =>
      '<button class="filter-chip" type="button" data-category="' + esc(name) + '" aria-pressed="false">' +
      esc(name === "All" ? "All projects" : name) + ' <span data-count>0</span></button>'
    ).join("");

    const counts = new Map();
    state.items.forEach((item) => item.tech.forEach((key) => counts.set(key, (counts.get(key) || 0) + 1)));
    const keys = Array.from(counts.keys())
      .filter((key) => counts.get(key) >= MIN_TECH_PROJECTS || state.tech.has(key))
      .sort((a, b) => counts.get(b) - counts.get(a) || state.techLabels.get(a).localeCompare(state.techLabels.get(b)));
    els.techFilters.innerHTML = keys.map((key) =>
      '<button class="filter-chip tech-chip" type="button" data-tech="' + esc(key) + '" aria-pressed="false">' +
      esc(state.techLabels.get(key)) + ' <span data-count>0</span></button>'
    ).join("");
  }

  function setChip(chip, count, active) {
    const counter = $("[data-count]", chip);
    if (counter) counter.textContent = String(count);
    chip.classList.toggle("is-active", active);
    chip.setAttribute("aria-pressed", String(active));
    chip.classList.toggle("is-empty", count === 0 && !active);
    chip.disabled = count === 0 && !active;
  }

  function updateChips() {
    $$("[data-category]", els.categoryFilters).forEach((chip) => {
      const name = chip.dataset.category;
      const count = state.items.filter((item) => matches(item, { ignoreCategory: true }) && (name === "All" || item.category === name)).length;
      setChip(chip, count, name === state.category);
    });
    $$("[data-flag]", els.quickFilters).forEach((chip) => {
      const flag = chip.dataset.flag;
      const active = state.flags.has(flag);
      const count = state.items.filter((item) =>
        matches(item, { ignoreFlag: flag }) && (active || FLAGS[flag].test(item))
      ).length;
      setChip(chip, count, active);
    });
    $$("[data-tech]", els.techFilters).forEach((chip) => {
      const key = chip.dataset.tech;
      const active = state.tech.has(key);
      const count = state.items.filter((item) =>
        matches(item, { ignoreTech: key }) && (active || item.tech.has(key))
      ).length;
      setChip(chip, count, active);
    });
    els.techActive.hidden = state.tech.size === 0;
    els.techActive.textContent = String(state.tech.size);
  }

  function pill(kind, value, text) {
    return '<button type="button" class="active-pill" data-remove="' + kind + '" data-value="' + esc(value) + '" aria-label="Remove filter: ' + esc(text) + '">' +
      esc(text) + ' <span aria-hidden="true">×</span></button>';
  }

  function updateActiveFilters() {
    const pills = [];
    if (state.query.trim()) pills.push(pill("query", "", "Search: " + state.query.trim()));
    if (state.category !== "All") pills.push(pill("category", state.category, state.category));
    state.flags.forEach((flag) => pills.push(pill("flag", flag, FLAGS[flag].label)));
    state.tech.forEach((key) => pills.push(pill("tech", key, state.techLabels.get(key) || key)));
    els.activeFilters.innerHTML = pills.join("");
    els.activeFilters.hidden = pills.length === 0;
    els.clear.hidden = pills.length === 0;
  }

  function update({ writeHistory = true } = {}) {
    const sort = effectiveSort();
    if (!state.sortTouched) els.sort.value = sort;
    const results = sortItems(state.items.filter((item) => matches(item)), sort);
    els.grid.replaceChildren(...results.map((item) => state.cards.get(item.id)));
    els.grid.hidden = results.length === 0;
    els.empty.hidden = results.length > 0;
    els.resultCount.innerHTML = "<strong>" + results.length + "</strong> of " + plural(state.items.length, "project");
    updateChips();
    updateActiveFilters();
    if (writeHistory) writeUrl();
  }

  function resetFilters() {
    state.category = "All";
    state.query = "";
    state.terms = [];
    state.tech.clear();
    state.flags.clear();
    els.search.value = "";
  }

  function setQuery(value) {
    state.query = value;
    state.terms = value.toLowerCase().split(/\s+/).filter(Boolean);
  }

  function scrollToIndex() {
    const target = document.getElementById("project-index");
    if (target) target.scrollIntoView({ behavior: reducedMotion() ? "auto" : "smooth", block: "start" });
  }

  /* ---------- URL state ---------- */

  function readUrl() {
    const params = new URLSearchParams(window.location.search);
    setQuery((params.get("q") || "").slice(0, 120));
    els.search.value = state.query;
    const category = params.get("cat");
    if (category && state.categories.includes(category)) state.category = category;
    (params.get("tech") || "").split(",").map((key) => key.trim().toLowerCase())
      .filter((key) => state.techLabels.has(key)).forEach((key) => state.tech.add(key));
    (params.get("f") || "").split(",").map((flag) => flag.trim()).filter((flag) => FLAGS[flag]).forEach((flag) => state.flags.add(flag));
    const sort = params.get("sort");
    if (SORTS.includes(sort)) { state.sort = sort; state.sortTouched = true; els.sort.value = sort; }
    return params.get("project") || "";
  }

  function writeUrl() {
    const params = new URLSearchParams();
    if (state.query.trim()) params.set("q", state.query.trim());
    if (state.category !== "All") params.set("cat", state.category);
    if (state.tech.size) params.set("tech", Array.from(state.tech).join(","));
    if (state.flags.size) params.set("f", Array.from(state.flags).join(","));
    if (state.sortTouched) params.set("sort", state.sort);
    if (state.openId) params.set("project", state.openId);
    const query = params.toString();
    try {
      window.history.replaceState(null, "", window.location.pathname + (query ? "?" + query : "") + window.location.hash);
    } catch (_) { /* file:// and sandboxed contexts may refuse history updates */ }
  }

  /* ---------- Project dialog and gallery ---------- */

  function buildSlides(project) {
    const gallery = (project.gallery || project.screenshots || [])
      .filter((entry) => entry && localAsset(entry.src))
      .map((entry, index) => ({ src: entry.src, alt: entry.alt || (project.title + " · frame " + (index + 1)) }));
    const cover = localAsset(project.cover);
    const slides = [];
    if (cover && !gallery.some((entry) => entry.src === cover)) slides.push({ src: cover, alt: project.title + " cover artwork" });
    return slides.concat(gallery);
  }

  function relatedItems(item) {
    return state.items
      .filter((other) => other.id !== item.id)
      .map((other) => {
        let score = other.category === item.category ? 2 : 0;
        other.tech.forEach((key) => { if (item.tech.has(key)) score += 1; });
        return { other, score };
      })
      .filter((entry) => entry.score > 0)
      .sort((a, b) => b.score - a.score || byFeatured(a.other, b.other) || byUpdated(a.other, b.other) || byTitle(a.other, b.other))
      .slice(0, 3)
      .map((entry) => entry.other);
  }

  function dialogMarkup(item) {
    const project = item.project;
    const slides = state.slides;
    const stack = (project.stack || []).map((name) => {
      const key = techKey(name);
      return '<button type="button" class="tech-tag tech-tag-button" data-filter-tech="' + esc(key) + '" title="Show all projects using ' + esc(techLabel(name)) + '">' + esc(name) + '</button>';
    }).join("");
    const highlights = (project.highlights || []).map((line) => '<li>' + esc(line) + '</li>').join("");
    const viewer = slides.length
      ? '<div class="viewer"><button type="button" class="viewer-stage" data-open-lightbox aria-label="Enlarge image"><img id="viewer-image" src="' + esc(slides[0].src) + '" alt="' + esc(slides[0].alt) + '" decoding="async"></button>' +
        (slides.length > 1
          ? '<button type="button" class="viewer-nav viewer-prev" data-viewer-step="-1" aria-label="Previous image">←</button>' +
            '<button type="button" class="viewer-nav viewer-next" data-viewer-step="1" aria-label="Next image">→</button>'
          : "") +
        '<span class="viewer-count" id="viewer-count"></span></div>' +
        (slides.length > 1
          ? '<div class="viewer-thumbs">' + slides.map((slide, index) =>
              '<button type="button" class="viewer-thumb" data-slide="' + index + '" aria-label="Show image ' + (index + 1) + ' of ' + slides.length + '"><img src="' + esc(slide.src) + '" alt="" loading="lazy" decoding="async"></button>'
            ).join("") + '</div>'
          : "")
      : '<div class="viewer viewer-empty" data-initial="' + esc(initials(project.title)) + '"></div>';
    const related = relatedItems(item);
    const relatedMarkup = related.length
      ? '<section class="dialog-related"><h3>Related projects</h3><div class="related-grid">' + related.map((other) =>
          '<button type="button" class="related-card" data-open-project="' + esc(other.id) + '"><span class="related-thumb" data-initial="' + esc(initials(other.project.title)) + '">' +
          (localAsset(other.project.cover) ? '<img src="' + esc(localAsset(other.project.cover)) + '" alt="" loading="lazy" decoding="async">' : "") +
          '</span><span class="related-copy"><strong>' + esc(other.project.title) + '</strong><small>' + esc(other.category) + '</small></span></button>'
        ).join("") + '</div></section>'
      : "";
    const actions =
      (item.live ? externalLink(item.live, "Open live preview", "button button-primary") : "") +
      (item.source ? externalLink(item.source, "View public source", "button button-secondary") : "") +
      '<button class="button button-ghost" type="button" data-copy-link="' + esc(item.id) + '">Copy link</button>';
    const note = project.demoNote ||
      (item.source ? "Public repository linked; live demo availability depends on the project." : "No source repository link is exposed in this catalog entry.");
    return viewer +
      '<div class="dialog-body">' +
      '<p class="dialog-eyebrow">' + esc(project.eyebrow || project.category) + '</p>' +
      '<div class="dialog-title-row"><h2 id="dialog-title">' + esc(project.title) + '</h2>' +
      '<span class="source-pill' + (item.source ? "" : " private") + '">' + (item.source ? "Public source" : "Source hidden") + '</span></div>' +
      '<p class="dialog-description">' + esc(project.description) + '</p>' +
      '<div class="dialog-actions">' + actions + '</div>' +
      '<div class="dialog-grid">' +
      '<section class="dialog-section"><h3>About this project</h3><p>' + esc(project.story || project.description) + '</p>' +
      (highlights ? '<h3 class="spaced">Highlights</h3><ul class="dialog-highlights">' + highlights + '</ul>' : "") + '</section>' +
      '<aside class="dialog-section dialog-facts"><dl>' +
      '<div><dt>Category</dt><dd>' + esc(project.category) + '</dd></div>' +
      '<div><dt>Status</dt><dd>' + esc(project.status || "In index") + '</dd></div>' +
      '<div><dt>Last repository update</dt><dd>' + esc(project.updated || "Not listed") + '</dd></div>' +
      '<div><dt>Live preview</dt><dd>' + (item.live ? "Listed" : "Not linked") + '</dd></div></dl>' +
      '<h3 class="spaced">Stack / tools</h3><div class="dialog-stack">' + stack + '</div></aside></div>' +
      '<div class="dialog-note">' + esc(note) + '</div>' + relatedMarkup + '</div>';
  }

  function openProject(projectId) {
    const item = state.byId.get(projectId);
    if (!item) return;
    state.openId = item.id;
    state.slides = buildSlides(item.project);
    state.slideIndex = 0;
    els.dialogContent.innerHTML = dialogMarkup(item);
    setSlide(0);
    if (!els.dialog.open && typeof els.dialog.showModal === "function") els.dialog.showModal();
    // Related-project navigation replaces dialog content while the modal stays open;
    // restore focus to its stable close control instead of a removed related-project button.
    const closeButton = $(".dialog-close", els.dialog);
    if (closeButton) closeButton.focus({ preventScroll: true });
    els.dialog.scrollTop = 0;
    writeUrl();
  }

  function closeDialog() {
    if (els.imageDialog.open) els.imageDialog.close();
    if (els.dialog.open) els.dialog.close();
  }

  function setSlide(index) {
    const count = state.slides.length;
    if (!count) return;
    state.slideIndex = (index + count) % count;
    const slide = state.slides[state.slideIndex];
    const image = $("#viewer-image");
    if (image) {
      const stage = image.closest(".viewer-stage");
      if (stage) stage.classList.remove("image-missing");
      image.src = slide.src;
      image.alt = slide.alt;
    }
    const label = $("#viewer-count");
    if (label) label.textContent = (state.slideIndex + 1) + " / " + count;
    $$(".viewer-thumb").forEach((thumb, position) => {
      const active = position === state.slideIndex;
      thumb.classList.toggle("is-active", active);
      thumb.setAttribute("aria-current", String(active));
    });
    if (els.imageDialog.open) updateLightbox();
  }

  function openLightbox() {
    if (!state.slides.length) return;
    updateLightbox();
    if (!els.imageDialog.open && typeof els.imageDialog.showModal === "function") els.imageDialog.showModal();
  }

  function updateLightbox() {
    const slide = state.slides[state.slideIndex];
    if (!slide) return;
    els.lightboxImage.src = slide.src;
    els.lightboxImage.alt = slide.alt || "Project image";
    els.lightboxCaption.textContent = (state.slideIndex + 1) + " / " + state.slides.length + " · " + (slide.alt || "");
    $(".image-prev", els.imageDialog).disabled = state.slides.length < 2;
    $(".image-next", els.imageDialog).disabled = state.slides.length < 2;
  }

  async function copyProjectLink(projectId, button) {
    const url = new URL(window.location.href);
    url.search = "";
    url.hash = "";
    url.searchParams.set("project", projectId);
    const original = button.textContent;
    let label = "Link copied";
    try { await navigator.clipboard.writeText(url.toString()); } catch (_) { label = "Copy failed"; }
    button.textContent = label;
    window.setTimeout(() => { button.textContent = original; }, 1800);
  }

  /* ---------- Footer ---------- */

  function renderFooter() {
    const counts = new Map();
    state.items.forEach((item) => counts.set(item.category, (counts.get(item.category) || 0) + 1));
    els.footerCategories.innerHTML = state.categories.map((name) =>
      '<li><a href="?cat=' + encodeURIComponent(name) + '#project-index" data-footer-category="' + esc(name) + '">' +
      esc(name) + ' <span>' + counts.get(name) + '</span></a></li>'
    ).join("") + '<li><a href="#project-index" data-footer-category="All">All projects <span>' + state.items.length + '</span></a></li>';
    els.footerYear.textContent = String(new Date().getFullYear());
  }

  /* ---------- Theme, header, navigation ---------- */

  function setTheme(theme) {
    root.dataset.theme = theme;
    try { localStorage.setItem("awesome-projects-theme", theme); } catch (_) {}
    const nextLabel = theme === "light" ? "Dark mode" : "Light mode";
    els.themeToggle.setAttribute("aria-label", "Switch to " + nextLabel.toLowerCase());
    els.themeToggle.title = "Switch to " + nextLabel.toLowerCase();
    $(".theme-label", els.themeToggle).textContent = nextLabel;
    const meta = $('meta[name="theme-color"]');
    if (meta) meta.content = theme === "light" ? "#f4f2eb" : "#101114";
  }

  function initTheme() {
    let saved = "";
    try { saved = localStorage.getItem("awesome-projects-theme") || ""; } catch (_) {}
    const system = window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
    setTheme(saved === "light" || saved === "dark" ? saved : system);
  }

  function setMenu(open) {
    els.nav.dataset.open = String(open);
    els.menuToggle.setAttribute("aria-expanded", String(open));
    els.menuToggle.setAttribute("aria-label", open ? "Close navigation menu" : "Open navigation menu");
  }

  function initScrollSpy() {
    if (!("IntersectionObserver" in window)) return;
    const setActive = (id) => $$("[data-spy]").forEach((link) => {
      if (link.dataset.spy === id) link.setAttribute("aria-current", "true"); else link.removeAttribute("aria-current");
    });
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => { if (entry.isIntersecting) setActive(entry.target.id); });
    }, { rootMargin: "-35% 0px -60% 0px" });
    ["featured", "project-index", "about-index"].forEach((id) => {
      const section = document.getElementById(id);
      if (section) observer.observe(section);
    });
    const hero = $(".hero");
    if (hero) new IntersectionObserver((entries) => {
      entries.forEach((entry) => { if (entry.isIntersecting) setActive(""); });
    }, { rootMargin: "-35% 0px -60% 0px" }).observe(hero);
  }

  /* ---------- Events ---------- */

  function bindEvents() {
    els.search.addEventListener("input", () => { setQuery(els.search.value); update(); });
    els.search.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && els.search.value) { event.stopPropagation(); setQuery(""); els.search.value = ""; update(); }
    });
    els.sort.addEventListener("change", () => { state.sort = els.sort.value; state.sortTouched = true; update(); });
    els.clear.addEventListener("click", () => { resetFilters(); update(); });
    els.emptyClear.addEventListener("click", () => { resetFilters(); update(); });
    els.retry.addEventListener("click", () => { init(); });

    els.categoryFilters.addEventListener("click", (event) => {
      const chip = event.target.closest("[data-category]");
      if (!chip) return;
      state.category = chip.dataset.category || "All";
      update();
    });
    els.quickFilters.addEventListener("click", (event) => {
      const chip = event.target.closest("[data-flag]");
      if (!chip) return;
      const flag = chip.dataset.flag;
      if (state.flags.has(flag)) state.flags.delete(flag); else state.flags.add(flag);
      update();
    });
    els.techFilters.addEventListener("click", (event) => {
      const chip = event.target.closest("[data-tech]");
      if (!chip) return;
      const key = chip.dataset.tech;
      if (state.tech.has(key)) state.tech.delete(key); else state.tech.add(key);
      update();
    });
    els.activeFilters.addEventListener("click", (event) => {
      const button = event.target.closest("[data-remove]");
      if (!button) return;
      const { remove, value } = button.dataset;
      if (remove === "query") { setQuery(""); els.search.value = ""; }
      if (remove === "category") state.category = "All";
      if (remove === "flag") state.flags.delete(value);
      if (remove === "tech") state.tech.delete(value);
      update();
    });

    document.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof Element)) return;

      const opener = target.closest("[data-open-project]");
      if (opener) { openProject(opener.dataset.openProject); return; }

      const lightbox = target.closest("[data-open-lightbox]");
      if (lightbox) { openLightbox(); return; }
      const step = target.closest("[data-viewer-step]");
      if (step) { setSlide(state.slideIndex + Number(step.dataset.viewerStep)); return; }
      const thumb = target.closest("[data-slide]");
      if (thumb) { setSlide(Number(thumb.dataset.slide)); return; }

      const techButton = target.closest("[data-filter-tech]");
      if (techButton) {
        resetFilters();
        state.tech.add(techButton.dataset.filterTech);
        closeDialog();
        update();
        els.techPanel.open = true;
        scrollToIndex();
        return;
      }
      const copy = target.closest("[data-copy-link]");
      if (copy) { copyProjectLink(copy.dataset.copyLink, copy); return; }

      const footerCategory = target.closest("[data-footer-category]");
      if (footerCategory) {
        event.preventDefault();
        resetFilters();
        state.category = footerCategory.dataset.footerCategory || "All";
        update();
        scrollToIndex();
        return;
      }

      if (target.closest("#site-nav a")) setMenu(false);

      const card = target.closest("[data-project-card]");
      if (card && !target.closest("a, button")) openProject(card.dataset.projectCard);
    });

    els.menuToggle.addEventListener("click", () => setMenu(els.nav.dataset.open !== "true"));
    els.dialog.addEventListener("click", (event) => { if (event.target === els.dialog) closeDialog(); });
    els.dialog.addEventListener("close", () => { state.openId = ""; writeUrl(); });
    els.imageDialog.addEventListener("click", (event) => { if (event.target === els.imageDialog) els.imageDialog.close(); });
    $(".image-prev", els.imageDialog).addEventListener("click", () => setSlide(state.slideIndex - 1));
    $(".image-next", els.imageDialog).addEventListener("click", () => setSlide(state.slideIndex + 1));

    let touchStartX = null;
    els.imageDialog.addEventListener("touchstart", (event) => { touchStartX = event.changedTouches[0].clientX; }, { passive: true });
    els.imageDialog.addEventListener("touchend", (event) => {
      if (touchStartX === null || state.slides.length < 2) return;
      const delta = event.changedTouches[0].clientX - touchStartX;
      touchStartX = null;
      if (Math.abs(delta) > 50) setSlide(state.slideIndex + (delta < 0 ? 1 : -1));
    }, { passive: true });

    // Images that fail to load fall back to a lettered placeholder (see .image-missing in styles.css).
    document.addEventListener("error", (event) => {
      const image = event.target;
      if (!(image instanceof HTMLImageElement)) return;
      const holder = image.closest(".project-cover, .showcase-card, .viewer-stage, .viewer-thumb, .related-thumb");
      if (holder) holder.classList.add("image-missing");
    }, true);

    document.addEventListener("keydown", (event) => {
      const tag = document.activeElement ? document.activeElement.tagName : "";
      const typing = ["INPUT", "TEXTAREA", "SELECT"].includes(tag);
      if (event.key === "/" && !typing && !els.dialog.open && !event.metaKey && !event.ctrlKey) {
        event.preventDefault();
        els.search.focus();
      }
      if (event.key === "Escape" && els.nav.dataset.open === "true") setMenu(false);
      if ((event.key === "ArrowLeft" || event.key === "ArrowRight") && !typing && state.slides.length > 1 && (els.imageDialog.open || els.dialog.open)) {
        setSlide(state.slideIndex + (event.key === "ArrowRight" ? 1 : -1));
      }
    });

    window.addEventListener("scroll", () => els.header.classList.toggle("is-scrolled", window.scrollY > 8), { passive: true });
    window.addEventListener("resize", () => { if (window.innerWidth > 860) setMenu(false); });
    els.themeToggle.addEventListener("click", () => setTheme(root.dataset.theme === "light" ? "dark" : "light"));
  }

  /* ---------- Boot ---------- */

  function showLoadError(error) {
    console.error("Unable to load project catalog:", error);
    els.featured.replaceChildren();
    els.grid.replaceChildren();
    els.heroShowcase.hidden = true;
    els.summary.textContent = "Catalog could not be loaded.";
    els.resultCount.textContent = "Please check projects.json and reload.";
    els.footerStats.textContent = "Project catalog unavailable.";
    els.empty.hidden = true;
    els.loadError.hidden = false;
  }

  async function init() {
    els.loadError.hidden = true;
    try {
      const response = await fetch("projects.json", { cache: "no-store" });
      if (!response.ok) throw new Error("Project catalog returned HTTP " + response.status);
      const projects = await response.json();
      if (!Array.isArray(projects)) throw new Error("Project catalog must be a JSON array.");
      buildModel(projects.filter((project) => project && project.id && project.title && project.category));
      resetFilters();
      state.sortTouched = false;
      state.sort = "featured";
      state.cards = new Map(state.items.map((item) => [item.id, createCard(item)]));
      const openId = readUrl();
      buildChips();
      renderStats();
      renderShowcase();
      renderFeatured();
      renderFooter();
      update({ writeHistory: false });
      staggerIn(els.grid);
      if (openId && state.byId.has(openId)) openProject(openId);
    } catch (error) {
      showLoadError(error);
    }
  }

  initTheme();
  bindEvents();
  initScrollSpy();
  init();
})();
