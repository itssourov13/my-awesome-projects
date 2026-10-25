(() => {
  "use strict";

  const root = document.documentElement;
  const $ = (selector, scope = document) => scope.querySelector(selector);
  const els = {
    metrics: { total: $("#metric-total"), categories: $("#metric-categories"), pub: $("#metric-public"), live: $("#metric-live") },
    navCount: $("#nav-project-count"),
    collage: $("#hero-collage"),
    featured: $("#featured-grid"),
    grid: $("#project-grid"),
    search: $("#project-search"),
    sort: $("#project-sort"),
    filters: $("#category-filters"),
    summary: $("#project-summary"),
    resultCount: $("#result-count"),
    clear: $("#clear-filters"),
    empty: $("#empty-state"),
    emptyTitle: $("#empty-title"),
    emptyText: $("#empty-text"),
    emptyButton: $("#empty-clear"),
    dialog: $("#project-dialog"),
    dialogContent: $("#dialog-content"),
    imageDialog: $("#image-dialog"),
    lightboxImage: $("#lightbox-image"),
    lightboxCaption: $("#lightbox-caption"),
    themeToggle: $("#theme-toggle"),
    menuToggle: $("#menu-toggle"),
    nav: $("#site-nav")
  };

  const FEATURED_LIMIT = 6;
  const CATEGORY_ORDER = ["Cybersecurity", "AI & Developer Tools", "Web Apps", "Creative & 3D", "Mobile Apps", "Utilities", "Writing & Publishing", "Open Source"];
  const CATEGORY_COLORS = ["#c6f56c", "#8ab4ff", "#ffaf7b", "#b7a2ff", "#ff8aa8", "#6fe0c5", "#ffd36b", "#9fb3c8"];
  const state = {
    projects: [], byId: new Map(), nodes: new Map(), categories: [],
    category: "All", query: "", sort: "featured",
    images: [], imageIndex: 0, projectId: ""
  };

  /* ---------- helpers ---------- */
  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);

  const parseHttps = (url) => {
    try { const parsed = new URL(url); return parsed.protocol === "https:" ? parsed : null; }
    catch { return null; }
  };
  const liveUrl = (project) => (parseHttps(project.liveUrl) ? project.liveUrl : "");
  const sourceUrl = (project) => {
    if (project.sourceAccess !== "public") return "";
    const parsed = parseHttps(project.sourceUrl);
    return parsed && ["github.com", "www.github.com"].includes(parsed.hostname.toLowerCase()) ? project.sourceUrl : "";
  };
  const galleryOf = (project) => (project.gallery || project.screenshots || []).filter((item) => item && item.src);
  const pad = (n) => String(n).padStart(2, "0");
  const plural = (n, word) => n + " " + word + (n === 1 ? "" : "s");

  const formatDate = (iso) => {
    const date = new Date(String(iso || "") + "T00:00:00Z");
    return Number.isNaN(date.getTime()) ? "" :
      date.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
  };
  const statusTone = (project) => {
    const status = String(project.status || "").toLowerCase();
    if (status.includes("live preview")) return "status-live";
    if (/pending|needs verification|needs documentation/.test(status)) return "status-pending";
    return "";
  };
  const catColor = (category) => CATEGORY_COLORS[Math.max(0, state.categories.indexOf(category)) % CATEGORY_COLORS.length];
  const toNode = (html) => { const t = document.createElement("template"); t.innerHTML = html.trim(); return t.content.firstElementChild; };

  const coverImg = (project, { eager = false, priority = false } = {}) =>
    '<img src="' + esc(project.cover || "") + '" alt="' + esc(project.title) + ' — project cover artwork" width="1200" height="700" ' +
    (eager ? 'loading="eager"' : 'loading="lazy"') + (priority ? ' fetchpriority="high"' : "") + ' decoding="async">';

  const actionsHtml = (project) => {
    const live = liveUrl(project), source = sourceUrl(project);
    return (live ? '<a class="act act-live" href="' + esc(live) + '" target="_blank" rel="noopener noreferrer" aria-label="Live preview of ' + esc(project.title) + ' (opens in a new tab)">Live preview <span aria-hidden="true">↗</span></a>' : "") +
      (source ? '<a class="act" href="' + esc(source) + '" target="_blank" rel="noopener noreferrer" aria-label="Public source of ' + esc(project.title) + ' (opens in a new tab)">Source <span aria-hidden="true">↗</span></a>' : "") +
      (project.sourceAccess !== "public" ? '<span class="act act-muted">Source hidden</span>' : "");
  };
  const chipsHtml = (items, limit) => '<ul class="chips" aria-label="Stack">' +
    (items || []).slice(0, limit).map((item) => "<li>" + esc(item) + "</li>").join("") + "</ul>";

  /* ---------- card builders (each node is built once, then reused) ---------- */
  function buildCard(project) {
    const date = formatDate(project.updated);
    return toNode(
      '<article class="card" data-id="' + esc(project.id) + '" style="--cat:' + catColor(project.category) + '">' +
      '<div class="card-media">' + coverImg(project) +
      '<span class="card-cat"><i class="dot"></i>' + esc(project.category) + "</span>" +
      (project.featured ? '<span class="card-flag">Featured</span>' : "") + "</div>" +
      '<div class="card-body"><div class="card-meta"><span class="status ' + statusTone(project) + '">' + esc(project.status || "In index") + "</span>" +
      (date ? '<time datetime="' + esc(project.updated) + '">' + esc(date) + "</time>" : "") + "</div>" +
      '<h3 class="card-title"><button class="stretch" type="button" data-open-project="' + esc(project.id) + '">' + esc(project.title) + "</button></h3>" +
      '<p class="card-desc">' + esc(project.description || "A project entry in the work index.") + "</p>" +
      chipsHtml(project.stack, 4) +
      '<div class="actions">' + actionsHtml(project) + "</div></div></article>"
    );
  }

  function buildPoster(project, index) {
    const variant = index === 0 ? " poster--lead" : index <= 2 ? " poster--side" : "";
    return toNode(
      '<article class="poster' + variant + '" data-id="' + esc(project.id) + '" style="--cat:' + catColor(project.category) + '">' +
      '<div class="poster-media">' + coverImg(project, { eager: index < 3, priority: index === 0 }) + "</div>" +
      '<div class="poster-body"><p class="poster-eyebrow"><i class="dot"></i>' + esc(project.eyebrow || project.category) + "</p>" +
      '<h3 class="poster-title"><button class="stretch" type="button" data-open-project="' + esc(project.id) + '">' + esc(project.title) + "</button></h3>" +
      '<p class="poster-desc">' + esc(project.description || "") + "</p>" +
      (index === 0 ? chipsHtml(project.stack, 5) : "") +
      '<div class="poster-foot"><span class="status ' + statusTone(project) + '">' + esc(project.status || "In index") + "</span>" +
      '<div class="actions">' + actionsHtml(project) + "</div></div></div></article>"
    );
  }

  /* ---------- sorting, filtering, rendering ---------- */
  const byTitle = (a, b) => a.title.localeCompare(b.title);
  const byRecent = (a, b) => String(b.updated || "").localeCompare(String(a.updated || ""));
  const comparators = {
    az: byTitle,
    recent: (a, b) => byRecent(a, b) || byTitle(a, b),
    featured: (a, b) => Number(Boolean(b.featured)) - Number(Boolean(a.featured)) || byRecent(a, b) || byTitle(a, b)
  };

  function visibleProjects() {
    const terms = state.query.trim().toLowerCase().split(/\s+/).filter(Boolean);
    return state.projects
      .filter((project) => (state.category === "All" || project.category === state.category) &&
        terms.every((term) => project._haystack.includes(term)))
      .sort(comparators[state.sort] || comparators.featured);
  }

  function renderGrid(animate) {
    const list = visibleProjects();
    const fragment = document.createDocumentFragment();
    list.forEach((project) => fragment.appendChild(state.nodes.get(project.id)));
    els.grid.replaceChildren(fragment);
    els.grid.hidden = list.length === 0;
    els.empty.hidden = list.length > 0;
    if (!list.length) {
      els.emptyTitle.textContent = "No projects found";
      els.emptyText.textContent = state.query.trim()
        ? "Nothing matches “" + state.query.trim() + "”" + (state.category === "All" ? "." : " in " + state.category + ".") + " Try a different keyword or clear your filters."
        : "Nothing is listed in this category yet.";
      els.emptyButton.hidden = false;
      els.emptyButton.textContent = "Reset search";
      els.emptyButton.onclick = resetFilters;
    }
    els.resultCount.innerHTML = "<strong>" + list.length + "</strong> of " + plural(state.projects.length, "project") +
      (state.category !== "All" ? " in " + esc(state.category) : "") + (state.query.trim() ? " matching “" + esc(state.query.trim()) + "”" : "");
    els.clear.hidden = state.category === "All" && !state.query.trim();
    if (animate) {
      els.grid.classList.remove("is-refreshing"); void els.grid.offsetWidth; els.grid.classList.add("is-refreshing");
    }
  }

  function renderFilters() {
    const counts = new Map();
    state.projects.forEach((project) => counts.set(project.category, (counts.get(project.category) || 0) + 1));
    const make = (category, label, count) => '<button class="filter-chip" type="button" data-category="' + esc(category) + '" aria-pressed="false">' +
      (category === "All" ? "" : '<i class="dot" style="--cat:' + catColor(category) + '"></i>') + esc(label) + " <small>" + count + "</small></button>";
    els.filters.innerHTML = make("All", "All projects", state.projects.length) +
      state.categories.map((category) => make(category, category, counts.get(category))).join("");
    syncFilters();
  }
  function syncFilters() {
    els.filters.querySelectorAll(".filter-chip").forEach((chip) => {
      const active = chip.dataset.category === state.category;
      chip.classList.toggle("is-active", active);
      chip.setAttribute("aria-pressed", String(active));
    });
  }

  function resetFilters() {
    state.category = "All"; state.query = ""; els.search.value = "";
    syncFilters(); renderGrid(true);
  }

  /* Featured + hero are catalog-only, so they render exactly once. */
  function renderStatic() {
    const featured = state.projects.filter((p) => p.featured).sort(comparators.featured).slice(0, FEATURED_LIMIT);
    const fragment = document.createDocumentFragment();
    featured.forEach((project, index) => fragment.appendChild(buildPoster(project, index)));
    els.featured.replaceChildren(fragment);
    els.featured.closest(".featured-section").hidden = featured.length === 0;

    els.collage.replaceChildren(...featured.slice(0, 3).map((project) => {
      const card = document.createElement("div");
      card.className = "collage-card";
      card.innerHTML = '<img src="' + esc(project.cover) + '" alt="" width="1200" height="700" decoding="async"><span class="collage-tag">' + esc(project.category) + "</span>";
      return card;
    }));

    const publicCount = state.projects.filter((p) => sourceUrl(p)).length;
    const liveCount = state.projects.filter((p) => liveUrl(p)).length;
    els.metrics.total.textContent = pad(state.projects.length);
    els.metrics.categories.textContent = pad(state.categories.length);
    els.metrics.pub.textContent = pad(publicCount);
    els.metrics.live.textContent = pad(liveCount);
    els.navCount.textContent = String(state.projects.length);
    els.summary.textContent = plural(state.projects.length, "project") + " across " + plural(state.categories.length, "discipline") +
      " · " + liveCount + " with a live preview · " + publicCount + " with public source";
  }

  /* ---------- project dialog ---------- */
  function openProject(projectId) {
    const project = state.byId.get(projectId);
    if (!project) return;
    state.projectId = project.id;
    const images = galleryOf(project);
    const date = formatDate(project.updated);
    const isPublic = project.sourceAccess === "public";
    const highlights = (project.highlights || []).map((item) => "<li>" + esc(item) + "</li>").join("");
    const gallery = images.length
      ? '<section class="d-gallery"><h3>Visual gallery · ' + images.length + '</h3><p class="d-gallery-note">These visuals are project artwork and public references, not guaranteed captures of the running application.</p><div class="d-thumbs">' +
        images.map((item, index) => '<button type="button" data-open-image="' + index + '" aria-label="View visual ' + (index + 1) + " of " + images.length + ": " + esc(item.alt || project.title) + '">' +
          '<img src="' + esc(item.src) + '" alt="" width="360" height="480" loading="lazy" decoding="async"><span class="thumb-n">' + pad(index + 1) + "</span></button>").join("") + "</div></section>"
      : "";
    els.dialogContent.innerHTML =
      '<div class="d-hero">' + coverImg(project, { eager: true }) + "</div>" +
      '<div class="d-body" style="--cat:' + catColor(project.category) + '">' +
      '<p class="d-eyebrow"><i class="dot"></i>' + esc(project.eyebrow || project.category) + "</p>" +
      '<div class="d-title-row"><h2 id="dialog-title">' + esc(project.title) + "</h2>" +
      '<span class="pill ' + (isPublic ? "pill-public" : "pill-private") + '">' + (isPublic ? "Public source" : "Source hidden") + "</span></div>" +
      '<p class="d-lede">' + esc(project.description) + "</p>" +
      '<div class="actions">' + actionsHtml(project) + "</div>" +
      '<div class="d-grid"><section><h3>About this project</h3><p class="d-story">' + esc(project.story || project.description) + "</p>" +
      (highlights ? '<ul class="d-highlights">' + highlights + "</ul>" : "") + "</section>" +
      '<dl class="d-facts"><div><dt>Category</dt><dd>' + esc(project.category) + "</dd></div>" +
      '<div><dt>Status</dt><dd><span class="status ' + statusTone(project) + '">' + esc(project.status || "In index") + "</span></dd></div>" +
      '<div><dt>Stack</dt><dd>' + chipsHtml(project.stack, 12) + "</dd></div>" +
      '<div><dt>Live preview</dt><dd>' + (liveUrl(project) ? "Listed" : "Not listed") + "</dd></div>" +
      '<div><dt>Source</dt><dd>' + (isPublic ? "Public repository" : "Not published") + "</dd></div>" +
      (date ? '<div><dt>Last updated</dt><dd>' + esc(date) + "</dd></div>" : "") + "</dl></div>" +
      gallery +
      '<p class="d-note">' + esc(project.demoNote || (isPublic ? "Public repository linked; live demo availability depends on the project." : "No source repository link is exposed in this catalog entry.")) + "</p></div>";
    els.dialogContent.scrollTop = 0;
    if (!els.dialog.open) els.dialog.showModal();
  }

  /* ---------- lightbox ---------- */
  function openImage(index) {
    const project = state.byId.get(state.projectId);
    const images = project ? galleryOf(project) : [];
    if (!images.length) return;
    state.images = images;
    state.imageIndex = (index + images.length) % images.length;
    updateLightbox();
    if (!els.imageDialog.open) els.imageDialog.showModal();
  }
  function stepImage(delta) {
    if (state.images.length < 2) return;
    state.imageIndex = (state.imageIndex + delta + state.images.length) % state.images.length;
    updateLightbox();
  }
  function updateLightbox() {
    const item = state.images[state.imageIndex];
    if (!item) return;
    els.lightboxImage.src = item.src;
    els.lightboxImage.alt = item.alt || "Project visual";
    els.lightboxCaption.textContent = pad(state.imageIndex + 1) + " / " + pad(state.images.length) + (item.alt ? " · " + item.alt : "");
    const multi = state.images.length > 1;
    $(".image-prev", els.imageDialog).disabled = !multi;
    $(".image-next", els.imageDialog).disabled = !multi;
    [1, -1].forEach((d) => { const n = state.images[(state.imageIndex + d + state.images.length) % state.images.length]; if (n) new Image().src = n.src; });
  }

  /* ---------- theme & menu ---------- */
  function setTheme(theme) {
    root.dataset.theme = theme;
    try { localStorage.setItem("awesome-projects-theme", theme); } catch (_) {}
    const next = theme === "light" ? "dark" : "light";
    els.themeToggle.setAttribute("aria-label", "Switch to " + next + " mode");
    els.themeToggle.title = "Switch to " + next + " mode";
    $(".theme-label", els.themeToggle).textContent = next === "light" ? "Light mode" : "Dark mode";
    const meta = $('meta[name="theme-color"]');
    if (meta) meta.content = theme === "light" ? "#f4f2eb" : "#0d0e11";
  }
  function initTheme() {
    let saved = "";
    try { saved = localStorage.getItem("awesome-projects-theme") || ""; } catch (_) {}
    const system = window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
    setTheme(saved === "light" || saved === "dark" ? saved : system);
  }
  function setMenu(open) {
    els.nav.classList.toggle("is-open", open);
    els.menuToggle.setAttribute("aria-expanded", String(open));
    els.menuToggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
  }

  /* ---------- events ---------- */
  els.filters.addEventListener("click", (event) => {
    const chip = event.target.closest("[data-category]");
    if (!chip) return;
    state.category = chip.dataset.category || "All";
    syncFilters(); renderGrid(true);
    chip.scrollIntoView({ inline: "nearest", block: "nearest", behavior: "smooth" });
  });
  els.search.addEventListener("input", () => { state.query = els.search.value; renderGrid(false); });
  els.sort.addEventListener("change", () => { state.sort = els.sort.value; renderGrid(true); });
  els.clear.addEventListener("click", resetFilters);
  els.themeToggle.addEventListener("click", () => setTheme(root.dataset.theme === "light" ? "dark" : "light"));
  els.menuToggle.addEventListener("click", () => setMenu(!els.nav.classList.contains("is-open")));
  els.nav.addEventListener("click", (event) => { if (event.target.closest("a")) setMenu(false); });
  document.addEventListener("click", (event) => {
    if (els.nav.classList.contains("is-open") && !event.target.closest(".site-header")) setMenu(false);
    const opener = event.target.closest("[data-open-project]");
    if (opener) { openProject(opener.dataset.openProject); return; }
    if (event.target.closest("[data-close-dialog]")) { els.dialog.close(); return; }
    if (event.target.closest("[data-close-image]")) { els.imageDialog.close(); return; }
    const thumb = event.target.closest("[data-open-image]");
    if (thumb) openImage(Number(thumb.dataset.openImage));
  });
  els.dialog.addEventListener("click", (event) => { if (event.target === els.dialog) els.dialog.close(); });
  els.imageDialog.addEventListener("click", (event) => {
    if (event.target === els.imageDialog || event.target.classList.contains("lightbox-figure")) els.imageDialog.close();
  });
  $(".image-prev", els.imageDialog).addEventListener("click", () => stepImage(-1));
  $(".image-next", els.imageDialog).addEventListener("click", () => stepImage(1));
  let touchX = null;
  els.imageDialog.addEventListener("touchstart", (event) => { touchX = event.touches[0].clientX; }, { passive: true });
  els.imageDialog.addEventListener("touchend", (event) => {
    if (touchX === null) return;
    const dx = event.changedTouches[0].clientX - touchX; touchX = null;
    if (Math.abs(dx) > 50) stepImage(dx < 0 ? 1 : -1);
  }, { passive: true });
  document.addEventListener("keydown", (event) => {
    if (els.imageDialog.open) {
      if (event.key === "ArrowLeft") { event.preventDefault(); stepImage(-1); }
      else if (event.key === "ArrowRight") { event.preventDefault(); stepImage(1); }
      return;
    }
    if (event.key === "Escape" && els.nav.classList.contains("is-open")) { setMenu(false); els.menuToggle.focus(); return; }
    const typing = ["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement && document.activeElement.tagName);
    if (event.key === "/" && !typing && !els.dialog.open && !event.metaKey && !event.ctrlKey) {
      event.preventDefault(); els.search.focus(); els.search.select();
    }
  });
  document.addEventListener("error", (event) => {
    const img = event.target;
    if (img && img.tagName === "IMG") {
      const holder = img.closest(".card-media, .poster-media, .d-hero, .collage-card");
      if (holder) holder.classList.add("image-missing");
    }
  }, true);

  const revealables = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => entries.forEach((entry) => {
      if (entry.isIntersecting) { entry.target.classList.add("in"); io.unobserve(entry.target); }
    }), { rootMargin: "0px 0px -8% 0px" });
    revealables.forEach((el) => io.observe(el));
  } else revealables.forEach((el) => el.classList.add("in"));

  /* ---------- init ---------- */
  function showError(message) {
    els.featured.closest(".featured-section").hidden = true;
    els.grid.replaceChildren(); els.grid.hidden = true;
    els.summary.textContent = "Catalog could not be loaded.";
    els.resultCount.textContent = "The catalog is unavailable.";
    els.emptyTitle.textContent = "The project index could not load";
    els.emptyText.textContent = message;
    els.emptyButton.hidden = false; els.emptyButton.textContent = "Try again";
    els.emptyButton.onclick = () => { els.empty.hidden = true; els.grid.hidden = false; init(); };
    els.empty.hidden = false;
  }

  function indexCatalog(data) {
    if (!Array.isArray(data)) throw new Error("The catalog must be a JSON array.");
    const valid = data.filter((p) => p && p.id && p.title && p.category);
    if (!valid.length) throw new Error("The catalog has no valid entries.");
    state.projects = valid;
    state.byId.clear(); state.nodes.clear();
    valid.forEach((project) => {
      project._haystack = [project.title, project.eyebrow, project.category, project.description, project.story, project.status,
        ...(project.stack || []), ...(project.highlights || [])].join(" ").toLowerCase();
      state.byId.set(project.id, project);
    });
    const found = [...new Set(valid.map((p) => p.category))];
    state.categories = CATEGORY_ORDER.filter((c) => found.includes(c)).concat(found.filter((c) => !CATEGORY_ORDER.includes(c)).sort());
    valid.forEach((project) => state.nodes.set(project.id, buildCard(project)));
  }

  async function init() {
    initTheme();
    try {
      const response = await fetch("projects.json", { cache: "no-cache" });
      if (!response.ok) throw new Error("The catalog returned HTTP " + response.status + ".");
      indexCatalog(await response.json());
      renderStatic(); renderFilters(); renderGrid(false);
    } catch (error) {
      console.error("Unable to load project catalog:", error);
      showError(error && error.message ? error.message : "The local catalog could not be read.");
    }
  }

  init();
})();
