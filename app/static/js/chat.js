(function () {
  const config = window.AGENT_CONFIG || {};
  const scenarios = Array.isArray(config.scenarios) ? config.scenarios : [];
  const scenarioMap = new Map(scenarios.map((item) => [String(item.id), item]));
  const scenarioDetailTemplate = config.endpoints?.scenarioDetail || "/scenario/__SCENARIO_ID__";
  const snippetTemplate = config.endpoints?.snippet || "/snippet/__SNIPPET__";

  const searchInput = document.getElementById("scenario-search");
  const categoryTabs = Array.from(document.querySelectorAll("[data-category-tab]"));
  const scenarioGroups = document.getElementById("scenario-groups");
  const scenarioCards = Array.from(document.querySelectorAll("[data-scenario-card]"));
  const emptyState = document.getElementById("scenario-no-results");
  const activeTitle = document.getElementById("active-scenario-title");
  const activeCategory = document.getElementById("active-scenario-category");
  const activeFilename = document.getElementById("active-scenario-filename");
  const activeTags = document.getElementById("active-scenario-tags");
  const chatFeedback = document.getElementById("chat-feedback");
  const copyButtons = Array.from(
    document.querySelectorAll('[data-action="copy-transcript"]')
  );
  const restartButtons = Array.from(
    document.querySelectorAll('[data-action="restart-scenario"]')
  );
  const chatTranscript = document.getElementById("chat-transcript");
  const chatEmptyState = document.getElementById("chat-empty-state");
  const helperText = document.getElementById("chat-helper-text");
  const container = document.getElementById("agents-factory");
  const chatForm = document.getElementById("chat-input-form");
  const chatInput = document.getElementById("chat-user-input");
  const chatSendButton = document.getElementById("chat-send-button");

  if (!scenarioGroups || !chatTranscript) {
    return;
  }

  const accentPalette = ["indigo", "teal", "amber", "pink", "slate"];
  let activeScenarioId = null;
  let isPlaying = false;
  let playbackToken = 0;

  function sleep(delay) {
    return new Promise((resolve) => setTimeout(resolve, delay));
  }

  function escapeHTML(value) {
    return value
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function hashAccentKey(id) {
    if (!id) {
      return accentPalette[0];
    }
    let sum = 0;
    const text = String(id);
    for (let index = 0; index < text.length; index += 1) {
      sum += text.charCodeAt(index);
    }
    return accentPalette[sum % accentPalette.length];
  }

  function setAccent(scenario) {
    if (!container) {
      return;
    }
    const accent = scenario?.accent || hashAccentKey(scenario?.id || "");
    container.dataset.accent = accent;
  }

  function setFeedback(message) {
    if (!chatFeedback) {
      return;
    }
    chatFeedback.textContent = "";
    if (message) {
      void chatFeedback.offsetHeight;
      chatFeedback.textContent = message;
    }
  }

  function toggleControls(disabled) {
    scenarioCards.forEach((card) => {
      card.classList.toggle("is-disabled", disabled);
      card.setAttribute("aria-disabled", disabled ? "true" : "false");
    });
    restartButtons.forEach((button) => {
      button.disabled = disabled;
    });
    copyButtons.forEach((button) => {
      button.disabled = disabled;
    });
    if (searchInput) {
      searchInput.disabled = disabled;
    }
    categoryTabs.forEach((tab) => {
      tab.disabled = disabled;
    });
  }

  function scrollTranscript() {
    requestAnimationFrame(() => {
      chatTranscript.scrollTop = chatTranscript.scrollHeight;
    });
  }

  function clearTranscript() {
    chatTranscript.innerHTML = "";
    chatTranscript.dataset.empty = "true";
    if (chatEmptyState) {
      chatTranscript.appendChild(chatEmptyState);
      chatEmptyState.classList.remove("d-none");
    }
  }

  function ensureTranscriptContainer() {
    if (chatEmptyState && chatEmptyState.parentElement === chatTranscript) {
      chatEmptyState.classList.add("d-none");
    }
    chatTranscript.dataset.empty = "false";
  }

  function createMessageSkeleton(role, speaker) {
    const isUser = role === "user";
    const wrapper = document.createElement("div");
    wrapper.className = "chat-message d-flex gap-3";
    wrapper.dataset.messageRole = role;

    const icon = document.createElement("div");
    icon.className = "flex-shrink-0 chat-icon fs-4";
    icon.innerHTML = `<i class="fa-solid ${isUser ? "fa-user" : "fa-robot"}"></i>`;
    wrapper.appendChild(icon);

    const bubble = document.createElement("div");
    bubble.className = "chat-bubble shadow-sm";

    const header = document.createElement("div");
    header.className = "d-flex align-items-start gap-3 mb-2";

    const meta = document.createElement("div");
    meta.className = "d-flex flex-column";
    const sender = document.createElement("span");
    sender.className = "fw-semibold small text-uppercase text-muted chat-sender";
    sender.textContent = speaker || (isUser ? "You" : "Agent");
    meta.appendChild(sender);
    header.appendChild(meta);

    bubble.appendChild(header);

    const body = document.createElement("div");
    body.className = "chat-bubble-content";
    bubble.appendChild(body);

    wrapper.appendChild(bubble);

    const spacer = document.createElement("div");
    spacer.className = "flex-grow-1";
    wrapper.appendChild(spacer);

    return { wrapper, content: body };
  }

  function formatTextContent(text) {
    return text
      .split(/\n/g)
      .map((segment) => `<span>${escapeHTML(segment)}</span>`)
      .join("<br />");
  }

  async function typeText(target, text, token) {
    const cursor = document.createElement("span");
    cursor.className = "typing-cursor";
    target.innerHTML = "";
    target.appendChild(cursor);
    for (const character of text) {
      if (token !== playbackToken) {
        cursor.remove();
        return;
      }
      if (character === "\n") {
        cursor.insertAdjacentHTML("beforebegin", "<br />");
      } else {
        cursor.insertAdjacentText("beforebegin", character);
      }
      await sleep(25);
    }
    cursor.remove();
  }

  async function fetchSnippet(snippetPath) {
    if (!snippetPath) {
      return null;
    }
    const cleaned = String(snippetPath).replace(/^\/+/, "");
    if (!cleaned) {
      return null;
    }
    const encoded = cleaned
      .split("/")
      .map((segment) => encodeURIComponent(segment))
      .join("/");
    const url = snippetTemplate.replace("__SNIPPET__", encoded);
    const response = await fetch(url, {
      headers: {
        Accept: "text/html, text/plain; charset=utf-8",
      },
    });
    if (!response.ok) {
      throw new Error(`Unable to fetch snippet: ${response.status}`);
    }
    const contentType = response.headers.get("Content-Type") || "";
    const payload = await response.text();
    if (contentType.includes("text/html")) {
      return { html: payload, isHtml: true };
    }
    const escaped = escapeHTML(payload);
    return {
      html: `<pre>${escaped}</pre>`,
      isHtml: true,
    };
  }

  async function renderUser(step, token) {
    if (token !== playbackToken) {
      return;
    }
    ensureTranscriptContainer();

    const typingIndicator = createTypingIndicator("user");
    const typingWrapper = document.createElement("div");
    typingWrapper.className = "chat-message d-flex gap-3";
    typingWrapper.dataset.messageRole = "user";
    const typingIcon = document.createElement("div");
    typingIcon.className = "flex-shrink-0 chat-icon fs-4";
    typingIcon.innerHTML = '<i class="fa-solid fa-user"></i>';
    typingWrapper.appendChild(typingIcon);
    const typingBubble = document.createElement("div");
    typingBubble.className = "chat-bubble shadow-sm";
    typingBubble.appendChild(typingIndicator);
    typingWrapper.appendChild(typingBubble);
    const typingSpacer = document.createElement("div");
    typingSpacer.className = "flex-grow-1";
    typingWrapper.appendChild(typingSpacer);
    chatTranscript.appendChild(typingWrapper);
    scrollTranscript();

    const fallbackMessage = step.message || step.text || "";
    const typingDelay =
      typeof step.typingDelay === "number"
        ? step.typingDelay
        : Math.min(1400, Math.max(400, String(fallbackMessage).length * 20));
    await sleep(typingDelay);

    if (token !== playbackToken) {
      typingWrapper.remove();
      return;
    }

    typingWrapper.remove();

    const { wrapper, content } = createMessageSkeleton("user", step.speaker || step.actorLabel);
    chatTranscript.appendChild(wrapper);
    scrollTranscript();

    if (step.message_html) {
      content.innerHTML = step.message_html;
    } else if (fallbackMessage) {
      await typeText(content, String(fallbackMessage), token);
      if (token !== playbackToken) {
        return;
      }
    }

    if (!step.message_html && !fallbackMessage) {
      content.innerHTML = "";
    }

    if (typeof step.pause === "number") {
      await sleep(Math.max(0, step.pause));
    }
  }

  function createTypingIndicator(role) {
    const indicator = document.createElement("div");
    indicator.className = "chat-typing-indicator";
    indicator.dataset.align = "start";
    indicator.innerHTML =
      '<span class="spinner-border" role="status" aria-hidden="true"></span><span>Typing…</span>';
    return indicator;
  }

  function appendUserMessage(text) {
    if (!chatTranscript) {
      return;
    }
    ensureTranscriptContainer();
    const { wrapper, content } = createMessageSkeleton("user");
    content.innerHTML = formatTextContent(text);
    chatTranscript.appendChild(wrapper);
    scrollTranscript();
  }

  async function renderAgent(step, token) {
    if (token !== playbackToken) {
      return;
    }
    ensureTranscriptContainer();
    const typingIndicator = createTypingIndicator("assistant");
    const typingWrapper = document.createElement("div");
    typingWrapper.className = "chat-message d-flex gap-3";
    typingWrapper.dataset.messageRole = "assistant";
    const icon = document.createElement("div");
    icon.className = "flex-shrink-0 chat-icon fs-4";
    icon.innerHTML = '<i class="fa-solid fa-robot"></i>';
    typingWrapper.appendChild(icon);
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble shadow-sm";
    bubble.appendChild(typingIndicator);
    typingWrapper.appendChild(bubble);
    const spacer = document.createElement("div");
    spacer.className = "flex-grow-1";
    typingWrapper.appendChild(spacer);
    chatTranscript.appendChild(typingWrapper);
    scrollTranscript();

    const typingDelay =
      typeof step.typingDelay === "number"
        ? step.typingDelay
        : Math.min(1600, Math.max(600, (step.message || "").length * 30));
    await sleep(typingDelay);

    if (token !== playbackToken) {
      typingWrapper.remove();
      return;
    }

    typingWrapper.remove();

    const { wrapper, content } = createMessageSkeleton("assistant", step.speaker || step.actorLabel);

    let snippetHtml = null;
    if (step.snippet) {
      try {
        snippetHtml = await fetchSnippet(step.snippet);
      } catch (error) {
        console.error(error);
        snippetHtml = {
          html: `<div class="alert alert-warning mb-0">Failed to load snippet: ${escapeHTML(
            String(step.snippet)
          )}</div>`,
          isHtml: true,
        };
      }
    }

    if (token !== playbackToken) {
      return;
    }

    chatTranscript.appendChild(wrapper);
    scrollTranscript();

    if (step.message_html) {
      content.innerHTML = step.message_html;
    } else if (step.message || step.text) {
      const message = step.message || step.text || "";
      await typeText(content, String(message), token);
      if (token !== playbackToken) {
        return;
      }
    }

    if (snippetHtml) {
      const snippetContainer = document.createElement("div");
      snippetContainer.innerHTML = snippetHtml.isHtml
        ? snippetHtml.html
        : formatTextContent(snippetHtml.html || "");
      content.appendChild(snippetContainer);
    }

    if (typeof step.pause === "number") {
      await sleep(Math.max(0, step.pause));
    }
  }

  function updatePromptState() {
    if (!chatSendButton) {
      return;
    }
    const hasValue = Boolean(chatInput?.value.trim());
    chatSendButton.disabled = !hasValue;
  }

  function bindPromptForm() {
    if (!chatForm || !chatInput) {
      return;
    }

    chatForm.addEventListener("submit", (event) => {
      event.preventDefault();
      if (!chatInput || chatInput.disabled) {
        return;
      }
      const value = chatInput.value.trim();
      if (!value) {
        setFeedback("Type a message before sending.");
        updatePromptState();
        return;
      }
      appendUserMessage(value);
      chatInput.value = "";
      updatePromptState();
      setFeedback("Message added to the conversation.");
      chatInput.focus();
    });

    chatInput.addEventListener("input", () => {
      updatePromptState();
    });

    updatePromptState();
  }

  async function playScenario(id, { restart = false } = {}) {
    const scenarioId = String(id || "");
    const metadata = scenarioMap.get(scenarioId);
    if (!metadata) {
      return;
    }
    const token = ++playbackToken;
    isPlaying = true;
    toggleControls(true);

    if (restart) {
      setFeedback("Scenario reset. Preparing playback.");
    } else {
      setFeedback("Loading scenario…");
    }

    clearTranscript();
    setAccent(metadata);

    try {
      const detailUrl = scenarioDetailTemplate.replace(
        "__SCENARIO_ID__",
        encodeURIComponent(scenarioId)
      );
      const response = await fetch(detailUrl, { headers: { Accept: "application/json" } });
      if (!response.ok) {
        throw new Error(`Failed to load scenario (${response.status})`);
      }
      const payload = await response.json();
      const steps = Array.isArray(payload.steps) ? payload.steps : [];
      helperText?.classList.toggle("text-muted", true);
      helperText?.classList.remove("text-danger");
      setFeedback("Scenario loaded. Playing conversation…");

      for (const step of steps) {
        if (token !== playbackToken) {
          break;
        }
        const actor = (step.actor || step.role || "assistant").toLowerCase();
        if (actor === "user" || actor === "human" || actor === "player") {
          await renderUser(step, token);
        } else if (actor === "assistant" || actor === "agent" || actor === "bot") {
          await renderAgent(step, token);
        }
      }

      if (token === playbackToken) {
        setFeedback("Scenario complete. Use restart to replay or copy the transcript.");
      }
    } catch (error) {
      console.error(error);
      helperText?.classList.add("text-danger");
      setFeedback("Unable to play this scenario. Check the console for details.");
    } finally {
      if (token === playbackToken) {
        isPlaying = false;
        toggleControls(false);
      }
    }
  }

  function updateActiveScenario(id) {
    const activeId = String(id || "");
    activeScenarioId = activeId;
    scenarioCards.forEach((card) => {
      const isActive = card.dataset.scenarioId === activeId;
      card.classList.toggle("active", isActive);
      card.setAttribute("aria-current", isActive ? "true" : "false");
    });
    const metadata = scenarioMap.get(activeId);
    if (!metadata) {
      if (activeTitle) {
        activeTitle.textContent = "Select a scenario to begin";
      }
      if (activeCategory) {
        activeCategory.textContent = "No category";
      }
      if (activeFilename) {
        activeFilename.textContent = "—";
      }
      if (activeTags) {
        activeTags.textContent = "Add tags to improve discovery";
      }
      setAccent(null);
      return;
    }

    if (activeTitle) {
      activeTitle.textContent = metadata.title || metadata.id;
    }
    if (activeCategory) {
      activeCategory.textContent = metadata.category || "Uncategorized";
    }
    if (activeFilename) {
      activeFilename.textContent = metadata.filename || `${metadata.id}.json`;
    }
    if (activeTags) {
      if (Array.isArray(metadata.tags) && metadata.tags.length > 0) {
        activeTags.textContent = metadata.tags.join(", ");
      } else {
        activeTags.textContent = "No tags provided";
      }
    }
    setAccent(metadata);
    document.dispatchEvent(
      new CustomEvent("scenario:selected", {
        detail: { scenario: metadata },
      })
    );
  }

  function applyFilters() {
    const term = (searchInput?.value || "").trim().toLowerCase();
    const activeCategoryFilter = categoryTabs.find((tab) => tab.classList.contains("active"))?.dataset
      .categoryTab;

    let visibleCount = 0;

    scenarioGroups
      .querySelectorAll("[data-category-panel]")
      .forEach((section) => {
        let sectionVisible = 0;
        section.querySelectorAll("[data-scenario-card]").forEach((card) => {
          const cardCategory = card.dataset.scenarioCategory;
          const searchText = (card.dataset.searchText || "").toLowerCase();
          const matchesCategory =
            !activeCategoryFilter || activeCategoryFilter === "__all__" || cardCategory === activeCategoryFilter;
          const matchesSearch = !term || searchText.includes(term);
          if (matchesCategory && matchesSearch) {
            card.classList.remove("d-none");
            visibleCount += 1;
            sectionVisible += 1;
          } else {
            card.classList.add("d-none");
          }
        });
        section.classList.toggle("d-none", sectionVisible === 0);
      });

    if (emptyState) {
      emptyState.classList.toggle("d-none", visibleCount > 0);
    }
  }

  function bindCategoryTabs() {
    categoryTabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        if (tab.disabled) {
          return;
        }
        categoryTabs.forEach((item) => item.classList.remove("active"));
        tab.classList.add("active");
        applyFilters();
      });
    });
  }

  function bindScenarioCards() {
    scenarioCards.forEach((card) => {
      card.addEventListener("click", (event) => {
        if (card.classList.contains("is-disabled")) {
          return;
        }
        if (
          event.metaKey ||
          event.ctrlKey ||
          event.shiftKey ||
          event.altKey ||
          event.button !== 0
        ) {
          return;
        }
        event.preventDefault();
        const scenarioId = card.dataset.scenarioId;
        if (!scenarioId) {
          return;
        }
        updateActiveScenario(scenarioId);
        playScenario(scenarioId);
        const url = new URL(window.location.href);
        url.searchParams.set("scenario", scenarioId);
        window.history.replaceState({}, "", url.toString());
      });
    });
  }

  function bindCopy() {
    copyButtons.forEach((button) => {
      button.addEventListener("click", async () => {
        if (isPlaying) {
          return;
        }
        const text = chatTranscript.innerText.trim();
        if (!text) {
          setFeedback("There is no transcript to copy yet.");
          return;
        }
        button.classList.add("transcript-copying");
        try {
          await navigator.clipboard.writeText(text);
          setFeedback("Transcript copied to your clipboard.");
        } catch (error) {
          console.error("Clipboard copy failed", error);
          setFeedback("Unable to copy transcript. Try using Ctrl+C instead.");
        } finally {
          button.classList.remove("transcript-copying");
        }
      });
    });
  }

  function bindRestart() {
    restartButtons.forEach((button) => {
      button.addEventListener("click", () => {
        if (!activeScenarioId) {
          setFeedback("Select a scenario before restarting playback.");
          return;
        }
        playScenario(activeScenarioId, { restart: true });
      });
    });
  }

  function autoStartFromQuery() {
    const url = new URL(window.location.href);
    const scenarioId = url.searchParams.get("scenario") || config.selectedScenarioId;
    if (!scenarioId) {
      return;
    }
    updateActiveScenario(scenarioId);
    const autoplay = url.searchParams.get("autoplay");
    if (autoplay === null && !config.selectedScenarioId) {
      return;
    }
    if (autoplay === "0" || autoplay === "false") {
      return;
    }
    playScenario(scenarioId);
  }

  function init() {
    if (!categoryTabs.find((tab) => tab.classList.contains("active"))) {
      categoryTabs[0]?.classList.add("active");
    }
    if (config.selectedScenarioId) {
      updateActiveScenario(config.selectedScenarioId);
    } else if (scenarioCards.length) {
      updateActiveScenario(scenarioCards[0].dataset.scenarioId);
    }
    bindCategoryTabs();
    bindScenarioCards();
    bindCopy();
    bindRestart();
    bindPromptForm();

    if (searchInput) {
      searchInput.addEventListener("input", () => applyFilters());
    }

    applyFilters();
    autoStartFromQuery();
  }

  document.addEventListener("scenario:restart", () => {
    if (activeScenarioId) {
      playScenario(activeScenarioId, { restart: true });
    }
  });

  document.addEventListener("DOMContentLoaded", init, { once: true });
})();
