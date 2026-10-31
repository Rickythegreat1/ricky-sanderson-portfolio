(() => {
  const grid = document.getElementById("work");
  const leaves = Array.from(document.querySelectorAll(".folio-leaf"));
  const details = Array.from(document.querySelectorAll(".inspect"));
  const marker = document.querySelector(".selection-indicator");
  const status = document.getElementById("selection-status");
  const narrow = window.matchMedia("(max-width: 760px)");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const closeTimers = new Map();
  const byId = new Map(leaves.map((leaf) => [leaf.dataset.project, leaf]));
  const detailById = new Map(details.map((item) => [item.dataset.project, item]));
  const defaultProject = "crossroads";
  let selectedProject = defaultProject;
  let expandedProject = null;
  let markerFrame = 0;

  const names = {
    crossroads: "Crossroads Education",
    pcx: "PCx Career Path",
    taska: "Taska"
  };

  function setSummaryState(item, isOpen) {
    const summary = item.querySelector("summary");
    const label = summary.querySelector(".inspect-label");
    const mark = summary.querySelector(".inspect-mark");
    const name = names[item.dataset.project];
    label.textContent = isOpen ? "Close" : "Inspect";
    mark.textContent = isOpen ? "−" : "+";
    summary.setAttribute("aria-label", `${isOpen ? "Collapse" : "Inspect"} ${name} evidence`);
  }

  function syncLeaves() {
    leaves.forEach((leaf) => {
      const id = leaf.dataset.project;
      leaf.classList.toggle("is-selected", id === selectedProject);
      leaf.classList.toggle("is-expanded", id === expandedProject);
      const titleButton = leaf.querySelector(".project-select");
      const titleLink = leaf.querySelector(".project-case");
      const isFocused = id === expandedProject;
      const activeTitle = document.activeElement === titleButton || document.activeElement === titleLink;
      titleButton.hidden = isFocused;
      titleButton.setAttribute("aria-expanded", String(isFocused));
      titleLink.hidden = !isFocused;
      // Preserve keyboard focus when the title changes from a selector to a link.
      if (activeTitle) (isFocused ? titleLink : titleButton).focus({ preventScroll: true });
    });
    grid.dataset.selected = selectedProject;
    grid.dataset.expanded = expandedProject || "";
  }

  function targetMarkerPosition() {
    const leaf = byId.get(selectedProject);
    if (!leaf) return { x: 0, y: 0 };
    if (narrow.matches) {
      const gridRect = grid.getBoundingClientRect();
      const leafRect = leaf.getBoundingClientRect();
      return { x: 0, y: leafRect.top - gridRect.top };
    }
    const width = grid.clientWidth;
    const style = window.getComputedStyle(grid);
    const gap = parseFloat(style.columnGap) || 0;
    const usable = Math.max(0, width - gap * 2);
    const ratios = expandedProject ? [0.72, 0.72, 0.72] : [1.65, 1, 1];
    const index = leaves.findIndex((item) => item.dataset.project === selectedProject);
    if (expandedProject) ratios[index] = 2.25;
    const total = ratios.reduce((sum, value) => sum + value, 0);
    const widths = ratios.map((value) => usable * value / total);
    const x = widths.slice(0, index).reduce((sum, value) => sum + value + gap, 0);
    return { x, y: 0 };
  }

  function updateMarker(animate = true) {
    if (markerFrame) cancelAnimationFrame(markerFrame);
    markerFrame = requestAnimationFrame(() => {
      const { x, y } = targetMarkerPosition();
      marker.style.transitionDuration = animate ? "" : "0ms";
      marker.style.transform = `translate3d(${Math.round(x)}px, ${Math.round(y)}px, 0)`;
      if (!animate) {
        requestAnimationFrame(() => { marker.style.transitionDuration = ""; });
      }
      markerFrame = 0;
    });
  }

  function announce(message) { status.textContent = message; }

  function pushHash(hash) {
    const next = `#${hash}`;
    if (window.location.hash === next) return;
    window.history.pushState({ folio: true }, "", `${window.location.pathname}${window.location.search}${next}`);
  }

  function finishClose(item) {
    const id = item.dataset.project;
    const timer = closeTimers.get(id);
    if (timer) window.clearTimeout(timer);
    closeTimers.delete(id);
    item.open = false;
    item.classList.remove("is-closing", "is-opening");
    setSummaryState(item, false);
  }

  function closeDetailAnimated(item) {
    if (!item || !item.open) return;
    const id = item.dataset.project;
    if (item.classList.contains("is-closing")) return;
    item.classList.remove("is-opening");
    const video = item.querySelector("video");
    if (video && !video.paused) video.pause();
    item.classList.add("is-closing");
    const duration = reduceMotion.matches ? 80 : 650;
    const timer = window.setTimeout(() => finishClose(item), duration);
    closeTimers.set(id, timer);
  }

  function openProject(id, { push = true, focus = false } = {}) {
    const target = detailById.get(id);
    if (!target) return;
    details.forEach((item) => {
      if (item === target) {
        const timer = closeTimers.get(id);
        if (timer) window.clearTimeout(timer);
        closeTimers.delete(id);
        const wasOpen = item.open;
        item.classList.remove("is-closing");
        item.open = true;
        if (!wasOpen) {
          item.classList.add("is-opening");
          requestAnimationFrame(() => requestAnimationFrame(() => {
            if (item.open && !item.classList.contains("is-closing")) item.classList.remove("is-opening");
          }));
        } else {
          item.classList.remove("is-opening");
        }
        setSummaryState(item, true);
      } else {
        closeDetailAnimated(item);
      }
    });
    selectedProject = id;
    expandedProject = id;
    syncLeaves();
    updateMarker(true);
    announce(`${names[id]} selected. Evidence expanded.`);
    if (push) pushHash(id);
    if (focus) target.querySelector("summary").focus();
  }

  function overview({ selected = defaultProject, push = false, focus = false } = {}) {
    details.forEach((item) => closeDetailAnimated(item));
    selectedProject = selected;
    expandedProject = null;
    syncLeaves();
    updateMarker(true);
    announce(`${names[selected]} selected. Project overview.`);
    if (push) pushHash("work");
    if (focus) detailById.get(selected)?.querySelector("summary")?.focus();
  }

  function toggleProject(id) {
    if (expandedProject === id) {
      overview({ selected: id, push: true, focus: true });
      return;
    }
    openProject(id, { push: true });
  }

  details.forEach((item) => {
    const summary = item.querySelector("summary");
    summary.addEventListener("click", (event) => {
      event.preventDefault();
      toggleProject(item.dataset.project);
    });
  });

  // The whole project preview selects the section; nested controls keep their own action.
  leaves.forEach((leaf) => {
    const id = leaf.dataset.project;
    leaf.querySelector(".project-select")?.addEventListener("click", () => openProject(id, { push: true }));
    leaf.addEventListener("click", (event) => {
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const target = event.target;
      if (!(target instanceof Element)) return;
      if (target.closest("a, button, summary, details, input, select, textarea, video, audio")) return;
      if (!target.closest(".leaf-head, .leaf-media, .leaf-copy")) return;
      if (window.getSelection()?.toString()) return;
      toggleProject(id);
    });
  });

  function applyHash() {
    const key = window.location.hash.replace(/^#/, "");
    if (detailById.has(key)) {
      openProject(key, { push: false });
    } else {
      overview({ selected: defaultProject, push: false });
    }
  }
  window.addEventListener("popstate", applyHash);
  window.addEventListener("hashchange", applyHash);

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape" || !expandedProject) return;
    if (event.target instanceof HTMLVideoElement && document.fullscreenElement) return;
    event.preventDefault();
    overview({ selected: expandedProject, push: true, focus: true });
  });

  const workLink = document.querySelector(".nav-work");
  workLink.addEventListener("click", () => {
    overview({ selected: defaultProject, push: false });
  });

  function onResize() {
    if (narrow.matches) grid.style.removeProperty("grid-template-columns");
    updateMarker(false);
  }
  window.addEventListener("resize", onResize, { passive: true });
  if ("ResizeObserver" in window) {
    const observer = new ResizeObserver(() => {
      if (narrow.matches) updateMarker(true);
    });
    observer.observe(grid);
  }
  if (typeof narrow.addEventListener === "function") {
    narrow.addEventListener("change", () => {
      if (narrow.matches) grid.style.removeProperty("grid-template-columns");
      updateMarker(false);
    });
  }

  grid.classList.add("has-js");
  if (detailById.has(window.location.hash.replace(/^#/, ""))) {
    applyHash();
  } else {
    selectedProject = defaultProject;
    expandedProject = null;
    syncLeaves();
    updateMarker(false);
    announce(`${names[defaultProject]} selected. Project overview.`);
  }
})();
