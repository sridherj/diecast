// cast-preso-review — shared shell runtime.
// Public surface attached to window.TPR for testability. No framework, no build step.
// Server POST branch for the Export button lands in sub-phase 1d.

(function () {
  "use strict";

  const SAVE_DEBOUNCE_MS = 200;

  function readJSON(id) {
    const node = document.getElementById(id);
    if (!node) return null;
    const text = (node.textContent || "").trim();
    if (!text) return null;
    try { return JSON.parse(text); }
    catch (err) { console.error("TPR: failed to parse", id, err); return null; }
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  const TPR = {
    state: { current: 0, editCount: 0 },
    meta: {},
    slides: [],
    sidebar: [],

    init() {
      this.meta = readJSON("data-meta") || {};
      this.slides = readJSON("data-slides") || [];
      this.sidebar = readJSON("data-sidebar") || [];

      this.renderSidebar();
      this.bindHeader();
      this.bindKeyboard();
      this.bindAutosave();
      this.bindSearch();

      if (this.slides.length === 0) {
        this.renderEmptyState();
      } else {
        this.goTo(0);
      }
      document.getElementById("app").dataset.state = "ready";
      this.refreshEditedMarkers();
    },

    // ---------- Sidebar ----------
    renderSidebar() {
      const list = document.getElementById("sidebar-list");
      list.innerHTML = "";
      let lastGroup = null;
      this.sidebar.forEach((entry, idx) => {
        if (entry.group && entry.group !== lastGroup) {
          const label = document.createElement("div");
          label.className = "sidebar-group-label";
          label.textContent = entry.group;
          list.appendChild(label);
          lastGroup = entry.group;
        }
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "nav-item";
        btn.setAttribute("role", "option");
        btn.dataset.slideId = entry.slide_id;
        btn.dataset.index = String(idx);
        btn.innerHTML =
          '<span class="nav-num">' + esc(String(idx + 1).padStart(2, "0")) + "</span>" +
          '<span class="nav-title">' + esc(entry.label) + "</span>" +
          (entry.summary
            ? '<span class="nav-summary">' + esc(entry.summary) + "</span>"
            : "");
        btn.addEventListener("click", () => this.goTo(idx));
        list.appendChild(btn);
      });
    },

    refreshEditedMarkers() {
      const list = document.getElementById("sidebar-list");
      const editedSlideIds = this.editedSlideIds();
      list.querySelectorAll(".nav-item").forEach((el) => {
        const id = el.dataset.slideId;
        el.classList.toggle("edited", editedSlideIds.has(id));
      });
    },

    // ---------- Header / navigation ----------
    bindHeader() {
      document.getElementById("btn-prev").addEventListener("click", () => this.goTo(this.state.current - 1));
      document.getElementById("btn-next").addEventListener("click", () => this.goTo(this.state.current + 1));
      document.getElementById("btn-revert").addEventListener("click", () => {
        const slide = this.slides[this.state.current];
        if (slide) this.revertSlide(slide.id);
      });
      document.getElementById("btn-clear").addEventListener("click", () => {
        if (confirmClear()) this.clearAll();
      });
      document.getElementById("btn-export").addEventListener("click", () => this.handleExport());
    },

    bindKeyboard() {
      document.addEventListener("keydown", (e) => {
        // Don't hijack typing in inputs or contenteditable blocks.
        const ae = document.activeElement;
        const typing = ae && (
          ae.tagName === "INPUT" ||
          ae.tagName === "TEXTAREA" ||
          ae.getAttribute("contenteditable") === "true"
        );
        if (e.key === "Escape") {
          if (ae && typeof ae.blur === "function") ae.blur();
          return;
        }
        if (typing) return;
        if (e.key === "ArrowRight") { this.goTo(this.state.current + 1); e.preventDefault(); }
        else if (e.key === "ArrowLeft") { this.goTo(this.state.current - 1); e.preventDefault(); }
        else if (e.key === "/") {
          const search = document.getElementById("sidebar-search");
          if (search) { search.focus(); search.select(); e.preventDefault(); }
        }
      });
    },

    bindSearch() {
      const input = document.getElementById("sidebar-search");
      if (!input) return;
      input.addEventListener("input", () => {
        const q = input.value.trim().toLowerCase();
        document.querySelectorAll("#sidebar-list .nav-item").forEach((el) => {
          if (!q) { el.classList.remove("hidden"); return; }
          const hay = (el.textContent || "").toLowerCase();
          el.classList.toggle("hidden", !hay.includes(q));
        });
      });
    },

    goTo(index) {
      if (this.slides.length === 0) return;
      const clamped = Math.max(0, Math.min(this.slides.length - 1, index));
      this.state.current = clamped;
      this.renderSlide(this.slides[clamped]);
      document.getElementById("stage-counter").textContent =
        (clamped + 1) + " / " + this.slides.length;
      document.querySelectorAll("#sidebar-list .nav-item").forEach((el) => {
        el.classList.toggle("active", Number(el.dataset.index) === clamped);
      });
      const active = document.querySelector("#sidebar-list .nav-item.active");
      if (active && typeof active.scrollIntoView === "function") {
        active.scrollIntoView({ block: "nearest" });
      }
    },

    // ---------- Slide render ----------
    renderSlide(slide) {
      const body = document.getElementById("stage-body");
      if (!slide) { body.innerHTML = ""; return; }
      const blocks = slide.mode === "decision"
        ? renderDecisionCard(slide)
        : (slide.blocks || []).map((b) => this.renderBlock(slide, b)).join("");
      body.innerHTML =
        '<article class="slide" data-slide-id="' + esc(slide.id) + '" data-mode="' + esc(slide.mode) + '">' +
        '<h2 class="slide-title">' + esc(slide.title) + "</h2>" +
        (slide.outcome
          ? '<p class="slide-outcome">' + esc(slide.outcome) + "</p>"
          : "") +
        blocks +
        (slide.source_path
          ? '<div class="slide-source">source: ' + esc(slide.source_path) + "</div>"
          : "") +
        "</article>";
      if (slide.mode === "decision") {
        this.hydrateDecision(slide);
      } else {
        this.rehydrateEdits(slide);
      }
    },

    renderBlock(slide, block) {
      // 1b/1c renderers produce blocks with fields:
      //   { id, kind: "text" | "decision" | ..., html, editable, ...extras }
      // This function renders the generic shell; decision cards etc. layer on top
      // using CSS classes defined in review.css. Unknown kinds render as plain text.
      const editable = !!block.editable;
      const attrs =
        ' class="block"' +
        ' data-block-id="' + esc(block.id || "") + '"' +
        ' data-kind="' + esc(block.kind || "text") + '"' +
        (editable
          ? ' contenteditable="true" spellcheck="true" role="textbox"'
          : "");
      const inner = block.html != null ? block.html : esc(block.text || "");
      return "<div" + attrs + ">" + inner + "</div>";
    },

    rehydrateEdits(slide) {
      const prefix = this.storageKeyPrefix(slide.id);
      const root = document.querySelector('#stage-body .slide[data-slide-id="' + cssEsc(slide.id) + '"]');
      if (!root) return;
      root.querySelectorAll('[data-block-id]').forEach((el) => {
        const blockId = el.dataset.blockId;
        const key = prefix + "/" + blockId;
        let saved = null;
        try { saved = window.localStorage.getItem(key); } catch (_) {}
        if (saved != null) {
          el.innerHTML = saved;
          el.classList.add("edited");
        }
      });
    },

    // ---------- Decision mode ----------
    decisionStorageKey(questionId) {
      return (this.meta.storage_key_prefix || "") + "/decision/" + questionId;
    },

    readDecisionAnswer(questionId) {
      try {
        const raw = window.localStorage.getItem(this.decisionStorageKey(questionId));
        if (!raw) return { picked: null, note: "" };
        const parsed = JSON.parse(raw);
        return {
          picked: parsed && typeof parsed.picked === "string" ? parsed.picked : null,
          note: parsed && typeof parsed.note === "string" ? parsed.note : "",
        };
      } catch (_) {
        return { picked: null, note: "" };
      }
    },

    writeDecisionAnswer(questionId, answer) {
      try {
        window.localStorage.setItem(
          this.decisionStorageKey(questionId),
          JSON.stringify(answer || { picked: null, note: "" })
        );
        this.setSaveState("saved");
      } catch (err) {
        console.error("TPR: decision save failed", err);
        this.setSaveState("error");
      }
    },

    buildDecisionAnswerMarkdown(slide, answer) {
      // Mirrors appendDecisionExport shape but emits one answer at a time
      // for the /decisions/<id> endpoint.
      const payload = (slide.blocks && slide.blocks[0]) || {};
      const questionId = payload.id || slide.id;
      const picked = answer && answer.picked
        ? (payload.options || []).find((o) => o.letter === answer.picked)
        : null;
      const lines = [];
      lines.push("## Decision: " + (payload.topic || slide.title) + " (" + questionId + ")");
      if (picked) {
        lines.push("**Picked:** " + picked.letter + " — " + picked.label);
      } else {
        lines.push("**Picked:** _(no option selected — note only)_");
      }
      const note = (answer && answer.note) || "";
      if (note.trim()) lines.push("**Note:** " + note.trim());
      lines.push("");
      return lines.join("\n");
    },

    hydrateDecision(slide) {
      const payload = (slide.blocks && slide.blocks[0]) || {};
      const questionId = payload.id || slide.id;
      const answer = this.readDecisionAnswer(questionId);
      const root = document.querySelector(
        '#stage-body .slide[data-slide-id="' + cssEsc(slide.id) + '"]'
      );
      if (!root) return;

      // Pre-select the saved radio, mark the option card picked.
      root.querySelectorAll('input[type="radio"][name="q-' + cssEsc(questionId) + '"]').forEach((input) => {
        const checked = answer.picked != null && input.value === answer.picked;
        input.checked = checked;
        const card = input.closest(".decision-option");
        if (card) card.classList.toggle("picked", checked);
      });
      const textarea = root.querySelector(".decision-response textarea");
      if (textarea) textarea.value = answer.note || "";

      // Wire up radio changes.
      root.querySelectorAll('input[type="radio"][name="q-' + cssEsc(questionId) + '"]').forEach((input) => {
        input.addEventListener("change", () => {
          root.querySelectorAll(".decision-option").forEach((c) => c.classList.remove("picked"));
          const card = input.closest(".decision-option");
          if (card) card.classList.add("picked");
          const note = textarea ? textarea.value : "";
          const answer = { picked: input.value, note };
          this.setSaveState("saving");
          this.writeDecisionAnswer(questionId, answer);
          this.refreshEditedMarkers();
          this.postDecisionAnswer(questionId, this.buildDecisionAnswerMarkdown(slide, answer));
        });
      });

      // Textarea autosave with debounce.
      if (textarea) {
        let timer = null;
        textarea.addEventListener("input", () => {
          this.setSaveState("saving");
          clearTimeout(timer);
          timer = setTimeout(() => {
            const picked = root.querySelector(
              'input[type="radio"][name="q-' + cssEsc(questionId) + '"]:checked'
            );
            const answer = {
              picked: picked ? picked.value : null,
              note: textarea.value,
            };
            this.writeDecisionAnswer(questionId, answer);
            this.refreshEditedMarkers();
            this.postDecisionAnswer(questionId, this.buildDecisionAnswerMarkdown(slide, answer));
          }, SAVE_DEBOUNCE_MS);
        });
      }
    },

    // ---------- Autosave ----------
    bindAutosave() {
      const body = document.getElementById("stage-body");
      let timer = null;
      body.addEventListener("input", (e) => {
        const el = e.target.closest("[contenteditable='true'][data-block-id]");
        if (!el) return;
        this.setSaveState("saving");
        clearTimeout(timer);
        timer = setTimeout(() => {
          const slideEl = el.closest(".slide");
          if (!slideEl) return;
          this.save(slideEl.dataset.slideId, el.dataset.blockId, el.innerHTML);
          el.classList.add("edited");
          this.setSaveState("saved");
          this.refreshEditedMarkers();
        }, SAVE_DEBOUNCE_MS);
      });
    },

    save(slideId, blockId, html) {
      const key = this.storageKeyPrefix(slideId) + "/" + blockId;
      try { window.localStorage.setItem(key, html); }
      catch (err) { console.error("TPR: save failed", err); this.setSaveState("error"); }
    },

    revertSlide(slideId) {
      const prefix = this.storageKeyPrefix(slideId) + "/";
      this.dropKeysWithPrefix(prefix);
      const slide = this.slides.find((s) => s.id === slideId);
      if (slide) this.renderSlide(slide);
      this.refreshEditedMarkers();
      this.setSaveState("saved");
    },

    clearAll() {
      const prefix = (this.meta.storage_key_prefix || "") + "/";
      this.dropKeysWithPrefix(prefix);
      if (this.slides.length) this.renderSlide(this.slides[this.state.current]);
      this.refreshEditedMarkers();
      this.setSaveState("saved");
    },

    dropKeysWithPrefix(prefix) {
      try {
        const victims = [];
        for (let i = 0; i < window.localStorage.length; i += 1) {
          const k = window.localStorage.key(i);
          if (k && k.indexOf(prefix) === 0) victims.push(k);
        }
        victims.forEach((k) => window.localStorage.removeItem(k));
      } catch (err) { console.error("TPR: dropKeysWithPrefix failed", err); }
    },

    setSaveState(s) {
      const node = document.getElementById("save-state");
      if (!node) return;
      node.classList.remove("saving", "error");
      if (s === "saving") { node.classList.add("saving"); node.textContent = "saving…"; }
      else if (s === "error") { node.classList.add("error"); node.textContent = "save failed"; }
      else { node.textContent = "saved"; }
    },

    // ---------- Export ----------
    storageKeyPrefix(slideId) {
      const meta = this.meta.storage_key_prefix || "";
      return meta + "/" + slideId;
    },

    editedSlideIds() {
      const ids = new Set();
      const rootPrefix = (this.meta.storage_key_prefix || "") + "/";
      const decisionPrefix = rootPrefix + "decision/";
      try {
        for (let i = 0; i < window.localStorage.length; i += 1) {
          const k = window.localStorage.key(i);
          if (!k || k.indexOf(rootPrefix) !== 0) continue;
          if (k.indexOf(decisionPrefix) === 0) {
            const qid = k.slice(decisionPrefix.length);
            if (qid) ids.add(qid);
            continue;
          }
          const rest = k.slice(rootPrefix.length);
          const slash = rest.indexOf("/");
          if (slash > 0) ids.add(rest.slice(0, slash));
        }
      } catch (_) {}
      return ids;
    },

    exportFeedback() {
      const iso = new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
      const stage = this.meta.stage || "unknown";
      const lines = ["# Review feedback — " + stage + " — " + iso, ""];
      const rootPrefix = (this.meta.storage_key_prefix || "") + "/";
      let wrote = false;

      this.slides.forEach((slide) => {
        if (slide.mode === "decision") {
          if (this.appendDecisionExport(lines, slide)) wrote = true;
          return;
        }
        const slidePrefix = rootPrefix + slide.id + "/";
        const edits = [];
        try {
          for (let i = 0; i < window.localStorage.length; i += 1) {
            const k = window.localStorage.key(i);
            if (!k || k.indexOf(slidePrefix) !== 0) continue;
            edits.push({ blockId: k.slice(slidePrefix.length), value: window.localStorage.getItem(k) });
          }
        } catch (_) {}
        if (edits.length === 0) return;
        wrote = true;
        lines.push("## Slide: " + slide.title);
        edits.sort((a, b) => a.blockId.localeCompare(b.blockId));
        edits.forEach((e) => {
          const before = this.originalBlockText(slide, e.blockId);
          const after = stripHtml(e.value);
          lines.push("### Block " + e.blockId);
          lines.push("**Before:**");
          lines.push("> " + (before || "_(empty)_"));
          lines.push("");
          lines.push("**After:**");
          lines.push("> " + (after || "_(empty)_"));
          lines.push("");
        });
      });
      if (!wrote) lines.push("_No edits recorded._", "");
      return lines.join("\n");
    },

    appendDecisionExport(lines, slide) {
      const payload = (slide.blocks && slide.blocks[0]) || {};
      const questionId = payload.id || slide.id;
      const answer = this.readDecisionAnswer(questionId);
      if (!answer.picked && !(answer.note || "").trim()) return false;

      const picked = answer.picked
        ? (payload.options || []).find((o) => o.letter === answer.picked)
        : null;
      lines.push("## Decision: " + (payload.topic || slide.title) + " (" + questionId + ")");
      if (picked) {
        lines.push("**Picked:** " + picked.letter + " — " + picked.label);
      } else {
        lines.push("**Picked:** _(no option selected — note only)_");
      }
      if ((answer.note || "").trim()) {
        lines.push("**Note:** " + answer.note.trim());
      }
      lines.push("");
      lines.push("### Original options");
      (payload.options || []).forEach((opt) => {
        const snippet = (opt.rationale || "").replace(/\s+/g, " ").slice(0, 180);
        const tag = opt.recommended ? " (recommended)" : "";
        lines.push("- " + opt.letter + " — " + (opt.label || "") + tag + " — " + snippet);
      });
      lines.push("");
      return true;
    },

    originalBlockText(slide, blockId) {
      const block = (slide.blocks || []).find((b) => b.id === blockId);
      if (!block) return "";
      if (block.text != null) return block.text;
      if (block.html != null) return stripHtml(block.html);
      return "";
    },

    handleExport() {
      const md = this.exportFeedback();
      const iso = new Date().toISOString().replace(/[:.]/g, "-");
      const stage = this.meta.stage || "review";
      const filename = "review-" + stage + "-" + iso + ".md";
      // Capability probe: when loaded over http://, POST directly so the file
      // lands in the goal dir. Anything else (file://, chrome-extension://)
      // falls back to the browser download path.
      if (window.location && window.location.protocol === "http:") {
        this.setSaveState("saving");
        fetch("/feedback", {
          method: "POST",
          headers: { "Content-Type": "text/markdown" },
          body: md,
        })
          .then((resp) => {
            if (!resp.ok) throw new Error("HTTP " + resp.status);
            return resp.json();
          })
          .then((data) => {
            this.setSaveState("saved");
            this.showToast("Saved → " + (data && data.path ? data.path : "goal dir"));
          })
          .catch((err) => {
            console.warn("TPR: server POST failed, falling back to download", err);
            this.setSaveState("error");
            this.downloadMarkdown(md, filename);
          });
        return;
      }
      this.downloadMarkdown(md, filename);
    },

    postDecisionAnswer(questionId, markdown) {
      // Decision-mode companion: when served over http://, stream answers as
      // soon as they autosave so the goal dir reflects the latest picked+note.
      if (!window.location || window.location.protocol !== "http:") return;
      try {
        fetch("/decisions/" + encodeURIComponent(questionId), {
          method: "POST",
          headers: { "Content-Type": "text/markdown" },
          body: markdown,
        }).catch((err) => {
          console.warn("TPR: decision POST failed (localStorage still has it)", err);
        });
      } catch (err) {
        console.warn("TPR: decision POST threw", err);
      }
    },

    showToast(text) {
      let host = document.getElementById("tpr-toast-host");
      if (!host) {
        host = document.createElement("div");
        host.id = "tpr-toast-host";
        host.setAttribute("role", "status");
        host.setAttribute("aria-live", "polite");
        document.body.appendChild(host);
      }
      const toast = document.createElement("div");
      toast.className = "tpr-toast";
      toast.textContent = String(text == null ? "" : text);
      host.appendChild(toast);
      // Fade + remove after 3s; CSS handles the transition.
      setTimeout(() => { toast.classList.add("leaving"); }, 2700);
      setTimeout(() => { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 3200);
    },

    downloadMarkdown(content, filename) {
      const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(url), 0);
    },

    renderEmptyState() {
      const body = document.getElementById("stage-body");
      body.innerHTML =
        '<div class="empty-state">' +
        "<p><strong>No slides to review.</strong></p>" +
        "<p>Run <code>build.py</code> with a populated goal directory once renderers are wired up.</p>" +
        "</div>";
      document.getElementById("stage-counter").textContent = "0 / 0";
    },
  };

  function renderDecisionCard(slide) {
    const payload = (slide.blocks && slide.blocks[0]) || {};
    const questionId = payload.id || slide.id;
    const topic = payload.topic || slide.title || "";
    const stage = payload.stage || "";
    const blocking = !!payload.blocking;
    const contextHtml = payload.context_html || "";
    const options = payload.options || [];
    const refs = payload.references || [];
    const warnings = payload.warnings || [];

    let out = '<section class="decision-card" data-question-id="' + esc(questionId) + '">';

    // Header chips
    out += '<div class="decision-card-header">';
    out += '<span class="chip id">' + esc(questionId) + "</span>";
    if (stage) out += '<span class="chip">' + esc(stage) + "</span>";
    if (blocking) out += '<span class="chip blocking">blocking</span>';
    out += "</div>";

    // Topic
    out += '<h3 class="decision-topic">' + esc(topic) + "</h3>";

    // Warnings banner
    if (warnings.length) {
      out += '<details class="decision-warnings">';
      out += "<summary>Build warnings (" + warnings.length + ")</summary>";
      out += "<ul>";
      warnings.forEach((w) => { out += "<li>" + esc(w) + "</li>"; });
      out += "</ul></details>";
    }

    // Context
    if (contextHtml) {
      out += '<div class="decision-context">' + contextHtml + "</div>";
    }

    // Options list
    out += '<div class="decision-options-list" role="radiogroup" aria-labelledby="topic-' + esc(questionId) + '">';
    options.forEach((opt) => {
      const letter = opt.letter || "";
      const label = opt.label || "";
      const rationaleHtml = opt.rationale_html
        || (opt.rationale ? "<p>" + esc(opt.rationale) + "</p>" : "");
      const classes = ["decision-option"];
      if (opt.recommended) classes.push("recommended");
      out += '<label class="' + classes.join(" ") + '">';
      out += '<input type="radio" name="q-' + esc(questionId) + '" value="' + esc(letter) + '">';
      out += '<div class="option-head">';
      out += '<span class="option-letter">' + esc(letter) + "</span>";
      out += '<span class="option-label">' + esc(label) + "</span>";
      out += "</div>";
      out += '<div class="option-rationale">' + rationaleHtml + "</div>";
      out += "</label>";
    });
    out += "</div>";

    // Free-text response
    out += '<div class="decision-response">';
    out += '<label for="note-' + esc(questionId) + '">Notes / caveat</label>';
    out += '<textarea id="note-' + esc(questionId) + '" ';
    out += 'placeholder="Optional free-text response — caveats, custom answer, push-back on framing…"></textarea>';
    out += "</div>";

    // References block
    if (refs.length) {
      out += '<div class="decision-references">';
      out += '<div class="ref-title">References</div>';
      out += "<ul>";
      refs.forEach((r) => {
        out += '<li><code>' + esc(r) + "</code></li>";
      });
      out += "</ul></div>";
    }

    out += "</section>";
    return out;
  }

  function stripHtml(html) {
    const tmp = document.createElement("div");
    tmp.innerHTML = html || "";
    return (tmp.textContent || "").trim();
  }

  function cssEsc(s) {
    if (window.CSS && typeof window.CSS.escape === "function") return window.CSS.escape(s);
    return String(s).replace(/["\\]/g, "\\$&");
  }

  function confirmClear() {
    // Intentionally simple; avoid modal libraries.
    return window.confirm("Clear all edits across every slide? This cannot be undone.");
  }

  window.TPR = TPR;
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => TPR.init());
  } else {
    TPR.init();
  }
})();
