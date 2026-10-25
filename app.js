(() => {
  "use strict";

  const root = document.documentElement;
  const $ = (selector, scope = document) => scope.querySelector(selector);
  const $$ = (selector, scope = document) => Array.from(scope.querySelectorAll(selector));
  const els = {
    heroTotal: $("#hero-total"),
    heroCategories: $("#hero-categories"),
    navCount: $("#nav-project-count"),
    featured: $("#featured-grid"),
    grid: $("#project-grid"),
    search: $("#project-search"),
    sort: $("#project-sort"),
    filters: $("#category-filters"),
    summary: $("#project-summary"),
    resultCount: $("#result-count"),
    clear: $("#clear-filters"),
    empty: $("#empty-state"),
    dialog: $("#project-dialog"),
    dialogContent: $("#dialog-content"),
    imageDialog: $("#image-dialog"),
    lightboxImage: $("#lightbox-image"),
    lightboxCaption: $("#lightbox-caption"),
    themeToggle: $("#theme-toggle")
  };

  const state = { projects: [], category: "All", query: "", sort: "featured", activeImages: [], imageIndex: 0 };

  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);

  const isSafeHttps = (url) => {
    try { const parsed = new URL(url); return parsed.protocol === "https:"; }
    catch { return false; }
  };

  const externalLink = (url, label, className = "card-action") => {
    if (!url || !isSafeHttps(url)) return "";
    return '<a class="' + className + '" href="' + esc(url) + '" target="_blank" rel="noopener noreferrer">' +
      esc(label) + ' <span aria-hidden="true">↗</span></a>';
  };

  const statusClass = (project) => {
    const status = (project.status || "").toLowerCase();
    if (status.includes("live preview")) return "status-live";
    if (status.includes("pending") || status.includes("needs verification") || status.includes("needs documentation")) return "status-pending";
    return "";
  };

  const imageWithFallback = (src, alt, className = "") =>
    '<img' + (className ? ' class="' + esc(className) + '"' : "") +
    ' src="' + esc(src) + '" alt="' + esc(alt) + '" loading="lazy" decoding="async"' +
    ' onerror="this.closest(\'.project-cover\')?.classList.add(\'image-missing\');this.removeAttribute(\'src\');" />';

  function renderCard(project, featured = false) {
    const sourcePill = project.sourceAccess === "public"
      ? '<span class="source-pill">Public source</span>'
      : '<span class="source-pill private">Source hidden</span>';
    const livePill = project.liveUrl && isSafeHttps(project.liveUrl)
      ? '<span class="status-pill status-live">Preview listed</span>'
      : "";
    const sourceButton = project.sourceAccess === "public" ? externalLink(project.sourceUrl, "Source", "card-action") : "";
    const liveButton = project.liveUrl && isSafeHttps(project.liveUrl)
      ? externalLink(project.liveUrl, "Live preview", "card-action live")
      : "";
    const detailsButton = '<button class="card-action spacer" type="button" data-open-project="' + esc(project.id) + '">Explore details <span aria-hidden="true">↗</span></button>';
    const tags = (project.stack || []).slice(0, 3).map(tag => '<span class="tech-tag">' + esc(tag) + '</span>').join("");
    const desc = project.description || "A project entry in the work index.";
    return '<article class="project-card' + (featured ? ' featured-card' : '') + '" data-project-card="' + esc(project.id) + '">' +
      '<button type="button" class="project-cover" data-open-project="' + esc(project.id) + '" aria-label="Explore ' + esc(project.title) + '">' +
      imageWithFallback(project.cover || "", project.title + " cover artwork") +
      '<span class="cover-overlay"></span><span class="cover-open">Open project ↗</span></button>' +
      '<div class="card-body"><div class="card-meta">' + sourcePill +
      (livePill || '<span class="status-pill ' + statusClass(project) + '">' + esc(project.status || "In index") + '</span>') +
      '</div><div class="card-title-row"><h3 class="card-title">' + esc(project.title) + '</h3><span class="card-category">' + esc(project.category) + '</span></div>' +
      '<p class="card-description">' + esc(desc) + '</p>' +
      '<div class="tag-row">' + tags + '</div>' +
      '<div class="card-footer">' + liveButton + sourceButton + detailsButton + '</div></div></article>';
  }

  function renderFilters() {
    const counts = new Map();
    state.projects.forEach((project) => counts.set(project.category, (counts.get(project.category) || 0) + 1));
    const categories = ["All", ...Array.from(counts.keys()).sort((a, b) => a.localeCompare(b))];
    els.filters.innerHTML = categories.map((category) => {
      const count = category === "All" ? state.projects.length : counts.get(category);
      const active = category === state.category;
      return '<button class="filter-chip' + (active ? ' is-active' : '') + '" type="button" data-category="' + esc(category) +
        '" aria-pressed="' + String(active) + '">' + esc(category === "All" ? "All projects" : category) +
        ' <span>' + count + '</span></button>';
    }).join("");
    els.heroCategories.textContent = counts.size.toString().padStart(2, "0");
  }

  function sortedProjects(projects) {
    const result = [...projects];
    if (state.sort === "az") return result.sort((a, b) => a.title.localeCompare(b.title));
    if (state.sort === "recent") return result.sort((a, b) => (b.updated || "").localeCompare(a.updated || ""));
    return result.sort((a, b) => Number(Boolean(b.featured)) - Number(Boolean(a.featured)) ||
      (b.updated || "").localeCompare(a.updated || "") || a.title.localeCompare(b.title));
  }

  function getFilteredProjects() {
    const query = state.query.trim().toLowerCase();
    return sortedProjects(state.projects.filter((project) => {
      if (state.category !== "All" && project.category !== state.category) return false;
      if (!query) return true;
      const haystack = [
        project.title, project.eyebrow, project.category, project.description, project.story,
        project.status, ...(project.stack || []), ...(project.highlights || [])
      ].join(" ").toLowerCase();
      return haystack.includes(query);
    }));
  }

  function bindProjectOpeners(container) {
    container.querySelectorAll("[data-open-project]").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const project = state.projects.find((entry) => entry.id === button.dataset.openProject);
        if (!project) return;
        els.dialog.dataset.projectId = project.id;
        openProject(project.id);
      });
    });
  }

  function render() {
    const filtered = getFilteredProjects();
    els.grid.innerHTML = filtered.map((project) => renderCard(project)).join("");
    els.grid.hidden = filtered.length === 0;
    els.empty.hidden = filtered.length > 0;
    els.resultCount.innerHTML = '<strong>' + filtered.length + '</strong> of ' + state.projects.length + ' projects';
    els.summary.textContent = state.projects.length + " projects · " + new Set(state.projects.map(p => p.category)).size + " disciplines · updated as work evolves";
    els.clear.hidden = state.category === "All" && !state.query;
    renderFilters();

    const featured = sortedProjects(state.projects.filter((p) => p.featured)).slice(0, 6);
    els.featured.innerHTML = featured.map((project) => renderCard(project, true)).join("");
    els.featured.querySelectorAll(".project-cover img").forEach((img) => img.loading = "eager");
    bindProjectOpeners(els.grid);
    bindProjectOpeners(els.featured);
  }

  function openProject(projectId) {
    const project = state.projects.find((entry) => entry.id === projectId);
    if (!project) return;
    const images = (project.gallery || project.screenshots || []).filter((item) => item && item.src);
    const stack = (project.stack || []).map((item) => '<span class="tech-tag">' + esc(item) + '</span>').join("");
    const highlights = (project.highlights || []).map((item) => '<li>' + esc(item) + '</li>').join("");
    const imageMarkup = images.length
      ? '<section class="dialog-section"><h3>Visual gallery / ' + images.length + ' assets</h3><div class="dialog-images">' +
        images.map((item, index) => '<figure><button type="button" data-open-image="' + index + '" aria-label="View project visual: ' + esc(item.alt || project.title) + '">' +
          '<img src="' + esc(item.src) + '" alt="' + esc(item.alt || project.title) + '" loading="lazy" decoding="async"></button><figcaption>' +
          esc(item.alt || (project.title + " · frame " + (index + 1))) + '</figcaption></figure>').join("") + '</div></section>'
      : '<section class="dialog-section"><h3>Visual gallery</h3><p>Additional interface screenshots can be added to this project\'s local asset folder. The cover above is original catalog artwork, not a captured application screen.</p></section>';
    const actions = [
      project.liveUrl && isSafeHttps(project.liveUrl) ? externalLink(project.liveUrl, "Open live preview", "button button-primary") : "",
      project.sourceAccess === "public" ? externalLink(project.sourceUrl, "View public source", "button button-secondary") : "",
      '<button class="button button-secondary" type="button" data-close-dialog>Back to index</button>'
    ].filter(Boolean).join("");
    els.dialogContent.innerHTML =
      '<div class="dialog-hero">' + imageWithFallback(project.cover || "", project.title + " cover artwork") + '</div>' +
      '<p class="dialog-eyebrow">' + esc(project.eyebrow || project.category) + '</p>' +
      '<div class="dialog-title-row"><h2 id="dialog-title">' + esc(project.title) + '</h2><span class="source-pill' +
      (project.sourceAccess === "public" ? "" : " private") + '">' +
      (project.sourceAccess === "public" ? "Public source" : "Source hidden") + '</span></div>' +
      '<p class="dialog-description">' + esc(project.description) + '</p>' +
      '<div class="dialog-grid"><section class="dialog-section"><h3>About this project</h3><p>' + esc(project.story || project.description) +
      '</p><div style="height:22px"></div><h3>Highlights</h3><ul class="dialog-highlights">' + highlights + '</ul></section>' +
      '<section class="dialog-section"><h3>Stack / tools</h3><div class="dialog-stack">' + stack + '</div><div style="height:22px"></div><h3>Project status</h3><p>' +
      esc(project.status || "In index") + '</p><div style="height:12px"></div><h3>Last repository update</h3><p>' +
      esc(project.updated || "Not listed") + '</p></section></div>' +
      '<div class="dialog-images">' + (images.length ? "" : "") + '</div>' + imageMarkup +
      '<div class="dialog-note">' + esc(project.demoNote || (project.sourceAccess === "public" ? "Public repository linked; live demo availability depends on the project." : "No source repository link is exposed in this catalog entry.")) + '</div>' +
      '<div class="dialog-actions">' + actions + '</div>';

    if (typeof els.dialog.showModal === "function") els.dialog.showModal();
  }

  function openImage(imageIndex) {
    const project = state.projects.find((entry) => entry.id === els.dialog.dataset.projectId);
    const images = project ? (project.gallery || project.screenshots || []).filter((item) => item && item.src) : [];
    if (!images.length) return;
    state.activeImages = images;
    state.imageIndex = (imageIndex + images.length) % images.length;
    updateLightbox();
    if (typeof els.imageDialog.showModal === "function") els.imageDialog.showModal();
  }

  function updateLightbox() {
    const item = state.activeImages[state.imageIndex];
    if (!item) return;
    els.lightboxImage.src = item.src;
    els.lightboxImage.alt = item.alt || "Project screenshot";
    els.lightboxCaption.textContent = (state.imageIndex + 1) + " / " + state.activeImages.length + " · " + (item.alt || "");
    $(".image-prev", els.imageDialog).disabled = state.activeImages.length < 2;
    $(".image-next", els.imageDialog).disabled = state.activeImages.length < 2;
  }

  function closeDialog() { if (els.dialog.open) els.dialog.close(); }

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

  els.filters.addEventListener("click", (event) => {
    const button = event.target.closest("[data-category]");
    if (!button) return;
    state.category = button.dataset.category || "All";
    render();
  });
  els.search.addEventListener("input", () => { state.query = els.search.value; render(); });
  els.sort.addEventListener("change", () => { state.sort = els.sort.value; render(); });
  els.clear.addEventListener("click", () => {
    state.category = "All"; state.query = ""; els.search.value = ""; render();
  });
  $("#empty-clear").addEventListener("click", () => {
    state.category = "All"; state.query = ""; els.search.value = ""; render();
  });

  document.addEventListener("click", (event) => {
    if (event.target.closest("[data-close-dialog]")) { closeDialog(); return; }
    const imageOpener = event.target.closest("[data-open-image]");
    if (imageOpener) { openImage(Number(imageOpener.dataset.openImage)); return; }
  });

  els.dialog.addEventListener("click", (event) => {
    if (event.target === els.dialog) closeDialog();
  });
  els.imageDialog.addEventListener("click", (event) => {
    if (event.target === els.imageDialog) els.imageDialog.close();
  });
  $(".image-prev", els.imageDialog).addEventListener("click", () => {
    state.imageIndex = (state.imageIndex - 1 + state.activeImages.length) % state.activeImages.length;
    updateLightbox();
  });
  $(".image-next", els.imageDialog).addEventListener("click", () => {
    state.imageIndex = (state.imageIndex + 1) % state.activeImages.length;
    updateLightbox();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "/" && !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName) && !els.dialog.open) {
      event.preventDefault(); els.search.focus();
    }
    if (event.key === "Escape" && els.imageDialog.open) return;
    if (els.imageDialog.open && event.key === "ArrowLeft") {
      state.imageIndex = (state.imageIndex - 1 + state.activeImages.length) % state.activeImages.length; updateLightbox();
    }
    if (els.imageDialog.open && event.key === "ArrowRight") {
      state.imageIndex = (state.imageIndex + 1) % state.activeImages.length; updateLightbox();
    }
  });
  els.themeToggle.addEventListener("click", () => setTheme(root.dataset.theme === "light" ? "dark" : "light"));

  async function init() {
    initTheme();
    try {
      const response = await fetch("projects.json", { cache: "no-store" });
      if (!response.ok) throw new Error("Project catalog returned HTTP " + response.status);
      const projects = await response.json();
      if (!Array.isArray(projects)) throw new Error("Project catalog must be a JSON array.");
      state.projects = projects.filter((project) => project && project.id && project.title && project.category);
      els.heroTotal.textContent = state.projects.length.toString().padStart(2, "0");
      els.navCount.textContent = state.projects.length.toString().padStart(2, "0");
      render();
    } catch (error) {
      console.error("Unable to load project catalog:", error);
      els.featured.innerHTML = "";
      els.grid.innerHTML = "";
      els.summary.textContent = "Catalog could not be loaded.";
      els.resultCount.textContent = "Please check projects.json and reload.";
      els.empty.hidden = false;
      $(".empty-state h3", els.empty).textContent = "The project index could not load";
      $(".empty-state p", els.empty).textContent = "The local catalog could not be read. Please refresh or check the project files.";
    }
  }

  init();
})();
