(() => {
  const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)");
  const panelClasses = ["is-out-left", "is-out-right", "is-in-from-left", "is-in-from-right"];
  const galleryStates = [];
  let resizeFrame = 0;

  const stopVideos = (scope = document) => {
    scope.querySelectorAll("video").forEach((video) => {
      video.pause();
      try { video.currentTime = 0; } catch { /* Some browsers wait for media metadata. */ }
    });
  };

  document.querySelectorAll("[data-tabs]").forEach((gallery) => {
    const tablist = gallery.querySelector("[data-tablist]");
    const tabs = [...gallery.querySelectorAll("[data-tab]")];
    const panels = [...gallery.querySelectorAll("[data-panel]")];
    const rail = gallery.querySelector(".tab-rail");
    const panelWrap = gallery.querySelector(".gallery-panels");
    if (!tablist || !panelWrap || tabs.length < 2 || tabs.length !== panels.length) return;

    let activeIndex = Math.max(0, tabs.findIndex((tab) => tab.hash === window.location.hash));
    let exitTimer = 0;
    let finishTimer = 0;

    const setActiveAttributes = () => {
      tabs.forEach((tab, index) => {
        tab.setAttribute("aria-selected", String(index === activeIndex));
        tab.tabIndex = index === activeIndex ? 0 : -1;
      });
      panels.forEach((panel, index) => {
        const active = index === activeIndex;
        panel.setAttribute("aria-hidden", String(!active));
        panel.inert = !active;
        panel.hidden = !active;
      });
    };

    const measurePanelWrap = () => {
      const previousHidden = panels.map((panel) => panel.hidden);
      let tallest = 0;
      panels.forEach((panel) => {
        panel.hidden = false;
        tallest = Math.max(tallest, panel.getBoundingClientRect().height);
      });
      panels.forEach((panel, index) => { panel.hidden = previousHidden[index]; });
      panelWrap.style.minHeight = `${Math.ceil(tallest)}px`;
    };

    const placeRail = (index = activeIndex) => {
      if (!rail) return;
      const tab = tabs[index];
      gallery.style.setProperty("--rail-x", `${tab.offsetLeft}px`);
      gallery.style.setProperty("--rail-width", `${tab.offsetWidth}px`);
    };

    const finishImmediately = () => {
      window.clearTimeout(exitTimer);
      window.clearTimeout(finishTimer);
      panels.forEach((panel) => panel.classList.remove(...panelClasses));
      setActiveAttributes();
      placeRail();
    };

    const activate = (index) => {
      if (index < 0 || index >= tabs.length) return;
      if (index === activeIndex) {
        placeRail();
        return;
      }

      window.clearTimeout(exitTimer);
      window.clearTimeout(finishTimer);
      stopVideos(gallery);

      const previousIndex = activeIndex;
      const outgoing = panels[previousIndex];
      const incoming = panels[index];
      const movingForward = index > previousIndex;
      activeIndex = index;

      tabs.forEach((tab, tabIndex) => {
        tab.setAttribute("aria-selected", String(tabIndex === activeIndex));
        tab.tabIndex = tabIndex === activeIndex ? 0 : -1;
      });
      panels.forEach((panel) => {
        panel.classList.remove(...panelClasses);
        panel.hidden = panel !== outgoing;
        panel.inert = panel !== outgoing;
        panel.setAttribute("aria-hidden", String(panel !== outgoing));
      });
      outgoing.hidden = false;
      outgoing.inert = true;
      outgoing.setAttribute("aria-hidden", "true");
      incoming.hidden = false;
      incoming.inert = false;
      incoming.setAttribute("aria-hidden", "false");
      placeRail();

      if (reducedMotion?.matches) {
        outgoing.hidden = true;
        return;
      }

      outgoing.classList.add(movingForward ? "is-out-left" : "is-out-right");
      incoming.classList.add(movingForward ? "is-in-from-right" : "is-in-from-left");

      exitTimer = window.setTimeout(() => {
        outgoing.hidden = true;
        outgoing.classList.remove("is-out-left", "is-out-right");
      }, 160);

      finishTimer = window.setTimeout(() => {
        panels.forEach((panel) => panel.classList.remove(...panelClasses));
        panels.forEach((panel, panelIndex) => {
          const active = panelIndex === activeIndex;
          panel.hidden = !active;
          panel.inert = !active;
          panel.setAttribute("aria-hidden", String(!active));
        });
      }, 420);
    };

    gallery.classList.add("is-enhanced");
    tablist.setAttribute("role", "tablist");
    tabs.forEach((tab, index) => {
      const panel = panels[index];
      if (!tab.id) tab.id = `${gallery.dataset.tabs}-tab-${index + 1}`;
      tab.setAttribute("role", "tab");
      tab.setAttribute("aria-controls", panel.id);
      panel.setAttribute("role", "tabpanel");
      panel.setAttribute("aria-labelledby", tab.id);
      panel.tabIndex = 0;

      tab.addEventListener("click", (event) => {
        event.preventDefault();
        activate(index);
      });

      tab.addEventListener("keydown", (event) => {
        const focusedIndex = tabs.indexOf(event.currentTarget);
        let nextIndex = focusedIndex;
        if (event.key === "ArrowRight") nextIndex = (focusedIndex + 1) % tabs.length;
        else if (event.key === "ArrowLeft") nextIndex = (focusedIndex - 1 + tabs.length) % tabs.length;
        else if (event.key === "Home") nextIndex = 0;
        else if (event.key === "End") nextIndex = tabs.length - 1;
        else if (event.key === " ") {
          event.preventDefault();
          activate(focusedIndex);
          return;
        } else return;

        event.preventDefault();
        tabs[nextIndex].focus();
        tabs[nextIndex].scrollIntoView({ block: "nearest", inline: "nearest" });
        activate(nextIndex);
      });
    });

    setActiveAttributes();
    measurePanelWrap();
    placeRail();
    galleryStates.push({ finishImmediately, measurePanelWrap });
  });

  window.addEventListener("resize", () => {
    window.cancelAnimationFrame(resizeFrame);
    resizeFrame = window.requestAnimationFrame(() => {
      galleryStates.forEach((state) => state.measurePanelWrap());
      document.querySelectorAll("[data-tabs]").forEach((gallery) => {
        const tabs = [...gallery.querySelectorAll("[data-tab]")];
        const selected = tabs.findIndex((tab) => tab.getAttribute("aria-selected") === "true");
        if (selected < 0 || !tabs[selected]) return;
        gallery.style.setProperty("--rail-x", `${tabs[selected].offsetLeft}px`);
        gallery.style.setProperty("--rail-width", `${tabs[selected].offsetWidth}px`);
      });
    });
  });

  document.querySelectorAll("[data-tablist]").forEach((tablist) => {
    tablist.addEventListener("scroll", () => {
      const gallery = tablist.closest("[data-tabs]");
      const selected = [...tablist.querySelectorAll('[data-tab][aria-selected="true"]')][0];
      if (!gallery || !selected) return;
      gallery.style.setProperty("--rail-x", `${selected.offsetLeft}px`);
      gallery.style.setProperty("--rail-width", `${selected.offsetWidth}px`);
    }, { passive: true });
  });

  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") stopVideos();
  });

  const handleMotionPreference = (event) => {
    if (event.matches) galleryStates.forEach((state) => state.finishImmediately());
  };
  if (reducedMotion?.addEventListener) reducedMotion.addEventListener("change", handleMotionPreference);
  else reducedMotion?.addListener?.(handleMotionPreference);
})();
